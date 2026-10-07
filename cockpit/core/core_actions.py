"""Aktionen des Kerns für die Aktionsliste.

Hier stehen die einfachen Aktionen ohne Dialoge. Aktionen mit Rückfragen und Hintergrund-Arbeit
(Hochladen, Herunterladen ...) stehen in der Oberfläche, siehe ui/project_actions.py.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.availability import Availability


def _open(path: Path) -> None:
    """Ordner oder Datei mit dem zuständigen Windows-Programm öffnen (in Tests ersetzbar)."""
    os.startfile(path)  # noqa: S606 (nur Windows, bewusst)


open_path = _open


def _start_program(path: Path) -> None:
    subprocess.Popen([str(path)], cwd=str(path.parent))


start_program = _start_program


# -- Verfügbarkeit ------------------------------------------------------------------------
def _project_found(context: ActionContext) -> Availability:
    if context.project is None or not context.project.folder_found:
        return Availability.no("Der Ordner wurde nicht gefunden.")
    return Availability.yes()


def _exe_dir_found(context: ActionContext) -> Availability:
    if context.project is None or not context.project.has_exe_dir:
        return Availability.no("Den Ordner Exe gibt es nicht.")
    return Availability.yes()


def _exe_found(context: ActionContext) -> Availability:
    state = _exe_dir_found(context)
    if not state:
        return state
    from cockpit.core.exe import current_exe
    if current_exe(context.project) is None:
        return Availability.no("Im Ordner Exe liegt keine Exe.")
    return Availability.yes()


# -- Ausführen ------------------------------------------------------------------------------
def _open_project_dir(context: ActionContext) -> None:
    open_path(context.project.project_dir)
    context.announce("Projektordner wird geöffnet.")


def _open_code_dir(context: ActionContext) -> None:
    open_path(context.project.code_dir)
    context.announce("Branch-Ordner wird geöffnet.")


def _open_repo_dir(context: ActionContext) -> None:
    open_path(context.project.code_root)
    context.announce("Repository-Ordner wird geöffnet.")


def _main_name(context: ActionContext) -> str:
    from cockpit.core.local_releases import main_name
    return main_name(context.project, context.status)


def _release_title(context: ActionContext) -> str:
    """Zum Beispiel "Exe-main" oder "Exe-neue-funktion"."""
    if context.release is None:
        return "Exe"
    return context.release.title(_main_name(context))


def _open_exe_dir(context: ActionContext) -> None:
    """Ordner dieses Releases, solange es ihn noch nicht gibt der Ordner Exe."""
    release = context.release
    path = release.path if release is not None and release.path.is_dir()         else context.project.exe_dir
    open_path(path)
    context.announce(f"{_release_title(context)}-Ordner wird geöffnet.")


def _open_releases_dir(context: ActionContext) -> None:
    open_path(context.project.exe_dir)
    context.announce("Release-Ordner wird geöffnet.")


def _release_exe_found(context: ActionContext) -> Availability:
    from cockpit.core.local_releases import release_exe
    if context.release is None or release_exe(context.release) is None:
        return Availability.no("In diesem Release liegt noch keine Exe.")
    return Availability.yes()


def _run_exe(context: ActionContext) -> None:
    from cockpit.core.exe import current_exe
    from cockpit.core.errors import CockpitError
    from cockpit.core.exe import BLOCKED, is_blocked
    from cockpit.core.local_releases import release_exe
    if context.target is Target.RELEASE:
        exe = release_exe(context.release)
    else:
        exe = current_exe(context.project)
    try:
        start_program(exe)
    except OSError as exc:
        if is_blocked(exc):
            raise CockpitError(BLOCKED, repr(exc)) from None
        raise
    context.announce(f"{exe.name} wird gestartet.")


CORE_ACTIONS: tuple[Action, ...] = (
    Action("open_project_dir", "Projektordner öffnen", Target.PROJECT, _open_project_dir,
           availability=_project_found, order=95),
    # Wunsch des Nutzers (06.10.2026): bei Main und den Branches ganz unten "Branch-Ordner
    # öffnen", beim Repository "Repository-Ordner öffnen"
    Action("open_code_dir", "Branch-Ordner öffnen", Target.CODE, _open_code_dir,
           availability=_project_found, order=99),
    Action("open_repo_dir", "Repository-Ordner öffnen", Target.REPOSITORY, _open_repo_dir,
           availability=_project_found, order=95),
    Action("run_exe", "Exe starten", Target.EXE, _run_exe, availability=_exe_found,
           is_default=True, order=10),
    # Wunsch des Nutzers (06.10.2026): "Exe-main-Ordner öffnen", bei einem Branch-Release
    # "Exe-neue-funktion-Ordner öffnen", jeweils ganz unten
    Action("open_exe_dir", "Exe-Ordner öffnen", Target.EXE, _open_exe_dir,
           availability=_exe_dir_found, order=99,
           title=lambda c: f"{_release_title(c)}-Ordner öffnen"),
    Action("run_release_exe", "Exe starten", Target.RELEASE, _run_exe,
           availability=_release_exe_found, is_default=True, order=10),
    Action("open_release_dir", "Exe-Ordner öffnen", Target.RELEASE, _open_exe_dir,
           availability=_exe_dir_found, order=99,
           title=lambda c: f"{_release_title(c)}-Ordner öffnen"),
    Action("open_releases_dir", "Release-Ordner öffnen", Target.RELEASES, _open_releases_dir,
           availability=_exe_dir_found, order=99),
)


def all_actions(context: ActionContext) -> list[Action]:
    """Aktionen des Kerns und aller für das Projekt aktiven Features."""
    actions = list(CORE_ACTIONS)
    if context.project is not None:
        for manifest in context.services.features.active_features(context.project):
            actions.extend(manifest.actions)
    return actions
