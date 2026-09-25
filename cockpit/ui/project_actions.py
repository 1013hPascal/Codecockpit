"""Aktionen rund um Projekte, die Dialoge oder Hintergrund-Arbeit brauchen (Phase 5a).

Der Kern (cockpit.core) kennt kein Qt. Deshalb stehen Aktionen mit Rückfragen, Ordnerwahl und
Hintergrund-Aufgaben hier in der Oberfläche. Sie kommen auf demselben Weg in die Aktionsliste wie
die Aktionen des Kerns und der Features.

- Vorhandenes Projekt hinzufügen (Menü Datei): Projektordner, Umstellen oder Nur verknüpfen.
- Neuen Ort angeben (Projekt, nur wenn der Ordner fehlt).
- Mit vorhandenem Repository verbinden (Code, nur wenn der Git-Ordner fehlt).
- Virtuelle Umgebung neu anlegen (Code, nur wenn sie nach dem Verschieben kaputt ist).
- Herunterladen und Auf GitHub öffnen (Repository, das nur auf der Plattform liegt).

Alles, was Dateien verändert, beschreibt vorher, was passiert, und braucht eine Bestätigung.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from cockpit.core import core_actions, git, identity, project_setup, venv_repair
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.availability import Availability
from cockpit.core.errors import CockpitError
from cockpit.core.projects import CODE_DIR, Project, classify_folder, same_drive
from cockpit.core.remote_repos import StoredRepo
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import ask_buttons, choose_from_list, confirm, pick_folder
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

log = logging.getLogger(__name__)

ENTER_ADDRESS = "Adresse eingeben …"


class ProjectController:
    """Führt die Projekt-Aktionen für das Hauptfenster aus."""

    def __init__(self, window: "MainWindow") -> None:
        self.window = window
        self.services = window.services
        self.busy: set[str] = set()               # laufende Vorgänge, zum Beispiel "clone:3"
        self.tasks: list[Task] = []

    # -- Aktionen für die Aktionsliste -----------------------------------------------------
    def actions(self) -> list[Action]:
        return [
            Action("relocate", "Neuen Ort angeben …", Target.PROJECT, self.relocate_action,
                   visible=lambda c: c.project is not None and not c.project.folder_found,
                   order=5),
            Action("connect_repo", "Mit vorhandenem Repository verbinden …", Target.CODE,
                   self.connect_action, visible=_git_missing, order=40),
            Action("repair_venv", "Virtuelle Umgebung neu anlegen …", Target.CODE,
                   self.repair_venv_action, visible=_venv_broken, order=45),
            Action("download", "Herunterladen", Target.REMOTE_REPO, self.download_action,
                   availability=self._download_availability, is_default=True, order=10),
            Action("open_remote", f"Auf {self.window.project_list.platform_name} öffnen",
                   Target.REMOTE_REPO, self.open_remote_action, order=20),
        ]

    # -- Hintergrund ------------------------------------------------------------------------
    def run_task(self, key: str, work: Callable[[Task], object],
                 done: Callable[[object], None], failed_title: str,
                 on_status: Callable[[str], None] | None = None) -> None:
        """work läuft im Hintergrund. done und Fehlermeldungen kommen im Thread der Oberfläche."""
        if key in self.busy:
            announce("Das läuft schon.")
            return
        self.busy.add(key)
        task = Task(work, self.window)

        def finish() -> None:
            self.busy.discard(key)
            if task in self.tasks:
                self.tasks.remove(task)
            task.deleteLater()

        def failed(message: str, details: str) -> None:
            announce(message, urgent=True)
            show_error(self.window, failed_title, message, details)

        task.result.connect(done)
        task.error.connect(failed)
        if on_status is not None:
            task.status.connect(on_status)
        task.cancelled.connect(lambda: announce("Abgebrochen."))
        task.finished.connect(finish)
        self.tasks.append(task)
        task.start()

    def wait(self) -> None:
        """Beim Schließen: laufende Aufgaben abbrechen und auf sie warten."""
        for task in list(self.tasks):
            task.cancel()
            task.wait(5000)

    # -- Vorhandenes Projekt hinzufügen ------------------------------------------------------
    def add_existing(self) -> None:
        root = self.services.settings.load().projects_root
        folder = pick_folder(self.window, "Vorhandenes Projekt hinzufügen", root)
        if folder is None:
            return
        kind, project_dir = classify_folder(folder)
        if kind == "project":
            existing = self.services.projects.find_by_dir(project_dir)
            if existing is not None:
                self.window.show_project(existing.id)
                announce(f"{existing.name} ist schon in der Liste.")
                return
            self._added(self.services.projects.add(project_dir))
            return
        self._add_other(folder, Path(root))

    def _add_other(self, folder: Path, root: Path) -> None:
        text = (f"Der Ordner {folder.name} hat keinen Unterordner Code. Das Cockpit erwartet "
                f"den Aufbau Projektordner mit Unterordner Code. "
                f"Umstellen: Das Cockpit legt den Projektordner {root / folder.name} an und "
                f"verschiebt den gewählten Ordner dorthin als Code. "
                f"Nur verknüpfen: Die Ordner bleiben, wo sie sind. Das ist gedacht für "
                f"Repositories, deren Aufbau Sie nicht ändern dürfen.")
        choice = ask_buttons(self.window, "Vorhandenes Projekt hinzufügen", text,
                             ["Umstellen …", "Nur verknüpfen …", "Abbrechen"], default=2, escape=2)
        if choice == 0:
            self._convert(folder, root)
        elif choice == 1:
            self._link(folder)

    def _convert(self, folder: Path, root: Path) -> None:
        target = root / folder.name
        if same_drive(folder, root):
            how = (f"Der Ordner {folder} wird nach {target / CODE_DIR} verschoben. Sein Inhalt "
                   "bleibt unverändert, nur der Ort ändert sich.")
        else:
            how = (f"Der Ordner liegt auf einem anderen Laufwerk. Deshalb wird er nach "
                   f"{target / CODE_DIR} kopiert. Der alte Ordner {folder} bleibt unverändert, "
                   "Sie können ihn später selbst löschen.")
        if not confirm(self.window, "Umstellen", f"{how} Umstellen?", yes="Umstellen",
                       no="Abbrechen"):
            return
        try:
            project, moved = self.services.projects.convert(folder, root)
        except CockpitError as exc:
            show_error(self.window, "Umstellen", exc.message, exc.details)
            return
        self._added(project)

    def _link(self, folder: Path) -> None:
        exe_dir = None
        if confirm(self.window, "Nur verknüpfen", f"Der Code-Ordner ist {folder}. Gibt es "
                   "zu diesem Projekt auch einen Exe-Ordner?", yes="Exe-Ordner wählen …",
                   no="Ohne Exe-Ordner"):
            exe_dir = pick_folder(self.window, "Exe-Ordner wählen", str(folder.parent))
        try:
            project = self.services.projects.add_linked(folder, exe_dir)
        except CockpitError as exc:
            show_error(self.window, "Nur verknüpfen", exc.message, exc.details)
            return
        self._added(project)

    def _added(self, project: Project) -> None:
        self.ensure_identity(project)
        self.window.reload_projects(refresh=False)
        self.window.show_project(project.id)
        self.window.refresh_status([project.id])
        announce(f"{project.name} hinzugefügt.")

    def ensure_identity(self, project: Project) -> None:
        settings = self.services.settings.load()
        try:
            identity.ensure(project.code_dir, project.name, settings.git_name,
                            settings.git_email, self.window.asker)
        except CockpitError as exc:
            log.warning("Git-Identität für %s: %s %s", project.name, exc.message, exc.details)

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

    # -- Herunterladen -----------------------------------------------------------------------
    def _download_availability(self, context: ActionContext) -> Availability:
        repo = context.remote_repo
        if repo is None:
            return Availability.no("Das Repository ist nicht mehr in der Liste.")
        if git.find_git() is None:
            return Availability.no("Git ist nicht installiert.")
        return Availability.yes()

    def download_action(self, context: ActionContext) -> None:
        self.download(context.remote_repo)

    def download(self, repo: StoredRepo, speak: bool = True) -> None:
        root = Path(self.services.settings.load().projects_root)
        target = project_setup.download_target(root, repo.name) / CODE_DIR
        if target.exists() and any(target.iterdir()):
            show_error(self.window, "Herunterladen", f"Den Ordner {target} gibt es schon, und er "
                       "ist nicht leer. Nichts wurde verändert.")
            return
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services = self.services
        if speak:
            announce(f"{repo.name} wird heruntergeladen.")

        def work(task: Task) -> Project:
            return project_setup.download(services, repo, root, task.cancel_event)

        def done(project: Project) -> None:
            self.ensure_identity(project)
            self.window.reload_projects(refresh=False)
            if speak:
                self.window.show_project(project.id)
            self.window.refresh_status([project.id])
            announce(f"{project.name} heruntergeladen.")

        self.run_task(f"clone:{repo.owner}/{repo.name}".lower(), work, done, "Herunterladen")

    def open_remote_action(self, context: ActionContext) -> None:
        core_actions.open_path(context.remote_repo.web_url)
        announce("Wird im Browser geöffnet.")

    # -- Mit vorhandenem Repository verbinden -------------------------------------------------
    def connect_action(self, context: ActionContext) -> None:
        project = context.project
        repos = self.services.remote_repos.all()
        items = [f"{r.name}, {r.owner}" for r in repos] + [ENTER_ADDRESS]
        current = next((i for i, r in enumerate(repos) if r.name.lower() ==
                        project.name.lower()), 0)
        index = choose_from_list(self.window, f"{project.name} verbinden", "Repositories",
                                 items, current)
        if index is None:
            return
        if index < len(repos):
            repo = repos[index]
            url, account_id, label = repo.clone_url, repo.account_id, f"{repo.owner}/{repo.name}"
        else:
            from PySide6.QtWidgets import QInputDialog
            url, ok = QInputDialog.getText(self.window, f"{project.name} verbinden",
                                           "Adresse des Repositories:")
            address = git.parse_remote(url) if ok else None
            if address is None:
                if ok:
                    show_error(self.window, "Verbinden", "Die Adresse wurde nicht erkannt. "
                               "Beispiel: https://github.com/Name/Projekt")
                return
            account = self.services.account_for_host(address.host)
            account_id = account.id if account else None
            label = f"{address.owner}/{address.name}"
        text = (f"{project.name} wird mit dem Repository {label} verbunden. Die Dateien im "
                "Ordner bleiben unverändert. Unterschiede zur Plattform erscheinen danach als "
                "Änderungen, die noch nicht hochgeladen sind. Verbinden?")
        if not confirm(self.window, "Verbinden", text, yes="Verbinden", no="Abbrechen"):
            return
        if account_id is not None and not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services = self.services
        announce(f"{project.name} wird verbunden.")

        def work(task: Task) -> str:
            return project_setup.connect(services, project, url, account_id, task.cancel_event)

        def done(branch: str) -> None:
            self.ensure_identity(project)
            self.window.reload_projects(refresh=False)
            self.window.refresh_status([project.id])
            announce(f"{project.name} ist verbunden, Branch {branch}.")

        self.run_task(f"project:{project.id}", work, done, "Verbinden")

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


def _git_missing(context: ActionContext) -> bool:
    status = context.status
    return (context.project is not None and context.project.folder_found
            and status is not None and status.repo is not None and not status.repo.is_repo)


def _venv_broken(context: ActionContext) -> bool:
    return context.status is not None and context.status.venv.broken
