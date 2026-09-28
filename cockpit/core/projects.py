"""Projekte und ihre Ordner (Konzept 7).

Jedes Projekt hat einen Projektordner mit den Unterordnern Code (das Git-Repository) und Exe.
Die Projekteinstellungen stehen ohne Geheimnisse in Code\\cockpit.toml und werden mitversioniert.
Die Zuordnung von Projekt und Pfad steht in der Datenbank.

Projekte kommen auf diesen Wegen in die Liste (Konzept 7.3 und 7.4):
- Im Projekte-Hauptordner gefunden oder als Projektordner mit Unterordner Code hinzugefügt.
- Umgestellt: Ein Ordner ohne Unterordner Code wird als Code in einen neuen Projektordner
  verschoben.
- Nur verknüpft: Code-Ordner und Exe-Ordner bleiben, wo sie sind (linked).
"""
from __future__ import annotations

import logging
import os
import shutil
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import tomli_w

from cockpit.core.database import Database
from cockpit.core.errors import CockpitError
from cockpit.core.git import RemoteAddress

log = logging.getLogger(__name__)

CODE_DIR = "Code"
EXE_DIR = "Exe"
CONFIG_NAME = "cockpit.toml"
REMOVED_KEY = "projects.removed"       # aus der Liste entfernte Ordner (Phase 5e)


