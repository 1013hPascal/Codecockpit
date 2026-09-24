"""Fehlerfenster: einfacher Text, auf Wunsch technische Details (Konzept 8.6).

Aufbau wie ein normales Meldungsfenster: oben der Text, darunter "Details anzeigen" (nur wenn es
Details gibt) und "OK". Der Fokus steht auf "OK", NVDA liest beim Öffnen den Text des Fensters.
Zusätzlich wird die Meldung vorher dringend angesagt. "Details anzeigen" öffnet eine Liste mit
einer Zeile pro Detailzeile und setzt den Fokus hinein.
"""
from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QListWidget, QPushButton,
                               QVBoxLayout, QWidget)

from cockpit.core.logging_setup import mask_secrets
from cockpit.ui.common import name_widget


class ErrorDialog(QDialog):
    def __init__(self, title: str, message: str, details: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)

        self.message = QLabel(message)
        self.message.setWordWrap(True)

        self.details = QListWidget()
        self.details.addItems([line for line in mask_secrets(details).splitlines()
                               if line.strip()])
        self.details.setCurrentRow(0)
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
        QWidget.setTabOrder(self.ok_button, self.details_button)
        QWidget.setTabOrder(self.details_button, self.details)
        self.resize(560, 200)
        self.ok_button.setFocus()

    def toggle_details(self) -> None:
        if self.details.isVisible():
            self.details.hide()
            self.details_button.setText("&Details anzeigen")
            self.details_button.setFocus()
        else:
            self.details.show()
            self.details_button.setText("&Details ausblenden")
            self.resize(self.width(), max(self.height(), 420))
            self.details.setFocus()


def show_error(parent: QWidget | None, title: str, message: str, details: str = "") -> None:
    ErrorDialog(title, message, details, parent).exec()
