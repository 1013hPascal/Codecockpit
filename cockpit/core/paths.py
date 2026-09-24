"""Ordner für Daten, Logs und Zwischenspeicher.

Mit der Umgebungsvariable CODECOCKPIT_HOME lässt sich der Datenordner umlenken (Tests, Testdaten).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from cockpit import APP_NAME

HOME_VARIABLE = "CODECOCKPIT_HOME"


def data_dir() -> Path:
    """Datenordner, normalerweise %APPDATA%\\CodeCockpit."""
    override = os.environ.get(HOME_VARIABLE)
    if override:
        base = Path(override)
    else:
        base = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def cache_dir() -> Path:
    """Ordner für große Dateien und Zwischenspeicher, normalerweise %LOCALAPPDATA%\\CodeCockpit."""
    override = os.environ.get(HOME_VARIABLE)
    if override:
        base = Path(override) / "cache"
    else:
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def logs_dir() -> Path:
    path = data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return data_dir() / "cockpit.db"


def program_dir() -> Path:
    """Ordner, in dem das Programm liegt: bei der Exe der Exe-Ordner, sonst der Code-Ordner."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resource_dir() -> Path:
    """Ordner mit mitgelieferten Dateien wie den Anleitungen (bei der Exe der Entpack-Ordner)."""
    bundle = getattr(sys, "_MEIPASS", None)
    return Path(bundle) if bundle else Path(__file__).resolve().parents[2]


def default_projects_root() -> Path:
    """Vorschlag für den Projekte-Hauptordner.

    Liegt das Cockpit selbst im Aufbau <Hauptordner>\\<Projekt>\\Code (oder \\Exe), ist das der
    Hauptordner. Sonst Dokumente\\GitHub."""
    here = program_dir()
    if here.name.lower() in ("code", "exe") and here.parent.parent != here.parent:
        return here.parent.parent
    return Path.home() / "Documents" / "GitHub"
