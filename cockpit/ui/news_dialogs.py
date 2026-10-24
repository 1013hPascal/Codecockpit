"""Fenster "Neuigkeiten" und "Aktivität" (Wunsch des Nutzers vom 22.10.2026).

NewsDialog: oben der Zeitraum, darunter die Liste. Jede Zeile beginnt mit dem Projekt, zum
Beispiel "Tagebuch: neuer Kommentar zu Issue 12, von anna, gestern 14:05". Enter zeigt das Issue
oder den Pull Request im Cockpit, sonst öffnet es den Browser. Tab führt zu den Knöpfen.
Dasselbe Fenster zeigt für ein Projekt "Kommentare und Issues".
ActivityDialog: oben der Zeitraum, darunter die Projekte mit ihren Zahlen. Enter zeigt die
Einzelheiten, Tab führt zu "Kommentare und Issues …".
Beide Fenster lesen nur aus der Datenbank. Sie fragen GitHub nicht selbst.
"""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core.text import count
from cockpit.features.activity import activity
from cockpit.features.news import news
from cockpit.ui import browser_login_dialog
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, label_for, make_copyable, name_widget
from cockpit.ui.repo_dialog_parts import _is_enter, button_row
from cockpit.ui.row_delegate import RowDelegate
from cockpit.ui.text_dialog import TextDialog

NO_NEWS = "Keine Neuigkeiten."


class NewsDialog(FocusDialog):
    """chosen: der Eintrag für "Im Cockpit zeigen", nach dem Schließen auszuführen."""

    def __init__(self, services, previous: str | None, parent: QWidget | None = None,
                 project=None, period: str = news.SINCE_START) -> None:
        """previous: Zeitpunkt des letzten Starts. project: nur Kommentare und Issues dieses
        Projekts."""
        super().__init__(parent)
        self.services = services
        self.previous = previous
        self.project = project
        self.entries: list[news.Entry] = []
        self.chosen: news.Entry | None = None
        self.period = QComboBox()
        period_label = label_for(self.period, "&Zeitraum:")
        self.periods = news.PERIODS if project is None else news.PERIODS[1:]
        self.period.addItems([text for _, text in self.periods])
        keys = [key for key, _ in self.periods]
        self.period.setCurrentIndex(keys.index(period) if period in keys else 0)
        self.period.currentIndexChanged.connect(lambda _index: self.fill())
        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.setItemDelegate(RowDelegate(self.list, head_sep=": "))   # nur für das Auge
        self.list_name = "Neuigkeiten" if project is None else "Kommentare und Issues"
        list_label = label_for(self.list, f"&{self.list_name}:")
        make_copyable(self.list)
        self.list.installEventFilter(self)
        self.list.currentRowChanged.connect(lambda _row: self.update_buttons())
        self.browser_button = QPushButton("Im &Browser öffnen")
        self.browser_button.clicked.connect(self.open_browser)
        self.cockpit_button = QPushButton("Im &Cockpit zeigen")
        self.cockpit_button.clicked.connect(self.show_in_cockpit)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(period_label)
        layout.addWidget(self.period)
        layout.addWidget(list_label)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(self.browser_button, self.cockpit_button, None, close))
        self.setTabOrder(self.period, self.list)
        self.resize(820, 480)
        self.initial_focus_widget = self.list
        self.fill()

    @property
    def period_key(self) -> str:
        return self.periods[self.period.currentIndex()][0]

    def fill(self) -> None:
        since = news.since_for(self.period_key, self.previous)
        if self.project is None:
            self.entries = news.stored(self.services, since)
            title = f"Neuigkeiten: {len(self.entries)}"
        else:
            self.entries = news.stored(self.services, since, self.project.id, news.DISCUSSION)
            title = f"Kommentare und Issues von {self.project.name}: {len(self.entries)}"
        self.setWindowTitle(f"{title}, {self.periods[self.period.currentIndex()][1]}")
        self.list.clear()
        self.list.addItems([news.line(e) for e in self.entries] or [NO_NEWS])
        self.list.setCurrentRow(0)
        name_widget(self.list, self.list_name)
        self.update_buttons()

    def current(self, quiet: bool = False) -> news.Entry | None:
        row = self.list.currentRow()
        if 0 <= row < len(self.entries):
            return self.entries[row]
        if not quiet:
            announce(NO_NEWS)
        return None

    def update_buttons(self) -> None:
        entry = self.current(quiet=True)
        self.browser_button.setVisible(entry is not None and bool(entry.item.url))
        self.cockpit_button.setVisible(entry is not None and news.shows_in_cockpit(entry.item))

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            entry = self.current()
            if entry is not None and news.shows_in_cockpit(entry.item):
                self.show_in_cockpit()
            elif entry is not None:
                self.open_browser()
            return True
        return super().eventFilter(watched, event)

    def open_browser(self) -> None:
        entry = self.current()
        if entry is not None and entry.item.url:
            browser_login_dialog.open_url(entry.item.url)
            announce("Wird im Browser geöffnet.")

    def show_in_cockpit(self) -> None:
        entry = self.current()
        if entry is not None and news.shows_in_cockpit(entry.item):
            self.chosen = entry
            self.accept()


