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
from dataclasses import dataclass
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


def _chime(notes: list[tuple[float, float]], volume: float = 0.16, decay: float = 9.0,
           ring: float = 0.45, overtone: float = 0.25) -> bytes:
    """Weiche Töne wie ein leises Glockenspiel: Sinus mit etwas Oberton, sanfter Anfang und
    langsames Ausklingen. notes: (Frequenz, Beginn in Sekunden). Gleicher Beginn: Akkord.
    decay: wie schnell ein Ton verklingt, groß wie bei Holz, klein wie bei einem Gong."""
    length = max(start for _f, start in notes) + ring
    samples = [0.0] * int(RATE * length)
    for frequency, start in notes:
        offset = int(RATE * start)
        for n in range(int(RATE * ring)):
            t = n / RATE
            envelope = min(1.0, t / 0.012) * math.exp(-t * decay)
            value = math.sin(2 * math.pi * frequency * t) + overtone * math.sin(
                2 * math.pi * frequency * 2 * t) * math.exp(-t * (decay + 5))
            samples[offset + n] += volume * envelope * value
    return b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples)


# -- Auswahl der Töne (Wunsch des Nutzers vom 24.10.2026) -----------------------------------------
# Menü Einstellungen, Signaltöne: je Art mehrere Töne zur Wahl. Jede Art hat ihre eigenen Töne, so
# klingen "Programm arbeitet", "KI arbeitet" und "Erfolg" nie gleich. Die Vorgaben sind tiefer und
# weicher als früher, weil der Nutzer die hohen Töne nervig fand. Die alten bleiben wählbar.
@dataclass(frozen=True)
class SoundChoice:
    id: str
    name: str
    make: Callable[[], bytes] | None          # None: kein Ton


CHOICES: dict[str, tuple[SoundChoice, ...]] = {
    TICK: (
        SoundChoice("work_soft_mid", "Weicher Ton, mittel", lambda: _chime([(440.0, 0.0)], 0.14)),
        SoundChoice("work_soft_low", "Weicher Ton, tief",
                    lambda: _chime([(329.6, 0.0)], 0.16, decay=7)),
        SoundChoice("work_wood", "Holzklopfen",
                    lambda: _chime([(392.0, 0.0)], 0.2, decay=30, ring=0.2, overtone=0.6)),
        SoundChoice("work_drops", "Zwei tiefe Tropfen",
                    lambda: _chime([(293.7, 0.0), (220.0, 0.12)], 0.14, decay=14)),
        SoundChoice("work_melody", "Kleine Melodie, aufwärts",
                    lambda: _chime([(261.6, 0.0), (329.6, 0.14), (392.0, 0.28)], 0.12)),
        SoundChoice("work_bell", "Glocke, hell, wie früher", lambda: _chime([(659.3, 0.0)])),
    ),
    AI_TICK: (
        SoundChoice("ai_two_low", "Zwei Töne, tief",
                    lambda: _chime([(261.6, 0.0), (329.6, 0.16)], 0.13)),
        SoundChoice("ai_chord", "Sanfter Akkord",
                    lambda: _chime([(196.0, 0.0), (246.9, 0.0), (293.7, 0.0)], 0.08, decay=5,
                                   ring=0.6)),
        SoundChoice("ai_knock", "Doppelklopfen",
                    lambda: _chime([(349.2, 0.0), (349.2, 0.15)], 0.2, decay=30, ring=0.2,
                                   overtone=0.6)),
        SoundChoice("ai_melody", "Melodie, auf und ab",
                    lambda: _chime([(392.0, 0.0), (440.0, 0.13), (523.3, 0.26), (440.0, 0.39)],
                                   0.11)),
        SoundChoice("ai_two_high", "Zwei Töne, hell, wie früher",
                    lambda: _chime([(523.3, 0.0), (659.3, 0.16)], 0.13)),
    ),
    DONE: (
        SoundChoice("done_soft", "Pling, weich",
                    lambda: _chime([(523.3, 0.0), (784.0, 0.09)], 0.18)),
        SoundChoice("done_triad", "Dreiklang, aufwärts",
                    lambda: _chime([(392.0, 0.0), (493.9, 0.1), (587.3, 0.2)], 0.15)),
        SoundChoice("done_gong", "Kurzer Gong",
                    lambda: _chime([(196.0, 0.0), (392.0, 0.0)], 0.16, decay=4, ring=0.8)),
        SoundChoice("done_bright", "Pling, hell, wie früher",
                    lambda: _chime([(784.0, 0.0), (1046.5, 0.08)], 0.2)),
        SoundChoice("done_none", "Kein Ton", None),
    ),
}
CATEGORY_NAMES = {TICK: "Programm arbeitet", AI_TICK: "KI arbeitet", DONE: "Erfolg"}
DEFAULTS = {kind: options[0].id for kind, options in CHOICES.items()}

