"""Die Exe in der Oberfläche (Konzept 10.4, Phase 10).

Aktionen: "Exe hinzufügen …" auf der Projektzeile. Bei "Exe" (zusammengefasst nach dem Wunsch des
Nutzers, 30.09.2026): Exe aus dem Code erstellen, Exe-Bau abschließen, Exe veröffentlichen, Exe
einlesen, Exe-Einstellungen, Links der Exe, Wie funktioniert die Exe?. Exe starten und
Exe-Ordner öffnen stehen im Kern.

"Exe aus dem Code erstellen …" führt seit dem 03.10.2026 Schritt für Schritt durch den Bau, immer
im Branch Cockpit-exe-bauen (exe_wizard.py). "Exe-Bau abschließen …" steht da, solange es diesen
Branch gibt: in main überführen, mit oder ohne Release, oder verwerfen.
"Exe einlesen …" fragt: Exe-Datei wählen oder Exe aus einem Release wählen.

BuildDialog: Ausgabe von PyInstaller als Liste, eine Zeile pro Zeile. Die Schritte sagt NVDA an
("Schritt 2 von 4: Exe wird gebaut"). Escape bricht einen laufenden Bau ab, danach schließt es.
Alles, was Dateien verändert, beschreibt vorher, was passiert, und braucht eine Bestätigung.
"""
from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFileDialog

from cockpit.core import exe, local_releases, paths, repo_admin
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import ask_buttons, choose_from_list, confirm, pick_folder, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

# Aufgeteilt am 21.10.2026: Die Fenster stehen in exe_dialogs.py. Die Namen bleiben hier
# erreichbar, für den Code im Cockpit und für die Tests.
from cockpit.ui.exe_dialogs import (  # noqa: F401
    ALWAYS, AUTO_PYTHON, BESIDE_ROLE, FOLDER, NOT_BESIDE, ONE_FILE, BuildDialog,
    BuildSettingsDialog, PublishDialog, beside_candidates, offer_long_paths)

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

log = logging.getLogger(__name__)

FEATURE_ID = "exe_build"


def _size(path: Path) -> str:
    size = path.stat().st_size if path.is_file() else sum(
        p.stat().st_size for p in path.rglob("*") if p.is_file())
    return f"{max(1, round(size / (1024 * 1024)))} MB"


FROM_FILE = "Exe-Datei wählen …"
FROM_RELEASE = "Exe aus einem Release wählen …"
ADD_NOW, IGNORE = "Jetzt hinzufügen", "Ignorieren und weiter"
MERGE_PUBLISH = "Jetzt in main überführen und Release veröffentlichen"
MERGE_ONLY = "Jetzt in main überführen, später veröffentlichen"
OPEN_TEST = "Ordner der neuen Exe im Explorer öffnen"
DISCARD = "Exe-Bau verwerfen …"
# Der Branch ist schon in main und gelöscht, die Exe aus ihm liegt noch da (04.10.2026)
ADOPT_PUBLISH = "Exe als normale Exe übernehmen und Release veröffentlichen"
ADOPT_ONLY = "Exe als normale Exe übernehmen, später veröffentlichen"
DISCARD_EXE = "Exe aus dem Branch verwerfen …"
PICK_BRANCH = "Exe aus dem Branch Cockpit-exe-bauen, die neuere"
PICK_NORMAL = "Normale Exe"
FINISH_HERE = "In main überführen oder verwerfen, Exe-Bau abschließen …"


def download_links(release, asset) -> list[tuple[str, str]]:
    """Links zum Release und zum Herunterladen der Exe. Bei GitHub folgt der Download-Link aus
    der Adresse des Releases: .../releases/tag/v1.2.0 wird .../releases/download/v1.2.0/Name."""
    links = [(f"Release {release.tag}", release.url)]
    marker = "/releases/tag/"
    if marker in release.url:
        base = release.url.split(marker, 1)[0]
        links.append((f"Download der Exe {release.tag}",
                       f"{base}/releases/download/{release.tag}/{asset.name}"))
        links.append(("Download der neuesten Exe",
                      f"{base}/releases/latest/download/{asset.name}"))
    return links


