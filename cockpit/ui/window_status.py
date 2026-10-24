"""Stand der Projekte im Hauptfenster: neu einlesen, Git-Stand und Stand auf der Plattform holen.

Teil von MainWindow (main_window.py). Die Arbeit läuft im Hintergrund.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from cockpit.core import project_status
from cockpit.core.actions import Target
from cockpit.core.errors import CockpitError
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.tasks import Task

log = logging.getLogger(__name__)


def _has_release(project) -> bool:
    """Liegt in einem Release-Ordner eine Exe? Fehler beim Lesen zählen als nein."""
    from cockpit.core import local_releases
    try:
        return local_releases.has_any_exe(project)
    except OSError:
        return False


def refresh_pull_requests(services, platform, account, cancel=None) -> None:
    """Offene Pull Requests der Projekte dieses Kontos in den Zwischenspeicher holen (Phase 6).
    Läuft im Hintergrund. Fehler bei einem Projekt stören die anderen nicht."""
    from cockpit.core import repo_admin
    from cockpit.platforms.base import SupportsPullRequests
    if not isinstance(platform, SupportsPullRequests):
        return
    for project in services.projects.all():
        if cancel is not None and cancel.is_set():
            return
        if project.remote is None:
            continue
        owner = repo_admin.account_for(services, project)
        if owner is None or owner.id != account.id:
            continue
        try:
            pulls = platform.pull_requests(repo_admin.repo_ref(project), "open")
        except CockpitError as exc:
            log.warning("Pull Requests von %s: %s", project.name, exc.message)
            continue
        services.pull_request_cache.replace(project.remote, pulls)


def refresh_activity(services, platform, projects, cancel=None) -> None:
    """Neuigkeiten und, einmal am Tag, die Zahlen der Aktivität holen (22.10.2026). Die Features
    prüfen selbst, ob sie eingeschaltet sind und die Plattform das kann."""
    from cockpit.features.activity import activity
    from cockpit.features.news import news
    news.refresh(services, platform, projects, cancel)
    activity.refresh(services, platform, projects, cancel)


class StatusMixin:
    """Projekte einlesen und ihren Stand holen."""

    def reload_projects(self, refresh: bool = True) -> list:
        """Hauptordner durchsuchen und Projektliste neu füllen. Gibt neu gefundene Projekte zurück.
        refresh: danach den Stand aller Projekte im Hintergrund abfragen."""
        root = Path(self.services.settings.load().projects_root)
        found = self.services.projects.scan(root) if root.is_dir() else []
        self.project_list.platform_name = self.platform_name()
        collections = self.services.collections
        projects = self.services.projects.all()
        collections.adopt(projects)                 # heruntergeladen: Sammlung übernehmen
        self.project_list.set_projects(projects, self._remote_only(), collections.all(),
                                       collections.membership(),
                                       collections.remote_membership())
        self.refresh_actions()
        if refresh:
            self.refresh_status()
        return found

    def rescan(self) -> None:
        found = self.reload_projects()
        total = len(self.services.projects.all())
        text = f"Projekte neu eingelesen. {count(total, 'Projekt', 'Projekte')}."
        if found:
            text += f" Neu: {', '.join(p.name for p in found)}."
        announce(text)
        self.refresh_remote()

    def show_project(self, project_id: int) -> None:
        """Projekt in der Liste markieren."""
        self.project_list.select(Target.PROJECT, project_id)

    def _reload_if_remote_changed(self) -> None:
        """Nur neu aufbauen, wenn sich die Zeilen "nur auf GitHub" geändert haben."""
        remote_ids = {r.id for r in self._remote_only()}
        if remote_ids != set(self.project_list.remote_ids()):
            self.reload_projects(refresh=False)

    def refresh_status(self, project_ids: list[int] | None = None,
                       on_done: Callable[[], None] | None = None) -> None:
        """Stand der Projekte im Hintergrund abfragen (ohne Ansage, der Fokus bleibt).
        on_done kommt, wenn keine Abfrage mehr läuft oder wartet."""
        if on_done is not None:
            self.status_callbacks.append(on_done)
        if self.status_task is not None:
            if project_ids is None:
                self.status_queue_all = True
            self.status_queue = (self.status_queue or set()) | set(project_ids or [])
            return
        store = self.services.projects
        pulls = self.services.pull_request_cache
        wanted = None if project_ids is None else set(project_ids)
        projects = [p for p in store.all() if wanted is None or p.id in wanted]

        def work(task: Task) -> list:
            result = []
            for project in projects:
                if task.cancel_event.is_set():
                    break
                status = project_status.compute(project)
                project_status.remember(store, project, status)
                if status.repo is not None and status.repo.branch:
                    # Aus dem Zwischenspeicher, ohne GitHub zu fragen (Phase 6)
                    status.open_pulls = pulls.count_for_branch(project.remote,
                                                               status.repo.branch)
                # Für Filter und Zeichen in der Liste (07.10.2026)
                open_pulls = pulls.open_pulls(project.remote) if project.remote else []
                status.repo_pulls = len(open_pulls)
                status.review_requests = sum(1 for p in open_pulls if p.reviewers)
                status.has_release = _has_release(project)
                if project.remote is not None:
                    # Gemerkt beim Abfragen der Repositories (Phase 14)
                    from cockpit.features.releases.runs import last_failed
                    status.actions_failed = last_failed(self.services.database,
                                                        project.remote.key)
                result.append(status)
            return result

        task = Task(work, self)
        task.result.connect(self._status_done)
        task.finished.connect(self._status_finished)
        self.status_task = task
        task.start()

    def _status_done(self, statuses: list) -> None:
        current = self.project_list.current_target()[1]
        for status in statuses:
            self.project_list.update_status(status, self.services.projects.get(status.project_id))
        if any(s.project_id == current for s in statuses):
            self.refresh_actions(keep_selection=True)
        self._reload_if_remote_changed()           # ein Projekt ist jetzt verbunden

    def _status_finished(self) -> None:
        task, self.status_task = self.status_task, None
        if task is not None:
            task.wait()                      # Thread ganz beendet, sonst bricht Qt ab
            task.deleteLater()
        if self.status_queue is not None:
            queued = None if self.status_queue_all else list(self.status_queue)
            self.status_queue, self.status_queue_all = None, False
            self.refresh_status(queued)
            return
        callbacks, self.status_callbacks = self.status_callbacks, []
        for callback in callbacks:
            callback()

    def refresh_remote(self) -> None:
        """Repositories der Plattform-Konten im Hintergrund abfragen. Ist die Tresordatei
        gesperrt, bleibt es bei der gemerkten Liste (das Master-Passwort kommt erst bei Bedarf)."""
        accounts = self.services.platform_accounts()
        vault = self.services.vault
        if not accounts or self.remote_task is not None or vault.vault is None:
            return
        if not vault.is_unlocked():
            return
        services = self.services

        def work(task: Task) -> tuple:
            new, problems = [], []
            for account in accounts:
                if task.cancel_event.is_set():
                    break
                try:
                    platform = services.platform(account.id)
                    if platform is None:
                        continue
                    repos = platform.repositories()
                    new.extend(services.remote_repos.replace(account.id, repos))
                    refresh_pull_requests(services, platform, account, task.cancel_event)
                    from cockpit.core import repo_admin
                    from cockpit.features.releases.runs import refresh_state
                    mine = [p for p in services.projects.all()
                            if (owner := repo_admin.account_for(services, p)) is not None
                            and owner.id == account.id]
                    refresh_state(services, platform, mine, task.cancel_event)
                    refresh_activity(services, platform, mine, task.cancel_event)
                except CockpitError as exc:
                    log.warning("Repositories von %s: %s %s", account.display_name,
                                exc.message, exc.details)
                    problems.append(f"{account.display_name}: {exc.message}")
            return new, problems

        task = Task(work, self)
        task.result.connect(self._remote_done)
        task.finished.connect(self._remote_finished)
        self.remote_task = task
        task.start()

    def _remote_done(self, outcome) -> None:
        new, problems = outcome
        for problem in problems:
            announce(f"Repositories nicht abgefragt. {problem}", speak=False)
        self._reload_if_remote_changed()
        self.refresh_status()                      # Hinweis auf fehlgeschlagene Läufe (14)
        self.news.after_refresh()                  # einmal pro Sitzung (22.10.2026)
        if new and self.services.settings.load().auto_clone_new:
            remote_ids = set(self.project_list.remote_ids())
            for repo in new:
                if repo.id in remote_ids:
                    self.controller.download(repo, speak=False)

    def _remote_finished(self) -> None:
        task, self.remote_task = self.remote_task, None
        if task is not None:
            task.wait()                      # Thread ganz beendet, sonst bricht Qt ab
            task.deleteLater()
