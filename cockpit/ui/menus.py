"""Barrierefreie Menüs (zusammengeführt aus Chatbot und Tagebuch).

Ohne eigenen Namen nennt NVDA beim Öffnen eines Menüs nur den Programmnamen, und die Meldung des
ersten Eintrags geht unter. AccessibleMenu setzt deshalb einen Namen, markiert beim Öffnen den
ersten Eintrag (wie Pfeil runter, ohne ein Untermenü zu öffnen) und meldet ihn nach 200 ms noch
einmal mit genauer Angabe des Eintrags.
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QAccessible, QAccessibleEvent, QKeyEvent
from PySide6.QtWidgets import QApplication, QMenu

FOCUS_REPEAT_MS = 200

# Wird vor jedem Öffnen eines Menüs aufgerufen, zum Beispiel für den Eintrag "Erklärung …" ganz
# oben (Feature Erklärungen, 25.10.2026). Ein Fehler darin stört das Menü nicht.
SHOW_HOOKS: list = []


class AccessibleMenu(QMenu):
    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(title, parent)
        self.setAccessibleName(title.replace("&", ""))
        self.aboutToShow.connect(self._run_hooks)

    def _run_hooks(self) -> None:
        for hook in list(SHOW_HOOKS):
            try:
                hook(self)
            except Exception:                      # noqa: BLE001 (nur Zusatz)
                import logging
                logging.getLogger(__name__).exception("Zusatz für das Menü fehlgeschlagen")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self.select_first)
        QTimer.singleShot(FOCUS_REPEAT_MS, self.repeat_focus_event)

    def select_first(self) -> None:
        if self.isVisible() and self.activeAction() is None:
            QApplication.sendEvent(self, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down,
                                                   Qt.KeyboardModifier.NoModifier))

    def repeat_focus_event(self) -> None:
        action = self.activeAction()
        if action is None or not self.isVisible():
            return
        event = QAccessibleEvent(self, QAccessible.Event.Focus)
        event.setChild(self.actions().index(action))
        QAccessible.updateAccessibility(event)
