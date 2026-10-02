"""Die Exe in der Oberfläche (Konzept 10.4, Phase 10).

Aktionen: "Exe hinzufügen …" auf der Projektzeile. Bei "Exe" (zusammengefasst nach dem Wunsch des
Nutzers, 30.09.2026): Exe aus dem Code erstellen, Exe veröffentlichen, Exe einlesen,
Exe-Einstellungen, Links der Exe, Wie funktioniert die Exe?. Exe starten und Exe-Ordner öffnen
stehen im Kern.

"Exe aus dem Code erstellen …" fragt zuerst: Exe mit KI einrichten oder Exe ohne KI einrichten.
Mit eingerichteter Text-KI steht "mit KI" oben. Danach zeigt ReadyDialog das Ergebnis mit "Exe
erstellen" und "Abbrechen". "Exe erstellen" startet den Bau in vier Schritten.
"Exe einlesen …" fragt: Exe-Datei wählen oder Exe aus einem Release wählen.

BuildDialog: Ausgabe von PyInstaller als Liste, eine Zeile pro Zeile. Die Schritte sagt NVDA an
("Schritt 2 von 4: Exe wird gebaut"). Escape bricht einen laufenden Bau ab, danach schließt es.
Alles, was Dateien verändert, beschreibt vorher, was passiert, und braucht eine Bestätigung.
"""
from __future__ import annotations

import dataclasses
import logging
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QItemSelectionModel, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QFileDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QVBoxLayout, QWidget)

from cockpit.core import exe, paths, repo_admin
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.features import settings_fields as sf
from cockpit.core.projects import Project
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import (FocusDialog, PlainEdit, ask_buttons, choose_from_list,
                               click_focused_button, confirm, label_for, make_copyable,
                               pick_folder, show_info)
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
NOT_BESIDE = {"cockpit.toml", "requirements.txt", ".gitignore"}
BESIDE_ROLE = Qt.ItemDataRole.UserRole + 1


def beside_candidates(code_dir: Path) -> list[str]:
    """Was neben die Exe kommen kann: Ordner und Dateien im Ordner Code, zum Beispiel auch die
    README (Wunsch des Nutzers, 02.10.2026). Ohne Python-Code, .spec-Datei, Pakete, versteckte
    und Build-Ordner."""
    from cockpit.features.exe_build.setup_check import SKIP_DIRS, _packages
    packages = _packages(code_dir)
    names = []
    for path in sorted(code_dir.iterdir(), key=lambda p: p.name.lower()):
        name = path.name
        if name.startswith(".") or name in SKIP_DIRS or name in packages or name in NOT_BESIDE:
            continue
        if path.is_file() and path.suffix.lower() in (".py", ".pyw", ".pyc", ".spec", ".exe"):
            continue
        names.append(name)
    return names


