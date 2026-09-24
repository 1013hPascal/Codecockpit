"""Ansagen für den Screenreader (Muster aus Chatbot und Tagebuch).

announce(text) sendet ein Accessibility-Ereignis, das NVDA vorliest, ohne dass der Fokus wechselt.
Ab Qt 6.8 gibt es dafür QAccessibleAnnouncementEvent. Jede Ansage steht zusätzlich im Log.

Neu im Cockpit: Die letzten 50 Meldungen werden gespeichert. Strg+Umschalt+M wiederholt die
letzte, Strg+Umschalt+L zeigt die Liste.

Wichtig (Test von Phase 3):
- Ein Fokuswechsel bricht in NVDA eine laufende Ansage ab. Nach einer Aktion springt der Fokus oft
  noch (Dialog schließt, Liste wird neu gefüllt). Deshalb wird jede Ansage erst gesendet, wenn sich
  der Fokus beruhigt hat (AFTER_FOCUS_MS), und zwar an das Steuerelement, das dann den Fokus hat.
- Ist das Cockpit gerade nicht vorne, wird die Ansage aufgehoben und beim Zurückkehren nachgeholt.
"""
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtGui import QAccessible, QAccessibleEvent, QGuiApplication
from PySide6.QtWidgets import QApplication

try:
    from PySide6.QtGui import QAccessibleAnnouncementEvent
except ImportError:                                    # Qt vor 6.8
    QAccessibleAnnouncementEvent = None

log = logging.getLogger(__name__)

MAX_MESSAGES = 50
AFTER_FOCUS_MS = 500              # Zeit, bis sich der Fokus nach einer Aktion beruhigt hat


@dataclass(frozen=True)
class Message:
    text: str
    urgent: bool = False
    time: datetime = field(default_factory=datetime.now)

    @property
    def label(self) -> str:
        """Für die Liste der Meldungen: Text zuerst, Uhrzeit am Ende."""
        return f"{self.text} {self.time:%H:%M}"


class Announcer:
    def __init__(self) -> None:
        self.target: QObject | None = None                 # Objekt, an dem das Ereignis hängt
        self.messages: deque[Message] = deque(maxlen=MAX_MESSAGES)
        self.listeners: list[Callable[[Message], None]] = []
        self.pending: list[Message] = []                   # für später, Cockpit war nicht vorne
        self._generation = 0                               # reset() verwirft wartende Ansagen
        self._watching_state = False

    @property
    def last_text(self) -> str:
        return self.messages[-1].text if self.messages else ""

    def announce(self, text: str, urgent: bool = False, speak: bool = True) -> None:
        """speak=False: nur in Statuszeile, Meldungsliste und Log, zum Beispiel wenn dieselbe
        Nachricht gleich als Meldungsfenster erscheint und sonst doppelt vorgelesen würde."""
        message = Message(text, urgent)
        self.messages.append(message)
        log.info("Ansage%s: %s", " (dringend)" if urgent else "", text)
        for listener in list(self.listeners):
            listener(message)
        if speak:
            self._send_later(text, urgent)

    def _send_later(self, text: str, urgent: bool) -> None:
        if QApplication.instance() is None:
            self._send(text, urgent)
            return
        generation = self._generation
        QTimer.singleShot(AFTER_FOCUS_MS, lambda: generation == self._generation
                          and self._send(text, urgent))

    def repeat_last(self) -> None:
        """Letzte Meldung noch einmal ansagen, ohne sie erneut zu speichern."""
        if not self.messages:
            self._send("Es gibt noch keine Meldung.", False)
            return
        self._send(self.messages[-1].text, False)

    def newest_first(self) -> list[Message]:
        return list(reversed(self.messages))

    def reset(self) -> None:
        self.target = None
        self.messages.clear()
        self.listeners.clear()
        self.pending.clear()
        self._generation += 1

    def current_target(self) -> QObject | None:
        """Steuerelement mit dem Fokus, sonst aktives Fenster, sonst das Hauptfenster."""
        if QApplication.instance() is None:
            return self.target
        return QApplication.focusWidget() or QApplication.activeWindow() or self.target

    @staticmethod
    def app_is_active() -> bool:
        app = QGuiApplication.instance()
        return app is None or app.applicationState() == Qt.ApplicationState.ApplicationActive

    def _watch_state(self) -> None:
        if self._watching_state or QGuiApplication.instance() is None:
            return
        QGuiApplication.instance().applicationStateChanged.connect(self._state_changed)
        self._watching_state = True

    def _state_changed(self, state) -> None:
        if state == Qt.ApplicationState.ApplicationActive and self.pending:
            waiting, self.pending = self.pending, []
            # kurz warten, bis NVDA das Fenster wieder als vorne kennt
            QTimer.singleShot(AFTER_FOCUS_MS, lambda: [self._send(m.text, m.urgent)
                                                       for m in waiting])

    def _send(self, text: str, urgent: bool) -> None:
        if self.target is None:
            return                                     # noch kein Hauptfenster: nur Log
        if not self.app_is_active():
            self.pending.append(Message(text, urgent))
            self._watch_state()
            return
        target = self.current_target()
        if target is None:
            return
        if QAccessibleAnnouncementEvent is not None:
            event = QAccessibleAnnouncementEvent(target, text)
            event.setPoliteness(QAccessible.AnnouncementPoliteness.Assertive if urgent
                                else QAccessible.AnnouncementPoliteness.Polite)
        else:
            event = QAccessibleEvent(target, QAccessible.Event.NameChanged)
        QAccessible.updateAccessibility(event)


announcer = Announcer()


def announce(text: str, urgent: bool = False, speak: bool = True) -> None:
    announcer.announce(text, urgent, speak)


def announce_after_focus(text: str, urgent: bool = False) -> None:
    """Früher nötig, heute gleichbedeutend mit announce: Jede Ansage wartet auf den Fokus."""
    announcer.announce(text, urgent)
