"""Aktionen des Kerns für die Aktionsliste.

Phase 2 enthält nur Aktionen, die schon funktionieren. Die übrigen Grundfunktionen (Hochladen,
Verlauf, Repository verwalten ...) kommen in Phase 5 dazu.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.availability import Availability

PHASE_5 = "Diese Funktion kommt in Phase 5."


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
    if context.project.newest_exe() is None:
        return Availability.no("Im Ordner Exe liegt keine Exe.")
    return Availability.yes()


# -- Ausführen ------------------------------------------------------------------------------
def _open_project_dir(context: ActionContext) -> None:
    open_path(context.project.project_dir)
    context.announce("Projektordner wird geöffnet.")


def _open_code_dir(context: ActionContext) -> None:
    open_path(context.project.code_dir)
    context.announce("Code-Ordner wird geöffnet.")


def _open_exe_dir(context: ActionContext) -> None:
    open_path(context.project.exe_dir)
    context.announce("Exe-Ordner wird geöffnet.")


def _run_exe(context: ActionContext) -> None:
    exe = context.project.newest_exe()
    start_program(exe)
    context.announce(f"{exe.name} wird gestartet.")


def _not_yet(context: ActionContext) -> None:
    context.announce(PHASE_5)


CORE_ACTIONS: tuple[Action, ...] = (
    Action("new_project", "Neues Projekt hochladen", Target.NEW_PROJECT, _not_yet,
           availability=lambda c: Availability.no(PHASE_5), is_default=True, order=10),
    Action("open_project_dir", "Projektordner öffnen", Target.PROJECT, _open_project_dir,
           availability=_project_found, order=80),
    Action("open_code_dir", "Code-Ordner öffnen", Target.CODE, _open_code_dir,
           availability=_project_found, order=90),
    Action("run_exe", "Exe starten", Target.EXE, _run_exe, availability=_exe_found,
           is_default=True, order=10),
    Action("open_exe_dir", "Exe-Ordner öffnen", Target.EXE, _open_exe_dir,
           availability=_exe_dir_found, order=90),
)


def all_actions(context: ActionContext) -> list[Action]:
    """Aktionen des Kerns und aller für das Projekt aktiven Features."""
    actions = list(CORE_ACTIONS)
    if context.project is not None:
        for manifest in context.services.features.active_features(context.project):
            actions.extend(manifest.actions)
    return actions
