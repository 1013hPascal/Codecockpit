"""Programme aus winget.

winget list gibt eine Tabelle aus. Die Spalten ergeben sich aus der Kopfzeile, über der Zeile aus
Strichen. Die Kopfzeile kann deutsch oder englisch sein, deshalb zählt nur die Reihenfolge: Name,
Kennung, Version, verfügbare Version. Ein Datum meldet winget nicht. Es kommt, wenn vorhanden,
aus der Windows-Registrierung (InstallDate), ebenso die Größe (EstimatedSize).
"""
from __future__ import annotations

import logging
import re
import threading
from datetime import datetime

from cockpit.features.packages import runner
from cockpit.features.packages.base import WINGET, Package

log = logging.getLogger(__name__)

AGREE = ["--accept-source-agreements", "--disable-interactivity"]


def available() -> bool:
    return runner.find("winget") is not None


def parse_table(lines: list[str]) -> list[list[str]]:
    """Zeilen einer Tabelle von winget als Spalten. Leer, wenn keine Tabelle gefunden wird."""
    for index, line in enumerate(lines[1:], start=1):
        if re.fullmatch(r"-{10,}", line.strip()):
            header = lines[index - 1]
            # Vor der Kopfzeile kann noch ein Rest der Fortschrittsanzeige stehen. Die Zeilen
            # darunter beginnen dort, wo "Name" steht.
            header = header[header.find("Name"):] if "Name" in header else header
            starts = [m.start() for m in re.finditer(r"\S+", header)]
            rows = []
            for row in lines[index + 1:]:
                if not row.strip() or re.fullmatch(r"\d+ .*", row.strip()):
                    continue                       # "3 Upgrades verfügbar." und ähnliches
                cells = [row[a:b].strip() for a, b in zip(starts, starts[1:] + [None])]
                rows.append(cells)
            return rows
    return []


def _registry() -> dict[str, tuple[datetime | None, int | None]]:
    """Anzeigename -> (Datum, Größe) aus den Einträgen zum Deinstallieren."""
    try:
        import winreg
    except ImportError:
        return {}
    found: dict[str, tuple[datetime | None, int | None]] = {}
    places = [(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
              (winreg.HKEY_LOCAL_MACHINE,
               r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
              (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")]
    for hive, path in places:
        try:
            root = winreg.OpenKey(hive, path)
        except OSError:
            continue
        with root:
            for number in range(winreg.QueryInfoKey(root)[0]):
                try:
                    with winreg.OpenKey(root, winreg.EnumKey(root, number)) as key:
                        values = {}
                        for name in ("DisplayName", "InstallDate", "EstimatedSize"):
                            try:
                                values[name] = winreg.QueryValueEx(key, name)[0]
                            except OSError:
                                pass
                except OSError:
                    continue
                name = str(values.get("DisplayName", "")).strip()
                if not name:
                    continue
                date = None
                try:
                    date = datetime.strptime(str(values.get("InstallDate", "")), "%Y%m%d")
                except ValueError:
                    pass
                size = values.get("EstimatedSize")
                found[name] = (date, int(size) * 1024 if isinstance(size, int) else None)
    return found


def _lookup(registry: dict, name: str) -> tuple[datetime | None, int | None]:
    if name in registry:
        return registry[name]
    if name.endswith("…"):
        start = name[:-1]
        for key, value in registry.items():
            if key.startswith(start):
                return value
    return None, None


def list_packages(cancel: threading.Event | None = None, registry: dict | None = None
                  ) -> list[Package]:
    """Mit winget installierte Programme, mit verfügbarer Version. Gleich als geprüft markiert,
    weil winget list die verfügbare Version gleich mitliefert."""
    result = runner.run(["winget", "list", "--source", "winget", *AGREE], cancel)
    rows = parse_table(result.lines)
    pinned = set(pins(cancel))
    registry = _registry() if registry is None else registry
    packages = []
    seen = set()
    for cells in rows:
        if len(cells) < 3 or not cells[1] or cells[1] in seen:
            continue
        seen.add(cells[1])
        name, key, version = cells[0], cells[1], cells[2]
        latest = cells[3] if len(cells) > 3 else ""
        date, size = _lookup(registry, name)
        packages.append(Package(WINGET, name, version, key=key, place="winget", latest=latest,
                                checked=True, size=size, added=date, pinned=key in pinned))
    return packages


def pins(cancel: threading.Event | None = None) -> list[str]:
    result = runner.run(["winget", "pin", "list", *AGREE], cancel)
    return [cells[1] for cells in parse_table(result.lines) if len(cells) > 1 and cells[1]]


def _common(package: Package) -> list[str]:
    return ["--id", package.id, "--exact", "--silent", "--accept-package-agreements", *AGREE]


def upgrade(package: Package, cancel=None, on_line=None) -> runner.Result:
    return runner.require(runner.run(["winget", "upgrade", *_common(package)], cancel, on_line),
                          f"Aktualisieren von {package.name}")


def install_version(package: Package, version: str, cancel=None, on_line=None) -> runner.Result:
    return runner.require(runner.run(["winget", "install", *_common(package), "--version",
                                      version, "--force"], cancel, on_line),
                          f"Version {version} von {package.name}")


def uninstall(package: Package, cancel=None, on_line=None) -> runner.Result:
    args = ["winget", "uninstall", "--id", package.id, "--exact", "--silent", *AGREE]
    return runner.require(runner.run(args, cancel, on_line), f"Löschen von {package.name}")


def pin(package: Package, on: bool, cancel=None) -> runner.Result:
    verb = "add" if on else "remove"
    return runner.require(runner.run(["winget", "pin", verb, "--id", package.id, "--exact",
                                      *AGREE], cancel), "Festhalten")


def versions(package: Package, cancel=None) -> list[str]:
    result = runner.run(["winget", "show", "--id", package.id, "--exact", "--versions", *AGREE],
                        cancel)
    lines = result.lines
    for index, line in enumerate(lines):
        if re.fullmatch(r"-{3,}", line.strip()):
            return [v.strip() for v in lines[index + 1:] if v.strip()]
    return []


def install_by_id(key: str, version: str = "", cancel=None, on_line=None) -> runner.Result:
    """Für die Liste eines neuen Rechners."""
    args = ["winget", "install", "--id", key, "--exact", "--silent",
            "--accept-package-agreements", *AGREE]
    if version:
        args += ["--version", version]
    return runner.require(runner.run(args, cancel, on_line), f"Installieren von {key}")
