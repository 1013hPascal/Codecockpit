"""Pull Requests ansehen, erstellen und kommentieren (Konzept 10.14, Teilschritt 6a).

PullRequestsDialog: oben die Auswahl "offene", "geschlossene" oder "alle", darunter die Liste, zum
Beispiel "Nr. 12: Suche in PDFs, von design nach main, von Anna, Entwurf". Nach dem Test von 6a
wirken alle Knöpfe direkt auf den markierten Pull Request: "Details …" (auch Enter),
"Kommentare …", "Zum Prüfen freigeben" (nur bei Entwürfen), "Pull Request schließen …" oder
"Wieder öffnen", "Neuer Pull Request …" und "Im Browser öffnen".
PullDetailsDialog: Angaben und geänderte Dateien.
PullCommentsDialog: Kommentare, darunter das Feld für einen neuen Kommentar und "Kommentar senden".
CreatePullRequestDialog: Titel, Beschreibung, Ziel-Branch, Prüfer und "Als Entwurf erstellen".

Alles, was mit der Plattform spricht, läuft im Hintergrund. Rückfragen haben die sichere Antwort als
Vorgabe. Knöpfe, die für den markierten Eintrag nicht passen, erscheinen nicht.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QVBoxLayout, QWidget)

from cockpit.core import pull_requests
from cockpit.core.text import count
from cockpit.platforms.base import PullRequest, RepoRef
from cockpit.ui import browser_login_dialog
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, PlainEdit, confirm, label_for, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import DialogWorker, _is_enter, button_row

if TYPE_CHECKING:
    from cockpit.core.git import RemoteAddress

FILTERS = [("open", "offene"), ("closed", "geschlossene"), ("all", "alle")]
NO_TITLE = "Bitte geben Sie einen Titel ein."


class PullRequestsDialog(FocusDialog):
    """Liste der Pull Requests. changed: etwas wurde erstellt, kommentiert oder geschlossen."""

    def __init__(self, platform, ref: RepoRef, address: "RemoteAddress | None", cache,
                 pulls: list[PullRequest], create=None, platform_name: str = "GitHub",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.platform = platform
        self.ref = ref
        self.address = address
        self.cache = cache
        self.pulls = pulls
        self.create = create                     # startet "Neuer Pull Request …", None: keiner
        self.platform_name = platform_name
        self.changed = False
        self.worker = DialogWorker(self, "Pull Requests")
        self.filter = QComboBox()
        filter_label = label_for(self.filter, "&Anzeigen:")
        self.filter.addItems([text for _, text in FILTERS])
        self.filter.currentIndexChanged.connect(lambda _index: self.load())
        self.list = QListWidget()
        name_widget(self.list, "Pull Requests")
        self.list.installEventFilter(self)
        self.list.currentRowChanged.connect(lambda _row: self.update_buttons())
        self.details_button = QPushButton("&Details …")
        self.details_button.clicked.connect(self.show_details)
        self.comments_button = QPushButton("&Kommentare …")
        self.comments_button.clicked.connect(self.show_comments)
        self.ready_button = QPushButton("Zum &Prüfen freigeben")
        self.ready_button.clicked.connect(self.mark_ready)
        self.state_button = QPushButton()
        self.state_button.clicked.connect(self.toggle_state)
        new = QPushButton("&Neuer Pull Request …")
        new.clicked.connect(self.new_pull)
        self.browser_button = QPushButton("Im &Browser öffnen")
        self.browser_button.clicked.connect(self.open_browser)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(filter_label)
        layout.addWidget(self.filter)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(self.details_button, self.comments_button, self.ready_button,
                                    self.state_button, new, self.browser_button, None, close))
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
        self.setWindowTitle(f"Pull Requests von {self.ref.name}: "
                            f"{count(len(self.pulls), 'Pull Request', 'Pull Requests')}, {what}")
        self.list.clear()
        self.list.addItems([pull_requests.pull_line(p) for p in self.pulls]
                           or [f"Keine {what} Pull Requests." if self.state != "all"
                               else "Keine Pull Requests."])
        numbers = [p.number for p in self.pulls]
        if select in numbers:
            row = numbers.index(select)
        self.list.setCurrentRow(min(row, self.list.count() - 1))
        self.update_buttons()

    def update_buttons(self) -> None:
        """Nur, was zum markierten Pull Request passt, erscheint."""
        row = self.list.currentRow()
        pull = self.pulls[row] if 0 <= row < len(self.pulls) else None
        for button in (self.details_button, self.comments_button, self.browser_button):
            button.setVisible(pull is not None)
        self.ready_button.setVisible(pull is not None and pull.draft and pull.state == "open")
        self.state_button.setVisible(pull is not None and pull.state != "merged")
        if pull is not None:
            self.state_button.setText("Pull Request s&chließen …" if pull.state == "open"
                                      else "Wieder ö&ffnen")

    def load(self, select: int = 0, then: str = "") -> None:
        platform, ref, state = self.platform, self.ref, self.state

        def done(pulls) -> None:
            self.pulls = pulls
            if state == "open" and self.address is not None:
                self.cache.replace(self.address, pulls)
            self.fill(select)
            if then:
                announce(then)

        self.worker.run(lambda: platform.pull_requests(ref, state), done)

    def current(self) -> PullRequest | None:
        row = self.list.currentRow()
        if 0 <= row < len(self.pulls):
            return self.pulls[row]
        announce("Es gibt keinen Pull Request.")
        return None

    def show_details(self) -> None:
        pull = self.current()
        if pull is not None:
            PullDetailsDialog(self.platform, self.ref, pull, self).exec()
            self.list.setFocus()

    def show_comments(self) -> None:
        pull = self.current()
        if pull is None:
            return
        dialog = PullCommentsDialog(self.platform, self.ref, pull, self)
        dialog.exec()
        self.changed |= dialog.changed
        self.list.setFocus()

    def mark_ready(self) -> None:
        pull = self.current()
        if pull is None:
            return
        if not confirm(self, "Zum Prüfen freigeben",
                       f"Der Entwurf Nr. {pull.number} wird zum Prüfen freigegeben. Die Prüfer "
                       f"bekommen dann eine Nachricht von {self.platform_name}. Freigeben?",
                       yes="Freigeben", no="Abbrechen"):
            return
        platform, ref = self.platform, self.ref

        def done(_value) -> None:
            self.changed = True
            self.list.setFocus()
            self.load(pull.number, "Zum Prüfen freigegeben.")

        self.worker.run(lambda: platform.mark_ready_for_review(ref, pull), done)

    def toggle_state(self) -> None:
        pull = self.current()
        if pull is None:
            return
        closing = pull.state == "open"
        if closing and not confirm(
                self, "Pull Request schließen",
                f"Nr. {pull.number} wird geschlossen, ohne übernommen zu werden. Der Branch "
                f"{pull.head} bleibt erhalten. Sie können den Pull Request später wieder öffnen. "
                "Schließen?", yes="Schließen", no="Abbrechen"):
            return
        platform, ref = self.platform, self.ref

        def done(_value) -> None:
            self.changed = True
            self.list.setFocus()
            self.load(pull.number, f"Nr. {pull.number} ist geschlossen." if closing
                      else f"Nr. {pull.number} ist wieder offen.")

        self.worker.run(lambda: platform.set_pull_request_open(ref, pull.number, not closing),
                        done)

    def open_browser(self) -> None:
        pull = self.current()
        if pull is not None and pull.url:
            browser_login_dialog.open_url(pull.url)
            announce("Wird im Browser geöffnet.")

    def new_pull(self) -> None:
        if self.create is None:
            show_error(self, "Neuer Pull Request",
                       "Ein Pull Request braucht einen Branch mit Ihren Änderungen. Wechseln Sie "
                       "zuerst zu diesem Branch, zum Beispiel in der Übersicht Branches.")
            return

        def created(pull: PullRequest) -> None:
            self.changed = True
            if self.isVisible():
                self.filter.blockSignals(True)
                self.filter.setCurrentIndex(0)
                self.filter.blockSignals(False)
                self.load(pull.number)
                self.list.setFocus()

        self.create(self, created)            # läuft im Hintergrund weiter


class PullDetailsDialog(FocusDialog):
    """Angaben und geänderte Dateien eines Pull Requests."""

    def __init__(self, platform, ref: RepoRef, pull: PullRequest,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.platform = platform
        self.ref = ref
        self.pull = pull
        self.worker = DialogWorker(self, f"Pull Request Nr. {pull.number}")
        self.setWindowTitle(f"Details: {pull_requests.pull_line(pull)}")
        self.info = QListWidget()
        name_widget(self.info, "Angaben")
        self.info.setWordWrap(True)
        self.files = QListWidget()
        files_label = label_for(self.files, "&Dateien:")
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        for widget in (self.info, self.files):
            widget.installEventFilter(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.info, 2)
        layout.addWidget(files_label)
        layout.addWidget(self.files, 1)
        layout.addLayout(button_row(None, close))
        self.resize(760, 520)
        self.initial_focus_widget = self.info
        self.info.addItems(pull_requests.pull_details(pull))
        self.info.setCurrentRow(0)
        self.files.addItem("Wird geladen …")
        self.load()

    def eventFilter(self, watched, event) -> bool:
        if watched in (self.info, self.files) and _is_enter(event):
            return True
        return super().eventFilter(watched, event)

    def done(self, code: int) -> None:
        self.worker.wait()
        super().done(code)

    def load(self) -> None:
        platform, ref, number = self.platform, self.ref, self.pull.number

        def done(result) -> None:
            self.pull, files = result
            row = max(0, self.info.currentRow())
            self.info.clear()
            self.info.addItems(pull_requests.pull_details(self.pull))
            self.info.setCurrentRow(min(row, self.info.count() - 1))
            self.files.clear()
            self.files.addItems([pull_requests.file_line(f) for f in files]
                                or ["Keine Dateien geändert."])
            self.files.setCurrentRow(0)

        self.worker.run(lambda: (platform.pull_request(ref, number),
                                 platform.pull_request_files(ref, number)), done)


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

        def done(comments) -> None:
            self.comments.clear()
            self.comments.addItems([pull_requests.comment_line(c) for c in comments]
                                   or ["Noch keine Kommentare."])
            # Neueste unten; nach dem Senden steht der Fokus auf dem eigenen Kommentar
            self.comments.setCurrentRow(self.comments.count() - 1 if then else 0)
            if then:
                announce(then)

        self.worker.run(lambda: platform.pull_request_comments(ref, number), done)

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
                 people: list[str], note: str = "", parent: QWidget | None = None) -> None:
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
        for widget in (title_label, self.title_edit, body_label, self.body_edit, base_label,
                       self.base_box, people_label, self.people, self.draft_box):
            layout.addWidget(widget)
        layout.addLayout(button_row(None, ok, cancel))
        self.resize(640, 560)
        self.initial_focus_widget = self.title_edit

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
