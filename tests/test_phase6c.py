"""Phase 6c: Schutzregeln, Hochladen in einen Branch bei geschütztem main, Feature für den Ablauf.

Die "Plattform" ist ein nacktes Repository. Ein Hook darin lehnt das Hochladen in main ab, wie
GitHub bei einem geschützten Branch. Kein echtes Netz, alle Tokens sind erfunden.
"""
from __future__ import annotations

import json

import pytest

from cockpit.core import branches, git, sync
from cockpit.core.features.registry import FeatureRegistry
from cockpit.features.branches_prs.manifest import FEATURE_ID, MANIFEST
from cockpit.platforms.base import BranchProtection, RepoRef, SupportsBranchProtection
from cockpit.ui import repo_dialogs, sync_dialogs, sync_flow
from tests.conftest import FakePlatform, said
from tests.test_github import platform as github_platform, server  # noqa: F401
from tests.test_phase5a import account, live, sh, wait_idle  # noqa: F401
from tests.test_phase5b import write
from tests.test_phase5c import head, labels, run_push, select_code, setup_repo
from tests.test_phase5e import info, manage_dialog

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

HOOK = "#!/bin/sh\nwhile read old new ref; do\n  if [ \"$ref\" = \"refs/heads/main\" ]; then\n" \
       "    echo \"error: GH006: Protected branch update failed for refs/heads/main.\" >&2\n" \
       "    exit 1\n  fi\ndone\nexit 0\n"


def protect(bare) -> None:
    """main auf der "Plattform" schützen wie GitHub."""
    hook = bare / "hooks" / "pre-receive"
    hook.write_bytes(HOOK.encode("ascii"))


def local_commit(code, name="neu.py", message="Suche ergänzt") -> None:
    write(code, name, "x\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", message)


# -- GitHub-Adapter -----------------------------------------------------------------------------
def test_github_reads_protection(server):
    server.route("GET", "/repos/o/r/branches/main/protection", body={
        "required_pull_request_reviews": {"required_approving_review_count": 2,
                                          "dismiss_stale_reviews": True},
        "enforce_admins": {"enabled": True}, "allow_deletions": {"enabled": False}})
    assert github_platform().branch_protection(RepoRef("o", "r"), "main") == BranchProtection(
        True, 2, True, True, True)
    server.route("GET", "/repos/o/r/branches/main/protection", 404,
                 {"message": "Branch not protected"})
    assert github_platform().branch_protection(RepoRef("o", "r"), "main") is None


def test_github_writes_and_removes_protection(server):
    ref = RepoRef("o", "r")
    server.route("PUT", "/repos/o/r/branches/main/protection", 200, {})
    github_platform().set_branch_protection(ref, "main", BranchProtection(True, 1, False, False,
                                                                          True))
    assert json.loads(server.requests[-1].content) == {
        "required_status_checks": None, "enforce_admins": False,
        "required_pull_request_reviews": {"required_approving_review_count": 1,
                                          "dismiss_stale_reviews": False},
        "restrictions": None, "allow_force_pushes": False, "allow_deletions": False}
    server.route("DELETE", "/repos/o/r/branches/main/protection", 204)
    github_platform().set_branch_protection(ref, "main", BranchProtection(prevent_deletion=False))
    assert server.requests[-1].method == "DELETE"


def test_github_explains_protection_on_free_private_repos(server):
    server.route("GET", "/repos/o/r/branches/main/protection", 403, {
        "message": "Upgrade to GitHub Pro or make this repository public to enable this "
                   "feature."})
    with pytest.raises(Exception, match="nur mit GitHub Pro"):
        github_platform().branch_protection(RepoRef("o", "r"), "main")


