"""README-Pflege in der Oberfläche (Konzept 10.2, Phase 9).

Aktion auf der Projektzeile: "README …" mit Auswahl. Wunsch des Nutzers vom 03.10.2026:
- Ohne README: "README-Einstellungen …", "README aus Ordner hochladen …" (eine fertige Datei
  übernehmen) und "README mit KI schreiben …".
- Mit README: "README-Einstellungen …" und "README bearbeiten …".
Beim Schreiben und Bearbeiten steht die ganze README in einem Textfeld. Darunter kommen Wünsche an
die KI, ein Knopf schickt sie ab, "fertig so" speichert. Danach übersetzt die KI in die weiteren
Sprachen, jede Übersetzung kommt einzeln zum Lesen.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (QComboBox, QFileDialog, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout, QWidget)

from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.features.readme import content
from cockpit.features.readme import document as doc
from cockpit.features.readme import plan
from cockpit.ui.announcer import announce
from cockpit.ui.common import (FocusDialog, PlainEdit, click_focused_button, confirm, label_for,
                               name_widget)
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import button_row
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

TAKE, SKIP = "take", "skip"
SETTINGS = "README-Einstellungen …"
IMPORT = "README aus Ordner hochladen …"
WRITE = "README mit KI schreiben …"
EDIT = "README bearbeiten …"
SENT = "Auszüge aus Ihrem Code, Ihre Infos und die README"


class ReadmeTextDialog(FocusDialog):
    """Die README als Text, darunter Wünsche an die KI. Der KI-Knopf schickt Text und Wünsche ab,
    die Antwort ersetzt den Text. "fertig so" schließt mit OK, gespeichert wird danach."""

    def __init__(self, services, project: Project, title: str, wishes_label: str,
                 ai_label: str, done_label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.project = project
        self.ai = None
        self.task: Task | None = None
        self.original = ""
        self.setWindowTitle(f"{title}: {project.name}")
        self.text = PlainEdit()
        self.text_label = label_for(self.text, "README-&Text:")
        self.wishes = PlainEdit()
        self.wishes_label = label_for(self.wishes, wishes_label)
        self.ai_button = QPushButton(ai_label)
        self.ai_button.clicked.connect(self.ask_ai)
        self.done_button = QPushButton(done_label)
        self.done_button.clicked.connect(self.finish)
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        for button in (self.ai_button, self.done_button, self.cancel_button):
            button.setAutoDefault(False)
        self.layout_ = QVBoxLayout(self)
        self.resize(820, 620)

    def add_text_fields(self) -> None:
        for widget in (self.text_label, self.text):
            self.layout_.addWidget(widget, 1 if widget is self.text else 0)
        for widget in (self.wishes_label, self.wishes):
            self.layout_.addWidget(widget)
        self.wishes.setMaximumHeight(120)
        self.layout_.addLayout(button_row(self.ai_button, self.done_button, None,
                                          self.cancel_button))

    @property
    def readme_text(self) -> str:
        return self.text.toPlainText().strip()

    def changed(self) -> bool:
        return self.readme_text != self.original.strip()

    # -- KI ---------------------------------------------------------------------------------
    def ai_input(self) -> dict | None:
        """Was an compose geht. None: nichts senden (die Ansage macht die Unterklasse)."""
        return {"current": self.readme_text, "wishes": self.wishes.toPlainText().strip()}

    def ask_ai(self) -> None:
        if self.task is not None:
            announce("Die KI schreibt noch.")
            return
        values = self.ai_input()
        if values is None:
            return
        if self.ai is None:
            from cockpit.ui import ai_ui
            tool = self.services.features.setting(plan.FEATURE_ID, "tool") or None
            ai = ai_ui.prepare(self.services, self, plan.FEATURE_ID, SENT, tool)
            if isinstance(ai, str):
                if ai != ai_ui.DECLINED:
                    show_error(self, self.windowTitle(), ai)
                return
            self.ai = ai
        services, project, ai = self.services, self.project, self.ai
        files = values.pop("files", [])

        def work(task: Task):
            info, skipped = plan.info_text(files, ai.max_chars // 4)
            text = plan.compose(services, project, ai, info=info, cancel=task.cancel_event,
                                **values)
            return text, skipped

        task = Task(work, self)
        self.task = task
        task.result.connect(self.show_text)
        task.error.connect(lambda message, details: show_error(self, self.windowTitle(), message,
                                                               details))
        task.finished.connect(self._finished)
        announce("Die KI überarbeitet die README." if values.get("current")
                 else "Die KI schreibt die README.")
        task.start()

    def show_text(self, outcome) -> None:
        text, skipped = outcome
        self.text.setPlainText(text)
        self.wishes.clear()
        for widget in (self.text_label, self.text, self.wishes_label, self.wishes):
            widget.setVisible(True)
        self.text.moveCursor(QTextCursor.MoveOperation.Start)
        self.text.setFocus()
        message = "Die README von der KI ist da."
        if skipped:
            message += f" Nicht an die KI gesendet: {', '.join(skipped)}."
        announce(message)

    def _finished(self) -> None:
        task, self.task = self.task, None
        if task is not None:
            task.wait()
            task.deleteLater()

    # -- Schließen --------------------------------------------------------------------------
    def finish(self) -> None:
        if self.task is not None:
            announce("Die KI schreibt noch.")
            return
        if not self.readme_text:
            announce("Es gibt noch keinen Text für die README.")
            return
        self.accept()

    def reject(self) -> None:
        if self.changed() and not confirm(self, self.windowTitle(), "Der Text der README ist "
                                          "nicht gespeichert. Verwerfen?", yes="Verwerfen",
                                          no="Zurück"):
            return
        super().reject()

    def done(self, code: int) -> None:
        if self.task is not None:
            self.task.cancel()
            self.task.wait(10000)
        super().done(code)

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)


class WriteDialog(ReadmeTextDialog):
    """README mit KI schreiben: Dateien mit Infos und Infos als Text. Textfeld und Vorschläge
    erscheinen, sobald die KI den ersten Text geliefert hat."""

    def __init__(self, services, project: Project, parent: QWidget | None = None) -> None:
        super().__init__(services, project, "README mit KI schreiben",
                         "Verbesserungsvorschläge für die &KI:", "Von KI &verfassen lassen",
                         "README ist &fertig so", parent)
        self.files = QListWidget()
        files_label = label_for(self.files, "&Dateien mit Infos zum Programm:")
        self.files.setMaximumHeight(110)
        add = QPushButton("Datei &hinzufügen …")
        add.clicked.connect(lambda: self.add_files())
        remove = QPushButton("Datei &entfernen")
        remove.clicked.connect(self.remove_file)
        for button in (add, remove):
            button.setAutoDefault(False)
        self.notes = PlainEdit()
        notes_label = label_for(self.notes, "&Infos für die README:")
        self.notes.setMaximumHeight(120)
        for widget in (files_label, self.files):
            self.layout_.addWidget(widget)
        self.layout_.addLayout(button_row(add, remove, None))
        for widget in (notes_label, self.notes):
            self.layout_.addWidget(widget)
        self.add_text_fields()
        for widget in (self.text_label, self.text, self.wishes_label, self.wishes):
            widget.setVisible(False)
        self.initial_focus_widget = self.files

    def paths(self) -> list[Path]:
        return [Path(self.files.item(r).data(Qt.ItemDataRole.UserRole))
                for r in range(self.files.count())]

    def add_files(self, chosen: list[str] | None = None) -> None:
        if not chosen:
            chosen, _ = QFileDialog.getOpenFileNames(self, "Dateien mit Infos wählen",
                                                     str(self.project.project_dir))
        known = {str(p) for p in self.paths()}
        added = 0
        for name in chosen or []:
            path = Path(name)
            if str(path) in known:
                continue
            known.add(str(path))
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.files.addItem(item)
            added += 1
        if added:
            self.files.setCurrentRow(self.files.count() - 1)
            announce("Datei hinzugefügt." if added == 1 else f"{added} Dateien hinzugefügt.")

    def remove_file(self) -> None:
        row = self.files.currentRow()
        if row < 0:
            announce("Keine Datei ausgewählt.")
            return
        name = self.files.takeItem(row).text()
        announce(f"{name} entfernt.")

    def ai_input(self) -> dict | None:
        values = {"notes": self.notes.toPlainText().strip(), "files": self.paths()}
        wishes = self.wishes.toPlainText().strip()
        if self.readme_text and wishes:            # Vorschläge: den Text überarbeiten
            values.update(current=self.readme_text, wishes=wishes)
        return values


class EditDialog(ReadmeTextDialog):
    """README bearbeiten: die README als Text, Anweisungen an die KI zur Überarbeitung."""

    def __init__(self, services, project: Project, parent: QWidget | None = None) -> None:
        super().__init__(services, project, "README bearbeiten",
                         "&Anweisungen an die KI zur Überarbeitung:",
                         "Von KI &überarbeiten lassen", "Die README ist &fertig so", parent)
        self.original = (project.code_dir / plan.MAIN_FILE).read_text(encoding="utf-8")
        self.text.setPlainText(self.original)
        self.add_text_fields()
        self.initial_focus_widget = self.text

    def ai_input(self) -> dict | None:
        values = super().ai_input()
        if not values["wishes"]:
            announce("Bitte schreiben Sie zuerst Anweisungen an die KI.")
            return None
        if not values["current"]:
            announce("Die README ist leer.")
            return None
        return values


class TranslationDialog(FocusDialog):
    """Eine Übersetzung zum Lesen und Anpassen. Escape überspringt (die sichere Wahl)."""

    def __init__(self, file: str, code: str, text: str, number: int, total: int,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.choice = SKIP
        language = content.LANGUAGE_NAMES.get(code, code)
        self.setWindowTitle(f"README übersetzt, {language}: {number} von {total}")
        self.edit = PlainEdit()
        self.edit.setPlainText(text)
        label = label_for(self.edit, f"&{file}, {language}:")
        take = QPushButton("Ü&bernehmen")
        take.clicked.connect(lambda: self.finish(TAKE))
        skip = QPushButton("Übe&rspringen")
        skip.clicked.connect(lambda: self.finish(SKIP))
        for button in (take, skip):
            button.setAutoDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.edit, 1)
        layout.addLayout(button_row(take, None, skip))
        self.resize(820, 560)
        self.initial_focus_widget = self.edit

    @property
    def text(self) -> str:
        return self.edit.toPlainText().strip()

    def finish(self, choice: str) -> None:
        self.choice = choice
        self.accept()

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)


def review(translations: list[tuple[str, str, str]], parent: QWidget | None) -> dict[str, str]:
    """Jede Übersetzung zeigen. Gibt die übernommenen als {Datei: Text} zurück."""
    taken: dict[str, str] = {}
    for number, (file, code, text) in enumerate(translations, start=1):
        dialog = TranslationDialog(file, code, text, number, len(translations), parent)
        dialog.exec()
        if dialog.choice == TAKE and dialog.text:
            taken[file] = dialog.text
    return taken


class LanguagesDialog(FocusDialog):
    """Sprachen eines Projekts: Hauptsprache und weitere als Kontrollkästchen (Frage 8)."""

    def __init__(self, services, project: Project, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"README-Einstellungen: {project.name}")
        main_code, codes = plan.languages(services, project.code_dir)
        names = list(doc.LANGUAGES)
        self.main = QComboBox()
        self.main.addItems(names)
        main_name = next(n for n, (c, _x) in doc.LANGUAGES.items() if c == main_code)
        self.main.setCurrentText(main_name)
        main_label = label_for(self.main, "&Hauptsprache, steht in README.md:")
        self.others = QListWidget()
        name_widget(self.others, "Weitere Sprachen")
        others_label = label_for(self.others, "&Weitere Sprachen:")
        for name in names:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if doc.LANGUAGES[name][0] in codes[1:]
                               else Qt.CheckState.Unchecked)
            self.others.addItem(item)
        self.others.setCurrentRow(0)
        save = QPushButton("&Speichern")
        save.clicked.connect(self.accept)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        for widget in (main_label, self.main, others_label, self.others):
            layout.addWidget(widget)
        layout.addLayout(button_row(None, save, cancel))
        self.resize(480, 360)
        self.initial_focus_widget = self.main

    def values(self) -> dict:
        main = self.main.currentText()
        others = [self.others.item(r).text() for r in range(self.others.count())
                  if self.others.item(r).checkState() == Qt.CheckState.Checked
                  and self.others.item(r).text() != main]
        return {"main_language": main, "languages": others}

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)


class ReadmeActions:
    def __init__(self, controller: "ProjectController") -> None:
        self.controller = controller
        self.window = controller.window
        self.services = controller.services

    def _active(self, context: ActionContext) -> bool:
        project = context.project
        if project is None or not project.folder_found or plan.FEATURE_ID not in \
                self.services.registry:
            return False
        try:
            return self.services.features.active(plan.FEATURE_ID, project)
        except CockpitError:
            return False

    @staticmethod
    def _has_readme(context: ActionContext) -> bool:
        return (context.project.code_dir / plan.MAIN_FILE).is_file()

    def actions(self) -> list[Action]:
        # Auf der Projektzeile (Wunsch des Nutzers zu Phase 9): die README gehört zum Projekt
        return [
            # Ein Eintrag mit Auswahl (Wunsch des Nutzers, 30.09.2026)
            Action("readme", "README …", Target.PROJECT, self.choose,
                   visible=self._active, order=40),
        ]

    def choose(self, context: ActionContext) -> None:
        """Reihenfolge wie im Wunsch des Nutzers vom 03.10.2026."""
        from cockpit.ui.common import choose_from_list
        if self._has_readme(context):
            options = [(SETTINGS, self.languages), (EDIT, self.edit)]
        else:
            options = [(SETTINGS, self.languages), (IMPORT, self.import_file),
                       (WRITE, self.write)]
        chosen = choose_from_list(self.window, "README", "README", [o[0] for o in options])
        if chosen is not None:
            options[chosen][1](context)

    # -- Einstellungen ----------------------------------------------------------------------
    def languages(self, context: ActionContext) -> None:
        dialog = LanguagesDialog(self.services, context.project, self.window)
        if not dialog.exec():
            return
        try:
            doc.save(context.project.code_dir, dialog.values())
        except OSError as exc:
            show_error(self.window, "README-Sprachen", "Die Sprachen ließen sich nicht in "
                       "cockpit.toml speichern.", str(exc))
            return
        announce("README-Sprachen gespeichert.")

    # -- Aus Ordner hochladen ---------------------------------------------------------------
    def import_file(self, context: ActionContext) -> None:
        project = context.project
        chosen, _ = QFileDialog.getOpenFileName(
            self.window, "README wählen", str(project.project_dir),
            "Markdown und Text (*.md *.markdown *.txt);;Alle Dateien (*)")
        if not chosen:
            return
        source = Path(chosen)
        if not confirm(self.window, "README aus Ordner hochladen",
                       f"{source.name} wird als README.md in den Ordner Code kopiert. "
                       "Übernehmen?", yes="Übernehmen", no="Abbrechen"):
            return
        try:
            backup = plan.import_file(self.services, project, source)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "README aus Ordner hochladen",
                       getattr(exc, "message", "Die README ließ sich nicht übernehmen."),
                       str(exc))
            return
        self.window.refresh_status([project.id])
        announce("README.md übernommen." + (" Die alte steht in den Sicherheitskopien."
                                            if backup else ""))

    # -- Mit KI schreiben und bearbeiten ----------------------------------------------------
    def write(self, context: ActionContext) -> None:
        dialog = WriteDialog(self.services, context.project, self.window)
        if dialog.exec():
            self._save(context.project, dialog.readme_text, dialog.ai)

    def edit(self, context: ActionContext) -> None:
        project = context.project
        try:
            dialog = EditDialog(self.services, project, self.window)
        except (OSError, UnicodeDecodeError) as exc:
            show_error(self.window, "README bearbeiten", "Die README ließ sich nicht lesen.",
                       str(exc))
            return
        if not dialog.exec():
            return
        if dialog.changed():
            self._save(project, dialog.readme_text, dialog.ai)
            return
        missing = plan.missing_translations(self.services, project)
        if missing:
            self._translate(project, dialog.readme_text, dialog.ai, missing)
        else:
            announce("Nichts geändert.")

    def _save(self, project: Project, text: str, ai) -> None:
        try:
            backup = plan.save_files(self.services, project, {plan.MAIN_FILE: text})
        except (CockpitError, OSError) as exc:
            show_error(self.window, "README", "Die README ließ sich nicht speichern.", str(exc))
            return
        self.window.refresh_status([project.id])
        announce("README.md gespeichert." + (" Die alte steht in den Sicherheitskopien."
                                             if backup else ""))
        _main, codes = plan.languages(self.services, project.code_dir)
        if len(codes) > 1:
            self._translate(project, text, ai, None)

    def _translate(self, project: Project, text: str, ai, only: list[str] | None) -> None:
        if ai is None:
            from cockpit.ui import ai_ui
            tool = self.services.features.setting(plan.FEATURE_ID, "tool") or None
            ai = ai_ui.prepare(self.services, self.window, plan.FEATURE_ID, "die README", tool)
            if isinstance(ai, str):
                if ai != ai_ui.DECLINED:
                    show_error(self.window, "README übersetzen", f"{ai} Die Übersetzungen "
                               "bleiben, wie sie sind.")
                return
        services = self.services

        def work(task: Task):
            return plan.translate(services, project, ai, text, only, task.cancel_event,
                                  task.status.emit)

        self.controller.run_task(
            f"readme:{project.id}", work,
            lambda translations: self._save_translations(project, translations),
            "README übersetzen", on_status=lambda message: announce(message, speak=False))
        announce("Die KI übersetzt die README.")

    def _save_translations(self, project: Project,
                           translations: list[tuple[str, str, str]]) -> None:
        taken = review(translations, self.window) if translations else {}
        if not taken:
            announce("Keine Übersetzung übernommen.")
            return
        try:
            plan.save_files(self.services, project, taken)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "README übersetzen", "Die Übersetzung ließ sich nicht "
                       "speichern.", str(exc))
            return
        self.window.refresh_status([project.id])
        announce(f"Übersetzung gespeichert: {', '.join(sorted(taken))}.")
