"""Projekte und ihre Ordner (Konzept 7).

Jedes Projekt hat einen Projektordner mit den Unterordnern Code (das Git-Repository) und Exe.
Die Projekteinstellungen stehen ohne Geheimnisse in Repository\\cockpit.toml und werden mitversioniert.
Die Zuordnung von Projekt und Pfad steht in der Datenbank.

Projekte kommen auf diesen Wegen in die Liste (Konzept 7.3 und 7.4):
- Im Projekte-Hauptordner gefunden oder als Projektordner mit Unterordner Repository hinzugefügt.
- Umgestellt: Ein Ordner ohne Unterordner Repository wird als Code in einen neuen Projektordner
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

# Antwort des Nutzers (06.10.2026): Code heißt jetzt Repository, Exe heißt Release. Projekte mit
# den alten Namen funktionieren weiter, bis das Cockpit ihre Ordner umbenannt hat.
CODE_DIR = "Repository"
EXE_DIR = "Release"
OLD_CODE_DIR = "Code"
OLD_EXE_DIR = "Exe"
CODE_NAMES = (CODE_DIR, OLD_CODE_DIR)
CONFIG_NAME = "cockpit.toml"
REMOVED_KEY = "projects.removed"       # aus der Liste entfernte Ordner (Phase 5e)


def is_code_name(name: str) -> bool:
    """Heißt der Ordner Repository oder noch Code?"""
    return name.lower() in (n.lower() for n in CODE_NAMES)


def code_root_in(project_dir: Path) -> Path:
    """Der Ordner Repository des Projekts, bei alten Projekten noch Code."""
    for name in CODE_NAMES:
        if (project_dir / name).is_dir():
            return project_dir / name
    return project_dir / CODE_DIR


def exe_dir_in(project_dir: Path) -> Path:
    """Der Ordner Release des Projekts. Bei alten Projekten Exe, solange es Release nicht gibt."""
    if (project_dir / EXE_DIR).is_dir():
        return project_dir / EXE_DIR
    old = project_dir / OLD_EXE_DIR
    if old.is_dir() or code_root_in(project_dir).name == OLD_CODE_DIR:
        return old
    return project_dir / EXE_DIR


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
        """Der Ordner Repository. Bei einem Ordner pro Branch (Phase 10f) liegt code_dir darin."""
        return self.code_dir.parent if self.has_branch_folders else self.code_dir

    @property
    def has_branch_folders(self) -> bool:
        """Code enthält nur Ordner: den Haupt-Branch, zum Beispiel Repository\\main, und die Branches."""
        return (not self.linked and is_code_name(self.code_dir.parent.name)
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
            exe_dir = None if linked else exe_dir_in(project_dir)
        remote = (RemoteAddress(row["remote_host"], row["remote_owner"], row["remote_name"])
                  if row["remote_name"] else None)
        return Project(
            id=row["id"], name=row["name"], project_dir=project_dir,
            code_dir=Path(row["code_dir"]), exe_dir=exe_dir,
            account_id=row["account_id"], last_updated=row["last_updated"], linked=linked,
            remote=remote)

    def all(self) -> list[Project]:
        """Alle Projekte, zuletzt aktualisierte oben. Liegt der Code inzwischen in Repository\\main,
        merkt sich das Cockpit den neuen Ort (Rückmeldung des Nutzers vom 04.10.2026: nach dem
        Verschieben von Hand hieß die Zeile weiter Code)."""
        projects = []
        for row in self.database.query("SELECT * FROM projects"):
            project = self._from_row(row)
            if not project.linked and project.code_dir == code_root_in(project.project_dir):
                found = main_code_dir(project.code_dir)
                if found != project.code_dir:
                    project = self.set_code_dir(project, found)
            projects.append(project)
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
        """Einen Projektordner mit Unterordner Repository aufnehmen. Schon vorhandene bleiben gleich."""
        project_dir = project_dir.resolve()
        self.forget_removed(project_dir)
        existing = self.find_by_dir(project_dir)
        if existing is not None:
            return existing
        if not code_root_in(project_dir).is_dir():
            raise CockpitError(f"Im Ordner {project_dir} gibt es keinen Unterordner "
                               f"{CODE_DIR}.")
        code_dir = main_code_dir(code_root_in(project_dir))
        self.database.execute(
            "INSERT INTO projects (name, project_dir, code_dir, exe_dir, added_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (project_dir.name, str(project_dir), str(code_dir), str(exe_dir_in(project_dir)),
             datetime.now().isoformat(timespec="seconds")))
        return self.find_by_dir(project_dir)

    def create_layout(self, project_dir: Path) -> Project:
        """Im gewählten Ordner Repository\\main und Release leer anlegen und ihn als Projekt
        aufnehmen (Wunsch des Nutzers vom 14.10.2026: Unterordner mit anderen Namen als Code und
        Exe). Was schon im Ordner liegt, bleibt unverändert. Den Code kopiert der Nutzer selbst
        nach Repository\\main."""
        project_dir = project_dir.resolve()
        if code_root_in(project_dir).is_dir():
            raise CockpitError(f"Im Ordner {project_dir.name} gibt es schon den Ordner "
                               f"{code_root_in(project_dir).name}.")
        try:
            (project_dir / CODE_DIR / MAIN_DIR).mkdir(parents=True)
            (project_dir / EXE_DIR).mkdir(exist_ok=True)
        except OSError as exc:
            raise CockpitError("Die Ordner ließen sich nicht anlegen.", str(exc)) from None
        return self.add(project_dir)

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
        sonst der Projektordner mit Unterordner Repository (oder dieser Unterordner selbst)."""
        new_dir = new_dir.resolve()
        if project.linked:
            project_dir = code_dir = new_dir
            exe_dir = str(project.exe_dir) if project.exe_dir else None
        else:
            kind, project_dir = classify_folder(new_dir)
            code_dir = main_code_dir(code_root_in(project_dir))
            exe_dir = str(exe_dir_in(project_dir))
            if kind != "project":
                raise CockpitError(f"Im Ordner {new_dir} gibt es keinen Unterordner "
                                   f"{CODE_DIR}.")
        if not code_dir.is_dir():
            raise CockpitError(f"Den Ordner {code_dir} gibt es nicht.")
        other = self.find_by_dir(project_dir)
        if other is not None and other.id != project.id:
            raise CockpitError(f"Der Ordner gehört schon zum Projekt {other.name}.")
        self.database.execute(
            "UPDATE projects SET project_dir = ?, code_dir = ?, exe_dir = ? WHERE id = ?",
            (str(project_dir), str(code_dir), exe_dir, project.id))
        return self.get(project.id)

    def rename(self, project: Project, name: str, project_dir: Path, code_dir: Path,
               exe_dir: Path | None) -> Project:
        """Neuer Name und neue Orte nach "Projekt umbenennen" (06.10.2026)."""
        self.database.execute(
            "UPDATE projects SET name = ?, project_dir = ?, code_dir = ?, exe_dir = ? "
            "WHERE id = ?",
            (name, str(project_dir), str(code_dir), str(exe_dir) if exe_dir else None,
             project.id))
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
        """Nach dem Einrichten der Branch-Ordner liegt der Code in Repository\\main (Phase 10f)."""
        self.database.execute("UPDATE projects SET code_dir = ? WHERE id = ?",
                              (str(code_dir.resolve()), project.id))
        return self.get(project.id)

    def set_account(self, project: Project, account_id: int | None) -> None:
        self.database.execute("UPDATE projects SET account_id = ? WHERE id = ?",
                              (account_id, project.id))

    def scan(self, root: Path) -> list[Project]:
        """Alle Unterordner des Hauptordners mit einem Ordner Repository aufnehmen (Konzept 7.2).
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
            if code_root_in(folder).is_dir() and self.find_by_dir(folder) is None:
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
    Ohne Git zählt auch ein Unterordner main (Wunsch des Nutzers vom 04.10.2026). Sonst ist es
    Code selbst, wie bisher."""
    if (code_root / ".git").exists():
        return code_root
    try:
        children = sorted(code_root.iterdir())
    except OSError:
        return code_root
    for child in children:
        if child.is_dir() and (child / ".git").is_dir():
            return child
    # Nur wenn in Code sonst nichts liegt: ein Paket namens main im Code zählt nicht
    if (code_root / MAIN_DIR).is_dir() and all(p.name == MAIN_DIR or p.name.startswith(".")
                                               for p in children):
        return code_root / MAIN_DIR
    return code_root


