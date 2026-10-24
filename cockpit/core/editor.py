"""Dateien und Ordner im Editor öffnen (Wunsch des Nutzers vom 21.10.2026, nach dem Vergleich mit
GitHub Desktop).

Welcher Editor: der aus den Grundeinstellungen, sonst der erste gefundene aus Visual Studio Code,
Notepad++ und dem Windows-Editor. Bei Visual Studio Code und Notepad++ springt der Editor gleich
in die richtige Zeile, zum Beispiel zur ersten Konfliktstelle.

Früher öffnete das Cockpit Dateien mit dem Programm, das Windows für die Endung kennt. Bei einer
.py-Datei kann das Python selbst sein, dann liefe die Datei, statt sich zu öffnen. Deshalb gehen
Dateien jetzt immer an einen Editor.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from cockpit.core.errors import CockpitError

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Editor:
    name: str
    program: Path
    kind: str                     # "vscode", "notepadpp", "notepad" oder "other"

    @property
    def opens_folders(self) -> bool:
        return self.kind == "vscode"

    def command(self, path: Path, line: int | None = None) -> list[str]:
        if self.kind == "vscode":
            if line and path.is_file():
                return [str(self.program), "--goto", f"{path}:{line}"]
            return [str(self.program), str(path)]
        if self.kind == "notepadpp" and line:
            return [str(self.program), f"-n{line}", str(path)]
        return [str(self.program), str(path)]


def _env_path(name: str, *parts: str) -> Path | None:
    base = os.environ.get(name)
    return Path(base, *parts) if base else None


def _vscode() -> Path | None:
    candidates = [_env_path("LOCALAPPDATA", "Programs", "Microsoft VS Code", "Code.exe"),
                  _env_path("ProgramFiles", "Microsoft VS Code", "Code.exe")]
    cmd = shutil.which("code")
    if cmd:
        # code.cmd liegt in <Ordner>\bin, Code.exe eine Ebene höher. Code.exe direkt, weil sich
        # .cmd-Dateien nur über cmd.exe starten lassen.
        candidates.insert(0, Path(cmd).resolve().parent.parent / "Code.exe")
    return next((p for p in candidates if p is not None and p.is_file()), None)


def _notepadpp() -> Path | None:
    candidates = [_env_path("ProgramFiles", "Notepad++", "notepad++.exe"),
                  _env_path("ProgramFiles(x86)", "Notepad++", "notepad++.exe")]
    found = shutil.which("notepad++")
    if found:
        candidates.insert(0, Path(found))
    return next((p for p in candidates if p is not None and p.is_file()), None)


def _notepad() -> Path | None:
    found = shutil.which("notepad")
    return Path(found) if found else None


def _kind_of(program: Path) -> str:
    name = program.name.lower()
    if name in ("code.exe", "code.cmd", "code"):
        return "vscode"
    if name.startswith("notepad++"):
        return "notepadpp"
    if name == "notepad.exe":
        return "notepad"
    return "other"


def find(setting: str = "") -> Editor | None:
    """Der Editor aus der Einstellung, sonst der erste gefundene. None: keiner gefunden."""
    if setting.strip():
        program = Path(setting.strip().strip('"'))
        if not program.is_file():
            raise CockpitError(f"Den Editor {program} gibt es nicht. Prüfen Sie die "
                               "Grundeinstellungen.")
        return Editor(program.stem, program, _kind_of(program))
    for name, kind, finder in (("Visual Studio Code", "vscode", _vscode),
                               ("Notepad++", "notepadpp", _notepadpp),
                               ("Windows-Editor", "notepad", _notepad)):
        program = finder()
        if program is not None:
            return Editor(name, program, kind)
    return None


def _start(command: list[str]) -> None:
    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True)


start = _start                                   # in Tests ersetzbar


def open_in_editor(path: Path, line: int | None = None, setting: str = "") -> str:
    """Datei oder Ordner im Editor öffnen. Gibt den Namen des Editors zurück. Ein Ordner geht an
    den Explorer, wenn der Editor keine Ordner kann."""
    editor = find(setting)
    if path.is_dir() and (editor is None or not editor.opens_folders):
        from cockpit.core import core_actions
        core_actions.open_path(path)
        return "Explorer"
    if editor is None:
        raise CockpitError("Es wurde kein Editor gefunden. Tragen Sie in den Grundeinstellungen "
                           "einen ein.")
    try:
        start(editor.command(path, line))
    except OSError as exc:
        raise CockpitError(f"{editor.name} ließ sich nicht starten.", repr(exc)) from None
    log.info("Im Editor geöffnet: %s mit %s", path.name, editor.name)
    return editor.name
