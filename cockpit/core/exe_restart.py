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
    current: list = [p for p in exe_dir.iterdir() if p.name != PENDING and not is_branch_exe(p)
                     and not is_version_home(p)]
    # Wunsch des Nutzers vom 26.10.2026: Ein Ordner wie Release\CodeCockpit bleibt stehen, nur
    # sein Inhalt wird getauscht. Sonst folgt ein offenes Explorer-Fenster dem umbenannten
    # Ordner, und man startet daraus wieder die alte Version.
    first = new_items[0]                          # darin liegt die neue Exe
    replacements = {p.name.lower(): p for p in new_items if p.is_dir()}
    old_items: list = []
    moves_in: list = []
    make_dirs: list[Path] = []
    for item in current:
        # Eine veröffentlichte bisherige Version bleibt als Name-vVersion daneben (20.10.2026)
        version = folder_version(item) if item.is_dir() else ""
        target = exe_dir / f"{item.name}-v{version}"
        keep = bool(version) and not target.exists()
        replacement = replacements.pop(item.name.lower(), None) if item.is_dir() else None
        if replacement is None:
            old_items.append((item, target) if keep else item)
            continue
        place = target if keep else folder / item.name
        make_dirs.append(place)
        old_items += [(child, place / child.name) for child in sorted(item.iterdir())]
        moves_in += [(child, item / child.name) for child in sorted(replacement.iterdir())]
        new_items.remove(replacement)
    new_exe = exe_in(first)
    script = swap_script(exe_dir, old_items, moves_in + new_items, folder,
                         exe_dir / new_exe.relative_to(pending), make_dirs=make_dirs)
    record = read_record(project.code_dir)
    if record is not None:
        record.pending = False
        write_record(project.code_dir, record)
    return script


def swap_script(exe_dir: Path, old_items: list, new_items: list[Path], backup: Path,
                start: Path | None, pid: int | None = None, new_dir: Path | None = None,
                make_dirs: list[Path] | tuple = ()) -> Path:
    """Skript, das auf das Ende des Cockpits wartet, old_items in die Sicherheitskopie backup
    verschiebt, new_items aus Release\\_neu nach new_dir (sonst exe_dir) holt und start startet
    (None: nicht starten). Ein Eintrag (Quelle, Ziel) in old_items kommt nicht in die
    Sicherheitskopie, sondern nach Ziel, zum Beispiel Release\\CodeCockpit-v1.1.30 (20.10.2026).
    make_dirs: Ordner, die vor dem Verschieben entstehen, zum Beispiel der Ordner für die
    bisherige Version (26.10.2026). Klappt der Tausch nicht, verschwinden sie wieder, wenn leer.
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
    lines += [f'if not exist "{folder}" mkdir "{folder}"' for folder in make_dirs]
    # Kurz nach dem Beenden kann Windows die alte Exe noch sperren: bis zu 30 Versuche
    moves = old_moves + [item if isinstance(item, tuple) else (item, new_dir / item.name)
                         for item in new_items]
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
    lines += [f'rmdir "{folder}" >nul 2>nul' for folder in make_dirs]   # nur, wenn leer
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
