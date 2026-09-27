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
                               QStackedWidget,
                               QVBoxLayout, QWidget)

from cockpit.adapters import registry as adapter_registry
from cockpit.adapters.base import TestResult
from cockpit.core.accounts import Account, AccountType, account_types, find_type
from cockpit.core.errors import CockpitError
from cockpit.core.features import settings_fields as sf
from cockpit.core.secret import Secret
from cockpit.core.services import Services
from cockpit.ui import browser_login_dialog, vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, name_widget, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.form_builder import FormError, SettingsForm
from cockpit.ui.tasks import Task
from cockpit.ui.text_dialog import TextDialog

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


def show_test_result(parent: QWidget, result: TestResult) -> None:
    announce(result.text, urgent=not result.ok, speak=False)     # das Fenster liest NVDA vor
    if result.ok:
        show_info(parent, "Verbindung testen", result.text)
        return
    show_error(parent, "Verbindung testen", result.text, result.details)
    if result.link and confirm(parent, "Verbindung testen", result.link_text or
                               "Seite im Browser öffnen?", default_yes=True):
        browser_login_dialog.open_url(result.link)


def wait_for(task: Task | None) -> None:
    """Beim Schließen auf einen laufenden Test warten. Ein zerstörter laufender Thread würde das
    Programm abstürzen lassen."""
    try:
        if task is not None and task.isRunning():
            task.wait(5000)
    except RuntimeError:                            # Task ist schon aufgeräumt
        pass


