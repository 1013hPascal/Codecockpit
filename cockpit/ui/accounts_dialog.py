"""Kontenverwaltung (Menü Konten, Konzept 5.1).

AccountsDialog: Liste "Konten", oben "Neues Konto anlegen …". Enter bearbeitet oder legt an, Entf
löscht (mit Rückfrage). Mit Tab erreichbar: "Verbindung testen", "Löschen", "Schließen".

AccountEditDialog: Formular aus den Angaben, die der Adapter verlangt (account_fields).
Geheimnisse sind verdeckt. Beim Bearbeiten bleiben leere Geheimnisse unverändert.
"""
from __future__ import annotations


from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core.accounts import Account, account_types, find_type
from cockpit.core.errors import CockpitError
from cockpit.core.services import Services
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, name_widget, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.text_dialog import TextDialog
# Aufgeteilt am 22.10.2026: Teile stehen in account_edit_dialog.py. Die Namen bleiben hier erreichbar.
from cockpit.ui.account_edit_dialog import (  # noqa: F401
    AccountEditDialog, ChoiceDialog, run_in_background, show_test_result, wait_for)

NEW_ACCOUNT_TEXT = "Neues Konto anlegen …"
HELP_TEXT = "Wofür sind Konten? …"
HELP_LINES = [
    "Ein Konto ist Ihr Zugang zu einem Dienst, den das Cockpit für Sie benutzt.",
    "Plattform-Konto, zum Beispiel GitHub: Damit lädt das Cockpit Ihren Code hoch, legt "
    "Repositories an und holt Rückmeldungen. Das brauchen fast alle.",
    "KI-Konto, zum Beispiel ein Firmen-Server oder ein Cloud-Anbieter mit API-Schlüssel: nur "
    "nötig, wenn Sie nicht die lokale KI Ollama nutzen. Welche KI das Cockpit nutzt, wählen Sie "
    "im Menü KI, KI-Verwaltung.",
    "E-Mail-Konto: für Berichte und Benachrichtigungen per E-Mail. Kommt in Phase 11.",
    "Automations-Konto, zum Beispiel n8n: für Abläufe im Hintergrund. Kommt in Phase 10.",
    "Zu jedem Konto gehören Zugangsdaten wie ein Token. Sie liegen nur im Tresor.",
    "Sie können mehrere Konten gleicher Art haben, zum Beispiel ein privates GitHub-Konto "
    "und eines für einen Verein. Jedes Projekt merkt sich, zu welchem Konto es gehört.",
    "Privat und Beruflich trennen Sie über getrennte Installationen auf verschiedenen "
    "Rechnern. Innerhalb einer Installation brauchen Sie meist nur ein Plattform-Konto.",
    "Mit Verbindung testen prüfen Sie, ob die Zugangsdaten stimmen.",
]


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
            if dialog.saved.kind == "platform":
                # Wunsch des Nutzers: wie im Einrichtungsassistenten gleich Name und anonyme
                # E-Mail-Adresse für Commits festlegen
                from cockpit.ui.identity_dialog import GitIdentityDialog
                GitIdentityDialog(self.services, dialog.saved, self).exec()
        self.list.setFocus()

    def test_current(self) -> None:
        account = self.current_account()
        if account is None:
            announce("Bitte zuerst ein Konto wählen.")
            self.list.setFocus()
            return
        if not vault_ui.ensure_unlocked(self.services, self):
            return
        accounts = self.services.accounts
        self.task = run_in_background(self, lambda task: accounts.test(account),
                                      lambda result: show_test_result(self, result),
                                      self.test_button)

    def done(self, code: int) -> None:
        wait_for(getattr(self, "task", None))
        super().done(code)

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
