"""Kurzanleitungen für das Hilfefenster (Wunsch des Nutzers vom 07.10.2026).

Die Anleitungen stehen in anleitungen\\kurzanleitungen.md, je Anleitung eine Überschrift „##“,
darunter „Bereich:“, „Aktionen:“, „Stichwörter:“ und die Schritte „Schritt 1: …“. Der Bereich
ordnet die Vorschläge: Ohne Suche stehen die Anleitungen für die markierte Zeile oben. Die
Aktionen prüft ein Test, damit keine Anleitung auf eine Aktion zeigt, die es nicht mehr gibt.
Der Kern importiert nie PySide6.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

GUIDES_FILE = "kurzanleitungen.md"
AREAS = ("start", "projekt", "repository", "branch", "releases", "alle")
_STEP = re.compile(r"^Schritt \d+:")
_WORD = re.compile(r"[a-zäöüß0-9+]+")


@dataclass
class Guide:
    title: str
    area: str = "alle"
    actions: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.steps)


def parse(text: str) -> list[Guide]:
    guides: list[Guide] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            guides.append(Guide(line[3:].strip()))
            continue
        if not guides or not line:
            continue
        guide = guides[-1]
        key, _sep, value = line.partition(":")
        if key == "Bereich":
            guide.area = value.strip() if value.strip() in AREAS else "alle"
        elif key == "Aktionen":
            guide.actions = [a.strip() for a in value.split(",") if a.strip()]
        elif key == "Stichwörter":
            guide.keywords = [k.strip() for k in value.split(",") if k.strip()]
        elif _STEP.match(line):
            guide.steps.append(line)
    return [g for g in guides if g.steps]


def load(folder: Path) -> list[Guide]:
    try:
        return parse((folder / GUIDES_FILE).read_text(encoding="utf-8"))
    except OSError:
        return []


def _words(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def score(guide: Guide, query: str) -> int:
    """Wie gut die Anleitung zur Suche passt. Titel zählt am meisten, dann Stichwörter, dann
    der Text der Schritte. Wortanfänge zählen auch, „hoch“ findet „hochladen“."""
    wanted = _words(query)
    if not wanted:
        return 0
    places = ((_words(guide.title), 6), (_words(" ".join(guide.keywords)), 4),
              (_words(guide.text), 1))
    phrase, title = query.strip().lower(), guide.title.lower()
    total = 20 if phrase == title else 10 if phrase in title else 0     # ganzer Titel passt
    for word in wanted:
        for found, weight in places:
            if word in found:
                total += weight
            elif any(w.startswith(word) for w in found):
                total += weight // 2 or 1
    return total


def search(guides: list[Guide], query: str, area: str = "alle") -> list[Guide]:
    """Ohne Suche: erst die Anleitungen für den Bereich, dann „alle“, dann der Rest. Mit Suche:
    nur passende, die besten oben, bei Gleichstand der Bereich zuerst."""
    def near(guide: Guide) -> int:
        return 0 if guide.area == area else 1 if guide.area == "alle" else 2

    if not query.strip():
        return sorted(guides, key=near)
    scored = [(score(g, query), g) for g in guides]
    return [g for s, g in sorted(scored, key=lambda pair: (-pair[0], near(pair[1]))) if s > 0]


def good_match(guides: list[Guide], query: str) -> Guide | None:
    """Für „KI fragen“: Passt eine Anleitung gut genug, kommt sie statt einer Antwort der KI."""
    found = search(guides, query)
    if found and score(found[0], query) >= 6 * max(1, len(_words(query)) // 2):
        return found[0]
    return None
