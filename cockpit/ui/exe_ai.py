"""Exe mit KI einrichten (Phase 10g), die Oberfläche.

Ablauf:
1. WishDialog: Sie beschreiben, was die Exe können soll, zum Beispiel "Der Ordner
   Meine-Vokabeln soll neben der Exe liegen". Freiwillig.
2. Im Hintergrund: fester Teil (Startdatei, Ordner neben der Exe, requirements.txt) und, wenn
   eine KI da ist, ihr Vorschlag für den Code.
3. ProposalDialog: jede Änderung als Zeile, Enter zeigt alten und neuen Text. "Übernehmen" legt
   eine Sicherheitskopie an und ändert die Dateien.
4. Danach bietet das Cockpit an, die Exe gleich zu bauen und zu testen. Aus "Exe aus dem Code
   erstellen …" (on_finished) zeigt stattdessen ReadyDialog das Ergebnis mit "Exe erstellen".
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PySide6.QtWidgets import QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import exe
from cockpit.core.actions import ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.features.exe_build import ai_fix, setup_check
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, PlainEdit, confirm, label_for, name_widget, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.exe_flow import ExeActions

TITLE = "Exe mit KI einrichten"


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
                 on_finished: Callable[[list[str]], None] | None = None) -> None:
        self.on_finished = on_finished
        self.actions = actions
        self.window = actions.window
        self.services = actions.services
        self.project = project

    def settings(self) -> exe.BuildSettings:
        current = exe.read_settings(self.project.code_dir)
        if current is not None:
            return current
        code_dir = self.project.code_dir
        return exe.BuildSettings(setup_check.guess_start_file(code_dir),
                                 self.project.name.replace(" ", "-"))

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
        project, settings, wish = self.project, self.settings(), dialog.wish

        def work(task: Task):
            return ai_fix.ask(ai, project.name, project.code_dir, settings, wish,
                              task.cancel_event)

        announce("Die KI sieht sich den Code an." if ai else "Die Einrichtung wird geprüft.")
        self.actions.controller.run_task(f"exe:{project.id}", work, self.review, TITLE)

    def review(self, proposal: ai_fix.Proposal) -> None:
        if proposal.empty:
            lines = [c.line() for c in proposal.changes]
            text = "Es gibt keine Änderung, die das Cockpit übernehmen kann."
            if proposal.summary:
                text += f" Die KI sagt: {proposal.summary}"
            if lines:
                text += " " + " ".join(lines)
            if self.on_finished is not None:
                self.on_finished([text])
                return
            show_info(self.window, TITLE, text)
            return
        announce("Vorschlag da.")
        if not ProposalDialog(self.project, proposal, self.window).exec():
            announce("Nichts geändert.")
            if self.on_finished is not None:
                self.on_finished(["Nichts geändert. Der Vorschlag der KI wurde nicht übernommen."])
            return
        if not confirm(self.window, TITLE, "Die passenden Änderungen werden übernommen. Die "
                       "betroffenen Dateien kommen vorher in die Sicherheitskopien. Übernehmen?",
                       yes="Übernehmen", no="Abbrechen"):
            if self.on_finished is not None:
                self.on_finished(["Nichts geändert. Der Vorschlag der KI wurde nicht übernommen."])
            return
        try:
            ai_fix.apply(self.project.name, self.project.code_dir, proposal)
        except (CockpitError, OSError) as exc:
            show_error(self.window, TITLE, getattr(exc, "message", str(exc)))
            return
        self.window.refresh_status([self.project.id])
        announce("Änderungen übernommen.")
        if self.on_finished is not None:
            self.on_finished(["Änderungen übernommen. Die betroffenen Dateien liegen in den "
                              "Sicherheitskopien."] + [c.line() for c in proposal.usable])
            return
        if confirm(self.window, TITLE, "Soll die Exe jetzt gebaut und getestet werden?",
                   yes="Bauen und testen", no="Später"):
            context = ActionContext(self.services, self.project, Target.EXE)
            self.actions.build(context)
