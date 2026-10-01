"""Releases und GitHub Actions in der Oberfläche (Phase 14).

Projektzeile: "Releases …" und, wenn das Repository Workflows hat, "GitHub Actions …".
Nach dem Hochladen einer neuen Version: "Für Version 1.4.0 ein Release auf GitHub anlegen?",
Vorgabe "Später" (Frage 1). Mit aktiver Exe-Erstellung wie "Exe veröffentlichen", sonst ein
Release nur mit dem Quellcode.

Alles, was mit GitHub spricht, läuft im Hintergrund. Löschen fragt vorher, Vorgabe "Abbrechen".
"""
from __future__ import annotations

import logging
import webbrowser
from typing import TYPE_CHECKING

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import git, repo_admin
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.features.releases import runs
from cockpit.features.releases.runs import FEATURE_ID
from cockpit.platforms.base import Release, WorkflowRun
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import (FocusDialog, PlainEdit, click_focused_button, confirm, label_for,
                               make_copyable, name_widget, show_info)
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

log = logging.getLogger(__name__)


# -- Fenster -------------------------------------------------------------------------------------
class _ListDialog(FocusDialog):
    """Liste mit Knöpfen. Knöpfe, die zur Zeile nicht passen, sind ausgeblendet. Enter auf der
    Liste führt die erste passende Aktion aus, Enter auf einem Knopf drückt ihn."""

    def __init__(self, title: str, name: str, parent: QWidget | None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.list = QListWidget()
        name_widget(self.list, name)
        self.list.installEventFilter(self)
        self.list.currentRowChanged.connect(lambda _row: self.update_buttons())
        self.initial_focus_widget = self.list

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            self.enter()
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)

    def enter(self) -> None:
        pass

    def update_buttons(self) -> None:
        pass


class ReleasesDialog(_ListDialog):
    def __init__(self, flow: "ReleasesActions", project: Project, releases: list[Release],
                 parent: QWidget | None = None) -> None:
        super().__init__(f"Releases von {project.name}: {len(releases)}", "Releases", parent)
        self.flow, self.project, self.releases = flow, project, releases
        self.show_button = QPushButton("Versionshinweise &ansehen")
        self.show_button.clicked.connect(self.show_notes)
        self.edit_button = QPushButton("Versionshinweise &bearbeiten …")
        self.edit_button.clicked.connect(self.edit_notes)
        self.copy_button = QPushButton("&Link kopieren")
        self.copy_button.clicked.connect(self.copy_link)
        self.open_button = QPushButton("Im B&rowser öffnen")
        self.open_button.clicked.connect(self.open_page)
        self.delete_button = QPushButton("Release l&öschen …")
        self.delete_button.clicked.connect(self.delete)
        close = QPushButton("&Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(self.show_button, self.edit_button, self.copy_button,
                                    self.open_button, self.delete_button, None, close))
        self.resize(760, 420)
        self.fill()

    def fill(self, row: int = 0) -> None:
        self.setWindowTitle(f"Releases von {self.project.name}: {len(self.releases)}")
        self.list.clear()
        self.list.addItems([runs.release_line(r) for r in self.releases]
                           or ["Noch keine Releases."])
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))
        self.update_buttons()

    def current(self) -> Release | None:
        row = self.list.currentRow()
        return self.releases[row] if 0 <= row < len(self.releases) else None

    def update_buttons(self) -> None:
        present = self.current() is not None
        for button in (self.show_button, self.edit_button, self.copy_button, self.open_button,
                       self.delete_button):
            button.setVisible(present)

    def enter(self) -> None:
        self.show_notes()

    def show_notes(self) -> None:
        from cockpit.core.text import one_sentence_per_line
        from cockpit.ui.text_dialog import TextDialog
        release = self.current()
        if release is None:
            return
        text = one_sentence_per_line(release.body) or "Keine Versionshinweise."
        TextDialog(f"Versionshinweise {release.tag}", text, "Versionshinweise", self).exec()

    def edit_notes(self) -> None:
        release = self.current()
        if release is None:
            return
        dialog = NotesDialog(release, self)
        if not dialog.exec():
            return
        row = self.list.currentRow()

        def done(updated: Release) -> None:
            self.releases[row] = updated
            self.fill(row)
            announce("Versionshinweise gespeichert.")

        self.flow.on_platform(self.project, lambda platform, ref: platform.update_release_notes(
            ref, release, dialog.text), done, "Versionshinweise ändern")

    def copy_link(self) -> None:
        release = self.current()
        if release is not None:
            QGuiApplication.clipboard().setText(release.url)
            announce("Link kopiert.")

    def open_page(self) -> None:
        release = self.current()
        if release is not None:
            webbrowser.open(release.url)
            announce("Wird im Browser geöffnet.")

    def delete(self) -> None:
        release = self.current()
        if release is None:
            return
        if not confirm(self, "Release löschen", f"Das Release {release.tag} wird auf GitHub "
                       "gelöscht, mit seinen Dateien. Das Tag im Code bleibt. Löschen?",
                       yes="Löschen", no="Abbrechen"):
            return
        row = self.list.currentRow()

        def done(_value) -> None:
            self.releases.pop(row)
            self.fill(row)
            announce(f"Release {release.tag} gelöscht.")

        self.flow.on_platform(self.project, lambda platform, ref: platform.delete_release(
            ref, release), done, "Release löschen")


