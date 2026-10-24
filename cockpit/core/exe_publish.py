"""Versionen und Veröffentlichen der Exe (Phase 10).

Aus exe.py herausgelöst am 21.10.2026, nur verschoben. Die Namen sind weiter über exe erreichbar.
Teile aus exe holen die Funktionen erst beim Aufruf, so gibt es keinen Kreis beim Import, und Tests,
die zum Beispiel exe.running_from ersetzen, greifen weiter.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
from pathlib import Path

from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project

log = logging.getLogger("cockpit.core.exe")

_VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def next_version(tags: list[str]) -> str:
    """Nach 1.3.0 kommt 1.3.1, ohne Release 1.0.0."""
    versions = sorted(tuple(int(x) for x in m.groups()) for m in map(_VERSION.match, tags) if m)
    if not versions:
        return "1.0.0"
    major, minor, patch = versions[-1]
    return f"{major}.{minor}.{patch + 1}"


def check_version(text: str, tags: list[str]) -> str:
    match = _VERSION.match(text.strip())
    if not match:
        raise CockpitError("Bitte eine Versionsnummer wie 1.0.0 eingeben.")
    version = ".".join(match.groups())
    if f"v{version}" in tags or version in tags:
        raise CockpitError(f"Die Version {version} gibt es schon.")
    return version


def asset_name(project: Project, exe: Path | None = None) -> str:
    """Fester Name der ZIP-Datei am Release, zum Beispiel VokabelApp.zip. So bleibt der Link
    auf die neueste Version gleich (Antwort des Nutzers vom 03.10.2026)."""
    from cockpit.core import exe as core
    return f"{core.home_name(project, exe)}.zip"


def asset_for_upload(project: Project, exe: Path, work: Path, version: str) -> Path:
    """Den ganzen Ordner der Exe als ZIP-Datei mit festem Namen. Darin liegt ein Ordner mit der
    Versionsnummer, zum Beispiel VokabelApp-1.2.0, damit beim Auspacken keine Version eine andere
    überschreibt (Wunsch des Nutzers vom 03.10.2026). Ordner neben der Exe kommen so in die ZIP,
    wie sie im Ordner Repository stehen, nicht mit den eigenen Daten aus dem Ordner Release. README und
    Lizenz kommen immer mit."""
    from cockpit.core import exe as core
    folder = exe.parent
    names = [n for n in core.beside_names(project) if (project.code_dir / n).exists()]
    one_file = folder.resolve() == project.exe_dir.resolve()      # alte Ablage ohne eigenen Ordner
    name = core.home_name(project, exe)
    staging = work / f"{name}-v{version}"               # mit v (Wunsch vom 04.10.2026)
    if one_file:
        staging.mkdir(parents=True)
        shutil.copy2(exe, staging / exe.name)
    else:
        shutil.copytree(folder, staging, ignore=lambda _d, items: [
            i for i in items if _d == str(folder) and i in names])
    (staging / core.VERSION_FILE).write_text(version + "\n", encoding="utf-8")
    for item in names:
        source = project.code_dir / item
        if source.is_dir():
            shutil.copytree(source, staging / item)
        else:
            shutil.copy2(source, staging / item)
    archive = shutil.make_archive(str(work / name), "zip", work, staging.name)
    return Path(archive)


def mark_published(project: Project, exe: Path, version: str, rename: bool = True) -> Path:
    """Nach dem Veröffentlichen: version.txt neben die Exe legen. So merkt die Exe, welche
    Version sie ist (04.10.2026). Der Ordner bleibt der feste Ordner, zum Beispiel
    Release\\VokabelApp. Erst wenn eine neue Exe sie ersetzt, heißt er VokabelApp-v1.2.0
    (retire_home, Wunsch des Nutzers vom 20.10.2026). Gibt die Exe an ihrem Ort zurück."""
    from cockpit.core import exe as core
    folder = exe.parent
    if folder.resolve() == project.exe_dir.resolve():
        return exe                                  # alte Ablage ohne eigenen Ordner
    (folder / core.VERSION_FILE).write_text(version + "\n", encoding="utf-8")
    if not rename:
        return exe                                  # Release eines Branches (06.10.2026)
    # Seit dem 20.10.2026 bleibt der feste Ordner. Eine Exe aus einem Branch oder einem alten
    # Versionsordner kommt dorthin.
    home = project.exe_dir / core.home_name(project, exe)
    if folder.resolve() != home.resolve() and not core.running_from(folder):
        core._make_room(project, home, "Exe durch die veröffentlichte ersetzt")
        try:
            os.rename(folder, home)
            exe = home / exe.name
        except OSError as exc:
            log.warning("Exe nicht in den festen Ordner verschoben: %s (%s)", folder, exc)
    core.prune_versions(project.exe_dir, home.name, project.name)
    return exe


def pick_asset(assets) -> object | None:
    """Exe-Datei bevorzugt, sonst eine ZIP-Datei."""
    for suffix in (".exe", ".zip"):
        for asset in assets:
            if asset.name.lower().endswith(suffix):
                return asset
    return None


def unpack(download: Path, work: Path) -> Path:
    """Heruntergeladene Datei: Exe direkt, ZIP-Datei entpackt (der Programmordner)."""
    if download.suffix.lower() == ".exe":
        return download
    target = work / download.stem
    shutil.unpack_archive(str(download), str(target))
    inner = [p for p in target.iterdir()]
    return inner[0] if len(inner) == 1 and inner[0].is_dir() else target
