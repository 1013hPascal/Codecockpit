"""Wissen für die KI-Hilfe (Teilschritt 8e), ohne Qt.

Drei Quellen: die Anleitungen (anleitungen/*.md), die Einführungen der Features und die Bedienung,
die die Oberfläche beim Fragen selbst beschreibt (Menüs, Tastenkürzel, Aktionen). Alles zusammen
ist zu viel für die Zeichengrenze aus den Grundeinstellungen. Deshalb kommen die Abschnitte, die
am besten zur Frage passen, und die Bedienung immer.
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from pathlib import Path

from cockpit.core.ai_tools import plain_text

_WORD = re.compile(r"[a-zäöüß0-9]{3,}")
# Häufige Wörter, die nichts über das Thema sagen
_STOP = {"der", "die", "das", "und", "oder", "wie", "was", "wo", "ich", "sie", "ein", "eine",
         "einen", "mit", "für", "auf", "ist", "kann", "man", "den", "dem", "des", "von", "zum",
         "zur", "nicht", "auch", "wird", "werden", "bei", "aus", "ins", "noch", "dann", "wenn"}
RESERVE = 1500                  # Zeichen für Frage, Anweisungen und Antwort


@dataclass(frozen=True)
class Section:
    title: str
    text: str
    always: bool = False        # immer mitschicken, zum Beispiel die Tastenkürzel

    @property
    def size(self) -> int:
        return len(self.title) + len(self.text) + 4


def words(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP}


def split_markdown(title: str, text: str) -> list[Section]:
    """Anleitung in Abschnitte nach Überschriften der zweiten Ebene."""
    parts = re.split(r"(?m)^## ", text)
    sections = []
    head = parts[0].strip()
    if head:
        sections.append(Section(title, head))
    for part in parts[1:]:
        heading, _, body = part.partition("\n")
        if body.strip():
            sections.append(Section(f"{title}, {heading.strip()}", body.strip()))
    return sections


def guide_sections(folder: Path) -> list[Section]:
    sections: list[Section] = []
    for path in sorted(folder.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"(?m)^# (.+)$", text)
        title = f"Anleitung {match.group(1).strip() if match else path.stem}"
        sections += split_markdown(title, re.sub(r"(?m)^# .+$", "", text, count=1))
    return sections


def intro_sections(manifests) -> list[Section]:
    sections = []
    for manifest in manifests:
        intro = re.sub(r"(?m)^# .+$", "", manifest.introduction_text(), count=1).strip()
        sections.append(Section(f"Feature {manifest.name}",
                                f"{manifest.description}\n{intro}".strip()))
    return sections


def select(question: str, sections: list[Section], max_chars: int) -> list[Section]:
    """Erst die, die immer mitgehen, dann die mit den meisten gemeinsamen Wörtern, solange sie
    in die Grenze passen. Abschnitte ohne gemeinsames Wort bleiben weg."""
    asked = words(question)
    chosen = [s for s in sections if s.always]
    budget = max_chars - sum(s.size for s in chosen)
    scored = sorted(((len(asked & words(s.title + " " + s.text)), index, s)
                     for index, s in enumerate(sections) if not s.always),
                    key=lambda entry: (-entry[0], entry[1]))
    for score, _index, section in scored:
        if score == 0:
            break
        if section.size <= budget:
            chosen.append(section)
            budget -= section.size
    return chosen


def build_prompt(question: str, sections: list[Section], max_chars: int) -> tuple[str, str]:
    from cockpit.ai import prompt_files
    chosen = select(question, sections, max(1000, max_chars - RESERVE))
    knowledge = "\n\n".join(f"{s.title}:\n{s.text}" for s in chosen)
    prompt = prompt_files.fill(prompt_files.load("ai_help"), wissen=knowledge,
                               frage=question.strip())
    return prompt, prompt_files.load("ai_help_system")


def ask(ai, question: str, sections: list[Section],
        cancel: threading.Event | None = None) -> str:
    """Antwort der KI, ohne Markdown und ohne Geheimnisse. Blockiert, also im Hintergrund."""
    prompt, system = build_prompt(question, sections, ai.max_chars)
    return plain_text(ai.ask(prompt, system, cancel))
