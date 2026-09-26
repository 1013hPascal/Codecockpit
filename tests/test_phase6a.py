"""Phase 6a: Pull Requests erstellen, ansehen, kommentieren, Entwürfe, schließen.

Die Plattform ist eine Attrappe (PullFake) oder der GitHub-Adapter gegen einen nachgebauten
Server. Kein echtes Netz, alle Tokens sind erfunden.
"""
from __future__ import annotations

import json

import pytest

from cockpit.core import git, project_status, pull_requests
from cockpit.core.git import RemoteAddress
from cockpit.platforms.base import (Collaborator, PullRequest, PullRequestComment,
                                    PullRequestFile, RepoRef, SupportsCollaborators,
                                    SupportsPullRequests)
from cockpit.platforms.github import GitHubPlatform, graphql_url
from cockpit.ui import pull_request_dialogs
from tests.conftest import FakePlatform, said
from tests.test_github import platform as github_platform, server  # noqa: F401
from tests.test_phase5a import account, live, sh, wait_idle  # noqa: F401
from tests.test_phase5b import write
from tests.test_phase5c import labels, select_code, setup_repo
from tests.test_phase5e import connected_project

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

ADDRESS = RemoteAddress("github.com", "tester", "Tagebuch")
REF = RepoRef("tester", "Tagebuch")


def pull(number=12, title="Suche in PDFs", head="design", state="open", draft=False, **kw):
    return PullRequest(number, title, head, "main", "anna", state, draft, **kw)


class PullFake(FakePlatform, SupportsPullRequests, SupportsCollaborators):
    """Plattform-Attrappe mit Pull Requests, merkt sich jeden Aufruf."""

    def __init__(self) -> None:
        super().__init__()
        self.pulls = [pull(12), pull(11, "Alt", "alt", "closed"), pull(10, "Fertig", "x",
                                                                         "merged")]
        self.comments = [PullRequestComment("anna", "2026-09-24T10:00:00Z", "Sieht gut aus")]
        self.calls: list[tuple] = []

    def pull_requests(self, repo, state="open"):
        self.calls.append(("list", state))
        if state == "all":
            return list(self.pulls)
        return [p for p in self.pulls if (p.state == "open") == (state == "open")]

    def pull_request(self, repo, number):
        return next(p for p in self.pulls if p.number == number)

    def create_pull_request(self, repo, head, base, title, body, draft=False, reviewers=()):
        self.calls.append(("create", head, base, title, body, draft, reviewers))
        created = PullRequest(13, title, head, base, "tester", "open", draft, body)
        self.pulls.insert(0, created)
        return created

    def pull_request_comments(self, repo, number):
        return list(self.comments)

    def add_pull_request_comment(self, repo, number, body):
        self.calls.append(("comment", number, body))
        self.comments.append(PullRequestComment("tester", "2026-09-26T10:00:00Z", body))

    def pull_request_files(self, repo, number):
        return [PullRequestFile("main.py", "modified", 5, 2)]

    def set_pull_request_open(self, repo, number, open_):
        self.calls.append(("open" if open_ else "close", number))
        self.pulls = [PullRequest(**{**p.__dict__, "state": "open" if open_ else "closed"})
                      if p.number == number else p for p in self.pulls]

    def mark_ready_for_review(self, repo, pull_):
        self.calls.append(("ready", pull_.number))
        self.pulls = [PullRequest(**{**p.__dict__, "draft": False})
                      if p.number == pull_.number else p for p in self.pulls]

    def collaborators(self, repo):
        return [Collaborator("ben", "write"), Collaborator("max", "read", 7)]


def idle(qtbot, dialog):
    qtbot.waitUntil(lambda: not dialog.worker.busy, timeout=10000)


# -- GitHub-Adapter -----------------------------------------------------------------------------
def pr_json(number=12, **extra):
    data = {"number": number, "title": "Suche", "head": {"ref": "design"},
            "base": {"ref": "main"}, "user": {"login": "anna"}, "state": "open", "draft": False,
            "body": "Text", "created_at": "2026-09-24T10:00:00Z",
            "html_url": f"https://github.com/o/r/pull/{number}", "node_id": f"PR_{number}",
            "requested_reviewers": [{"login": "ben"}]}
    data.update(extra)
    return data


