"""Aktionsliste des Hauptfensters: Kontext, Ausführen, Kontextmenü, Fokus.

Teil von MainWindow (main_window.py).
"""
from __future__ import annotations

import dataclasses
import logging
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from cockpit.core import core_actions, project_status
from cockpit.core.actions import (
    ActionContext, ActionEntry, MORE_TEXT, Target, default_entry, entries_for, find_entry,
    shown_entries)
from cockpit.core.errors import CockpitError
from cockpit.ui.announcer import announce
from cockpit.ui.error_dialog import show_error
from cockpit.ui.menus import AccessibleMenu

log = logging.getLogger(__name__)


SHOW_KEY = "projects.branch_show"          # Auswahl beim Repository je Projekt (06.10.2026)


class ActionsMixin:
    """Aktionen zur markierten Zeile."""

    # -- Aktionen -------------------------------------------------------------------------
    def action_context(self) -> ActionContext:
        target, item_id = self.project_list.current_target()
        key = self.project_list.current_key()
        project = remote = None
        collection = None
        if target is Target.REMOTE_REPO:
            remote = self.services.remote_repos.get(item_id) if item_id is not None else None
        elif target is Target.COLLECTION:
            collection = self.services.collections.get(item_id) if item_id is not None else None
        elif item_id is not None:
            project = self.services.projects.get(item_id)
        status = self.project_list.status_of(project.id) if project is not None else None
        context = ActionContext(self.services, project, target, announce=announce,
                                asker=self.asker, status=status, remote_repo=remote,
                                collection=collection)
        if target is Target.BRANCH and project is not None:
            # Die Aktionen von Code, aber im Branch-Ordner (Phase 10f)
            tree = next((t for t, _s in (status.worktrees if status else []) if t.folder == key),
                        None)
            if tree is not None:
                context.target, context.worktree, context.main_project = \
                    Target.CODE, tree, project
                context.project = dataclasses.replace(project, code_dir=tree.path)
                context.status = project_status.for_folder(status, key)
        elif target is Target.REMOTE_BRANCH and project is not None:
            context.remote_branch = self.project_list.remote_branch(project.id, key)
        elif target in (Target.EXE, Target.RELEASE) and project is not None                 and project.has_exe_dir:
            # Releases (06.10.2026): EXE ist Exe-main, RELEASE das Release eines Branches
            from cockpit.core import local_releases
            folder = key if target is Target.RELEASE else local_releases.MAIN
            context.release = local_releases.find(project, folder or local_releases.MAIN)
            if target is Target.RELEASE:
                context.main_project = project
                context.worktree = next((t for t, _s in (status.worktrees if status else [])
                                         if t.folder == key), None)
        return context

    def _save_show(self, project_id: int, show: str) -> None:
        saved = dict(self.services.database.get_value(SHOW_KEY, {}) or {})
        saved[str(project_id)] = show
        self.services.database.set_value(SHOW_KEY, saved)
        self.refresh_actions(keep_selection=True)

    def current_entries(self) -> list[ActionEntry]:
        context = self.action_context()
        actions = core_actions.all_actions(context) + self.controller.actions()
        return entries_for(actions, context)

    def refresh_actions(self, keep_selection: bool = False) -> None:
        self.actions_list.set_entries(self.current_entries(), keep_selection)

    def run_entry(self, entry: ActionEntry) -> None:
        if entry.children:
            self.show_more(entry)
            return
        if not entry.availability.available:
            announce(f"{entry.text} ist nicht verfügbar. {entry.availability.reason}")
            return
        try:
            entry.action.run(self.action_context())
        except CockpitError as exc:
            announce(exc.message, urgent=True)
            show_error(self, entry.text, exc.message, exc.details)
        except OSError as exc:
            log.warning("Aktion %s fehlgeschlagen: %r", entry.action.id, exc)
            message = f"{entry.text} hat nicht geklappt."
            announce(message, urgent=True)
            show_error(self, entry.text, message, str(exc))
        # Die Markierung bleibt auf der ausgeführten Aktion, statt nach oben zu springen
        self.refresh_actions(keep_selection=True)

    def run_default_action(self) -> None:
        """Enter in der Projektliste: wichtigste Aktion, sonst in die Aktionsliste springen."""
        entries = self.current_entries()
        entry = default_entry(entries)
        if entry is not None:
            self.run_entry(entry)
            return
        blocked = next((e for e in entries if e.action.is_default), None)
        if blocked is not None:
            self.run_entry(blocked)                    # sagt den Grund an
            return
        self.focus_actions()

    def show_context_menu(self, position) -> None:
        entries = self.current_entries()
        if not entries:
            return
        menu = AccessibleMenu("Aktionen", self)
        # Wunsch des Nutzers (07.10.2026): bei einem ausgeklappten Projekt zuerst die
        # Schnellnavigation als Untermenü
        target, item_id = self.project_list.current_target()
        expanded = self.project_list.expanded_project_id
        if expanded is not None and item_id == expanded and target is not Target.COLLECTION:
            from cockpit.ui.quick_nav import quick_menu
            menu.addMenu(quick_menu(self, expanded))
            menu.addSeparator()
        chosen: dict[QAction, ActionEntry] = {}
        for entry in shown_entries(entries):
            if entry.children:
                more = menu.addMenu(entry.label.replace("&", "&&"))
                for child in entry.children:
                    chosen[more.addAction(child.label.replace("&", "&&"))] = child
                continue
            chosen[menu.addAction(entry.label.replace("&", "&&"))] = entry
        picked = menu.exec(position)
        self.project_list.setFocus()
        if picked is not None:
            self.run_entry(chosen[picked])

    def show_more(self, entry: ActionEntry) -> None:
        """Untermenü "Weitere …" unter der markierten Aktion. Escape führt zurück in die
        Aktionsliste (Aufräumrunde vom 20.10.2026)."""
        menu = AccessibleMenu(MORE_TEXT.removesuffix(" …"), self)
        chosen: dict[QAction, ActionEntry] = {}
        for child in entry.children:
            chosen[menu.addAction(child.label.replace("&", "&&"))] = child
        listing = self.actions_list
        item = listing.currentItem()
        rect = listing.visualItemRect(item) if item is not None else listing.rect()
        first = next(iter(chosen), None)
        picked = menu.exec(listing.viewport().mapToGlobal(rect.bottomLeft()), first)
        if picked is None:
            listing.setFocus()
            return
        self.run_entry(chosen[picked])

    def open_terminal_here(self) -> None:
        """Strg+T: das Terminal der markierten Zeile, ohne Menü (20.10.2026)."""
        entry = next((e for e in self.current_entries()
                      if e.action.id.startswith("terminal_")), None)
        if entry is None:
            announce("Hier gibt es kein Terminal.")
            return
        self.run_entry(entry)

    # -- Bereiche -------------------------------------------------------------------------
    def focus_project_list(self) -> None:
        self.project_list.setFocus()

    def focus_actions(self) -> None:
        self.actions_list.setFocus()

    def focus_action(self, project_id: int, action_id: str,
                     target: Target = Target.PROJECT) -> bool:
        """Zeile markieren und in der Aktionsliste auf eine Aktion springen, zum Beispiel
        "Lizenz …" beim Repository (Wunsch des Nutzers vom 03.10.2026: "Jetzt hinzufügen" beim
        Bauen). False, wenn es die Aktion dort nicht gibt."""
        self.project_list.select(target, project_id)
        self.refresh_actions()
        entries = self.actions_list.entries
        row = next((i for i, e in enumerate(entries) if e.action.id == action_id), None)
        if row is None:                            # vielleicht unter "Weitere …"
            row = next((i for i, e in enumerate(entries)
                        if find_entry(list(e.children), action_id) is not None), None)
        if row is None:
            self.project_list.setFocus()
            return False
        self.actions_list.setCurrentRow(row)
        self.actions_list.setFocus()
        return True

    def cycle_area(self, step: int) -> None:
        focused = QApplication.focusWidget()
        index = self.areas.index(focused) if focused in self.areas else -1
        self.areas[(index + step) % len(self.areas)].setFocus()
