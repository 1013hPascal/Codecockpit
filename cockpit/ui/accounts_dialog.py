"""Kontenverwaltung (Menü Konten, Konzept 5.1).

AccountsDialog: Liste "Konten", oben "Neues Konto anlegen …". Enter bearbeitet oder legt an, Entf
löscht (mit Rückfrage). Mit Tab erreichbar: "Verbindung testen", "Löschen", "Schließen".

AccountEditDialog: Formular aus den Angaben, die der Adapter verlangt (account_fields).
Geheimnisse sind verdeckt. Beim Bearbeiten bleiben leere Geheimnisse unverändert.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QDialogButtonBox, QHBoxLayout, QListWidget, QPushButton,
                               QVBoxLayout, QWidget)

from cockpit.adapters import registry as adapter_registry
from cockpit.adapters.base import TestResult
from cockpit.core.accounts import Account, AccountType, account_types, find_type
from cockpit.core.errors import CockpitError
from cockpit.core.features import settings_fields as sf
from cockpit.core.secret import Secret
from cockpit.core.services import Services
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, name_widget, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.form_builder import FormError, SettingsForm
from cockpit.ui.text_dialog import TextDialog

NEW_ACCOUNT_TEXT = "Neues Konto anlegen …"
HELP_TEXT = "Wofür sind Konten? …"
HELP_LINES = [
    "Ein Konto ist Ihr Zugang zu einem Dienst, den das Cockpit für Sie benutzt.",
    "Plattform-Konto, zum Beispiel GitHub: Damit lädt das Cockpit Ihren Code hoch, legt "
    "Repositories an und holt Rückmeldungen. Das brauchen fast alle.",
    "KI-Konto, zum Beispiel ein Cloud-Anbieter mit API-Schlüssel: nur nötig, wenn Sie nicht "
    "die lokale KI Ollama nutzen. Kommt ab Phase 7.",
    "E-Mail-Konto: für Berichte und Benachrichtigungen per E-Mail. Kommt in Phase 11.",
    "Automations-Konto, zum Beispiel n8n: für Abläufe im Hintergrund. Kommt in Phase 10.",
    "Zu jedem Konto gehören Zugangsdaten wie ein Token. Sie liegen nur im Tresor.",
    "Sie können mehrere Konten gleicher Art haben, zum Beispiel ein privates GitHub-Konto "
    "und eines für einen Verein. Jedes Projekt merkt sich, zu welchem Konto es gehört.",
    "Privat und Beruflich trennen Sie über getrennte Installationen auf verschiedenen "
    "Rechnern. Innerhalb einer Installation brauchen Sie meist nur ein Plattform-Konto.",
    "Mit Verbindung testen prüfen Sie, ob die Zugangsdaten stimmen.",
]


def show_test_result(parent: QWidget, result: TestResult) -> None:
    announce(result.text, urgent=not result.ok)
    if result.ok:
        show_info(parent, "Verbindung testen", result.text)
    else:
        show_error(parent, "Verbindung testen", result.text, result.details)


class ChoiceDialog(FocusDialog):
    """Auswahl aus einer Liste. Enter oder "OK" wählt, Escape bricht ab."""

    def __init__(self, title: str, name: str, options: list[str],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.list = QListWidget()
        name_widget(self.list, name)
        self.list.addItems(options)
        self.list.setCurrentRow(0)
        self.list.itemActivated.connect(lambda item: self.accept())
        buttons = QDialogButtonBox()
        buttons.addButton("OK", QDialogButtonBox.ButtonRole.AcceptRole).setDefault(True)
        buttons.addButton("Abbrechen", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addWidget(buttons)
        self.list.setFocus()
        self.initial_focus_widget = self.list

    @property
    def chosen(self) -> int:
        return self.list.currentRow()


class AccountEditDialog(FocusDialog):
    def __init__(self, services: Services, account_type: AccountType,
                 account: Account | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.account_type = account_type
        self.account = account
        self.saved: Account | None = None
        self.setWindowTitle(f"Konto bearbeiten: {account.display_name}" if account
                            else f"Neues Konto: {account_type.display_name}")

        fields: list[sf.SettingField] = [sf.Text("display_name", "Anzeigename", required=True)]
        for f in account_type.fields:
            if f.secret:
                fields.append(sf.SecretText(f.key, f.label, required=f.required,
                                            keep_if_empty=account is not None))
            else:
                fields.append(sf.Text(f.key, f.label, f.default, required=f.required))
        values = {"display_name": account.display_name if account else account_type.display_name}
        if account is not None:
            values.update(services.accounts.values(account, with_secrets=False))
        self.form = SettingsForm(fields, values)

        buttons = QDialogButtonBox()
        self.test_button = buttons.addButton("&Verbindung testen",
                                             QDialogButtonBox.ButtonRole.ActionRole)
        self.save_button = buttons.addButton("&Speichern", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Abbrechen", QDialogButtonBox.ButtonRole.RejectRole)
        self.save_button.setDefault(True)
        self.test_button.clicked.connect(self.test_connection)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.form)
        layout.addWidget(buttons)
        self.resize(560, 280)
        self.initial_focus_widget = self.form.first_focus()
        self.initial_focus_widget.setFocus()

    def _values(self) -> tuple[str, dict[str, Any]] | None:
        try:
            values = self.form.values()
        except FormError as exc:
            show_error(self, self.windowTitle(), exc.message)
            self.form.focus_field(exc.key)
            return None
        return values.pop("display_name"), values

    def test_connection(self) -> None:
        checked = self._values()
        if checked is None:
            return
        _, values = checked
        if self.account is not None:
            if not vault_ui.ensure_unlocked(self.services, self):
                return
            stored = self.services.accounts.values(self.account)
            for key, value in values.items():
                if isinstance(value, Secret) and not value.reveal():
                    values[key] = stored.get(key) or value
        cls = adapter_registry.adapter_class(self.account_type.kind, self.account_type.adapter)
        try:
            result = cls.from_account(values).test_connection()
        except CockpitError as exc:
            result = TestResult(False, exc.message, exc.details)
        show_test_result(self, result)
        self.test_button.setFocus()

    def save(self) -> None:
        checked = self._values()
        if checked is None:
            return
        name, values = checked
        if not vault_ui.ensure_unlocked(self.services, self):
            return
        try:
            if self.account is None:
                self.saved = self.services.accounts.create(self.account_type, name, values)
            else:
                self.saved = self.services.accounts.update(self.account, name, values)
        except CockpitError as exc:
            show_error(self, self.windowTitle(), exc.message, exc.details)
            return
        self.accept()


class AccountsDialog(FocusDialog):
    def __init__(self, services: Services, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.setWindowTitle("Kontenverwaltung")
        self.accounts: list[Account] = []
        self.list = QListWidget()
        name_widget(self.list, "Konten")
        self.list.itemActivated.connect(lambda item: self.open_current())
        delete_key = QShortcut(QKeySequence.StandardKey.Delete, self.list)
        delete_key.setContext(Qt.ShortcutContext.WidgetShortcut)
        delete_key.activated.connect(self.delete_current)

        self.test_button = QPushButton("&Verbindung testen")
        self.test_button.clicked.connect(self.test_current)
        self.delete_button = QPushButton("&Löschen")
        self.delete_button.clicked.connect(self.delete_current)
        close = QPushButton("&Schließen")
        close.clicked.connect(self.accept)
        buttons = QHBoxLayout()
        for button in (self.test_button, self.delete_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addLayout(buttons)
        self.resize(640, 420)
        self.refresh()
        self.list.setFocus()
        self.initial_focus_widget = self.list

    def refresh(self, select_id: int | None = None) -> None:
        row = self.list.currentRow()
        self.accounts = self.services.accounts.all()
        self.list.clear()
        self.list.addItem(NEW_ACCOUNT_TEXT)
        self.list.addItems([a.label for a in self.accounts])
        self.list.addItem(HELP_TEXT)                 # Erklärung, immer am Ende der Liste
        if select_id is not None:
            row = next((i + 1 for i, a in enumerate(self.accounts) if a.id == select_id), 0)
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))

    def current_account(self) -> Account | None:
        row = self.list.currentRow()
        return self.accounts[row - 1] if 1 <= row <= len(self.accounts) else None

    def open_current(self) -> None:
        if self.list.currentRow() == self.list.count() - 1:
            TextDialog("Wofür sind Konten?", HELP_LINES, "Erklärung Konten", self).exec()
            self.list.setFocus()
            return
        account = self.current_account()
        if account is None:
            self.new_account()
            return
        account_type = find_type(account.kind, account.adapter)
        if account_type is None:
            show_error(self, "Konto bearbeiten", f"Die Kontoart {account.adapter} gibt es nicht.")
            return
        dialog = AccountEditDialog(self.services, account_type, account, self)
        if dialog.exec():
            announce(f"Konto {dialog.saved.display_name} gespeichert.")
            self.refresh(dialog.saved.id)
        self.list.setFocus()

    def new_account(self) -> None:
        types = account_types()
        if not types:
            show_info(self, "Neues Konto", "Es gibt noch keine Kontoarten. Die Anbindung an "
                      "GitHub kommt in Phase 4.")
            return
        account_type = types[0]
        if len(types) > 1:
            chooser = ChoiceDialog("Neues Konto", "Kontoart", [t.label for t in types], self)
            if not chooser.exec():
                self.list.setFocus()
                return
            account_type = types[chooser.chosen]
        dialog = AccountEditDialog(self.services, account_type, None, self)
        if dialog.exec():
            announce(f"Konto {dialog.saved.display_name} angelegt.")
            self.refresh(dialog.saved.id)
        self.list.setFocus()

    def test_current(self) -> None:
        account = self.current_account()
        if account is None:
            announce("Bitte zuerst ein Konto wählen.")
            self.list.setFocus()
            return
        if vault_ui.ensure_unlocked(self.services, self):
            show_test_result(self, self.services.accounts.test(account))
        self.test_button.setFocus()

    def delete_current(self) -> None:
        account = self.current_account()
        if account is None:
            announce("Bitte zuerst ein Konto wählen.")
            self.list.setFocus()
            return
        text = (f"Das Konto {account.display_name} und seine Zugangsdaten im Tresor werden "
                "gelöscht. Auf der Plattform ändert sich nichts. Löschen?")
        if not confirm(self, "Konto löschen", text, yes="Löschen", no="Abbrechen"):
            self.list.setFocus()
            return
        if not vault_ui.ensure_unlocked(self.services, self):
            return
        try:
            self.services.accounts.delete(account)
        except CockpitError as exc:
            show_error(self, "Konto löschen", exc.message, exc.details)
            return
        announce(f"Konto {account.display_name} gelöscht.")
        self.refresh()
        self.list.setFocus()