# -- Kern -----------------------------------------------------------------------------------------
def test_protection_summary():
    text = repo_dialogs.protection_summary
    assert text("main", BranchProtection(True, 1, True, True, True)) == (
        "Änderungen kommen nur über einen Pull Request mit mindestens 1 Genehmigung in main. "
        "Genehmigungen verfallen, wenn neue Commits dazukommen. Das gilt auch für "
        "Administratoren, also auch für Sie. main darf nicht gelöscht werden. Force push bleibt "
        "immer verboten.")
    assert text("main", BranchProtection(prevent_deletion=False)).startswith(
        "main wird nicht mehr geschützt.")


def test_move_commits_to_new_branch(tmp_path, projects_root):
    bare, code, _ = setup_repo(tmp_path, projects_root)
    uploaded = head(code)
    local_commit(code)
    mine = head(code)
    write(code, "offen.py", "noch ohne Commit\n")
    old = branches.move_commits_to_new_branch(code, "suche-ergaenzt")
    assert old == "main"
    assert git.status(code).branch == "suche-ergaenzt" and head(code) == mine
    assert head(code, "main") == uploaded                          # main wie auf der Plattform
    assert (code / "neu.py").exists() and (code / "offen.py").exists()   # Dateien bleiben
    kept = sh(code, "for-each-ref", "--format=%(objectname)", branches.MOVED_REF).split()
    assert kept == [mine]


def test_push_to_protected_main_is_recognized(make_services, tmp_path, projects_root):
    services = make_services()
    bare, code, _ = setup_repo(tmp_path, projects_root)
    protect(bare)
    write(code, "neu.py", "x\n")
    summary, data, _ = run_push(services, code, "Suche ergänzt")
    assert not summary.completed and data["protected"] == "main"
    assert "geschützt" in summary.text()


def test_feature_manifest_and_default_setting(make_services):
    assert MANIFEST.problems() == []
    services = make_services(manifests=[MANIFEST])
    assert FEATURE_ID not in services.features.default_features()
    services.settings.update(branches_by_default=True)
    assert FEATURE_ID in services.features.default_features()


# -- Oberfläche: Ablauf beim Hochladen ----------------------------------------------------------
@pytest.fixture
def pr_project(account, tmp_path, projects_root):
    """Projekt mit Konto, Feature eingeschaltet, Plattform ist ein nacktes Repository."""
    services, acc, _ = account
    services.registry = FeatureRegistry([MANIFEST])
    services.features.registry = services.registry
    bare, code, _ = setup_repo(tmp_path, projects_root)
    project = services.projects.add(code.parent)
    services.projects.set_account(project, acc.id)
    project = services.projects.get(project.id)
    services.features.enable(FEATURE_ID, project)
    sh(code, "add", "cockpit.toml")
    sh(code, "commit", "-q", "-m", "Feature an")
    sh(code, "push", "-q")
    return services, bare, code, project


def test_upload_asks_for_a_branch_and_offers_a_pull_request(live, qtbot, pr_project,
                                                            monkeypatch):
    from cockpit.ui import branch_dialogs
    services, bare, code, project = pr_project
    write(code, "neu.py", "x\n")
    win = live(services)
    select_code(win, services, code)
    lists, questions = [], []

    class Message:
        def __init__(self, title, changes, parent=None):
            self.message = "Suche in PDFs"

        def exec(self):
            return 1

    class Name:
        def __init__(self, title, hint, code_dir, current="", parent=None):
            lists.append(("name", current, hint))
            self.name = current

        def exec(self):
            return 1

    def choose(parent, title, name, items, current=0):
        lists.append((title, items))
        return 0

    monkeypatch.setattr(sync_dialogs, "CommitDialog", Message)
    monkeypatch.setattr(branch_dialogs, "BranchNameDialog", Name)
    monkeypatch.setattr(sync_flow, "choose_from_list", choose)
    monkeypatch.setattr(sync_flow, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or False)
    entry = next(e for e in win.current_entries() if e.action.id == "push_changes")
    win.run_entry(entry)
    qtbot.waitUntil(lambda: bool(questions), timeout=20000)
    title, items = lists[0]
    assert title == "In welchen Branch hochladen?"
    assert items == ["Neuer Branch: suche-in-pdfs …", "Direkt in main"]
    assert lists[1][1] == "suche-in-pdfs" and "main bleibt, wie es ist" in lists[1][2]
    assert "suche-in-pdfs" in sh(bare, "branch", "--list")
    assert "Suche in PDFs" not in sh(bare, "log", "--format=%s", "main")
    text, buttons = questions[0]
    assert text.startswith("suche-in-pdfs ist hochgeladen. Jetzt einen Pull Request erstellen")
    assert buttons == {"yes": "Pull Request erstellen …", "no": "Später"}
    wait_idle(qtbot, win)


