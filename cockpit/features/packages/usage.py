"""Wer benutzt was (Stufe 2 der Paketübersicht).

- Bibliotheken im globalen Python: Projekte, deren requirements.txt sie nennt.
- Modelle: Projekte, in deren Code oder Einstellungen der Name des Modells steht, und die
  KI-Verwaltung des Cockpits (Ollama-Modelle). Gesucht wird in Code- und Einstellungsdateien,
  nicht in .env und anderen vertraulichen Dateien, und nicht in Umgebungen, .git und Build-Ordnern.

Ein Modell ohne Benutzer bekommt "von keinem Projekt benutzt". Das ist ein Hinweis, kein Beweis:
Ein Programm außerhalb der Projekte kann es trotzdem brauchen.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from cockpit.features.packages import models
from cockpit.features.packages.base import MODEL, PIP, Package

log = logging.getLogger(__name__)

TEXT_SUFFIXES = (".py", ".pyw", ".toml", ".json", ".yaml", ".yml", ".cfg", ".ini", ".txt", ".md")
SKIP_DIRS = {".git", ".venv", "venv", "env", "__pycache__", "node_modules", "build", "dist",
             ".mypy_cache", ".pytest_cache", "site-packages"}
MAX_FILE_BYTES = 1_000_000
MAX_FILES = 3000


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_names(path: Path) -> set[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return set()
    found = set()
    for line in lines:
        line = line.split("#", 1)[0].strip()
        match = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if match and not line.startswith("-"):
            found.add(normalize(match.group(1)))
    return found


def project_texts(project) -> str:
    """Der Text der Code- und Einstellungsdateien eines Projekts, klein geschrieben."""
    from cockpit.features.ai_assistant.context import confidential
    parts, seen = [], 0
    root = project.code_dir
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if seen >= MAX_FILES:
                return "\n".join(parts)
            path = Path(folder) / name
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            relative = path.relative_to(root).as_posix()
            if confidential(relative):
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
                parts.append(path.read_text(encoding="utf-8", errors="replace").lower())
                seen += 1
            except OSError:
                continue
    return "\n".join(parts)


def model_names(package: Package) -> list[str]:
    """Wonach im Code gesucht wird, klein geschrieben."""
    name = package.id.lower()
    if package.kind == models.HF:
        return [name, name.split("/", 1)[-1]]
    if package.kind == models.OLLAMA:
        base = name.rsplit(":", 1)[0]
        names = [name]
        if name.endswith(":latest"):
            names.append(base)
        return names
    if package.kind == models.FILE:
        return [package.name.lower()]
    return []


def _contains(text: str, word: str) -> bool:
    return re.search(r"(?<![\w.-])" + re.escape(word) + r"(?![\w-])", text) is not None


def mark(source: str, packages: list[Package], projects, services=None) -> None:
    """used_by setzen. Läuft im Hintergrund."""
    if source == PIP:
        wanted = {}
        for project in projects:
            for name in requirement_names(project.code_dir / "requirements.txt"):
                wanted.setdefault(name, []).append(project.name)
        for package in packages:
            if package.extra.get("project_id") is None and not package.cockpit:
                package.used_by = tuple(wanted.get(normalize(package.name), ()))
        return
    if source != MODEL:
        return
    texts = {p.name: project_texts(p) for p in projects if p.code_dir.is_dir()}
    cockpit_models = set()
    if services is not None:
        try:
            cockpit_models = {t.model.lower() for t in services.ai_tools.all() if t.model}
        except Exception as exc:                  # KI-Verwaltung nicht lesbar
            log.info("KI-Werkzeuge: %r", exc)
    for package in packages:
        if package.kind == models.OWN:
            continue
        names = model_names(package)
        users = [project for project, text in texts.items()
                 if any(_contains(text, n) for n in names)]
        if package.kind == models.OLLAMA and package.id.lower() in cockpit_models | {
                m + ":latest" for m in cockpit_models}:
            users.insert(0, "KI-Verwaltung des Cockpits")
        package.used_by = tuple(users)
        package.extra["unused"] = not users
