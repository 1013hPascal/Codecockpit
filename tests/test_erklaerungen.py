"""Feature Erklärungen (Wunsch des Nutzers vom 25.10.2026): Zeilen ganz oben, Menüeinträge,
Knöpfe in Fenstern, Ausblenden. Die Navigation wird mit und ohne Erklärungen geprüft."""
from __future__ import annotations

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication

from cockpit.core import core_actions
from cockpit.core.actions import Target
from cockpit.features.explanations import texts
from cockpit.features.explanations.manifest import FEATURE_ID, MANIFEST, SHOWN
from cockpit.ui import common, explanations, menus
from cockpit.ui.main_window import MainWindow
from cockpit.ui.menus import AccessibleMenu
from cockpit.ui.project_list import NEW_COLLECTION_TEXT
from tests.conftest import make_project


@pytest.fixture
def window(qtbot, make_services, projects_root, monkeypatch):
    monkeypatch.setattr(MainWindow, "refresh_status", lambda self, ids=None, on_done=None: None)

    def factory(enabled=True):
        for name in ("PDF-Chat", "Tagebuch"):
            make_project(projects_root, name, exe=name == "PDF-Chat")
        services = make_services([MANIFEST])
        if not enabled:
            services.features.set_globally_enabled(FEATURE_ID, False)
        win = MainWindow(services)
        qtbot.addWidget(win)
        win.show()
        win.activateWindow()
        qtbot.waitUntil(win.isActiveWindow, timeout=3000)
        win.initial_focus()
        return win
    return factory


def texts_of(listing) -> list[str]:
    return [listing.item(r).text() for r in range(listing.count())]


def with_dialog(qtbot, action):
    """Modales Fenster nach dem Öffnen an action geben, danach schließen."""
    seen = []

    def closer():
        dialog = QApplication.activeModalWidget()
        if dialog is None:
            QTimer.singleShot(20, closer)
            return
        seen.append(dialog)
        action(dialog)
        if dialog.isVisible():
            dialog.reject()
    QTimer.singleShot(20, closer)
    return seen


def select_project(win, name):
    project = next(p for p in win.services.projects.all() if p.name == name)
    win.project_list.select(Target.PROJECT, project.id)
    return project


# -- Texte --------------------------------------------------------------------------------------
def test_titles_are_unique_and_all_shown_by_default():
    assert len(set(texts.ALL_TITLES)) == len(texts.ALL_TITLES)
    field = MANIFEST.settings[0]
    assert field.key == SHOWN and tuple(field.default) == texts.ALL_TITLES


def test_every_action_has_an_explanation(window):
    win = window()
    actions = list(core_actions.CORE_ACTIONS) + win.controller.actions()
    missing = sorted({a.id for a in actions if not texts.action_text(a.id)})
    assert missing == []
    targets = {a.target for a in actions}
    assert targets <= set(texts.TARGET_TITLES)


def test_every_menu_bar_menu_has_an_explanation(window):
    win = window()
    names = [top.text().replace("&", "") for top in win.menuBar().actions()]
    assert names and all(name in texts.MENUS for name in names)


# -- Projektliste -------------------------------------------------------------------------------
def test_project_list_starts_with_explanation_but_selection_stays_on_new_collection(window,
                                                                                     qtbot):
    win = window()
    rows = win.project_list.texts()
    assert rows[0] == texts.ROW_TEXT
    assert rows[1] == NEW_COLLECTION_TEXT
    assert win.project_list.currentRow() == 1
    qtbot.keyClick(win.project_list, Qt.Key.Key_Up)
    assert win.project_list.current_target() == (Target.EXPLANATION, None)
    qtbot.keyClick(win.project_list, Qt.Key.Key_Down)
    assert win.project_list.current_target() == (Target.NEW_COLLECTION, None)


def test_without_feature_the_list_is_unchanged(window):
    win = window(enabled=False)
    rows = win.project_list.texts()
    assert texts.ROW_TEXT not in rows
    assert rows[0] == NEW_COLLECTION_TEXT
    assert win.project_list.currentRow() == 0
    select_project(win, "PDF-Chat")
    win.refresh_actions()
    assert texts.ACTIONS_ROW not in win.actions_list.texts()
    assert win.actions_list.offset == 0


def test_enter_on_the_explanation_opens_paragraphs_and_buttons(window, qtbot):
    win = window()
    win.project_list.setCurrentRow(0)
    found = {}

    def look(dialog):
        found["title"] = dialog.windowTitle()
        found["name"] = dialog.list.accessibleName()
        found["lines"] = texts_of(dialog.list)
        found["buttons"] = [b.text() for b in (dialog.hide_button, dialog.settings_button,
                                               dialog.close_button)]
    with_dialog(qtbot, look)
    qtbot.keyClick(win.project_list, Qt.Key.Key_Return)
    assert found["title"] == "Erklärung: Projektliste"
    assert found["name"] == "Erklärung"
    assert found["lines"][0] == texts.PROJECT_LIST_TEXT[0]
    assert found["lines"][-1] == texts.CLOSING
    assert found["buttons"] == [texts.HIDE_TEXT, texts.SETTINGS_TEXT, "&Schließen"]
    assert win.project_list.current_target() == (Target.EXPLANATION, None)


