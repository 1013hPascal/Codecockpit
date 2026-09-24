"""Grundeinstellungen der Installation.

Es gibt keine Profile (siehe ENTSCHEIDUNGEN.md): Eine Installation ist ein Einsatzbereich. Die
Felder sind mit denselben Klassen beschrieben wie die Einstellungen der Features, damit das
Formular automatisch entsteht.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from cockpit.core import paths
from cockpit.core.database import Database
from cockpit.core.features.settings_fields import (Choice, Email, Folder, SettingField, Text,
                                                   YesNo)

LICENSES = ("MIT", "Apache-2.0", "BSD-3-Clause", "GPL-3.0", "LGPL-3.0", "MPL-2.0",
            "Keine Lizenz / firmenintern")

_PREFIX = "core."


def setting_fields() -> list[SettingField]:
    """Die Felder in der Reihenfolge des Formulars."""
    return [
        Folder("projects_root", "Projekte-Hauptordner", str(paths.default_projects_root())),
        Text("git_name", "Git-Name für Commits"),
        Email("git_email", "Git-E-Mail-Adresse für Commits"),
        YesNo("default_private", "Neue Repositories privat anlegen", True),
        Choice("default_license", "Standard-Lizenz für neue Projekte", "MIT", options=LICENSES),
        YesNo("ai_local_only", "Code-Auszüge nur an lokale oder firmeninterne KI senden", False),
        YesNo("branches_by_default", "Neue Projekte mit Branches und Pull Requests", False),
    ]


@dataclass
class Settings:
    projects_root: str = ""
    git_name: str = ""
    git_email: str = ""
    default_private: bool = True
    default_license: str = "MIT"
    ai_local_only: bool = False
    branches_by_default: bool = False
    default_features: list[str] | None = None     # None: Standard der Features
    # Nicht im Formular der Grundeinstellungen, sondern in eigenen Dialogen:
    setup_done: bool = False                      # Einrichtungsassistent abgeschlossen
    vault_kind: str = ""                          # "windows", "vault_file" oder leer
    auto_lock_minutes: int = 0                    # Tresordatei nach Inaktivität sperren, 0: nie


class SettingsStore:
    """Lädt und speichert die Grundeinstellungen in der Datenbank."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def load(self) -> Settings:
        settings = Settings()
        defaults = {f.key: f.default for f in setting_fields()}
        for f in fields(Settings):
            fallback = defaults.get(f.name, getattr(settings, f.name))
            value = self.database.get_value(_PREFIX + f.name, fallback)
            expected = type(getattr(settings, f.name))
            if getattr(settings, f.name) is None or isinstance(value, expected):
                setattr(settings, f.name, value)
            else:
                setattr(settings, f.name, fallback)
        return settings

    def save(self, settings: Settings) -> None:
        for f in fields(Settings):
            self.database.set_value(_PREFIX + f.name, getattr(settings, f.name))

    def update(self, **values: Any) -> Settings:
        """Einzelne Werte prüfen und speichern. Wirft ValueError bei ungültigen Werten."""
        by_key = {f.key: f for f in setting_fields()}
        settings = self.load()
        for key, value in values.items():
            if not hasattr(settings, key):
                raise KeyError(key)
            if key in by_key:
                value = by_key[key].check(value)
            setattr(settings, key, value)
        self.save(settings)
        return settings
