"""Git-Aktionen auf Main-Branch und Branch: hochladen, holen, Verlauf, Branches, Beiseitelegen.

Teil von ProjectController (project_actions.py).
"""
from __future__ import annotations

import logging
from pathlib import Path

from cockpit.core import git, history, identity, repo_admin
from cockpit.core.actions import ActionContext
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.core.text import count
from cockpit.ui import vault_ui
from cockpit.ui.action_conditions import _git_availability, _has_commits, _pulls_text
from cockpit.ui.announcer import announce
from cockpit.ui.common import confirm, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

log = logging.getLogger(__name__)


MANAGE_BRANCHES, MANAGE_BRANCHES_TEXT = "manage", "Branches verwalten …"


def refresh_pulls_for(services, project) -> None:
    """Offene Pull Requests eines Projekts auffrischen, wenn die Plattform das kann. Im
    Hintergrund aufrufen. Klappt es nicht, bleibt der letzte bekannte Stand."""
    from cockpit.platforms.base import SupportsPullRequests
    if project.remote is None:
        return
    try:
        platform = services.platform_for(project)
        if isinstance(platform, SupportsPullRequests):
            services.pull_request_cache.replace(
                project.remote, platform.pull_requests(repo_admin.repo_ref(project), "open"))
    except CockpitError as exc:
        log.warning("Pull Requests von %s: %s", project.name, exc.message)


