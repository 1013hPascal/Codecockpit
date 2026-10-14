"""Töne beim Hoch- und Herunterladen (Wunsch des Nutzers vom 07.10.2026) und während die KI
schreibt (Wunsch des Nutzers vom 14.10.2026).

Ein kurzer Windows-Ton beim Start, alle 3 Sekunden ein leiser Warteton, solange es läuft, und am
Ende der Ton für fertig oder für einen Fehler. So hört man, dass etwas passiert, auch wenn das
Cockpit gerade nicht vorne ist. Abschalten: Grundeinstellungen, „Töne beim Hoch- und
Herunterladen“ und „Töne, während die KI schreibt“.

Wunsch des Nutzers vom 14.10.2026:
- Töne nur, solange der Nutzer nichts tun muss. Stellt ein Ablauf eine Frage (welcher Branch,
  kleine oder große Änderung, README-Vorschlag übernehmen), schweigt der Warteton (user_turn).
- Ein angenehmerer Warteton statt des Pieptons: ein weicher, leiser Klang. Das Cockpit erzeugt
  ihn selbst als WAV-Datei, ohne neue Bibliothek und ohne fremde Lizenz. Beim Hochladen ein Ton,
  während die KI schreibt zwei, so hört man den Unterschied.
"""
from __future__ import annotations

import logging
import math
import struct
import sys
import time
import wave
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

from PySide6.QtCore import QObject, QTimer

log = logging.getLogger(__name__)

TICK_MS = 3_000                 # Antwort des Nutzers vom 07.10.2026: alle 3 Sekunden
AI_FIRST_MS = 1_500             # kurze Antworten der KI ohne Ton
START, TICK, AI_TICK, DONE, ERROR = "start", "tick", "ai_tick", "done", "error"

# -- Wartet das Cockpit auf den Nutzer? ---------------------------------------------------------
_user_turns = 0
_transfers = 0


@contextmanager
def user_turn() -> Iterator[None]:
    """Solange eine Frage an den Nutzer offen ist: kein Warteton."""
    global _user_turns
    _user_turns += 1
    try:
        yield
    finally:
        _user_turns -= 1


def waiting_for_user() -> bool:
    return _user_turns > 0


# -- Klänge ---------------------------------------------------------------------------------------
RATE = 22050


def _chime(notes: list[tuple[float, float]], volume: float = 0.16) -> bytes:
    """Weiche Töne wie ein leises Glockenspiel: Sinus mit etwas Oberton, sanfter Anfang und
    langsames Ausklingen. notes: (Frequenz, Beginn in Sekunden)."""
    length = max(start for _f, start in notes) + 0.45
    samples = [0.0] * int(RATE * length)
    for frequency, start in notes:
        offset = int(RATE * start)
        for n in range(int(RATE * 0.45)):
            t = n / RATE
            envelope = min(1.0, t / 0.012) * math.exp(-t * 9)
            value = math.sin(2 * math.pi * frequency * t) + 0.25 * math.sin(
                2 * math.pi * frequency * 2 * t) * math.exp(-t * 14)
            samples[offset + n] += volume * envelope * value
    return b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples)


SOUNDS: dict[str, Callable[[], bytes]] = {
    TICK: lambda: _chime([(659.3, 0.0)]),                         # e'' allein
    AI_TICK: lambda: _chime([(523.3, 0.0), (659.3, 0.16)], 0.13),  # c'' und e'', leiser
}


def sound_file(kind: str) -> Path:
    """Die WAV-Datei des Klangs, beim ersten Mal erzeugt."""
    from cockpit.core import paths
    path = paths.cache_dir() / "sounds" / f"{kind}.wav"
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(RATE)
            out.writeframes(SOUNDS[kind]())
    return path


def _windows_sound(kind: str) -> None:
    import winsound
    if kind in SOUNDS:
        winsound.PlaySound(str(sound_file(kind)), winsound.SND_FILENAME | winsound.SND_ASYNC
                           | winsound.SND_NODEFAULT)
        return
    flags = {START: winsound.MB_ICONASTERISK, DONE: winsound.MB_ICONASTERISK,
             ERROR: winsound.MB_ICONHAND}
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
        self.timer.timeout.connect(self.tick)

    def tick(self) -> None:
        if not waiting_for_user():
            play(TICK)

    def start(self) -> None:
        global _transfers
        if self.enabled:
            play(START)
            self.timer.start()
            _transfers += 1

    def _end(self) -> None:
        global _transfers
        if self.timer.isActive():
            self.timer.stop()
            _transfers -= 1

    def stop(self) -> None:
        """Abgebrochen: ohne Ton aufhören."""
        self._end()

    def finish(self, ok: bool) -> None:
        if not self.enabled or not self.timer.isActive():
            return
        self._end()
        play(DONE if ok else ERROR)


class AISound(QObject):
    """Leiser Warteton, solange die KI schreibt. Eine für das ganze Programm, im Hauptfenster.
    Schaut zweimal pro Sekunde nach, ob eine Anfrage läuft (cockpit.core.activity). Kein Ton bei
    kurzen Antworten, während einer Frage an den Nutzer und während einer Übertragung, die schon
    ihren eigenen Ton hat."""

    def __init__(self, enabled: Callable[[], bool], parent: QObject | None = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        super().__init__(parent)
        self.enabled = enabled
        self.clock = clock
        self.since: float | None = None
        self.last = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.check)
        self.timer.start()

    def check(self) -> None:
        from cockpit.core import activity
        if not activity.ai_busy():
            self.since = None
            return
        now = self.clock()
        if self.since is None:
            self.since, self.last = now, now - TICK_MS / 1000 + AI_FIRST_MS / 1000
        if now - self.last < TICK_MS / 1000 or waiting_for_user() or _transfers:
            return
        self.last = now
        try:
            wanted = self.enabled()
        except Exception:                              # noqa: BLE001 (Ton ist nur Zusatz)
            wanted = True
        if wanted:
            play(AI_TICK)
