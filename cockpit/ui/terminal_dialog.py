"""Fenster "Terminal" (Konzept 9.9, Teilschritt 8a).

Aufbau nach dem Wunsch des Nutzers: Der Fokus beginnt im Feld "Befehl". Umschalt+Tab führt in die
Ausgabe, eine Liste mit einer Zeile pro Zeile der Ausgabe. Jede Ausgabe beginnt mit "Anfrage um
16:42:10: Befehl". Enter führt den Befehl aus. Pfeil hoch und runter im Befehlsfeld holen frühere
Befehle zurück, wie in PowerShell. In der Ausgabe wählen Umschalt+Pfeil und Strg+A mehrere Zeilen
aus, Strg+C kopiert sie.

Escape bricht einen laufenden Befehl ab, sonst schließt es das Fenster. Die Ausgabe erscheint im
Hintergrund, der Fokus bleibt im Befehlsfeld. Am Ende sagt NVDA "Fertig." oder den Rückgabewert.

Ist das Feature Terminal-Erklärung aktiv (Teilschritt 8b), kommt mit Tab nach dem Befehlsfeld die
Liste "Erklärung der KI", ein Satz pro Zeile. Schlägt ein Befehl fehl, schreibt die KI im
Hintergrund hinein. NVDA sagt "Erklärung der KI bereit.", der Fokus bleibt, wo er ist.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEvent, QItemSelectionModel, Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import terminal
from cockpit.core.errors import CockpitError
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, copy_selected, label_for, make_copyable, name_widget
from cockpit.ui.repo_dialogs import button_row
from cockpit.ui.tasks import Task

MAX_LINES = 5000                  # ältere Zeilen fallen weg, damit die Liste schnell bleibt
NO_EXPLANATION_YET = "Noch keine Erklärung. Sie erscheint, wenn ein Befehl fehlschlägt."
EXPLAINING = "Die KI erklärt den Fehler …"
READY = "Erklärung der KI bereit."

# Bekommt das Terminal-Fenster, gibt eine TextAI oder den Grund zurück (ui/ai_ui.prepare)
Explainer = Callable[[QWidget], object]


class TerminalDialog(FocusDialog):
    def __init__(self, folder: Path, title: str, env: dict[str, str] | None = None,
                 parent: QWidget | None = None, explainer: Explainer | None = None,
                 command: str = "") -> None:
        """explainer: nur bei aktivem Feature Terminal-Erklärung. command: steht schon im
        Befehlsfeld und läuft erst mit Enter (zum Beispiel ollama pull)."""
        super().__init__(parent)
        self.folder = folder
        self.env = env or {}
        self.history: list[str] = []
        self.history_index = 0
        self.task: Task | None = None
        self.explainer = explainer
        self.explain_task: Task | None = None
        self.last_command = ""
        self.setWindowTitle(f"Terminal: {title}")
        self.output = QListWidget()
        name_widget(self.output, "Ausgabe")
        self.output.setWordWrap(True)
        make_copyable(self.output)
        self.edit = QLineEdit()
        edit_label = label_for(self.edit, "&Befehl:")
        self.edit.returnPressed.connect(self.run_command)
        self.edit.installEventFilter(self)
        self.stop_button = QPushButton("&Abbrechen")
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setVisible(False)
        close = QPushButton("Schließen")
        close.clicked.connect(self.close_terminal)
        # Test von 8a: Enter im Befehlsfeld drückte zusätzlich den gerade sichtbar gewordenen Knopf
        # "Abbrechen" (Standardknopf des Dialogs). Deshalb gibt es hier keinen Standardknopf.
        for button in (self.stop_button, close):
            button.setAutoDefault(False)
            button.setDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(label_for(self.output, "Ausgabe:"))
        layout.addWidget(self.output, 1)
        layout.addWidget(edit_label)
        layout.addWidget(self.edit)
        self.explanation: QListWidget | None = None
        order: list[QWidget] = [self.output, self.edit]
        if explainer is not None:
            self.explanation = QListWidget()
            self.explanation.setWordWrap(True)
            make_copyable(self.explanation)
            layout.addWidget(label_for(self.explanation, "Erklärung der &KI:"))
            layout.addWidget(self.explanation)
            self.set_explanation([NO_EXPLANATION_YET])
            order.append(self.explanation)
        layout.addLayout(button_row(self.stop_button, None, close))
        order += [self.stop_button, close]
        for first, second in zip(order, order[1:]):
            self.setTabOrder(first, second)
        self.resize(820, 600)
        self.add_line(f"Ordner: {folder}")
        if command:
            self.edit.setText(command)
        self.initial_focus_widget = self.edit

    # -- Bedienung ---------------------------------------------------------------------------
    def eventFilter(self, watched, event) -> bool:
        if watched is self.edit and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                self.recall(-1)
                return True
            if event.key() == Qt.Key.Key_Down:
                self.recall(1)
                return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        """Enter drückt nie einen Knopf von selbst, außer er hat den Fokus."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            focus = self.focusWidget()
            if isinstance(focus, QPushButton):
                focus.click()
            return
        super().keyPressEvent(event)

    def recall(self, step: int) -> None:
        """Frühere Befehle wie in PowerShell."""
        if not self.history:
            return
        self.history_index = max(0, min(len(self.history), self.history_index + step))
        text = self.history[self.history_index] if self.history_index < len(self.history) else ""
        self.edit.setText(text)

    def reject(self) -> None:
        """Escape: erst einen laufenden Befehl abbrechen, sonst schließen."""
        if self.running:
            self.stop()
            return
        self.stop_explanation(wait=True)
        super().reject()

    def close_terminal(self) -> None:
        if self.running:
            self.stop()
            if self.task is not None:
                self.task.wait(5000)
        self.stop_explanation(wait=True)
        super().reject()

    @property
    def running(self) -> bool:
        return self.task is not None

    def add_line(self, text: str) -> None:
        self.output.addItem(text)
        while self.output.count() > MAX_LINES:
            self.output.takeItem(0)
        self.output.scrollToBottom()
        if not self.output.hasFocus():
            # Nur die neue Zeile markieren, sonst wächst die Auswahl zum Kopieren mit
            self.output.setCurrentRow(self.output.count() - 1,
                                      QItemSelectionModel.SelectionFlag.ClearAndSelect)

    def copy_line(self) -> None:
        copy_selected(self.output)

    # -- Ausführen ---------------------------------------------------------------------------
    def run_command(self) -> None:
        command = self.edit.text().strip()
        if not command:
            return
        if self.running:
            announce("Es läuft noch ein Befehl. Escape bricht ihn ab.")
            return
        if not self.history or self.history[-1] != command:
            self.history.append(command)
        self.history_index = len(self.history)
        self.edit.clear()
        self.last_command = command
        self.stop_explanation()
        if self.explanation is not None:              # die Erklärung gehört zum letzten Befehl
            self.set_explanation([NO_EXPLANATION_YET])
        # Wunsch aus dem Test von 8a: Jede Ausgabe beginnt mit Uhrzeit und Befehl
        self.add_line(f"Anfrage um {datetime.now():%H:%M:%S}: {command}")
        if terminal.is_force_push(command):
            self.add_line(terminal.FORCE_PUSH)
            announce("Gesperrt. " + terminal.FORCE_PUSH)
            return
        folder, env = self.folder, self.env

        def work(task: Task):
            return terminal.run(command, folder, task.status.emit, env, task.cancel_event)

        task = Task(work, self)
        task.status.connect(self.add_line)
        task.result.connect(self.command_finished)
        task.error.connect(self.command_failed)
        task.cancelled.connect(self.command_cancelled)
        task.finished.connect(self._task_done)
        self.task = task
        self.stop_button.setVisible(True)
        announce("Läuft.")
        task.start()

    def _task_done(self) -> None:
        task, self.task = self.task, None
        self.stop_button.setVisible(False)
        if task is not None:
            task.deleteLater()
        if not self.edit.hasFocus() and self.isVisible() and not self.output.hasFocus():
            self.edit.setFocus()

    def command_finished(self, result: terminal.Result) -> None:
        text = "Fertig." if result.ok else f"Fehler, Rückgabewert {result.code}."
        self.add_line(text)
        lines = len(result.lines)
        announce(f"{text} {lines} Zeilen Ausgabe." if lines != 1 else f"{text} 1 Zeile Ausgabe.")
        if not result.ok:
            self.explain(self.last_command, result)

    def command_failed(self, message: str, details: str) -> None:
        self.add_line(message)
        announce(message, urgent=True)

    def command_cancelled(self) -> None:
        self.add_line("Abgebrochen.")
        announce("Abgebrochen.")

    def stop(self) -> None:
        if self.task is not None:
            self.task.cancel()
            announce("Wird abgebrochen.")

    # -- Erklärung der KI (Feature Terminal-Erklärung) ---------------------------------------
    def set_explanation(self, lines: list[str]) -> None:
        if self.explanation is None:
            return
        from cockpit.core.text import one_sentence_per_line
        self.explanation.clear()
        for line in lines:
            self.explanation.addItems([s for s in one_sentence_per_line(line).splitlines()
                                       if s.strip()])
        if not self.explanation.hasFocus():
            self.explanation.setCurrentRow(0)

    def explanation_lines(self) -> list[str]:
        if self.explanation is None:
            return []
        return [self.explanation.item(i).text() for i in range(self.explanation.count())]

    def explain(self, command: str, result: terminal.Result) -> None:
        """Im Hintergrund die KI fragen. Der Fokus bleibt, wo er ist."""
        if self.explainer is None:
            return
        ai = self.explainer(self)
        if isinstance(ai, str):
            self.set_explanation([f"Keine Erklärung. {ai}"])
            return
        from cockpit.features.terminal_explain.explain import explain
        code, lines = result.code, list(result.lines)

        def work(task: Task) -> str:
            return explain(ai, command, code, lines, task.cancel_event)

        task = Task(work, self)
        task.result.connect(self.explanation_ready)
        task.error.connect(self.explanation_failed)
        task.finished.connect(self._explain_done)
        self.explain_task = task
        self.set_explanation([EXPLAINING])
        task.start()

    def explanation_ready(self, text: str) -> None:
        self.set_explanation([text or "Die KI hat keine Erklärung geliefert."])
        announce(READY)

    def explanation_failed(self, message: str, details: str) -> None:
        self.set_explanation([f"Keine Erklärung. {message}"])
        announce(f"Keine Erklärung der KI. {message}")

    def _explain_done(self) -> None:
        task, self.explain_task = self.explain_task, None
        if task is not None:
            task.deleteLater()

    def stop_explanation(self, wait: bool = False) -> None:
        task = self.explain_task
        if task is None:
            return
        task.cancel()
        try:
            task.result.disconnect(self.explanation_ready)
            task.error.disconnect(self.explanation_failed)
        except (RuntimeError, TypeError):
            pass
        if wait:
            task.wait(5000)


