"""Selbst-Aktualisierung der Exe des Cockpits (Konzept 10.5).

Quelle ist das neueste Release im öffentlichen Repository des Cockpits. Ob es eine neue Datei
gibt, zeigt die Prüfsumme (SHA-256), die GitHub zu jeder Datei eines Releases angibt: Weicht sie
von der laufenden Exe ab und ist das Release jünger als die Exe, gibt es ein Update. Eine selbst
gebaute, neuere Exe wird so nicht durch ein älteres Release ersetzt.

Die neue Exe wird heruntergeladen, gegen die Prüfsumme geprüft und wartet in Exe\\_neu. Nach dem
Beenden tauscht ein kleines Skript sie aus, die bisherige Exe kommt in die Sicherheitskopien.

Liegen Dateien neben der Exe (zum Beispiel LICENSE), steht am Release statt der Exe die ZIP-Datei
CodeCockpit.zip. Dann wird die ZIP-Datei geladen und geprüft, und die Exe kommt aus ihr
(Rückmeldung des Nutzers vom 03.10.2026: ab Version 1.1.13 fand die Suche kein Update mehr).
Einstellungen, Konten und Tresor liegen in %APPDATA% und bleiben unberührt.
"""
from __future__ import annotations

import hashlib
import logging
import shutil
import sys
import threading
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

from cockpit.core import backups, exe, http
from cockpit.core.errors import Cancelled, CockpitError

log = logging.getLogger(__name__)

OWNER, REPO = "1013hPascal", "Codecockpit"
ZIP_PREFIX = "codecockpit"                   # nur CodeCockpit.zip, keine fremde ZIP-Datei
API = "https://api.github.com"
SKIPPED_KEY = "update.skipped"               # übersprungene Version (Tag)
LAST_CHECK_KEY = "update.last_check"         # Zeitpunkt der letzten Prüfung, Sekunden
CHECK_EVERY = 24 * 60 * 60
NO_CONNECTION = "Keine Verbindung zu GitHub. Bitte später erneut versuchen."


@dataclass
class Update:
    tag: str
    notes: str
    asset_name: str
    url: str                                  # Download-Adresse der Datei
    size: int
    digest: str                               # SHA-256, klein geschrieben
    published: datetime

    @property
    def version(self) -> str:
        return self.tag.lstrip("v")

    @property
    def is_zip(self) -> bool:
        return self.asset_name.lower().endswith(".zip")

    @property
    def size_text(self) -> str:
        return f"{max(1, round(self.size / (1024 * 1024)))} MB"