def test_github_lists_pull_requests(server):
    server.route("GET", "/repos/o/r/pulls", body=[
        pr_json(12), pr_json(11, state="closed", merged_at="2026-09-20T10:00:00Z"),
        pr_json(10, state="closed", draft=True)])
    pulls = github_platform().pull_requests(RepoRef("o", "r"), "all")
    assert [(p.number, p.state) for p in pulls] == [(12, "open"), (11, "merged"), (10, "closed")]
    assert pulls[0].head == "design" and pulls[0].reviewers == ("ben",)
    assert pulls[0].node_id == "PR_12" and pulls[2].draft
    params = server.requests[-1].url.params
    assert params["state"] == "all" and params["direction"] == "desc"


def test_github_creates_with_reviewers(server):
    server.route("POST", "/repos/o/r/pulls", 201, pr_json(13, draft=True))
    server.route("POST", "/repos/o/r/pulls/13/requested_reviewers", 201, {})
    created = github_platform().create_pull_request(RepoRef("o", "r"), "design", "main", "T",
                                                    "B", True, ("ben",))
    assert created.number == 13 and created.reviewers == ("ben",)
    sent = json.loads(server.requests[-2].content)
    assert sent == {"title": "T", "head": "design", "base": "main", "body": "B", "draft": True}
    assert json.loads(server.requests[-1].content) == {"reviewers": ["ben"]}


def test_github_explains_rejected_pull_requests(server):
    server.route("POST", "/repos/o/r/pulls", 422, {
        "message": "Validation Failed",
        "errors": [{"message": "No commits between main and design"}]})
    with pytest.raises(Exception, match="keinen Unterschied"):
        github_platform().create_pull_request(RepoRef("o", "r"), "design", "main", "T", "")
    server.route("POST", "/repos/o/r/pulls", 422, {
        "message": "Validation Failed",
        "errors": [{"message": "A pull request already exists for o:design."}]})
    with pytest.raises(Exception, match="schon einen offenen Pull Request"):
        github_platform().create_pull_request(RepoRef("o", "r"), "design", "main", "T", "")


def test_github_comments_files_and_state(server):
    ref = RepoRef("o", "r")
    server.route("GET", "/repos/o/r/issues/12/comments", body=[
        {"user": {"login": "anna"}, "created_at": "2026-09-24T12:00:00Z", "body": "Später"}])
    server.route("GET", "/repos/o/r/pulls/12/comments", body=[
        {"user": {"login": "ben"}, "created_at": "2026-09-24T11:00:00Z", "body": "Test fehlt",
         "path": "main.py", "line": None, "original_line": 12}])
    comments = github_platform().pull_request_comments(ref, 12)
    assert [pull_requests.comment_line(c) for c in comments] == [
        "ben zu main.py Zeile 12, 24.09.2026: Test fehlt", "anna, 24.09.2026: Später"]
    server.route("POST", "/repos/o/r/issues/12/comments", 201, {})
    github_platform().add_pull_request_comment(ref, 12, "Danke")
    assert json.loads(server.requests[-1].content) == {"body": "Danke"}
    server.route("GET", "/repos/o/r/pulls/12/files", body=[
        {"filename": "main.py", "status": "modified", "additions": 5, "deletions": 2,
         "patch": "@@ -1 +1 @@"}])
    files = github_platform().pull_request_files(ref, 12)
    assert pull_requests.file_line(files[0]) == "main.py, geändert, 5 Zeilen dazu, 2 Zeilen weg"
    server.route("PATCH", "/repos/o/r/pulls/12", 200, pr_json(12, state="closed"))
    github_platform().set_pull_request_open(ref, 12, False)
    assert json.loads(server.requests[-1].content) == {"state": "closed"}


def test_github_ready_for_review_uses_graphql(server):
    server.route("POST", "/graphql", 200, {"data": {}})
    github_platform().mark_ready_for_review(RepoRef("o", "r"), pull(node_id="PR_12"))
    request = server.requests[-1]
    assert str(request.url) == "https://api.github.com/graphql"
    assert json.loads(request.content)["variables"] == {"id": "PR_12"}
    server.route("POST", "/graphql", 200, {"errors": [{"message": "nope"}]})
    with pytest.raises(Exception, match="Freigabe abgelehnt"):
        github_platform().mark_ready_for_review(RepoRef("o", "r"), pull(node_id="PR_12"))
    assert graphql_url("https://git.firma.de") == "https://git.firma.de/api/graphql"


