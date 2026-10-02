"""Phase 10f: Ein Ordner pro Branch (Worktrees von Git).

Die "Plattform" ist ein nacktes Repository auf der Festplatte, ein zweiter Klon spielt den anderen
Rechner. Kein echtes Netz.
"""
from __future__ import annotations

import dataclasses

import pytest

from cockpit.core import backups, git, project_status, sync, worktrees
from cockpit.core.actions import Target
from cockpit.core.errors import CockpitError
from cockpit.core.projects import classify_folder, main_code_dir
from tests.test_phase5a import account, sh  # noqa: F401
from tests.test_phase5f import branch_repo, commit

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


def structured(tmp_path, projects_root, make_services):
    """Tagebuch mit Branches (siehe branch_repo), schon auf Ordner pro Branch umgestellt."""
    bare, code, other = branch_repo(tmp_path, projects_root)
    services = make_services([])
    project = services.projects.add(code.parent)
    main = worktrees.convert(project)
    project = services.projects.set_code_dir(project, main)
    return services, project, other


# -- Einrichten -----------------------------------------------------------------------------------
def test_folder_names():
    assert worktrees.folder_name("feature/login") == "feature-login"
    assert worktrees.folder_name("neue funktion") == "neue-funktion"
    assert worktrees.folder_name("...") == "branch"


def test_convert_moves_code_into_main(tmp_path, projects_root, make_services):
    bare, code, other = branch_repo(tmp_path, projects_root)
    (code / "notiz.txt").write_text("nicht hochgeladen\n", encoding="utf-8")
    services = make_services([])
    project = services.projects.add(code.parent)
    assert worktrees.can_convert(project) and not project.has_branch_folders
    steps = []
    main = worktrees.convert(project, steps.append)
    assert main == code / "main"
    assert sorted(p.name for p in code.iterdir()) == ["main"]
    assert (main / "notiz.txt").read_text(encoding="utf-8") == "nicht hochgeladen\n"
    assert git.status(main).branch == "main"
    assert steps == ["Sicherheitskopie wird angelegt", "Dateien werden nach Code\\main verschoben"]
    saved = [p for p in backups.backups_dir().iterdir() if "Branch-Ordner" in p.name]
    assert (saved[0] / "Code" / "notiz.txt").is_file()
    moved = services.projects.set_code_dir(project, main)
    assert moved.has_branch_folders and moved.code_root == code
    assert not worktrees.can_convert(moved)
    # Ein neu eingelesenes Projekt findet Code\main von selbst
    assert main_code_dir(code) == main
    assert classify_folder(main) == ("project", code.parent)


def test_convert_puts_everything_back_if_a_file_is_open(tmp_path, projects_root, make_services):
    bare, code, other = branch_repo(tmp_path, projects_root)
    services = make_services([])
    project = services.projects.add(code.parent)
    before = sorted(p.name for p in code.iterdir())
    with open(code / "main.py", encoding="utf-8"):
        with pytest.raises(CockpitError, match="nichts geändert"):
            worktrees.convert(project)
    assert sorted(p.name for p in code.iterdir()) == before
    assert git.status(code).branch == "main"


# -- Branch-Ordner --------------------------------------------------------------------------------
def test_new_branch_gets_its_own_folder(tmp_path, projects_root, make_services):
    services, project, other = structured(tmp_path, projects_root, make_services)
    sh(other, "switch", "-q", "main")
    commit(other, "Main auf der Plattform weiter", {"neu.py": "1\n"})
    sh(other, "push", "-q")
    tree = worktrees.create(project, "neue-funktion")
    assert tree.path == project.code_root / "neue-funktion"
    # Beginnt beim neuesten Stand von main auf der Plattform, lädt später unter eigenem Namen hoch
    assert (tree.path / "neu.py").is_file()
    state = git.status(tree.path)
    assert state.branch == "neue-funktion" and state.upstream == ""
    # Ein Commit im Ordner landet im Branch, main bleibt unverändert
    commit(tree.path, "Im Branch", {"funktion.py": "x\n"})
    assert "Im Branch" in sh(project.code_dir, "log", "-1", "--format=%s", "neue-funktion")
    assert "Im Branch" not in sh(project.code_dir, "log", "-1", "--format=%s", "main")
    assert [t.branch for t in worktrees.list_worktrees(project)] == ["neue-funktion"]
    with pytest.raises(CockpitError, match="gibt es schon"):
        worktrees.create(project, "neue-funktion")


