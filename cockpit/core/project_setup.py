"""Projekte herunterladen und wieder verbinden (Konzept 7.3 und 7.5).

Beides läuft im Hintergrund und braucht den Zugang des Kontos. Git bekommt ihn nur über
Umgebungsvariablen, nie über die Befehlszeile.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path

from cockpit.core import git, worktrees
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project, code_root_in
from cockpit.core.remote_repos import StoredRepo

log = logging.getLogger(__name__)


def _environment(services, account_id: int | None) -> dict[str, str]:
    if account_id is None:
        return {}
    platform = services.platform(account_id)
    return dict(platform.git_credentials().environment) if platform is not None else {}


DOWNLOADING = "wird-heruntergeladen"


def download_target(root: Path, name: str) -> Path:
    """Projektordner für ein heruntergeladenes Repository: <Hauptordner>\\<Name>."""
    return root / name


def download(services, repo: StoredRepo, root: Path,
             cancel: threading.Event | None = None) -> Project:
    """Repository in <Hauptordner>\\<Name>\\Code herunterladen und in die Liste aufnehmen."""
    project_dir = download_target(root, repo.name)
    code_dir = code_root_in(project_dir)        # auch ein alter Ordner Code zählt
    if code_dir.exists() and any(code_dir.iterdir()):
        raise CockpitError(f"Den Ordner {code_dir} gibt es schon, und er ist nicht leer. "
                           "Nichts wurde verändert.")
    folders = services.settings.load().branch_folders
    # Phase 10f: mit einem Ordner pro Branch nach Repository\<Haupt-Branch>, zum Beispiel Repository\main
    target = code_dir / DOWNLOADING if folders else code_dir
    git.clone(repo.clone_url, target, _environment(services, repo.account_id), cancel)
    if folders:
        state = git.status(target)
        target.rename(code_dir / worktrees.folder_name(state.branch or state.default_branch))
    project = services.projects.add(project_dir)
    services.projects.set_account(project, repo.account_id)
    services.projects.set_remote(project, repo.address, repo.pushed_at[:19] or None)
    services.remote_repos.unhide(repo.address)          # wieder geholt: wieder in der Liste
    return services.projects.get(project.id)


def download_fork(services, original: StoredRepo, root: Path,
                  cancel: threading.Event | None = None) -> Project:
    """Fork des Originals im Konto anlegen, den Fork herunterladen und das Original als upstream
    eintragen (21.10.2026)."""
    from cockpit.core import forks
    from cockpit.platforms.base import RepoRef, SupportsForks
    platform = services.platform(original.account_id) if original.account_id else None
    if not isinstance(platform, SupportsForks):
        raise CockpitError("Die Plattform kennt keine Forks.")
    fork = platform.fork(RepoRef(original.owner, original.name), cancel)
    stored = StoredRepo(0, original.account_id, original.host, fork.ref.owner, fork.ref.name,
                        fork.private, fork.clone_url, fork.web_url, fork.pushed_at)
    project = download(services, stored, root, cancel)
    url = original.clone_url or f"https://{original.host}/{original.owner}/{original.name}.git"
    forks.add_upstream(project.code_dir, url)
    try:
        forks.fetch(project.code_dir, _environment(services, original.account_id), cancel)
    except CockpitError as exc:                 # später mit "Vom Original holen" noch einmal
        log.warning("Original holen: %s %s", exc.message, exc.details)
    return project


def connect(services, project: Project, url: str, account_id: int | None,
            cancel: threading.Event | None = None) -> str:
    """Code-Ordner ohne Git-Ordner mit seinem Repository verbinden. Die Dateien bleiben
    unverändert. Gibt den Branch zurück."""
    branch = git.connect(project.code_dir, url, _environment(services, account_id), cancel)
    if account_id is not None:
        services.projects.set_account(project, account_id)
    services.projects.set_remote(project, git.parse_remote(url), None)
    return branch
