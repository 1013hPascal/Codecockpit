"""Projekt und Plattform: Repository anlegen, herunterladen, verbinden, löschen, ausblenden.

Teil von ProjectController (project_actions.py).
"""
from __future__ import annotations

import logging
from pathlib import Path

from cockpit.core import core_actions, git, project_setup, repo_admin
from cockpit.core.actions import ActionContext
from cockpit.core.availability import Availability
from cockpit.core.errors import CockpitError
from cockpit.core.projects import CODE_DIR, Project
from cockpit.core.remote_repos import StoredRepo
from cockpit.ui import vault_ui
from cockpit.ui.action_conditions import _not_on_platform
from cockpit.ui.announcer import announce
from cockpit.ui.common import choose_from_list, confirm
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

log = logging.getLogger(__name__)


ENTER_ADDRESS = "Adresse eingeben …"


def _key(repo) -> str:
    from urllib.parse import urlparse
    host = (urlparse(repo.web_url or repo.clone_url).hostname or "").lower()
    return git.RemoteAddress(host, repo.ref.owner, repo.ref.name).key


class RemoteActions:
    """Aktionen zwischen dem Projekt auf dem Rechner und dem Repository auf der Plattform."""

    # -- Hochladen (Konzept 9.1) -------------------------------------------------------------
    # -- Repository fehlt auf der Plattform (Wunsch des Nutzers vom 04.10.2026) -------------
    def _repo_missing(self, context: ActionContext) -> bool:
        return context.project is not None and context.project.id in self.missing_repos

    def _needs_repo(self, context: ActionContext) -> bool:
        return _not_on_platform(context) or (self._repo_missing(context)
                                             and context.project.folder_found)

    def check_repo(self, project: Project, ask: bool) -> None:
        """Im Hintergrund nachsehen, ob es das Repository auf der Plattform gibt. Fehlt es,
        steht "Repository … anlegen und hochladen …" in den Aktionen. ask: dann auch fragen."""
        if not (project.folder_found and git.is_repo(project.code_dir)
                and git.config_get(project.code_dir, "remote.origin.url")):
            if ask:
                self.offer_upload(project)
            return
        if not self.services.platform_accounts() or \
                not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services = self.services

        def done(missing: bool) -> None:
            if missing:
                self.missing_repos.add(project.id)
            else:
                self.missing_repos.discard(project.id)
            self.window.refresh_actions(keep_selection=True)
            if missing and ask:
                self.offer_create(project)

        self.run_task(f"repo-check:{project.id}",
                      lambda task: repo_admin.repo_missing(services, project), done,
                      "Repository prüfen")

    def offer_create(self, project: Project) -> None:
        name = self.window.project_list.platform_name
        remote = project.remote
        where = f"{remote.owner}/{remote.name}" if remote is not None else project.name
        if confirm(self.window, f"Auf {name} hochladen",
                   f"Das Repository {where} gibt es auf {name} noch nicht. Jetzt anlegen und "
                   f"hochladen? Sie können das auch später mit der Aktion Repository auf {name} "
                   "anlegen und hochladen machen.", yes="Jetzt anlegen …", no="Später"):
            from cockpit.ui.upload_flow import UploadRunner
            UploadRunner(self, project).start()

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
            # Fremdes Repository: vorher fragen, ob ein Fork entstehen soll (21.10.2026)
            from cockpit.ui import fork_flow
            fork_flow.download_or_fork(self, stored)
            return
        self.download(stored)

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

        self.run_task(f"clone:{repo.owner}/{repo.name}".lower(), work, done, "Herunterladen",
                      transfer=True)

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

    def _remote_account_availability(self, context: ActionContext) -> Availability:
        repo = context.remote_repo
        if repo is None:
            return Availability.no("Das Repository ist nicht mehr in der Liste.")
        account = self.services.accounts.get(repo.account_id)
        if account is None:
            return Availability.no("Das Konto zu diesem Repository gibt es nicht mehr.")
        return Availability.yes()

    def delete_remote_action(self, context: ActionContext) -> None:
        """Repository löschen, das nur auf der Plattform liegt. Dieselben Rückfragen wie bei
        "Projekt verwalten": Warnung mit "Stattdessen archivieren …", dann den Namen eintippen."""
        from cockpit.platforms.base import RepoRef
        from cockpit.ui.repo_dialogs import RepoDeleter, _Worker
        repo = context.remote_repo
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        platform = self.services.platform(repo.account_id)
        if platform is None:
            show_error(self.window, "Repository löschen", "Das Konto zu diesem Repository gibt "
                       "es nicht mehr.")
            return
        name = self.window.project_list.platform_name
        ref = RepoRef(repo.owner, repo.name)
        worker = _Worker(self.window, "Repository löschen")
        self.remote_worker = worker                 # lebt, solange die Aufgabe läuft

        def deleted() -> None:
            self.services.remote_repos.forget(repo.address)
            cut = repo_admin.forget_address(self.services, repo.address)
            self.window.reload_projects(refresh=False)
            text = f"{repo.name} ist auf {name} gelöscht."
            if cut:
                text += f" Verbindung entfernt bei: {', '.join(cut)}."
            announce(text)

        def archive() -> None:
            text = (f"{repo.name} wird schreibgeschützt. Niemand kann mehr hochladen, auch Sie "
                    f"nicht. Das Repository bleibt auf {name} erhalten, und die Archivierung lässt "
                    "sich jederzeit wieder aufheben. Archivieren?")
            if confirm(self.window, "Archivieren", text, yes="Archivieren", no="Abbrechen"):
                worker.run(lambda: platform.archive(ref),
                           lambda _value: announce(f"{repo.name} ist archiviert."))

        RepoDeleter(self.window, worker, platform, ref, name, False, deleted, archive,
                    local=False).start()

    def hide_remote_action(self, context: ActionContext) -> None:
        repo = context.remote_repo
        name = self.window.project_list.platform_name
        text = (f"{repo.name} erscheint nicht mehr in der Liste. Auf {name} ändert sich nichts. "
                f"Mit „Projekt von {name} herunterladen“ können Sie es jederzeit holen. "
                "Entfernen?")
        if not confirm(self.window, "Aus der Liste entfernen", text, yes="Entfernen",
                       no="Abbrechen"):
            return
        self.services.remote_repos.hide(repo.address)
        self.window.reload_projects(refresh=False)
        announce(f"{repo.name} aus der Liste entfernt.")

    def open_repo_remote_action(self, context: ActionContext) -> None:
        """Link zum Repository im Browser öffnen."""
        import webbrowser
        remote = context.project.remote
        webbrowser.open(f"https://{remote.host}/{remote.owner}/{remote.name}")
        announce(f"{remote.name} wird im Browser geöffnet.")
