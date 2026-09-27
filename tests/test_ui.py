"""Oberfläche: Barrierefreiheit, Tastatur, Projektliste, Aktionen, Dialoge."""
from __future__ import annotations

import re
import shutil

import pytest
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QLineEdit,
                               QListWidget, QPlainTextEdit, QPushButton, QWidget)

from cockpit.core import core_actions
from cockpit.core.actions import Target
from cockpit.core.features import settings_fields as sf
from cockpit.ui import main_window as mw
from cockpit.ui.announcer import announcer
from cockpit.ui.error_dialog import ErrorDialog
from cockpit.ui.form_builder import FormError, SettingsForm
from cockpit.ui.main_window import MainWindow
from cockpit.ui.project_list import ADD_LOCAL_TEXT
from cockpit.ui.settings_dialog import SettingsDialog
from tests.conftest import FAKE_TOKEN, make_project, said


@pytest.fixture
def window(qtbot, make_services, projects_root, monkeypatch):
    """Hauptfenster ohne Abfrage des Stands im Hintergrund, damit die Zeilen nur den Namen zeigen.
    Den Stand prüfen die Tests in test_phase5a.py."""
    monkeypatch.setattr(MainWindow, "refresh_status", lambda self, ids=None, on_done=None: None)

    def factory(names=("PDF-Chat", "Tagebuch"), exe=("PDF-Chat",)):
        for name in names:
            make_project(projects_root, name, exe=name in exe)
        win = MainWindow(make_services())
        qtbot.addWidget(win)
        win.show()
        win.activateWindow()
        qtbot.waitUntil(win.isActiveWindow, timeout=3000)
        win.initial_focus()
        return win
    return factory


def show_active(qtbot, widget):
    """Fenster zeigen und aktivieren, damit der Fokus wie in echt gesetzt wird."""
    widget.show()
    widget.activateWindow()
    qtbot.waitUntil(widget.isActiveWindow, timeout=3000)


def press(qtbot, widget, key, modifier=Qt.KeyboardModifier.NoModifier):
    qtbot.keyClick(widget, key, modifier)


def current_text(win: MainWindow) -> str:
    return win.project_list.currentItem().text()


def select_project(win: MainWindow, name: str) -> None:
    project = next(p for p in win.services.projects.all() if p.name == name)
    win.project_list.select(Target.PROJECT, project.id)


def close_dialogs_later(qtbot, action=lambda d: d.reject()):
    """Modalen Dialog nach dem Öffnen schließen, damit exec() zurückkehrt."""
    def closer():
        dialog = QApplication.activeModalWidget()
        if dialog is None:
            QTimer.singleShot(20, closer)
            return
        action(dialog)
    QTimer.singleShot(20, closer)


# -- Allgemeine Barrierefreiheit ------------------------------------------------------------
def test_every_focusable_control_has_a_name(window):
    win = window()
    for widget in win.findChildren(QWidget):
        if widget.focusPolicy() != Qt.FocusPolicy.NoFocus and widget.isVisibleTo(win) \
                and isinstance(widget, (QListWidget, QPlainTextEdit, QLineEdit)) \
                or widget in (win.project_list, win.actions_list):
            assert widget.accessibleName(), f"{type(widget).__name__} ohne Namen"
    assert win.project_list.accessibleName() == "Projekte"
    assert win.actions_list.accessibleName() == "Aktionen"
    assert win.status_label.accessibleName() == "Status"


def test_no_widget_has_an_accessible_description(window):
    """Braillezeile: nur Name und Rolle, keine Beschreibung."""
    win = window()
    for widget in win.findChildren(QWidget):
        assert widget.accessibleDescription() == "", widget.accessibleName()


def test_no_fixed_colors(window):
    win = window()
    for widget in [win, *win.findChildren(QWidget)]:
        assert "color" not in widget.styleSheet().lower()


