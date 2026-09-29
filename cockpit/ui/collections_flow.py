"""Projektsammlungen in der Projektliste (Wunsch des Nutzers vom 29.09.2026).

- "Neue Projektsammlung" ganz oben: Name eingeben, OK.
- Auf einer Sammlung: "Projekte für die Sammlung …" (Liste mit Kontrollkästchen),
  "Projektsammlung umbenennen …" und "Projektsammlung auflösen …".

Ein Projekt steht in höchstens einer Sammlung. Die Zuordnung steht nur in der Datenbank, Ordner
und Dateien bleiben unverändert. Deshalb braucht das Auflösen keine Sicherheitskopie.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialogButtonBox, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QVBoxLayout, QWidget)

from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.project_collections import Collection
from cockpit.core.projects import Project
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, label_for, name_widget, show_info
from cockpit.ui.repo_dialogs import _is_enter

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

ROLE_ID = Qt.ItemDataRole.UserRole + 1


class NameDialog(FocusDialog):
    """Ein Textfeld "Name" und OK. Enter im Textfeld drückt OK."""

    def __init__(self, title: str, name: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.edit = QLineEdit(name)
        self.edit.selectAll()
        label = label_for(self.edit, "&Name:")
        buttons = QDialogButtonBox()
        ok = buttons.addButton("OK", QDialogButtonBox.ButtonRole.AcceptRole)
        ok.setDefault(True)
        buttons.addButton("Abbrechen", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.edit)
        layout.addWidget(buttons)
        self.initial_focus_widget = self.edit
        self.edit.setFocus()

    @property
    def name(self) -> str:
        return self.edit.text()


def member_hint(collection: Collection) -> str:
    return (f"Markieren Sie alle Projekte, die der {collection.title} zugeordnet werden sollen. "
            "Ein Projekt kann nur in einer Sammlung sein. Steht bei einem Projekt eine andere "
            "Sammlung und Sie markieren es, wird es dort entfernt und hier hinzugefügt.")


def member_line(project: Project, other: Collection | None) -> str:
    """Zum Beispiel "PDF-Chat, in Sammlung KI"."""
    return f"{project.name}, in {other.title}" if other is not None else project.name


def _plain_item(text: str) -> QListWidgetItem:
    """Zeile ohne Kontrollkästchen, zum Beispiel der Hinweis oben in der Liste."""
    item = QListWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
    item.setData(ROLE_ID, None)
    return item


class MembersDialog(FocusDialog):
    """Liste mit Kontrollkästchen. Oben der Hinweis als erster Eintrag, unten Speichern.
    Leertaste markiert, Enter speichert."""

    def __init__(self, collection: Collection, projects: list[Project],
                 membership: dict[int, int], collections: dict[int, Collection],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Projekte für die {collection.title}")
        self.list = QListWidget()
        self.list.setWordWrap(True)
        label = label_for(self.list, "&Projekte:")
        self.list.addItem(_plain_item(member_hint(collection)))
        for project in sorted(projects, key=lambda p: p.name.lower()):
            owner = membership.get(project.id)
            other = collections.get(owner) if owner not in (None, collection.id) else None
            item = QListWidgetItem(member_line(project, other))
            item.setData(ROLE_ID, project.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if owner == collection.id
                               else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        if not projects:
            self.list.addItem(_plain_item("Es gibt noch keine Projekte."))
        self.list.setCurrentRow(0)
        self.list.installEventFilter(self)
        self.save_button = QPushButton("&Speichern")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.accept)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        buttons = QDialogButtonBox()
        buttons.addButton(self.save_button, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(cancel, QDialogButtonBox.ButtonRole.RejectRole)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.list, 1)
        layout.addWidget(buttons)
        self.resize(620, 480)
        self.initial_focus_widget = self.list
        self.list.setFocus()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            self.accept()
            return True
        return super().eventFilter(watched, event)

    def items(self) -> list[QListWidgetItem]:
        return [self.list.item(r) for r in range(self.list.count())
                if self.list.item(r).data(ROLE_ID) is not None]

    def chosen(self) -> set[int]:
        return {item.data(ROLE_ID) for item in self.items()
                if item.checkState() == Qt.CheckState.Checked}


class CollectionActions:
    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services

    def actions(self) -> list[Action]:
        return [
            Action("new_collection", "Neue Projektsammlung …", Target.NEW_COLLECTION,
                   lambda c: self.create(), is_default=True, order=10),
            Action("collection_members", "Projekte für die Sammlung …", Target.COLLECTION,
                   self.members, order=10),
            Action("rename_collection", "Projektsammlung umbenennen …", Target.COLLECTION,
                   self.rename, order=20),
            Action("dissolve_collection", "Projektsammlung auflösen …", Target.COLLECTION,
                   self.dissolve, order=30),
        ]

    # -- Hilfen ----------------------------------------------------------------------------
    def _ask_name(self, title: str, name: str, save) -> Collection | None:
        """Name abfragen, bis er passt oder abgebrochen wird. save wirft CockpitError."""
        while True:
            dialog = NameDialog(title, name, self.window)
            if not dialog.exec():
                return None
            name = dialog.name
            try:
                return save(name)
            except CockpitError as exc:
                show_info(self.window, title, exc.message)

    def _reload(self) -> None:
        self.window.reload_projects(refresh=False)

    # -- Aktionen --------------------------------------------------------------------------
    def create(self) -> None:
        store = self.services.collections
        collection = self._ask_name("Neue Projektsammlung", "", store.create)
        if collection is None:
            return
        self._reload()
        self.window.project_list.select(Target.COLLECTION, collection.id)
        announce(f"{collection.title} angelegt. Mit Tab wählen Sie die Projekte dafür.")

    def members(self, context: ActionContext) -> None:
        collection = context.collection
        if collection is None:
            return
        store = self.services.collections
        dialog = MembersDialog(collection, self.services.projects.all(), store.membership(),
                               {c.id: c for c in store.all()}, self.window)
        if not dialog.exec():
            return
        chosen = dialog.chosen()
        store.set_members(collection.id, chosen)
        self._reload()
        self.window.project_list.select(Target.COLLECTION, collection.id)
        announce(f"Gespeichert. {collection.title}: "
                 f"{count(len(chosen), 'Projekt', 'Projekte')}.")

    def rename(self, context: ActionContext) -> None:
        collection = context.collection
        if collection is None:
            return
        store = self.services.collections
        renamed = self._ask_name("Projektsammlung umbenennen", collection.name,
                                 lambda name: store.rename(collection.id, name))
        if renamed is None:
            return
        self._reload()
        self.window.project_list.select(Target.COLLECTION, renamed.id)
        announce(f"Umbenannt in {renamed.title}.")

    def dissolve(self, context: ActionContext) -> None:
        collection = context.collection
        if collection is None:
            return
        store = self.services.collections
        members = store.members(collection.id)
        text = f"Die {collection.title} wird aufgelöst."
        if len(members) == 1:
            text += (" Das Projekt darin steht danach wieder einzeln in der Projektliste, "
                     "ohne Sammlung.")
        elif members:
            text += (f" Die {len(members)} Projekte darin stehen danach wieder einzeln in der "
                     "Projektliste, ohne Sammlung.")
        text += " Ordner und Dateien bleiben unverändert."
        if not confirm(self.window, "Projektsammlung auflösen", text, yes="Auflösen",
                       no="Abbrechen"):
            return
        store.dissolve(collection.id)
        listing = self.window.project_list
        listing.close_collection(speak=False)
        self._reload()
        first = next((p.id for p in self.services.projects.all() if p.id in members), None)
        if first is None or not listing.select(Target.PROJECT, first):
            listing.select(Target.NEW_COLLECTION, None)
        announce(f"{collection.title} aufgelöst.")
