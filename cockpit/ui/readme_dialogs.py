"""Dialoge für die README: Text, Schreiben, Ändern, Übersetzen, Sprachen.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget)
from pathlib import Path

from cockpit.core.projects import Project
from cockpit.features.readme import content, document as doc, plan
from cockpit.ui.announcer import announce
from cockpit.ui.common import (
    FocusDialog, PlainEdit, click_focused_button, confirm, label_for, name_widget)
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import button_row
from cockpit.ui.tasks import Task


TAKE, SKIP = "take", "skip"


SENT = "Auszüge aus Ihrem Code, Ihre Infos und die README"


# Wunsch des Nutzers (14.10.2026): Die Felder sollen klar sagen, dass sie Hinweise an die KI sind
WRITE_NOTES = "Hinweise an die KI: Was soll in der README &stehen?"


WRITE_WISHES = "Hinweise an die &KI: Was soll sich am Text ändern?"


EDIT_WISHES = "Hinweise an die KI: W&as soll sich an der README ändern?"


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
                         WRITE_WISHES, "Von KI &verfassen lassen",
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
        notes_label = label_for(self.notes, WRITE_NOTES)
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
                         EDIT_WISHES,
                         "Von KI &überarbeiten lassen", "Die README ist &fertig so", parent)
        self.original = (project.code_dir / plan.MAIN_FILE).read_text(encoding="utf-8")
        self.text.setPlainText(self.original)
        self.add_text_fields()
        self.initial_focus_widget = self.text

    def ai_input(self) -> dict | None:
        values = super().ai_input()
        if not values["wishes"]:
            announce("Bitte schreiben Sie zuerst Hinweise an die KI.")
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
