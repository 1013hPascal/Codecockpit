"""Was die Paketübersicht sich merkt.

- Verlauf: alte und neue Version bei jedem Ändern. Daraus kommt "Zurück zur vorherigen Version".
- Festhalten bei pip: steht nur in der Datenbank. winget und Chocolatey halten selbst fest.
- Vor dem Löschen: keine Kopie der Dateien, sondern eine Liste in den Sicherheitskopien mit Name,
  Version, Ort und dem Befehl zum Wiederherstellen (Antwort des Nutzers vom 21.10.2026). Modelle
  und Umgebungen sind oft Gigabyte groß und lassen sich neu herunterladen.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from cockpit.core import backups
from cockpit.features.packages.base import CHOCO, MODEL, PIP, SOURCE_NAMES, WINGET, Package

BACKUP_NAME = "Paketübersicht"
SCAN_FOLDERS_KEY = "packages.scan_folders"


def remember(database, package: Package, new_version: str) -> None:
    database.execute(
        "INSERT INTO package_history (source, place, key, name, old_version, new_version, "
        "changed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (package.source, package.place, package.id, package.name, package.version, new_version,
         datetime.now().isoformat(timespec="seconds")))


def previous_version(database, package: Package) -> str:
    """Die Version vor der letzten Änderung, leer wenn keine bekannt ist."""
    row = database.query_one(
        "SELECT old_version FROM package_history WHERE source = ? AND place = ? AND key = ? "
        "AND new_version = ? ORDER BY id DESC LIMIT 1",
        (package.source, package.place, package.id, package.version))
    if row is None or row["old_version"] == package.version or not row["old_version"]:
        return ""
    return row["old_version"]


def history(database, limit: int = 200) -> list[str]:
    rows = database.query("SELECT * FROM package_history ORDER BY id DESC LIMIT ?", (limit,))
    return [f"{r['name']}: {r['old_version'] or 'neu'} zu {r['new_version'] or 'gelöscht'}, "
            f"{r['place']}, {datetime.fromisoformat(r['changed_at']):%d.%m.%Y %H:%M}"
            for r in rows]


def pinned(database, package: Package) -> bool:
    return database.query_one(
        "SELECT 1 FROM package_pins WHERE source = ? AND place = ? AND key = ?",
        (package.source, package.place, package.id)) is not None


def set_pinned(database, package: Package, on: bool) -> None:
    if on:
        database.execute(
            "INSERT INTO package_pins (source, place, key, version) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(source, place, key) DO UPDATE SET version = excluded.version",
            (package.source, package.place, package.id, package.version))
    else:
        database.execute("DELETE FROM package_pins WHERE source = ? AND place = ? AND key = ?",
                         (package.source, package.place, package.id))


def mark_pins(database, packages: list[Package]) -> None:
    """pip-Pakete aus der Datenbank als festgehalten markieren."""
    rows = database.query("SELECT source, place, key FROM package_pins")
    wanted = {(r["source"], r["place"], r["key"]) for r in rows}
    for package in packages:
        if (package.source, package.place, package.id) in wanted:
            package.pinned = True


def restore_command(package: Package) -> str:
    """Wie man es wieder holt. Steht in der Liste in den Sicherheitskopien."""
    if package.source == PIP:
        return f'"{package.location}" -m pip install {package.id}=={package.version}'
    if package.source == WINGET:
        return f"winget install --id {package.id} --exact --version {package.version}"
    if package.source == CHOCO:
        return f"choco install {package.id} --version {package.version} -y"
    if package.kind == "ollama":
        return f"ollama pull {package.id}"
    if package.kind == "huggingface":
        revision = package.extra.get("revision", "")
        return f"Hugging Face: {package.id}" + (f", Fassung {revision}" if revision else "")
    if package.kind == "cockpit":
        return "Spracheingabe des Cockpits: Modell im Menü KI neu herunterladen"
    return f"Datei {package.location}: nur aus einer eigenen Sicherung"


def save_list(packages: list[Package], reason: str) -> Path:
    """Liste vor dem Löschen in den Sicherheitskopien. Gibt den Ordner zurück."""
    lines = ["", "Diese Liste ersetzt die Kopie der Dateien. Mit den Befehlen holen Sie alles "
             "wieder:", ""]
    for package in packages:
        lines += [f"{SOURCE_NAMES.get(package.source, package.source)}: {package.name} "
                  f"{package.version}".rstrip(),
                  f"  Ort: {package.place}" + (f", {package.location}" if package.location
                                               and package.source == MODEL else ""),
                  f"  Wiederherstellen: {restore_command(package)}"]
    folder = backups.new_backup_dir(BACKUP_NAME, reason, notes=lines)
    (folder / "Pakete.txt").write_text("\n".join(lines[3:]) + "\n", encoding="utf-8")
    return folder


def scan_folders(database) -> list[Path]:
    return [Path(p) for p in database.get_value(SCAN_FOLDERS_KEY, []) or []]


def add_scan_folder(database, folder: Path) -> None:
    folders = [str(p) for p in scan_folders(database)]
    if str(folder) not in folders:
        database.set_value(SCAN_FOLDERS_KEY, folders + [str(folder)])
