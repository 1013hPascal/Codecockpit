"""Dialog Grundeinstellungen (Menü Einstellungen).

Einfaches Formular mit "Speichern" und "Abbrechen" (Konzept 13). Bei einem ungültigen Wert
erscheint eine Meldung, danach steht der Fokus im betroffenen Feld.
"""
from __future__ import annotations

from dataclasses import asdict

from PySide6.QtWidgets import QDialogButtonBox, QVBoxLayout, QWidget

from cockpit.core.settings import SettingsStore, setting_fields
from cockpit.ui.common import FocusDialog
from cockpit.ui.error_dialog import show_error
from cockpit.ui.form_builder import FormError, SettingsForm


class SettingsDialog(FocusDialog):
    def __init__(self, store: SettingsStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store
        self.saved_values: dict | None = None
        self.setWindowTitle("Grundeinstellungen")
        self.form = SettingsForm(setting_fields(), asdict(store.load()))
        buttons = QDialogButtonBox()
        self.save_button = buttons.addButton("&Speichern", QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_button = buttons.addButton("Abbrechen",
                                               QDialogButtonBox.ButtonRole.RejectRole)
        self.save_button.setDefault(True)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.form)
        layout.addWidget(buttons)
        self.resize(640, 360)
        first = self.form.first_focus()
        if first is not None:
            first.setFocus()
        self.initial_focus_widget = first

    def save(self) -> None:
        try:
            values = self.form.values()
        except FormError as exc:
            show_error(self, "Eingabe prüfen", exc.message)
            self.form.focus_field(exc.key)
            return
        self.store.update(**values)
        self.saved_values = values
        self.accept()
