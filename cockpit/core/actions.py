"""Aktionen für die Aktionsliste (Konzept 8.3).

Kern und Features bringen ihre Aktionen auf demselben Weg ein. Nicht verfügbare Aktionen werden
nicht versteckt, sondern mit Grund angezeigt.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable, Iterable

from cockpit.core.availability import Availability

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from cockpit.core.branches import Branch
    from cockpit.core.project_collections import Collection
    from cockpit.core.flows.questions import Asker
    from cockpit.core.worktrees import Worktree
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
    # Phase 10f: Ein Branch-Ordner steht in der Liste als BRANCH. Seine Aktionen sind die von
    # CODE, mit dem Branch-Ordner als code_dir (ActionContext.worktree ist dann gesetzt).
    BRANCH = "branch"
    REMOTE_BRANCH = "remote_branch"      # Branch nur auf der Plattform, noch ohne Ordner
    NEW_COLLECTION = "new_collection"    # oberster Eintrag "Neue Projektsammlung"
    COLLECTION = "collection"            # "Sammlung Webseiten, 3 Projekte"
    # Wunsch des Nutzers (06.10.2026): erste Zeile unter dem Projekt, mit den Aktionen für das
    # Repository und der Auswahl, welche Branches darunter stehen
    REPOSITORY = "repository"
    # Wunsch des Nutzers (06.10.2026): Zeile Releases unter den Branches. Darunter das Release
    # aus dem Haupt-Branch als EXE ("Exe-main") und je Branch-Release eine Zeile RELEASE.
    RELEASES = "releases"
    RELEASE = "release"


@dataclass
class ActionContext:
    services: "Services"
    project: "Project | None"
    target: Target
    announce: Callable[[str], None] = lambda text: None
    asker: "Asker | None" = None
    status: "ProjectStatus | None" = None            # Stand des Projekts, falls schon bekannt
    remote_repo: "StoredRepo | None" = None          # bei Target.REMOTE_REPO
    worktree: "Worktree | None" = None               # Branch-Ordner (Phase 10f)
    main_project: "Project | None" = None            # bei worktree: das Projekt mit Code\main
    remote_branch: "Branch | None" = None            # bei Target.REMOTE_BRANCH
    collection: "Collection | None" = None           # bei Target.COLLECTION
    release: "LocalRelease | None" = None            # bei Target.EXE und Target.RELEASE


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
    # Stand hinter dem Namen, zum Beispiel "3 Dateien offen" oder "alles aktuell" (Wunsch des
    # Nutzers, 02.10.2026: Man sieht in der Aktionsliste, ob es etwas zu tun gibt)
    detail: Callable[[ActionContext], str] | None = None
    # Name, der von der Zeile abhängt, zum Beispiel "Exe aus neue-funktion erstellen …"
    # (Wunsch des Nutzers vom 06.10.2026). Sonst gilt text.
    title: Callable[[ActionContext], str] | None = None


@dataclass(frozen=True)
class ActionEntry:
    """Eine Zeile der Aktionsliste."""
    action: Action
    availability: Availability
    detail: str = ""
    title: str = ""

    @property
    def text(self) -> str:
        return self.title or self.action.text

    @property
    def label(self) -> str:
        if not self.availability.available:
            return f"{self.text}, nicht verfügbar: {self.availability.reason}"
        return f"{self.text}, {self.detail}" if self.detail else self.text


def entries_for(actions: Iterable[Action], context: ActionContext) -> list[ActionEntry]:
    """Alle Aktionen für das Ziel des Kontexts, sortiert, mit Verfügbarkeit."""
    result = []
    for action in actions:
        if action.target is not context.target:
            continue
        if action.visible is not None and not action.visible(context):
            continue
        availability = action.availability(context) if action.availability else Availability.yes()
        title = action.title(context) if action.title is not None else ""
        result.append(ActionEntry(action, availability, _detail(action, context), title))
    return sorted(result, key=lambda e: (e.action.order, e.action.text))


def _detail(action: Action, context: ActionContext) -> str:
    """Stand hinter dem Namen. Ein Fehler dabei darf die Aktionsliste nie verhindern."""
    if action.detail is None:
        return ""
    try:
        return action.detail(context) or ""
    except Exception:                      # noqa: BLE001 (nur Zusatzinfo)
        log.exception("Stand für die Aktion %s nicht ermittelt", action.id)
        return ""


def default_entry(entries: list[ActionEntry]) -> ActionEntry | None:
    return next((e for e in entries if e.action.is_default and e.availability.available), None)
