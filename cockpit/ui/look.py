"""Aussehen für das Auge (PLAN-OPTIK.md, Schritte 4, 5 und 7, 22.10.2026).

- Deutlicher Fokus: Listen haben mit Fokus einen Rahmen von 2 Pixeln in der Hervorhebungsfarbe.
- Erklärungen sehen aus wie Text: Listen mit explanation=True haben keinen Rahmen und den
  Hintergrund des Fensters. Für den Screenreader bleiben sie Listen, eine Zeile pro Satz.
- Programmsymbol "CC" und einige Symbole aus dem Windows-Stil in den Menüs. Symbole haben keinen
  eigenen Namen für den Screenreader.

Alle Farben kommen aus der Palette des Windows-Themas (palette(...)), hell und dunkel. Keine festen
Farben.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QAction, QFont, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QListWidget, QStyle

STYLE = """
QAbstractItemView {
    border: 1px solid palette(mid);
    border-radius: 4px;
    padding: 1px;
}
QAbstractItemView:focus {
    border: 2px solid palette(highlight);
    padding: 0px;
}
QAbstractItemView[explanation="true"] {
    border: none;
    padding: 2px;
    background: palette(window);
}
QAbstractItemView[explanation="true"]:focus {
    border: none;
    border-left: 2px solid palette(highlight);
    padding: 2px;
}
"""

MENU_ICONS = {
    "Projekt vom &Rechner hinzufügen …": QStyle.StandardPixmap.SP_DirOpenIcon,
    "Projekte &neu einlesen": QStyle.StandardPixmap.SP_BrowserReload,
    "&Terminal hier öffnen": QStyle.StandardPixmap.SP_ComputerIcon,
    "Tresor &sperren": QStyle.StandardPixmap.SP_DialogNoButton,
    "Hilfe und &Kurzanleitungen …": QStyle.StandardPixmap.SP_DialogHelpButton,
    "&Meldungen …": QStyle.StandardPixmap.SP_MessageBoxInformation,
    "Nach &Updates suchen …": QStyle.StandardPixmap.SP_ArrowDown,
}


def apply(app: QApplication) -> None:
    """Beim Start einmal aufrufen: Stylesheet und Programmsymbol."""
    app.setStyleSheet(STYLE)
    app.setWindowIcon(app_icon(app.palette()))


def mark_explanation(widget: QListWidget) -> None:
    """Liste mit Erklärungen: sieht aus wie Text, bleibt für den Screenreader eine Liste."""
    widget.setProperty("explanation", True)
    widget.setFrameShape(QListWidget.Shape.NoFrame)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def app_icon(palette: QPalette) -> QIcon:
    """Die Buchstaben CC auf der Akzentfarbe des Themas, in mehreren Größen."""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(palette.color(QPalette.ColorRole.Highlight))
        painter.drawRoundedRect(QRectF(0, 0, size, size), size * 0.2, size * 0.2)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(max(7, int(size * 0.5)))
        painter.setFont(font)
        painter.setPen(palette.color(QPalette.ColorRole.HighlightedText))
        painter.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "CC")
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def menu_icon(action: QAction) -> None:
    """Symbol aus dem Windows-Stil für bekannte Menüeinträge."""
    pixmap = MENU_ICONS.get(action.text())
    app = QApplication.instance()
    if pixmap is not None and app is not None:
        action.setIcon(app.style().standardIcon(pixmap))