def test_menu_bar_order_and_unique_mnemonics(window):
    win = window()
    titles = [a.text() for a in win.menuBar().actions()]
    assert [t.replace("&", "") for t in titles] == ["Datei", "Features", "KI", "Konten",
                                                    "Einstellungen", "Hilfe"]
    keys = [re.search(r"&(\w)", t).group(1).lower() for t in titles]
    assert len(keys) == len(set(keys))
    for top in win.menuBar().actions():
        menu = top.menu()
        assert menu.accessibleName() == top.text().replace("&", "")
        inner = [re.search(r"&(\w)", a.text()).group(1).lower()
                 for a in menu.actions() if not a.isSeparator()]
        assert len(inner) == len(set(inner)), top.text()


def test_help_menu_entries_and_shortcuts(window):
    win = window()
    help_menu = win.menuBar().actions()[-1].menu()
    entries = {a.text().replace("&", ""): a.shortcut().toString()
               for a in help_menu.actions() if not a.isSeparator()}
    assert entries["Tastenkürzel"] == "F1"
    assert entries["Letzte Meldung wiederholen"] == "Ctrl+Shift+M"
    assert entries["Meldungen …"] == "Ctrl+Shift+L"
    assert "Git installieren …" in entries
    assert "GitHub-Token erstellen …" in entries
    assert "Über CodeCockpit" in entries


def test_shortcut_list_mentions_every_shortcut(window):
    win = window()
    for action in win.actions():
        shortcut = action.shortcut().toString()
        if shortcut:
            readable = shortcut.replace("Ctrl", "Strg").replace("Shift", "Umschalt")
            assert any(readable in line for line in mw.SHORTCUTS), readable


# -- Tab-Reihenfolge und Bereiche -------------------------------------------------------------
def test_tab_circle_list_actions_list(window, qtbot):
    win = window()
    assert win.project_list.hasFocus()
    press(qtbot, win.project_list, Qt.Key.Key_Tab)
    assert win.actions_list.hasFocus()
    press(qtbot, win.actions_list, Qt.Key.Key_Tab)
    assert win.project_list.hasFocus()


def test_shift_tab_returns_to_the_same_list_entry(window, qtbot):
    win = window()
    select_project(win, "Tagebuch")
    press(qtbot, win.project_list, Qt.Key.Key_Tab)
    press(qtbot, win.actions_list, Qt.Key.Key_Backtab, Qt.KeyboardModifier.ShiftModifier)
    assert win.project_list.hasFocus()
    assert current_text(win) == "Tagebuch"


def test_area_shortcuts(window, qtbot):
    win = window()
    win.focus_actions()
    assert win.actions_list.hasFocus()
    win.cycle_area(+1)
    assert win.project_list.hasFocus()
    win.cycle_area(-1)
    assert win.actions_list.hasFocus()


# -- Projektliste ----------------------------------------------------------------------------
def test_list_starts_with_new_project_and_lists_projects(window):
    win = window()
    texts = win.project_list.texts()
    assert texts[:2] == [ADD_LOCAL_TEXT, "Projekt von GitHub herunterladen"]
    assert sorted(texts[2:]) == ["PDF-Chat", "Tagebuch"]          # zugeklappt, keine Unterordner
    assert current_text(win) == ADD_LOCAL_TEXT
    assert win.project_list.accessibleName() == "Projekte"


def test_right_expands_and_says_so(window, qtbot):
    win = window()
    select_project(win, "PDF-Chat")
    press(qtbot, win.project_list, Qt.Key.Key_Right)
    texts = win.project_list.texts()
    row = texts.index("PDF-Chat, ausgeklappt")
    assert texts[row + 1:row + 3] == ["Code", "Exe, leer"]
    assert current_text(win) == "PDF-Chat, ausgeklappt"            # Fokus bleibt
    assert announcer.last_text == "Ausgeklappt, 2 Unterordner."


