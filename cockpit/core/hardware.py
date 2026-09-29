"""Arbeitsspeicher, Prozessor und Grafikkarte auslesen (Konzept 11.1). Vorbild: Chatbot.

Der Arbeitsspeicher entscheidet über die Stufe der lokalen KI. Gelingt das Auslesen nicht, gibt man
ihn in der KI-Verwaltung selbst ein. Diese Angabe hat dann Vorrang.
"""
from __future__ import annotations

import ctypes
import json
import subprocess
import sys
from dataclasses import dataclass, field

MANUAL_KEY = "ai.ram_gb"               # von Hand eingegebener Arbeitsspeicher in GB
WHERE_TO_LOOK = ("Den Arbeitsspeicher finden Sie in Windows unter Einstellungen, System, Info, "
                 "bei Installierter RAM.")


@dataclass
class Machine:
    ram_gb: float | None = None
    cpu: str = ""
    gpus: list[str] = field(default_factory=list)
    manual: bool = False                # Arbeitsspeicher von Hand eingegeben

    def lines(self) -> list[str]:
        """Für die KI-Verwaltung, das Wichtigste vorne."""
        if self.ram_gb is None:
            ram = f"Arbeitsspeicher Ihres Computers: nicht erkannt. {WHERE_TO_LOOK}"
        else:
            ram = f"Arbeitsspeicher Ihres Computers: {format_gb(self.ram_gb)}"
            if self.manual:
                ram += ", von Ihnen eingegeben"
        lines = [ram, f"Prozessor: {self.cpu or 'nicht erkannt'}"]
        lines.append(f"Grafikkarte: {', '.join(self.gpus)}" if self.gpus
                     else "Grafikkarte: nicht erkannt")
        return lines


def format_gb(value: float) -> str:
    return f"{value:.0f} GB" if abs(value - round(value)) < 0.05 else \
        f"{value:.1f} GB".replace(".", ",")


class _MemoryStatus(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def ram_gb() -> float | None:
    if sys.platform != "win32":
        return None
    status = _MemoryStatus()
    status.dwLength = ctypes.sizeof(_MemoryStatus)
    try:
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None
    except (AttributeError, OSError):
        return None
    return round(status.ullTotalPhys / 2 ** 30, 1)


def cpu_name() -> str:
    if sys.platform != "win32":
        return ""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            return " ".join(str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).split())
    except OSError:
        return ""


def gpu_names() -> list[str]:
    """Über PowerShell, dauert etwa eine Sekunde. Also im Hintergrund aufrufen."""
    if sys.platform != "win32":
        return []
    try:
        out = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name | "
             "ConvertTo-Json"],
            capture_output=True, timeout=20, stdin=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        data = json.loads(out.stdout.decode("utf-8", "replace") or "null")
    except (OSError, ValueError, subprocess.SubprocessError):
        return []
    names = data if isinstance(data, list) else [data] if data else []
    return [str(n).strip() for n in names if str(n).strip()]


def detect(manual_ram_gb: float | None = None) -> Machine:
    """Alles auslesen. Ein von Hand eingegebener Arbeitsspeicher hat Vorrang."""
    if manual_ram_gb:
        return Machine(float(manual_ram_gb), cpu_name(), gpu_names(), manual=True)
    return Machine(ram_gb(), cpu_name(), gpu_names())
