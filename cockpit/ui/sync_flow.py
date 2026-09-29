"""Änderungen hochladen und holen in der Oberfläche (Konzept 9.2 und 9.3, Teilschritt 5c).

Hochladen (PushRunner):
1. Im Hintergrund: Änderungen lesen.
2. CommitDialog: Was haben Sie geändert? Gibt es keine Änderungen, aber Commits, die noch nicht
   hochgeladen sind, fragt das Cockpit nur, ob es sie hochladen soll.
3. Im Hintergrund: Git-Identität, Sicherheitsprüfung. Bei Funden der SafetyDialog.
4. Im Hintergrund der Ablauf PUSH_CHANGES mit "Schritt 1 von 3: …".
5. Gibt es auf der Plattform neue Commits, bietet das Cockpit an, sie zu holen und danach
   hochzuladen. Vorgabe ist "Später".
Ab Phase 6c:
- Ist das Feature "Branches und Pull Requests" aktiv und Sie sind auf main, fragt das Cockpit
  nach der Nachricht, in welchen Branch hochgeladen wird. Danach bietet es einen Pull Request an.
- Lehnt die Plattform das Hochladen ab, weil der Branch geschützt ist, bietet das Cockpit an, die
  Commits in einen neuen Branch zu verschieben, hochzuladen und einen Pull Request zu erstellen.

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

from cockpit.core import branches, git, history, sync, upload
from cockpit.core.errors import CockpitError
from cockpit.core.flows.engine import FlowContext
from cockpit.core.projects import Project
from cockpit.core.sync import ConflictKind, Incoming, MergeOutcome
from cockpit.core.text import count, join_words
from cockpit.ui import sync_dialogs, upload_dialogs, vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import ask_buttons, choose_from_list, confirm
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
                 confirmed: bool = False, then: Callable[[], None] | None = None) -> None:
        super().__init__(controller, project)
        self.title = "Änderungen hochladen"
        self.confirmed = confirmed            # schon bestätigt, zum Beispiel nach dem Holen
        self.then = then                      # danach, zum Beispiel Pull Request erstellen
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
            self.choose_target(state)
            return
        from cockpit.ui import ai_suggest
        source = ai_suggest.for_commit(self.services, self.project)
        dialog = sync_dialogs.CommitDialog(self.title, changes, self.window, source=source)
        if not dialog.exec():
            return
        self.message = dialog.message
        self.choose_target(state)

    # -- 2b. Branch wählen (Feature "Branches und Pull Requests", Phase 6c) ------------------------
    def pull_requests_active(self) -> bool:
        from cockpit.features.branches_prs.manifest import FEATURE_ID
        services = self.services
        try:
            return (FEATURE_ID in services.registry
                    and services.features.active(FEATURE_ID, self.project))
        except CockpitError:
            return False

    def choose_target(self, state) -> None:
        """Auf main mit aktivem Feature: in welchen Branch? Sonst gleich weiter."""
        main = state.default_branch
        if self.then is not None or state.branch != main or not self.pull_requests_active():
            self.check()
            return
        code_dir = self.project.code_dir
        subject = self.message.splitlines()[0] if self.message else git.run(
            ["log", "-1", "--format=%s"], code_dir, check=False).stdout.strip()
        suggestion = branches.suggest_name(subject) or "neue-aenderung"
        others = [] if state.ahead else [
            b.name for b in branches.list_branches(code_dir) if b.local and not b.default]
        items = ([f"Neuer Branch: {suggestion} …"] + [f"Vorhandener Branch: {b}" for b in others]
                 + [f"Direkt in {main}"])
        index = choose_from_list(self.window, "In welchen Branch hochladen?", "Branches", items)
        if index is None:
            announce("Hochladen abgebrochen.")
            return
        try:
            if index == 0:
                from cockpit.ui.branch_dialogs import BranchNameDialog
                dialog = BranchNameDialog("Neuer Branch", f"Ihre Änderungen kommen in diesen "
                                          f"neuen Branch. {main} bleibt, wie es ist.", code_dir,
                                          suggestion, self.window)
                if not dialog.exec():
                    announce("Hochladen abgebrochen.")
                    return
                if state.ahead:
                    branches.move_commits_to_new_branch(code_dir, dialog.name)
                else:
                    branches.create(code_dir, dialog.name)
            elif index <= len(others):
                branches.switch(code_dir, others[index - 1])
        except CockpitError as exc:
            show_error(self.window, self.title, exc.message, exc.details)
            self.refresh()
            return
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
        if data.get("commit"):
            # Für die Details im Verlauf (ENTSCHEIDUNGEN.md)
            history.record_steps(self.services.database, self.project.id, data["commit"],
                                 history.feature_step_lines(summary))
        if summary.completed:
            announce(summary.text())
            if self.then is not None:
                then, self.then = self.then, None
                then()
                return
            if data.get("version") and self.controller.releases.offer_after_version(
                    self.project, data["version"]):
                return                          # Release statt Pull Request (Phase 14)
            self.offer_pull_request(data.get("branch", ""))
            return
        if data.get("protected"):
            self.offer_new_branch(data["protected"])
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

    # -- 6. Pull Request (Phase 6c) --------------------------------------------------------------
    def offer_pull_request(self, branch: str) -> None:
        """Mit aktivem Feature nach dem Hochladen eines Branches einen Pull Request anbieten, wenn
        es für ihn noch keinen offenen gibt."""
        state = git.status(self.project.code_dir)
        if not branch or branch == state.default_branch or not self.pull_requests_active():
            return
        if self.services.pull_request_cache.count_for_branch(self.project.remote, branch):
            return
        if confirm(self.window, "Pull Request erstellen",
                   f"{branch} ist hochgeladen. Jetzt einen Pull Request erstellen, damit die "
                   f"Änderungen nach einer Prüfung in {state.default_branch} kommen?",
                   yes="Pull Request erstellen …", no="Später"):
            from cockpit.ui.pull_request_flow import PullRequestRunner
            PullRequestRunner(self.controller, self.project).create()

    def offer_new_branch(self, protected: str) -> None:
        """Die Plattform lässt in diesen Branch nichts direkt hochladen (Konzept 10.14)."""
        code_dir = self.project.code_dir
        text = (f"{self.platform_name} lässt in {protected} nichts direkt hochladen. Der Branch "
                "ist geschützt, Änderungen kommen nur über einen Pull Request hinein. Ihr Commit "
                "ist gespeichert, aber nicht hochgeladen. Das Cockpit kann die Commits in einen "
                "neuen Branch verschieben, ihn hochladen und einen Pull Request erstellen. "
                f"{protected} kommt dabei auf den Stand von {self.platform_name}. Ihre Dateien "
                "bleiben unverändert.")
        choice = ask_buttons(self.window, self.title, text,
                             ["In neuen Branch hochladen …", "Später"], default=1, escape=1)
        if choice != 0:
            return
        subject = git.run(["log", "-1", "--format=%s"], code_dir, check=False).stdout.strip()
        from cockpit.ui.branch_dialogs import BranchNameDialog
        dialog = BranchNameDialog("Neuer Branch", f"Die Commits, die noch nicht hochgeladen sind, "
                                  f"kommen in diesen Branch.", code_dir,
                                  branches.suggest_name(subject) or "neue-aenderung",
                                  self.window)
        if not dialog.exec():
            return
        try:
            branches.move_commits_to_new_branch(code_dir, dialog.name)
        except CockpitError as exc:
            show_error(self.window, self.title, exc.message, exc.details)
            return
        self.refresh()
        from cockpit.ui.pull_request_flow import PullRequestRunner
        runner = PullRequestRunner(self.controller, self.project)
        PushRunner(self.controller, self.project, confirmed=True, then=runner.create).start()


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
            self.after_merge(outcome, incoming.behind, incoming.branch)

        self.controller.run_task(self.key, work, done, self.title)

    def after_merge(self, outcome: MergeOutcome, behind: int = 0, branch: str = "") -> None:
        self.refresh()
        if outcome.kind is not ConflictKind.NONE:
            self.resolve(outcome.kind)
            return
        if behind:
            # Ansagen nennen den Branch, wenn es nicht der Haupt-Branch ist (Konzept 10.14)
            where = "" if not branch or branch == git.status(self.project.code_dir).default_branch \
                else f" in Branch {branch}"
            announce(f"Geholt: {count(behind, 'neuer Commit', 'neue Commits')} von "
                     f"{self.platform_name}{where}.")
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
        # Beim Übernehmen eines Branches ist die zweite Fassung die des Branches (Phase 5f)
        label = (sync.merge_source_label(code_dir, self.platform_name)
                 if kind is ConflictKind.MERGE else self.platform_name)
        dialog = sync_dialogs.ConflictDialog(code_dir, kind, label, self.window)
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