_config: dict[str, object] = {"muted": False, **DEFAULTS}


def configure(muted: bool = False, work: str = "", ai: str = "", done: str = "") -> None:
    """Auswahl aus den Einstellungen übernehmen. Leer oder unbekannt: die Vorgabe."""
    _config["muted"] = muted
    for kind, wanted in ((TICK, work), (AI_TICK, ai), (DONE, done)):
        known = {c.id for c in CHOICES[kind]}
        _config[kind] = wanted if wanted in known else DEFAULTS[kind]


def configure_from(settings) -> None:
    configure(settings.sounds_off, settings.sound_work, settings.sound_ai, settings.sound_done)


def muted() -> bool:
    return bool(_config["muted"])


def chosen(kind: str) -> str:
    return str(_config[kind])


def find(sound_id: str) -> SoundChoice:
    return next(c for options in CHOICES.values() for c in options if c.id == sound_id)


def sound_file(kind: str) -> Path | None:
    """Die WAV-Datei des gewählten Klangs einer Art (TICK, AI_TICK, DONE) oder eines Klangs mit
    dieser Kennung, beim ersten Mal erzeugt. None bei "Kein Ton"."""
    choice = find(chosen(kind) if kind in CHOICES else kind)
    if choice.make is None:
        return None
    from cockpit.core import paths
    path = paths.cache_dir() / "sounds" / f"{choice.id}.wav"
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(RATE)
            out.writeframes(choice.make())
    return path


def _windows_sound(kind: str) -> None:
    import winsound
    if kind in (START, ERROR):
        flags = {START: winsound.MB_ICONASTERISK, ERROR: winsound.MB_ICONHAND}
        winsound.MessageBeep(flags[kind])
        return
    path = sound_file(kind)                       # eine Art oder die Kennung eines Tons
    if path is not None:
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC
                           | winsound.SND_NODEFAULT)


def preview(sound_id: str) -> None:
    """Einen Ton zum Anhören abspielen, auch wenn die Signaltöne aus sind."""
    _sound(sound_id)


def _play(kind: str) -> None:
    if muted():
        return
    _sound(kind)


def _sound(kind: str) -> None:
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
        self.ticked = False            # schon ein Warteton gespielt, dann am Ende das Pling
        self.failures = 0
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.check)
        self.timer.start()

    def check(self) -> None:
        from cockpit.core import activity
        if not activity.ai_busy():
            # Wunsch des Nutzers vom 20.10.2026: Nach dem Warteton ein Pling, wenn die KI fertig
            # ist. Nur wenn vorher ein Warteton kam und keine Anfrage gescheitert ist.
            if self.ticked and activity.ai_failures() == self.failures and self._wanted():
                play(DONE)
            self.since, self.ticked = None, False
            return
        now = self.clock()
        if self.since is None:
            self.since, self.last = now, now - TICK_MS / 1000 + AI_FIRST_MS / 1000
            self.failures = activity.ai_failures()
        if now - self.last < TICK_MS / 1000 or waiting_for_user() or _transfers:
            return
        self.last = now
        if self._wanted():
            play(AI_TICK)
            self.ticked = True

    def _wanted(self) -> bool:
        try:
            return bool(self.enabled())
        except Exception:                              # noqa: BLE001 (Ton ist nur Zusatz)
            return True
