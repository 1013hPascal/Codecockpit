"""Lizenzdatei eines Projekts (Wunsch des Nutzers vom 03.10.2026), ohne Qt.

Die Lizenz liegt im Ordner Code als LICENSE, kommt mit ins Repository und liegt immer neben der
Exe. Auf der Projektzeile steht dafür "Lizenz …".
"""
from __future__ import annotations

import shutil
from pathlib import Path

from cockpit.core import backups
from cockpit.core.errors import CockpitError

FILE = "LICENSE"
NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md", "LICENCE.txt",
         "COPYING", "COPYING.md", "COPYING.txt")
KNOWN = (("Apache License", "Apache-2.0"), ("GNU LESSER GENERAL PUBLIC", "LGPL-3.0"),
         ("GNU GENERAL PUBLIC", "GPL-3.0"), ("Mozilla Public License", "MPL-2.0"),
         ("BSD 3-Clause", "BSD-3-Clause"), ("Redistribution and use in source and binary",
                                            "BSD-3-Clause"),
         ("MIT License", "MIT"), ("Permission is hereby granted, free of charge", "MIT"),
         ("The Unlicense", "Unlicense"), ("This is free and unencumbered", "Unlicense"))


def find(code_dir: Path) -> Path | None:
    return next((code_dir / n for n in NAMES if (code_dir / n).is_file()), None)


def name(code_dir: Path) -> str:
    """Kurzname der Lizenz, zum Beispiel "MIT". Leer ohne Lizenz, "eigene Lizenz" wenn das
    Cockpit sie nicht erkennt."""
    path = find(code_dir)
    if path is None:
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:2000]
    except OSError:
        return "eigene Lizenz"
    return next((short for marker, short in KNOWN if marker.lower() in text.lower()),
                "eigene Lizenz")


def state(code_dir: Path) -> str:
    """Für die Aktion "Lizenz …": ob es eine gibt und welche."""
    found = name(code_dir)
    return found if found else "noch keine Lizenz"


def write(project_name: str, code_dir: Path, text: str) -> Path | None:
    """Text als LICENSE speichern. Eine vorhandene Lizenzdatei kommt vorher in die
    Sicherheitskopien. Gibt deren Ordner zurück, None wenn es noch keine gab."""
    if not text.strip():
        raise CockpitError("Der Lizenztext ist leer.")
    old = find(code_dir)
    backup = None
    if old is not None:
        backup = backups.new_backup_dir(project_name, "Lizenz ersetzt", code_dir)
        shutil.copy2(old, backup / old.name)
        if old.name != FILE:
            old.unlink()
    (code_dir / FILE).write_text(text.replace("\r\n", "\n").rstrip() + "\n", encoding="utf-8")
    return backup


def read_file(source: Path) -> str:
    """Text einer gewählten Lizenzdatei."""
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise CockpitError(f"Die Datei {source.name} ließ sich nicht lesen.", str(exc)) from None
    try:
        if b"\0" in data:
            raise UnicodeDecodeError("utf-8", data, 0, 1, "Nullbyte")
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise CockpitError(f"{source.name} ist keine Textdatei in UTF-8.") from None
