"""Hauptfenster: Menüleiste, Projektbaum, Aktionsliste und Statuszeile.

Tab-Kreis: Projektbaum, Aktionsliste, wieder Projektbaum. Umschalt+Tab führt aus der Aktionsliste
zurück auf den Eintrag im Baum, von dem man kam. Die Statuszeile ist kein Tab-Stopp. Ihre Meldungen
kommen als Ansage, Strg+Umschalt+M wiederholt die letzte.

Es erscheinen nur Menüpunkte, die schon funktionieren (ENTSCHEIDUNGEN.md).
"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
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
from cockpit.ui.asker import QtAsker
from cockpit.ui.error_dialog import show_error
from cockpit.ui.menus import AccessibleMenu
from cockpit.ui.messages_dialog import MessagesDialog
from cockpit.ui.project_tree import ProjectTree
from cockpit.ui.settings_dialog import SettingsDialog
from cockpit.ui.text_dialog import TextDialog

log = logging.getLogger(__name__)

SHORTCUTS = """\
Aufbau des Fensters
Links der Projektbaum, rechts die Aktionen.
Tab wechselt zwischen Projektbaum und Aktionen.
Umschalt+Tab führt aus den Aktionen zurück auf den Eintrag im Baum.

Projektbaum
Pfeil hoch und runter: zwischen den Einträgen wechseln
Pfeil rechts auf einem Projekt: ausklappen, alle anderen Projekte klappen zu
Pfeil rechts auf einem ausgeklappten Projekt: zum ersten Unterordner
Pfeil links auf einem Unterordner: zurück zum Projekt
Pfeil links auf einem ausgeklappten Projekt: zuklappen
Enter auf einem Projekt: aus- oder zuklappen
Enter auf Code oder Exe: wichtigste Aktion ausführen
Menütaste oder Umschalt+F10: Aktionen als Kontextmenü

Aktionen
Enter oder Leertaste: markierte Aktion ausführen
Bei nicht verfügbaren Aktionen wird der Grund angesagt.

Bereiche
Strg+1: Projektbaum
Strg+2: Aktionen
F6 und Umschalt+F6: nächster und vorheriger Bereich

Meldungen
Strg+Umschalt+M: letzte Meldung wiederholen
Strg+Umschalt+L: Liste der letzten Meldungen

Menüs
Alt+D: Datei
Alt+E: Einstellungen
Alt+H: Hilfe
Strg+R: Projekte neu einlesen
Strg+Q: Beenden
F1: dieses Fenster
"""


class MainWindow(QMainWindow):
    def __init__(self, services: Services, testdata: bool = False) -> None:
        super().__init__()
        self.services = services
        self.testdata = testdata
        self.asker = QtAsker(self)
        self.setWindowTitle(f"{APP_NAME} (Testdaten)" if testdata else APP_NAME)

        self.tree = ProjectTree()
        self.actions_list = ActionList()
        tree_label = QLabel("&Projekte:")
        tree_label.setBuddy(self.tree)
        actions_label = QLabel("A&ktionen:")
        actions_label.setBuddy(self.actions_list)

        left = QVBoxLayout()
        left.addWidget(tree_label)
        left.addWidget(self.tree, 1)
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
        QWidget.setTabOrder(self.tree, self.actions_list)
        QWidget.setTabOrder(self.actions_list, self.tree)
        self.areas = [self.tree, self.actions_list]

        self.tree.selectionModel().currentChanged.connect(lambda *_: self.refresh_actions())
        self.tree.defaultActionRequested.connect(self.run_default_action)
        self.tree.contextMenuRequested.connect(self.show_context_menu)
        self.actions_list.entryTriggered.connect(self.run_entry)

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

        settings_menu = AccessibleMenu("&Einstellungen", self)
        bar.addMenu(settings_menu)
        self._action(settings_menu, "&Grundeinstellungen …", self.open_settings)

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
        QShortcut(QKeySequence("Ctrl+1"), self, activated=self.focus_tree)
        QShortcut(QKeySequence("Ctrl+2"), self, activated=self.focus_actions)
        QShortcut(QKeySequence("F6"), self, activated=lambda: self.cycle_area(+1))
        QShortcut(QKeySequence("Shift+F6"), self, activated=lambda: self.cycle_area(-1))

    def _show_status(self, message) -> None:
        self.status_label.setText(message.text)

    # -- Start ----------------------------------------------------------------------------
    def initial_focus(self) -> None:
        self.tree.setFocus()

    def startup(self) -> None:
        """Nach dem Anzeigen: Projekte melden, Voraussetzungen prüfen."""
        number = len(self.services.projects.all())
        prefix = f"{APP_NAME} mit Testdaten bereit." if self.testdata else f"{APP_NAME} bereit."
        announce(f"{prefix} {count(number, 'Projekt', 'Projekte')}.")
        if git.find_git() is None:
            announce("Git wurde nicht gefunden. Die Anleitung steht im Menü Hilfe unter "
                     "Git installieren.", urgent=True)
        for problem in self.services.registry.load_errors:
            announce(problem, urgent=True)

    # -- Projekte -------------------------------------------------------------------------
    def reload_projects(self) -> list:
        """Hauptordner durchsuchen und Baum neu füllen. Gibt neu gefundene Projekte zurück."""
        root = Path(self.services.settings.load().projects_root)
        found = self.services.projects.scan(root) if root.is_dir() else []
        self.tree.set_projects(self.services.projects.all())
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
        target, project_id = self.tree.current_target()
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
        """Enter im Baum: wichtigste Aktion, sonst in die Aktionsliste springen."""
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
        self.tree.setFocus()
        if picked is not None:
            self.run_entry(chosen[picked])

    # -- Bereiche -------------------------------------------------------------------------
    def focus_tree(self) -> None:
        self.tree.setFocus()

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
        text = (f"{APP_NAME} Version {__version__}\n"
                "Verwaltet Code-Projekte auf GitHub und GitLab ohne Terminal.\n"
                "Barrierefrei entwickelt, vollständig per Tastatur bedienbar.\n"
                f"Daten: {paths.data_dir()}")
        TextDialog(f"Über {APP_NAME}", text, f"Über {APP_NAME}", self).exec()

    # -- Ende -----------------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        if self._show_status in announcer.listeners:
            announcer.listeners.remove(self._show_status)
        super().closeEvent(event)
