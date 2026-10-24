"""Stand und Bedingungen hinter den Aktionen der Projektliste (Wunsch des Nutzers, 02.10.2026).

Kurze Texte wie "2 Dateien offen" und die Prüfungen, wann eine Aktion erscheint.
Aus project_actions.py herausgelöst am 21.10.2026, nur verschoben. Die Namen sind weiter über
project_actions erreichbar.
"""
from __future__ import annotations

from cockpit.core import git
from cockpit.core.actions import ActionContext
from cockpit.core.availability import Availability
from cockpit.core.text import count


def _push_detail(context: ActionContext) -> str:
    status = context.status
    if status is None or status.repo is None or not status.repo.is_repo:
        return ""
    parts = []
    if status.pending:
        parts.append(f"{count(status.pending, 'Datei', 'Dateien')} offen")
    if status.repo.ahead:
        parts.append(f"{count(status.repo.ahead, 'Commit', 'Commits')} nicht hochgeladen")
    return ", ".join(parts) or "nichts offen"


def _pull_detail(context: ActionContext) -> str:
    status = context.status
    if status is None or status.repo is None or not status.repo.is_repo:
        return ""
    behind = status.repo.behind
    return count(behind, "neue Änderung", "neue Änderungen") if behind else "alles aktuell"


def _changed_detail(context: ActionContext) -> str:
    status = context.status
    if status is None or status.repo is None or not status.repo.is_repo:
        return ""
    changed = len(status.repo.changed)
    return f"{count(changed, 'Datei', 'Dateien')} geändert" if changed else "nichts geändert"


def _pulls_text(number: int) -> str:
    return f"{number} offen" if number else "keine offen"


def _branch_pulls_detail(context: ActionContext) -> str:
    return _pulls_text(context.status.open_pulls) if context.status is not None else ""


def _has_commits(context: ActionContext) -> bool:
    """Branches gibt es erst ab dem ersten Commit."""
    status = context.status
    return (status is not None and status.repo is not None and status.repo.is_repo
            and status.repo.has_commits)


def _has_stashes(context: ActionContext) -> bool:
    status = context.status
    return status is not None and status.repo is not None and status.repo.stashes > 0


def _on_other_branch(context: ActionContext) -> bool:
    """Auf einem anderen Branch als main, und das Projekt liegt auf der Plattform."""
    return (_has_remote(context) and context.status is not None
            and bool(context.status.other_branch))


def _has_remote(context: ActionContext) -> bool:
    return context.project is not None and context.project.remote is not None


def _has_upstream(context: ActionContext) -> bool:
    """Ein Fork mit eingetragenem Original (21.10.2026)."""
    from cockpit.core import forks
    return (context.project is not None and context.project.folder_found
            and forks.has_upstream(context.project.code_dir))


def _not_on_platform(context: ActionContext) -> bool:
    status = context.status
    return (context.project is not None and context.project.folder_found
            and status is not None and status.repo is not None and not status.on_platform)


def _on_platform(context: ActionContext) -> bool:
    return (context.project is not None and context.project.folder_found
            and context.status is not None and context.status.on_platform)


def _branch_unpublished(context: ActionContext) -> bool:
    """Der Branch hat Commits, liegt aber noch nicht auf der Plattform (Phase 10f)."""
    return (_on_platform(context) and context.status.repo.has_commits
            and bool(context.status.repo.branch) and not context.status.repo.upstream)


def _unfinished_merge(context: ActionContext) -> bool:
    return context.status is not None and bool(context.status.unfinished_merge)


def _git_availability(context: ActionContext) -> Availability:
    if git.find_git() is None:
        return Availability.no("Git ist nicht installiert.")
    return Availability.yes()


def _discard_availability(context: ActionContext) -> Availability:
    status = context.status
    if status is not None and status.unfinished_merge:
        return Availability.no("Bitte lösen Sie zuerst die Konflikte.")
    if status is not None and status.repo is not None and not status.repo.changed:
        return Availability.no("Es gibt keine Änderungen ohne Commit.")
    return _git_availability(context)


def _is_repo(context: ActionContext) -> bool:
    status = context.status
    return status is not None and status.repo is not None and status.repo.is_repo


def _git_missing(context: ActionContext) -> bool:
    status = context.status
    return (context.project is not None and context.project.folder_found
            and status is not None and status.repo is not None and not status.repo.is_repo)


def _venv_broken(context: ActionContext) -> bool:
    return context.status is not None and context.status.venv.broken
