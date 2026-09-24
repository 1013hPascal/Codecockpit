"""Fenster mit einem lesbaren Text, zum Beispiel Tastenkürzel, Anleitungen und Einführungen.

Der Fokus steht im Textfeld. Pfeiltasten lesen Zeile für Zeile, Tab führt zu "Schließen",
Escape schließt.
"""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QWidget

from cockpit.ui.common import PlainEdit, name_widget


class TextDialog(QDialog):
    def __init__(self, title: str, text: str, name: str | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.text = PlainEdit()
        self.text.setReadOnly(True)
        self.text.setPlainText(text)
        name_widget(self.text, name or title)
        self.close_button = QPushButton("&Schließen")
        self.close_button.setDefault(True)
        self.close_button.clicked.connect(self.accept)
        layout = QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.close_button)
        self.resize(640, 560)
        self.text.setFocus()
