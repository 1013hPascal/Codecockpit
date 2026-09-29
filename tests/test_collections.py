"""Projektsammlungen: Speicher, Projektliste, Tastatur und Aktionen."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from cockpit.core.actions import Target
from cockpit.core.database import Database
from cockpit.core.errors import CockpitError
from cockpit.core.project_collections import CollectionStore, clean_name
from cockpit.core.projects import ProjectStore
from cockpit.ui import collections_flow
from cockpit.ui.announcer import announcer
from cockpit.ui.collections_flow import MembersDialog, NameDialog
from tests.conftest import make_project, said
from tests.test_ui import close_dialogs_later, current_text, press, select_project, window  # noqa: F401


def project_id(win, name: str) -> int:
    return next(p.id for p in win.services.projects.all() if p.name == name)


def web_window(window, names=("PDF-Chat", "Tagebuch", "Webseite")):
    """Fenster mit der Sammlung Web, darin nur die Webseite."""
    win = window(names=names)
    store = win.services.collections
    web = store.create("Web")
    store.set_members(web.id, {project_id(win, "Webseite")})
    win.reload_projects(refresh=False)
    return win, web


# -- Speicher ---------------------------------------------------------------------------------
@pytest.fixture
def stores(tmp_path, projects_root):
    database = Database(tmp_path / "c.db")
    projects = ProjectStore(database)
    ids = [projects.add(make_project(projects_root, name)).id for name in ("A", "B", "C")]
    return CollectionStore(database), projects, ids


def test_names_are_cleaned_and_must_be_unique(stores):
    store, _projects, _ids = stores
    assert clean_name("  Sammlung   Eigene  Programme ") == "Eigene Programme"
    web = store.create("Web")
    assert web.title == "Sammlung Web"
    with pytest.raises(CockpitError, match="gibt es schon"):
        store.create("web")
    with pytest.raises(CockpitError, match="Namen ein"):
        store.create("   ")
    assert store.rename(web.id, "Web").name == "Web"          # der eigene Name ist erlaubt
    assert store.rename(web.id, "Webseiten").name == "Webseiten"
    assert [c.name for c in store.all()] == ["Webseiten"]


def test_a_project_is_in_one_collection_only(stores):
    store, _projects, (a, b, c) = stores
    ki = store.create("KI")
    web = store.create("Web")
    store.set_members(ki.id, {a, b})
    store.set_members(web.id, {b, c})                         # b wechselt von KI zu Web
    assert store.membership() == {a: ki.id, b: web.id, c: web.id}
    store.set_members(web.id, {c})                            # b steht wieder ohne Sammlung
    assert store.membership() == {a: ki.id, c: web.id}


def test_dissolving_keeps_the_projects(stores):
    store, projects, (a, b, _c) = stores
    ki = store.create("KI")
    store.set_members(ki.id, {a, b})
    store.dissolve(ki.id)
    assert store.all() == [] and store.membership() == {}
    assert len(projects.all()) == 3


def test_removing_a_project_removes_it_from_its_collection(stores):
    store, projects, (a, b, _c) = stores
    ki = store.create("KI")
    store.set_members(ki.id, {a, b})
    projects.remove(a)
    assert store.members(ki.id) == {b}


# -- Projektliste ---------------------------------------------------------------------------
def test_collections_stand_below_the_first_entries(window):
    win, _web = web_window(window)
    texts = win.project_list.texts()
    assert texts[:4] == ["Neue Projektsammlung", "Projekt vom Rechner hinzufügen",
                         "Projekt von GitHub herunterladen", "Sammlung Web, 1 Projekt"]
    assert sorted(texts[4:]) == ["PDF-Chat", "Tagebuch"]       # Webseite steht in der Sammlung
    assert current_text(win) == "Neue Projektsammlung"


def test_empty_collection_says_so(window):
    win = window()
    win.services.collections.create("Leer")
    win.reload_projects(refresh=False)
    assert "Sammlung Leer, leer" in win.project_list.texts()


@pytest.mark.parametrize("key", [Qt.Key.Key_Return, Qt.Key.Key_Space])
def test_enter_opens_and_closes_a_collection(window, qtbot, key):
    win, web = web_window(window)
    win.project_list.select(Target.COLLECTION, web.id)
    press(qtbot, win.project_list, key)
    assert win.project_list.texts() == ["Sammlung Web, 1 Projekt, geöffnet", "Webseite"]
    assert current_text(win) == "Sammlung Web, 1 Projekt, geöffnet"
    assert announcer.last_text == "Geöffnet, 1 Projekt."
    press(qtbot, win.project_list, key)
    assert current_text(win) == "Sammlung Web, 1 Projekt"
    assert "PDF-Chat" in win.project_list.texts()
    assert announcer.last_text == "Geschlossen."


def test_arrows_move_through_collection_and_project(window, qtbot):
    win, web = web_window(window)
    listing = win.project_list
    listing.select(Target.COLLECTION, web.id)
    press(qtbot, listing, Qt.Key.Key_Right)                   # öffnen
    press(qtbot, listing, Qt.Key.Key_Right)                   # zum ersten Projekt
    assert current_text(win) == "Webseite"
    press(qtbot, listing, Qt.Key.Key_Right)                   # Projekt ausklappen
    assert current_text(win) == "Webseite, ausgeklappt"
    press(qtbot, listing, Qt.Key.Key_Right)
    assert current_text(win) == "Code"
    press(qtbot, listing, Qt.Key.Key_Left)                    # zuklappen, zurück zum Projekt
    assert current_text(win) == "Webseite"
    press(qtbot, listing, Qt.Key.Key_Left)                    # zur Sammlung
    assert current_text(win) == "Sammlung Web, 1 Projekt, geöffnet"
    press(qtbot, listing, Qt.Key.Key_Left)                    # schließen
    assert current_text(win) == "Sammlung Web, 1 Projekt"


def test_backspace_closes_from_inside(window, qtbot):
    win, web = web_window(window)
    win.project_list.select(Target.CODE, project_id(win, "Webseite"))
    assert win.project_list.opened_collection_id == web.id    # von selbst geöffnet
    assert current_text(win) == "Code"
    press(qtbot, win.project_list, Qt.Key.Key_Backspace)
    assert current_text(win) == "Sammlung Web, 1 Projekt"


def test_selecting_a_top_entry_closes_the_collection(window):
    win, web = web_window(window)
    win.project_list.open_collection(web.id, speak=False)
    assert win.project_list.select(Target.PROJECT, project_id(win, "PDF-Chat"))
    assert win.project_list.opened_collection_id is None


def test_reload_keeps_the_open_collection(window):
    win, web = web_window(window)
    win.project_list.select(Target.PROJECT, project_id(win, "Webseite"))
    win.reload_projects(refresh=False)
    assert win.project_list.opened_collection_id == web.id
    assert current_text(win) == "Webseite"


# -- Aktionen -------------------------------------------------------------------------------
def test_actions_of_a_collection(window):
    win, web = web_window(window)
    win.project_list.select(Target.COLLECTION, web.id)
    assert win.actions_list.texts() == ["Projekte für die Sammlung …",
                                        "Projektsammlung umbenennen …",
                                        "Projektsammlung auflösen …"]
    win.project_list.select(Target.NEW_COLLECTION, None)
    assert win.actions_list.texts() == ["Neue Projektsammlung …"]


def fill_name(name):
    def action(dialog):
        assert isinstance(dialog, NameDialog)
        dialog.edit.setText(name)
        dialog.accept()
    return action


def test_new_collection_with_enter(window, qtbot):
    win = window()
    win.project_list.select(Target.NEW_COLLECTION, None)
    close_dialogs_later(qtbot, fill_name("Private Programme"))
    press(qtbot, win.project_list, Qt.Key.Key_Return)
    assert current_text(win) == "Sammlung Private Programme, leer"
    assert said("Sammlung Private Programme angelegt.")


def test_duplicate_name_asks_again(window, qtbot, monkeypatch):
    win, _web = web_window(window)
    shown = []
    monkeypatch.setattr(collections_flow, "show_info", lambda parent, title, text: shown.append(text))
    answers = iter(["web", "KI"])
    monkeypatch.setattr(NameDialog, "exec", lambda self: self.edit.setText(next(answers)) or 1)
    win.controller.collections.create()
    assert shown == ["Die Sammlung web gibt es schon. Bitte wählen Sie einen anderen Namen."]
    assert "Sammlung KI, leer" in win.project_list.texts()


def test_name_dialog_is_accessible(qtbot):
    dialog = NameDialog("Neue Projektsammlung", "Web")
    qtbot.addWidget(dialog)
    assert dialog.edit.accessibleName() == "Name"
    assert dialog.edit.selectedText() == "Web"


def test_members_dialog_lists_all_projects_with_hint(window, qtbot):
    win, web = web_window(window)
    store = win.services.collections
    ki = store.create("KI")
    store.set_members(ki.id, {project_id(win, "Tagebuch")})
    dialog = MembersDialog(web, win.services.projects.all(), store.membership(),
                           {c.id: c for c in store.all()})
    qtbot.addWidget(dialog)
    first = dialog.list.item(0)
    assert first.text().startswith("Markieren Sie alle Projekte, die der Sammlung Web "
                                   "zugeordnet werden sollen.")
    assert not first.flags() & Qt.ItemFlag.ItemIsUserCheckable
    assert [i.text() for i in dialog.items()] == [
        "PDF-Chat, nur auf dem Rechner", "Tagebuch, nur auf dem Rechner, in Sammlung KI",
        "Webseite, nur auf dem Rechner"]
    assert dialog.chosen() == {project_id(win, "Webseite")}
    assert dialog.list.accessibleName() == "Projekte"
    assert dialog.save_button.isDefault()


def test_saving_members_moves_projects(window, qtbot, monkeypatch):
    win, web = web_window(window)
    store = win.services.collections
    ki = store.create("KI")
    store.set_members(ki.id, {project_id(win, "Tagebuch")})
    win.reload_projects(refresh=False)
    win.project_list.select(Target.COLLECTION, web.id)

    def check_all(dialog):
        for item in dialog.items():
            item.setCheckState(Qt.CheckState.Checked)
        qtbot.keyClick(dialog.list, Qt.Key.Key_Return)          # Enter speichert
    close_dialogs_later(qtbot, check_all)
    win.run_entry(win.current_entries()[0])
    assert len(store.members(web.id)) == 3 and store.members(ki.id) == set()
    assert current_text(win) == "Sammlung Web, 3 Projekte"
    assert said("Gespeichert. Sammlung Web: 3 Projekte.")


def test_cancel_keeps_members(window, qtbot):
    win, web = web_window(window)
    win.project_list.select(Target.COLLECTION, web.id)
    close_dialogs_later(qtbot)
    win.run_entry(win.current_entries()[0])
    assert win.services.collections.members(web.id) == {project_id(win, "Webseite")}


def test_rename(window, qtbot):
    win, web = web_window(window)
    win.project_list.select(Target.COLLECTION, web.id)
    close_dialogs_later(qtbot, fill_name("Webseiten"))
    win.run_entry(win.current_entries()[1])
    assert current_text(win) == "Sammlung Webseiten, 1 Projekt"
    assert said("Umbenannt in Sammlung Webseiten.")


def test_dissolve_asks_and_puts_projects_back(window, monkeypatch):
    win, web = web_window(window)
    asked = []
    monkeypatch.setattr(collections_flow, "confirm",
                        lambda parent, title, text, yes, no: asked.append((text, yes)) or True)
    win.project_list.open_collection(web.id, speak=False)
    win.run_entry(win.current_entries()[2])
    assert asked == [("Die Sammlung Web wird aufgelöst. Das Projekt darin steht danach "
                      "wieder einzeln in der Projektliste, ohne Sammlung. Ordner und Dateien "
                      "bleiben unverändert.", "Auflösen")]
    assert win.services.collections.all() == []
    assert win.project_list.opened_collection_id is None
    assert current_text(win) == "Webseite"
    assert "Sammlung Web, 1 Projekt" not in win.project_list.texts()
    assert said("Sammlung Web aufgelöst.")


def test_dissolve_can_be_cancelled(window, monkeypatch):
    win, web = web_window(window)
    monkeypatch.setattr(collections_flow, "confirm", lambda *args, **kwargs: False)
    win.project_list.select(Target.COLLECTION, web.id)
    win.run_entry(win.current_entries()[2])
    assert [c.id for c in win.services.collections.all()] == [web.id]


# -- Nachtrag: Repositories nur auf GitHub ----------------------------------------------------
def add_remote_repos(services, *names):
    """Erfundenes Konto mit Repositories, die nur auf GitHub liegen."""
    from cockpit.platforms.base import RemoteRepo, RepoRef
    cursor = services.database.execute(
        "INSERT INTO accounts (kind, adapter, display_name) VALUES ('platform', 'github', 'T')")
    services.remote_repos.replace(cursor.lastrowid, [
        RemoteRepo(RepoRef("tester", name), True, f"https://github.com/tester/{name}.git",
                   f"https://github.com/tester/{name}", "2026-09-01T00:00:00Z")
        for name in names])
    return {r.name: r for r in services.remote_repos.all()}


def test_store_keeps_remote_members_by_address(stores):
    store, projects, (a, _b, _c) = stores
    web = store.create("Web")
    ki = store.create("KI")
    store.set_members(web.id, {a}, {"github.com/tester/Vokabeln"})
    assert store.remote_membership() == {"github.com/tester/vokabeln": web.id}
    store.set_members(ki.id, set(), {"github.com/tester/vokabeln"})   # wechselt zu KI
    assert store.remote_members(web.id) == set()
    store.dissolve(ki.id)
    assert store.remote_membership() == {}


def test_downloaded_repo_keeps_its_collection(stores):
    from cockpit.core.git import RemoteAddress
    store, projects, (a, _b, _c) = stores
    web = store.create("Web")
    store.set_members(web.id, set(), {"github.com/tester/vokabeln"})
    projects.set_remote(projects.get(a), RemoteAddress("github.com", "tester", "Vokabeln"), None)
    store.adopt(projects.all())
    assert store.membership() == {a: web.id} and store.remote_membership() == {}


def test_remote_repo_in_collection(window, qtbot):
    win, web = web_window(window)
    repos = add_remote_repos(win.services, "Vokabeln", "Blog")
    store = win.services.collections
    store.set_members(web.id, {project_id(win, "Webseite")}, {repos["Vokabeln"].address.key})
    win.reload_projects(refresh=False)
    texts = win.project_list.texts()
    assert "Sammlung Web, 2 Projekte" in texts
    assert not any(t.startswith("Vokabeln") for t in texts)
    assert any(t.startswith("Blog, nur auf GitHub") for t in texts)
    assert win.project_list.select(Target.REMOTE_REPO, repos["Vokabeln"].id)   # öffnet
    assert win.project_list.opened_collection_id == web.id
    assert current_text(win).startswith("Vokabeln, nur auf GitHub")


def test_members_dialog_offers_remote_repos(window, qtbot):
    win, web = web_window(window)
    add_remote_repos(win.services, "Vokabeln")
    win.reload_projects(refresh=False)
    win.project_list.select(Target.COLLECTION, web.id)

    def check_vokabeln(dialog):
        texts = [i.text() for i in dialog.items()]
        assert "Vokabeln, nur auf GitHub" in texts
        item = dialog.items()[texts.index("Vokabeln, nur auf GitHub")]
        item.setCheckState(Qt.CheckState.Checked)
        dialog.accept()
    close_dialogs_later(qtbot, check_vokabeln)
    win.run_entry(win.current_entries()[0])
    assert win.services.collections.remote_members(web.id) == {"github.com/tester/vokabeln"}
    assert current_text(win) == "Sammlung Web, 2 Projekte"


def test_where_text():
    from cockpit.core.git import RemoteAddress
    from cockpit.core.projects import Project
    from cockpit.ui.collections_flow import where_text
    local = Project(1, "A", Path("x"), Path("x/Code"), None)
    assert where_text(local) == "nur auf dem Rechner"
    online = Project(1, "A", Path("x"), Path("x/Code"), None,
                     remote=RemoteAddress("github.com", "t", "A"))
    assert where_text(online) == "auf dem Rechner und auf GitHub"


# -- Nachtrag: Stand der Sammlung -------------------------------------------------------------
def status_for(pid, pending=0):
    from cockpit.core.git import RepoStatus
    from cockpit.core.project_status import ProjectStatus
    return ProjectStatus(pid, RepoStatus(is_repo=True, remote_url="https://github.com/t/x.git"),
                         pending=pending)


def test_collection_line_says_if_something_is_open(window):
    win = window(names=("A", "B", "C"))
    store = win.services.collections
    web = store.create("Web")
    store.set_members(web.id, {project_id(win, "A"), project_id(win, "B")})
    win.reload_projects(refresh=False)
    listing = win.project_list
    row = listing.row_of(Target.COLLECTION, web.id)
    assert listing.item(row).text() == "Sammlung Web, 2 Projekte"      # Stand noch unbekannt
    listing.update_status(status_for(project_id(win, "A")))
    assert listing.item(row).text() == "Sammlung Web, 2 Projekte"      # B fehlt noch
    listing.update_status(status_for(project_id(win, "B")))
    assert listing.item(row).text() == "Sammlung Web, 2 Projekte, nichts offen"
    listing.update_status(status_for(project_id(win, "B"), pending=2))
    assert listing.item(row).text() == "Sammlung Web, 2 Projekte, Änderungen offen"
    listing.open_collection(web.id, speak=False)
    assert listing.item(0).text() == "Sammlung Web, 2 Projekte, Änderungen offen, geöffnet"


def test_open_changes_in_branch_folder_count(tmp_path):
    from cockpit.core.project_status import has_open_changes
    from cockpit.core.worktrees import Worktree
    outer = status_for(1)
    assert not has_open_changes(outer)
    tree = Worktree.__new__(Worktree)
    outer.worktrees = [(tree, status_for(1, pending=1))]
    assert has_open_changes(outer)
