"""Kleine Hilfen für die Oberfläche (Muster aus Chatbot und Tagebuch)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAccessible, QAccessibleEvent
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QLabel, QMessageBox, QPlainTextEdit,
                               QWidget)

REFOCUS_DELAY_MS = 80


class FocusDialog(QDialog):
    """Dialog, der seinen Startfokus erst nach dem Anzeigen setzt und NVDA meldet.

    Test von Phase 2: Wurde der Fokus schon im Konstruktor gesetzt, zeigte die Braillezeile nach
    dem Öffnen aus einem Menü noch den alten Fokus im Hauptfenster ("Exe starten"), bis man eine
    Pfeiltaste drückte. Deshalb wird der Fokus kurz nach dem Anzeigen noch einmal gesetzt und ein
    Fokus-Ereignis gesendet, bei Listen für den markierten Eintrag."""

    initial_focus_widget: QWidget | None = None

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(REFOCUS_DELAY_MS, self.refocus)

    def refocus(self) -> None:
        widget = self.initial_focus_widget
        if widget is None or not self.isVisible() or not widget.isVisible():
            return
        widget.setFocus()
        announce_focus(widget)


def announce_focus(widget: QWidget) -> None:
    """Fokus-Ereignis für NVDA senden, bei Listen für den markierten Eintrag."""
    event = QAccessibleEvent(widget, QAccessible.Event.Focus)
    if isinstance(widget, QAbstractItemView) and widget.currentIndex().isValid():
        event.setChild(widget.currentIndex().row())
    QAccessible.updateAccessibility(event)


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


def ask_buttons(parent: QWidget | None, title: str, text: str, buttons: list[str],
                default: int, escape: int) -> int:
    """Rückfrage mit mehreren Antworten als Knöpfe. Gibt den Index des gewählten Knopfs zurück.
    default und escape sollten die sichere Antwort sein (CLAUDE.md)."""
    box = QMessageBox(QMessageBox.Icon.Question, title, text, QMessageBox.StandardButton.NoButton,
                      parent)
    added = [box.addButton(label, QMessageBox.ButtonRole.ActionRole) for label in buttons]
    box.setDefaultButton(added[default])
    box.setEscapeButton(added[escape])
    box.exec()
    clicked = box.clickedButton()
    return added.index(clicked) if clicked in added else escape


def pick_folder(parent: QWidget | None, title: str, start: str = "") -> Path | None:
    """Ordner wählen mit dem Dialog von Windows (NVDA kennt ihn). None bei Abbruch."""
    from PySide6.QtWidgets import QFileDialog
    chosen = QFileDialog.getExistingDirectory(parent, title, start)
    return Path(chosen) if chosen else None


class ListChoiceDialog(FocusDialog):
    """Auswahl aus einer Liste mit OK und Abbrechen. Enter wählt, Escape bricht ab."""

    def __init__(self, title: str, name: str, items: list[str], current: int = 0,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from PySide6.QtWidgets import QDialogButtonBox, QListWidget, QVBoxLayout
        self.setWindowTitle(title)
        self.list = QListWidget()
        name_widget(self.list, name)
        self.list.addItems(items)
        self.list.setCurrentRow(max(0, min(current, len(items) - 1)))
        self.list.itemActivated.connect(lambda _item: self.accept())
        buttons = QDialogButtonBox()
        buttons.addButton("OK", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Abbrechen", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addWidget(buttons)
        self.resize(560, 400)
        self.initial_focus_widget = self.list
        self.list.setFocus()

    @property
    def chosen(self) -> int:
        return self.list.currentRow()


def choose_from_list(parent: QWidget | None, title: str, name: str, items: list[str],
                     current: int = 0) -> int | None:
    """Index des gewählten Eintrags oder None bei Abbruch."""
    dialog = ListChoiceDialog(title, name, items, current, parent)
    return dialog.chosen if dialog.exec() else None


def make_copyable(listing) -> None:
    """Textlisten (Wunsch aus dem Test von 8a): Umschalt+Pfeil und Strg+Umschalt+Pfeil wählen
    mehrere Zeilen aus, Strg+A alle. Strg+C kopiert die Auswahl, eine Zeile pro Eintrag."""
    from PySide6.QtGui import QKeySequence, QShortcut
    listing.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    shortcut = QShortcut(QKeySequence.StandardKey.Copy, listing)
    shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
    shortcut.activated.connect(lambda: copy_selected(listing))


def copy_selected(listing) -> int:
    """Ausgewählte Zeilen in die Zwischenablage, sonst die markierte. Gibt die Anzahl zurück."""
    from PySide6.QtGui import QGuiApplication
    from cockpit.ui.announcer import announce
    rows = sorted({index.row() for index in listing.selectedIndexes()})
    if not rows and listing.currentRow() >= 0:
        rows = [listing.currentRow()]
    if not rows:
        return 0
    QGuiApplication.clipboard().setText("\n".join(listing.item(r).text() for r in rows))
    announce("Zeile kopiert." if len(rows) == 1 else f"{len(rows)} Zeilen kopiert.")
    return len(rows)
