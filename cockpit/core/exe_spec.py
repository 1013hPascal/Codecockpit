"""Die .spec-Datei für PyInstaller: schreiben, erkennen, Einstellungen ändern.
"""
from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path

from cockpit.core import backups
from cockpit.core.exe_state import BuildSettings, read_settings, write_settings


# -- .spec-Datei ---------------------------------------------------------------------------------
SPEC_MARK = "# Erstellt von CodeCockpit."


def own_spec(path: Path) -> bool:
    """Hat das Cockpit diese .spec-Datei selbst geschrieben? Eine fehlende zählt als eigene.
    Eine von Hand geschriebene, etwa die des Cockpits, ändert es nie (Rückmeldung des Nutzers
    vom 03.10.2026: die Standardvorlage hatte sie überschrieben, der Exe fehlten danach Dateien)."""
    if not path.is_file():
        return True
    return path.read_text(encoding="utf-8", errors="replace").startswith(SPEC_MARK)


def spec_text(settings: BuildSettings) -> str:
    icon = repr(settings.icon) if settings.icon else "None"
    datas = [tuple(d) for d in settings.datas]
    head = (f"{SPEC_MARK} Sie dürfen die Datei anpassen, das Cockpit nutzt sie\n"
            f"# bei jedem Bau weiter. Pfade sind relativ zum Ordner Repository.\n\n"
            f"a = Analysis([{settings.start_file!r}], pathex=[], binaries=[], "
            f"datas={datas!r},\n"
            f"             hiddenimports={settings.hidden_imports!r}, excludes=[])\n"
            f"pyz = PYZ(a.pure)\n\n")
    if settings.one_file:
        return head + (f"exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], "
                       f"name={settings.name!r},\n"
                       f"          console={not settings.windowed!r}, icon={icon}, upx=False)\n")
    return head + (f"exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name={settings.name!r},\n"
                   f"          console={not settings.windowed!r}, icon={icon}, upx=False)\n"
                   f"coll = COLLECT(exe, a.binaries, a.datas, name={settings.name!r}, "
                   f"upx=False)\n")


def ensure_spec(code_dir: Path, settings: BuildSettings) -> Path:
    """Vorhandene .spec-Datei weiterverwenden, sonst eine neue schreiben."""
    path = code_dir / settings.spec_name
    if not path.is_file():
        path.write_text(spec_text(settings), encoding="utf-8")
    return path


def change_settings(code_dir: Path, project_name: str, settings: BuildSettings) -> Path | None:
    """Exe-Einstellungen ändern (Phase 10g). Die .spec-Datei wird neu geschrieben, wenn sich
    etwas darin ändert. Die alte kommt vorher in die Sicherheitskopien. Gibt diese zurück.
    Eine von Hand geschriebene .spec-Datei bleibt, wie sie ist. Dann ändern sich nur die
    Einstellungen in cockpit.toml, zum Beispiel die Ordner neben der Exe."""
    old = read_settings(code_dir)
    if old is not None and not own_spec(code_dir / old.spec_name):
        write_settings(code_dir, dataclasses.replace(settings, name=old.name))
        return None
    write_settings(code_dir, settings)
    backup = None
    if old is not None and (code_dir / old.spec_name).is_file():
        spec = code_dir / old.spec_name
        if spec.read_text(encoding="utf-8", errors="replace") != spec_text(settings) \
                or old.spec_name != settings.spec_name:
            backup = backups.new_backup_dir(project_name, "Exe-Einstellungen geändert", code_dir)
            shutil.copy2(spec, backup / spec.name)
            if old.spec_name != settings.spec_name:
                spec.unlink()
    (code_dir / settings.spec_name).write_text(spec_text(settings), encoding="utf-8")
    return backup


def spec_is_one_file(spec: Path) -> bool:
    return "COLLECT(" not in spec.read_text(encoding="utf-8", errors="replace")