# -- Aufbau Projektordner\Repository\main und Projektordner\Exe (Wunsch des Nutzers, 04.10.2026) ----
MAIN_DIR = "main"
GIT_OUTSIDE, FLAT = "git_outside", "flat"


def layout_problem(code_root: Path) -> str:
    """GIT_OUTSIDE: Der Code liegt schon in Repository\\main, der Git-Ordner .git aber noch in Code
    (zum Beispiel nach dem Verschieben von Hand). FLAT: Der Code liegt direkt in Repository. Leer:
    alles passt."""
    try:
        names = {p.name for p in code_root.iterdir()}
    except OSError:
        return ""
    main = code_root / MAIN_DIR
    if ".git" in names and main.is_dir() and not (main / ".git").exists() \
            and names <= {".git", MAIN_DIR}:
        return GIT_OUTSIDE
    if main_code_dir(code_root) == code_root and any(not n.startswith(".") or n == ".git"
                                                     for n in names):
        return FLAT
    return ""


def fix_git_outside(code_root: Path) -> Path:
    """Den Git-Ordner zum Code nach Repository\\main verschieben. Am Inhalt ändert sich nichts."""
    if layout_problem(code_root) != GIT_OUTSIDE:
        raise CockpitError("Der Ordner Repository hat nicht den erwarteten Aufbau.")
    try:
        os.rename(code_root / ".git", code_root / MAIN_DIR / ".git")
    except OSError as exc:
        raise CockpitError("Der Git-Ordner ließ sich nicht verschieben. Ist der Ordner noch in "
                           "einem anderen Programm geöffnet?", str(exc)) from None
    return code_root / MAIN_DIR


