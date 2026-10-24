"""Projekt vom Rechner hinzufügen: Aufbau prüfen, Ordner umstellen, danach hochladen anbieten.

Teil von ProjectController (project_actions.py).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from cockpit.core import git
from cockpit.core.errors import CockpitError
from cockpit.core.projects import (
    CODE_DIR, EXE_DIR, FLAT, GIT_OUTSIDE, MAIN_DIR, Project, classify_folder, code_root_in,
    fix_git_outside, layout_problem, nest_code, same_drive)
from cockpit.ui.announcer import announce
from cockpit.ui.common import ask_buttons, confirm, pick_folder, show_info
from cockpit.ui.error_dialog import show_error

log = logging.getLogger(__name__)


class AddProjectActions:
    """Projekte vom Rechner in die Liste bringen."""

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
        self._tidy_release(project, title)
        then(self._exe_dir(project))
        return True

    def _tidy_release(self, project: Project, title: str) -> None:
        """Liegt die Exe direkt im Ordner Release, sie mit allem, was dazugehört, in den Ordner der
        normalen Exe verschieben, also nach Exe-main (Wunsch des Nutzers vom 14.10.2026)."""
        from cockpit.core import exe
        items = exe.loose_items(project)
        if not items:
            return
        home = exe.home_name(project)
        names = ", ".join(p.name for p in items[:6]) + (" und weitere" if len(items) > 6 else "")
        if not confirm(self.window, title, f"Bei {project.name} liegt die Exe direkt im Ordner "
                       f"{project.exe_dir.name}: {names}. Richtig ist ein eigener Ordner, dann "
                       f"steht sie unter Releases als Exe-main. Das Cockpit verschiebt alles nach "
                       f"{project.exe_dir.name}\\{home}. Nur der Ort ändert sich. Verschieben?",
                       yes="Verschieben", no="So lassen"):
            return
        try:
            exe.tidy_release(project)
        except CockpitError as exc:
            show_error(self.window, title, exc.message, exc.details)
            return
        announce(f"Die Exe liegt jetzt in {project.exe_dir.name}\\{home}.")

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
            # Code und Exe gleich in Repository und Release umbenennen, danach den Aufbau prüfen
            # (Wunsch des Nutzers vom 14.10.2026)
            self.folder_renamer.offer_one(self.services.projects.add(project_dir),
                                          lambda project: self.check_layout(project,
                                                                            self._added))
            return
        self._add_other(folder, Path(root))

    def _add_other(self, folder: Path, root: Path) -> None:
        text = (f"Der Ordner {folder.name} hat keinen Unterordner Repository. "
                f"Hier Repository und Release anlegen: {folder.name} wird der Projektordner. "
                f"Das Cockpit legt darin die leeren Ordner {CODE_DIR}\\{MAIN_DIR} und {EXE_DIR} "
                "an. Ihren Code kopieren Sie danach selbst nach "
                f"{CODE_DIR}\\{MAIN_DIR}. "
                f"In den Projekte-Hauptordner verschieben: Das Cockpit legt den Projektordner "
                f"{root / folder.name} an und verschiebt den gewählten Ordner dorthin als Code. "
                f"Am Ort lassen: Der Ordner bleibt, wo er ist. Das Cockpit merkt sich nur, wo er "
                f"liegt. Das passt auch für Repositories, deren Aufbau Sie nicht ändern dürfen.")
        choice = ask_buttons(self.window, "Projekt vom Rechner hinzufügen", text,
                             ["Hier Repository und Release anlegen …",
                              "In den Projekte-Hauptordner verschieben …", "Am Ort lassen …",
                              "Abbrechen"], default=3, escape=3)
        if choice == 0:
            self._create_layout(folder)
        elif choice == 1:
            self._convert(folder, root)
        elif choice == 2:
            self._link(folder)

    def _create_layout(self, folder: Path) -> None:
        """Wunsch des Nutzers (14.10.2026): Unterordner mit anderen Namen als Code und Exe. Das
        Cockpit legt Repository\\main und Release an, den Code kopiert der Nutzer selbst."""
        title = "Repository und Release anlegen"
        others = sorted(p.name for p in folder.iterdir() if not p.name.startswith("."))
        if not confirm(self.window, title, f"Im Ordner {folder} entstehen die leeren Ordner "
                       f"{CODE_DIR}\\{MAIN_DIR} und {EXE_DIR}. Was schon darin liegt, bleibt "
                       "unverändert. Anlegen?", yes="Anlegen", no="Abbrechen"):
            return
        try:
            project = self.services.projects.create_layout(folder)
        except CockpitError as exc:
            show_error(self.window, title, exc.message, exc.details)
            return
        self.window.reload_projects(refresh=False)
        self.window.show_project(project.id)
        self.window.refresh_status([project.id])
        hint = (f"{project.name} ist in der Liste. Kopieren Sie jetzt Ihren Code in den Ordner "
                f"{CODE_DIR}\\{MAIN_DIR}: {project.code_dir}. Danach wählen Sie auf der "
                "Projektzeile „Projekt neu einlesen“.")
        if others:
            hint += f" Im Projektordner liegen schon: {', '.join(others[:8])}."
        announce(f"{project.name} hinzugefügt.")
        show_info(self.window, title, hint)

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
