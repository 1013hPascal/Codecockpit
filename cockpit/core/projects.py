"""Projekte und ihre Ordner (Konzept 7).

Jedes Projekt hat einen Projektordner mit den Unterordnern Code (das Git-Repository) und Exe.
Die Projekteinstellungen stehen ohne Geheimnisse in Code\\cockpit.toml und werden mitversioniert.
Die Zuordnung von Projekt und Pfad steht in der Datenbank.

Phase 2 enthält nur das Nötigste: Projekte im Hauptordner finden, auflisten und die aktiven
Features aus cockpit.toml lesen und schreiben. Der Rest folgt in Phase 5.
"""
from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import tomli_w

from cockpit.core.database import Database
from cockpit.core.errors import CockpitError

log = logging.getLogger(__name__)

CODE_DIR = "Code"
EXE_DIR = "Exe"
CONFIG_NAME = "cockpit.toml"


@dataclass(frozen=True)
class Project:
    id: int
    name: str
    project_dir: Path
    code_dir: Path
    exe_dir: Path
    account_id: int | None = None
    last_updated: str | None = None      # letztes Hochladen, ab Phase 5

    @property
    def folder_found(self) -> bool:
        return self.code_dir.is_dir()

    @property
    def has_exe_dir(self) -> bool:
        return self.exe_dir.is_dir()

    @property
    def config_path(self) -> Path:
        return self.code_dir / CONFIG_NAME

    def newest_exe(self) -> Path | None:
        if not self.has_exe_dir:
            return None
        exes = [p for p in self.exe_dir.rglob("*.exe") if p.is_file()]
        return max(exes, key=lambda p: p.stat().st_mtime) if exes else None

    def last_activity(self) -> float:
        """Zeitpunkt der letzten Änderung im Code-Ordner (oberste Ebene), 0 wenn nicht gefunden."""
        try:
            return self.code_dir.stat().st_mtime
        except OSError:
            return 0.0


def read_config(code_dir: Path) -> dict[str, Any]:
    """Inhalt von cockpit.toml. Fehlt die Datei oder ist sie kaputt, ein leeres Wörterbuch."""
    path = code_dir / CONFIG_NAME
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        log.warning("cockpit.toml nicht lesbar: %s (%s)", path, exc)
        return {}


def write_config(code_dir: Path, data: dict[str, Any]) -> None:
    path = code_dir / CONFIG_NAME
    path.write_text(tomli_w.dumps(data), encoding="utf-8")


class ProjectStore:
    def __init__(self, database: Database) -> None:
        self.database = database

    # -- Lesen ---------------------------------------------------------------------------
    @staticmethod
    def _from_row(row) -> Project:
        project_dir = Path(row["project_dir"])
        return Project(
            id=row["id"], name=row["name"], project_dir=project_dir,
            code_dir=Path(row["code_dir"]),
            exe_dir=Path(row["exe_dir"]) if row["exe_dir"] else project_dir / EXE_DIR,
            account_id=row["account_id"], last_updated=row["last_updated"])

    def all(self) -> list[Project]:
        """Alle Projekte, zuletzt aktualisierte oben."""
        projects = [self._from_row(r) for r in self.database.query("SELECT * FROM projects")]
        return sorted(projects, key=lambda p: (p.last_updated or "", p.last_activity()),
                      reverse=True)

    def get(self, project_id: int) -> Project | None:
        row = self.database.query_one("SELECT * FROM projects WHERE id = ?", (project_id,))
        return self._from_row(row) if row else None

    def find_by_dir(self, project_dir: Path) -> Project | None:
        row = self.database.query_one("SELECT * FROM projects WHERE project_dir = ?",
                                      (str(project_dir.resolve()),))
        return self._from_row(row) if row else None

    # -- Ändern --------------------------------------------------------------------------
    def add(self, project_dir: Path) -> Project:
        """Einen Projektordner mit Unterordner Code aufnehmen. Schon vorhandene bleiben gleich."""
        project_dir = project_dir.resolve()
        existing = self.find_by_dir(project_dir)
        if existing is not None:
            return existing
        code_dir = project_dir / CODE_DIR
        if not code_dir.is_dir():
            raise CockpitError(f"Im Ordner {project_dir} gibt es keinen Unterordner Code.")
        self.database.execute(
            "INSERT INTO projects (name, project_dir, code_dir, exe_dir, added_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (project_dir.name, str(project_dir), str(code_dir), str(project_dir / EXE_DIR),
             datetime.now().isoformat(timespec="seconds")))
        return self.find_by_dir(project_dir)

    def scan(self, root: Path) -> list[Project]:
        """Alle Unterordner des Hauptordners mit einem Ordner Code aufnehmen (Konzept 7.2).
        Gibt die neu gefundenen Projekte zurück."""
        found: list[Project] = []
        try:
            candidates = sorted(p for p in root.iterdir() if p.is_dir())
        except OSError as exc:
            log.warning("Hauptordner nicht lesbar: %s (%s)", root, exc)
            return found
        for folder in candidates:
            if (folder / CODE_DIR).is_dir() and self.find_by_dir(folder) is None:
                found.append(self.add(folder))
        return found

    def remove(self, project_id: int) -> None:
        """Nur aus der Liste des Cockpits entfernen. Ordner und Plattform bleiben unverändert."""
        self.database.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    # -- Features pro Projekt (cockpit.toml) ---------------------------------------------
    def enabled_features(self, project: Project) -> set[str] | None:
        """Die in cockpit.toml eingeschalteten Features. None, wenn dort nichts steht."""
        features = read_config(project.code_dir).get("features", {})
        enabled = features.get("enabled") if isinstance(features, dict) else None
        if not isinstance(enabled, list):
            return None
        return {str(f) for f in enabled}

    def set_enabled_features(self, project: Project, feature_ids: set[str]) -> None:
        if not project.folder_found:
            raise CockpitError(f"Der Ordner von {project.name} wurde nicht gefunden.")
        data = read_config(project.code_dir)
        features = data.get("features") if isinstance(data.get("features"), dict) else {}
        features["enabled"] = sorted(feature_ids)
        data["features"] = features
        write_config(project.code_dir, data)
