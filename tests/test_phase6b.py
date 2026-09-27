"""Phase 6b: Reviews, Änderungen ansehen, in main übernehmen und aufräumen.

Die Plattform ist eine Attrappe (ReviewFake) oder der GitHub-Adapter gegen einen nachgebauten
Server. Das Aufräumen läuft mit echtem Git gegen ein nacktes Repository. Kein echtes Netz.
"""
from __future__ import annotations

import json

import pytest

from cockpit.core import branches, git, pull_requests
from cockpit.core.errors import CockpitError
from cockpit.platforms.base import PullRequest, PullRequestFile, RepoRef, Review
from cockpit.ui import pull_request_dialogs
from tests.conftest import said
from tests.test_github import platform as github_platform, server  # noqa: F401
from tests.test_phase5a import sh
from tests.test_phase5b import write
from tests.test_phase5c import setup_repo
from tests.test_phase6a import ADDRESS, REF, PullFake, idle, pr_json, pull

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

PATCH = "@@ -1,3 +1,3 @@\n a\n-b\n+B\n c\n@@ -10,2 +10,3 @@\n x\n+\n+neu\n\\ No newline at end of file"


class ReviewFake(PullFake):
    def __init__(self) -> None:
        super().__init__()
        self.review_list = [Review("ben", "APPROVED", "Passt", "2026-09-24T12:00:00Z")]
        self.methods = ["merge", "squash", "rebase"]
        self.merged: list = []

    def reviews(self, repo, number):
        return list(self.review_list) if number == 12 else []

    def submit_review(self, repo, number, event, body):
        self.calls.append(("review", number, event, body))

    def merge_methods(self, repo):
        return list(self.methods)

    def merge_pull_request(self, repo, number, method):
        self.calls.append(("merge", number, method))
        self.pulls = [PullRequest(**{**p.__dict__, "state": "merged"})
                      if p.number == number else p for p in self.pulls]

    def pull_request_files(self, repo, number):
        return [PullRequestFile("main.py", "modified", 2, 1, PATCH),
                PullRequestFile("bild.png", "added")]


def list_dialog(qtbot, make_services, fake, **kw):
    services = make_services()
    dialog = pull_request_dialogs.PullRequestsDialog(
        fake, REF, ADDRESS, services.pull_request_cache, fake.pull_requests(REF, "open"),
        summaries={12: "1 Genehmigung"}, **kw)
    qtbot.addWidget(dialog)
    return dialog


# -- GitHub-Adapter -----------------------------------------------------------------------------
def test_github_reviews_and_submit(server):
    ref = RepoRef("o", "r")
    server.route("GET", "/repos/o/r/pulls/12/reviews", body=[
        {"user": {"login": "ben"}, "state": "APPROVED", "body": "", "submitted_at": "x"}])
    assert github_platform().reviews(ref, 12) == [Review("ben", "APPROVED", "", "x")]
    server.route("POST", "/repos/o/r/pulls/12/reviews", 200, {})
    github_platform().submit_review(ref, 12, "REQUEST_CHANGES", "Test fehlt")
    assert json.loads(server.requests[-1].content) == {"event": "REQUEST_CHANGES",
                                                       "body": "Test fehlt"}
    server.route("POST", "/repos/o/r/pulls/12/reviews", 422,
                 {"message": "Unprocessable Entity",
                  "errors": ["Can not approve your own pull request"]})
    with pytest.raises(CockpitError, match="eigenen Pull Request"):
        github_platform().submit_review(ref, 12, "APPROVE", "")


def test_github_merge_methods_and_merge(server):
    ref = RepoRef("o", "r")
    server.route("GET", "/repos/o/r", body={"allow_merge_commit": True,
                                            "allow_squash_merge": False,
                                            "allow_rebase_merge": True})
    assert github_platform().merge_methods(ref) == ["merge", "rebase"]
    server.route("PUT", "/repos/o/r/pulls/12/merge", 200, {"merged": True})
    github_platform().merge_pull_request(ref, 12, "squash")
    assert json.loads(server.requests[-1].content) == {"merge_method": "squash"}
    server.route("PUT", "/repos/o/r/pulls/12/merge", 405,
                 {"message": "Pull Request is not mergeable"})
    with pytest.raises(CockpitError, match="kann den Pull Request so nicht übernehmen"):
        github_platform().merge_pull_request(ref, 12, "merge")


def test_github_reads_mergeable_state(server):
    server.route("GET", "/repos/o/r/pulls/12", body=pr_json(12, mergeable=False,
                                                            mergeable_state="dirty"))
    fresh = github_platform().pull_request(RepoRef("o", "r"), 12)
    assert fresh.mergeable is False and fresh.mergeable_state == "dirty"


# -- Kern -----------------------------------------------------------------------------------------
def test_review_summary_counts_the_latest_per_person():
    reviews = [Review("ben", "CHANGES_REQUESTED", "", "1"), Review("ben", "APPROVED", "", "2"),
               Review("anna", "COMMENTED", "Frage", "3"), Review("max", "APPROVED", "", "4"),
               Review("zora", "CHANGES_REQUESTED", "", "5")]
    assert pull_requests.review_summary(reviews) == (2, 1)
    assert pull_requests.summary_text(2, 1) == "2 Genehmigungen, Änderungen angefordert"
    assert pull_requests.summary_text(0, 0) == ""


