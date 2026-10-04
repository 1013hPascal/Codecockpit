"""Lizenz eines Projekts in der Oberfläche (Wunsch des Nutzers vom 03.10.2026).

Auf der Projektzeile steht "Lizenz …", neben "README …". Der Eintrag nennt, welche Lizenz da ist,
zum Beispiel "Lizenz …, MIT" oder "Lizenz …, noch keine Lizenz".
- Ohne Lizenz: "Lizenz auswählen …" (Vorlage von GitHub mit Name und Jahr) und "Lizenz aus Ordner
  hochladen …" (eine fertige Datei).
- Mit Lizenz: "Lizenz ansehen" und "Lizenz ändern …". Ändern bietet dieselben zwei Wege an, die
  bisherige Lizenz kommt vorher in die Sicherheitskopien.
Die Datei heißt LICENSE, liegt im Ordner Code und kommt wie jede Änderung ins Repository.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog

from cockpit.core import git, licenses
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.core.settings import LICENSES
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import choose_from_list, confirm
from cockpit.ui.error_dialog import show_error

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

TITLE = "Lizenz"
CHOOSE = "Lizenz auswählen …"
IMPORT = "Lizenz aus Ordner hochladen …"
SHOW = "Lizenz ansehen"
CHANGE = "Lizenz ändern …"
ACTION_ID = "license"


class LicenseActions:
    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services

    def actions(self) -> list[Action]:
        return [Action(ACTION_ID, "Lizenz …", Target.PROJECT, self.choose,
                       visible=lambda c: c.project is not None and c.project.folder_found,
                       detail=lambda c: licenses.state(c.project.code_dir), order=41)]

    def choose(self, context: ActionContext) -> None:
        project = context.project
        if licenses.find(project.code_dir) is None:
            options = [(CHOOSE, self.from_template), (IMPORT, self.from_file)]
        else:
            options = [(SHOW, self.show), (CHANGE, self.change)]
        chosen = choose_from_list(self.window, TITLE, TITLE, [o[0] for o in options])
        if chosen is not None:
            options[chosen][1](project)

    def change(self, project: Project) -> None:
        options = [(CHOOSE, self.from_template), (IMPORT, self.from_file)]
        chosen = choose_from_list(self.window, CHANGE.rstrip(" …"), TITLE,
                                  [o[0] for o in options])
        if chosen is not None:
            options[chosen][1](project)

    # -- Ansehen ------------------------------------------------------------------------------
    def show(self, project: Project) -> None:
        from cockpit.ui.text_dialog import TextDialog
        path = licenses.find(project.code_dir)
        try:
            lines = [l for l in path.read_text(encoding="utf-8", errors="replace").splitlines()
                     if l.strip()]
        except OSError as exc:
            show_error(self.window, TITLE, "Die Lizenz ließ sich nicht lesen.", str(exc))
            return
        TextDialog(f"Lizenz von {project.name}: {licenses.name(project.code_dir)}", lines,
                   "Lizenz", self.window).exec()

    # -- Vorlage ------------------------------------------------------------------------------
    def from_template(self, project: Project) -> None:
        default = self.services.settings.load().default_license
        current = licenses.name(project.code_dir)
        start = LICENSES.index(current) if current in LICENSES else \
            (LICENSES.index(default) if default in LICENSES else 0)
        chosen = choose_from_list(self.window, CHOOSE.rstrip(" …"), "Lizenzen", list(LICENSES),
                                  start)
        if chosen is None:
            return
        spdx = LICENSES[chosen]
        platform = self._platform(project)
        if platform is None:
            return
        holder = git.identity(project.code_dir)[0] if git.is_repo(project.code_dir) else ""
        holder = holder or project.name
        year = datetime.now().year
        text = (f"Die Lizenz {spdx} wird als LICENSE in den Ordner Code geschrieben, mit dem "
                f"Namen {holder} und dem Jahr {year}.")
        if licenses.find(project.code_dir) is not None:
            text += " Die bisherige Lizenz kommt vorher in die Sicherheitskopien."
        if not confirm(self.window, CHOOSE.rstrip(" …"), text + " Schreiben?", yes="Schreiben",
                       no="Abbrechen"):
            return

        def work(task):
            found = platform.license_text(spdx, holder, year)
            if not found:
                raise CockpitError(f"Die Vorlage für {spdx} war nicht erreichbar.")
            return licenses.write(project.name, project.code_dir, found)

        announce("Die Lizenz wird geholt.")
        self.controller.run_task(f"license:{project.id}", work,
                                 lambda backup: self._done(project, spdx, backup), TITLE)

    def _platform(self, project: Project):
        """Plattform für die Vorlagen: die des Projekts, sonst das erste Konto."""
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return None
        platform = self.services.platform_for(project)
        if platform is None:
            accounts = self.services.platform_accounts()
            platform = self.services.platform(accounts[0].id) if accounts else None
        if platform is None or not hasattr(platform, "license_text"):
            show_error(self.window, TITLE, "Für die Vorlagen braucht das Cockpit ein Konto bei "
                       "GitHub. Sie können die Lizenz auch mit „Lizenz aus Ordner hochladen …“ "
                       "übernehmen.")
            return None
        return platform

    # -- Datei --------------------------------------------------------------------------------
    def from_file(self, project: Project) -> None:
        chosen, _ = QFileDialog.getOpenFileName(self.window, "Lizenz wählen",
                                                str(project.project_dir),
                                                "Alle Dateien (*);;Text (*.txt *.md)")
        if not chosen:
            return
        source = Path(chosen)
        text = f"{source.name} wird als LICENSE in den Ordner Code kopiert."
        if licenses.find(project.code_dir) is not None:
            text += " Die bisherige Lizenz kommt vorher in die Sicherheitskopien."
        if not confirm(self.window, IMPORT.rstrip(" …"), text + " Übernehmen?", yes="Übernehmen",
                       no="Abbrechen"):
            return
        try:
            backup = licenses.write(project.name, project.code_dir, licenses.read_file(source))
        except (CockpitError, OSError) as exc:
            show_error(self.window, TITLE, getattr(exc, "message", "Die Lizenz ließ sich nicht "
                                                   "übernehmen."), str(exc))
            return
        self._done(project, licenses.name(project.code_dir), backup)

    def _done(self, project: Project, shown: str, backup) -> None:
        self.window.refresh_status([project.id])
        self.window.refresh_actions(keep_selection=True)
        announce(f"Lizenz gespeichert: {shown}." + (" Die bisherige steht in den "
                                                    "Sicherheitskopien." if backup else ""))
