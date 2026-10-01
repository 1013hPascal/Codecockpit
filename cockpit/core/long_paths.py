"""Lange Pfade in Windows (Wunsch des Nutzers, 01.10.2026).

Ohne diese Einstellung erlaubt Windows höchstens 260 Zeichen pro Pfad. Bibliotheken wie PySide6
haben tief verschachtelte Dateien. Liegt das Projekt tief, scheitert pip dann beim Installieren.
Einschalten braucht einmal Administratorrechte. Das Cockpit fragt vorher und startet dafür reg.exe
über die Rückfrage von Windows (Benutzerkontensteuerung).
"""
from __future__ import annotations

import subprocess
import sys

KEY = r"SYSTEM\CurrentControlSet\Control\FileSystem"
VALUE = "LongPathsEnabled"
PIP_HINT = "long path"                 # steht in der Meldung von pip, kleingeschrieben verglichen
LIMIT = 260


def enabled() -> bool:
    """True, wenn Windows lange Pfade erlaubt. Außerhalb von Windows immer True."""
    if sys.platform != "win32":
        return True
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, KEY) as key:
            value, _kind = winreg.QueryValueEx(key, VALUE)
    except OSError:
        return False
    return value == 1


def is_long_path_error(text: str) -> bool:
    """Die Ausgabe von pip nennt das Problem mit langen Pfaden."""
    return PIP_HINT in text.lower()


def enable() -> bool:
    """Lange Pfade einschalten. Windows fragt nach Administratorrechten. Gibt zurück, ob die
    Einstellung danach an ist. Lehnt der Nutzer ab, ändert sich nichts."""
    if sys.platform != "win32":
        return True
    arguments = f"add HKLM\\{KEY} /v {VALUE} /t REG_DWORD /d 1 /f"
    command = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
               f"Start-Process -FilePath reg.exe -ArgumentList '{arguments}' -Verb RunAs "
               "-WindowStyle Hidden -Wait"]
    try:
        subprocess.run(command, capture_output=True, timeout=300,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return False
    return enabled()