def run_in_background(parent: QWidget, fn, on_result, button: QPushButton) -> Task:
    """Netzwerk nie im Vordergrund: Die Oberfläche bleibt bedienbar, die Schaltfläche ist
    solange gesperrt."""
    button.setEnabled(False)
    announce("Verbindung wird getestet …")
    task = Task(fn, parent)

    def done() -> None:
        button.setEnabled(True)
        button.setFocus()

    task.result.connect(lambda result: (done(), on_result(result)))
    task.error.connect(lambda message, details: (done(), show_test_result(
        parent, TestResult(False, message, details))))
    task.finished.connect(task.deleteLater)
    task.start()
    return task


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
    """Konto anlegen oder bearbeiten (Test Phase 4: erst wählen, dann nur das Nötige zeigen).

    Neues Konto bei einer Plattform mit Anmeldung im Browser:
    - Seite "Auswahl": Erklärung, dann "Im Browser anmelden …" und "Mit Token anmelden …".
    - Nach der Anmeldung im Browser Seite "Angemeldet": Ergebnis, Anzeigename, Speichern.
    - "Mit Token anmelden" führt zur Seite "Token": Anzeigename, Serveradresse, Anleitung, Token.
    Ohne Anmeldung im Browser oder beim Bearbeiten gibt es nur die Seite "Token".

    Felder mit auto=True (zum Beispiel der Benutzername) erscheinen nie. Das Cockpit holt sie
    beim Anmelden bzw. beim Speichern mit einem Verbindungstest selbst.
    """

    def __init__(self, services: Services, account_type: AccountType,
                 account: Account | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.account_type = account_type
        self.account = account
        self.saved: Account | None = None
        self.device_token: Secret | None = None           # aus der Anmeldung im Browser
        self.task: Task | None = None
        self.adapter_cls = adapter_registry.adapter_class(account_type.kind, account_type.adapter)
        self.auto_keys = [f.key for f in account_type.fields if f.auto]
        stored = services.accounts.values(account, with_secrets=False) if account else {}
        self.auto_values: dict[str, Any] = {k: stored.get(k, "") for k in self.auto_keys}
        self.setWindowTitle(f"Konto bearbeiten: {account.display_name}" if account
                            else f"Neues Konto: {account_type.display_name}")

        # -- Formular für den Weg mit Token ----------------------------------------------
        fields: list[sf.SettingField] = [sf.Text("display_name", "Anzeigename", required=True)]
        for f in account_type.fields:
            if f.auto:
                continue
            if f.secret:
                fields.append(sf.SecretText(f.key, f.label, required=f.required,
                                            keep_if_empty=account is not None))
            elif f.yes_no:
                fields.append(sf.YesNo(f.key, f.label, f.default == "ja"))
            else:
                fields.append(sf.Text(f.key, f.label, f.default, required=f.required))
        values = {"display_name": account.display_name if account else account_type.display_name}
        values.update({k: v for k, v in stored.items() if k not in self.auto_keys})
        self.form = SettingsForm(fields, values)
        self.guide_button = None
        if self.adapter_cls.account_guide:
            self.add_guide_button()
        self.test_button = QPushButton("&Verbindung testen")
        self.test_button.clicked.connect(lambda: self.test_connection())
        self.save_button = QPushButton("&Speichern")
        self.save_button.clicked.connect(self.save)
        self.back_button = QPushButton("&Zurück zur Auswahl")
        self.back_button.clicked.connect(lambda: self.show_page(self.choice_page))

        browser = account is None and self.has_browser_login()
        lines = self.adapter_cls.account_explanation(browser)
        self.explanation = self._lines("Erklärung", lines) if lines else None

        # -- Seite Auswahl -------------------------------------------------------------------
        self.choice_page = QWidget()
        self.browser_button = None
        self.token_button = None
        if browser:
            choice = QVBoxLayout(self.choice_page)
            choice.addWidget(self.explanation, 1)
            self.browser_button = QPushButton("Im &Browser anmelden …")
            self.browser_button.clicked.connect(self.browser_login)
            self.token_button = QPushButton("Mit &Token anmelden …")
            self.token_button.clicked.connect(lambda: self.show_page(self.token_page))
            row = QHBoxLayout()
            row.addWidget(self.browser_button)
            row.addWidget(self.token_button)
            row.addStretch(1)
            choice.addLayout(row)

        # -- Seite Token ---------------------------------------------------------------------
        self.token_page = QWidget()
        token = QVBoxLayout(self.token_page)
        self.token_explanation = None
        if not browser and self.explanation is not None and account is None:
            token.addWidget(self.explanation, 1)
            self.token_explanation = self.explanation
        token.addWidget(self.form)
        row = QHBoxLayout()
        if browser:
            row.addWidget(self.back_button)
        row.addStretch(1)
        row.addWidget(self.test_button)
        row.addWidget(self.save_button)
        token.addLayout(row)

        # -- Seite Angemeldet (nach der Anmeldung im Browser) ------------------------------
        self.done_page = QWidget()
        done = QVBoxLayout(self.done_page)
        self.done_info = self._lines("Ergebnis", [])
        self.done_form = SettingsForm([sf.Text("display_name", "Anzeigename", required=True)],
                                      {"display_name": account_type.display_name})
        self.done_save_button = QPushButton("&Speichern")
        self.done_save_button.clicked.connect(self.save_browser_account)
        done.addWidget(self.done_info, 1)
        done.addWidget(self.done_form)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.done_save_button)
        done.addLayout(row)

        self.stack = QStackedWidget()
        for page in (self.choice_page, self.token_page, self.done_page):
            self.stack.addWidget(page)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack, 1)
        layout.addLayout(bottom)
        self.resize(640, 460)
        self.show_page(self.choice_page if browser else self.token_page, speak=False)

    @staticmethod
    def _lines(name: str, lines: list[str]) -> QListWidget:
        widget = QListWidget()
        name_widget(widget, name)
        widget.addItems(lines)
        widget.setCurrentRow(0)
        widget.setWordWrap(True)
        return widget

    def show_page(self, page: QWidget, speak: bool = True) -> None:
        self.stack.setCurrentWidget(page)
        if page is self.choice_page:
            first, title = self.explanation, "Auswahl"
        elif page is self.token_page:
            first = self.token_explanation or self.form.first_focus()
            title = "Mit Token anmelden"
            self.save_button.setDefault(True)
        else:
            first, title = self.done_info, "Angemeldet"
            self.done_save_button.setDefault(True)
        self.initial_focus_widget = first
        first.setFocus()
        if speak:
            announce(title)

    # -- Werte -----------------------------------------------------------------------------
    def _values(self) -> tuple[str, dict[str, Any]] | None:
        try:
            values = self.form.values()
        except FormError as exc:
            show_error(self, self.windowTitle(), exc.message)
            self.form.focus_field(exc.key)
            return None
        name = values.pop("display_name")
        values.update(self.auto_values)
        return name, values

    def _with_stored_secrets(self, values: dict[str, Any]) -> dict[str, Any] | None:
        """Beim Bearbeiten: leere Geheimnisse durch die gespeicherten ersetzen."""
        if self.account is None:
            return values
        if not vault_ui.ensure_unlocked(self.services, self):
            return None
        stored = self.services.accounts.values(self.account)
        for key, value in values.items():
            if isinstance(value, Secret) and not value.reveal():
                values[key] = stored.get(key) or value
        return values

    # -- Anleitung ------------------------------------------------------------------------
    def add_guide_button(self) -> None:
        """Knopf direkt vor dem ersten Geheimnis-Feld (Test Phase 4)."""
        self.guide_button = QPushButton("&Anleitung für den Token …")
        self.guide_button.clicked.connect(self.show_guide)
        secret = next((f for f in self.form.fields.values()
                       if isinstance(f.spec, sf.SecretText)), None)
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.guide_button)
        row.addStretch(1)
        layout = self.form.layout_
        if secret is None:
            layout.addRow(holder)
            return
        position, _role = layout.getWidgetPosition(secret.widget)
        layout.insertRow(position, holder)
        order = self.form._order
        index = order.index(secret.focus)
        if index > 0:
            QWidget.setTabOrder(order[index - 1], self.guide_button)
        QWidget.setTabOrder(self.guide_button, secret.focus)

    def show_guide(self) -> None:
        from cockpit.core import paths
        cls = self.adapter_cls
        try:
            text = (paths.resource_dir() / cls.account_guide).read_text(encoding="utf-8")
        except OSError as exc:
            show_error(self, cls.account_guide_title, "Die Anleitung wurde nicht gefunden.",
                       str(exc))
            return
        TextDialog(cls.account_guide_title, text, f"Anleitung {cls.account_guide_title}",
                   self).exec()
        self.guide_button.setFocus()

    # -- Anmeldung im Browser --------------------------------------------------------------
    def current_url(self) -> str:
        field = self.form.fields.get("url")
        return str(field.get()) if field is not None else ""

    def has_browser_login(self) -> bool:
        check = getattr(self.adapter_cls, "browser_login_available", None)
        return bool(check and check(self.current_url()))

    def browser_login(self) -> None:
        dialog = browser_login_dialog.BrowserLoginDialog(self.adapter_cls, self.current_url(),
                                                         self)
        if not dialog.exec() or dialog.token is None:
            self.browser_button.setFocus()
            return
        self.device_token = dialog.token
        if "username" in self.auto_values:
            self.auto_values["username"] = dialog.username
        self.done_form.fields["display_name"].set(
            f"{self.account_type.display_name} {dialog.username}".strip())
        self.done_info.clear()
        self.done_info.addItems([
            f"Angemeldet als {dialog.username}.",
            "Mit Speichern ist das Konto fertig. Der Zugang kommt verschlüsselt in den Tresor.",
            "Den Anzeigenamen können Sie vorher ändern, zum Beispiel in GitHub privat.",
        ])
        self.done_info.setCurrentRow(0)
        self.show_page(self.done_page)

    def save_browser_account(self) -> None:
        try:
            name = self.done_form.values()["display_name"]
        except FormError as exc:
            show_error(self, self.windowTitle(), exc.message)
            self.done_form.focus_field(exc.key)
            return
        values: dict[str, Any] = {f.key: f.default for f in self.account_type.fields
                                  if not f.secret}
        values.update(self.auto_values)
        for f in self.account_type.fields:
            if f.secret:
                values[f.key] = self.device_token
        self._store(name, values)

    # -- Verbindung testen und speichern --------------------------------------------------
    def test_connection(self, then_save: bool = False) -> None:
        checked = self._values()
        if checked is None:
            return
        name, values = checked
        values = self._with_stored_secrets(values)
        if values is None:
            return
        cls = self.adapter_cls

        def work(task: Task):
            adapter = cls.from_account(values)
            return adapter.test_connection(), getattr(adapter, "username", "")

        def finished(outcome) -> None:
            result, username = outcome
            self.task = None
            if result.ok and username and "username" in self.auto_values:
                self.auto_values["username"] = username      # Benutzername selbst eintragen
            if then_save and result.ok:
                values.update(self.auto_values)
                self._store(name, values)
                return
            show_test_result(self, result)

        self.task = run_in_background(self, work, finished,
                                      self.save_button if then_save else self.test_button)

    def save(self) -> None:
        """Fehlt ein Wert, den das Cockpit selbst einträgt, oder ist der Token neu, wird vorher
        die Verbindung getestet. Klappt der Test nicht, wird nichts gespeichert."""
        missing_auto = [k for k in self.auto_keys if not self.auto_values.get(k)]
        token_changed = any(isinstance(f.spec, sf.SecretText) and f.get()
                            for f in self.form.fields.values())
        if missing_auto or (self.auto_keys and token_changed):
            self.test_connection(then_save=True)
            return
        checked = self._values()
        if checked is not None:
            self._store(*checked)

    def _store(self, name: str, values: dict[str, Any]) -> None:
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

    def done(self, code: int) -> None:
        wait_for(self.task)
        super().done(code)


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
