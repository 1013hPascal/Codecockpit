"""Vorschlag zum Lesen, Übernehmen, Bearbeiten oder Überspringen (Rückmeldung vom 07.10.2026).

Vorher kam der Vorschlag der KI für die README beim Hochladen in einem mehrzeiligen Eingabefeld.
Darin schrieb Tab ein Tabzeichen, und man kam nicht mehr heraus. Jetzt steht der Text in einem
Ausgabefeld: lesen und kopieren ja, schreiben erst nach „Bearbeiten“. Tab führt zu den Knöpfen,
Umschalt+Tab zurück in den Text. Escape und die Vorgabe sind „Überspringen“, die sichere Antwort.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, PlainEdit, click_focused_button, label_for
from cockpit.ui.repo_dialogs import button_row

READ_ONLY_FLAGS = (Qt.TextInteractionFlag.TextSelectableByKeyboard
                   | Qt.TextInteractionFlag.TextSelectableByMouse)


class ProposalDialog(FocusDialog):
    def __init__(self, title: str, text: str, proposal: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.note = QLabel(text)
        self.note.setWordWrap(True)
        self.edit = PlainEdit()
        self.edit.setPlainText(proposal)
        self.edit.setReadOnly(True)
        self.edit.setTextInteractionFlags(READ_ONLY_FLAGS)
        edit_label = label_for(self.edit, "&Vorschlag:")
        self.take_button = QPushButton("Ü&bernehmen")
        self.take_button.clicked.connect(self.accept)
        self.edit_button = QPushButton("B&earbeiten")
        self.edit_button.clicked.connect(self.start_editing)
        self.skip_button = QPushButton("Über&springen")
        self.skip_button.clicked.connect(self.reject)
        self.skip_button.setDefault(True)               # die sichere Antwort
        layout = QVBoxLayout(self)
        layout.addWidget(self.note)
        layout.addWidget(edit_label)
        layout.addWidget(self.edit)
        layout.addLayout(button_row(None, self.take_button, self.edit_button,
                                    self.skip_button))
        self.resize(640, 460)
        self.initial_focus_widget = self.edit

    @property
    def text(self) -> str:
        return self.edit.toPlainText()

    def start_editing(self) -> None:
        self.edit.setReadOnly(False)
        self.edit.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.edit_button.setEnabled(False)
        self.edit.setFocus()
        announce("Text bearbeitbar.")

    def keyPressEvent(self, event) -> None:
        # Enter auf einem Knopf drückt diesen Knopf, nicht die Vorgabe. Enter im Text tut nichts,
        # wie in den anderen Ausgabefeldern (Überprüfung vom 08.10.2026: sonst übersprang ein
        # versehentliches Enter beim Lesen den Vorschlag).
        if self.focusWidget() is self.edit:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                event.accept()
                return
        elif click_focused_button(self, event):
            return
        super().keyPressEvent(event)


def ask_proposal(parent: QWidget | None, title: str, text: str, proposal: str) -> str | None:
    """Der übernommene, vielleicht bearbeitete Text, None bei Überspringen oder Escape."""
    dialog = ProposalDialog(title, text, proposal, parent)
    return dialog.text if dialog.exec() else None
