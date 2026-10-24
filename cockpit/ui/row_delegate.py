"""Zeilen in Listen mit zwei Textebenen, nur für das Auge (PLAN-OPTIK.md, Schritt 3).

Der Anfang einer Zeile (bis zum ersten Trenner, zum Beispiel der Projektname) ist fett. Teile wie
"heute 18:03", "aktualisiert am 18.09.2026" oder "ausgeklappt" sind in der gedämpften Farbe des
Themas. Der Text der Zeile bleibt genau gleich, Screenreader und Braillezeile lesen ihn wie bisher.
Farben kommen nur aus der Palette.
"""
from __future__ import annotations

import re
from typing import Callable

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QFont, QFontMetrics, QPalette
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem, QWidget

HEAD, NORMAL, DIM = "head", "normal", "dim"
PART = ", "
DIM_PART = re.compile(r"^(aktualisiert am |heute |gestern |vor \d|\d{1,2}\.\d{1,2}\.|"
                      r"ausgeklappt$|geöffnet$)")


def runs(text: str, head_sep: str = PART, bold_head: bool = True) -> list[tuple[str, str]]:
    """Die Zeile in Stücke mit Stil zerlegen. Zusammengesetzt ergeben sie wieder den Text."""
    result: list[tuple[str, str]] = []
    rest = text
    if bold_head and head_sep in text:
        head, rest = text.split(head_sep, 1)
        result.append((head, HEAD))
        result.append((head_sep, NORMAL))
    elif bold_head and head_sep == PART:
        return [(text, HEAD)]
    parts = rest.split(PART)
    for number, part in enumerate(parts):
        if number:
            result.append((PART, NORMAL))
        result.append((part, DIM if DIM_PART.match(part) else NORMAL))
    return [(t, s) for t, s in result if t]


class RowDelegate(QStyledItemDelegate):
    """head_sep: Trenner nach dem fetten Anfang, ", " oder ": ". bold_head(row): ob die Zeile
    einen fetten Anfang hat."""

    def __init__(self, parent: QWidget, head_sep: str = PART,
                 bold_head: Callable[[int], bool] = lambda row: True) -> None:
        super().__init__(parent)
        self.head_sep = head_sep
        self.bold_head = bold_head

    def paint(self, painter, option: QStyleOptionViewItem, index) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        text, opt.text = opt.text, ""
        widget = opt.widget
        style = widget.style() if widget is not None else None
        if style is None:
            super().paint(painter, option, index)
            return
        pieces = runs(text, self.head_sep, self.bold_head(index.row()))
        box = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, opt, widget)
        box = box.adjusted(2, 0, -2, 0)
        if (opt.features & QStyleOptionViewItem.ViewItemFeature.WrapText
                and self.width_of(opt, pieces) > box.width()):
            super().paint(painter, option, index)   # lange Zeile: wie bisher mit Umbruch
            return
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)
        self.draw_runs(painter, opt, box, pieces)

    @staticmethod
    def width_of(opt: QStyleOptionViewItem, pieces: list[tuple[str, str]]) -> int:
        width = 0
        for text, kind in pieces:
            font = QFont(opt.font)
            font.setBold(kind == HEAD)
            width += QFontMetrics(font).horizontalAdvance(text)
        return width

    @staticmethod
    def draw_runs(painter, opt: QStyleOptionViewItem, box: QRect,
                  pieces: list[tuple[str, str]]) -> None:
        palette = opt.palette
        normal = palette.color(QPalette.ColorRole.Text)
        dim = palette.color(QPalette.ColorRole.PlaceholderText)
        painter.save()
        x = box.left()
        for text, kind in pieces:
            font = QFont(opt.font)
            font.setBold(kind == HEAD)
            painter.setFont(font)
            painter.setPen(dim if kind == DIM else normal)
            metrics = QFontMetrics(font)
            room = box.right() - x
            if room <= 0:
                break
            shown = metrics.elidedText(text, Qt.TextElideMode.ElideRight, room)
            painter.drawText(QRect(x, box.top(), room, box.height()),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, shown)
            if shown != text:
                break
            x += metrics.horizontalAdvance(text)
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index):
        size = super().sizeHint(option, index)
        bold = QFont(option.font)
        bold.setBold(True)
        head = runs(index.data() or "", self.head_sep, self.bold_head(index.row()))
        extra = sum(QFontMetrics(bold).horizontalAdvance(t) - option.fontMetrics.horizontalAdvance(t)
                    for t, kind in head if kind == HEAD)
        size.setWidth(size.width() + extra)
        return size
