"""Ein Ordner pro Branch in der Oberfläche (Phase 10f).

Aktionen:
- Code: "Ordner für Branches einrichten …" (alte Struktur) und "Neuer Branch …" (neue Struktur).
- Branch-Ordner: die Aktionen von Code. "Branch-Ordner entfernen …" gibt es seit dem 03.10.2026
  nicht mehr, "Löschen …" in "Branches verwalten" erledigt das (Wunsch des Nutzers).
- Ein Branch nur auf GitHub steht in der Liste, wenn die Auswahl beim Repository ihn zeigt
  (06.10.2026). "Herunterladen" legt seinen Ordner an, dazu "Auf GitHub öffnen".

Was mit Git oder der Plattform spricht, läuft im Hintergrund. Ein neuer Branch-Ordner bekommt eine
eigene virtuelle Umgebung, wenn der Haupt-Branch eine hat.
"""
from __future__ import annotations

import logging
import webbrowser
from typing import TYPE_CHECKING, Callable

from cockpit.core import branches, git, sync, venv_repair, worktrees
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.core.worktrees import Worktree
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import confirm
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

log = logging.getLogger(__name__)


def main_of(context: ActionContext) -> Project | None:
    """Das Projekt mit dem Ordner des Haupt-Branches, auch von einem Branch-Ordner aus."""
    return context.main_project or context.project


def _repo_with_commits(context: ActionContext) -> bool:
    return (context.status is not None and context.status.repo is not None
            and context.status.repo.is_repo and context.status.repo.has_commits)


