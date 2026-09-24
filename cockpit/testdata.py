"""Testdaten für den Test des Projektbaums mit NVDA (Start mit start_testdaten.bat).

Alles liegt in einem eigenen Ordner %LOCALAPPDATA%\\CodeCockpit\\Testdaten und wird bei jedem
Start neu angelegt. Die echten Daten des Cockpits werden nicht berührt.

Beispielprojekte:
- PDF-Chat: Code und Exe. Die Exe ist absichtlich keine echte Exe, damit man das Fehlerfenster
  testen kann.
- Tagebuch: nur Code.
- Bildbeschreiber: Code und ein leerer Ordner Exe.
- Notizen: steht in der Liste, der Ordner fehlt aber ("Ordner nicht gefunden").
"""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from cockpit import APP_NAME
from cockpit.core.paths import HOME_VARIABLE

FAKE_EXE_TEXT = "Dies ist keine echte Exe. Sie gehört zu den Testdaten von CodeCockpit.\n"


def base_dir() -> Path:
    local = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    return local / APP_NAME / "Testdaten"


def prepare(base: Path | None = None) -> tuple[Path, Path]:
    """Testdaten neu anlegen. Gibt (Datenordner, Projekte-Hauptordner) zurück und lenkt den
    Datenordner des Cockpits dorthin um."""
    base = base or base_dir()
    if base.exists():
        shutil.rmtree(base)
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