@pytest.mark.parametrize("key", [Qt.Key.Key_Space, Qt.Key.Key_Return])
def test_space_and_enter_toggle_a_project(window, qtbot, key):
    win = window()
    select_project(win, "Tagebuch")
    press(qtbot, win.project_list, key)
    assert current_text(win) == "Tagebuch, ausgeklappt"
    assert announcer.last_text == "Ausgeklappt, 1 Unterordner."
    press(qtbot, win.project_list, key)
    assert current_text(win) == "Tagebuch"
    assert "Code" not in win.project_list.texts()
    assert announcer.last_text == "Zugeklappt."


def test_expanding_one_collapses_the_other(window, qtbot):
    win = window()
    select_project(win, "PDF-Chat")
    press(qtbot, win.project_list, Qt.Key.Key_Right)
    select_project(win, "Tagebuch")
    press(qtbot, win.project_list, Qt.Key.Key_Right)
    texts = win.project_list.texts()
    assert "PDF-Chat" in texts and "Tagebuch, ausgeklappt" in texts
    assert texts.count("Code") == 1
    assert current_text(win) == "Tagebuch, ausgeklappt"


def test_right_goes_to_child_left_collapses_back_to_project(window, qtbot):
    win = window()
    select_project(win, "PDF-Chat")
    press(qtbot, win.project_list, Qt.Key.Key_Right)
    press(qtbot, win.project_list, Qt.Key.Key_Right)
    assert current_text(win) == "Code"
    press(qtbot, win.project_list, Qt.Key.Key_Down)
    assert current_text(win) == "Exe, leer"
    press(qtbot, win.project_list, Qt.Key.Key_Left)
    assert current_text(win) == "PDF-Chat"
    assert win.project_list.texts().count("Code") == 0              # wieder die normale Liste
    assert announcer.last_text == "Zugeklappt."


def test_every_project_stays_reachable_after_collapsing(window, qtbot):
    """Rückmeldung aus Phase 2: Nach dem Zuklappen waren Projekte nicht mehr erreichbar."""
    win = window(names=("A", "B", "C"))
    select_project(win, "B")
    press(qtbot, win.project_list, Qt.Key.Key_Right)
    press(qtbot, win.project_list, Qt.Key.Key_Right)
    press(qtbot, win.project_list, Qt.Key.Key_Left)
    win.project_list.setCurrentRow(0)
    seen = [current_text(win)]
    for _ in range(5):
        press(qtbot, win.project_list, Qt.Key.Key_Down)
        seen.append(current_text(win))
    assert {ADD_LOCAL_TEXT, "A", "B", "C"} <= set(seen)


def test_left_on_expanded_project_collapses(window, qtbot):
    win = window()
    select_project(win, "PDF-Chat")
    press(qtbot, win.project_list, Qt.Key.Key_Right)
    press(qtbot, win.project_list, Qt.Key.Key_Left)
    assert current_text(win) == "PDF-Chat"
    assert "Code" not in win.project_list.texts()


def test_missing_folder_is_named_and_cannot_expand(window, qtbot, projects_root):
    win = window()
    shutil.rmtree(projects_root / "Tagebuch")
    win.reload_projects()
    assert "Tagebuch, Ordner nicht gefunden" in win.project_list.texts()
    select_project(win, "Tagebuch")
    press(qtbot, win.project_list, Qt.Key.Key_Return)
    assert announcer.last_text == "Der Ordner wurde nicht gefunden."
    assert win.project_list.hasFocus()


def test_rescan_keeps_selection_and_expanded_project(window, qtbot, projects_root):
    win = window()
    select_project(win, "PDF-Chat")
    press(qtbot, win.project_list, Qt.Key.Key_Right)
    press(qtbot, win.project_list, Qt.Key.Key_Right)
    make_project(projects_root, "Bildbeschreiber")
    win.rescan()
    assert "Bildbeschreiber" in win.project_list.texts()
    assert current_text(win) == "Code"
    assert "PDF-Chat, ausgeklappt" in win.project_list.texts()
    assert said("Neu: Bildbeschreiber.")


