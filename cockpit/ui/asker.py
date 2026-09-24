"""Brücke für Rückfragen aus Hintergrund-Abläufen an die Oberfläche.

Ein Schritt im Hintergrund ruft asker.ask(frage) auf. Die Frage wird im Thread der Oberfläche als
Dialog gezeigt, der Hintergrund wartet auf die Antwort. Wird ask() direkt im Thread der Oberfläche
aufgerufen, erscheint der Dialog sofort.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import QInputDialog, QLineEdit, QWidget

from cockpit.core.flows.questions import ChoiceQuestion, ConfirmQuestion, Question, TextQuestion
from cockpit.ui.common import confirm


class QtAsker(QObject):
    _request = Signal(object, object)            # Frage, Behälter für die Antwort

    def __init__(self, parent_widget: QWidget | None = None) -> None:
        super().__init__()
        self.parent_widget = parent_widget
        self._request.connect(self._show, Qt.ConnectionType.BlockingQueuedConnection)

    def ask(self, question: Question) -> Any:
        if QThread.currentThread() is self.thread():
            return self.show_question(question)
        holder: list[Any] = []
        self._request.emit(question, holder)
        return holder[0] if holder else None

    @Slot(object, object)
    def _show(self, question: Question, holder: list) -> None:
        holder.append(self.show_question(question))

    def show_question(self, question: Question) -> Any:
        parent = self.parent_widget
        if isinstance(question, ConfirmQuestion):
            return confirm(parent, question.title, question.text, question.yes, question.no,
                           question.default_yes)
        if isinstance(question, ChoiceQuestion):
            text, ok = QInputDialog.getItem(parent, question.title, question.text,
                                            list(question.options), question.default_index,
                                            False)
            return question.options.index(text) if ok else None
        if isinstance(question, TextQuestion):
            if question.multiline:
                text, ok = QInputDialog.getMultiLineText(parent, question.title, question.label,
                                                         question.default)
            else:
                text, ok = QInputDialog.getText(parent, question.title, question.label,
                                                QLineEdit.EchoMode.Normal, question.default)
            return text if ok else None
        raise TypeError(type(question))
