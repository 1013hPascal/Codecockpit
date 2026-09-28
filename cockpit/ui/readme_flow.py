"""README-Pflege in der Oberfläche (Konzept 10.2, Phase 9).

Aktionen auf Code (und auf Branch-Zeilen): "README erstellen …" oder "README aktualisieren …",
"README ansehen", "README-Sprachen …".

Wunsch des Nutzers zu Phase 9: Jeder neue Abschnitt kommt einzeln zum Lesen. Übernehmen (auch
angepasst), Überspringen oder alles Abbrechen. In der README steht danach keine Markierung.
Erst nach der Hauptsprache kommen die Übersetzungen, ebenfalls einzeln.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout, QWidget)

from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.features.readme import document as doc
from cockpit.features.readme import plan
from cockpit.features.readme.content import Proposal
from cockpit.ui.announcer import announce
from cockpit.ui.common import (FocusDialog, PlainEdit, click_focused_button, confirm, label_for,
                               name_widget)
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import button_row
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.project_actions import ProjectController

TAKE, SKIP, STOP = "take", "skip", "stop"


class SectionDialog(FocusDialog):
    """Ein Vorschlag: Überschrift, Text zum Lesen und Anpassen, Übernehmen oder Überspringen.
    Escape überspringt (die sichere Wahl)."""

    def __init__(self, proposal: Proposal, number: int, total: int,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.choice = SKIP
        language = next((n for n, (c, _native) in doc.LANGUAGES.items() if c == proposal.code),
                        proposal.code)
        self.setWindowTitle(f"README, {language}: {proposal.title}, {number} von {total}")
        self.edit = PlainEdit()
        self.edit.setPlainText(proposal.text)
        label = label_for(self.edit, f"&{proposal.title}, {proposal.reason}:")
        take = QPushButton("Ü&bernehmen")
        take.clicked.connect(lambda: self.finish(TAKE))
        skip = QPushButton("Übe&rspringen")
        skip.clicked.connect(lambda: self.finish(SKIP))
        stop = QPushButton("Alle &abbrechen")
        stop.clicked.connect(lambda: self.finish(STOP))
        for button in (take, skip, stop):
            button.setAutoDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.edit, 1)
        layout.addLayout(button_row(take, skip, None, stop))
        self.resize(760, 460)
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


def review(proposals: list[Proposal], parent: QWidget | None) -> list[Proposal] | None:
    """Jeden Vorschlag zeigen. Gibt die übernommenen zurück, None bei "Alle abbrechen"."""
    taken: list[Proposal] = []
    for number, proposal in enumerate(proposals, start=1):
        dialog = SectionDialog(proposal, number, len(proposals), parent)
        dialog.exec()
        if dialog.choice == STOP:
            return None
        if dialog.choice == TAKE and dialog.text:
            proposal.text = dialog.text
            taken.append(proposal)
    return taken


class LanguagesDialog(FocusDialog):
    """Sprachen eines Projekts: Hauptsprache und weitere als Kontrollkästchen (Frage 8)."""

    def __init__(self, services, project: Project, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"README-Sprachen: {project.name}")
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
        return (context.project.code_dir / "README.md").is_file()

    def actions(self) -> list[Action]:
        return [
            Action("readme_create", "README erstellen …", Target.CODE, self.start,
                   visible=lambda c: self._active(c) and not self._has_readme(c), order=50),
            Action("readme_update", "README aktualisieren …", Target.CODE, self.start,
                   visible=lambda c: self._active(c) and self._has_readme(c), order=50),
            Action("readme_show", "README ansehen", Target.CODE, self.show,
                   visible=lambda c: self._active(c) and self._has_readme(c), order=51),
            Action("readme_languages", "README-Sprachen …", Target.CODE, self.languages,
                   visible=self._active, order=52),
        ]

    # -- Ansehen und Sprachen ---------------------------------------------------------------
    def show(self, context: ActionContext) -> None:
        from cockpit.ui.text_dialog import TextDialog
        path = context.project.code_dir / "README.md"
        lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        TextDialog(f"README von {context.project.name}", lines, "README", self.window).exec()

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

    # -- Erstellen und aktualisieren --------------------------------------------------------
    def start(self, context: ActionContext) -> None:
        from cockpit.ui import ai_ui
        project = context.project
        tool = self.services.features.setting(plan.FEATURE_ID, "tool") or None
        ai = ai_ui.prepare(self.services, self.window, plan.FEATURE_ID,
                           "Auszüge aus Ihrem Code und die README", tool)
        if isinstance(ai, str):
            if ai == ai_ui.DECLINED or not confirm(
                    self.window, "README", f"{ai} Ohne KI schreibt das Cockpit nur die "
                    "Abschnitte, die es selbst weiß, zum Beispiel Download und Installation. "
                    "Weiter?", yes="Weiter", no="Abbrechen"):
                return
            ai = None
        services = self.services

        def work(task: Task):
            return plan.plan_main(services, project, ai, task.cancel_event, task.status.emit)

        announce("Die README wird vorbereitet.")
        self.controller.run_task(f"readme:{project.id}", work,
                                 lambda proposals: self.review_main(project, ai, proposals),
                                 "README", on_status=lambda text: announce(text, speak=False))

    def review_main(self, project: Project, ai, proposals: list[Proposal]) -> None:
        if not proposals:
            show_info_text = "Die README ist aktuell. Es gibt nichts Neues vorzuschlagen."
            announce(show_info_text)
            return
        taken = review(proposals, self.window)
        if not taken:
            announce("Nichts übernommen." if taken is not None else "Abgebrochen.")
            return
        if not self._write(project, taken):
            return
        _main, codes = plan.languages(self.services, project.code_dir)
        if len(codes) < 2 or ai is None:
            self._done(project, taken)
            return
        services = self.services

        def work(task: Task):
            return plan.plan_translations(services, project, ai, taken, task.cancel_event,
                                          task.status.emit)

        announce("Die Übersetzungen werden vorbereitet.")
        self.controller.run_task(
            f"readme:{project.id}", work,
            lambda translations: self.review_translations(project, taken, translations),
            "README übersetzen", on_status=lambda text: announce(text, speak=False))

    def review_translations(self, project: Project, taken: list[Proposal],
                            translations: list[Proposal]) -> None:
        more = review(translations, self.window) or [] if translations else []
        if more and self._write(project, more):
            taken = taken + more
        self._done(project, taken)

    def _write(self, project: Project, proposals: list[Proposal]) -> bool:
        try:
            plan.apply(self.services, project, proposals)
        except (CockpitError, OSError) as exc:
            show_error(self.window, "README", getattr(exc, "message", "Die README ließ sich "
                       "nicht schreiben."), str(exc))
            return False
        return True

    def _done(self, project: Project, taken: list[Proposal]) -> None:
        files = sorted({p.file for p in taken})
        self.window.refresh_status([project.id])
        announce(f"README geschrieben: {', '.join(files)}.")
