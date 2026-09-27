"""Beschreibung eines Features (Konzept 3.2).

Jedes Feature ist ein Unterpaket von cockpit.features mit einer Datei manifest.py, die eine
Variable MANIFEST enthält. Das Manifest ist Python und kein JSON, weil es auf die Funktionen der
Aktionen und Schritte verweist.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from cockpit.core.actions import Action
from cockpit.core.features.settings_fields import SettingField
from cockpit.core.flows.step import Step
from cockpit.platforms.base import Capability

# Dienste, die ein Feature brauchen kann, mit deutschem Namen
SERVICES = {"ai": "KI", "automation": "Automation", "email": "E-Mail"}

ID_PATTERN = re.compile(r"[a-z][a-z0-9_]*")


@dataclass(frozen=True)
class FeatureManifest:
    id: str                                              # "exe"
    name: str                                            # "Exe-Erstellung"
    description: str                                     # ein bis zwei kurze Sätze
    requires_features: tuple[str, ...] = ()
    requires_services: tuple[str, ...] = ()              # Schlüssel aus SERVICES
    requires_capabilities: tuple[Capability, ...] = ()
    settings: tuple[SettingField, ...] = ()
    actions: tuple[Action, ...] = ()
    steps: tuple[Step, ...] = ()
    introduction: str = "EINFUEHRUNG.md"                 # Schritt-für-Schritt-Einführung
    n8n_workflows: str = ""                              # Ordner mit Workflows, leer: keine
    enabled_by_default: bool = False                     # Vorauswahl für neue Projekte
    # Name einer alten Ja-Nein-Grundeinstellung, die die Vorauswahl bestimmt, solange in der
    # Feature-Verwaltung noch keine Vorauswahl gespeichert ist (Phase 7). Leer: keine.
    default_setting: str = ""
    package_dir: Path | None = field(default=None, compare=False)

    def introduction_path(self) -> Path | None:
        if self.package_dir is None or not self.introduction:
            return None
        return self.package_dir / self.introduction

    def introduction_text(self) -> str:
        path = self.introduction_path()
        if path is None or not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def problems(self) -> list[str]:
        """Fehler im Manifest, leer wenn alles stimmt."""
        found = []
        if not ID_PATTERN.fullmatch(self.id):
            found.append(f"Kennung {self.id!r} ist ungültig (Kleinbuchstaben, Ziffern, _).")
        if not self.name.strip():
            found.append(f"Feature {self.id} hat keinen Namen.")
        if not self.description.strip():
            found.append(f"Feature {self.id} hat keine Beschreibung.")
        unknown = [s for s in self.requires_services if s not in SERVICES]
        if unknown:
            found.append(f"Feature {self.id} braucht unbekannte Dienste: {', '.join(unknown)}.")
        keys = [s.key for s in self.settings]
        if len(keys) != len(set(keys)):
            found.append(f"Feature {self.id} hat doppelte Einstellungen.")
        ids = [a.id for a in self.actions] + [s.id for s in self.steps]
        if len(ids) != len(set(ids)):
            found.append(f"Feature {self.id} hat doppelte Kennungen bei Aktionen oder Schritten.")
        if self.id in self.requires_features:
            found.append(f"Feature {self.id} braucht sich selbst.")
        path = self.introduction_path()
        if path is not None and not path.is_file():
            found.append(f"Feature {self.id}: Einführung {self.introduction} fehlt.")
        return found
