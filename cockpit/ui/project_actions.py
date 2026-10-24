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
from typing import TYPE_CHECKING, Callable

from cockpit.core import list_filter
from cockpit.core.actions import Action, TERMINAL_ORDER, Target
from cockpit.ui import vault_ui  # noqa: F401  (Tests ersetzen project_actions.vault_ui)
from cockpit.ui.announcer import announce
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

# Aufgeteilt am 21.10.2026: Stand und Bedingungen stehen in action_conditions.py.
from cockpit.ui.action_conditions import (  # noqa: F401
    _branch_pulls_detail, _branch_unpublished, _changed_detail, _discard_availability,
    _git_availability, _git_missing, _has_commits, _has_remote, _has_stashes, _has_upstream,
    _is_repo, _not_on_platform, _on_other_branch, _on_platform, _pull_detail, _pulls_text,
    _push_detail, _unfinished_merge, _venv_broken)
# Aufgeteilt am 22.10.2026: Die Aktionen stehen nach Bereichen in eigenen Dateien. ProjectController
# setzt sie zusammen.
from cockpit.ui.project_add_actions import AddProjectActions
from cockpit.ui.project_remote_actions import RemoteActions
from cockpit.ui.project_git_actions import GitActions, MANAGE_BRANCHES  # noqa: F401
from cockpit.ui.project_manage_actions import ManageActions

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

log = logging.getLogger(__name__)


class ProjectController(AddProjectActions, RemoteActions, GitActions, ManageActions):
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
            Action("branch_show", "Branches …", Target.REPOSITORY,
                   self.branch_show_action, detail=self._branch_show_detail, is_default=True,
                   order=0),
            # Wunsch des Nutzers (07.10.2026): Filter über den Projekten
            Action("list_filter", "Liste filtern …", Target.LIST_FILTER, self.list_filter_action,
                   detail=lambda c: list_filter.names(platform_name)[
                       self.window.project_list.filter_kind],
                   is_default=True, order=0),
            Action("terminal_repository", "Terminal …", Target.REPOSITORY,
                   lambda c: self.terminal_action(c, c.project.code_root, "Repository"),
                   visible=found, order=TERMINAL_ORDER),
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
            # Forks (21.10.2026): Neues aus dem Original holen
            Action("update_from_original", "Vom Original holen …", Target.CODE,
                   self.update_from_original_action, availability=_git_availability,
                   visible=lambda c: on_main(c) and _has_upstream(c), order=21),
            # "Branches verwalten …" steht seit der Aufräumrunde vom 20.10.2026 in "Branches …"
            Action("create_pull", "Pull Request erstellen …", Target.CODE,
                   self.create_pull_action, availability=self._account_availability,
                   visible=_on_other_branch, order=26),
            Action("pull_requests", "Pull Requests …", Target.CODE, self.pull_requests_action,
                   availability=self._account_availability, detail=self._all_pulls_detail,
                   visible=lambda c: _has_remote(c) and on_main(c), order=27),
            # Wunsch des Nutzers (21.10.2026): Issues, mit und ohne KI
            Action("issues", "Issues …", Target.CODE, self.issues_action,
                   availability=self._account_availability,
                   visible=lambda c: _has_remote(c) and on_main(c), order=28),
            Action("pull_requests_branch", "Pull Requests …", Target.CODE,
                   self.pull_requests_action, availability=self._account_availability,
                   detail=_branch_pulls_detail,
                   visible=lambda c: _has_remote(c) and not on_main(c), order=27),
            Action("stash_push", "Änderungen beiseitelegen …", Target.CODE, self.stash_push_action,
                   availability=_discard_availability, visible=_has_commits, order=36,
                   detail=_changed_detail, more=True),
            Action("stashes", "Beiseitegelegte Änderungen …", Target.CODE, self.stashes_action,
                   visible=_has_stashes, order=37, more=True),
            Action("history", "Verlauf …", Target.CODE, self.history_action,
                   availability=_git_availability, visible=_is_repo, order=30),
            # Wunsch des Nutzers (07.10.2026): wer wann in diesen Branch hochgeladen hat
            Action("upload_history", "Hochladeverlauf …", Target.CODE,
                   self.upload_history_action, availability=_git_availability,
                   visible=_on_platform, order=31, more=True),
            Action("discard", "Änderungen verwerfen …", Target.CODE, self.discard_action,
                   availability=_discard_availability, visible=_is_repo, order=35,
                   detail=_changed_detail),
            Action("project_features", "Features dieses Projekts …", Target.PROJECT,
                   self.project_features_action, availability=self._features_availability,
                   visible=found, order=30, more=True),
            Action("terminal_project", "Terminal …", Target.PROJECT,
                   lambda c: self.terminal_action(c, c.project.project_dir, ""),
                   visible=found, order=TERMINAL_ORDER),
            Action("terminal_code", "Terminal …", Target.CODE,
                   lambda c: self.terminal_action(c, c.project.code_dir,
                                                  c.worktree.branch if c.worktree else "Code"),
                   visible=found, order=TERMINAL_ORDER),
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
                   self.connect_action, visible=_git_missing, order=40, more=True),
            Action("git_identity", "Git-Name und E-Mail …", Target.REPOSITORY,
                   self.identity_action, visible=_is_repo, order=85, more=True),
            Action("repair_venv", "Virtuelle Umgebung neu anlegen …", Target.CODE,
                   self.repair_venv_action, visible=_venv_broken, order=45, more=True),
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


