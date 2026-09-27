"""Pull Requests in der Oberfläche (Teilschritt 6a).

PullRequestRunner.open_list: im Hintergrund die offenen Pull Requests holen, dann das Fenster.
PullRequestRunner.create: einen Pull Request aus dem aktuellen Branch erstellen.
1. Ist der Branch main, erklärt das Cockpit, dass es einen anderen Branch braucht.
2. Ist der Branch nicht oder nicht ganz auf GitHub, lädt das Cockpit ihn nach Rückfrage hoch, mit
   der Sicherheitsprüfung wie bei "Änderungen hochladen".
3. Im Hintergrund: Mitarbeiter als mögliche Prüfer und die Branches als mögliche Ziele.
4. Fenster "Pull Request erstellen", dann im Hintergrund erstellen.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from cockpit.core import git, pull_requests, repo_admin, sync
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.core.text import count
from cockpit.platforms.base import (PullRequest, SupportsCollaborators, SupportsPullRequests)
from cockpit.ui import pull_request_dialogs, vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import confirm
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

log = logging.getLogger(__name__)

NO_PULLS = "Die Plattform dieses Projekts kennt keine Pull Requests."


class PullRequestRunner:
    def __init__(self, controller: "ProjectController", project: Project) -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services
        self.project = project
        self.platform_name = self.window.project_list.platform_name
        controller.pull_runner = self            # Qt hält Verbindungen nur schwach

    @property
    def key(self) -> str:
        return f"project:{self.project.id}"

    def _platform(self):
        platform = self.services.platform_for(self.project)
        if platform is None:
            raise CockpitError(repo_admin.NO_ACCOUNT)
        if not isinstance(platform, SupportsPullRequests):
            raise CockpitError(NO_PULLS)
        return platform

    # -- Liste -----------------------------------------------------------------------------
    def open_list(self) -> None:
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        project, services = self.project, self.services
        announce("Pull Requests werden abgefragt.")

        def work(task: Task):
            platform = self._platform()
            ref = repo_admin.repo_ref(project)
            pulls = platform.pull_requests(ref, "open")
            services.pull_request_cache.replace(project.remote, pulls)
            summaries = pull_request_dialogs.load_summaries(platform, ref, pulls)
            return platform, pulls, summaries, sync.environment(services, project)

        self.controller.run_task(self.key, work, self._show_list, "Pull Requests")

    def _show_list(self, outcome) -> None:
        platform, pulls, summaries, env = outcome
        project = self.project
        dialog = pull_request_dialogs.PullRequestsDialog(
            platform, repo_admin.repo_ref(project), project.remote,
            self.services.pull_request_cache, pulls, self.create, self.platform_name,
            self.window, summaries, project, env, getattr(platform, "username", "") or "")
        dialog.exec()
        self.window.refresh_status([project.id])

    # -- Erstellen ---------------------------------------------------------------------------
    def create(self, parent=None, on_created: Callable[[PullRequest], None] | None = None
               ) -> None:
        parent = parent or self.window
        code_dir = self.project.code_dir
        state = git.status(code_dir)
        head, main = state.branch, state.default_branch
        title = "Pull Request erstellen"
        if not head:
            show_error(parent, title, "Es ist gerade kein Branch ausgewählt.")
            return
        if head == main:
            show_error(parent, title,
                       f"Sie sind auf {main}. Ein Pull Request bringt die Änderungen aus einem "
                       f"anderen Branch nach {main}. Wechseln Sie zuerst zu dem Branch mit Ihren "
                       "Änderungen, zum Beispiel in der Übersicht Branches.")
            return
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        missing = pull_requests.upload_needed(code_dir, head)
        if missing != 0:
            what = (f"Der Branch {head} ist noch nicht auf {self.platform_name}." if missing < 0
                    else f"{count(missing, 'Commit', 'Commits')} von {head} "
                         f"{'ist' if missing == 1 else 'sind'} noch nicht auf "
                         f"{self.platform_name}.")
            if not confirm(parent, title, f"{what} Das Cockpit lädt den Branch zuerst hoch, mit "
                           "der Sicherheitsprüfung wie bei „Änderungen hochladen“. Weiter?",
                           yes="Hochladen und weiter", no="Abbrechen"):
                return
            from cockpit.ui.sync_flow import PushRunner
            PushRunner(self.controller, self.project, confirmed=True,
                       then=lambda: self._prepare(head, main, parent, on_created)).start()
            return
        self._prepare(head, main, parent, on_created)

    def _prepare(self, head: str, main: str, parent,
                 on_created: Callable[[PullRequest], None] | None) -> None:
        project, services = self.project, self.services
        code_dir = project.code_dir

        def work(task: Task):
            platform = self._platform()
            ref = repo_admin.repo_ref(project)
            people: list[str] = []
            if isinstance(platform, SupportsCollaborators):
                try:
                    own = (getattr(platform, "username", "") or "").lower()
                    # Den eigenen Pull Request kann man nicht selbst prüfen
                    people = [p.login for p in platform.collaborators(ref)
                              if not p.invited and p.login.lower() != own]
                except CockpitError as exc:
                    log.warning("Mitarbeiter von %s: %s", project.name, exc.message)
            bases = remote_branches(code_dir)
            title, body = pull_requests.suggest(code_dir, head, main)
            return platform, people, bases, title, body

        def done(outcome) -> None:
            platform, people, bases, title, body = outcome
            bases = [b for b in bases if b != head] or [main]
            note = ""
            if sync.changes(code_dir):
                note = ("Sie haben Änderungen ohne Commit. Sie sind nicht im Pull Request. Laden "
                        "Sie sie vorher mit „Änderungen hochladen“ hoch.")
            dialog = pull_request_dialogs.CreatePullRequestDialog(head, bases, main, title, body,
                                                                  people, note, parent)
            if not dialog.exec():
                return
            self._create(platform, dialog, on_created)

        self.controller.run_task(self.key, work, done, "Pull Request erstellen")

    def _create(self, platform, dialog, on_created) -> None:
        project, services = self.project, self.services
        ref = repo_admin.repo_ref(project)
        announce("Pull Request wird erstellt.")

        def work(task: Task) -> PullRequest:
            created = platform.create_pull_request(ref, dialog.head, dialog.base, dialog.title,
                                                   dialog.body, dialog.draft, dialog.reviewers)
            try:
                services.pull_request_cache.replace(project.remote,
                                                    platform.pull_requests(ref, "open"))
            except CockpitError as exc:
                log.warning("Pull Requests von %s: %s", project.name, exc.message)
            return created

        def done(created: PullRequest) -> None:
            self.window.refresh_status([project.id])
            draft = " als Entwurf" if created.draft else ""
            announce(f"Pull Request Nr. {created.number} erstellt{draft}.")
            if on_created is not None:
                on_created(created)

        self.controller.run_task(self.key, work, done, "Pull Request erstellen")


def remote_branches(code_dir) -> list[str]:
    """Branches der Plattform (origin), der Haupt-Branch zuerst."""
    result = git.run(["for-each-ref", "--format=%(refname:strip=3)", "refs/remotes/origin"],
                     code_dir, check=False)
    names = [n for n in result.stdout.splitlines() if n and n != "HEAD"]
    main = git.status(code_dir).default_branch
    return sorted(names, key=lambda n: (n != main, n.lower()))