@dataclass(frozen=True)
class Project:
    id: int
    name: str
    project_dir: Path
    code_dir: Path
    exe_dir: Path | None                 # None: verknüpftes Projekt ohne Exe-Ordner
    account_id: int | None = None
    last_updated: str | None = None      # Datum des letzten hochgeladenen Commits
    linked: bool = False                 # nur verknüpft, die Ordner stehen einzeln
    remote: RemoteAddress | None = None  # Adresse auf der Plattform, zuletzt gesehen

    @property
    def folder_found(self) -> bool:
        return self.code_dir.is_dir()

    @property
    def code_root(self) -> Path:
        """Der Ordner Code. Bei einem Ordner pro Branch (Phase 10f) liegt code_dir darin."""
        return self.code_dir.parent if self.has_branch_folders else self.code_dir

    @property
    def has_branch_folders(self) -> bool:
        """Code enthält nur Ordner: den Haupt-Branch, zum Beispiel Code\\main, und die Branches."""
        return (not self.linked and self.code_dir.parent.name.lower() == CODE_DIR.lower()
                and self.code_dir.parent.parent == self.project_dir)

    @property
    def has_exe_dir(self) -> bool:
        return self.exe_dir is not None and self.exe_dir.is_dir()

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
        linked = bool(row["linked"])
        if row["exe_dir"]:
            exe_dir = Path(row["exe_dir"])
        else:
            exe_dir = None if linked else project_dir / EXE_DIR
        remote = (RemoteAddress(row["remote_host"], row["remote_owner"], row["remote_name"])
                  if row["remote_name"] else None)
        return Project(
            id=row["id"], name=row["name"], project_dir=project_dir,
            code_dir=Path(row["code_dir"]), exe_dir=exe_dir,
            account_id=row["account_id"], last_updated=row["last_updated"], linked=linked,
            remote=remote)

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

    def find_by_code_dir(self, code_dir: Path) -> Project | None:
        row = self.database.query_one("SELECT * FROM projects WHERE code_dir = ?",
                                      (str(code_dir.resolve()),))
        return self._from_row(row) if row else None

    # -- Ändern --------------------------------------------------------------------------
    def add(self, project_dir: Path) -> Project:
        """Einen Projektordner mit Unterordner Code aufnehmen. Schon vorhandene bleiben gleich."""
        project_dir = project_dir.resolve()
        self.forget_removed(project_dir)
        existing = self.find_by_dir(project_dir)
        if existing is not None:
            return existing
        if not (project_dir / CODE_DIR).is_dir():
            raise CockpitError(f"Im Ordner {project_dir} gibt es keinen Unterordner Code.")
        code_dir = main_code_dir(project_dir / CODE_DIR)
        self.database.execute(
            "INSERT INTO projects (name, project_dir, code_dir, exe_dir, added_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (project_dir.name, str(project_dir), str(code_dir), str(project_dir / EXE_DIR),
             datetime.now().isoformat(timespec="seconds")))
        return self.find_by_dir(project_dir)

    def add_linked(self, code_dir: Path, exe_dir: Path | None = None) -> Project:
        """Nur verknüpfen (Konzept 7.4): Die Ordner bleiben, wo sie sind."""
        code_dir = code_dir.resolve()
        self.forget_removed(code_dir)
        existing = self.find_by_dir(code_dir) or self.find_by_code_dir(code_dir)
        if existing is not None:
            return existing
        if not code_dir.is_dir():
            raise CockpitError(f"Den Ordner {code_dir} gibt es nicht.")
        self.database.execute(
            "INSERT INTO projects (name, project_dir, code_dir, exe_dir, added_at, linked) "
            "VALUES (?, ?, ?, ?, ?, 1)",
            (code_dir.name, str(code_dir), str(code_dir),
             str(exe_dir.resolve()) if exe_dir else None,
             datetime.now().isoformat(timespec="seconds")))
        return self.find_by_dir(code_dir)

    def convert(self, folder: Path, root: Path, inner: str = "") -> tuple[Project, bool]:
        """Umstellen (Konzept 7.4): Projektordner root/<Name> anlegen und folder als Code
        hineinverschieben. Auf einem anderen Laufwerk wird kopiert, der alte Ordner bleibt dann
        unverändert. Gibt das Projekt zurück und ob verschoben (True) oder kopiert wurde.
        inner: Ordner des Haupt-Branches in Code, zum Beispiel "main" (Phase 10f)."""
        folder = folder.resolve()
        target = root / folder.name
        if target.exists():
            raise CockpitError(f"Den Ordner {target} gibt es schon. Bitte benennen Sie zuerst "
                               "einen der Ordner um.")
        target.mkdir(parents=True)
        code_dir = target / CODE_DIR
        if inner:
            code_dir.mkdir()
            code_dir = code_dir / inner
        moved = same_drive(folder, target)
        try:
            if moved:
                os.rename(folder, code_dir)         # ändert keinen Inhalt, nur den Ort
            else:
                shutil.copytree(folder, code_dir, symlinks=True)
        except OSError as exc:
            if not moved:
                from cockpit.core.backups import remove_tree
                remove_tree(code_dir)
            for empty in ((target / CODE_DIR, target) if inner else (target,)):
                try:
                    empty.rmdir()
                except OSError:
                    pass
            raise CockpitError("Der Ordner ließ sich nicht umstellen. Ist er noch in einem "
                               "anderen Programm geöffnet?", str(exc)) from None
        return self.add(target), moved

    def relocate(self, project: Project, new_dir: Path) -> Project:
        """Neuen Ort angeben (Konzept 7.2). Bei verknüpften Projekten ist new_dir der Code-Ordner,
        sonst der Projektordner mit Unterordner Code (oder dieser Unterordner selbst)."""
        new_dir = new_dir.resolve()
        if project.linked:
            project_dir = code_dir = new_dir
            exe_dir = str(project.exe_dir) if project.exe_dir else None
        else:
            kind, project_dir = classify_folder(new_dir)
            code_dir = main_code_dir(project_dir / CODE_DIR)
            exe_dir = str(project_dir / EXE_DIR)
            if kind != "project":
                raise CockpitError(f"Im Ordner {new_dir} gibt es keinen Unterordner Code.")
        if not code_dir.is_dir():
            raise CockpitError(f"Den Ordner {code_dir} gibt es nicht.")
        other = self.find_by_dir(project_dir)
        if other is not None and other.id != project.id:
            raise CockpitError(f"Der Ordner gehört schon zum Projekt {other.name}.")
        self.database.execute(
            "UPDATE projects SET project_dir = ?, code_dir = ?, exe_dir = ? WHERE id = ?",
            (str(project_dir), str(code_dir), exe_dir, project.id))
        return self.get(project.id)

    def set_remote(self, project: Project, remote: RemoteAddress | None,
                   last_updated: str | None) -> None:
        """Adresse auf der Plattform und Datum des letzten Hochladens merken."""
        self.database.execute(
            "UPDATE projects SET remote_host = ?, remote_owner = ?, remote_name = ?, "
            "last_updated = ? WHERE id = ?",
            (remote.host if remote else "", remote.owner if remote else "",
             remote.name if remote else "", last_updated or None, project.id))

    def set_exe_dir(self, project: Project, exe_dir: Path) -> Project:
        """Exe-Ordner eines verknüpften Projekts festlegen (Phase 10, "Exe hinzufügen")."""
        self.database.execute("UPDATE projects SET exe_dir = ? WHERE id = ?",
                              (str(exe_dir.resolve()), project.id))
        return self.get(project.id)

    def set_code_dir(self, project: Project, code_dir: Path) -> Project:
        """Nach dem Einrichten der Branch-Ordner liegt der Code in Code\\main (Phase 10f)."""
        self.database.execute("UPDATE projects SET code_dir = ? WHERE id = ?",
                              (str(code_dir.resolve()), project.id))
        return self.get(project.id)

    def set_account(self, project: Project, account_id: int | None) -> None:
        self.database.execute("UPDATE projects SET account_id = ? WHERE id = ?",
                              (account_id, project.id))

    def scan(self, root: Path) -> list[Project]:
        """Alle Unterordner des Hauptordners mit einem Ordner Code aufnehmen (Konzept 7.2).
        Gibt die neu gefundenen Projekte zurück."""
        found: list[Project] = []
        try:
            candidates = sorted(p for p in root.iterdir() if p.is_dir())
        except OSError as exc:
            log.warning("Hauptordner nicht lesbar: %s (%s)", root, exc)
            return found
        removed = self.removed_dirs()
        for folder in candidates:
            if _key(folder) in removed:
                continue                        # "Aus der Liste entfernen" gilt weiter
            if (folder / CODE_DIR).is_dir() and self.find_by_dir(folder) is None:
                found.append(self.add(folder))
        return found

    def remove(self, project_id: int) -> None:
        """Nur aus der Liste des Cockpits entfernen. Ordner und Plattform bleiben unverändert.
        Das Cockpit merkt sich den Ordner, damit ihn das Durchsuchen des Hauptordners nicht
        wieder aufnimmt. Wer ihn selbst wieder hinzufügt, hebt das auf."""
        project = self.get(project_id)
        self.database.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        if project is not None:
            removed = self.removed_dirs() | {_key(project.project_dir)}
            self.database.set_value(REMOVED_KEY, sorted(removed))

    def removed_dirs(self) -> set[str]:
        return set(self.database.get_value(REMOVED_KEY, []) or [])

    def forget_removed(self, folder: Path) -> None:
        removed = self.removed_dirs()
        if _key(folder) in removed:
            removed.discard(_key(folder))
            self.database.set_value(REMOVED_KEY, sorted(removed))

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