def explainer_for(services, project) -> Explainer | None:
    """Nur bei aktivem Feature Terminal-Erklärung: eingeschaltet und eine Text-KI eingerichtet.
    Ohne Projekt (zum Beispiel beim Herunterladen eines Modells) zählt die globale Einstellung."""
    from cockpit.features.terminal_explain.manifest import FEATURE_ID
    if FEATURE_ID not in services.registry:
        return None
    features = services.features
    active = (features.active(FEATURE_ID, project) if project is not None
              else features.availability(FEATURE_ID).available)
    if not active:
        return None

    def prepare(parent: QWidget):
        from cockpit.ui import ai_ui
        tool_id = features.setting(FEATURE_ID, "tool") or None
        return ai_ui.prepare(services, parent, FEATURE_ID, "der Befehl und die Ausgabe",
                             tool_id)
    return prepare


def open_terminal(services, window, folder: Path, title: str, project=None,
                  command: str = "") -> None:
    """Terminal öffnen. Beim allerersten Mal ein Hinweis (ENTSCHEIDUNGEN.md). Git bekommt die
    Zugangsdaten des Projekts, wenn sie ohne Rückfrage verfügbar sind."""
    from cockpit.core import sync
    from cockpit.ui.common import show_info
    if not services.database.get_value("terminal.warned", False):
        show_info(window, "Terminal", terminal.WARNING)
        services.database.set_value("terminal.warned", True)
    env: dict[str, str] = {}
    if project is not None:
        try:
            env = sync.environment(services, project)
        except CockpitError:
            env = {}                                   # zum Beispiel Tresor gesperrt
    TerminalDialog(folder, title, env, window, explainer_for(services, project), command).exec()
