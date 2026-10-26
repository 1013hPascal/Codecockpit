"""Hintergrund-Aufgaben (Muster aus Chatbot und Tagebuch). Die Oberfläche blockiert nie.

Fehler gehen nie still verloren: Erwartete Fehler (CockpitError) kommen mit einfachem Text und
Details, unerwartete zusätzlich ins Log.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable

from PySide6.QtCore import QThread, Signal, Slot

from cockpit.core.errors import Cancelled, CockpitError

log = logging.getLogger(__name__)


class Task(QThread):
    """Führt fn(task) im Hintergrund aus. Ergebnisse kommen über Signale zurück."""
    status = Signal(str)
    result = Signal(object)
    error = Signal(str, str)          # einfacher Text, Details
    cancelled = Signal()

    _running: set["Task"] = set()          # alle laufenden Aufgaben, für wait_all

    def __init__(self, fn: Callable[["Task"], object], parent=None) -> None:
        super().__init__(parent)
        self._fn = fn
        self.cancel_event = threading.Event()
        self._delete_when_done = False

    def delete_when_done(self) -> None:
        """Nach dem Ende löschen. Statt finished mit deleteLater zu verbinden: "fertig" kommt
        kurz bevor der Thread wirklich zu Ende ist. Gelöscht wird erst danach (26.10.2026)."""
        self._delete_when_done = True

    def cancel(self) -> None:
        self.cancel_event.set()

    @classmethod
    def wait_all(cls, timeout_ms: int = 20000) -> None:
        """Alle laufenden Aufgaben abbrechen und auf sie warten, zum Beispiel bevor die
        Datenbank geschlossen wird (Überprüfung vom 08.10.2026: Eine Standabfrage lief noch, als
        ein Test die Datenbank schloss, und der nächste Test brach ab)."""
        from PySide6.QtCore import QCoreApplication
        app = QCoreApplication.instance()
        from shiboken6 import isValid
        for _round in range(10):
            for task in list(cls._running):
                if not isValid(task):
                    # Mit dem Fenster gelöscht, bevor "fertig" ankam (14.10.2026: brach sonst
                    # das Aufräumen nach einem Test ab)
                    cls._running.discard(task)
                    continue
                task.cancel()
                task.wait(timeout_ms)
            # Ergebnisse und "fertig" noch zustellen, solange die Empfänger leben. Dabei kann
            # eine wartende Abfrage starten, deshalb mehrere Runden.
            if app is not None:
                app.processEvents()
            if not cls._running:
                break

    def start(self, *args) -> None:
        Task._running.add(self)              # schon beim Starten, nicht erst im Thread
        # Früher ein Lambda: Es lief noch im Thread, kurz vor seinem Ende. wait_all wartete dann
        # nicht mehr auf ihn, und Qt brach den Testlauf ab ("QThreadStorage: entry 0 destroyed
        # before end of thread", 26.10.2026). Jetzt im Hauptthread, erst nach dem echten Ende.
        self.finished.connect(self._ended)
        super().start(*args)

    @Slot()
    def _ended(self) -> None:
        self.wait()                          # der Thread ist danach wirklich beendet
        Task._running.discard(self)
        if self._delete_when_done:
            self.deleteLater()

    def run(self) -> None:
        try:
            outcome = self._fn(self)
        except Cancelled:
            self.cancelled.emit()
        except CockpitError as exc:
            self.error.emit(exc.message, exc.details)
        except Exception as exc:                       # nie den Thread still sterben lassen
            log.exception("Unerwarteter Fehler im Hintergrund")
            self.error.emit("Unerwarteter Fehler.", repr(exc))
        else:
            if self.cancel_event.is_set():
                self.cancelled.emit()
            else:
                self.result.emit(outcome)
