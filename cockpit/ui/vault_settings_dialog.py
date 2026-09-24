"""Dialog Tresor-Einstellungen (Menü Konten, Konzept 13).

Oben eine Liste mit dem Zustand des Tresors, darunter die Schaltflächen. Speicherart wechseln,
Master-Passwort ändern und automatisches Sperren gibt es nur, wo es passt.
"""
from __future__ import annotations

from PySide6.QtWidgets import (QFormLayout, QHBoxLayout, QListWidget, QPushButton, QSpinBox,
                               QVBoxLayout, QWidget)

from cockpit.core.errors import CockpitError
from cockpit.core.services import Services
from cockpit.core.text import count
from cockpit.core.vault_service import KINDS
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, label_for, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.password_dialogs import NewPasswordDialog


class VaultSettingsDialog(FocusDialog):
    def __init__(self, services: Services, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.setWindowTitle("Tresor-Einstellungen")

        self.state = QListWidget()
        name_widget(self.state, "Tresor")
        self.switch_button = QPushButton()
        self.switch_button.clicked.connect(self.switch)
        self.password_button = QPushButton("Master-&Passwort ändern …")
        self.password_button.clicked.connect(self.change_password)
        self.auto_lock = QSpinBox()
        self.auto_lock.setRange(0, 480)
        self.auto_lock.setSuffix(" Minuten")
        self.auto_lock.setSpecialValueText("nie")
        self.auto_lock.setValue(services.settings.load().auto_lock_minutes)
        self.auto_lock.valueChanged.connect(self.save_auto_lock)
        close = QPushButton("&Schließen")
        close.setDefault(True)
        close.clicked.connect(self.accept)

        self.lock_row = QWidget()
        lock_form = QFormLayout(self.lock_row)
        lock_form.setContentsMargins(0, 0, 0, 0)
        lock_form.addRow(label_for(self.auto_lock, "&Automatisch sperren nach:"), self.auto_lock)
        buttons = QHBoxLayout()
        buttons.addWidget(self.switch_button)
        buttons.addWidget(self.password_button)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.state)
        layout.addWidget(self.lock_row)
        layout.addLayout(buttons)
        self.resize(640, 320)
        self.refresh()
        self.state.setFocus()
        self.initial_focus_widget = self.state

    def other_kind(self) -> str:
        return "windows" if self.services.vault.kind == "vault_file" else "vault_file"

    def refresh(self) -> None:
        vault = self.services.vault
        lines = [f"Speicherart: {vault.display_name}"]
        if vault.vault is not None:
            if vault.needs_unlock:
                lines.append("Zustand: entsperrt" if vault.is_unlocked() else "Zustand: gesperrt")
            lines.append(f"Gespeicherte Zugangsdaten: "
                         f"{count(len(vault.index.list()), 'Eintrag', 'Einträge')}")
        self.state.clear()
        self.state.addItems(lines)
        self.state.setCurrentRow(0)
        self.switch_button.setText(f"&Wechseln zu {KINDS[self.other_kind()]} …")
        is_file = vault.kind == "vault_file"
        self.password_button.setVisible(is_file)
        self.lock_row.setVisible(is_file)

    def switch(self) -> None:
        if vault_ui.switch_vault(self.services, self.other_kind(), self):
            self.refresh()
        self.switch_button.setFocus()

    def change_password(self) -> None:
        dialog = NewPasswordDialog(ask_old=True, parent=self)
        if dialog.exec():
            try:
                self.services.vault.vault.change_password(dialog.old_password,
                                                          dialog.new_password)
            except CockpitError as exc:
                show_error(self, "Master-Passwort ändern", exc.message, exc.details)
            else:
                announce("Master-Passwort geändert.")
                self.refresh()
        self.password_button.setFocus()

    def save_auto_lock(self, minutes: int) -> None:
        self.services.settings.update(auto_lock_minutes=minutes)
