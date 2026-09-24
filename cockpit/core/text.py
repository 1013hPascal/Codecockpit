"""Kleine Hilfen für deutsche Texte."""
from __future__ import annotations

import re
from typing import Iterable

# Satzende: Punkt, Ausrufe- oder Fragezeichen, dann Leerraum und ein Großbuchstabe oder eine Ziffer.
# So trennen Abkürzungen wie "z. B. etwas" nicht.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ0-9„\"])")


# Abkürzungen, nach denen kein Satz endet: einzelne Buchstaben (z. B., u. a.) und häufige Kürzel
_ABBREVIATION = re.compile(r"(?:^|\s)(?:\w|Dr|Nr|Hr|Fr|bzw|usw|ca|vgl|ggf|inkl|evtl|Abs|Str)\.$")


def _sentences(paragraph: str) -> list[str]:
    parts = _SENTENCE_END.split(paragraph)
    merged: list[str] = []
    for part in parts:
        if merged and _ABBREVIATION.search(merged[-1]):
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    return merged


def one_sentence_per_line(text: str) -> str:
    """Jeder Satz in eine eigene Zeile (wie im Chatbot). Mit Pfeiltasten liest man dann Satz für
    Satz, und die Braillezeile zeigt nicht einen langen Absatz in einer Zeile."""
    lines = []
    for paragraph in text.splitlines():
        lines.extend(_sentences(paragraph.strip()) if paragraph.strip() else [""])
    return "\n".join(lines).strip()


def join_words(words: Iterable[str]) -> str:
    """["A"] -> "A", ["A", "B"] -> "A und B", ["A", "B", "C"] -> "A, B und C"."""
    items = [w for w in words if w]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " und " + items[-1]


def count(number: int, one: str, many: str) -> str:
    """count(1, "Projekt", "Projekte") -> "1 Projekt", count(3, ...) -> "3 Projekte"."""
    return f"{number} {one if number == 1 else many}"
