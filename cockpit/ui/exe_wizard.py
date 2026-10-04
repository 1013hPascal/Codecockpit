"""Exe aus dem Code erstellen, Schritt für Schritt (Wunsch des Nutzers vom 03.10.2026).

1. Dateien neben der Exe: Was der Code unbedingt braucht, ist angehakt. README und Lizenz kommen
   immer mit.
2. Mit oder ohne KI, nur wenn eine Text-KI eingerichtet ist. Gebaut wird in beiden Fällen im
   Branch Cockpit-exe-bauen, main bleibt unverändert.
3. Einrichtung: Das Cockpit legt den Branch an, ohne zu fragen, speichert dort die Einstellungen
   und prüft die Einrichtung. Mit KI liest die KI den Code und schlägt Änderungen vor.
4. Zusammenfassung, was passiert. "Mit KI schreiben" klappt erst auf Wunsch die Frage an die KI
   und das Gespräch auf. Weiter heißt "Exe erstellen".
5. Der Bau mit Ausgabe.
6. Ergebnis im selben Fenster. Bei einem Fehler: "Problem mit KI lösen" (nur mit KI), "Neuer
   Versuch, Exe zu bauen", "Zurück", "Abbrechen". Bei Erfolg: "Erst testen …" (öffnet den Ordner
   der neuen Exe), "Jetzt in main überführen und Release veröffentlichen", "Jetzt in main
   überführen, später veröffentlichen".
Jeder Schritt hat "Zurück" und "Abbrechen". Abbrechen löscht den Branch wieder, wenn dieser
Durchgang ihn angelegt hat. Main bleibt dann, wie es war.
"""
from __future__ import annotations

import dataclasses
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import exe
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.features.exe_build import ai_fix, exe_branch, setup_check
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, click_focused_button, confirm, label_for, make_copyable
from cockpit.ui.error_dialog import show_error
from cockpit.ui.exe_flow import BuildDialog, BuildSettingsDialog, beside_line
from cockpit.ui.repo_dialogs import _is_enter, button_row

if TYPE_CHECKING:
    from cockpit.ui.exe_flow import ExeActions

log = logging.getLogger(__name__)

TITLE = "Exe aus dem Code erstellen"
BACK, NEXT, CANCEL, REPEAT, FIX, RETRY = "back", "next", "cancel", "repeat", "fix", "retry"
TEST_LATER, MERGE_PUBLISH, MERGE_ONLY = "test_later", "merge_publish", "merge_only"
WITH_AI = "Mit KI-Unterstützung die Exe bauen"
WITHOUT_AI = "Ohne KI die Exe bauen"
MODE_TEXT = ("Sie können den Vorgang der Exe-Erstellung mit oder ohne KI durchführen. Empfohlen "
             "ist mit KI, da diese versuchen kann, Probleme zu lösen, die auftreten. Es wird ein "
             "neuer Branch für den Exe-Bau erstellt und nichts an main verändert.")
TEST_LATER_TEXT = "&Erst testen, später in main überführen und Release veröffentlichen"
MERGE_PUBLISH_TEXT = "Jetzt in main überführen und Release &veröffentlichen"
MERGE_ONLY_TEXT = "Jetzt in &main überführen, später veröffentlichen"


def step_title(project: Project, number: int, name: str) -> str:
    return f"{TITLE}: {project.name}, Schritt {number}: {name}"


class StepDialog(FocusDialog):
    """Ein Schritt mit "Zurück", dem Knopf zum nächsten Schritt und "Abbrechen". Escape bricht
    ab. Nach dem Schließen steht in choice, was gewählt wurde."""

    def __init__(self, title: str, next_text: str, parent: QWidget | None = None,
                 back: bool = True) -> None:
        super().__init__(parent)
        self.choice = CANCEL
        self.setWindowTitle(title)
        self.body = QVBoxLayout()
        self.back_button = QPushButton("&Zurück")
        self.back_button.clicked.connect(lambda: self.finish(BACK))
        self.back_button.setVisible(back)
        self.next_button = QPushButton(next_text)
        self.next_button.clicked.connect(lambda: self.finish(NEXT))
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        for button in (self.back_button, self.next_button, self.cancel_button):
            button.setAutoDefault(False)
        self.extra: list[QPushButton] = []
        layout = QVBoxLayout(self)
        layout.addLayout(self.body, 1)
        self.button_layout = button_row(self.back_button, None, self.next_button,
                                        self.cancel_button)
        layout.addLayout(self.button_layout)
        self.resize(720, 480)

    def finish(self, choice: str) -> None:
        self.choice = choice
        self.accept()

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)