# -- Hilfen zum Hinzufügen -------------------------------------------------------------------
def _key(folder: Path) -> str:
    """Vergleichbarer Schlüssel eines Ordners, ohne Groß- und Kleinschreibung (Windows)."""
    return str(Path(folder).resolve()).lower()


def main_code_dir(code_root: Path) -> Path:
    """Der Arbeitsordner des Haupt-Branches (Phase 10f). Hat Code selbst kein Git, aber ein
    Unterordner einen Ordner .git (nicht nur eine Datei wie die Branch-Ordner), ist er es.
    Sonst ist es Code selbst, wie bisher."""
    if (code_root / ".git").exists():
        return code_root
    try:
        for child in sorted(code_root.iterdir()):
            if child.is_dir() and (child / ".git").is_dir():
                return child
    except OSError:
        pass
    return code_root


def classify_folder(folder: Path) -> tuple[str, Path]:
    """Was für ein Ordner wurde gewählt?

    ("project", Projektordner): enthält einen Unterordner Code.
    ("project", Projektordner): ist selbst der Ordner Code eines Projekts.
    ("other", folder): passt nicht zum Aufbau, Umstellen oder Verknüpfen nötig."""
    folder = folder.resolve()
    if (folder / CODE_DIR).is_dir():
        return "project", folder
    if folder.name.lower() == CODE_DIR.lower() and folder.parent != folder:
        return "project", folder.parent
    if folder.parent.name.lower() == CODE_DIR.lower() and (folder / ".git").exists() \
            and folder.parent.parent != folder.parent:
        return "project", folder.parent.parent        # Code\main oder ein Branch-Ordner
    return "other", folder


def same_drive(a: Path, b: Path) -> bool:
    return a.resolve().drive.lower() == b.resolve().drive.lower()
