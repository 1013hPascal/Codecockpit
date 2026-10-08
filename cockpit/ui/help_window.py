"""Hilfefenster mit Kurzanleitungen (Wunsch des Nutzers vom 07.10.2026). F1 oder Menü Hilfe.

Das Fenster ist nicht modal: Es bleibt offen, und mit Alt+Tab arbeiten Sie im Cockpit weiter.
Von oben nach unten:
- „Suchen“: Text eingeben, die Liste darunter zeigt die passenden Anleitungen, die besten oben.
- „KI fragen“: Passt eine Anleitung gut, zeigt das Cockpit sie. Sonst fragt es die KI. Sie
  bekommt die Anleitungen und die Bedienung des Cockpits und schreibt Schritte mit Tasten.
- „Anleitungen“: Ohne Suche stehen die Anleitungen für die markierte Zeile oben. Enter springt in
  die Schritte.
- „Schritte“: Ausgabefeld, lesen und kopieren.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import paths, quick_guides
from cockpit.core.actions import Target
from cockpit.core.quick_guides import Guide
from cockpit.ui.announcer import announce
from cockpit.ui.common import PlainEdit, label_for
from cockpit.ui.repo_dialogs import button_row
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

TITLE = "Hilfe"
AREA_OF = {Target.PROJECT: "projekt", Target.REPOSITORY: "repository", Target.CODE: "branch",
           Target.BRANCH: "branch", Target.REMOTE_BRANCH: "branch", Target.RELEASES: "releases",
           Target.EXE: "releases", Target.RELEASE: "releases"}
AI_WISH = ("Antworte als kurze Schritt-für-Schritt-Anleitung, jede Zeile beginnt mit „Schritt 1:“, "
           "„Schritt 2:“ und so weiter, und nenne die Tasten. Frage: ")


def area_of(window: "MainWindow") -> str:
    target, _item = window.project_list.current_target()
    return AREA_OF.get(target, "start")


class HelpWindow(QWidget):
    def __init__(self, window: "MainWindow", guides: list[Guide] | None = None) -> None:
        super().__init__(window, Qt.WindowType.Window)
        self.main = window
        self.guides = guides if guides is not None else quick_guides.load(
            paths.resource_dir() / "anleitungen")
        self.area = "start"
        self.shown: list[Guide] = []
        self.task: Task | None = None
        self.setWindowTitle(TITLE)
        self.search = QLineEdit()
        search_label = label_for(self.search, "&Suchen:")
        self.search.textChanged.connect(lambda _text: self.fill())
        self.search.returnPressed.connect(self.jump_to_list)
        self.ask_button = QPushButton("KI &fragen")
        self.ask_button.clicked.connect(self.ask)
        self.list = QListWidget()
        list_label = label_for(self.list, "&Anleitungen:")
        self.list.currentRowChanged.connect(lambda _row: self.show_steps())
        self.list.itemActivated.connect(lambda _item: self.steps.setFocus())
        self.steps = PlainEdit()
        self.steps.setReadOnly(True)
        steps_label = label_for(self.steps, "S&chritte:")
        close = QPushButton("Schließen")
        close.clicked.connect(self.close)
        layout = QVBoxLayout(self)
        layout.addWidget(search_label)
        layout.addWidget(self.search)
        layout.addLayout(button_row(self.ask_button, None))
        layout.addWidget(list_label)
        layout.addWidget(self.list, 1)
        layout.addWidget(steps_label)
        layout.addWidget(self.steps, 1)
        layout.addLayout(button_row(None, close))
        self.resize(720, 640)

    # -- Öffnen ------------------------------------------------------------------------------
    def open_for(self, area: str) -> None:
        """Zeigen und nach vorne holen. Ohne Suche stehen die Anleitungen für area oben."""
        self.area = area
        self.fill()
        self.show()
        self.raise_()
        self.activateWindow()
        self.search.setFocus()
        self.search.selectAll()

    def fill(self) -> None:
        self.shown = quick_guides.search(self.guides, self.search.text(), self.area)
        self.list.blockSignals(True)
        self.list.clear()
        self.list.addItems([g.title for g in self.shown] or ["Keine passende Anleitung. Fragen "
                                                              "Sie die KI."])
        self.list.setCurrentRow(0)
        self.list.blockSignals(False)
        self.show_steps()

    def current(self) -> Guide | None:
        row = self.list.currentRow()
        return self.shown[row] if 0 <= row < len(self.shown) else None

    def show_steps(self) -> None:
        guide = self.current()
        self.steps.setPlainText(guide.text if guide is not None else "")

    def jump_to_list(self) -> None:
        if self.shown:
            self.list.setFocus()
        else:
            announce("Keine passende Anleitung.")

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    # -- KI fragen ---------------------------------------------------------------------------
    def ask(self) -> None:
        question = self.search.text().strip()
        if not question:
            announce("Bitte schreiben Sie zuerst ins Feld Suchen, was Sie wissen möchten.")
            self.search.setFocus()
            return
        guide = quick_guides.good_match(self.guides, question)
        if guide is not None:
            self.fill()
            self.list.setCurrentRow(self.shown.index(guide))
            self.steps.setFocus()
            announce(f"Passende Anleitung: {guide.title}.")
            return
        self.ask_ai(question)

    def ask_ai(self, question: str) -> None:
        from cockpit.features.ai_help import knowledge
        from cockpit.features.ai_help.manifest import FEATURE_ID
        from cockpit.ui import ai_ui
        from cockpit.ui.ai_help_dialog import all_sections
        from cockpit.ui.error_dialog import show_error
        if self.task is not None:
            announce("Die KI antwortet noch.")
            return
        services = self.main.services
        tool_id = None
        if FEATURE_ID in services.registry:
            tool_id = services.features.setting(FEATURE_ID, "tool") or None
        ai = ai_ui.prepare(services, self, FEATURE_ID,
                           "Ihre Frage und Auszüge aus der Hilfe des Cockpits", tool_id)
        if isinstance(ai, str):
            show_error(self, TITLE, ai)
            return
        sections = all_sections(self.main)
        task = Task(lambda t: knowledge.ask(ai, AI_WISH + question, sections, t.cancel_event),
                    self)
        self.task = task
        task.result.connect(self.show_answer)
        task.error.connect(lambda message, details: show_error(self, TITLE, message, details))
        task.finished.connect(self._finished)
        self.steps.setPlainText("Die KI schreibt eine Anleitung …")
        announce("Die KI schreibt eine Anleitung.")
        task.start()

    def show_answer(self, text: str) -> None:
        from cockpit.core.text import one_sentence_per_line
        lines = [line.strip() for line in one_sentence_per_line(text).splitlines()
                 if line.strip()]
        self.steps.setPlainText("\n".join(lines) or "Die KI hat nichts geantwortet.")
        self.steps.setFocus()
        announce("Anleitung der KI da.")

    def _finished(self) -> None:
        task, self.task = self.task, None
        if task is not None:
            task.wait()
            task.deleteLater()

    def closeEvent(self, event) -> None:
        if self.task is not None:
            self.task.cancel()
            self.task.wait(10000)
        super().closeEvent(event)
