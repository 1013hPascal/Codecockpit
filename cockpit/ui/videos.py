"""Erklärvideos im Ordner erklärvideos (Wunsch des Nutzers, 29.09.2026).

Die Videos kommen mit dem Programm und mit der Exe. Das Cockpit öffnet sie mit dem Programm, das
Windows für Videos eingestellt hat. Beide Videos hat der Nutzer mit Google NotebookLM erstellt.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget

from cockpit.core import core_actions, paths
from cockpit.ui.announcer import announce
from cockpit.ui.error_dialog import show_error

FOLDER = "erklärvideos"
INTRO = "Code-Projekte_barrierefrei_und_mit_KI_verwalten.mp4"
GIT_BASICS = "Git_für_Anfänger.mp4"


def open_video(parent: QWidget, name: str, title: str) -> bool:
    """Video mit dem Standardprogramm öffnen. Fehlt die Datei, erscheint eine Meldung."""
    path = paths.resource_dir() / FOLDER / name
    if not path.is_file():
        show_error(parent, title, "Das Video wurde nicht gefunden.", str(path))
        return False
    try:
        core_actions.open_path(path)
    except OSError as exc:
        show_error(parent, title, "Das Video lässt sich nicht öffnen.", str(exc))
        return False
    announce("Das Video wird geöffnet.")
    return True
