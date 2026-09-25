"""Dateien in den Papierkorb von Windows verschieben (Konzept 9.7, ENTSCHEIDUNGEN.md).

Ohne neue Bibliothek über die Funktion SHFileOperationW von Windows. Aus dem Papierkorb lässt sich
eine Datei wie gewohnt wiederherstellen. In Tests wird move_to_recycle_bin ersetzt, damit nichts
im echten Papierkorb landet.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from cockpit.core.errors import CockpitError

log = logging.getLogger(__name__)

_FO_DELETE = 3
_FOF_SILENT = 0x0004
_FOF_NOCONFIRMATION = 0x0010
_FOF_ALLOWUNDO = 0x0040
_FOF_NOERRORUI = 0x0400


def _move_to_recycle_bin(paths: list[Path]) -> None:
    """Dateien in den Papierkorb. Wirft CockpitError, wenn eine Datei danach noch da ist."""
    if not paths:
        return
    if sys.platform != "win32":
        raise CockpitError("Der Papierkorb geht nur unter Windows.")
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT),
                    ("pFrom", ctypes.c_void_p), ("pTo", ctypes.c_void_p),
                    ("fFlags", ctypes.c_uint16), ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", ctypes.c_void_p)]

    # Die Liste der Pfade endet mit zwei Nullzeichen, jeder Pfad mit einem.
    buffer = ctypes.create_unicode_buffer("\0".join(str(p.resolve()) for p in paths) + "\0")
    operation = SHFILEOPSTRUCTW(
        None, _FO_DELETE, ctypes.cast(buffer, ctypes.c_void_p), None,
        _FOF_ALLOWUNDO | _FOF_NOCONFIRMATION | _FOF_SILENT | _FOF_NOERRORUI, False, None, None)
    code = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))
    left = [p for p in paths if p.exists()]
    if code != 0 or operation.fAnyOperationsAborted or left:
        names = ", ".join(p.name for p in left) or ", ".join(p.name for p in paths)
        raise CockpitError(f"{names} ließ sich nicht in den Papierkorb verschieben. Vielleicht ist "
                           "die Datei noch geöffnet.", f"SHFileOperationW: {code}")
    log.info("In den Papierkorb: %s", ", ".join(str(p) for p in paths))


move_to_recycle_bin = _move_to_recycle_bin
