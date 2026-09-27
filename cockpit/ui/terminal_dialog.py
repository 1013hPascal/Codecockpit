"""Fenster "Terminal" (Konzept 9.9, Teilschritt 8a).

Aufbau nach dem Wunsch des Nutzers: Der Fokus beginnt im Feld "Befehl". Umschalt+Tab führt in die
Ausgabe, eine Liste mit einer Zeile pro Zeile der Ausgabe. Jede Ausgabe beginnt mit "Anfrage um
16:42:10: Befehl". Enter führt den Befehl aus. Pfeil hoch und runter im Befehlsfeld holen frühere
Befehle zurück, wie in PowerShell. In der Ausgabe wählen Umschalt+Pfeil und Strg+A mehrere Zeilen
aus, Strg+C kopiert sie.

Escape bricht einen laufenden Befehl ab, sonst schließt es das Fenster. Die Ausgabe erscheint im
Hintergrund, der Fokus bleibt im Befehlsfeld. Am Ende sagt NVDA "Fertig." oder den Rückgabewert.

Ab 8b kommt mit Tab das Feld "Erklärung der KI" dazu (Feature Terminal-Erklärung).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEvent, QItemSelectionModel, Qt
from PySide6.QtWidgets import QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import terminal
from cockpit.core.errors import CockpitError
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, copy_selected, label_for, make_copyable, name_widget
from cockpit.ui.repo_dialogs import button_row
from cockpit.ui.tasks import Task

MAX_LINES = 5000                  # ältere Zeilen fallen weg, damit die Liste schnell bleibt


class TerminalDialog(FocusDialog):
    def __init__(self, folder: Path, title: str, env: dict[str, str] | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.folder = folder
        self.env = env or {}
        self.history: list[str] = []
        self.history_index = 0
        self.task: Task | None = None
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
        layout.addLayout(button_row(self.stop_button, None, close))
        self.setTabOrder(self.output, self.edit)
        self.setTabOrder(self.edit, self.stop_button)
        self.setTabOrder(self.stop_button, close)
        self.resize(820, 560)
        self.add_line(f"Ordner: {folder}")
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
        super().reject()

    def close_terminal(self) -> None:
        if self.running:
            self.stop()
            if self.task is not None:
                self.task.wait(5000)
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


def open_terminal(services, window, folder: Path, title: str, project=None) -> None:
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
    TerminalDialog(folder, title, env, window).exec()
