"""Menüleiste und Tastenkürzel des Hauptfensters, dazu die Fenster, die die Menüs öffnen.

Teil von MainWindow (main_window.py).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import QMenu

from cockpit import APP_NAME, __version__
from cockpit.core import git, paths
from cockpit.ui import look
from cockpit.ui.announcer import announce, announcer
from cockpit.ui.error_dialog import show_error
from cockpit.ui.menus import AccessibleMenu
from cockpit.ui.messages_dialog import MessagesDialog
from cockpit.ui.settings_dialog import SettingsDialog
from cockpit.ui.setup_wizard import SetupWizard
from cockpit.ui.text_dialog import TextDialog


SHORTCUTS = [
    "Aufbau: links die Projektliste, rechts die Aktionen",
    "Zwischen Projektliste und Aktionen wechseln, Tab",
    "Aus den Aktionen zurück zum Eintrag in der Projektliste, Umschalt+Tab",
    "Projektliste",
    "Projekt ausklappen, Pfeil rechts, Leertaste oder Enter",
    "Im ausgeklappten Projekt zum ersten Unterordner, Pfeil rechts",
    "Projekt zuklappen, Leertaste oder Enter auf dem Projekt",
    "Zuklappen und zurück zum Projekt, Pfeil links auf einer Zeile darunter",
    "Wichtigste Aktion auf einer Zeile unter dem Projekt, Enter",
    "Aktionen als Kontextmenü, Menütaste oder Umschalt+F10",
    "Bei einem ausgeklappten Projekt steht im Kontextmenü zuerst die Schnellnavigation",
    "Filter über den Projekten, Enter auf der Zeile Anzeigen",
    "Repository herunterladen, das nur auf GitHub liegt, Enter",
    "Projektsammlung öffnen, Pfeil rechts, Leertaste oder Enter",
    "Projektsammlung schließen, Pfeil links oder Enter auf der Sammlung, Rücktaste überall darin",
    "In einer Sammlung vom Projekt zur Sammlung, Pfeil links",
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
    "Neuigkeiten, Alt+N",
    "KI, Alt+K",
    "Konten, Alt+O",
    "Einstellungen, Alt+E",
    "Hilfe, Alt+H",
    "Projekte neu einlesen und Stand abfragen, Strg+R",
    "Terminal im Ordner der markierten Zeile öffnen, Strg+T",
    "Beenden, Strg+Q",
    "Spracheingabe",
    "Diktieren starten und beenden, in einem Textfeld, Strg+D",
    "Diktieren abbrechen, Strg+Umschalt+D",
    "Hilfe mit Kurzanleitungen und KI fragen, F1",
    "Diese Liste, Strg+Umschalt+F1",
    "Befehl suchen, alle Aktionen und Menüs, Strg+K",
    "Paketübersicht, Menü Pakete, Strg+Umschalt+P",
    "Neuigkeiten seit dem letzten Start, Strg+Umschalt+N",
    "Tasten für das Element mit dem Fokus ansagen, Strg+F1",
    "KI-Hilfe, Fragen zur Bedienung, Umschalt+F1",
    "In Listen wie dieser: Zeile kopieren, Strg+C",
]


class MenuMixin:
    """Menüs und Tastenkürzel."""

    # -- Aufbau ---------------------------------------------------------------------------
    def _action(self, menu: QMenu, text: str, slot, shortcut: str | None = None) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
            self.addAction(action)                     # Kürzel gelten auch bei geschlossenem Menü
        action.triggered.connect(lambda checked=False: slot())
        look.menu_icon(action)                         # nur für das Auge (PLAN-OPTIK.md)
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
        # Aufräumrunde vom 20.10.2026: Terminal im Ordner der markierten Zeile
        self._action(file_menu, "&Terminal hier öffnen", self.open_terminal_here, "Ctrl+T")
        file_menu.addSeparator()
        self._action(file_menu, "&Beenden", self.close, "Ctrl+Q")

        features_menu = AccessibleMenu("&Features", self)
        bar.addMenu(features_menu)
        self._action(features_menu, "Feature-&Verwaltung …", self.open_features)

        # Wunsch des Nutzers vom 21.10.2026: Paketübersicht. Alt+P bleibt für "Projekte".
        from cockpit.ui.package_flow import PackageMenu
        self.packages = PackageMenu(self)
        bar.addMenu(self.packages.build())

        ai_menu = AccessibleMenu("&KI", self)
        bar.addMenu(ai_menu)
        # Wunsch des Nutzers (07.10.2026): oben steht, ob die KI auf den Rechner eingestellt ist
        from cockpit.ui.ai_tuning_ui import Calibrator
        self.calibrator = Calibrator(self.services, self)
        self.act_ai_tuning = self._action(ai_menu, self.calibrator.menu_text,
                                          self.open_ai_tuning)
        ai_menu.aboutToShow.connect(
            lambda: self.act_ai_tuning.setText(self.calibrator.menu_text))
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

        # Wunsch des Nutzers vom 22.10.2026: Neuigkeiten seit dem letzten Start und Aktivität
        from cockpit.ui.news_flow import NewsMenu
        self.news = NewsMenu(self)
        bar.addMenu(self.news.build())

        help_menu = AccessibleMenu("&Hilfe", self)
        bar.addMenu(help_menu)
        # Wunsch des Nutzers (07.10.2026): F1 öffnet die Hilfe mit den Kurzanleitungen
        self._action(help_menu, "Hilfe und &Kurzanleitungen …", self.open_help, "F1")
        self._action(help_menu, "&Tastenkürzel", self.show_shortcuts, "Ctrl+Shift+F1")
        self._action(help_menu, "KI-&Hilfe …", self.open_ai_help, "Shift+F1")
        # Wunsch des Nutzers (07.10.2026): Befehle suchen und Tasten ansagen lassen
        self._action(help_menu, "Befehl &suchen …", self.search_commands, "Ctrl+K")
        self._action(help_menu, "Tasten hier a&nsagen", self.announce_keys, "Ctrl+F1")
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

    def open_ai_help(self) -> None:
        """Fragen zur Bedienung (Konzept 10.17, Teilschritt 8e)."""
        from cockpit.ui.ai_help_dialog import open_help
        open_help(self)

    def open_ai_tuning(self) -> None:
        """Erklärung der Messung, Art und Stufe von +3 bis -3 (07.10.2026)."""
        from cockpit.ui.ai_tuning_ui import AITuningDialog
        calibrator = self.calibrator
        name = calibrator.name
        if not name:
            tool = self.services.text_tool(None)
            name = self.services.ai_tools.label(tool, mark_default=False) if tool else ""
        AITuningDialog(self.services, name, calibrator.state, self).exec()

    def start_ai_tuning(self) -> None:
        """Nach dem Start, nicht in startup(): Starttest der KI im Hintergrund (07.10.2026)."""
        if not self.testdata:
            self.calibrator.start()

    def open_ai_manager(self) -> None:
        """KI-Werkzeuge für Text, lokal oder extern (Konzept 11.1)."""
        from cockpit.ui.ai_dialogs import AIManagerDialog
        AIManagerDialog(self.services, self).exec()
        self.services.forget_platforms()
        self.refresh_actions(keep_selection=True)

    def open_ai_features(self) -> None:
        """Feature-Verwaltung, markiert beim ersten KI-Feature (Konzept 11.1)."""
        from cockpit.core.features.manifest import AI_SERVICES
        ai_features = [m.id for m in self.services.registry.all()
                       if set(AI_SERVICES) & set(m.requires_services)]
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
            self.packages.update_menu()
            self.news.update_menu()

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

    # -- Menüs ----------------------------------------------------------------------------
    def open_settings(self) -> None:
        old_root = self.services.settings.load().projects_root
        dialog = SettingsDialog(self.services.settings, self)
        if dialog.exec():
            announce("Grundeinstellungen gespeichert.")
            if self.services.settings.load().projects_root != old_root:
                self.rescan()

    def open_help(self) -> None:
        """Hilfefenster, nicht modal. Ein Fenster für die ganze Sitzung."""
        from cockpit.ui.help_window import HelpWindow, area_of
        if getattr(self, "help_window", None) is None:
            self.help_window = HelpWindow(self)
        self.help_window.open_for(area_of(self))

    def search_commands(self) -> None:
        from cockpit.ui.quick_nav import search_commands
        search_commands(self)

    def announce_keys(self) -> None:
        from cockpit.ui.quick_nav import announce_hint
        announce_hint(self)

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

    def open_wizard(self) -> None:
        SetupWizard(self.services, self).exec()
        self.update_vault_actions()
        self.reload_projects()
