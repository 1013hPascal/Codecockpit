"""Fehlerfenster einer gestarteten Exe finden (Rückmeldung des Nutzers vom 02.10.2026).

Eine Exe mit Fenster, die PyInstaller gebaut hat, zeigt einen Absturz beim Start in einem
Meldungsfenster, zum Beispiel "Unhandled exception in script". Das Programm läuft dann weiter, bis
man das Fenster schließt. Ein Start-Test, der nur prüft, ob es nach 10 Sekunden noch läuft, hält
das für einen Erfolg. Dieses Modul sucht solche Fenster des Programms und seiner Kindprozesse und
liest ihren Text, also die Fehlermeldung mit Traceback. Nur Windows, über ctypes, ohne Qt.
"""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

TITLES = ("Unhandled exception", "Fatal error detected", "Failed to execute script")
_TH32CS_SNAPPROCESS = 0x00000002


class _ProcessEntry(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]


def _process_tree(pid: int) -> set[int]:
    """pid und alle Kindprozesse (eine einzelne Exe-Datei startet sich selbst ein zweites Mal)."""
    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
    if snapshot in (0, -1, ctypes.c_void_p(-1).value):
        return {pid}
    parents: dict[int, int] = {}
    try:
        entry = _ProcessEntry()
        entry.dwSize = ctypes.sizeof(_ProcessEntry)
        ok = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            parents[entry.th32ProcessID] = entry.th32ParentProcessID
            ok = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    tree = {pid}
    changed = True
    while changed:
        changed = False
        for child, parent in parents.items():
            if parent in tree and child not in tree:
                tree.add(child)
                changed = True
    return tree


def _text(hwnd) -> str:
    user32 = ctypes.windll.user32
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def error_text(pid: int) -> str:
    """Text eines Fehlerfensters des Prozesses oder seiner Kinder, sonst leer."""
    if sys.platform != "win32":
        return ""
    user32 = ctypes.windll.user32
    tree = _process_tree(pid)
    found: list[str] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def child(hwnd, _param):
        text = _text(hwnd).strip()
        if text:
            found.append(text)
        return True

    def window(hwnd, _param):
        if not user32.IsWindowVisible(hwnd):
            return True
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value not in tree:
            return True
        title = _text(hwnd)
        if any(title.startswith(t) for t in TITLES):
            found.append(title)
            user32.EnumChildWindows(hwnd, callback_type(child), 0)
            return False                         # das erste Fehlerfenster reicht
        return True

    user32.EnumWindows(callback_type(window), 0)
    # Knöpfe wie "OK" sind keine Fehlermeldung
    return "\n".join(t for t in found if t not in ("OK", "&OK", "Abbrechen", "Cancel"))
