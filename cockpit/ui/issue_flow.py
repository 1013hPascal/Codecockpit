"""Issues in der Oberfläche (21.10.2026): im Hintergrund die offenen Issues, die Labels und die
Personen holen, dann das Fenster. Ein Branch für ein Issue entsteht wie "Neuer Branch": mit
Branch-Ordnern in einem eigenen Ordner, sonst wechselt das Cockpit hin.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cockpit.core import branches, repo_admin
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.platforms.base import SupportsIssues
from cockpit.ui import issue_dialogs, vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

log = logging.getLogger(__name__)

NO_ISSUES = "Die Plattform dieses Projekts kennt keine Issues."


class IssueRunner:
    def __init__(self, controller: "ProjectController", project: Project) -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services
        self.project = project
        self.select = 0
        controller.issue_runner = self              # Qt hält Verbindungen nur schwach

    def _platform(self):
        platform = self.services.platform_for(self.project)
        if platform is None:
            raise CockpitError(repo_admin.NO_ACCOUNT)
        if not isinstance(platform, SupportsIssues):
            raise CockpitError(NO_ISSUES)
        return platform

    def open_list(self, select: int = 0) -> None:
        """select: Nummer des Issues, das markiert sein soll (aus den Neuigkeiten)."""
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        project = self.project
        self.select = select
        announce("Issues werden abgefragt.")

        def work(task: Task):
            platform = self._platform()
            ref = repo_admin.repo_ref(project)
            found = platform.issues(ref, "open")
            labels: list[str] = []
            people: list[str] = []
            try:
                labels = platform.issue_labels(ref)
                people = platform.assignable(ref)
            except CockpitError as exc:          # ohne Labels und Personen geht es trotzdem
                log.warning("Labels oder Personen von %s: %s", project.name, exc.message)
            return platform, ref, found, labels, people

        self.controller.run_task(f"project:{project.id}", work, self._show, "Issues")

    def _show(self, outcome) -> None:
        from cockpit.ui import ai_suggest
        platform, ref, found, labels, people = outcome
        services, project = self.services, self.project

        def ai_source(load):
            return ai_suggest.for_issue(services, project, load)

        dialog = issue_dialogs.IssuesDialog(platform, ref, found, labels, people, self.window,
                                            ai_source, self.create_branch, project.code_dir)
        if self.select:
            dialog.fill(self.select)
        dialog.exec()
        self.window.refresh_status([project.id])

    def create_branch(self, name: str) -> None:
        main = self.services.projects.get(self.project.id) or self.project
        if main.has_branch_folders:
            self.controller.worktrees.create(main, name)
            return
        try:
            branches.create(main.code_dir, name)
        except CockpitError as exc:
            show_error(self.window, "Branch für das Issue", exc.message, exc.details)
            return
        self.window.refresh_status([main.id])
        announce(f"Branch {name} angelegt. Sie sind jetzt auf {name}.")
