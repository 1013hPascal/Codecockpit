"""Zeichner der Projektliste, nur für das Auge (PLAN-OPTIK.md, Schritte 1 und 3, 22.10.2026).

Zeilen unter einem Projekt und Projekte in einer geöffneten Sammlung sind eingerückt. Vor Projekten
und Sammlungen steht ein Pfeil: nach rechts zugeklappt, nach unten ausgeklappt. Bei Projekten und
Sammlungen ist der Name fett, Datum und "ausgeklappt" sind gedämpft (row_delegate). Text und
Accessible Name der Zeilen ändern sich nicht. Was der Pfeil zeigt, steht als "ausgeklappt" oder
"geöffnet" auch im Text.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QStyleOptionViewItem

from cockpit.ui.row_delegate import RowDelegate

if TYPE_CHECKING:
    from cockpit.ui.project_list import ProjectList

INDENT = 24                      # Pixel je Ebene
ARROW = 18                       # Platz für den Pfeil vor jeder Zeile
OPEN, CLOSED = "▾", "▸"


class ProjectRowDelegate(RowDelegate):
    def __init__(self, view: "ProjectList") -> None:
        super().__init__(view, bold_head=lambda row: view.row_look(row)[2])
        self.view = view

    def paint(self, painter, option: QStyleOptionViewItem, index) -> None:
        depth, arrow, _ = self.view.row_look(index.row())
        left = option.rect.left() + INDENT * depth
        shifted = QStyleOptionViewItem(option)
        shifted.rect = QRect(option.rect)
        shifted.rect.setLeft(left + ARROW)
        super().paint(painter, shifted, index)
        if not arrow:
            return
        painter.save()
        # Textfarbe wie die Zeile: Der Stil von Windows 11 hebt die Auswahl nur leicht hervor
        painter.setPen(option.palette.color(QPalette.ColorRole.Text))
        box = QRect(left, option.rect.top(), ARROW, option.rect.height())
        painter.drawText(box, Qt.AlignmentFlag.AlignCenter, arrow)
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index):
        size = super().sizeHint(option, index)
        size.setWidth(size.width() + ARROW + INDENT * self.view.row_look(index.row())[0])
        return size
