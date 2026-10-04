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


def repo_missing(services, project: Project) -> bool:
    """True, wenn das Projekt eine Adresse hat, das Repository auf der Plattform aber fehlt.
    Ohne Konto oder ohne Zugang aus dem Tresor: False (unbekannt)."""
    from cockpit.core import upload
    if not project.folder_found or not git.is_repo(project.code_dir):
        return False
    address = git.parse_remote(git.config_get(project.code_dir, "remote.origin.url"))
    if address is None:
        return False
    try:
        account = services.account_for_host(address.host)
        account_id = project.account_id or (account.id if account else None)
        platform = services.platform(account_id) if account_id is not None else None
        return platform is not None and upload.repo_missing(platform, project.code_dir)
    except CockpitError:
        return False


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


def forget_address(services, address) -> list[str]:
    """Nach dem Löschen eines Repositorys: bei jedem Projekt mit dieser Adresse die Verbindung
    origin entfernen, auch bei Projekten, die aus der Liste entfernt wurden (Rückmeldung des
    Nutzers vom 04.10.2026: die Adresse blieb stehen, das Cockpit hielt das Projekt danach für
    hochgeladen). Gibt die Namen der getrennten Projekte zurück."""
    from cockpit.core.projects import CODE_DIR, main_code_dir
    folders = [(p.code_dir, p.name) for p in services.projects.all() if p.folder_found]
    for removed in services.projects.removed_dirs():
        code_root = Path(removed) / CODE_DIR
        # Gemerkt ist der Ordner klein geschrieben, angesagt wird der echte Name
        folder = Path(removed)
        try:
            folder = next((p for p in folder.parent.iterdir()
                           if p.name.lower() == folder.name.lower()), folder)
        except OSError:
            pass
        folders.append((main_code_dir(code_root) if code_root.is_dir() else folder,
                        folder.name))
    done: list[str] = []
    for code_dir, label in folders:
        try:
            found = git.parse_remote(git.config_get(code_dir, "remote.origin.url")) \
                if git.is_repo(code_dir) else None
            if found is None or found.key != address.key:
                continue
            disconnect(code_dir)
        except CockpitError as exc:
            log.warning("Verbindung nicht entfernt: %s (%s)", code_dir, exc.message)
            continue
        done.append(label)
        project = services.projects.find_by_code_dir(code_dir)
        if project is not None:
            services.projects.set_remote(project, None, None)
    return done


def disconnect(code_dir: Path) -> None:
    """Nach dem Löschen auf der Plattform, wenn das Projekt nur lokal bleiben soll: die Verbindung
    origin entfernen. Dateien und Verlauf bleiben, das Projekt heißt danach "noch nicht auf
    GitHub"."""
    if git.is_repo(code_dir) and git.config_get(code_dir, "remote.origin.url"):
        git.run(["remote", "remove", "origin"], code_dir, action="Verbindung entfernen")
        log.info("Verbindung origin entfernt: %s", code_dir)