# -- Kern -----------------------------------------------------------------------------------------
def test_lines_for_pull_requests():
    assert pull_requests.pull_line(pull(draft=True)) == (
        "Nr. 12: Suche in PDFs, von design nach main, von anna, Entwurf")
    assert pull_requests.pull_line(pull(state="merged")).endswith(", übernommen")
    lines = pull_requests.pull_details(pull(body="Zeile eins\n\nZeile zwei",
                                            created="2026-09-24T10:00:00Z", reviewers=("ben",)))
    assert lines == ["Nr. 12: Suche in PDFs", "Offen", "Von design nach main",
                     "Erstellt von anna am 24.09.2026", "Prüfer angefragt: ben",
                     "Beschreibung:", "Zeile eins", "Zeile zwei"]
    assert pull_requests.file_line(PullRequestFile("neu.py", "added", 1, 0)) == (
        "neu.py, neu, 1 Zeile dazu")


def test_cache_counts_open_pulls_per_branch(make_services):
    services = make_services()
    cache = services.pull_request_cache
    cache.replace(ADDRESS, [pull(12), pull(11, head="design"), pull(10, head="x",
                                                                    state="closed")])
    assert [p.number for p in cache.open_pulls(ADDRESS)] == [12, 11]
    assert cache.count_for_branch(ADDRESS, "design") == 2
    assert cache.count_for_branch(ADDRESS, "x") == 0
    assert cache.count_for_branch(None, "design") == 0
    cache.replace(ADDRESS, [])
    assert cache.open_pulls(ADDRESS) == []


def test_suggestion_from_commits(tmp_path, projects_root):
    _, code, _ = setup_repo(tmp_path, projects_root)
    sh(code, "switch", "-q", "-c", "suche-pdfs")
    write(code, "a.py", "1\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Suche ergänzt", "-m", "Mit Test.")
    assert pull_requests.suggest(code, "suche-pdfs", "main") == ("Suche ergänzt", "Mit Test.")
    write(code, "b.py", "1\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Noch mehr")
    assert pull_requests.suggest(code, "suche-pdfs", "main") == (
        "Suche pdfs", "- Suche ergänzt\n- Noch mehr")
    assert pull_requests.upload_needed(code, "suche-pdfs") == -1
    sh(code, "push", "-q", "-u", "origin", "suche-pdfs")
    assert pull_requests.upload_needed(code, "suche-pdfs") == 0
    write(code, "c.py", "1\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Dritter")
    assert pull_requests.upload_needed(code, "suche-pdfs") == 1


def test_code_line_and_branch_line_name_open_pulls(make_services, tmp_path, projects_root):
    from cockpit.core import branches
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = services.projects.add(code.parent)
    status = project_status.compute(project)
    status.open_pulls = 1
    assert project_status.code_line(status) == "Code, alles hochgeladen, 1 offener Pull Request"
    item = branches.Branch("design", local=True, remote=True, open_pulls=2)
    assert "2 offene Pull Requests" in item.line()


def test_refresh_fills_the_cache(account, tmp_path, projects_root):
    from cockpit.ui.main_window import refresh_pull_requests
    services, acc, _ = account
    _, code, _ = setup_repo(tmp_path, projects_root)
    connected_project(services, code, acc.id)
    fake = PullFake()
    refresh_pull_requests(services, fake, acc)
    assert services.pull_request_cache.count_for_branch(ADDRESS, "design") == 1
    refresh_pull_requests(services, FakePlatform(), acc)            # ohne Pull Requests: nichts
    assert services.pull_request_cache.count_for_branch(ADDRESS, "design") == 1


