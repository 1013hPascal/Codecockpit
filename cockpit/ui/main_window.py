"""Hauptfenster: Menüleiste, Projektliste, Aktionsliste und Statuszeile.

Tab-Kreis: Projektliste, Aktionsliste, wieder Projektliste. Umschalt+Tab führt aus der
Aktionsliste zurück auf den Eintrag, von dem man kam. Die Statuszeile ist kein Tab-Stopp. Ihre Meldungen
kommen als Ansage, Strg+Umschalt+M wiederholt die letzte.

Es erscheinen nur Menüpunkte, die schon funktionieren (ENTSCHEIDUNGEN.md).
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from cockpit import APP_NAME
from cockpit.core import backups, git
from cockpit.core.services import Services
from cockpit.core.text import count
from cockpit.ui.announcer import announce, announcer
from cockpit.ui.action_list import ActionList
from cockpit.ui.asker import QtAsker
from cockpit.ui.project_actions import ProjectController
from cockpit.ui.project_list import ProjectList
from cockpit.ui.tasks import Task
# Aufgeteilt am 22.10.2026: Menüs, Aktionen, Stand der Projekte und Tresor stehen in eigenen
# Dateien. MainWindow setzt sie zusammen.
from cockpit.ui.window_menus import MenuMixin, SHORTCUTS  # noqa: F401
from cockpit.ui.window_actions import ActionsMixin, SHOW_KEY  # noqa: F401
from cockpit.ui.window_status import StatusMixin, refresh_pull_requests  # noqa: F401
from cockpit.ui.window_vault import VaultMixin

log = logging.getLogger(__name__)

LOCK_CHECK_MS = 15_000


class MainWindow(MenuMixin, ActionsMixin, StatusMixin, VaultMixin, QMainWindow):
    def __init__(self, services: Services, testdata: bool = False) -> None:
        super().__init__()
        self.services = services
        self.testdata = testdata
        self.asker = QtAsker(self)
        # Leiser Warteton, solange die KI schreibt (Wunsch des Nutzers vom 14.10.2026)
        from cockpit.ui import sounds
        from cockpit.ui.sounds import AISound
        sounds.configure_from(services.settings.load())   # Auswahl der Signaltöne (24.10.2026)
        self.ai_sound = AISound(lambda: services.settings.load().ai_sounds, self)
        self.setWindowTitle(f"{APP_NAME} (Testdaten)" if testdata else APP_NAME)

        self.project_list = ProjectList()
        self.controller = ProjectController(self)
        self.status_task: Task | None = None
        self.status_queue: set[int] | None = None       # wartet auf den laufenden Abruf
        self.status_queue_all = False
        self.status_callbacks: list[Callable[[], None]] = []
        self.remote_task: Task | None = None
        self.actions_list = ActionList()
        # Die Aktionen sind schmaler (PLAN-OPTIK.md): lange Einträge umbrechen statt abschneiden
        self.actions_list.setWordWrap(True)
        self.actions_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        list_label = QLabel("&Projekte:")
        list_label.setBuddy(self.project_list)
        actions_label = QLabel("A&ktionen:")
        actions_label.setBuddy(self.actions_list)
        # Feature Erklärungen (25.10.2026): Zeilen ganz oben, Einträge in Menüs und Fenstern
        from cockpit.ui.explanations import Explainer
        self.explainer = Explainer(self)
        self.project_list.set_explanation(self.explainer.project_row())
        self.project_list.explanationRequested.connect(self.explainer.show_project_list)
        self.actions_list.explanationRequested.connect(lambda: self.explainer.show_actions())

        left = QVBoxLayout()
        left.addWidget(list_label)
        left.addWidget(self.project_list, 1)
        right = QVBoxLayout()
        right.addWidget(actions_label)
        right.addWidget(self.actions_list, 1)
        # Stand der markierten Zeile, nur für das Auge, kein Tab-Stopp (PLAN-OPTIK.md, Schritt 2)
        from cockpit.ui.state_panel import StatePanel
        self.state_panel = StatePanel(self.project_list)
        right.addWidget(self.state_panel)
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.addLayout(left, 2)                      # Aktionen schmaler, ein Drittel
        layout.addLayout(right, 1)
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
        from cockpit.ui.dictation import Dictation
        self.dictation = Dictation(self)            # Strg+D in jedem Textfeld (8d)
        self._build_menus()
        self._build_shortcuts()
        QWidget.setTabOrder(self.project_list, self.actions_list)
        QWidget.setTabOrder(self.actions_list, self.project_list)
        self.areas = [self.project_list, self.actions_list]

        self.project_list.currentRowChanged.connect(lambda _row: self.refresh_actions())
        self.project_list.currentRowChanged.connect(lambda _row: self._update_hint())
        self.actions_list.setToolTip("Enter oder Leertaste führt die Aktion aus, Umschalt+Tab "
                                     "führt zurück zur Projektliste")
        self.project_list.defaultActionRequested.connect(self.run_default_action)
        self.project_list.contextMenuRequested.connect(self.show_context_menu)
        self.actions_list.entryTriggered.connect(self.run_entry)
        # Auswahl beim Repository je Projekt merken (06.10.2026)
        saved = services.database.get_value(SHOW_KEY, {}) or {}
        self.project_list.set_shows({int(k): v for k, v in saved.items() if str(k).isdigit()})
        self.project_list.showChanged.connect(self._save_show)
        # Filter "Anzeigen:" über den Projekten merken (07.10.2026), gilt ab dem ersten Füllen
        from cockpit.core import list_filter
        self.project_list.restore_filter(
            services.database.get_value(list_filter.FILTER_KEY, list_filter.ALL))
        self.project_list.filterChanged.connect(
            lambda kind: (services.database.set_value(list_filter.FILTER_KEY, kind),
                          self.refresh_actions(keep_selection=True)))

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
        if self.remote_task is None:
            self.news.after_refresh()            # ohne Abfrage: aus der Datenbank (22.10.2026)

    def offer_folder_rename(self) -> None:
        """Nach dem Start, nicht in startup(): Ordner Code und Exe umbenennen (06.10.2026)."""
        if not self.testdata:
            self.controller.folder_renamer.offer()

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

    def _update_hint(self) -> None:
        """Tooltip der Projektliste: welche Tasten auf der markierten Zeile etwas tun."""
        from cockpit.ui.quick_nav import key_hint
        self.project_list.setToolTip(key_hint(self.project_list, self))

    def refresh_explanations(self) -> None:
        """Nach dem Ein- oder Ausschalten von Erklärungen: Zeilen oben neu setzen."""
        self.project_list.set_explanation(self.explainer.project_row())
        self.refresh_actions(keep_selection=True)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Jede Taste und jeder Mausklick startet die Zeit bis zum automatischen Sperren neu."""
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress):
            self.last_input = time.time()
        return False

    # -- Ende -----------------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        QApplication.instance().removeEventFilter(self)
        self.explainer.shutdown()
        self.lock_timer.stop()
        self.controller.wait()
        self.calibrator.stop()
        if getattr(self, "help_window", None) is not None:
            self.help_window.close()             # wartet auf eine laufende Frage an die KI
        self.updater.shutdown()
        self.dictation.shutdown()
        self.news.shutdown()                        # merkt sich den Zeitpunkt (22.10.2026)
        for task in (self.status_task, self.remote_task):
            if task is not None:
                task.cancel()
                task.wait(5000)
        if self._show_status in announcer.listeners:
            announcer.listeners.remove(self._show_status)
        from cockpit.ai import ollama
        ollama.server().stop()                      # nur ein selbst gestartetes Ollama
        super().closeEvent(event)


