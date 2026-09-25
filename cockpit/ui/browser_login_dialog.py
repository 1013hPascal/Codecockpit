"""Anmeldung im Browser (Konzept 6.1, Device Flow).

Ablauf:
1. Das Cockpit holt einen Code und kopiert ihn in die Zwischenablage.
2. Der Browser öffnet die Anmeldeseite. Dort meldet sich der Nutzer an, fügt den Code ein und
   bestätigt.
3. Das Cockpit wartet im Hintergrund, bis GitHub den Token schickt, und liest den Benutzernamen.

Das Fenster zeigt die Schritte als Liste, der Code steht in der ersten Zeile. Mit Tab erreichbar:
"Code kopieren", "Seite erneut öffnen" und "Abbrechen". Nach Erfolg schließt das Fenster selbst.

Mit scopes holt dasselbe Fenster eine zweite, kurze Anmeldung mit anderen Rechten, zum Beispiel nur
zum Löschen eines Repositories (Phase 5e). Der Zugang daraus wird nicht gespeichert.
"""
from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core.secret import Secret
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task


def open_url(url: str) -> None:
    """Im Standardbrowser öffnen (in Tests ersetzbar)."""
    QDesktopServices.openUrl(QUrl(url))


class BrowserLoginDialog(FocusDialog):
    """platform_cls: Plattform mit SupportsBrowserLogin. Nach accept stehen token und username
    bereit."""

    def __init__(self, platform_cls, url: str = "", parent: QWidget | None = None,
                 scopes: str = "", title: str = "", confirm_line: str = "") -> None:
        super().__init__(parent)
        self.platform_cls = platform_cls
        self.url = url
        self.scopes = scopes
        self.confirm_line = confirm_line or (
            "Auf der nächsten Seite fragt GitHub, ob CodeCockpit auf Ihr Konto zugreifen darf. "
            "Bestätigen Sie mit Authorize.")
        self.token: Secret | None = None
        self.username = ""
        self.login = None
        self.task: Task | None = None
        self.setWindowTitle(title or f"Mit {platform_cls.display_name} anmelden")

        self.steps = QListWidget()
        name_widget(self.steps, "Anmeldung")
        self.steps.addItem("Anmeldung wird vorbereitet …")
        self.steps.setCurrentRow(0)
        self.copy_button = QPushButton("Code &kopieren")
        self.copy_button.clicked.connect(self.copy_code)
        self.open_button = QPushButton("Seite erneut ö&ffnen")
        self.open_button.clicked.connect(self.open_page)
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        for button in (self.copy_button, self.open_button):
            button.setEnabled(False)
        buttons = QHBoxLayout()
        buttons.addWidget(self.copy_button)
        buttons.addWidget(self.open_button)
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.steps)
        layout.addLayout(buttons)
        self.resize(620, 300)
        self.steps.setFocus()
        self.initial_focus_widget = self.steps
        self.start()

    # -- Ablauf ----------------------------------------------------------------------------
    def start(self) -> None:
        cls, url, scopes = self.platform_cls, self.url, self.scopes
        if scopes:
            self._run(lambda task: cls.start_browser_login(url, scopes), self.code_received)
        else:
            self._run(lambda task: cls.start_browser_login(url), self.code_received)

    def code_received(self, login) -> None:
        self.login = login
        QGuiApplication.clipboard().setText(login.user_code)
        self.steps.clear()
        self.steps.addItems([
            f"Ihr Code: {login.user_code}",
            "Der Code ist in der Zwischenablage.",
            f"Der Browser öffnet die Seite {login.verification_uri}.",
            "Melden Sie sich dort an, fügen Sie den Code mit Strg+V ein und wählen Sie Continue.",
            self.confirm_line,
            "Danach kehren Sie hierher zurück. Das Cockpit wartet, bis Sie fertig sind.",
            f"Der Code gilt {login.expires_in // 60} Minuten.",
        ])
        self.steps.setCurrentRow(0)
        self.copy_button.setEnabled(True)
        self.open_button.setEnabled(True)
        announce(f"Ihr Code: {login.user_code}. Er ist in der Zwischenablage. "
                 "Der Browser wird geöffnet.")
        self.open_page()
        cls, url = self.platform_cls, self.url

        def wait(task: Task):
            token = cls.wait_for_browser_login(login, url, task.cancel_event)
            user = cls(url, token).current_user()
            return token, user.login

        self._run(wait, self.finished_login)

    def finished_login(self, result) -> None:
        self.token, self.username = result
        announce(f"Angemeldet als {self.username}.")
        self.accept()

    def _run(self, fn, on_result) -> None:
        task = Task(fn, self)
        task.result.connect(on_result)
        task.error.connect(self.failed)
        task.finished.connect(task.deleteLater)
        self.task = task
        task.start()

    def failed(self, message: str, details: str) -> None:
        self.task = None
        announce(message, urgent=True)
        show_error(self, self.windowTitle(), message, details)
        self.reject()

    # -- Schaltflächen ---------------------------------------------------------------------
    def copy_code(self) -> None:
        if self.login is not None:
            QGuiApplication.clipboard().setText(self.login.user_code)
            announce("Code kopiert.")

    def open_page(self) -> None:
        if self.login is not None:
            open_url(self.login.verification_uri)

    def reject(self) -> None:
        if self.task is not None and self.task.isRunning():
            self.task.cancel()
            self.task.wait(3000)                    # nie einen laufenden Thread zerstören
        super().reject()
