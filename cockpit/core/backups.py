"""Sicherheitskopien vor Änderungen an Dateien (Konzept 9.7, CLAUDE.md).

Jede Sicherheitskopie ist ein eigener Ordner unter <Datenordner>\\backups mit Datum, Uhrzeit,
Projekt und Anlass im Namen, zum Beispiel "2026-09-25_14-03-12 Tagebuch vor dem Holen". Kopien, die
älter als 30 Tage sind, löscht das Cockpit beim Start.

In jedem Ordner steht die Datei Sicherheitskopie.txt mit Projekt, Anlass und dem Ordner, aus dem
die Dateien kommen. Darüber findet das Fenster "Sicherheitskopien" (Menü Datei) zurück, wohin eine
Datei beim Wiederherstellen gehört.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import stat
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from cockpit.core import paths
from cockpit.core.errors import CockpitError
from cockpit.core.text import count

log = logging.getLogger(__name__)

KEEP_DAYS = 30
INFO_FILE = "Sicherheitskopie.txt"
_STAMP = "%Y-%m-%d_%H-%M-%S"
_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def remove_tree(path: Path) -> None:
    """Ordner löschen, auch mit schreibgeschützten Dateien (Git legt solche an). Fehler bleiben
    still, der Aufrufer prüft bei Bedarf selbst, ob der Ordner weg ist."""
    def retry(function, name, _error) -> None:
        try:
            os.chmod(name, stat.S_IWRITE)
            function(name)
        except OSError:
            pass
    if path.exists():
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=retry)
        else:
            shutil.rmtree(path, onerror=retry)


def backups_dir() -> Path:
    path = paths.data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def new_backup_dir(project_name: str, reason: str, source_dir: Path | None = None,
                   notes: list[str] | None = None) -> Path:
    """Ordner für eine neue Sicherheitskopie anlegen, nur mit Sicherheitskopie.txt darin.
    source_dir: Ordner, zu dem die Pfade in der Kopie gehören (zum Wiederherstellen)."""
    name = _UNSAFE.sub("_", f"{datetime.now():{_STAMP}} {project_name} {reason}")
    path = backups_dir() / name
    number = 2
    while path.exists():
        path = backups_dir() / f"{name} {number}"
        number += 1
    path.mkdir(parents=True)
    lines = [f"Projekt: {project_name}", f"Anlass: {reason}"]
    if source_dir is not None:
        lines.append(f"Ordner: {source_dir}")
    lines.extend(notes or [])
    (path / INFO_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def move_into_backup(source: Path, project_name: str, reason: str) -> Path:
    """Ordner oder Datei als Sicherheitskopie verschieben. Gibt den neuen Ort zurück."""
    target = new_backup_dir(project_name, reason, source.parent) / source.name
    shutil.move(str(source), str(target))
    log.info("Sicherheitskopie: %s nach %s", source, target)
    return target


def remove_old(now: datetime | None = None) -> int:
    """Sicherheitskopien löschen, die älter als 30 Tage sind. Gibt die Anzahl zurück."""
    limit = (now or datetime.now()) - timedelta(days=KEEP_DAYS)
    removed = 0
    for folder in backups_dir().iterdir():
        try:
            created = datetime.strptime(folder.name[:19], _STAMP)
        except ValueError:
            continue                                   # fremder Ordner: nie anfassen
        if created < limit:
            remove_tree(folder)
            removed += 1
    return removed


# -- Fenster "Sicherheitskopien" ------------------------------------------------------------------
@dataclass
class BackupInfo:
    path: Path
    created: datetime
    project: str
    reason: str
    source_dir: Path | None = None
    notes: list[str] = field(default_factory=list)

    def files(self) -> list[str]:
        """Alle Dateien der Kopie, relativ und mit /, ohne Sicherheitskopie.txt."""
        return sorted(p.relative_to(self.path).as_posix() for p in self.path.rglob("*")
                      if p.is_file() and p != self.path / INFO_FILE)

    def line(self) -> str:
        """Zeile für die Liste, das Datum vorne: "25.09.2026 14:03, Tagebuch, vor dem Holen,
        1 Datei"."""
        parts = [f"{self.created:%d.%m.%Y %H:%M}", self.project]
        if self.reason:
            parts.append(self.reason)
        parts.append(count(len(self.files()), "Datei", "Dateien"))
        return ", ".join(parts)


def read_info(folder: Path) -> BackupInfo | None:
    """Angaben zu einer Sicherheitskopie. None bei fremden Ordnern."""
    try:
        created = datetime.strptime(folder.name[:19], _STAMP)
    except ValueError:
        return None
    info = BackupInfo(folder, created, folder.name[20:], "")
    try:
        text = (folder / INFO_FILE).read_text(encoding="utf-8")
    except OSError:
        return info                       # ältere Kopie ohne Angaben
    for line in text.splitlines():
        key, _, value = line.partition(": ")
        if key == "Projekt":
            info.project = value
        elif key == "Anlass":
            info.reason = value
        elif key == "Ordner" and value:
            info.source_dir = Path(value)
        elif line.strip():
            info.notes.append(line)
    return info


def all_backups() -> list[BackupInfo]:
    """Alle Sicherheitskopien, die neueste zuerst."""
    found = [read_info(f) for f in backups_dir().iterdir() if f.is_dir()]
    return sorted((i for i in found if i is not None), key=lambda i: i.path.name, reverse=True)


def restore_target(info: BackupInfo, relative: str) -> Path:
    """Wohin die Datei beim Wiederherstellen kommt."""
    if info.source_dir is None:
        raise CockpitError("Bei dieser Sicherheitskopie ist nicht bekannt, woher die Dateien "
                           "kommen. Sie können die Datei öffnen und von Hand zurückkopieren.")
    return info.source_dir / relative


def restore(info: BackupInfo, relative: str) -> Path | None:
    """Eine Datei zurückholen. Gibt es sie am Ziel noch, kommt die jetzige Fassung vorher selbst
    in eine neue Sicherheitskopie. Gibt deren Ordner zurück, sonst None."""
    source = info.path / relative
    target = restore_target(info, relative)
    if not source.is_file():
        raise CockpitError(f"{relative} ist nicht mehr in der Sicherheitskopie.")
    before = None
    if target.exists():
        before = new_backup_dir(info.project, "vor dem Wiederherstellen", info.source_dir)
        copy = before / relative
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, copy)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    log.info("Wiederhergestellt: %s aus %s", target, info.path)
    return before


def delete(info: BackupInfo) -> None:
    """Sicherheitskopie löschen (nach Rückfrage in der Oberfläche)."""
    remove_tree(info.path)
    if info.path.exists():
        raise CockpitError("Die Sicherheitskopie ließ sich nicht ganz löschen. Vielleicht ist "
                           "eine Datei daraus noch geöffnet.")
