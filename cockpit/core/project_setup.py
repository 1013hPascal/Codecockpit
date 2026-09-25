"""Projekte herunterladen und wieder verbinden (Konzept 7.3 und 7.5).

Beides läuft im Hintergrund und braucht den Zugang des Kontos. Git bekommt ihn nur über
Umgebungsvariablen, nie über die Befehlszeile.
"""
from __future__ import annotations

import threading
from pathlib import Path

from cockpit.core import git
from cockpit.core.errors import CockpitError
from cockpit.core.projects import CODE_DIR, Project
from cockpit.core.remote_repos import StoredRepo


def _environment(services, account_id: int | None) -> dict[str, str]:
    if account_id is None:
        return {}
    platform = services.platform(account_id)
    return dict(platform.git_credentials().environment) if platform is not None else {}


def download_target(root: Path, name: str) -> Path:
    """Projektordner für ein heruntergeladenes Repository: <Hauptordner>\\<Name>."""
    return root / name


def download(services, repo: StoredRepo, root: Path,
             cancel: threading.Event | None = None) -> Project:
    """Repository in <Hauptordner>\\<Name>\\Code herunterladen und in die Liste aufnehmen."""
    project_dir = download_target(root, repo.name)
    code_dir = project_dir / CODE_DIR
    if code_dir.exists() and any(code_dir.iterdir()):
        raise CockpitError(f"Den Ordner {code_dir} gibt es schon, und er ist nicht leer. "
                           "Nichts wurde verändert.")
    git.clone(repo.clone_url, code_dir, _environment(services, repo.account_id), cancel)
    project = services.projects.add(project_dir)
    services.projects.set_account(project, repo.account_id)
    services.projects.set_remote(project, repo.address, repo.pushed_at[:19] or None)
    return services.projects.get(project.id)


def connect(services, project: Project, url: str, account_id: int | None,
            cancel: threading.Event | None = None) -> str:
    """Code-Ordner ohne Git-Ordner mit seinem Repository verbinden. Die Dateien bleiben
    unverändert. Gibt den Branch zurück."""
    branch = git.connect(project.code_dir, url, _environment(services, account_id), cancel)
    if account_id is not None:
        services.projects.set_account(project, account_id)
    services.projects.set_remote(project, git.parse_remote(url), None)
    return branch
