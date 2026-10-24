"""Aufräumen (Stufe 2 der Paketübersicht): wo Platz frei werden kann.

- Umgebungen für den Exe-Bau, deren Projekt nicht mehr in der Liste steht.
- Der Zwischenspeicher von pip. pip lädt daraus nur schneller, nötig ist er nicht.
- Unvollständige Downloads bei Hugging Face.
- Alte Fassungen von Modellen bei Hugging Face.
- Modelle, die kein Projekt und nicht das Cockpit benutzt. Das ist nur ein Hinweis: Ein Programm
  außerhalb der Projekte kann sie trotzdem brauchen. Deshalb ist nichts vorab angehakt.

Vor dem Löschen kommt eine Liste in die Sicherheitskopien (record.save_list).
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from cockpit.core import backups, paths
from cockpit.features.packages import models, record
from cockpit.features.packages.base import MODEL, Package, folder_size, size_text
from cockpit.core.text import count

log = logging.getLogger(__name__)


@dataclass
class Candidate:
    text: str                                  # Zeile in der Liste, das Wichtigste vorne
    size: int
    remove: Callable[[], None]
    packages: list[Package] = field(default_factory=list)   # für die Liste vor dem Löschen

    def line(self) -> str:
        return f"{self.text}, {size_text(self.size)}"


def pip_cache_dir() -> Path:
    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return Path(os.environ.get("PIP_CACHE_DIR", local / "pip" / "cache"))


def _empty_folder(folder: Path) -> Callable[[], None]:
    def remove() -> None:
        for item in folder.iterdir():
            if item.is_dir():
                backups.remove_tree(item)
            else:
                try:
                    item.unlink()
                except OSError:
                    pass
    return remove


def orphan_build_envs(projects, cache_dir: Path | None = None) -> list[Candidate]:
    root = (cache_dir or paths.cache_dir()) / "venvs"
    ids = {p.id for p in projects}
    found = []
    if not root.is_dir():
        return found
    for venv in sorted(root.iterdir()):
        match = re.search(r"-p(\d+)(?:-|$)", venv.name)
        if not venv.is_dir() or (match and int(match.group(1)) in ids):
            continue
        package = Package("pip", f"Umgebung {venv.name}", "", place="Exe-Bau ohne Projekt",
                          location=venv, kind="umgebung")
        found.append(Candidate(f"Umgebung für den Exe-Bau ohne Projekt: {venv.name}",
                               folder_size(venv), lambda v=venv: backups.remove_tree(v),
                               [package]))
    return found


def pip_cache() -> list[Candidate]:
    folder = pip_cache_dir()
    if not folder.is_dir():
        return []
    size = folder_size(folder)
    if not size:
        return []
    return [Candidate("Zwischenspeicher von pip, wird bei Bedarf neu gefüllt", size,
                      _empty_folder(folder))]


def incomplete_downloads(cache: Path | None = None) -> list[Candidate]:
    cache = cache or models.hf_cache()
    found = []
    try:
        folders = [p for p in cache.iterdir() if p.name.startswith("models--")]
    except OSError:
        return []
    for folder in folders:
        parts = list((folder / "blobs").glob("*.incomplete")) if (folder / "blobs").is_dir() \
            else []
        snapshots = [p for p in (folder / "snapshots").glob("*") if p.is_dir()] \
            if (folder / "snapshots").is_dir() else []
        empty = not snapshots or all(not any(s.iterdir()) for s in snapshots)
        if parts:
            size = sum(p.stat().st_size for p in parts if p.is_file())
            found.append(Candidate(f"Unvollständiger Download: {models._hf_repo(folder)}", size,
                                   lambda ps=parts: [p.unlink() for p in ps if p.exists()]))
        elif empty:
            package = Package(MODEL, models._hf_repo(folder), "", location=folder, kind=models.HF,
                              place="Hugging Face")
            found.append(Candidate(f"Leerer Download: {models._hf_repo(folder)}",
                                   folder_size(folder), lambda f=folder: backups.remove_tree(f),
                                   [package]))
    return found


def old_revisions(model_packages: list[Package]) -> list[Candidate]:
    found = []
    for package in model_packages:
        if package.kind != models.HF:
            continue
        old = models.hf_old_revisions(package)
        if old:
            size = sum(folder_size(p) for p in old)
            found.append(Candidate(f"{count(len(old), 'alte Fassung', 'alte Fassungen')} von "
                                   f"{package.name}", size,
                                   lambda p=package: models.hf_remove_old(p), [package]))
    return found


def unused_models(model_packages: list[Package]) -> list[Candidate]:
    found = []
    for package in model_packages:
        if package.extra.get("unused") and not package.cockpit and package.size:
            where = f", {package.place}" if package.place else ""
            found.append(Candidate(f"Modell ohne bekannten Benutzer: {package.name}{where}",
                                   package.size,
                                   lambda p=package: models.delete(p), [package]))
    return found


def candidates(projects, model_packages: list[Package], cache_dir: Path | None = None
               ) -> list[Candidate]:
    return (orphan_build_envs(projects, cache_dir) + pip_cache() + incomplete_downloads()
            + old_revisions(model_packages) + unused_models(model_packages))


def apply(chosen: list[Candidate]) -> tuple[int, list[str]]:
    """Gewählte aufräumen. Gibt frei gewordene Bytes und Fehler zurück."""
    listed = [p for c in chosen for p in c.packages]
    if listed:
        record.save_list(listed, "vor dem Aufräumen")
    freed, failed = 0, []
    for candidate in chosen:
        try:
            candidate.remove()
            freed += candidate.size
        except Exception as exc:                     # gesperrte Dateien, Ollama läuft nicht
            message = getattr(exc, "message", "") or repr(exc)
            log.warning("Aufräumen %s: %s", candidate.text, message)
            failed.append(f"{candidate.text}: {message}")
    return freed, failed