def test_review_lines():
    assert pull_requests.review_line(Review("ben", "APPROVED", "Passt",
                                            "2026-09-24T12:00:00Z")) == (
        "ben hat genehmigt, 24.09.2026: Passt")
    assert pull_requests.review_line(Review("ben", "CHANGES_REQUESTED", "", "")) == (
        "ben fordert Änderungen an")
    assert pull_requests.review_line(Review("ben", "COMMENTED", "", "")) == ""


def test_merge_state_texts():
    text = pull_requests.merge_state_text
    assert text(pull(mergeable=True, mergeable_state="clean")) == "Kann übernommen werden"
    assert text(pull(mergeable=False, mergeable_state="dirty")).startswith(
        "Hat Konflikte mit main")
    assert "Schutzregeln" in text(pull(mergeable_state="blocked"))
    assert text(pull(draft=True)).startswith("Entwurf")
    assert text(pull(state="closed")) == ""


def test_diff_lines_are_readable():
    assert pull_requests.diff_lines(PATCH) == [
        "Weg Zeile 2: b", "Neu Zeile 2: B", "Neu Zeile 11: (leere Zeile)", "Neu Zeile 12: neu"]
    assert pull_requests.diff_lines("") == []


def merged_on_platform(tmp_path, projects_root):
    """Branch design ist hochgeladen und auf der Plattform in main übernommen."""
    bare, code, other = setup_repo(tmp_path, projects_root)
    sh(code, "switch", "-q", "-c", "design")
    write(code, "design.css", "x\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Design")
    sh(code, "push", "-q", "-u", "origin", "design")
    sh(other, "fetch", "-q")
    sh(other, "merge", "-q", "--no-edit", "origin/design")
    sh(other, "push", "-q")
    return bare, code


def test_clean_up_after_merge(tmp_path, projects_root):
    bare, code = merged_on_platform(tmp_path, projects_root)
    done = pull_requests.clean_up(code, "Tagebuch", "design")
    assert done == ["Sie sind auf main.", "Die Änderungen von main sind geholt.",
                    "Der Branch design ist gelöscht."]
    assert git.status(code).branch == "main" and (code / "design.css").exists()
    assert "design" not in sh(bare, "branch", "--list")
    assert "design" not in {b.name for b in branches.list_branches(code)}


def test_clean_up_needs_a_clean_folder(tmp_path, projects_root):
    _, code = merged_on_platform(tmp_path, projects_root)
    write(code, "design.css", "anders\n")
    with pytest.raises(CockpitError, match="Änderungen ohne Commit"):
        pull_requests.clean_up(code, "Tagebuch", "design")
    assert git.status(code).branch == "design"


# -- Fenster ------------------------------------------------------------------------------
def test_list_shows_reviews_and_buttons(qtbot, make_services):
    fake = ReviewFake()
    dialog = list_dialog(qtbot, make_services, fake)
    dialog.show()
    assert dialog.list.item(0).text() == ("Nr. 12: Suche in PDFs, von design nach main, "
                                          "von anna, 1 Genehmigung")
    assert dialog.review_button.isVisible() and dialog.merge_button.isVisible()
    assert dialog.merge_button.text() == "In main &übernehmen …"
    dialog.load()
    idle(qtbot, dialog)
    assert dialog.list.item(0).text().endswith(", 1 Genehmigung")


def test_review_from_the_list(qtbot, make_services, monkeypatch):
    fake = ReviewFake()
    dialog = list_dialog(qtbot, make_services, fake, own_login="tester")

    class Approve:
        def __init__(self, pull_, own, parent=None):
            assert own is False                              # anna hat ihn erstellt
            self.verdict, self.body = "APPROVE", ""

        def exec(self):
            return 1

    monkeypatch.setattr(pull_request_dialogs, "ReviewDialog", Approve)
    dialog.review_current()
    idle(qtbot, dialog)
    qtbot.waitUntil(lambda: said("Nr. 12 genehmigt."), timeout=5000)
    assert fake.calls[-2] == ("review", 12, "APPROVE", "")


