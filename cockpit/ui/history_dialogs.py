"""Fenster für Verlauf und Rückgängig machen (Konzept 9.4 und 9.7, Teilschritt 5d).

HistoryDialog: alle Versionen, neueste oben, zum Beispiel "23.09.2026, Version 1.4.0: Suche
ergänzt". Enter zeigt die Details.
VersionDialog: Angaben und geänderte Dateien einer Version. Per Tab: "Datei wiederherstellen …",
"Version rückgängig machen …" und beim neuesten Commit, solange er nicht hochgeladen ist, "Commit
zurücknehmen …".
DiscardDialog: Änderungen ohne Commit als Liste mit Kontrollkästchen. Leertaste wählt aus.

Alles, was Dateien verändert, beschreibt vorher, was passiert, braucht eine Bestätigung und legt
eine Sicherheitskopie an. Vorgabe ist immer "Abbrechen". Wie in den anderen Listen mit Knöpfen löst
Enter in Angaben, Dateien und Änderungen nichts aus, Enter auf einem Knopf genau diesen Knopf.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QHBoxLayout, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import history, rewrite
from cockpit.core.errors import CockpitError
from cockpit.core.history import Commit
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, label_for, name_widget
from cockpit.ui.error_dialog import show_error
# Aufgeteilt am 22.10.2026: Teile stehen in history_edit_dialogs.py. Die Namen bleiben hier erreichbar.
from cockpit.ui.history_edit_dialogs import (  # noqa: F401
    BACKUP_NOTE, DiscardDialog, NO_CHOICE, ReorderDialog, UploadHistoryDialog, VersionDialog)

if TYPE_CHECKING:
    from cockpit.core.projects import Project
    from cockpit.core.services import Services


class HistoryDialog(FocusDialog):
    """Verlauf eines Projekts (Wunsch des Nutzers vom 07.10.2026): oben die Versionen, zuerst
    „In Arbeit“ mit dem, was seit der letzten Version dazukam. Tab führt in die Commits der
    gewählten Version (Datum, Person, Text), Enter dort zeigt die Details. Ohne jede Version stehen
    oben die Tage. Nach dem Schließen: changed ist True, wenn sich Dateien oder der Verlauf
    geändert haben."""

    def __init__(self, services: "Services", project: "Project", commits: list[Commit],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.project = project
        self.commits = commits
        self.groups: list[history.Group] = []
        self.changed = False
        self.versions = QListWidget()
        self.versions_label = label_for(self.versions, "&Versionen:")
        self.versions.currentRowChanged.connect(lambda _row: self._fill_commits())
        self.versions.itemActivated.connect(lambda _item: self.list.setFocus())
        self.list = QListWidget()
        self.commits_label = label_for(self.list, "&Commits:")
        self.list.itemActivated.connect(lambda _item: self.show_details())
        details = QPushButton("&Details anzeigen …")
        details.clicked.connect(self.show_details)
        self.back_button = QPushButton("Zu dieser Version &zurück …")
        self.back_button.clicked.connect(self.back_to_version)
        # 21.10.2026: Commits, die noch nicht hochgeladen sind, umsortieren und zusammenfassen
        self.reorder_button = QPushButton("&Reihenfolge und Zusammenfassen …")
        self.reorder_button.clicked.connect(self.reorder)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(details)
        buttons.addWidget(self.back_button)
        buttons.addWidget(self.reorder_button)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout = QVBoxLayout(self)
        layout.addWidget(self.versions_label)
        layout.addWidget(self.versions, 1)
        layout.addWidget(self.commits_label)
        layout.addWidget(self.list, 1)
        layout.addLayout(buttons)
        self.resize(720, 560)
        self.initial_focus_widget = self.versions
        self.fill()

    def fill(self, row: int = 0) -> None:
        self.groups = history.group_versions(self.commits)
        by_version = any(g.kind != history.DAY for g in self.groups)
        title = f"Verlauf von {self.project.name}: "
        if by_version:
            versions = sum(1 for g in self.groups if g.kind == history.VERSION)
            title += f"{count(versions, 'Version', 'Versionen')}, "
        self.setWindowTitle(title + count(len(self.commits), "Commit", "Commits"))
        self.versions_label.setText("&Versionen:" if by_version else "&Tage:")
        name_widget(self.versions, "Versionen" if by_version else "Tage")
        self.versions.blockSignals(True)
        self.versions.clear()
        self.versions.addItems([g.line() for g in self.groups] or ["Noch keine Commits."])
        self.versions.setCurrentRow(max(0, min(row, self.versions.count() - 1)))
        self.versions.blockSignals(False)
        self.reorder_button.setVisible(sum(1 for c in self.commits if not c.uploaded) >= 2)
        self._fill_commits()

    def group(self) -> history.Group | None:
        row = self.versions.currentRow()
        return self.groups[row] if 0 <= row < len(self.groups) else None

    def _fill_commits(self) -> None:
        group = self.group()
        self.list.clear()
        self.list.addItems([c.short_line() for c in group.commits] if group else
                           ["Noch keine Commits."])
        self.list.setCurrentRow(0)
        head = group.head if group is not None else None
        self.back_button.setEnabled(group is not None and group.kind == history.VERSION
                                    and head is not None and not head.newest)

    def reload(self, row: int = 0) -> None:
        try:
            self.commits = history.log_commits(self.project.code_dir)
        except CockpitError as exc:
            show_error(self, "Verlauf", exc.message, exc.details)
        self.fill(row)

    def current(self) -> Commit | None:
        group = self.group()
        row = self.list.currentRow()
        if group is None or not 0 <= row < len(group.commits):
            return None
        return group.commits[row]

    def back_to_version(self) -> None:
        """Alle Dateien auf den Stand der gewählten Version, als neuer Commit."""
        group = self.group()
        if group is None or group.kind != history.VERSION or group.head is None:
            announce("Bitte wählen Sie eine Version.")
            return
        title = "Zu dieser Version zurück"
        commit = group.head
        text = (f"Das Cockpit setzt alle Dateien auf den Stand der Version {group.version} vom "
                f"{commit.date:%d.%m.%Y} und erstellt dafür einen neuen Commit "
                f"„{history.back_to_message(group.version)}“. Alles, was danach kam, bleibt im "
                f"Verlauf und lässt sich später wiederholen. {BACKUP_NOTE} Der neue Commit ist "
                "danach noch nicht hochgeladen. Zurück zu dieser Version?")
        if not confirm(self, title, text, yes="Zurück zur Version", no="Abbrechen"):
            return
        settings = self.services.settings.load()
        try:
            history.back_to(self.project.code_dir, self.project.name, commit,
                            settings.git_name, settings.git_email)
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            return
        self.changed = True
        self.reload(0)
        self.versions.setFocus()
        announce(f"Zurück zu Version {group.version}. Neuer Commit, noch nicht hochgeladen.")

    def reorder(self) -> None:
        title = "Reihenfolge und Zusammenfassen"
        try:
            local = rewrite.local_commits(self.project.code_dir, self.commits)
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            return
        dialog = ReorderDialog(local, self)
        if not dialog.exec():
            return
        try:
            rewrite.reorder(self.project.code_dir, dialog.plan)
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            return
        self.changed = True
        self.reload(0)
        self.versions.setFocus()
        announce("Verlauf geändert, noch nicht hochgeladen.")

    def show_details(self) -> None:
        commit = self.current()
        if commit is None:
            announce("Es gibt noch keine Version.")
            return
        try:
            dialog = VersionDialog(self.services, self.project, commit, self)
        except CockpitError as exc:
            show_error(self, "Verlauf", exc.message, exc.details)
            return
        dialog.exec()
        self.changed |= dialog.files_changed or dialog.history_changed
        if dialog.history_changed:
            self.reload(0)                  # der neue oder zurückgenommene Commit ist oben
            self.versions.setFocus()
            return
        self.list.setFocus()


