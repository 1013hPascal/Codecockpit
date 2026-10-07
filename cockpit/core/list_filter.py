"""Filter oben in der Projektliste und Zeichen für Offenes (Wunsch des Nutzers vom 07.10.2026).

Die Auswahl „Anzeigen:“ steht über den Projekten und Sammlungen:
- Alle Projekte (Vorgabe)
- Mit offenen Sachen: Änderungen ohne Commit, Commits nicht hochgeladen, auf GitHub neuer,
  Zusammenführen offen, offene Pull Requests, angefragte Reviews, auch in Branch-Ordnern
- Auf GitHub: Projekte mit Repository auf der Plattform und Repositories nur dort
- Mit Release: Projekte mit einer Exe in einem Release-Ordner
- Nur auf dem Rechner: Projekte ohne Repository auf der Plattform

Eine Sammlung zeigt nur ihre passenden Projekte. Der Kern importiert nie PySide6.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from cockpit.core.text import count

if TYPE_CHECKING:
    from cockpit.core.project_status import ProjectStatus
    from cockpit.core.projects import Project

ALL, OPEN, GITHUB, RELEASE, LOCAL = "all", "open", "github", "release", "local"
KINDS = (ALL, OPEN, GITHUB, RELEASE, LOCAL)
FILTER_KEY = "projects.list_filter"


def names(platform_name: str = "GitHub") -> dict[str, str]:
    return {ALL: "Alle Projekte", OPEN: "Mit offenen Sachen", GITHUB: f"Auf {platform_name}",
            RELEASE: "Mit Release", LOCAL: "Nur auf dem Rechner"}


def row_text(kind: str, platform_name: str = "GitHub", shown: int | None = None) -> str:
    """Zeile über den Projekten, zum Beispiel "Anzeigen: Mit offenen Sachen, 3 Projekte"."""
    text = f"Anzeigen: {names(platform_name).get(kind, names(platform_name)[ALL])}"
    if kind != ALL and shown is not None:
        text += f", {count(shown, 'Projekt', 'Projekte')}" if shown else ", keine Projekte"
    return text


def _open_here(status: "ProjectStatus") -> bool:
    repo = status.repo
    if status.pending or status.unfinished_merge:
        return True
    return repo is not None and repo.is_repo and bool(repo.changed or repo.ahead or repo.behind)


def is_open(status: "ProjectStatus | None") -> bool:
    if status is None:
        return False
    if _open_here(status) or status.repo_pulls or status.review_requests:
        return True
    return any(_open_here(inner) for _tree, inner in status.worktrees)


def on_platform(project: "Project", status: "ProjectStatus | None") -> bool:
    if status is not None and status.repo is not None:
        return status.on_platform
    return project.remote is not None              # gemerkt, solange der Stand noch fehlt


def matches(project: "Project", status: "ProjectStatus | None", kind: str) -> bool:
    if kind == OPEN:
        return is_open(status)
    if kind == GITHUB:
        return on_platform(project, status)
    if kind == RELEASE:
        return status is not None and status.has_release
    if kind == LOCAL:
        return project.folder_found and not on_platform(project, status)
    return True


def matches_remote(kind: str) -> bool:
    """Repositories nur auf der Plattform."""
    return kind in (ALL, GITHUB)


def markers(status: "ProjectStatus | None") -> str:
    """Kurze Zeichen für das Auge, vorne an der Zeile als Bild. Dieselbe Information steht als
    Text in der Zeile (keine Information nur über Zeichen oder Farbe)."""
    if status is None or status.repo is None:
        return ""
    repo = status.repo
    found = []
    if repo.changed or status.unfinished_merge:
        found.append("●")                          # Änderungen ohne Commit oder Konflikt
    if repo.ahead or (status.pending and not repo.changed):
        found.append("↑")                          # noch nicht hochgeladen
    if repo.behind:
        found.append("↓")                          # auf der Plattform neuer
    if status.repo_pulls:
        found.append("PR")
    if status.review_requests:
        found.append("R")
    return " ".join(found)
