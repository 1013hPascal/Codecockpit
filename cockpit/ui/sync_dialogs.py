"""Fenster für Änderungen hochladen und holen (Konzept 9.2 und 9.3).

CommitDialog: Was haben Sie geändert? Der Titel nennt die Änderungen kurz, die Liste darunter jede
Datei. Der Fokus beginnt im Feld für die Nachricht, Enter lädt hoch.

ConflictDialog: Dateien mit Konflikt als Liste. Für die markierte Datei: "Meine Fassung
behalten", "Fassung von GitHub übernehmen" oder "Konflikt im Editor anzeigen". Im Editor stehen
über jedem Abschnitt "Meine Fassung" oder "Fassung von GitHub" mit Dateiname und Zeile.
"Erneut prüfen" erkennt im Editor gelöste Dateien daran, dass keine Konfliktmarken mehr darin
stehen. "Zusammenführen abschließen" ist immer erreichbar und sagt, was noch offen ist. Ist der
letzte Konflikt gelöst, springt der Fokus dorthin. Escape wählt "Zusammenführen abbrechen".
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (QHBoxLayout, QLineEdit, QListWidget, QPushButton, QVBoxLayout,
                               QWidget)

from cockpit.core import core_actions, sync
from cockpit.core.errors import CockpitError
from cockpit.core.sync import Changes, ConflictKind
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, PlainEdit, label_for, name_widget
from cockpit.ui.error_dialog import show_error

NO_MESSAGE = "Bitte schreiben Sie kurz, was Sie geändert haben."


class CommitDialog(FocusDialog):
    """Commit-Nachricht. Nach accept() steht sie in message: erste Zeile, Leerzeile, Rest."""

    def __init__(self, title: str, changes: Changes, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{title}: {changes.summary()}")
        self.message = ""
        self.summary = QLineEdit()
        summary_label = label_for(self.summary, "&Was haben Sie geändert?")
        self.details = PlainEdit()
        details_label = label_for(self.details, "&Beschreibung:")
        self.files = QListWidget()
        files_label = label_for(self.files, "Ä&nderungen:")
        self.files.addItems(changes.lines())
        self.files.setCurrentRow(0)
        self.ok_button = QPushButton("&Hochladen")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.ok_button)
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        for widget in (summary_label, self.summary, details_label, self.details, files_label,
                       self.files):
            layout.addWidget(widget)
        layout.addLayout(buttons)
        self.setTabOrder(self.summary, self.details)
        self.setTabOrder(self.details, self.files)
        self.setTabOrder(self.files, self.ok_button)
        self.setTabOrder(self.ok_button, cancel)
        self.resize(600, 420)
        self.initial_focus_widget = self.summary
        self.summary.setFocus()

    def check(self) -> None:
        summary = " ".join(self.summary.text().split())
        if not summary:
            show_error(self, self.windowTitle(), NO_MESSAGE)
            self.summary.setFocus()
            return
        details = self.details.toPlainText().strip()
        self.message = f"{summary}\n\n{details}" if details else summary
        self.accept()


class ConflictDialog(FocusDialog):
    """Konflikte Datei für Datei lösen. accept(): alles gelöst, reject(): abbrechen."""

    def __init__(self, code_dir: Path, kind: ConflictKind, platform_name: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.code_dir = code_dir
        self.kind = kind
        self.platform_name = platform_name
        self.files = sync.conflicted(code_dir)
        self.state: dict[str, str] = {}              # Datei -> "gelöst: …" oder "im Editor"
        self.list = QListWidget()
        name_widget(self.list, "Dateien mit Konflikt")
        self.list.currentRowChanged.connect(lambda _row: self.update_buttons())
        self.mine_button = QPushButton("&Meine Fassung behalten")
        self.mine_button.clicked.connect(lambda: self.choose(True))
        self.theirs_button = QPushButton(f"Fassung von &{platform_name} übernehmen")
        self.theirs_button.clicked.connect(lambda: self.choose(False))
        self.editor_button = QPushButton("Konflikt im &Editor anzeigen")
        self.editor_button.clicked.connect(self.open_current)
        self.recheck_button = QPushButton("E&rneut prüfen")
        self.recheck_button.clicked.connect(self.recheck)
        self.finish_button = QPushButton("Zusammenführen ab&schließen")
        self.finish_button.clicked.connect(self.finish)
        cancel = QPushButton("Zusammenführen abbrechen")
        cancel.clicked.connect(self.reject)
        actions = QHBoxLayout()
        for button in (self.mine_button, self.theirs_button, self.editor_button,
                       self.recheck_button):
            actions.addWidget(button)
        actions.addStretch(1)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(self.finish_button)
        bottom.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(actions)
        layout.addLayout(bottom)
        self.resize(720, 360)
        self.initial_focus_widget = self.list
        # Wie in der Sicherheitsprüfung: Enter in der Liste löst nichts aus, Enter auf einem Knopf
        # genau diesen Knopf.
        self.list.installEventFilter(self)
        self.fill()

    # -- Anzeige ---------------------------------------------------------------------------
    def open_files(self) -> list[str]:
        return [f for f in self.files if not self.state.get(f, "").startswith("gelöst")]

    def line(self, path: str) -> str:
        return f"{path}, {self.state.get(path, 'Konflikt')}"

    def fill(self, row: int = 0) -> None:
        remaining = len(self.open_files())
        what = (f"{count(remaining, 'Konflikt', 'Konflikte')} offen" if remaining
                else "alle Konflikte gelöst")
        self.setWindowTitle(f"Konflikte beim Zusammenführen: {what}")
        self.list.clear()
        self.list.addItems([self.line(f) for f in self.files]
                           or ["Keine Konflikte mehr."])
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))
        self.update_buttons()

    def current(self) -> str | None:
        row = self.list.currentRow()
        return self.files[row] if 0 <= row < len(self.files) else None

    def update_buttons(self) -> None:
        path = self.current()
        unresolved = path is not None and path in self.open_files()
        for button in (self.mine_button, self.theirs_button, self.editor_button):
            button.setEnabled(unresolved)

    def _next_row(self, row: int) -> int:
        """Nächste offene Datei nach row, sonst die erste offene, sonst row."""
        open_files = self.open_files()
        for index in list(range(row + 1, len(self.files))) + list(range(0, row + 1)):
            if self.files[index] in open_files:
                return index
        return row

    def _remaining_text(self) -> str:
        remaining = len(self.open_files())
        return (f"Noch {count(remaining, 'Konflikt', 'Konflikte')}." if remaining
                else "Alle Konflikte gelöst.")

    # -- Knöpfe ----------------------------------------------------------------------------
    def choose(self, keep_mine: bool) -> None:
        path = self.current()
        if path is None or path not in self.open_files():
            return
        try:
            sync.resolve(self.code_dir, path, self.kind, keep_mine)
        except CockpitError as exc:
            show_error(self, "Konflikt lösen", exc.message, exc.details)
            return
        which = "Ihre Fassung" if keep_mine else f"Fassung von {self.platform_name}"
        self.state[path] = f"gelöst: {which}"
        row = self.list.currentRow()
        self.fill(self._next_row(row))
        self._focus_next()
        announce(f"{path}: {which}. {self._remaining_text()}")

    def _focus_next(self) -> None:
        """Ist alles gelöst, geht der Fokus auf "Zusammenführen abschließen", sonst in die
        Liste (Rückmeldung aus dem Test von 5c)."""
        (self.list if self.open_files() else self.finish_button).setFocus()

    def open_current(self) -> None:
        path = self.current()
        if path is None:
            return
        sync.label_conflicts(self.code_dir, path, self.kind, self.platform_name)
        self.state[path] = "im Editor angezeigt, noch Konfliktmarken"
        self.fill(self.list.currentRow())
        core_actions.open_path(self.code_dir / path)

    def recheck(self) -> None:
        """Im Editor bearbeitete Dateien ohne Konfliktmarken gelten als gelöst."""
        row = self.list.currentRow()
        solved = []
        for path in self.open_files():
            if not sync.has_markers(self.code_dir, path) and path in self.state:
                try:
                    sync.mark_resolved(self.code_dir, path)
                except CockpitError as exc:
                    show_error(self, "Konflikt lösen", exc.message, exc.details)
                    return
                self.state[path] = "gelöst: im Editor bearbeitet"
                solved.append(path)
        self.fill(self._next_row(row) if solved else row)
        self._focus_next()
        head = f"Gelöst: {', '.join(solved)}." if solved else "Keine Änderung."
        announce(f"{head} {self._remaining_text()}")

    def eventFilter(self, watched, event) -> bool:
        from PySide6.QtCore import QEvent, Qt
        if watched is self.list and event.type() == QEvent.Type.KeyPress and event.key() in (
                Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return True
        return super().eventFilter(watched, event)

    def finish(self) -> None:
        remaining = self.open_files()
        if not remaining:
            self.accept()
            return
        self.list.setCurrentRow(self.files.index(remaining[0]))
        self.list.setFocus()
        announce(f"Noch nicht fertig. {self._remaining_text()}")
