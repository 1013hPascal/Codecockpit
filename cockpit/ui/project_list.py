"""Die Projektliste (Konzept 8.2, umgesetzt als Liste statt Baum, siehe ENTSCHEIDUNGEN.md).

Der Qt-Baum (QTreeView) meldete NVDA den Zustand "ausgeklappt" nicht zuverlässig, und nach dem
Zuklappen waren Einträge nicht mehr erreichbar. Deshalb ist die Projektliste eine normale Liste,
in die beim Ausklappen die Unterordner eingefügt werden.

Oben stehen "Projekt vom Rechner hinzufügen" und "Projekt von GitHub herunterladen", darunter
die Projekte, zuletzt aktualisierte oben.
Ein ausgeklapptes Projekt heißt "PDF-Chat, ausgeklappt", darunter stehen "Code" und "Exe, ...".
Repositories des Kontos, die noch nicht auf dem Rechner liegen, stehen dazwischen als
"Rechner, nur auf GitHub". Enter lädt sie herunter.

Der Stand der Projekte (project_status) kommt aus dem Hintergrund. Die Zeilen werden dann an Ort
und Stelle geändert, ohne die Liste neu aufzubauen. So bleiben Auswahl und Fokus, wo sie sind.

Tastatur:
- Pfeil rechts, Leertaste oder Enter auf einem Projekt: ausklappen. Das vorher offene Projekt
  klappt dabei zu. Der Fokus bleibt auf dem Projekt.
- Pfeil rechts auf einem ausgeklappten Projekt: zum ersten Unterordner.
- Leertaste oder Enter auf einem ausgeklappten Projekt: zuklappen.
- Pfeil links auf Code oder Exe: zuklappen, der Fokus springt zurück auf das Projekt.
- Pfeil links auf einem ausgeklappten Projekt: zuklappen.
- Enter oder Leertaste auf Code, Exe, den beiden obersten Einträgen oder einem Repository, das
  nur auf der Plattform liegt: wichtigste Aktion (Signal defaultActionRequested).
- Menütaste oder Umschalt+F10: Signal contextMenuRequested.
"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from cockpit.core.actions import Target
from cockpit.core.branches import Branch
from cockpit.core.project_status import (ProjectStatus, code_line, project_line,
                                         remote_line)
from cockpit.core.projects import Project
from cockpit.core.remote_repos import StoredRepo
from cockpit.core.text import count
from cockpit.core.worktrees import Worktree
from cockpit.ui.announcer import announce
from cockpit.ui.common import name_widget

ROLE_TARGET = Qt.ItemDataRole.UserRole + 1
ROLE_PROJECT = Qt.ItemDataRole.UserRole + 2
ROLE_KEY = Qt.ItemDataRole.UserRole + 3       # Ordner oder Name eines Branches (Phase 10f)

ADD_LOCAL_TEXT = "Projekt vom Rechner hinzufügen"


def add_remote_text(platform_name: str) -> str:
    return f"Projekt von {platform_name} herunterladen"
EXPANDED_SUFFIX = ", ausgeklappt"


def project_label(project: Project, status: ProjectStatus | None = None,
                  platform_name: str = "GitHub") -> str:
    return project_line(project, status, platform_name)


def exe_label(project: Project) -> str:
    """Zum Beispiel "Exe, vom Cockpit erstellt am 23.09.2026, aktuell" (Konzept 10.4)."""
    from cockpit.core.exe import status_line
    return status_line(project)


def children_of(project: Project, status: ProjectStatus | None = None,
                platform_name: str = "GitHub", shown: list[Branch] | None = None
                ) -> list[tuple[str, Target, str | None]]:
    """Die Unterordner, die es gibt (Konzept 8.2: nur vorhandene Ordner). Mit Branch-Ordnern
    (Phase 10f): Code des Haupt-Branches, die Branch-Ordner, "Branches auf GitHub" und die dort
    ausgewählten Branches anderer. Der dritte Wert unterscheidet Zeilen mit gleichem Ziel."""
    if not project.folder_found:
        return []
    if not project.has_branch_folders:
        rows = [(code_line(status, platform_name), Target.CODE, None)]
    else:
        rows = [(code_line(status, platform_name, f"Code, {project.code_dir.name}"),
                 Target.CODE, None)]
        for tree, inner in (status.worktrees if status is not None else []):
            rows.append((branch_label(tree, inner, platform_name), Target.BRANCH, tree.folder))
        if status is not None and status.on_platform:
            rows.append((f"Branches auf {platform_name}", Target.REMOTE_BRANCHES, None))
            main = status.repo.default_branch
            for branch in shown or []:
                rows.append((f"Branch {branch.line(main, platform_name)}", Target.REMOTE_BRANCH,
                             branch.name))
    if project.has_exe_dir:
        rows.append((exe_label(project), Target.EXE, None))
    return rows


def branch_label(tree: Worktree, status: ProjectStatus | None,
                 platform_name: str = "GitHub") -> str:
    """Zum Beispiel "Branch neue-funktion, 2 Dateien noch nicht hochgeladen"."""
    head = f"Branch {tree.branch or tree.folder}"
    if tree.gone:
        head += f", auf {platform_name} gelöscht"
    return code_line(status, platform_name, head)


CHILD_TARGETS = (Target.CODE, Target.EXE, Target.BRANCH, Target.REMOTE_BRANCHES,
                 Target.REMOTE_BRANCH)


def _sort_key(entry: Project | StoredRepo) -> str:
    """Zuletzt aktualisierte oben. Projekte ohne Datum nach der letzten Änderung im Ordner."""
    if isinstance(entry, StoredRepo):
        return entry.pushed_at[:19]
    if entry.last_updated:
        return entry.last_updated[:19]
    activity = entry.last_activity()
    return datetime.fromtimestamp(activity).isoformat(timespec="seconds") if activity else ""


class ProjectList(QListWidget):
    defaultActionRequested = Signal()
    contextMenuRequested = Signal(QPoint)
    expandedChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        name_widget(self, "Projekte")
        self._projects: dict[int, Project] = {}
        self._remote: dict[int, StoredRepo] = {}
        self._status: dict[int, ProjectStatus] = {}
        self._shown: dict[int, list[Branch]] = {}     # ausgewählte Branches anderer (10f)
        self._expanded: int | None = None
        self.platform_name = "GitHub"
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.itemDoubleClicked.connect(lambda item: self._activate())

    # -- Inhalt ---------------------------------------------------------------------------
    def set_projects(self, projects: list[Project],
                     remote_repos: list[StoredRepo] | None = None) -> None:
        """Liste neu füllen. Auswahl und ausgeklapptes Projekt bleiben erhalten, wenn möglich."""
        keep = (*self.current_target(), self.current_key())
        expanded = self._expanded
        self._projects = {p.id: p for p in projects}
        self._remote = {r.id: r for r in remote_repos or []}
        self._status = {k: v for k, v in self._status.items() if k in self._projects}
        self._expanded = None
        self.clear()
        self.addItem(self._item(ADD_LOCAL_TEXT, Target.ADD_LOCAL, None))
        self.addItem(self._item(add_remote_text(self.platform_name), Target.ADD_REMOTE, None))
        entries: list[Project | StoredRepo] = [*projects, *(remote_repos or [])]
        entries.sort(key=_sort_key, reverse=True)
        for entry in entries:
            if isinstance(entry, StoredRepo):
                self.addItem(self._item(remote_line(entry.name, entry.pushed_at,
                                                    self.platform_name),
                                        Target.REMOTE_REPO, entry.id))
            else:
                self.addItem(self._item(self._project_text(entry), Target.PROJECT, entry.id))
        if expanded in self._projects:
            self.expand(expanded, speak=False)
        if not self.select(*keep):
            self.setCurrentRow(0)

    def _project_text(self, project: Project) -> str:
        text = project_label(project, self._status.get(project.id), self.platform_name)
        return text + EXPANDED_SUFFIX if project.id == self._expanded else text

    def remote_ids(self) -> list[int]:
        return list(self._remote)

    def status_of(self, project_id: int | None) -> ProjectStatus | None:
        return self._status.get(project_id) if project_id is not None else None

    def project(self, project_id: int) -> Project | None:
        return self._projects.get(project_id)

    def update_status(self, status: ProjectStatus, project: Project | None = None) -> None:
        """Neuen Stand eintragen und nur die betroffenen Zeilen ändern. Keine Ansage, der Fokus
        bleibt, wo er ist."""
        if project is not None:
            self._projects[project.id] = project
        project = self._projects.get(status.project_id)
        if project is None:
            return
        self._status[status.project_id] = status
        row = self.row_of(Target.PROJECT, project.id)
        if row >= 0:
            self._set_text(row, self._project_text(project))
        if project.id == self._expanded:
            self._update_children(project)

    def _children(self, project: Project) -> list[tuple[str, Target, str | None]]:
        return children_of(project, self._status.get(project.id), self.platform_name,
                           self._shown.get(project.id))

    def _update_children(self, project: Project) -> None:
        """Zeilen unter dem ausgeklappten Projekt auffrischen. Sind Zeilen dazugekommen oder
        weggefallen (neuer Branch-Ordner), werden sie neu eingefügt. Die Markierung bleibt auf
        demselben Eintrag, sonst auf dem Projekt."""
        children = self._children(project)
        row = self.row_of(Target.PROJECT, project.id)
        current = [(self.item(r).data(ROLE_TARGET), self.item(r).data(ROLE_KEY))
                   for r in range(row + 1, self.count())
                   if self.item(r).data(ROLE_TARGET) in CHILD_TARGETS]
        if current == [(target, key) for _text, target, key in children]:
            for offset, (text, _target, _key) in enumerate(children, start=1):
                self._set_text(row + offset, text)
            return
        target, project_id = self.current_target()
        key = self.current_key()
        self.blockSignals(True)
        try:
            for _ in current:
                self.takeItem(row + 1)
            for offset, (text, child_target, child_key) in enumerate(children, start=1):
                self.insertItem(row + offset, self._item(text, child_target, project.id,
                                                         child_key))
            new_row = self.row_of(target, project_id, key)
            if new_row < 0:
                new_row = self.row_of(Target.PROJECT, project.id)
            self.setCurrentRow(new_row)
        finally:
            self.blockSignals(False)
        self.currentRowChanged.emit(self.currentRow())

    def show_remote_branch(self, project_id: int, branch: Branch) -> None:
        """Einen Branch anderer vorübergehend zeigen (bis zum Beenden oder Anpinnen)."""
        shown = self._shown.setdefault(project_id, [])
        if all(b.name != branch.name for b in shown):
            shown.append(branch)
        project = self._projects.get(project_id)
        if project is not None and project_id == self._expanded:
            self._update_children(project)

    def hide_remote_branch(self, project_id: int, name: str) -> None:
        self._shown[project_id] = [b for b in self._shown.get(project_id, []) if b.name != name]
        project = self._projects.get(project_id)
        if project is not None and project_id == self._expanded:
            self._update_children(project)

    def shown_branch(self, project_id: int | None, name: str | None) -> Branch | None:
        return next((b for b in self._shown.get(project_id, []) if b.name == name), None)

    def _set_text(self, row: int, text: str) -> None:
        item = self.item(row)
        if item.text() != text:                    # unveränderte Zeilen nicht anfassen
            item.setText(text)

    @staticmethod
    def _item(text: str, target: Target, project_id: int | None,
              key: str | None = None) -> QListWidgetItem:
        item = QListWidgetItem(text)
        item.setData(ROLE_TARGET, target)
        item.setData(ROLE_PROJECT, project_id)
        item.setData(ROLE_KEY, key)
        return item

    def texts(self) -> list[str]:
        return [self.item(r).text() for r in range(self.count())]

    # -- Auswahl --------------------------------------------------------------------------
    def current_target(self) -> tuple[Target, int | None]:
        item = self.currentItem()
        if item is None:
            return Target.ADD_LOCAL, None
        return item.data(ROLE_TARGET), item.data(ROLE_PROJECT)

    def current_key(self) -> str | None:
        """Ordner eines Branch-Ordners oder Name eines Branches anderer (Phase 10f)."""
        item = self.currentItem()
        return item.data(ROLE_KEY) if item is not None else None

    def row_of(self, target: Target, project_id: int | None, key: str | None = None) -> int:
        for row in range(self.count()):
            item = self.item(row)
            if item.data(ROLE_TARGET) == target and item.data(ROLE_PROJECT) == project_id \
                    and (key is None or item.data(ROLE_KEY) == key):
                return row
        return -1

    def select(self, target: Target, project_id: int | None, key: str | None = None) -> bool:
        """Eintrag markieren. Für Unterordner wird das Projekt dafür ausgeklappt. Steht die
        Markierung auf einem Branch-Ordner, bleibt sie dort, wenn Code gewünscht ist: Die
        Aktionen von Code laufen dort im Branch-Ordner (Phase 10f)."""
        if target is Target.CODE and self.current_target() == (Target.BRANCH, project_id):
            return True
        if target in CHILD_TARGETS and project_id != self._expanded:
            self.expand(project_id, speak=False)
        row = self.row_of(target, project_id, key)
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
        children = self._children(project)
        if not children:
            if speak:
                announce("Der Ordner wurde nicht gefunden." if not project.folder_found
                         else "Keine Unterordner.")
            return False
        if self._expanded is not None:
            self._remove_children()
        row = self.row_of(Target.PROJECT, project_id)
        for offset, (text, target, key) in enumerate(children, start=1):
            self.insertItem(row + offset, self._item(text, target, project_id, key))
        self._expanded = project_id
        self.item(row).setText(self._project_text(project))
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
        while row + 1 < self.count() and self.item(row + 1).data(ROLE_TARGET) in CHILD_TARGETS:
            self.takeItem(row + 1)
        project = self._projects.get(project_id)
        if project is not None and row >= 0:
            self.item(row).setText(self._project_text(project))

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
        if key == Qt.Key.Key_Left and (target in CHILD_TARGETS
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
