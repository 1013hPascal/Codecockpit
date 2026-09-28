"""Hauptfenster: Menüleiste, Projektliste, Aktionsliste und Statuszeile.

Tab-Kreis: Projektliste, Aktionsliste, wieder Projektliste. Umschalt+Tab führt aus der
Aktionsliste zurück auf den Eintrag, von dem man kam. Die Statuszeile ist kein Tab-Stopp. Ihre Meldungen
kommen als Ansage, Strg+Umschalt+M wiederholt die letzte.

Es erscheinen nur Menüpunkte, die schon funktionieren (ENTSCHEIDUNGEN.md).
"""
from __future__ import annotations

import dataclasses
import logging
import time
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow, QMenu,
                               QVBoxLayout, QWidget)

from cockpit import APP_NAME, __version__
from cockpit.core import backups, core_actions, git, paths, project_status
from cockpit.core.actions import (ActionContext, ActionEntry, Target, default_entry,
                                  entries_for)
from cockpit.core.errors import CockpitError
from cockpit.core.services import Services
from cockpit.core.text import count
from cockpit.ui.announcer import announce, announcer
from cockpit.ui.action_list import ActionList
from cockpit.ui import vault_ui
from cockpit.ui.accounts_dialog import AccountsDialog
from cockpit.ui.asker import QtAsker
from cockpit.ui.common import show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.menus import AccessibleMenu
from cockpit.ui.messages_dialog import MessagesDialog
from cockpit.ui.project_actions import ProjectController
from cockpit.ui.project_list import ProjectList
from cockpit.ui.settings_dialog import SettingsDialog
from cockpit.ui.setup_wizard import SetupWizard
from cockpit.ui.tasks import Task
from cockpit.ui.text_dialog import TextDialog
from cockpit.ui.vault_settings_dialog import VaultSettingsDialog

log = logging.getLogger(__name__)

LOCK_CHECK_MS = 15_000

SHORTCUTS = [
    "Aufbau: links die Projektliste, rechts die Aktionen",
    "Zwischen Projektliste und Aktionen wechseln, Tab",
    "Aus den Aktionen zurück zum Eintrag in der Projektliste, Umschalt+Tab",
    "Projektliste",
    "Projekt ausklappen, Pfeil rechts, Leertaste oder Enter",
    "Im ausgeklappten Projekt zum ersten Unterordner, Pfeil rechts",
    "Projekt zuklappen, Leertaste oder Enter auf dem Projekt",
    "Zuklappen und zurück zum Projekt, Pfeil links auf Code oder Exe",
    "Wichtigste Aktion auf Code oder Exe, Enter",
    "Aktionen als Kontextmenü, Menütaste oder Umschalt+F10",
    "Repository herunterladen, das nur auf GitHub liegt, Enter",
    "Aktionen",
    "Markierte Aktion ausführen, Enter oder Leertaste",
    "Bei nicht verfügbaren Aktionen wird der Grund angesagt",
    "Bereiche",
    "Projektliste, Strg+1",
    "Aktionen, Strg+2",
    "Nächster und vorheriger Bereich, F6 und Umschalt+F6",
    "Meldungen",
    "Letzte Meldung wiederholen, Strg+Umschalt+M",
    "Liste der letzten Meldungen, Strg+Umschalt+L",
    "Menüs",
    "Datei, Alt+D",
    "Features, Alt+F",
    "KI, Alt+K",
    "Konten, Alt+O",
    "Einstellungen, Alt+E",
    "Hilfe, Alt+H",
    "Projekte neu einlesen und Stand abfragen, Strg+R",
    "Beenden, Strg+Q",
    "Diese Liste, F1",
    "In Listen wie dieser: Zeile kopieren, Strg+C",
]


