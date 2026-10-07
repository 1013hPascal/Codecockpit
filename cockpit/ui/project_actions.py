"""Aktionen rund um Projekte, die Dialoge oder Hintergrund-Arbeit brauchen (Phase 5a).

Der Kern (cockpit.core) kennt kein Qt. Deshalb stehen Aktionen mit Rückfragen, Ordnerwahl und
Hintergrund-Aufgaben hier in der Oberfläche. Sie kommen auf demselben Weg in die Aktionsliste wie
die Aktionen des Kerns und der Features.

- Projekt vom Rechner hinzufügen: Projektordner, in den Hauptordner verschieben oder am Ort
  lassen. Danach auf Wunsch gleich auf GitHub hochladen.
- Projekt von GitHub herunterladen: eigene Repositories, die der Organisationen oder eine Adresse.
- Neuen Ort angeben (Projekt, nur wenn der Ordner fehlt).
- Mit vorhandenem Repository verbinden (Code, nur wenn der Git-Ordner fehlt).
- Virtuelle Umgebung neu anlegen (Code, nur wenn sie nach dem Verschieben kaputt ist).
- Herunterladen und Auf GitHub öffnen (Repository, das nur auf der Plattform liegt).
- Änderungen hochladen, Änderungen holen und Konflikte lösen (Code, ab Phase 5c, sync_flow.py).
- Verlauf und Änderungen verwerfen (Code, ab Phase 5d, history_dialogs.py).
- Links, Repository verwalten und Aus der Liste entfernen (Projekt, ab Phase 5e, repo_dialogs.py).
- Branches, Beiseitelegen und beiseitegelegte Änderungen (Code, ab Phase 5f, branch_dialogs.py).

Reihenfolge der Aktionen nach dem Wunsch des Nutzers (30.09.2026):
- Main-Branch: Projekt neu einlesen, Terminal, Änderungen hochladen, Änderungen holen, Pull
  Requests, Verlauf, Änderungen verwerfen, Änderungen beiseitelegen, Git-Identität, Code-Ordner.
- Branch: wie Main-Branch, aber "Pull Request erstellen" und "Pull-Requests-Übersicht".
- Projekt: Projekt neu einlesen, Terminal, Projekt verwalten, Links, README, Lizenz, Features dieses
  Projekts, Aus der Liste entfernen, Projektordner öffnen.
- Die Branches selbst verwaltet die Zeile "Branches verwalten" unter dem Haupt-Branch.
Aktionen, die nur manchmal passen (Konflikte lösen, Neuen Ort angeben ...), erscheinen nur dann.

Alles, was Dateien verändert, beschreibt vorher, was passiert, und braucht eine Bestätigung.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from cockpit.core import (core_actions, git, history, identity, project_setup, repo_admin,
                          venv_repair)
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.availability import Availability
from cockpit.core.errors import CockpitError
from cockpit.core.projects import (CODE_DIR, EXE_DIR, FLAT, GIT_OUTSIDE, MAIN_DIR, Project,
                                   classify_folder, code_root_in, fix_git_outside,
                                   layout_problem, nest_code, same_drive)
from cockpit.core.remote_repos import StoredRepo
from cockpit.core.text import count
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import (ask_buttons, choose_from_list, confirm, pick_folder,
                               show_info)
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

log = logging.getLogger(__name__)

ENTER_ADDRESS = "Adresse eingeben …"


class ProjectController:
    """Führt die Projekt-Aktionen für das Hauptfenster aus."""

    def __init__(self, window: "MainWindow") -> None:
        self.window = window
        self.services = window.services
        self.busy: set[str] = set()               # laufende Vorgänge, zum Beispiel "clone:3"
        self.tasks: list[Task] = []
        self.upload = None                        # laufendes Hochladen (UploadRunner)
        self.pull_runner = None                   # laufender Ablauf für Pull Requests
        self.missing_repos: set[int] = set()      # Adresse da, Repository fehlt (04.10.2026)
        from cockpit.ui.exe_flow import ExeActions
        self.exe = ExeActions(self)                # Phase 10
        from cockpit.ui.worktree_flow import WorktreeActions
        self.worktrees = WorktreeActions(self)     # Phase 10f
        from cockpit.ui.readme_flow import ReadmeActions
        self.readme = ReadmeActions(self)          # Phase 9
        from cockpit.ui.license_flow import LicenseActions
        self.licenses = LicenseActions(self)       # Wunsch vom 03.10.2026
        from cockpit.ui.releases_flow import ReleasesActions
        self.releases = ReleasesActions(self)      # Phase 14
        from cockpit.ui.collections_flow import CollectionActions
        self.collections = CollectionActions(self)  # Projektsammlungen
        from cockpit.ui.project_manage import ProjectManager
        self.project_manager = ProjectManager(self)  # Projekt verwalten (06.10.2026)
        from cockpit.ui.release_rows import ReleaseRowActions
        self.release_rows = ReleaseRowActions(self)  # Zeile Releases (06.10.2026)
        from cockpit.ui.folder_rename_flow import FolderRenamer
        self.folder_renamer = FolderRenamer(self)   # Code und Exe umbenennen (06.10.2026)

    # -- Aktionen für die Aktionsliste -----------------------------------------------------
    def actions(self) -> list[Action]:
        platform_name = self.window.project_list.platform_name
        # Wunsch des Nutzers (06.10.2026): beim Repository und bei den Branches "Repository neu
        # einlesen"
        reread = [Action(f"reread_{target.value}", text, target, self.reread_action,
                         visible=lambda c: c.project is not None, order=1)
                  for target, text in ((Target.PROJECT, "Projekt neu einlesen"),
                                       (Target.REPOSITORY, "Repository neu einlesen"),
                                       (Target.CODE, "Repository neu einlesen"),
                                       (Target.RELEASES, "Releases neu einlesen"),
                                       (Target.EXE, "Releases neu einlesen"),
                                       (Target.RELEASE, "Releases neu einlesen"))]
        on_main = lambda c: c.worktree is None                          # noqa: E731
        found = lambda c: c.project is not None and c.project.folder_found  # noqa: E731
        return reread + [
            Action("branch_show", "Branches anzeigen …", Target.REPOSITORY,
                   self.branch_show_action, detail=self._branch_show_detail, is_default=True,
                   order=0),
            Action("terminal_repository", "Terminal …", Target.REPOSITORY,
                   lambda c: self.terminal_action(c, c.project.code_root, "Repository"),
                   visible=found, order=5),
            Action("manage_project", "Projekt verwalten …", Target.PROJECT,
                   self.project_manager.manage, visible=lambda c: c.project is not None,
                   order=20),
            Action("open_repo_remote", f"Auf {platform_name} öffnen", Target.REPOSITORY,
                   self.open_repo_remote_action, visible=_has_remote, order=88),
            Action("add_local", "Projekt vom Rechner hinzufügen …", Target.ADD_LOCAL,
                   lambda c: self.add_local(), is_default=True, order=10),
            Action("add_remote", f"Projekt von {platform_name} herunterladen …",
                   Target.ADD_REMOTE, lambda c: self.add_remote(),
                   availability=self._upload_availability, is_default=True, order=10),
            Action("upload_existing", f"Auf {platform_name} hochladen …", Target.CODE,
                   self.upload_action, availability=self._upload_availability,
                   visible=self._needs_repo, is_default=True, order=10),
            # Wunsch des Nutzers (04.10.2026): auch auf der Projektzeile, gut sichtbar oben
            Action("create_repo", f"Repository auf {platform_name} anlegen und hochladen …",
                   Target.PROJECT, self.upload_action, availability=self._upload_availability,
                   visible=self._needs_repo, order=3),
            Action("resolve_conflicts", "Konflikte lösen …", Target.CODE, self.resolve_action,
                   visible=_unfinished_merge, is_default=True, order=2),
            Action("push_changes", f"Änderungen auf {platform_name} hochladen …", Target.CODE,
                   self.push_action, detail=_push_detail,
                   availability=_git_availability,
                   visible=lambda c: _on_platform(c) and not _branch_unpublished(c)
                   and not self._repo_missing(c), is_default=True, order=10),
            # Wunsch aus dem Test von 10f: Ein Branch, den es auf der Plattform noch nicht gibt,
            # sagt das in der Aktion. Sie lädt ihn hoch, mit den Änderungen, falls es welche gibt.
            Action("publish_branch", f"Branch auf {platform_name} hochladen …", Target.CODE,
                   self.push_action, availability=_git_availability,
                   visible=_branch_unpublished, is_default=True, order=10),
            Action("pull_changes", f"Änderungen von {platform_name} holen …", Target.CODE,
                   self.pull_action, availability=_git_availability, detail=_pull_detail,
                   visible=lambda c: _on_platform(c) and not _branch_unpublished(c), order=20),
            # Seit dem 06.10.2026 eine Aktion des Repositorys (Wunsch des Nutzers)
            Action("branches", "Branches verwalten …", Target.REPOSITORY,
                   self.branches_action, availability=_git_availability,
                   visible=_has_commits, order=25),
            Action("create_pull", "Pull Request erstellen …", Target.CODE,
                   self.create_pull_action, availability=self._account_availability,
                   visible=_on_other_branch, order=26),
            Action("pull_requests", "Pull Requests …", Target.CODE, self.pull_requests_action,
                   availability=self._account_availability, detail=self._all_pulls_detail,
                   visible=lambda c: _has_remote(c) and on_main(c), order=27),
            Action("pull_requests_branch", "Pull-Requests-Übersicht …", Target.CODE,
                   self.pull_requests_action, availability=self._account_availability,
                   detail=_branch_pulls_detail,
                   visible=lambda c: _has_remote(c) and not on_main(c), order=27),
            Action("stash_push", "Änderungen beiseitelegen …", Target.CODE, self.stash_push_action,
                   availability=_discard_availability, visible=_has_commits, order=36,
                   detail=_changed_detail),
            Action("stashes", "Beiseitegelegte Änderungen …", Target.CODE, self.stashes_action,
                   visible=_has_stashes, order=37),
            Action("history", "Verlauf …", Target.CODE, self.history_action,
                   availability=_git_availability, visible=_is_repo, order=30),
            Action("discard", "Änderungen verwerfen …", Target.CODE, self.discard_action,
                   availability=_discard_availability, visible=_is_repo, order=35,
                   detail=_changed_detail),
            Action("project_features", "Features dieses Projekts …", Target.PROJECT,
                   self.project_features_action, availability=self._features_availability,
                   visible=found, order=30),
            Action("terminal_project", "Terminal …", Target.PROJECT,
                   lambda c: self.terminal_action(c, c.project.project_dir, ""),
                   visible=found, order=10),
            Action("terminal_code", "Terminal …", Target.CODE,
                   lambda c: self.terminal_action(c, c.project.code_dir,
                                                  c.worktree.branch if c.worktree else "Code"),
                   visible=found, order=5),
            Action("links", "Links …", Target.REPOSITORY, self.links_action,
                   availability=self._account_availability, visible=_has_remote, order=30),
            # "Projekt verwalten …" hieß bis zum 06.10.2026 das, was jetzt beim Repository steht
            Action("manage_repo", "Repository verwalten …", Target.REPOSITORY,
                   self.manage_action, availability=self._account_availability,
                   visible=_has_remote, order=20),
            # Wunsch des Nutzers (02.10.2026): löschen, ohne vorher herunterzuladen
            Action("delete_remote_repo", "Repository löschen …", Target.REMOTE_REPO,
                   self.delete_remote_action, availability=self._remote_account_availability,
                   order=85),
            Action("hide_remote", "Aus der Liste entfernen …", Target.REMOTE_REPO,
                   self.hide_remote_action, order=90),
            Action("relocate", "Neuen Ort angeben …", Target.PROJECT, self.relocate_action,
                   visible=lambda c: c.project is not None and not c.project.folder_found,
                   order=5),
            Action("connect_repo", "Mit vorhandenem Repository verbinden …", Target.CODE,
                   self.connect_action, visible=_git_missing, order=40),
            Action("git_identity", "Repository-Identität …", Target.REPOSITORY,
                   self.identity_action, visible=_is_repo, order=85),
            Action("repair_venv", "Virtuelle Umgebung neu anlegen …", Target.CODE,
                   self.repair_venv_action, visible=_venv_broken, order=45),
            Action("download", "Herunterladen", Target.REMOTE_REPO, self.download_action,
                   availability=self._download_availability, is_default=True, order=10),
            Action("open_remote", f"Auf {platform_name} öffnen",
                   Target.REMOTE_REPO, self.open_remote_action, order=20),
        ] + self.exe.actions() + self.worktrees.actions() + self.readme.actions() \
            + self.licenses.actions() + self.releases.actions() + self.collections.actions() \
            + self.release_rows.actions() + self.folder_renamer.actions()

    # -- Hintergrund ------------------------------------------------------------------------
    def run_task(self, key: str, work: Callable[[Task], object],
                 done: Callable[[object], None], failed_title: str,
                 on_status: Callable[[str], None] | None = None,
                 on_failed: Callable[[], None] | None = None, transfer: bool = False) -> None:
        """work läuft im Hintergrund. done und Fehlermeldungen kommen im Thread der Oberfläche.
        transfer: Hoch- oder Herunterladen, mit Tönen (Wunsch des Nutzers vom 07.10.2026)."""
        if key in self.busy:
            announce("Das läuft schon.")
            return
        self.busy.add(key)
        task = Task(work, self.window)
        from cockpit.ui.sounds import TransferSound
        sound = TransferSound(transfer and self.services.settings.load().transfer_sounds,
                              task)

        def finish() -> None:
            self.busy.discard(key)
            if task in self.tasks:
                self.tasks.remove(task)
            task.wait()                      # Thread ganz beendet, sonst bricht Qt ab
            task.deleteLater()

        def failed(message: str, details: str) -> None:
            self.busy.discard(key)
            # Mit Details ins Protokoll (Wunsch aus dem Test von 10f: der Grund stand nirgends)
            log.warning("%s: %s %s", failed_title, message, details)
            sound.finish(False)
            if on_failed is not None:
                on_failed()
            announce(message, urgent=True)
            show_error(self.window, failed_title, message, details)

        def result(value) -> None:
            self.busy.discard(key)          # done darf gleich den nächsten Schritt starten
            sound.finish(True)
            done(value)

        task.result.connect(result)
        task.error.connect(failed)
        if on_status is not None:
            task.status.connect(on_status)
        task.cancelled.connect(lambda: (sound.stop(), announce("Abgebrochen.")))
        task.finished.connect(finish)
        self.tasks.append(task)
        sound.start()
        task.start()

    def wait(self) -> None:
        """Beim Schließen: laufende Aufgaben abbrechen und auf sie warten."""
        for task in list(self.tasks):
            task.cancel()
            task.wait(5000)

    # -- Projekt neu einlesen ----------------------------------------------------------------
    def reread_action(self, context: ActionContext) -> None:
        """Stand dieses einen Projekts neu abfragen (Wunsch aus dem Test von 5c). Im Menü Datei
        steht weiter "Projekte neu einlesen" für alle."""
        name, project_id = context.project.name, context.project.id
        if not self.check_layout(context.project, lambda project: None):
            return
        self.check_repo(context.project, ask=True)
        self.window.reload_projects(refresh=False)
        self.window.refresh_status([project_id],
                                   on_done=lambda: announce(f"{name} neu eingelesen."))

    # -- Aufbau Projektordner\\Repository\\main und Exe (Wunsch des Nutzers vom 04.10.2026) ----------
    def check_layout(self, project: Project, then: Callable[[Project], None]) -> bool:
        """Passt der Aufbau nicht, die Reparatur anbieten. Danach then(Projekt). False, wenn das
        im Hintergrund weiterläuft (then kommt dann später)."""
        if project.linked or not project.folder_found:
            then(project)
            return True
        code_root = code_root_in(project.project_dir)
        problem = layout_problem(code_root)
        title = "Aufbau des Projekts"
        if problem == GIT_OUTSIDE:
            if confirm(self.window, title, f"Bei {project.name} liegt der Code in "
                       f"{code_root.name}\\{MAIN_DIR}, der Git-Ordner .git aber noch direkt in "
                       f"{code_root.name}. Darum sieht das Cockpit den Code noch in "
                       f"{code_root.name}. Das Cockpit verschiebt .git nach "
                       f"{code_root.name}\\{MAIN_DIR}. Am Code ändert sich nichts. Verschieben?",
                       yes="Verschieben", no="So lassen"):
                try:
                    project = self.services.projects.set_code_dir(project,
                                                                  fix_git_outside(code_root))
                    announce(f"Der Code liegt jetzt in {code_root.name}\\{MAIN_DIR}.")
                except CockpitError as exc:
                    show_error(self.window, title, exc.message, exc.details)
        elif problem == FLAT and self.services.settings.load().branch_folders:
            intro = (f"Bei {project.name} liegt der Code direkt im Ordner {code_root.name}. "
                     f"Richtig ist Projektordner, darin {CODE_DIR} und {EXE_DIR}, und in "
                     f"{CODE_DIR} der Ordner {MAIN_DIR} mit dem Code. ")
            from cockpit.core import worktrees
            if worktrees.can_convert(project):
                # Abbrechen lässt den Aufbau, wie er ist, und macht mit then weiter
                if self.worktrees.convert(project, intro,
                                          lambda moved: then(self._exe_dir(moved))):
                    return False
            elif confirm(self.window, title, intro + f"Das Cockpit verschiebt den Code nach "
                       f"{code_root.name}\\{MAIN_DIR}. Nur der Ort ändert sich, der Inhalt bleibt. "
                       "Verschieben?", yes="Verschieben", no="So lassen"):
                try:
                    project = self.services.projects.set_code_dir(project, nest_code(code_root))
                    announce(f"Der Code liegt jetzt in {code_root.name}\\{MAIN_DIR}.")
                except CockpitError as exc:
                    show_error(self.window, title, exc.message, exc.details)
        then(self._exe_dir(project))
        return True

    def _exe_dir(self, project: Project) -> Project:
        """Neben Code gehört der Ordner Release. Fehlt er, legt ihn das Cockpit leer an."""
        if not project.linked and project.exe_dir is not None and not project.exe_dir.exists():
            try:
                project.exe_dir.mkdir(parents=True)
                announce("Ordner Release angelegt.")
            except OSError as exc:
                log.warning("Ordner Release nicht angelegt: %s", exc)
        return project

    # -- Projekt vom Rechner hinzufügen ------------------------------------------------------
    def add_local(self) -> None:
        root = self.services.settings.load().projects_root
        # Wunsch des Nutzers (04.10.2026): Der Titel sagt, welcher Aufbau gemeint ist
        folder = pick_folder(self.window, "Projektordner wählen, darin Code und Exe, in Code der "
                             "Ordner main", root)
        if folder is None:
            return
        kind, project_dir = classify_folder(folder)
        if kind == "project":
            existing = self.services.projects.find_by_dir(project_dir)
            if existing is not None:
                self.window.show_project(existing.id)
                announce(f"{existing.name} ist schon in der Liste.")
                self.check_layout(existing, lambda project: self.window.reload_projects(
                    refresh=False))
                return
            self.check_layout(self.services.projects.add(project_dir), self._added)
            return
        self._add_other(folder, Path(root))

    def _add_other(self, folder: Path, root: Path) -> None:
        text = (f"Der Ordner {folder.name} hat keinen Unterordner Repository. "
                f"In den Projekte-Hauptordner verschieben: Das Cockpit legt den Projektordner "
                f"{root / folder.name} an und verschiebt den gewählten Ordner dorthin als Code. "
                f"Am Ort lassen: Der Ordner bleibt, wo er ist. Das Cockpit merkt sich nur, wo er "
                f"liegt. Das passt auch für Repositories, deren Aufbau Sie nicht ändern dürfen.")
        choice = ask_buttons(self.window, "Projekt vom Rechner hinzufügen", text,
                             ["In den Projekte-Hauptordner verschieben …", "Am Ort lassen …",
                              "Abbrechen"], default=2, escape=2)
        if choice == 0:
            self._convert(folder, root)
        elif choice == 1:
            self._link(folder)

    def _convert(self, folder: Path, root: Path) -> None:
        from cockpit.core import worktrees
        target = root / folder.name
        # Phase 10f: Ein Git-Ordner kommt gleich nach Repository\<Branch>, wenn so eingestellt
        inner = ""
        if self.services.settings.load().branch_folders:
            # Ohne Git heißt der Ordner main (Wunsch des Nutzers vom 04.10.2026)
            inner = MAIN_DIR
            if (folder / ".git").is_dir():
                state = git.status(folder)
                inner = worktrees.folder_name(state.branch or state.default_branch)
        destination = target / CODE_DIR / inner if inner else target / CODE_DIR
        if same_drive(folder, root):
            how = (f"Der Ordner {folder} wird nach {destination} verschoben. Sein Inhalt "
                   "bleibt unverändert, nur der Ort ändert sich.")
        else:
            how = (f"Der Ordner liegt auf einem anderen Laufwerk. Deshalb wird er nach "
                   f"{destination} kopiert. Der alte Ordner {folder} bleibt unverändert, "
                   "Sie können ihn später selbst löschen.")
        if inner:
            how += " Jeder weitere Branch bekommt einen eigenen Ordner daneben."
        how += f" Daneben entsteht der Ordner {target / EXE_DIR}."
        if not confirm(self.window, "Verschieben", f"{how} Verschieben?", yes="Verschieben",
                       no="Abbrechen"):
            return
        try:
            project, moved = self.services.projects.convert(folder, root, inner)
        except CockpitError as exc:
            show_error(self.window, "Verschieben", exc.message, exc.details)
            return
        self._added(self._exe_dir(project))

    def _link(self, folder: Path) -> None:
        exe_dir = None
        if confirm(self.window, "Am Ort lassen", f"Der Code-Ordner ist {folder}. Gibt es "
                   "zu diesem Projekt auch einen Exe-Ordner?", yes="Exe-Ordner wählen …",
                   no="Ohne Exe-Ordner"):
            exe_dir = pick_folder(self.window, "Exe-Ordner wählen", str(folder.parent))
        try:
            project = self.services.projects.add_linked(folder, exe_dir)
        except CockpitError as exc:
            show_error(self.window, "Am Ort lassen", exc.message, exc.details)
            return
        self._added(project)

    def _added(self, project: Project) -> None:
        self.ensure_identity(project)
        self.window.reload_projects(refresh=False)
        self.window.show_project(project.id)
        self.window.refresh_status([project.id])
        announce(f"{project.name} hinzugefügt.")
        self.offer_upload(project)

    def offer_upload(self, project: Project) -> None:
        """Liegt das Projekt noch nicht auf der Plattform, gleich das Hochladen anbieten.
        Vorgabe ist "Später"."""
        on_platform = git.is_repo(project.code_dir) and bool(
            git.config_get(project.code_dir, "remote.origin.url"))
        if on_platform:
            self.check_repo(project, ask=True)        # Adresse da, aber gibt es das Repository?
            return
        if not self._upload_availability(None).available:
            return
        name = self.window.project_list.platform_name
        if confirm(self.window, f"Auf {name} hochladen",
                   f"{project.name} ist noch nicht auf {name}. Jetzt hochladen? Sie können das "
                   f"auch später bei Code mit der Aktion Auf {name} hochladen machen.",
                   yes="Jetzt hochladen …", no="Später"):
            from cockpit.ui.upload_flow import UploadRunner
            UploadRunner(self, project).start()

    def ensure_identity(self, project: Project) -> None:
        settings = self.services.settings.load()
        try:
            identity.ensure(project.code_dir, project.name, settings.git_name,
                            settings.git_email, self.window.asker)
        except CockpitError as exc:
            log.warning("Git-Identität für %s: %s %s", project.name, exc.message, exc.details)

    def identity_action(self, context: ActionContext) -> None:
        """Git-Identität des Projekts anzeigen und bei Bedarf die aus den Grundeinstellungen
        übernehmen (Wunsch aus dem Test von Phase 5a)."""
        project = context.project
        settings = self.services.settings.load()
        name, email = settings.git_name, settings.git_email
        title = f"Git-Identität von {project.name}"
        current = identity.state(project.code_dir, name, email)
        own = ", ".join(v for v in git.identity(project.code_dir) if v)
        if current is identity.IdentityState.NOT_SET:
            text = f"Eingetragen: {own}." if own else "Im Projekt ist keine eingetragen."
            show_info(self.window, title, f"{text} In den Grundeinstellungen fehlen Name oder "
                      "E-Mail-Adresse. Sie stehen im Menü Einstellungen unter "
                      "Grundeinstellungen.")
            return
        if current is identity.IdentityState.SAME:
            show_info(self.window, title, f"{own}. Das ist die Identität aus den "
                      "Grundeinstellungen.")
            return
        if current is identity.IdentityState.MISSING:
            text = (f"{project.name} hat noch keine eigene Git-Identität. In den "
                    f"Grundeinstellungen steht: {name}, {email}. Übernehmen?")
        else:
            text = (f"Eingetragen: {own}. In den Grundeinstellungen steht: {name}, {email}. "
                    "Soll das Projekt die Identität aus den Grundeinstellungen bekommen?")
        if confirm(self.window, title, text, yes="Grundeinstellungen übernehmen",
                   no="Vorhandene behalten"):
            git.set_identity(project.code_dir, name, email)
            announce(f"Git-Identität von {project.name}: {name}, {email}.")

    # -- Hochladen (Konzept 9.1) -------------------------------------------------------------
    # -- Repository fehlt auf der Plattform (Wunsch des Nutzers vom 04.10.2026) -------------
    def _repo_missing(self, context: ActionContext) -> bool:
        return context.project is not None and context.project.id in self.missing_repos

    def _needs_repo(self, context: ActionContext) -> bool:
        return _not_on_platform(context) or (self._repo_missing(context)
                                             and context.project.folder_found)

    def check_repo(self, project: Project, ask: bool) -> None:
        """Im Hintergrund nachsehen, ob es das Repository auf der Plattform gibt. Fehlt es,
        steht "Repository … anlegen und hochladen …" in den Aktionen. ask: dann auch fragen."""
        if not (project.folder_found and git.is_repo(project.code_dir)
                and git.config_get(project.code_dir, "remote.origin.url")):
            if ask:
                self.offer_upload(project)
            return
        if not self.services.platform_accounts() or \
                not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services = self.services

        def done(missing: bool) -> None:
            if missing:
                self.missing_repos.add(project.id)
            else:
                self.missing_repos.discard(project.id)
            self.window.refresh_actions(keep_selection=True)
            if missing and ask:
                self.offer_create(project)

        self.run_task(f"repo-check:{project.id}",
                      lambda task: repo_admin.repo_missing(services, project), done,
                      "Repository prüfen")

    def offer_create(self, project: Project) -> None:
        name = self.window.project_list.platform_name
        remote = project.remote
        where = f"{remote.owner}/{remote.name}" if remote is not None else project.name
        if confirm(self.window, f"Auf {name} hochladen",
                   f"Das Repository {where} gibt es auf {name} noch nicht. Jetzt anlegen und "
                   f"hochladen? Sie können das auch später mit der Aktion Repository auf {name} "
                   "anlegen und hochladen machen.", yes="Jetzt anlegen …", no="Später"):
            from cockpit.ui.upload_flow import UploadRunner
            UploadRunner(self, project).start()

    def _upload_availability(self, context: ActionContext) -> Availability:
        if git.find_git() is None:
            return Availability.no("Git ist nicht installiert.")
        if not self.services.platform_accounts():
            return Availability.no("Es ist noch kein Konto bei einer Plattform eingerichtet.")
        return Availability.yes()

    def add_remote(self) -> None:
        """Projekt von der Plattform herunterladen: eigene Repositories und die der
        Organisationen, neueste oben, dazu "Adresse eingeben …"."""
        accounts = self.services.platform_accounts()
        if not accounts:
            return
        if len(accounts) > 1:
            index = choose_from_list(self.window, "Konto wählen", "Konten",
                                     [a.label for a in accounts])
            if index is None:
                return
            accounts = [accounts[index]]
        account = accounts[0]
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services = self.services
        local = {p.remote.key for p in services.projects.all() if p.remote is not None}
        announce("Repositories werden abgefragt.")

        def work(task: Task) -> list:
            platform = services.platform(account.id)
            repos = list(platform.repositories())
            try:
                organizations = platform.organizations()
            except CockpitError:
                organizations = []
            for organization in organizations:
                try:
                    repos.extend(platform.repositories(organization))
                except CockpitError as exc:
                    log.warning("Repositories von %s: %s", organization, exc.message)
            return sorted(repos, key=lambda r: r.pushed_at, reverse=True)

        def done(repos: list) -> None:
            self.choose_remote(account, [r for r in repos if _key(r) not in local])

        self.run_task(f"remote-list:{account.id}", work, done, "Herunterladen")

    def choose_remote(self, account, repos: list) -> None:
        from datetime import datetime
        from urllib.parse import urlparse
        name = self.window.project_list.platform_name

        def line(repo) -> str:
            parts = [repo.ref.name, repo.ref.owner, "privat" if repo.private else "öffentlich"]
            try:
                pushed = datetime.fromisoformat(repo.pushed_at.replace("Z", "+00:00"))
                parts.append(f"aktualisiert am {pushed:%d.%m.%Y}")
            except ValueError:
                pass
            return ", ".join(parts)

        # "Adresse eingeben …" steht oben (Wunsch aus dem Test von 5b)
        items = [ENTER_ADDRESS] + [line(r) for r in repos]
        index = choose_from_list(self.window, f"Projekt von {name} herunterladen",
                                 "Repositories", items)
        if index is None:
            return
        if index > 0:
            repo = repos[index - 1]
            host = (urlparse(repo.web_url or repo.clone_url).hostname or "").lower()
            stored = StoredRepo(0, account.id, host, repo.ref.owner, repo.ref.name,
                                repo.private, repo.clone_url, repo.web_url, repo.pushed_at)
        else:
            from PySide6.QtWidgets import QInputDialog
            url, ok = QInputDialog.getText(self.window, f"Projekt von {name} herunterladen",
                                           "Adresse des Repositories:")
            address = git.parse_remote(url) if ok else None
            if address is None:
                if ok:
                    show_error(self.window, "Herunterladen", "Die Adresse wurde nicht erkannt. "
                               "Beispiel: https://github.com/Name/Projekt")
                return
            match = self.services.account_for_host(address.host)
            stored = StoredRepo(0, match.id if match else None, address.host, address.owner,
                                address.name, True, url.strip(), "", "")
        self.download(stored)

    def upload_action(self, context: ActionContext) -> None:
        from cockpit.ui.upload_flow import UploadRunner
        UploadRunner(self, context.project).start()

    # -- Änderungen hochladen und holen (Konzept 9.2 und 9.3) ---------------------------------
    def push_action(self, context: ActionContext) -> None:
        from cockpit.ui.sync_flow import PushRunner
        PushRunner(self, context.project).start()

    def pull_action(self, context: ActionContext) -> None:
        from cockpit.ui.sync_flow import PullRunner
        PullRunner(self, context.project).start()

    def resolve_action(self, context: ActionContext) -> None:
        from cockpit.core import sync
        from cockpit.ui.sync_flow import PullRunner
        kind = sync.conflict_kind(context.project.code_dir)
        if kind is sync.ConflictKind.NONE:
            self.window.refresh_status([context.project.id])
            announce("Es gibt keine Konflikte mehr.")
            return
        PullRunner(self, context.project).resolve(kind)

    # -- Verlauf und Rückgängig machen (Konzept 9.4 und 9.7) -------------------------------
    def history_action(self, context: ActionContext) -> None:
        project = context.project
        services, window = self.services, self.window

        def work(task: Task) -> list:
            return history.log_commits(project.code_dir)

        def done(commits: list) -> None:
            from cockpit.ui.history_dialogs import HistoryDialog
            dialog = HistoryDialog(services, project, commits, window)
            dialog.exec()
            if dialog.changed:
                window.refresh_status([project.id])

        self.run_task(f"project:{project.id}", work, done, "Verlauf")

    def discard_action(self, context: ActionContext) -> None:
        from cockpit.ui.history_dialogs import DiscardDialog
        project = context.project
        title = "Änderungen verwerfen"
        try:
            changes = history.local_changes(project.code_dir)
        except CockpitError as exc:
            show_error(self.window, title, exc.message, exc.details)
            return
        if not changes:
            self.window.refresh_status([project.id])
            announce("Es gibt keine Änderungen ohne Commit.")
            return
        dialog = DiscardDialog(project.name, changes, self.window)
        if not dialog.exec():
            return
        try:
            history.discard(project.code_dir, project.name, dialog.chosen)
        except CockpitError as exc:
            show_error(self.window, title, exc.message, exc.details)
            self.window.refresh_status([project.id])
            return
        self.window.refresh_status([project.id])
        announce(f"{count(len(dialog.chosen), 'Änderung', 'Änderungen')} verworfen.")

    # -- Branches und beiseitegelegte Änderungen (Konzept 10.14) ----------------------------
    def branches_action(self, context: ActionContext) -> None:
        from cockpit.core import branches, sync, worktrees
        # Mit Branch-Ordnern arbeitet die Übersicht immer im Ordner des Haupt-Branches (10f)
        project = context.main_project or context.project
        on_platform = bool(git.config_get(project.code_dir, "remote.origin.url"))
        needs_account = project.account_id is not None or (
            project.remote is not None
            and self.services.account_for_host(project.remote.host) is not None)
        if on_platform and needs_account and not vault_ui.ensure_unlocked(self.services,
                                                                          self.window):
            return
        services, window = self.services, self.window
        platform_name = window.project_list.platform_name

        def work(task: Task):
            env = sync.environment(services, project) if on_platform else {}
            note = ""
            try:
                branches.refresh(project.code_dir, env, task.cancel_event)
            except CockpitError as exc:
                log.warning("Branches von %s nicht abgefragt: %s", project.name, exc.message)
                note = f"Stand von {platform_name} nicht abgefragt. {exc.message}"
            items = branches.list_branches(project.code_dir)
            refresh_pulls_for(services, project)
            for item in items:
                item.open_pulls = services.pull_request_cache.count_for_branch(project.remote,
                                                                               item.name)
            folders = {t.branch: t.folder for t in worktrees.list_worktrees(project)}
            return env, items, note, folders

        def done(outcome) -> None:
            from cockpit.ui.branch_dialogs import BranchesDialog
            env, items, note, folders = outcome
            if note:
                announce(note)
            dialog = BranchesDialog(project, items, env, platform_name, window, folders)
            dialog.exec()
            window.refresh_status([project.id])
            if dialog.new_request:
                self.worktrees.create(project, dialog.new_request)
            elif dialog.open_request:
                self.worktrees.open_folder_for(project, dialog.open_request)
            elif getattr(dialog, "rename_main_request", ""):
                self.worktrees.rename_main(project, dialog.main, dialog.rename_main_request, env)
            elif getattr(dialog, "delete_request", ""):
                tree = next((t for t in worktrees.list_worktrees(project)
                             if t.branch == dialog.delete_request), None)
                if tree is not None:
                    self.worktrees.delete(project, tree, env)

        self.run_task(f"project:{project.id}", work, done, "Branches")

    def _all_pulls_detail(self, context: ActionContext) -> str:
        """Beim Haupt-Branch zählen alle offenen Pull Requests des Repositories, aus dem
        Zwischenspeicher, ohne Netz."""
        if context.project is None or context.project.remote is None:
            return ""
        return _pulls_text(len(self.services.pull_request_cache.open_pulls(
            context.project.remote)))

    # -- Pull Requests (Konzept 10.14, Phase 6) ---------------------------------------------
    def pull_requests_action(self, context: ActionContext) -> None:
        from cockpit.ui.pull_request_flow import PullRequestRunner
        PullRequestRunner(self, context.project).open_list()

    def create_pull_action(self, context: ActionContext) -> None:
        from cockpit.ui.pull_request_flow import PullRequestRunner
        PullRequestRunner(self, context.project).create()

    # -- Terminal (Konzept 9.9, Phase 8a) --------------------------------------------------
    def terminal_action(self, context: ActionContext, folder: Path, where: str) -> None:
        """Terminal im Ordner der Zeile (Wunsch des Nutzers vom 06.10.2026): Projekt im
        Projektordner, Repository im Ordner des Repositorys, Branch im Ordner des Branches."""
        from cockpit.ui.terminal_dialog import open_terminal
        project = context.main_project or context.project
        title = f"{project.name}, {where}" if where else project.name
        open_terminal(self.services, self.window, folder, title, project)
        self.window.refresh_status([project.id])

    # -- Repository (06.10.2026) ---------------------------------------------------------------
    def _branch_show_detail(self, context: ActionContext) -> str:
        from cockpit.ui.project_list import main_name, show_names
        project_list = self.window.project_list
        names = show_names(main_name(context.project, context.status), project_list.platform_name)
        return names[project_list.show_of(context.project.id)]

    def branch_show_action(self, context: ActionContext) -> None:
        """Auswahl, welche Branches unter dem Repository stehen. Pfeil hoch und runter, Enter
        wählt, Escape lässt alles, wie es ist."""
        from cockpit.ui import project_list as listing
        project_list = self.window.project_list
        project = context.project
        names = listing.show_names(listing.main_name(project, context.status),
                                   project_list.platform_name)
        show = listing.pick_show(project_list, names, project_list.show_of(project.id))
        project_list.setFocus()
        if show is None:
            return
        project_list.set_show(project.id, show)
        status = context.status
        shown = 0
        if status is not None:
            if show in ("local", "all"):
                shown += len(status.worktrees)
            if show in ("remote", "all"):
                shown += len(status.remote_branches)
        announce(f"{names[show]}: {count(shown, 'weiterer Branch', 'weitere Branches')}"
                 if show != "main" else names[show])

    def open_repo_remote_action(self, context: ActionContext) -> None:
        """Link zum Repository im Browser öffnen."""
        import webbrowser
        remote = context.project.remote
        webbrowser.open(f"https://{remote.host}/{remote.owner}/{remote.name}")
        announce(f"{remote.name} wird im Browser geöffnet.")

    # -- Features dieses Projekts (Konzept 8.4, Phase 7) ----------------------------------------
    def _features_availability(self, context: ActionContext) -> Availability:
        if not self.services.features.visible_features():
            return Availability.no("Es ist kein Feature eingeschaltet. Das geht im Menü Features.")
        return Availability.yes()

    def project_features_action(self, context: ActionContext) -> None:
        from cockpit.ui.features_dialogs import ProjectFeaturesDialog
        dialog = ProjectFeaturesDialog(self.services, context.project, self.window)
        dialog.exec()
        if dialog.changed:
            self.window.refresh_actions(keep_selection=True)
            self.window.refresh_status([context.project.id])

    def stash_push_action(self, context: ActionContext) -> None:
        from cockpit.core import branches, sync
        project = context.project
        title = "Änderungen beiseitelegen"
        try:
            changes = sync.changes(project.code_dir)
        except CockpitError as exc:
            show_error(self.window, title, exc.message, exc.details)
            return
        if not changes:
            announce("Es gibt keine Änderungen ohne Commit.")
            return
        text = (f"Alle Änderungen ohne Commit werden beiseitegelegt: {changes.summary()}. Die "
                "Dateien kommen danach auf den Stand des letzten Commits. Mit „Beiseitegelegte "
                "Änderungen“ holen Sie sie zurück. Vorher kommen die Dateien auch als "
                "Sicherheitskopie in den Ordner backups. Beiseitelegen?")
        if not confirm(self.window, title, text, yes="Beiseitelegen", no="Abbrechen"):
            return
        try:
            branches.stash_push(project.code_dir, project.name)
        except CockpitError as exc:
            show_error(self.window, title, exc.message, exc.details)
            return
        self.window.refresh_status([project.id])
        announce("Änderungen beiseitegelegt.")

    def stashes_action(self, context: ActionContext) -> None:
        from cockpit.ui.branch_dialogs import StashDialog
        project = context.project
        dialog = StashDialog(project, self.window)
        dialog.exec()
        if dialog.changed:
            self.window.refresh_status([project.id])

    # -- Links, Repository verwalten, Aus der Liste entfernen (Konzept 9.5) --------------------
    def _account_availability(self, context: ActionContext) -> Availability:
        if context.project is None or repo_admin.account_for(self.services,
                                                             context.project) is None:
            return Availability.no(repo_admin.NO_ACCOUNT)
        return Availability.yes()

    def links_action(self, context: ActionContext) -> None:
        from cockpit.ui.repo_dialogs import LinksDialog
        project = context.project
        try:
            links = repo_admin.links(self.services, project)
        except CockpitError as exc:
            show_error(self.window, "Links", exc.message, exc.details)
            return
        if not self.services.vault.is_unlocked():
            LinksDialog(project.name, links, self.window).exec()
            return
        services = self.services

        def work(task: Task):
            """Wunsch des Nutzers (30.09.2026): auch das neueste Release, wenn es eins gibt.
            Klappt die Abfrage nicht, kommen die Links ohne Release."""
            from cockpit.platforms.base import SupportsReleases
            try:
                platform = services.platform_for(project)
                if isinstance(platform, SupportsReleases):
                    releases = platform.releases(repo_admin.repo_ref(project))
                    if releases:
                        return [(f"Neuestes Release {releases[0].tag}", releases[0].url)]
            except CockpitError as exc:
                log.info("Releases von %s nicht abgefragt: %s", project.name, exc.message)
            return []

        self.run_task(f"project:{project.id}", work,
                      lambda extra: LinksDialog(project.name, links + extra, self.window).exec(),
                      "Links")

    def manage_action(self, context: ActionContext) -> None:
        project = context.project
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services, window = self.services, self.window
        platform_name = window.project_list.platform_name
        announce("Repository wird abgefragt.")

        def work(task: Task):
            from cockpit.platforms.base import NotFound
            platform = services.platform_for(project)
            if platform is None:
                raise CockpitError(repo_admin.NO_ACCOUNT)
            try:
                return platform, platform.repo_info(repo_admin.repo_ref(project))
            except NotFound:
                return None                      # das Repository fehlt auf der Plattform

        def done(outcome) -> None:
            from cockpit.ui.repo_dialogs import ManageRepoDialog
            if outcome is None:
                self.missing_repos.add(project.id)
                self.window.refresh_actions(keep_selection=True)
                self.offer_create(project)
                return
            self.missing_repos.discard(project.id)
            platform, info = outcome
            dialog = ManageRepoDialog(services, project, platform, info, platform_name, window)
            dialog.exec()
            if dialog.deleted:
                window.reload_projects(refresh=False)
                if not dialog.removed:
                    window.show_project(project.id)
                    window.refresh_status([project.id])
            elif dialog.changed:
                window.refresh_status([project.id])

        self.run_task(f"project:{project.id}", work, done, "Repository verwalten")

    def remove_action(self, context: ActionContext) -> None:
        project = context.project
        where = f" und das Repository auf {self.window.project_list.platform_name}" if (
            project.remote is not None) else ""
        text = (f"{project.name} wird nur aus der Liste des Cockpits entfernt. Der Ordner "
                f"{project.project_dir}{where} bleiben unverändert. Mit „Projekt vom Rechner "
                "hinzufügen“ kommt es jederzeit zurück. Entfernen?")
        if not confirm(self.window, "Aus der Liste entfernen", text, yes="Entfernen",
                       no="Abbrechen"):
            return
        self.services.projects.remove(project.id)
        if project.remote is not None:
            self.services.remote_repos.hide(project.remote)   # nicht als "nur auf GitHub"
        self.window.reload_projects(refresh=False)
        announce(f"{project.name} aus der Liste entfernt.")

    def _remote_account_availability(self, context: ActionContext) -> Availability:
        repo = context.remote_repo
        if repo is None:
            return Availability.no("Das Repository ist nicht mehr in der Liste.")
        account = self.services.accounts.get(repo.account_id)
        if account is None:
            return Availability.no("Das Konto zu diesem Repository gibt es nicht mehr.")
        return Availability.yes()

    def delete_remote_action(self, context: ActionContext) -> None:
        """Repository löschen, das nur auf der Plattform liegt. Dieselben Rückfragen wie bei
        "Projekt verwalten": Warnung mit "Stattdessen archivieren …", dann den Namen eintippen."""
        from cockpit.platforms.base import RepoRef
        from cockpit.ui.repo_dialogs import RepoDeleter, _Worker
        repo = context.remote_repo
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        platform = self.services.platform(repo.account_id)
        if platform is None:
            show_error(self.window, "Repository löschen", "Das Konto zu diesem Repository gibt "
                       "es nicht mehr.")
            return
        name = self.window.project_list.platform_name
        ref = RepoRef(repo.owner, repo.name)
        worker = _Worker(self.window, "Repository löschen")
        self.remote_worker = worker                 # lebt, solange die Aufgabe läuft

        def deleted() -> None:
            self.services.remote_repos.forget(repo.address)
            cut = repo_admin.forget_address(self.services, repo.address)
            self.window.reload_projects(refresh=False)
            text = f"{repo.name} ist auf {name} gelöscht."
            if cut:
                text += f" Verbindung entfernt bei: {', '.join(cut)}."
            announce(text)

        def archive() -> None:
            text = (f"{repo.name} wird schreibgeschützt. Niemand kann mehr hochladen, auch Sie "
                    f"nicht. Das Repository bleibt auf {name} erhalten, und die Archivierung lässt "
                    "sich jederzeit wieder aufheben. Archivieren?")
            if confirm(self.window, "Archivieren", text, yes="Archivieren", no="Abbrechen"):
                worker.run(lambda: platform.archive(ref),
                           lambda _value: announce(f"{repo.name} ist archiviert."))

        RepoDeleter(self.window, worker, platform, ref, name, False, deleted, archive,
                    local=False).start()

    def hide_remote_action(self, context: ActionContext) -> None:
        repo = context.remote_repo
        name = self.window.project_list.platform_name
        text = (f"{repo.name} erscheint nicht mehr in der Liste. Auf {name} ändert sich nichts. "
                f"Mit „Projekt von {name} herunterladen“ können Sie es jederzeit holen. "
                "Entfernen?")
        if not confirm(self.window, "Aus der Liste entfernen", text, yes="Entfernen",
                       no="Abbrechen"):
            return
        self.services.remote_repos.hide(repo.address)
        self.window.reload_projects(refresh=False)
        announce(f"{repo.name} aus der Liste entfernt.")

    # -- Neuen Ort angeben -----------------------------------------------------------------
    def relocate_action(self, context: ActionContext) -> None:
        project = context.project
        start = str(project.project_dir.parent)
        what = "den Code-Ordner" if project.linked else "den Projektordner"
        folder = pick_folder(self.window, f"Neuer Ort von {project.name}: {what} wählen", start)
        if folder is None:
            return
        try:
            moved = self.services.projects.relocate(project, folder)
        except CockpitError as exc:
            show_error(self.window, "Neuen Ort angeben", exc.message, exc.details)
            return
        self.window.reload_projects(refresh=False)
        self.window.show_project(moved.id)
        self.window.refresh_status([moved.id])
        announce(f"Neuer Ort für {moved.name} gespeichert.")

    # -- Herunterladen -----------------------------------------------------------------------
    def _download_availability(self, context: ActionContext) -> Availability:
        repo = context.remote_repo
        if repo is None:
            return Availability.no("Das Repository ist nicht mehr in der Liste.")
        if git.find_git() is None:
            return Availability.no("Git ist nicht installiert.")
        return Availability.yes()

    def download_action(self, context: ActionContext) -> None:
        self.download(context.remote_repo)

    def download(self, repo: StoredRepo, speak: bool = True) -> None:
        root = Path(self.services.settings.load().projects_root)
        target = project_setup.download_target(root, repo.name) / CODE_DIR
        if target.exists() and any(target.iterdir()):
            show_error(self.window, "Herunterladen", f"Den Ordner {target} gibt es schon, und er "
                       "ist nicht leer. Nichts wurde verändert.")
            return
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services = self.services
        if speak:
            announce(f"{repo.name} wird heruntergeladen.")

        def work(task: Task) -> Project:
            return project_setup.download(services, repo, root, task.cancel_event)

        def done(project: Project) -> None:
            self.ensure_identity(project)
            self.window.reload_projects(refresh=False)
            if speak:
                self.window.show_project(project.id)
            self.window.refresh_status([project.id])
            announce(f"{project.name} heruntergeladen.")

        self.run_task(f"clone:{repo.owner}/{repo.name}".lower(), work, done, "Herunterladen",
                      transfer=True)

    def open_remote_action(self, context: ActionContext) -> None:
        core_actions.open_path(context.remote_repo.web_url)
        announce("Wird im Browser geöffnet.")

    # -- Mit vorhandenem Repository verbinden -------------------------------------------------
    def connect_action(self, context: ActionContext) -> None:
        project = context.project
        repos = self.services.remote_repos.all()
        items = [ENTER_ADDRESS] + [f"{r.name}, {r.owner}" for r in repos]
        current = next((i + 1 for i, r in enumerate(repos) if r.name.lower() ==
                        project.name.lower()), 0)
        index = choose_from_list(self.window, f"{project.name} verbinden", "Repositories",
                                 items, current)
        if index is None:
            return
        if index > 0:
            repo = repos[index - 1]
            url, account_id, label = repo.clone_url, repo.account_id, f"{repo.owner}/{repo.name}"
        else:
            from PySide6.QtWidgets import QInputDialog
            url, ok = QInputDialog.getText(self.window, f"{project.name} verbinden",
                                           "Adresse des Repositories:")
            address = git.parse_remote(url) if ok else None
            if address is None:
                if ok:
                    show_error(self.window, "Verbinden", "Die Adresse wurde nicht erkannt. "
                               "Beispiel: https://github.com/Name/Projekt")
                return
            account = self.services.account_for_host(address.host)
            account_id = account.id if account else None
            label = f"{address.owner}/{address.name}"
        text = (f"{project.name} hat keinen Git-Ordner. Das passiert zum Beispiel, wenn beim "
                "Kopieren oder Verschieben der versteckte Ordner .git fehlte. Ohne ihn weiß das "
                "Projekt nicht, zu welchem Repository es gehört, und hat keinen Verlauf. "
                f"{project.name} wird jetzt mit dem Repository {label} verbunden. Die Dateien im "
                "Ordner bleiben unverändert. Unterschiede zur Plattform erscheinen danach als "
                "Änderungen, die noch nicht hochgeladen sind. Verbinden?")
        if not confirm(self.window, "Verbinden", text, yes="Verbinden", no="Abbrechen"):
            return
        if account_id is not None and not vault_ui.ensure_unlocked(self.services, self.window):
            return
        services = self.services
        announce(f"{project.name} wird verbunden.")

        def work(task: Task) -> str:
            return project_setup.connect(services, project, url, account_id, task.cancel_event)

        def done(branch: str) -> None:
            self.ensure_identity(project)
            self.window.reload_projects(refresh=False)
            self.window.refresh_status([project.id])
            announce(f"{project.name} ist verbunden, Branch {branch}.")

        self.run_task(f"project:{project.id}", work, done, "Verbinden")

    # -- Virtuelle Umgebung -------------------------------------------------------------------
    def repair_venv_action(self, context: ActionContext) -> None:
        project = context.project
        state = venv_repair.check(project.code_dir)
        names = venv_repair.steps(project.code_dir)
        packages = (" Danach installiert es die Pakete aus requirements.txt. Das kann einige "
                    "Minuten dauern." if len(names) == 3 else "")
        text = (f"Die virtuelle Umgebung von {project.name} funktioniert nicht mehr. "
                f"{state.reason} Das Cockpit verschiebt sie als Sicherheitskopie in den Ordner "
                f"backups im Datenordner und legt sie neu an.{packages} Neu anlegen?")
        if not confirm(self.window, "Virtuelle Umgebung", text, yes="Neu anlegen",
                       no="Abbrechen"):
            return
        window = self.window

        def work(task: Task) -> Path:
            def progress(step: int, total: int, name: str) -> None:
                task.status.emit(f"Schritt {step} von {total}: {name} …")
            return venv_repair.repair(project.code_dir, project.name, progress,
                                      task.cancel_event)

        def done(_backup: Path) -> None:
            window.refresh_status([project.id])
            announce(f"Virtuelle Umgebung von {project.name} neu angelegt.")

        self.run_task(f"project:{project.id}", work, done, "Virtuelle Umgebung",
                      on_status=announce)


def _key(repo) -> str:
    from urllib.parse import urlparse
    host = (urlparse(repo.web_url or repo.clone_url).hostname or "").lower()
    return git.RemoteAddress(host, repo.ref.owner, repo.ref.name).key


# -- Stand hinter den Aktionen (Wunsch des Nutzers, 02.10.2026) --------------------------------
def _push_detail(context: ActionContext) -> str:
    status = context.status
    if status is None or status.repo is None or not status.repo.is_repo:
        return ""
    parts = []
    if status.pending:
        parts.append(f"{count(status.pending, 'Datei', 'Dateien')} offen")
    if status.repo.ahead:
        parts.append(f"{count(status.repo.ahead, 'Commit', 'Commits')} nicht hochgeladen")
    return ", ".join(parts) or "nichts offen"


def _pull_detail(context: ActionContext) -> str:
    status = context.status
    if status is None or status.repo is None or not status.repo.is_repo:
        return ""
    behind = status.repo.behind
    return count(behind, "neue Änderung", "neue Änderungen") if behind else "alles aktuell"


def _changed_detail(context: ActionContext) -> str:
    status = context.status
    if status is None or status.repo is None or not status.repo.is_repo:
        return ""
    changed = len(status.repo.changed)
    return f"{count(changed, 'Datei', 'Dateien')} geändert" if changed else "nichts geändert"


def _pulls_text(number: int) -> str:
    return f"{number} offen" if number else "keine offen"


def _branch_pulls_detail(context: ActionContext) -> str:
    return _pulls_text(context.status.open_pulls) if context.status is not None else ""


def _has_commits(context: ActionContext) -> bool:
    """Branches gibt es erst ab dem ersten Commit."""
    status = context.status
    return (status is not None and status.repo is not None and status.repo.is_repo
            and status.repo.has_commits)


def _has_stashes(context: ActionContext) -> bool:
    status = context.status
    return status is not None and status.repo is not None and status.repo.stashes > 0


def _on_other_branch(context: ActionContext) -> bool:
    """Auf einem anderen Branch als main, und das Projekt liegt auf der Plattform."""
    return (_has_remote(context) and context.status is not None
            and bool(context.status.other_branch))


def _has_remote(context: ActionContext) -> bool:
    return context.project is not None and context.project.remote is not None


def _not_on_platform(context: ActionContext) -> bool:
    status = context.status
    return (context.project is not None and context.project.folder_found
            and status is not None and status.repo is not None and not status.on_platform)


def _on_platform(context: ActionContext) -> bool:
    return (context.project is not None and context.project.folder_found
            and context.status is not None and context.status.on_platform)


def _branch_unpublished(context: ActionContext) -> bool:
    """Der Branch hat Commits, liegt aber noch nicht auf der Plattform (Phase 10f)."""
    return (_on_platform(context) and context.status.repo.has_commits
            and bool(context.status.repo.branch) and not context.status.repo.upstream)


def _unfinished_merge(context: ActionContext) -> bool:
    return context.status is not None and bool(context.status.unfinished_merge)


def _git_availability(context: ActionContext) -> Availability:
    if git.find_git() is None:
        return Availability.no("Git ist nicht installiert.")
    return Availability.yes()


def _discard_availability(context: ActionContext) -> Availability:
    status = context.status
    if status is not None and status.unfinished_merge:
        return Availability.no("Bitte lösen Sie zuerst die Konflikte.")
    if status is not None and status.repo is not None and not status.repo.changed:
        return Availability.no("Es gibt keine Änderungen ohne Commit.")
    return _git_availability(context)


def _is_repo(context: ActionContext) -> bool:
    status = context.status
    return status is not None and status.repo is not None and status.repo.is_repo


def _git_missing(context: ActionContext) -> bool:
    status = context.status
    return (context.project is not None and context.project.folder_found
            and status is not None and status.repo is not None and not status.repo.is_repo)


def _venv_broken(context: ActionContext) -> bool:
    return context.status is not None and context.status.venv.broken


def refresh_pulls_for(services, project) -> None:
    """Offene Pull Requests eines Projekts auffrischen, wenn die Plattform das kann. Im
    Hintergrund aufrufen. Klappt es nicht, bleibt der letzte bekannte Stand."""
    from cockpit.platforms.base import SupportsPullRequests
    if project.remote is None:
        return
    try:
        platform = services.platform_for(project)
        if isinstance(platform, SupportsPullRequests):
            services.pull_request_cache.replace(
                project.remote, platform.pull_requests(repo_admin.repo_ref(project), "open"))
    except CockpitError as exc:
        log.warning("Pull Requests von %s: %s", project.name, exc.message)

