"""Schnellnavigation, Befehlssuche (Strg+K) und Tastenhinweise (Strg+F1), Wunsch des Nutzers vom
07.10.2026. Projekte sind kleine Ordner ohne Git. Keine Plattform, keine Geheimnisse.
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QCheckBox, QLineEdit, QPlainTextEdit, QPushButton

from cockpit.core.actions import Target
from cockpit.ui import main_window as main_window_module
from cockpit.ui import quick_nav
from cockpit.ui.menus import AccessibleMenu
from tests.conftest import make_project, said


def window_with_project(qtbot, make_services, projects_root):
    from tests.test_phase10f import window
    services = make_services()
    project = services.projects.add(make_project(projects_root, "Tagebuch", exe=True))
    win = window(qtbot, services)
    return services, win, project


# -- Schnellnavigation -----------------------------------------------------------------------------
def test_quick_menu_entries(qtbot, make_services, projects_root):
    _services, win, project = window_with_project(qtbot, make_services, projects_root)
    menu = quick_nav.quick_menu(win, project.id)
    assert menu.title() == "&Schnellnavigation Tagebuch"
    assert [a.text() for a in menu.actions()] == [
        "&Hilfe, mit der KI chatten …", "&Tastenbefehle …", "&Projekt verwalten …",
        "&Repository verwalten …", "&Branches verwalten …", "Re&leases verwalten …"]


def test_context_menu_starts_with_quick_navigation_when_expanded(qtbot, make_services,
                                                                 projects_root, monkeypatch):
    _services, win, project = window_with_project(qtbot, make_services, projects_root)
    shown = []

    class Recorder(AccessibleMenu):
        def exec(self, *args):
            shown.append([a.text() for a in self.actions()])
            return None

    monkeypatch.setattr(main_window_module, "AccessibleMenu", Recorder)
    win.project_list.select(Target.PROJECT, project.id)
    win.show_context_menu(QPoint(0, 0))
    assert not shown[-1][0].startswith("&Schnellnavigation")         # zugeklappt
    win.project_list.expand(project.id, speak=False)
    win.show_context_menu(QPoint(0, 0))
    assert shown[-1][0] == "&Schnellnavigation Tagebuch"
    win.project_list.select(Target.RELEASES, project.id)
    win.show_context_menu(QPoint(0, 0))
    assert shown[-1][0] == "&Schnellnavigation Tagebuch"             # auch auf den Zeilen darunter


def test_go_to_runs_the_action_or_explains(qtbot, make_services, projects_root, monkeypatch):
    _services, win, project = window_with_project(qtbot, make_services, projects_root)
    managed = []
    monkeypatch.setattr(win.controller.project_manager, "manage", managed.append)
    quick_nav.go_to(win, project.id, Target.PROJECT, "manage_project")
    assert managed and managed[0].project.id == project.id
    quick_nav.go_to(win, project.id, Target.REPOSITORY, "manage_repo")    # ohne GitHub
    assert said("Das geht bei diesem Projekt nicht, zum Beispiel ohne Repository auf GitHub.")
    assert win.project_list.current_target() == (Target.REPOSITORY, project.id)
    quick_nav.go_to(win, project.id, Target.RELEASES, "")
    assert win.project_list.current_target() == (Target.RELEASES, project.id)
    assert win.actions_list.hasFocus() or win.focusWidget() is win.actions_list


# -- Befehlssuche ----------------------------------------------------------------------------------
def test_command_search_filters_and_runs(qtbot, make_services, projects_root):
    _services, win, project = window_with_project(qtbot, make_services, projects_root)
    win.project_list.select(Target.PROJECT, project.id)
    commands = quick_nav.menu_commands(win)
    assert ("Menü Hilfe: Befehl suchen …" in [c[0] for c in commands])
    dialog = quick_nav.CommandSearchDialog(win.current_entries(), commands, win)
    qtbot.addWidget(dialog)
    assert dialog.edit.accessibleName() == "Suchen" and dialog.list.accessibleName() == "Treffer"
    dialog.edit.setText("verwalt")
    texts = [dialog.list.item(i).text() for i in range(dialog.list.count())]
    assert texts[0] == "Projekt verwalten …"
    assert "Menü KI: KI-Verwaltung …" in texts
    dialog.edit.setText("gibt es nicht")
    assert dialog.list.item(0).text() == "Keine Treffer."
    dialog.edit.setText("ki verwaltung")
    dialog.run()
    assert dialog.chosen.text() == "KI-&Verwaltung …"


def test_arrows_in_the_search_field_choose(qtbot, make_services, projects_root):
    _services, win, _project = window_with_project(qtbot, make_services, projects_root)
    dialog = quick_nav.CommandSearchDialog([], quick_nav.menu_commands(win), win)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.edit.setFocus()
    qtbot.keyClick(dialog.edit, Qt.Key.Key_Down)
    assert dialog.list.currentRow() == 1
    assert said(dialog.list.item(1).text())


# -- Tastenhinweise ------------------------------------------------------------------------------
def test_key_hints_follow_the_row(qtbot, make_services, projects_root):
    _services, win, project = window_with_project(qtbot, make_services, projects_root)
    listing = win.project_list
    listing.select(Target.PROJECT, project.id)
    assert quick_nav.key_hint(listing, win).startswith("Pfeil rechts oder Enter klappt auf")
    assert "Schnellnavigation" in listing.toolTip()
    listing.select(Target.LIST_FILTER, None)
    assert quick_nav.key_hint(listing, win).startswith("Enter öffnet die Auswahl")
    listing.select(Target.RELEASES, project.id)
    assert quick_nav.key_hint(listing, win) == quick_nav.CHILD_HINT
    assert quick_nav.key_hint(win.actions_list, win).startswith("Enter oder Leertaste führt")


def test_key_hints_for_widgets(qtbot):
    box, button, line = QCheckBox("A"), QPushButton("B"), QLineEdit()
    output = QPlainTextEdit()
    output.setReadOnly(True)
    for widget in (box, button, line, output):
        qtbot.addWidget(widget)
    assert quick_nav.key_hint(box).startswith("Leertaste hakt an")
    assert quick_nav.key_hint(button).startswith("Enter oder Leertaste drückt")
    assert quick_nav.key_hint(line).startswith("Text eingeben, Enter bestätigt")
    assert quick_nav.key_hint(output).startswith("Pfeiltasten lesen")
    assert quick_nav.key_hint(None) == "Kein Element hat den Fokus."


def test_ctrl_f1_says_the_keys(qtbot, make_services, projects_root):
    _services, win, project = window_with_project(qtbot, make_services, projects_root)
    win.project_list.select(Target.PROJECT, project.id)
    win.show()
    win.project_list.setFocus()
    qtbot.waitUntil(lambda: win.project_list.hasFocus(), timeout=2000)
    win.announce_keys()
    assert said("Tasten hier: Pfeil rechts oder Enter klappt auf")