def test_open_existing_and_remote_branches(tmp_path, projects_root, make_services):
    services, project, other = structured(tmp_path, projects_root, make_services)
    local = worktrees.open_branch(project, "lokal-neu")
    assert (local.path / "lokal.py").is_file()
    remote = worktrees.open_branch(project, "design")
    assert (remote.path / "design.css").is_file()
    assert git.status(remote.path).upstream == "origin/design"
    assert worktrees.open_branch(project, "design") == remote       # schon da
    with pytest.raises(CockpitError, match="gibt es nicht mehr"):
        worktrees.open_branch(project, "gibt-es-nicht")


def test_status_lists_branch_folders(tmp_path, projects_root, make_services):
    from cockpit.ui.project_list import children_of
    services, project, other = structured(tmp_path, projects_root, make_services)
    tree = worktrees.open_branch(project, "suche")
    (tree.path / "neu.txt").write_text("x\n", encoding="utf-8")
    status = project_status.compute(project)
    assert [t.folder for t, _s in status.worktrees] == ["suche"]
    assert project_status.for_folder(status, "suche").pending == 1
    rows = children_of(project, status, "GitHub")
    # Wunsch vom 30.09.2026: "Main-Branch" und darunter "Branches verwalten"
    # Seit dem 02.10.2026 nur lokale Branches, ohne "Branches auf GitHub"
    assert [r[0] for r in rows] == ["Main-Branch, alles hochgeladen", "Branches verwalten",
                                    "Branch suche, 1 Datei noch nicht hochgeladen"]
    assert [r[1] for r in rows] == [Target.CODE, Target.BRANCH_OVERVIEW, Target.BRANCH]


def test_merge_state_is_found_in_a_branch_folder(tmp_path, projects_root, make_services):
    services, project, other = structured(tmp_path, projects_root, make_services)
    tree = worktrees.open_branch(project, "suche")
    assert git.git_dir(tree.path).is_dir() and (tree.path / ".git").is_file()
    assert not sync.merging(tree.path)
    (git.git_dir(tree.path) / "MERGE_HEAD").write_text("x\n", encoding="utf-8")
    assert sync.merging(tree.path) and git.status(tree.path).merging


def test_remove_keeps_branch_and_backs_up_changes(tmp_path, projects_root, make_services):
    services, project, other = structured(tmp_path, projects_root, make_services)
    clean = worktrees.open_branch(project, "suche")
    assert worktrees.remove(project, clean) is None
    assert not clean.path.exists()
    assert "suche" in sh(project.code_dir, "branch", "--list", "suche")
    busy = worktrees.open_branch(project, "suche")
    (busy.path / "entwurf.txt").write_text("wichtig\n", encoding="utf-8")
    saved = worktrees.remove(project, busy)
    assert (saved / "suche" / "entwurf.txt").read_text(encoding="utf-8") == "wichtig\n"
    assert worktrees.list_worktrees(project) == []


def test_branch_merged_on_the_platform_is_marked_gone(tmp_path, projects_root, make_services):
    services, project, other = structured(tmp_path, projects_root, make_services)
    tree = worktrees.open_branch(project, "suche")
    sh(other, "push", "-q", "origin", "--delete", "suche")
    sh(project.code_dir, "fetch", "-q", "--prune")
    assert worktrees.list_worktrees(project)[0].gone
    assert not worktrees.needs_backup(worktrees.list_worktrees(project)[0])
    assert tree.branch == "suche"


# -- Oberfläche -----------------------------------------------------------------------------------
def window(qtbot, services):
    """Hauptfenster. Wartet, bis die Standabfrage im Hintergrund fertig ist. Sonst beendet Qt den
    Testlauf, wenn das Fenster zerstört wird, während sie noch läuft."""
    from cockpit.ui.main_window import MainWindow
    win = MainWindow(services)
    qtbot.addWidget(win)
    qtbot.waitUntil(lambda: win.status_task is None, timeout=20000)
    win.reload_projects(refresh=False)
    return win

