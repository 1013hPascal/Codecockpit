"""Aktionen der Zeile Releases und der Release-Zeilen (Wunsch des Nutzers vom 06.10.2026).

Releases: neu einlesen, Terminal, Release für einen lokalen Branch anlegen, veröffentlichen,
entfernen und den Release-Ordner öffnen. Ein Release-Zeile ("Exe-main", "Exe-neue-funktion"):
Terminal, Exe aus dem Branch erstellen, entfernen. Die übrigen Exe-Aktionen von Exe-main stehen
in exe_flow.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import git, local_releases, repo_admin
from cockpit.core.actions import TERMINAL_ORDER, Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.local_releases import LocalRelease
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, ask_buttons, click_focused_button, label_for, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import button_row

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

CREATE_NOTE = ("Releases können nur für Branches erstellt werden, die lokal auf dem Rechner "
               "sind.")
ONLY_LOCAL, ONLY_REMOTE, BOTH, CANCEL = ("Nur lokal auf dem Rechner", "Nur auf {platform}",
                                         "Beides", "Abbrechen")


class ReleaseListDialog(FocusDialog):
    """Hinweis oben, darunter eine Liste, Tab führt zum Knopf. Enter in der Liste drückt den
    Knopf, Escape schließt ohne Änderung."""

    def __init__(self, title: str, note: str, name: str, items: list[str], button: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.note = QLabel(note)
        self.note.setWordWrap(True)
        self.list = QListWidget()
        self.list.addItems(items)
        self.list.setCurrentRow(0)
        list_label = label_for(self.list, name)
        self.list.itemActivated.connect(lambda _item: self.accept())
        self.ok_button = QPushButton(button)
        self.ok_button.clicked.connect(self.accept)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        if note:
            layout.addWidget(self.note)
        layout.addWidget(list_label)
        layout.addWidget(self.list)
        layout.addLayout(button_row(None, self.ok_button, close))
        self.resize(560, 380)
        self.initial_focus_widget = self.list

    @property
    def chosen(self) -> int:
        return self.list.currentRow()

    def keyPressEvent(self, event) -> None:
        if self.focusWidget() is not self.list and click_focused_button(self, event):
            return
        super().keyPressEvent(event)


def pick(parent: QWidget, title: str, note: str, name: str, items: list[str],
         button: str) -> int | None:
    """Index des gewählten Eintrags oder None (in Tests ersetzbar)."""
    dialog = ReleaseListDialog(title, note, name, items, button, parent)
    return dialog.chosen if dialog.exec() else None


class ReleaseRowActions:
    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services

    # -- Hilfen ------------------------------------------------------------------------------
    def _main(self, context: ActionContext) -> str:
        return local_releases.main_name(context.project, context.status)

    def _platform_name(self) -> str:
        return self.window.project_list.platform_name

    def _after(self, project, text: str, target: Target = Target.RELEASES,
               key: str | None = None) -> None:
        self.window.reload_projects(refresh=False)
        self.window.project_list.select(target, project.id, key)
        self.window.refresh_status([project.id])
        announce(text)

    def _terminal(self, context: ActionContext) -> None:
        release = context.release
        if context.target is Target.RELEASES or release is None:
            folder, where = context.project.exe_dir, "Releases"
        else:
            folder = release.path if release.path.is_dir() else context.project.exe_dir
            where = release.title(self._main(context))
        self.controller.terminal_action(context, folder, where)

    # -- Aktionen ----------------------------------------------------------------------------
    def actions(self) -> list[Action]:
        has_exe_dir = lambda c: c.project is not None and c.project.has_exe_dir  # noqa: E731
        return [
            Action("terminal_releases", "Terminal …", Target.RELEASES, self._terminal,
                   visible=has_exe_dir, order=TERMINAL_ORDER),
            Action("terminal_exe", "Terminal …", Target.EXE, self._terminal,
                   visible=has_exe_dir, order=TERMINAL_ORDER),
            Action("terminal_release", "Terminal …", Target.RELEASE, self._terminal,
                   visible=has_exe_dir, order=TERMINAL_ORDER),
            Action("create_release", "Exe für einen Branch erstellen …",
                   Target.RELEASES, self.create_action, visible=has_exe_dir, order=10),
            Action("publish_release", "Release veröffentlichen …", Target.RELEASES,
                   self.publish_action, availability=self.controller._account_availability,
                   visible=lambda c: has_exe_dir(c) and c.project.remote is not None, order=20),
            Action("remove_release", "Release entfernen …", Target.RELEASES,
                   self.remove_action, visible=has_exe_dir, order=30),
            Action("build_release_exe", "Exe aus dem Branch erstellen …", Target.RELEASE,
                   self.controller.exe.build_branch,
                   visible=self.controller.exe._branch_building, order=20,
                   title=lambda c: f"Exe aus {c.worktree.branch or c.release.folder} "
                                   "erstellen …"),
            Action("remove_this_release", "Dieses Release entfernen …", Target.RELEASE,
                   lambda c: self.remove(c, c.release), order=90),
        ]

    # -- Release für Branch erstellen ---------------------------------------------------------
    def create_action(self, context: ActionContext) -> None:
        project, status = context.project, context.status
        taken = {r.folder for r in local_releases.branch_releases(project)}
        trees = [t for t, _s in (status.worktrees if status is not None else [])
                 if t.folder not in taken]
        title = "Release für Branch erstellen"
        if not trees:
            show_info(self.window, title, f"{CREATE_NOTE} Alle lokalen Branches haben schon ein "
                      "Release, oder es gibt außer dem Haupt-Branch noch keinen.")
            return
        chosen = pick(self.window, title, CREATE_NOTE, "Lokale &Branches:",
                      [f"Branch {t.branch or t.folder}" for t in trees],
                      "Release-Ordner &lokal anlegen")
        if chosen is None:
            return
        tree = trees[chosen]
        try:
            local_releases.create_branch_release(project, tree.folder)
        except (CockpitError, OSError) as exc:
            show_error(self.window, title, getattr(exc, "message", str(exc)))
            return
        self._after(project, f"Release Exe-{tree.folder} angelegt.", Target.RELEASE,
                    tree.folder)

    # -- Veröffentlichen -----------------------------------------------------------------------
    def publish_action(self, context: ActionContext) -> None:
        project = context.project
        main = self._main(context)
        releases = local_releases.all_releases(project)
        title = "Release veröffentlichen"
        items = [f"{r.title(main)}, {local_releases.published_line(project, r)}"
                 for r in releases]
        chosen = pick(self.window, title, "", "&Releases:", items, "&Veröffentlichen")
        if chosen is None:
            return
        release = releases[chosen]
        built = local_releases.release_exe(release)
        if built is None:
            show_info(self.window, title, f"In {release.title(main)} liegt noch keine Exe. "
                      "Bitte erstellen Sie sie zuerst.")
            return
        exe_context = ActionContext(self.services, project, Target.EXE, status=context.status)
        if release.is_main:
            self.controller.exe.publish(exe_context, built)
            return
        tree = next((t for t, _s in (context.status.worktrees if context.status else [])
                     if t.folder == release.folder), None)
        branch = tree.branch if tree is not None and tree.branch else release.folder
        remote = git.run(["rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
                         project.code_dir, check=False)
        if remote.returncode != 0:
            show_info(self.window, title, f"Den Branch {branch} gibt es noch nicht auf "
                      f"{self._platform_name()}. Bitte laden Sie ihn zuerst hoch.")
            return
        self.controller.exe.publish(exe_context, built, release.folder, branch)

    # -- Entfernen -------------------------------------------------------------------------------
    def remove_action(self, context: ActionContext) -> None:
        project = context.project
        main = self._main(context)
        releases = local_releases.all_releases(project)
        items = [f"{r.title(main)}, {local_releases.published_line(project, r)}"
                 for r in releases]
        chosen = pick(self.window, "Release entfernen", "", "&Releases:", items,
                      "Release &entfernen")
        if chosen is not None:
            self.remove(context, releases[chosen])

    def remove(self, context: ActionContext, release: LocalRelease | None) -> None:
        """Fragt: nur lokal, nur auf der Plattform oder beides. Vorgabe und Escape: Abbrechen.
        Lokal kommt der Ordner vorher in die Sicherheitskopien. Auf der Plattform wird das
        Release der zuletzt veröffentlichten Version gelöscht, das Tag bleibt."""
        if release is None:
            return
        project = context.project
        name = release.title(self._main(context))
        platform_name = self._platform_name()
        version = local_releases.published_version(project, release)
        local = release.path.exists()
        remote = project.remote is not None and bool(version)
        title = "Release entfernen"
        parts = []
        if local:
            parts.append(f"Lokal kommt der Ordner {release.path.name} in die Sicherheitskopien.")
        if remote:
            parts.append(f"Auf {platform_name} wird das Release der Version {version} gelöscht. "
                         "Das Tag im Repository bleibt.")
        if not parts:
            show_info(self.window, title, f"{name} gibt es weder lokal noch auf "
                      f"{platform_name}.")
            return
        options = ([ONLY_LOCAL] if local else []) \
            + ([ONLY_REMOTE.format(platform=platform_name)] if remote else []) \
            + ([BOTH] if local and remote else []) + [CANCEL]
        choice = options[ask_buttons(self.window, title, f"{name} entfernen? " + " ".join(parts),
                                     options, default=len(options) - 1,
                                     escape=len(options) - 1)]
        if choice == CANCEL:
            return
        removed = []
        if choice in (ONLY_LOCAL, BOTH):
            try:
                backup = local_releases.remove_local(project, release, self._main(context))
            except CockpitError as exc:
                show_error(self.window, title, exc.message, exc.details)
                return
            if backup is not None:
                removed.append("lokal entfernt, die Sicherheitskopie liegt in "
                               f"{Path(backup).name}")
        if choice in (ONLY_LOCAL,):
            self._after(project, f"{name} {removed[0] if removed else 'entfernt'}.")
            return
        self._remove_remote(project, release, name, removed)

    def _remove_remote(self, project, release: LocalRelease, name: str,
                       removed: list[str]) -> None:
        platform = self.controller.exe._platform(project)
        if platform is None:
            return
        ref = repo_admin.repo_ref(project)

        def work(task):
            found = local_releases.remote_release(project, release, platform.releases(ref))
            if found is None:
                return ""
            platform.delete_release(ref, found)
            return found.tag

        def done(tag: str) -> None:
            where = f"auf {self._platform_name()}"
            text = f"Release {tag} {where} gelöscht" if tag else f"{where} nicht gefunden"
            self._after(project, f"{name}: " + ", ".join([*removed, text]) + ".")

        self.controller.run_task(f"exe:{project.id}", work, done, "Release entfernen")
