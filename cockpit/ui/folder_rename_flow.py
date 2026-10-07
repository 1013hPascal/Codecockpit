"""Ordner Code und Exe in Repository und Release umbenennen (Antwort des Nutzers vom 06.10.2026).

Beim Start fragt das Cockpit einmal für alle Projekte mit den alten Namen. "Später" fragt beim
nächsten Start wieder, "Nicht umbenennen" nie mehr. Ohne Sicherheitskopie, weil sich nur die Namen
ändern (Antwort des Nutzers). Dafür gibt es auf der Projektzeile "Ordnernamen zurücksetzen …".
Einzelne Projekte lassen sich dort auch später umbenennen.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cockpit.core import project_admin
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import ask_buttons, confirm, show_info
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

log = logging.getLogger(__name__)

SKIP_KEY = "projects.folder_rename_skip"     # Projekte, bei denen nicht mehr gefragt wird
DONE_KEY = "projects.folder_renamed"         # vom Cockpit umbenannt, zum Zurücksetzen
RENAME, LATER, NEVER = "Umbenennen", "Später", "Nicht umbenennen"
CLOSE_PROGRAMS = (" Schließen Sie vorher alle Programme, die die Ordner geöffnet haben, zum "
                  "Beispiel den Explorer, ein Terminal oder Claude.")
VENV_NOTE = " Virtuelle Umgebungen enthalten feste Pfade und werden danach neu angelegt."


class FolderRenamer:
    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services

    # -- Gemerkte Projekte ---------------------------------------------------------------------
    def _ids(self, key: str) -> set[int]:
        return set(self.services.database.get_value(key, []) or [])

    def _remember(self, key: str, ids: set[int]) -> None:
        self.services.database.set_value(key, sorted(ids))

    def candidates(self) -> list[Project]:
        """Projekte mit den alten Namen, ohne die abgelehnten und ohne das laufende Cockpit."""
        skip = self._ids(SKIP_KEY)
        return [p for p in self.services.projects.all()
                if p.id not in skip and project_admin.folder_plan(p)
                and not project_admin.contains_program(p)]

    # -- Beim Start ----------------------------------------------------------------------------
    def offer(self) -> None:
        projects = self.candidates()
        if not projects:
            return
        names = ", ".join(p.name for p in projects)
        text = ("Die Ordner Code und Exe heißen jetzt Repository und Release. Das Cockpit benennt "
                f"sie bei {count(len(projects), 'Projekt', 'Projekten')} um: {names}. Nur die "
                "Namen ändern sich, der Inhalt bleibt. Auf der Projektzeile können Sie es mit "
                "„Ordnernamen zurücksetzen …“ rückgängig machen." + VENV_NOTE + CLOSE_PROGRAMS)
        choice = ask_buttons(self.window, "Ordner umbenennen", text, [RENAME, LATER, NEVER],
                             default=1, escape=1)
        if choice == 2:
            self._remember(SKIP_KEY, self._ids(SKIP_KEY) | {p.id for p in projects})
            announce("Die Ordner bleiben, wie sie sind.")
            return
        if choice == 0:
            self.run(projects)

    def run(self, projects: list[Project], back: bool = False) -> None:
        store = self.services.projects
        title = "Ordnernamen zurücksetzen" if back else "Ordner umbenennen"

        def work(task: Task):
            from cockpit.ui.project_manage import _repair_venvs
            changed, failed = [], []
            for project in projects:
                task.status.emit(f"{project.name}: Ordner werden umbenannt")
                try:
                    renamed = project_admin.rename_folders(store, project, back)
                except CockpitError as exc:
                    log.warning("Ordner von %s nicht umbenannt: %s", project.name, exc.details)
                    failed.append(project.name)
                    continue
                changed.append(renamed)
            for renamed in changed:
                _repair_venvs(renamed, task)
            return changed, failed

        def done(outcome) -> None:
            changed, failed = outcome
            ids = {p.id for p in changed}
            if back:
                self._remember(DONE_KEY, self._ids(DONE_KEY) - ids)
                self._remember(SKIP_KEY, self._ids(SKIP_KEY) | ids)
            else:
                self._remember(DONE_KEY, self._ids(DONE_KEY) | ids)
                self._remember(SKIP_KEY, self._ids(SKIP_KEY) - ids)
            self.window.reload_projects(refresh=False)
            self.window.refresh_status([p.id for p in changed])
            verb = "zurückgesetzt" if back else "umbenannt"
            text = f"Ordner bei {count(len(changed), 'Projekt', 'Projekten')} {verb}."
            if failed:
                text += (f" Nicht geklappt bei {', '.join(failed)}. Die Ordner sind noch "
                         "geöffnet. Es wurde dort nichts geändert.")
                show_info(self.window, title, text + CLOSE_PROGRAMS.replace(" vorher", ""))
            announce(text)

        announce(f"{title}.")
        self.controller.run_task("folder_rename", work, done, title, on_status=announce)

    # -- Auf der Projektzeile ------------------------------------------------------------------
    def actions(self) -> list[Action]:
        return [
            Action("rename_folders", "Ordner in Repository und Release umbenennen …",
                   Target.PROJECT, lambda c: self.one(c, back=False),
                   visible=lambda c: c.project is not None
                   and bool(project_admin.folder_plan(c.project)), order=97),
            Action("rename_folders_back", "Ordnernamen zurücksetzen …", Target.PROJECT,
                   lambda c: self.one(c, back=True),
                   visible=lambda c: c.project is not None
                   and c.project.id in self._ids(DONE_KEY)
                   and bool(project_admin.folder_plan(c.project, back=True)), order=97),
        ]

    def one(self, context: ActionContext, back: bool) -> None:
        project = context.project
        if project_admin.contains_program(project):
            show_info(self.window, "Ordner umbenennen", "Das Cockpit läuft gerade aus diesem "
                      "Projekt. Seine Ordner lassen sich deshalb nicht umbenennen.")
            return
        names = " und ".join(f"{s.name} in {t.name}"
                             for s, t in project_admin.folder_plan(project, back))
        if not confirm(self.window, "Ordner umbenennen", f"Bei {project.name} wird {names} "
                       "umbenannt. Nur die Namen ändern sich, der Inhalt bleibt." + VENV_NOTE
                       + CLOSE_PROGRAMS + " Umbenennen?", yes="Umbenennen", no="Abbrechen"):
            return
        self.run([project], back)
