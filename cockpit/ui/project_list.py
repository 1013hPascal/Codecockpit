"""Die Projektliste (Konzept 8.2, umgesetzt als Liste statt Baum, siehe ENTSCHEIDUNGEN.md).

Der Qt-Baum (QTreeView) meldete NVDA den Zustand "ausgeklappt" nicht zuverlässig, und nach dem
Zuklappen waren Einträge nicht mehr erreichbar. Deshalb ist die Projektliste eine normale Liste,
in die beim Ausklappen die Unterordner eingefügt werden.

Oberste Zeile: "Neues Projekt hochladen", darunter die Projekte, zuletzt aktualisierte oben.
Ein ausgeklapptes Projekt heißt "PDF-Chat, ausgeklappt", darunter stehen "Code" und "Exe, ...".

Tastatur:
- Pfeil rechts, Leertaste oder Enter auf einem Projekt: ausklappen. Das vorher offene Projekt
  klappt dabei zu. Der Fokus bleibt auf dem Projekt.
- Pfeil rechts auf einem ausgeklappten Projekt: zum ersten Unterordner.
- Leertaste oder Enter auf einem ausgeklappten Projekt: zuklappen.
- Pfeil links auf Code oder Exe: zuklappen, der Fokus springt zurück auf das Projekt.
- Pfeil links auf einem ausgeklappten Projekt: zuklappen.
- Enter oder Leertaste auf Code, Exe oder "Neues Projekt hochladen": wichtigste Aktion
  (Signal defaultActionRequested).
- Menütaste oder Umschalt+F10: Signal contextMenuRequested.
"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from cockpit.core.actions import Target
from cockpit.core.projects import Project
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import name_widget

ROLE_TARGET = Qt.ItemDataRole.UserRole + 1
ROLE_PROJECT = Qt.ItemDataRole.UserRole + 2

NEW_PROJECT_TEXT = "Neues Projekt hochladen"
EXPANDED_SUFFIX = ", ausgeklappt"


def project_label(project: Project) -> str:
    if not project.folder_found:
        return f"{project.name}, Ordner nicht gefunden"
    return project.name


def exe_label(project: Project) -> str:
    exe = project.newest_exe()
    if exe is None:
        return "Exe, leer"
    created = datetime.fromtimestamp(exe.stat().st_mtime)
    return f"Exe, {exe.name}, erstellt am {created:%d.%m.%Y}"


def children_of(project: Project) -> list[tuple[str, Target]]:
    """Die Unterordner, die es gibt (Konzept 8.2: nur vorhandene Ordner)."""
    if not project.folder_found:
        return []
    rows = [("Code", Target.CODE)]
    if project.has_exe_dir:
        rows.append((exe_label(project), Target.EXE))
    return rows


class ProjectList(QListWidget):
    defaultActionRequested = Signal()
    contextMenuRequested = Signal(QPoint)
    expandedChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        name_widget(self, "Projekte")
        self._projects: dict[int, Project] = {}
        self._expanded: int | None = None
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.itemDoubleClicked.connect(lambda item: self._activate())

    # -- Inhalt ---------------------------------------------------------------------------
    def set_projects(self, projects: list[Project]) -> None:
        """Liste neu füllen. Auswahl und ausgeklapptes Projekt bleiben erhalten, wenn möglich."""
        keep = self.current_target()
        expanded = self._expanded
        self._projects = {p.id: p for p in projects}
        self._expanded = None
        self.clear()
        self.addItem(self._item(NEW_PROJECT_TEXT, Target.NEW_PROJECT, None))
        for project in projects:
            self.addItem(self._item(project_label(project), Target.PROJECT, project.id))
        if expanded in self._projects:
            self.expand(expanded, speak=False)
        if not self.select(*keep):
            self.setCurrentRow(0)

    @staticmethod
    def _item(text: str, target: Target, project_id: int | None) -> QListWidgetItem:
        item = QListWidgetItem(text)
        item.setData(ROLE_TARGET, target)
        item.setData(ROLE_PROJECT, project_id)
        return item

    def texts(self) -> list[str]:
        return [self.item(r).text() for r in range(self.count())]

    # -- Auswahl --------------------------------------------------------------------------
    def current_target(self) -> tuple[Target, int | None]:
        item = self.currentItem()
        if item is None:
            return Target.NEW_PROJECT, None
        return item.data(ROLE_TARGET), item.data(ROLE_PROJECT)

    def row_of(self, target: Target, project_id: int | None) -> int:
        for row in range(self.count()):
            item = self.item(row)
            if item.data(ROLE_TARGET) == target and item.data(ROLE_PROJECT) == project_id:
                return row
        return -1

    def select(self, target: Target, project_id: int | None) -> bool:
        """Eintrag markieren. Für Code und Exe wird das Projekt dafür ausgeklappt."""
        if target in (Target.CODE, Target.EXE) and project_id != self._expanded:
            self.expand(project_id, speak=False)
        row = self.row_of(target, project_id)
        if row < 0:
            return False
        self.setCurrentRow(row)
        return True

    @property
    def expanded_project_id(self) -> int | None:
        return self._expanded

    # -- Aus- und Zuklappen ---------------------------------------------------------------
    def expand(self, project_id: int, speak: bool = True) -> bool:
        project = self._projects.get(project_id)
        if project is None or project_id == self._expanded:
            return project_id == self._expanded
        children = children_of(project)
        if not children:
            if speak:
                announce("Der Ordner wurde nicht gefunden." if not project.folder_found
                         else "Keine Unterordner.")
            return False
        if self._expanded is not None:
            self._remove_children()
        row = self.row_of(Target.PROJECT, project_id)
        for offset, (text, target) in enumerate(children, start=1):
            self.insertItem(row + offset, self._item(text, target, project_id))
        self.item(row).setText(project_label(project) + EXPANDED_SUFFIX)
        self._expanded = project_id
        self.setCurrentRow(row)
        if speak:
            announce(f"Ausgeklappt, {count(len(children), 'Unterordner', 'Unterordner')}.")
        self.expandedChanged.emit()
        return True

    def collapse(self, speak: bool = True) -> None:
        """Offenes Projekt zuklappen. Der Fokus springt auf das Projekt."""
        if self._expanded is None:
            return
        project_id = self._expanded
        self._remove_children()
        self.setCurrentRow(self.row_of(Target.PROJECT, project_id))
        if speak:
            announce("Zugeklappt.")
        self.expandedChanged.emit()

    def _remove_children(self) -> None:
        project_id = self._expanded
        self._expanded = None
        row = self.row_of(Target.PROJECT, project_id)
        while row + 1 < self.count() and self.item(row + 1).data(ROLE_TARGET) in (Target.CODE,
                                                                                  Target.EXE):
            self.takeItem(row + 1)
        project = self._projects.get(project_id)
        if project is not None and row >= 0:
            self.item(row).setText(project_label(project))

    # -- Tastatur und Maus ----------------------------------------------------------------
    def keyPressEvent(self, event) -> None:
        if event.modifiers() not in (Qt.KeyboardModifier.NoModifier,
                                     Qt.KeyboardModifier.KeypadModifier):
            super().keyPressEvent(event)
            return
        target, project_id = self.current_target()
        key = event.key()
        if key == Qt.Key.Key_Right and target == Target.PROJECT:
            if project_id == self._expanded:
                self.setCurrentRow(self.currentRow() + 1)
            else:
                self.expand(project_id)
            event.accept()
            return
        if key == Qt.Key.Key_Left and (target in (Target.CODE, Target.EXE)
                                       or (target == Target.PROJECT
                                           and project_id == self._expanded)):
            self.collapse()
            event.accept()
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self._activate()
            event.accept()
            return
        super().keyPressEvent(event)

    def _activate(self) -> None:
        target, project_id = self.current_target()
        if target == Target.PROJECT:
            if project_id == self._expanded:
                self.collapse()
            else:
                self.expand(project_id)          # ohne Unterordner sagt es den Grund an
            return
        self.defaultActionRequested.emit()

    def _context_menu(self, _pos: QPoint) -> None:
        """Tastatur und Maus: Das Menü gehört immer zum markierten Eintrag."""
        item = self.currentItem()
        if item is None:
            return
        rect = self.visualItemRect(item)
        self.contextMenuRequested.emit(self.viewport().mapToGlobal(rect.bottomLeft()))
