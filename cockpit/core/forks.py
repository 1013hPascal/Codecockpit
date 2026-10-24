"""Forks: zu fremden Projekten beitragen (Wunsch des Nutzers vom 21.10.2026, nach dem Vergleich
mit GitHub Desktop).

Darf das Konto nicht in ein Repository hochladen, bietet das Cockpit beim Herunterladen einen Fork
an: eine eigene Kopie im Konto. Heruntergeladen wird der Fork (origin). Das Original heißt in Git
"upstream". So geht alles wie gewohnt: Hochladen landet im Fork, und ein Pull Request geht auf
Wunsch an das Original.

"Vom Original holen" bringt den Haupt-Branch auf den Stand des Originals. Das geht nur vorwärts
(fast-forward), damit nie etwas verloren geht. Hat der Haupt-Branch eigene Commits, erklärt das
Cockpit, dass sie besser in einen Branch gehören.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Mapping

from cockpit.core import git
from cockpit.core.errors import CockpitError

log = logging.getLogger(__name__)

UPSTREAM = "upstream"


def upstream(code_dir: Path) -> git.RemoteAddress | None:
    """Das Original eines Forks, None bei einem gewöhnlichen Projekt."""
    if not git.is_repo(code_dir):
        return None
    return git.parse_remote(git.config_get(code_dir, f"remote.{UPSTREAM}.url"))


def has_upstream(code_dir: Path) -> bool:
    """Schnell, ohne Git zu starten (für die Aktionsliste): steht upstream in der Konfiguration?
    In einem Branch-Ordner liegt sie im gemeinsamen Git-Ordner."""
    folder = git.git_dir(code_dir)
    common = folder / "commondir"
    if common.is_file():
        try:
            folder = (folder / common.read_text(encoding="utf-8").strip()).resolve()
        except OSError:
            return False
    try:
        text = (folder / "config").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return f'[remote "{UPSTREAM}"]' in text


def add_upstream(code_dir: Path, url: str) -> None:
    """Das Original als upstream eintragen. Die Adresse enthält nie Zugangsdaten."""
    if upstream(code_dir) is not None:
        git.run(["remote", "set-url", UPSTREAM, url], code_dir, action="Original eintragen")
    else:
        git.run(["remote", "add", UPSTREAM, url], code_dir, action="Original eintragen")


def fetch(code_dir: Path, env: Mapping[str, str] | None = None,
          cancel: threading.Event | None = None) -> None:
    git.run(["fetch", "--prune", UPSTREAM], code_dir, env=env, cancel=cancel, timeout=None,
            action="Vom Original holen")
    # Damit main_branch() den Haupt-Branch des Originals kennt
    git.run(["remote", "set-head", UPSTREAM, "--auto"], code_dir, env=env, check=False)


def main_branch(code_dir: Path) -> str:
    """Haupt-Branch des Originals, soweit bekannt, sonst der eigene."""
    head = git.run(["symbolic-ref", "--short", "-q", f"refs/remotes/{UPSTREAM}/HEAD"], code_dir,
                   check=False).stdout.strip()
    if head:
        return head.partition("/")[2]
    return git.status(code_dir).default_branch


def branches(code_dir: Path) -> list[str]:
    """Branches des Originals, der Haupt-Branch zuerst (für den Pull Request)."""
    result = git.run(["for-each-ref", "--format=%(refname:strip=3)", f"refs/remotes/{UPSTREAM}"],
                     code_dir, check=False)
    names = [n for n in result.stdout.splitlines() if n and n != "HEAD"]
    main = main_branch(code_dir)
    return sorted(names, key=lambda n: (n != main, n.lower())) or [main]


def _count(code_dir: Path, spec: str) -> int:
    result = git.run(["rev-list", "--count", spec], code_dir, check=False)
    try:
        return int(result.stdout.strip() or 0)
    except ValueError:
        return 0


def behind(code_dir: Path) -> tuple[int, int]:
    """(neue Commits im Original, eigene Commits im Haupt-Branch) nach dem letzten Holen."""
    main = main_branch(code_dir)
    theirs = f"refs/remotes/{UPSTREAM}/{main}"
    return _count(code_dir, f"{main}..{theirs}"), _count(code_dir, f"{theirs}..{main}")


def update_main(code_dir: Path) -> int:
    """Haupt-Branch vorwärts auf den Stand des Originals bringen. Gibt die Zahl der neuen
    Commits zurück. Danach ist der Haupt-Branch im Fork noch nicht hochgeladen."""
    main = main_branch(code_dir)
    state = git.status(code_dir)
    if state.branch != main:
        raise CockpitError(f"Das geht im Haupt-Branch {main}. Sie sind gerade auf "
                           f"{state.branch or 'keinem Branch'}.")
    new, own = behind(code_dir)
    if own:
        raise CockpitError(f"{main} hat eigene Commits, die das Original nicht kennt. Dann lässt "
                           f"sich {main} nicht einfach nachziehen. Legen Sie Ihre Arbeit besser "
                           "in einen eigenen Branch und stellen Sie von dort einen Pull Request.")
    if not new:
        return 0
    git.run(["merge", "-q", "--ff-only", f"refs/remotes/{UPSTREAM}/{main}"], code_dir,
            action="Vom Original holen")
    log.info("%d Commits vom Original geholt", new)
    return new