def test_upload_directly_into_main(live, qtbot, pr_project, monkeypatch):
    services, bare, code, project = pr_project
    write(code, "neu.py", "x\n")
    win = live(services)
    select_code(win, services, code)

    class Message:
        def __init__(self, title, changes, parent=None):
            self.message = "Direkt"

        def exec(self):
            return 1

    monkeypatch.setattr(sync_dialogs, "CommitDialog", Message)
    monkeypatch.setattr(sync_flow, "choose_from_list", lambda p, t, n, items, current=0:
                        len(items) - 1)
    monkeypatch.setattr(sync_flow, "confirm", lambda *a, **k: pytest.fail("keine Frage"))
    entry = next(e for e in win.current_entries() if e.action.id == "push_changes")
    win.run_entry(entry)
    qtbot.waitUntil(lambda: said("Fertig. Commit „Direkt“. Branch main ist hochgeladen."),
                    timeout=20000)
    wait_idle(qtbot, win)


def test_protected_main_offers_a_new_branch(live, qtbot, account, tmp_path, projects_root,
                                            monkeypatch):
    from cockpit.ui import branch_dialogs, pull_request_flow
    services, acc, _ = account
    bare, code, _ = setup_repo(tmp_path, projects_root)
    protect(bare)
    write(code, "neu.py", "x\n")
    win = live(services)
    select_code(win, services, code)
    asked, created = [], []

    class Message:
        def __init__(self, title, changes, parent=None):
            self.message = "Suche in PDFs"

        def exec(self):
            return 1

    class Name:
        def __init__(self, title, hint, code_dir, current="", parent=None):
            self.name = current

        def exec(self):
            return 1

    def ask_buttons(parent, title, text, buttons, default, escape):
        asked.append((text, buttons, default))
        return 0

    monkeypatch.setattr(sync_dialogs, "CommitDialog", Message)
    monkeypatch.setattr(branch_dialogs, "BranchNameDialog", Name)
    monkeypatch.setattr(sync_flow, "ask_buttons", ask_buttons)
    monkeypatch.setattr(sync_flow, "show_error", lambda *a: pytest.fail(a[2]))
    monkeypatch.setattr(pull_request_flow.PullRequestRunner, "create",
                        lambda self, *a, **k: created.append(True))
    entry = next(e for e in win.current_entries() if e.action.id == "push_changes")
    win.run_entry(entry)
    qtbot.waitUntil(lambda: bool(created), timeout=30000)
    text, buttons, default = asked[0]
    assert text.startswith("GitHub lässt in main nichts direkt hochladen.")
    assert buttons == ["In neuen Branch hochladen …", "Später"] and default == 1
    assert "suche-in-pdfs" in sh(bare, "branch", "--list")
    assert git.status(code).branch == "suche-in-pdfs"
    assert head(code, "main") == head(code, "origin/main")
    wait_idle(qtbot, win)


