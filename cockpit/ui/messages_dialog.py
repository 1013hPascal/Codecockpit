"""Liste der letzten Meldungen, neueste oben (Strg+Umschalt+L).

Jede Zeile beginnt mit dem Text, die Uhrzeit steht am Ende. Escape schließt.
"""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.ui.announcer import Message
from cockpit.ui.common import name_widget


class MessagesDialog(QDialog):
    def __init__(self, messages: list[Message], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Meldungen")
        self.list = QListWidget()
        name_widget(self.list, "Meldungen")
        if messages:
            self.list.addItems([m.label for m in messages])
        else:
            self.list.addItem("Es gibt noch keine Meldung.")
        self.list.setCurrentRow(0)
        close = QPushButton("&Schließen")
        close.setDefault(True)
        close.clicked.connect(self.accept)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addWidget(close)
        self.resize(640, 480)
        self.list.setFocus()
