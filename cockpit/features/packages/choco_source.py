"""Programme aus Chocolatey.

choco list -r und choco outdated -r liefern Zeilen mit | dazwischen. Datum und Größe kommen aus
dem Ordner lib des Pakets. Die Größe ist die des Pakets, bei Programmen mit eigenem Installer
liegt das Programm selbst woanders. Ändern braucht Administratorrechte, Windows fragt danach.
"""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

from cockpit.features.packages import runner
from cockpit.features.packages.base import CHOCO, Package, folder_size, mtime

log = logging.getLogger(__name__)


def available() -> bool:
    return runner.find("choco") is not None


def lib_dir() -> Path:
    return Path(os.environ.get("ChocolateyInstall", r"C:\ProgramData\chocolatey")) / "lib"


def _rows(lines: list[str]) -> list[list[str]]:
    return [line.strip().split("|") for line in lines if line.count("|") >= 1]


def _choco() -> str:
    return runner.find("choco") or "choco"


def list_packages(cancel: threading.Event | None = None, sizes: bool = True) -> list[Package]:
    result = runner.run([_choco(), "list", "-r", "--limit-output"], cancel)
    packages = []
    for cells in _rows(result.lines):
        name, version = cells[0], cells[1] if len(cells) > 1 else ""
        folder = lib_dir() / name
        packages.append(Package(CHOCO, name, version, key=name, place="Chocolatey",
                                location=folder if folder.is_dir() else None,
                                size=folder_size(folder) if sizes and folder.is_dir() else None,
                                added=mtime(folder) if folder.is_dir() else None))
    return packages


def check_outdated(packages: list[Package], cancel: threading.Event | None = None) -> None:
    result = runner.run([_choco(), "outdated", "-r", "--limit-output"], cancel)
    if not result.ok and not result.lines:
        return
    newer = {}
    pinned = set()
    for cells in _rows(result.lines):
        if len(cells) >= 3:
            newer[cells[0].lower()] = cells[2]
            if len(cells) > 3 and cells[3].strip().lower() == "true":
                pinned.add(cells[0].lower())
    for package in packages:
        package.checked = True
        package.latest = newer.get(package.name.lower(), "")
        package.pinned = package.pinned or package.name.lower() in pinned
    for name in pins(cancel):
        for package in packages:
            if package.name.lower() == name.lower():
                package.pinned = True


def pins(cancel: threading.Event | None = None) -> list[str]:
    result = runner.run([_choco(), "pin", "list", "-r", "--limit-output"], cancel)
    return [cells[0] for cells in _rows(result.lines)]


def upgrade(package: Package, cancel=None, on_line=None) -> runner.Result:
    return runner.require(runner.elevated([_choco(), "upgrade", package.id, "-y",
                                           "--no-progress"], cancel),
                          f"Aktualisieren von {package.name}")


def install_version(package: Package, version: str, cancel=None, on_line=None) -> runner.Result:
    return runner.require(runner.elevated([_choco(), "install", package.id, "--version", version,
                                           "--allow-downgrade", "--force", "-y", "--no-progress"],
                                          cancel), f"Version {version} von {package.name}")


def uninstall(package: Package, cancel=None, on_line=None) -> runner.Result:
    return runner.require(runner.elevated([_choco(), "uninstall", package.id, "-y"], cancel),
                          f"Löschen von {package.name}")


def pin(package: Package, on: bool, cancel=None) -> runner.Result:
    verb = "add" if on else "remove"
    return runner.require(runner.elevated([_choco(), "pin", verb, f"--name={package.id}"],
                                          cancel), "Festhalten")


def versions(package: Package, cancel=None) -> list[str]:
    from cockpit.features.packages.base import version_key
    result = runner.run([_choco(), "search", package.id, "--exact", "--all-versions", "-r"],
                        cancel)
    found = [cells[1] for cells in _rows(result.lines)
             if len(cells) > 1 and cells[0].lower() == package.id.lower()]
    return sorted(set(found), key=version_key, reverse=True)


def install_by_id(key: str, version: str = "", cancel=None, on_line=None) -> runner.Result:
    args = [_choco(), "install", key, "-y", "--no-progress"]
    if version:
        args += ["--version", version]
    return runner.require(runner.elevated(args, cancel), f"Installieren von {key}")
