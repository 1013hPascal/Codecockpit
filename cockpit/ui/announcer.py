"""Ansagen für den Screenreader (Muster aus Chatbot und Tagebuch).

announce(text) sendet ein Accessibility-Ereignis, das NVDA vorliest, ohne dass der Fokus wechselt.
Ab Qt 6.8 gibt es dafür QAccessibleAnnouncementEvent. Jede Ansage steht zusätzlich im Log.

Neu im Cockpit: Die letzten 50 Meldungen werden gespeichert. Strg+Umschalt+M wiederholt die
letzte, Strg+Umschalt+L zeigt die Liste.
"""
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from PySide6.QtCore import QObject
from PySide6.QtGui import QAccessible, QAccessibleEvent

try:
    from PySide6.QtGui import QAccessibleAnnouncementEvent
except ImportError:                                    # Qt vor 6.8
    QAccessibleAnnouncementEvent = None

log = logging.getLogger(__name__)

MAX_MESSAGES = 50


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

    @property
    def last_text(self) -> str:
        return self.messages[-1].text if self.messages else ""

    def announce(self, text: str, urgent: bool = False) -> None:
        message = Message(text, urgent)
        self.messages.append(message)
        log.info("Ansage%s: %s", " (dringend)" if urgent else "", text)
        for listener in list(self.listeners):
            listener(message)
        self._send(text, urgent)

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

    def _send(self, text: str, urgent: bool) -> None:
        target = self.target
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


def announce(text: str, urgent: bool = False) -> None:
    announcer.announce(text, urgent)