# -- Aktionen -----------------------------------------------------------------------------------
def test_code_actions(live, qtbot, account, tmp_path, projects_root):
    services, acc, _ = account
    services.platforms[acc.id] = PullFake()
    _, code, _ = setup_repo(tmp_path, projects_root)
    connected_project(services, code, acc.id)
    win = live(services)
    select_code(win, services, code)
    texts = labels(win)
    assert "Pull Requests …" in texts and "Pull Request erstellen …" not in texts
    assert texts.index("Branches …") < texts.index("Pull Requests …")
    sh(code, "switch", "-q", "-c", "design")
    win.refresh_status()
    wait_idle(qtbot, win)
    assert "Pull Request erstellen …" in labels(win)


def test_open_list_from_the_window(live, qtbot, account, tmp_path, projects_root, monkeypatch):
    services, acc, _ = account
    fake = PullFake()
    services.platforms[acc.id] = fake
    _, code, _ = setup_repo(tmp_path, projects_root)
    connected_project(services, code, acc.id)
    win = live(services)
    select_code(win, services, code)
    shown = []

    class FakeList:
        def __init__(self, platform, ref, address, cache, pulls, create, platform_name,
                     parent=None):
            shown.append([p.number for p in pulls])

        def exec(self):
            return 0

    monkeypatch.setattr(pull_request_dialogs, "PullRequestsDialog", FakeList)
    entry = next(e for e in win.current_entries() if e.action.id == "pull_requests")
    win.run_entry(entry)
    qtbot.waitUntil(lambda: bool(shown), timeout=10000)
    assert shown == [[12]]
    assert services.pull_request_cache.count_for_branch(ADDRESS, "design") == 1
    wait_idle(qtbot, win)


def test_create_on_main_explains(live, qtbot, account, tmp_path, projects_root, monkeypatch):
    from cockpit.ui import pull_request_flow
    services, acc, _ = account
    services.platforms[acc.id] = PullFake()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code, acc.id)
    win = live(services)
    errors = []
    monkeypatch.setattr(pull_request_flow, "show_error", lambda *a: errors.append(a[2]))
    pull_request_flow.PullRequestRunner(win.controller, project).create()
    assert errors[0].startswith("Sie sind auf main.")


def test_create_uploads_first_then_creates(live, qtbot, account, tmp_path, projects_root,
                                           monkeypatch):
    from cockpit.ui import pull_request_flow, sync_flow
    services, acc, _ = account
    fake = PullFake()
    services.platforms[acc.id] = fake
    bare, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code, acc.id)
    sh(code, "remote", "set-url", "origin", str(bare))            # hochladen geht in den Ordner
    sh(code, "switch", "-q", "-c", "suche-pdfs")
    write(code, "a.py", "1\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Suche ergänzt")
    win = live(services)
    questions = []
    monkeypatch.setattr(pull_request_flow, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or True)
    monkeypatch.setattr(sync_flow, "confirm", lambda *a, **k: True)
    seen = []

    class FakeCreate:
        def __init__(self, head, bases, main, title, body, people, note, parent=None):
            seen.append((head, bases, main, title, body, people, note))
            self.head, self.base, self.title, self.body = head, "main", title, body
            self.draft, self.reviewers = True, ("ben",)

        def exec(self):
            return 1

    monkeypatch.setattr(pull_request_dialogs, "CreatePullRequestDialog", FakeCreate)
    pull_request_flow.PullRequestRunner(win.controller, project).create()
    text, buttons = questions[0]
    assert text.startswith("Der Branch suche-pdfs ist noch nicht auf GitHub.")
    assert buttons == {"yes": "Hochladen und weiter", "no": "Abbrechen"}
    qtbot.waitUntil(lambda: said("Pull Request Nr. 13 erstellt als Entwurf."), timeout=20000)
    assert "suche-pdfs" in sh(bare, "branch", "--list")
    head, bases, main, title, body, people, note = seen[0]
    assert (head, main, title, people) == ("suche-pdfs", "main", "Suche ergänzt", ["ben"])
    assert bases[0] == "main" and "suche-pdfs" not in bases and note == ""
    assert fake.calls[-2][0] == "create" and fake.calls[-2][5:] == (True, ("ben",))
    wait_idle(qtbot, win)