def test_exe_label_names_file_and_date(window, projects_root):
    win = window()
    (projects_root / "PDF-Chat" / "Exe" / "PDF-Chat.exe").write_text("x")
    win.reload_projects()
    select_project(win, "PDF-Chat")
    win.project_list.expand(win.project_list.current_target()[1])
    assert any(t.startswith("Exe, PDF-Chat.exe, erstellt am ") for t in win.project_list.texts())


# -- Aktionen -------------------------------------------------------------------------------
def test_actions_follow_the_tree_selection(window):
    win = window()
    assert win.actions_list.texts() == ["Projekt vom Rechner hinzufügen …"]
    win.project_list.setCurrentRow(1)
    assert win.actions_list.texts() == [
        "Projekt von GitHub herunterladen …, nicht verfügbar: Es ist noch kein Konto bei einer "
        "Plattform eingerichtet."]
    select_project(win, "PDF-Chat")
    assert win.actions_list.texts() == [
        "Projekt neu einlesen",
        "Features dieses Projekts …, nicht verfügbar: Es ist kein Feature eingeschaltet. Das "
        "geht im Menü Features.",
        "Terminal …", "Projektordner öffnen", "Aus der Liste entfernen …"]
    project = next(p for p in win.services.projects.all() if p.name == "PDF-Chat")
    win.project_list.select(Target.EXE, project.id)
    assert win.actions_list.texts() == [
        "Projekt neu einlesen", "Exe starten, nicht verfügbar: Im Ordner Exe liegt keine Exe.",
        "Exe-Ordner öffnen"]


def test_unavailable_action_announces_reason(window, qtbot):
    win = window()
    win.project_list.setCurrentRow(1)
    win.focus_actions()
    press(qtbot, win.actions_list, Qt.Key.Key_Return)
    assert announcer.last_text == ("Projekt von GitHub herunterladen … ist nicht verfügbar. "
                                   "Es ist noch kein Konto bei einer Plattform eingerichtet.")


def test_enter_and_space_run_actions(window, qtbot, monkeypatch):
    opened = []
    monkeypatch.setattr(core_actions, "open_path", opened.append)
    win = window()
    select_project(win, "PDF-Chat")
    win.focus_actions()
    press(qtbot, win.actions_list, Qt.Key.Key_Down)          # oben steht Projekt neu einlesen
    press(qtbot, win.actions_list, Qt.Key.Key_Down)          # dann Features dieses Projekts
    press(qtbot, win.actions_list, Qt.Key.Key_Down)          # dann Terminal
    press(qtbot, win.actions_list, Qt.Key.Key_Return)
    press(qtbot, win.actions_list, Qt.Key.Key_Space)
    assert len(opened) == 2 and opened[0].name == "PDF-Chat"
    assert announcer.last_text == "Projektordner wird geöffnet."


def test_enter_on_code_without_default_moves_to_actions(window, qtbot):
    win = window()
    project = next(p for p in win.services.projects.all() if p.name == "PDF-Chat")
    win.project_list.select(Target.CODE, project.id)
    win.project_list.setFocus()
    press(qtbot, win.project_list, Qt.Key.Key_Return)
    assert win.actions_list.hasFocus()


def test_enter_on_exe_starts_it(window, qtbot, monkeypatch, projects_root):
    started = []
    monkeypatch.setattr(core_actions, "start_program", started.append)
    win = window()
    (projects_root / "PDF-Chat" / "Exe" / "PDF-Chat.exe").write_text("x")
    win.reload_projects()
    project = next(p for p in win.services.projects.all() if p.name == "PDF-Chat")
    win.project_list.select(Target.EXE, project.id)
    press(qtbot, win.project_list, Qt.Key.Key_Return)
    assert started[0].name == "PDF-Chat.exe"
    assert said("PDF-Chat.exe wird gestartet.")


