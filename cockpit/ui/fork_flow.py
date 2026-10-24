"""Forks in der Oberfläche (Wunsch des Nutzers vom 21.10.2026, siehe core/forks.py).

download_or_fork: Beim Herunterladen über eine Adresse fragt das Cockpit, ob das Konto dort
hochladen darf. Wenn nicht, bietet es einen Fork an.
update_from_original: "Vom Original holen …" beim Haupt-Branch eines Forks.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from cockpit.core import forks, project_setup, sync
from cockpit.core.errors import CockpitError
from cockpit.core.remote_repos import StoredRepo
from cockpit.core.text import count
from cockpit.platforms.base import RepoRef, SupportsForks
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import ask_buttons, confirm
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

FORK, ONLY_DOWNLOAD, CANCEL = 0, 1, 2


def download_or_fork(controller: "ProjectController", repo: StoredRepo) -> None:
    services = controller.services
    if repo.account_id is None or not vault_ui.ensure_unlocked(services, controller.window):
        controller.download(repo)
        return
    platform = services.platform(repo.account_id)
    if not isinstance(platform, SupportsForks):
        controller.download(repo)
        return

    def work(task: Task) -> bool:
        try:
            return platform.can_push(RepoRef(repo.owner, repo.name))
        except CockpitError:
            return True                       # unbekannt: wie bisher einfach herunterladen

    def done(can_push: bool) -> None:
        if can_push:
            controller.download(repo)
            return
        choice = ask_buttons(
            controller.window, "Herunterladen",
            f"In {repo.owner}/{repo.name} dürfen Sie nicht direkt hochladen. Mit einem Fork "
            "bekommen Sie eine eigene Kopie in Ihrem Konto. Dort laden Sie Ihre Änderungen hoch "
            "und stellen dem Original einen Pull Request. Das Cockpit legt den Fork an und lädt "
            "ihn herunter.",
            ["Fork anlegen und herunterladen", "Nur herunterladen", "Abbrechen"],
            default=CANCEL, escape=CANCEL)
        if choice == FORK:
            download_fork(controller, repo)
        elif choice == ONLY_DOWNLOAD:
            controller.download(repo)

    controller.run_task(f"remote-check:{repo.owner}/{repo.name}".lower(), work, done,
                        "Herunterladen")


def download_fork(controller: "ProjectController", repo: StoredRepo) -> None:
    services, window = controller.services, controller.window
    root = Path(services.settings.load().projects_root)
    announce(f"Fork von {repo.name} wird angelegt und heruntergeladen.")

    def work(task: Task):
        return project_setup.download_fork(services, repo, root, task.cancel_event)

    def done(project) -> None:
        controller.ensure_identity(project)
        window.reload_projects(refresh=False)
        window.show_project(project.id)
        window.refresh_status([project.id])
        announce(f"Fork {project.name} heruntergeladen. Das Original ist {repo.owner}/"
                 f"{repo.name}.")

    controller.run_task(f"clone:{repo.owner}/{repo.name}".lower(), work, done, "Fork anlegen",
                        transfer=True)


def update_from_original(controller: "ProjectController", project) -> None:
    """Neues aus dem Original holen und den Haupt-Branch vorwärts nachziehen."""
    services, window = controller.services, controller.window
    original = forks.upstream(project.code_dir)
    if original is None:
        return
    if not vault_ui.ensure_unlocked(services, window):
        return
    code_dir = project.code_dir
    announce("Original wird abgefragt.")

    def work(task: Task):
        forks.fetch(code_dir, sync.environment(services, project), task.cancel_event)
        return forks.behind(code_dir)

    def done(numbers) -> None:
        new, _own = numbers
        name = f"{original.owner}/{original.name}"
        if not new:
            announce(f"Ihr Fork ist auf dem Stand von {name}.")
            return
        main = forks.main_branch(code_dir)
        if not confirm(window, "Vom Original holen",
                       f"{name} hat {count(new, 'neuen Commit', 'neue Commits')}. Das Cockpit "
                       f"zieht {main} hier nach. Ihre Branches bleiben, wie sie sind. Danach "
                       f"laden Sie {main} wie gewohnt hoch, dann ist auch Ihr Fork auf dem "
                       "Stand. Nachziehen?", yes="Nachziehen", no="Abbrechen"):
            return
        try:
            forks.update_main(code_dir)
        except CockpitError as exc:
            show_error(window, "Vom Original holen", exc.message, exc.details)
            return
        window.refresh_status([project.id])
        announce(f"{count(new, 'Commit', 'Commits')} vom Original geholt. Laden Sie {main} "
                 "jetzt hoch.")

    controller.run_task(f"project:{project.id}", work, done, "Vom Original holen",
                        transfer=True)
