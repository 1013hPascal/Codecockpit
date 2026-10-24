"""Eine Version ansehen und den Verlauf ändern: umsortieren, nachbessern, verwerfen, hochladen.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget)
from pathlib import Path

from cockpit.core import history, rewrite
from cockpit.core.errors import CockpitError
from cockpit.core.history import Commit, LocalChange
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, label_for, make_copyable, name_widget
from cockpit.ui.error_dialog import show_error


NO_CHOICE = "Bitte wählen Sie mit der Leertaste mindestens eine Datei aus."


BACKUP_NOTE = "Vorher kommen die betroffenen Dateien als Sicherheitskopie in den Ordner backups."


def _ignore_enter(dialog: FocusDialog, watched, event, lists) -> bool:
    from PySide6.QtCore import QEvent
    return (watched in lists and event.type() == QEvent.Type.KeyPress
            and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter))


class VersionDialog(FocusDialog):
    def __init__(self, services: "Services", project: "Project", commit: Commit,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.project = project
        self.commit = commit
        self.code_dir: Path = project.code_dir
        self.files_changed = False
        self.history_changed = False
        self.changes = history.commit_files(self.code_dir, commit)
        self.paths = [line.rpartition(", ")[0] for line in self.changes.lines()]
        self.setWindowTitle(commit.line())
        steps = history.recorded_steps(services.database, project.id, commit.sha)
        self.info = QListWidget()
        name_widget(self.info, "Angaben")
        make_copyable(self.info)
        self.info.addItems(history.details(commit, steps))
        self.info.setCurrentRow(0)
        self.info.setWordWrap(True)
        self.files = QListWidget()
        files_label = label_for(self.files, f"&Dateien, {self.changes.summary()}:")
        self.files.addItems(self.changes.lines() or ["Keine Dateien geändert."])
        self.files.setCurrentRow(0)
        buttons = QHBoxLayout()
        restore = QPushButton("Datei &wiederherstellen …")
        restore.clicked.connect(self.restore_current)
        revert = QPushButton("Version &rückgängig machen …")
        revert.clicked.connect(self.revert)
        buttons.addWidget(restore)
        buttons.addWidget(revert)
        self.undo_button = None
        self.amend_button = None
        if history.can_undo(commit):
            self.undo_button = QPushButton("Commit &zurücknehmen …")
            self.undo_button.clicked.connect(self.undo)
            buttons.addWidget(self.undo_button)
        # Vergleich mit GitHub Desktop (21.10.2026): nachbessern, übernehmen, Branch ab hier
        if rewrite.can_amend(commit):
            self.amend_button = QPushButton("Commit &nachbessern …")
            self.amend_button.clicked.connect(self.amend)
            buttons.addWidget(self.amend_button)
        self.pick_button = QPushButton("In anderen &Branch übernehmen …")
        self.pick_button.clicked.connect(self.pick)
        self.pick_button.setVisible(not commit.is_merge)
        buttons.addWidget(self.pick_button)
        branch_here = QPushButton("Neuer Branch a&b hier …")
        branch_here.clicked.connect(self.branch_here)
        buttons.addWidget(branch_here)
        buttons.addStretch(1)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        buttons.addWidget(close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.info, 1)
        layout.addWidget(files_label)
        layout.addWidget(self.files, 1)
        layout.addLayout(buttons)
        self.resize(720, 520)
        self.initial_focus_widget = self.info
        for widget in (self.info, self.files):
            widget.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        if _ignore_enter(self, watched, event, (self.info, self.files)):
            return True
        return super().eventFilter(watched, event)

    def _when(self) -> str:
        return f"vom {self.commit.date:%d.%m.%Y} „{self.commit.subject}“"

    # -- Datei wiederherstellen --------------------------------------------------------------
    def current_path(self) -> str | None:
        row = self.files.currentRow()
        if 0 <= row < len(self.paths):
            return self.paths[row]
        announce("Es gibt keine Datei.")
        return None

    def restore_current(self) -> None:
        path = self.current_path()
        if path is None:
            return
        deleted = path in self.changes.deleted
        if deleted:
            what = (f"{path} wurde in der Version {self._when()} gelöscht. Die Datei kommt mit dem "
                    "Stand direkt davor zurück.")
        else:
            what = f"{path} kommt auf den Stand der Version {self._when()}."
        now = (" Die jetzige Datei kommt vorher als Sicherheitskopie in den Ordner backups."
               if (self.code_dir / path).is_file() else "")
        text = (f"{what}{now} Danach ist das eine normale Änderung, die Sie wie gewohnt hochladen. "
                "Wiederherstellen?")
        if not confirm(self, "Datei wiederherstellen", text, yes="Wiederherstellen",
                       no="Abbrechen"):
            return
        try:
            history.restore_file(self.code_dir, self.project.name, self.commit, path,
                                 self.changes)
        except CockpitError as exc:
            show_error(self, "Datei wiederherstellen", exc.message, exc.details)
            return
        self.files_changed = True
        self.files.setFocus()
        announce(f"{path} wiederhergestellt.")

    # -- Version rückgängig machen -----------------------------------------------------------
    def revert(self) -> None:
        title = "Version rückgängig machen"
        if self.commit.is_merge or not self.commit.parents:
            try:
                history.revert(self.code_dir, self.project.name, self.commit)
            except CockpitError as exc:
                show_error(self, title, exc.message, exc.details)
            return
        text = (f"Das Cockpit erstellt einen neuen Commit „{history.revert_message(self.commit)}“. "
                f"Er hebt die Änderungen der Version {self._when()} auf: "
                f"{self.changes.summary()}. Der Verlauf bleibt vollständig erhalten. "
                f"{BACKUP_NOTE} Der neue Commit ist danach noch nicht hochgeladen. "
                "Rückgängig machen?")
        if not confirm(self, title, text, yes="Rückgängig machen", no="Abbrechen"):
            return
        settings = self.services.settings.load()
        try:
            history.revert(self.code_dir, self.project.name, self.commit, settings.git_name,
                           settings.git_email)
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            return
        self.history_changed = True
        self.accept()
        announce(f"Rückgängig gemacht. Neuer Commit „{history.revert_message(self.commit)}“.")

    # -- Commit zurücknehmen -----------------------------------------------------------------
    def undo(self) -> None:
        title = "Commit zurücknehmen"
        text = (f"Der Commit „{self.commit.subject}“ wird zurückgenommen. Er ist noch nicht "
                "hochgeladen. Seine Änderungen bleiben in den Dateien und erscheinen wieder als "
                "Änderungen ohne Commit. Keine Datei wird verändert. Zurücknehmen?")
        if not confirm(self, title, text, yes="Zurücknehmen", no="Abbrechen"):
            return
        try:
            history.undo_commit(self.code_dir, self.commit)
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            return
        self.history_changed = True
        self.accept()
        announce("Commit zurückgenommen. Die Änderungen sind noch da, ohne Commit.")

    # -- Nachbessern (21.10.2026) ------------------------------------------------------------
    def amend(self) -> None:
        dialog = AmendDialog(self.commit, self)
        if not dialog.exec():
            return
        try:
            rewrite.amend(self.code_dir, self.commit, dialog.message, dialog.with_changes)
        except CockpitError as exc:
            show_error(self, "Commit nachbessern", exc.message, exc.details)
            return
        self.history_changed = True
        self.accept()
        announce("Commit nachgebessert, noch nicht hochgeladen.")

    # -- In einen anderen Branch übernehmen ------------------------------------------------------
    def _targets(self) -> list[tuple[str, Path]]:
        """Branches mit eigenem Ordner, ohne den, in dem man gerade ist."""
        from cockpit.core import git, worktrees
        main = self.services.projects.get(self.project.id) or self.project
        found = [(git.status(main.code_dir).branch or "main", main.code_dir)]
        found += [(t.branch, t.path) for t in worktrees.list_worktrees(main)]
        here = self.code_dir.resolve()
        return [(name, path) for name, path in found if path.resolve() != here and name]

    def pick(self) -> None:
        from cockpit.ui.common import choose_from_list
        title = "In anderen Branch übernehmen"
        targets = self._targets()
        if not targets:
            show_error(self, title, "Es gibt keinen anderen Branch mit eigenem Ordner. Legen Sie "
                       "zuerst in „Branches verwalten …“ einen an.")
            return
        index = choose_from_list(self, title, "Ziel-Branch", [name for name, _p in targets])
        if index is None:
            return
        name, path = targets[index]
        if not confirm(self, title, f"Die Änderungen aus „{self.commit.subject}“ kommen als neuer "
                       f"Commit in den Branch {name}. Hier bleibt alles, wie es ist. Der neue "
                       "Commit ist danach noch nicht hochgeladen. Übernehmen?",
                       yes="Übernehmen", no="Abbrechen"):
            return
        try:
            rewrite.cherry_pick(path, self.commit)
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            return
        self.files_changed = True
        announce(f"In {name} übernommen, noch nicht hochgeladen.")

    # -- Neuer Branch ab hier ------------------------------------------------------------------
    def branch_here(self) -> None:
        from cockpit.core import branches, worktrees
        from cockpit.ui.branch_dialogs import BranchNameDialog
        title = "Neuer Branch ab hier"
        dialog = BranchNameDialog(title, f"Der neue Branch beginnt beim Stand von "
                                  f"„{self.commit.subject}“ {self._when()}. Der jetzige Branch "
                                  "bleibt, wie er ist.", self.code_dir,
                                  branches.suggest_name(self.commit.subject) or "neuer-branch",
                                  self)
        if not dialog.exec():
            return
        main = self.services.projects.get(self.project.id) or self.project
        try:
            if main.has_branch_folders:
                tree = worktrees.create_at(main, dialog.name, self.commit.sha)
                where = f" Er hat den Ordner {tree.path.name}."
            else:
                rewrite.branch_at(self.code_dir, dialog.name, self.commit)
                where = " Wechseln können Sie in „Branches verwalten …“."
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            return
        self.history_changed = True
        announce(f"Branch {dialog.name} angelegt.{where}")


class ReorderDialog(FocusDialog):
    """Die Commits, die noch nicht hochgeladen sind, neueste oben. Strg+Pfeil hoch und runter
    oder die Knöpfe verschieben, "Mit dem darunter zusammenfassen" schaltet um. Nach accept()
    steht das Ergebnis in plan. Vorher fragt das Cockpit nach."""

    def __init__(self, commits: list[Commit], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Reihenfolge und Zusammenfassen: "
                            f"{count(len(commits), 'Commit', 'Commits')}, noch nicht hochgeladen")
        self.plan = rewrite.Plan([rewrite.Step(c) for c in commits])     # älteste zuerst
        self.list = QListWidget()
        label = label_for(self.list, "&Commits, neueste oben:")
        self.list.installEventFilter(self)
        up = QPushButton("Nach &oben")
        up.clicked.connect(lambda: self.move(1))
        down = QPushButton("Nach &unten")
        down.clicked.connect(lambda: self.move(-1))
        squash = QPushButton("Mit dem darunter &zusammenfassen")
        squash.clicked.connect(self.toggle_squash)
        ok = QPushButton("Ü&bernehmen …")
        ok.clicked.connect(self.take)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        for button in (up, down, squash):
            buttons.addWidget(button)
        buttons.addStretch(1)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.list, 1)
        layout.addLayout(buttons)
        self.resize(680, 400)
        self.initial_focus_widget = self.list
        self.fill(0)

    def fill(self, row: int) -> None:
        self.list.clear()
        self.list.addItems(self.plan.lines())
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))

    def _index(self) -> int:
        """Position im Plan (älteste zuerst) zur markierten Zeile (neueste oben)."""
        return len(self.plan.steps) - 1 - self.list.currentRow()

    def eventFilter(self, watched, event) -> bool:
        from PySide6.QtCore import QEvent
        if watched is self.list and event.type() == QEvent.Type.KeyPress and \
                event.modifiers() == Qt.KeyboardModifier.ControlModifier and \
                event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            self.move(1 if event.key() == Qt.Key.Key_Up else -1)
            return True
        return super().eventFilter(watched, event)

    def move(self, step: int) -> None:
        """step 1: eine Zeile nach oben, also neuer; -1: nach unten."""
        index = self._index()
        target = index + step
        steps = self.plan.steps
        if not 0 <= target < len(steps):
            announce("Weiter geht es nicht.")
            return
        steps[index], steps[target] = steps[target], steps[index]
        steps[0].squash = False                     # der älteste hat keinen darunter
        self.fill(len(steps) - 1 - target)
        announce(f"{steps[target].commit.subject}, jetzt an Stelle {self.list.currentRow() + 1}.")

    def toggle_squash(self) -> None:
        index = self._index()
        if index <= 0:
            announce("Darunter gibt es keinen Commit zum Zusammenfassen.")
            return
        step = self.plan.steps[index]
        step.squash = not step.squash
        self.fill(self.list.currentRow())
        announce("Wird zusammengefasst." if step.squash else "Wird nicht zusammengefasst.")

    def take(self) -> None:
        groups = sum(1 for s in self.plan.steps if not s.squash)
        text = (f"Das Cockpit baut die {count(len(self.plan.steps), 'Commit', 'Commits')}, die "
                f"noch nicht hochgeladen sind, in der neuen Reihenfolge neu auf. Danach sind es "
                f"{count(groups, 'Commit', 'Commits')}. Hochgeladene Commits bleiben, wie sie sind. "
                "Der alte Stand bleibt in Git gemerkt. Passen die Commits so nicht zusammen, "
                "bleibt alles, wie es war. Übernehmen?")
        if confirm(self, self.windowTitle(), text, yes="Übernehmen", no="Abbrechen"):
            self.accept()


class AmendDialog(FocusDialog):
    """Nachricht des neuesten Commits ändern, auf Wunsch die Änderungen ohne Commit dazu."""

    def __init__(self, commit: Commit, parent: QWidget | None = None) -> None:
        from PySide6.QtWidgets import QCheckBox, QLineEdit
        from cockpit.ui.common import PlainEdit
        super().__init__(parent)
        self.setWindowTitle(f"Commit nachbessern: {commit.subject}")
        self.message = ""
        self.with_changes = False
        self.summary = QLineEdit(commit.subject)
        summary_label = label_for(self.summary, "&Was haben Sie geändert?")
        self.details = PlainEdit()
        self.details.setPlainText(commit.body)
        details_label = label_for(self.details, "&Beschreibung:")
        self.changes = QCheckBox("Änderungen ohne Commit mit &hineinnehmen")
        ok = QPushButton("&Nachbessern")
        ok.setDefault(True)
        ok.clicked.connect(self.take)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        for widget in (summary_label, self.summary, details_label, self.details, self.changes):
            layout.addWidget(widget)
        layout.addLayout(buttons)
        self.resize(600, 380)
        self.initial_focus_widget = self.summary

    def take(self) -> None:
        summary = " ".join(self.summary.text().split())
        if not summary:
            show_error(self, self.windowTitle(), "Bitte schreiben Sie eine Nachricht.")
            return
        details = self.details.toPlainText().strip()
        self.message = f"{summary}\n\n{details}" if details else summary
        self.with_changes = self.changes.isChecked()
        self.accept()


class DiscardDialog(FocusDialog):
    """Änderungen ohne Commit auswählen. Nach accept() stehen sie in chosen."""

    def __init__(self, project_name: str, changes: list[LocalChange],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.changes = changes
        self.chosen: list[LocalChange] = []
        self.setWindowTitle(f"Änderungen verwerfen in {project_name}: "
                            f"{count(len(changes), 'Änderung', 'Änderungen')}")
        self.list = QListWidget()
        name_widget(self.list, "Änderungen")
        for change in changes:
            item = QListWidgetItem(change.line())
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        self.list.installEventFilter(self)
        self.all_button = QPushButton("&Alle auswählen")
        self.all_button.clicked.connect(self.toggle_all)
        discard = QPushButton("&Verwerfen …")
        discard.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(self.all_button)
        buttons.addStretch(1)
        buttons.addWidget(discard)
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(buttons)
        self.resize(640, 420)
        self.initial_focus_widget = self.list

    def eventFilter(self, watched, event) -> bool:
        if _ignore_enter(self, watched, event, (self.list,)):
            return True
        return super().eventFilter(watched, event)

    def checked(self) -> list[LocalChange]:
        return [c for row, c in enumerate(self.changes)
                if self.list.item(row).checkState() == Qt.CheckState.Checked]

    def toggle_all(self) -> None:
        select = len(self.checked()) < len(self.changes)
        state = Qt.CheckState.Checked if select else Qt.CheckState.Unchecked
        for row in range(self.list.count()):
            self.list.item(row).setCheckState(state)
        self.all_button.setText("Alle &abwählen" if select else "&Alle auswählen")
        announce("Alle ausgewählt." if select else "Keine ausgewählt.")

    def check(self) -> None:
        chosen = self.checked()
        if not chosen:
            show_error(self, self.windowTitle(), NO_CHOICE)
            self.list.setFocus()
            return
        text = (f"{history.discard_description(chosen)} Vorher kommen die Dateien als "
                "Sicherheitskopie in den Ordner backups. Verwerfen?")
        if not confirm(self, "Änderungen verwerfen", text, yes="Verwerfen", no="Abbrechen"):
            return
        self.chosen = chosen
        self.accept()


class UploadHistoryDialog(FocusDialog):
    """Hochladeverlauf eines Branches (Wunsch des Nutzers vom 07.10.2026). Oben jedes Hochladen,
    zum Beispiel „06.10.2026 14:12, Pascal, 3 Commits nach main“. Tab führt in die Commits dieses
    Hochladens, Enter dort zeigt die Details mit Rückgängig machen."""

    def __init__(self, services: "Services", project: "Project", branch: str,
                 uploads: list, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.project = project
        self.uploads = uploads
        self.changed = False
        self.setWindowTitle(f"Hochladeverlauf von {branch}: "
                            f"{count(len(uploads), 'Eintrag', 'Einträge')}")
        self.uploads_list = QListWidget()
        uploads_label = label_for(self.uploads_list, "&Hochgeladen:")
        self.uploads_list.addItems([u.text for u in uploads] or [
            "Noch nichts hochgeladen."])
        self.uploads_list.currentRowChanged.connect(lambda _row: self._fill_commits())
        self.uploads_list.itemActivated.connect(lambda _item: self.list.setFocus())
        self.list = QListWidget()
        commits_label = label_for(self.list, "&Commits:")
        self.list.itemActivated.connect(lambda _item: self.show_details())
        details = QPushButton("&Details anzeigen …")
        details.clicked.connect(self.show_details)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(details)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout = QVBoxLayout(self)
        for widget in (uploads_label, self.uploads_list, commits_label, self.list):
            layout.addWidget(widget)
        layout.addLayout(buttons)
        self.resize(720, 560)
        self.initial_focus_widget = self.uploads_list
        self.uploads_list.setCurrentRow(0)
        self._fill_commits()

    def _commits(self) -> list[Commit]:
        row = self.uploads_list.currentRow()
        return self.uploads[row].commits if 0 <= row < len(self.uploads) else []

    def _fill_commits(self) -> None:
        self.list.clear()
        self.list.addItems([c.short_line() for c in self._commits()] or ["Keine Commits."])
        self.list.setCurrentRow(0)

    def show_details(self) -> None:
        commits = self._commits()
        row = self.list.currentRow()
        if not 0 <= row < len(commits):
            announce("Es gibt keinen Commit.")
            return
        try:
            dialog = VersionDialog(self.services, self.project, commits[row], self)
        except CockpitError as exc:
            show_error(self, "Hochladeverlauf", exc.message, exc.details)
            return
        dialog.exec()
        self.changed |= dialog.files_changed or dialog.history_changed
        self.list.setFocus()