def test_review_dialog(qtbot, monkeypatch):
    errors = []
    monkeypatch.setattr(pull_request_dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog = pull_request_dialogs.ReviewDialog(pull(), own=False)
    qtbot.addWidget(dialog)
    assert [dialog.choice.itemText(i) for i in range(3)] == [
        "Nur kommentieren", "Genehmigen", "Änderungen anfordern"]
    assert dialog.choice.accessibleName() == "Ergebnis"
    dialog.choice.setCurrentIndex(2)
    dialog.check()
    assert "Nur beim Genehmigen darf er fehlen" in errors[0] and dialog.result() == 0
    dialog.edit.setPlainText("Test fehlt")
    dialog.check()
    assert (dialog.verdict, dialog.body) == ("REQUEST_CHANGES", "Test fehlt")
    own = pull_request_dialogs.ReviewDialog(pull(), own=True)
    qtbot.addWidget(own)
    assert own.choice.count() == 1 and own.choice.itemText(0) == "Nur kommentieren"


def test_merge_dialog(qtbot):
    dialog = pull_request_dialogs.MergeDialog(pull(mergeable=True, mergeable_state="clean"),
                                              ["merge", "squash"], "1 Genehmigung")
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "In main übernehmen: Nr. 12: Suche in PDFs"
    assert dialog.choice.accessibleName() == "Art des Übernehmens"
    assert dialog.choice.itemText(0).startswith("Merge-Commit:")
    assert dialog.choice.count() == 2
    buttons = [b for b in dialog.findChildren(pull_request_dialogs.QPushButton) if b.isDefault()]
    assert [b.text() for b in buttons] == ["Abbrechen"]                # sichere Vorgabe
    dialog.choice.setCurrentIndex(1)
    dialog.check()
    assert dialog.method == "squash"


def test_merge_and_clean_up_from_the_list(qtbot, make_services, tmp_path, projects_root,
                                          monkeypatch):
    _, code = merged_on_platform(tmp_path, projects_root)
    services = make_services()
    project = services.projects.add(code.parent)
    fake = ReviewFake()
    questions = []

    class Squash:
        def __init__(self, pull_, methods, reviews, parent=None):
            assert methods == ["merge", "squash", "rebase"] and reviews == "1 Genehmigung"
            self.method = "squash"

        def exec(self):
            return 1

    def ask_buttons(parent, title, text, buttons, default, escape):
        questions.append((text, buttons, default))
        return 0

    monkeypatch.setattr(pull_request_dialogs, "MergeDialog", Squash)
    monkeypatch.setattr(pull_request_dialogs, "ask_buttons", ask_buttons)
    dialog = list_dialog(qtbot, make_services, fake, project=project)
    dialog.merge_current()
    qtbot.waitUntil(lambda: said("Sie sind auf main. Die Änderungen von main sind geholt. Der "
                                 "Branch design ist gelöscht."), timeout=20000)
    assert ("merge", 12, "squash") in fake.calls
    assert said("Nr. 12 ist in main übernommen.")
    text, buttons, default = questions[0]
    assert text.startswith("Nr. 12 ist in main übernommen. Zu main wechseln, die Änderungen "
                           "holen und den Branch design hier und auf GitHub löschen?")
    assert buttons == ["Aufräumen", "Später"] and default == 1
    assert git.status(code).branch == "main"


def test_merge_later_keeps_the_branch(qtbot, make_services, tmp_path, projects_root,
                                      monkeypatch):
    _, code = merged_on_platform(tmp_path, projects_root)
    services = make_services()
    project = services.projects.add(code.parent)
    fake = ReviewFake()

    class Merge:
        def __init__(self, *a, **k):
            self.method = "merge"

        def exec(self):
            return 1

    monkeypatch.setattr(pull_request_dialogs, "MergeDialog", Merge)
    monkeypatch.setattr(pull_request_dialogs, "ask_buttons", lambda *a, **k: 1)   # Später
    dialog = list_dialog(qtbot, make_services, fake, project=project)
    dialog.merge_current()
    qtbot.waitUntil(lambda: said("Nr. 12 ist in main übernommen."), timeout=10000)
    idle(qtbot, dialog)
    assert git.status(code).branch == "design"


def test_details_show_changes_and_state(qtbot, monkeypatch):
    from cockpit.ui import text_dialog
    fake = ReviewFake()
    fake.pulls[0] = pull(12, mergeable=True, mergeable_state="clean")
    shown = []

    class FakeText:
        def __init__(self, title, lines, name, parent=None):
            shown.append((title, lines))

        def exec(self):
            return 0

    monkeypatch.setattr(text_dialog, "TextDialog", FakeText)
    dialog = pull_request_dialogs.PullDetailsDialog(fake, REF, fake.pulls[0])
    qtbot.addWidget(dialog)
    idle(qtbot, dialog)
    lines = [dialog.info.item(i).text() for i in range(dialog.info.count())]
    assert lines[:4] == ["Nr. 12: Suche in PDFs", "Offen", "1 Genehmigung",
                         "Kann übernommen werden"]
    from PySide6.QtCore import Qt
    dialog.files.setCurrentRow(0)
    qtbot.keyClick(dialog.files, Qt.Key.Key_Return)
    assert shown[0][0] == "Änderungen in main.py: 4 Zeilen"
    assert shown[0][1][0] == "Weg Zeile 2: b"
    dialog.files.setCurrentRow(1)
    dialog.show_changes()
    assert shown[1][1][0].startswith("Keine Anzeige möglich")


def test_comments_include_reviews(qtbot):
    fake = ReviewFake()
    dialog = pull_request_dialogs.PullCommentsDialog(fake, REF, fake.pulls[0])
    qtbot.addWidget(dialog)
    idle(qtbot, dialog)
    assert [dialog.comments.item(i).text() for i in range(dialog.comments.count())] == [
        "anna, 24.09.2026: Sieht gut aus", "ben hat genehmigt, 24.09.2026: Passt"]
