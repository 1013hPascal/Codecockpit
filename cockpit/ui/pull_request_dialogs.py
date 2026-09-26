"""Pull Requests ansehen, erstellen und kommentieren (Konzept 10.14, Teilschritt 6a).

PullRequestsDialog: oben die Auswahl "offene", "geschlossene" oder "alle", darunter die Liste, zum
Beispiel "Nr. 12: Suche in PDFs, von design nach main, von Anna, Entwurf". Enter zeigt die Details.
PullRequestDialog: Angaben, geänderte Dateien und Kommentare als Listen, dazu ein Feld zum
Kommentieren. Knöpfe: "Kommentar senden", "Zum Prüfen freigeben" (nur bei Entwürfen),
"Pull Request schließen …" oder "Wieder öffnen", "Im Browser öffnen".
CreatePullRequestDialog: Titel, Beschreibung, Ziel-Branch, Prüfer und "Als Entwurf erstellen".

Alles, was mit der Plattform spricht, läuft im Hintergrund. Rückfragen haben die sichere Antwort als
Vorgabe.
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
        details = QPushButton("&Details …")
        details.clicked.connect(self.show_details)
        new = QPushButton("&Neuer Pull Request …")
        new.clicked.connect(self.new_pull)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(filter_label)
        layout.addWidget(self.filter)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(details, new, None, close))
        self.setTabOrder(self.filter, self.list)
        self.resize(760, 440)
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
        if pull is None:
            return
        dialog = PullRequestDialog(self.platform, self.ref, pull, self.platform_name, self)
        dialog.exec()
        if dialog.changed:
            self.changed = True
            self.load(pull.number)
        self.list.setFocus()

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


class PullRequestDialog(FocusDialog):
    """Details, Dateien und Kommentare eines Pull Requests."""

    def __init__(self, platform, ref: RepoRef, pull: PullRequest, platform_name: str = "GitHub",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.platform = platform
        self.ref = ref
        self.pull = pull
        self.platform_name = platform_name
        self.changed = False
        self.worker = DialogWorker(self, f"Pull Request Nr. {pull.number}")
        self.setWindowTitle(pull_requests.pull_line(pull))
        self.info = QListWidget()
        name_widget(self.info, "Angaben")
        self.info.setWordWrap(True)
        self.files = QListWidget()
        files_label = label_for(self.files, "&Dateien:")
        self.comments = QListWidget()
        comments_label = label_for(self.comments, "&Kommentare:")
        self.comments.setWordWrap(True)
        self.edit = PlainEdit()
        edit_label = label_for(self.edit, "&Neuer Kommentar:")
        self.edit.setMaximumHeight(90)
        send = QPushButton("Kommentar &senden")
        send.clicked.connect(self.send_comment)
        self.ready_button = QPushButton("Zum &Prüfen freigeben")
        self.ready_button.clicked.connect(self.mark_ready)
        self.state_button = QPushButton()
        self.state_button.clicked.connect(self.toggle_state)
        browser = QPushButton("Im &Browser öffnen")
        browser.clicked.connect(self.open_browser)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        for widget in (self.info, self.files, self.comments):
            widget.installEventFilter(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.info, 2)
        layout.addWidget(files_label)
        layout.addWidget(self.files, 1)
        layout.addWidget(comments_label)
        layout.addWidget(self.comments, 2)
        layout.addWidget(edit_label)
        layout.addWidget(self.edit)
        layout.addLayout(button_row(send, self.ready_button, self.state_button, browser, None,
                                    close))
        self.resize(800, 640)
        self.initial_focus_widget = self.info
        self.fill_info()
        self.files.addItem("Wird geladen …")
        self.comments.addItem("Wird geladen …")
        self.load()

    def eventFilter(self, watched, event) -> bool:
        if watched in (self.info, self.files, self.comments) and _is_enter(event):
            return True
        return super().eventFilter(watched, event)

    def done(self, code: int) -> None:
        self.worker.wait()
        super().done(code)

    def fill_info(self) -> None:
        row = max(0, self.info.currentRow())
        self.info.clear()
        self.info.addItems(pull_requests.pull_details(self.pull))
        self.info.setCurrentRow(min(row, self.info.count() - 1))
        self.setWindowTitle(pull_requests.pull_line(self.pull))
        self.ready_button.setVisible(self.pull.draft and self.pull.state == "open")
        self.state_button.setVisible(self.pull.state != "merged")
        self.state_button.setText("Pull Request s&chließen …" if self.pull.state == "open"
                                  else "Wieder ö&ffnen")

    def load(self, then: str = "") -> None:
        platform, ref, number = self.platform, self.ref, self.pull.number

        def work():
            return (platform.pull_request(ref, number), platform.pull_request_files(ref, number),
                    platform.pull_request_comments(ref, number))

        def done(result) -> None:
            self.pull, files, comments = result
            self.fill_info()
            self.files.clear()
            self.files.addItems([pull_requests.file_line(f) for f in files]
                                or ["Keine Dateien geändert."])
            self.files.setCurrentRow(0)
            row = self.comments.currentRow()
            self.comments.clear()
            self.comments.addItems([pull_requests.comment_line(c) for c in comments]
                                   or ["Noch keine Kommentare."])
            self.comments.setCurrentRow(self.comments.count() - 1 if then else max(0, row))
            if then:
                announce(then)

        self.worker.run(work, done)

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

    def mark_ready(self) -> None:
        platform, ref, pull = self.platform, self.ref, self.pull
        if not confirm(self, "Zum Prüfen freigeben",
                       f"Der Entwurf Nr. {pull.number} wird zum Prüfen freigegeben. Die Prüfer "
                       "bekommen dann eine Nachricht von GitHub. Freigeben?",
                       yes="Freigeben", no="Abbrechen"):
            return

        def done(_value) -> None:
            self.changed = True
            self.info.setFocus()
            self.load("Zum Prüfen freigegeben.")

        self.worker.run(lambda: platform.mark_ready_for_review(ref, pull), done)

    def toggle_state(self) -> None:
        platform, ref, pull = self.platform, self.ref, self.pull
        closing = pull.state == "open"
        if closing and not confirm(
                self, "Pull Request schließen",
                f"Nr. {pull.number} wird geschlossen, ohne übernommen zu werden. Der Branch "
                f"{pull.head} bleibt erhalten. Sie können den Pull Request später wieder öffnen. "
                "Schließen?", yes="Schließen", no="Abbrechen"):
            return

        def done(_value) -> None:
            self.changed = True
            self.info.setFocus()
            self.load(f"Nr. {pull.number} ist geschlossen." if closing
                      else f"Nr. {pull.number} ist wieder offen.")

        self.worker.run(lambda: platform.set_pull_request_open(ref, pull.number, not closing),
                        done)

    def open_browser(self) -> None:
        if self.pull.url:
            browser_login_dialog.open_url(self.pull.url)
            announce("Wird im Browser geöffnet.")


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
