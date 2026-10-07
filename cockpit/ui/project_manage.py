"""Projekt verwalten (Wunsch des Nutzers vom 06.10.2026).

Das Fenster zeigt oben den derzeitigen Namen. Mit Tab: "Projekt umbenennen …", "Aus der Liste
entfernen …" und "Projekt löschen …". Beim Löschen steht schon im Knopf, was gelöscht wird: der
lokale Ordner auf dem Rechner, das Repository und das Release.

Umbenennen ändert den Namen in der Liste, den Ordner und das Repository auf der Plattform. Löschen
fragt zweimal, zuletzt muss der Name eingetippt werden. Der Ordner kommt vorher in die
Sicherheitskopien. Was mit Git oder der Plattform spricht, läuft im Hintergrund.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLineEdit, QPushButton, QVBoxLayout, QWidget

from cockpit.core import project_admin, repo_admin, venv_repair
from cockpit.core.actions import ActionContext
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, ask_buttons, confirm, label_for, show_info
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

log = logging.getLogger(__name__)

RENAME, REMOVE, DELETE = "rename", "remove", "delete"


def deleted_parts(project: Project) -> list[str]:
    """Was "Projekt löschen" löscht, für den Knopf und die Rückfrage."""
    parts = ["lokaler Ordner auf dem Rechner"]
    if project.remote is not None:
        parts.append("Repository")
    if project.has_exe_dir or project.remote is not None:
        parts.append("Release")
    return parts


def delete_text(project: Project) -> str:
    """Zum Beispiel "Projekt löschen …, lokaler Ordner auf dem Rechner, Repository und Release
    werden gelöscht"."""
    parts = deleted_parts(project)
    joined = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " und " + parts[-1]
    verb = "wird" if len(parts) == 1 else "werden"
    return f"Projekt &löschen …, {joined} {verb} gelöscht"


class ProjectManageDialog(FocusDialog):
    """Nach dem Schließen steht in choice, was der Nutzer gewählt hat, sonst None."""

    def __init__(self, project: Project, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.choice: str | None = None
        self.setWindowTitle(f"Projekt verwalten: {project.name}")
        self.name_edit = QLineEdit(project.name)
        self.name_edit.setReadOnly(True)
        label = label_for(self.name_edit, "Derzeitiger &Name:")
        self.rename_button = QPushButton("Projekt &umbenennen …")
        self.remove_button = QPushButton("Aus der &Liste entfernen …")
        self.delete_button = QPushButton(delete_text(project))
        close = QPushButton("Schließen")
        for button, choice in ((self.rename_button, RENAME), (self.remove_button, REMOVE),
                               (self.delete_button, DELETE)):
            button.setAutoDefault(False)
            button.clicked.connect(lambda _checked=False, c=choice: self.pick(c))
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.name_edit)
        for widget in (self.rename_button, self.remove_button, self.delete_button, close):
            layout.addWidget(widget)
        self.initial_focus_widget = self.name_edit

    def pick(self, choice: str) -> None:
        self.choice = choice
        self.accept()


