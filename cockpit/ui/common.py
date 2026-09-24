"""Kleine Hilfen für die Oberfläche (Muster aus Chatbot und Tagebuch)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QPlainTextEdit, QWidget


def name_widget(widget: QWidget, name: str) -> None:
    """Namen für Screenreader setzen. Bewusst keine Beschreibung: Die Braillezeile zeigt sonst
    Name, Rolle und Beschreibung, und Tastenkürzel gehören nur ins Menü."""
    widget.setAccessibleName(name)


def label_for(widget: QWidget, text: str) -> QLabel:
    """Sichtbares Label mit Buddy. Der Accessible Name ist der Text ohne Doppelpunkt und &."""
    label = QLabel(text)
    label.setBuddy(widget)
    name_widget(widget, text.replace("&", "").rstrip(":").strip())
    return label


class PlainEdit(QPlainTextEdit):
    """Mehrzeiliges Textfeld für Screenreader und Braillezeile.

    - Tab wechselt den Fokus, statt ein Tabzeichen einzufügen (wie im Tagebuch).
    - Umschalt+Enter fügt einen echten Absatz ein. Qt fügt sonst den Zeilentrenner U+2028 ein, und
      die Braillezeile zeigt keine neue Zeile (wie im Chatbot). Eingefügter Text wird ebenso
      bereinigt."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTabChangesFocus(True)

    def keyPressEvent(self, event) -> None:
        if (event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.insertPlainText("\n")
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source) -> None:
        if source.hasText():
            self.insertPlainText(source.text().replace(" ", "\n").replace(" ", "\n"))
        else:
            super().insertFromMimeData(source)


def confirm(parent: QWidget | None, title: str, text: str, yes: str = "Ja", no: str = "Nein",
            default_yes: bool = False) -> bool:
    """Rückfrage mit deutschen Schaltflächen. Vorgabe ist die sichere Antwort, Escape auch."""
    box = QMessageBox(QMessageBox.Icon.Question, title, text, QMessageBox.StandardButton.NoButton,
                      parent)
    yes_button = box.addButton(yes, QMessageBox.ButtonRole.YesRole)
    no_button = box.addButton(no, QMessageBox.ButtonRole.NoRole)
    box.setDefaultButton(yes_button if default_yes else no_button)
    box.setEscapeButton(no_button)
    box.exec()
    return box.clickedButton() is yes_button


def show_info(parent: QWidget | None, title: str, text: str) -> None:
    box = QMessageBox(QMessageBox.Icon.Information, title, text,
                      QMessageBox.StandardButton.NoButton, parent)
    box.setEscapeButton(box.addButton("OK", QMessageBox.ButtonRole.AcceptRole))
    box.exec()