def own_exe() -> Path | None:
    """Die laufende Exe, None beim Start aus dem Code."""
    if not getattr(sys, "frozen", False):
        return None
    return Path(sys.executable)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _time(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def latest(transport: httpx.BaseTransport | None = None) -> Update | None:
    """Neuestes Release mit Exe-Datei und Prüfsumme, None wenn es keins gibt."""
    try:
        with http.make_client(API, {"Accept": "application/vnd.github+json"},
                              transport=transport) as client:
            response = client.get(f"/repos/{OWNER}/{REPO}/releases/latest")
    except httpx.HTTPError as exc:
        raise CockpitError(NO_CONNECTION, repr(exc)) from None
    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise CockpitError("GitHub hat die Anfrage nach Updates abgelehnt. Bitte später erneut "
                           "versuchen.", f"HTTP {response.status_code}")
    data = response.json()
    usable = [a for a in data.get("assets") or []
              if (a.get("digest") or "").startswith("sha256:")]
    exes = [a for a in usable if a.get("name", "").lower().endswith(".exe")]
    zips = [a for a in usable if a.get("name", "").lower().endswith(".zip")
            and a.get("name", "").lower().startswith(ZIP_PREFIX)]
    for asset in exes + zips:                   # Exe bevorzugt, sonst CodeCockpit.zip
        return Update(data.get("tag_name", ""), data.get("body") or "", asset["name"],
                      asset["browser_download_url"], int(asset.get("size", 0)),
                      asset["digest"].split(":", 1)[1].lower(),
                      _time(data.get("published_at") or asset["updated_at"]))
    return None


def is_newer(update: Update, exe_path: Path) -> bool:
    """Andere Datei als die laufende Exe und jünger als sie."""
    if sha256(exe_path) == update.digest:
        return False
    built = datetime.fromtimestamp(exe_path.stat().st_mtime, timezone.utc)
    return update.published > built


def check(exe_path: Path, skipped: str = "",
          transport: httpx.BaseTransport | None = None) -> Update | None:
    """Gibt es ein Update für exe_path? skipped: vom Nutzer übersprungene Version."""
    update = latest(transport)
    if update is None or (skipped and update.tag == skipped):
        return None
    return update if is_newer(update, exe_path) else None


def download(update: Update, exe_path: Path, cancel: threading.Event | None = None,
             transport: httpx.BaseTransport | None = None) -> Path:
    """Neue Exe nach Exe\\_neu laden, unter dem Namen der laufenden Exe. Prüft die Prüfsumme."""
    pending = exe_path.parent / exe.PENDING
    backups.remove_tree(pending)
    pending.mkdir()
    target = pending / (update.asset_name if update.is_zip else exe_path.name)
    digest = hashlib.sha256()
    try:
        with http.make_client(transport=transport) as client, \
                client.stream("GET", update.url, follow_redirects=True,
                              timeout=httpx.Timeout(3600, connect=15)) as response:
            if response.status_code >= 400:
                raise CockpitError("Die neue Version ließ sich nicht herunterladen.",
                                   f"HTTP {response.status_code}")
            with open(target, "wb") as file:
                for chunk in response.iter_bytes(1024 * 256):
                    if cancel is not None and cancel.is_set():
                        raise Cancelled()
                    digest.update(chunk)
                    file.write(chunk)
    except httpx.HTTPError as exc:
        backups.remove_tree(pending)
        raise CockpitError(NO_CONNECTION, repr(exc)) from None
    except BaseException:
        backups.remove_tree(pending)
        raise
    if digest.hexdigest() != update.digest:
        backups.remove_tree(pending)
        raise CockpitError("Die heruntergeladene Datei ist beschädigt oder verändert. Sie wurde "
                           "gelöscht, die bisherige Version bleibt.", "SHA-256 weicht ab")
    if update.is_zip:
        try:
            return _exe_from_zip(target, pending / exe_path.name)
        except BaseException:
            backups.remove_tree(pending)
            raise
    return target


def _exe_from_zip(archive: Path, target: Path) -> Path:
    """Die Exe aus der geprüften ZIP-Datei holen, unter dem Namen der laufenden Exe. Nur diese
    eine Datei wird geschrieben, an einen festen Ort, egal welche Pfade in der ZIP stehen."""
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = [m for m in bundle.infolist()
                       if not m.is_dir() and m.filename.lower().endswith(".exe")]
            same = [m for m in members if Path(m.filename).name.lower() == target.name.lower()]
            chosen = (same or members)[:1]
            if not chosen or len(members) > 1 and not same:
                raise CockpitError("In der ZIP-Datei der neuen Version steckt keine passende "
                                   "Exe. Die bisherige Version bleibt.",
                                   ", ".join(m.filename for m in members) or "keine Exe")
            if any("_internal/" in m.filename.replace("\\", "/") for m in bundle.infolist()):
                raise CockpitError("Die neue Version ist ein Programmordner. Den kann das Cockpit "
                                   "nicht selbst austauschen. Laden Sie die ZIP-Datei bitte von "
                                   "der Release-Seite.", archive.name)
            with bundle.open(chosen[0]) as source, open(target, "wb") as file:
                shutil.copyfileobj(source, file)
    except zipfile.BadZipFile as exc:
        raise CockpitError("Die ZIP-Datei der neuen Version ist beschädigt. Die bisherige Version "
                           "bleibt.", repr(exc)) from None
    archive.unlink()
    return target


def is_waiting(exe_path: Path) -> bool:
    return (exe_path.parent / exe.PENDING / exe_path.name).is_file()


def swap(exe_path: Path, version: str, start: bool) -> Path:
    """Austausch-Skript für die wartende Exe. Die bisherige kommt in die Sicherheitskopien."""
    new = exe_path.parent / exe.PENDING / exe_path.name
    if not new.is_file():
        raise CockpitError("Es wartet keine neue Version.")
    folder = backups.new_backup_dir("CodeCockpit", f"Exe vor dem Update auf {version} ersetzt",
                                    exe_path.parent)
    return exe.swap_script(exe_path.parent, [exe_path], [new], folder,
                           exe_path if start else None)