def beside_line(project: Project, code_dir: Path | None = None) -> str:
    """Was neben die Exe kommt (Rückmeldung des Nutzers vom 02.10.2026)."""
    names = exe.beside_names(project, code_dir) if code_dir is not None else \
        exe.beside_names(project)
    if names:
        return f"Neben die Exe kommen: {', '.join(names)}."
    return "Neben die Exe kommt nichts. Das ändern Sie im ersten Schritt."


# -- Aktionen ---------------------------------------------------------------------------------------
class ExeActions:
    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services
        self.uploading: set[int] = set()          # Projekte, deren Release gerade hochlädt

    def _publish_detail(self, context: ActionContext) -> str:
        """Wunsch des Nutzers (04.10.2026): Während des Hochladens nicht "noch nicht
        veröffentlicht", sondern "wird gerade hochgeladen"."""
        if context.project.id in self.uploading:
            return "wird gerade hochgeladen"
        return exe.publish_state(context.project)

    # -- Sichtbarkeit ------------------------------------------------------------------------
    def _building(self, context: ActionContext) -> bool:
        project = context.project
        if project is None or not project.has_exe_dir or FEATURE_ID not in self.services.registry:
            return False
        try:
            return self.services.features.active(FEATURE_ID, project)
        except CockpitError:
            return False

    def _branch_open(self, context: ActionContext) -> bool:
        """Es gibt den Branch Cockpit-exe-bauen oder noch seine Exe: "Exe-Bau abschließen …"
        anbieten (Rückmeldung des Nutzers vom 04.10.2026: der Branch war schon in main und
        gelöscht, die Exe lag noch da, und der Eintrag fehlte)."""
        from cockpit.features.exe_build import exe_branch
        try:
            return self._building(context) and (
                exe_branch.exists(context.project)
                or exe.branch_home(context.project, exe_branch.BRANCH) is not None)
        except CockpitError:
            return False

    @staticmethod
    def _publishable(project: Project) -> list[Path]:
        """Exen, die sich veröffentlichen lassen: die normale und die aus dem Branch
        Cockpit-exe-bauen. Release und Repository sind getrennt, die Exe muss dafür nicht in
        main sein (Wunsch des Nutzers vom 04.10.2026)."""
        from cockpit.features.exe_build import exe_branch
        found = [p for p in (exe.current_exe(project),) if p is not None]
        home = exe.branch_home(project, exe_branch.BRANCH) if project.has_exe_dir else None
        if home is not None:
            found.append(exe.exe_in(home))
        return found

    def actions(self) -> list[Action]:
        has_exe = lambda c: bool(self._publishable(c.project))         # noqa: E731
        return [
            Action("add_exe", "Exe hinzufügen …", Target.PROJECT, self.add_exe,
                   visible=lambda c: c.project is not None and c.project.folder_found
                   and not c.project.has_exe_dir, order=72),
            # Wunsch des Nutzers (06.10.2026): "Exe aus main erstellen …"
            Action("build_exe", "Exe aus dem Code erstellen …", Target.EXE, self.build_menu,
                   visible=self._building, order=20,
                   detail=lambda c: exe.build_state(c.project),
                   title=lambda c: f"Exe aus {local_releases.main_name(c.project, c.status)} "
                                   "erstellen …"),
            Action("finish_exe", "Exe-Bau abschließen …", Target.EXE, self.finish_menu,
                   visible=self._branch_open, order=30),
            Action("publish_exe", "Exe veröffentlichen …", Target.EXE, self.publish,
                   availability=self.controller._account_availability,
                   detail=self._publish_detail,
                   visible=lambda c: self._building(c) and has_exe(c)
                   and c.project.remote is not None, order=40),
            Action("import_exe", "Exe aus einem Release holen …", Target.EXE, self.import_exe,
                   visible=lambda c: c.project is not None and c.project.has_exe_dir, order=45),
            Action("exe_settings", "Exe-Einstellungen …", Target.EXE, self.edit_settings,
                   visible=lambda c: self._building(c)
                   and exe.read_settings(c.project.code_dir) is not None, order=50),
            Action("exe_links", "Links der Exe …", Target.EXE, self.links,
                   availability=self.controller._account_availability,
                   visible=lambda c: c.project is not None and c.project.has_exe_dir
                   and c.project.remote is not None, order=55),
            Action("exe_guide", "Wie funktioniert die Exe? …", Target.EXE,
                   lambda c: self.window.show_guide(exe.EXE_GUIDE, "Wie funktioniert die Exe?"),
                   visible=lambda c: c.project is not None, order=95, more=True),
            Action("build_branch_exe", "Exe aus dem Branch erstellen …", Target.CODE,
                   self.build_branch, visible=self._branch_building, order=92,
                   title=lambda c: f"Exe aus {c.worktree.branch} erstellen …"),
            # Wunsch des Nutzers (11.10.2026): auch dort, wo der Branch Cockpit-exe-bauen und
            # seine Exe stehen, nicht nur bei Exe-main
            Action("finish_exe_branch", FINISH_HERE, Target.CODE, self.finish_here,
                   visible=self._exe_branch_row, order=1),
            Action("finish_exe_release", FINISH_HERE, Target.RELEASE, self.finish_here,
                   visible=self._exe_branch_row, order=1),
        ]

    def _exe_branch_row(self, context: ActionContext) -> bool:
        """Zeile des Branches Cockpit-exe-bauen unter Repository oder sein Release."""
        from cockpit.features.exe_build import exe_branch
        main = context.main_project
        if main is None:
            return False
        here = (context.worktree is not None and context.worktree.branch == exe_branch.BRANCH) \
            or (context.release is not None and context.release.folder == exe_branch.BRANCH)
        return here and self._branch_open(ActionContext(self.services, main, Target.EXE))

    def finish_here(self, context: ActionContext) -> None:
        self.finish_menu(ActionContext(self.services, context.main_project, Target.EXE))

    def _branch_building(self, context: ActionContext) -> bool:
        """Nur in einem Branch-Ordner, wenn der Haupt-Branch eine Exe baut (Phase 10f)."""
        if context.worktree is None or context.main_project is None:
            return False
        main = ActionContext(context.services, context.main_project, Target.EXE)
        return self._building(main) and exe.read_settings(context.main_project.code_dir) \
            is not None

    def build_branch(self, context: ActionContext) -> None:
        project, tree = context.main_project, context.worktree
        settings = exe.read_settings(project.code_dir)
        name = exe.branch_exe_name(settings.name, tree.folder)
        text = (f"Das Cockpit baut die Exe aus dem Ordner "
                f"{project.code_root.name}\\{tree.folder} und testet sie. "
                f"Sie kommt in den Ordner {project.exe_dir.name}\\{name}. Die normale Exe aus "
                f"{project.code_dir.name} bleibt unverändert. Starten?")
        if not confirm(self.window, "Exe aus dem Branch erstellen", text, yes="Starten",
                       no="Abbrechen"):
            return
        BuildDialog(self.services, project, settings, self.window, branch_dir=tree.path).exec()
        self.window.refresh_status([project.id])

    def _after(self, project: Project, text: str) -> None:
        self.window.reload_projects(refresh=False)
        self.window.project_list.select(Target.EXE, project.id)
        self.window.refresh_status([project.id])
        announce(text)

    # -- README und Lizenz (Wunsch des Nutzers vom 03.10.2026) --------------------------------
    def docs_ok(self, project: Project, title: str) -> bool:
        """Vor dem Bauen und Veröffentlichen: Fehlen README oder Lizenz, warnen. "Jetzt
        hinzufügen" schließt alles und springt beim Projekt zur passenden Aktion."""
        missing = exe.missing_docs(project.code_dir)
        if not missing:
            return True
        names = " und ".join(missing)
        verb = "fehlen" if len(missing) > 1 else "fehlt"
        choice = ask_buttons(self.window, title, f"Bei {project.name} {verb} {names}. README und "
                             "Lizenz gehören neben die Exe und ins Repository.",
                             [ADD_NOW, IGNORE, "Abbrechen"], default=0, escape=2)
        if choice == 1:
            return True
        if choice == 0:
            wanted = ["readme", "license"] if "README" in missing else ["license"]
            if not any(self.window.focus_action(project.id, w, Target.REPOSITORY)
                       for w in wanted):
                announce("Die Aktion gibt es hier nicht. Schalten Sie bei Features die "
                         "README-Pflege ein.")
        return False

    # -- Exe hinzufügen ---------------------------------------------------------------------
    def add_exe(self, context: ActionContext) -> None:
        project = context.project
        if project.exe_dir is None:                      # verknüpftes Projekt
            folder = pick_folder(self.window, "Ordner für die Exe wählen", str(project.code_dir))
            if folder is None:
                return
            project = self.services.projects.set_exe_dir(project, folder)
        elif not confirm(self.window, "Exe hinzufügen",
                         f"Im Projektordner wird der Ordner Release angelegt: {project.exe_dir}. "
                         "Danach steht Exe unter Code. Anlegen?", yes="Anlegen", no="Abbrechen"):
            return
        try:
            exe.add_exe_dir(project)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "Exe hinzufügen", getattr(exc, "message", str(exc)))
            return
        self._after(project, "Ordner Release angelegt.")

    # -- Exe-Datei wählen -------------------------------------------------------------------
    def choose(self, context: ActionContext) -> None:
        project = context.project
        kind = choose_from_list(self.window, "Exe-Datei wählen", "Was übernehmen?",
                                ["Eine Exe-Datei …", "Einen Programmordner …"])
        if kind is None:
            return
        if kind == 0:
            chosen, _ = QFileDialog.getOpenFileName(self.window, "Exe-Datei wählen",
                                                    str(project.project_dir),
                                                    "Programme (*.exe)")
            source = Path(chosen) if chosen else None
        else:
            source = pick_folder(self.window, "Programmordner wählen", str(project.project_dir))
        if source is None:
            return
        text = f"{source.name} wird in einen eigenen Ordner im Ordner Release kopiert."
        if exe.current_exe(project) is not None:
            text += " Die bisherige Exe kommt vorher in die Sicherheitskopien."
        if not confirm(self.window, "Exe-Datei wählen", text + " Übernehmen?", yes="Übernehmen",
                       no="Abbrechen"):
            return
        self.controller.run_task(f"exe:{project.id}", lambda task: exe.adopt(project, source),
                                 lambda target: self._after(project,
                                                            f"Exe übernommen: {target.name}."),
                                 "Exe-Datei wählen")

    # -- Bauen ------------------------------------------------------------------------------
    def build_menu(self, context: ActionContext) -> None:
        """Schritt für Schritt (Wunsch des Nutzers vom 03.10.2026), siehe exe_wizard.py."""
        project = context.project
        if exe.find_python() is None and not exe.python_in(exe.build_venv(project)).is_file():
            if confirm(self.window, "Exe erstellen", "Python wurde nicht gefunden. Zum Erstellen "
                       "einer Exe braucht das Cockpit Python. Anleitung anzeigen?",
                       yes="Anleitung", no="Schließen", default_yes=True):
                self.window.show_guide(exe.PYTHON_GUIDE, "Python installieren")
            return
        if not self.docs_ok(project, "Exe aus dem Code erstellen"):
            return
        from cockpit.ui.exe_wizard import ExeWizard
        ExeWizard(self, project).run()

    def offer_restart(self, project: Project) -> None:
        if not confirm(self.window, "Neue Version", "Die neue Version wird beim nächsten Start "
                       "übernommen. Jetzt neu starten?", yes="Neu starten", no="Später"):
            return
        try:
            script = exe.restart_script(project)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "Neu starten", getattr(exc, "message", str(exc)))
            return
        exe.launch_restart(script)
        self.window.close()

    # -- Exe-Bau abschließen ------------------------------------------------------------------
    def finish_menu(self, context: ActionContext) -> None:
        """Für später, nach "Erst testen": überführen, mit oder ohne Release, oder verwerfen."""
        from cockpit.features.exe_build import exe_branch
        project = context.project
        merged = not exe_branch.exists(project)        # Branch schon in main und gelöscht
        options = [ADOPT_PUBLISH, ADOPT_ONLY] if merged else [MERGE_PUBLISH, MERGE_ONLY]
        if exe.branch_home(project, exe_branch.BRANCH) is not None:
            options.append(OPEN_TEST)
        options.append(DISCARD_EXE if merged else DISCARD)
        chosen = choose_from_list(self.window, "Exe-Bau abschließen", "Wie geht es weiter?",
                                  options)
        if chosen is None:
            return
        if options[chosen] == OPEN_TEST:
            self.open_branch_exe(project)
        elif options[chosen] == DISCARD:
            if confirm(self.window, "Exe-Bau verwerfen", f"Der Branch {exe_branch.BRANCH} wird "
                       "gelöscht, seine Exe kommt in die Sicherheitskopien. Main bleibt, wie es "
                       "ist. Verwerfen?", yes="Verwerfen", no="Abbrechen"):
                self.discard_branch(project)
        elif options[chosen] == DISCARD_EXE:
            if confirm(self.window, "Exe aus dem Branch verwerfen", "Die Exe aus dem Branch "
                       f"{exe_branch.BRANCH} kommt in die Sicherheitskopien. Verwerfen?",
                       yes="Verwerfen", no="Abbrechen"):
                self.discard_branch(project)
        else:
            self.merge_branch(project, publish=options[chosen] in (MERGE_PUBLISH,
                                                                   ADOPT_PUBLISH))

    def open_branch_exe(self, project: Project) -> None:
        from cockpit.core import core_actions
        from cockpit.features.exe_build import exe_branch
        home = exe.branch_home(project, exe_branch.BRANCH)
        if home is None:
            announce("Die Exe aus dem Branch gibt es nicht mehr.")
            return
        try:
            core_actions.open_path(home)
        except OSError as exc:
            show_error(self.window, "Explorer", "Der Ordner ließ sich nicht öffnen.", str(exc))

    def merge_branch(self, project: Project, publish: bool) -> None:
        """Den Branch in main überführen. Die getestete Exe aus dem Branch wird die normale Exe,
        der Branch wird danach gelöscht. publish: danach gleich "Exe veröffentlichen"."""
        from cockpit.core.sync import ConflictKind
        from cockpit.features.exe_build import exe_branch
        branch = exe_branch.BRANCH
        if exe_branch.exists(project):
            try:
                outcome = exe_branch.merge_into_main(project)
            except CockpitError as exc:
                show_error(self.window, "In main überführen", exc.message, exc.details)
                return
            if outcome.kind is not ConflictKind.NONE and \
                    not self._resolve(project, outcome.kind):
                self.window.refresh_status([project.id])
                return
            text = f"{branch} ist in main überführt. Main ist noch nicht hochgeladen."
        else:
            text = f"{branch} ist schon in main."          # nur noch die Exe übernehmen
        result = None
        if exe.branch_home(project, branch) is not None:
            try:
                result = exe.promote_branch(project, branch, exe.head_commit(project.code_dir))
            except CockpitError as exc:
                show_error(self.window, "In main überführen", "Die Änderungen sind in main. Die "
                           f"Exe aus dem Branch ließ sich nicht übernehmen. {exc.message}",
                           exc.details)
        if result is not None:
            text += (" Die neue Exe wird beim nächsten Start übernommen." if result.pending
                     else " Die Exe aus dem Branch ist jetzt die normale Exe.")
            if exe_branch.exists(project):
                try:
                    exe_branch.delete(project)
                    text += f" Der Branch {branch} ist gelöscht."
                except CockpitError as exc:
                    log.warning("Branch %s nicht gelöscht: %s", branch, exc.message)
        self._after(project, text)
        if result is not None and result.pending:
            self.offer_restart(project)
            return
        if publish and exe.current_exe(project) is not None:
            self.publish(ActionContext(self.services, project, Target.EXE))

    def discard_branch(self, project: Project) -> None:
        """Exe-Bau abbrechen: Branch löschen, seine Exe in die Sicherheitskopien. Main bleibt."""
        from cockpit.core import backups
        from cockpit.features.exe_build import exe_branch
        try:
            home = exe.branch_home(project, exe_branch.BRANCH)
            if home is not None:
                backups.move_into_backup(home, project.name, "Exe-Bau verworfen")
            if exe_branch.exists(project):
                exe_branch.abandon(project)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "Exe-Bau verwerfen", getattr(exc, "message", str(exc)),
                       getattr(exc, "details", ""))
            return
        self._after(project, f"Exe-Bau verworfen. Main ist, wie es war.")

    def _resolve(self, project: Project, kind) -> bool:
        from cockpit.core import sync
        from cockpit.features.exe_build import exe_branch
        from cockpit.ui import sync_dialogs
        announce(f"Konflikte beim Überführen von {exe_branch.BRANCH}.")
        dialog = sync_dialogs.ConflictDialog(project.code_dir, kind,
                                             f"Branch {exe_branch.BRANCH}", self.window)
        try:
            if dialog.exec():
                sync.finish(project.code_dir, kind)
                return True
            sync.abort(project.code_dir, kind)
            announce("Überführen abgebrochen. Main ist wie vorher.")
        except CockpitError as exc:
            show_error(self.window, "Überführen", exc.message, exc.details)
        return False

    # -- Exe einlesen (30.09.2026) --------------------------------------------------------------
    def import_exe(self, context: ActionContext) -> None:
        options = [FROM_FILE] + ([FROM_RELEASE] if context.project.remote is not None else [])
        chosen = choose_from_list(self.window, "Exe einlesen", "Woher kommt die Exe?", options)
        if chosen is None:
            return
        if options[chosen] == FROM_FILE:
            self.choose(context)
        else:
            self.fetch(context)

    # -- Links der Exe (30.09.2026) -------------------------------------------------------------
    def links(self, context: ActionContext) -> None:
        from cockpit.ui.repo_dialogs import LinksDialog
        project = context.project
        platform = self._platform(project)
        if platform is None:
            return
        ref = repo_admin.repo_ref(project)

        def work(task: Task):
            for release in platform.releases(ref):
                asset = exe.pick_asset(release.assets)
                if asset is not None:
                    return download_links(release, asset)
            return []

        def done(found: list[tuple[str, str]]) -> None:
            if not found:
                show_info(self.window, "Links der Exe", "Die Exe ist noch nicht veröffentlicht. "
                          "Mit „Exe veröffentlichen …“ kommt sie in ein Release.")
                return
            LinksDialog(f"{project.name}, Exe", found, self.window).exec()

        self.controller.run_task(f"exe:{project.id}", work, done, "Links der Exe")

    # -- Einstellungen ändern (Phase 10g) ---------------------------------------------------
    def edit_settings(self, context: ActionContext) -> None:
        project = context.project
        dialog = BuildSettingsDialog(project, self.window, exe.read_settings(project.code_dir))
        if not dialog.exec() or dialog.settings is None:
            return
        settings = dialog.settings
        spec = (f"Die von Hand geschriebene Datei {settings.spec_name} bleibt unverändert."
                if dialog.handmade else
                f"Die Datei {settings.spec_name} wird neu geschrieben, die bisherige kommt in die "
                "Sicherheitskopien.")
        if not confirm(self.window, "Exe-Einstellungen",
                       f"Die Einstellungen kommen in cockpit.toml. {spec} Die Exe ändert sich "
                       "erst beim nächsten Bau. Speichern?", yes="Speichern", no="Abbrechen"):
            return
        try:
            exe.change_settings(project.code_dir, project.name, settings)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "Exe-Einstellungen", getattr(exc, "message", str(exc)))
            return
        announce("Exe-Einstellungen gespeichert.")

    # -- Einrichtung prüfen -----------------------------------------------------------------
    def check_setup(self, context: ActionContext) -> None:
        from cockpit.features.exe_build.setup_check import check
        from cockpit.ui.text_dialog import TextDialog
        project = context.project

        def done(lines: list[str]) -> None:
            announce(lines[0])
            TextDialog(f"Exe-Einrichtung: {project.name}", lines, "Ergebnis",
                       self.window).exec()

        self.controller.run_task(f"exe:{project.id}", lambda task: check(project), done,
                                 "Exe-Einrichtung prüfen")

    # -- Releases ---------------------------------------------------------------------------
    def _platform(self, project: Project):
        from cockpit.platforms.base import SupportsReleases
        if not vault_ui.ensure_unlocked(self.services, self.window):
            return None
        platform = self.services.platform_for(project)
        if platform is None:
            show_error(self.window, "Releases", "Für dieses Projekt ist kein Konto eingerichtet.")
            return None
        if not isinstance(platform, SupportsReleases):
            show_error(self.window, "Releases", "Diese Plattform unterstützt keine Releases.")
            return None
        return platform

    def publish(self, context: ActionContext, chosen: Path | None = None,
                branch: str = "", branch_ref: str = "") -> None:
        """chosen: diese Exe ohne Rückfrage (aus "Release veröffentlichen …"). branch und
        branch_ref beim Release eines anderen Branches: Tag v1.0.0-<branch>, auf dem Stand des
        Branches (Wunsch des Nutzers vom 06.10.2026)."""
        project = context.project
        if not self.docs_ok(project, "Exe veröffentlichen"):
            return
        platform = self._platform(project)
        if platform is None:
            return
        ref = repo_admin.repo_ref(project)
        found = [chosen] if chosen is not None else self._publishable(project)
        if not found:
            show_info(self.window, "Exe veröffentlichen", "Es gibt noch keine Exe.")
            return
        current = found[0]
        if len(found) > 1:
            # Ist die Exe aus dem Branch neuer, steht sie oben (Vorgabe)
            newer = found[1].stat().st_mtime > found[0].stat().st_mtime
            options = [(PICK_BRANCH, found[1]), (PICK_NORMAL, found[0])] if newer \
                else [(PICK_NORMAL, found[0]), (PICK_BRANCH.replace(", die neuere", ""),
                                                found[1])]
            chosen = choose_from_list(self.window, "Exe veröffentlichen", "Welche Exe?",
                                      [o[0] for o in options])
            if chosen is None:
                return
            current = options[chosen][1]

        def work(task: Task):
            return [r.tag for r in platform.releases(ref)]

        self.controller.run_task(f"exe:{project.id}", work,
                                 lambda tags: self._ask_publish(project, platform, ref, current,
                                                                tags, branch, branch_ref),
                                 "Exe veröffentlichen")

    def _ask_publish(self, project, platform, ref, current: Path, tags: list[str],
                     branch: str = "", branch_ref: str = "") -> None:
        """Wunsch des Nutzers (03.10.2026): Hochgeladen wird der ganze Ordner der Exe als
        Name.zip, darin der Ordner Name-Version. README und Lizenz hängen zusätzlich einzeln am
        Release."""
        from cockpit.ui import ai_suggest
        name = exe.asset_name(project, current)
        source = ai_suggest.for_release_notes(self.services, project, tags)
        if branch:
            suffix = f"-{branch}"
            tags = [t.removesuffix(suffix) for t in tags if t.endswith(suffix)]
            suggestion = exe.next_version(tags)
        else:
            suffix, suggestion = "", self._suggested_version(project, tags)
        dialog = PublishDialog(project, suggestion, tags, name, self.window, source=source)
        if not dialog.exec():
            return
        version, notes = dialog.version, dialog.notes
        work_dir = Path(tempfile.mkdtemp(prefix="codecockpit-release-", dir=paths.cache_dir()))
        try:
            asset = exe.asset_for_upload(project, current, work_dir, version)
        except (CockpitError, OSError) as exc:
            shutil.rmtree(work_dir, ignore_errors=True)
            show_error(self.window, "Exe veröffentlichen", "Die ZIP-Datei ließ sich nicht "
                       "anlegen.", str(exc))
            return
        docs = exe.release_docs(project)
        record = None if branch else exe.read_record(project.code_dir)
        target = branch_ref or self._release_target(project, record)
        tag = f"v{version}{suffix}"
        text = (f"Auf {self.window.project_list.platform_name} wird das Release {tag} "
                f"angelegt, mit dem Tag {tag} auf dem Stand {target[:12]}. Angehängt wird "
                f"{asset.name} ({_size(asset)}) mit dem ganzen Ordner der Exe, darin der Ordner "
                f"{exe.home_name(project, current)}-{version}.")
        if docs:
            text += f" Dazu einzeln: {', '.join(d.name for d in docs)}."
        text += " Jeder mit Zugriff auf das Repository kann sie herunterladen."
        if record is not None and record.source == "cockpit" and \
                exe.status_line(project).endswith("älter als der Code"):
            text += " Achtung: Die Exe ist älter als der Code."
        if not confirm(self.window, "Exe veröffentlichen", text + " Veröffentlichen?",
                       yes="Veröffentlichen", no="Abbrechen"):
            shutil.rmtree(work_dir, ignore_errors=True)
            return

        def work(task: Task):
            try:
                title = f"Version {version}" + (f", Branch {branch_ref}" if branch else "")
                release = platform.create_release(ref, tag, title, notes, target)
                platform.upload_asset(ref, release, asset)
                for doc in docs:
                    platform.upload_asset(ref, release, doc)
            finally:
                shutil.rmtree(work_dir, ignore_errors=True)
            return release

        def done(release) -> None:
            self.uploading.discard(project.id)
            if record is not None:
                record.version = version
                exe.write_record(project.code_dir, record)
            moved = exe.mark_published(project, current, version, rename=not branch)
            where = f" Die Exe liegt jetzt in {project.exe_dir.name}\\{moved.parent.name}." \
                if moved.parent != current.parent else ""
            QGuiApplication.clipboard().setText(release.url)
            self._after(project, f"Version {version} veröffentlicht. Link kopiert.{where}")
            show_info(self.window, "Exe veröffentlicht", f"Version {version} ist veröffentlicht. "
                      f"Der Link ist in der Zwischenablage: {release.url}")

        def failed() -> None:
            self.uploading.discard(project.id)
            self.window.refresh_actions(keep_selection=True)

        announce("Release wird angelegt und die Exe hochgeladen.")
        self.uploading.add(project.id)
        self.window.refresh_actions(keep_selection=True)
        self.controller.run_task(f"exe:{project.id}", work, done, "Exe veröffentlichen",
                                 on_failed=failed, transfer=True)

    def _suggested_version(self, project: Project, tags: list[str]) -> str:
        """Mit dem Feature Versionen die zuletzt gesetzte, wenn es dazu noch kein Release gibt
        (Frage 4 zu Phase 9). Sonst die nächste nach dem letzten Release."""
        from cockpit.features.versions import versions
        from cockpit.features.versions.manifest import FEATURE_ID
        try:
            active = (FEATURE_ID in self.services.registry
                      and self.services.features.active(FEATURE_ID, project))
        except CockpitError:
            active = False
        if active:
            latest = versions.current(project.code_dir)
            if latest and f"v{latest}" not in tags and latest not in tags:
                return latest
        return exe.next_version(tags)

    def _release_target(self, project: Project, record) -> str:
        """Commit der Exe, wenn er schon auf der Plattform ist, sonst der Haupt-Branch."""
        from cockpit.core import git
        state = git.status(project.code_dir)
        branch = state.default_branch or "main"
        if record is not None and record.commit:
            remote = git.run(["branch", "-r", "--contains", record.commit], project.code_dir,
                             check=False).stdout
            if remote.strip():
                return record.commit
        return branch

    def fetch(self, context: ActionContext) -> None:
        project = context.project
        platform = self._platform(project)
        if platform is None:
            return
        ref = repo_admin.repo_ref(project)

        def work(task: Task):
            for release in platform.releases(ref):
                asset = exe.pick_asset(release.assets)
                if asset is not None:
                    return release, asset
            return None

        self.controller.run_task(f"exe:{project.id}", work,
                                 lambda found: self._ask_fetch(project, platform, ref, found),
                                 "Exe aus dem Release holen")

    def _ask_fetch(self, project, platform, ref, found) -> None:
        if found is None:
            show_info(self.window, "Exe aus dem Release holen", "In den Releases dieses "
                      "Repositories gibt es keine Exe-Datei und keine ZIP-Datei.")
            return
        release, asset = found
        size = f"{max(1, round(asset.size / (1024 * 1024)))} MB"
        text = (f"Die Datei {asset.name} ({size}) aus dem Release {release.tag} wird "
                "heruntergeladen und in den Ordner Release übernommen.")
        if exe.current_exe(project) is not None:
            text += " Die bisherige Exe kommt vorher in die Sicherheitskopien."
        if not confirm(self.window, "Exe aus dem Release holen", text + " Holen?", yes="Holen",
                       no="Abbrechen"):
            return
        version = release.tag.lstrip("v")

        def work(task: Task):
            work_dir = Path(tempfile.mkdtemp(prefix="codecockpit-download-",
                                             dir=paths.cache_dir()))
            try:
                download = work_dir / asset.name
                platform.download_asset(ref, asset, download, task.cancel_event)
                return exe.adopt(project, exe.unpack(download, work_dir), "release", version,
                                 move=True)
            finally:
                shutil.rmtree(work_dir, ignore_errors=True)

        announce("Exe wird heruntergeladen.")
        self.controller.run_task(f"exe:{project.id}", work,
                                 lambda target: self._after(
                                     project, f"Exe aus dem Release {release.tag} übernommen."),
                                 "Exe aus dem Release holen", transfer=True)
