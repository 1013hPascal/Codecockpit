"""Virtuelle Umgebung nach dem Verschieben eines Projekts (Konzept 7.5).

Eine virtuelle Umgebung (.venv) enthält feste Pfade und funktioniert nach dem Verschieben nicht
mehr. Das Cockpit erkennt das und legt sie nach Rückfrage neu an:
1. Die alte Umgebung wandert als Sicherheitskopie in den Ordner backups.
2. python -m venv .venv mit derselben Python-Version.
3. pip install -r requirements.txt, falls die Datei da ist.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from cockpit.core import backups
from cockpit.core.errors import Cancelled, CockpitError

VENV = ".venv"
_ACTIVATE = re.compile(r'set\s+"?VIRTUAL_ENV=([^"\r\n]+)"?', re.IGNORECASE)


@dataclass(frozen=True)
class VenvState:
    exists: bool
    broken: bool = False
    reason: str = ""                 # einfacher Text, warum sie nicht funktioniert
    python: str = ""                 # Python, mit dem sie angelegt wurde
    version: str = ""                # "3.14.6"


def _config(venv: Path) -> dict[str, str]:
    result = {}
    try:
        lines = (venv / "pyvenv.cfg").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return result
    for line in lines:
        key, sep, value = line.partition("=")
        if sep:
            result[key.strip().lower()] = value.strip()
    return result


def _recorded_location(venv: Path, config: dict[str, str]) -> str:
    """Wo die Umgebung angelegt wurde: aus activate.bat, sonst aus pyvenv.cfg (command)."""
    try:
        match = _ACTIVATE.search((venv / "Scripts" / "activate.bat").read_text(
            encoding="utf-8", errors="replace"))
        if match:
            return match.group(1).strip()
    except OSError:
        pass
    command = config.get("command", "")
    marker = " -m venv "
    if marker in command:
        return command.split(marker, 1)[1].strip().strip('"')
    return ""


def check(code_dir: Path) -> VenvState:
    venv = code_dir / VENV
    config = _config(venv)
    if not config:
        return VenvState(False)
    python = config.get("executable") or str(Path(config.get("home", "")) / "python.exe")
    version = config.get("version") or config.get("version_info", "")
    recorded = _recorded_location(venv, config)
    if recorded and os.path.normcase(os.path.normpath(recorded)) != os.path.normcase(
            os.path.normpath(str(venv.resolve()))):
        return VenvState(True, True, "Das Projekt wurde verschoben.", python, version)
    if python and not Path(python).is_file():
        return VenvState(True, True, "Das Python, mit dem sie angelegt wurde, fehlt.", python,
                         version)
    return VenvState(True, False, "", python, version)


def find_python(state: VenvState) -> list[str]:
    """Befehl für dasselbe Python wie vorher. Sonst den Python-Starter py mit der Version."""
    if state.python and Path(state.python).is_file():
        return [state.python]
    launcher = shutil.which("py")
    short = ".".join(state.version.split(".")[:2])
    if launcher and short:
        return [launcher, f"-{short}"]
    name = f"Python {short}" if short else "Python"
    raise CockpitError(f"{name} wurde nicht gefunden. Bitte installieren Sie es und versuchen "
                       "Sie es erneut.")


def _run(command: list[str], cwd: Path, cancel: threading.Event | None) -> None:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(command, cwd=str(cwd), stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               creationflags=flags)
    while True:
        try:
            out, _ = process.communicate(timeout=0.2)
            break
        except subprocess.TimeoutExpired:
            if cancel is not None and cancel.is_set():
                process.kill()
                process.communicate()
                raise Cancelled() from None
    if process.returncode != 0:
        text = out.decode("utf-8", "replace").strip()
        raise CockpitError("Die virtuelle Umgebung ließ sich nicht neu anlegen.",
                           f"{' '.join(command[1:])}: {text[-3000:]}")


def steps(code_dir: Path) -> list[str]:
    """Die Schritte als Text, für "Schritt 1 von 3"."""
    result = ["Alte Umgebung wird gesichert", "Neue Umgebung wird angelegt"]
    if (code_dir / "requirements.txt").is_file():
        result.append("Pakete aus requirements.txt werden installiert")
    return result


def repair(code_dir: Path, project_name: str, progress: Callable[[int, int, str], None],
           cancel: threading.Event | None = None) -> Path:
    """Umgebung neu anlegen. Blockiert, also nur im Hintergrund. Gibt den Ort der
    Sicherheitskopie zurück."""
    state = check(code_dir)
    python = find_python(state)
    names = steps(code_dir)
    total = len(names)
    progress(1, total, names[0])
    backup = backups.move_into_backup(code_dir / VENV, project_name, "venv")
    progress(2, total, names[1])
    _run([*python, "-m", "venv", VENV], code_dir, cancel)
    if total == 3:
        progress(3, total, names[2])
        _run([str(code_dir / VENV / "Scripts" / "python.exe"), "-m", "pip", "install", "-r",
              "requirements.txt"], code_dir, cancel)
    return backup
