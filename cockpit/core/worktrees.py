"""Ein Ordner pro Branch (Phase 10f).

Der Ordner Code enthält dann nur Ordner: den Haupt-Branch, zum Beispiel Code\\main, und daneben
einen Ordner pro Branch, zum Beispiel Code\\neue-funktion. Technisch sind das Worktrees von Git:
Alle Ordner teilen sich ein Repository, und ein Commit in einem Ordner landet immer in dessen
Branch. Der Haupt-Branch bleibt code_dir des Projekts, damit Exe-Bau, cockpit.toml und alles
andere wie bisher arbeiten.

Ein Branch-Ordner wird nie ohne Sicherheitskopie gelöscht, wenn darin etwas liegt, das es sonst
nirgends gibt. Der Branch selbst bleibt beim Entfernen des Ordners erhalten.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from cockpit.core import backups, branches, git
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project

log = logging.getLogger(__name__)

MOVING = ".codecockpit-umzug"               # Zwischenordner beim Einrichten
SKIP_IN_BACKUP = shutil.ignore_patterns(".venv", "__pycache__")


@dataclass(frozen=True)
class Worktree:
    path: Path
    branch: str                              # leer: kein Branch (detached)
    gone: bool = False                       # auf der Plattform gelöscht, meist nach dem Übernehmen

    @property
    def folder(self) -> str:
        return self.path.name


def folder_name(branch: str) -> str:
    """Ordnername für einen Branch: "feature/login" wird zu "feature-login"."""
    name = re.sub(r'[\\/:*?"<>|\s]+', "-", branch).strip("-. ")
    return name or "branch"


def _same(a: Path, b: Path) -> bool:
    return os.path.normcase(str(a.resolve())) == os.path.normcase(str(b.resolve()))


def list_worktrees(project: Project) -> list[Worktree]:
    """Die Branch-Ordner, ohne den Haupt-Branch. Nur bei Projekten mit Branch-Ordnern."""
    if not project.has_branch_folders or not project.folder_found:
        return []
    result = git.run(["worktree", "list", "--porcelain"], project.code_dir, check=False)
    found: list[Worktree] = []
    # Der erste Eintrag ist immer der Haupt-Branch (Code\main), auch von einem Branch-Ordner aus
    for block in result.stdout.replace("\r", "").strip().split("\n\n")[1:]:
        fields: dict[str, str] = {}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            fields[key] = value
        if "worktree" not in fields or "prunable" in fields or "bare" in fields:
            continue
        path = Path(fields["worktree"])
        if not path.is_dir() or _same(path, project.code_dir):
            continue
        branch = fields.get("branch", "").removeprefix("refs/heads/")
        found.append(Worktree(path, branch, _gone(project.code_dir, branch)))
    return sorted(found, key=lambda w: w.folder.lower())


def _gone(code_dir: Path, branch: str) -> bool:
    if not branch:
        return False
    result = git.run(["for-each-ref", "--format=%(upstream:track)", f"refs/heads/{branch}"],
                     code_dir, check=False)
    return "[gone]" in result.stdout


def prune(code_dir: Path) -> None:
    """Einträge von Branch-Ordnern vergessen, deren Ordner es nicht mehr gibt (git worktree
    prune). Sonst weigert sich Git, dort wieder einen Ordner anzulegen ("missing but already
    registered worktree"), zum Beispiel nachdem ein Ordner im Explorer gelöscht wurde oder ein
    Entfernen mittendrin abbrach. Löscht keine Dateien."""
    git.run(["worktree", "prune"], code_dir, check=False)


def free_folder(project: Project, branch: str) -> Path:
    base = folder_name(branch)
    path = project.code_root / base
    number = 2
    while path.exists():
        path = project.code_root / f"{base}-{number}"
        number += 1
    return path


def _refresh(project: Project, env: Mapping[str, str] | None,
             cancel: threading.Event | None) -> None:
    """Stand der Plattform holen. Klappt es nicht, geht es mit dem lokalen Stand weiter."""
    try:
        branches.refresh(project.code_dir, dict(env or {}), cancel)
    except CockpitError as exc:
        log.warning("Holen vor dem Branch-Ordner: %s %s", exc.message, exc.details)


def _exists(code_dir: Path, ref: str) -> bool:
    return git.run(["rev-parse", "-q", "--verify", ref], code_dir, check=False).returncode == 0


def create(project: Project, name: str, env: Mapping[str, str] | None = None,
           cancel: threading.Event | None = None) -> Worktree:
    """Neuer Branch mit eigenem Ordner. Er beginnt beim neuesten Stand des Haupt-Branches auf
    der Plattform (vorher wird geholt), sonst beim lokalen Haupt-Branch."""
    problem = branches.name_problem(project.code_dir, name)
    if problem:
        raise CockpitError(problem)
    _refresh(project, env, cancel)
    prune(project.code_dir)
    main = git.status(project.code_dir).default_branch
    base = next((ref for ref in (f"origin/{main}", main) if _exists(project.code_dir, ref)),
                "HEAD")
    path = free_folder(project, name)
    # --no-track: Der neue Branch lädt später unter eigenem Namen hoch, nicht nach main.
    git.run(["worktree", "add", "-q", "--no-track", "-b", name, str(path), base],
            project.code_dir, action="Branch-Ordner anlegen")
    return Worktree(path, name)


def open_branch(project: Project, name: str, env: Mapping[str, str] | None = None,
                cancel: threading.Event | None = None) -> Worktree:
    """Ordner für einen vorhandenen Branch, auch für einen, den es nur auf der Plattform gibt."""
    for existing in list_worktrees(project):
        if existing.branch == name:
            return existing
    prune(project.code_dir)
    path = free_folder(project, name)
    if _exists(project.code_dir, f"refs/heads/{name}"):
        args = ["worktree", "add", "-q", str(path), name]
    else:
        _refresh(project, env, cancel)
        if not _exists(project.code_dir, f"refs/remotes/origin/{name}"):
            raise CockpitError(f"Den Branch {name} gibt es nicht mehr.")
        args = ["worktree", "add", "-q", "--track", "-b", name, str(path), f"origin/{name}"]
    result = git.run(args, project.code_dir, check=False)
    if result.returncode != 0:
        text = (result.stderr or result.stdout).lower()
        if "already" in text and ("checked out" in text or "used by worktree" in text):
            raise CockpitError(f"{name} ist schon in einem anderen Ordner geöffnet, vielleicht "
                               "im Ordner des Haupt-Branches. Wechseln Sie dort zuerst zu "
                               "main.", (result.stderr or result.stdout).strip())
        raise git.explain(result, "Branch-Ordner anlegen")
    return Worktree(path, name)


def needs_backup(worktree: Worktree) -> bool:
    """Liegt im Ordner etwas, das es sonst nirgends gibt? Änderungen ohne Commit, Commits, die
    noch nicht hochgeladen sind, oder ein Branch, der nie hochgeladen wurde."""
    state = git.status(worktree.path)
    return bool(state.changed or state.ahead or (state.has_commits and not state.upstream
                                                 and not worktree.gone))


def remove(project: Project, worktree: Worktree) -> Path | None:
    """Branch-Ordner entfernen. Der Branch bleibt. Gibt die Sicherheitskopie zurück, falls
    eine nötig war."""
    backup = None
    if needs_backup(worktree):
        folder = backups.new_backup_dir(project.name, f"Branch-Ordner {worktree.folder}",
                                        worktree.path)
        try:
            shutil.copytree(worktree.path, folder / worktree.folder, ignore=SKIP_IN_BACKUP,
                            symlinks=True)
        except OSError as exc:
            raise CockpitError("Die Sicherheitskopie ließ sich nicht anlegen. Der Ordner bleibt.",
                               str(exc)) from None
        backup = folder
    result = git.run(["worktree", "remove", "--force", str(worktree.path)], project.code_dir,
                     check=False)
    if result.returncode != 0 and worktree.path.exists():
        backups.remove_tree(worktree.path)
        if worktree.path.exists():
            raise CockpitError("Der Ordner ließ sich nicht ganz löschen. Ist er noch in einem "
                               "anderen Programm geöffnet?", (result.stderr or "").strip())
    git.run(["worktree", "prune"], project.code_dir, check=False)
    return backup


def can_convert(project: Project) -> bool:
    return (not project.linked and not project.has_branch_folders and project.folder_found
            and git.is_repo(project.code_dir) and (project.code_dir / ".git").is_dir())


def convert(project: Project, on_step: Callable[[str], None] = lambda text: None) -> Path:
    """Ordner für Branches einrichten: Der Inhalt von Code wandert nach Code\\<Branch>, zum
    Beispiel Code\\main. Vorher kommt eine Sicherheitskopie in den Ordner backups (ohne die
    virtuelle Umgebung, die danach ohnehin neu angelegt wird). Gibt den neuen Ordner zurück."""
    if not can_convert(project):
        raise CockpitError("Dieses Projekt lässt sich nicht umstellen.")
    root = project.code_dir
    state = git.status(root)
    name = folder_name(state.branch or state.default_branch)
    on_step("Sicherheitskopie wird angelegt")
    folder = backups.new_backup_dir(project.name, "vor dem Einrichten der Branch-Ordner", root)
    try:
        shutil.copytree(root, folder / root.name, ignore=SKIP_IN_BACKUP, symlinks=True)
    except OSError as exc:
        raise CockpitError("Die Sicherheitskopie ließ sich nicht anlegen. Es wurde nichts "
                           "verschoben.", str(exc)) from None
    on_step(f"Dateien werden nach Code\\{name} verschoben")
    moving = root / MOVING
    moving.mkdir()
    moved: list[Path] = []
    try:
        for item in sorted(root.iterdir()):
            if item == moving:
                continue
            os.rename(item, moving / item.name)       # ändert keinen Inhalt, nur den Ort
            moved.append(item)
        target = root / name
        os.rename(moving, target)
    except OSError as exc:
        for item in reversed(moved):
            try:
                os.rename(moving / item.name, item)
            except OSError:
                log.exception("Zurückverschieben fehlgeschlagen: %s", item)
        try:
            moving.rmdir()
        except OSError:
            pass
        raise CockpitError("Die Dateien ließen sich nicht verschieben. Ist der Ordner noch in "
                           "einem anderen Programm geöffnet, zum Beispiel im Explorer, in einem "
                           "Terminal oder in Claude? Es wurde nichts geändert.", str(exc)) from None
    return target
