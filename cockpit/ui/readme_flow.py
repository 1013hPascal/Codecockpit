"""README-Pflege in der Oberfläche (Konzept 10.2, Phase 9).

Aktion auf der Projektzeile: "README …" mit Auswahl. Wunsch des Nutzers vom 03.10.2026:
- Ohne README: "README-Einstellungen …", "README aus Ordner hochladen …" (eine fertige Datei
  übernehmen) und "README mit KI schreiben …".
- Mit README: "README-Einstellungen …" und "README bearbeiten …".
Beim Schreiben und Bearbeiten steht die ganze README in einem Textfeld. Darunter kommen Wünsche an
die KI, ein Knopf schickt sie ab, "fertig so" speichert. Danach übersetzt die KI in die weiteren
Sprachen, jede Übersetzung kommt einzeln zum Lesen.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFileDialog

from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.features.readme import document as doc
from cockpit.features.readme import plan
from cockpit.ui.announcer import announce
from cockpit.ui.common import confirm
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task
# Aufgeteilt am 22.10.2026: Teile stehen in readme_dialogs.py. Die Namen bleiben hier erreichbar.
from cockpit.ui.readme_dialogs import (  # noqa: F401
    EditDialog, LanguagesDialog, SKIP, TAKE, TranslationDialog, WriteDialog, review)

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

SETTINGS = "README-Einstellungen …"
IMPORT = "README aus Ordner hochladen …"
WRITE = "README mit KI schreiben …"
EDIT = "README bearbeiten …"


class ReadmeActions:
    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services

    def _active(self, context: ActionContext) -> bool:
        project = context.project
        if project is None or not project.folder_found or plan.FEATURE_ID not in \
                self.services.registry:
            return False
        try:
            return self.services.features.active(plan.FEATURE_ID, project)
        except CockpitError:
            return False

    @staticmethod
    def _has_readme(context: ActionContext) -> bool:
        return (context.project.code_dir / plan.MAIN_FILE).is_file()

    def actions(self) -> list[Action]:
        # Auf der Projektzeile (Wunsch des Nutzers zu Phase 9): die README gehört zum Projekt
        return [
            # Ein Eintrag mit Auswahl (Wunsch des Nutzers, 30.09.2026)
            Action("readme", "README …", Target.REPOSITORY, self.choose,
                   visible=self._active, order=40),
        ]

    def choose(self, context: ActionContext) -> None:
        """Reihenfolge wie im Wunsch des Nutzers vom 03.10.2026."""
        from cockpit.ui.common import choose_from_list
        if self._has_readme(context):
            options = [(SETTINGS, self.languages), (EDIT, self.edit)]
        else:
            options = [(SETTINGS, self.languages), (IMPORT, self.import_file),
                       (WRITE, self.write)]
        chosen = choose_from_list(self.window, "README", "README", [o[0] for o in options])
        if chosen is not None:
            options[chosen][1](context)

    # -- Einstellungen ----------------------------------------------------------------------
    def languages(self, context: ActionContext) -> None:
        dialog = LanguagesDialog(self.services, context.project, self.window)
        if not dialog.exec():
            return
        try:
            doc.save(context.project.code_dir, dialog.values())
        except OSError as exc:
            show_error(self.window, "README-Sprachen", "Die Sprachen ließen sich nicht in "
                       "cockpit.toml speichern.", str(exc))
            return
        announce("README-Sprachen gespeichert.")

    # -- Aus Ordner hochladen ---------------------------------------------------------------
    def import_file(self, context: ActionContext) -> None:
        project = context.project
        chosen, _ = QFileDialog.getOpenFileName(
            self.window, "README wählen", str(project.project_dir),
            "Markdown und Text (*.md *.markdown *.txt);;Alle Dateien (*)")
        if not chosen:
            return
        source = Path(chosen)
        if not confirm(self.window, "README aus Ordner hochladen",
                       f"{source.name} wird als README.md in den Ordner Repository kopiert. "
                       "Übernehmen?", yes="Übernehmen", no="Abbrechen"):
            return
        try:
            backup = plan.import_file(self.services, project, source)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "README aus Ordner hochladen",
                       getattr(exc, "message", "Die README ließ sich nicht übernehmen."),
                       str(exc))
            return
        self.window.refresh_status([project.id])
        announce("README.md übernommen." + (" Die alte steht in den Sicherheitskopien."
                                            if backup else ""))

    # -- Mit KI schreiben und bearbeiten ----------------------------------------------------
    def write(self, context: ActionContext) -> None:
        dialog = WriteDialog(self.services, context.project, self.window)
        if dialog.exec():
            self._save(context.project, dialog.readme_text, dialog.ai)

    def edit(self, context: ActionContext) -> None:
        project = context.project
        try:
            dialog = EditDialog(self.services, project, self.window)
        except (OSError, UnicodeDecodeError) as exc:
            show_error(self.window, "README bearbeiten", "Die README ließ sich nicht lesen.",
                       str(exc))
            return
        if not dialog.exec():
            return
        if dialog.changed():
            self._save(project, dialog.readme_text, dialog.ai)
            return
        missing = plan.missing_translations(self.services, project)
        if missing:
            self._translate(project, dialog.readme_text, dialog.ai, missing)
        else:
            announce("Nichts geändert.")

    def _save(self, project: Project, text: str, ai) -> None:
        try:
            backup = plan.save_files(self.services, project, {plan.MAIN_FILE: text})
        except (CockpitError, OSError) as exc:
            show_error(self.window, "README", "Die README ließ sich nicht speichern.", str(exc))
            return
        self.window.refresh_status([project.id])
        announce("README.md gespeichert." + (" Die alte steht in den Sicherheitskopien."
                                             if backup else ""))
        _main, codes = plan.languages(self.services, project.code_dir)
        if len(codes) > 1:
            self._translate(project, text, ai, None)

    def _translate(self, project: Project, text: str, ai, only: list[str] | None) -> None:
        if ai is None:
            from cockpit.ui import ai_ui
            tool = self.services.features.setting(plan.FEATURE_ID, "tool") or None
            ai = ai_ui.prepare(self.services, self.window, plan.FEATURE_ID, "die README", tool)
            if isinstance(ai, str):
                if ai != ai_ui.DECLINED:
                    show_error(self.window, "README übersetzen", f"{ai} Die Übersetzungen "
                               "bleiben, wie sie sind.")
                return
        services = self.services

        def work(task: Task):
            return plan.translate(services, project, ai, text, only, task.cancel_event,
                                  task.status.emit)

        self.controller.run_task(
            f"readme:{project.id}", work,
            lambda translations: self._save_translations(project, translations),
            "README übersetzen", on_status=lambda message: announce(message, speak=False))
        announce("Die KI übersetzt die README.")

    def _save_translations(self, project: Project,
                           translations: list[tuple[str, str, str]]) -> None:
        taken = review(translations, self.window) if translations else {}
        if not taken:
            announce("Keine Übersetzung übernommen.")
            return
        try:
            plan.save_files(self.services, project, taken)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "README übersetzen", "Die Übersetzung ließ sich nicht "
                       "speichern.", str(exc))
            return
        self.window.refresh_status([project.id])
        announce(f"Übersetzung gespeichert: {', '.join(sorted(taken))}.")
