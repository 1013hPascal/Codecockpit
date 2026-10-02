"""Exe mit KI einrichten (Phase 10g), die Oberfläche.

Ablauf:
1. WishDialog: Sie beschreiben, was die Exe können soll, zum Beispiel "Der Ordner
   Meine-Vokabeln soll neben der Exe liegen". Freiwillig.
2. Im Hintergrund: fester Teil (Startdatei, Ordner neben der Exe, requirements.txt) und, wenn
   eine KI da ist, ihr Vorschlag für den Code. Dabei ist WorkDialog offen (Wunsch des Nutzers,
   01.10.2026): Liste "Fortschritt" mit der Zeit seit dem Start und jeder gelesenen Datei,
   dazu "Abbrechen". Ist die KI fertig, schließt es sich und der Vorschlag kommt.
3. ProposalDialog: jede Änderung als Zeile, Enter zeigt alten und neuen Text. "Übernehmen" legt
   eine Sicherheitskopie an und ändert die Dateien.
4. Danach bietet das Cockpit an, die Exe gleich zu bauen und zu testen. Aus "Exe aus dem Code
   erstellen …" (on_finished) zeigt stattdessen ReadyDialog das Ergebnis mit "Exe erstellen".
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import exe
from cockpit.core.actions import ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.text import count
from cockpit.core.projects import Project
from cockpit.features.exe_build import ai_fix, exe_branch, setup_check
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, PlainEdit, confirm, label_for, name_widget, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.exe_flow import ExeActions

TITLE = "Exe mit KI einrichten"
_RUNNING: list[Task] = []           # abgebrochene Aufgaben, die noch auslaufen


class WishDialog(FocusDialog):
    def __init__(self, project: Project, with_ai: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{TITLE}: {project.name}")
        self.wish = ""
        self.edit = PlainEdit()
        label = label_for(self.edit, "&Was soll die Exe können? Freiwillig:" if with_ai
                          else "&Wunsch, ohne KI nicht genutzt:")
        ok = QPushButton("&Weiter")
        ok.setDefault(True)
        ok.clicked.connect(self.accept_wish)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.edit, 1)
        layout.addLayout(button_row(None, ok, cancel))
        self.resize(600, 300)
        self.initial_focus_widget = self.edit

    def accept_wish(self) -> None:
        self.wish = self.edit.toPlainText().strip()
        self.accept()


class WorkDialog(FocusDialog):
    """Fortschritt, solange das Cockpit liest und die KI arbeitet. Die erste Zeile nennt die Zeit
    seit dem Start, darunter steht jeder Schritt. Neue Zeilen verschieben die Markierung nicht,
    damit NVDA nicht ständig vorliest. Escape oder "Abbrechen" bricht ab."""

    TICK_MS = 5000                     # so oft wird die Zeile mit der Zeit erneuert

    def __init__(self, project: Project, work, with_ai: bool,
                 parent: QWidget | None = None, what: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{TITLE}: {project.name}, läuft")
        self.result_value = None
        self.failure: tuple[str, str] | None = None
        self.closed = False
        self.what = what or ("Die KI liest den Code" if with_ai
                             else "Die Einrichtung wird geprüft")
        self.started = time.monotonic()
        self.list = QListWidget()
        label = label_for(self.list, "&Fortschritt:")
        self.list.setWordWrap(True)
        self.list.addItem(f"{self.what}. Gerade gestartet.")
        self.list.setCurrentRow(0)
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(None, self.cancel_button))
        self.resize(700, 380)
        self.initial_focus_widget = self.list
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.task = Task(work, self)
        self.task.status.connect(self.add_line)
        self.task.result.connect(self.finished_ok)
        self.task.error.connect(self.failed)
        self.task.cancelled.connect(self.stopped)

    def exec(self) -> int:
        announce(f"{self.what}.")
        self.timer.start(self.TICK_MS)
        self.task.start()
        return super().exec()

    def seconds(self) -> int:
        return int(time.monotonic() - self.started)

    def tick(self) -> None:
        seconds = self.seconds()
        if seconds < 60:
            since = count(seconds, "Sekunde", "Sekunden")
        else:
            since = f"{count(seconds // 60, 'Minute', 'Minuten')} {seconds % 60} Sekunden"
        self.list.item(0).setText(f"{self.what}. Läuft seit {since}.")

    def add_line(self, text: str) -> None:
        if self.closed:
            return
        self.list.addItem(text)
        if text.startswith("An die KI gesendet"):
            announce("Der Code ist gelesen. Die KI arbeitet.")

    def finished_ok(self, value) -> None:
        if self.closed:
            return
        self.result_value = value
        self._stop_timer()
        self.accept()

    def failed(self, message: str, details: str) -> None:
        if self.closed:
            return
        self.failure = (message, details)
        self._stop_timer()
        super().reject()

    def stopped(self) -> None:
        if self.closed:
            return
        self._stop_timer()
        super().reject()

    def _stop_timer(self) -> None:
        self.timer.stop()

    def reject(self) -> None:
        """Abbrechen: Die KI bekommt das Signal zum Aufhören. Das Fenster schließt sofort. Die
        Aufgabe läuft am Hauptfenster aus, ihr Ergebnis wird nicht mehr gebraucht. So friert
        nichts ein, auch wenn die KI erst nach einer Weile aufhört."""
        self._stop_timer()
        self._release_task()
        super().reject()

    def _release_task(self) -> None:
        task = self.task
        if not task.isRunning():
            return
        task.cancel()
        self.closed = True                        # späte Meldungen der Aufgabe zählen nicht
        task.setParent(None)
        _RUNNING.append(task)                     # nie einen laufenden Thread zerstören
        task.finished.connect(lambda: _RUNNING.remove(task) if task in _RUNNING else None)

    def done(self, code: int) -> None:
        self._stop_timer()
        self._release_task()
        super().done(code)


class ProposalDialog(FocusDialog):
    """Vorschlag als Liste. Enter auf einer Änderung zeigt alten und neuen Text."""

    def __init__(self, project: Project, proposal: ai_fix.Proposal,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.proposal = proposal
        usable = len(proposal.usable) + (1 if proposal.settings is not None else 0)
        self.setWindowTitle(f"Vorschlag für die Exe von {project.name}: "
                            f"{usable} {'Änderung' if usable == 1 else 'Änderungen'}")
        self.rows: list[ai_fix.Change | None] = []
        self.list = QListWidget()
        name_widget(self.list, "Vorschlag")
        if proposal.summary:
            self._add(f"Zusammenfassung der KI: {proposal.summary}", None)
        for line in proposal.settings_lines:
            self._add(f"Einstellung: {line}", None)
        for change in proposal.changes:
            self._add(change.line(), change)
        self.list.setCurrentRow(0)
        self.list.installEventFilter(self)
        show = QPushButton("&Anzeigen")
        show.clicked.connect(self.show_current)
        apply = QPushButton("Ü&bernehmen")
        apply.setDefault(False)
        apply.clicked.connect(self.accept)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(show, None, apply, cancel))
        self.resize(760, 420)
        self.initial_focus_widget = self.list

    def _add(self, text: str, change: ai_fix.Change | None) -> None:
        self.list.addItem(text)
        self.rows.append(change)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            self.show_current()
            return True
        return super().eventFilter(watched, event)

    def show_current(self) -> None:
        from cockpit.ui.text_dialog import TextDialog
        row = self.list.currentRow()
        change = self.rows[row] if 0 <= row < len(self.rows) else None
        if change is None:
            announce(self.list.currentItem().text() if self.list.currentItem() else "")
            return
        lines = [change.line(), "Bisher:"] + (change.old.splitlines() or ["(neue Datei)"]) \
            + ["Neu:"] + change.new.splitlines()
        TextDialog(f"Änderung an {change.file}", lines, "Änderung", self).exec()


class ExeAIFlow:
    def __init__(self, actions: "ExeActions", project: Project,
                 on_finished: Callable[..., None] | None = None) -> None:
        self.on_finished = on_finished
        self.actions = actions
        self.window = actions.window
        self.services = actions.services
        self.project = project
        # Gibt es den Branch Cockpit-exe-bauen schon, liest die KI dort. So baut ein weiterer
        # Versuch auf dem vorigen auf (Wunsch des Nutzers, 02.10.2026: mehrere Durchgänge).
        try:
            self.branch_folder = exe_branch.current_folder(project) if project else None
        except CockpitError:
            self.branch_folder = None
        self.source_dir = self.branch_folder or (project.code_dir if project else None)

    def _finish(self, lines: list[str]) -> None:
        """Ohne Änderung weiter: Gebaut wird dann aus dem Branch, wenn es ihn schon gibt."""
        if self.branch_folder is not None:
            self.on_finished(lines, self.branch_folder)
        else:
            self.on_finished(lines)

    def settings(self) -> exe.BuildSettings:
        current = exe.read_settings(self.source_dir) or exe.read_settings(self.project.code_dir)
        if current is not None:
            return current
        return exe.BuildSettings(setup_check.guess_start_file(self.source_dir),
                                 self.project.name.replace(" ", "-"))

    def _ai(self, purpose: str):
        """Text-KI oder None. purpose ergänzt die Rückfrage, wenn keine KI da ist."""
        from cockpit.ui import ai_ui
        ai = ai_ui.prepare(self.services, self.window, "exe_fix",
                           "die Prüfung der Exe, Fehlermeldungen und Auszüge aus dem Code")
        if not isinstance(ai, str):
            return ai
        if ai != ai_ui.DECLINED:
            show_error(self.window, TITLE, f"{ai} {purpose}")
        return False

    def start(self) -> None:
        from cockpit.ui import ai_ui
        ai = ai_ui.prepare(self.services, self.window, "exe_fix",
                           "die Prüfung der Exe und Auszüge aus dem Code")
        if isinstance(ai, str):
            if ai == ai_ui.DECLINED or not confirm(
                    self.window, TITLE, f"{ai} Ohne KI schlägt das Cockpit nur die Einstellungen "
                    "und fehlende Bibliotheken vor. Weiter?", yes="Weiter", no="Abbrechen"):
                return
            ai = None
        dialog = WishDialog(self.project, ai is not None, self.window)
        if not dialog.exec():
            return
        self.run(ai, dialog.wish)

    def start_fix(self, error: str) -> None:
        """Problem mit KI lösen (Wunsch des Nutzers, 02.10.2026): Die KI bekommt die
        Fehlermeldung des Baus. Danach geht es wie beim Einrichten weiter, mit "Exe erstellen".
        Scheitert der Bau wieder, beginnt der nächste Durchgang."""
        ai = self._ai("Ohne KI lässt sich der Fehler nicht automatisch lösen.")
        if ai is False:
            return
        self.run(ai, "", error)

    def run(self, ai, wish: str, error: str = "") -> None:
        project, settings, source = self.project, self.settings(), self.source_dir

        def work(task: Task):
            return ai_fix.ask(ai, project.name, source, settings, wish, task.cancel_event,
                              progress=task.status.emit, error=error)

        # Wunsch des Nutzers (01.10.2026): ein Fenster mit Fortschritt und "Abbrechen"
        what = "Die KI versucht, das Problem zu lösen" if error else ""
        progress = WorkDialog(project, work, ai is not None, self.window, what)
        if progress.exec() and progress.result_value is not None:
            self.review(progress.result_value)
        elif progress.failure is not None:
            show_error(self.window, TITLE, *progress.failure)
        else:
            announce("Abgebrochen. Nichts geändert.")

    def review(self, proposal: ai_fix.Proposal) -> None:
        if proposal.empty:
            lines = [c.line() for c in proposal.changes]
            text = "Es gibt keine Änderung, die das Cockpit übernehmen kann."
            if proposal.summary:
                text += f" Die KI sagt: {proposal.summary}"
            if lines:
                text += " " + " ".join(lines)
            if self.on_finished is not None:
                self._finish([text])
                return
            show_info(self.window, TITLE, text)
            return
        announce("Vorschlag da.")
        if not ProposalDialog(self.project, proposal, self.window).exec():
            announce("Nichts geändert.")
            if self.on_finished is not None:
                self._finish(["Nichts geändert. Der Vorschlag der KI wurde nicht übernommen."])
            return
        # Wunsch des Nutzers (01.10.2026): nie direkt in main, sondern im Branch Cockpit-exe-bauen
        text = (f"{exe_branch.where_text(self.project)} Die betroffenen Dateien kommen vorher in "
                "die Sicherheitskopien. Danach wird die Exe aus dem Branch gebaut und getestet. "
                "Erst dann entscheiden Sie, ob die Änderungen in main kommen. Übernehmen?")
        if not confirm(self.window, TITLE, text, yes="Übernehmen", no="Abbrechen"):
            if self.on_finished is not None:
                self._finish(["Nichts geändert. Der Vorschlag der KI wurde nicht übernommen."])
            return
        self.apply_in_branch(proposal)

    def apply_in_branch(self, proposal: ai_fix.Proposal) -> None:
        """Branch vorbereiten, Änderungen dort übernehmen und committen, im Hintergrund."""
        project = self.project
        files = [c.file for c in proposal.usable] + ["cockpit.toml"]
        if proposal.settings is not None:
            files.append(proposal.settings.spec_name)

        def work(task: Task):
            folder = exe_branch.prepare(project)
            ai_fix.apply(project.name, folder, proposal)
            exe_branch.commit(folder, files)
            return folder

        def done(folder) -> None:
            self.window.reload_projects(refresh=False)
            self.window.refresh_status([project.id])
            announce(f"Änderungen im Branch {exe_branch.BRANCH} übernommen.")
            lines = ([f"Änderungen im Branch {exe_branch.BRANCH} übernommen, Ordner {folder}. "
                      "Main ist unverändert."]
                     + [c.line() for c in proposal.usable]
                     + ["Mit „Exe erstellen“ baut das Cockpit die Exe aus diesem Branch und "
                        "testet sie. Sie kommt als eigene Datei neben die normale Exe."])
            if self.on_finished is not None:
                self.on_finished(lines, folder)
                return
            context = ActionContext(self.services, project, Target.EXE)
            self.actions.offer_build(context, lines, folder)

        announce(f"Branch {exe_branch.BRANCH} wird vorbereitet.")
        self.actions.controller.run_task(f"exe:{project.id}", work, done, TITLE)
