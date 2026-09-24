"""Die Aktionsliste (Konzept 8.3).

Sie zeigt die Aktionen für den im Baum markierten Eintrag. Nicht verfügbare Aktionen stehen mit
Grund in der Liste ("Exe starten, nicht verfügbar: Im Ordner Exe liegt keine Exe."). Enter oder
Leertaste führt die markierte Aktion aus.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from cockpit.core.actions import ActionEntry
from cockpit.ui.common import name_widget

EMPTY_TEXT = "Keine Aktionen"


class ActionList(QListWidget):
    entryTriggered = Signal(object)              # ActionEntry

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        name_widget(self, "Aktionen")
        self.entries: list[ActionEntry] = []
        self.itemActivated.connect(self._activated)

    def set_entries(self, entries: list[ActionEntry]) -> None:
        self.entries = list(entries)
        self.clear()
        if not entries:
            self.addItem(QListWidgetItem(EMPTY_TEXT))
        for entry in entries:
            item = QListWidgetItem(entry.label)
            item.setData(Qt.ItemDataRole.UserRole, entry.action.id)
            self.addItem(item)
        self.setCurrentRow(0)

    def texts(self) -> list[str]:
        return [self.item(r).text() for r in range(self.count())]

    def current_entry(self) -> ActionEntry | None:
        row = self.currentRow()
        return self.entries[row] if 0 <= row < len(self.entries) else None

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Space and not event.modifiers():
            self._activated(self.currentItem())
            event.accept()
            return
        super().keyPressEvent(event)

    def _activated(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        entry = self.current_entry()
        if entry is not None:
            self.entryTriggered.emit(entry)