class ProjectManager:
    """Abläufe hinter "Projekt verwalten …"."""

    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services

    @property
    def platform_name(self) -> str:
        return self.window.project_list.platform_name

    def manage(self, context: ActionContext) -> None:
        project = context.project
        dialog = ProjectManageDialog(project, self.window)
        dialog.exec()
        if dialog.choice == RENAME:
            self.rename(project)
        elif dialog.choice == REMOVE:
            self.controller.remove_action(context)
        elif dialog.choice == DELETE:
            self.delete(project)

    # -- Umbenennen ------------------------------------------------------------------------
    def ask_name(self, project: Project) -> str | None:
        from cockpit.ui.collections_flow import NameDialog
        store = self.services.projects
        name = project.name
        while True:
            dialog = NameDialog("Projekt umbenennen", name, self.window)
            if not dialog.exec():
                return None
            name = dialog.name.strip()
            problem = project_admin.name_problem(store, project, name)
            if not problem:
                return name
            show_info(self.window, "Projekt umbenennen", problem)

    def rename(self, project: Project) -> None:
        name = self.ask_name(project)
        if name is None:
            return
        platform_name = self.platform_name
        parts = ["den Namen in der Liste"]
        if not project.linked and project.folder_found:
            parts.append(f"den Ordner {project.project_dir} in {project.project_dir.parent / name}")
        if project.remote is not None:
            parts.append(f"das Repository {project.remote.owner}/{project.remote.name} auf "
                         f"{platform_name} in {project.remote.owner}/{name}. {platform_name} "
                         "leitet die alte Adresse weiter")
        text = (f"Das Cockpit ändert {', '.join(parts[:-1])} und {parts[-1]}." if len(parts) > 1
                else f"Das Cockpit ändert {parts[0]}.")
        text += (" Schließen Sie vorher alle Programme, die den Ordner geöffnet haben, zum Beispiel "
                 "den Explorer, ein Terminal oder Claude. Umbenennen?")
        if not confirm(self.window, "Projekt umbenennen", text, yes="Umbenennen", no="Abbrechen"):
            return
        if project.remote is not None and not vault_ui.ensure_unlocked(self.services,
                                                                       self.window):
            return
        services = self.services
        store = services.projects

        def work(task: Task):
            renamed = project_admin.rename_local(store, project, name, task.status.emit)
            note = ""
            if project.remote is not None:
                platform = services.platform_for(project)
                if platform is None:
                    note = (f"Das Repository auf {platform_name} heißt weiter "
                            f"{project.remote.name}. Es gibt kein Konto dafür im Cockpit.")
                else:
                    task.status.emit("Repository wird umbenannt")
                    try:
                        address = project_admin.rename_remote(platform, renamed, name)
                        store.set_remote(renamed, address, renamed.last_updated)
                        services.remote_repos.forget(project.remote)
                    except CockpitError as exc:
                        note = (f"Das Repository auf {platform_name} wurde nicht umbenannt. "
                                f"{exc.message}")
            _repair_venvs(store.get(renamed.id) or renamed, task)
            return store.get(renamed.id) or renamed, note

        def done(outcome) -> None:
            renamed, note = outcome
            self.window.reload_projects(refresh=False)
            self.window.show_project(renamed.id)
            self.window.refresh_status([renamed.id])
            if note:
                show_info(self.window, "Projekt umbenennen", f"{renamed.name} ist umbenannt. "
                          f"{note}")
            else:
                announce(f"Umbenannt in {renamed.name}.")

        announce("Wird umbenannt.")
        self.controller.run_task(f"project:{project.id}", work, done, "Projekt umbenennen",
                                 on_status=lambda text: announce(text, speak=False))

    # -- Löschen ---------------------------------------------------------------------------
    def delete(self, project: Project) -> None:
        from cockpit.ui.repo_dialogs import TypeNameDialog
        platform_name = self.platform_name
        folders = (f"die Ordner {project.code_dir} und {project.exe_dir}" if project.linked
                   and project.exe_dir is not None else
                   f"der Ordner {project.code_dir if project.linked else project.project_dir}")
        text = f"{project.name} wird gelöscht: {folders} auf dem Rechner"
        if project.remote is not None:
            text += (f" und das Repository {project.remote.owner}/{project.remote.name} auf "
                     f"{platform_name} mit Verlauf, Issues und allen Releases")
        text += (". Der Ordner kommt vorher in die Sicherheitskopien und bleibt dort 30 Tage.")
        if project.remote is not None:
            text += f" Auf {platform_name} lässt sich das Löschen nicht rückgängig machen."
        choice = ask_buttons(self.window, "Projekt löschen", text,
                             ["Weiter zum Löschen …", "Abbrechen"], default=1, escape=1)
        if choice != 0:
            return
        if not TypeNameDialog(project.name, self.window).exec():
            return
        if project.remote is None:
            self.delete_local(project)
            return
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        platform = self.services.platform_for(project)
        if platform is None:
            show_info(self.window, "Projekt löschen", f"{repo_admin.NO_ACCOUNT} Es wurde nichts "
                      "gelöscht.")
            return
        from cockpit.ui.repo_dialogs import RepoDeleter, _Worker
        self._worker = _Worker(self.window, "Projekt löschen")
        RepoDeleter(self.window, self._worker, platform, repo_admin.repo_ref(project),
                    platform_name, True, lambda: self.delete_local(project)).delete_now()

    def delete_local(self, project: Project) -> None:
        services = self.services
        if project.remote is not None:
            services.remote_repos.forget(project.remote)

        def done(_kept) -> None:
            self.window.reload_projects(refresh=False)
            announce(f"{project.name} ist gelöscht.")

        self.controller.run_task(f"project:{project.id}",
                                 lambda task: project_admin.delete_local(services.projects,
                                                                         project),
                                 done, "Projekt löschen")


def _repair_venvs(project: Project, task: Task) -> None:
    """Virtuelle Umgebungen enthalten feste Pfade. Nach dem Umbenennen neu anlegen."""
    from cockpit.core import worktrees
    folders = [project.code_dir] + [t.path for t in worktrees.list_worktrees(project)]
    for folder in folders:
        if not venv_repair.check(folder).broken:
            continue
        task.status.emit("Virtuelle Umgebung wird neu angelegt")
        try:
            venv_repair.repair(folder, project.name, lambda *a: None, task.cancel_event)
        except CockpitError as exc:
            log.warning("Virtuelle Umgebung nach dem Umbenennen: %s", exc.message)
