"""Fenster für Änderungen hochladen und holen (Konzept 9.2 und 9.3).

CommitDialog: Was haben Sie geändert? Der Titel nennt die Änderungen kurz, die Liste darunter jede
Datei. Der Fokus beginnt im Feld für die Nachricht, Enter lädt hoch.

ConflictDialog: Dateien mit Konflikt als Liste. Für die markierte Datei: "Stellen lesen und
lösen" (auch mit Enter, siehe conflict_dialogs.py), "Meine Fassung behalten", "Fassung von GitHub
übernehmen" oder "Konflikt im Editor anzeigen". Im Editor stehen
über jedem Abschnitt "Meine Fassung" oder "Fassung von GitHub" mit Dateiname und Zeile.
"Erneut prüfen" erkennt im Editor gelöste Dateien daran, dass keine Konfliktmarken mehr darin
stehen. "Zusammenführen abschließen" ist immer erreichbar und sagt, was noch offen ist. Ist der
letzte Konflikt gelöst, springt der Fokus dorthin. Escape wählt "Zusammenführen abbrechen".
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout, QWidget)

from cockpit.core import sync
from cockpit.core.errors import CockpitError
from cockpit.core.sync import Changes, ConflictKind
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, PlainEdit, label_for, name_widget
from cockpit.ui.error_dialog import show_error

NO_MESSAGE = "Bitte schreiben Sie kurz, was Sie geändert haben."
NOTHING_CHOSEN = ("Es ist keine Datei angehakt. Haken Sie mit der Leertaste an, was in den Commit "
                  "soll.")


class CommitDialog(FocusDialog):
    """Commit-Nachricht. Nach accept() steht sie in message: erste Zeile, Leerzeile, Rest."""

    def __init__(self, title: str, changes: Changes, parent: QWidget | None = None,
                 source=None, code_dir: Path | None = None) -> None:
        """source: Vorschlag der KI (Feature KI-Assistent), None: kein Knopf. code_dir: Ordner
        für die Abschnitte der Dateien, None: nur ganze Dateien wählbar."""
        super().__init__(parent)
        self.setWindowTitle(f"{title}: {changes.summary()}")
        self.message = ""
        self.summary = QLineEdit()
        summary_label = label_for(self.summary, "&Was haben Sie geändert?")
        self.details = PlainEdit()
        details_label = label_for(self.details, "&Beschreibung:")
        self.suggest_button = None
        if source is not None:
            from cockpit.ui.ai_suggest import SuggestButton
            self.suggest_button = SuggestButton(self, source, self.apply_suggestion,
                                                self.summary)
        # Wunsch des Nutzers vom 21.10.2026: Dateien abhaken, Enter zeigt die Abschnitte einer
        # Datei. Was nicht angehakt ist, bleibt für einen späteren Commit.
        self.changes = changes
        self.code_dir = code_dir
        self.kinds = changes.kinds()
        self.chosen_hunks: dict[str, set[int]] = {}       # Datei -> gewählte Abschnitte
        self.hunk_counts: dict[str, int] = {}
        self.files = QListWidget()
        files_label = label_for(self.files, "Ä&nderungen:")
        for line, path in zip(changes.lines(), self._paths()):
            item = QListWidgetItem(line)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.files.addItem(item)
        self.files.setCurrentRow(0)
        self.files.installEventFilter(self)
        # Co-Autoren (21.10.2026): Personen, die mitgearbeitet haben, aus dem Verlauf wählen
        self.coauthors: list[str] = []
        self.coauthors_button = None
        if code_dir is not None:
            self.coauthors_button = QPushButton("Co-&Autoren …")
            self.coauthors_button.clicked.connect(self.choose_coauthors)
        self.ok_button = QPushButton("&Hochladen")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        if self.coauthors_button is not None:
            buttons.addWidget(self.coauthors_button)
        buttons.addStretch(1)
        buttons.addWidget(self.ok_button)
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        for widget in (summary_label, self.summary, details_label, self.details):
            layout.addWidget(widget)
        if self.suggest_button is not None:
            row = QHBoxLayout()
            row.addWidget(self.suggest_button)
            row.addStretch(1)
            layout.addLayout(row)
        for widget in (files_label, self.files):
            layout.addWidget(widget)
        layout.addLayout(buttons)
        order = [self.summary, self.details, self.suggest_button, self.files,
                 self.coauthors_button, self.ok_button, cancel]
        order = [w for w in order if w is not None]
        for first, second in zip(order, order[1:]):
            self.setTabOrder(first, second)
        self.resize(600, 460)
        self.initial_focus_widget = self.summary
        self.summary.setFocus()

    def apply_suggestion(self, suggestion) -> None:
        self.summary.setText(suggestion.summary)
        self.details.setPlainText(suggestion.details)

    # -- Auswahl der Dateien und Abschnitte (21.10.2026) ------------------------------------
    def _paths(self) -> list[str]:
        """Pfade in derselben Reihenfolge wie Changes.lines()."""
        c = self.changes
        return c.modified + c.added + c.deleted + c.renamed

    def eventFilter(self, watched, event) -> bool:
        from cockpit.ui.repo_dialogs import _is_enter
        if watched is self.files and _is_enter(event):
            self.show_file()
            return True
        return super().eventFilter(watched, event)

    def show_file(self) -> None:
        """Enter auf einer Datei: ihre Abschnitte zum Wählen, bei neuen Dateien der Inhalt."""
        from cockpit.core import staging
        from cockpit.ui.text_dialog import TextDialog
        item = self.files.currentItem()
        if item is None:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        kind = self.kinds.get(path, "geändert")
        if self.code_dir is None:
            announce("Hier lassen sich nur ganze Dateien wählen.")
            return
        diff = staging.file_diff(self.code_dir, path, kind)
        if not diff.partial_possible:
            lines = diff.text or [line for h in diff.hunks for line in h.readable()] or [
                f"{path}: {diff.summary()}."]
            TextDialog(f"Änderungen an {path}", lines, "Änderungen", self).exec()
            return
        dialog = HunksDialog(diff, self.chosen_hunks.get(path), self)
        if not dialog.exec():
            return
        self.hunk_counts[path] = len(diff.hunks)
        chosen = dialog.chosen
        self.chosen_hunks[path] = chosen
        item.setCheckState(Qt.CheckState.Checked if chosen else Qt.CheckState.Unchecked)
        base = item.text().split(", ")[0] + ", " + kind
        item.setText(base if len(chosen) in (0, len(diff.hunks)) else
                     f"{base}, {len(chosen)} von {len(diff.hunks)} Abschnitten")
        announce(f"{len(chosen)} von {len(diff.hunks)} Abschnitten gewählt.")

    @property
    def selection(self):
        """None: alles, wie früher. Sonst Pfad -> None (ganze Datei) oder Abschnitte."""
        result = {}
        everything = True
        for row in range(self.files.count()):
            item = self.files.item(row)
            path = item.data(Qt.ItemDataRole.UserRole)
            if item.checkState() != Qt.CheckState.Checked:
                everything = False
                continue
            chosen = self.chosen_hunks.get(path)
            # Leere Auswahl, aber wieder angehakt: dann gilt die ganze Datei
            if chosen and len(chosen) < self.hunk_counts.get(path, 0):
                everything = False
                result[path] = set(chosen)
            else:
                result[path] = None
        return None if everything else result

    def reject(self) -> None:
        from cockpit.ui.ai_suggest import handle_escape
        if not handle_escape(self.suggest_button):
            super().reject()

    def done(self, code: int) -> None:
        if self.suggest_button is not None:
            self.suggest_button.wait()
        super().done(code)

    def check(self) -> None:
        summary = " ".join(self.summary.text().split())
        if not summary:
            show_error(self, self.windowTitle(), NO_MESSAGE)
            self.summary.setFocus()
            return
        if self.selection == {}:
            show_error(self, self.windowTitle(), NOTHING_CHOSEN)
            self.files.setFocus()
            return
        details = self.details.toPlainText().strip()
        self.message = sync.with_coauthors(f"{summary}\n\n{details}" if details else summary,
                                           self.coauthors)
        self.accept()

    def choose_coauthors(self) -> None:
        people = sync.known_people(self.code_dir)
        if not people:
            announce("Im Verlauf gibt es noch keine anderen Personen.")
            return
        dialog = CheckListDialog("Co-Autoren", "&Personen:", people, set(self.coauthors), self)
        if not dialog.exec():
            return
        self.coauthors = dialog.chosen
        self.coauthors_button.setText(f"Co-&Autoren ({len(self.coauthors)}) …"
                                      if self.coauthors else "Co-&Autoren …")
        announce(f"{count(len(self.coauthors), 'Co-Autor', 'Co-Autoren')} gewählt.")


class CheckListDialog(FocusDialog):
    """Einträge mit Kästchen, Leertaste hakt an. Nach accept() stehen die angehakten in chosen."""

    def __init__(self, title: str, label: str, items: list[str], checked: set[str],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.items = items
        self.chosen: list[str] = []
        self.list = QListWidget()
        list_label = label_for(self.list, label)
        for text in items:
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if text in checked
                               else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        ok = QPushButton("Ü&bernehmen")
        ok.setDefault(True)
        ok.clicked.connect(self.take)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(list_label)
        layout.addWidget(self.list, 1)
        layout.addLayout(buttons)
        self.resize(520, 380)
        self.initial_focus_widget = self.list

    def take(self) -> None:
        self.chosen = [self.items[r] for r in range(self.list.count())
                       if self.list.item(r).checkState() == Qt.CheckState.Checked]
        self.accept()


class HunksDialog(FocusDialog):
    """Die Abschnitte einer Datei mit Kästchen. Leertaste hakt an oder ab, Enter liest den
    Abschnitt vor. Nach accept() stehen die gewählten Nummern in chosen."""

    def __init__(self, diff, chosen: set[int] | None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.diff = diff
        self.chosen: set[int] = set()
        self.setWindowTitle(f"Abschnitte von {diff.path}")
        self.list = QListWidget()
        label = label_for(self.list, "&Abschnitte:")
        for hunk in diff.hunks:
            item = QListWidgetItem(hunk.label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if chosen is None or hunk.number in chosen
                               else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        self.list.installEventFilter(self)
        ok = QPushButton("Ü&bernehmen")
        ok.clicked.connect(self.take)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.list, 1)
        layout.addLayout(buttons)
        self.resize(600, 400)
        self.initial_focus_widget = self.list

    def eventFilter(self, watched, event) -> bool:
        from cockpit.ui.repo_dialogs import _is_enter
        if watched is self.list and _is_enter(event):
            self.read_current()
            return True
        return super().eventFilter(watched, event)

    def read_current(self) -> None:
        from cockpit.ui.text_dialog import TextDialog
        row = self.list.currentRow()
        if 0 <= row < len(self.diff.hunks):
            hunk = self.diff.hunks[row]
            TextDialog(hunk.label, hunk.readable(), "Abschnitt", self).exec()

    def take(self) -> None:
        self.chosen = {hunk.number for row, hunk in enumerate(self.diff.hunks)
                       if self.list.item(row).checkState() == Qt.CheckState.Checked}
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
        # 21.10.2026: Enter oder "Stellen lesen" liest die Konfliktstellen einzeln vor
        self.blocks_button = QPushButton("Stellen &lesen und lösen …")
        self.blocks_button.clicked.connect(self.read_blocks)
        self.editor_button = QPushButton("Konflikt im &Editor anzeigen")
        self.editor_button.clicked.connect(self.open_current)
        self.recheck_button = QPushButton("E&rneut prüfen")
        self.recheck_button.clicked.connect(self.recheck)
        self.finish_button = QPushButton("Zusammenführen ab&schließen")
        self.finish_button.clicked.connect(self.finish)
        cancel = QPushButton("Zusammenführen abbrechen")
        cancel.clicked.connect(self.reject)
        actions = QHBoxLayout()
        for button in (self.blocks_button, self.mine_button, self.theirs_button,
                       self.editor_button, self.recheck_button):
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
        # Enter in der Liste öffnet die Konfliktstellen der Datei (21.10.2026), Enter auf einem
        # Knopf genau diesen Knopf.
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
        for button in (self.blocks_button, self.mine_button, self.theirs_button,
                       self.editor_button):
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
        from cockpit.core import conflicts
        from cockpit.ui import editor_ui
        sync.label_conflicts(self.code_dir, path, self.kind, self.platform_name)
        self.state[path] = "im Editor angezeigt, noch Konfliktmarken"
        self.fill(self.list.currentRow())
        try:
            found = conflicts.blocks(self.code_dir, path, self.kind, self.platform_name)
        except CockpitError:
            found = []
        # Der Editor springt zur ersten Konfliktstelle
        editor_ui.open_in_editor(self, self.code_dir / path, found[0].line if found else None)

    def read_blocks(self) -> None:
        """Die Konfliktstellen der markierten Datei einzeln vorlesen und lösen."""
        from cockpit.ui.conflict_dialogs import ConflictBlocksDialog
        path = self.current()
        if path is None or path not in self.open_files():
            return
        if not sync.has_markers(self.code_dir, path):
            announce("In dieser Datei gibt es keine Konfliktstellen. Wählen Sie eine Fassung.")
            return
        dialog = ConflictBlocksDialog(self.code_dir, path, self.kind, self.platform_name, self)
        dialog.exec()
        row = self.list.currentRow()
        if sync.has_markers(self.code_dir, path):
            self.state[path] = "Stellen teilweise gelöst"
            self.fill(row)
            self.list.setFocus()
            return
        try:
            sync.mark_resolved(self.code_dir, path)
        except CockpitError as exc:
            show_error(self, "Konflikt lösen", exc.message, exc.details)
            return
        self.state[path] = "gelöst: Stelle für Stelle"
        self.fill(self._next_row(row))
        self._focus_next()
        announce(f"{path} gelöst. {self._remaining_text()}")

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
            self.read_blocks()
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
