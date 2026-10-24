"""Die einzelnen Schritte des Exe-Assistenten.
"""
from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget
from pathlib import Path

from cockpit.core import exe
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.features.exe_build import ai_fix, exe_branch
from cockpit.ui.announcer import announce
from cockpit.ui.common import (
    FocusDialog, PlainEdit, click_focused_button, label_for, make_copyable)
from cockpit.ui.exe_flow import BuildDialog
from cockpit.ui.repo_dialogs import _is_enter, button_row


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


CHAT_TEXT = "Mit KI &chatten"                        # vorher "Mit KI schreiben" (04.10.2026)


FIX_TEXT = "Problem mit &KI lösen"


RETRY_TEXT = "&Neuer Versuch, Exe zu bauen"


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
    "Mit KI chatten" klappt die Frage an die KI und das Gespräch auf (Wunsch des Nutzers)."""

    def __init__(self, project: Project, number: int, lines: list[str],
                 changes: list[ai_fix.Change | None], services=None, next_text: str = "",
                 parent: QWidget | None = None, code_dir: Path | None = None,
                 start_file: str = "", error: str = "") -> None:
        super().__init__(step_title(project, number, "Zusammenfassung"),
                         next_text or "Exe e&rstellen", parent)
        self.hints = ""
        self.changes = changes
        self.error = error                # Fehler des letzten Versuchs, geht mit in den Chat
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
                                f"{exe_branch.BRANCH}.", self.lines, self, code_dir,
                                start_file)
            self.chat.setVisible(False)
            self.body.addWidget(self.chat, 1)
            self.chat_button = QPushButton(CHAT_TEXT)
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
        if self.error:
            result += ["Fehler beim letzten Versuch:"] + self.error.splitlines()[-40:]
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


class ProblemDialog(StepDialog):
    """Ein Fehler unterwegs: Meldung und Ausgabe zum Lesen, der Text liegt in der Zwischenablage.
    Mit KI: "Problem mit KI lösen" (choice FIX) und "Mit KI chatten". Die Hinweise aus dem
    Gespräch stehen danach in hints. Immer "Zurück" und als letztes "Abbrechen"."""

    def __init__(self, project: Project, number: int, message: str, details: str,
                 services=None, parent: QWidget | None = None, code_dir: Path | None = None,
                 start_file: str = "") -> None:
        super().__init__(step_title(project, number, "Fehler"), FIX_TEXT, parent)
        self.hints = ""
        self.text = "\n\n".join(p for p in (message.strip(), details.strip()) if p)
        label = QLabel(message)
        label.setWordWrap(True)
        self.output = PlainEdit()
        self.output.setReadOnly(True)
        self.output.setPlainText(self.text)
        output_label = label_for(self.output, "&Ausgabe:")
        self.body.addWidget(label)
        self.body.addWidget(output_label)
        self.body.addWidget(self.output, 1)
        self.next_button.setVisible(services is not None)
        self.chat = None
        self.chat_button = None
        if services is not None:
            from cockpit.ui.exe_chat import ExeChat
            self.chat = ExeChat(services, project.name, "Beim Erstellen der Exe ist ein Fehler "
                                "aufgetreten. Die Ausgabe steht im Fenster.",
                                lambda: self.text.splitlines(), self, code_dir, start_file)
            self.chat.setVisible(False)
            self.body.addWidget(self.chat, 1)
            self.chat_button = QPushButton(CHAT_TEXT)
            self.chat_button.setAutoDefault(False)
            self.chat_button.clicked.connect(self.open_chat)
            self.button_layout.insertWidget(self.button_layout.indexOf(self.next_button) + 1,
                                            self.chat_button)
        # Wunsch des Nutzers: der Fehler liegt gleich in der Zwischenablage
        QGuiApplication.clipboard().setText(self.text)
        self.resize(760, 520)
        self.initial_focus_widget = self.output

    def showEvent(self, event) -> None:
        super().showEvent(event)
        announce("Fehler. Der Text ist in der Zwischenablage.", urgent=True)

    def open_chat(self) -> None:
        self.chat.setVisible(True)
        self.chat_button.setVisible(False)
        self.chat.question.setFocus()

    def finish(self, choice: str) -> None:
        if self.chat is not None:
            self.hints = self.chat.hints()
        # Der Knopf zum nächsten Schritt ist hier "Problem mit KI lösen" (Rückmeldung vom
        # 04.10.2026: vorher kam stattdessen die Frage nach dem Abbrechen)
        super().finish(FIX if choice == NEXT else choice)

    def done(self, code: int) -> None:
        if self.chat is not None:
            self.chat.stop()
        super().done(code)


class WizardBuildDialog(BuildDialog):
    """Schritte 5 und 6: der Bau, danach im selben Fenster das Ergebnis mit den Knöpfen für den
    nächsten Schritt.
    Besteht die Exe den Test nicht oder blockiert Windows ihn, ist sie trotzdem gebaut. Dann gibt
    es "Trotzdem behalten" neben "Problem mit KI lösen", "Mit KI chatten" und "Neuer Versuch"
    (Wunsch des Nutzers vom 11.10.2026: vorher ließ sich eine von Windows blockierte Exe hier
    nicht behalten). Nach "Trotzdem behalten" folgen dieselben Knöpfe wie bei Erfolg."""

    keep_failed = True

    def __init__(self, services, project: Project, settings: exe.BuildSettings, folder: Path,
                 with_ai: bool, parent: QWidget | None = None) -> None:
        self.choice = CANCEL
        self.with_ai = with_ai
        self.pending: exe.BuildResult | None = None   # gebaut, Test nicht bestanden
        self.build_settings = settings
        self.hints = ""
        self.chat = None
        self.result_buttons: list[QPushButton] = []
        super().__init__(services, project, settings, parent, branch_dir=folder,
                         branch_name=exe_branch.BRANCH)
        self.setWindowTitle(step_title(project, 5, "Exe wird gebaut"))
        self.close_button.setVisible(False)

    def _button(self, text: str, choice: str | None = None, slot=None) -> QPushButton:
        button = QPushButton(text)
        button.setAutoDefault(False)
        button.clicked.connect(slot or (lambda: self.finish(choice)))
        self.buttons.insertWidget(self.buttons.count() - 1, button)
        self.result_buttons.append(button)
        return button

    def finish(self, choice: str) -> None:
        if self.chat is not None:
            self.hints = self.chat.hints()
        self.choice = choice
        self.accept()

    def finished_ok(self, result: exe.BuildResult) -> None:
        if not result.untested:
            super().finished_ok(result)
            return
        self._sound(False)                            # gebaut, Test nicht bestanden
        self.pending = result
        self.failed_build = True
        if result.test_error:
            text = f"Die Exe ist gebaut, hat den Test aber nicht bestanden. {result.test_error}"
            if result.test_details:
                self.output.addItem(result.test_details)
        else:
            text = ("Die Exe ist gebaut, aber Windows hat den Test blockiert. Sie können sie "
                    "trotzdem behalten und selbst starten.")
        # Bericht zum Bau: was geklappt hat, was die Exe meldete, was zu tun ist (14.10.2026)
        for line in result.report:
            self.output.addItem(line)
        self.ended(text, urgent=True)
        output = [self.output.item(r).text() for r in range(self.output.count())]
        self.error_text = "\n".join(output[-60:])

    def after_build(self) -> None:
        self.setWindowTitle(step_title(self.project, 6, "Ergebnis"))
        if self.result is not None and not self.failed_build:
            self._success_buttons()
            return
        first = None
        if self.pending is not None:
            first = self._button("Trotzdem &behalten", slot=self.keep)
        fix = self._button("Problem mit &KI lösen", FIX) if self.with_ai else None
        if self.with_ai:
            self._button(CHAT_TEXT, slot=self.open_chat)
        retry = self._button(RETRY_TEXT, RETRY)
        self._button("&Zurück", BACK)
        cancel = self._button("Abbrechen", CANCEL)
        self.buttons.removeWidget(cancel)
        self.buttons.addWidget(cancel)                 # Abbrechen immer als letztes
        self.choice = CANCEL
        (first or fix or retry).setDefault(True)

    def _success_buttons(self) -> None:
        first = self._button(TEST_LATER_TEXT, TEST_LATER)
        self._button(MERGE_PUBLISH_TEXT, MERGE_PUBLISH)
        self._button(MERGE_ONLY_TEXT, MERGE_ONLY)
        self.choice = TEST_LATER                      # Escape: nichts überführen, Branch bleibt
        first.setDefault(True)

    def keep(self) -> None:
        """Die nicht bestandene oder blockierte Exe als Exe des Branches behalten."""
        pending, self.pending = self.pending, None
        try:
            result = exe.install_untested(self.project, pending, self.build_settings,
                                          self.branch_dir)
        except CockpitError as exc:
            self.ended(f"Fehler: {exc.message}", urgent=True)
            return
        self.result, self.failed_build = result, False
        for button in self.result_buttons:
            self.buttons.removeWidget(button)
            button.deleteLater()
        self.result_buttons = []
        if self.chat is not None:
            self.chat.setVisible(False)
        text = (f"Exe behalten, nicht geprüft: Ordner {result.exe.parent.parent.name}\\"
                f"{result.exe.parent.name}. Bitte starten Sie sie selbst und prüfen Sie sie.")
        self.ended(text)
        self._success_buttons()
        self.result_buttons[0].setFocus()

    def open_chat(self) -> None:
        from cockpit.ui.exe_chat import ExeChat
        if self.chat is None:
            self.chat = ExeChat(self.services, self.project.name, "Die Exe ist gebaut, hat den "
                                "Test aber nicht bestanden oder Windows hat ihn blockiert. Die "
                                "Ausgabe steht im Fenster.", self.error_text.splitlines, self,
                                self.branch_dir, self.build_settings.start_file)
            self.layout_.insertWidget(self.layout_.count() - 1, self.chat, 1)
        self.chat.setVisible(True)
        self.chat.question.setFocus()

    def reject(self) -> None:
        if self.running:
            self.stop()
            return
        FocusDialog.reject(self)

    def done(self, code: int) -> None:
        if self.chat is not None:
            self.chat.stop()
        if self.pending is not None:                   # nicht behalten: aufräumen
            exe.discard(self.pending)
            self.pending = None
        super().done(code)