def test_branch_row_uses_the_branch_folder(qtbot, tmp_path, projects_root, make_services):
    services, project, other = structured(tmp_path, projects_root, make_services)
    tree = worktrees.open_branch(project, "suche")
    win = window(qtbot, services)
    status = project_status.compute(project)
    win.project_list.update_status(status, project)
    assert win.project_list.select(Target.BRANCH, project.id, "suche")
    context = win.action_context()
    assert context.target is Target.CODE and context.worktree.folder == "suche"
    assert context.project.code_dir == tree.path and context.main_project.code_dir == \
        project.code_dir
    labels = [e.label for e in win.current_entries()]
    # Seit dem 30.09.2026 in "Branches verwalten"
    assert "Branch-Ordner entfernen …" not in labels and "Neuer Branch …" not in labels
    assert "Ordner für Branches einrichten …" not in labels
    # "Code" gewünscht, Markierung bleibt auf dem Branch-Ordner
    assert win.project_list.select(Target.CODE, project.id)
    assert win.project_list.current_key() == "suche"


def test_setup_action_only_for_old_structure(qtbot, tmp_path, projects_root, make_services):
    bare, code, other = branch_repo(tmp_path, projects_root)
    services = make_services([])
    project = services.projects.add(code.parent)
    win = window(qtbot, services)
    win.project_list.update_status(project_status.compute(project), project)
    win.project_list.select(Target.CODE, project.id)
    labels = [e.label for e in win.current_entries()]
    assert "Ordner für Branches einrichten …" in labels and "Neuer Branch …" not in labels


def test_branch_context_project_is_a_copy(tmp_path, projects_root, make_services):
    services, project, other = structured(tmp_path, projects_root, make_services)
    tree = worktrees.open_branch(project, "suche")
    copy = dataclasses.replace(project, code_dir=tree.path)
    assert copy.has_branch_folders and copy.code_root == project.code_root
    # Vom Branch-Ordner aus: weder main noch der Ordner selbst zählen als weitere Branch-Ordner
    assert worktrees.list_worktrees(copy) == []


# -- Neue Projekte --------------------------------------------------------------------------------
def test_download_without_branch_folders(account, projects_root, tmp_path):
    from cockpit.core import project_setup
    from tests.test_phase5a import make_remote, stored_repo
    services, acc, _ = account
    services.settings.update(branch_folders=False)
    bare = make_remote(tmp_path, "Rechner")
    repo = stored_repo(services, acc.id, bare, "Rechner", "2026-09-20T10:00:00Z")
    project = project_setup.download(services, repo, projects_root)
    assert project.code_dir == projects_root / "Rechner" / "Code"
    assert not project.has_branch_folders


def test_add_local_repo_into_main_folder(tmp_path, projects_root, make_services):
    services = make_services([])
    folder = tmp_path / "irgendwo" / "Notizen"
    folder.mkdir(parents=True)
    sh(folder, "init", "-q")
    commit(folder, "Erste Version", {"notizen.py": "x\n"})
    project, moved = services.projects.convert(folder, projects_root, "main")
    assert moved and project.code_dir == projects_root / "Notizen" / "Code" / "main"
    assert project.has_branch_folders and (project.code_dir / "notizen.py").is_file()

def test_new_folder_in_main_does_not_block_merging(qtbot, tmp_path, projects_root, make_services,
                                                   monkeypatch):
    """Rückmeldung zum Test von 8e: Ein neuer Ordner in main verhinderte das Übernehmen."""
    from cockpit.core import branches
    from cockpit.ui import branch_dialogs
    services, project, other = structured(tmp_path, projects_root, make_services)
    (project.code_dir / "erklärvideos").mkdir()
    (project.code_dir / "erklärvideos" / "notiz.txt").write_text("x\n", encoding="utf-8")
    assert sync.blocking_merge(project.code_dir, "suche") == []
    (project.code_dir / "main.py").write_text("geändert\n", encoding="utf-8")
    assert sync.blocking_merge(project.code_dir, "suche") == ["main.py"]
    sh(project.code_dir, "checkout", "--", "main.py")
    questions, errors = [], []
    monkeypatch.setattr(branch_dialogs, "confirm", lambda parent, title, text, **kw:
                        questions.append(text) or False)
    monkeypatch.setattr(branch_dialogs, "show_error", lambda parent, title, text, *a:
                        errors.append(text))
    items = [b for b in branches.list_branches(project.code_dir) if b.name == "suche"]
    dialog = branch_dialogs.BranchesDialog(project, items, single=True)
    qtbot.addWidget(dialog)
    dialog.merge_current()
    assert errors == [] and questions[0].startswith("Die 2 Commits aus suche kommen in main")