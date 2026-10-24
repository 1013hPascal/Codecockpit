"""Bereich "Stand" unter den Aktionen, nur für das Auge (PLAN-OPTIK.md, Schritt 2, 22.10.2026).

Er zeigt die Angaben der markierten Zeile der Projektliste untereinander, zum Beispiel
"Tagebuch", darunter "aktualisiert am 18.09.2026" und "3 Dateien noch nicht hochgeladen". Er ist
kein Tab-Stopp und sagt nichts an: Für Screenreader und Braillezeile steht alles schon in der
Zeile selbst (Entscheidung, weil der Nutzer "was du besser findest" sagte). Deshalb darf hier nie
etwas stehen, das nicht auch in der Zeile steht.
"""
from __future__ import annotations

import html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel

from cockpit.ui.project_labels import EXPANDED_SUFFIX, OPENED_SUFFIX
from cockpit.ui.row_delegate import PART


def state_lines(text: str) -> tuple[str, list[str]]:
    """Überschrift und Zeilen aus dem Text einer Zeile. "ausgeklappt" und "geöffnet" fallen weg,
    sie zeigt die Liste selbst."""
    for suffix in (EXPANDED_SUFFIX, OPENED_SUFFIX):
        if text.endswith(suffix):
            text = text[:-len(suffix)]
    head, *rest = text.split(PART)
    return head, rest


class StatePanel(QLabel):
    def __init__(self, project_list) -> None:
        super().__init__()
        self.project_list = project_list
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMargin(8)
        self.setMinimumHeight(120)
        # Fester Name: Ändert sich der Text, soll kein Screenreader eine Namensänderung melden
        self.setAccessibleName("Stand")
        project_list.currentRowChanged.connect(lambda _row: self.update_text())
        project_list.model().dataChanged.connect(lambda *_args: self.update_text())
        self.update_text()

    def update_text(self) -> None:
        item = self.project_list.currentItem()
        head, lines = state_lines(item.text()) if item is not None else ("", [])
        # Der Bereich bleibt stehen, auch leer. So springen die Aktionen darüber nicht.
        if not lines:
            self.clear()
            self.setFrameShape(QFrame.Shape.NoFrame)
            return
        body = "<br>".join(html.escape(line) for line in lines)
        self.setText(f"<b>{html.escape(head)}</b><br>{body}")
        self.setFrameShape(QFrame.Shape.StyledPanel)
