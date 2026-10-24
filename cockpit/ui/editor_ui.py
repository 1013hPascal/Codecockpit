"""Im Editor öffnen, aus jedem Dialog heraus (21.10.2026).

Der Editor aus den Grundeinstellungen wird über das Hauptfenster gefunden: Der erste Eltern-
Widget mit services liefert sie. Ohne Hauptfenster, zum Beispiel in Tests, sucht das Cockpit
selbst einen Editor.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget

from cockpit.core import editor
from cockpit.core.errors import CockpitError
from cockpit.ui.announcer import announce
from cockpit.ui.error_dialog import show_error


def setting(widget: QWidget | None) -> str:
    while widget is not None:
        services = getattr(widget, "services", None)
        if services is not None:
            return services.settings.load().editor
        widget = widget.parentWidget()
    return ""


def open_in_editor(widget: QWidget | None, path: Path, line: int | None = None) -> bool:
    """Öffnen und ansagen. Bei einem Fehler kommt eine Meldung, dann False."""
    try:
        name = editor.open_in_editor(path, line, setting(widget))
    except CockpitError as exc:
        show_error(widget, "Im Editor öffnen", exc.message, exc.details)
        return False
    where = f", Zeile {line}" if line and name != "Explorer" else ""
    announce(f"Wird in {name} geöffnet{where}.")
    return True
