"""Fenster "Sicherheitskopien" im Menü Datei (Wunsch aus dem Test von 5c).

BackupsDialog: alle Sicherheitskopien, die neueste oben, zum Beispiel "25.09.2026 14:03, Tagebuch,
vor dem Holen, 1 Datei". Knöpfe: "Dateien anzeigen …", "Im Explorer öffnen", "Löschen …".
BackupFilesDialog: die Dateien einer Kopie. Knöpfe: "Datei öffnen", "Wiederherstellen …".

Wiederherstellen beschreibt vorher, was passiert, braucht eine Bestätigung und legt von der
jetzigen Datei vorher selbst eine Sicherheitskopie an (CLAUDE.md). Wie in der Sicherheitsprüfung
löst Enter in der Liste nichts aus, Enter auf einem Knopf genau diesen Knopf. Knöpfe sind nie
ausgegraut, damit man sie mit Tab findet. Passen sie nicht, sagen sie den Grund.
"""
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import backups, core_actions
from cockpit.core.backups import BackupInfo
from cockpit.core.errors import CockpitError
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, name_widget
from cockpit.ui.error_dialog import show_error

TITLE = "Sicherheitskopien"


class _ListDialog(FocusDialog):
    """Liste mit Knöpfen darunter. Enter in der Liste tut nichts."""

    def __init__(self, list_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.list = QListWidget()
        name_widget(self.list, list_name)
        self.list.installEventFilter(self)
        self.buttons = QHBoxLayout()
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        self.close_button = close
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(self.buttons)
        self.initial_focus_widget = self.list

    def add_button(self, text: str, slot) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(slot)
        self.buttons.addWidget(button)
        return button

    def finish_buttons(self) -> None:
        self.buttons.addStretch(1)
        self.buttons.addWidget(self.close_button)

    def eventFilter(self, watched, event) -> bool:
        from PySide6.QtCore import QEvent, Qt
        if watched is self.list and event.type() == QEvent.Type.KeyPress and event.key() in (
                Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return True
        return super().eventFilter(watched, event)


class BackupsDialog(_ListDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Sicherheitskopien", parent)
        self.items: list[BackupInfo] = []
        self.add_button("&Dateien anzeigen …", self.show_files)
        self.add_button("Im E&xplorer öffnen", self.open_folder)
        self.add_button("&Löschen …", self.delete_current)
        self.finish_buttons()
        self.resize(640, 400)
        self.fill()

    def fill(self, row: int = 0) -> None:
        self.items = backups.all_backups()
        self.setWindowTitle(f"{TITLE}: {count(len(self.items), 'Kopie', 'Kopien')}")
        self.list.clear()
        self.list.addItems([i.line() for i in self.items] or ["Keine Sicherheitskopien."])
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))

    def current(self) -> BackupInfo | None:
        row = self.list.currentRow()
        if 0 <= row < len(self.items):
            return self.items[row]
        announce("Es gibt keine Sicherheitskopie.")
        return None

    def show_files(self) -> None:
        info = self.current()
        if info is not None:
            BackupFilesDialog(info, self).exec()
            self.fill(self.list.currentRow())
            self.list.setFocus()

    def open_folder(self) -> None:
        info = self.current()
        if info is not None:
            core_actions.open_path(info.path)
            announce("Wird im Explorer geöffnet.")

    def delete_current(self) -> None:
        info = self.current()
        if info is None:
            return
        if not confirm(self, "Sicherheitskopie löschen",
                       f"Die Sicherheitskopie vom {info.created:%d.%m.%Y %H:%M} zu {info.project} "
                       f"mit {count(len(info.files()), 'Datei', 'Dateien')} wird endgültig "
                       "gelöscht. Löschen?", yes="Löschen", no="Abbrechen"):
            return
        row = self.list.currentRow()
        try:
            backups.delete(info)
        except CockpitError as exc:
            show_error(self, "Sicherheitskopie löschen", exc.message, exc.details)
            self.fill(row)
            return
        self.fill(row)
        self.list.setFocus()
        announce("Sicherheitskopie gelöscht.")


class BackupFilesDialog(_ListDialog):
    def __init__(self, info: BackupInfo, parent: QWidget | None = None) -> None:
        super().__init__("Dateien", parent)
        self.info = info
        self.files = info.files()
        where = f", aus {info.source_dir}" if info.source_dir else ""
        self.setWindowTitle(f"{info.line()}{where}")
        self.list.addItems(self.files or ["Keine Dateien."])
        self.list.setCurrentRow(0)
        self.add_button("Datei ö&ffnen", self.open_current)
        self.add_button("&Wiederherstellen …", self.restore_current)
        self.finish_buttons()
        self.resize(640, 400)

    def current(self) -> str | None:
        row = self.list.currentRow()
        if 0 <= row < len(self.files):
            return self.files[row]
        announce("Es gibt keine Datei.")
        return None

    def open_current(self) -> None:
        relative = self.current()
        if relative is not None:
            core_actions.open_path(self.info.path / relative)

    def restore_current(self) -> None:
        relative = self.current()
        if relative is None:
            return
        try:
            target = backups.restore_target(self.info, relative)
        except CockpitError as exc:
            show_error(self, "Wiederherstellen", exc.message)
            return
        now = (" Die jetzige Datei kommt vorher selbst als Sicherheitskopie in den Ordner "
               "backups." if target.exists() else " Dort gibt es die Datei zurzeit nicht.")
        if not confirm(self, "Wiederherstellen",
                       f"{relative} aus der Sicherheitskopie vom "
                       f"{self.info.created:%d.%m.%Y %H:%M} kommt zurück nach {target}.{now} "
                       "Wiederherstellen?", yes="Wiederherstellen", no="Abbrechen"):
            return
        try:
            backups.restore(self.info, relative)
        except (CockpitError, OSError) as exc:
            message = exc.message if isinstance(exc, CockpitError) else (
                f"{relative} ließ sich nicht wiederherstellen.")
            show_error(self, "Wiederherstellen", message, getattr(exc, "details", repr(exc)))
            return
        self.list.setFocus()
        announce(f"{relative} wiederhergestellt.")
