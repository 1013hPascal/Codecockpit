"""Bausteine der Repository-Dialoge: Hintergrundarbeit und Knopfzeile.
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QHBoxLayout, QWidget
from typing import Callable

from cockpit.ui.announcer import announce
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task


def _is_enter(event) -> bool:
    return event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return,
                                                                    Qt.Key.Key_Enter)


class _Worker:
    """Eine Hintergrund-Aufgabe zur Zeit für ein Fenster. Fehler kommen als Meldung im Fenster."""

    def __init__(self, dialog: QWidget, title: str) -> None:
        self.dialog = dialog
        self.title = title
        self.task: Task | None = None

    @property
    def busy(self) -> bool:
        return self.task is not None

    def run(self, work: Callable[[], object], done: Callable[[object], None],
            speak: str = "") -> None:
        if self.task is not None:
            announce("Das läuft schon.")
            return
        if speak:
            announce(speak)
        task = Task(lambda _task: work(), self.dialog)
        self.task = task

        def on_result(value) -> None:
            self.task = None
            done(value)

        def on_error(message: str, details: str) -> None:
            self.task = None
            announce(message, urgent=True)
            show_error(self.dialog, self.title, message, details)

        task.result.connect(on_result)
        task.error.connect(on_error)
        task.finished.connect(task.deleteLater)
        task.start()

    def wait(self) -> None:
        try:
            if self.task is not None and self.task.isRunning():
                self.task.cancel()
                self.task.wait(10000)          # nie einen laufenden Thread zerstören
        except RuntimeError:
            pass


def _buttons(*widgets) -> QHBoxLayout:
    row = QHBoxLayout()
    for widget in widgets:
        if widget is None:
            row.addStretch(1)
        else:
            row.addWidget(widget)
    return row


# Auch für andere Fenster mit Hintergrund-Arbeit (Branches, Phase 5f)
DialogWorker = _Worker


button_row = _buttons
