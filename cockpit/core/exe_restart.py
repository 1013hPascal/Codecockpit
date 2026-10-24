"""Eigene Exe des Cockpits: Austausch beim Neustart.

Das Cockpit kann seine laufende Exe nicht ersetzen. Ein kleines Skript tauscht sie nach dem Beenden.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from cockpit.core import backups, paths
from cockpit.core.errors import CockpitError
from cockpit.core.exe_state import (
    FLAGS, PENDING, exe_in, folder_version, is_branch_exe, is_version_home, read_record,
    write_record)
from cockpit.core.projects import Project


# -- Eigene Exe: Austausch beim Neustart ------------------------------------------------------------
def restart_script(project: Project) -> Path:
    """Startskript, das auf das Ende des Cockpits wartet, die wartende Exe übernimmt und sie
    startet. Die bisherige Exe kommt vorher in eine Sicherheitskopie."""
    exe_dir = project.exe_dir
    pending = exe_dir / PENDING
    new_items = list(pending.iterdir()) if pending.is_dir() else []
    if not new_items:
        raise CockpitError("Es wartet keine neue Version.")
    folder = backups.new_backup_dir(project.name, "Exe vor dem Neustart ersetzt", exe_dir)
    # Versionen bleiben, wie bei backup_current (Rückmeldung des Nutzers vom 11.10.2026: Das
    # Cockpit lief aus CodeCockpit-v1.1.23, der Ordner ließ sich nicht verschieben, und die neue
    # Exe blieb in Release\_neu liegen)
    old_items: list = [p for p in exe_dir.iterdir() if p.name != PENDING and not is_branch_exe(p)
                       and not is_version_home(p)]
    # Eine veröffentlichte bisherige Version bleibt als Name-vVersion daneben (20.10.2026)
    for number, item in enumerate(old_items):
        version = folder_version(item) if item.is_dir() else ""
        target = exe_dir / f"{item.name}-v{version}"
        if version and not target.exists():
            old_items[number] = (item, target)
    new_exe = exe_in(new_items[0])
    script = swap_script(exe_dir, old_items, new_items, folder,
                         exe_dir / new_exe.relative_to(pending))
    record = read_record(project.code_dir)
    if record is not None:
        record.pending = False
        write_record(project.code_dir, record)
    return script


def swap_script(exe_dir: Path, old_items: list, new_items: list[Path], backup: Path,
                start: Path | None, pid: int | None = None, new_dir: Path | None = None) -> Path:
    """Skript, das auf das Ende des Cockpits wartet, old_items in die Sicherheitskopie backup
    verschiebt, new_items aus Release\\_neu nach new_dir (sonst exe_dir) holt und start startet
    (None: nicht starten). Ein Eintrag (Quelle, Ziel) in old_items kommt nicht in die
    Sicherheitskopie, sondern nach Ziel, zum Beispiel Release\\CodeCockpit-v1.1.30 (20.10.2026).
    Genutzt vom Neustart nach dem Bauen und von der Selbst-Aktualisierung (update.py)."""
    pending = exe_dir / PENDING
    new_dir = new_dir or exe_dir
    old_moves = [item if isinstance(item, tuple) else (item, backup / item.name)
                 for item in old_items]
    pid = pid or os.getpid()                  # auf das Ende dieses Prozesses warten
    # Befehle mit vollem Pfad (kein anderes find aus dem Suchpfad). Beim Test des Nutzers kam
    # das Skript nicht aus der Warteschleife, und die neue Exe blieb in Release\_neu liegen.
    system = r"%SystemRoot%\System32"
    lines = ["@echo off", "chcp 65001 >nul", "set versuche=0",
             ":warten",
             f'"{system}\\tasklist.exe" /FI "PID eq {pid}" /NH | "{system}\\find.exe" '
             f'" {pid} " >nul',
             "if not errorlevel 1 (timeout /t 1 /nobreak >nul & goto warten)"]
    # Kurz nach dem Beenden kann Windows die alte Exe noch sperren: bis zu 30 Versuche
    moves = old_moves + [(item, new_dir / item.name) for item in new_items]
    for number, (source, target) in enumerate(moves, start=1):
        if number == len(old_moves) + 1 and new_dir != exe_dir:
            # Der feste Ordner entsteht erst, wenn der bisherige umbenannt ist
            lines.append(f'if not exist "{new_dir}" mkdir "{new_dir}"')
        lines += [f":schieben{number}",
                  f'move /Y "{source}" "{target}" >nul 2>nul',
                  f"if not errorlevel 1 goto fertig{number}",
                  "set /a versuche+=1",
                  "if %versuche% geq 30 goto aufgeben",
                  "timeout /t 1 /nobreak >nul",
                  f"goto schieben{number}",
                  f":fertig{number}"]
    lines.append(f'rmdir /S /Q "{pending}"')
    if start is not None:
        lines.append(f'start "" "{start}"')
    lines.append('(goto) 2>nul & del "%~f0"')
    lines.append(":aufgeben")
    # Klappt das Tauschen nicht, kommt schon Verschobenes zurück. So bleibt nichts halb getauscht,
    # und die neue Exe wartet weiter in Release\_neu (Rückmeldung des Nutzers vom 11.10.2026)
    for item, target in old_moves:
        lines.append(f'if exist "{target}" if not exist "{item}" '
                     f'move /Y "{target}" "{item}" >nul 2>nul')
    # Startet wenigstens die bisherige Exe wieder, falls sie noch da ist
    if start is not None:
        lines.append(f'if exist "{start}" start "" "{start}"')
    lines.append('(goto) 2>nul & del "%~f0"')
    script = paths.cache_dir() / "cockpit-neustart.bat"
    script.parent.mkdir(parents=True, exist_ok=True)
    # Genau CR LF je Zeile. write_text hätte aus jedem \n noch einmal \r\n gemacht.
    script.write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))
    return script


def launch_restart(script: Path) -> None:
    """Skript unsichtbar starten. Ohne DETACHED_PROCESS: Damit bekam jeder Befehl im Skript ein
    eigenes Konsolenfenster, beim Test des Nutzers das leere Fenster "find". Die neue
    Prozessgruppe lässt das Skript weiterlaufen, wenn das Cockpit sich beendet.
    Ohne die Variablen von PyInstaller (20.10.2026): Eine Exe, die das Skript startet, hielt sich
    sonst für einen Teil der alten Exe und meldete beim Start einen Fehler."""
    subprocess.Popen(["cmd.exe", "/c", str(script)], close_fds=True, env=clean_environment(),
                     creationflags=FLAGS | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))


def clean_environment() -> dict[str, str]:
    """Umgebung ohne die Variablen, die eine Exe von PyInstaller für sich selbst setzt.
    PYINSTALLER_RESET_ENVIRONMENT sagt einer neu gestarteten Exe, dass sie eigenständig ist."""
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith(("_PYI_", "_MEIPASS"))}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env
