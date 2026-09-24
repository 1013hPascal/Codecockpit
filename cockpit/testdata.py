"""Testdaten für die Tests mit NVDA (Start mit start_testdaten.bat).

Alles liegt in einem eigenen Ordner %LOCALAPPDATA%\\CodeCockpit\\Testdaten und wird bei jedem
Start neu angelegt. Die echten Daten des Cockpits werden nicht berührt.

Die Einrichtung beginnt bei jedem Start neu. Wählt man die Windows-Anmeldeinformationsverwaltung,
liegen die Test-Zugangsdaten dort unter einem eigenen Namen (VAULT_SERVICE) und werden beim nächsten
Start gelöscht. Dazu gibt es die Testplattform für die Kontenverwaltung (testdata_platform.py).

Beispielprojekte:
- PDF-Chat: Code und Exe. Die Exe ist absichtlich keine echte Exe, damit man das Fehlerfenster
  testen kann.
- Tagebuch: nur Code.
- Bildbeschreiber: Code und ein leerer Ordner Exe.
- Notizen: steht in der Liste, der Ordner fehlt aber ("Ordner nicht gefunden").
"""
from __future__ import annotations

import logging
import os
import shutil
import sqlite3
import time
from pathlib import Path

from cockpit import APP_NAME
from cockpit.core.errors import CockpitError
from cockpit.core.paths import HOME_VARIABLE

log = logging.getLogger(__name__)

VAULT_SERVICE = "CodeCockpit Testdaten"
IN_USE = ("Die Testdaten werden noch von einem offenen CodeCockpit benutzt. Bitte schließen Sie "
          "zuerst alle Fenster von CodeCockpit mit Testdaten.")

FAKE_EXE_TEXT = "Dies ist keine echte Exe. Sie gehört zu den Testdaten von CodeCockpit.\n"


def base_dir() -> Path:
    local = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    return local / APP_NAME / "Testdaten"


def prepare(base: Path | None = None) -> tuple[Path, Path]:
    """Testdaten neu anlegen. Gibt (Datenordner, Projekte-Hauptordner) zurück und lenkt den
    Datenordner des Cockpits dorthin um."""
    base = base or base_dir()
    if base.exists():
        # Erst umbenennen: Das klappt nur, wenn kein offenes Cockpit Dateien darin benutzt.
        # So wird nie ein halber Ordner gelöscht, während ein anderes Fenster ihn noch braucht.
        old = base.with_name(base.name + "-alt")
        shutil.rmtree(old, ignore_errors=True)
        try:
            base.rename(old)
        except PermissionError as exc:
            raise CockpitError(IN_USE, str(exc)) from None
        remove_old_vault_entries(old / "Daten" / "cockpit.db")
        shutil.rmtree(old, ignore_errors=True)
    home = base / "Daten"
    root = base / "Projekte"
    home.mkdir(parents=True)
    root.mkdir(parents=True)

    def project(name: str, files: dict[str, str], exe: str | None = None,
                empty_exe: bool = False) -> Path:
        code = root / name / "Code"
        code.mkdir(parents=True)
        for filename, content in files.items():
            (code / filename).write_text(content, encoding="utf-8")
        if exe is not None or empty_exe:
            (root / name / "Exe").mkdir()
        if exe is not None:
            (root / name / "Exe" / exe).write_text(FAKE_EXE_TEXT, encoding="utf-8")
        return code

    # Reihenfolge der Änderungszeit: zuletzt angelegte stehen oben
    project("Notizen", {"notizen.py": "print('Notizen')\n"})
    project("Bildbeschreiber", {"main.py": "print('Bildbeschreiber')\n"}, empty_exe=True)
    time.sleep(0.02)
    project("Tagebuch", {"main.py": "print('Tagebuch')\n", "README.md": "# Tagebuch\n"})
    time.sleep(0.02)
    project("PDF-Chat", {"main.py": "print('PDF-Chat')\n", "README.md": "# PDF-Chat\n"},
            exe="PDF-Chat.exe")
    os.environ[HOME_VARIABLE] = str(home)
    return home, root


def remove_missing_example(root: Path) -> None:
    """Nach dem ersten Einlesen den Ordner von Notizen löschen, damit er als fehlend erscheint."""
    shutil.rmtree(root / "Notizen", ignore_errors=True)


def remove_old_vault_entries(database: Path, backend=None) -> int:
    """Test-Zugangsdaten des letzten Starts aus der Windows-Anmeldeinformationsverwaltung löschen.
    Gelöscht wird nur unter VAULT_SERVICE, nie unter dem echten Namen des Cockpits."""
    if not database.is_file():
        return 0
    try:
        connection = sqlite3.connect(database)
        try:
            names = [row[0] for row in connection.execute("SELECT name FROM vault_names")]
        finally:
            connection.close()                  # sonst lässt Windows den Ordner nicht löschen
    except sqlite3.Error:
        return 0
    if not names:
        return 0
    import keyring
    from keyring.errors import KeyringError
    backend = backend or keyring.get_keyring()
    removed = 0
    for name in names:
        try:
            backend.delete_password(VAULT_SERVICE, name)
            removed += 1
        except KeyringError:
            pass
    log.info("%s alte Test-Einträge im Tresor gelöscht", removed)
    return removed
