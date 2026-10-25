"""Gemeinsame Bausteine der Paketübersicht.

Ein Package ist eine Zeile in der Liste: eine Bibliothek in einer Python-Umgebung, ein Programm aus
winget oder Chocolatey oder ein Sprachmodell. Das Wichtigste steht vorne in der Zeile: Name,
Version, aktuell oder veraltet.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

PIP, WINGET, CHOCO, MODEL = "pip", "winget", "choco", "model"
SOURCE_NAMES = {PIP: "Python-Bibliotheken (pip)", WINGET: "Programme aus winget",
                CHOCO: "Programme aus Chocolatey", MODEL: "Sprachmodelle"}
SOURCES = (PIP, WINGET, CHOCO, MODEL)

# Filter oben im Fenster (Wunsch des Nutzers vom 21.10.2026, Namen vom 24.10.2026). Vorgabe ist
# immer "Alle".
ALL, COCKPIT, MACHINE = "Alle", "Nur im Cockpit", "Nur auf dem Rechner, nicht im Cockpit"
FILTERS = (ALL, COCKPIT, MACHINE)


@dataclass
class Package:
    source: str                         # PIP, WINGET, CHOCO oder MODEL
    name: str                           # angezeigter Name
    version: str
    key: str = ""                       # Kennung für die Befehle, leer: wie name
    place: str = ""                     # wo es liegt: "Python 3.14", "Projekt Tagebuch", "Ollama"
    location: Path | None = None        # Python der Umgebung oder Ordner des Modells
    latest: str = ""                    # neueste Version, leer: unbekannt oder schon aktuell
    checked: bool = False               # wurde geprüft, ob es aktuell ist
    size: int | None = None             # Bytes
    added: datetime | None = None
    owner: str = ""                     # Projekt, zu dem es gehört
    cockpit: bool = False               # gehört zu einem Projekt oder zum Cockpit selbst
    used_by: tuple[str, ...] = ()       # Projekte, die es benutzen (Stufe 2)
    license: str = ""
    pinned: bool = False                # festgehalten: "Alle aktualisieren" lässt es aus
    warning: str = ""                   # zum Beispiel eine bekannte Sicherheitslücke
    kind: str = ""                      # bei Modellen: "huggingface", "ollama", "cockpit", "datei"
    extra: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.key or self.name

    @property
    def outdated(self) -> bool:
        return bool(self.latest) and self.latest != self.version

    def state(self) -> str:
        if self.outdated:
            # Ollama nennt keine Nummer, nur "neuere Fassung"
            return f"veraltet, {self.latest} verfügbar" if " " in self.latest \
                else f"veraltet, neu: {self.latest}"
        return "aktuell" if self.checked else "noch nicht geprüft"

    def line(self) -> str:
        """Eine Zeile der Liste, das Wichtigste vorne."""
        parts = [f"{self.name} {self.version}".strip(), self.state()]
        if self.pinned:
            parts.append("festgehalten")
        if self.warning:
            parts.append(self.warning)
        if self.size is not None:
            parts.append(size_text(self.size))
        if self.added is not None:
            parts.append(self.added.strftime("%d.%m.%Y"))
        if self.place:
            parts.append(self.place)
        if self.used_by:
            parts.append("benutzt von " + ", ".join(self.used_by))
        elif self.extra.get("unused"):
            parts.append("von keinem Projekt benutzt")
        if self.license:
            parts.append(f"Lizenz {self.license}")
        return ", ".join(parts)


def size_text(size: int | None) -> str:
    if size is None:
        return "Größe unbekannt"
    for unit, factor in (("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if size >= factor:
            value = size / factor
            text = f"{value:.1f}" if value < 10 else f"{value:.0f}"
            return f"{text.replace('.', ',')} {unit}"
    return f"{size} Bytes"


def folder_size(path: Path) -> int:
    """Größe eines Ordners in Bytes, ohne Verknüpfungen doppelt zu zählen."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            file = Path(root) / name
            try:
                if not file.is_symlink():
                    total += file.stat().st_size
            except OSError:
                continue
    return total


def mtime(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except (OSError, ValueError, OverflowError):
        return None


def newest_first(packages: list[Package]) -> list[Package]:
    """Neueste oben, ohne Datum ans Ende, dann nach Namen (Wunsch des Nutzers)."""
    return sorted(packages, key=lambda p: (p.added is None, -(p.added.timestamp()
                                           if p.added else 0), p.name.lower()))


def for_cockpit(package: Package) -> bool:
    """Gehört zu einem Projekt, zum Cockpit selbst oder wird von einem Projekt benutzt."""
    return package.cockpit or bool(package.used_by)


def apply_filter(packages: list[Package], chosen: str) -> list[Package]:
    if chosen == COCKPIT:
        return [p for p in packages if for_cockpit(p)]
    if chosen == MACHINE:
        return [p for p in packages if not for_cockpit(p)]
    return list(packages)


def version_key(version: str) -> tuple:
    """Grobe Ordnung für Versionen wie 1.10.2, 2.0.0rc1 oder 18.4-1. Vorabversionen vor der
    fertigen Version."""
    import re
    parts = re.split(r"[.\-+_]", version.lower())
    key = []
    for part in parts:
        match = re.match(r"(\d+)(.*)", part)
        if match:
            key.append((int(match.group(1)), match.group(2) == "", match.group(2)))
        else:
            key.append((-1, False, part))
    return tuple(key)


def major_jump(old: str, new: str) -> bool:
    """Springt die erste Stelle, zum Beispiel von 1.x auf 2.x? Dann ändert sich oft viel."""
    first = lambda v: v.split(".")[0].split("-")[0]          # noqa: E731
    return bool(old and new) and first(old).isdigit() and first(new).isdigit() \
        and int(first(new)) > int(first(old))
