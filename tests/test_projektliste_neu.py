"""Neue Projektliste (Wunsch des Nutzers vom 06.10.2026).

Projekt verwalten mit Umbenennen und Löschen, die Zeile Repository mit der Auswahl der Branches,
Infos und Umbenennen beim Haupt-Branch. Die Plattform ist eine Attrappe, Git arbeitet mit einem
nackten Repository. Alle Geheimnisse sind erfunden.
"""
from __future__ import annotations

import dataclasses

import pytest

from cockpit.core import branches, git, project_admin, project_status, worktrees
from cockpit.core.actions import Target
from cockpit.core.errors import CockpitError
from cockpit.core.git import RemoteAddress
from cockpit.platforms.base import RepoRef
from cockpit.ui import project_list as listing
from cockpit.ui.project_manage import ProjectManageDialog, delete_text
from tests.conftest import FakePlatform, said
from tests.test_phase10f import structured, window
from tests.test_phase5a import sh

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

REMOTE = RemoteAddress("github.com", "tester", "Tagebuch")


class RenamingPlatform(FakePlatform):
    """Benennt Repository und Branch um wie GitHub, den Branch im nackten Repository."""

    def __init__(self, bare=None) -> None:
        super().__init__()
        self.bare = bare
        self.renamed: list = []

    def rename_repo(self, repo: RepoRef, name: str) -> RepoRef:
        self.renamed.append((repo.name, name))
        return RepoRef(repo.owner, name)

    def rename_branch(self, repo: RepoRef, old: str, new: str) -> None:
        self.renamed.append((old, new))
        sh(self.bare, "branch", "-m", old, new)
        sh(self.bare, "symbolic-ref", "HEAD", f"refs/heads/{new}")


