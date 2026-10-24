"""Konfliktstellen einer Datei: vorlesen und Stelle für Stelle lösen (21.10.2026).

Die Liste nennt jede Stelle mit Zeile und Umfang, zum Beispiel "Stelle 1 von 2, Zeile 7: meine
Fassung 2 Zeilen, GitHub 3 Zeilen". Enter liest die Stelle vor: erst meine Fassung, dann die der
Plattform. Die Knöpfe lösen die markierte Stelle. Ist keine Stelle mehr offen, schließt sich das
Fenster, und die Datei gilt als gelöst.

"Alle Stellen zurückholen" stellt die Konfliktmarken der ganzen Datei wieder her, solange das
Zusammenführen noch läuft. Das ist der Rückweg, falls eine Wahl falsch war.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QHBoxLayout, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import conflicts
from cockpit.core.errors import CockpitError
from cockpit.core.sync import ConflictKind
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, label_for
from cockpit.ui.error_dialog import show_error


class ConflictBlocksDialog(FocusDialog):
    """accept(): keine Stelle mehr offen, reject(): noch Stellen offen oder abgebrochen."""

    def __init__(self, code_dir: Path, path: str, kind: ConflictKind, platform_name: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.code_dir = code_dir
        self.path = path
        self.kind = kind
        self.platform_name = platform_name
        self.blocks: list[conflicts.Block] = []
        self.list = QListWidget()
        list_label = label_for(self.list, "&Stellen:")
        self.list.installEventFilter(self)
        self.mine_button = QPushButton("&Meine Fassung")
        self.mine_button.clicked.connect(lambda: self.choose(conflicts.MINE))
        self.theirs_button = QPushButton(f"Fassung von &{platform_name}")
        self.theirs_button.clicked.connect(lambda: self.choose(conflicts.THEIRS))
        self.both_button = QPushButton("&Beide, meine zuerst")
        self.both_button.clicked.connect(lambda: self.choose(conflicts.BOTH))
        self.editor_button = QPushButton("Stelle im &Editor anzeigen")
        self.editor_button.clicked.connect(self.open_editor)
        restore = QPushButton("Alle Stellen &zurückholen …")
        restore.clicked.connect(self.restore)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        actions = QHBoxLayout()
        for button in (self.mine_button, self.theirs_button, self.both_button):
            actions.addWidget(button)
        actions.addStretch(1)
        bottom = QHBoxLayout()
        bottom.addWidget(self.editor_button)
        bottom.addWidget(restore)
        bottom.addStretch(1)
        bottom.addWidget(close)
        layout = QVBoxLayout(self)
        layout.addWidget(list_label)
        layout.addWidget(self.list, 1)
        layout.addLayout(actions)
        layout.addLayout(bottom)
        self.resize(720, 400)
        self.initial_focus_widget = self.list
        self.fill()

    def fill(self, row: int = 0) -> None:
        try:
            self.blocks = conflicts.blocks(self.code_dir, self.path, self.kind,
                                           self.platform_name)
        except CockpitError as exc:
            show_error(self, "Konfliktstellen", exc.message, exc.details)
            self.blocks = []
        total = len(self.blocks)
        self.setWindowTitle(f"Konfliktstellen in {self.path}: "
                            f"{count(total, 'Stelle', 'Stellen')} offen")
        self.list.clear()
        self.list.addItems([b.label(total) for b in self.blocks] or ["Keine Stellen mehr."])
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))
        for button in (self.mine_button, self.theirs_button, self.both_button):
            button.setEnabled(bool(self.blocks))

    def current(self) -> conflicts.Block | None:
        row = self.list.currentRow()
        return self.blocks[row] if 0 <= row < len(self.blocks) else None

    def eventFilter(self, watched, event) -> bool:
        from cockpit.ui.repo_dialogs import _is_enter
        if watched is self.list and _is_enter(event):
            self.read_current()
            return True
        return super().eventFilter(watched, event)

    def read_current(self) -> None:
        from cockpit.ui.text_dialog import TextDialog
        block = self.current()
        if block is not None:
            TextDialog(block.label(len(self.blocks)), block.readable(), "Konfliktstelle",
                       self).exec()

    def choose(self, choice: str) -> None:
        block = self.current()
        if block is None:
            return
        try:
            left = conflicts.resolve_block(self.code_dir, self.path, block.number, choice,
                                           self.kind)
        except CockpitError as exc:
            show_error(self, "Konfliktstelle lösen", exc.message, exc.details)
            return
        which = {conflicts.MINE: "meine Fassung", conflicts.THEIRS: f"{self.platform_name}",
                 conflicts.BOTH: "beide"}[choice]
        if not left:
            announce(f"Stelle {block.number}: {which}. Keine Stelle mehr offen.")
            self.accept()
            return
        self.fill(self.list.currentRow())
        announce(f"Stelle {block.number}: {which}. Noch {count(left, 'Stelle', 'Stellen')}.")

    def open_editor(self) -> None:
        from cockpit.core import sync
        from cockpit.ui import editor_ui
        # Beschriften ändert nur die Markenzeilen, die Zeilennummern bleiben
        sync.label_conflicts(self.code_dir, self.path, self.kind, self.platform_name)
        block = self.current()
        editor_ui.open_in_editor(self, self.code_dir / self.path,
                                 block.line if block is not None else None)

    def restore(self) -> None:
        if not confirm(self, "Alle Stellen zurückholen",
                       f"Alle Konfliktstellen in {self.path} kommen zurück, so wie Git sie beim "
                       "Zusammenführen angelegt hat. Die Datei, wie sie jetzt ist, kommt vorher "
                       "in eine Sicherheitskopie.", yes="Zurückholen",
                       no="Abbrechen"):
            return
        try:
            conflicts.restore(self.code_dir, self.path)
        except CockpitError as exc:
            show_error(self, "Alle Stellen zurückholen", exc.message, exc.details)
            return
        self.fill()
        announce(f"{count(len(self.blocks), 'Stelle', 'Stellen')} zurückgeholt.")
