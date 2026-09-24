"""Fenster, das einen Text als Liste zeigt: eine Zeile pro Eintrag.

Für Tastenkürzel, Anleitungen, "Über" und später die Einführungen der Features. Eine Liste lässt
sich mit NVDA und Braillezeile zuverlässiger lesen als ein schreibgeschütztes Textfeld (Rückmeldung
aus dem Test von Phase 2).

Bedienung: Pfeiltasten lesen Zeile für Zeile, Pos1 und Ende springen an Anfang und Ende,
Strg+C kopiert die markierte Zeile (zum Beispiel einen Befehl), Tab führt zu "Schließen",
Escape schließt.
"""
from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import QDialog, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.ui.announcer import announce
from cockpit.ui.common import name_widget


def text_to_lines(text: str) -> list[str]:
    """Macht aus Text oder Markdown einzelne Zeilen: ohne Leerzeilen, ohne #, ohne Aufzählungs-
    zeichen, ohne Backticks und Sternchen. Nummerierte Schritte behalten ihre Nummer."""
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^[-*]\s+", "", line)
        line = line.replace("`", "").replace("**", "")
        lines.append(line)
    return lines


class TextDialog(QDialog):
    def __init__(self, title: str, text: str | list[str], name: str | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.lines = text if isinstance(text, list) else text_to_lines(text)
        self.list = QListWidget()
        name_widget(self.list, name or title)
        self.list.addItems(self.lines)
        self.list.setCurrentRow(0)
        self.list.setWordWrap(True)
        copy = QShortcut(QKeySequence.StandardKey.Copy, self.list)
        copy.setContext(Qt.ShortcutContext.WidgetShortcut)
        copy.activated.connect(self.copy_current)
        self.close_button = QPushButton("&Schließen")
        self.close_button.setDefault(True)
        self.close_button.clicked.connect(self.accept)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addWidget(self.close_button)
        self.resize(700, 560)
        self.list.setFocus()

    def copy_current(self) -> None:
        item = self.list.currentItem()
        if item is not None:
            QGuiApplication.clipboard().setText(item.text())
            announce("Zeile kopiert.")