class NotesDialog(FocusDialog):
    def __init__(self, release: Release, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Versionshinweise {release.tag} bearbeiten")
        self.edit = PlainEdit()
        self.edit.setPlainText(release.body)
        label = label_for(self.edit, "&Versionshinweise:")
        save = QPushButton("&Speichern")
        save.clicked.connect(self.accept)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        for button in (save, cancel):
            button.setAutoDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.edit, 1)
        layout.addLayout(button_row(None, save, cancel))
        self.resize(640, 420)
        self.initial_focus_widget = self.edit

    @property
    def text(self) -> str:
        return self.edit.toPlainText().strip()

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)


class ActionsDialog(_ListDialog):
    def __init__(self, flow: "ReleasesActions", project: Project, items: list[WorkflowRun],
                 parent: QWidget | None = None) -> None:
        super().__init__(f"GitHub Actions von {project.name}", "Läufe", parent)
        self.flow, self.project, self.runs = flow, project, items
        self.error_button = QPushButton("&Fehler lesen")
        self.error_button.clicked.connect(self.read_error)
        self.rerun_button = QPushButton("&Neu starten")
        self.rerun_button.clicked.connect(self.rerun)
        self.open_button = QPushButton("Im B&rowser öffnen")
        self.open_button.clicked.connect(self.open_page)
        refresh = QPushButton("&Aktualisieren")
        refresh.clicked.connect(self.refresh)
        close = QPushButton("&Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(self.error_button, self.rerun_button, self.open_button,
                                    refresh, None, close))
        self.resize(820, 420)
        self.fill()

    def fill(self, row: int = 0) -> None:
        self.list.clear()
        self.list.addItems([runs.run_line(r) for r in self.runs] or ["Noch keine Läufe."])
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))
        self.update_buttons()

    def current(self) -> WorkflowRun | None:
        row = self.list.currentRow()
        return self.runs[row] if 0 <= row < len(self.runs) else None

    def update_buttons(self) -> None:
        run = self.current()
        self.error_button.setVisible(run is not None and run.failed)
        self.rerun_button.setVisible(run is not None and run.status == "completed")
        self.open_button.setVisible(run is not None)

    def enter(self) -> None:
        run = self.current()
        if run is not None and run.failed:
            self.read_error()
        elif run is not None:
            announce(runs.run_line(run))

    def read_error(self) -> None:
        run = self.current()
        if run is not None:
            self.flow.read_error(self.project, run, self)

    def rerun(self) -> None:
        run = self.current()
        if run is None:
            return

        def done(_value) -> None:
            announce(f"{run.workflow} wird neu gestartet.")
            self.refresh()

        self.flow.on_platform(self.project, lambda platform, ref: platform.rerun(ref, run), done,
                              "Neu starten")

    def open_page(self) -> None:
        run = self.current()
        if run is not None:
            webbrowser.open(run.url)
            announce("Wird im Browser geöffnet.")

    def refresh(self) -> None:
        row = self.list.currentRow()

        def done(items: list[WorkflowRun]) -> None:
            self.runs = items
            self.fill(row)
            announce("Aktualisiert.")

        self.flow.on_platform(self.project, lambda platform, ref: platform.workflow_runs(ref),
                              done, "GitHub Actions")


