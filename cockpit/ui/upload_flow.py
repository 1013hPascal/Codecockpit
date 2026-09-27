"""Ablauf "Auf GitHub hochladen" in der Oberfläche (Konzept 9.1).

Das Projekt ist schon in der Liste. Hinzufügen und Hochladen sind getrennt, es wird nie kopiert
(ENTSCHEIDUNGEN.md).

1. Konto wählen (bei mehreren), Tresor entsperren, Konto und Organisationen abfragen.
2. Angaben im UploadDialog.
3. Rückfrage, die genau beschreibt, was passiert.
4. Im Hintergrund: Git, .gitignore, LICENSE, Identität, Prüfung.
5. SafetyDialog, falls die Sicherheitsprüfung etwas findet.
6. Im Hintergrund der Ablauf NEW_PROJECT mit "Schritt 1 von 4: …".
7. Link in die Zwischenablage und eine Meldung mit OK.

Bricht etwas ab, bleibt das Projekt in der Liste. "Auf GitHub hochladen" setzt dort wieder an.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtGui import QGuiApplication

from cockpit.core import git, upload
from cockpit.core.errors import CockpitError
from cockpit.core.flows.engine import FlowContext
from cockpit.core.projects import Project
from cockpit.core.upload import UploadSpec
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import choose_from_list, confirm, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task
from cockpit.ui import upload_dialogs

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

log = logging.getLogger(__name__)

NO_ACCOUNT = ("Es ist noch kein Konto bei einer Plattform eingerichtet. Sie richten es im Menü "
              "Konten unter Kontenverwaltung ein.")


class UploadRunner:
    """Ein Durchlauf für ein Projekt, das noch nicht auf der Plattform ist."""

    def __init__(self, controller: "ProjectController", project: Project) -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services
        self.project = project
        self.account = None
        self.platform = None
        self.spec: UploadSpec | None = None
        # Qt hält Verbindungen zu Methoden nur schwach. Ohne diesen Verweis würde der Durchlauf
        # gelöscht, bevor die Antwort aus dem Hintergrund kommt.
        controller.upload = self
        self.title = f"{project.name} auf {self.window.project_list.platform_name} hochladen"

    # -- 1. Konto -------------------------------------------------------------------------
    def start(self) -> None:
        accounts = self.services.platform_accounts()
        if not accounts:
            show_error(self.window, self.title, NO_ACCOUNT)
            return
        if self.project.account_id is not None:
            accounts = [a for a in accounts if a.id == self.project.account_id] or accounts
        if len(accounts) > 1:
            index = choose_from_list(self.window, self.title, "Konten",
                                     [a.label for a in accounts])
            if index is None:
                return
            accounts = [accounts[index]]
        self.account = accounts[0]
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services, account_id = self.services, self.account.id

        def work(task: Task):
            platform = services.platform(account_id)
            user = platform.current_user()
            try:
                organizations = platform.organizations()
            except CockpitError:
                organizations = []
            return platform, user.login, organizations

        self.controller.run_task(f"upload-start:{account_id}", work, self.ask_details,
                                 self.title)

    # -- 2. und 3. Angaben und Rückfrage ----------------------------------------------------
    def ask_details(self, outcome) -> None:
        self.platform, user, organizations = outcome
        settings = self.services.settings.load()
        features = self.services.features
        offered = [(m.id, m.name) for m in features.visible_features()]
        from cockpit.ui import ai_suggest
        source = ai_suggest.for_description(self.services, self.project)
        dialog = upload_dialogs.UploadDialog(
            self.title, upload.suggest_name(self.project.name), self.window.project_list.platform_name,
            user, organizations, settings.default_private, settings.default_license,
            self.window, offered, features.project_features(self.project), source=source)
        if not dialog.exec() or dialog.spec is None:
            return
        self.spec = dialog.spec
        if self.spec.features is not None:
            # Was ein gewähltes Feature braucht, kommt mit (Konzept 8.4)
            needed = {d for f in self.spec.features
                      for d in self.services.registry.dependencies(f)}
            self.spec.features |= needed
        self.spec.account_id = self.account.id
        owner = self.spec.organization or user
        kind = "private" if self.spec.private else "öffentliche"
        parts = [f"Das Cockpit prüft den Code auf Geheimnisse, legt auf "
                     f"{self.window.project_list.platform_name} das {kind} Repository "
                     f"{owner}/{self.spec.name} an und lädt alles hoch. Vorher legt es bei Bedarf "
                     "die Dateien .gitignore und LICENSE an."]
        if not self.spec.private:
            parts.append("Öffentlich heißt: Jeder im Internet kann den Code sehen.")
        if not confirm(self.window, self.title, " ".join(parts) + " Hochladen?",
                       yes="Hochladen", no="Abbrechen"):
            return
        self.prepare()

    # -- 4. Vorbereiten ------------------------------------------------------------------------
    def prepare(self) -> None:
        services, spec, platform = self.services, self.spec, self.platform
        project = self.project
        settings = services.settings.load()
        asker = self.window.asker
        announce("Wird vorbereitet.")

        def work(task: Task):
            notes = upload.prepare(project.code_dir, project.name, spec, platform,
                                   settings.git_name, settings.git_email, asker)
            report = upload.scan(project.code_dir, spec, settings.git_email)
            return project, notes, report

        def done(outcome) -> None:
            self.project, notes, report = outcome
            self.window.reload_projects(refresh=False)
            self.window.show_project(self.project.id)
            for note in notes:
                announce(note, speak=False)
            self.check(report)

        self.controller.run_task(f"project:{project.id}", work, done, self.title)

    # -- 5. Sicherheitsprüfung ---------------------------------------------------------------
    def check(self, report) -> None:
        email = self.services.settings.load().git_email
        if report.findings:
            code_dir, spec = self.project.code_dir, self.spec
            dialog = upload_dialogs.SafetyDialog(
                report, code_dir, spec, email,
                rescan=lambda: upload.scan(code_dir, spec, email), parent=self.window)
            if not dialog.exec():
                announce(f"Hochladen abgebrochen. {self.project.name} ist in der Liste. Mit "
                         f"Auf {self.window.project_list.platform_name} hochladen geht es "
                         "später weiter.")
                self.window.refresh_status([self.project.id])
                return
            self.spec.accepted |= dialog.accepted
        self.run_flow(email)

    # -- 6. Ablauf ---------------------------------------------------------------------------
    def run_flow(self, email: str) -> None:
        services, project, spec, platform = self.services, self.project, self.spec, self.platform
        asker = self.window.asker

        def work(task: Task):
            context = FlowContext(services, project, asker, task.cancel_event,
                                  data={"spec": spec, "platform": platform, "git_email": email})
            summary = services.flows.run(upload.NEW_PROJECT, context,
                                         lambda n, total, text: task.status.emit(text + " …"))
            return summary, context.data

        self.controller.run_task(f"project:{project.id}", work, self.finished, self.title,
                                 on_status=announce)

    # -- 7. Ergebnis -------------------------------------------------------------------------
    def finished(self, outcome) -> None:
        summary, data = outcome
        project = self.project
        self.window.refresh_status([project.id])
        if not summary.completed:
            failure = summary.results[-1][1] if summary.results else None
            show_error(self.window, self.title, summary.text(),
                       failure.details if failure else "")
            return
        from cockpit.platforms.base import RepoRef
        address = git.parse_remote(data.get("remote_url", ""))
        ref = data.get("repo") or (RepoRef(address.owner, address.name) if address else None)
        link = self.platform.links(ref).project_page if ref is not None else ""
        self.services.projects.set_account(project, self.spec.account_id)
        self.services.projects.set_remote(project, git.parse_remote(link) or address,
                                          datetime.now().isoformat(timespec="seconds"))
        text = summary.text()
        if link:
            QGuiApplication.clipboard().setText(link)
            text += f" Der Link {link} ist in der Zwischenablage."
        self.window.reload_projects(refresh=False)
        self.window.show_project(project.id)
        self.window.refresh_status([project.id])
        self.window.refresh_remote()
        announce(text, speak=False)
        show_info(self.window, self.title, text)
