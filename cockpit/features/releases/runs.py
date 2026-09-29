"""Releases und GitHub Actions ohne Qt (Phase 14).

- Zeilen für die Übersichten der Releases und der Läufe, das Wichtigste vorne.
- Die Ausgabe eines fehlgeschlagenen Laufs lesbar machen: ohne Zeitstempel und Farbcodes, nur
  das Ende und die Zeilen mit Fehlern (Frage 5).
- Für die Projektliste merken, welche Repositories einen fehlgeschlagenen letzten Lauf haben
  (Frage 6). Abgefragt wird zusammen mit den Pull Requests.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime

from cockpit.core.errors import CockpitError
from cockpit.core.terminal import clean_line
from cockpit.core.text import count
from cockpit.platforms.base import Release, WorkflowRun

log = logging.getLogger(__name__)

FEATURE_ID = "releases"
FAILED_KEY = "actions.failed"                # Liste von Repository-Schlüsseln
LOG_LINES = 60
_STAMP = re.compile(r"^\d{4}-\d\d-\d\dT[\d:.]+Z ")


def _day(iso: str) -> str:
    try:
        return f"{datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone():%d.%m.%Y}"
    except ValueError:
        return ""


def _time(iso: str) -> str:
    try:
        return f"{datetime.fromisoformat(iso.replace('Z', '+00:00')).astimezone():%d.%m.%Y %H:%M}"
    except ValueError:
        return ""


def release_line(release: Release) -> str:
    """Zum Beispiel "1.4.0, 29.09.2026, 12 Downloads, mit Exe"."""
    parts = [release.tag.lstrip("v") or release.name]
    if _day(release.published):
        parts.append(_day(release.published))
    parts.append(count(release.downloads, "Download", "Downloads"))
    names = [a.name.lower() for a in release.assets]
    if any(n.endswith(".exe") for n in names):
        parts.append("mit Exe")
    elif any(n.endswith(".zip") for n in names):
        parts.append("mit ZIP-Datei")
    else:
        parts.append("nur Quellcode")
    return ", ".join(parts)


def run_line(run: WorkflowRun) -> str:
    """Zum Beispiel "Fehlgeschlagen: Tests, Branch main, 29.09.2026 14:10, Neue Suche"."""
    parts = [f"{run.state_text()}: {run.workflow}", f"Branch {run.branch}"]
    if _time(run.created):
        parts.append(_time(run.created))
    if run.title:
        parts.append(run.title)
    return ", ".join(parts)


def readable_log(text: str, lines: int = LOG_LINES) -> list[str]:
    """Ausgabe eines Laufs: ohne Zeitstempel und Farbcodes. Das Ende und davor alle Zeilen mit
    ##[error], denn dort steht meist der Grund."""
    cleaned = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = clean_line(_STAMP.sub("", raw)).rstrip()
        if line.strip():
            cleaned.append(line.replace("##[error]", "Fehler: ").replace("##[group]", "")
                           .replace("##[endgroup]", "").strip())
    errors = [l for l in cleaned[:-lines] if l.startswith("Fehler: ")]
    return errors + [l for l in cleaned[-lines:] if l]


def remember_failed(database, remote_key: str, failed: bool) -> None:
    keys = set(database.get_value(FAILED_KEY, []) or [])
    keys = keys | {remote_key} if failed else keys - {remote_key}
    database.set_value(FAILED_KEY, sorted(keys))


def last_failed(database, remote_key: str) -> bool:
    return remote_key in set(database.get_value(FAILED_KEY, []) or [])


def refresh_state(services, platform, projects, cancel=None) -> None:
    """Letzten Lauf pro Projekt abfragen, im Hintergrund. Fehler stören andere Projekte nicht.
    Nur für Projekte, in denen das Feature aktiv ist."""
    from cockpit.core import repo_admin
    from cockpit.platforms.base import SupportsActions
    if not isinstance(platform, SupportsActions):
        return
    for project in projects:
        if cancel is not None and cancel.is_set():
            return
        if project.remote is None:
            continue
        try:
            if FEATURE_ID not in services.registry or \
                    not services.features.active(FEATURE_ID, project):
                continue
            runs = platform.workflow_runs(repo_admin.repo_ref(project), limit=1)
        except CockpitError as exc:
            log.warning("GitHub Actions von %s: %s", project.name, exc.message)
            continue
        remember_failed(services.database, project.remote.key, bool(runs) and runs[0].failed)