def test_failing_action_shows_error_dialog(window, monkeypatch, qtbot):
    def broken(path):
        raise OSError(f"[WinError 193] keine Anwendung {FAKE_TOKEN}")
    monkeypatch.setattr(core_actions, "start_program", broken)
    shown = []
    monkeypatch.setattr(mw, "show_error", lambda *args: shown.append(args))
    win = window()
    project = next(p for p in win.services.projects.all() if p.name == "PDF-Chat")
    (project.exe_dir / "PDF-Chat.exe").write_text("x")
    win.project_list.select(Target.EXE, project.id)
    win.run_default_action()
    assert shown[0][2] == "Exe starten hat nicht geklappt."
    assert said("Exe starten hat nicht geklappt.")


def test_context_menu_offers_the_same_actions(window, qtbot, monkeypatch):
    win = window()
    select_project(win, "PDF-Chat")
    seen = []

    def fake_exec(menu, position):
        seen.extend(a.text() for a in menu.actions())
        assert menu.accessibleName() == "Aktionen"
        return None
    monkeypatch.setattr(mw.AccessibleMenu, "exec", fake_exec)
    win.show_context_menu(win.project_list.mapToGlobal(win.project_list.rect().center()))
    assert seen == win.actions_list.texts()
    assert win.project_list.hasFocus()


# -- Meldungen ------------------------------------------------------------------------------
def test_startup_announces_projects(window):
    win = window()
    win.startup()
    assert said("CodeCockpit bereit. 2 Projekte.")


def test_missing_git_is_announced(window, monkeypatch):
    monkeypatch.setattr(mw.git, "find_git", lambda: None)
    win = window()
    win.startup()
    message = announcer.messages[-1]
    assert message.urgent and "Git wurde nicht gefunden" in message.text


def test_messages_go_to_status_and_can_be_repeated(window, monkeypatch):
    win = window()
    sent = []
    monkeypatch.setattr(announcer, "_send", lambda text, urgent: sent.append(text))
    announcer.announce("Erste Meldung.")
    announcer.announce("Zweite Meldung.")
    assert win.status_label.text() == "Zweite Meldung."
    announcer.repeat_last()
    assert sent[-1] == "Zweite Meldung."
    assert len(announcer.messages) == 2                 # Wiederholen speichert nicht erneut
    assert [m.text for m in announcer.newest_first()] == ["Zweite Meldung.", "Erste Meldung."]


def test_only_fifty_messages_are_kept():
    for number in range(60):
        announcer.announce(f"Meldung {number}")
    assert len(announcer.messages) == 50
    assert announcer.newest_first()[0].text == "Meldung 59"


def test_messages_dialog_lists_newest_first(window, qtbot):
    from cockpit.ui.messages_dialog import MessagesDialog
    announcer.announce("Alt.")
    announcer.announce("Neu.")
    dialog = MessagesDialog(announcer.newest_first())
    qtbot.addWidget(dialog)
    assert dialog.list.item(0).text().startswith("Neu. ")
    assert dialog.list.accessibleName() == "Meldungen"


# -- Dialoge --------------------------------------------------------------------------------
def test_error_dialog_details_get_focus_and_hide_secrets(qtbot):
    dialog = ErrorDialog("Fehler", "Es ging nicht. Bitte erneut versuchen.",
                         f"Traceback\nZeile mit {FAKE_TOKEN}")
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    assert dialog.message.text() == "Es ging nicht. Bitte erneut versuchen."
    assert dialog.ok_button.hasFocus()
    assert not dialog.details.isVisible()
    dialog.details_button.click()
    assert dialog.details.isVisible() and dialog.details.hasFocus()
    lines = [dialog.details.item(r).text() for r in range(dialog.details.count())]
    assert lines[0] == "Traceback" and FAKE_TOKEN not in lines[1]
    assert dialog.details_button.text() == "&Details ausblenden"
    assert not dialog.findChildren(QPlainTextEdit)                 # keine Eingabefelder


def test_error_dialog_without_details_has_no_button(qtbot):
    dialog = ErrorDialog("Fehler", "Kurz.")
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    assert not dialog.details_button.isVisible()
    assert dialog.ok_button.isDefault()


