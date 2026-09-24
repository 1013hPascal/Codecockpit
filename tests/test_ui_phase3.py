"""Oberfläche Phase 3: Master-Passwort, Einrichtungsassistent, Kontenverwaltung, Tresor-Einstellungen."""
from __future__ import annotations

import re

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QWidget

from cockpit.core.accounts import find_type
from cockpit.core.secret import Secret
from cockpit.ui import accounts_dialog as ad
from cockpit.ui import password_dialogs as pd
from cockpit.ui import setup_wizard as sw
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announcer
from cockpit.ui.main_window import MainWindow
from cockpit.ui.vault_settings_dialog import VaultSettingsDialog
from cockpit.vault.vault_file import FileVault
from tests.conftest import FAKE_TOKEN, FakeVault, said
from tests.test_ui import show_active

PASSWORD = "ErfundenesMasterPasswort1"


shown_infos: list[str] = []


@pytest.fixture(autouse=True)
def no_blocking_questions(monkeypatch):
    """Rückfragen beim Schließen (zum Beispiel "Einrichtung abbrechen?") würden die Tests
    anhalten. Tests, die eine Antwort prüfen, ersetzen confirm selbst."""
    monkeypatch.setattr(sw, "confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(ad, "show_info", lambda *args, **kwargs: None)
    shown_infos.clear()
    monkeypatch.setattr("cockpit.ui.vault_settings_dialog.show_info",
                        lambda parent, title, text: shown_infos.append(text))


class FakeNewPassword:
    """Ersetzt NewPasswordDialog: gibt sofort ein Passwort zurück."""

    def __init__(self, *args, **kwargs) -> None:
        self.old_password = Secret(PASSWORD)
        self.new_password = Secret(PASSWORD)

    def exec(self) -> bool:
        return True


def errors_to(monkeypatch, module) -> list[str]:
    shown: list[str] = []
    monkeypatch.setattr(module, "show_error", lambda parent, title, text, details="":
                        shown.append(text))
    return shown


# -- Master-Passwort --------------------------------------------------------------------------
def test_unlock_dialog_wrong_then_right(qtbot, tmp_path, monkeypatch):
    vault = FileVault(tmp_path / "vault.bin")
    vault.create(Secret(PASSWORD))
    vault.lock()
    shown = errors_to(monkeypatch, pd)
    dialog = pd.UnlockDialog(vault.unlock)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    assert dialog.password.hasFocus()
    assert dialog.password.echoMode() == QLineEdit.EchoMode.Password
    assert dialog.password.accessibleName() == "Master-Passwort"
    dialog.password.setText("falsch-falsch")
    dialog.try_unlock()
    assert shown == ["Das Master-Passwort ist falsch."]
    assert dialog.password.text() == "" and dialog.password.hasFocus()
    dialog.password.setText(PASSWORD)
    dialog.try_unlock()
    assert dialog.result() == QDialog.DialogCode.Accepted and vault.is_unlocked()


def test_new_password_dialog_checks_and_clears(qtbot, monkeypatch):
    shown = errors_to(monkeypatch, pd)
    dialog = pd.NewPasswordDialog()
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    assert dialog.new.hasFocus()
    dialog.new.setText("langes-pass1")
    dialog.repeat.setText("langes-pass2")
    dialog.check()
    assert shown == ["Die beiden Passwörter stimmen nicht überein."]
    assert dialog.new.text() == "" and dialog.new.hasFocus()
    dialog.new.setText("langes-pass1")
    dialog.repeat.setText("langes-pass1")
    dialog.check()
    assert dialog.new_password.reveal() == "langes-pass1"
    assert dialog.new.text() == "" and dialog.repeat.text() == ""


def test_change_password_dialog_asks_old_first(qtbot):
    dialog = pd.NewPasswordDialog(ask_old=True)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    assert dialog.old.hasFocus()
    names = [w.accessibleName() for w in dialog.findChildren(QLineEdit)]
    assert names == ["Bisheriges Master-Passwort", "Neues Master-Passwort",
                     "Neues Passwort wiederholen"]


# -- Einrichtungsassistent ------------------------------------------------------------------
@pytest.fixture
def wizard(qtbot, make_services):
    def factory():
        services = make_services()
        dialog = sw.SetupWizard(services)
        qtbot.addWidget(dialog)
        show_active(qtbot, dialog)
        return dialog, services
    return factory


def test_wizard_pages_and_announcements(wizard, monkeypatch):
    dialog, services = wizard()
    assert [p.title for p in dialog.pages] == ["Willkommen", "Git", "Tresor",
                                               "Projekte-Hauptordner", "Git-Identität",
                                               "Zusammenfassung"]
    assert dialog.heading.text() == "Schritt 1 von 6: Willkommen"
    assert not dialog.skip_button.isVisible()
    assert not dialog.back_button.isEnabled()
    dialog.next()
    assert said("Schritt 2 von 6: Git.")
    assert dialog.skip_button.isVisible()
    dialog.next()
    assert dialog.page.title == "Tresor"
    assert not dialog.skip_button.isVisible()                  # Tresor ist Pflicht
    assert dialog.page.chosen_kind() == "windows"
    assert dialog.focusWidget() is dialog.page.text            # zuerst die Erklärung
    assert dialog.page.choice.accessibleName() == "Speicherart"
    assert [dialog.page.choice.item(r).text() for r in range(2)] == [
        "Windows-Anmeldeinformationsverwaltung (empfohlen)",
        "Verschlüsselte Tresordatei mit Master-Passwort"]
    lines = [dialog.page.text.item(r).text() for r in range(dialog.page.text.count())]
    assert any(line.startswith("Gesperrt heißt:") for line in lines)


def test_wizard_full_run_with_windows_vault(wizard, projects_root):
    dialog, services = wizard()
    dialog.next()                                            # Willkommen
    dialog.next()                                            # Git
    dialog.next()                                            # Tresor: Windows
    assert services.settings.load().vault_kind == "windows"
    dialog.next()                                            # Hauptordner
    identity = dialog.page
    identity.form.fields["git_name"].set("1013hPascal")
    identity.form.fields["git_email"].set("94653295+1013hPascal@users.noreply.github.com")
    dialog.next()
    summary = [dialog.page.list.item(r).text() for r in range(dialog.page.list.count())]
    assert "Eingerichtet: Tresor: Windows-Anmeldeinformationsverwaltung." in summary
    assert any(s.startswith("Eingerichtet: Git-Identität: 1013hPascal") for s in summary)
    assert dialog.next_button.text() == "&Fertig"
    dialog.next()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert services.settings.load().setup_done


def test_wizard_skip_is_listed_in_summary(wizard):
    dialog, services = wizard()
    for _ in range(3):
        dialog.next()
    dialog.skip()                                            # Hauptordner
    dialog.skip()                                            # Git-Identität
    summary = [dialog.page.list.item(r).text() for r in range(dialog.page.list.count())]
    assert "Übersprungen: Git-Identität. Nachholen: Menü Einstellungen, Grundeinstellungen." \
        in summary


def test_wizard_with_vault_file(wizard, monkeypatch, home):
    monkeypatch.setattr(vault_ui, "NewPasswordDialog", FakeNewPassword)
    dialog, services = wizard()
    dialog.next()
    dialog.next()
    dialog.page.choice.setCurrentRow(1)
    dialog.next()
    assert services.settings.load().vault_kind == "vault_file"
    assert (home / "vault.bin").is_file()
    assert services.vault.is_unlocked()


def test_wizard_cancelled_vault_password_stays_on_page(wizard, monkeypatch):
    class Cancelled(FakeNewPassword):
        def exec(self):
            return False
    monkeypatch.setattr(vault_ui, "NewPasswordDialog", Cancelled)
    dialog, services = wizard()
    dialog.next()
    dialog.next()
    dialog.page.choice.setCurrentRow(1)
    dialog.next()
    assert dialog.page.title == "Tresor"
    assert services.settings.load().vault_kind == ""


def test_wizard_identity_needs_both_or_skip(wizard, monkeypatch):
    shown = errors_to(monkeypatch, sw)
    dialog, _ = wizard()
    for _ in range(4):
        dialog.next()
    dialog.page.form.fields["git_name"].set("Nur Name")
    dialog.next()
    assert dialog.page.title == "Git-Identität"
    assert "Bitte Name und E-Mail-Adresse" in shown[0]


def test_wizard_cancel_asks_first(wizard, monkeypatch):
    answers = [False, True]
    monkeypatch.setattr(sw, "confirm", lambda *args, **kwargs: answers.pop(0))
    dialog, _ = wizard()
    dialog.reject()
    assert dialog.isVisible()                                 # "Weiter einrichten"
    dialog.reject()
    assert dialog.result() == QDialog.DialogCode.Rejected


def test_wizard_missing_git_offers_guide(wizard, monkeypatch):
    monkeypatch.setattr(sw.git, "find_git", lambda: None)
    dialog, _ = wizard()
    dialog.next()
    lines = [dialog.page.state.item(r).text() for r in range(dialog.page.state.count())]
    assert lines[0] == "Git wurde nicht gefunden."
    assert dialog.page.guide_button.isVisible() and dialog.page.check_button.isVisible()


def test_wizard_mnemonics_are_unique_per_page(wizard):
    dialog, _ = wizard()
    buttons = [dialog.back_button, dialog.skip_button, dialog.next_button, dialog.cancel_button]
    for page in dialog.pages:
        texts = [b.text() for b in buttons]
        texts += [w.text() for w in page.findChildren(QPushButton)]
        texts += [w.text() for w in page.findChildren(QLabel)]
        keys = [m.group(1).lower() for t in texts if (m := re.search(r"&(\w)", t))]
        assert len(keys) == len(set(keys)), (page.title, texts)


# -- Kontenverwaltung -----------------------------------------------------------------------
@pytest.fixture
def accounts(qtbot, make_services, account_adapter):
    services = make_services(vault=FakeVault())
    dialog = ad.AccountsDialog(services)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    return dialog, services, find_type("platform", account_adapter.kind)


def test_accounts_list_starts_with_new_account(accounts):
    dialog, _, _ = accounts
    assert dialog.list.item(0).text() == "Neues Konto anlegen …"
    assert dialog.list.item(dialog.list.count() - 1).text() == "Wofür sind Konten? …"
    assert dialog.list.accessibleName() == "Konten"
    assert dialog.list.hasFocus()


def test_account_edit_dialog_builds_fields_and_saves(qtbot, accounts):
    dialog, services, account_type = accounts
    edit = ad.AccountEditDialog(services, account_type)
    qtbot.addWidget(edit)
    names = [w.accessibleName() for w in edit.findChildren(QLineEdit)]
    assert names == ["Anzeigename", "Benutzername", "Serveradresse", "Team", "Token"]
    token = edit.form.fields["token"].focus
    assert token.echoMode() == QLineEdit.EchoMode.Password
    edit.form.fields["display_name"].set("GitHub privat")
    edit.form.fields["username"].set("1013hPascal")
    token.setText(FAKE_TOKEN)
    edit.save()
    assert edit.saved.display_name == "GitHub privat"
    assert services.accounts.values(edit.saved)["token"].reveal() == FAKE_TOKEN
    dialog.refresh(edit.saved.id)
    assert dialog.list.currentItem().text() == "GitHub privat, Kontotest, Plattform, 1013hPascal"


def test_account_edit_never_shows_the_secret(qtbot, accounts):
    dialog, services, account_type = accounts
    account = services.accounts.create(account_type, "A", {"username": "a",
                                                            "token": Secret(FAKE_TOKEN)})
    edit = ad.AccountEditDialog(services, account_type, account)
    qtbot.addWidget(edit)
    token = edit.form.fields["token"].focus
    assert token.text() == ""
    assert token.placeholderText() == "Leer lassen: bleibt unverändert"
    edit.save()                                               # Token bleibt
    assert services.accounts.values(account)["token"].reveal() == FAKE_TOKEN


def test_account_edit_connection_test_uses_stored_secret(qtbot, accounts, monkeypatch):
    dialog, services, account_type = accounts
    account = services.accounts.create(account_type, "A", {"username": "a",
                                                            "token": Secret(FAKE_TOKEN)})
    infos = []
    monkeypatch.setattr(ad, "show_info", lambda parent, title, text: infos.append(text))
    edit = ad.AccountEditDialog(services, account_type, account)
    qtbot.addWidget(edit)
    edit.test_connection()
    assert infos == ["Angemeldet als a."]
    assert said("Angemeldet als a.")


def test_failed_connection_test_shows_details(qtbot, accounts, monkeypatch):
    dialog, services, account_type = accounts
    errors = []
    monkeypatch.setattr(ad, "show_error", lambda parent, title, text, details="":
                        errors.append((text, details)))
    edit = ad.AccountEditDialog(services, account_type)
    qtbot.addWidget(edit)
    edit.form.fields["username"].set("a")
    edit.form.fields["token"].focus.setText("falsch-1")
    edit.test_connection()
    assert errors == [("Der Token wurde abgelehnt.", "HTTP 401")]
    assert announcer.messages[-1].urgent


def test_delete_account_asks_with_safe_default(accounts, monkeypatch):
    dialog, services, account_type = accounts
    services.accounts.create(account_type, "A", {"username": "a", "token": Secret(FAKE_TOKEN)})
    dialog.refresh()
    dialog.list.setCurrentRow(1)
    asked = []

    def fake_confirm(parent, title, text, yes="Ja", no="Nein", default_yes=False):
        asked.append((text, default_yes))
        return len(asked) > 1

    monkeypatch.setattr(ad, "confirm", fake_confirm)
    dialog.delete_current()
    assert services.accounts.all() and asked[0][1] is False
    assert "Auf der Plattform ändert sich nichts" in asked[0][0]
    dialog.delete_current()
    assert services.accounts.all() == []
    assert said("Konto A gelöscht.")


def test_delete_key_and_no_account_selected(accounts, qtbot):
    dialog, _, _ = accounts
    dialog.list.setCurrentRow(0)
    qtbot.keyClick(dialog.list, Qt.Key.Key_Delete)
    assert said("Bitte zuerst ein Konto wählen.")


def test_accounts_need_unlocked_vault(qtbot, make_services, account_adapter, tmp_path,
                                      monkeypatch):
    vault = FileVault(tmp_path / "vault.bin")
    vault.create(Secret(PASSWORD))
    services = make_services(vault=vault)
    account_type = find_type("platform", account_adapter.kind)
    vault.lock()
    unlock_calls = []

    class FakeUnlock:
        def __init__(self, unlock, parent=None):
            self.unlock = unlock

        def exec(self):
            unlock_calls.append(1)
            self.unlock(Secret(PASSWORD))
            return True

    monkeypatch.setattr(vault_ui, "UnlockDialog", FakeUnlock)
    edit = ad.AccountEditDialog(services, account_type)
    qtbot.addWidget(edit)
    edit.form.fields["username"].set("a")
    edit.form.fields["token"].focus.setText(FAKE_TOKEN)
    edit.save()
    assert unlock_calls == [1] and edit.saved is not None


# -- Tresor-Einstellungen -------------------------------------------------------------------
def test_vault_settings_switch_windows_to_file(qtbot, make_services, monkeypatch, home):
    services = make_services()
    services.use_vault(services.make_vault("windows"))
    services.vault.write("codecockpit/account/1/token", Secret(FAKE_TOKEN))
    monkeypatch.setattr(vault_ui, "confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(vault_ui, "NewPasswordDialog", FakeNewPassword)
    dialog = VaultSettingsDialog(services)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    lines = [dialog.state.item(r).text() for r in range(dialog.state.count())]
    assert lines[0] == "Speicherart: Windows-Anmeldeinformationsverwaltung"
    assert not dialog.password_button.isVisible()
    assert dialog.switch_button.text() == "&Wechseln zu Verschlüsselte Tresordatei …"
    dialog.switch()
    assert shown_infos == ["Speicherart gewechselt. 1 Eintrag übertragen."]
    assert dialog.close_button.hasFocus()
    qtbot.waitUntil(lambda: said("Speicherart gewechselt."), timeout=2000)
    assert services.settings.load().vault_kind == "vault_file"
    assert services.vault.read("codecockpit/account/1/token").reveal() == FAKE_TOKEN
    assert (home / "vault.bin").is_file()
    assert dialog.password_button.isVisible()
    assert said("Speicherart gewechselt. 1 Eintrag übertragen.")


def test_vault_settings_switch_file_to_windows_removes_file(qtbot, make_services, monkeypatch,
                                                            home, memory_keyring):
    services = make_services()
    file = services.make_vault("vault_file")
    file.create(Secret(PASSWORD))
    services.use_vault(file)
    services.vault.write("codecockpit/account/1/token", Secret(FAKE_TOKEN))
    monkeypatch.setattr(vault_ui, "confirm", lambda *args, **kwargs: True)
    dialog = VaultSettingsDialog(services)
    qtbot.addWidget(dialog)
    dialog.switch()
    assert services.vault.kind == "windows"
    assert not (home / "vault.bin").exists()
    assert services.vault.read("codecockpit/account/1/token").reveal() == FAKE_TOKEN


def test_vault_switch_declined_changes_nothing(qtbot, make_services, monkeypatch):
    services = make_services()
    services.use_vault(services.make_vault("windows"))
    monkeypatch.setattr(vault_ui, "confirm", lambda *args, **kwargs: False)
    dialog = VaultSettingsDialog(services)
    qtbot.addWidget(dialog)
    dialog.switch()
    assert services.vault.kind == "windows"


def test_auto_lock_setting_is_saved(qtbot, make_services):
    services = make_services()
    file = services.make_vault("vault_file")
    file.create(Secret(PASSWORD))
    services.use_vault(file)
    dialog = VaultSettingsDialog(services)
    qtbot.addWidget(dialog)
    assert dialog.auto_lock.specialValueText() == "nie"
    dialog.auto_lock.setValue(15)
    assert services.settings.load().auto_lock_minutes == 15


# -- Hauptfenster -----------------------------------------------------------------------------
def konten_menu(win: MainWindow):
    return next(a.menu() for a in win.menuBar().actions() if a.text() == "K&onten")


def visible_texts(menu) -> list[str]:
    return [a.text().replace("&", "") for a in menu.actions() if a.isVisible()]


def test_konten_menu_for_windows_vault(qtbot, make_services):
    services = make_services()
    services.use_vault(services.make_vault("windows"))
    win = MainWindow(services)
    qtbot.addWidget(win)
    win.update_vault_actions()
    assert visible_texts(konten_menu(win)) == ["Kontenverwaltung …", "Tresor-Einstellungen …"]


def test_lock_and_unlock_file_vault_from_menu(qtbot, make_services, monkeypatch):
    services = make_services()
    file = services.make_vault("vault_file")
    file.create(Secret(PASSWORD))
    services.use_vault(file)
    win = MainWindow(services)
    qtbot.addWidget(win)
    win.update_vault_actions()
    assert "Tresor sperren" in visible_texts(konten_menu(win))
    win.lock_vault()
    assert not services.vault.is_unlocked()
    assert said("Tresor gesperrt.")
    win.update_vault_actions()
    assert visible_texts(konten_menu(win))[-1] == "Tresor entsperren …"
    win.startup()
    assert not said("gesperrt. Entsperren")                  # beim Start keine Frage, keine Ansage


def test_auto_lock_after_inactivity(qtbot, make_services, monkeypatch):
    services = make_services()
    file = services.make_vault("vault_file")
    file.create(Secret(PASSWORD))
    services.use_vault(file)
    services.settings.update(auto_lock_minutes=5)
    win = MainWindow(services)
    qtbot.addWidget(win)
    assert win.lock_timer.isActive()
    win.check_auto_lock()
    assert services.vault.is_unlocked()                      # noch keine 5 Minuten
    win.last_input -= 5 * 60 + 1                             # auch Standby zählt mit
    infos = []
    monkeypatch.setattr("cockpit.ui.main_window.show_info",
                        lambda parent, title, text: infos.append(text))
    win.check_auto_lock()
    assert infos == ["Der Tresor wurde nach 5 Minuten ohne Eingabe gesperrt."]
    assert not services.vault.is_unlocked()
    assert said("Der Tresor wurde nach 5 Minuten ohne Eingabe gesperrt.")


def test_no_auto_lock_for_windows_vault(qtbot, make_services):
    services = make_services()
    services.use_vault(services.make_vault("windows"))
    services.settings.update(auto_lock_minutes=5)
    win = MainWindow(services)
    qtbot.addWidget(win)
    assert not win.lock_timer.isActive()


def test_all_new_dialogs_have_named_controls(qtbot, make_services, account_adapter):
    services = make_services(vault=FakeVault())
    dialogs = [pd.UnlockDialog(lambda s: None), pd.NewPasswordDialog(ask_old=True),
               sw.SetupWizard(services), ad.AccountsDialog(services),
               ad.AccountEditDialog(services, find_type("platform", account_adapter.kind)),
               VaultSettingsDialog(services)]
    for dialog in dialogs:
        qtbot.addWidget(dialog)
        for widget in dialog.findChildren(QWidget):
            assert widget.accessibleDescription() == ""
        for edit in dialog.findChildren(QLineEdit):
            if edit.objectName() == "qt_spinbox_lineedit":
                edit = edit.parent()                      # Name steht am Zahlenfeld selbst
            assert edit.accessibleName(), type(dialog).__name__


def test_input_restarts_the_lock_clock(qtbot, make_services):
    import time
    services = make_services()
    file = services.make_vault("vault_file")
    file.create(Secret(PASSWORD))
    services.use_vault(file)
    services.settings.update(auto_lock_minutes=1)
    win = MainWindow(services)
    qtbot.addWidget(win)
    win.last_input = time.time() - 120
    qtbot.keyClick(win.project_list, Qt.Key.Key_Down)
    win.check_auto_lock()
    assert services.vault.is_unlocked()


def test_accounts_help_entry_opens_explanation(accounts, monkeypatch):
    dialog, _, _ = accounts
    opened = []

    class FakeText:
        def __init__(self, title, lines, name, parent=None):
            opened.append((title, lines))

        def exec(self):
            return True

    monkeypatch.setattr(ad, "TextDialog", FakeText)
    dialog.list.setCurrentRow(dialog.list.count() - 1)
    dialog.open_current()
    assert opened[0][0] == "Wofür sind Konten?"
    assert any("mehrere Konten gleicher Art" in line for line in opened[0][1])
    assert dialog.current_account() is None


def test_focus_goes_to_close_after_password_change(qtbot, make_services, monkeypatch):
    services = make_services()
    file = services.make_vault("vault_file")
    file.create(Secret(PASSWORD))
    services.use_vault(file)
    monkeypatch.setattr("cockpit.ui.vault_settings_dialog.NewPasswordDialog", FakeNewPassword)
    dialog = VaultSettingsDialog(services)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    dialog.change_password()
    assert shown_infos == ["Das Master-Passwort wurde geändert."]   # Meldung mit OK
    assert dialog.close_button.hasFocus()


# -- Ansagen an das aktive Fenster (Test von Phase 3) ---------------------------------------
def test_announcement_goes_to_the_focused_widget_in_a_dialog(qtbot, make_services, monkeypatch):
    from cockpit.ui import announcer as announcer_module
    win = MainWindow(make_services())
    qtbot.addWidget(win)
    dialog = pd.UnlockDialog(lambda s: None, win)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    dialog.password.setFocus()
    targets = []
    monkeypatch.setattr(announcer_module.QAccessible, "updateAccessibility",
                        lambda event: targets.append(event.object()))
    announcer.announce("Probe.")
    assert targets == [dialog.password]                      # nicht das Hauptfenster


def test_announcement_waits_while_cockpit_is_in_background(qtbot, make_services, monkeypatch):
    from cockpit.ui import announcer as announcer_module
    win = MainWindow(make_services())
    qtbot.addWidget(win)
    sent = []
    monkeypatch.setattr(announcer_module.QAccessible, "updateAccessibility",
                        lambda event: sent.append(event))
    monkeypatch.setattr(announcer_module.Announcer, "app_is_active", staticmethod(lambda: False))
    announcer.announce("Der Tresor wurde gesperrt.")
    assert sent == [] and [m.text for m in announcer.pending] == ["Der Tresor wurde gesperrt."]
    monkeypatch.setattr(announcer_module.Announcer, "app_is_active", staticmethod(lambda: True))
    announcer._state_changed(Qt.ApplicationState.ApplicationActive)
    qtbot.waitUntil(lambda: bool(sent), timeout=2000)
    assert announcer.pending == []
