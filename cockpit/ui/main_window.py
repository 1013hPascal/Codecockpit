"""Hauptfenster: Menüleiste, Projektliste, Aktionsliste und Statuszeile.

Tab-Kreis: Projektliste, Aktionsliste, wieder Projektliste. Umschalt+Tab führt aus der
Aktionsliste zurück auf den Eintrag, von dem man kam. Die Statuszeile ist kein Tab-Stopp. Ihre Meldungen
kommen als Ansage, Strg+Umschalt+M wiederholt die letzte.

Es erscheinen nur Menüpunkte, die schon funktionieren (ENTSCHEIDUNGEN.md).
"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow, QMenu,
                               QVBoxLayout, QWidget)

from cockpit import APP_NAME, __version__
from cockpit.core import core_actions, git, paths
from cockpit.core.actions import ActionContext, ActionEntry, default_entry, entries_for
from cockpit.core.errors import CockpitError
from cockpit.core.services import Services
from cockpit.core.text import count
from cockpit.ui.announcer import announce, announcer
from cockpit.ui.action_list import ActionList
from cockpit.ui import vault_ui
from cockpit.ui.accounts_dialog import AccountsDialog
from cockpit.ui.asker import QtAsker
from cockpit.ui.error_dialog import show_error
from cockpit.ui.menus import AccessibleMenu
from cockpit.ui.messages_dialog import MessagesDialog
from cockpit.ui.project_list import ProjectList
from cockpit.ui.settings_dialog import SettingsDialog
from cockpit.ui.setup_wizard import SetupWizard
from cockpit.ui.text_dialog import TextDialog
from cockpit.ui.vault_settings_dialog import VaultSettingsDialog

log = logging.getLogger(__name__)

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
    "Konten, Alt+O",
    "Einstellungen, Alt+E",
    "Hilfe, Alt+H",
    "Projekte neu einlesen, Strg+R",
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

        self._build_menus()
        self._build_shortcuts()
        QWidget.setTabOrder(self.project_list, self.actions_list)
        QWidget.setTabOrder(self.actions_list, self.project_list)
        self.areas = [self.project_list, self.actions_list]

        self.project_list.currentRowChanged.connect(lambda _row: self.refresh_actions())
        self.project_list.defaultActionRequested.connect(self.run_default_action)
        self.project_list.contextMenuRequested.connect(self.show_context_menu)
        self.actions_list.entryTriggered.connect(self.run_entry)

        # Automatisches Sperren der Tresordatei nach Inaktivität (Tresor-Einstellungen)
        self.lock_timer = QTimer(self)
        self.lock_timer.setSingleShot(True)
        self.lock_timer.timeout.connect(self.auto_lock)
        QApplication.instance().installEventFilter(self)
        self.restart_lock_timer()

        self.reload_projects()

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
        self._action(file_menu, "Projekte &neu einlesen", self.rescan, "Ctrl+R")
        file_menu.addSeparator()
        self._action(file_menu, "&Beenden", self.close, "Ctrl+Q")

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
        help_menu.addSeparator()
        self._action(help_menu, f"Ü&ber {APP_NAME}", self.show_about)

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
        """Nach dem Anzeigen: Projekte melden, Voraussetzungen prüfen."""
        number = len(self.services.projects.all())
        prefix = f"{APP_NAME} mit Testdaten bereit." if self.testdata else f"{APP_NAME} bereit."
        announce(f"{prefix} {count(number, 'Projekt', 'Projekte')}.")
        if self.services.vault.needs_unlock and not self.services.vault.is_unlocked():
            announce("Der Tresor ist gesperrt. Entsperren im Menü Konten.")
        if git.find_git() is None:
            announce("Git wurde nicht gefunden. Die Anleitung steht im Menü Hilfe unter "
                     "Git installieren.", urgent=True)
        for problem in self.services.registry.load_errors:
            announce(problem, urgent=True)

    # -- Projekte -------------------------------------------------------------------------
    def reload_projects(self) -> list:
        """Hauptordner durchsuchen und Projektliste neu füllen. Gibt neu gefundene Projekte zurück."""
        root = Path(self.services.settings.load().projects_root)
        found = self.services.projects.scan(root) if root.is_dir() else []
        self.project_list.set_projects(self.services.projects.all())
        self.refresh_actions()
        return found

    def rescan(self) -> None:
        found = self.reload_projects()
        total = len(self.services.projects.all())
        text = f"Projekte neu eingelesen. {count(total, 'Projekt', 'Projekte')}."
        if found:
            text += f" Neu: {', '.join(p.name for p in found)}."
        announce(text)

    # -- Aktionen -------------------------------------------------------------------------
    def action_context(self) -> ActionContext:
        target, project_id = self.project_list.current_target()
        project = self.services.projects.get(project_id) if project_id is not None else None
        return ActionContext(self.services, project, target, announce=announce,
                             asker=self.asker)

    def current_entries(self) -> list[ActionEntry]:
        context = self.action_context()
        return entries_for(core_actions.all_actions(context), context)

    def refresh_actions(self) -> None:
        self.actions_list.set_entries(self.current_entries())

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
        self.refresh_actions()

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

    def show_git_guide(self) -> None:
        path = paths.resource_dir() / git.GUIDE
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            show_error(self, "Git installieren", "Die Anleitung wurde nicht gefunden.", str(exc))
            return
        TextDialog("Git installieren", text, "Anleitung Git installieren", self).exec()

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
        self.restart_lock_timer()

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
        if vault.needs_unlock and vault.is_unlocked() and minutes > 0:
            self.lock_timer.start(minutes * 60_000)
        else:
            self.lock_timer.stop()

    def auto_lock(self) -> None:
        if self.services.vault.needs_unlock and self.services.vault.is_unlocked():
            self.services.vault.lock()
            self.update_vault_actions()
            minutes = self.services.settings.load().auto_lock_minutes
            announce(f"Der Tresor wurde nach {count(minutes, 'Minute', 'Minuten')} ohne "
                     "Eingabe gesperrt.")

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Jede Taste und jeder Mausklick startet die Zeit bis zum automatischen Sperren neu."""
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress)                 and self.lock_timer.isActive():
            self.lock_timer.start()
        return False

    # -- Ende -----------------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        QApplication.instance().removeEventFilter(self)
        self.lock_timer.stop()
        if self._show_status in announcer.listeners:
            announcer.listeners.remove(self._show_status)
        super().closeEvent(event)
