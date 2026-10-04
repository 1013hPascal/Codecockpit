"""Fortschritt beim Einrichten der Exe (Phase 10g, seit dem 03.10.2026 Schritt 3 von "Exe aus dem
Code erstellen …", siehe exe_wizard.py).

WorkDialog (Wunsch des Nutzers, 01.10.2026): Liste "Fortschritt" mit der Zeit seit dem Start und
jeder gelesenen Datei, dazu "Zurück" und "Abbrechen". Ist die Arbeit fertig, schließt es sich, und
der nächste Schritt kommt.
"""
from __future__ import annotations

import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core.projects import Project
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, label_for
from cockpit.ui.repo_dialogs import button_row
from cockpit.ui.tasks import Task

TITLE = "Exe aus dem Code erstellen"
_RUNNING: list[Task] = []           # abgebrochene Aufgaben, die noch auslaufen


class WorkDialog(FocusDialog):
    """Fortschritt, solange das Cockpit liest und die KI arbeitet. Die erste Zeile nennt die Zeit
    seit dem Start, darunter steht jeder Schritt. Neue Zeilen verschieben die Markierung nicht,
    damit NVDA nicht ständig vorliest. "Zurück" (back_requested) und "Abbrechen" brechen die
    Arbeit ab, Escape auch."""

    TICK_MS = 5000                     # so oft wird die Zeile mit der Zeit erneuert

    def __init__(self, project: Project, work, with_ai: bool,
                 parent: QWidget | None = None, what: str = "", title: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle(title or f"{TITLE}: {project.name}, läuft")
        self.result_value = None
        self.failure: tuple[str, str] | None = None
        self.back_requested = False
        self.closed = False
        self.what = what or ("Die KI liest den Code" if with_ai
                             else "Die Einrichtung wird geprüft")
        self.started = time.monotonic()
        self.list = QListWidget()
        label = label_for(self.list, "&Fortschritt:")
        self.list.setWordWrap(True)
        self.list.addItem(f"{self.what}. Gerade gestartet.")
        self.list.setCurrentRow(0)
        self.back_button = QPushButton("&Zurück")
        self.back_button.clicked.connect(self.go_back)
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(self.back_button, None, self.cancel_button))
        self.resize(700, 380)
        self.initial_focus_widget = self.list
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.task = Task(work, self)
        self.task.status.connect(self.add_line)
        self.task.result.connect(self.finished_ok)
        self.task.error.connect(self.failed)
        self.task.cancelled.connect(self.stopped)

    def exec(self) -> int:
        announce(f"{self.what}.")
        self.timer.start(self.TICK_MS)
        self.task.start()
        return super().exec()

    def seconds(self) -> int:
        return int(time.monotonic() - self.started)

    def tick(self) -> None:
        seconds = self.seconds()
        if seconds < 60:
            since = count(seconds, "Sekunde", "Sekunden")
        else:
            since = f"{count(seconds // 60, 'Minute', 'Minuten')} {seconds % 60} Sekunden"
        self.list.item(0).setText(f"{self.what}. Läuft seit {since}.")

    def add_line(self, text: str) -> None:
        if self.closed:
            return
        self.list.addItem(text)
        if text.startswith("An die KI gesendet"):
            announce("Der Code ist gelesen. Die KI arbeitet.")

    def finished_ok(self, value) -> None:
        if self.closed:
            return
        self.result_value = value
        self._stop_timer()
        self.accept()

    def failed(self, message: str, details: str) -> None:
        if self.closed:
            return
        self.failure = (message, details)
        self._stop_timer()
        super().reject()

    def stopped(self) -> None:
        if self.closed:
            return
        self._stop_timer()
        super().reject()

    def _stop_timer(self) -> None:
        self.timer.stop()

    def go_back(self) -> None:
        self.back_requested = True
        self.reject()

    def reject(self) -> None:
        """Abbrechen: Die KI bekommt das Signal zum Aufhören. Das Fenster schließt sofort. Die
        Aufgabe läuft am Hauptfenster aus, ihr Ergebnis wird nicht mehr gebraucht. So friert
        nichts ein, auch wenn die KI erst nach einer Weile aufhört."""
        self._stop_timer()
        self._release_task()
        super().reject()

    def _release_task(self) -> None:
        task = self.task
        if not task.isRunning():
            return
        task.cancel()
        self.closed = True                        # späte Meldungen der Aufgabe zählen nicht
        task.setParent(None)
        _RUNNING.append(task)                     # nie einen laufenden Thread zerstören
        task.finished.connect(lambda: _RUNNING.remove(task) if task in _RUNNING else None)

    def done(self, code: int) -> None:
        self._stop_timer()
        self._release_task()
        super().done(code)
