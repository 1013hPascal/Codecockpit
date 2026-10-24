"""Fenster zur Exe (Phase 10): Einstellungen zum Bau, der Bau selbst und das Veröffentlichen.

Aus exe_flow.py herausgelöst am 21.10.2026, nur verschoben. Die Namen sind weiter über exe_flow
erreichbar.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtWidgets import (QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout, QWidget)

from cockpit.core import exe
from cockpit.core.errors import CockpitError
from cockpit.core.features import settings_fields as sf
from cockpit.core.projects import Project
from cockpit.ui.announcer import announce
from cockpit.ui.common import (FocusDialog, PlainEdit, click_focused_button, confirm, label_for,
                               make_copyable, show_info)
from cockpit.ui.error_dialog import show_error
from cockpit.ui.form_builder import FormError, SettingsForm
from cockpit.ui.repo_dialogs import button_row
from cockpit.ui.tasks import Task

ONE_FILE, FOLDER = "Eine Exe-Datei", "Programmordner"
AUTO_PYTHON = "Automatisch (empfohlen)"


# -- Fenster ----------------------------------------------------------------------------------------
NOT_BESIDE = {"cockpit.toml", "requirements.txt", ".gitignore"}
BESIDE_ROLE = Qt.ItemDataRole.UserRole + 1
ALWAYS = ", kommt immer mit"


def beside_candidates(code_dir: Path) -> list[str]:
    """Was neben die Exe kommen kann: Ordner und Dateien im Ordner Repository. Ohne Python-Code,
    .spec-Datei, Pakete, versteckte und Build-Ordner. README und Lizenz stehen nicht hier, sie
    kommen immer mit (Wunsch des Nutzers vom 03.10.2026)."""
    from cockpit.features.exe_build.setup_check import SKIP_DIRS, _packages
    packages = _packages(code_dir)
    names = []
    for path in sorted(code_dir.iterdir(), key=lambda p: p.name.lower()):
        name = path.name
        if name.startswith(".") or name in SKIP_DIRS or name in packages or name in NOT_BESIDE:
            continue
        if path.is_file() and (path.suffix.lower() in (".py", ".pyw", ".pyc", ".spec", ".exe")
                               or exe.is_doc(name)):
            continue
        names.append(name)
    return names


class BuildSettingsDialog(FocusDialog):
    """Startdatei, Name, Bauart, Konsolenfenster, Symbol. Darunter die Liste "Ordner und Dateien
    neben der Exe" mit Kontrollkästchen (Wunsch des Nutzers, 02.10.2026): Was der Code unbedingt
    braucht, heißt "…, unbedingt nötig, vom Code benutzt" und ist immer vorab angehakt. Wer es
    abhakt, wird beim Weiter gewarnt. README und Lizenz stehen ohne Kästchen in der Liste, mit
    "kommt immer mit" (Wunsch des Nutzers vom 03.10.2026).
    Bei einer von Hand geschriebenen .spec-Datei stehen Startdatei, Name und Bauart dort. Das
    Formular dafür ist dann ausgeblendet, das Fenster sagt das, und gespeichert wird nur die
    Liste."""

    def __init__(self, project: Project, parent: QWidget | None = None,
                 current: exe.BuildSettings | None = None, in_flow: bool = False,
                 code_dir: Path | None = None) -> None:
        from cockpit.features.exe_build.setup_check import guess_start_file, required_beside
        super().__init__(parent)
        code_dir = code_dir or project.code_dir
        # in_flow: Schritt 1 von "Exe aus dem Code erstellen". Gespeichert wird dort erst im
        # Branch, nie in main (Wunsch des Nutzers vom 03.10.2026).
        if in_flow:
            self.setWindowTitle(f"Exe aus dem Code erstellen: {project.name}, Schritt 1: "
                                "Dateien neben der Exe")
        else:
            self.setWindowTitle(f"Exe-Einstellungen: {project.name}" if current
                                else f"Exe einrichten: {project.name}")
        self.current = current
        self.settings: exe.BuildSettings | None = None
        if current is None:
            current = exe.BuildSettings(guess_start_file(code_dir),
                                        project.name.replace(" ", "-"),
                                        beside=required_beside(code_dir))
        fields = [sf.Text("start_file", "Startdatei", current.start_file, required=True),
                  sf.Text("name", "Name der Exe", current.name, required=True,
                          pattern=r"[\w\-. ]+", pattern_hint="Bitte nur Buchstaben, Ziffern, "
                          "Leerzeichen, Punkt und Bindestrich."),
                  sf.Choice("mode", "Bauart", ONE_FILE if current.one_file else FOLDER,
                            options=(ONE_FILE, FOLDER)),
                  sf.YesNo("windowed", "Ohne Konsolenfenster (für Programme mit Fenster)",
                           current.windowed),
                  sf.Text("icon", "Symbol, freiwillig, eine .ico-Datei im Ordner Repository",
                          current.icon)]
        # Wunsch des Nutzers vom 20.10.2026: Python für den Bau wählen. Automatisch nimmt das
        # neueste, für das es alle Bibliotheken fertig gibt.
        self.pythons = [AUTO_PYTHON] + [f"Python {p.label}" for p in exe.find_pythons()]
        wanted = f"Python {current.python}" if current.python else AUTO_PYTHON
        if wanted not in self.pythons:
            self.pythons.append(wanted)
        fields.append(sf.Choice("python", "Python für den Bau", wanted,
                                options=tuple(self.pythons)))
        self.form = SettingsForm(fields)
        self.handmade = self.current is not None and \
            not exe.own_spec(code_dir / self.current.spec_name)
        self.required = [n for n in required_beside(code_dir, self.current) if not exe.is_doc(n)]
        self.beside = QListWidget()
        beside_label = label_for(self.beside, "&Ordner und Dateien neben der Exe:")
        names = list(self.required)
        names += [n for n in beside_candidates(code_dir) if n not in names]
        names += [n for n in current.beside if n not in names and not exe.is_doc(n)]
        for name in names:
            needed = name in self.required
            self._add_beside(name, needed or name in current.beside, needed,
                             not (code_dir / name).exists())
        for name in exe.doc_files(code_dir):
            item = QListWidgetItem(name + ALWAYS)
            item.setData(BESIDE_ROLE, name)
            self.beside.addItem(item)
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
        self.code_dir = code_dir
        layout = QVBoxLayout(self)
        if in_flow:
            hint = QLabel("Wählen Sie in diesem Schritt, welche Dateien und Ordner neben der Exe "
                          "liegen sollen. Was der Code unbedingt braucht, ist angehakt. README "
                          "und Lizenz kommen immer mit.")
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
                       "im Ordner Repository nicht.")
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
                                          keep.self_test, keep.test_seconds, beside,
                                          "" if values["python"] == AUTO_PYTHON
                                          else values["python"].removeprefix("Python "))
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
        """Die angehakten Einträge. README und Lizenz zählen nicht, sie kommen immer mit."""
        return [self.beside.item(r).data(BESIDE_ROLE) for r in range(self.beside.count())
                if self.beside.item(r).flags() & Qt.ItemFlag.ItemIsUserCheckable
                and self.beside.item(r).checkState() == Qt.CheckState.Checked]

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

    # Besteht die Exe den Test nicht, bleibt sie zur Auswahl (WizardBuildDialog)
    keep_failed = False

    def __init__(self, services, project: Project, settings: exe.BuildSettings,
                 parent: QWidget | None = None, branch_dir: Path | None = None,
                 branch_name: str = "") -> None:
        super().__init__(parent)
        self.services = services
        self.project = project
        self.branch_dir = branch_dir                 # Exe aus einem Branch-Ordner (10f)
        self.result: exe.BuildResult | None = None
        self.failed_build = False
        shown = branch_name or (branch_dir.name if branch_dir else "")
        self.setWindowTitle(f"Exe erstellen: {project.name}" + (f", Branch {shown}"
                                                                 if shown else ""))
        self.output = QListWidget()
        self.output.setWordWrap(True)
        make_copyable(self.output)
        self.stop_button = QPushButton("&Abbrechen")
        self.stop_button.clicked.connect(self.stop)
        self.close_button = QPushButton("&Schließen")
        self.close_button.clicked.connect(self.reject)
        self.error_text = ""
        for button in (self.stop_button, self.close_button):
            button.setAutoDefault(False)
        self.layout_ = QVBoxLayout(self)
        self.layout_.addWidget(label_for(self.output, "&Ausgabe:"))
        self.layout_.addWidget(self.output, 1)
        self.buttons = button_row(None, self.stop_button, self.close_button)
        self.layout_.addLayout(self.buttons)
        self.resize(820, 560)
        self.initial_focus_widget = self.output

        extra = {"keep_failed": True} if self.keep_failed else {}

        def work(task: Task):
            return exe.build(project, settings, task.status.emit, task.status.emit,
                             task.cancel_event, branch_dir, branch_name, **extra)

        self.task: Task | None = Task(work, self)
        self.task.status.connect(self.add_line)
        self.task.result.connect(self.finished_ok)
        self.task.error.connect(self.failed)
        self.task.cancelled.connect(self.cancelled)
        self.task.finished.connect(self._done)
        # Wunsch des Nutzers vom 20.10.2026: beim Bau derselbe Warteton wie beim Hochladen
        from cockpit.ui.sounds import TransferSound
        self.sound = TransferSound(services is not None and
                                   services.settings.load().transfer_sounds, self)
        self.add_line("Der Bau läuft. Beim ersten Mal dauert er einige Minuten.")
        self.sound.start()
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
        self._sound(not result.untested)              # nicht bestanden: Fehlerton
        if result.untested:
            result = self.ask_untested(result)
            if result is None:
                return
        self.result = result
        if result.branch:
            text = (f"Exe aus dem Branch erstellt und getestet: Ordner "
                    f"{result.exe.parent.parent.name}\\{result.exe.parent.name}.")
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
        for line in result.report:
            self.output.addItem(line)
        text = ("Das Cockpit kann die neue Exe nicht selbst prüfen, weil Windows den Start "
                "blockiert. Soll sie trotzdem übernommen werden? Die bisherige kommt in die "
                "Sicherheitskopien. Bitte starten Sie die neue Exe danach selbst und prüfen Sie "
                "sie. Beim nächsten Bau versucht das Cockpit den Test wieder.")
        if not confirm(self, "Exe nicht geprüft", text, yes="Übernehmen", no="Verwerfen"):
            exe.discard(result)
            self.failed_build = True
            self.ended("Die neue Exe wurde verworfen. Die bisherige bleibt.")
            return None
        try:
            return exe.install_untested(self.project, result)
        except CockpitError as exc:
            self.failed_build = True
            self.ended(f"Fehler: {exc.message}", urgent=True)
            return None

    def failed(self, message: str, details: str) -> None:
        self._sound(False)
        self.failed_build = True
        if details:
            self.output.addItem(details)
        self.ended(f"Fehler: {message}", urgent=True)
        if message == exe.LONG_PATHS:
            offer_long_paths(self)
        # Für die KI: Meldung, Details und das Ende der Ausgabe, dort steht meist der Grund
        output = [self.output.item(r).text() for r in range(self.output.count())]
        self.error_text = "\n".join([message, details] + output[-60:])

    def _sound(self, ok: bool | None) -> None:
        """Warteton beenden: mit Pling (ok), Fehlerton (False) oder still (None)."""
        sound = getattr(self, "sound", None)
        if sound is None:
            return
        if ok is None:
            sound.stop()
        else:
            sound.finish(ok)

    def cancelled(self) -> None:
        self._sound(None)
        self.failed_build = True
        self.ended("Abgebrochen. Die bisherige Exe bleibt.")

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
        self.after_build()

    def after_build(self) -> None:
        """Nach dem Ende des Baus, für Unterklassen (exe_wizard.py)."""

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
        self._sound(None)
        if self.task is not None:
            self.task.cancel()
            self.task.wait(10000)
        super().done(code)


class PublishDialog(FocusDialog):
    """Version und Versionshinweise für "Exe veröffentlichen"."""

    def __init__(self, project: Project, suggestion: str, tags: list[str], asset: str,
                 parent: QWidget | None = None, source=None,
                 title: str = "Exe veröffentlichen") -> None:
        """title: "Release anlegen" bei einem Release nur mit Quellcode (21.10.2026)."""
        super().__init__(parent)
        self.tags = tags
        self.version = self.notes = ""
        self.setWindowTitle(f"{title}: {project.name}, {asset}")
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
