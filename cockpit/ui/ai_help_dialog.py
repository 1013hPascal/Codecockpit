"""KI-Hilfe (Konzept 10.17, Teilschritt 8e): Hilfe, KI-Hilfe oder Umschalt+F1.

Feld "Frage", Enter fragt. Die Antwort steht in der Liste "Antwort", ein Satz pro Zeile, Strg+C
kopiert. Der Fokus bleibt beim Warten im Feld, NVDA sagt "Antwort da.".

Die Beschreibung der Bedienung entsteht hier beim Fragen aus dem laufenden Programm: Menüs mit
Tastenkürzeln, die Liste unter F1 und alle Aktionen nach Art der Zeile. Dazu kommen Anleitungen und
Einführungen (features/ai_help/knowledge.py).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import core_actions, paths
from cockpit.core.actions import Target
from cockpit.core.text import one_sentence_per_line
from cockpit.features.ai_help import knowledge
from cockpit.features.ai_help.manifest import FEATURE_ID
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, click_focused_button, label_for, make_copyable
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

TITLE = "KI-Hilfe"
TARGET_NAMES = {
    Target.NEW_COLLECTION: "auf dem obersten Eintrag „Neue Projektsammlung“",
    Target.COLLECTION: "auf einer Projektsammlung",
    Target.ADD_LOCAL: "auf dem obersten Eintrag „Projekt vom Rechner hinzufügen“",
    Target.ADD_REMOTE: "auf dem zweiten Eintrag „Projekt von GitHub herunterladen“",
    Target.PROJECT: "auf einer Projektzeile",
    Target.CODE: "auf Code bzw. Main-Branch und auf einer Branch-Zeile",
    Target.BRANCH_OVERVIEW: "auf „Branches verwalten“",
    Target.EXE: "auf Exe",
    Target.REMOTE_REPO: "auf einem Repository, das nur auf GitHub liegt",
    Target.REMOTE_BRANCHES: "auf „Branches auf GitHub“",
    Target.REMOTE_BRANCH: "auf einem ausgewählten Branch anderer",
}
LAYOUT = ("Das Hauptfenster hat links die Projektliste und rechts die Aktionen. Tab wechselt "
          "zwischen beiden. Projekte lassen sich in Projektsammlungen ordnen, zum Beispiel "
          "„Sammlung Webseiten“. Enter oder Pfeil rechts öffnet eine Sammlung, dann stehen nur "
          "ihre Projekte in der Liste. Rücktaste oder Pfeil links auf der Sammlung schließt sie. "
          "Ein Projekt ist in höchstens einer Sammlung. In der Projektliste klappt Pfeil rechts, Leertaste oder Enter ein "
          "Projekt aus. Darunter stehen Code, bei Branch-Ordnern „Code, main“, die Zeilen der "
          "Branches und Exe. Enter führt die wichtigste Aktion der Zeile aus. Tab führt zu allen "
          "Aktionen der Zeile, die Menütaste öffnet sie als Kontextmenü.")


def _clean(text: str) -> str:
    return text.replace("&&", "\0").replace("&", "").replace("\0", "&")


def ui_sections(window: "MainWindow") -> list[knowledge.Section]:
    """Bedienung aus dem laufenden Programm."""
    from cockpit.ui.main_window import SHORTCUTS
    sections = [knowledge.Section("Aufbau", LAYOUT, always=True),
                knowledge.Section("Tastenkürzel (F1)", "\n".join(SHORTCUTS), always=True)]
    menus = []
    for top in window.menuBar().actions():
        menu = top.menu()
        if menu is None:
            continue
        entries = []
        for action in menu.actions():
            if action.isSeparator() or not action.text():
                continue
            entry = _clean(action.text())
            shortcut = action.shortcut().toString()
            entries.append(f"{entry} ({shortcut})" if shortcut else entry)
        menus.append(f"Menü {_clean(top.text())}: {', '.join(entries)}")
    sections.append(knowledge.Section("Menüs", "\n".join(menus), always=True))
    actions = list(core_actions.CORE_ACTIONS) + window.controller.actions()
    for manifest in window.services.registry.all():
        actions += list(manifest.actions)
    by_target: dict[Target, list[str]] = {}
    for action in actions:
        names = by_target.setdefault(action.target, [])
        if action.text not in names:
            names.append(action.text)
    for target, names in by_target.items():
        where = TARGET_NAMES.get(target, target.value)
        sections.append(knowledge.Section(f"Aktionen {where}", ", ".join(names)))
    return sections


def all_sections(window: "MainWindow") -> list[knowledge.Section]:
    services = window.services
    return (ui_sections(window) + knowledge.guide_sections(paths.resource_dir() / "anleitungen")
            + knowledge.intro_sections(services.registry.all()))


class AIHelpDialog(FocusDialog):
    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self.window_ = window
        self.services = window.services
        self.task: Task | None = None
        self.setWindowTitle(TITLE)
        self.question = QLineEdit()
        question_label = label_for(self.question, "&Frage:")
        self.question.installEventFilter(self)
        self.ask_button = QPushButton("F&ragen")
        self.ask_button.clicked.connect(self.ask)
        self.answer = QListWidget()
        answer_label = label_for(self.answer, "&Antwort:")
        self.answer.setWordWrap(True)
        make_copyable(self.answer)
        close = QPushButton("&Schließen")
        close.clicked.connect(self.reject)
        for button in (self.ask_button, close):
            button.setAutoDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(question_label)
        layout.addWidget(self.question)
        layout.addLayout(button_row(self.ask_button, None))
        layout.addWidget(answer_label)
        layout.addWidget(self.answer, 1)
        layout.addLayout(button_row(None, close))
        self.resize(720, 480)
        self.initial_focus_widget = self.question

    def eventFilter(self, watched, event) -> bool:
        if watched is self.question and _is_enter(event):
            self.ask()
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)

    def ask(self) -> None:
        from cockpit.ui import ai_ui
        question = self.question.text().strip()
        if not question:
            announce("Bitte schreiben Sie zuerst eine Frage.")
            return
        if self.task is not None:
            announce("Die KI antwortet noch.")
            return
        tool_id = self.services.features.setting(FEATURE_ID, "tool") or None
        ai = ai_ui.prepare(self.services, self, FEATURE_ID,
                           "Ihre Frage und Auszüge aus der Hilfe des Cockpits", tool_id)
        if isinstance(ai, str):
            show_error(self, TITLE, ai)
            return
        sections = all_sections(self.window_)
        task = Task(lambda t: knowledge.ask(ai, question, sections, t.cancel_event), self)
        self.task = task
        task.result.connect(self.show_answer)
        task.error.connect(lambda message, details: show_error(self, TITLE, message, details))
        task.finished.connect(self._finished)
        self.answer.clear()
        self.answer.addItem("Die KI antwortet …")
        announce("Die KI antwortet.")
        task.start()

    def show_answer(self, text: str) -> None:
        self.answer.clear()
        lines = [line for line in one_sentence_per_line(text).splitlines() if line.strip()]
        self.answer.addItems(lines or ["Die KI hat nichts geantwortet."])
        self.answer.setCurrentRow(0)
        announce("Antwort da.")

    def _finished(self) -> None:
        task, self.task = self.task, None
        if task is not None:
            task.wait()
            task.deleteLater()

    def done(self, code: int) -> None:
        if self.task is not None:
            self.task.cancel()
            self.task.wait(10000)
        super().done(code)


def open_help(window: "MainWindow") -> None:
    """Menü Hilfe, KI-Hilfe. Ohne das Feature sagt das Cockpit, warum es nicht geht."""
    services = window.services
    if FEATURE_ID not in services.registry:
        announce("Die KI-Hilfe gibt es in dieser Fassung nicht.")
        return
    state = services.features.availability(FEATURE_ID)
    if not state.available:
        show_error(window, TITLE, state.reason)
        return
    AIHelpDialog(window).exec()
