"""Links und Repository verwalten (Konzept 9.5, Teilschritt 5e).

Hier steht, was ohne Oberfläche geht: welches Konto zu einem Projekt gehört, die Links, die
Sicherheitsprüfung vor dem Wechsel auf öffentlich und was nach dem Löschen auf dem Rechner passiert.
Das Gespräch mit der Plattform (Sichtbarkeit, Archivieren, Löschen, Mitarbeiter) läuft über die
Schnittstelle Platform und SupportsCollaborators.
"""
from __future__ import annotations

import logging
from pathlib import Path

from cockpit.adapters import registry as adapter_registry
from cockpit.core import git, safety_check
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.platforms.base import RepoRef

log = logging.getLogger(__name__)

NO_ACCOUNT = "Zur Adresse dieses Projekts gibt es kein Konto in der Kontenverwaltung."


def account_for(services, project: Project):
    """Konto des Projekts: das zugeordnete, sonst das passende zur Adresse. None: keines."""
    if project.account_id is not None:
        account = services.accounts.get(project.account_id)
        if account is not None:
            return account
    if project.remote is None:
        return None
    return services.account_for_host(project.remote.host)


def repo_ref(project: Project) -> RepoRef:
    if project.remote is None:
        raise CockpitError(f"{project.name} ist nicht mit einem Repository verbunden.")
    return RepoRef(project.remote.owner, project.remote.name)


def links(services, project: Project) -> list[tuple[str, str]]:
    """Links des Repositories, das Wichtigste zuerst. Braucht keinen Zugang aus dem Tresor.
    Der Download-Link kommt mit dem Feature Releases (Phase 14)."""
    account = account_for(services, project)
    if account is None:
        raise CockpitError(NO_ACCOUNT)
    cls = adapter_registry.adapter_class(account.kind, account.adapter)
    platform = cls.from_account(services.accounts.values(account, with_secrets=False))
    found = platform.links(repo_ref(project))
    return [("Projektseite", found.project_page), ("README", found.readme)]


def public_scan(code_dir: Path) -> safety_check.Report:
    """Sicherheitsprüfung über das ganze Repository vor dem Wechsel auf öffentlich (Konzept 9.5):
    alle Dateien in Git, der ganze Verlauf und alle E-Mail-Adressen in den Commits."""
    if not git.is_repo(code_dir):
        raise CockpitError("Der Code-Ordner ist kein Git-Repository.")
    result = git.run(["ls-files", "-z"], code_dir, action="Sicherheitsprüfung")
    files = [f for f in result.stdout.split("\0") if f]
    emails = safety_check.commit_emails(code_dir, "HEAD")
    return safety_check.scan(code_dir, files=files, public=True, emails=emails,
                             history_range="HEAD")


def disconnect(code_dir: Path) -> None:
    """Nach dem Löschen auf der Plattform, wenn das Projekt nur lokal bleiben soll: die Verbindung
    origin entfernen. Dateien und Verlauf bleiben, das Projekt heißt danach "noch nicht auf
    GitHub"."""
    if git.is_repo(code_dir) and git.config_get(code_dir, "remote.origin.url"):
        git.run(["remote", "remove", "origin"], code_dir, action="Verbindung entfernen")
        log.info("Verbindung origin entfernt: %s", code_dir)