class GitActions:
    """Aktionen für den Code eines Projekts."""

    def ensure_identity(self, project: Project) -> None:
        settings = self.services.settings.load()
        try:
            identity.ensure(project.code_dir, project.name, settings.git_name,
                            settings.git_email, self.window.asker)
        except CockpitError as exc:
            log.warning("Git-Identität für %s: %s %s", project.name, exc.message, exc.details)

    def identity_action(self, context: ActionContext) -> None:
        """Git-Identität des Projekts anzeigen und bei Bedarf die aus den Grundeinstellungen
        übernehmen (Wunsch aus dem Test von Phase 5a)."""
        project = context.project
        settings = self.services.settings.load()
        name, email = settings.git_name, settings.git_email
        title = f"Git-Identität von {project.name}"
        current = identity.state(project.code_dir, name, email)
        own = ", ".join(v for v in git.identity(project.code_dir) if v)
        if current is identity.IdentityState.NOT_SET:
            text = f"Eingetragen: {own}." if own else "Im Projekt ist keine eingetragen."
            show_info(self.window, title, f"{text} In den Grundeinstellungen fehlen Name oder "
                      "E-Mail-Adresse. Sie stehen im Menü Einstellungen unter "
                      "Grundeinstellungen.")
            return
        if current is identity.IdentityState.SAME:
            show_info(self.window, title, f"{own}. Das ist die Identität aus den "
                      "Grundeinstellungen.")
            return
        if current is identity.IdentityState.MISSING:
            text = (f"{project.name} hat noch keine eigene Git-Identität. In den "
                    f"Grundeinstellungen steht: {name}, {email}. Übernehmen?")
        else:
            text = (f"Eingetragen: {own}. In den Grundeinstellungen steht: {name}, {email}. "
                    "Soll das Projekt die Identität aus den Grundeinstellungen bekommen?")
        if confirm(self.window, title, text, yes="Grundeinstellungen übernehmen",
                   no="Vorhandene behalten"):
            git.set_identity(project.code_dir, name, email)
            announce(f"Git-Identität von {project.name}: {name}, {email}.")

    def upload_action(self, context: ActionContext) -> None:
        from cockpit.ui.upload_flow import UploadRunner
        UploadRunner(self, context.project).start()

    # -- Änderungen hochladen und holen (Konzept 9.2 und 9.3) ---------------------------------
    def push_action(self, context: ActionContext) -> None:
        from cockpit.ui.sync_flow import PushRunner
        PushRunner(self, context.project).start()

    def pull_action(self, context: ActionContext) -> None:
        from cockpit.ui.sync_flow import PullRunner
        PullRunner(self, context.project).start()

    def issues_action(self, context: ActionContext) -> None:
        from cockpit.ui.issue_flow import IssueRunner
        IssueRunner(self, context.project).open_list()

    def update_from_original_action(self, context: ActionContext) -> None:
        from cockpit.ui import fork_flow
        fork_flow.update_from_original(self, context.project)

    def resolve_action(self, context: ActionContext) -> None:
        from cockpit.core import sync
        from cockpit.ui.sync_flow import PullRunner
        kind = sync.conflict_kind(context.project.code_dir)
        if kind is sync.ConflictKind.NONE:
            self.window.refresh_status([context.project.id])
            announce("Es gibt keine Konflikte mehr.")
            return
        PullRunner(self, context.project).resolve(kind)

    # -- Verlauf und Rückgängig machen (Konzept 9.4 und 9.7) -------------------------------
    def history_action(self, context: ActionContext) -> None:
        project = context.project
        services, window = self.services, self.window

        def work(task: Task) -> list:
            return history.log_commits(project.code_dir)

        def done(commits: list) -> None:
            from cockpit.ui.history_dialogs import HistoryDialog
            dialog = HistoryDialog(services, project, commits, window)
            dialog.exec()
            if dialog.changed:
                window.refresh_status([project.id])

        self.run_task(f"project:{project.id}", work, done, "Verlauf")

    def upload_history_action(self, context: ActionContext) -> None:
        project = context.project
        services, window = self.services, self.window
        project_id = (context.main_project or project).id
        branch = git.status(project.code_dir).branch

        def work(task: Task) -> list:
            return history.upload_history(services.database, project_id, project.code_dir,
                                          branch)

        def done(uploads: list) -> None:
            from cockpit.ui.history_dialogs import UploadHistoryDialog
            dialog = UploadHistoryDialog(services, project, branch, uploads, window)
            dialog.exec()
            if dialog.changed:
                window.refresh_status([project_id])

        self.run_task(f"project:{project_id}", work, done, "Hochladeverlauf")

    def discard_action(self, context: ActionContext) -> None:
        from cockpit.ui.history_dialogs import DiscardDialog
        project = context.project
        title = "Änderungen verwerfen"
        try:
            changes = history.local_changes(project.code_dir)
        except CockpitError as exc:
            show_error(self.window, title, exc.message, exc.details)
            return
        if not changes:
            self.window.refresh_status([project.id])
            announce("Es gibt keine Änderungen ohne Commit.")
            return
        dialog = DiscardDialog(project.name, changes, self.window)
        if not dialog.exec():
            return
        try:
            history.discard(project.code_dir, project.name, dialog.chosen)
        except CockpitError as exc:
            show_error(self.window, title, exc.message, exc.details)
            self.window.refresh_status([project.id])
            return
        self.window.refresh_status([project.id])
        announce(f"{count(len(dialog.chosen), 'Änderung', 'Änderungen')} verworfen.")

    # -- Branches und beiseitegelegte Änderungen (Konzept 10.14) ----------------------------
    def branches_action(self, context: ActionContext) -> None:
        from cockpit.core import branches, sync, worktrees
        # Mit Branch-Ordnern arbeitet die Übersicht immer im Ordner des Haupt-Branches (10f)
        project = context.main_project or context.project
        on_platform = bool(git.config_get(project.code_dir, "remote.origin.url"))
        needs_account = project.account_id is not None or (
            project.remote is not None
            and self.services.account_for_host(project.remote.host) is not None)
        if on_platform and needs_account and not vault_ui.ensure_unlocked(self.services,
                                                                          self.window):
            return
        services, window = self.services, self.window
        platform_name = window.project_list.platform_name

        def work(task: Task):
            env = sync.environment(services, project) if on_platform else {}
            note = ""
            try:
                branches.refresh(project.code_dir, env, task.cancel_event)
            except CockpitError as exc:
                log.warning("Branches von %s nicht abgefragt: %s", project.name, exc.message)
                note = f"Stand von {platform_name} nicht abgefragt. {exc.message}"
            items = branches.list_branches(project.code_dir)
            refresh_pulls_for(services, project)
            for item in items:
                item.open_pulls = services.pull_request_cache.count_for_branch(project.remote,
                                                                               item.name)
            folders = {t.branch: t.folder for t in worktrees.list_worktrees(project)}
            return env, items, note, folders

        def done(outcome) -> None:
            from cockpit.ui.branch_dialogs import BranchesDialog
            env, items, note, folders = outcome
            if note:
                announce(note)
            dialog = BranchesDialog(project, items, env, platform_name, window, folders)
            dialog.exec()
            window.refresh_status([project.id])
            if dialog.new_request:
                self.worktrees.create(project, dialog.new_request)
            elif dialog.open_request:
                self.worktrees.open_folder_for(project, dialog.open_request)
            elif getattr(dialog, "rename_main_request", ""):
                self.worktrees.rename_main(project, dialog.main, dialog.rename_main_request, env)
            elif getattr(dialog, "delete_request", ""):
                tree = next((t for t in worktrees.list_worktrees(project)
                             if t.branch == dialog.delete_request), None)
                if tree is not None:
                    self.worktrees.delete(project, tree, env)

        self.run_task(f"project:{project.id}", work, done, "Branches")

    def _all_pulls_detail(self, context: ActionContext) -> str:
        """Beim Haupt-Branch zählen alle offenen Pull Requests des Repositories, aus dem
        Zwischenspeicher, ohne Netz."""
        if context.project is None or context.project.remote is None:
            return ""
        return _pulls_text(len(self.services.pull_request_cache.open_pulls(
            context.project.remote)))

    # -- Pull Requests (Konzept 10.14, Phase 6) ---------------------------------------------
    def pull_requests_action(self, context: ActionContext) -> None:
        from cockpit.ui.pull_request_flow import PullRequestRunner
        PullRequestRunner(self, context.project).open_list()

    def create_pull_action(self, context: ActionContext) -> None:
        from cockpit.ui.pull_request_flow import PullRequestRunner
        PullRequestRunner(self, context.project).create()

    # -- Terminal (Konzept 9.9, Phase 8a) --------------------------------------------------
    def terminal_action(self, context: ActionContext, folder: Path, where: str) -> None:
        """Terminal im Ordner der Zeile (Wunsch des Nutzers vom 06.10.2026): Projekt im
        Projektordner, Repository im Ordner des Repositorys, Branch im Ordner des Branches."""
        from cockpit.ui.terminal_dialog import open_terminal
        project = context.main_project or context.project
        title = f"{project.name}, {where}" if where else project.name
        open_terminal(self.services, self.window, folder, title, project)
        self.window.refresh_status([project.id])

    # -- Repository (06.10.2026) ---------------------------------------------------------------
    def _branch_show_detail(self, context: ActionContext) -> str:
        from cockpit.ui.project_list import main_name, show_names
        project_list = self.window.project_list
        names = show_names(main_name(context.project, context.status), project_list.platform_name)
        return names[project_list.show_of(context.project.id)]

    def branch_show_action(self, context: ActionContext) -> None:
        """Auswahl, welche Branches unter dem Repository stehen. Pfeil hoch und runter, Enter
        wählt, Escape lässt alles, wie es ist."""
        from cockpit.ui import project_list as listing
        project_list = self.window.project_list
        project = context.project
        names = listing.show_names(listing.main_name(project, context.status),
                                   project_list.platform_name)
        # Aufräumrunde vom 20.10.2026: "Branches verwalten …" steht hier mit drin
        extra = {}
        if _has_commits(context) and _git_availability(context).available:
            extra[MANAGE_BRANCHES] = MANAGE_BRANCHES_TEXT
        show = listing.pick_show(project_list, names, project_list.show_of(project.id),
                                 extra=extra)
        project_list.setFocus()
        if show == MANAGE_BRANCHES:
            self.branches_action(context)
            return
        if show is None:
            return
        project_list.set_show(project.id, show)
        status = context.status
        shown = 0
        if status is not None:
            if show in ("local", "all"):
                shown += len(status.worktrees)
            if show in ("remote", "all"):
                shown += len(status.remote_branches)
        announce(f"{names[show]}: {count(shown, 'weiterer Branch', 'weitere Branches')}"
                 if show != "main" else names[show])

    def stash_push_action(self, context: ActionContext) -> None:
        from cockpit.core import branches, sync
        project = context.project
        title = "Änderungen beiseitelegen"
        try:
            changes = sync.changes(project.code_dir)
        except CockpitError as exc:
            show_error(self.window, title, exc.message, exc.details)
            return
        if not changes:
            announce("Es gibt keine Änderungen ohne Commit.")
            return
        text = (f"Alle Änderungen ohne Commit werden beiseitegelegt: {changes.summary()}. Die "
                "Dateien kommen danach auf den Stand des letzten Commits. Mit „Beiseitegelegte "
                "Änderungen“ holen Sie sie zurück. Vorher kommen die Dateien auch als "
                "Sicherheitskopie in den Ordner backups. Beiseitelegen?")
        if not confirm(self.window, title, text, yes="Beiseitelegen", no="Abbrechen"):
            return
        try:
            branches.stash_push(project.code_dir, project.name)
        except CockpitError as exc:
            show_error(self.window, title, exc.message, exc.details)
            return
        self.window.refresh_status([project.id])
        announce("Änderungen beiseitegelegt.")

    def stashes_action(self, context: ActionContext) -> None:
        from cockpit.ui.branch_dialogs import StashDialog
        project = context.project
        dialog = StashDialog(project, self.window)
        dialog.exec()
        if dialog.changed:
            self.window.refresh_status([project.id])
