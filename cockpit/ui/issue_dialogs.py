"""Issues lesen, anlegen, kommentieren, schließen, mit Labels und Zuweisen (Wunsch des Nutzers vom
21.10.2026). Alles geht ohne KI. Ist der KI-Assistent im Projekt aktiv, gibt es dazu "Mit KI
zusammenfassen": Die KI fasst das Issue zusammen und schlägt einen Branch-Namen vor.

IssuesDialog: oben "offene", "geschlossene" oder "alle", darunter die Liste, zum Beispiel "Nr. 12:
Suche in PDFs, von Anna, Fehler, zugewiesen an Ben, 3 Kommentare". Die Knöpfe wirken auf das
markierte Issue. Enter öffnet die Details.
IssueDetailsDialog: Angaben, Kommentare und das Feld für einen neuen Kommentar.
CreateIssueDialog: Titel, Beschreibung, Labels und Personen.

Alles, was mit der Plattform spricht, läuft im Hintergrund.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QComboBox, QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import issues
from cockpit.core.text import count
from cockpit.platforms.base import Issue, RepoRef
from cockpit.ui import browser_login_dialog
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, PlainEdit, confirm, label_for, make_copyable, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import DialogWorker, _is_enter, button_row

FILTERS = [("open", "offene"), ("closed", "geschlossene"), ("all", "alle")]
NO_TITLE = "Bitte geben Sie einen Titel ein."
AI_BUTTON = "Mit &KI zusammenfassen"


class IssuesDialog(FocusDialog):
    """Liste der Issues. changed: etwas wurde angelegt, kommentiert oder geändert."""

    def __init__(self, platform, ref: RepoRef, found: list[Issue], labels: list[str],
                 people: list[str], parent: QWidget | None = None,
                 ai_source: Callable | None = None,
                 create_branch: Callable[[str], None] | None = None, code_dir=None) -> None:
        """ai_source(load) gibt die Quelle für die KI oder None. create_branch(name) legt den
        Branch an, None: kein Knopf. code_dir: zum Prüfen des Branch-Namens."""
        super().__init__(parent)
        self.code_dir = code_dir
        self.platform = platform
        self.ref = ref
        self.issues = found
        self.labels = labels
        self.people = people
        self.ai_source = ai_source
        self.create_branch = create_branch
        self.suggested: dict[int, str] = {}           # Nummer -> Branch-Name von der KI
        self.changed = False
        self.worker = DialogWorker(self, "Issues")
        self.filter = QComboBox()
        filter_label = label_for(self.filter, "&Anzeigen:")
        self.filter.addItems([text for _, text in FILTERS])
        self.filter.currentIndexChanged.connect(lambda _index: self.load())
        self.list = QListWidget()
        name_widget(self.list, "Issues")
        self.list.installEventFilter(self)
        self.list.currentRowChanged.connect(lambda _row: self.update_buttons())
        self.details_button = QPushButton("&Details …")
        self.details_button.clicked.connect(self.show_details)
        new = QPushButton("&Neues Issue …")
        new.clicked.connect(self.new_issue)
        self.labels_button = QPushButton("&Labels …")
        self.labels_button.clicked.connect(self.edit_labels)
        self.assign_button = QPushButton("&Zuweisen …")
        self.assign_button.clicked.connect(self.edit_assignees)
        self.branch_button = QPushButton("Branch dafür anle&gen …")
        self.branch_button.clicked.connect(self.branch_for_current)
        self.state_button = QPushButton()
        self.state_button.clicked.connect(self.toggle_state)
        self.browser_button = QPushButton("Im &Browser öffnen")
        self.browser_button.clicked.connect(self.open_browser)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(filter_label)
        layout.addWidget(self.filter)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(self.details_button, new, self.labels_button,
                                    self.assign_button, self.branch_button, self.state_button,
                                    self.browser_button, None, close))
        self.setTabOrder(self.filter, self.list)
        self.resize(820, 440)
        self.initial_focus_widget = self.list
        self.fill()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            self.show_details()
            return True
        return super().eventFilter(watched, event)

    def done(self, code: int) -> None:
        self.worker.wait()
        super().done(code)

    @property
    def state(self) -> str:
        return FILTERS[self.filter.currentIndex()][0]

    def fill(self, select: int = 0) -> None:
        row = max(0, self.list.currentRow())
        what = FILTERS[self.filter.currentIndex()][1]
        self.setWindowTitle(f"Issues von {self.ref.name}: "
                            f"{count(len(self.issues), 'Issue', 'Issues')}, {what}")
        self.list.clear()
        self.list.addItems([issues.issue_line(i) for i in self.issues]
                           or [f"Keine {what} Issues." if self.state != "all"
                               else "Keine Issues."])
        numbers = [i.number for i in self.issues]
        if select in numbers:
            row = numbers.index(select)
        self.list.setCurrentRow(min(row, self.list.count() - 1))
        self.update_buttons()

    def update_buttons(self) -> None:
        found = self.current(quiet=True)
        for button in (self.details_button, self.labels_button, self.assign_button,
                       self.state_button, self.browser_button):
            button.setVisible(found is not None)
        self.branch_button.setVisible(found is not None and found.state == "open"
                                      and self.create_branch is not None)
        if found is not None:
            self.state_button.setText("Issue s&chließen …" if found.state == "open"
                                      else "Wieder ö&ffnen")

    def current(self, quiet: bool = False) -> Issue | None:
        row = self.list.currentRow()
        if 0 <= row < len(self.issues):
            return self.issues[row]
        if not quiet:
            announce("Es gibt kein Issue.")
        return None

    def load(self, select: int = 0, then: str = "") -> None:
        platform, ref, state = self.platform, self.ref, self.state

        def done(found) -> None:
            self.issues = found
            self.fill(select)
            if then:
                announce(then)

        self.worker.run(lambda: platform.issues(ref, state), done)

    # -- Knöpfe ----------------------------------------------------------------------------------
    def show_details(self) -> None:
        found = self.current()
        if found is None:
            return
        dialog = IssueDetailsDialog(self.platform, self.ref, found, self, self.ai_source)
        dialog.exec()
        if dialog.branch_suggestion:
            self.suggested[found.number] = dialog.branch_suggestion
        if dialog.changed:
            self.changed = True
            self.load(found.number)
        self.list.setFocus()

    def new_issue(self) -> None:
        dialog = CreateIssueDialog(self.labels, self.people, self)
        if not dialog.exec():
            return
        platform, ref = self.platform, self.ref

        def done(created: Issue) -> None:
            self.changed = True
            self.filter.blockSignals(True)
            self.filter.setCurrentIndex(0)
            self.filter.blockSignals(False)
            self.list.setFocus()
            self.load(created.number, f"Issue Nr. {created.number} angelegt.")

        self.worker.run(lambda: platform.create_issue(ref, dialog.title, dialog.body,
                                                      dialog.chosen_labels,
                                                      dialog.chosen_people), done)

    def _choose(self, title: str, label: str, items: list[str], checked) -> list[str] | None:
        from cockpit.ui.sync_dialogs import CheckListDialog
        if not items:
            announce(f"Im Repository gibt es keine {title}.")
            return None
        dialog = CheckListDialog(title, label, items, set(checked), self)
        return dialog.chosen if dialog.exec() else None

    def edit_labels(self) -> None:
        found = self.current()
        if found is None:
            return
        chosen = self._choose("Labels", "&Labels:", self.labels, found.labels)
        if chosen is None:
            return
        platform, ref = self.platform, self.ref
        said = f"Labels: {', '.join(chosen)}." if chosen else "Keine Labels mehr."
        self.worker.run(lambda: platform.set_issue_labels(ref, found.number, tuple(chosen)),
                        lambda _v: self._after_change(found.number, said))

    def edit_assignees(self) -> None:
        found = self.current()
        if found is None:
            return
        chosen = self._choose("Personen", "&Personen:", self.people, found.assignees)
        if chosen is None:
            return
        platform, ref = self.platform, self.ref
        said = (f"Zugewiesen an {', '.join(chosen)}." if chosen
                else "Niemandem mehr zugewiesen.")
        self.worker.run(lambda: platform.set_issue_assignees(ref, found.number, tuple(chosen)),
                        lambda _v: self._after_change(found.number, said))

    def _after_change(self, number: int, said: str) -> None:
        self.changed = True
        self.list.setFocus()
        self.load(number, said)

    def toggle_state(self) -> None:
        found = self.current()
        if found is None:
            return
        closing = found.state == "open"
        if closing and not confirm(self, "Issue schließen",
                                   f"Nr. {found.number} wird geschlossen. Sie können es später "
                                   "wieder öffnen. Schließen?", yes="Schließen", no="Abbrechen"):
            return
        platform, ref = self.platform, self.ref
        said = (f"Nr. {found.number} ist geschlossen." if closing
                else f"Nr. {found.number} ist wieder offen.")
        self.worker.run(lambda: platform.set_issue_open(ref, found.number, not closing),
                        lambda _v: self._after_change(found.number, said))

    def branch_for_current(self) -> None:
        from cockpit.ui.branch_dialogs import BranchNameDialog
        found = self.current()
        if found is None or self.create_branch is None:
            return
        name = self.suggested.get(found.number) or issues.branch_name(found)
        dialog = BranchNameDialog("Branch für das Issue",
                                  f"Für Nr. {found.number}: {found.title}. Der Name ist ein "
                                  "Vorschlag, Sie können ihn ändern.", self.code_dir, name, self)
        if dialog.exec():
            self.create_branch(dialog.name)

    def open_browser(self) -> None:
        found = self.current()
        if found is not None and found.url:
            browser_login_dialog.open_url(found.url)
            announce("Wird im Browser geöffnet.")


class IssueDetailsDialog(FocusDialog):
    """Angaben und Kommentare. changed: ein Kommentar wurde gesendet. branch_suggestion: der
    Branch-Name, den die KI vorgeschlagen hat."""

    def __init__(self, platform, ref: RepoRef, found: Issue, parent: QWidget | None = None,
                 ai_source: Callable | None = None) -> None:
        super().__init__(parent)
        self.platform = platform
        self.ref = ref
        self.issue = found
        self.changed = False
        self.branch_suggestion = ""
        self.comment_items: list = []
        self.worker = DialogWorker(self, f"Issue Nr. {found.number}")
        self.setWindowTitle(f"Issue {issues.issue_line(found)}")
        self.info = QListWidget()
        name_widget(self.info, "Angaben")
        self.info.setWordWrap(True)
        make_copyable(self.info)
        self.info.addItems(issues.issue_details(found))
        self.info.setCurrentRow(0)
        self.comments = QListWidget()
        comments_label = label_for(self.comments, "K&ommentare:")
        self.comments.setWordWrap(True)
        make_copyable(self.comments)
        self.edit = PlainEdit()
        edit_label = label_for(self.edit, "&Neuer Kommentar:")
        self.edit.setMaximumHeight(110)
        send = QPushButton("Kommentar &senden")
        send.clicked.connect(self.send_comment)
        self.ai_button = None
        source = ai_source(self.loaded) if ai_source is not None else None
        if source is not None:
            from cockpit.ui.ai_suggest import SuggestButton
            self.ai_button = SuggestButton(self, source, self.apply_summary, self.info)
            self.ai_button.setText(AI_BUTTON)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        for widget in (self.info, self.comments):
            widget.installEventFilter(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.info, 2)
        layout.addWidget(comments_label)
        layout.addWidget(self.comments, 2)
        layout.addWidget(edit_label)
        layout.addWidget(self.edit)
        layout.addLayout(button_row(send, self.ai_button, None, close))
        self.resize(780, 560)
        self.initial_focus_widget = self.info
        self.comments.addItem("Wird geladen …")
        self.load()

    def eventFilter(self, watched, event) -> bool:
        if watched in (self.info, self.comments) and _is_enter(event):
            return True
        return super().eventFilter(watched, event)

    def reject(self) -> None:
        from cockpit.ui.ai_suggest import handle_escape
        if not handle_escape(self.ai_button):
            super().reject()

    def done(self, code: int) -> None:
        if self.ai_button is not None:
            self.ai_button.wait()
        self.worker.wait()
        super().done(code)

    def loaded(self) -> tuple:
        """Für die KI, im Hintergrund: das Issue und seine Kommentare, frisch gelesen."""
        return (self.platform.issue(self.ref, self.issue.number),
                self.platform.issue_comments(self.ref, self.issue.number))

    def load(self, then: str = "") -> None:
        platform, ref, number = self.platform, self.ref, self.issue.number

        def done(found) -> None:
            self.comment_items = found
            self.comments.clear()
            self.comments.addItems([issues.comment_line(c) for c in found]
                                   or ["Noch keine Kommentare."])
            self.comments.setCurrentRow(self.comments.count() - 1 if then else 0)
            if then:
                announce(then)

        self.worker.run(lambda: platform.issue_comments(ref, number), done)

    def apply_summary(self, suggestion) -> None:
        """Die Zusammenfassung der KI steht oben in den Angaben, der Branch-Name darunter."""
        self.branch_suggestion = suggestion.summary
        lines = [f"Zusammenfassung der KI: {' '.join(suggestion.details.split())}"
                 if suggestion.details else "",
                 f"Vorgeschlagener Branch: {suggestion.summary}"]
        for offset, line in enumerate(line for line in lines if line):
            self.info.insertItem(1 + offset, line)
        self.info.setCurrentRow(1)

    def send_comment(self) -> None:
        text = self.edit.toPlainText().strip()
        if not text:
            show_error(self, "Kommentar", "Bitte schreiben Sie zuerst einen Kommentar.")
            self.edit.setFocus()
            return
        platform, ref, number = self.platform, self.ref, self.issue.number

        def done(_value) -> None:
            self.changed = True
            self.edit.clear()
            self.comments.setFocus()
            self.load("Kommentar gesendet.")

        self.worker.run(lambda: platform.add_issue_comment(ref, number, text), done)


class CreateIssueDialog(FocusDialog):
    """Neues Issue. Nach accept() stehen die Angaben in title, body, chosen_labels und
    chosen_people."""

    def __init__(self, labels: list[str], people: list[str],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.labels = labels
        self.people = people
        self.title = self.body = ""
        self.chosen_labels: tuple[str, ...] = ()
        self.chosen_people: tuple[str, ...] = ()
        self.setWindowTitle("Neues Issue")
        self.title_edit = QLineEdit()
        title_label = label_for(self.title_edit, "&Titel:")
        self.body_edit = PlainEdit()
        body_label = label_for(self.body_edit, "&Beschreibung:")
        self.labels_button = QPushButton("&Labels …")
        self.labels_button.clicked.connect(self.choose_labels)
        self.labels_button.setVisible(bool(labels))
        self.people_button = QPushButton("&Zuweisen …")
        self.people_button.clicked.connect(self.choose_people)
        self.people_button.setVisible(bool(people))
        ok = QPushButton("&Anlegen")
        ok.setDefault(True)
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        for widget in (title_label, self.title_edit, body_label, self.body_edit):
            layout.addWidget(widget)
        layout.addLayout(button_row(self.labels_button, self.people_button, None, ok, cancel))
        self.resize(640, 420)
        self.initial_focus_widget = self.title_edit

    def _choose(self, title: str, label: str, items: list[str], checked) -> tuple | None:
        from cockpit.ui.sync_dialogs import CheckListDialog
        dialog = CheckListDialog(title, label, items, set(checked), self)
        return tuple(dialog.chosen) if dialog.exec() else None

    def choose_labels(self) -> None:
        chosen = self._choose("Labels", "&Labels:", self.labels, self.chosen_labels)
        if chosen is not None:
            self.chosen_labels = chosen
            self.labels_button.setText(f"&Labels ({len(chosen)}) …" if chosen else "&Labels …")
            announce(f"{count(len(chosen), 'Label', 'Labels')} gewählt.")

    def choose_people(self) -> None:
        chosen = self._choose("Personen", "&Personen:", self.people, self.chosen_people)
        if chosen is not None:
            self.chosen_people = chosen
            self.people_button.setText(f"&Zuweisen ({len(chosen)}) …" if chosen
                                       else "&Zuweisen …")
            announce(f"{count(len(chosen), 'Person', 'Personen')} gewählt.")

    def check(self) -> None:
        title = " ".join(self.title_edit.text().split())
        if not title:
            show_error(self, "Neues Issue", NO_TITLE)
            self.title_edit.setFocus()
            return
        self.title = title
        self.body = self.body_edit.toPlainText().strip()
        self.accept()
