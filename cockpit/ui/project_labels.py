"""Texte der Projektliste: Beschriftungen, Filter und Kinder eines Eintrags.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget
from datetime import datetime

from cockpit.core.actions import Target
from cockpit.core.project_collections import Collection
from cockpit.core.project_status import ProjectStatus, code_line, project_line
from cockpit.core.projects import Project
from cockpit.core.remote_repos import StoredRepo
from cockpit.core.text import count
from cockpit.core.worktrees import Worktree
from cockpit.ui.common import name_widget


ROLE_TARGET = Qt.ItemDataRole.UserRole + 1


ROLE_PROJECT = Qt.ItemDataRole.UserRole + 2


ROLE_KEY = Qt.ItemDataRole.UserRole + 3       # Ordner oder Name eines Branches (Phase 10f)


ADD_LOCAL_TEXT = "Projekt vom Rechner hinzufügen"


NEW_COLLECTION_TEXT = "Neue Projektsammlung"


OPENED_SUFFIX = ", geöffnet"


def add_remote_text(platform_name: str) -> str:
    return f"Projekt von {platform_name} herunterladen"


EXPANDED_SUFFIX = ", ausgeklappt"


def project_label(project: Project, status: ProjectStatus | None = None,
                  platform_name: str = "GitHub") -> str:
    return project_line(project, status, platform_name)


def exe_label(project: Project) -> str:
    """Zum Beispiel "Exe, vom Cockpit erstellt am 23.09.2026, aktuell" (Konzept 10.4)."""
    from cockpit.core.exe import status_line
    return status_line(project)


SHOW_MAIN, SHOW_LOCAL, SHOW_REMOTE, SHOW_ALL = "main", "local", "remote", "all"


SHOW_DEFAULT = SHOW_LOCAL                 # Wunsch des Nutzers: nur die eigenen, lokalen Branches


def show_names(main: str = "main", platform_name: str = "GitHub") -> dict[str, str]:
    """Die Auswahl bei der Zeile Repository. Main steht immer da, das zeigt "main &"."""
    return {SHOW_MAIN: f"Nur {main}", SHOW_LOCAL: f"{main} & die Sie lokal haben",
            SHOW_REMOTE: f"{main} & die nur auf {platform_name} sind", SHOW_ALL: f"{main} & alle"}


def pick_filter(listing: QListWidget, names: dict[str, str], current: str) -> str | None:
    """Auswahl für "Anzeigen:" über den Projekten (07.10.2026). None bei Escape."""
    return pick_show(listing, names, current, "Anzeigen")


def pick_show(listing: QListWidget, names: dict[str, str], current: str,
              title: str = "Branches", extra: dict[str, str] | None = None) -> str | None:
    """Menü mit der Auswahl unter der markierten Zeile, wie "Branches anzeigen" in "Branches
    verwalten". extra: weitere Einträge unter einem Trennstrich, ohne Häkchen, zum Beispiel
    "Branches verwalten …" (20.10.2026). None bei Escape."""
    from PySide6.QtGui import QActionGroup
    from PySide6.QtWidgets import QMenu
    menu = QMenu(listing)
    name_widget(menu, title)
    group = QActionGroup(menu)
    chosen = {}
    for key, label in names.items():
        action = menu.addAction(label.replace("&", "&&"))
        action.setCheckable(True)
        action.setChecked(key == current)
        group.addAction(action)
        chosen[action] = key
    if extra:
        menu.addSeparator()
        for key, label in extra.items():
            chosen[menu.addAction(label.replace("&", "&&"))] = key
    active = next((a for a, k in chosen.items() if k == current), None)
    menu.setActiveAction(active)
    item = listing.currentItem()
    rect = listing.visualItemRect(item) if item is not None else listing.rect()
    picked = menu.exec(listing.viewport().mapToGlobal(rect.bottomLeft()), active)
    return chosen.get(picked)


def main_name(project: Project, status: ProjectStatus | None) -> str:
    from cockpit.core.local_releases import main_name as name
    return name(project, status)


def repository_label(project: Project, status: ProjectStatus | None, show: str = SHOW_DEFAULT,
                     platform_name: str = "GitHub") -> str:
    """Zum Beispiel "Repository, Branches: main & die Sie lokal haben"."""
    names = show_names(main_name(project, status), platform_name)
    return f"Repository, Branches: {names.get(show, names[SHOW_DEFAULT])}"


def children_of(project: Project, status: ProjectStatus | None = None,
                platform_name: str = "GitHub", show: str = SHOW_DEFAULT
                ) -> list[tuple[str, Target, str | None]]:
    """Die Zeilen unter dem Projekt (Konzept 8.2: nur vorhandene Ordner). Der dritte Wert
    unterscheidet Zeilen mit gleichem Ziel.
    Wunsch des Nutzers (06.10.2026): Oben steht "Repository". Darunter der Haupt-Branch und je
    nach Auswahl beim Repository die lokalen Branches (Branch-Ordner) und die Branches, die es
    nur auf der Plattform gibt. "Branches verwalten" ist eine Aktion des Repositorys."""
    if not project.folder_found:
        return []
    rows = [(repository_label(project, status, show, platform_name), Target.REPOSITORY, None)]
    if not project.has_branch_folders:
        rows.append((code_line(status, platform_name), Target.CODE, None))
    else:
        rows.append((code_line(status, platform_name, main_head(project)), Target.CODE, None))
        if show in (SHOW_LOCAL, SHOW_ALL):
            for tree, inner in (status.worktrees if status is not None else []):
                rows.append((branch_label(tree, inner, platform_name), Target.BRANCH,
                             tree.folder))
    if show in (SHOW_REMOTE, SHOW_ALL) and status is not None:
        main = main_name(project, status)
        for branch in status.remote_branches:
            rows.append((f"Branch {branch.line(main, platform_name)}", Target.REMOTE_BRANCH,
                         branch.name))
    if project.has_exe_dir:
        rows += release_rows(project, main_name(project, status))
    return rows


def release_rows(project: Project, main: str = "main") -> list[tuple[str, Target, str | None]]:
    """Zeile Releases, darunter Exe-main und je Branch-Release eine Zeile (Wunsch des Nutzers
    vom 06.10.2026)."""
    from cockpit.core import local_releases
    rows = [(local_releases.releases_line(project), Target.RELEASES, None)]
    for release in local_releases.all_releases(project):
        if release.is_main:
            rows.append((local_releases.line(project, release, main), Target.EXE, None))
        else:
            rows.append((local_releases.line(project, release, main), Target.RELEASE,
                         release.folder))
    return rows


def main_head(project: Project) -> str:
    """Anfang der Zeile des Haupt-Branches, zum Beispiel "Main-Branch" oder "Main-Branch master"."""
    name = project.code_dir.name
    return "Main-Branch" if name == "main" else f"Main-Branch {name}"


def has_branches(status: ProjectStatus | None) -> bool:
    """Branches gibt es erst ab dem ersten Commit."""
    return (status is not None and status.repo is not None and status.repo.is_repo
            and status.repo.has_commits)


def branch_label(tree: Worktree, status: ProjectStatus | None,
                 platform_name: str = "GitHub") -> str:
    """Zum Beispiel "Branch neue-funktion, 2 Dateien noch nicht hochgeladen"."""
    head = f"Branch {tree.branch or tree.folder}"
    if tree.gone:
        head += f", auf {platform_name} gelöscht"
    return code_line(status, platform_name, head)


OPEN_CHANGES = "Änderungen offen"


NOTHING_OPEN = "nichts offen"


def collection_label(collection: Collection, size: int, opened: bool = False,
                     state: str = "", shown: int | None = None) -> str:
    """Zum Beispiel "Sammlung Webseiten, 3 Projekte, Änderungen offen". state ist leer, solange
    der Stand der Projekte noch abgefragt wird. shown: mit Filter die passenden, zum Beispiel
    "Sammlung Webseiten, 2 von 5 Projekten"."""
    if shown is not None and shown != size:
        amount = f"{shown} von {size} {'Projekt' if size == 1 else 'Projekten'}"
    else:
        amount = count(size, "Projekt", "Projekte") if size else "leer"
    parts = [collection.title, amount]
    if size and state:
        parts.append(state)
    text = ", ".join(parts)
    return text + OPENED_SUFFIX if opened else text


CHILD_TARGETS = (Target.REPOSITORY, Target.CODE, Target.EXE, Target.BRANCH,
                 Target.REMOTE_BRANCH, Target.RELEASES, Target.RELEASE)


def _sort_key(entry: Project | StoredRepo) -> str:
    """Zuletzt aktualisierte oben. Projekte ohne Datum nach der letzten Änderung im Ordner."""
    if isinstance(entry, StoredRepo):
        return entry.pushed_at[:19]
    if entry.last_updated:
        return entry.last_updated[:19]
    activity = entry.last_activity()
    return datetime.fromtimestamp(activity).isoformat(timespec="seconds") if activity else ""
