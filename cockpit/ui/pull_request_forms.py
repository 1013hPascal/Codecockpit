"""Pull Request anlegen, kommentieren, prüfen und übernehmen.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout,
    QWidget)

from cockpit.core import pull_requests
from cockpit.platforms.base import PullRequest, RepoRef
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, PlainEdit, label_for, make_copyable, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import DialogWorker, _is_enter, button_row


NO_TITLE = "Bitte geben Sie einen Titel ein."


class PullCommentsDialog(FocusDialog):
    """Kommentare lesen und schreiben. changed: ein Kommentar wurde gesendet."""

    def __init__(self, platform, ref: RepoRef, pull: PullRequest,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.platform = platform
        self.ref = ref
        self.pull = pull
        self.changed = False
        self.worker = DialogWorker(self, f"Pull Request Nr. {pull.number}")
        self.setWindowTitle(f"Kommentare: Nr. {pull.number}: {pull.title}")
        self.comments = QListWidget()
        name_widget(self.comments, "Kommentare")
        make_copyable(self.comments)
        self.comments.setWordWrap(True)
        self.comments.installEventFilter(self)
        self.edit = PlainEdit()
        edit_label = label_for(self.edit, "&Neuer Kommentar:")
        self.edit.setMaximumHeight(110)
        send = QPushButton("Kommentar &senden")
        send.clicked.connect(self.send_comment)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.comments, 1)
        layout.addWidget(edit_label)
        layout.addWidget(self.edit)
        layout.addLayout(button_row(send, None, close))
        self.resize(760, 480)
        self.initial_focus_widget = self.comments
        self.comments.addItem("Wird geladen …")
        self.load()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.comments and _is_enter(event):
            return True
        return super().eventFilter(watched, event)

    def done(self, code: int) -> None:
        self.worker.wait()
        super().done(code)

    def load(self, then: str = "") -> None:
        platform, ref, number = self.platform, self.ref, self.pull.number

        def done(result) -> None:
            comments, reviews = result
            entries = [(c.created, pull_requests.comment_line(c)) for c in comments]
            entries += [(r.submitted, pull_requests.review_line(r)) for r in reviews]
            lines = [text for _, text in sorted(entries, key=lambda e: e[0]) if text]
            self.comments.clear()
            self.comments.addItems(lines or ["Noch keine Kommentare."])
            # Neueste unten; nach dem Senden steht der Fokus auf dem eigenen Kommentar
            self.comments.setCurrentRow(self.comments.count() - 1 if then else 0)
            if then:
                announce(then)

        self.worker.run(lambda: (platform.pull_request_comments(ref, number),
                                 platform.reviews(ref, number)), done)

    def send_comment(self) -> None:
        text = self.edit.toPlainText().strip()
        if not text:
            show_error(self, "Kommentar", "Bitte schreiben Sie zuerst einen Kommentar.")
            self.edit.setFocus()
            return
        platform, ref, number = self.platform, self.ref, self.pull.number

        def done(_value) -> None:
            self.changed = True
            self.edit.clear()
            self.comments.setFocus()
            self.load("Kommentar gesendet.")

        self.worker.run(lambda: platform.add_pull_request_comment(ref, number, text), done)


class CreatePullRequestDialog(FocusDialog):
    """Neuer Pull Request. Nach accept() stehen die Angaben in title, body, base, reviewers und
    draft."""

    def __init__(self, head: str, bases: list[str], default_base: str, title: str, body: str,
                 people: list[str], note: str = "", parent: QWidget | None = None,
                 source=None) -> None:
        """source: Vorschlag der KI (Feature KI-Assistent), None: kein Knopf."""
        super().__init__(parent)
        self.head = head
        self.bases = bases
        self.title = self.body = self.base = ""
        self.reviewers: tuple[str, ...] = ()
        self.draft = False
        self.setWindowTitle(f"Pull Request erstellen: von {head}")
        self.title_edit = QLineEdit(title)
        title_label = label_for(self.title_edit, "&Titel:")
        self.body_edit = PlainEdit()
        self.body_edit.setPlainText(body)
        body_label = label_for(self.body_edit, "&Beschreibung:")
        self.base_box = QComboBox()
        base_label = label_for(self.base_box, f"&Ziel-Branch, dahin sollen die Änderungen aus "
                                              f"{head}:")
        self.base_box.addItems(bases)
        if default_base in bases:
            self.base_box.setCurrentIndex(bases.index(default_base))
        self.people = QListWidget()
        people_label = label_for(self.people, "&Prüfer, freiwillig:")
        self.people_names = people
        for login in people:
            item = QListWidgetItem(login)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.people.addItem(item)
        if not people:
            self.people.addItem("Keine Mitarbeiter, die prüfen könnten.")
        self.people.setCurrentRow(0)
        self.people.setMaximumHeight(100)
        self.people.installEventFilter(self)
        self.draft_box = QCheckBox("Als &Entwurf erstellen")
        ok = QPushButton("&Erstellen")
        ok.setDefault(True)
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        if note:
            hint = QListWidget()
            name_widget(hint, "Hinweis")
            hint.addItem(note)
            hint.setMaximumHeight(50)
            hint.setWordWrap(True)
            layout.addWidget(hint)
        for widget in (title_label, self.title_edit, body_label, self.body_edit):
            layout.addWidget(widget)
        self.suggest_button = None
        if source is not None:
            from cockpit.ui.ai_suggest import SuggestButton
            self.suggest_button = SuggestButton(self, source, self.apply_suggestion,
                                                self.title_edit)
            layout.addLayout(button_row(self.suggest_button, None))
        for widget in (base_label, self.base_box, people_label, self.people, self.draft_box):
            layout.addWidget(widget)
        layout.addLayout(button_row(None, ok, cancel))
        order = [self.title_edit, self.body_edit, self.suggest_button, self.base_box,
                 self.people, self.draft_box, ok, cancel]
        order = [w for w in order if w is not None]
        for first, second in zip(order, order[1:]):
            self.setTabOrder(first, second)
        self.resize(640, 580)
        self.initial_focus_widget = self.title_edit

    def apply_suggestion(self, suggestion) -> None:
        self.title_edit.setText(suggestion.summary)
        self.body_edit.setPlainText(suggestion.details)

    def reject(self) -> None:
        from cockpit.ui.ai_suggest import handle_escape
        if not handle_escape(self.suggest_button):
            super().reject()

    def done(self, code: int) -> None:
        if self.suggest_button is not None:
            self.suggest_button.wait()
        super().done(code)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.people and _is_enter(event):
            return True
        return super().eventFilter(watched, event)

    def check(self) -> None:
        title = " ".join(self.title_edit.text().split())
        if not title:
            show_error(self, self.windowTitle(), NO_TITLE)
            self.title_edit.setFocus()
            return
        base = self.base_box.currentText()
        if base == self.head:
            show_error(self, self.windowTitle(), f"Ziel und Branch sind beide {base}. Wählen Sie "
                       "als Ziel einen anderen Branch.")
            self.base_box.setFocus()
            return
        self.title, self.base = title, base
        self.body = self.body_edit.toPlainText().strip()
        self.reviewers = tuple(self.people_names[row] for row in range(len(self.people_names))
                               if self.people.item(row).checkState() == Qt.CheckState.Checked)
        self.draft = self.draft_box.isChecked()
        self.accept()


class ReviewDialog(FocusDialog):
    """Review abgeben. Nach accept() stehen die Angaben in verdict und body."""

    def __init__(self, pull: PullRequest, own: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.verdict = "COMMENT"
        self.body = ""
        self.events = [e for e in pull_requests.REVIEW_EVENTS if not own or e[0] == "COMMENT"]
        self.setWindowTitle(f"Prüfen: Nr. {pull.number}: {pull.title}")
        self.choice = QComboBox()
        choice_label = label_for(self.choice, "&Ergebnis:")
        self.choice.addItems([text for _, text in self.events])
        self.edit = PlainEdit()
        edit_label = label_for(self.edit, "&Kommentar zum Review:")
        ok = QPushButton("Review &abgeben")
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        if own:
            hint = QListWidget()
            name_widget(hint, "Hinweis")
            hint.addItem("Das ist Ihr eigener Pull Request. Genehmigen und Änderungen anfordern "
                         "erlaubt GitHub dann nicht, nur einen Kommentar.")
            hint.setWordWrap(True)
            hint.setMaximumHeight(60)
            layout.addWidget(hint)
        for widget in (choice_label, self.choice, edit_label, self.edit):
            layout.addWidget(widget)
        layout.addLayout(button_row(None, ok, cancel))
        self.resize(560, 360)
        self.initial_focus_widget = self.choice

    def check(self) -> None:
        event = self.events[self.choice.currentIndex()][0]
        body = self.edit.toPlainText().strip()
        if event != "APPROVE" and not body:
            show_error(self, self.windowTitle(), "Bitte schreiben Sie dazu einen Kommentar. Nur "
                       "beim Genehmigen darf er fehlen.")
            self.edit.setFocus()
            return
        self.verdict, self.body = event, body
        self.accept()


class MergeDialog(FocusDialog):
    """Art des Übernehmens wählen. Vorgabe beim Knopf ist "Abbrechen". method nach accept()."""

    def __init__(self, pull: PullRequest, methods: list[str], reviews: str = "",
                 parent: QWidget | None = None, checks: str = "") -> None:
        super().__init__(parent)
        self.methods = methods
        self.method = ""
        self.setWindowTitle(f"In {pull.base} übernehmen: Nr. {pull.number}: {pull.title}")
        info = QListWidget()
        name_widget(info, "Stand")
        lines = [f"Die Änderungen aus {pull.head} kommen in {pull.base}, auf "
                 "GitHub. Das lässt sich nicht einfach rückgängig machen."]
        # Fehlgeschlagene Checks stehen gleich nach dem ersten Satz (21.10.2026)
        lines += [line for line in (checks, reviews, pull_requests.merge_state_text(pull))
                  if line]
        info.addItems(lines)
        info.setCurrentRow(0)
        info.setWordWrap(True)
        info.setMaximumHeight(110)
        self.choice = QComboBox()
        choice_label = label_for(self.choice, "&Art des Übernehmens:")
        self.choice.addItems([pull_requests.METHOD_TEXTS[m] for m in methods])
        ok = QPushButton("&Übernehmen")
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.setDefault(True)
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        for widget in (info, choice_label, self.choice):
            layout.addWidget(widget)
        layout.addLayout(button_row(None, ok, cancel))
        self.resize(620, 300)
        self.initial_focus_widget = info

    def check(self) -> None:
        self.method = self.methods[self.choice.currentIndex()]
        self.accept()