def test_form_builder_names_and_checks_fields(qtbot, tmp_path):
    fields = [sf.Text("name", "Name", required=True), sf.YesNo("private", "Privat", True),
              sf.Choice("lic", "Lizenz", options=("MIT", "GPL")),
              sf.Number("days", "Tage", 7, minimum=1, maximum=30),
              sf.MultiChoice("langs", "Sprachen", ("Englisch",),
                             options=("Englisch", "Deutsch")),
              sf.Folder("root", "Hauptordner", str(tmp_path))]
    form = SettingsForm(fields)
    qtbot.addWidget(form)
    names = {w.accessibleName() for w in form.findChildren(QWidget) if w.accessibleName()}
    assert {"Name", "Privat", "Lizenz", "Tage", "Sprachen", "Hauptordner",
            "Ordner wählen"} <= names
    assert form.findChildren(QCheckBox)[0].isChecked()
    with pytest.raises(FormError) as info:
        form.values()
    assert info.value.key == "name"
    form.fields["name"].set("Test")
    values = form.values()
    assert values["langs"] == ["Englisch"] and values["days"] == 7 and values["lic"] == "MIT"


def test_multichoice_list_toggles_with_space(qtbot):
    form = SettingsForm([sf.MultiChoice("langs", "Sprachen", options=("Englisch", "Deutsch"))])
    qtbot.addWidget(form)
    form.show()
    listing = form.fields["langs"].focus
    listing.setFocus()
    listing.setCurrentRow(1)
    qtbot.keyClick(listing, Qt.Key.Key_Space)
    assert form.values()["langs"] == ["Deutsch"]


def test_settings_dialog_saves(qtbot, make_services, tmp_path):
    services = make_services()
    dialog = SettingsDialog(services.settings)
    qtbot.addWidget(dialog)
    dialog.form.fields["git_name"].set("1013hPascal")
    dialog.form.fields["git_email"].set("94653295+1013hPascal@users.noreply.github.com")
    dialog.save()
    assert dialog.result() == QDialog.DialogCode.Accepted
    settings = services.settings.load()
    assert settings.git_name == "1013hPascal"
    assert settings.git_email.endswith("@users.noreply.github.com")


def test_settings_dialog_error_puts_focus_in_the_field(qtbot, make_services, monkeypatch):
    import cockpit.ui.settings_dialog as sd
    errors = []
    monkeypatch.setattr(sd, "show_error", lambda parent, title, text: errors.append(text))
    services = make_services()
    dialog = SettingsDialog(services.settings)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    dialog.form.fields["git_email"].set("falsch")
    dialog.save()
    assert errors == ["Bitte eine gültige E-Mail-Adresse eingeben."]
    assert dialog.form.fields["git_email"].focus.hasFocus()
    assert dialog.result() != QDialog.DialogCode.Accepted


def test_settings_dialog_first_field_has_focus_and_buttons_are_german(qtbot, make_services):
    dialog = SettingsDialog(make_services().settings)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    assert dialog.form.fields["projects_root"].focus.hasFocus()
    texts = [b.text() for b in dialog.findChildren(QPushButton)]
    assert "&Speichern" in texts and "Abbrechen" in texts
    assert dialog.findChildren(QComboBox)[0].accessibleName() == \
        "Standard-Lizenz für neue Projekte"


def test_text_windows_are_lists_with_focus(window, qtbot):
    win = window()
    for opener, expected in ((win.show_shortcuts, "Projekt ausklappen, Pfeil rechts"),
                             (win.show_git_guide, "winget install --id Git.Git -e --source winget"),
                             (win.show_about, "Datenordner: ")):
        def check(dialog, expected=expected):
            assert dialog.list.hasFocus()
            assert any(line.startswith(expected) for line in dialog.lines), expected
            assert not dialog.findChildren(QPlainTextEdit)
            dialog.accept()
        close_dialogs_later(qtbot, check)
        opener()


