"""Projekt umbenennen und löschen (Wunsch des Nutzers vom 06.10.2026, "Projekt verwalten").

Umbenennen ändert alles: den Namen in der Liste, den Projektordner auf dem Rechner und das
Repository auf der Plattform. Erst der Ordner, weil er am ehesten scheitert (ein Programm hat ihn
offen). Dann ist noch nichts geändert. Danach das Repository. Die Plattform leitet die alte
Adresse weiter.

Löschen entfernt das Repository auf der Plattform (das macht die Oberfläche mit ihren Rückfragen)
und legt den Projektordner in die Sicherheitskopien. Dort bleibt er 30 Tage.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import replace
from pathlib import Path
from typing import Callable

from cockpit.core import git
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project, ProjectStore

log = logging.getLogger(__name__)

_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
             *(f"lpt{i}" for i in range(1, 10))}
LOCKED = ("Der Ordner ließ sich nicht umbenennen. Ist er noch in einem anderen Programm geöffnet, "
          "zum Beispiel im Explorer, in einem Terminal oder in Claude? Es wurde nichts geändert.")


def name_problem(store: ProjectStore, project: Project, name: str) -> str:
    """Grund, warum der neue Name nicht geht, sonst leer."""
    name = name.strip()
    if not name:
        return "Bitte geben Sie einen Namen ein."
    if name == project.name:
        return "Das ist schon der Name des Projekts."
    if _FORBIDDEN.search(name) or name.endswith((".", " ")) or name.lower() in _RESERVED:
        return ("Der Name darf diese Zeichen nicht enthalten: < > : \" / \\ | ? * und nicht mit "
                "Punkt oder Leerzeichen enden.")
    if any(p.name.lower() == name.lower() and p.id != project.id for p in store.all()):
        return f"Es gibt schon ein Projekt {name}."
    if not project.linked:
        target = project.project_dir.parent / name
        if target.exists() and not _same(target, project.project_dir):
            return f"Den Ordner {target} gibt es schon."
    return ""


def _same(a: Path, b: Path) -> bool:
    return os.path.normcase(str(a)) == os.path.normcase(str(b))


def _moved(path: Path | None, old: Path, new: Path) -> Path | None:
    """Pfad nach dem Umbenennen von old in new."""
    if path is None:
        return None
    try:
        return new / path.relative_to(old)
    except ValueError:
        return path


def rename_local(store: ProjectStore, project: Project, name: str,
                 on_step: Callable[[str], None] = lambda text: None) -> Project:
    """Projektordner und Namen in der Liste ändern. Branch-Ordner werden danach repariert, weil
    Git ihre Orte fest einträgt. Verknüpfte Projekte behalten ihre Ordner, nur der Name ändert
    sich. Gibt das geänderte Projekt zurück."""
    name = name.strip()
    problem = name_problem(store, project, name)
    if problem:
        raise CockpitError(problem)
    if project.linked or not project.folder_found:
        return store.rename(project, name, project.project_dir, project.code_dir,
                            project.exe_dir)
    from cockpit.core import worktrees
    old_dir = project.project_dir
    new_dir = old_dir.parent / name
    trees = [t.path for t in worktrees.list_worktrees(project)]
    on_step("Ordner wird umbenannt")
    try:
        os.rename(old_dir, new_dir)                # ändert keinen Inhalt, nur den Namen
    except OSError as exc:
        raise CockpitError(LOCKED, str(exc)) from None
    log.info("Projektordner umbenannt: %s -> %s", old_dir, new_dir)
    renamed = store.rename(project, name, new_dir, _moved(project.code_dir, old_dir, new_dir),
                           _moved(project.exe_dir, old_dir, new_dir))
    if trees:
        on_step("Branch-Ordner werden angepasst")
        git.run(["worktree", "repair", *(str(_moved(t, old_dir, new_dir)) for t in trees)],
                renamed.code_dir, check=False)
    return renamed


def rename_remote(platform, project: Project, name: str) -> git.RemoteAddress | None:
    """Repository auf der Plattform umbenennen und die Adresse origin anpassen. Gibt die neue
    Adresse zurück, None ohne Repository."""
    if project.remote is None:
        return None
    from cockpit.core.repo_admin import repo_ref
    ref = platform.rename_repo(repo_ref(project), name.strip())
    url = platform.clone_url(ref)
    if git.is_repo(project.code_dir) and git.config_get(project.code_dir, "remote.origin.url"):
        git.run(["remote", "set-url", "origin", url], project.code_dir, action="Verbinden")
    return replace(project.remote, owner=ref.owner, name=ref.name)


def rename_main(store: ProjectStore, project: Project, old: str, new: str, platform=None,
                env: dict[str, str] | None = None,
                on_step: Callable[[str], None] = lambda text: None) -> tuple[Project, str]:
    """Den Haupt-Branch umbenennen (Wunsch des Nutzers vom 06.10.2026, "Branches verwalten").
    Auf der Plattform über ihre Schnittstelle, weil man den Haupt-Branch dort nicht löschen und
    neu hochladen kann. Sie stellt auch den Haupt-Branch um. Dann hier, und der Ordner
    Code\\<alt> heißt danach Code\\<neu>. Gibt das Projekt und einen Hinweis zurück, wenn etwas
    nicht geklappt hat."""
    from cockpit.core import branches, worktrees
    code_dir = project.code_dir
    remote = git.run(["rev-parse", "-q", "--verify", f"refs/remotes/origin/{old}"], code_dir,
                     check=False).returncode == 0
    if remote:
        if platform is None:
            raise CockpitError("Für das Umbenennen auf der Plattform fehlt das Konto. Es wurde "
                               "nichts geändert.")
        from cockpit.core.repo_admin import repo_ref
        on_step("Branch wird auf der Plattform umbenannt")
        platform.rename_branch(repo_ref(project), old, new)
    on_step("Branch wird hier umbenannt")
    git.run(["branch", "-m", old, new], code_dir, action="Umbenennen")
    if remote:
        try:
            branches.refresh(code_dir, env)
        except CockpitError as exc:
            log.warning("Nach dem Umbenennen nicht abgefragt: %s", exc.message)
        git.run(["branch", "-u", f"origin/{new}", new], code_dir, check=False)
        git.run(["remote", "set-head", "origin", new], code_dir, check=False)
    if not project.has_branch_folders or code_dir.name != worktrees.folder_name(old):
        return project, ""
    target = code_dir.parent / worktrees.folder_name(new)
    if target.exists():
        return project, f"Der Ordner heißt weiter {code_dir.name}, {target.name} gibt es schon."
    trees = [t.path for t in worktrees.list_worktrees(project)]
    on_step("Ordner wird umbenannt")
    try:
        os.rename(code_dir, target)
    except OSError as exc:
        log.warning("Ordner %s nicht umbenannt: %s", code_dir, exc)
        return project, (f"Der Ordner heißt weiter {code_dir.name}. Er war noch in einem anderen "
                         "Programm geöffnet.")
    if trees:
        git.run(["worktree", "repair", *(str(t) for t in trees)], target, check=False)
    return store.set_code_dir(project, target), ""


def delete_local(store: ProjectStore, project: Project) -> list[Path]:
    """Projektordner in die Sicherheitskopien legen und das Projekt aus der Liste nehmen. Bei
    einem verknüpften Projekt der Code-Ordner und der Exe-Ordner. Gibt die Orte der Kopien
    zurück."""
    from cockpit.core.backups import move_into_backup
    folders = ([project.code_dir, project.exe_dir] if project.linked else [project.project_dir])
    kept: list[Path] = []
    for folder in folders:
        if folder is None or not folder.exists():
            continue
        try:
            kept.append(move_into_backup(folder, project.name, "Projekt gelöscht"))
        except OSError as exc:
            raise CockpitError("Der Ordner ließ sich nicht löschen. Ist er noch in einem anderen "
                               "Programm geöffnet?", str(exc)) from None
    store.remove(project.id)
    return kept
