"""Python-Bibliotheken: das globale Python, die Umgebungen der Projekte und die für den Exe-Bau.

Ein kleines Prüfprogramm läuft im jeweiligen Python und meldet Name, Version, Datum, Größe und
Lizenz als JSON. Datum ist das des Ordners .dist-info, das stimmt fast immer mit dem Installieren
überein. Ob ein Paket veraltet ist, fragt pip selbst bei PyPI nach (pip list --outdated).
In einer Umgebung gibt es immer nur eine Version einer Bibliothek.
"""
from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from cockpit.core.errors import CockpitError
from cockpit.features.packages import runner
from cockpit.features.packages.base import PIP, Package

log = logging.getLogger(__name__)

SCRIPT = r'''
import importlib.metadata as m, json, os
out, seen = [], set()
for d in m.distributions():
    name = d.metadata.get("Name") or ""
    if not name or name.lower() in seen:
        continue
    seen.add(name.lower())
    path = getattr(d, "_path", None)
    try:
        stamp = os.path.getmtime(path) if path else 0
    except OSError:
        stamp = 0
    size = 0
    for f in d.files or []:
        size += getattr(f, "size", None) or 0
    lic = d.metadata.get("License-Expression") or d.metadata.get("License") or ""
    if len(lic) > 40 or "\n" in lic:
        lic = ""
    if not lic:
        found = [c.split(" :: ")[-1] for c in d.metadata.get_all("Classifier") or []
                 if c.startswith("License ::")]
        lic = ", ".join(found[:2])
    out.append([name, d.version, stamp, size, lic])
print(json.dumps(out))
'''


@dataclass
class Environment:
    label: str                          # "Python 3.14", "Projekt Tagebuch", "Exe-Bau Tagebuch"
    python: Path
    owner: str = ""                     # Projekt
    cockpit: bool = False
    project_id: int | None = None       # gehört zu diesem Projekt, None: global oder verwaist
    requirements: Path | None = None    # requirements.txt des Projekts


def environments(projects, cache_dir: Path | None = None) -> list[Environment]:
    """Alle Python-Umgebungen, die die Übersicht kennt. projects: Liste von Project."""
    from cockpit.core import exe, paths
    found: list[Environment] = []
    seen: set[str] = set()

    def add(env: Environment) -> None:
        key = str(env.python).lower()
        if env.python.is_file() and key not in seen:
            seen.add(key)
            found.append(env)

    for install in exe.find_pythons():
        add(Environment(f"Python {install.label}", Path(install.command[0])))
    for project in projects:
        folders = [project.code_dir]
        if project.has_branch_folders and project.code_root.is_dir():
            folders += sorted(p for p in project.code_root.iterdir()
                              if p.is_dir() and p != project.code_dir)
        for folder in folders:
            label = f"Projekt {project.name}" if folder == project.code_dir else \
                f"Projekt {project.name}, Branch-Ordner {folder.name}"
            add(Environment(label, exe.venv_python(folder), project.name, True, project.id,
                            folder / "requirements.txt"))
    root = (cache_dir or paths.cache_dir()) / "venvs"
    by_id = {p.id: p for p in projects}
    if root.is_dir():
        for venv in sorted(root.iterdir()):
            match = re.search(r"-p(\d+)(?:-|$)", venv.name)
            project = by_id.get(int(match.group(1))) if match else None
            if project is not None:
                add(Environment(f"Exe-Bau {project.name}", exe.python_in(venv), project.name,
                                True, project.id))
            else:
                add(Environment(f"Exe-Bau ohne Projekt ({venv.name})", exe.python_in(venv),
                                "", True))
    return found


def list_packages(env: Environment, cancel: threading.Event | None = None) -> list[Package]:
    result = runner.run([str(env.python), "-I", "-X", "utf8", "-c", SCRIPT], cancel)
    try:
        rows = json.loads(result.lines[-1]) if result.ok and result.lines else []
    except ValueError:
        rows = []
    if not result.ok:
        log.warning("pip-Liste von %s: %s", env.label, result.text[-300:])
    packages = []
    for name, version, stamp, size, lic in rows:
        packages.append(Package(
            PIP, name, version, key=name, place=env.label, location=env.python,
            size=int(size) or None, added=datetime.fromtimestamp(stamp) if stamp else None,
            owner=env.owner, cockpit=env.cockpit, license=lic,
            extra={"env": env.label, "project_id": env.project_id}))
    return packages


def check_outdated(env: Environment, packages: list[Package],
                   cancel: threading.Event | None = None) -> None:
    """latest und checked setzen. Braucht das Internet, dauert einige Sekunden."""
    result = runner.run([str(env.python), "-I", "-m", "pip", "list", "--outdated",
                         "--format=json", "--disable-pip-version-check"], cancel)
    rows = []
    for line in reversed(result.lines):
        if line.startswith("["):
            try:
                rows = json.loads(line)
            except ValueError:
                pass
            break
    if not result.ok and not rows:
        return                                   # zum Beispiel ohne Internet: unbekannt lassen
    newer = {r["name"].lower(): r.get("latest_version", "") for r in rows}
    for package in packages:
        package.checked = True
        package.latest = newer.get(package.name.lower(), "")


def _pip(package: Package, *args: str) -> list[str]:
    return [str(package.location), "-I", "-m", "pip", *args, "--disable-pip-version-check"]


def upgrade(package: Package, cancel=None, on_line=None) -> runner.Result:
    return runner.require(runner.run(_pip(package, "install", "--upgrade", package.id), cancel,
                                     on_line), f"Aktualisieren von {package.name}")


def install_version(package: Package, version: str, cancel=None, on_line=None) -> runner.Result:
    return runner.require(runner.run(_pip(package, "install", f"{package.id}=={version}"),
                                     cancel, on_line), f"Version {version} von {package.name}")


def uninstall(package: Package, cancel=None, on_line=None) -> runner.Result:
    return runner.require(runner.run(_pip(package, "uninstall", "-y", package.id), cancel,
                                     on_line), f"Löschen von {package.name}")


def versions(name: str, client=None) -> list[str]:
    """Alle Versionen auf PyPI, neueste zuerst. Ohne Vorabversionen."""
    from cockpit.features.packages import web
    data = web.get_json(f"https://pypi.org/pypi/{name}/json", client)
    if not data:
        raise CockpitError(f"Die Versionen von {name} ließen sich nicht abfragen.")
    from cockpit.features.packages.base import version_key
    found = [v for v, files in data.get("releases", {}).items()
             if files and not re.search(r"(a|b|rc|dev)\d*$", v)]
    return sorted(found, key=version_key, reverse=True)


def change_log(name: str, client=None) -> str:
    """Link auf die Liste der Änderungen, sonst auf die Seite bei PyPI."""
    from cockpit.features.packages import web
    data = web.get_json(f"https://pypi.org/pypi/{name}/json", client) or {}
    urls = (data.get("info") or {}).get("project_urls") or {}
    for key, url in urls.items():
        if re.search(r"change|release|history|news", key, re.IGNORECASE):
            return url
    return f"https://pypi.org/project/{name}/#history"