class ActivityDialog(FocusDialog):
    """Zahlen aller Projekte mit Verbindung zur Plattform. discussion: das Projekt für
    "Kommentare und Issues", nach dem Schließen zu öffnen."""

    def __init__(self, services, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.projects = [p for p in services.projects.all() if p.remote is not None
                         or activity.snapshot(services.database, p.id) is not None]
        self.discussion = None
        self.period = QComboBox()
        period_label = label_for(self.period, "&Zeitraum:")
        self.period.addItems([text for _, text in activity.PERIODS])
        self.period.currentIndexChanged.connect(lambda _index: self.fill())
        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.setItemDelegate(RowDelegate(self.list, head_sep=": "))   # nur für das Auge
        list_label = label_for(self.list, "&Projekte:")
        make_copyable(self.list)
        self.list.installEventFilter(self)
        self.details_button = QPushButton("&Einzelheiten …")
        self.details_button.clicked.connect(self.show_details)
        self.discussion_button = QPushButton("&Kommentare und Issues …")
        self.discussion_button.clicked.connect(self.show_discussion)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(period_label)
        layout.addWidget(self.period)
        layout.addWidget(list_label)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(self.discussion_button, self.details_button, None, close))
        self.setTabOrder(self.period, self.list)
        self.setTabOrder(self.list, self.discussion_button)
        self.resize(820, 480)
        self.initial_focus_widget = self.list
        self.fill()

    @property
    def period_key(self) -> str:
        return activity.PERIODS[self.period.currentIndex()][0]

    def fill(self) -> None:
        row = max(0, self.list.currentRow())
        database = self.services.database
        self.setWindowTitle(f"Aktivität: {count(len(self.projects), 'Projekt', 'Projekte')}, "
                            f"{activity.PERIODS[self.period.currentIndex()][1]}")
        self.list.clear()
        self.list.addItems([activity.project_line(database, p, self.period_key)
                            for p in self.projects]
                           or ["Kein Projekt ist mit einer Plattform verbunden."])
        self.list.setCurrentRow(min(row, self.list.count() - 1))
        name_widget(self.list, "Projekte")
        for button in (self.details_button, self.discussion_button):
            button.setVisible(bool(self.projects))

    def current(self):
        row = self.list.currentRow()
        if 0 <= row < len(self.projects):
            return self.projects[row]
        announce("Kein Projekt ist mit einer Plattform verbunden.")
        return None

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            self.show_details()
            return True
        return super().eventFilter(watched, event)

    def show_details(self) -> None:
        project = self.current()
        if project is None:
            return
        lines = activity.details(self.services.database, project, self.period_key)
        TextDialog(f"Aktivität von {project.name}", lines, "Einzelheiten", self).exec()

    def show_discussion(self) -> None:
        project = self.current()
        if project is None:
            return
        dialog = NewsDialog(self.services, None, self, project, news.MONTH)
        dialog.exec()
        if dialog.chosen is not None:
            self.discussion = dialog.chosen
            self.accept()
