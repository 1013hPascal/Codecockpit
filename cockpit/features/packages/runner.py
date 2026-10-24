"""Programme der Paketübersicht aufrufen: pip, winget, choco und ollama.

Alle Aufrufe gehen über run() oder elevated(). Tests ersetzen diese beiden Funktionen, damit nie
ein echtes Programm etwas installiert oder löscht. Geheimnisse kommen hier nie auf die
Befehlszeile.
"""
from __future__ import annotations

import ctypes
import logging
import os
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from cockpit.core.errors import Cancelled, CockpitError

log = logging.getLogger(__name__)


@dataclass
class Result:
    code: int
    lines: list[str]

    @property
    def ok(self) -> bool:
        return self.code == 0

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def environment() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    return env


def find(program: str) -> str | None:
    """Ganzer Pfad eines Programms, None wenn es fehlt."""
    found = shutil.which(program)
    if found is None and program == "choco":
        candidate = Path(os.environ.get("ChocolateyInstall", r"C:\ProgramData\chocolatey")) \
            / "bin" / "choco.exe"
        found = str(candidate) if candidate.is_file() else None
    return found


def run(args: list[str], cancel: threading.Event | None = None,
        on_line: Callable[[str], None] | None = None, cwd: Path | None = None) -> Result:
    """Programm ausführen und die Ausgabe sammeln. Wirft Cancelled bei Abbruch und
    CockpitError, wenn es sich nicht starten lässt."""
    from cockpit.core.exe import run_process
    lines: list[str] = []

    def collect(line: str) -> None:
        lines.append(line)
        if on_line is not None:
            on_line(line)

    code = run_process(args, cwd or Path.home(), collect, cancel, env=environment())
    return Result(code, lines)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


class _ShellExecuteInfo(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("fMask", ctypes.c_ulong),
                ("hwnd", ctypes.c_void_p), ("lpVerb", ctypes.c_wchar_p),
                ("lpFile", ctypes.c_wchar_p), ("lpParameters", ctypes.c_wchar_p),
                ("lpDirectory", ctypes.c_wchar_p), ("nShow", ctypes.c_int),
                ("hInstApp", ctypes.c_void_p), ("lpIDList", ctypes.c_void_p),
                ("lpClass", ctypes.c_wchar_p), ("hkeyClass", ctypes.c_void_p),
                ("dwHotKey", ctypes.c_ulong), ("hIcon", ctypes.c_void_p),
                ("hProcess", ctypes.c_void_p)]


def _quote(arg: str) -> str:
    return subprocess.list2cmdline([arg])


def elevated(args: list[str], cancel: threading.Event | None = None) -> Result:
    """Mit Administratorrechten ausführen, Windows fragt vorher nach. Die Ausgabe kommt über
    eine Datei zurück, weil ein Programm mit anderen Rechten nicht in dieses Fenster schreibt.
    Hat das Cockpit schon Administratorrechte, läuft es wie run()."""
    if is_admin():
        return run(args, cancel)
    handle, name = tempfile.mkstemp(prefix="cockpit-paket-", suffix=".txt")
    os.close(handle)
    output = Path(name)
    command = " ".join(_quote(a) for a in args) + f" > {_quote(str(output))} 2>&1"
    info = _ShellExecuteInfo()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x00000040                      # SEE_MASK_NOCLOSEPROCESS
    info.lpVerb = "runas"
    info.lpFile = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32",
                               "cmd.exe")
    info.lpParameters = f'/c "{command}"'
    info.nShow = 0                               # SW_HIDE
    try:
        if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(info)):
            raise CockpitError("Windows hat die Administratorrechte nicht gegeben. Die Änderung "
                               "wurde nicht ausgeführt.")
        kernel = ctypes.windll.kernel32
        while kernel.WaitForSingleObject(ctypes.c_void_p(info.hProcess), 500) == 0x102:
            if cancel is not None and cancel.is_set():
                kernel.TerminateProcess(ctypes.c_void_p(info.hProcess), 1)
                raise Cancelled()
        code = ctypes.c_ulong()
        kernel.GetExitCodeProcess(ctypes.c_void_p(info.hProcess), ctypes.byref(code))
        kernel.CloseHandle(ctypes.c_void_p(info.hProcess))
        text = output.read_bytes().decode("utf-8", "replace") if output.is_file() else ""
        return Result(code.value, [line for line in text.splitlines() if line.strip()])
    finally:
        try:
            output.unlink()
        except OSError:
            pass


def require(result: Result, what: str) -> Result:
    """Fehler mit den letzten Zeilen der Ausgabe als Details."""
    if not result.ok:
        raise CockpitError(f"{what} hat nicht geklappt.", "\n".join(result.lines[-30:]))
    return result
