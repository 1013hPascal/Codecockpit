"""Beiseitegelegte Änderungen und Name für einen neuen Branch.
"""
from __future__ import annotations

from PySide6.QtWidgets import QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import branches
from cockpit.core.branches import Stash
from cockpit.core.errors import CockpitError
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, label_for, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row


class BranchNameDialog(FocusDialog):
    """Name für einen neuen oder umbenannten Branch. Prüft den Namen wie Git."""

    def __init__(self, title: str, hint: str, code_dir, current: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.code_dir = code_dir
        self.name = ""
        self.setWindowTitle(title)
        self.edit = QLineEdit(current)
        label = label_for(self.edit, "&Name des Branches:")
        ok = QPushButton("OK")
        ok.setDefault(True)
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.edit)
        if hint:
            info = QListWidget()
            name_widget(info, "Hinweis")
            info.addItem(hint)
            info.setMaximumHeight(60)
            layout.addWidget(info)
        layout.addLayout(button_row(None, ok, cancel))
        self.resize(480, 180)
        self.initial_focus_widget = self.edit

    def check(self) -> None:
        name = self.edit.text().strip()
        problem = branches.name_problem(self.code_dir, name)
        if problem:
            show_error(self, self.windowTitle(), problem)
            self.edit.setFocus()
            return
        self.name = name
        self.accept()


class StashDialog(FocusDialog):
    """Beiseitegelegte Änderungen. changed: Dateien oder Branch haben sich geändert."""

    def __init__(self, project: "Project", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project = project
        self.code_dir = project.code_dir
        self.items: list[Stash] = []
        self.changed = False
        self.list = QListWidget()
        name_widget(self.list, "Beiseitegelegte Änderungen")
        self.list.installEventFilter(self)
        restore = QPushButton("&Zurückholen …")
        restore.clicked.connect(self.restore_current)
        as_branch = QPushButton("Als neuen &Branch zurückholen …")
        as_branch.clicked.connect(self.branch_current)
        delete = QPushButton("&Löschen …")
        delete.clicked.connect(self.delete_current)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(restore, as_branch, delete, None, close))
        self.resize(720, 360)
        self.initial_focus_widget = self.list
        self.fill()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            return True
        return super().eventFilter(watched, event)

    def fill(self) -> None:
        row = max(0, self.list.currentRow())
        self.items = branches.stashes(self.code_dir)
        self.setWindowTitle(f"Beiseitegelegte Änderungen von {self.project.name}: "
                            f"{count(len(self.items), 'Eintrag', 'Einträge')}")
        self.list.clear()
        self.list.addItems([s.line() for s in self.items] or ["Nichts beiseitegelegt."])
        self.list.setCurrentRow(min(row, self.list.count() - 1))

    def current(self) -> Stash | None:
        row = self.list.currentRow()
        if 0 <= row < len(self.items):
            return self.items[row]
        announce("Es ist nichts beiseitegelegt.")
        return None

    def _done(self, text: str) -> None:
        self.changed = True
        self.fill()
        self.list.setFocus()
        announce(text)

    def restore_current(self) -> None:
        stash = self.current()
        if stash is None:
            return
        where = f" Sie wurden auf {stash.branch} beiseitegelegt." if stash.branch else ""
        if not confirm(self, "Zurückholen",
                       f"Die Änderungen kommen zurück in Ihre Dateien: "
                       f"{count(len(stash.files), 'Datei', 'Dateien')}.{where} Zurückholen?",
                       yes="Zurückholen", no="Abbrechen"):
            return
        try:
            branches.stash_restore(self.code_dir, stash)
        except CockpitError as exc:
            show_error(self, "Zurückholen", exc.message, exc.details)
            return
        self._done("Änderungen zurückgeholt.")

    def branch_current(self) -> None:
        stash = self.current()
        if stash is None:
            return
        suggestion = f"beiseitegelegt-{stash.date:%Y-%m-%d}" if stash.date else "beiseitegelegt"
        dialog = BranchNameDialog("Als neuen Branch zurückholen",
                                  "Der Branch beginnt dort, wo die Änderungen beiseitegelegt "
                                  "wurden. So passen sie immer. Sie wechseln dabei zu ihm.",
                                  self.code_dir, suggestion, self)
        if not dialog.exec():
            return
        try:
            branches.stash_to_branch(self.code_dir, stash, dialog.name)
        except CockpitError as exc:
            show_error(self, "Als neuen Branch zurückholen", exc.message, exc.details)
            return
        self._done(f"Zurückgeholt in den neuen Branch {dialog.name}. Sie sind jetzt dort.")

    def delete_current(self) -> None:
        stash = self.current()
        if stash is None:
            return
        if not confirm(self, "Löschen",
                       f"Die beiseitegelegten Änderungen vom "
                       f"{stash.date:%d.%m.%Y %H:%M} werden gelöscht. Ihre Dateien kommen vorher "
                       "als Sicherheitskopie in den Ordner backups. Löschen?"
                       if stash.date else "Die beiseitegelegten Änderungen werden gelöscht. "
                       "Ihre Dateien kommen vorher als Sicherheitskopie in den Ordner backups. "
                       "Löschen?", yes="Löschen", no="Abbrechen"):
            return
        try:
            branches.stash_drop(self.code_dir, self.project.name, stash)
        except CockpitError as exc:
            show_error(self, "Löschen", exc.message, exc.details)
            return
        self._done("Beiseitegelegte Änderungen gelöscht.")
