"""Prompts als Textdateien (Konzept 11, Frage 14 zu Phase 8).

Die Prompts liegen in cockpit/ai/prompts. Liegt im Datenordner unter "prompts" eine Datei mit
demselben Namen, nimmt das Cockpit diese Fassung. So lassen sie sich anpassen, ohne den Code zu
ändern.

Platzhalter stehen in doppelten spitzen Klammern, zum Beispiel <<befehl>>. Geschweifte Klammern
bleiben frei, weil sie in Befehlen und Ausgaben oft vorkommen.
"""
from __future__ import annotations

from pathlib import Path

from cockpit.core import paths
from cockpit.core.errors import CockpitError

BUILT_IN = Path(__file__).resolve().parent / "prompts"


def user_dir() -> Path:
    return paths.data_dir() / "prompts"


def load(name: str) -> str:
    """Text des Prompts name (ohne .txt). Die Fassung im Datenordner hat Vorrang."""
    for folder in (user_dir(), BUILT_IN):
        path = folder / f"{name}.txt"
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    raise CockpitError(f"Der Prompt {name} fehlt.", str(BUILT_IN / f"{name}.txt"))


def fill(text: str, **values: str) -> str:
    for key, value in values.items():
        text = text.replace(f"<<{key}>>", value)
    return text