# -- Fenster ------------------------------------------------------------------------------
def test_list_dialog_filter_and_details(qtbot, make_services, monkeypatch):
    services = make_services()
    fake = PullFake()
    dialog = pull_request_dialogs.PullRequestsDialog(
        fake, REF, ADDRESS, services.pull_request_cache, fake.pull_requests(REF, "open"))
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Pull Requests von Tagebuch: 1 Pull Request, offene"
    assert dialog.list.item(0).text() == ("Nr. 12: Suche in PDFs, von design nach main, "
                                          "von anna")
    assert dialog.filter.accessibleName() == "Anzeigen"
    dialog.filter.setCurrentIndex(2)                                # alle
    idle(qtbot, dialog)
    assert dialog.list.count() == 3 and dialog.list.item(2).text().endswith(", übernommen")
    dialog.filter.setCurrentIndex(1)                                # geschlossene
    idle(qtbot, dialog)
    assert dialog.list.count() == 2
    errors = []
    monkeypatch.setattr(pull_request_dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog.new_pull()                                              # ohne Branch mit Änderungen
    assert "Wechseln Sie zuerst" in errors[0]


def test_details_comment_close_and_ready(qtbot, monkeypatch):
    fake = PullFake()
    fake.pulls[0] = pull(12, draft=True)
    questions = []
    monkeypatch.setattr(pull_request_dialogs, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or True)
    dialog = pull_request_dialogs.PullRequestDialog(fake, REF, fake.pulls[0])
    qtbot.addWidget(dialog)
    dialog.show()
    idle(qtbot, dialog)
    assert dialog.info.item(1).text() == "Offen, Entwurf"
    assert dialog.files.item(0).text() == "main.py, geändert, 5 Zeilen dazu, 2 Zeilen weg"
    assert dialog.comments.item(0).text() == "anna, 24.09.2026: Sieht gut aus"
    assert dialog.comments.accessibleName() == "Kommentare"
    assert dialog.ready_button.isVisible()
    errors = []
    monkeypatch.setattr(pull_request_dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog.send_comment()
    assert errors == ["Bitte schreiben Sie zuerst einen Kommentar."]
    dialog.edit.setPlainText("Danke!")
    dialog.send_comment()
    idle(qtbot, dialog)
    qtbot.waitUntil(lambda: said("Kommentar gesendet."), timeout=5000)
    assert dialog.comments.currentItem().text() == "tester, 26.09.2026: Danke!"
    assert dialog.edit.toPlainText() == ""
    dialog.mark_ready()
    idle(qtbot, dialog)
    qtbot.waitUntil(lambda: said("Zum Prüfen freigegeben."), timeout=5000)
    assert not dialog.ready_button.isVisible()
    assert dialog.state_button.text() == "Pull Request s&chließen …"
    dialog.toggle_state()
    assert "ohne übernommen zu werden" in questions[-1][0]
    assert questions[-1][1] == {"yes": "Schließen", "no": "Abbrechen"}
    idle(qtbot, dialog)
    qtbot.waitUntil(lambda: said("Nr. 12 ist geschlossen."), timeout=5000)
    assert dialog.state_button.text() == "Wieder ö&ffnen"
    dialog.toggle_state()
    idle(qtbot, dialog)
    qtbot.waitUntil(lambda: said("Nr. 12 ist wieder offen."), timeout=5000)
    assert [c[0] for c in fake.calls] == ["comment", "ready", "close", "open"]
    assert dialog.changed


def test_create_dialog(qtbot, monkeypatch):
    from PySide6.QtCore import Qt
    errors = []
    monkeypatch.setattr(pull_request_dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog = pull_request_dialogs.CreatePullRequestDialog(
        "design", ["main", "entwicklung"], "main", "Vorschlag", "- A", ["ben", "max"],
        "Hinweis")
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Pull Request erstellen: von design"
    assert dialog.title_edit.accessibleName() == "Titel"
    assert dialog.base_box.currentText() == "main"
    assert not dialog.draft_box.isChecked()
    dialog.title_edit.setText("  ")
    dialog.check()
    assert errors == [pull_request_dialogs.NO_TITLE] and dialog.result() == 0
    dialog.title_edit.setText("Neues  Design")
    dialog.people.item(1).setCheckState(Qt.CheckState.Checked)
    dialog.draft_box.setChecked(True)
    dialog.check()
    assert (dialog.title, dialog.base, dialog.body, dialog.reviewers, dialog.draft) == (
        "Neues Design", "main", "- A", ("max",), True)
