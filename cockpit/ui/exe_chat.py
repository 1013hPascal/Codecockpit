"""Fragen an die KI nach einem Schritt beim Einrichten der Exe (Wunsch des Nutzers, 02.10.2026).

Unter dem Vorschlag der KI und unter dem Ergebnis der Einrichtung steht das Feld "Frage an die KI".
Enter oder "Frage senden" schickt die Frage. Die Antwort kommt in die Liste "Gespräch mit der KI",
ein Satz pro Zeile. So kann man nachfragen und diskutieren. Die KI ändert dabei nichts.
Danach wählt man im Fenster "Weiter" (zum Beispiel "Übernehmen" oder "Exe erstellen") oder "Mit den
Hinweisen wiederholen". Dann läuft der letzte Schritt noch einmal, mit dem Gespräch als Hinweis.

Wunsch des Nutzers vom 03.10.2026: Die KI antwortet zuerst in verständlichen Sätzen und zeigt erst
danach Code. Sätze stehen einzeln in der Liste, Code Zeile für Zeile nach der Zeile "Code:".
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

import re

from cockpit.core.text import one_sentence_per_line
from cockpit.features.exe_build import ai_fix
from cockpit.ui.announcer import announce
from cockpit.ui.common import label_for, make_copyable
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row
from cockpit.ui.tasks import Task

REPEAT_TEXT = "Mit den Hinweisen &wiederholen"
NO_HINTS = ("Stellen Sie zuerst eine Frage an die KI. Das Gespräch ist dann der Hinweis für die "
            "Wiederholung.")


_FENCE = re.compile(r"```[^\n]*\n(.*?)(?:```|$)", re.DOTALL)


def answer_lines(answer: str) -> list[str]:
    """Sätze einzeln, Code-Blöcke Zeile für Zeile, eingeleitet von "Code:"."""
    lines: list[str] = []
    position = 0
    text = answer.replace("\r\n", "\n")
    for match in _FENCE.finditer(text):
        lines += [l for l in one_sentence_per_line(text[position:match.start()]).splitlines()
                  if l.strip()]
        code = [l.rstrip() for l in match.group(1).splitlines() if l.strip()]
        if code:
            lines += ["Code:"] + code
        position = match.end()
    lines += [l for l in one_sentence_per_line(text[position:]).splitlines() if l.strip()]
    return lines


class ExeChat(QWidget):
    def __init__(self, services, project_name: str, step: str,
                 content: Callable[[], list[str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.project_name = project_name
        self.step = step
        self.content = content
        self.history: list[tuple[str, str]] = []
        self.task: Task | None = None
        self.ai = None
        self.question = QLineEdit()
        question_label = label_for(self.question, "&Frage an die KI:")
        self.question.installEventFilter(self)
        self.send_button = QPushButton("Frage &senden")
        self.send_button.setAutoDefault(False)
        self.send_button.clicked.connect(self.ask)
        self.answers = QListWidget()
        answers_label = label_for(self.answers, "Gespräch mit der &KI:")
        self.answers.setWordWrap(True)
        make_copyable(self.answers)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(question_label)
        layout.addLayout(button_row(self.question, self.send_button))
        layout.addWidget(answers_label)
        layout.addWidget(self.answers, 1)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.question and _is_enter(event):
            self.ask()
            return True
        return super().eventFilter(watched, event)

    def hints(self) -> str:
        return ai_fix.chat_hints(self.history)

    def _prepare_ai(self):
        from cockpit.ui import ai_ui
        if self.ai is None:
            ai = ai_ui.prepare(self.services, self.window(), "exe_fix",
                               "Ihre Frage und was das Fenster zeigt")
            if isinstance(ai, str):
                if ai != ai_ui.DECLINED:
                    show_error(self.window(), "Frage an die KI", ai)
                return None
            self.ai = ai
        return self.ai

    def ask(self) -> None:
        question = self.question.text().strip()
        if not question:
            announce("Bitte schreiben Sie zuerst eine Frage.")
            return
        if self.task is not None:
            announce("Die KI antwortet noch.")
            return
        ai = self._prepare_ai()
        if ai is None:
            return
        name, step, content, history = self.project_name, self.step, self.content(), \
            list(self.history)
        task = Task(lambda t: ai_fix.ask_chat(ai, name, step, content, history, question,
                                              t.cancel_event), self)
        self.task = task
        task.result.connect(lambda answer: self.show_answer(question, answer))
        task.error.connect(lambda message, details: show_error(self.window(), "Frage an die KI",
                                                               message, details))
        task.finished.connect(self._finished)
        self.answers.addItem(f"Sie: {question}")
        self.answers.addItem("Die KI antwortet …")
        announce("Die KI antwortet.")
        task.start()

    def show_answer(self, question: str, answer: str) -> None:
        self.history.append((question, answer.strip()))
        waiting = self.answers.count() - 1
        if waiting >= 0 and self.answers.item(waiting).text() == "Die KI antwortet …":
            self.answers.takeItem(waiting)
        lines = answer_lines(answer)
        first = self.answers.count()
        for number, line in enumerate(lines or ["Die KI hat nichts geantwortet."]):
            self.answers.addItem(f"KI: {line}" if number == 0 else line)
        self.answers.setCurrentRow(first)
        self.question.clear()
        announce("Antwort da.")

    def _finished(self) -> None:
        last = self.answers.count() - 1
        if last >= 0 and self.answers.item(last).text() == "Die KI antwortet …":
            self.answers.takeItem(last)               # bei einem Fehler kam keine Antwort
        task, self.task = self.task, None
        if task is not None:
            task.wait()
            task.deleteLater()

    def stop(self) -> None:
        """Beim Schließen des Fensters: eine laufende Frage abbrechen."""
        if self.task is not None:
            self.task.cancel()
            self.task.wait(10000)
