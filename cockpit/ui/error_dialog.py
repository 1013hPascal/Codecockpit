"""Fehlerfenster: einfacher Text, auf Wunsch technische Details (Konzept 8.6).

Aufbau: Textfeld "Meldung" (ein Satz je Zeile), Schaltfläche "Details anzeigen" (nur wenn es
Details gibt) und "OK". "Details anzeigen" öffnet ein zweites Textfeld und setzt den Fokus
hinein. Escape und Enter schließen.
"""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from cockpit.core.logging_setup import mask_secrets
from cockpit.core.text import one_sentence_per_line
from cockpit.ui.common import PlainEdit, name_widget


class ErrorDialog(QDialog):
    def __init__(self, title: str, message: str, details: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)

        self.message = PlainEdit()
        self.message.setReadOnly(True)
        self.message.setPlainText(one_sentence_per_line(message))
        self.message.setMaximumHeight(140)
        name_widget(self.message, "Meldung")

        self.details = PlainEdit()
        self.details.setReadOnly(True)
        self.details.setPlainText(mask_secrets(details))
        name_widget(self.details, "Details")
        self.details.hide()

        self.details_button = QPushButton("&Details anzeigen")
        self.details_button.clicked.connect(self.toggle_details)
        self.details_button.setVisible(bool(details.strip()))
        self.ok_button = QPushButton("OK")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)

        buttons = QHBoxLayout()
        buttons.addWidget(self.details_button)
        buttons.addStretch(1)
        buttons.addWidget(self.ok_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.message)
        layout.addWidget(self.details, 1)
        layout.addLayout(buttons)
        QWidget.setTabOrder(self.message, self.details)
        QWidget.setTabOrder(self.details, self.details_button)
        QWidget.setTabOrder(self.details_button, self.ok_button)
        self.resize(560, 260)
        self.message.setFocus()

    def toggle_details(self) -> None:
        if self.details.isVisible():
            self.details.hide()
            self.details_button.setText("&Details anzeigen")
            self.details_button.setFocus()
        else:
            self.details.show()
            self.details_button.setText("&Details ausblenden")
            self.resize(self.width(), max(self.height(), 460))
            self.details.setFocus()


def show_error(parent: QWidget | None, title: str, message: str, details: str = "") -> None:
    ErrorDialog(title, message, details, parent).exec()
