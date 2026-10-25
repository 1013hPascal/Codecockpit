"""Die Aktionsliste (Konzept 8.3).

Sie zeigt die Aktionen für den im Baum markierten Eintrag. Nicht verfügbare Aktionen stehen mit
Grund in der Liste ("Exe starten, nicht verfügbar: Im Ordner Release liegt keine Exe."). Enter oder
Leertaste führt die markierte Aktion aus.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from cockpit.core.actions import ActionEntry, shown_entries
from cockpit.ui.common import name_widget

EMPTY_TEXT = "Keine Aktionen"


class ActionList(QListWidget):
    entryTriggered = Signal(object)              # ActionEntry
    explanationRequested = Signal()              # Enter auf "Erklärung: Aktionen" (25.10.2026)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        name_widget(self, "Aktionen")
        self.entries: list[ActionEntry] = []
        # Feature Erklärungen: Text der obersten Zeile, leer ohne Erklärung. Die Markierung
        # startet trotzdem auf der ersten Aktion, die Erklärung steht darüber.
        self.explanation = ""
        self.offset = 0                          # 1, wenn die Erklärung oben steht
        self.itemActivated.connect(self._activated)

    def set_entries(self, entries: list[ActionEntry], keep_selection: bool = False) -> None:
        """Liste neu füllen. keep_selection: nur neu füllen, wenn sich etwas geändert hat, und
        die markierte Aktion behalten (für Änderungen aus dem Hintergrund). Seltene Aktionen
        stehen unter "Weitere …", "Terminal …" zuletzt (20.10.2026)."""
        entries = shown_entries(entries)
        top = [self.explanation] if self.explanation and entries else []
        labels = top + [e.label for e in entries] or [EMPTY_TEXT]
        if keep_selection and labels == self.texts():
            self.entries = list(entries)
            return
        current = self.current_entry()
        keep_id = current.action.id if keep_selection and current is not None else None
        on_explanation = keep_selection and self.on_explanation() and bool(top)
        self.entries = list(entries)
        self.offset = len(top)
        self.clear()
        if not entries:
            self.addItem(QListWidgetItem(EMPTY_TEXT))
        for text in top:
            self.addItem(QListWidgetItem(text))
        for entry in entries:
            item = QListWidgetItem(entry.label)
            item.setData(Qt.ItemDataRole.UserRole, entry.action.id)
            self.addItem(item)
        row = next((i for i, e in enumerate(entries) if e.action.id == keep_id), 0)
        self.setCurrentRow(0 if on_explanation else row + self.offset)

    def texts(self) -> list[str]:
        return [self.item(r).text() for r in range(self.count())]

    def on_explanation(self) -> bool:
        return self.offset > 0 and self.currentRow() == 0

    def row_of_entry(self, index: int) -> int:
        """Zeile in der Liste für den Eintrag Nummer index in entries."""
        return index + self.offset

    def current_entry(self) -> ActionEntry | None:
        row = self.currentRow() - self.offset
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
        if self.on_explanation():
            self.explanationRequested.emit()
            return
        entry = self.current_entry()
        if entry is not None:
            self.entryTriggered.emit(entry)
