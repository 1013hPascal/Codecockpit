"""Schnellnavigation, Befehlssuche und Tastenhinweise (Wunsch des Nutzers vom 07.10.2026).

Schnellnavigation: Im Kontextmenü eines ausgeklappten Projekts steht als erster Eintrag ein
Untermenü „Schnellnavigation Tagebuch“ mit Hilfe, Tastenbefehlen und den Fenstern zum Verwalten von
Projekt, Repository, Branches und Releases. So spart man die Wege durch die Zeilen.

Befehlssuche (Strg+K): ein Suchfeld über allen Aktionen der markierten Zeile und allen Menüs. Man
tippt zum Beispiel „hoch“, Pfeil runter wählt, Enter führt aus.

Tastenhinweise (Strg+F1): Das Cockpit sagt kurz an, welche Tasten beim Element mit dem Fokus
etwas tun. Der Hinweis steht nicht als Beschreibung am Element (Regel in CLAUDE.md: keine
Accessible Description), sondern kommt nur auf Wunsch. Sehende sehen ihn als Tooltip.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QAbstractButton, QCheckBox, QComboBox, QDialogButtonBox,
                               QLineEdit, QListWidget, QMenu, QPlainTextEdit, QTextEdit,
                               QVBoxLayout, QWidget)

from cockpit.core.actions import ActionEntry, Target
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, label_for
from cockpit.ui.menus import AccessibleMenu

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

# (Text im Menü, Zeile, Kennung der Aktion). Ohne Aktion: nur die Zeile markieren.
QUICK_TARGETS = (("&Projekt verwalten …", Target.PROJECT, "manage_project"),
                 ("&Repository verwalten …", Target.REPOSITORY, "manage_repo"),
                 ("&Branches verwalten …", Target.REPOSITORY, "branches"),
                 ("Re&leases verwalten …", Target.RELEASES, ""))


# -- Schnellnavigation -----------------------------------------------------------------------------
def quick_menu(window: "MainWindow", project_id: int) -> AccessibleMenu:
    project = window.services.projects.get(project_id)
    name = project.name if project is not None else ""
    menu = AccessibleMenu(f"&Schnellnavigation {name}".strip(), window)
    menu.addAction("&Hilfe, Kurzanleitungen und KI fragen …").triggered.connect(
        window.open_help)
    menu.addAction("&Tastenbefehle …").triggered.connect(window.show_shortcuts)
    for text, target, action_id in QUICK_TARGETS:
        menu.addAction(text).triggered.connect(
            lambda checked=False, t=target, a=action_id: go_to(window, project_id, t, a))
    return menu


def go_to(window: "MainWindow", project_id: int, target: Target, action_id: str) -> None:
    """Zeile markieren und die Aktion ausführen. Gibt es sie dort nicht, sagt das Cockpit warum
    und lässt die Markierung auf der Zeile, damit man mit Tab weitersuchen kann."""
    if not window.project_list.select(target, project_id):
        announce("Diese Zeile gibt es bei diesem Projekt nicht.")
        return
    window.refresh_actions()
    if not action_id:
        window.focus_actions()
        return
    entry = next((e for e in window.current_entries() if e.action.id == action_id), None)
    if entry is None:
        announce("Das geht bei diesem Projekt nicht, zum Beispiel ohne Repository auf GitHub.")
        window.project_list.setFocus()
        return
    window.run_entry(entry)


# -- Befehlssuche ----------------------------------------------------------------------------------
def menu_commands(window: "MainWindow") -> list[tuple[str, QAction]]:
    """Alle Einträge der Menüs, zum Beispiel „Menü KI: KI-Verwaltung …“."""
    found: list[tuple[str, QAction]] = []

    def walk(menu: QMenu, prefix: str) -> None:
        for action in menu.actions():
            if action.isSeparator() or not action.isVisible():
                continue
            text = action.text().replace("&", "")
            if action.menu() is not None:
                walk(action.menu(), f"{prefix}{text}, ")
            elif action.isEnabled():
                found.append((f"{prefix}{text}", action))

    for top in window.menuBar().actions():
        if top.menu() is not None:
            walk(top.menu(), f"Menü {top.text().replace('&', '')}: ")
    return found


class CommandSearchDialog(FocusDialog):
    """Suchfeld oben, darunter die Treffer. Enter im Suchfeld führt den markierten Treffer aus,
    Pfeil runter und hoch wählen, auch aus dem Suchfeld heraus. Escape schließt."""

    def __init__(self, entries: list[ActionEntry], commands: list[tuple[str, QAction]],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Befehl suchen")
        self.items: list[tuple[str, object]] = [(e.label, e) for e in entries] + commands
        self.chosen: object | None = None
        self.edit = QLineEdit()
        edit_label = label_for(self.edit, "&Suchen:")
        self.list = QListWidget()
        list_label = label_for(self.list, "&Treffer:")
        self.edit.textChanged.connect(self.filter)
        self.edit.returnPressed.connect(self.run)
        self.list.itemActivated.connect(lambda _item: self.run())
        buttons = QDialogButtonBox()
        buttons.addButton("Schließen", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        for widget in (edit_label, self.edit, list_label, self.list, buttons):
            layout.addWidget(widget)
        self.resize(600, 460)
        self.initial_focus_widget = self.edit
        self.shown: list[tuple[str, object]] = []
        self.filter("")

    def filter(self, text: str) -> None:
        words = text.lower().split()
        self.shown = [(label, item) for label, item in self.items
                      if all(w in label.lower() for w in words)]
        self.list.clear()
        self.list.addItems([label for label, _item in self.shown] or ["Keine Treffer."])
        self.list.setCurrentRow(0)

    def keyPressEvent(self, event) -> None:
        from PySide6.QtCore import Qt
        if self.focusWidget() is self.edit and event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            step = 1 if event.key() == Qt.Key.Key_Down else -1
            row = max(0, min(self.list.currentRow() + step, self.list.count() - 1))
            self.list.setCurrentRow(row)
            announce(self.list.currentItem().text() if self.list.currentItem() else "")
            return
        super().keyPressEvent(event)

    def run(self) -> None:
        row = self.list.currentRow()
        if not 0 <= row < len(self.shown):
            announce("Keine Treffer.")
            return
        self.chosen = self.shown[row][1]
        self.accept()


def search_commands(window: "MainWindow") -> None:
    dialog = CommandSearchDialog(window.current_entries(), menu_commands(window), window)
    if not dialog.exec() or dialog.chosen is None:
        return
    if isinstance(dialog.chosen, ActionEntry):
        window.run_entry(dialog.chosen)
    else:
        dialog.chosen.trigger()


# -- Tastenhinweise ------------------------------------------------------------------------------
ROW_HINTS = {
    Target.PROJECT: "Pfeil rechts oder Enter klappt auf, Tab führt zu den Aktionen, Menütaste "
                    "öffnet das Kontextmenü mit der Schnellnavigation",
    Target.COLLECTION: "Pfeil rechts oder Enter öffnet, Pfeil links schließt, Tab führt zu den "
                       "Aktionen",
    Target.LIST_FILTER: "Enter öffnet die Auswahl, Pfeiltasten wählen, Escape lässt alles",
    Target.REPOSITORY: "Enter öffnet die Auswahl der Branches, Tab führt zu den Aktionen, Pfeil "
                       "links klappt zu",
    Target.REMOTE_REPO: "Enter lädt herunter, Tab führt zu den Aktionen",
}
CHILD_HINT = "Enter führt die wichtigste Aktion aus, Tab führt zu den Aktionen, Pfeil links klappt zu"
TOP_HINT = "Enter führt aus, Pfeil runter führt zu den Projekten"


def key_hint(widget: QWidget | None, window: "MainWindow | None" = None) -> str:
    """Kurzer Satz, welche Tasten hier etwas tun."""
    if widget is None:
        return "Kein Element hat den Fokus."
    if window is not None and widget is window.project_list:
        target, _item = window.project_list.current_target()
        if target in ROW_HINTS:
            return ROW_HINTS[target]
        if target in (Target.NEW_COLLECTION, Target.ADD_LOCAL, Target.ADD_REMOTE):
            return TOP_HINT
        return CHILD_HINT
    if window is not None and widget is window.actions_list:
        return ("Enter oder Leertaste führt die Aktion aus, Umschalt+Tab führt zurück zur "
                "Projektliste")
    if isinstance(widget, QCheckBox):
        return "Leertaste hakt an oder ab, Tab führt weiter"
    if isinstance(widget, QAbstractButton):
        return "Enter oder Leertaste drückt den Knopf, Tab führt weiter"
    if isinstance(widget, QComboBox):
        return "Pfeiltasten wählen, Tab führt weiter"
    if isinstance(widget, QListWidget):
        return "Pfeiltasten wählen, Enter führt aus oder öffnet, Tab führt weiter"
    if isinstance(widget, (QPlainTextEdit, QTextEdit)):
        if widget.isReadOnly():
            return "Pfeiltasten lesen, Strg+A und Strg+C kopieren, Tab führt weiter"
        return "Text eingeben, Umschalt+Enter für einen neuen Absatz, Tab führt weiter"
    if isinstance(widget, QLineEdit):
        return "Text eingeben, Enter bestätigt, Tab führt weiter"
    return "Tab führt weiter, Umschalt+Tab zurück, Escape schließt ein Fenster"


def announce_hint(window: "MainWindow | None" = None) -> None:
    from PySide6.QtWidgets import QApplication
    announce(f"Tasten hier: {key_hint(QApplication.focusWidget(), window)}.")