def test_navigation_of_projects_still_works_with_explanation(window, qtbot):
    win = window()
    project = select_project(win, "PDF-Chat")
    qtbot.keyClick(win.project_list, Qt.Key.Key_Right)
    assert win.project_list.expanded_project_id == project.id
    qtbot.keyClick(win.project_list, Qt.Key.Key_Right)
    assert win.project_list.current_target()[0] is Target.REPOSITORY
    qtbot.keyClick(win.project_list, Qt.Key.Key_Left)
    assert win.project_list.current_target() == (Target.PROJECT, project.id)
    assert win.project_list.texts()[0] == texts.ROW_TEXT


def test_opened_collection_has_no_explanation_row(window):
    win = window()
    collection = win.services.collections.create("Webseiten")
    win.reload_projects()
    win.project_list.open_collection(collection.id, speak=False)
    assert texts.ROW_TEXT not in win.project_list.texts()
    win.project_list.close_collection(speak=False)
    assert win.project_list.texts()[0] == texts.ROW_TEXT


# -- Aktionen -----------------------------------------------------------------------------------
def test_actions_start_on_first_action_with_explanation_above(window, qtbot):
    win = window()
    select_project(win, "PDF-Chat")
    listing = win.actions_list
    assert listing.texts()[0] == texts.ACTIONS_ROW
    assert listing.currentRow() == 1
    assert listing.current_entry() is listing.entries[0]
    listing.setFocus()
    qtbot.keyClick(listing, Qt.Key.Key_Up)
    assert listing.on_explanation() and listing.current_entry() is None
    found = {}
    with_dialog(qtbot, lambda d: found.update(title=d.windowTitle(), lines=texts_of(d.list)))
    qtbot.keyClick(listing, Qt.Key.Key_Return)
    assert found["title"] == "Erklärung: Aktionen: Projektzeile"
    assert found["lines"][0] == texts.TARGET_INTROS[Target.PROJECT]
    first = listing.entries[0]
    assert any(line.startswith(first.text.removesuffix(" …") + ": ") for line in found["lines"])
    assert any(line.startswith("Weitere: ") for line in found["lines"])
    assert found["lines"][-1] == texts.CLOSING


def test_space_on_an_action_still_runs_it(window, qtbot, monkeypatch):
    win = window()
    select_project(win, "PDF-Chat")
    ran = []
    monkeypatch.setattr(win, "run_entry", lambda entry: ran.append(entry.action.id))
    win.actions_list.entryTriggered.disconnect()
    win.actions_list.entryTriggered.connect(win.run_entry)
    win.actions_list.setFocus()
    qtbot.keyClick(win.actions_list, Qt.Key.Key_Space)
    assert ran == [win.actions_list.entries[0].action.id]


def test_focus_action_lands_on_the_right_row(window):
    win = window()
    project = select_project(win, "PDF-Chat")
    assert win.focus_action(project.id, "open_project_dir")
    assert win.actions_list.current_entry().action.id == "open_project_dir"


def test_keep_selection_stays_on_explanation(window):
    win = window()
    select_project(win, "PDF-Chat")
    win.actions_list.setCurrentRow(0)
    win.refresh_actions(keep_selection=True)
    assert win.actions_list.on_explanation()


# -- Ausblenden und Einstellungen ---------------------------------------------------------------
def test_hide_removes_only_this_explanation(window, qtbot):
    win = window()
    win.project_list.setCurrentRow(0)
    with_dialog(qtbot, lambda d: d.hide_button.click())
    qtbot.keyClick(win.project_list, Qt.Key.Key_Return)
    shown = win.services.features.setting(FEATURE_ID, SHOWN)
    assert texts.PROJECT_LIST not in shown
    assert len(shown) == len(texts.ALL_TITLES) - 1
    assert texts.ROW_TEXT not in win.project_list.texts()
    select_project(win, "PDF-Chat")
    assert win.actions_list.texts()[0] == texts.ACTIONS_ROW        # andere bleiben


def test_turning_the_feature_off_removes_all_rows(window):
    win = window()
    win.services.features.set_globally_enabled(FEATURE_ID, False)
    win.refresh_explanations()
    assert texts.ROW_TEXT not in win.project_list.texts()
    select_project(win, "PDF-Chat")
    assert texts.ACTIONS_ROW not in win.actions_list.texts()
    win.services.features.set_globally_enabled(FEATURE_ID, True)
    win.refresh_explanations()
    assert win.project_list.texts()[0] == texts.ROW_TEXT


