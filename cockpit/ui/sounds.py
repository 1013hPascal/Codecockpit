"""Töne beim Hoch- und Herunterladen (Wunsch des Nutzers vom 07.10.2026).

Ein kurzer Windows-Ton beim Start, alle 3 Sekunden ein leiser Ton, solange es läuft, und am Ende
der Ton für fertig oder für einen Fehler. So hört man, dass etwas passiert, auch wenn das
Cockpit gerade nicht vorne ist. Abschalten: Grundeinstellungen, „Töne beim Hoch- und
Herunterladen“. Es sind die Systemklänge von Windows (winsound), keine neue Bibliothek.
"""
from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QObject, QTimer

log = logging.getLogger(__name__)

TICK_MS = 3_000                 # Antwort des Nutzers vom 07.10.2026: alle 3 Sekunden
START, TICK, DONE, ERROR = "start", "tick", "done", "error"


def _windows_sound(kind: str) -> None:
    import winsound
    flags = {START: winsound.MB_ICONASTERISK, TICK: winsound.MB_OK,
             DONE: winsound.MB_ICONASTERISK, ERROR: winsound.MB_ICONHAND}
    if kind == TICK:
        winsound.Beep(880, 60)                       # leise und kurz, kein Systemklang
        return
    winsound.MessageBeep(flags[kind])


def _play(kind: str) -> None:
    try:
        if sys.platform == "win32":
            _windows_sound(kind)
        else:
            from PySide6.QtWidgets import QApplication
            QApplication.beep()
    except Exception as exc:                          # noqa: BLE001 (Ton ist nur Zusatz)
        log.warning("Ton nicht abgespielt: %r", exc)


play = _play                                          # in Tests ersetzbar


class TransferSound(QObject):
    """Begleitet eine Übertragung: start(), dann finish(ok)."""

    def __init__(self, enabled: bool, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.enabled = enabled
        self.timer = QTimer(self)
        self.timer.setInterval(TICK_MS)
        self.timer.timeout.connect(lambda: play(TICK))

    def start(self) -> None:
        if self.enabled:
            play(START)
            self.timer.start()

    def stop(self) -> None:
        """Abgebrochen: ohne Ton aufhören."""
        self.timer.stop()

    def finish(self, ok: bool) -> None:
        if not self.enabled or not self.timer.isActive():
            return
        self.timer.stop()
        play(DONE if ok else ERROR)
