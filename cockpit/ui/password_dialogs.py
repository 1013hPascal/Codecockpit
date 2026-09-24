"""Dialoge für das Master-Passwort der Tresordatei (Konzept 5.2).

- UnlockDialog: beim Start und bei "Tresor entsperren". Falsches Passwort: Meldung, Feld leer,
  Fokus zurück ins Feld.
- NewPasswordDialog: Master-Passwort festlegen oder ändern, mit Hinweis, dass ein verlorenes
  Passwort nicht wiederherstellbar ist.

Passwortfelder werden nach jedem Versuch geleert. Die Werte gehen nur als Secret weiter.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QVBoxLayout,
                               QWidget)

from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret
from cockpit.ui.common import FocusDialog, label_for
from cockpit.ui.error_dialog import show_error
from cockpit.vault.vault_file import MIN_PASSWORD_LENGTH, check_new_password

LOSS_HINT = ("Wichtig: Geht das Master-Passwort verloren, lassen sich die Zugangsdaten nicht "
             "wiederherstellen. Sie müssen dann alle neu eingeben.")


def password_field() -> QLineEdit:
    edit = QLineEdit()
    edit.setEchoMode(QLineEdit.EchoMode.Password)
    return edit


def _buttons(dialog, ok_text: str) -> QDialogButtonBox:
    buttons = QDialogButtonBox()
    ok = buttons.addButton(ok_text, QDialogButtonBox.ButtonRole.AcceptRole)
    buttons.addButton("Abbrechen", QDialogButtonBox.ButtonRole.RejectRole)
    ok.setDefault(True)
    buttons.rejected.connect(dialog.reject)
    return buttons


class UnlockDialog(FocusDialog):
    """unlock bekommt das Passwort als Secret und wirft CockpitError, wenn es falsch ist."""

    def __init__(self, unlock: Callable[[Secret], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.unlock = unlock
        self.setWindowTitle("Tresor entsperren")
        self.password = password_field()
        form = QFormLayout()
        form.addRow(label_for(self.password, "&Master-Passwort:"), self.password)
        buttons = _buttons(self, "&Entsperren")
        buttons.accepted.connect(self.try_unlock)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.password.setFocus()
        self.initial_focus_widget = self.password

    def try_unlock(self) -> None:
        secret = Secret(self.password.text())
        self.password.clear()
        try:
            self.unlock(secret)
        except CockpitError as exc:
            show_error(self, "Tresor entsperren", exc.message, exc.details)
            self.password.setFocus()
            return
        self.accept()


class NewPasswordDialog(FocusDialog):
    """Neues Master-Passwort festlegen (ask_old=False) oder ändern (ask_old=True).
    Nach accept stehen die Werte in old_password und new_password."""

    def __init__(self, ask_old: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Master-Passwort ändern" if ask_old else "Master-Passwort festlegen")
        self.old_password: Secret | None = None
        self.new_password: Secret | None = None
        self.old = password_field() if ask_old else None
        self.new = password_field()
        self.repeat = password_field()
        hint = QLabel(f"Mindestens {MIN_PASSWORD_LENGTH} Zeichen. {LOSS_HINT}")
        hint.setWordWrap(True)
        form = QFormLayout()
        if self.old is not None:
            form.addRow(label_for(self.old, "&Bisheriges Master-Passwort:"), self.old)
        form.addRow(label_for(self.new, "&Neues Master-Passwort:"), self.new)
        form.addRow(label_for(self.repeat, "Neues Passwort &wiederholen:"), self.repeat)
        buttons = _buttons(self, "&Speichern")
        buttons.accepted.connect(self.check)
        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addLayout(form)
        layout.addWidget(buttons)
        first = self.old if self.old is not None else self.new
        first.setFocus()
        self.initial_focus_widget = first

    def check(self) -> None:
        new, repeated = Secret(self.new.text()), Secret(self.repeat.text())
        old = Secret(self.old.text()) if self.old is not None else None
        try:
            check_new_password(new, repeated)
        except CockpitError as exc:
            self.new.clear()
            self.repeat.clear()
            show_error(self, self.windowTitle(), exc.message)
            self.new.setFocus()
            return
        self.old_password, self.new_password = old, new
        for field in (self.old, self.new, self.repeat):
            if field is not None:
                field.clear()
        self.accept()
