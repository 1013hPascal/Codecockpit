"""Stand der Projekte für die Projektliste (Konzept 8.2).

Der Stand wird im Hintergrund ermittelt: beim Start, nach jeder Aktion am Projekt und mit Strg+R
(ENTSCHEIDUNGEN.md). Dabei gibt es keine Ansage, und der Fokus bleibt, wo er ist.

Beispiele für die Zeilen, das Wichtigste vorne:
- "Tagebuch, aktualisiert am 18.09.2026, 3 Dateien noch nicht hochgeladen"
- "Bildbeschreiber, noch nicht auf GitHub"
- "Rechner, nur auf GitHub, aktualisiert am 10.09.2026"
- "Code, Branch suche-pdfs, alles hochgeladen"
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from cockpit.core import git, venv_repair
from cockpit.core.errors import CockpitError
from cockpit.core.git import RepoStatus
from cockpit.core.projects import Project, ProjectStore
from cockpit.core.text import count
from cockpit.core.venv_repair import VenvState

log = logging.getLogger(__name__)


@dataclass
class ProjectStatus:
    project_id: int
    repo: RepoStatus | None = None           # None: Ordner fehlt oder Git ist fehlgeschlagen
    pending: int = 0                         # Dateien noch nicht hochgeladen
    venv: VenvState = field(default_factory=lambda: VenvState(False))
    error: str = ""

    @property
    def on_platform(self) -> bool:
        return self.repo is not None and self.repo.is_repo and bool(self.repo.remote_url)

    @property
    def unfinished_merge(self) -> str:
        """Kurzer Text, wenn ein Zusammenführen offen ist, sonst leer."""
        if self.repo is None or not self.repo.is_repo:
            return ""
        if self.repo.conflicts:
            return (f"{count(len(self.repo.conflicts), 'Konflikt', 'Konflikte')} beim "
                    "Zusammenführen")
        return "Zusammenführen nicht abgeschlossen" if self.repo.merging else ""

    @property
    def other_branch(self) -> str:
        """Name des Branches, wenn es nicht der Haupt-Branch ist, sonst leer."""
        if self.repo is None or not self.repo.is_repo or not self.repo.branch:
            return ""
        return "" if self.repo.branch == self.repo.default_branch else self.repo.branch


def compute(project: Project) -> ProjectStatus:
    """Stand eines Projekts. Blockiert kurz (Git), also im Hintergrund aufrufen."""
    status = ProjectStatus(project.id)
    if not project.folder_found:
        return status
    status.venv = venv_repair.check(project.code_dir)
    try:
        status.repo = git.status(project.code_dir)
        if status.repo.is_repo:
            status.pending = git.pending_files(project.code_dir, status.repo)
    except CockpitError as exc:
        log.warning("Stand von %s nicht lesbar: %s %s", project.name, exc.message, exc.details)
        status.error = exc.message
        status.repo = None
    return status


def remember(store: ProjectStore, project: Project, status: ProjectStatus) -> None:
    """Adresse und Datum des letzten Hochladens in der Datenbank merken, für den nächsten Start."""
    if status.repo is None:
        return
    remote = status.repo.remote if status.repo.is_repo else None
    last = status.repo.last_upload[:19] if status.repo.last_upload else None
    if remote != project.remote or (last or None) != (project.last_updated or None):
        store.set_remote(project, remote, last)


def _date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return f"{datetime.fromisoformat(iso.replace('Z', '+00:00')):%d.%m.%Y}"
    except ValueError:
        return ""


def project_line(project: Project, status: ProjectStatus | None,
                 platform_name: str = "GitHub") -> str:
    parts = [project.name]
    if not project.folder_found:
        parts.append("Ordner nicht gefunden")
        return ", ".join(parts)
    if status is not None and status.repo is not None and not status.on_platform:
        parts.append(f"noch nicht auf {platform_name}")
    elif project.last_updated:
        parts.append(f"aktualisiert am {_date(project.last_updated)}")
    if status is not None and status.unfinished_merge:
        parts.append(status.unfinished_merge)
    if status is not None and status.on_platform:
        if status.pending:
            parts.append(f"{count(status.pending, 'Datei', 'Dateien')} noch nicht hochgeladen")
        if status.repo.behind:
            parts.append(f"{count(status.repo.behind, 'Änderung', 'Änderungen')} auf "
                         f"{platform_name} noch nicht geholt")
    if status is not None and status.venv.broken:
        parts.append("virtuelle Umgebung muss neu angelegt werden")
    return ", ".join(parts)


def code_line(status: ProjectStatus | None, platform_name: str = "GitHub") -> str:
    parts = ["Code"]
    if status is None or status.repo is None:
        return parts[0]
    if status.other_branch:
        parts.append(f"Branch {status.other_branch}")
    if status.unfinished_merge:
        parts.append(status.unfinished_merge)
    if not status.on_platform:
        parts.append(f"noch nicht auf {platform_name}")
    elif status.repo.branch and not status.repo.upstream:
        parts.append(f"Branch noch nicht auf {platform_name}")   # neuer Branch (Phase 5f)
    elif status.pending:
        parts.append(f"{count(status.pending, 'Datei', 'Dateien')} noch nicht hochgeladen")
    else:
        parts.append("alles hochgeladen")
    if status.on_platform and status.repo.behind:
        # Wie beim Projekt, damit man an Code sieht, dass hier geholt werden muss
        parts.append(f"{count(status.repo.behind, 'Änderung', 'Änderungen')} auf "
                     f"{platform_name} noch nicht geholt")
    if status.repo.stashes:
        parts.append("Änderungen beiseitegelegt")
    return ", ".join(parts)


def remote_line(name: str, pushed_at: str, platform_name: str = "GitHub") -> str:
    parts = [name, f"nur auf {platform_name}"]
    if _date(pushed_at):
        parts.append(f"aktualisiert am {_date(pushed_at)}")
    return ", ".join(parts)
