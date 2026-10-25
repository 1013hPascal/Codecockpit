"""Gespeicherte Liste der Paketübersicht (Wunsch des Nutzers vom 24.10.2026).

Ist die Liste einmal gelesen und geprüft, merkt sich das Cockpit sie in der Datenbank. Beim
nächsten Öffnen, auch nach einem Neustart, steht sie sofort da. Neu gelesen wird nur mit
"Aktualisieren" und nach einer Änderung an einem Paket (dann nur die betroffene Quelle).
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, fields
from datetime import datetime
from pathlib import Path

from cockpit.features.packages.base import Package

log = logging.getLogger(__name__)

KEY = "packages.cache"


def _plain(package: Package) -> dict:
    data = asdict(package)
    data["location"] = str(package.location) if package.location is not None else None
    data["added"] = package.added.isoformat() if package.added is not None else None
    data["used_by"] = list(package.used_by)
    return data


def _package(data: dict) -> Package:
    known = {f.name for f in fields(Package)}
    values = {k: v for k, v in data.items() if k in known}
    if values.get("location"):
        values["location"] = Path(values["location"])
    if values.get("added"):
        values["added"] = datetime.fromisoformat(values["added"])
    values["used_by"] = tuple(values.get("used_by") or ())
    return Package(**values)


def save(database, data: dict[str, list[Package] | None], checked: set[str],
         now: datetime | None = None) -> None:
    """Nur fertig gelesene Quellen. Was nicht in JSON passt, wird zu Text."""
    stored = {source: [_plain(p) for p in packages]
              for source, packages in data.items() if packages is not None}
    value = {"saved": (now or datetime.now()).isoformat(timespec="minutes"),
             "checked": sorted(checked & set(stored)), "data": stored}
    database.set_value(KEY, json.loads(json.dumps(value, default=str)))


def load(database) -> tuple[dict[str, list[Package]], set[str], datetime | None]:
    """Gespeicherte Quellen, geprüfte Quellen und Zeitpunkt. Leer, wenn nichts oder Unlesbares
    gespeichert ist."""
    raw = database.get_value(KEY, None)
    if not isinstance(raw, dict):
        return {}, set(), None
    try:
        data = {source: [_package(p) for p in packages]
                for source, packages in (raw.get("data") or {}).items()}
        saved = datetime.fromisoformat(raw["saved"]) if raw.get("saved") else None
    except (TypeError, ValueError, KeyError) as exc:
        log.warning("Gespeicherte Paketliste unlesbar: %r", exc)
        return {}, set(), None
    return data, set(raw.get("checked") or ()), saved