def test_settings_button_opens_the_feature_settings(window, qtbot):
    win = window()
    dialog = explanations.ExplanationDialog(win.explainer, "Menü Datei", ["Ein Satz."], win)
    qtbot.addWidget(dialog)
    seen = with_dialog(qtbot, lambda d: None)
    dialog.settings_button.click()
    assert seen and seen[0].windowTitle() == "Einstellungen: Erklärungen"


# -- Menüs --------------------------------------------------------------------------------------
def menu_named(win, name):
    return next(top.menu() for top in win.menuBar().actions()
                if top.text().replace("&", "") == name)


def test_menu_gets_explanation_on_top(window):
    win = window()
    menu = menu_named(win, "Datei")
    menu.aboutToShow.emit()
    first = menu.actions()[0]
    assert first.text() == texts.ENTRY_TEXT and first.isVisible()
    assert menu.actions()[1].isSeparator()
    menu.aboutToShow.emit()                                     # nicht doppelt
    assert [a.text() for a in menu.actions()].count(texts.ENTRY_TEXT) == 1


def test_menu_explanation_hidden_without_feature(window):
    win = window(enabled=False)
    menu = menu_named(win, "Datei")
    menu.aboutToShow.emit()
    assert texts.ENTRY_TEXT not in [a.text() for a in menu.actions()]


def test_menu_explanation_follows_the_setting(window):
    win = window()
    menu = menu_named(win, "Hilfe")
    menu.aboutToShow.emit()
    win.explainer.hide("Menü Hilfe")
    menu.aboutToShow.emit()
    assert not menu.actions()[0].isVisible()


def test_menu_entry_opens_the_menu_explanation(window, qtbot):
    win = window()
    menu = menu_named(win, "Datei")
    menu.aboutToShow.emit()
    found = {}
    with_dialog(qtbot, lambda d: found.update(title=d.windowTitle(), lines=texts_of(d.list)))
    menu.actions()[0].trigger()
    assert found["title"] == "Erklärung: Menü Datei"
    assert found["lines"][0] == texts.MENUS["Datei"][0]


def test_context_menu_explanation_runs_no_action(window, monkeypatch):
    win = window()
    select_project(win, "PDF-Chat")
    ran = []
    monkeypatch.setattr(win, "run_entry", lambda entry: ran.append(entry))
    shown = []

    def fake_exec(menu, *args):
        menu.aboutToShow.emit()
        shown.append(menu.actions()[0].text())
        return menu._explanation_action                         # Eintrag "Erklärung …" gewählt
    monkeypatch.setattr(AccessibleMenu, "exec", fake_exec)
    monkeypatch.setattr(win.explainer, "show", lambda *args: None)
    win.show_context_menu(win.project_list.rect().center())
    assert shown == [texts.ENTRY_TEXT]
    assert ran == []


# -- Fenster ------------------------------------------------------------------------------------
def tab_chain(dialog):
    """Fokussierbare Elemente in der Tab-Folge, vom ersten bis zum letzten."""
    chain, widget = [], dialog.nextInFocusChain()
    while widget is not dialog and len(chain) < 200:
        if (widget.focusPolicy() & Qt.FocusPolicy.TabFocus) and widget.isVisibleTo(dialog) \
                and widget.isEnabled():
            chain.append(widget)
        widget = widget.nextInFocusChain()
    return chain


def test_dialog_gets_explanation_button_last_in_tab_order(window, qtbot):
    from cockpit.ui.settings_dialog import SettingsDialog
    win = window()
    dialog = SettingsDialog(win.services.settings, win)
    qtbot.addWidget(dialog)
    dialog.show()
    button = dialog.explanation_button
    assert button.text() == texts.ENTRY_TEXT
    assert not button.autoDefault() and button.isVisible()
    assert tab_chain(dialog)[-1] is button
    found = {}
    with_dialog(qtbot, lambda d: found.update(title=d.windowTitle()))
    button.click()
    assert found["title"] == "Erklärung: Fenster Grundeinstellungen"


def test_dialog_without_feature_has_no_button(window, qtbot):
    from cockpit.ui.settings_dialog import SettingsDialog
    win = window(enabled=False)
    dialog = SettingsDialog(win.services.settings, win)
    qtbot.addWidget(dialog)
    dialog.show()
    assert not hasattr(dialog, "explanation_button")


def test_hooks_are_removed_when_the_window_closes(window):
    win = window()
    assert win.explainer.on_menu in menus.SHOW_HOOKS
    win.close()
    assert win.explainer.on_menu not in menus.SHOW_HOOKS
    assert win.explainer.on_dialog not in common.SHOW_HOOKS
