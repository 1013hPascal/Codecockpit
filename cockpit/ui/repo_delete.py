"""Repository löschen: Name zur Bestätigung eintippen, dann löschen.
"""
from __future__ import annotations

from PySide6.QtWidgets import QLineEdit, QPushButton, QVBoxLayout, QWidget
from typing import Callable

from cockpit.platforms.base import Capability, NotFound, PermissionMissing
from cockpit.ui import browser_login_dialog
from cockpit.ui.common import FocusDialog, ask_buttons, confirm, label_for
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialog_parts import _buttons


NAME_MISMATCH = "Der eingetippte Name stimmt nicht. Es wurde nichts gelöscht."


class RepoDeleter:
    """Ein Repository auf der Plattform löschen, mit allen Rückfragen (Konzept 9.5): erst die
    Warnung mit "Stattdessen archivieren …", dann den Namen eintippen. Fehlt dem Zugang das Recht
    zum Löschen, gibt es eine zweite, kurze Anmeldung im Browser, deren Zugang nicht gespeichert
    wird. Nie ohne Bestätigung.
    Für "Projekt verwalten" und für Repositories, die nur auf der Plattform liegen (Wunsch des
    Nutzers, 02.10.2026: löschen, ohne vorher herunterzuladen). local: Es gibt einen Ordner auf
    dem Rechner, die Warnung sagt dann, dass er bleibt."""

    def __init__(self, parent: QWidget, worker: "_Worker", platform, ref, platform_name: str,
                 archived: bool, on_deleted: Callable[[], None],
                 on_archive: Callable[[], object] | None = None, local: bool = True) -> None:
        self.parent = parent
        self.worker = worker
        self.platform = platform
        self.ref = ref
        self.platform_name = platform_name
        self.archived = archived
        self.on_deleted = on_deleted
        self.on_archive = on_archive
        self.local = local

    def start(self) -> None:
        name = self.ref.name
        text = (f"Löschen lässt sich nicht rückgängig machen. {name} ist danach mit Verlauf, "
                f"Issues und allen Einstellungen auf {self.platform_name} weg.")
        text += (" Der Ordner auf Ihrem Rechner bleibt immer erhalten." if self.local else
                 " Auf Ihrem Rechner gibt es keine Kopie.")
        options = ["Weiter zum Löschen …"]
        if not self.archived and self.on_archive is not None:
            text += (" Sanfter ist Archivieren: Das Repository wird schreibgeschützt und bleibt "
                     "erhalten.")
            options.append("Stattdessen archivieren …")
        options.append("Abbrechen")
        cancel = len(options) - 1
        choice = ask_buttons(self.parent, "Löschen", text, options, default=cancel,
                             escape=cancel)
        if choice == cancel:
            return
        if choice == 1:
            self.on_archive()
            return
        dialog = TypeNameDialog(name, self.parent)
        if not dialog.exec():
            return
        self.delete_now()

    def delete_now(self) -> None:
        """Ohne weitere Rückfrage löschen, wenn schon bestätigt ist (auch für "Projekt löschen",
        06.10.2026). Fehlt das Recht, kommt die zweite Anmeldung."""
        allowed = self.platform.permissions().get(Capability.DELETE_REPO)
        if allowed is not None and not allowed.available:
            self.second_login()
            return
        platform, ref = self.platform, self.ref

        def work() -> bool:
            try:
                platform.delete(ref)
            except PermissionMissing:
                return False                      # Recht fehlt: zweite Anmeldung anbieten
            except NotFound:
                pass                              # schon weg, das Ziel ist erreicht
            return True

        def done(ok: bool) -> None:
            if ok:
                self.on_deleted()
            else:
                self.second_login()

        self.worker.run(work, done, speak="Wird gelöscht.")

    def second_login(self) -> None:
        cls = type(self.platform)
        url = getattr(self.platform, "url", "")
        scopes = getattr(cls, "delete_login_scopes", "")
        available = getattr(cls, "browser_login_available", lambda url="": False)(url)
        name = self.ref.name
        if not scopes or not available:
            show_error(self.parent, "Löschen",
                       f"Dem Zugang fehlt das Recht zum Löschen (delete_repo). Es wurde nichts "
                       f"gelöscht. Sie können in der Kontenverwaltung einen Token mit diesem Recht "
                       f"eintragen oder {name} auf {self.platform_name} selbst löschen.")
            page = self.platform.settings_url(self.ref)
            if page and confirm(self.parent, "Löschen", "Einstellungen des Repositories im "
                                "Browser öffnen? Dort steht Löschen ganz unten.",
                                yes="Im Browser öffnen", no="Abbrechen"):
                browser_login_dialog.open_url(page)
            return
        text = (f"Zum Löschen braucht das Cockpit ein zusätzliches Recht von {self.platform_name}. "
                "Dafür melden Sie sich im Browser noch einmal kurz an und bestätigen das Recht zum "
                "Löschen. Der Zugang wird nur für dieses eine Löschen benutzt und nicht "
                "gespeichert. Weiter?")
        if not confirm(self.parent, "Löschen", text, yes="Im Browser bestätigen …",
                       no="Abbrechen"):
            return
        login = browser_login_dialog.BrowserLoginDialog(
            cls, url, self.parent, scopes=scopes, title="Recht zum Löschen holen",
            confirm_line=f"Auf der nächsten Seite fragt {self.platform_name}, ob CodeCockpit "
                         "Repositories löschen darf. Bestätigen Sie mit Authorize.")
        if not login.exec() or login.token is None:
            return
        own = (getattr(self.platform, "username", "") or "").lower()
        if own and login.username.lower() != own:
            show_error(self.parent, "Löschen", f"Sie haben sich als {login.username} angemeldet, "
                       f"das Konto im Cockpit ist {own}. Es wurde nichts gelöscht.")
            return
        temporary = cls(url, login.token)          # nur für dieses Löschen, nicht gespeichert
        login.token = None
        ref = self.ref

        def done(_value) -> None:
            temporary.token = None
            self.on_deleted()

        self.worker.run(lambda: temporary.delete(ref), done, speak="Wird gelöscht.")


class TypeNameDialog(FocusDialog):
    """Zur Bestätigung den Namen des Repositories eintippen (Konzept 9.5)."""

    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.name = name
        self.setWindowTitle(f"{name} endgültig löschen")
        self.edit = QLineEdit()
        label = label_for(self.edit, f"Zur Bestätigung den &Namen eintippen: {name}")
        self.ok_button = QPushButton("Endgültig löschen")
        self.ok_button.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.setDefault(True)
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.edit)
        layout.addLayout(_buttons(None, self.ok_button, cancel))
        self.initial_focus_widget = self.edit

    def check(self) -> None:
        if self.edit.text().strip() != self.name:
            show_error(self, self.windowTitle(), NAME_MISMATCH)
            self.edit.setFocus()
            return
        self.accept()
