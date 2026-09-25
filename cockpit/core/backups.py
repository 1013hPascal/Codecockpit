"""Sicherheitskopien vor Änderungen an Dateien (Konzept 9.7, CLAUDE.md).

Jede Sicherheitskopie ist ein eigener Ordner unter <Datenordner>\\backups mit Datum, Uhrzeit,
Projekt und Anlass im Namen, zum Beispiel "2026-09-25_14-03-12 Tagebuch venv". Kopien, die älter
als 30 Tage sind, löscht das Cockpit beim Start.
"""
from __future__ import annotations

import logging
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from cockpit.core import paths

log = logging.getLogger(__name__)

KEEP_DAYS = 30
_STAMP = "%Y-%m-%d_%H-%M-%S"
_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def backups_dir() -> Path:
    path = paths.data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def new_backup_dir(project_name: str, reason: str) -> Path:
    """Leeren Ordner für eine neue Sicherheitskopie anlegen."""
    name = _UNSAFE.sub("_", f"{datetime.now():{_STAMP}} {project_name} {reason}")
    path = backups_dir() / name
    number = 2
    while path.exists():
        path = backups_dir() / f"{name} {number}"
        number += 1
    path.mkdir(parents=True)
    return path


def move_into_backup(source: Path, project_name: str, reason: str) -> Path:
    """Ordner oder Datei als Sicherheitskopie verschieben. Gibt den neuen Ort zurück."""
    target = new_backup_dir(project_name, reason) / source.name
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
            shutil.rmtree(folder, ignore_errors=True)
            removed += 1
    return removed