def nest_code(code_root: Path, name: str = MAIN_DIR) -> Path:
    """Den Code, der direkt in Repository liegt, nach Repository\\<name> verschieben. Nur der Ort ändert
    sich. Klappt ein Teil nicht, kommt alles zurück."""
    target = code_root / name
    if target.exists():
        raise CockpitError(f"Den Ordner {target} gibt es schon.")
    children = [p for p in code_root.iterdir()]
    target.mkdir()
    moved: list[Path] = []
    try:
        for child in children:
            os.rename(child, target / child.name)
            moved.append(child)
    except OSError as exc:
        for child in moved:
            try:
                os.rename(target / child.name, child)
            except OSError:
                log.exception("Zurückverschieben fehlgeschlagen: %s", child)
        try:
            target.rmdir()
        except OSError:
            pass
        raise CockpitError("Der Code ließ sich nicht verschieben. Ist der Ordner noch in einem "
                           "anderen Programm geöffnet?", str(exc)) from None
    return target


def classify_folder(folder: Path) -> tuple[str, Path]:
    """Was für ein Ordner wurde gewählt?

    ("project", Projektordner): enthält einen Unterordner Repository.
    ("project", Projektordner): ist selbst der Ordner Repository eines Projekts.
    ("other", folder): passt nicht zum Aufbau, Umstellen oder Verknüpfen nötig."""
    folder = folder.resolve()
    if code_root_in(folder).is_dir():
        return "project", folder
    if is_code_name(folder.name) and folder.parent != folder:
        return "project", folder.parent
    if is_code_name(folder.parent.name) and (folder / ".git").exists() \
            and folder.parent.parent != folder.parent:
        return "project", folder.parent.parent        # Repository\main oder ein Branch-Ordner
    return "other", folder


def same_drive(a: Path, b: Path) -> bool:
    return a.resolve().drive.lower() == b.resolve().drive.lower()