def test_text_to_lines_cleans_markdown():
    from cockpit.ui.text_dialog import text_to_lines
    assert text_to_lines("# Titel\n\n- Punkt\n1. Schritt\n   `befehl -x`\n**fett**") == \
        ["Titel", "Punkt", "1. Schritt", "befehl -x", "fett"]


def test_text_window_copies_the_current_line(qtbot):
    from cockpit.ui.text_dialog import TextDialog
    dialog = TextDialog("Test", ["eins", "zwei"])
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    dialog.list.setCurrentRow(1)
    qtbot.keyClick(dialog.list, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    assert QApplication.clipboard().text() == "zwei"
    assert announcer.last_text == "Zeile kopiert."


def test_text_edit_makes_real_line_breaks(qtbot):
    from cockpit.ui.common import PlainEdit
    edit = PlainEdit()
    qtbot.addWidget(edit)
    qtbot.keyClicks(edit, "eins")
    qtbot.keyClick(edit, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
    qtbot.keyClicks(edit, "zwei")
    assert edit.toPlainText() == "eins\nzwei"
    assert " " not in edit.toPlainText()
    assert edit.tabChangesFocus()


def test_asker_answers_in_gui_thread(monkeypatch, qtbot):
    from cockpit.core.flows.questions import ConfirmQuestion
    from cockpit.ui import asker as asker_module
    monkeypatch.setattr(asker_module, "confirm", lambda *args: True)
    assert asker_module.QtAsker().ask(ConfirmQuestion("Titel", "Wirklich?")) is True


def test_asker_answers_from_background_thread(monkeypatch, qtbot):
    import threading
    from cockpit.core.flows.questions import TextQuestion
    from cockpit.ui import asker as asker_module
    from PySide6.QtWidgets import QInputDialog
    monkeypatch.setattr(QInputDialog, "getText", lambda *args: ("Neue Suche", True))
    asker = asker_module.QtAsker()
    answers = []
    thread = threading.Thread(
        target=lambda: answers.append(asker.ask(TextQuestion("Commit", "Was geändert?"))))
    thread.start()
    qtbot.waitUntil(lambda: bool(answers), timeout=5000)
    thread.join(5)
    assert answers == ["Neue Suche"]


def test_testdata_are_complete(tmp_path, monkeypatch):
    from cockpit import testdata
    home, root = testdata.prepare(tmp_path / "Testdaten")
    assert (root / "PDF-Chat" / "Exe" / "PDF-Chat.exe").is_file()
    assert not (root / "Tagebuch" / "Exe").exists()
    assert (root / "Bildbeschreiber" / "Exe").is_dir()
    testdata.remove_missing_example(root)
    assert not (root / "Notizen").exists()


def test_dialogs_refocus_after_showing_and_tell_nvda(qtbot, monkeypatch):
    """Test Phase 2: Beim Öffnen aus dem Menü zeigte die Braillezeile noch den alten Fokus."""
    from cockpit.ui import common
    from cockpit.ui.text_dialog import TextDialog
    sent = []
    monkeypatch.setattr(common.QAccessible, "updateAccessibility",
                        lambda event: sent.append((event.type(), event.child())))
    dialog = TextDialog("Test", ["eins", "zwei"])
    qtbot.addWidget(dialog)
    dialog.list.setCurrentRow(1)
    show_active(qtbot, dialog)
    qtbot.waitUntil(lambda: bool(sent), timeout=2000)
    assert dialog.list.hasFocus()
    assert sent[-1] == (common.QAccessible.Event.Focus, 1)


def test_all_dialogs_use_the_refocus(qtbot, make_services):
    from cockpit.ui.common import FocusDialog
    from cockpit.ui.messages_dialog import MessagesDialog
    from cockpit.ui.text_dialog import TextDialog
    dialogs = [TextDialog("T", ["x"]), MessagesDialog([]), ErrorDialog("F", "Text."),
               SettingsDialog(make_services().settings)]
    for dialog in dialogs:
        qtbot.addWidget(dialog)
        assert isinstance(dialog, FocusDialog)
        assert dialog.initial_focus_widget is not None
