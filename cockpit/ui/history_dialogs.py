"""Fenster für Verlauf und Rückgängig machen (Konzept 9.4 und 9.7, Teilschritt 5d).

HistoryDialog: alle Versionen, neueste oben, zum Beispiel "23.09.2026, Version 1.4.0: Suche
ergänzt". Enter zeigt die Details.
VersionDialog: Angaben und geänderte Dateien einer Version. Per Tab: "Datei wiederherstellen …",
"Version rückgängig machen …" und beim neuesten Commit, solange er nicht hochgeladen ist, "Commit
zurücknehmen …".
DiscardDialog: Änderungen ohne Commit als Liste mit Kontrollkästchen. Leertaste wählt aus.

Alles, was Dateien verändert, beschreibt vorher, was passiert, braucht eine Bestätigung und legt
eine Sicherheitskopie an. Vorgabe ist immer "Abbrechen". Wie in den anderen Listen mit Knöpfen löst
Enter in Angaben, Dateien und Änderungen nichts aus, Enter auf einem Knopf genau diesen Knopf.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout, QWidget)

from cockpit.core import history
from cockpit.core.errors import CockpitError
from cockpit.core.history import Commit, LocalChange
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, label_for, make_copyable, name_widget
from cockpit.ui.error_dialog import show_error

if TYPE_CHECKING:
    from cockpit.core.projects import Project
    from cockpit.core.services import Services

NO_CHOICE = "Bitte wählen Sie mit der Leertaste mindestens eine Datei aus."
BACKUP_NOTE = "Vorher kommen die betroffenen Dateien als Sicherheitskopie in den Ordner backups."


def _ignore_enter(dialog: FocusDialog, watched, event, lists) -> bool:
    from PySide6.QtCore import QEvent
    return (watched in lists and event.type() == QEvent.Type.KeyPress
            and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter))


class HistoryDialog(FocusDialog):
    """Verlauf eines Projekts. Nach dem Schließen: changed ist True, wenn sich Dateien oder der
    Verlauf geändert haben."""

    def __init__(self, services: "Services", project: "Project", commits: list[Commit],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.project = project
        self.commits = commits
        self.changed = False
        self.list = QListWidget()
        name_widget(self.list, "Versionen")
        self.list.itemActivated.connect(lambda _item: self.show_details())
        details = QPushButton("&Details anzeigen …")
        details.clicked.connect(self.show_details)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(details)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(buttons)
        self.resize(720, 460)
        self.initial_focus_widget = self.list
        self.fill()

    def fill(self, row: int = 0) -> None:
        self.setWindowTitle(f"Verlauf von {self.project.name}: "
                            f"{count(len(self.commits), 'Version', 'Versionen')}")
        self.list.clear()
        self.list.addItems([c.line() for c in self.commits] or ["Noch keine Versionen."])
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))

    def reload(self, row: int = 0) -> None:
        try:
            self.commits = history.log_commits(self.project.code_dir)
        except CockpitError as exc:
            show_error(self, "Verlauf", exc.message, exc.details)
        self.fill(row)

    def current(self) -> Commit | None:
        row = self.list.currentRow()
        return self.commits[row] if 0 <= row < len(self.commits) else None

    def show_details(self) -> None:
        commit = self.current()
        if commit is None:
            announce("Es gibt noch keine Version.")
            return
        try:
            dialog = VersionDialog(self.services, self.project, commit, self)
        except CockpitError as exc:
            show_error(self, "Verlauf", exc.message, exc.details)
            return
        dialog.exec()
        self.changed |= dialog.files_changed or dialog.history_changed
        if dialog.history_changed:
            self.reload(0)                  # der neue oder zurückgenommene Commit ist oben
        self.list.setFocus()


class VersionDialog(FocusDialog):
    def __init__(self, services: "Services", project: "Project", commit: Commit,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.project = project
        self.commit = commit
        self.code_dir: Path = project.code_dir
        self.files_changed = False
        self.history_changed = False
        self.changes = history.commit_files(self.code_dir, commit)
        self.paths = [line.rpartition(", ")[0] for line in self.changes.lines()]
        self.setWindowTitle(commit.line())
        steps = history.recorded_steps(services.database, project.id, commit.sha)
        self.info = QListWidget()
        name_widget(self.info, "Angaben")
        make_copyable(self.info)
        self.info.addItems(history.details(commit, steps))
        self.info.setCurrentRow(0)
        self.info.setWordWrap(True)
        self.files = QListWidget()
        files_label = label_for(self.files, f"&Dateien, {self.changes.summary()}:")
        self.files.addItems(self.changes.lines() or ["Keine Dateien geändert."])
        self.files.setCurrentRow(0)
        buttons = QHBoxLayout()
        restore = QPushButton("Datei &wiederherstellen …")
        restore.clicked.connect(self.restore_current)
        revert = QPushButton("Version &rückgängig machen …")
        revert.clicked.connect(self.revert)
        buttons.addWidget(restore)
        buttons.addWidget(revert)
        self.undo_button = None
        if history.can_undo(commit):
            self.undo_button = QPushButton("Commit &zurücknehmen …")
            self.undo_button.clicked.connect(self.undo)
            buttons.addWidget(self.undo_button)
        buttons.addStretch(1)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        buttons.addWidget(close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.info, 1)
        layout.addWidget(files_label)
        layout.addWidget(self.files, 1)
        layout.addLayout(buttons)
        self.resize(720, 520)
        self.initial_focus_widget = self.info
        for widget in (self.info, self.files):
            widget.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        if _ignore_enter(self, watched, event, (self.info, self.files)):
            return True
        return super().eventFilter(watched, event)

    def _when(self) -> str:
        return f"vom {self.commit.date:%d.%m.%Y} „{self.commit.subject}“"

    # -- Datei wiederherstellen --------------------------------------------------------------
    def current_path(self) -> str | None:
        row = self.files.currentRow()
        if 0 <= row < len(self.paths):
            return self.paths[row]
        announce("Es gibt keine Datei.")
        return None

    def restore_current(self) -> None:
        path = self.current_path()
        if path is None:
            return
        deleted = path in self.changes.deleted
        if deleted:
            what = (f"{path} wurde in der Version {self._when()} gelöscht. Die Datei kommt mit dem "
                    "Stand direkt davor zurück.")
        else:
            what = f"{path} kommt auf den Stand der Version {self._when()}."
        now = (" Die jetzige Datei kommt vorher als Sicherheitskopie in den Ordner backups."
               if (self.code_dir / path).is_file() else "")
        text = (f"{what}{now} Danach ist das eine normale Änderung, die Sie wie gewohnt hochladen. "
                "Wiederherstellen?")
        if not confirm(self, "Datei wiederherstellen", text, yes="Wiederherstellen",
                       no="Abbrechen"):
            return
        try:
            history.restore_file(self.code_dir, self.project.name, self.commit, path,
                                 self.changes)
        except CockpitError as exc:
            show_error(self, "Datei wiederherstellen", exc.message, exc.details)
            return
        self.files_changed = True
        self.files.setFocus()
        announce(f"{path} wiederhergestellt.")

    # -- Version rückgängig machen -----------------------------------------------------------
    def revert(self) -> None:
        title = "Version rückgängig machen"
        if self.commit.is_merge or not self.commit.parents:
            try:
                history.revert(self.code_dir, self.project.name, self.commit)
            except CockpitError as exc:
                show_error(self, title, exc.message, exc.details)
            return
        text = (f"Das Cockpit erstellt einen neuen Commit „{history.revert_message(self.commit)}“. "
                f"Er hebt die Änderungen der Version {self._when()} auf: "
                f"{self.changes.summary()}. Der Verlauf bleibt vollständig erhalten. "
                f"{BACKUP_NOTE} Der neue Commit ist danach noch nicht hochgeladen. "
                "Rückgängig machen?")
        if not confirm(self, title, text, yes="Rückgängig machen", no="Abbrechen"):
            return
        settings = self.services.settings.load()
        try:
            history.revert(self.code_dir, self.project.name, self.commit, settings.git_name,
                           settings.git_email)
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            return
        self.history_changed = True
        self.accept()
        announce(f"Rückgängig gemacht. Neuer Commit „{history.revert_message(self.commit)}“.")

    # -- Commit zurücknehmen -----------------------------------------------------------------
    def undo(self) -> None:
        title = "Commit zurücknehmen"
        text = (f"Der Commit „{self.commit.subject}“ wird zurückgenommen. Er ist noch nicht "
                "hochgeladen. Seine Änderungen bleiben in den Dateien und erscheinen wieder als "
                "Änderungen ohne Commit. Keine Datei wird verändert. Zurücknehmen?")
        if not confirm(self, title, text, yes="Zurücknehmen", no="Abbrechen"):
            return
        try:
            history.undo_commit(self.code_dir, self.commit)
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            return
        self.history_changed = True
        self.accept()
        announce("Commit zurückgenommen. Die Änderungen sind noch da, ohne Commit.")


class DiscardDialog(FocusDialog):
    """Änderungen ohne Commit auswählen. Nach accept() stehen sie in chosen."""

    def __init__(self, project_name: str, changes: list[LocalChange],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.changes = changes
        self.chosen: list[LocalChange] = []
        self.setWindowTitle(f"Änderungen verwerfen in {project_name}: "
                            f"{count(len(changes), 'Änderung', 'Änderungen')}")
        self.list = QListWidget()
        name_widget(self.list, "Änderungen")
        for change in changes:
            item = QListWidgetItem(change.line())
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        self.list.installEventFilter(self)
        self.all_button = QPushButton("&Alle auswählen")
        self.all_button.clicked.connect(self.toggle_all)
        discard = QPushButton("&Verwerfen …")
        discard.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(self.all_button)
        buttons.addStretch(1)
        buttons.addWidget(discard)
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(buttons)
        self.resize(640, 420)
        self.initial_focus_widget = self.list

    def eventFilter(self, watched, event) -> bool:
        if _ignore_enter(self, watched, event, (self.list,)):
            return True
        return super().eventFilter(watched, event)

    def checked(self) -> list[LocalChange]:
        return [c for row, c in enumerate(self.changes)
                if self.list.item(row).checkState() == Qt.CheckState.Checked]

    def toggle_all(self) -> None:
        select = len(self.checked()) < len(self.changes)
        state = Qt.CheckState.Checked if select else Qt.CheckState.Unchecked
        for row in range(self.list.count()):
            self.list.item(row).setCheckState(state)
        self.all_button.setText("Alle &abwählen" if select else "&Alle auswählen")
        announce("Alle ausgewählt." if select else "Keine ausgewählt.")

    def check(self) -> None:
        chosen = self.checked()
        if not chosen:
            show_error(self, self.windowTitle(), NO_CHOICE)
            self.list.setFocus()
            return
        text = (f"{history.discard_description(chosen)} Vorher kommen die Dateien als "
                "Sicherheitskopie in den Ordner backups. Verwerfen?")
        if not confirm(self, "Änderungen verwerfen", text, yes="Verwerfen", no="Abbrechen"):
            return
        self.chosen = chosen
        self.accept()
