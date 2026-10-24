"""Bekannte Sicherheitslücken in Python-Bibliotheken (Stufe 3 der Paketübersicht).

Die freie Datenbank OSV (osv.dev) beantwortet für Name und Version, ob eine Lücke bekannt ist,
und in welcher Version sie behoben ist. Gesendet werden nur Namen und Versionen von Bibliotheken,
nie Code oder Geheimnisse.
"""
from __future__ import annotations

import logging

from cockpit.features.packages import web
from cockpit.features.packages.base import Package, version_key

log = logging.getLogger(__name__)

BATCH = "https://api.osv.dev/v1/querybatch"
DETAILS = "https://api.osv.dev/v1/vulns/{}"
MAX_BATCH = 500


def fixed_versions(vuln: dict) -> list[str]:
    found = []
    for affected in vuln.get("affected", []):
        for span in affected.get("ranges", []):
            found += [e["fixed"] for e in span.get("events", []) if "fixed" in e]
    return found


def mark(packages: list[Package]) -> int:
    """warning setzen, wenn eine Lücke bekannt ist. Gibt die Zahl der betroffenen zurück.
    Ohne Internet bleibt alles, wie es ist."""
    hits = 0
    for start in range(0, len(packages), MAX_BATCH):
        part = packages[start:start + MAX_BATCH]
        body = {"queries": [{"package": {"name": p.name, "ecosystem": "PyPI"},
                             "version": p.version} for p in part]}
        answer = web.post_json(BATCH, body)
        if not answer:
            return hits
        for package, result in zip(part, answer.get("results", [])):
            ids = [v.get("id") for v in result.get("vulns") or [] if v.get("id")]
            if not ids:
                continue
            hits += 1
            fixes = []
            for vuln_id in ids[:5]:
                details = web.get_json(DETAILS.format(vuln_id)) or {}
                fixes += [f for f in fixed_versions(details)
                          if version_key(f) > version_key(package.version)]
            fix = min(fixes, key=version_key) if fixes else ""
            package.warning = "Sicherheitslücke bekannt" + (f", behoben in {fix}" if fix else "")
            package.extra["vulnerabilities"] = ids
    return hits
