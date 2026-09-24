"""Rückfragen aus einem laufenden Ablauf an den Nutzer.

Ein Schritt läuft im Hintergrund. Braucht er eine Entscheidung, stellt er eine Frage über den
Asker. Die Oberfläche zeigt einen Dialog, der Schritt wartet auf die Antwort. In Tests beantwortet
ein ScriptedAsker die Fragen.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ConfirmQuestion:
    title: str
    text: str
    yes: str = "Ja"
    no: str = "Nein"
    default_yes: bool = False            # Vorgabe ist die sichere Antwort


@dataclass(frozen=True)
class ChoiceQuestion:
    title: str
    text: str
    options: tuple[str, ...]
    default_index: int = 0


@dataclass(frozen=True)
class TextQuestion:
    title: str
    label: str
    default: str = ""
    multiline: bool = False


Question = ConfirmQuestion | ChoiceQuestion | TextQuestion


class Asker(Protocol):
    def ask(self, question: Question) -> Any:
        """Antwort: bool (Bestätigung), Index (Auswahl) oder Text. None heißt abgebrochen."""


class ScriptedAsker:
    """Für Tests: gibt vorbereitete Antworten der Reihe nach zurück und merkt sich die Fragen."""

    def __init__(self, *answers: Any) -> None:
        self.answers = list(answers)
        self.questions: list[Question] = []

    def ask(self, question: Question) -> Any:
        self.questions.append(question)
        return self.answers.pop(0) if self.answers else None