class BuildSettingsDialog(FocusDialog):
    """Erster Bau: Startdatei, Name, Bauart, Konsolenfenster, Symbol. Darunter die Liste "Ordner
    und Dateien neben der Exe" mit Kontrollkästchen (Wunsch des Nutzers, 02.10.2026): vom Code
    benutzte Ordner sind vorgeschlagen und so benannt. Mit "Neuer Ordner" kommt ein Name dazu,
    den es im Ordner Code noch nicht gibt. Er wird neben der Exe leer angelegt.
    Wunsch des Nutzers (03.10.2026): Was der Code unbedingt braucht, heißt "…, unbedingt nötig"
    und ist immer vorab angehakt. Wer es abhakt, wird beim Weiter gewarnt.
    Bei einer von Hand geschriebenen .spec-Datei stehen Startdatei, Name und Bauart dort. Das
    Formular dafür ist dann ausgeblendet, das Fenster sagt das, und gespeichert wird nur die
    Liste."""

    def __init__(self, project: Project, parent: QWidget | None = None,
                 current: exe.BuildSettings | None = None, in_flow: bool = False) -> None:
        from cockpit.features.exe_build.setup_check import (data_folders, guess_start_file,
                                                            required_beside)
        super().__init__(parent)
        # in_flow: erster Schritt von "Exe aus dem Code erstellen" (Wunsch des Nutzers,
        # 02.10.2026). Mit Weiter wird gespeichert wie unter "Exe-Einstellungen …".
        if in_flow:
            self.setWindowTitle(f"Exe aus dem Code erstellen: {project.name}, Einstellungen")
        else:
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
                          current.icon)]
        self.form = SettingsForm(fields)
        self.handmade = self.current is not None and \
            not exe.own_spec(project.code_dir / self.current.spec_name)
        self.required = required_beside(project.code_dir, self.current)
        self.beside = QListWidget()
        beside_label = label_for(self.beside, "&Ordner und Dateien neben der Exe:")
        names = list(self.required)
        names += [n for n in beside_candidates(project.code_dir) if n not in names]
        names += [n for n in current.beside if n not in names]
        for name in names:
            needed = name in self.required
            self._add_beside(name, needed or name in current.beside, needed,
                             not (project.code_dir / name).exists())
        self.beside.setCurrentRow(0)
        self.new_name = QLineEdit()
        new_label = label_for(self.new_name, "&Neuer Ordner neben der Exe:")
        add = QPushButton("&Hinzufügen")
        add.clicked.connect(self.add_new)
        ok = QPushButton("&Weiter")
        ok.setDefault(True)
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        self.code_dir = project.code_dir
        layout = QVBoxLayout(self)
        if in_flow:
            hint = QLabel("Prüfen Sie zuerst die Einstellungen, vor allem die Ordner neben der "
                          "Exe. Mit Weiter werden sie gespeichert, wie unter Exe-Einstellungen. "
                          "Danach richten Sie die Exe mit oder ohne KI ein.")
            hint.setWordWrap(True)
            layout.addWidget(hint)
        if self.handmade:
            spec = QLabel(f"Die Bauanleitung {self.current.spec_name} ist von Hand geschrieben. "
                          "Startdatei, Name, Bauart und Symbol stehen dort. Das Cockpit ändert "
                          "sie nicht, hier wählen Sie nur, was neben die Exe kommt.")
            spec.setWordWrap(True)
            layout.addWidget(spec)
            self.form.setVisible(False)
        layout.addWidget(self.form)
        layout.addWidget(beside_label)
        layout.addWidget(self.beside, 1)
        layout.addWidget(new_label)
        layout.addLayout(button_row(self.new_name, add, None))
        layout.addLayout(button_row(None, ok, cancel))
        self.resize(600, 560 if in_flow else 520)
        # Im Ablauf zuerst die Ordner, darum geht es meistens; mit Umschalt+Tab die übrigen Felder
        self.initial_focus_widget = self.beside if in_flow or self.handmade \
            else self.form.first_focus()

    def _missing_required_ok(self) -> bool:
        """Ist etwas Unbedingtes abgehakt, nachfragen. Die sichere Antwort hakt es wieder an."""
        chosen = set(self.chosen_beside())
        missing = [n for n in self.required if n not in chosen]
        if not missing:
            return True
        names = ", ".join(missing)
        if confirm(self, self.windowTitle(), f"{names} ist unbedingt nötig, der Code benutzt "
                   "es. Ohne liegt es nicht neben der Exe, und die Exe findet es dann vermutlich "
                   "nicht. Trotzdem weglassen?", yes="Trotzdem weglassen", no="Wieder anhaken"):
            return True
        for row in range(self.beside.count()):
            item = self.beside.item(row)
            if item.data(BESIDE_ROLE) in missing:
                item.setCheckState(Qt.CheckState.Checked)
        self.beside.setFocus()
        return False

    def check(self) -> None:
        if not self._missing_required_ok():
            return
        if self.handmade:
            self.settings = dataclasses.replace(self.current, beside=self.chosen_beside())
            self.accept()
            return
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
        beside = self.chosen_beside()
        keep = self.current or exe.BuildSettings()
        self.settings = exe.BuildSettings(values["start_file"], values["name"],
                                          values["mode"] == ONE_FILE, values["windowed"],
                                          values["icon"], keep.datas, keep.hidden_imports,
                                          keep.self_test, keep.test_seconds, beside)
        self.accept()

    def _add_beside(self, name: str, checked: bool, used: bool, missing: bool) -> None:
        text = name
        if used:
            text += ", unbedingt nötig, vom Code benutzt"
        if missing:
            text += ", wird neben der Exe leer angelegt"
        item = QListWidgetItem(text)
        item.setData(BESIDE_ROLE, name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.beside.addItem(item)

    def chosen_beside(self) -> list[str]:
        return [self.beside.item(r).data(BESIDE_ROLE) for r in range(self.beside.count())
                if self.beside.item(r).checkState() == Qt.CheckState.Checked]

    def add_new(self) -> None:
        name = self.new_name.text().strip().strip("\\/")
        if not name or any(c in name for c in '\\/:*?"<>|'):
            show_error(self, self.windowTitle(),
                       "Bitte einen Ordnernamen ohne \\ / : * ? \" < > | eingeben.")
            self.new_name.setFocus()
            return
        existing = [self.beside.item(r).data(BESIDE_ROLE) for r in range(self.beside.count())]
        if name in existing:
            row = existing.index(name)
            self.beside.item(row).setCheckState(Qt.CheckState.Checked)
        else:
            self._add_beside(name, True, False, not (self.code_dir / name).exists())
            row = self.beside.count() - 1
        self.new_name.clear()
        self.beside.setCurrentRow(row)
        self.beside.setFocus()
        announce(f"{name} kommt neben die Exe.")


def offer_long_paths(parent: QWidget) -> bool:
    """Lange Pfade in Windows einschalten, nach Rückfrage (Wunsch des Nutzers, 01.10.2026).
    Windows fragt danach selbst nach Administratorrechten."""
    from cockpit.core import long_paths
    if long_paths.enabled():
        return True
    if not confirm(parent, "Lange Pfade einschalten",
                   "Windows erlaubt zurzeit nur Pfade bis 260 Zeichen. Einige Bibliotheken haben "
                   "längere Pfade, deshalb ließen sie sich nicht installieren. Soll das Cockpit "
                   "lange Pfade in Windows einschalten? Das gilt für den ganzen Rechner und "
                   "schadet nicht. Windows fragt danach nach Administratorrechten.",
                   yes="Einschalten", no="Nicht jetzt"):
        return False
    if long_paths.enable():
        announce("Lange Pfade sind eingeschaltet. Starten Sie den Bau noch einmal.")
        show_info(parent, "Lange Pfade einschalten", "Lange Pfade sind eingeschaltet. Starten "
                  "Sie den Bau noch einmal.")
        return True
    show_error(parent, "Lange Pfade einschalten", "Lange Pfade wurden nicht eingeschaltet. "
               "Vielleicht wurde die Rückfrage von Windows abgelehnt. Die Anleitung „Wie "
               "funktioniert die Exe?“ beschreibt, wie es von Hand geht.")
    return False


class BuildDialog(FocusDialog):
    """Bau im Hintergrund mit Ausgabe. result nach dem Ende: BuildResult oder None."""

    def __init__(self, services, project: Project, settings: exe.BuildSettings,
                 parent: QWidget | None = None, branch_dir: Path | None = None,
                 branch_name: str = "", continue_after: bool = False) -> None:
        super().__init__(parent)
        # continue_after: nach Erfolg selbst schließen, damit der Ablauf weitergeht (Wunsch
        # des Nutzers, 01.10.2026: beim Bau aus Cockpit-exe-bauen kommt danach die Frage)
        self.continue_after = continue_after
        self.services = services
        self.project = project
        self.branch_dir = branch_dir                 # Exe aus einem Branch-Ordner (10f)
        self.result: exe.BuildResult | None = None
        shown = branch_name or (branch_dir.name if branch_dir else "")
        self.setWindowTitle(f"Exe erstellen: {project.name}" + (f", Branch {shown}"
                                                                 if shown else ""))
        self.output = QListWidget()
        self.output.setWordWrap(True)
        make_copyable(self.output)
        self.stop_button = QPushButton("&Abbrechen")
        self.stop_button.clicked.connect(self.stop)
        self.close_button = QPushButton("&Weiter" if continue_after else "&Schließen")
        self.close_button.clicked.connect(self.reject)
        # Wunsch des Nutzers (02.10.2026): nach einem Fehler die KI das Problem lösen lassen
        self.fix_button = QPushButton("Problem mit &KI lösen")
        self.fix_button.clicked.connect(self.request_fix)
        self.fix_button.setVisible(False)
        self.fix_requested = False
        self.error_text = ""
        for button in (self.stop_button, self.fix_button, self.close_button):
            button.setAutoDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(label_for(self.output, "&Ausgabe:"))
        layout.addWidget(self.output, 1)
        layout.addLayout(button_row(None, self.stop_button, self.fix_button, self.close_button))
        self.resize(820, 560)
        self.initial_focus_widget = self.output

        def work(task: Task):
            return exe.build(project, settings, task.status.emit, task.status.emit,
                             task.cancel_event, branch_dir, branch_name)

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
            if result.placed:
                text += f" Neu neben der Exe: {', '.join(result.placed)}."
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
        if message == exe.LONG_PATHS:
            offer_long_paths(self)
            return
        # Für die KI: Meldung, Details und das Ende der Ausgabe, dort steht meist der Grund
        output = [self.output.item(r).text() for r in range(self.output.count())]
        self.error_text = "\n".join([message, details] + output[-60:])
        self.fix_button.setVisible(True)
        self.fix_button.setDefault(True)
        self.fix_button.setFocus()

    def request_fix(self) -> None:
        if self.running:
            return
        self.fix_requested = True
        self.accept()

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
        if self.continue_after and self.result is not None:
            QTimer.singleShot(0, self.accept)    # erst wenn der Thread ganz fertig ist

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


AFTER_TEST_LATER = "Selbst testen, später in main übernehmen"
AFTER_TEST_KEEP = "Jetzt in main übernehmen, Branch behalten"
AFTER_TEST_DELETE = "Jetzt in main übernehmen und Branch löschen"
WITH_AI = "Exe mit KI einrichten …"
WITHOUT_AI = "Exe ohne KI einrichten …"
FROM_FILE = "Exe-Datei wählen …"
FROM_RELEASE = "Exe aus einem Release wählen …"


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


class SelfTestDialog(FocusDialog):
    """Selbst testen: die Exe starten, ausprobieren und bei einem Problem die Fehlermeldung
    einfügen. "Problem mit KI lösen" gibt sie an die KI (Wunsch des Nutzers, 02.10.2026)."""
    FIX, MERGE = "fix", "merge"

    def __init__(self, project: Project, exe_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.exe_path = exe_path
        self.choice = ""
        self.error_text = ""
        self.setWindowTitle(f"Exe selbst testen: {project.name}")
        self.info = QListWidget()
        info_label = label_for(self.info, "&Hinweise:")
        self.info.setWordWrap(True)
        self.info.addItems([
            f"Starten Sie die Exe mit „Exe starten“ und probieren Sie sie aus. Sie liegt hier: "
            f"{exe_path}.",
            "Klappt etwas nicht, fügen Sie die Fehlermeldung unten ein oder beschreiben Sie, "
            "was passiert. Dann wählen Sie „Problem mit KI lösen“.",
            "Klappt alles, wählen Sie „Funktioniert, in main übernehmen …“.",
            "„Später“ lässt den Branch, wie er ist.",
        ])
        self.info.setCurrentRow(0)
        self.edit = PlainEdit()
        edit_label = label_for(self.edit, "&Fehlermeldung oder Beschreibung:")
        start = QPushButton("Exe &starten")
        start.clicked.connect(self.start_exe)
        fix = QPushButton("Problem mit &KI lösen")
        fix.clicked.connect(self.request_fix)
        merge = QPushButton("Funktioniert, in &main übernehmen …")
        merge.clicked.connect(self.request_merge)
        later = QPushButton("S&päter")
        later.clicked.connect(self.reject)
        for button in (start, fix, merge, later):
            button.setAutoDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(info_label)
        layout.addWidget(self.info, 1)
        layout.addWidget(edit_label)
        layout.addWidget(self.edit, 2)
        layout.addLayout(button_row(start, fix, merge, None, later))
        self.resize(720, 480)
        self.initial_focus_widget = self.info

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)

    def start_exe(self) -> None:
        from cockpit.core import core_actions
        try:
            core_actions.start_program(self.exe_path)
        except OSError as exc:
            show_error(self, self.windowTitle(), "Die Exe ließ sich nicht starten.", repr(exc))
            return
        announce(f"{self.exe_path.name} wird gestartet.")

    def request_fix(self) -> None:
        text = self.edit.toPlainText().strip()
        if not text:
            announce("Bitte fügen Sie zuerst die Fehlermeldung ein oder beschreiben Sie, was "
                     "passiert.")
            self.edit.setFocus()
            return
        self.choice, self.error_text = self.FIX, text
        self.accept()

    def request_merge(self) -> None:
        self.choice = self.MERGE
        self.accept()


def beside_line(project: Project, code_dir: Path | None = None) -> str:
    """Welche Ordner neben die Exe kommen (Rückmeldung des Nutzers vom 02.10.2026)."""
    settings = exe.read_settings(code_dir or project.code_dir) or         exe.read_settings(project.code_dir)
    names = list(settings.beside) if settings is not None else []
    if names:
        return f"Neben die Exe kommen: {', '.join(names)}."
    return "Neben die Exe kommt kein Ordner. Das ändern Sie unter „Exe-Einstellungen …“."


class ReadyDialog(FocusDialog):
    """Nach dem Einrichten: Ergebnis lesen, dann "Exe erstellen" oder "Abbrechen"."""

    def __init__(self, project: Project, lines: list[str], parent: QWidget | None = None,
                 services=None) -> None:
        super().__init__(parent)
        self.repeat_hints = ""            # gesetzt: letzten Schritt mit Hinweisen wiederholen
        self.setWindowTitle(f"Exe aus dem Code erstellen: {project.name}")
        self.list = QListWidget()
        label = label_for(self.list, "&Ergebnis der Einrichtung:")
        self.list.setWordWrap(True)
        self.list.addItems(lines or ["Die Einrichtung ist abgeschlossen."])
        self.list.setCurrentRow(0)
        make_copyable(self.list)
        self.build_button = QPushButton("Exe e&rstellen")
        self.build_button.setDefault(True)
        self.build_button.clicked.connect(self.accept)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.list, 1)
        self.chat = None
        buttons = [self.build_button]
        if services is not None:          # Fragen an die KI (Wunsch des Nutzers, 02.10.2026)
            from cockpit.ui.exe_chat import REPEAT_TEXT, ExeChat
            self.chat = ExeChat(services, project.name, "Die Änderungen der KI sind im Branch "
                                "Cockpit-exe-bauen übernommen, die Exe ist noch nicht gebaut.",
                                lambda: [self.list.item(r).text()
                                         for r in range(self.list.count())], self)
            layout.addWidget(self.chat, 1)
            repeat = QPushButton(REPEAT_TEXT)
            repeat.setAutoDefault(False)
            repeat.clicked.connect(self.repeat)
            buttons.append(repeat)
        layout.addLayout(button_row(*buttons, cancel, None))
        self.resize(700, 560 if services is not None else 380)
        self.initial_focus_widget = self.list

    def repeat(self) -> None:
        from cockpit.ui.exe_chat import NO_HINTS
        if not self.chat.history:
            announce(NO_HINTS)
            self.chat.question.setFocus()
            return
        self.repeat_hints = self.chat.hints()
        self.reject()

    def done(self, code: int) -> None:
        if self.chat is not None:
            self.chat.stop()
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
            Action("build_exe", "Exe aus dem Code erstellen …", Target.EXE, self.build_menu,
                   visible=self._building, order=20,
                   detail=lambda c: exe.build_state(c.project)),
            Action("publish_exe", "Exe veröffentlichen …", Target.EXE, self.publish,
                   availability=self.controller._account_availability,
                   detail=lambda c: exe.publish_state(c.project),
                   visible=lambda c: self._building(c) and has_exe(c)
                   and c.project.remote is not None, order=40),
            Action("import_exe", "Exe einlesen …", Target.EXE, self.import_exe,
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
                   visible=lambda c: c.project is not None, order=95),
            Action("build_branch_exe", "Exe aus diesem Branch erstellen …", Target.CODE,
                   self.build_branch, visible=self._branch_building, order=92),
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
        if exe.find_python() is None and not exe.python_in(exe.build_venv(project)).is_file():
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
        parts.append("Das Cockpit bereitet eine virtuelle Umgebung mit Ihren Bibliotheken "
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
        if dialog.fix_requested:
            self.fix_with_ai(project, dialog.error_text)
            return
        if dialog.result is not None and dialog.result.pending:
            self.offer_restart(project)

    def fix_with_ai(self, project: Project, error: str) -> None:
        """Die KI bekommt die Fehlermeldung, schlägt eine Lösung vor, und die kommt in den Branch
        Cockpit-exe-bauen. Danach "Exe erstellen" aus dem Branch. Scheitert der Bau wieder, gibt
        es wieder "Problem mit KI lösen". So sind mehrere Durchgänge möglich."""
        from cockpit.ui.exe_ai import ExeAIFlow
        context = ActionContext(self.services, project, Target.EXE)
        flow = ExeAIFlow(self, project)
        flow.on_finished = lambda lines, folder=None: self.offer_build(context, lines, folder,
                                                                      flow)
        flow.start_fix(error)

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

    # -- Ein Knopf für Einrichten und Bauen (30.09.2026) ----------------------------------------
    def build_menu(self, context: ActionContext) -> None:
        """In einem Rutsch (Wunsch des Nutzers, 02.10.2026): zuerst die Exe-Einstellungen mit
        den Ordnern neben der Exe, dann einrichten mit oder ohne KI, dann bauen. Mit Text-KI
        steht "mit KI" oben."""
        if not self.settings_step(context.project):
            return
        with_ai_first = not self.services.ai_problem()
        options = [WITH_AI, WITHOUT_AI] if with_ai_first else [WITHOUT_AI, WITH_AI]
        chosen = choose_from_list(self.window, "Exe aus dem Code erstellen", "Einrichtung",
                                  options)
        if chosen is None:
            return
        project = context.project
        if options[chosen] == WITH_AI:
            from cockpit.ui.exe_ai import ExeAIFlow
            flow = ExeAIFlow(self, project)
            flow.on_finished = lambda lines, folder=None: self.offer_build(context, lines,
                                                                          folder, flow)
            flow.start()
            return
        from cockpit.features.exe_build.setup_check import check
        self.controller.run_task(f"exe:{project.id}", lambda task: check(project),
                                 lambda lines: self.offer_build(context, lines),
                                 "Exe einrichten")

    def settings_step(self, project: Project) -> bool:
        """Exe-Einstellungen zeigen, mit dem gespeicherten Stand. Weiter speichert sie in
        cockpit.toml und die .spec-Datei, die bisherige .spec kommt vorher in die
        Sicherheitskopien. False: abgebrochen."""
        current = exe.read_settings(project.code_dir)
        dialog = BuildSettingsDialog(project, self.window, current, in_flow=True)
        if not dialog.exec() or dialog.settings is None:
            return False
        settings = dialog.settings
        if current is not None and settings == current:
            return True
        try:
            exe.change_settings(project.code_dir, project.name, settings)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "Exe-Einstellungen", getattr(exc, "message", str(exc)))
            return False
        announce("Exe-Einstellungen gespeichert.")
        return True

    def offer_build(self, context: ActionContext, lines: list[str],
                    branch_dir: Path | None = None, flow=None) -> None:
        """Ergebnis zeigen. "Exe erstellen" startet den Bau wie bisher in vier Schritten. Hat die
        KI etwas geändert, liegt das im Branch Cockpit-exe-bauen (branch_dir), und gebaut wird
        aus dem Branch."""
        if lines:
            announce(lines[0])
        lines = list(lines) + [beside_line(context.project, branch_dir)]
        with_ai = flow is not None and getattr(flow, "ai", None) is not None
        dialog = ReadyDialog(context.project, lines, self.window,
                             self.services if with_ai else None)
        accepted = dialog.exec()
        if dialog.repeat_hints:
            flow.repeat(dialog.repeat_hints)
            return
        if not accepted:
            return
        if branch_dir is None:
            self.build(context)
        else:
            self.build_ai_branch(context.project, branch_dir)

    # -- Exe aus dem Branch Cockpit-exe-bauen (01.10.2026) -----------------------------------------
    def build_ai_branch(self, project: Project, branch_dir: Path) -> None:
        from cockpit.features.exe_build import exe_branch
        if exe.find_python() is None and \
                not exe.python_in(exe.build_venv(project, branch_dir)).is_file():
            show_error(self.window, "Exe erstellen", "Python wurde nicht gefunden. Zum Erstellen "
                       "einer Exe braucht das Cockpit Python.")
            return
        settings = exe.read_settings(branch_dir) or exe.read_settings(project.code_dir)
        main = exe.read_settings(project.code_dir)
        if settings is not None and main is not None:
            # Die Ordner aus dem ersten Schritt gelten auch für den Branch, dazu was die KI dort
            # ergänzt hat. Ein älterer Branch kennt die neue Auswahl sonst nicht.
            settings.beside = list(dict.fromkeys(main.beside + settings.beside))
        if settings is None:
            dialog = BuildSettingsDialog(project, self.window)
            if not dialog.exec() or dialog.settings is None:
                return
            settings = dialog.settings
        settings.test_seconds = int(self.services.features.setting(FEATURE_ID, "test_seconds"))
        dialog = BuildDialog(self.services, project, settings, self.window,
                             branch_dir=branch_dir, branch_name=exe_branch.BRANCH,
                             continue_after=True)
        dialog.exec()
        self.window.refresh_status([project.id])
        if dialog.fix_requested:
            self.fix_with_ai(project, dialog.error_text)
            return
        if dialog.result is not None and not dialog.result.untested:
            built = dialog.result.exe
            try:                             # Programmordner: Unterordner mit nennen
                shown = str(built.relative_to(project.exe_dir))
            except (ValueError, TypeError):
                shown = built.name
            self.after_branch_test(project, shown, built)

    def after_branch_test(self, project: Project, exe_name: str,
                          exe_path: Path | None = None) -> None:
        """Wunsch des Nutzers: Die Exe aus dem Branch funktioniert. Wie geht es weiter?"""
        from cockpit.features.exe_build import exe_branch
        branch = exe_branch.BRANCH
        choice = ask_buttons(
            self.window, f"Exe aus {branch}",
            f"Die Exe aus dem Branch {branch} ist fertig gebaut und getestet. Sie liegt als "
            f"{exe_name} im Ordner Exe, die normale Exe bleibt. Wie geht es weiter?",
            [AFTER_TEST_LATER, AFTER_TEST_KEEP, AFTER_TEST_DELETE], default=0, escape=0)
        if choice == 0:
            if exe_path is not None:
                self.self_test(project, exe_path)
                return
            self.keep_branch_later(project)
            return
        self.merge_ai_branch(project, delete=choice == 2)

    def keep_branch_later(self, project: Project) -> None:
        from cockpit.features.exe_build import exe_branch
        branch = exe_branch.BRANCH
        where = "" if project.has_branch_folders else (
            f" Der Ordner Code steht noch auf {branch}. Zurück zu main geht es über "
            "„Branches verwalten“.")
        announce(f"Der Branch {branch} bleibt. Übernehmen geht später über „Branches "
                 f"verwalten“, „In main übernehmen …“.{where}")

    def self_test(self, project: Project, exe_path: Path) -> None:
        """Selbst testen (Wunsch des Nutzers, 02.10.2026): Klappt etwas nicht, fügt man die
        Fehlermeldung ein, und die KI versucht, das Problem zu lösen."""
        dialog = SelfTestDialog(project, exe_path, self.window)
        dialog.exec()
        if dialog.choice == SelfTestDialog.FIX:
            self.fix_with_ai(project, dialog.error_text)
        elif dialog.choice == SelfTestDialog.MERGE:
            answer = ask_buttons(self.window, "In main übernehmen",
                                 "Die Exe funktioniert. Soll der Branch nach dem Übernehmen "
                                 "bleiben?", ["Branch behalten", "Branch löschen", "Abbrechen"],
                                 default=2, escape=2)
            if answer == 2:
                self.keep_branch_later(project)
                return
            self.merge_ai_branch(project, delete=answer == 1)
        else:
            self.keep_branch_later(project)

    def merge_ai_branch(self, project: Project, delete: bool) -> None:
        from cockpit.core.sync import ConflictKind
        from cockpit.features.exe_build import exe_branch
        branch = exe_branch.BRANCH
        try:
            outcome = exe_branch.merge_into_main(project)
        except CockpitError as exc:
            show_error(self.window, "In main übernehmen", exc.message, exc.details)
            return
        if outcome.kind is not ConflictKind.NONE and not self._resolve(project, outcome.kind):
            self.window.refresh_status([project.id])
            return
        text = f"{branch} ist in main übernommen. Main ist noch nicht hochgeladen."
        if delete:
            try:
                exe_branch.delete(project)
                text += f" Der Branch {branch} ist gelöscht."
            except CockpitError as exc:
                show_error(self.window, "Branch löschen", exc.message, exc.details)
        self.window.reload_projects(refresh=False)
        self.window.refresh_status([project.id])
        announce(text)

    def _resolve(self, project: Project, kind) -> bool:
        from cockpit.core import sync
        from cockpit.features.exe_build import exe_branch
        from cockpit.ui import sync_dialogs
        announce(f"Konflikte beim Übernehmen von {exe_branch.BRANCH}.")
        dialog = sync_dialogs.ConflictDialog(project.code_dir, kind,
                                             f"Branch {exe_branch.BRANCH}", self.window)
        try:
            if dialog.exec():
                sync.finish(project.code_dir, kind)
                return True
            sync.abort(project.code_dir, kind)
            announce("Übernehmen abgebrochen. Main ist wie vorher.")
        except CockpitError as exc:
            show_error(self.window, "Übernehmen", exc.message, exc.details)
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
        dialog = PublishDialog(project, self._suggested_version(project, tags), tags, asset.name,
                               self.window, source=source)
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
