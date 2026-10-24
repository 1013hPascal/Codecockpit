"""Menü Neuigkeiten und die Ansage nach dem Start (Wunsch des Nutzers vom 22.10.2026).

Menü "&Neuigkeiten" (Alt+N):
- Neuigkeiten seit dem letzten Start … (Strg+Umschalt+N), mit Feature Neuigkeiten
- Aktivität der Projekte …, mit Feature Aktivität
Abgefragt wird zusammen mit den Repositories (window_status.py), im Hintergrund. Danach kommt
einmal pro Sitzung eine kurze Ansage, wenn es Neues gibt. Ein Fenster öffnet sich nie von selbst,
der Fokus bleibt, wo er ist. Die Zahlen für die Aktivität holt das Cockpit einmal am Tag. Läuft es
über Mitternacht, fragt ein Zeitgeber stündlich, ob ein neuer Tag begonnen hat.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer

from cockpit.features.activity import activity
from cockpit.features.news import news
from cockpit.ui.announcer import announce
from cockpit.ui.menus import AccessibleMenu

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

DAY_CHECK_MS = 60 * 60 * 1000
NEWS_OFF = "Die Neuigkeiten sind ausgeschaltet. Sie schalten sie in der Feature-Verwaltung ein."
ACTIVITY_OFF = ("Die Aktivität ist ausgeschaltet. Sie schalten sie in der Feature-Verwaltung "
                "ein.")


class NewsMenu:
    def __init__(self, window: "MainWindow") -> None:
        self.window = window
        self.services = window.services
        self.menu: AccessibleMenu | None = None
        # Gelesen beim Start, gesetzt erst beim Beenden: So bleibt "seit dem letzten Start" gleich
        self.previous = news.last_seen(self.services.database)
        self.announced = False
        self.timer = QTimer(window)
        self.timer.setInterval(DAY_CHECK_MS)
        self.timer.timeout.connect(self.check_new_day)
        self.timer.start()

    def build(self) -> AccessibleMenu:
        menu = AccessibleMenu("&Neuigkeiten", self.window)
        self.act_news = self.window._action(menu, "&Neuigkeiten seit dem letzten Start …",
                                            self.open_news, "Ctrl+Shift+N")
        self.act_activity = self.window._action(menu, "&Aktivität der Projekte …",
                                                self.open_activity)
        self.menu = menu
        self.update_menu()
        return menu

    def update_menu(self) -> None:
        if self.menu is None:
            return
        news_on, activity_on = news.enabled(self.services), activity.enabled(self.services)
        self.act_news.setVisible(news_on)
        self.act_activity.setVisible(activity_on)
        self.menu.menuAction().setVisible(news_on or activity_on)

    # -- Nach dem Abfragen ---------------------------------------------------------------------
    def after_refresh(self) -> None:
        """Einmal pro Sitzung: kurz ansagen, was seit dem letzten Start neu ist."""
        if self.announced or not news.enabled(self.services):
            return
        self.announced = True
        if not self.previous:
            return                                   # erster Start: noch kein Vergleich
        text = news.summary(news.stored(self.services, self.previous), self.previous)
        if text:
            announce(text)

    def check_new_day(self) -> None:
        if activity.enabled(self.services) and activity.due(self.services.database):
            self.window.refresh_remote()

    def shutdown(self) -> None:
        self.timer.stop()
        if news.enabled(self.services):
            news.mark_seen(self.services.database)

    # -- Fenster -------------------------------------------------------------------------------
    def open_news(self) -> None:
        if not news.enabled(self.services):
            announce(NEWS_OFF)
            return
        from cockpit.ui.news_dialogs import NewsDialog
        dialog = NewsDialog(self.services, self.previous, self.window)
        dialog.exec()
        if dialog.chosen is not None:
            self.show_in_cockpit(dialog.chosen)

    def open_activity(self) -> None:
        if not activity.enabled(self.services):
            announce(ACTIVITY_OFF)
            return
        from cockpit.ui.news_dialogs import ActivityDialog
        dialog = ActivityDialog(self.services, self.window)
        dialog.exec()
        if dialog.discussion is not None:
            self.show_in_cockpit(dialog.discussion)

    def show_in_cockpit(self, entry: news.Entry) -> None:
        """Issues oder Pull Requests des Projekts öffnen, das Issue markiert."""
        project = self.services.projects.get(entry.project_id)
        if project is None:
            return
        controller = self.window.controller
        self.window.show_project(project.id)
        if entry.item.on_pull or entry.item.kind == news.PULL:
            from cockpit.ui.pull_request_flow import PullRequestRunner
            PullRequestRunner(controller, project).open_list()
        else:
            from cockpit.ui.issue_flow import IssueRunner
            IssueRunner(controller, project).open_list(select=entry.item.number)