# -- Umbenennen -------------------------------------------------------------------------------
def test_name_problem(tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    store = services.projects
    assert project_admin.name_problem(store, project, " ") == "Bitte geben Sie einen Namen ein."
    assert "schon der Name" in project_admin.name_problem(store, project, "Tagebuch")
    assert "Zeichen" in project_admin.name_problem(store, project, "Tage:buch")
    assert "Zeichen" in project_admin.name_problem(store, project, "Tagebuch.")
    (project.project_dir.parent / "Belegt").mkdir()
    assert "gibt es schon" in project_admin.name_problem(store, project, "Belegt")
    assert project_admin.name_problem(store, project, "Notizbuch") == ""


def test_rename_moves_the_folder_and_keeps_branch_folders(tmp_path, projects_root,
                                                          make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    worktrees.open_branch(project, "suche")
    old_dir = project.project_dir
    steps = []
    renamed = project_admin.rename_local(services.projects, project, "Notizbuch", steps.append)
    assert not old_dir.exists()
    assert renamed.name == "Notizbuch" and renamed.project_dir == old_dir.parent / "Notizbuch"
    assert renamed.code_dir == renamed.project_dir / "Code" / "main"
    assert renamed.exe_dir == renamed.project_dir / "Exe"
    trees = worktrees.list_worktrees(renamed)
    assert [t.folder for t in trees] == ["suche"]
    assert trees[0].path.parent == renamed.project_dir / "Code"
    assert git.status(trees[0].path).branch == "suche"            # Git findet sich zurecht
    assert services.projects.get(project.id).name == "Notizbuch"
    assert "Ordner wird umbenannt" in steps


def test_rename_stops_when_the_folder_is_busy(tmp_path, projects_root, make_services,
                                              monkeypatch):
    services, project, _other = structured(tmp_path, projects_root, make_services)

    def busy(*_args):
        raise PermissionError("in Benutzung")

    monkeypatch.setattr(project_admin.os, "rename", busy)
    with pytest.raises(CockpitError, match="Es wurde nichts geändert"):
        project_admin.rename_local(services.projects, project, "Notizbuch")
    assert services.projects.get(project.id).name == "Tagebuch"
    assert project.project_dir.exists()


def test_rename_remote_changes_the_address(tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    project = dataclasses.replace(project, remote=REMOTE)
    platform = RenamingPlatform()
    address = project_admin.rename_remote(platform, project, "Notizbuch")
    assert platform.renamed == [("Tagebuch", "Notizbuch")]
    assert address == RemoteAddress("github.com", "tester", "Notizbuch")
    assert git.config_get(project.code_dir, "remote.origin.url") == \
        "https://x/tester/Notizbuch.git"


# -- Löschen ----------------------------------------------------------------------------------
def test_delete_moves_the_project_into_the_backups(tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    kept = project_admin.delete_local(services.projects, project)
    assert not project.project_dir.exists()
    assert len(kept) == 1 and (kept[0] / "Code" / "main" / "main.py").is_file()
    assert services.projects.get(project.id) is None


def test_manage_dialog_names_what_is_deleted(qtbot, tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    assert delete_text(project) == ("Projekt &löschen …, lokaler Ordner auf dem Rechner wird "
                                    "gelöscht")
    with_remote = dataclasses.replace(project, remote=REMOTE)
    assert delete_text(with_remote) == ("Projekt &löschen …, lokaler Ordner auf dem Rechner, "
                                        "Repository und Release werden gelöscht")
    dialog = ProjectManageDialog(with_remote)
    qtbot.addWidget(dialog)
    assert dialog.name_edit.text() == "Tagebuch" and dialog.name_edit.isReadOnly()
    assert dialog.name_edit.accessibleName() == "Derzeitiger Name"
    assert dialog.rename_button.text() == "Projekt &umbenennen …"
    assert dialog.remove_button.text() == "Aus der &Liste entfernen …"
    dialog.delete_button.click()
    assert dialog.choice == "delete"


# -- Zeile Repository -------------------------------------------------------------------------
def test_show_choice_changes_rows_and_is_kept(qtbot, tmp_path, projects_root, make_services,
                                             monkeypatch):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    worktrees.open_branch(project, "suche")
    win = window(qtbot, services)
    win.project_list.update_status(project_status.compute(project), project)
    assert win.project_list.select(Target.REPOSITORY, project.id)
    assert any(t.startswith("Branch suche") for t in win.project_list.texts())
    offered = []
    monkeypatch.setattr(listing, "pick_show",
                        lambda widget, names, current: offered.append((names, current)) or "main")
    entry = next(e for e in win.current_entries() if e.action.id == "branch_show")
    win.run_entry(entry)
    names, current = offered[0]
    assert current == "local" and list(names.values()) == [
        "Nur main", "main & die Sie lokal haben", "main & die nur auf GitHub sind", "main & alle"]
    texts = win.project_list.texts()
    assert "Repository, Branches: Nur main" in texts
    assert not any(t.startswith("Branch suche") for t in texts)
    assert win.project_list.current_target() == (Target.REPOSITORY, project.id)
    assert said("Nur main")
    assert services.database.get_value("projects.branch_show") == {str(project.id): "main"}


def test_enter_on_repository_opens_the_choice(qtbot, tmp_path, projects_root, make_services,
                                              monkeypatch):
    from PySide6.QtCore import Qt
    services, project, _other = structured(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    win.project_list.select(Target.REPOSITORY, project.id)
    opened = []
    monkeypatch.setattr(listing, "pick_show",
                        lambda widget, names, current: opened.append(current) or None)
    win.project_list.setFocus()
    qtbot.keyClick(win.project_list, Qt.Key.Key_Return)
    assert opened == ["local"]                                      # Escape: nichts geändert


# -- Haupt-Branch ----------------------------------------------------------------------------
def test_info_lines_for_main(tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    main = next(b for b in branches.list_branches(project.code_dir) if b.default)
    lines = branches.info_lines(project.code_dir, main)
    assert lines[0] == "main, hier und auf GitHub"
    assert lines[1].startswith("Angelegt von ")
    assert any(line.startswith("Zuletzt geändert von ") for line in lines)
    assert any(line.endswith("Commits") or line == "1 Commit" for line in lines)


def test_rename_main_everywhere(tmp_path, projects_root, make_services):
    from tests.test_phase5f import branch_repo
    bare, code, _other = branch_repo(tmp_path, projects_root)
    services = make_services([])
    project = services.projects.add(code.parent)
    project = services.projects.set_code_dir(project, worktrees.convert(project))
    project = dataclasses.replace(project, remote=REMOTE)
    worktrees.open_branch(project, "suche")
    platform = RenamingPlatform(bare)
    renamed, note = project_admin.rename_main(services.projects, project, "main", "haupt",
                                              platform)
    assert note == ""
    assert platform.renamed == [("main", "haupt")]
    assert renamed.code_dir == project.code_dir.parent / "haupt"
    assert git.status(renamed.code_dir).branch == "haupt"
    assert git.status(renamed.code_dir).upstream == "origin/haupt"
    assert [t.folder for t in worktrees.list_worktrees(renamed)] == ["suche"]
    assert "haupt" in sh(bare, "branch", "--list")


# -- Releases (Schritt 4) ----------------------------------------------------------------------
def with_releases(tmp_path, projects_root, make_services):
    """Tagebuch mit Branch suche, Exe-main mit einer Exe-Datei und Exe-suche ohne Exe."""
    from cockpit.core import local_releases
    services, project, _other = structured(tmp_path, projects_root, make_services)
    worktrees.open_branch(project, "suche")
    home = project.exe_dir / "Tagebuch"
    home.mkdir(parents=True)
    (home / "Tagebuch.exe").write_bytes(b"MZ")
    local_releases.create_branch_release(project, "suche")
    return services, project


def test_local_releases_are_listed_main_first(tmp_path, projects_root, make_services):
    from cockpit.core import local_releases
    services, project = with_releases(tmp_path, projects_root, make_services)
    releases = local_releases.all_releases(project)
    assert [r.folder for r in releases] == ["", "suche"]
    assert [r.title() for r in releases] == ["Exe-main", "Exe-suche"]
    assert releases[0].path == project.exe_dir / "Tagebuch"
    assert local_releases.line(project, releases[1]) == "Exe-suche, noch keine Exe-Datei"
    assert local_releases.line(project, releases[0]).startswith("Exe-main, ")
    assert local_releases.releases_line(project) == "Releases, 2 Releases"
    with pytest.raises(CockpitError, match="gibt es schon"):
        local_releases.create_branch_release(project, "suche")


def test_published_line_and_remote_release(tmp_path, projects_root, make_services):
    from cockpit.core import exe, local_releases
    from cockpit.platforms.base import Release
    services, project = with_releases(tmp_path, projects_root, make_services)
    branch = local_releases.find(project, "suche")
    assert local_releases.published_line(project, branch) == "noch nicht veröffentlicht"
    (branch.path / exe.VERSION_FILE).write_text("1.1.0\n", encoding="utf-8")
    assert local_releases.published_line(project, branch).startswith("zuletzt Version 1.1.0 am ")
    published = [Release(1, "v1.1.0", "Version 1.1.0", "u", ""),
                 Release(2, "v1.1.0-suche", "Version 1.1.0, Branch suche", "u", "")]
    assert local_releases.remote_release(project, branch, published).id == 2


def test_remove_local_release_goes_into_the_backups(tmp_path, projects_root, make_services):
    from cockpit.core import local_releases
    services, project = with_releases(tmp_path, projects_root, make_services)
    main = local_releases.find(project, "")
    kept = local_releases.remove_local(project, main)
    assert not main.path.exists() and (kept / "Tagebuch.exe").is_file()
    assert local_releases.find(project, "suche").path.is_dir()          # das andere bleibt


def test_rows_and_actions_of_the_releases(qtbot, tmp_path, projects_root, make_services):
    services, project = with_releases(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    win.project_list.update_status(project_status.compute(project), project)
    assert win.project_list.select(Target.RELEASES, project.id)
    texts = win.project_list.texts()
    start = texts.index("Releases, 2 Releases")
    assert texts[start + 1].startswith("Exe-main, ")
    assert texts[start + 2] == "Exe-suche, noch keine Exe-Datei"
    assert win.project_list.select(Target.RELEASES, project.id)
    labels = [e.label for e in win.current_entries()]
    assert labels[:4] == ["Releases neu einlesen", "Terminal …",
                          "Release für Branch aus Repository erstellen …",
                          "Release entfernen …"]
    assert labels[-1] == "Release-Ordner öffnen"
    assert win.project_list.select(Target.EXE, project.id)
    labels = [e.label for e in win.current_entries()]
    assert "Release einlesen …" in labels and labels[-1] == "Exe-main-Ordner öffnen"
    assert "Terminal …" in labels
    assert win.project_list.select(Target.RELEASE, project.id, "suche")
    context = win.action_context()
    assert context.release.folder == "suche" and context.worktree.folder == "suche"
    labels = [e.label for e in win.current_entries()]
    assert labels[0] == "Releases neu einlesen"
    assert "Exe starten, nicht verfügbar: In diesem Release liegt noch keine Exe." in labels
    assert labels[-1] == "Exe-suche-Ordner öffnen"


def test_create_release_for_a_local_branch(qtbot, tmp_path, projects_root, make_services,
                                           monkeypatch):
    from cockpit.ui import release_rows
    services, project, _other = structured(tmp_path, projects_root, make_services)
    worktrees.open_branch(project, "suche")
    project.exe_dir.mkdir()
    win = window(qtbot, services)
    win.project_list.update_status(project_status.compute(project), project)
    win.project_list.select(Target.RELEASES, project.id)
    asked = []
    monkeypatch.setattr(release_rows, "pick", lambda parent, title, note, name, items, button:
                        asked.append((note, items, button)) or 0)
    entry = next(e for e in win.current_entries() if e.action.id == "create_release")
    win.run_entry(entry)
    assert asked == [(release_rows.CREATE_NOTE, ["Branch suche"],
                      "Release-Ordner &lokal anlegen")]
    assert (project.exe_dir / "Tagebuch_branch_suche").is_dir()
    assert win.project_list.current_target() == (Target.RELEASE, project.id)
    assert win.project_list.current_key() == "suche"
    assert said("Release Exe-suche angelegt.")


def test_remove_release_asks_and_cancel_keeps_it(qtbot, tmp_path, projects_root, make_services,
                                                 monkeypatch):
    from cockpit.core import local_releases
    from cockpit.ui import release_rows
    services, project = with_releases(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    win.project_list.update_status(project_status.compute(project), project)
    win.project_list.select(Target.RELEASE, project.id, "suche")
    questions = []
    answers = iter([1, 0])                          # erst Abbrechen, dann "Nur lokal"
    monkeypatch.setattr(release_rows, "ask_buttons", lambda parent, title, text, options,
                        default, escape: questions.append((options, default, escape))
                        or next(answers))
    entry = next(e for e in win.current_entries() if e.action.id == "remove_this_release")
    win.run_entry(entry)
    assert questions[0] == (["Nur lokal auf dem Rechner", "Abbrechen"], 1, 1)
    assert local_releases.find(project, "suche") is not None
    win.run_entry(entry)
    assert local_releases.find(project, "suche") is None
    assert said("Exe-suche lokal entfernt")
