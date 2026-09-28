"""Die Exe in der Oberfläche (Konzept 10.4, Phase 10).

Aktionen: "Exe hinzufügen …" auf der Projektzeile. Bei "Exe": Exe aus dem Code erstellen bzw.
aktualisieren, Exe-Datei wählen, Exe veröffentlichen, Exe aus dem Release holen, Exe-Einrichtung
prüfen, Wie funktioniert die Exe?. Exe starten und Exe-Ordner öffnen stehen im Kern.

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

from PySide6.QtCore import QItemSelectionModel
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFileDialog, QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import exe, paths, repo_admin
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.features import settings_fields as sf
from cockpit.core.projects import Project
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import (FocusDialog, PlainEdit, choose_from_list, click_focused_button,
                               confirm, label_for, make_copyable, pick_folder, show_info)
from cockpit.ui.error_dialog import show_error
from cockpit.ui.form_builder import FormError, SettingsForm
from cockpit.ui.repo_dialogs import button_row
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

log = logging.getLogger(__name__)

FEATURE_ID = "exe_build"
ONE_FILE, FOLDER = "Eine Exe-Datei", "Programmordner"


def _size(path: Path) -> str:
    size = path.stat().st_size if path.is_file() else sum(
        p.stat().st_size for p in path.rglob("*") if p.is_file())
    return f"{max(1, round(size / (1024 * 1024)))} MB"


# -- Fenster ----------------------------------------------------------------------------------------
class BuildSettingsDialog(FocusDialog):
    """Erster Bau: Startdatei, Name, Bauart, Konsolenfenster, Symbol."""

    def __init__(self, project: Project, parent: QWidget | None = None,
                 current: exe.BuildSettings | None = None) -> None:
        from cockpit.features.exe_build.setup_check import data_folders, guess_start_file
        super().__init__(parent)
        self.setWindowTitle(f"Exe-Einstellungen: {project.name}" if current
                            else f"Exe einrichten: {project.name}")
        self.current = current
        self.settings: exe.BuildSettings | None = None
        if current is None:
            current = exe.BuildSettings(guess_start_file(project.code_dir),
                                        project.name.replace(" ", "-"),
                                        beside=data_folders(project.code_dir))
        fields = [sf.Text("start_file", "Startdatei", current.start_file, required=True),
                  sf.Text("name", "Name der Exe", current.name, required=True,
                          pattern=r"[\w\-. ]+", pattern_hint="Bitte nur Buchstaben, Ziffern, "
                          "Leerzeichen, Punkt und Bindestrich."),
                  sf.Choice("mode", "Bauart", ONE_FILE if current.one_file else FOLDER,
                            options=(ONE_FILE, FOLDER)),
                  sf.YesNo("windowed", "Ohne Konsolenfenster (für Programme mit Fenster)",
                           current.windowed),
                  sf.Text("icon", "Symbol, freiwillig, eine .ico-Datei im Ordner Code",
                          current.icon),
                  sf.Text("beside", "Ordner neben der Exe, mit Komma getrennt, zum Beispiel "
                          "Meine-Vokabeln", ", ".join(current.beside))]
        self.form = SettingsForm(fields)
        ok = QPushButton("&Weiter")
        ok.setDefault(True)
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        self.code_dir = project.code_dir
        layout = QVBoxLayout(self)
        layout.addWidget(self.form)
        layout.addLayout(button_row(None, ok, cancel))
        self.resize(560, 280)
        self.initial_focus_widget = self.form.first_focus()

    def check(self) -> None:
        try:
            values = self.form.values()
        except FormError as exc:
            show_error(self, self.windowTitle(), exc.message)
            self.form.focus_field(exc.key)
            return
        if not (self.code_dir / values["start_file"]).is_file():
            show_error(self, self.windowTitle(), f"Die Startdatei {values['start_file']} gibt es "
                       "im Ordner Code nicht.")
            self.form.focus_field("start_file")
            return
        if values["icon"] and not (self.code_dir / values["icon"]).is_file():
            show_error(self, self.windowTitle(), f"Das Symbol {values['icon']} gibt es nicht.")
            self.form.focus_field("icon")
            return
        beside = [n.strip() for n in values["beside"].split(",") if n.strip()]
        missing = [n for n in beside if not (self.code_dir / n).exists()]
        if missing:
            show_error(self, self.windowTitle(), f"Im Ordner Code gibt es {missing[0]} nicht.")
            self.form.focus_field("beside")
            return
        keep = self.current or exe.BuildSettings()
        self.settings = exe.BuildSettings(values["start_file"], values["name"],
                                          values["mode"] == ONE_FILE, values["windowed"],
                                          values["icon"], keep.datas, keep.hidden_imports,
                                          keep.self_test, keep.test_seconds, beside)
        self.accept()


class BuildDialog(FocusDialog):
    """Bau im Hintergrund mit Ausgabe. result nach dem Ende: BuildResult oder None."""

    def __init__(self, services, project: Project, settings: exe.BuildSettings,
                 parent: QWidget | None = None, branch_dir: Path | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.project = project
        self.branch_dir = branch_dir                 # Exe aus einem Branch-Ordner (10f)
        self.result: exe.BuildResult | None = None
        self.setWindowTitle(f"Exe erstellen: {project.name}" + (f", Branch {branch_dir.name}"
                                                                 if branch_dir else ""))
        self.output = QListWidget()
        self.output.setWordWrap(True)
        make_copyable(self.output)
        self.stop_button = QPushButton("&Abbrechen")
        self.stop_button.clicked.connect(self.stop)
        self.close_button = QPushButton("&Schließen")
        self.close_button.clicked.connect(self.reject)
        for button in (self.stop_button, self.close_button):
            button.setAutoDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(label_for(self.output, "&Ausgabe:"))
        layout.addWidget(self.output, 1)
        layout.addLayout(button_row(None, self.stop_button, self.close_button))
        self.resize(820, 560)
        self.initial_focus_widget = self.output

        def work(task: Task):
            return exe.build(project, settings, task.status.emit, task.status.emit,
                             task.cancel_event, branch_dir)

        self.task: Task | None = Task(work, self)
        self.task.status.connect(self.add_line)
        self.task.result.connect(self.finished_ok)
        self.task.error.connect(self.failed)
        self.task.cancelled.connect(lambda: self.ended("Abgebrochen. Die bisherige Exe bleibt."))
        self.task.finished.connect(self._done)
        self.add_line("Der Bau läuft. Beim ersten Mal dauert er einige Minuten.")
        self.task.start()

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)

    def add_line(self, text: str) -> None:
        self.output.addItem(text)
        if text.startswith("Schritt "):
            announce(text)
        if not self.output.hasFocus():
            self.output.setCurrentRow(self.output.count() - 1,
                                      QItemSelectionModel.SelectionFlag.ClearAndSelect)

    def finished_ok(self, result: exe.BuildResult) -> None:
        if result.untested:
            result = self.ask_untested(result)
            if result is None:
                return
        self.result = result
        if result.branch:
            text = f"Exe aus dem Branch erstellt und abgelegt: {result.exe.name}."
            if result.backup is not None:
                text += " Die vorherige Exe dieses Branches steht in den Sicherheitskopien."
            self.ended(text)
            return
        tested = "getestet" if exe.read_record(self.project.code_dir) is None or \
            exe.read_record(self.project.code_dir).tested else "nicht geprüft"
        text = (f"Exe erstellt, {tested}. Sie wird beim nächsten Start übernommen."
                if result.pending else f"Exe erstellt, {tested} und übernommen: "
                                       f"{result.exe.name}.")
        if result.backup is not None:
            text += " Die bisherige Exe steht in den Sicherheitskopien."
        if result.placed:
            text += f" Neu neben der Exe: {', '.join(result.placed)}."
        self.ended(text)

    def ask_untested(self, result: exe.BuildResult) -> exe.BuildResult | None:
        """Windows ließ den Test nicht zu: Der Nutzer prüft selbst (Wunsch aus Phase 10)."""
        self.output.addItem("Das Cockpit kann die neue Exe nicht selbst prüfen, weil Windows den "
                            "Start aus dem Cockpit blockiert.")
        text = ("Das Cockpit kann die neue Exe nicht selbst prüfen, weil Windows den Start "
                "blockiert. Soll sie trotzdem übernommen werden? Die bisherige kommt in die "
                "Sicherheitskopien. Bitte starten Sie die neue Exe danach selbst und prüfen Sie "
                "sie. Beim nächsten Bau versucht das Cockpit den Test wieder.")
        if not confirm(self, "Exe nicht geprüft", text, yes="Übernehmen", no="Verwerfen"):
            exe.discard(result)
            self.ended("Die neue Exe wurde verworfen. Die bisherige bleibt.")
            return None
        try:
            return exe.install_untested(self.project, result)
        except CockpitError as exc:
            self.ended(f"Fehler: {exc.message}", urgent=True)
            return None

    def failed(self, message: str, details: str) -> None:
        if details:
            self.output.addItem(details)
        self.ended(f"Fehler: {message}", urgent=True)

    def ended(self, text: str, urgent: bool = False) -> None:
        self.output.addItem(text)
        self.output.setCurrentRow(self.output.count() - 1,
                                  QItemSelectionModel.SelectionFlag.ClearAndSelect)
        announce(text, urgent=urgent)

    def _done(self) -> None:
        task, self.task = self.task, None
        self.stop_button.setVisible(False)
        if task is not None:
            task.wait()                      # Thread ganz beendet, sonst bricht Qt ab
            task.deleteLater()

    @property
    def running(self) -> bool:
        return self.task is not None

    def stop(self) -> None:
        if self.task is not None:
            self.task.cancel()
            announce("Wird abgebrochen.")

    def reject(self) -> None:
        if self.running:
            self.stop()
            return
        super().reject()

    def done(self, code: int) -> None:
        if self.task is not None:
            self.task.cancel()
            self.task.wait(10000)
        super().done(code)


class PublishDialog(FocusDialog):
    """Version und Versionshinweise für "Exe veröffentlichen"."""

    def __init__(self, project: Project, suggestion: str, tags: list[str], asset: str,
                 parent: QWidget | None = None, source=None) -> None:
        super().__init__(parent)
        self.tags = tags
        self.version = self.notes = ""
        self.setWindowTitle(f"Exe veröffentlichen: {project.name}, {asset}")
        self.version_edit = QLineEdit(suggestion)
        version_label = label_for(self.version_edit, "&Version:")
        self.notes_edit = PlainEdit()
        notes_label = label_for(self.notes_edit, "Versions&hinweise:")
        ok = QPushButton("&Veröffentlichen")
        ok.setDefault(True)
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        for widget in (version_label, self.version_edit, notes_label, self.notes_edit):
            layout.addWidget(widget)
        self.suggest_button = None
        if source is not None:
            from cockpit.ui.ai_suggest import SuggestButton
            self.suggest_button = SuggestButton(self, source, self.apply_suggestion,
                                                self.notes_edit)
            self.suggest_button.setText("Vorschlag der K&I")
            layout.addLayout(button_row(self.suggest_button, None))
        layout.addLayout(button_row(None, ok, cancel))
        self.resize(600, 420)
        self.initial_focus_widget = self.version_edit

    def apply_suggestion(self, suggestion) -> None:
        text = "\n".join(p for p in (suggestion.summary, suggestion.details) if p)
        self.notes_edit.setPlainText(text)

    def check(self) -> None:
        try:
            self.version = exe.check_version(self.version_edit.text(), self.tags)
        except CockpitError as exc:
            show_error(self, self.windowTitle(), exc.message)
            self.version_edit.setFocus()
            return
        self.notes = self.notes_edit.toPlainText().strip()
        self.accept()

    def reject(self) -> None:
        from cockpit.ui.ai_suggest import handle_escape
        if not handle_escape(self.suggest_button):
            super().reject()

    def done(self, code: int) -> None:
        if self.suggest_button is not None:
            self.suggest_button.wait()
        super().done(code)


# -- Aktionen ---------------------------------------------------------------------------------------
class ExeActions:
    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services

    # -- Sichtbarkeit ------------------------------------------------------------------------
    def _building(self, context: ActionContext) -> bool:
        project = context.project
        if project is None or not project.has_exe_dir or FEATURE_ID not in self.services.registry:
            return False
        try:
            return self.services.features.active(FEATURE_ID, project)
        except CockpitError:
            return False

    def actions(self) -> list[Action]:
        has_exe = lambda c: exe.current_exe(c.project) is not None     # noqa: E731
        return [
            Action("add_exe", "Exe hinzufügen …", Target.PROJECT, self.add_exe,
                   visible=lambda c: c.project is not None and c.project.folder_found
                   and not c.project.has_exe_dir, order=72),
            Action("build_exe", "Exe aus dem Code erstellen …", Target.EXE, self.build,
                   visible=lambda c: self._building(c) and not has_exe(c), order=20),
            Action("update_exe", "Exe aus dem Code aktualisieren …", Target.EXE, self.build,
                   visible=lambda c: self._building(c) and has_exe(c), order=20),
            Action("choose_exe", "Exe-Datei wählen …", Target.EXE, self.choose,
                   visible=lambda c: c.project is not None and c.project.has_exe_dir, order=30),
            Action("publish_exe", "Exe veröffentlichen …", Target.EXE, self.publish,
                   availability=self.controller._account_availability,
                   visible=lambda c: self._building(c) and has_exe(c)
                   and c.project.remote is not None, order=40),
            Action("fetch_exe", "Exe aus dem Release holen …", Target.EXE, self.fetch,
                   availability=self.controller._account_availability,
                   visible=lambda c: c.project is not None and c.project.has_exe_dir
                   and c.project.remote is not None, order=45),
            Action("check_exe", "Exe-Einrichtung prüfen", Target.EXE, self.check_setup,
                   visible=self._building, order=60),
            Action("exe_settings", "Exe-Einstellungen …", Target.EXE, self.edit_settings,
                   visible=lambda c: self._building(c)
                   and exe.read_settings(c.project.code_dir) is not None, order=62),
            Action("exe_ai_fix", "Exe mit KI einrichten …", Target.EXE, self.ai_fix,
                   visible=self._building, order=64),
            Action("exe_guide", "Wie funktioniert die Exe? …", Target.EXE,
                   lambda c: self.window.show_guide(exe.EXE_GUIDE, "Wie funktioniert die Exe?"),
                   visible=lambda c: c.project is not None, order=95),
            Action("build_branch_exe", "Exe aus diesem Branch erstellen …", Target.CODE,
                   self.build_branch, visible=self._branch_building, order=70),
        ]

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
        name = exe.branch_exe_name(settings, tree.folder, Path("x.exe") if settings.one_file
                                   else Path("."))
        text = (f"Das Cockpit baut die Exe aus dem Ordner Code\\{tree.folder} und testet sie. "
                f"Sie kommt als {name} in den Ordner Exe. Die normale Exe aus "
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

    # -- Exe hinzufügen ---------------------------------------------------------------------
    def add_exe(self, context: ActionContext) -> None:
        project = context.project
        if project.exe_dir is None:                      # verknüpftes Projekt
            folder = pick_folder(self.window, "Ordner für die Exe wählen", str(project.code_dir))
            if folder is None:
                return
            project = self.services.projects.set_exe_dir(project, folder)
        elif not confirm(self.window, "Exe hinzufügen",
                         f"Im Projektordner wird der Ordner Exe angelegt: {project.exe_dir}. "
                         "Danach steht Exe unter Code. Anlegen?", yes="Anlegen", no="Abbrechen"):
            return
        try:
            exe.add_exe_dir(project)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "Exe hinzufügen", getattr(exc, "message", str(exc)))
            return
        self._after(project, "Ordner Exe angelegt.")

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
        text = f"{source.name} wird in den Ordner Exe kopiert."
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
    def build(self, context: ActionContext) -> None:
        project = context.project
        if exe.find_python() is None and not exe.venv_python(project.code_dir).is_file():
            if confirm(self.window, "Exe erstellen", "Python wurde nicht gefunden. Zum Erstellen "
                       "einer Exe braucht das Cockpit Python. Anleitung anzeigen?",
                       yes="Anleitung", no="Schließen", default_yes=True):
                self.window.show_guide(exe.PYTHON_GUIDE, "Python installieren")
            return
        settings = exe.read_settings(project.code_dir)
        first = settings is None
        if first:
            dialog = BuildSettingsDialog(project, self.window)
            if not dialog.exec() or dialog.settings is None:
                return
            settings = dialog.settings
        settings.test_seconds = int(self.services.features.setting(FEATURE_ID, "test_seconds"))
        current = exe.current_exe(project)
        parts = []
        if first:
            parts.append(f"Im Ordner Code entsteht die Datei {settings.spec_name} mit den "
                         "Einstellungen. Sie wird mit hochgeladen.")
        parts.append("Das Cockpit bereitet die virtuelle Umgebung .venv mit Ihren Bibliotheken "
                     "und PyInstaller vor, baut die Exe in einem temporären Ordner und startet "
                     "sie zum Test.")
        if current is not None:
            parts.append("Nur wenn der Test klappt, kommt die bisherige Exe in die "
                         "Sicherheitskopien, und die neue ersetzt sie.")
        if not confirm(self.window, "Exe erstellen", " ".join(parts) + " Starten?",
                       yes="Starten", no="Abbrechen"):
            return
        if first:
            exe.write_settings(project.code_dir, settings)
        dialog = BuildDialog(self.services, project, settings, self.window)
        dialog.exec()
        self.window.reload_projects(refresh=False)
        self.window.project_list.select(Target.EXE, project.id)
        self.window.refresh_status([project.id])
        if dialog.result is not None and dialog.result.pending:
            self.offer_restart(project)

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

    # -- Einstellungen ändern (Phase 10g) ---------------------------------------------------
    def edit_settings(self, context: ActionContext) -> None:
        project = context.project
        dialog = BuildSettingsDialog(project, self.window, exe.read_settings(project.code_dir))
        if not dialog.exec() or dialog.settings is None:
            return
        settings = dialog.settings
        if not confirm(self.window, "Exe-Einstellungen",
                       f"Die Einstellungen kommen in cockpit.toml. Die Datei {settings.spec_name} "
                       "wird neu geschrieben, die bisherige kommt in die Sicherheitskopien. Die "
                       "Exe ändert sich erst beim nächsten Bau. Speichern?", yes="Speichern",
                       no="Abbrechen"):
            return
        try:
            exe.change_settings(project.code_dir, project.name, settings)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "Exe-Einstellungen", getattr(exc, "message", str(exc)))
            return
        announce("Exe-Einstellungen gespeichert.")
        if confirm(self.window, "Exe-Einstellungen", "Soll die Exe jetzt mit den neuen "
                   "Einstellungen gebaut werden?", yes="Jetzt bauen", no="Später"):
            self.build(context)

    # -- Mit KI einrichten (Phase 10g) --------------------------------------------------------
    def ai_fix(self, context: ActionContext) -> None:
        from cockpit.ui.exe_ai import ExeAIFlow
        ExeAIFlow(self, context.project).start()

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

    def publish(self, context: ActionContext) -> None:
        project = context.project
        platform = self._platform(project)
        if platform is None:
            return
        ref = repo_admin.repo_ref(project)
        current = exe.current_exe(project)

        def work(task: Task):
            return [r.tag for r in platform.releases(ref)]

        self.controller.run_task(f"exe:{project.id}", work,
                                 lambda tags: self._ask_publish(project, platform, ref, current,
                                                                tags), "Exe veröffentlichen")

    def _ask_publish(self, project, platform, ref, current: Path, tags: list[str]) -> None:
        from cockpit.ui import ai_suggest
        work_dir = Path(tempfile.mkdtemp(prefix="codecockpit-release-", dir=paths.cache_dir()))
        asset = exe.asset_for_upload(project, current, work_dir)
        source = ai_suggest.for_release_notes(self.services, project, tags)
        dialog = PublishDialog(project, exe.next_version(tags), tags, asset.name, self.window,
                               source=source)
        if not dialog.exec():
            shutil.rmtree(work_dir, ignore_errors=True)
            return
        record = exe.read_record(project.code_dir)
        target = self._release_target(project, record)
        text = (f"Auf {self.window.project_list.platform_name} wird das Release v{dialog.version} "
                f"angelegt, mit dem Tag v{dialog.version} auf dem Stand {target[:12]}. Die Exe "
                f"{asset.name} ({_size(asset)}) wird angehängt. Jeder mit Zugriff auf das "
                "Repository kann sie herunterladen.")
        if record is not None and record.source == "cockpit" and \
                exe.status_line(project).endswith("älter als der Code"):
            text += " Achtung: Die Exe ist älter als der Code."
        if not confirm(self.window, "Exe veröffentlichen", text + " Veröffentlichen?",
                       yes="Veröffentlichen", no="Abbrechen"):
            shutil.rmtree(work_dir, ignore_errors=True)
            return
        version, notes = dialog.version, dialog.notes

        def work(task: Task):
            try:
                release = platform.create_release(ref, f"v{version}", f"Version {version}",
                                                  notes, target)
                platform.upload_asset(ref, release, asset)
            finally:
                shutil.rmtree(work_dir, ignore_errors=True)
            return release

        def done(release) -> None:
            if record is not None:
                record.version = version
                exe.write_record(project.code_dir, record)
            QGuiApplication.clipboard().setText(release.url)
            self._after(project, f"Version {version} veröffentlicht. Link kopiert.")
            show_info(self.window, "Exe veröffentlicht", f"Version {version} ist veröffentlicht. "
                      f"Der Link ist in der Zwischenablage: {release.url}")

        announce("Release wird angelegt und die Exe hochgeladen.")
        self.controller.run_task(f"exe:{project.id}", work, done, "Exe veröffentlichen")

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
                "heruntergeladen und in den Ordner Exe übernommen.")
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
                                 "Exe aus dem Release holen")