class ModeDialog(StepDialog):
    """Schritt 2: mit oder ohne KI. Mit KI steht oben und ist empfohlen."""

    def __init__(self, project: Project, number: int, with_ai: bool,
                 parent: QWidget | None = None) -> None:
        super().__init__(step_title(project, number, "Mit oder ohne KI"), "&Weiter", parent)
        text = QLabel(MODE_TEXT)
        text.setWordWrap(True)
        self.list = QListWidget()
        label = label_for(self.list, "&Exe bauen:")
        self.list.addItems([WITH_AI, WITHOUT_AI])
        self.list.setCurrentRow(0 if with_ai else 1)
        self.list.itemActivated.connect(lambda _item: self.finish(NEXT))
        for widget in (text, label):
            self.body.addWidget(widget)
        self.body.addWidget(self.list, 1)
        self.resize(640, 320)
        self.initial_focus_widget = self.list

    def showEvent(self, event) -> None:
        super().showEvent(event)
        announce(MODE_TEXT)

    @property
    def with_ai(self) -> bool:
        return self.list.currentRow() == 0


class SummaryDialog(StepDialog):
    """Schritt 4: was passiert. Enter auf einer Änderung der KI zeigt alten und neuen Text.
    "Mit KI schreiben" klappt die Frage an die KI und das Gespräch auf (Wunsch des Nutzers)."""

    def __init__(self, project: Project, number: int, lines: list[str],
                 changes: list[ai_fix.Change | None], services=None, next_text: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(step_title(project, number, "Zusammenfassung"),
                         next_text or "Exe e&rstellen", parent)
        self.hints = ""
        self.changes = changes
        self.list = QListWidget()
        label = label_for(self.list, "&Zusammenfassung:")
        self.list.setWordWrap(True)
        self.list.addItems(lines)
        self.list.setCurrentRow(0)
        self.list.installEventFilter(self)
        make_copyable(self.list)
        self.body.addWidget(label)
        self.body.addWidget(self.list, 1)
        self.chat = None
        self.chat_button = None
        self.repeat_button = None
        if services is not None:
            from cockpit.ui.exe_chat import REPEAT_TEXT, ExeChat
            self.chat = ExeChat(services, project.name, "Die Einrichtung ist fertig, die Exe ist "
                                "noch nicht gebaut. Gebaut wird im Branch "
                                f"{exe_branch.BRANCH}.", self.lines, self)
            self.chat.setVisible(False)
            self.body.addWidget(self.chat, 1)
            self.chat_button = QPushButton("Mit &KI schreiben")
            self.chat_button.setAutoDefault(False)
            self.chat_button.clicked.connect(self.open_chat)
            self.repeat_button = QPushButton(REPEAT_TEXT)
            self.repeat_button.setAutoDefault(False)
            self.repeat_button.setVisible(False)
            self.repeat_button.clicked.connect(self.repeat)
            self.button_layout.insertWidget(1, self.chat_button)
            self.button_layout.insertWidget(2, self.repeat_button)
        self.resize(760, 560)
        self.initial_focus_widget = self.list

    def lines(self) -> list[str]:
        result = []
        for row in range(self.list.count()):
            result.append(self.list.item(row).text())
            change = self.changes[row] if row < len(self.changes) else None
            if change is not None:
                result += ["Bisher:", change.old or "(neue Datei)", "Neu:", change.new]
        return result

    def open_chat(self) -> None:
        self.chat.setVisible(True)
        self.repeat_button.setVisible(True)
        self.chat_button.setVisible(False)
        self.chat.question.setFocus()

    def repeat(self) -> None:
        from cockpit.ui.exe_chat import NO_HINTS
        if not self.chat.history:
            announce(NO_HINTS)
            self.chat.question.setFocus()
            return
        self.hints = self.chat.hints()
        self.finish(REPEAT)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            self.show_current()
            return True
        return super().eventFilter(watched, event)

    def show_current(self) -> None:
        from cockpit.ui.text_dialog import TextDialog
        row = self.list.currentRow()
        change = self.changes[row] if 0 <= row < len(self.changes) else None
        if change is None:
            return
        lines = [change.line(), "Bisher:"] + (change.old.splitlines() or ["(neue Datei)"]) \
            + ["Neu:"] + change.new.splitlines()
        TextDialog(f"Änderung an {change.file}", lines, "Änderung", self).exec()

    def done(self, code: int) -> None:
        if self.chat is not None:
            self.chat.stop()
        super().done(code)


class WizardBuildDialog(BuildDialog):
    """Schritte 5 und 6: der Bau, danach im selben Fenster das Ergebnis mit den Knöpfen für den
    nächsten Schritt."""

    def __init__(self, services, project: Project, settings: exe.BuildSettings, folder: Path,
                 with_ai: bool, parent: QWidget | None = None) -> None:
        self.choice = CANCEL
        self.with_ai = with_ai
        super().__init__(services, project, settings, parent, branch_dir=folder,
                         branch_name=exe_branch.BRANCH)
        self.setWindowTitle(step_title(project, 5, "Exe wird gebaut"))
        self.close_button.setVisible(False)
        self.result_buttons: list[QPushButton] = []

    def _button(self, text: str, choice: str) -> QPushButton:
        button = QPushButton(text)
        button.setAutoDefault(False)
        button.clicked.connect(lambda: self.finish(choice))
        self.buttons.insertWidget(self.buttons.count() - 1, button)
        self.result_buttons.append(button)
        return button

    def finish(self, choice: str) -> None:
        self.choice = choice
        self.accept()

    def after_build(self) -> None:
        self.setWindowTitle(step_title(self.project, 6, "Ergebnis"))
        if self.result is not None and not self.failed_build:
            first = self._button(TEST_LATER_TEXT, TEST_LATER)
            self._button(MERGE_PUBLISH_TEXT, MERGE_PUBLISH)
            self._button(MERGE_ONLY_TEXT, MERGE_ONLY)
            self.choice = TEST_LATER                  # Escape: nichts überführen, Branch bleibt
        else:
            first = self._button("Problem mit &KI lösen", FIX) if self.with_ai else None
            retry = self._button("&Neuer Versuch, Exe zu bauen", RETRY)
            self._button("&Zurück", BACK)
            cancel = QPushButton("Abbrechen")
            cancel.setAutoDefault(False)
            cancel.clicked.connect(lambda: self.finish(CANCEL))
            self.buttons.addWidget(cancel)
            first = first or retry
            self.choice = CANCEL
        first.setDefault(True)

    def reject(self) -> None:
        if self.running:
            self.stop()
            return
        FocusDialog.reject(self)


class ExeWizard:
    """Führt durch die Schritte. Jeder Schritt gibt den Namen des nächsten zurück, None am Ende."""

    def __init__(self, actions: "ExeActions", project: Project) -> None:
        self.actions = actions
        self.window = actions.window
        self.services = actions.services
        self.project = project
        self.ai_available = not self.services.ai_problem()
        self.use_ai = self.ai_available
        self.ai = None
        self.settings: exe.BuildSettings | None = None
        self.had_branch = exe_branch.exists(project)
        self.folder: Path | None = exe_branch.current_folder(project) if self.had_branch else None
        self.proposal: ai_fix.Proposal | None = None
        self.lines: list[str] = []
        self.hints = ""
        self.error = ""

    def run(self) -> None:
        step = "files"
        while step:
            step = getattr(self, f"step_{step}")()

    def _number(self, name: str) -> int:
        order = ["files", "mode", "setup", "summary"] if self.ai_available \
            else ["files", "setup", "summary"]
        return order.index(name) + 1

    # -- Schritt 1 ----------------------------------------------------------------------------
    def step_files(self):
        source = self.folder or self.project.code_dir
        current = self.settings or exe.read_settings(source) or \
            exe.read_settings(self.project.code_dir)
        dialog = BuildSettingsDialog(self.project, self.window, current, in_flow=True,
                                     code_dir=self.project.code_dir)
        if not dialog.exec() or dialog.settings is None:
            return self.cancel("files")
        self.settings = dialog.settings
        return "mode" if self.ai_available else "setup"

    # -- Schritt 2 ----------------------------------------------------------------------------
    def step_mode(self):
        dialog = ModeDialog(self.project, self._number("mode"), self.use_ai, self.window)
        dialog.exec()
        if dialog.choice == BACK:
            return "files"
        if dialog.choice != NEXT:
            return self.cancel("mode")
        self.use_ai = dialog.with_ai
        if self.use_ai and self.ai is None:
            from cockpit.ui import ai_ui
            ai = ai_ui.prepare(self.services, self.window, "exe_fix",
                               "die Prüfung der Exe, Fehlermeldungen und Auszüge aus dem Code")
            if isinstance(ai, str):
                if ai != ai_ui.DECLINED:
                    show_error(self.window, TITLE, ai)
                return "mode"
            self.ai = ai
        return "setup"

    # -- Schritt 3 ----------------------------------------------------------------------------
    def step_setup(self):
        from cockpit.ui.exe_ai import WorkDialog
        project, settings = self.project, dataclasses.replace(self.settings)
        ai = self.ai if self.use_ai else None
        wish, error = ai_fix.with_hints("", self.hints), self.error

        def work(task):
            task.status.emit(f"Branch {exe_branch.BRANCH} wird vorbereitet.")
            folder = exe_branch.prepare(project)
            if exe.read_settings(folder) != settings:
                exe.change_settings(folder, project.name, settings)
                exe_branch.commit(folder, ["cockpit.toml", settings.spec_name],
                                  "Exe-Einstellungen")
            saved = exe.read_settings(folder) or settings
            if ai is None:
                return folder, None, setup_check.check_for(folder, saved,
                                                           exe.current_exe(project))
            return folder, ai_fix.ask(ai, project.name, folder, saved, wish, task.cancel_event,
                                      progress=task.status.emit, error=error), []

        what = ("Die KI versucht, das Problem zu lösen" if error else
                "Die KI liest den Code" if ai is not None else "Die Einrichtung wird geprüft")
        progress = WorkDialog(project, work, ai is not None, self.window, what,
                              step_title(project, self._number("setup"), "Einrichtung"))
        progress.exec()
        if progress.result_value is not None:
            self.folder, self.proposal, self.lines = progress.result_value
            return "summary"
        previous = "mode" if self.ai_available else "files"
        if progress.failure is not None:
            show_error(self.window, TITLE, *progress.failure)
            return previous
        if progress.back_requested:
            return previous
        return self.cancel("setup")

    # -- Schritt 4 ----------------------------------------------------------------------------
    def summary_lines(self) -> tuple[list[str], list[ai_fix.Change | None]]:
        lines: list[str] = []
        changes: list[ai_fix.Change | None] = []

        def add(text: str, change: ai_fix.Change | None = None) -> None:
            lines.append(text)
            changes.append(change)

        proposal = self.proposal
        if proposal is not None:
            if proposal.empty:
                add("Die KI schlägt keine Änderung vor." + (f" {proposal.summary}"
                                                            if proposal.summary else ""))
                for change in proposal.changes:
                    add(change.line())
            else:
                count = len(proposal.usable) + (1 if proposal.settings is not None else 0)
                add(f"Die KI schlägt {count} {'Änderung' if count == 1 else 'Änderungen'} vor. "
                    "Sie kommen mit „Exe erstellen“ in den Branch." + (
                        f" {proposal.summary}" if proposal.summary else ""))
                for line in proposal.settings_lines:
                    add(f"Einstellung: {line}")
                for change in proposal.changes:
                    add(change.line(), change)
                for note in proposal.notes:
                    add(note)
        for line in self.lines:
            add(line)
        settings = self.settings
        name = exe.branch_exe_name(settings.name if settings else self.project.name,
                                   exe_branch.BRANCH)
        add(f"Gebaut wird im Branch {exe_branch.BRANCH}, Ordner {self.folder}. Main bleibt "
            "unverändert.")
        add(beside_line(self.project, self.folder))
        add(f"Die neue Exe kommt in den Ordner Exe\\{name} und wird getestet. Die bisherige Exe "
            "bleibt, bis Sie die neue in main überführen.")
        return lines, changes

    def step_summary(self):
        lines, changes = self.summary_lines()
        announce(lines[0])
        with_chat = self.use_ai and self.ai is not None
        dialog = SummaryDialog(self.project, self._number("summary"), lines, changes,
                               self.services if with_chat else None,
                               "&Neuer Versuch, Exe zu bauen" if self.error else "", self.window)
        dialog.exec()
        if dialog.choice == BACK:
            self.error = ""
            return "mode" if self.ai_available else "files"
        if dialog.choice == REPEAT:
            self.hints = dialog.hints
            return "setup"
        if dialog.choice != NEXT:
            return self.cancel("summary")
        if not self.apply_proposal():
            return "summary"
        return "build"

    def apply_proposal(self) -> bool:
        """Die Änderungen der KI im Branch übernehmen und committen. Die betroffenen Dateien
        kommen vorher in die Sicherheitskopien."""
        proposal, self.proposal = self.proposal, None
        if proposal is None or proposal.empty:
            return True
        files = [c.file for c in proposal.usable] + ["cockpit.toml"]
        if proposal.settings is not None:
            files.append(proposal.settings.spec_name)
        try:
            ai_fix.apply(self.project.name, self.folder, proposal)
            exe_branch.commit(self.folder, files)
        except (CockpitError, OSError) as exc:
            self.proposal = proposal
            show_error(self.window, TITLE, getattr(exc, "message", "Die Änderungen ließen sich "
                                                   "nicht übernehmen."), str(exc))
            return False
        self.settings = exe.read_settings(self.folder) or self.settings
        announce(f"Änderungen im Branch {exe_branch.BRANCH} übernommen.")
        return True

    # -- Schritte 5 und 6 ---------------------------------------------------------------------
    def step_build(self):
        project = self.project
        settings = exe.read_settings(self.folder) or self.settings
        try:
            seconds = int(self.services.features.setting("exe_build", "test_seconds"))
        except (KeyError, LookupError, TypeError, ValueError, CockpitError):
            seconds = settings.test_seconds
        settings = dataclasses.replace(settings, test_seconds=seconds)
        dialog = WizardBuildDialog(self.services, project, settings, self.folder,
                                   self.use_ai and self.ai is not None, self.window)
        dialog.exec()
        self.window.refresh_status([project.id])
        choice = dialog.choice
        if choice == TEST_LATER:
            self.actions.open_branch_exe(project)
            announce(f"Der Branch {exe_branch.BRANCH} bleibt. Wenn die Exe passt, wählen Sie bei "
                     "Exe „Exe-Bau abschließen …“.")
            return None
        if choice in (MERGE_PUBLISH, MERGE_ONLY):
            self.actions.merge_branch(project, publish=choice == MERGE_PUBLISH)
            return None
        if choice == FIX:
            self.error = dialog.error_text
            self.hints = ""
            return "setup"
        if choice == RETRY:
            return "build"
        if choice == BACK:
            return "summary"
        return self.cancel("build")

    # -- Abbrechen ----------------------------------------------------------------------------
    def cancel(self, back_to: str):
        """Abbrechen. Hat dieser Durchgang den Branch angelegt, wird er nach Rückfrage gelöscht.
        Die sichere Antwort ist "Zurück"."""
        if self.had_branch or not exe_branch.exists(self.project):
            announce("Abgebrochen. Main ist unverändert." if not self.had_branch else
                     f"Abgebrochen. Der Branch {exe_branch.BRANCH} bleibt, wie er war.")
            return None
        if not confirm(self.window, TITLE, f"Den Exe-Bau abbrechen? Der Branch "
                       f"{exe_branch.BRANCH} und eine darin gebaute Exe werden gelöscht. Main "
                       "bleibt, wie es war.", yes="Abbrechen und löschen", no="Zurück"):
            return back_to if back_to != "build" else "summary"
        self.actions.discard_branch(self.project)
        return None
