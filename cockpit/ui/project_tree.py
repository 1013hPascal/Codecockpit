"""Der Projektbaum (Konzept 8.2).

Oberste Ebene: "Neues Projekt hochladen", darunter die Projekte, zuletzt aktualisierte oben.
Zweite Ebene: die vorhandenen Unterordner Code und Exe.

Tastatur (Standard von QTreeView, dazu das automatische Zuklappen):
- Pfeil rechts auf einem Projekt klappt es aus. Alle anderen Projekte klappen dabei zu, der Fokus
  bleibt auf dem ausgeklappten Projekt.
- Pfeil rechts auf einem ausgeklappten Projekt springt zum ersten Unterordner.
- Pfeil links auf einem Unterordner springt zum Projekt, auf einem ausgeklappten Projekt klappt
  es zu.
- Enter klappt ein Projekt aus oder zu, sonst meldet der Baum defaultActionRequested.
- Menütaste und Umschalt+F10 melden contextMenuRequested.
"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QModelIndex, QPoint, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QTreeView

from cockpit.core.actions import Target
from cockpit.core.projects import Project

ROLE_TARGET = Qt.ItemDataRole.UserRole + 1
ROLE_PROJECT = Qt.ItemDataRole.UserRole + 2

NEW_PROJECT_TEXT = "Neues Projekt hochladen"


def project_label(project: Project) -> str:
    if not project.folder_found:
        return f"{project.name}, Ordner nicht gefunden"
    return project.name


def code_label(project: Project) -> str:
    return "Code"


def exe_label(project: Project) -> str:
    exe = project.newest_exe()
    if exe is None:
        return "Exe, leer"
    created = datetime.fromtimestamp(exe.stat().st_mtime)
    return f"Exe, {exe.name}, erstellt am {created:%d.%m.%Y}"


class ProjectTree(QTreeView):
    defaultActionRequested = Signal()
    contextMenuRequested = Signal(QPoint)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model_ = QStandardItemModel(self)
        self.setModel(self.model_)
        self.setHeaderHidden(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setUniformRowHeights(True)
        self.setExpandsOnDoubleClick(True)
        self.setAccessibleName("Projekte")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.expanded.connect(self._collapse_others)
        self.doubleClicked.connect(self._double_clicked)

    # -- Inhalt ---------------------------------------------------------------------------
    def set_projects(self, projects: list[Project]) -> None:
        """Baum neu füllen. Auswahl und ausgeklapptes Projekt bleiben erhalten, wenn möglich."""
        keep = self.current_target()
        expanded_id = self.expanded_project_id()
        self.model_.clear()
        top = QStandardItem(NEW_PROJECT_TEXT)
        top.setData(Target.NEW_PROJECT, ROLE_TARGET)
        top.setEditable(False)
        self.model_.appendRow(top)
        for project in projects:
            item = QStandardItem(project_label(project))
            item.setData(Target.PROJECT, ROLE_TARGET)
            item.setData(project.id, ROLE_PROJECT)
            item.setEditable(False)
            if project.folder_found:
                item.appendRow(self._child(code_label(project), Target.CODE, project.id))
                if project.has_exe_dir:
                    item.appendRow(self._child(exe_label(project), Target.EXE, project.id))
            self.model_.appendRow(item)
        if expanded_id is not None:
            index = self.index_for(Target.PROJECT, expanded_id)
            if index.isValid():
                self.expand(index)
        if not self.select(*keep):
            self.setCurrentIndex(self.model_.index(0, 0))

    @staticmethod
    def _child(text: str, target: Target, project_id: int) -> QStandardItem:
        item = QStandardItem(text)
        item.setData(target, ROLE_TARGET)
        item.setData(project_id, ROLE_PROJECT)
        item.setEditable(False)
        return item

    def texts(self) -> list[str]:
        """Alle sichtbaren und unsichtbaren Einträge, Unterordner mit zwei Leerzeichen (Tests)."""
        result = []
        for row in range(self.model_.rowCount()):
            item = self.model_.item(row)
            result.append(item.text())
            result += ["  " + item.child(r).text() for r in range(item.rowCount())]
        return result

    # -- Auswahl --------------------------------------------------------------------------
    def current_target(self) -> tuple[Target, int | None]:
        index = self.currentIndex()
        if not index.isValid():
            return Target.NEW_PROJECT, None
        return index.data(ROLE_TARGET), index.data(ROLE_PROJECT)

    def index_for(self, target: Target, project_id: int | None) -> QModelIndex:
        for row in range(self.model_.rowCount()):
            item = self.model_.item(row)
            if item.data(ROLE_TARGET) == target and item.data(ROLE_PROJECT) == project_id:
                return item.index()
            for r in range(item.rowCount()):
                child = item.child(r)
                if child.data(ROLE_TARGET) == target and child.data(ROLE_PROJECT) == project_id:
                    return child.index()
        return QModelIndex()

    def select(self, target: Target, project_id: int | None) -> bool:
        index = self.index_for(target, project_id)
        if not index.isValid():
            return False
        if index.parent().isValid():
            self.expand(index.parent())
        self.setCurrentIndex(index)
        return True

    def expanded_project_id(self) -> int | None:
        for row in range(self.model_.rowCount()):
            index = self.model_.index(row, 0)
            if self.isExpanded(index):
                return index.data(ROLE_PROJECT)
        return None

    # -- Verhalten ------------------------------------------------------------------------
    def _collapse_others(self, index: QModelIndex) -> None:
        """Immer höchstens ein Projekt offen (Konzept 8.2)."""
        if index.parent().isValid():
            return
        current = self.currentIndex()
        for row in range(self.model_.rowCount()):
            other = self.model_.index(row, 0)
            if other != index and self.isExpanded(other):
                if current.parent() == other:
                    self.setCurrentIndex(index)
                self.collapse(other)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers():
            index = self.currentIndex()
            if index.isValid() and index.data(ROLE_TARGET) == Target.PROJECT \
                    and self.model_.itemFromIndex(index).rowCount():
                self.setExpanded(index, not self.isExpanded(index))
            else:
                self.defaultActionRequested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def _double_clicked(self, index: QModelIndex) -> None:
        if index.data(ROLE_TARGET) != Target.PROJECT:
            self.defaultActionRequested.emit()

    def _context_menu(self, _pos: QPoint) -> None:
        """Tastatur und Maus: Das Menü gehört immer zum markierten Eintrag."""
        index = self.currentIndex()
        if not index.isValid():
            return
        rect = self.visualRect(index)
        self.contextMenuRequested.emit(self.viewport().mapToGlobal(rect.bottomLeft()))
