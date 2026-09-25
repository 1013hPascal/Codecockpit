"""Phase 5e: Links, Repository verwalten mit Mitarbeitern, Aus der Liste entfernen.

Die Plattform ist eine Attrappe (RepoFake) oder der GitHub-Adapter gegen einen nachgebauten Server.
Kein echtes Netz, alle Tokens sind erfunden.
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from cockpit.core import git, repo_admin
from cockpit.core.git import RemoteAddress
from cockpit.core.secret import Secret
from cockpit.platforms.base import (Capability, Collaborator, PermissionMissing, RepoInfo,
                                    RepoRef, SupportsCollaborators)
from cockpit.platforms.github import GitHubPlatform
from cockpit.ui import repo_dialogs
from tests.conftest import FakePlatform, said
from tests.test_github import TOKEN, platform as github_platform, server  # noqa: F401
from tests.test_phase5a import account, live, sh, wait_idle  # noqa: F401
from tests.test_phase5b import write
from tests.test_phase5c import labels, setup_repo

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

ADDRESS = RemoteAddress("github.com", "tester", "Tagebuch")


class RepoFake(FakePlatform, SupportsCollaborators):
    """Plattform-Attrappe, die sich jeden Aufruf merkt."""
    delete_login_scopes = "repo delete_repo"
    can_delete = True                     # False: dem Zugang fehlt das Recht zum Löschen

    def __init__(self, url: str = "https://github.com", token=None) -> None:
        super().__init__()
        self.url = url
        self.token = token
        self.username = "tester"
        self.calls: list[tuple] = []
        self.people = [Collaborator("erika", "write"), Collaborator("max", "read", 7)]

    @classmethod
    def browser_login_available(cls, url: str = "") -> bool:
        return True

    def permissions(self):
        from cockpit.core.availability import Availability
        result = super().permissions()
        if not self.can_delete:
            result[Capability.DELETE_REPO] = Availability.no("Recht fehlt.")
        return result

    def set_visibility(self, repo, private):
        self.calls.append(("visibility", repo.name, private))

    def archive(self, repo):
        self.calls.append(("archive", repo.name))

    def unarchive(self, repo):
        self.calls.append(("unarchive", repo.name))

    def delete(self, repo):
        if self.token is None and not self.can_delete:
            raise PermissionMissing(Capability.DELETE_REPO, "Dem Token fehlt ein Recht.")
        self.calls.append(("delete", repo.name, self.token.reveal() if self.token else ""))
        DELETED.append(repo.name)

    def settings_url(self, repo):
        return f"https://x/{repo.name}/settings"

    def collaborators(self, repo):
        return list(self.people)

    def invite(self, repo, login, permission):
        self.calls.append(("invite", login, permission))
        self.people.append(Collaborator(login, permission, 9))
        return True

    def remove_collaborator(self, repo, login):
        self.calls.append(("remove", login))
        self.people = [p for p in self.people if p.login != login]

    def cancel_invitation(self, repo, invitation_id):
        self.calls.append(("cancel", invitation_id))
        self.people = [p for p in self.people if p.invitation_id != invitation_id]


DELETED: list[str] = []


def info(private: bool = True, archived: bool = False) -> RepoInfo:
    return RepoInfo(RepoRef("tester", "Tagebuch"), private, archived, "main",
                    "https://github.com/tester/Tagebuch")


def connected_project(services, code: Path, account_id: int | None = None):
    """Projekt, das laut Git und Liste zu github.com/tester/Tagebuch gehört."""
    sh(code, "remote", "set-url", "origin", "https://github.com/tester/Tagebuch.git")
    project =services.projects.find_by_dir(code.parent) or services.projects.add(code.parent)
    services.projects.set_remote(project, ADDRESS, None)
    if account_id is not None:
        services.projects.set_account(project, account_id)
    return services.projects.get(project.id)


def manage_dialog(qtbot, services, project, fake, **kwargs):
    dialog = repo_dialogs.ManageRepoDialog(services, project, fake, info(**kwargs))
    qtbot.addWidget(dialog)
    return dialog


def idle(qtbot, dialog):
    qtbot.waitUntil(lambda: not dialog.worker.busy, timeout=10000)


@pytest.fixture
def answers(monkeypatch):
    """Rückfragen mitschreiben. answers.yes steuert die Antwort, answers.choice die Knöpfe."""
    class Answers:
        yes = True
        choice = 0
        questions: list = []
        errors: list = []
    record = Answers()
    record.questions, record.errors = [], []

    def confirm(parent, title, text, **k):
        record.questions.append((title, text, k))
        return record.yes

    def ask_buttons(parent, title, text, buttons, default, escape):
        record.questions.append((title, text, {"buttons": buttons, "default": default}))
        return record.choice(buttons) if callable(record.choice) else record.choice

    monkeypatch.setattr(repo_dialogs, "confirm", confirm)
    monkeypatch.setattr(repo_dialogs, "ask_buttons", ask_buttons)
    monkeypatch.setattr(repo_dialogs, "show_error", lambda *a: record.errors.append(a[2]))
    return record


# -- Kern ---------------------------------------------------------------------------------------
def test_links_come_from_the_account_without_secrets(account, tmp_path, projects_root):
    services, acc, _ = account
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code, acc.id)
    assert repo_admin.links(services, project) == [
        ("Projektseite", "https://x/Tagebuch"), ("README", "https://x/Tagebuch#readme")]


def test_links_need_an_account(make_services, tmp_path, projects_root):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    with pytest.raises(Exception, match="kein Konto"):
        repo_admin.links(services, project)


def test_github_links_and_settings_page():
    platform = GitHubPlatform("https://github.com", Secret(""))
    links = platform.links(RepoRef("o", "r"))
    assert links.project_page == "https://github.com/o/r"
    assert links.readme == "https://github.com/o/r#readme"
    assert platform.settings_url(RepoRef("o", "r")) == "https://github.com/o/r/settings"


def test_public_scan_sees_the_whole_history(tmp_path, projects_root):
    _, code, _ = setup_repo(tmp_path, projects_root)
    assert repo_admin.public_scan(code).blocking == []
    fake = "ghp" + "_" + "Erfunden" + "0123456789" * 3
    write(code, "config.py", f'TOKEN = "{fake}"\n')
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Mit Token")
    write(code, "config.py", "TOKEN = ''\n")
    sh(code, "commit", "-q", "-am", "Token raus")
    report = repo_admin.public_scan(code)
    assert [f.kind.value for f in report.blocking] == ["secret_history"]
    assert any(f.kind.value == "private_email" for f in report.findings)   # t@example.org


def test_disconnect_removes_only_the_connection(tmp_path, projects_root):
    _, code, _ = setup_repo(tmp_path, projects_root)
    before = sh(code, "rev-parse", "HEAD")
    repo_admin.disconnect(code)
    assert git.config_get(code, "remote.origin.url") == ""
    assert sh(code, "rev-parse", "HEAD") == before and (code / "main.py").exists()
    repo_admin.disconnect(code)                                     # zweimal schadet nicht


def test_removed_project_stays_removed_until_added_again(make_services, projects_root):
    from tests.conftest import make_project
    services = make_services()
    make_project(projects_root, "Tagebuch")
    services.projects.scan(projects_root)
    project = services.projects.all()[0]
    services.projects.remove(project.id)
    assert services.projects.scan(projects_root) == []
    assert services.projects.all() == []
    services.projects.add(projects_root / "Tagebuch")               # selbst hinzugefügt
    assert services.projects.removed_dirs() == set()
    services.projects.remove(services.projects.all()[0].id)
    services.projects.add_linked(projects_root / "Tagebuch" / "Code")
    assert len(services.projects.all()) == 1


def test_hidden_remote_repos(account, tmp_path):
    from cockpit.platforms.base import RemoteRepo
    services, acc, _ = account
    services.remote_repos.replace(acc.id, [
        RemoteRepo(RepoRef("tester", "A"), True, "https://github.com/tester/A.git",
                   "https://github.com/tester/A"),
        RemoteRepo(RepoRef("tester", "B"), True, "https://github.com/tester/B.git",
                   "https://github.com/tester/B")])
    a = RemoteAddress("github.com", "tester", "A")
    services.remote_repos.hide(a)
    assert [r.name for r in services.remote_repos.only_remote(set())] == ["B"]
    assert len(services.remote_repos.all()) == 2                    # zum Herunterladen bleibt es
    services.remote_repos.unhide(a)
    assert len(services.remote_repos.only_remote(set())) == 2
    services.remote_repos.set_private(a, False)
    assert not services.remote_repos.find(a).private
    services.remote_repos.forget(a)
    assert [r.name for r in services.remote_repos.all()] == ["B"]


def test_download_shows_a_hidden_repo_again(account, tmp_path, projects_root):
    from cockpit.core import project_setup
    from tests.test_phase5a import make_remote, stored_repo
    services, acc, _ = account
    bare = make_remote(tmp_path, "Rechner")
    repo = stored_repo(services, acc.id, bare, "Rechner")
    services.remote_repos.hide(repo.address)
    project_setup.download(services, repo, projects_root)
    assert services.remote_repos.hidden() == set()


# -- GitHub-Adapter -----------------------------------------------------------------------------
def test_github_collaborators_and_invitations(server):
    server.route("GET", "/repos/o/r/collaborators", body=[
        {"login": "zora", "role_name": "admin"},
        {"login": "anna", "permissions": {"pull": True, "push": True}}])
    server.route("GET", "/repos/o/r/invitations", body=[
        {"id": 42, "invitee": {"login": "max"}, "permissions": "read"}])
    people = github_platform().collaborators(RepoRef("o", "r"))
    assert [repo_dialogs.collaborator_line(p) for p in people] == [
        "anna, schreiben", "max, eingeladen, lesen", "zora, verwalten"]
    assert people[1].invitation_id == 42
    assert server.requests[0].url.params["affiliation"] == "direct"


def test_github_invite_remove_cancel_and_unarchive(server):
    ref = RepoRef("o", "r")
    platform = github_platform()
    server.route("PUT", "/repos/o/r/collaborators/erika", 201, {"id": 1})
    assert platform.invite(ref, "erika", "write") is True
    assert json.loads(server.requests[-1].content) == {"permission": "push"}
    server.route("PUT", "/repos/o/r/collaborators/erika", 204)
    assert platform.invite(ref, "erika", "read") is False
    assert json.loads(server.requests[-1].content) == {"permission": "pull"}
    with pytest.raises(Exception, match="Den Benutzer niemand gibt es auf GitHub nicht"):
        platform.invite(ref, "niemand", "write")
    server.route("DELETE", "/repos/o/r/collaborators/erika", 204)
    platform.remove_collaborator(ref, "erika")
    server.route("DELETE", "/repos/o/r/invitations/42", 204)
    platform.cancel_invitation(ref, 42)
    server.route("PATCH", "/repos/o/r", 200, {})
    platform.unarchive(ref)
    assert json.loads(server.requests[-1].content) == {"archived": False}


def test_github_invite_rejected_explains(server):
    server.route("PUT", "/repos/o/r/collaborators/o", 422,
                 {"message": "Repository owner cannot be a collaborator"})
    with pytest.raises(Exception, match="GitHub hat die Einladung abgelehnt"):
        github_platform().invite(RepoRef("o", "r"), "o", "write")


def test_second_login_asks_only_for_delete_rights(server):
    server.route("POST", "/login/device/code", body={
        "device_code": "d", "user_code": "ABCD-1234", "verification_uri": "https://github.com/login/device",
        "interval": 5, "expires_in": 900})
    GitHubPlatform.start_browser_login("", GitHubPlatform.delete_login_scopes)
    body = server.requests[-1].content.decode()
    assert "scope=repo+delete_repo" in body
    GitHubPlatform.start_browser_login()
    assert "delete_repo" not in server.requests[-1].content.decode()


def test_github_permissions_without_delete_repo(server):
    platform = github_platform()
    platform.current_user()                            # Scopes: repo, read:org, workflow
    assert not platform.permissions()[Capability.DELETE_REPO].available
    assert platform.permissions()[Capability.COLLABORATORS].available


# -- Aktionen ---------------------------------------------------------------------------------
def test_project_actions(live, qtbot, account, tmp_path, projects_root):
    from cockpit.core.actions import Target
    services, acc, _ = account
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code, acc.id)
    win = live(services)
    win.project_list.select(Target.PROJECT, project.id)
    texts = labels(win)
    assert texts.index("Links …") < texts.index("Repository verwalten …")
    assert texts[-1] == "Aus der Liste entfernen …"
    services.projects.set_remote(project, None, None)
    win.refresh_actions()
    texts = labels(win)
    assert "Links …" not in texts and "Aus der Liste entfernen …" in texts


def test_remove_from_list(live, qtbot, account, tmp_path, projects_root, monkeypatch):
    from cockpit.core.actions import Target
    from cockpit.ui import project_actions
    services, acc, _ = account
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code, acc.id)
    win = live(services)
    questions = []
    monkeypatch.setattr(project_actions, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or len(questions) > 1)
    win.project_list.select(Target.PROJECT, project.id)
    entry = next(e for e in win.current_entries() if e.action.id == "remove_project")
    win.run_entry(entry)                                           # Escape
    assert services.projects.get(project.id) is not None
    text, buttons = questions[0]
    assert text.startswith("Tagebuch wird nur aus der Liste des Cockpits entfernt.")
    assert buttons == {"yes": "Entfernen", "no": "Abbrechen"}
    win.run_entry(entry)
    assert services.projects.all() == []
    assert said("Tagebuch aus der Liste entfernt.")
    win.reload_projects(refresh=False)                             # Strg+R findet es nicht wieder
    assert services.projects.all() == []
    assert ADDRESS.key in services.remote_repos.hidden()
    assert code.exists()


def test_hide_remote_repo(live, qtbot, account, tmp_path, projects_root, monkeypatch):
    from cockpit.core.actions import Target
    from cockpit.platforms.base import RemoteRepo
    from cockpit.ui import project_actions
    services, acc, _ = account
    services.remote_repos.replace(acc.id, [RemoteRepo(
        RepoRef("tester", "Wetter"), True, "https://github.com/tester/Wetter.git",
        "https://github.com/tester/Wetter")])
    win = live(services)
    repo = services.remote_repos.all()[0]
    win.project_list.select(Target.REMOTE_REPO, repo.id)
    assert "Aus der Liste entfernen …" in labels(win)
    monkeypatch.setattr(project_actions, "confirm", lambda *a, **k: True)
    entry = next(e for e in win.current_entries() if e.action.id == "hide_remote")
    win.run_entry(entry)
    assert said("Wetter aus der Liste entfernt.")
    assert repo.id not in win.project_list.remote_ids()


def test_manage_opens_with_repo_info(live, qtbot, account, tmp_path, projects_root, monkeypatch):
    from cockpit.core.actions import Target
    services, acc, _ = account
    fake = RepoFake()
    fake.repos[RepoRef("tester", "Tagebuch")] = info()
    services.platforms[acc.id] = fake
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code, acc.id)
    win = live(services)
    shown = []

    class FakeManage:
        def __init__(self, services, project, platform, repo_info, platform_name, parent=None):
            shown.append((platform, repo_info.private, platform_name))
            self.deleted = self.removed = False
            self.changed = True

        def exec(self):
            return 0

    monkeypatch.setattr(repo_dialogs, "ManageRepoDialog", FakeManage)
    win.project_list.select(Target.PROJECT, project.id)
    entry = next(e for e in win.current_entries() if e.action.id == "manage_repo")
    win.run_entry(entry)
    qtbot.waitUntil(lambda: bool(shown), timeout=10000)
    assert shown[0][0] is fake and shown[0][1] is True
    wait_idle(qtbot, win)


# -- Fenster ------------------------------------------------------------------------------
def test_links_dialog(qtbot, monkeypatch):
    from PySide6.QtGui import QGuiApplication
    opened = []
    monkeypatch.setattr(repo_dialogs.browser_login_dialog, "open_url", opened.append)
    dialog = repo_dialogs.LinksDialog("Tagebuch", [("Projektseite", "https://x/T"),
                                                   ("README", "https://x/T#readme")])
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Links von Tagebuch"
    assert dialog.list.item(0).text() == "Projektseite: https://x/T"
    dialog.copy_current()
    assert QGuiApplication.clipboard().text() == "https://x/T"
    assert said("Link zu Projektseite kopiert.")
    dialog.list.setCurrentRow(1)
    dialog.open_current()
    assert opened == ["https://x/T#readme"]


def test_manage_dialog_lines(qtbot, make_services, tmp_path, projects_root):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    dialog = manage_dialog(qtbot, services, project, RepoFake(), archived=True)
    lines = [dialog.list.item(i).text() for i in range(dialog.list.count())]
    assert lines == ["tester/Tagebuch auf GitHub",
                     "Privat, nur Sie und Ihre Mitarbeiter sehen den Code",
                     "Archiviert, schreibgeschützt",
                     "Adresse: https://github.com/tester/Tagebuch"]
    assert dialog.visibility_button.text() == "Ö&ffentlich machen …"
    assert dialog.archive_button.text() == "Archivierung &aufheben …"


def test_make_public_after_a_clean_check(qtbot, account, tmp_path, projects_root, answers):
    from cockpit.platforms.base import RemoteRepo
    services, acc, _ = account
    services.remote_repos.replace(acc.id, [RemoteRepo(
        RepoRef("tester", "Tagebuch"), True, "https://github.com/tester/Tagebuch.git",
        "https://github.com/tester/Tagebuch")])
    _, code, _ = setup_repo(tmp_path, projects_root)
    sh(code, "-c", "user.email=1+t@users.noreply.github.com", "commit", "-q", "--allow-empty",
       "--amend", "--reset-author", "-m", "Erste Version")
    project = connected_project(services, code, acc.id)
    fake = RepoFake()
    dialog = manage_dialog(qtbot, services, project, fake)
    dialog.change_visibility()
    idle(qtbot, dialog)
    title, text, buttons = answers.questions[-1]
    assert text.endswith("Tagebuch wird öffentlich. Jeder im Internet kann danach den Code und "
                         "den ganzen Verlauf sehen. Öffentlich machen?")
    assert buttons == {"yes": "Öffentlich machen", "no": "Abbrechen"}
    idle(qtbot, dialog)
    assert fake.calls == [("visibility", "Tagebuch", False)]
    assert not services.remote_repos.find(ADDRESS).private
    assert dialog.changed and dialog.visibility_button.text() == "&Privat machen …"
    assert said("Tagebuch ist jetzt öffentlich.")


def test_make_public_is_refused_with_a_secret(qtbot, make_services, tmp_path, projects_root,
                                              answers):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    fake_token = "ghp" + "_" + "Erfunden" + "0123456789" * 3
    write(code, "config.py", f'TOKEN = "{fake_token}"\n')
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Token")
    project = connected_project(services, code)
    fake = RepoFake()
    dialog = manage_dialog(qtbot, services, project, fake)
    dialog.change_visibility()
    idle(qtbot, dialog)
    assert "macht das Cockpit Tagebuch nicht öffentlich" in answers.errors[0]
    assert fake_token not in answers.errors[0]
    assert fake.calls == [] and answers.questions == []


def test_make_private_and_archive(qtbot, make_services, tmp_path, projects_root, answers):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    fake = RepoFake()
    dialog = manage_dialog(qtbot, services, project, fake, private=False)
    answers.yes = False
    dialog.change_visibility()
    dialog.change_archive()
    assert fake.calls == []                                       # Escape: nichts passiert
    assert answers.questions[0][2] == {"yes": "Privat machen", "no": "Abbrechen"}
    assert "lässt sich jederzeit wieder aufheben" in answers.questions[1][1]
    answers.yes = True
    dialog.change_visibility()
    idle(qtbot, dialog)
    dialog.change_archive()
    idle(qtbot, dialog)
    dialog.change_archive()
    idle(qtbot, dialog)
    assert fake.calls == [("visibility", "Tagebuch", True), ("archive", "Tagebuch"),
                          ("unarchive", "Tagebuch")]
    assert said("Archivierung von Tagebuch aufgehoben.")


def test_delete_offers_archive_and_needs_the_name(qtbot, make_services, tmp_path, projects_root,
                                                  answers, monkeypatch):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    fake = RepoFake()
    dialog = manage_dialog(qtbot, services, project, fake)
    answers.choice = 2                                            # Abbrechen
    dialog.delete()
    title, text, extra = answers.questions[0]
    assert text.startswith("Löschen lässt sich nicht rückgängig machen.")
    assert "Der Ordner auf Ihrem Rechner bleibt immer erhalten." in text
    assert extra == {"buttons": ["Weiter zum Löschen …", "Stattdessen archivieren …",
                                 "Abbrechen"], "default": 2}
    answers.choice = 1                                            # stattdessen archivieren
    dialog.delete()
    idle(qtbot, dialog)
    assert fake.calls == [("archive", "Tagebuch")]

    class WrongName:
        def __init__(self, name, parent=None):
            pass

        def exec(self):
            return 0                                             # Name falsch oder Escape

    monkeypatch.setattr(repo_dialogs, "TypeNameDialog", WrongName)
    answers.choice = 0
    dialog.delete()
    assert fake.calls == [("archive", "Tagebuch")]


def test_delete_and_keep_local(qtbot, make_services, tmp_path, projects_root, answers,
                               monkeypatch):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    fake = RepoFake()
    dialog = manage_dialog(qtbot, services, project, fake)
    monkeypatch.setattr(repo_dialogs.TypeNameDialog, "exec", lambda self: 1)
    answers.choice = lambda buttons: 0          # Weiter zum Löschen, danach Nur lokal behalten
    dialog.delete()
    idle(qtbot, dialog)
    assert fake.calls == [("delete", "Tagebuch", "")]
    assert dialog.deleted and not dialog.removed and dialog.result() == 1
    last = answers.questions[-1]
    assert last[2]["buttons"] == ["Nur lokal behalten", "Aus der Liste entfernen"]
    assert last[2]["default"] == 0
    assert git.config_get(code, "remote.origin.url") == ""
    assert services.projects.get(project.id).remote is None
    assert (code / "main.py").exists()


def test_delete_and_remove_from_list(qtbot, make_services, tmp_path, projects_root, answers,
                                     monkeypatch):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    fake = RepoFake()
    dialog = manage_dialog(qtbot, services, project, fake)
    monkeypatch.setattr(repo_dialogs.TypeNameDialog, "exec", lambda self: 1)
    answers.choice = lambda buttons: 1 if buttons[0] == "Nur lokal behalten" else 0
    dialog.delete()
    idle(qtbot, dialog)
    assert dialog.removed and services.projects.get(project.id) is None
    assert code.exists()


def test_delete_with_a_second_login(qtbot, make_services, tmp_path, projects_root, answers,
                                    monkeypatch):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    monkeypatch.setattr(RepoFake, "can_delete", False)
    fake = RepoFake()
    dialog = manage_dialog(qtbot, services, project, fake)
    monkeypatch.setattr(repo_dialogs.TypeNameDialog, "exec", lambda self: 1)
    logins = []

    class FakeLogin:
        def __init__(self, cls, url, parent=None, scopes="", title="", confirm_line=""):
            logins.append((cls, scopes, title))
            self.token = Secret("gho_ErfundenNurZumLoeschen123")
            self.username = "Tester"

        def exec(self):
            return 1

    monkeypatch.setattr(repo_dialogs.browser_login_dialog, "BrowserLoginDialog", FakeLogin)
    answers.choice = lambda buttons: 0
    dialog.delete()
    idle(qtbot, dialog)
    assert logins == [(RepoFake, "repo delete_repo", "Recht zum Löschen holen")]
    question = next(q for q in answers.questions if q[0] == "Löschen" and "zusätzliches" in q[1])
    assert "nicht gespeichert" in question[1]
    assert question[2] == {"yes": "Im Browser bestätigen …", "no": "Abbrechen"}
    assert fake.calls == []                                        # nicht mit dem alten Zugang
    assert DELETED[-1] == "Tagebuch" and dialog.deleted


def test_second_login_with_another_account_deletes_nothing(qtbot, make_services, tmp_path,
                                                           projects_root, answers, monkeypatch):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    monkeypatch.setattr(RepoFake, "can_delete", False)
    fake = RepoFake()
    dialog = manage_dialog(qtbot, services, project, fake)
    monkeypatch.setattr(repo_dialogs.TypeNameDialog, "exec", lambda self: 1)

    class OtherLogin:
        def __init__(self, *a, **k):
            self.token = Secret("gho_ErfundenNurZumLoeschen123")
            self.username = "jemand-anders"

        def exec(self):
            return 1

    monkeypatch.setattr(repo_dialogs.browser_login_dialog, "BrowserLoginDialog", OtherLogin)
    answers.choice = lambda buttons: 0
    before = len(DELETED)
    dialog.delete()
    assert "Sie haben sich als jemand-anders angemeldet" in answers.errors[-1]
    assert len(DELETED) == before and not dialog.deleted


def test_delete_without_browser_login_explains(qtbot, make_services, tmp_path, projects_root,
                                               answers, monkeypatch):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    monkeypatch.setattr(RepoFake, "can_delete", False)
    monkeypatch.setattr(RepoFake, "delete_login_scopes", "")
    opened = []
    monkeypatch.setattr(repo_dialogs.browser_login_dialog, "open_url", opened.append)
    fake = RepoFake()
    dialog = manage_dialog(qtbot, services, project, fake)
    monkeypatch.setattr(repo_dialogs.TypeNameDialog, "exec", lambda self: 1)
    answers.choice = lambda buttons: 0
    dialog.delete()
    assert "fehlt das Recht zum Löschen (delete_repo)" in answers.errors[-1]
    assert opened == ["https://x/Tagebuch/settings"]
    assert not dialog.deleted


def test_type_name_dialog(qtbot, monkeypatch):
    errors = []
    monkeypatch.setattr(repo_dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog = repo_dialogs.TypeNameDialog("codecockpit-test")
    qtbot.addWidget(dialog)
    assert dialog.edit.accessibleName() == ("Zur Bestätigung den Namen eintippen: "
                                            "codecockpit-test")
    dialog.edit.setText("codecockpit")
    dialog.check()
    assert errors == [repo_dialogs.NAME_MISMATCH] and dialog.result() == 0
    dialog.edit.setText("codecockpit-test")
    dialog.check()
    assert dialog.result() == 1


def test_collaborators_dialog(qtbot, answers, monkeypatch):
    fake = RepoFake()
    dialog = repo_dialogs.CollaboratorsDialog(fake, RepoRef("tester", "Tagebuch"))
    qtbot.addWidget(dialog)
    idle(qtbot, dialog)
    assert dialog.windowTitle() == "Mitarbeiter von Tagebuch: 2 Einträge"
    assert [dialog.list.item(i).text() for i in range(2)] == ["erika, schreiben",
                                                              "max, eingeladen, lesen"]

    class FakeInvite:
        def __init__(self, platform_name, parent=None):
            self.login, self.permission = "neu", "admin"

        def exec(self):
            return 1

    monkeypatch.setattr(repo_dialogs, "InviteDialog", FakeInvite)
    dialog.invite()
    idle(qtbot, dialog)
    qtbot.waitUntil(lambda: said("Einladung an neu verschickt."), timeout=5000)
    assert ("invite", "neu", "admin") in fake.calls
    dialog.list.setCurrentRow(1)                                   # max, eingeladen
    dialog.remove_current()
    assert answers.questions[-1][2] == {"yes": "Zurückziehen", "no": "Abbrechen"}
    idle(qtbot, dialog)
    qtbot.waitUntil(lambda: said("Einladung an max zurückgezogen."), timeout=5000)
    dialog.list.setCurrentRow(0)                                   # erika
    dialog.remove_current()
    assert "wird als Mitarbeiter entfernt" in answers.questions[-1][1]
    idle(qtbot, dialog)
    qtbot.waitUntil(lambda: said("erika entfernt."), timeout=5000)
    assert fake.calls[-2:] == [("cancel", 7), ("remove", "erika")]


def test_invite_dialog(qtbot, monkeypatch):
    errors = []
    monkeypatch.setattr(repo_dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog = repo_dialogs.InviteDialog()
    qtbot.addWidget(dialog)
    assert dialog.rights.currentText() == "schreiben"              # Vorgabe
    assert [dialog.rights.itemText(i) for i in range(3)] == ["lesen", "schreiben", "verwalten"]
    dialog.check()
    assert errors and dialog.result() == 0
    dialog.edit.setText("@erika")
    dialog.rights.setCurrentIndex(0)
    dialog.check()
    assert (dialog.login, dialog.permission) == ("erika", "read") and dialog.result() == 1


def test_collaborators_need_the_capability(qtbot, make_services, tmp_path, projects_root,
                                           answers):
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    dialog = manage_dialog(qtbot, services, project, FakePlatform())
    dialog.show_collaborators()
    assert answers.errors == ["GitHub kennt keine Mitarbeiter."]
