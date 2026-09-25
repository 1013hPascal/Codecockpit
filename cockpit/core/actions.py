"""Aktionen für die Aktionsliste (Konzept 8.3).

Kern und Features bringen ihre Aktionen auf demselben Weg ein. Nicht verfügbare Aktionen werden
nicht versteckt, sondern mit Grund angezeigt.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable, Iterable

from cockpit.core.availability import Availability

if TYPE_CHECKING:
    from cockpit.core.flows.questions import Asker
    from cockpit.core.project_status import ProjectStatus
    from cockpit.core.projects import Project
    from cockpit.core.remote_repos import StoredRepo
    from cockpit.core.services import Services


class Target(Enum):
    ADD_LOCAL = "add_local"          # oberster Eintrag "Projekt vom Rechner hinzufügen"
    ADD_REMOTE = "add_remote"        # zweiter Eintrag "Projekt von GitHub herunterladen"
    PROJECT = "project"
    CODE = "code"
    EXE = "exe"
    REMOTE_REPO = "remote_repo"      # Repository, das nur auf der Plattform liegt


@dataclass
class ActionContext:
    services: "Services"
    project: "Project | None"
    target: Target
    announce: Callable[[str], None] = lambda text: None
    asker: "Asker | None" = None
    status: "ProjectStatus | None" = None            # Stand des Projekts, falls schon bekannt
    remote_repo: "StoredRepo | None" = None          # bei Target.REMOTE_REPO


@dataclass(frozen=True)
class Action:
    id: str
    text: str                                          # "Exe neu erstellen"
    target: Target
    run: Callable[[ActionContext], None]
    availability: Callable[[ActionContext], Availability] | None = None
    is_default: bool = False                           # wird mit Enter im Baum ausgeführt
    order: int = 100
    # Nur zeigen, wenn es passt, zum Beispiel "Neuen Ort angeben" nur bei fehlendem Ordner.
    # Anders als availability: Eine versteckte Aktion steht gar nicht in der Liste.
    visible: Callable[[ActionContext], bool] | None = None


@dataclass(frozen=True)
class ActionEntry:
    """Eine Zeile der Aktionsliste."""
    action: Action
    availability: Availability

    @property
    def label(self) -> str:
        if self.availability.available:
            return self.action.text
        return f"{self.action.text}, nicht verfügbar: {self.availability.reason}"


def entries_for(actions: Iterable[Action], context: ActionContext) -> list[ActionEntry]:
    """Alle Aktionen für das Ziel des Kontexts, sortiert, mit Verfügbarkeit."""
    result = []
    for action in actions:
        if action.target is not context.target:
            continue
        if action.visible is not None and not action.visible(context):
            continue
        availability = action.availability(context) if action.availability else Availability.yes()
        result.append(ActionEntry(action, availability))
    return sorted(result, key=lambda e: (e.action.order, e.action.text))


def default_entry(entries: list[ActionEntry]) -> ActionEntry | None:
    return next((e for e in entries if e.action.is_default and e.availability.available), None)