class LogDialog(FocusDialog):
    """Ausgabe des fehlgeschlagenen Schritts und darunter die Erklärung der KI (Frage 5)."""

    def __init__(self, title: str, lines: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.output = QListWidget()
        self.output.setWordWrap(True)
        make_copyable(self.output)
        self.output.addItems(lines or ["Keine Ausgabe."])
        self.output.setCurrentRow(max(0, self.output.count() - 1))
        output_label = label_for(self.output, "&Ausgabe:")
        self.explanation = QListWidget()
        self.explanation.setWordWrap(True)
        make_copyable(self.explanation)
        explanation_label = label_for(self.explanation, "&Erklärung der KI:")
        close = QPushButton("&Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        for widget in (output_label, self.output):
            layout.addWidget(widget)
        layout.addWidget(explanation_label)
        layout.addWidget(self.explanation)
        layout.addLayout(button_row(None, close))
        self.resize(820, 560)
        self.initial_focus_widget = self.output

    def set_explanation(self, text: str) -> None:
        from cockpit.core.text import one_sentence_per_line
        self.explanation.clear()
        self.explanation.addItems([l for l in one_sentence_per_line(text).splitlines() if l]
                                  or ["Keine Erklärung."])
        self.explanation.setCurrentRow(0)
        announce("Erklärung der KI bereit.")

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)


# -- Aktionen -------------------------------------------------------------------------------------
class ReleasesActions:
    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services

    def active(self, project: Project | None) -> bool:
        if project is None or project.remote is None or FEATURE_ID not in self.services.registry:
            return False
        try:
            return self.services.features.active(FEATURE_ID, project)
        except CockpitError:
            return False

    @staticmethod
    def has_workflows(project: Project) -> bool:
        folder = project.code_dir / ".github" / "workflows"
        return folder.is_dir() and any(folder.glob("*.y*ml"))

    def actions(self) -> list[Action]:
        return [
            Action("releases_list", "Releases …", Target.PROJECT, self.open_releases,
                   visible=lambda c: self.active(c.project), order=45),
            Action("actions_list", "GitHub Actions …", Target.PROJECT, self.open_actions,
                   visible=lambda c: self.active(c.project) and self.has_workflows(c.project),
                   order=46),
        ]

    # -- Hilfen -----------------------------------------------------------------------------
    def on_platform(self, project: Project, work, done, title: str) -> None:
        """work(platform, ref) im Hintergrund, done im Vordergrund. Fehler als Meldungsfenster."""
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        platform = self.services.platform_for(project)
        if platform is None:
            show_error(self.window, title, "Für dieses Projekt ist kein Konto eingerichtet.")
            return
        ref = repo_admin.repo_ref(project)
        self.controller.run_task(f"releases:{project.id}", lambda task: work(platform, ref), done,
                                 title)

    def open_releases(self, context: ActionContext) -> None:
        project = context.project
        announce("Releases werden abgefragt.")
        self.on_platform(project, lambda platform, ref: platform.releases(ref),
                         lambda items: ReleasesDialog(self, project, items, self.window).exec(),
                         "Releases")

    def open_actions(self, context: ActionContext) -> None:
        project = context.project

        def done(items: list[WorkflowRun]) -> None:
            if items:
                runs.remember_failed(self.services.database, project.remote.key, items[0].failed)
            ActionsDialog(self, project, items, self.window).exec()
            self.window.refresh_status([project.id])

        announce("Läufe werden abgefragt.")
        self.on_platform(project, lambda platform, ref: platform.workflow_runs(ref), done,
                         "GitHub Actions")

    # -- Fehler lesen -----------------------------------------------------------------------
    def read_error(self, project: Project, run: WorkflowRun, parent: QWidget) -> None:
        def work(platform, ref):
            jobs = [j for j in platform.run_jobs(ref, run.id) if j.conclusion == "failure"]
            if not jobs:
                return None, []
            job = jobs[0]
            return job, runs.readable_log(platform.job_log(ref, job.id))

        def done(outcome) -> None:
            job, lines = outcome
            if job is None:
                show_info(parent, "Fehler lesen", "GitHub nennt keinen fehlgeschlagenen Teil.")
                return
            step = f", Schritt {job.failed_steps[0]}" if job.failed_steps else ""
            title = f"Fehler: {run.workflow}, {job.name}{step}"
            dialog = LogDialog(title, lines, parent)
            self._explain(dialog, f"GitHub Actions: {run.workflow}, {job.name}{step}", lines)
            dialog.exec()

        announce("Die Ausgabe wird geholt.")
        self.on_platform(project, work, done, "Fehler lesen")

    def _explain(self, dialog: LogDialog, command: str, lines: list[str]) -> None:
        """Erklärung der KI im Hintergrund. Ohne KI steht dort, warum."""
        from cockpit.features.terminal_explain.explain import explain
        from cockpit.ui import ai_ui
        tool = self.services.features.setting(FEATURE_ID, "tool") or None
        ai = ai_ui.prepare(self.services, dialog, FEATURE_ID, "die Ausgabe des Laufs", tool)
        if isinstance(ai, str):
            dialog.explanation.addItem(ai)
            return
        dialog.explanation.addItem("Die KI erklärt …")
        task = Task(lambda t: explain(ai, command, 1, lines, t.cancel_event), dialog)
        task.result.connect(dialog.set_explanation)
        task.error.connect(lambda message, details: (dialog.explanation.clear(),
                                                     dialog.explanation.addItem(message)))

        def finished() -> None:
            task.wait()
            task.deleteLater()

        task.finished.connect(finished)
        dialog.finished.connect(lambda _code: (task.cancel(), task.wait(10000)))
        task.start()

    # -- Release nach einer neuen Version (Frage 1) -----------------------------------------
    def offer_after_version(self, project: Project, version: str) -> bool:
        """True, wenn der Nutzer ein Release anlegen will (dann kein Angebot eines Pull
        Requests mehr)."""
        if not self.active(project):
            return False
        if not confirm(self.window, "Release", f"Für Version {version} ein Release auf GitHub "
                       "anlegen?", yes="Release anlegen", no="Später"):
            return False
        from cockpit.core import exe
        exe_actions = self.controller.exe
        context = ActionContext(self.services, project, Target.EXE)
        if exe_actions._building(context) and exe.current_exe(project) is not None:
            exe_actions.publish(context)                # schlägt diese Version vor (Phase 9)
        else:
            self.publish_source(project, version)
        return True

    def publish_source(self, project: Project, version: str) -> None:
        """Release nur mit dem Quellcode. GitHub hängt ihn selbst als ZIP-Datei an."""
        def work(platform, ref):
            return [r.tag for r in platform.releases(ref)]

        self.on_platform(project, work, lambda tags: self._ask_source(project, version, tags),
                         "Release")

    def _ask_source(self, project: Project, version: str, tags: list[str]) -> None:
        from cockpit.ui import ai_suggest
        from cockpit.ui.exe_flow import PublishDialog
        source = ai_suggest.for_release_notes(self.services, project, tags)
        dialog = PublishDialog(project, version, tags, "nur Quellcode", self.window,
                               source=source)
        if not dialog.exec():
            return
        chosen, notes = dialog.version, dialog.notes
        tag = f"v{chosen}"
        found = git.run(["rev-list", "-n", "1", tag], project.code_dir, check=False)
        target = found.stdout.strip() or git.status(project.code_dir).default_branch or "main"

        def work(platform, ref):
            return platform.create_release(ref, tag, f"Version {chosen}", notes, target)

        def done(release: Release) -> None:
            QGuiApplication.clipboard().setText(release.url)
            announce(f"Release {chosen} angelegt. Link kopiert.")

        announce("Release wird angelegt.")
        self.on_platform(project, work, done, "Release anlegen")
