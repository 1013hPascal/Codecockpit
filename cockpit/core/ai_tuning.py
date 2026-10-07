"""Die KI auf den Rechner einstellen (Wunsch des Nutzers vom 07.10.2026).

Vorschläge für Textfelder dauerten 30 Sekunden und mehr. Der größte Teil der Zeit geht beim Lesen
des Textes verloren, den die KI bekommt, und beim ersten Laden des Modells. Deshalb:

- Zwei Arten von Aufgaben: Vorschläge für Textfelder (kurz und schnell) und Antworten und
  Bearbeitung für Code oder komplexe Fragen (gründlich).
- Ein Starttest misst im Hintergrund, wie schnell die KI auf diesem Rechner liest und schreibt.
  Daraus folgt, wie viel Text sie für jede Art bekommt, damit sie in der Zielzeit antwortet.
- Pro Art eine Stufe von +3 (sehr genau, langsamer) bis -3 (ungenau, schneller), Vorgabe 0.
  Die 0 bei Textfeldern ist schon knapper als die 0 bei Code.
- Ab +2 darf die KI bei Code und komplexen Fragen nachdenken.

Gemessen wird nur bei einer KI auf diesem Rechner (Ollama) oder im eigenen Netz. Eine KI außerhalb
bekommt nichts ohne Zustimmung, deshalb gelten dort feste Werte. Der Kern importiert nie PySide6.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime

from cockpit.core.errors import Cancelled

TEXT_FIELDS = "text_fields"
COMPLEX = "complex"
PURPOSES = {TEXT_FIELDS: "Vorschläge für Textfelder",
            COMPLEX: "Antworten und Bearbeitung für Code oder komplexe Fragen"}
# Welche Aufgabe zu welcher Art gehört. Alles andere zählt als komplex.
TASK_PURPOSE = {"ai_assistant": TEXT_FIELDS, "terminal_explain": TEXT_FIELDS}
LEVELS = (3, 2, 1, 0, -1, -2, -3)
LEVEL_NAMES = {3: "+3 sehr genau, langsamer", 2: "+2 genauer, nachdenken bei Code",
               1: "+1 etwas genauer", 0: "0 Standard", -1: "-1 etwas schneller",
               -2: "-2 schneller", -3: "-3 ungenau, am schnellsten"}

CALIBRATION_KEY = "ai.calibration"
LEVELS_KEY = "ai.precision"
CHARS_PER_TOKEN = 4                      # grobe Schätzung für Deutsch und Code
STEP = 1.6                               # eine Stufe: 1,6-mal so viel Zeit
TARGET_SECONDS = {TEXT_FIELDS: 6.0, COMPLEX: 45.0}
ANSWER_TOKENS = {TEXT_FIELDS: 120, COMPLEX: 0}     # 0: was die Aufgabe selbst verlangt
MIN_CHARS = {TEXT_FIELDS: 1200, COMPLEX: 4000}
UNCALIBRATED_CHARS = {TEXT_FIELDS: 3000, COMPLEX: 0}   # 0: Grenze der Grundeinstellung
KEEP_ALIVE = "30m"                       # so lange behält Ollama das Modell im Speicher
_FILLER = ("Das Cockpit misst, wie schnell die KI einen längeren Text liest. Der Inhalt ist "
           "unwichtig. ")


@dataclass(frozen=True)
class Calibration:
    read_tps: float                      # gelesene Token pro Sekunde
    write_tps: float                     # geschriebene Token pro Sekunde
    date: str

    @property
    def day(self) -> str:
        try:
            return f"{datetime.fromisoformat(self.date):%d.%m.%Y}"
        except ValueError:
            return ""


@dataclass(frozen=True)
class Tuning:
    """Was eine Aufgabe bekommt: höchstens so viele Zeichen, Länge der Antwort, Nachdenken."""
    max_chars: int
    answer_factor: float = 1.0
    think: bool = False


def purpose_of(task: str) -> str:
    return TASK_PURPOSE.get(task, COMPLEX)


def tuning(purpose: str, level: int, calibration: Calibration | None,
           limit: int) -> Tuning:
    """Budget für eine Art und Stufe. limit ist die Grenze der Grundeinstellung."""
    level = max(-3, min(3, int(level)))
    factor = STEP ** level
    answer_factor = 1.25 ** level
    think = purpose == COMPLEX and level >= 2
    if calibration is None or calibration.read_tps <= 0:
        chars = UNCALIBRATED_CHARS[purpose] or limit
        return Tuning(min(limit, int(chars * factor)), answer_factor, think)
    target = TARGET_SECONDS[purpose] * factor
    answer = ANSWER_TOKENS[purpose] * answer_factor
    writing = answer / calibration.write_tps if calibration.write_tps > 0 else 0
    reading = max(target - writing, target * 0.3)
    chars = int(reading * calibration.read_tps * CHARS_PER_TOKEN)
    return Tuning(max(MIN_CHARS[purpose], min(limit, chars)), answer_factor, think)


def _tokens(text: str) -> float:
    return max(1.0, len(text) / CHARS_PER_TOKEN)


def measure(ask, cancel: threading.Event | None = None,
            clock=time.monotonic) -> Calibration:
    """Drei kleine Anfragen. ask(prompt, max_tokens) gibt die Antwort zurück und blockiert.
    1. Aufwärmen: lädt das Modell, zählt nicht.
    2. Kurz fragen, lang antworten lassen: Tempo beim Schreiben.
    3. Lang fragen, kurz antworten lassen: Tempo beim Lesen."""
    ask("Antworte nur mit OK.", 5)
    if cancel is not None and cancel.is_set():
        raise Cancelled()
    start = clock()
    answer = ask("Zähle von 1 bis 40, durch Kommas getrennt.", 120)
    write_seconds = max(clock() - start, 0.05)
    write_tps = _tokens(answer) / write_seconds
    if cancel is not None and cancel.is_set():
        raise Cancelled()
    long_text = _FILLER * 40 + "Antworte nur mit OK."
    start = clock()
    ask(long_text, 5)
    read_seconds = max(clock() - start - 5 / write_tps, 0.05)
    read_tps = _tokens(long_text) / read_seconds
    return Calibration(round(read_tps, 1), round(write_tps, 1),
                       datetime.now().isoformat(timespec="seconds"))


class TuningStore:
    """Messungen pro KI und Modell, Stufen pro Art. In der Datenbank, ohne Geheimnisse."""

    def __init__(self, database) -> None:
        self.database = database

    def calibration(self, name: str) -> Calibration | None:
        found = (self.database.get_value(CALIBRATION_KEY, {}) or {}).get(name)
        if not found:
            return None
        try:
            return Calibration(float(found["read_tps"]), float(found["write_tps"]),
                               str(found.get("date", "")))
        except (KeyError, TypeError, ValueError):
            return None

    def save_calibration(self, name: str, calibration: Calibration) -> None:
        saved = dict(self.database.get_value(CALIBRATION_KEY, {}) or {})
        saved[name] = {"read_tps": calibration.read_tps, "write_tps": calibration.write_tps,
                       "date": calibration.date}
        self.database.set_value(CALIBRATION_KEY, saved)

    def level(self, purpose: str) -> int:
        try:
            return int((self.database.get_value(LEVELS_KEY, {}) or {}).get(purpose, 0))
        except (TypeError, ValueError):
            return 0

    def set_level(self, purpose: str, level: int) -> None:
        saved = dict(self.database.get_value(LEVELS_KEY, {}) or {})
        saved[purpose] = max(-3, min(3, int(level)))
        self.database.set_value(LEVELS_KEY, saved)

    def tuning(self, name: str, purpose: str, limit: int) -> Tuning:
        return tuning(purpose, self.level(purpose), self.calibration(name), limit)