class MainWindow(QMainWindow):
    def __init__(self, services: Services, testdata: bool = False) -> None:
        super().__init__()
        self.services = services
        self.testdata = testdata
        self.asker = QtAsker(self)
        self.setWindowTitle(f"{APP_NAME} (Testdaten)" if testdata else APP_NAME)

        self.project_list = ProjectList()
        self.controller = ProjectController(self)
        self.status_task: Task | None = None
        self.status_queue: set[int] | None = None       # wartet auf den laufenden Abruf
        self.status_queue_all = False
        self.status_callbacks: list[Callable[[], None]] = []
        self.remote_task: Task | None = None
        self.actions_list = ActionList()
        list_label = QLabel("&Projekte:")
        list_label.setBuddy(self.project_list)
        actions_label = QLabel("A&ktionen:")
        actions_label.setBuddy(self.actions_list)

        left = QVBoxLayout()
        left.addWidget(list_label)
        left.addWidget(self.project_list, 1)
        right = QVBoxLayout()
        right.addWidget(actions_label)
        right.addWidget(self.actions_list, 1)
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.addLayout(left, 3)
        layout.addLayout(right, 2)
        self.setCentralWidget(central)
        self.resize(1000, 700)

        self.status_label = QLabel("Bereit")
        self.status_label.setAccessibleName("Status")
        self.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.statusBar().addWidget(self.status_label, 1)

        announcer.target = self
        announcer.listeners.append(self._show_status)

        from cockpit.ui.update_ui import Updater
        self.updater = Updater(self)
        self._build_menus()
        self._build_shortcuts()
        QWidget.setTabOrder(self.project_list, self.actions_list)
        QWidget.setTabOrder(self.actions_list, self.project_list)
        self.areas = [self.project_list, self.actions_list]

        self.project_list.currentRowChanged.connect(lambda _row: self.refresh_actions())
        self.project_list.defaultActionRequested.connect(self.run_default_action)
        self.project_list.contextMenuRequested.connect(self.show_context_menu)
        self.actions_list.entryTriggered.connect(self.run_entry)

        # Automatisches Sperren der Tresordatei nach Inaktivität (Tresor-Einstellungen).
        # Geprüft wird alle 15 Sekunden gegen die Uhrzeit der letzten Eingabe. So zählt auch
        # die Zeit im Standby mit, und nach dem Aufwachen wird sofort gesperrt.
        self.last_input = time.time()
        self.lock_timer = QTimer(self)
        self.lock_timer.setInterval(LOCK_CHECK_MS)
        self.lock_timer.timeout.connect(self.check_auto_lock)
        QApplication.instance().installEventFilter(self)
        self.restart_lock_timer()

        self.reload_projects()
        self.updater.start()

    # -- Aufbau ---------------------------------------------------------------------------
    def _action(self, menu: QMenu, text: str, slot, shortcut: str | None = None) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
            self.addAction(action)                     # Kürzel gelten auch bei geschlossenem Menü
        action.triggered.connect(lambda checked=False: slot())
        menu.addAction(action)
        return action

    def _build_menus(self) -> None:
        bar = self.menuBar()
        file_menu = AccessibleMenu("&Datei", self)
        bar.addMenu(file_menu)
        self._action(file_menu, "Projekt vom &Rechner hinzufügen …", self.controller.add_local)
        self.act_download = self._action(file_menu, "Projekt von GitHub &herunterladen …",
                                         self.controller.add_remote)
        file_menu.aboutToShow.connect(self.update_file_menu)
        self._action(file_menu, "Projekte &neu einlesen", self.rescan, "Ctrl+R")
        self._action(file_menu, "&Sicherheitskopien …", self.open_backups)
        file_menu.addSeparator()
        self._action(file_menu, "&Beenden", self.close, "Ctrl+Q")

        features_menu = AccessibleMenu("&Features", self)
        bar.addMenu(features_menu)
        self._action(features_menu, "Feature-&Verwaltung …", self.open_features)

        ai_menu = AccessibleMenu("&KI", self)
        bar.addMenu(ai_menu)
        self._action(ai_menu, "KI-&Verwaltung …", self.open_ai_manager)
        self._action(ai_menu, "KI-&Features …", self.open_ai_features)

        accounts_menu = AccessibleMenu("K&onten", self)
        bar.addMenu(accounts_menu)
        self._action(accounts_menu, "&Kontenverwaltung …", self.open_accounts)
        self._action(accounts_menu, "&Tresor-Einstellungen …", self.open_vault_settings)
        self.act_lock = self._action(accounts_menu, "Tresor &sperren", self.lock_vault)
        self.act_unlock = self._action(accounts_menu, "Tresor &entsperren …", self.unlock_vault)
        accounts_menu.aboutToShow.connect(self.update_vault_actions)
        self.update_vault_actions()

        settings_menu = AccessibleMenu("&Einstellungen", self)
        bar.addMenu(settings_menu)
        self._action(settings_menu, "&Grundeinstellungen …", self.open_settings)
        self._action(settings_menu, "&Einrichtungsassistent …", self.open_wizard)

        help_menu = AccessibleMenu("&Hilfe", self)
        bar.addMenu(help_menu)
        self._action(help_menu, "&Tastenkürzel", self.show_shortcuts, "F1")
        self._action(help_menu, "&Letzte Meldung wiederholen", announcer.repeat_last,
                     "Ctrl+Shift+M")
        self._action(help_menu, "&Meldungen …", self.show_messages, "Ctrl+Shift+L")
        self._action(help_menu, "&Git installieren …", self.show_git_guide)
        self._action(help_menu, "GitHub-T&oken erstellen …", self.show_token_guide)
        self._action(help_menu, "B&ranches verstehen …", self.show_branches_guide)
        self._action(help_menu, "&Python installieren …",
                     lambda: self.show_guide("anleitungen/python-installieren.md",
                                             "Python installieren"))
        self._action(help_menu, "Wie funktioniert die &Exe? …",
                     lambda: self.show_guide("anleitungen/exe-verstehen.md",
                                             "Wie funktioniert die Exe?"))
        self._action(help_menu, "Oll&ama installieren …",
                     lambda: self.show_guide("anleitungen/ollama-installieren.md",
                                             "Ollama installieren"))
        help_menu.addSeparator()
        self._action(help_menu, "Nach &Updates suchen …", self.updater.check_now)
        self._action(help_menu, f"Ü&ber {APP_NAME}", self.show_about)

    def open_ai_manager(self) -> None:
        """KI-Werkzeuge für Text, lokal oder extern (Konzept 11.1)."""
        from cockpit.ui.ai_dialogs import AIManagerDialog
        AIManagerDialog(self.services, self).exec()
        self.services.forget_platforms()
        self.refresh_actions(keep_selection=True)

    def open_ai_features(self) -> None:
        """Feature-Verwaltung, markiert beim ersten KI-Feature (Konzept 11.1)."""
        ai_features = [m.id for m in self.services.registry.all() if "ai" in m.requires_services]
        self.open_features(select=ai_features[0] if ai_features else None)

    def open_features(self, select: str | None = None) -> None:
        """Feature-Verwaltung für alle Projekte (Konzept 8.5)."""
        from cockpit.ui.features_dialogs import GlobalFeaturesDialog
        dialog = GlobalFeaturesDialog(self.services, self)
        if select is not None:
            dialog.select(select)
        dialog.exec()
        if dialog.changed:
            self.refresh_actions(keep_selection=True)
            self.refresh_status()

    def open_backups(self) -> None:
        from cockpit.ui.backups_dialog import BackupsDialog
        BackupsDialog(self).exec()
        self.refresh_status()                  # Wiederherstellen kann den Stand ändern

    def update_file_menu(self) -> None:
        self.act_download.setText(f"Projekt von {self.platform_name()} &herunterladen …")

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+1"), self, activated=self.focus_project_list)
        QShortcut(QKeySequence("Ctrl+2"), self, activated=self.focus_actions)
        QShortcut(QKeySequence("F6"), self, activated=lambda: self.cycle_area(+1))
        QShortcut(QKeySequence("Shift+F6"), self, activated=lambda: self.cycle_area(-1))

    def _show_status(self, message) -> None:
        self.status_label.setText(message.text)

    # -- Start ----------------------------------------------------------------------------
    def initial_focus(self) -> None:
        self.project_list.setFocus()

    def startup(self) -> None:
        """Nach dem Anzeigen: Projekte melden, Voraussetzungen prüfen, Repositories abfragen."""
        number = len(self.services.projects.all())
        prefix = f"{APP_NAME} mit Testdaten bereit." if self.testdata else f"{APP_NAME} bereit."
        announce(f"{prefix} {count(number, 'Projekt', 'Projekte')}.")
        if git.find_git() is None:
            announce("Git wurde nicht gefunden. Die Anleitung steht im Menü Hilfe unter "
                     "Git installieren.", urgent=True)
        for problem in self.services.registry.load_errors:
            announce(problem, urgent=True)
        try:
            backups.remove_old()
        except OSError as exc:
            log.warning("Alte Sicherheitskopien nicht gelöscht: %r", exc)
        self.refresh_remote()

    # -- Projekte -------------------------------------------------------------------------
    def platform_name(self) -> str:
        """Name der Plattform für "nur auf GitHub" und "noch nicht auf GitHub"."""
        from cockpit.core.accounts import find_type
        for account in self.services.platform_accounts():
            account_type = find_type(account.kind, account.adapter)
            if account_type is not None:
                return account_type.display_name
        return "GitHub"

    def _remote_only(self) -> list:
        local = {p.remote.key for p in self.services.projects.all() if p.remote is not None}
        return self.services.remote_repos.only_remote(local)

    def reload_projects(self, refresh: bool = True) -> list:
        """Hauptordner durchsuchen und Projektliste neu füllen. Gibt neu gefundene Projekte zurück.
        refresh: danach den Stand aller Projekte im Hintergrund abfragen."""
        root = Path(self.services.settings.load().projects_root)
        found = self.services.projects.scan(root) if root.is_dir() else []
        self.project_list.platform_name = self.platform_name()
        self.project_list.set_projects(self.services.projects.all(), self._remote_only())
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
        if new and self.services.settings.load().auto_clone_new:
            remote_ids = set(self.project_list.remote_ids())
            for repo in new:
                if repo.id in remote_ids:
                    self.controller.download(repo, speak=False)

    def _remote_finished(self) -> None:
        task, self.remote_task = self.remote_task, None
        if task is not None:
            task.deleteLater()

    # -- Aktionen -------------------------------------------------------------------------
    def action_context(self) -> ActionContext:
        target, item_id = self.project_list.current_target()
        key = self.project_list.current_key()
        project = remote = None
        if target is Target.REMOTE_REPO:
            remote = self.services.remote_repos.get(item_id) if item_id is not None else None
        elif item_id is not None:
            project = self.services.projects.get(item_id)
        status = self.project_list.status_of(project.id) if project is not None else None
        context = ActionContext(self.services, project, target, announce=announce,
                                asker=self.asker, status=status, remote_repo=remote)
        if target is Target.BRANCH and project is not None:
            # Die Aktionen von Code, aber im Branch-Ordner (Phase 10f)
            tree = next((t for t, _s in (status.worktrees if status else []) if t.folder == key),
                        None)
            if tree is not None:
                context.target, context.worktree, context.main_project = \
                    Target.CODE, tree, project
                context.project = dataclasses.replace(project, code_dir=tree.path)
                context.status = project_status.for_folder(status, key)
        elif target is Target.REMOTE_BRANCH and project is not None:
            context.remote_branch = self.project_list.shown_branch(project.id, key)
        return context

    def current_entries(self) -> list[ActionEntry]:
        context = self.action_context()
        actions = core_actions.all_actions(context) + self.controller.actions()
        return entries_for(actions, context)

    def refresh_actions(self, keep_selection: bool = False) -> None:
        self.actions_list.set_entries(self.current_entries(), keep_selection)

    def run_entry(self, entry: ActionEntry) -> None:
        if not entry.availability.available:
            announce(f"{entry.action.text} ist nicht verfügbar. {entry.availability.reason}")
            return
        try:
            entry.action.run(self.action_context())
        except CockpitError as exc:
            announce(exc.message, urgent=True)
            show_error(self, entry.action.text, exc.message, exc.details)
        except OSError as exc:
            log.warning("Aktion %s fehlgeschlagen: %r", entry.action.id, exc)
            message = f"{entry.action.text} hat nicht geklappt."
            announce(message, urgent=True)
            show_error(self, entry.action.text, message, str(exc))
        # Die Markierung bleibt auf der ausgeführten Aktion, statt nach oben zu springen
        self.refresh_actions(keep_selection=True)

    def run_default_action(self) -> None:
        """Enter in der Projektliste: wichtigste Aktion, sonst in die Aktionsliste springen."""
        entries = self.current_entries()
        entry = default_entry(entries)
        if entry is not None:
            self.run_entry(entry)
            return
        blocked = next((e for e in entries if e.action.is_default), None)
        if blocked is not None:
            self.run_entry(blocked)                    # sagt den Grund an
            return
        self.focus_actions()

    def show_context_menu(self, position) -> None:
        entries = self.current_entries()
        if not entries:
            return
        menu = AccessibleMenu("Aktionen", self)
        chosen: dict[QAction, ActionEntry] = {}
        for entry in entries:
            chosen[menu.addAction(entry.label.replace("&", "&&"))] = entry
        picked = menu.exec(position)
        self.project_list.setFocus()
        if picked is not None:
            self.run_entry(chosen[picked])

    # -- Bereiche -------------------------------------------------------------------------
    def focus_project_list(self) -> None:
        self.project_list.setFocus()

    def focus_actions(self) -> None:
        self.actions_list.setFocus()

    def cycle_area(self, step: int) -> None:
        focused = QApplication.focusWidget()
        index = self.areas.index(focused) if focused in self.areas else -1
        self.areas[(index + step) % len(self.areas)].setFocus()

    # -- Menüs ----------------------------------------------------------------------------
    def open_settings(self) -> None:
        old_root = self.services.settings.load().projects_root
        dialog = SettingsDialog(self.services.settings, self)
        if dialog.exec():
            announce("Grundeinstellungen gespeichert.")
            if self.services.settings.load().projects_root != old_root:
                self.rescan()

    def show_shortcuts(self) -> None:
        TextDialog("Tastenkürzel", SHORTCUTS, "Liste der Tastenkürzel", self).exec()

    def show_messages(self) -> None:
        MessagesDialog(announcer.newest_first(), self).exec()

    def show_guide(self, relative_path: str, title: str) -> None:
        """Anleitung aus dem Ordner anleitungen als Liste zeigen."""
        try:
            text = (paths.resource_dir() / relative_path).read_text(encoding="utf-8")
        except OSError as exc:
            show_error(self, title, "Die Anleitung wurde nicht gefunden.", str(exc))
            return
        TextDialog(title, text, f"Anleitung {title}", self).exec()

    def show_git_guide(self) -> None:
        self.show_guide(git.GUIDE, "Git installieren")

    def show_token_guide(self) -> None:
        self.show_guide("anleitungen/github-token-erstellen.md", "GitHub-Token erstellen")

    def show_branches_guide(self) -> None:
        self.show_guide("anleitungen/branches-verstehen.md", "Branches verstehen")

    def show_about(self) -> None:
        text = [f"{APP_NAME} Version {__version__}",
                f"Datenordner: {paths.data_dir()}",
                "Verwaltet Code-Projekte auf GitHub und GitLab ohne Terminal.",
                "Barrierefrei entwickelt, vollständig per Tastatur bedienbar."]
        TextDialog(f"Über {APP_NAME}", text, f"Über {APP_NAME}", self).exec()

    # -- Konten und Tresor ---------------------------------------------------------------
    def update_vault_actions(self) -> None:
        """Sperren und Entsperren gibt es nur bei der Tresordatei."""
        vault = self.services.vault
        self.act_lock.setVisible(vault.needs_unlock and vault.is_unlocked())
        self.act_unlock.setVisible(vault.needs_unlock and not vault.is_unlocked())

    def open_accounts(self) -> None:
        AccountsDialog(self.services, self).exec()
        self.services.forget_platforms()
        self.restart_lock_timer()
        self.reload_projects(refresh=False)
        self.refresh_remote()

    def open_vault_settings(self) -> None:
        VaultSettingsDialog(self.services, self).exec()
        self.update_vault_actions()
        self.restart_lock_timer()

    def lock_vault(self) -> None:
        self.services.vault.lock()
        self.update_vault_actions()
        announce("Tresor gesperrt.")

    def unlock_vault(self) -> None:
        vault_ui.ensure_unlocked(self.services, self)
        self.update_vault_actions()
        self.restart_lock_timer()

    def open_wizard(self) -> None:
        SetupWizard(self.services, self).exec()
        self.update_vault_actions()
        self.reload_projects()

    def restart_lock_timer(self) -> None:
        vault = self.services.vault
        minutes = self.services.settings.load().auto_lock_minutes
        self.last_input = time.time()
        if vault.needs_unlock and vault.is_unlocked() and minutes > 0:
            self.lock_timer.start()
        else:
            self.lock_timer.stop()

    def check_auto_lock(self) -> None:
        minutes = self.services.settings.load().auto_lock_minutes
        if minutes > 0 and time.time() - self.last_input >= minutes * 60:
            self.auto_lock()

    def auto_lock(self) -> None:
        self.lock_timer.stop()
        if self.services.vault.needs_unlock and self.services.vault.is_unlocked():
            self.services.vault.lock()
            self.update_vault_actions()
            minutes = self.services.settings.load().auto_lock_minutes
            text = (f"Der Tresor wurde nach {count(minutes, 'Minute', 'Minuten')} ohne "
                    "Eingabe gesperrt.")
            # Meldungsfenster mit OK (Wunsch aus dem Test): NVDA liest es sicher vor, auch wenn
            # man gerade in einem anderen Programm war und zurückkommt.
            announce(text, speak=False)
            show_info(self, "Tresor gesperrt", text)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Jede Taste und jeder Mausklick startet die Zeit bis zum automatischen Sperren neu."""
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress):
            self.last_input = time.time()
        return False

    # -- Ende -----------------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        QApplication.instance().removeEventFilter(self)
        self.lock_timer.stop()
        self.controller.wait()
        self.updater.shutdown()
        for task in (self.status_task, self.remote_task):
            if task is not None:
                task.cancel()
                task.wait(5000)
        if self._show_status in announcer.listeners:
            announcer.listeners.remove(self._show_status)
        from cockpit.ai import ollama
        ollama.server().stop()                      # nur ein selbst gestartetes Ollama
        super().closeEvent(event)


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

