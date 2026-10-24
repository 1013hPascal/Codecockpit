"""Projekt verwalten: neu einlesen, Filter, Features, Links, entfernen, neuer Ort, Umgebung.

Teil von ProjectController (project_actions.py).
"""
from __future__ import annotations

import logging
from pathlib import Path

from cockpit.core import list_filter, repo_admin, venv_repair
from cockpit.core.actions import ActionContext
from cockpit.core.availability import Availability
from cockpit.core.errors import CockpitError
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import confirm, pick_folder
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

log = logging.getLogger(__name__)


class ManageActions:
    """Aktionen auf der Zeile Projekt."""

    # -- Projekt neu einlesen ----------------------------------------------------------------
    def reread_action(self, context: ActionContext) -> None:
        """Stand dieses einen Projekts neu abfragen (Wunsch aus dem Test von 5c). Im Menü Datei
        steht weiter "Projekte neu einlesen" für alle."""
        name, project_id = context.project.name, context.project.id
        if not self.check_layout(context.project, lambda project: None):
            return
        self.check_repo(context.project, ask=True)
        self.window.reload_projects(refresh=False)
        self.window.refresh_status([project_id],
                                   on_done=lambda: announce(f"{name} neu eingelesen."))

    def list_filter_action(self, context: ActionContext) -> None:
        """Auswahl "Anzeigen:" über den Projekten. Pfeil hoch und runter, Enter wählt, Escape
        lässt alles, wie es ist (Wunsch des Nutzers vom 07.10.2026)."""
        from cockpit.ui import project_list as listing
        project_list = self.window.project_list
        names = list_filter.names(project_list.platform_name)
        kind = listing.pick_filter(project_list, names, project_list.filter_kind)
        project_list.setFocus()
        if kind is not None:
            project_list.set_filter(kind, speak=True)

    # -- Features dieses Projekts (Konzept 8.4, Phase 7) ----------------------------------------
    def _features_availability(self, context: ActionContext) -> Availability:
        if not self.services.features.visible_features():
            return Availability.no("Es ist kein Feature eingeschaltet. Das geht im Menü Features.")
        return Availability.yes()

    def project_features_action(self, context: ActionContext) -> None:
        from cockpit.ui.features_dialogs import ProjectFeaturesDialog
        dialog = ProjectFeaturesDialog(self.services, context.project, self.window)
        dialog.exec()
        if dialog.changed:
            self.window.refresh_actions(keep_selection=True)
            self.window.refresh_status([context.project.id])

    # -- Links, Repository verwalten, Aus der Liste entfernen (Konzept 9.5) --------------------
    def _account_availability(self, context: ActionContext) -> Availability:
        if context.project is None or repo_admin.account_for(self.services,
                                                             context.project) is None:
            return Availability.no(repo_admin.NO_ACCOUNT)
        return Availability.yes()

    def links_action(self, context: ActionContext) -> None:
        from cockpit.ui.repo_dialogs import LinksDialog
        project = context.project
        try:
            links = repo_admin.links(self.services, project)
        except CockpitError as exc:
            show_error(self.window, "Links", exc.message, exc.details)
            return
        if not self.services.vault.is_unlocked():
            LinksDialog(project.name, links, self.window).exec()
            return
        services = self.services

        def work(task: Task):
            """Wunsch des Nutzers (30.09.2026): auch das neueste Release, wenn es eins gibt.
            Klappt die Abfrage nicht, kommen die Links ohne Release."""
            from cockpit.platforms.base import SupportsReleases
            try:
                platform = services.platform_for(project)
                if isinstance(platform, SupportsReleases):
                    releases = platform.releases(repo_admin.repo_ref(project))
                    if releases:
                        return [(f"Neuestes Release {releases[0].tag}", releases[0].url)]
            except CockpitError as exc:
                log.info("Releases von %s nicht abgefragt: %s", project.name, exc.message)
            return []

        self.run_task(f"project:{project.id}", work,
                      lambda extra: LinksDialog(project.name, links + extra, self.window).exec(),
                      "Links")

    def manage_action(self, context: ActionContext) -> None:
        project = context.project
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services, window = self.services, self.window
        platform_name = window.project_list.platform_name
        announce("Repository wird abgefragt.")

        def work(task: Task):
            from cockpit.platforms.base import NotFound
            platform = services.platform_for(project)
            if platform is None:
                raise CockpitError(repo_admin.NO_ACCOUNT)
            try:
                return platform, platform.repo_info(repo_admin.repo_ref(project))
            except NotFound:
                return None                      # das Repository fehlt auf der Plattform

        def done(outcome) -> None:
            from cockpit.ui.repo_dialogs import ManageRepoDialog
            if outcome is None:
                self.missing_repos.add(project.id)
                self.window.refresh_actions(keep_selection=True)
                self.offer_create(project)
                return
            self.missing_repos.discard(project.id)
            platform, info = outcome
            dialog = ManageRepoDialog(services, project, platform, info, platform_name, window)
            dialog.exec()
            if dialog.deleted:
                window.reload_projects(refresh=False)
                if not dialog.removed:
                    window.show_project(project.id)
                    window.refresh_status([project.id])
            elif dialog.changed:
                window.refresh_status([project.id])

        self.run_task(f"project:{project.id}", work, done, "Repository verwalten")

    def remove_action(self, context: ActionContext) -> None:
        project = context.project
        where = f" und das Repository auf {self.window.project_list.platform_name}" if (
            project.remote is not None) else ""
        text = (f"{project.name} wird nur aus der Liste des Cockpits entfernt. Der Ordner "
                f"{project.project_dir}{where} bleiben unverändert. Mit „Projekt vom Rechner "
                "hinzufügen“ kommt es jederzeit zurück. Entfernen?")
        if not confirm(self.window, "Aus der Liste entfernen", text, yes="Entfernen",
                       no="Abbrechen"):
            return
        self.services.projects.remove(project.id)
        if project.remote is not None:
            self.services.remote_repos.hide(project.remote)   # nicht als "nur auf GitHub"
        self.window.reload_projects(refresh=False)
        announce(f"{project.name} aus der Liste entfernt.")

    # -- Neuen Ort angeben -----------------------------------------------------------------
    def relocate_action(self, context: ActionContext) -> None:
        project = context.project
        start = str(project.project_dir.parent)
        what = "den Code-Ordner" if project.linked else "den Projektordner"
        folder = pick_folder(self.window, f"Neuer Ort von {project.name}: {what} wählen", start)
        if folder is None:
            return
        try:
            moved = self.services.projects.relocate(project, folder)
        except CockpitError as exc:
            show_error(self.window, "Neuen Ort angeben", exc.message, exc.details)
            return
        self.window.reload_projects(refresh=False)
        self.window.show_project(moved.id)
        self.window.refresh_status([moved.id])
        announce(f"Neuer Ort für {moved.name} gespeichert.")

    # -- Virtuelle Umgebung -------------------------------------------------------------------
    def repair_venv_action(self, context: ActionContext) -> None:
        project = context.project
        state = venv_repair.check(project.code_dir)
        names = venv_repair.steps(project.code_dir)
        packages = (" Danach installiert es die Pakete aus requirements.txt. Das kann einige "
                    "Minuten dauern." if len(names) == 3 else "")
        text = (f"Die virtuelle Umgebung von {project.name} funktioniert nicht mehr. "
                f"{state.reason} Das Cockpit verschiebt sie als Sicherheitskopie in den Ordner "
                f"backups im Datenordner und legt sie neu an.{packages} Neu anlegen?")
        if not confirm(self.window, "Virtuelle Umgebung", text, yes="Neu anlegen",
                       no="Abbrechen"):
            return
        window = self.window

        def work(task: Task) -> Path:
            def progress(step: int, total: int, name: str) -> None:
                task.status.emit(f"Schritt {step} von {total}: {name} …")
            return venv_repair.repair(project.code_dir, project.name, progress,
                                      task.cancel_event)

        def done(_backup: Path) -> None:
            window.refresh_status([project.id])
            announce(f"Virtuelle Umgebung von {project.name} neu angelegt.")

        self.run_task(f"project:{project.id}", work, done, "Virtuelle Umgebung",
                      on_status=announce)
