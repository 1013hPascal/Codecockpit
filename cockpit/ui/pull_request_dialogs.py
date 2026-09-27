"""Pull Requests ansehen, erstellen und kommentieren (Konzept 10.14, Teilschritt 6a).

PullRequestsDialog: oben die Auswahl "offene", "geschlossene" oder "alle", darunter die Liste, zum
Beispiel "Nr. 12: Suche in PDFs, von design nach main, von Anna, Entwurf". Nach dem Test von 6a
wirken alle Knöpfe direkt auf den markierten Pull Request: "Details …" (auch Enter),
"Kommentare …", "Zum Prüfen freigeben" (nur bei Entwürfen), "Pull Request schließen …" oder
"Wieder öffnen", "Neuer Pull Request …" und "Im Browser öffnen".
PullDetailsDialog: Angaben und geänderte Dateien. Enter auf einer Datei oder "Änderungen
ansehen …" zeigt ihre Änderungen lesbar: "Neu Zeile 12: …" und "Weg Zeile 8: …" (6b).
PullCommentsDialog: Kommentare und Reviews, darunter das Feld für einen neuen Kommentar.
ReviewDialog: Nur kommentieren, genehmigen oder Änderungen anfordern (6b).
MergeDialog: Art des Übernehmens: Merge-Commit, Squash oder Rebase (6b). Danach bietet die Liste
an, zu main zu wechseln, zu holen und den Branch aufzuräumen.
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
from cockpit.core.errors import CockpitError
from cockpit.core.text import count
from cockpit.platforms.base import PullRequest, RepoRef
from cockpit.ui import browser_login_dialog
from cockpit.ui.announcer import announce
from cockpit.ui.common import (FocusDialog, PlainEdit, ask_buttons, confirm, label_for,
                               make_copyable, name_widget)
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
                 parent: QWidget | None = None, summaries: dict[int, str] | None = None,
                 project=None, env: dict[str, str] | None = None, own_login: str = "") -> None:
        super().__init__(parent)
        self.platform = platform
        self.ref = ref
        self.address = address
        self.cache = cache
        self.pulls = pulls
        self.summaries = summaries or {}         # Nummer -> "1 Genehmigung"
        self.project = project                   # für das Aufräumen nach dem Übernehmen
        self.env = env or {}
        self.own_login = own_login
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
        self.review_button = QPushButton("&Prüfen …")
        self.review_button.clicked.connect(self.review_current)
        self.merge_button = QPushButton()
        self.merge_button.clicked.connect(self.merge_current)
        # Wunsch aus dem Test von 6b: Aufräumen geht auch später noch
        self.cleanup_button = QPushButton("Aufräu&men …")
        self.cleanup_button.clicked.connect(self.clean_up_current)
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
                                    self.review_button, self.merge_button, self.cleanup_button,
                                    self.state_button, new,
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
        self.setWindowTitle(f"Pull Requests von {self.ref.name}: "
                            f"{count(len(self.pulls), 'Pull Request', 'Pull Requests')}, {what}")
        self.list.clear()
        self.list.addItems([pull_requests.pull_line(p, self.summaries.get(p.number, ""))
                            for p in self.pulls]
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
        ready = pull is not None and pull.state == "open" and not pull.draft
        self.review_button.setVisible(ready)
        self.merge_button.setVisible(ready)
        self.cleanup_button.setVisible(pull is not None and pull.state == "merged"
                                       and self.project is not None
                                       and pull.head in self.local_branches())
        if pull is not None:
            self.merge_button.setText(f"In {pull.base.replace('&', '&&')} &übernehmen …")
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

        def work():
            pulls = platform.pull_requests(ref, state)
            return pulls, load_summaries(platform, ref, pulls)

        def done_both(result) -> None:
            pulls, self.summaries = result
            done(pulls)

        self.worker.run(work, done_both)

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

    # -- Prüfen und übernehmen (6b) --------------------------------------------------------------
    def review_current(self) -> None:
        pull = self.current()
        if pull is None:
            return
        own = bool(self.own_login) and pull.author.lower() == self.own_login.lower()
        dialog = ReviewDialog(pull, own, self)
        if not dialog.exec():
            return
        platform, ref = self.platform, self.ref
        said = {"APPROVE": f"Nr. {pull.number} genehmigt.",
                "REQUEST_CHANGES": f"Änderungen an Nr. {pull.number} angefordert.",
                "COMMENT": "Review abgegeben."}[dialog.verdict]

        def done(_value) -> None:
            self.changed = True
            self.list.setFocus()
            self.load(pull.number, said)

        self.worker.run(lambda: platform.submit_review(ref, pull.number, dialog.verdict,
                                                       dialog.body), done)

    def merge_current(self) -> None:
        pull = self.current()
        if pull is None:
            return
        platform, ref = self.platform, self.ref

        def ask(result) -> None:
            fresh, methods = result
            if not methods:
                show_error(self, "Übernehmen", "Das Repository erlaubt keine Art des Übernehmens. "
                           "Das stellt man auf GitHub in den Einstellungen des Repositories ein.")
                return
            dialog = MergeDialog(fresh, methods, self.summaries.get(fresh.number, ""), self)
            if not dialog.exec():
                return
            self.worker.run(lambda: platform.merge_pull_request(ref, fresh.number, dialog.method),
                            lambda _value: self.merged(fresh))

        self.worker.run(lambda: (platform.pull_request(ref, pull.number),
                                 platform.merge_methods(ref)), ask)

    def local_branches(self) -> set[str]:
        """Branches, die es hier oder auf der Plattform noch gibt (ohne Netz, schnell)."""
        if self.project is None:
            return set()
        from cockpit.core import git
        result = git.run(["for-each-ref", "--format=%(refname:lstrip=2)", "refs/heads",
                          "refs/remotes/origin"], self.project.code_dir, check=False)
        names = set()
        for name in result.stdout.split():
            names.add(name[len("origin/"):] if name.startswith("origin/") else name)
        return names

    def merged(self, pull: PullRequest) -> None:
        self.changed = True
        announce(f"Nr. {pull.number} ist in {pull.base} übernommen.")
        if self.project is None:
            self.load(pull.number)
            return
        self.offer_clean_up(pull, f"Nr. {pull.number} ist in {pull.base} übernommen. ")

    def clean_up_current(self) -> None:
        pull = self.current()
        if pull is not None:
            self.offer_clean_up(pull)

    def offer_clean_up(self, pull: PullRequest, before: str = "") -> None:
        choice = ask_buttons(self, "Aufräumen",
                             f"{before}Zu {pull.base} wechseln, die Änderungen holen und den "
                             f"Branch {pull.head} hier und auf {self.platform_name} löschen? Er "
                             "wird nicht mehr gebraucht.",
                             ["Aufräumen", "Später"], default=1, escape=1)
        if choice != 0:
            self.load(pull.number)
            return
        project, env = self.project, self.env

        def done(lines) -> None:
            self.list.setFocus()
            self.load(pull.number, " ".join(lines) or "Nichts aufzuräumen.")

        self.worker.run(lambda: pull_requests.clean_up(project.code_dir, project.name,
                                                       pull.head, env), done,
                        speak="Wird aufgeräumt.")

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
        make_copyable(self.info)
        self.files = QListWidget()
        files_label = label_for(self.files, "&Dateien:")
        self.changed_files: list = []
        changes = QPushButton("Änderungen &ansehen …")
        changes.clicked.connect(self.show_changes)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        for widget in (self.info, self.files):
            widget.installEventFilter(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.info, 2)
        layout.addWidget(files_label)
        layout.addWidget(self.files, 1)
        layout.addLayout(button_row(changes, None, close))
        self.resize(760, 520)
        self.initial_focus_widget = self.info
        self.info.addItems(pull_requests.pull_details(pull))
        self.info.setCurrentRow(0)
        self.files.addItem("Wird geladen …")
        self.load()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.files and _is_enter(event):
            self.show_changes()                       # Enter auf einer Datei (6b)
            return True
        if watched is self.info and _is_enter(event):
            return True
        return super().eventFilter(watched, event)

    def show_changes(self) -> None:
        from cockpit.ui.text_dialog import TextDialog
        row = self.files.currentRow()
        if not 0 <= row < len(self.changed_files):
            announce("Es gibt keine Datei.")
            return
        changed = self.changed_files[row]
        lines = pull_requests.diff_lines(changed.patch) or [
            "Keine Anzeige möglich, zum Beispiel bei einer Bilddatei oder einer sehr großen "
            "Änderung. Im Browser sehen Sie die Datei."]
        TextDialog(f"Änderungen in {changed.path}: {count(len(lines), 'Zeile', 'Zeilen')}",
                   lines, "Änderungen", self).exec()
        self.files.setFocus()

    def done(self, code: int) -> None:
        self.worker.wait()
        super().done(code)

    def load(self) -> None:
        platform, ref, number = self.platform, self.ref, self.pull.number

        def done(result) -> None:
            self.pull, files, reviews = result
            self.changed_files = files
            row = max(0, self.info.currentRow())
            self.info.clear()
            lines = pull_requests.pull_details(self.pull)
            extra = [pull_requests.summary_text(*pull_requests.review_summary(reviews)),
                     pull_requests.merge_state_text(self.pull)]
            lines[2:2] = [line for line in extra if line]
            self.info.addItems(lines)
            self.info.setCurrentRow(min(row, self.info.count() - 1))
            self.files.clear()
            self.files.addItems([pull_requests.file_line(f) for f in files]
                                or ["Keine Dateien geändert."])
            self.files.setCurrentRow(0)

        self.worker.run(lambda: (platform.pull_request(ref, number),
                                 platform.pull_request_files(ref, number),
                                 platform.reviews(ref, number)), done)


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


def load_summaries(platform, ref: RepoRef, pulls: list[PullRequest]) -> dict[int, str]:
    """Reviews der offenen Pull Requests zusammengefasst, zum Beispiel "1 Genehmigung". Im
    Hintergrund aufrufen. Höchstens 30, damit die Liste schnell kommt."""
    result: dict[int, str] = {}
    for pull in [p for p in pulls if p.state == "open"][:30]:
        try:
            text = pull_requests.summary_text(
                *pull_requests.review_summary(platform.reviews(ref, pull.number)))
        except (CockpitError, NotImplementedError):
            continue
        if text:
            result[pull.number] = text
    return result


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
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.methods = methods
        self.method = ""
        self.setWindowTitle(f"In {pull.base} übernehmen: Nr. {pull.number}: {pull.title}")
        info = QListWidget()
        name_widget(info, "Stand")
        lines = [f"Die Änderungen aus {pull.head} kommen in {pull.base}, auf "
                 "GitHub. Das lässt sich nicht einfach rückgängig machen."]
        lines += [line for line in (reviews, pull_requests.merge_state_text(pull)) if line]
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