def test_feature_toggle_actions(live, qtbot, account, tmp_path, projects_root, monkeypatch):
    from cockpit.ui import project_actions
    from tests.test_phase5e import connected_project
    services, acc, _ = account
    services.registry = FeatureRegistry([MANIFEST])
    services.features.registry = services.registry
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code, acc.id)
    win = live(services)
    select_code(win, services, code)
    assert "Hochladen über Pull Requests einschalten …" in labels(win)
    questions = []
    monkeypatch.setattr(project_actions, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or True)
    entry = next(e for e in win.current_entries() if e.action.id == "pull_feature_on")
    win.run_entry(entry)
    assert "cockpit.toml" in questions[0][0]
    assert questions[0][1] == {"yes": "Einschalten", "no": "Abbrechen"}
    assert said("Hochladen über Pull Requests eingeschaltet.")
    assert services.features.enabled_in_project(FEATURE_ID, project)
    win.refresh_actions()
    assert "Hochladen über Pull Requests ausschalten …" in labels(win)
    entry = next(e for e in win.current_entries() if e.action.id == "pull_feature_off")
    win.run_entry(entry)
    assert not services.features.enabled_in_project(FEATURE_ID, project)
    wait_idle(qtbot, win)


# -- Oberfläche: Schutzregeln -------------------------------------------------------------------
class ProtectFake(FakePlatform, SupportsBranchProtection):
    def __init__(self, rules=None) -> None:
        super().__init__()
        self.rules = rules
        self.saved: list = []

    def branch_protection(self, repo, branch):
        return self.rules

    def set_branch_protection(self, repo, branch, rules):
        self.saved.append((branch, rules))


def test_protection_dialog(qtbot):
    dialog = repo_dialogs.ProtectionDialog("main", None)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Schutzregeln für main: nicht geschützt"
    assert not dialog.pull_box.isChecked() and not dialog.delete_box.isChecked()
    assert dialog.approvals.accessibleName() == "Mindestens so viele Genehmigungen"
    dialog.pull_box.setChecked(True)
    dialog.approvals.setCurrentIndex(2)
    dialog.stale_box.setChecked(True)
    dialog.delete_box.setChecked(True)
    dialog.check()
    assert dialog.rules == BranchProtection(True, 2, True, False, True)
    shown = repo_dialogs.ProtectionDialog("main", BranchProtection(True, 1, False, True, True))
    qtbot.addWidget(shown)
    assert shown.windowTitle() == "Schutzregeln für main: geschützt"
    assert shown.admins_box.isChecked() and shown.approvals.currentText() == "1"


def test_protection_from_manage_dialog(qtbot, make_services, tmp_path, projects_root,
                                       monkeypatch):
    from tests.test_phase5e import connected_project
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    fake = ProtectFake()
    questions = []
    monkeypatch.setattr(repo_dialogs, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or True)

    class Rules:
        def __init__(self, branch, rules, parent=None):
            assert rules is None
            self.rules = BranchProtection(True, 1, False, False, True)

        def exec(self):
            return 1

    monkeypatch.setattr(repo_dialogs, "ProtectionDialog", Rules)
    dialog = manage_dialog(qtbot, services, project, fake)
    assert dialog.rules_button.text() == "&Schutzregeln für main …"
    dialog.show_protection()
    qtbot.waitUntil(lambda: said("Schutzregeln für main gespeichert."), timeout=5000)
    assert questions[0][0].startswith("Änderungen kommen nur über einen Pull Request mit "
                                      "mindestens 1 Genehmigung in main.")
    assert questions[0][1] == {"yes": "Speichern", "no": "Abbrechen"}
    assert fake.saved == [("main", BranchProtection(True, 1, False, False, True))]


def test_protection_needs_the_capability(qtbot, make_services, tmp_path, projects_root,
                                         monkeypatch):
    from tests.test_phase5e import connected_project
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    project = connected_project(services, code)
    errors = []
    monkeypatch.setattr(repo_dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog = manage_dialog(qtbot, services, project, FakePlatform())
    dialog.show_protection()
    assert errors == ["GitHub kennt keine Schutzregeln."]
    assert info().default_branch == "main"
