"""Aktionen rund um Projekte, die Dialoge oder Hintergrund-Arbeit brauchen (Phase 5a).

Der Kern (cockpit.core) kennt kein Qt. Deshalb stehen Aktionen mit Rückfragen, Ordnerwahl und
Hintergrund-Aufgaben hier in der Oberfläche. Sie kommen auf demselben Weg in die Aktionsliste wie
die Aktionen des Kerns und der Features.

- Projekt vom Rechner hinzufügen: Projektordner, in den Hauptordner verschieben oder am Ort
  lassen. Danach auf Wunsch gleich auf GitHub hochladen.
- Projekt von GitHub herunterladen: eigene Repositories, die der Organisationen oder eine Adresse.
- Neuen Ort angeben (Projekt, nur wenn der Ordner fehlt).
- Mit vorhandenem Repository verbinden (Code, nur wenn der Git-Ordner fehlt).
- Virtuelle Umgebung neu anlegen (Code, nur wenn sie nach dem Verschieben kaputt ist).
- Herunterladen und Auf GitHub öffnen (Repository, das nur auf der Plattform liegt).
- Änderungen hochladen, Änderungen holen und Konflikte lösen (Code, ab Phase 5c, sync_flow.py).
- Verlauf und Änderungen verwerfen (Code, ab Phase 5d, history_dialogs.py).

Alles, was Dateien verändert, beschreibt vorher, was passiert, und braucht eine Bestätigung.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from cockpit.core import core_actions, git, history, identity, project_setup, venv_repair
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.availability import Availability
from cockpit.core.errors import CockpitError
from cockpit.core.projects import CODE_DIR, Project, classify_folder, same_drive
from cockpit.core.remote_repos import StoredRepo
from cockpit.core.text import count
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import (ask_buttons, choose_from_list, confirm, pick_folder,
                               show_info)
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
        self.upload = None                        # laufendes Hochladen (UploadRunner)

    # -- Aktionen für die Aktionsliste -----------------------------------------------------
    def actions(self) -> list[Action]:
        platform_name = self.window.project_list.platform_name
        reread = [Action(f"reread_{target.value}", "Projekt neu einlesen", target,
                         self.reread_action, visible=lambda c: c.project is not None, order=1)
                  for target in (Target.PROJECT, Target.CODE, Target.EXE)]
        return reread + [
            Action("add_local", "Projekt vom Rechner hinzufügen …", Target.ADD_LOCAL,
                   lambda c: self.add_local(), is_default=True, order=10),
            Action("add_remote", f"Projekt von {platform_name} herunterladen …",
                   Target.ADD_REMOTE, lambda c: self.add_remote(),
                   availability=self._upload_availability, is_default=True, order=10),
            Action("upload_existing", f"Auf {platform_name} hochladen …", Target.CODE,
                   self.upload_action, availability=self._upload_availability,
                   visible=_not_on_platform, is_default=True, order=10),
            Action("resolve_conflicts", "Konflikte lösen …", Target.CODE, self.resolve_action,
                   visible=_unfinished_merge, is_default=True, order=5),
            Action("push_changes", "Änderungen hochladen …", Target.CODE, self.push_action,
                   availability=_git_availability, visible=_on_platform, is_default=True,
                   order=10),
            Action("pull_changes", f"Änderungen von {platform_name} holen …", Target.CODE,
                   self.pull_action, availability=_git_availability, visible=_on_platform,
                   order=20),
            Action("history", "Verlauf …", Target.CODE, self.history_action,
                   availability=_git_availability, visible=_is_repo, order=30),
            Action("discard", "Änderungen verwerfen …", Target.CODE, self.discard_action,
                   availability=_discard_availability, visible=_is_repo, order=35),
            Action("relocate", "Neuen Ort angeben …", Target.PROJECT, self.relocate_action,
                   visible=lambda c: c.project is not None and not c.project.folder_found,
                   order=5),
            Action("connect_repo", "Mit vorhandenem Repository verbinden …", Target.CODE,
                   self.connect_action, visible=_git_missing, order=40),
            Action("git_identity", "Git-Identität …", Target.CODE, self.identity_action,
                   visible=_is_repo, order=85),
            Action("repair_venv", "Virtuelle Umgebung neu anlegen …", Target.CODE,
                   self.repair_venv_action, visible=_venv_broken, order=45),
            Action("download", "Herunterladen", Target.REMOTE_REPO, self.download_action,
                   availability=self._download_availability, is_default=True, order=10),
            Action("open_remote", f"Auf {platform_name} öffnen",
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
            self.busy.discard(key)
            announce(message, urgent=True)
            show_error(self.window, failed_title, message, details)

        def result(value) -> None:
            self.busy.discard(key)          # done darf gleich den nächsten Schritt starten
            done(value)

        task.result.connect(result)
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

    # -- Projekt neu einlesen ----------------------------------------------------------------
    def reread_action(self, context: ActionContext) -> None:
        """Stand dieses einen Projekts neu abfragen (Wunsch aus dem Test von 5c). Im Menü Datei
        steht weiter "Projekte neu einlesen" für alle."""
        name, project_id = context.project.name, context.project.id
        self.window.refresh_status([project_id],
                                   on_done=lambda: announce(f"{name} neu eingelesen."))

    # -- Projekt vom Rechner hinzufügen ------------------------------------------------------
    def add_local(self) -> None:
        root = self.services.settings.load().projects_root
        folder = pick_folder(self.window, "Projekt vom Rechner hinzufügen", root)
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
        text = (f"Der Ordner {folder.name} hat keinen Unterordner Code. "
                f"In den Projekte-Hauptordner verschieben: Das Cockpit legt den Projektordner "
                f"{root / folder.name} an und verschiebt den gewählten Ordner dorthin als Code. "
                f"Am Ort lassen: Der Ordner bleibt, wo er ist. Das Cockpit merkt sich nur, wo er "
                f"liegt. Das passt auch für Repositories, deren Aufbau Sie nicht ändern dürfen.")
        choice = ask_buttons(self.window, "Projekt vom Rechner hinzufügen", text,
                             ["In den Projekte-Hauptordner verschieben …", "Am Ort lassen …",
                              "Abbrechen"], default=2, escape=2)
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
        if not confirm(self.window, "Verschieben", f"{how} Verschieben?", yes="Verschieben",
                       no="Abbrechen"):
            return
        try:
            project, moved = self.services.projects.convert(folder, root)
        except CockpitError as exc:
            show_error(self.window, "Verschieben", exc.message, exc.details)
            return
        self._added(project)

    def _link(self, folder: Path) -> None:
        exe_dir = None
        if confirm(self.window, "Am Ort lassen", f"Der Code-Ordner ist {folder}. Gibt es "
                   "zu diesem Projekt auch einen Exe-Ordner?", yes="Exe-Ordner wählen …",
                   no="Ohne Exe-Ordner"):
            exe_dir = pick_folder(self.window, "Exe-Ordner wählen", str(folder.parent))
        try:
            project = self.services.projects.add_linked(folder, exe_dir)
        except CockpitError as exc:
            show_error(self.window, "Am Ort lassen", exc.message, exc.details)
            return
        self._added(project)

    def _added(self, project: Project) -> None:
        self.ensure_identity(project)
        self.window.reload_projects(refresh=False)
        self.window.show_project(project.id)
        self.window.refresh_status([project.id])
        announce(f"{project.name} hinzugefügt.")
        self.offer_upload(project)

    def offer_upload(self, project: Project) -> None:
        """Liegt das Projekt noch nicht auf der Plattform, gleich das Hochladen anbieten.
        Vorgabe ist "Später"."""
        on_platform = git.is_repo(project.code_dir) and bool(
            git.config_get(project.code_dir, "remote.origin.url"))
        if on_platform or not self._upload_availability(None).available:
            return
        name = self.window.project_list.platform_name
        if confirm(self.window, f"Auf {name} hochladen",
                   f"{project.name} ist noch nicht auf {name}. Jetzt hochladen? Sie können das "
                   f"auch später bei Code mit der Aktion Auf {name} hochladen machen.",
                   yes="Jetzt hochladen …", no="Später"):
            from cockpit.ui.upload_flow import UploadRunner
            UploadRunner(self, project).start()

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

    # -- Hochladen (Konzept 9.1) -------------------------------------------------------------
    def _upload_availability(self, context: ActionContext) -> Availability:
        if git.find_git() is None:
            return Availability.no("Git ist nicht installiert.")
        if not self.services.platform_accounts():
            return Availability.no("Es ist noch kein Konto bei einer Plattform eingerichtet.")
        return Availability.yes()

    def add_remote(self) -> None:
        """Projekt von der Plattform herunterladen: eigene Repositories und die der
        Organisationen, neueste oben, dazu "Adresse eingeben …"."""
        accounts = self.services.platform_accounts()
        if not accounts:
            return
        if len(accounts) > 1:
            index = choose_from_list(self.window, "Konto wählen", "Konten",
                                     [a.label for a in accounts])
            if index is None:
                return
            accounts = [accounts[index]]
        account = accounts[0]
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services = self.services
        local = {p.remote.key for p in services.projects.all() if p.remote is not None}
        announce("Repositories werden abgefragt.")

        def work(task: Task) -> list:
            platform = services.platform(account.id)
            repos = list(platform.repositories())
            try:
                organizations = platform.organizations()
            except CockpitError:
                organizations = []
            for organization in organizations:
                try:
                    repos.extend(platform.repositories(organization))
                except CockpitError as exc:
                    log.warning("Repositories von %s: %s", organization, exc.message)
            return sorted(repos, key=lambda r: r.pushed_at, reverse=True)

        def done(repos: list) -> None:
            self.choose_remote(account, [r for r in repos if _key(r) not in local])

        self.run_task(f"remote-list:{account.id}", work, done, "Herunterladen")

    def choose_remote(self, account, repos: list) -> None:
        from datetime import datetime
        from urllib.parse import urlparse
        name = self.window.project_list.platform_name

        def line(repo) -> str:
            parts = [repo.ref.name, repo.ref.owner, "privat" if repo.private else "öffentlich"]
            try:
                pushed = datetime.fromisoformat(repo.pushed_at.replace("Z", "+00:00"))
                parts.append(f"aktualisiert am {pushed:%d.%m.%Y}")
            except ValueError:
                pass
            return ", ".join(parts)

        # "Adresse eingeben …" steht oben (Wunsch aus dem Test von 5b)
        items = [ENTER_ADDRESS] + [line(r) for r in repos]
        index = choose_from_list(self.window, f"Projekt von {name} herunterladen",
                                 "Repositories", items)
        if index is None:
            return
        if index > 0:
            repo = repos[index - 1]
            host = (urlparse(repo.web_url or repo.clone_url).hostname or "").lower()
            stored = StoredRepo(0, account.id, host, repo.ref.owner, repo.ref.name,
                                repo.private, repo.clone_url, repo.web_url, repo.pushed_at)
        else:
            from PySide6.QtWidgets import QInputDialog
            url, ok = QInputDialog.getText(self.window, f"Projekt von {name} herunterladen",
                                           "Adresse des Repositories:")
            address = git.parse_remote(url) if ok else None
            if address is None:
                if ok:
                    show_error(self.window, "Herunterladen", "Die Adresse wurde nicht erkannt. "
                               "Beispiel: https://github.com/Name/Projekt")
                return
            match = self.services.account_for_host(address.host)
            stored = StoredRepo(0, match.id if match else None, address.host, address.owner,
                                address.name, True, url.strip(), "", "")
        self.download(stored)

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
        items = [ENTER_ADDRESS] + [f"{r.name}, {r.owner}" for r in repos]
        current = next((i + 1 for i, r in enumerate(repos) if r.name.lower() ==
                        project.name.lower()), 0)
        index = choose_from_list(self.window, f"{project.name} verbinden", "Repositories",
                                 items, current)
        if index is None:
            return
        if index > 0:
            repo = repos[index - 1]
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
        text = (f"{project.name} hat keinen Git-Ordner. Das passiert zum Beispiel, wenn beim "
                "Kopieren oder Verschieben der versteckte Ordner .git fehlte. Ohne ihn weiß das "
                "Projekt nicht, zu welchem Repository es gehört, und hat keinen Verlauf. "
                f"{project.name} wird jetzt mit dem Repository {label} verbunden. Die Dateien im "
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


def _key(repo) -> str:
    from urllib.parse import urlparse
    host = (urlparse(repo.web_url or repo.clone_url).hostname or "").lower()
    return git.RemoteAddress(host, repo.ref.owner, repo.ref.name).key


def _not_on_platform(context: ActionContext) -> bool:
    status = context.status
    return (context.project is not None and context.project.folder_found
            and status is not None and status.repo is not None and not status.on_platform)


def _on_platform(context: ActionContext) -> bool:
    return (context.project is not None and context.project.folder_found
            and context.status is not None and context.status.on_platform)


def _unfinished_merge(context: ActionContext) -> bool:
    return context.status is not None and bool(context.status.unfinished_merge)


def _git_availability(context: ActionContext) -> Availability:
    if git.find_git() is None:
        return Availability.no("Git ist nicht installiert.")
    return Availability.yes()


def _discard_availability(context: ActionContext) -> Availability:
    status = context.status
    if status is not None and status.unfinished_merge:
        return Availability.no("Bitte lösen Sie zuerst die Konflikte.")
    if status is not None and status.repo is not None and not status.repo.changed:
        return Availability.no("Es gibt keine Änderungen ohne Commit.")
    return _git_availability(context)


def _is_repo(context: ActionContext) -> bool:
    status = context.status
    return status is not None and status.repo is not None and status.repo.is_repo


def _git_missing(context: ActionContext) -> bool:
    status = context.status
    return (context.project is not None and context.project.folder_found
            and status is not None and status.repo is not None and not status.repo.is_repo)


def _venv_broken(context: ActionContext) -> bool:
    return context.status is not None and context.status.venv.broken
