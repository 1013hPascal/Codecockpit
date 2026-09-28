"""Fenster "Git-Identität" nach dem Anlegen eines Plattform-Kontos (Wunsch des Nutzers, 28.09.2026).

Wie die Seite Git-Identität im Einrichtungsassistenten (Konzept 9.8): Name und E-Mail-Adresse für
Commits, dazu "Anonyme GitHub-Adresse übernehmen". Die Werte kommen in die Grundeinstellungen.
"Überspringen" und Escape lassen alles, wie es ist.
"""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from cockpit.core.settings import setting_fields
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog
from cockpit.ui.error_dialog import show_error
from cockpit.ui.form_builder import FormError, SettingsForm
from cockpit.ui.repo_dialogs import button_row
from cockpit.ui.tasks import Task


class GitIdentityDialog(FocusDialog):
    def __init__(self, services, account, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.account = account
        self.task: Task | None = None
        self.setWindowTitle(f"Git-Identität für Commits: {account.display_name}")
        fields = [f for f in setting_fields() if f.key in ("git_name", "git_email")]
        settings = services.settings.load()
        self.form = SettingsForm(fields, {"git_name": settings.git_name,
                                          "git_email": settings.git_email})
        hint = QLabel("Name und E-Mail-Adresse stehen in jedem Commit. Bei öffentlichen "
                      "Repositories kann sie jeder sehen. Die anonyme noreply-Adresse von GitHub "
                      "schützt Ihre private Adresse.")
        hint.setWordWrap(True)
        self.noreply_button = QPushButton("&Anonyme GitHub-Adresse übernehmen")
        self.noreply_button.clicked.connect(self.take_noreply)
        save = QPushButton("&Speichern")
        save.setDefault(True)
        save.clicked.connect(self.save)
        skip = QPushButton("Ü&berspringen")
        skip.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addWidget(self.form)
        layout.addLayout(button_row(self.noreply_button, None))
        layout.addLayout(button_row(None, save, skip))
        self.resize(560, 260)
        self.initial_focus_widget = self.form.first_focus()

    def take_noreply(self) -> None:
        """Name und anonyme Adresse vom Konto holen, im Hintergrund (wie im Assistenten)."""
        if self.task is not None or not vault_ui.ensure_unlocked(self.services, self):
            return
        accounts, account = self.services.accounts, self.account

        def work(task):
            adapter = accounts.adapter_for(account)
            return adapter.noreply_email(), getattr(adapter, "username", "")

        self.noreply_button.setEnabled(False)
        self.task = Task(work, self)
        self.task.result.connect(self.noreply_received)
        self.task.error.connect(self.noreply_failed)
        self.task.finished.connect(self._done)
        self.task.start()

    def _done(self) -> None:
        task, self.task = self.task, None
        self.noreply_button.setEnabled(True)
        if task is not None:
            task.deleteLater()

    def noreply_received(self, result) -> None:
        email, login = result
        if not email:
            show_error(self, self.windowTitle(), "Diese Plattform nennt keine anonyme Adresse.")
            return
        if not self.form.fields["git_name"].get():
            self.form.fields["git_name"].set(login)
        self.form.fields["git_email"].set(email)
        announce(f"Adresse übernommen: {email}")
        self.form.focus_field("git_email")

    def noreply_failed(self, message: str, details: str) -> None:
        show_error(self, self.windowTitle(), message, details)
        self.noreply_button.setFocus()

    def save(self) -> None:
        try:
            values = self.form.values()
        except FormError as exc:
            show_error(self, self.windowTitle(), exc.message)
            self.form.focus_field(exc.key)
            return
        if not values["git_name"] or not values["git_email"]:
            show_error(self, self.windowTitle(), "Bitte Name und E-Mail-Adresse eingeben, oder "
                       "Überspringen wählen.")
            self.form.focus_field("git_name" if not values["git_name"] else "git_email")
            return
        self.services.settings.update(**values)
        announce(f"Git-Identität gespeichert: {values['git_name']}, {values['git_email']}.")
        self.accept()

    def done(self, code: int) -> None:
        if self.task is not None:
            self.task.wait(5000)
        super().done(code)