class WorktreeActions:
    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services

    @property
    def platform_name(self) -> str:
        return self.window.project_list.platform_name

    def actions(self) -> list[Action]:
        name = self.platform_name
        return [
            # Neuer Branch, übernehmen, umbenennen, Ordner entfernen und löschen stehen seit
            # dem 30.09.2026 in "Branches verwalten" (Wunsch des Nutzers)
            Action("setup_branch_folders", "Ordner für Branches einrichten …", Target.CODE,
                   self.setup, visible=lambda c: c.worktree is None and c.project is not None
                   and _repo_with_commits(c) and worktrees.can_convert(c.project), order=94),
            Action("pin_branch", "Herunterladen", Target.REMOTE_BRANCH, self.pin,
                   is_default=True, order=10),
            Action("open_branch_remote", f"Auf {name} öffnen", Target.REMOTE_BRANCH,
                   self.open_remote, visible=lambda c: c.project is not None
                   and c.project.remote is not None, order=20),
        ]

    def _manage_text(self) -> str:
        """Der Name steht in der Aktion, zum Beispiel "neue-funktion verwalten …"."""
        project_list = self.window.project_list
        if project_list.current_target()[0] is Target.BRANCH and project_list.current_key():
            return f"{project_list.current_key()} verwalten …"
        return "Branch verwalten …"

    # -- Verwalten ----------------------------------------------------------------------------
    def manage(self, context: ActionContext) -> None:
        """Übersicht nur für diesen einen Branch: hochladen steht in der Aktionsliste, hier
        übernehmen, umbenennen, Ordner entfernen und löschen."""
        project, tree = context.main_project, context.worktree
        env = self._environment(project)
        if env is None:
            return
        services = self.services

        def work(task: Task):
            try:
                branches.refresh(project.code_dir, env, task.cancel_event)
            except CockpitError as exc:
                log.warning("Stand für %s: %s", tree.branch, exc.message)
            return [b for b in branches.list_branches(project.code_dir) if b.name == tree.branch]

        def done(items) -> None:
            from cockpit.ui.branch_dialogs import BranchesDialog
            dialog = BranchesDialog(project, items, env, self.platform_name, self.window,
                                    {tree.branch: tree.folder}, single=True)
            dialog.exec()
            if dialog.delete_request:
                self.delete(project, tree, env)
            else:
                self.window.refresh_status([project.id])

        self.controller.run_task(f"project:{project.id}", work, done,
                                 f"{tree.branch} verwalten")

    def delete(self, project: Project, tree: Worktree, env: dict[str, str]) -> None:
        """Branch mit Ordner löschen. Der Ordner kommt in die Sicherheitskopien, wenn darin etwas
        liegt, das es sonst nirgends gibt. Die Commits bleiben unter einem Sicherungsverweis."""
        from cockpit.ui.common import ask_buttons
        name = tree.branch
        remote = git.run(["rev-parse", "-q", "--verify", f"refs/remotes/origin/{name}"],
                         project.code_dir, check=False).returncode == 0
        buttons = ["Nur auf diesem Rechner"] + ([f"Hier und auf {self.platform_name}"]
                                                if remote else []) + ["Abbrechen"]
        # Wunsch des Nutzers (03.10.2026): Löschen verwirft alles, nichts kommt nach main
        text = (f"{name} wird gelöscht, mit dem Ordner "
                f"{project.code_root.name}\\{tree.folder}. Änderungen darin "
                "werden verworfen und kommen nicht nach main. Liegt darin etwas, das noch nicht "
                "hochgeladen ist, kommt der Ordner vorher in die Sicherheitskopien.")
        choice = ask_buttons(self.window, "Branch löschen", text, buttons,
                             default=len(buttons) - 1, escape=len(buttons) - 1)
        if choice == len(buttons) - 1:
            return
        with_remote = remote and choice == 1

        def work(task: Task):
            worktrees.remove(project, tree)
            branches.delete_local(project.code_dir, name)
            if with_remote:
                branches.delete_remote(project.code_dir, name, env)

        def done(_value) -> None:
            self.window.refresh_status([project.id], on_done=lambda: self.window.project_list
                                       .select(Target.CODE, project.id))
            announce(f"{name} gelöscht" + (f", auch auf {self.platform_name}."
                                           if with_remote else "."))

        self.controller.run_task(f"project:{project.id}", work, done, "Branch löschen")

    def rename_main(self, project: Project, old: str, new: str, env: dict[str, str]) -> None:
        """Haupt-Branch umbenennen, im Hintergrund (Wunsch des Nutzers vom 06.10.2026)."""
        from cockpit.core import project_admin
        services = self.services

        def work(task: Task):
            platform = services.platform_for(project) if project.remote is not None else None
            renamed, note = project_admin.rename_main(services.projects, project, old, new,
                                                      platform, env, task.status.emit)
            if renamed.code_dir != project.code_dir and venv_repair.check(
                    renamed.code_dir).broken:
                task.status.emit("Virtuelle Umgebung wird neu angelegt")
                try:
                    venv_repair.repair(renamed.code_dir, project.name, lambda *a: None,
                                       task.cancel_event)
                except CockpitError as exc:
                    log.warning("Virtuelle Umgebung nach dem Umbenennen: %s", exc.message)
            return renamed, note

        def done(outcome) -> None:
            renamed, note = outcome
            self.window.reload_projects(refresh=False)
            self.window.refresh_status([renamed.id], on_done=lambda: self.window.project_list
                                       .select(Target.CODE, renamed.id))
            announce(f"Der Haupt-Branch heißt jetzt {new}. {note}".strip())

        announce("Wird umbenannt.")
        self.controller.run_task(f"project:{project.id}", work, done, "Haupt-Branch umbenennen",
                                 on_status=lambda text: announce(text, speak=False))

    # -- Hilfen -------------------------------------------------------------------------------
    def _environment(self, project: Project) -> dict[str, str] | None:
        """Zugang für Git. None, wenn der Nutzer das Entsperren des Tresors abbricht."""
        if not git.config_get(project.code_dir, "remote.origin.url"):
            return {}
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return None
        try:
            return sync.environment(self.services, project)
        except CockpitError as exc:
            log.warning("Zugang für %s: %s", project.name, exc.message)
            return {}

    def after_created(self, project: Project, tree: Worktree, text: str) -> None:
        """Liste auffrischen, den neuen Ordner markieren, dann im Hintergrund die virtuelle
        Umgebung anlegen, wenn der Haupt-Branch eine hat."""
        window = self.window

        def select() -> None:
            window.project_list.select(Target.BRANCH, project.id, tree.folder)

        window.refresh_status([project.id], on_done=select)
        announce(text)
        if not venv_repair.check(project.code_dir).exists:
            return

        def work(task: Task):
            return venv_repair.create_like(project.code_dir, tree.path, task.cancel_event)

        def done(created: bool) -> None:
            if created:
                announce(f"Virtuelle Umgebung für {tree.folder} angelegt.", speak=False)
                window.refresh_status([project.id])

        self.controller.run_task(f"venv:{tree.path}", work, done, "Virtuelle Umgebung anlegen")

    # -- Einrichten ---------------------------------------------------------------------------
    def setup(self, context: ActionContext) -> None:
        self.convert(context.project)

    def convert(self, project: Project, intro: str = "",
                after: Callable[[Project], None] | None = None) -> bool:
        """Ordner für Branches einrichten, nach Rückfrage. intro steht vor der Erklärung, after
        bekommt danach das umgestellte Projekt (Projekt vom Rechner hinzufügen, 04.10.2026).
        False, wenn der Nutzer abbricht."""
        state = git.status(project.code_dir)
        folder = worktrees.folder_name(state.branch or state.default_branch)
        text = intro + (f"Der Inhalt des Ordners {project.code_root.name} "
                f"wandert nach {project.code_root.name}\\{folder}. Danach bekommt jeder "
                "Branch einen eigenen Ordner neben diesem. Ihre Dateien und Änderungen bleiben "
                "erhalten. Vorher kommt eine Sicherheitskopie in den Ordner backups.")
        if venv_repair.check(project.code_dir).exists:
            text += (" Die virtuelle Umgebung enthält feste Pfade. Sie wird danach neu "
                     "angelegt, das dauert etwas.")
        text += (" Schließen Sie vorher alle Programme, die den Ordner geöffnet haben, zum "
                 "Beispiel den Explorer, ein Terminal oder Claude. Einrichten?")
        if not confirm(self.window, "Ordner für Branches einrichten", text, yes="Einrichten",
                       no="Abbrechen"):
            return False
        services = self.services

        def work(task: Task):
            target = worktrees.convert(project, task.status.emit)
            moved = services.projects.set_code_dir(project, target)
            if venv_repair.check(target).broken:
                task.status.emit("Virtuelle Umgebung wird neu angelegt")
                try:
                    venv_repair.repair(target, project.name, lambda *a: None, task.cancel_event)
                except CockpitError as exc:
                    log.warning("Virtuelle Umgebung nach dem Einrichten: %s", exc.message)
            return moved

        def done(moved: Project) -> None:
            self.window.reload_projects(refresh=False)
            self.window.refresh_status([moved.id], on_done=lambda: self.window.project_list
                                       .select(Target.CODE, moved.id))
            announce(f"Ordner für Branches eingerichtet. Der Code liegt jetzt in "
                     f"{moved.code_root.name}\\{moved.code_dir.name}.")
            if after is not None:
                after(moved)

        announce("Ordner für Branches werden eingerichtet.")
        self.controller.run_task(f"project:{project.id}", work, done,
                                 "Ordner für Branches einrichten", on_status=announce)
        return True

    # -- Neuer Branch -------------------------------------------------------------------------
    def new_branch(self, context: ActionContext) -> None:
        from cockpit.ui.branch_dialogs import BranchNameDialog
        project = main_of(context)
        main = context.status.repo.default_branch if context.status else "main"
        dialog = BranchNameDialog("Neuer Branch", f"Er bekommt einen eigenen Ordner im Ordner "
                                  f"Code und beginnt beim neuesten Stand von {main} auf "
                                  f"{self.platform_name}.", project.code_dir, parent=self.window)
        if not dialog.exec():
            return
        self.create(project, dialog.name)

    def create(self, project: Project, name: str) -> None:
        env = self._environment(project)
        if env is None:
            return

        def work(task: Task):
            return worktrees.create(project, name, env, task.cancel_event)

        announce(f"Branch {name} wird angelegt.")
        self.controller.run_task(
            f"project:{project.id}", work,
            lambda tree: self.after_created(project, tree, f"Branch {name} angelegt, im Ordner "
                                            f"{project.code_root.name}\\{tree.folder}."), "Neuer Branch")

    # -- Branches nur auf der Plattform -------------------------------------------------------
    def pin(self, context: ActionContext) -> None:
        project, branch = context.project, context.remote_branch
        if branch is None:
            return
        env = self._environment(project)
        if env is None:
            return

        def work(task: Task):
            return worktrees.open_branch(project, branch.name, env, task.cancel_event)

        def done(tree: Worktree) -> None:
            listing = self.window.project_list
            if listing.show_of(project.id) not in ("local", "all"):
                listing.set_show(project.id, "all")      # der neue Ordner soll zu sehen sein
            self.after_created(project, tree, f"{branch.name} heruntergeladen, im Ordner "
                                              f"{project.code_root.name}\\{tree.folder}.")

        announce(f"{branch.name} wird heruntergeladen.")
        self.controller.run_task(f"project:{project.id}", work, done, "Herunterladen")

    def open_folder_for(self, project: Project, name: str) -> None:
        """Aus der Übersicht Branches: Ordner für einen vorhandenen Branch anlegen."""
        env = self._environment(project)
        if env is None:
            return

        def work(task: Task):
            return worktrees.open_branch(project, name, env, task.cancel_event)

        self.controller.run_task(
            f"project:{project.id}", work,
            lambda tree: self.after_created(project, tree, f"Ordner für {name} angelegt: "
                                            f"{project.code_root.name}\\{tree.folder}."), "Branch-Ordner anlegen")

    def open_remote(self, context: ActionContext) -> None:
        remote, branch = context.project.remote, context.remote_branch
        if remote is None or branch is None:
            return
        webbrowser.open(f"https://{remote.host}/{remote.owner}/{remote.name}/tree/{branch.name}")
        announce(f"{branch.name} wird im Browser geöffnet.")
