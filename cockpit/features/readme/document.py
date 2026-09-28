"""Aufbau einer README und was das Cockpit darin pflegt (Konzept 10.2, Phase 9), ohne Qt.

Eine README ist hier: ein Kopf (Titel, Zeile mit den Sprachen, Kurzbeschreibung) und Abschnitte
mit einer Überschrift der zweiten Ebene (## Funktionen). Abschnitte ordnet das Cockpit über ihre
Überschrift einer festen Art zu, zum Beispiel "features", in allen vier Sprachen.

Wunsch des Nutzers zu Phase 9: keine Markierungen in der README. Welche Abschnitte vom Cockpit
stammen, merkt es sich deshalb in cockpit.toml, als Fingerabdruck des Textes. Steht der Text noch
genau so da, darf das Cockpit ihn später erneuern. Hat der Nutzer ihn geändert, ist es seiner, und
das Cockpit lässt ihn in Ruhe.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from cockpit.core.projects import read_config, write_config

SECTION = "readme"

# Sprache: Kürzel und Name in der eigenen Sprache (für die Zeile mit den Sprachen)
LANGUAGES = {"Englisch": ("en", "English"), "Deutsch": ("de", "Deutsch"),
             "Französisch": ("fr", "Français"), "Spanisch": ("es", "Español")}

KEYS = ("download", "features", "usage", "requirements", "tools", "install", "changes",
        "windows", "license")
KEY_NAMES = {"download": "Download", "features": "Funktionen", "usage": "Bedienung",
             "requirements": "Systemanforderungen", "tools": "Werkzeuge und Bibliotheken",
             "install": "Installation aus dem Quellcode", "changes": "Änderungen",
             "windows": "Hinweis zu Windows-Warnungen", "license": "Lizenz"}
HEADINGS = {
    "en": ("Download", "Features", "Usage", "System requirements", "Tools and libraries",
           "Installation from source", "Changes", "Windows warnings", "License"),
    "de": ("Download", "Funktionen", "Bedienung", "Systemanforderungen",
           "Werkzeuge und Bibliotheken", "Installation aus dem Quellcode", "Änderungen",
           "Windows-Warnungen", "Lizenz"),
    "fr": ("Téléchargement", "Fonctionnalités", "Utilisation", "Configuration requise",
           "Outils et bibliothèques", "Installation depuis les sources", "Modifications",
           "Avertissements de Windows", "Licence"),
    "es": ("Descarga", "Funciones", "Uso", "Requisitos del sistema", "Herramientas y bibliotecas",
           "Instalación desde el código fuente", "Cambios", "Advertencias de Windows",
           "Licencia"),
}
# Weitere übliche Überschriften, die das Cockpit als dieselbe Art erkennt
SYNONYMS = {"installation": "install", "requirements": "requirements", "changelog": "changes",
            "lizenz und bibliotheken": "license", "benutzung": "usage", "bedienung und tasten":
            "usage", "features and usage": "features"}


def heading(key: str, code: str) -> str:
    return HEADINGS.get(code, HEADINGS["en"])[KEYS.index(key)]


def key_of(title: str) -> str:
    """Art eines Abschnitts nach seiner Überschrift, leer wenn unbekannt."""
    normalized = title.strip().lower()
    for headings in HEADINGS.values():
        for key, text in zip(KEYS, headings):
            if text.lower() == normalized:
                return key
    return SYNONYMS.get(normalized, "")


def file_name(code: str, main_code: str) -> str:
    return "README.md" if code == main_code else f"README.{code}.md"


def fingerprint(text: str) -> str:
    return hashlib.sha1(" ".join(text.split()).encode("utf-8")).hexdigest()[:12]


@dataclass
class Part:
    title: str                          # Überschrift ohne "## "
    body: str                           # Text darunter, ohne Leerzeilen am Rand

    @property
    def key(self) -> str:
        return key_of(self.title)


@dataclass
class Readme:
    head: str = ""                      # alles vor dem ersten "## "
    parts: list[Part] = field(default_factory=list)

    def find(self, key: str) -> Part | None:
        return next((p for p in self.parts if p.key == key), None)

    def put(self, key: str, title: str, body: str) -> None:
        """Abschnitt ersetzen oder in der festen Reihenfolge einfügen."""
        existing = self.find(key)
        if existing is not None:
            existing.body = body.strip()
            return
        new = Part(title, body.strip())
        order = KEYS.index(key)
        for index, part in enumerate(self.parts):
            if part.key and KEYS.index(part.key) > order:
                self.parts.insert(index, new)
                return
        self.parts.append(new)

    def text(self) -> str:
        chunks = [self.head.rstrip()] if self.head.strip() else []
        chunks += [f"## {p.title}\n\n{p.body}".rstrip() for p in self.parts]
        return "\n\n".join(chunks).strip() + "\n"


def parse(text: str) -> Readme:
    pieces = re.split(r"(?m)^## ", text.replace("\r\n", "\n"))
    readme = Readme(pieces[0].strip())
    for piece in pieces[1:]:
        title, _, body = piece.partition("\n")
        readme.parts.append(Part(title.strip(), body.strip()))
    return readme


def language_line(current: str, codes: list[str], main_code: str) -> str:
    """Zum Beispiel "English | [Deutsch](README.de.md)". Die eigene Sprache ohne Link."""
    names = {code: native for code, native in LANGUAGES.values()}
    items = [names[c] if c == current else f"[{names[c]}]({file_name(c, main_code)})"
             for c in codes]
    return " | ".join(items)


def set_head(readme: Readme, title: str, description: str, line: str) -> None:
    """Kopf: Titel, Zeile mit den Sprachen (nur bei mehr als einer), Kurzbeschreibung. Ein
    vorhandener Kopf bleibt, nur die Zeile mit den Sprachen wird eingefügt oder erneuert."""
    names = [native for _code, native in LANGUAGES.values()]
    lines = readme.head.splitlines() if readme.head.strip() else [f"# {title}", "",
                                                                  description.strip()]
    lines = [l for l in lines if not (l.strip() and any(n in l for n in names)
                                      and l.count("|") >= 1)]
    if line:
        position = 1 if lines and lines[0].startswith("# ") else 0
        lines[position:position] = ["", line] if position else [line, ""]
    readme.head = "\n".join(lines).strip()


# -- cockpit.toml -------------------------------------------------------------------------------
def settings(code_dir: Path) -> dict:
    data = read_config(code_dir).get(SECTION, {})
    return data if isinstance(data, dict) else {}


def save(code_dir: Path, values: dict) -> None:
    data = read_config(code_dir)
    section = data.get(SECTION) if isinstance(data.get(SECTION), dict) else {}
    section.update(values)
    data[SECTION] = section
    write_config(code_dir, data)


def managed(code_dir: Path, file: str) -> dict[str, str]:
    value = settings(code_dir).get("managed", {}).get(file, {})
    return dict(value) if isinstance(value, dict) else {}


def remember(code_dir: Path, file: str, key: str, body: str) -> None:
    """Abschnitt stammt vom Cockpit: Fingerabdruck merken."""
    all_managed = settings(code_dir).get("managed", {})
    all_managed = dict(all_managed) if isinstance(all_managed, dict) else {}
    entry = dict(all_managed.get(file, {}))
    entry[key] = fingerprint(body)
    all_managed[file] = entry
    save(code_dir, {"managed": all_managed})


def is_own(code_dir: Path, file: str, part: Part) -> bool:
    """Selbst geschrieben oder nach dem Cockpit geändert: dann nie anfassen."""
    return managed(code_dir, file).get(part.key) != fingerprint(part.body)
