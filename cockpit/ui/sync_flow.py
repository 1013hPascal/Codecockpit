"""Änderungen hochladen und holen in der Oberfläche (Konzept 9.2 und 9.3, Teilschritt 5c).

Hochladen (PushRunner):
1. Im Hintergrund: Änderungen lesen.
2. CommitDialog: Was haben Sie geändert? Gibt es keine Änderungen, aber Commits, die noch nicht
   hochgeladen sind, fragt das Cockpit nur, ob es sie hochladen soll.
3. Im Hintergrund: Git-Identität, Sicherheitsprüfung. Bei Funden der SafetyDialog.
4. Im Hintergrund der Ablauf PUSH_CHANGES mit "Schritt 1 von 3: …".
5. Gibt es auf der Plattform neue Commits, bietet das Cockpit an, sie zu holen und danach
   hochzuladen. Vorgabe ist "Später".

Holen (PullRunner):
1. Im Hintergrund: git fetch.
2. Rückfrage, die beschreibt, was passiert. Stören eigene Änderungen, fragt das Cockpit nach
   Beiseitelegen (Stash). Vorgabe ist "Abbrechen".
3. Im Hintergrund: Sicherheitskopie, git merge, Änderungen zurücklegen.
4. Bei Konflikten der ConflictDialog. Abbrechen führt zurück zum Stand vor dem Holen.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from cockpit.core import git, sync, upload
from cockpit.core.errors import CockpitError
from cockpit.core.flows.engine import FlowContext
from cockpit.core.projects import Project
from cockpit.core.sync import ConflictKind, Incoming, MergeOutcome
from cockpit.core.text import count, join_words
from cockpit.ui import sync_dialogs, upload_dialogs, vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import ask_buttons, confirm
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

log = logging.getLogger(__name__)


class _Runner:
    def __init__(self, controller: "ProjectController", project: Project) -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services
        self.project = project
        self.platform_name = self.window.project_list.platform_name
        # Qt hält Verbindungen zu Methoden nur schwach, deshalb merkt sich der Controller den
        # laufenden Durchlauf (wie beim ersten Hochladen).
        controller.upload = self

    @property
    def key(self) -> str:
        return f"project:{self.project.id}"

    def unlock(self) -> bool:
        """Tresor öffnen, falls das Projekt einen Zugang braucht."""
        project = self.project
        needs_account = project.account_id is not None or (
            project.remote is not None
            and self.services.account_for_host(project.remote.host) is not None)
        return vault_ui.ensure_unlocked(self.services, self.window) if needs_account else True

    def refresh(self) -> None:
        self.window.refresh_status([self.project.id])


class PushRunner(_Runner):
    """Änderungen hochladen."""

    def __init__(self, controller: "ProjectController", project: Project,
                 confirmed: bool = False) -> None:
        super().__init__(controller, project)
        self.title = "Änderungen hochladen"
        self.confirmed = confirmed            # schon bestätigt, zum Beispiel nach dem Holen
        self.message = ""
        self.public = False
        self.accepted: set[tuple[str, str, str]] = set()

    # -- 1. Änderungen lesen ---------------------------------------------------------------
    def start(self) -> None:
        code_dir = self.project.code_dir
        kind = sync.conflict_kind(code_dir)
        if kind is not ConflictKind.NONE:
            announce("Das Zusammenführen ist noch nicht abgeschlossen.")
            PullRunner(self.controller, self.project).resolve(kind)
            return
        if not self.unlock():
            return

        def work(task: Task):
            return sync.changes(code_dir), git.status(code_dir)

        self.controller.run_task(self.key, work, self.ask_message, self.title)

    # -- 2. Nachricht ------------------------------------------------------------------------
    def ask_message(self, outcome) -> None:
        changes, state = outcome
        if not changes:
            if state.upstream and not state.ahead:
                announce("Es gibt nichts zum Hochladen. Alles ist hochgeladen.")
                return
            commits = count(state.ahead, "Commit ist", "Commits sind") if state.upstream else (
                f"Der Branch {state.branch} ist")
            if not self.confirmed and not confirm(self.window, self.title,
                           f"{commits} noch nicht auf {self.platform_name}. Jetzt hochladen?",
                           yes="Hochladen", no="Abbrechen"):
                return
            self.check()
            return
        dialog = sync_dialogs.CommitDialog(self.title, changes, self.window)
        if not dialog.exec():
            return
        self.message = dialog.message
        self.check()

    # -- 3. Identität und Sicherheitsprüfung -------------------------------------------------
    def check(self) -> None:
        services, project = self.services, self.project
        settings = services.settings.load()
        self.public = sync.is_public(services, project)
        public = self.public

        def work(task: Task):
            if self.message:
                sync.prepare_commit(project.code_dir, project.name, settings.git_name,
                                    settings.git_email)
            return sync.scan(project.code_dir, public, settings.git_email)

        self.controller.run_task(self.key, work, self.review, self.title)

    def review(self, report) -> None:
        email = self.services.settings.load().git_email
        if report.findings:
            code_dir, public = self.project.code_dir, self.public
            spec = upload.UploadSpec(self.project.name, private=not public)
            dialog = upload_dialogs.SafetyDialog(
                report, code_dir, spec, email,
                rescan=lambda: sync.scan(code_dir, public, email), parent=self.window)
            if not dialog.exec():
                announce("Hochladen abgebrochen.")
                self.refresh()
                return
            self.accepted |= dialog.accepted
        self.run_flow(email)

    # -- 4. Ablauf ---------------------------------------------------------------------------
    def run_flow(self, email: str) -> None:
        services, project = self.services, self.project
        asker = self.window.asker
        data = {"message": self.message, "public": self.public, "accepted": self.accepted,
                "git_email": email}

        def work(task: Task):
            data["env"] = sync.environment(services, project)
            context = FlowContext(services, project, asker, task.cancel_event, data=data)
            summary = services.flows.run(sync.PUSH_CHANGES, context,
                                         lambda n, total, text: task.status.emit(text + " …"))
            return summary, context.data

        self.controller.run_task(self.key, work, self.finished, self.title, on_status=announce)

    # -- 5. Ergebnis -------------------------------------------------------------------------
    def finished(self, outcome) -> None:
        summary, data = outcome
        self.refresh()
        if summary.completed:
            announce(summary.text())
            return
        behind = data.get("behind")
        if behind:
            saved = "Ihr Commit ist gespeichert, aber noch nicht hochgeladen. " if (
                self.message) else ""
            if confirm(self.window, self.title,
                       f"{saved}Auf {self.platform_name} gibt es "
                       f"{count(behind, 'neuen Commit', 'neue Commits')}, die hier noch fehlen. "
                       "Jetzt holen und danach hochladen?",
                       yes="Holen und hochladen …", no="Später"):
                PullRunner(self.controller, self.project,
                           then=lambda: PushRunner(self.controller, self.project,
                                                   confirmed=True).start()).start()
            return
        failure = summary.results[-1][1] if summary.results else None
        show_error(self.window, self.title, summary.text(), failure.details if failure else "")


class PullRunner(_Runner):
    """Änderungen von der Plattform holen."""

    def __init__(self, controller: "ProjectController", project: Project,
                 then: Callable[[], None] | None = None) -> None:
        super().__init__(controller, project)
        self.title = f"Änderungen von {self.platform_name} holen"
        self.then = then                      # danach, zum Beispiel wieder hochladen

    # -- 1. Holen ------------------------------------------------------------------------------
    def start(self) -> None:
        code_dir = self.project.code_dir
        kind = sync.conflict_kind(code_dir)
        if kind is not ConflictKind.NONE:
            self.resolve(kind)
            return
        if not self.unlock():
            return
        services, project = self.services, self.project
        announce("Wird geholt.")

        def work(task: Task) -> Incoming:
            return sync.fetch(code_dir, sync.environment(services, project), task.cancel_event)

        self.controller.run_task(self.key, work, self.ask, self.title)

    # -- 2. Rückfrage --------------------------------------------------------------------------
    def ask(self, incoming: Incoming) -> None:
        if not incoming.behind:
            self.refresh()
            announce(f"Keine neuen Änderungen auf {self.platform_name}.")
            self._continue()
            return
        what = (f"Auf {self.platform_name} gibt es "
                f"{count(incoming.behind, 'neuen Commit', 'neue Commits')}, sie ändern "
                f"{count(len(incoming.files), 'Datei', 'Dateien')}. ")
        how = ("Das Cockpit führt sie mit Ihrem Stand zusammen, wie git pull. Vorher kommen die "
               "betroffenen Dateien als Sicherheitskopie in den Ordner backups im Datenordner.")
        stash = bool(incoming.overlap)
        if stash:
            text = (f"{what}In {join_words(incoming.overlap[:5])} haben Sie auch Änderungen, die "
                    "noch nicht hochgeladen sind. Das Cockpit legt Ihre Änderungen deshalb vorher "
                    "beiseite (Stash) und danach wieder zurück. Ändern beide dieselbe Stelle, "
                    f"wählen Sie danach pro Datei, welche Fassung gilt. {how}")
            choice = ask_buttons(self.window, self.title, text,
                                 ["Beiseitelegen und holen", "Abbrechen"], default=1, escape=1)
            if choice != 0:
                return
        elif not confirm(self.window, self.title, f"{what}{how} Holen?", yes="Holen",
                         no="Abbrechen"):
            return
        self.merge(incoming, stash)

    # -- 3. Zusammenführen -------------------------------------------------------------------
    def merge(self, incoming: Incoming, stash: bool) -> None:
        services, project = self.services, self.project
        settings = services.settings.load()
        announce("Wird zusammengeführt.")

        def work(task: Task) -> MergeOutcome:
            sync.prepare_commit(project.code_dir, project.name, settings.git_name,
                                settings.git_email)
            sync.backup(project.code_dir, project.name, incoming)
            return sync.merge(project.code_dir, stash)

        def done(outcome: MergeOutcome) -> None:
            self.after_merge(outcome, incoming.behind)

        self.controller.run_task(self.key, work, done, self.title)

    def after_merge(self, outcome: MergeOutcome, behind: int = 0) -> None:
        self.refresh()
        if outcome.kind is not ConflictKind.NONE:
            self.resolve(outcome.kind)
            return
        if behind:
            announce(f"Geholt: {count(behind, 'neuer Commit', 'neue Commits')} von "
                     f"{self.platform_name}.")
        else:
            announce("Zusammenführen abgeschlossen.")
        self._continue()

    def _continue(self) -> None:
        if self.then is not None:
            then, self.then = self.then, None
            then()

    # -- 4. Konflikte --------------------------------------------------------------------------
    def resolve(self, kind: ConflictKind) -> None:
        """Konflikte lösen. Wird auch aufgerufen, wenn das Cockpit mitten im Zusammenführen
        geschlossen wurde."""
        code_dir = self.project.code_dir
        announce(f"Konflikte beim Zusammenführen in {self.project.name}.")
        dialog = sync_dialogs.ConflictDialog(code_dir, kind, self.platform_name, self.window)
        if dialog.exec():
            try:
                outcome = sync.finish(code_dir, kind)
            except CockpitError as exc:
                show_error(self.window, self.title, exc.message, exc.details)
                self.refresh()
                return
            self.after_merge(outcome)
            return
        try:
            kept = sync.abort(code_dir, kind)
        except CockpitError as exc:
            show_error(self.window, self.title, exc.message, exc.details)
            self.refresh()
            return
        self.refresh()
        text = "Zusammenführen abgebrochen. Alles ist wie vor dem Holen."
        if kept:
            text += " Ihre Änderungen liegen beiseitegelegt im Stash."
        announce(text)
