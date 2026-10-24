"""Exe aus dem Code erstellen, Schritt für Schritt (Wunsch des Nutzers vom 03.10.2026).

1. Dateien neben der Exe: Was der Code unbedingt braucht, ist angehakt. README und Lizenz kommen
   immer mit.
2. Mit oder ohne KI, nur wenn eine Text-KI eingerichtet ist. Gebaut wird in beiden Fällen im
   Branch Cockpit-exe-bauen, main bleibt unverändert.
3. Einrichtung: Das Cockpit legt den Branch an, ohne zu fragen, speichert dort die Einstellungen
   und prüft die Einrichtung. Mit KI liest die KI den Code und schlägt Änderungen vor.
4. Zusammenfassung, was passiert. "Mit KI chatten" klappt erst auf Wunsch die Frage an die KI
   und das Gespräch auf. Weiter heißt "Exe erstellen".
5. Der Bau mit Ausgabe.
6. Ergebnis im selben Fenster. Bei einem Fehler: "Problem mit KI lösen" (nur mit KI), "Neuer
   Versuch, Exe zu bauen", "Zurück", "Abbrechen". Ist die Exe gebaut, aber der Test nicht
   bestanden oder von Windows blockiert, zuerst "Trotzdem behalten", mit KI auch "Mit KI
   chatten". Bei Erfolg: "Erst testen …" (öffnet den Ordner
   der neuen Exe), "Jetzt in main überführen und Release veröffentlichen", "Jetzt in main
   überführen, später veröffentlichen".
Jeder Schritt hat "Zurück" und "Abbrechen". Abbrechen löscht den Branch wieder, wenn dieser
Durchgang ihn angelegt hat. Main bleibt dann, wie es war.

Fehler unterwegs, zum Beispiel beim Übernehmen der Änderungen der KI, zeigt ProblemDialog
(Wunsch des Nutzers vom 04.10.2026): die Ausgabe in einem Feld zum Lesen, der Text liegt schon in
der Zwischenablage. "Problem mit KI lösen" gibt den Fehler an die KI und wiederholt die
Einrichtung, "Mit KI chatten" klappt das Gespräch auf, dessen Hinweise dann mitgehen.
"""
from __future__ import annotations

import dataclasses
import logging
from pathlib import Path
from typing import TYPE_CHECKING


from cockpit.core import exe
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.features.exe_build import ai_fix, exe_branch, setup_check
from cockpit.ui.announcer import announce
from cockpit.ui.common import confirm
from cockpit.ui.error_dialog import show_error
from cockpit.ui.exe_flow import BuildSettingsDialog, beside_line
# Aufgeteilt am 22.10.2026: Teile stehen in exe_wizard_steps.py. Die Namen bleiben hier erreichbar.
from cockpit.ui.exe_wizard_steps import (  # noqa: F401
    BACK, CANCEL, CHAT_TEXT, FIX, FIX_TEXT, MERGE_ONLY, MERGE_ONLY_TEXT, MERGE_PUBLISH,
    MERGE_PUBLISH_TEXT, ModeDialog, NEXT, ProblemDialog, REPEAT, RETRY, RETRY_TEXT, SummaryDialog,
    TEST_LATER, TEST_LATER_TEXT, TITLE, WITHOUT_AI, WITH_AI, WizardBuildDialog, step_title)

if TYPE_CHECKING:
    from cockpit.ui.exe_flow import ExeActions

log = logging.getLogger(__name__)


class ExeWizard:
    """Führt durch die Schritte. Jeder Schritt gibt den Namen des nächsten zurück, None am Ende."""

    def __init__(self, actions: "ExeActions", project: Project) -> None:
        self.actions = actions
        self.window = actions.window
        self.services = actions.services
        self.project = project
        self.ai_available = not self.services.ai_problem()
        self.use_ai = self.ai_available
        self.ai = None
        self.settings: exe.BuildSettings | None = None
        self.had_branch = exe_branch.exists(project)
        self.folder: Path | None = exe_branch.current_folder(project) if self.had_branch else None
        self.proposal: ai_fix.Proposal | None = None
        self.lines: list[str] = []
        self.hints = ""
        self.error = ""

    def run(self) -> None:
        step = "files"
        while step:
            step = getattr(self, f"step_{step}")()

    def _number(self, name: str) -> int:
        order = ["files", "mode", "setup", "summary"] if self.ai_available \
            else ["files", "setup", "summary"]
        return order.index(name) + 1

    # -- Schritt 1 ----------------------------------------------------------------------------
    def step_files(self):
        source = self.folder or self.project.code_dir
        current = self.settings or exe.read_settings(source) or \
            exe.read_settings(self.project.code_dir)
        dialog = BuildSettingsDialog(self.project, self.window, current, in_flow=True,
                                     code_dir=self.project.code_dir)
        if not dialog.exec() or dialog.settings is None:
            return self.cancel("files")
        self.settings = dialog.settings
        return "mode" if self.ai_available else "setup"

    # -- Schritt 2 ----------------------------------------------------------------------------
    def step_mode(self):
        dialog = ModeDialog(self.project, self._number("mode"), self.use_ai, self.window)
        dialog.exec()
        if dialog.choice == BACK:
            return "files"
        if dialog.choice != NEXT:
            return self.cancel("mode")
        self.use_ai = dialog.with_ai
        if self.use_ai and self.ai is None:
            from cockpit.ui import ai_ui
            ai = ai_ui.prepare(self.services, self.window, "exe_fix",
                               "die Prüfung der Exe, Fehlermeldungen und Auszüge aus dem Code")
            if isinstance(ai, str):
                if ai != ai_ui.DECLINED:
                    show_error(self.window, TITLE, ai)
                return "mode"
            self.ai = ai
        return "setup"

    # -- Schritt 3 ----------------------------------------------------------------------------
    def step_setup(self):
        from cockpit.ui.exe_ai import WorkDialog
        project, settings = self.project, dataclasses.replace(self.settings)
        ai = self.ai if self.use_ai else None
        wish, error = ai_fix.with_hints("", self.hints), self.error

        def work(task):
            task.status.emit(f"Branch {exe_branch.BRANCH} wird vorbereitet.")
            folder = exe_branch.prepare(project)
            if exe.read_settings(folder) != settings:
                exe.change_settings(folder, project.name, settings)
                exe_branch.commit(folder, ["cockpit.toml", settings.spec_name],
                                  "Exe-Einstellungen")
            saved = exe.read_settings(folder) or settings
            # Fehlende Bibliotheken gleich im Branch eintragen, sonst fehlen sie in der Exe
            # (Rückmeldung des Nutzers vom 14.10.2026)
            first = []
            added = setup_check.complete_requirements(folder)
            if added:
                first.append(f"requirements.txt ergänzt: {', '.join(added)}. Der Code importiert "
                             "sie, ohne diese Einträge fehlten sie in der Exe.")
            # Python wählen und vorher prüfen, ob es alle Bibliotheken fertig gibt (20.10.2026).
            # Dann Einträge berichtigen, die sich so nicht installieren lassen (14.10.2026).
            notes: list[str] = []
            python = exe.choose_python(folder, saved.python, notes.append, task.cancel_event)
            for note in notes:
                task.status.emit(note)
            first = setup_check.repair_requirements(folder, python.version) + first
            if first:
                exe_branch.commit(folder, ["requirements.txt"], "requirements.txt ergänzt")
            told = [n for n in notes if not n.startswith("Es wird geprüft")]
            if not any(n.startswith("Python ") for n in told):
                told.insert(0, f"Gebaut wird mit Python {python.label}.")
            first.append(" ".join(told))
            if ai is None:
                return folder, None, first + setup_check.check_for(folder, saved,
                                                                   exe.current_exe(project))
            return folder, ai_fix.ask(ai, project.name, folder, saved, wish, task.cancel_event,
                                      progress=task.status.emit, error=error), first

        # Wunsch des Nutzers (04.10.2026): sagen, was an die KI ging
        handed = ("Fehler und Chat wurden an die KI übergeben" if self.hints
                  else "Fehler wurde an die KI übergeben")
        what = (f"Die KI versucht, das Problem zu lösen. {handed}" if error else
                "Die KI liest den Code" if ai is not None else "Die Einrichtung wird geprüft")
        progress = WorkDialog(project, work, ai is not None, self.window, what,
                              step_title(project, self._number("setup"), "Einrichtung"))
        progress.exec()
        if progress.result_value is not None:
            self.folder, self.proposal, self.lines = progress.result_value
            return "summary"
        previous = "mode" if self.ai_available else "files"
        if progress.failure is not None:
            return self.problem(*progress.failure, back_to=previous)
        if progress.back_requested:
            return previous
        return self.cancel("setup")

    # -- Schritt 4 ----------------------------------------------------------------------------
    def summary_lines(self) -> tuple[list[str], list[ai_fix.Change | None]]:
        lines: list[str] = []
        changes: list[ai_fix.Change | None] = []

        def add(text: str, change: ai_fix.Change | None = None) -> None:
            lines.append(text)
            changes.append(change)

        proposal = self.proposal
        if proposal is not None and self.error:
            # Wunsch des Nutzers (14.10.2026): erst sagen, was beim letzten Versuch das Problem
            # war, dann, wie die KI es jetzt löst
            add(f"Problem beim letzten Versuch: {proposal.problem or exe.first_error(self.error)}")
        if proposal is not None:
            solved = "So löst die KI es: " if self.error else ""
            button = "„Neuer Versuch, Exe zu bauen“" if self.error else "„Exe erstellen“"
            if proposal.empty:
                add(("Die KI findet keine Änderung, die das Problem löst." if solved else
                     "Die KI schlägt keine Änderung vor.") + (
                    f" {proposal.summary}" if proposal.summary else ""))
                for change in proposal.changes:
                    add(change.line())
            else:
                count = len(proposal.usable) + (1 if proposal.settings is not None else 0)
                add(solved + (f"{proposal.summary} " if proposal.summary and solved else "")
                    + f"Die KI schlägt {count} {'Änderung' if count == 1 else 'Änderungen'} "
                    f"vor. Sie kommen mit {button} in den Branch." + (
                        f" {proposal.summary}" if proposal.summary and not solved else ""))
                for line in proposal.settings_lines:
                    add(f"Einstellung: {line}")
                for change in proposal.changes:
                    add(change.line(), change)
                for note in proposal.notes:
                    add(note)
        for line in self.lines:
            add(line)
        settings = self.settings
        name = exe.branch_exe_name(settings.name if settings else self.project.name,
                                   exe_branch.BRANCH)
        add(f"Gebaut wird im Branch {exe_branch.BRANCH}, Ordner {self.folder}. Main bleibt "
            "unverändert.")
        add(beside_line(self.project, self.folder))
        add(f"Die neue Exe kommt in den Ordner {self.project.exe_dir.name}\\{name} und wird "
            "getestet. Die bisherige Exe "
            "bleibt, bis Sie die neue in main überführen.")
        return lines, changes

    def step_summary(self):
        lines, changes = self.summary_lines()
        # Nach "Problem mit KI lösen": Problem und Lösung zusammen ansagen
        announce(" ".join(lines[:2]) if self.error and self.proposal is not None else lines[0])
        with_chat = self.use_ai and self.ai is not None
        dialog = SummaryDialog(self.project, self._number("summary"), lines, changes,
                               self.services if with_chat else None,
                               RETRY_TEXT if self.error else "", self.window,
                               code_dir=self.folder, error=self.error,
                               start_file=self.settings.start_file if self.settings else "")
        dialog.exec()
        if dialog.choice == BACK:
            self.error = ""
            return "mode" if self.ai_available else "files"
        if dialog.choice == REPEAT:
            self.hints = dialog.hints
            return "setup"
        if dialog.choice != NEXT:
            return self.cancel("summary")
        failure = self.apply_proposal()
        if failure is not None:
            return self.problem(*failure, back_to="summary")
        return "build"

    def problem(self, message: str, details: str, back_to: str):
        """Fehler unterwegs: Fenster mit der Ausgabe. "Problem mit KI lösen" wiederholt die
        Einrichtung mit dem Fehler und den Hinweisen aus dem Gespräch."""
        with_ai = self.use_ai and self.ai is not None
        dialog = ProblemDialog(self.project, self._number("setup"), message, details,
                               self.services if with_ai else None, self.window,
                               code_dir=self.folder or self.project.code_dir,
                               start_file=self.settings.start_file if self.settings else "")
        dialog.exec()
        if dialog.choice in (FIX, NEXT):
            self.error = dialog.text
            self.hints = dialog.hints
            self.proposal = None
            return "setup"
        if dialog.choice == BACK:
            return back_to
        return self.cancel(back_to)

    def apply_proposal(self) -> tuple[str, str] | None:
        """Die Änderungen der KI im Branch übernehmen und committen. Die betroffenen Dateien
        kommen vorher in die Sicherheitskopien. Gibt bei einem Fehler (Meldung, Details) zurück."""
        proposal, self.proposal = self.proposal, None
        if proposal is None or proposal.empty:
            return None
        files = [c.file for c in proposal.usable] + ["cockpit.toml"]
        if proposal.settings is not None:
            files.append(proposal.settings.spec_name)
        try:
            ai_fix.apply(self.project.name, self.folder, proposal)
            exe_branch.commit(self.folder, files)
        except (CockpitError, OSError) as exc:
            self.proposal = proposal
            # Vorher stand unter "Details" nur noch einmal die Meldung (Rückmeldung vom 04.10.)
            return (getattr(exc, "message", "Die Änderungen ließen sich nicht übernehmen."),
                    getattr(exc, "details", "") or str(exc))
        self.settings = exe.read_settings(self.folder) or self.settings
        announce(f"Änderungen im Branch {exe_branch.BRANCH} übernommen.")
        return None

    # -- Schritte 5 und 6 ---------------------------------------------------------------------
    def step_build(self):
        project = self.project
        settings = exe.read_settings(self.folder) or self.settings
        try:
            seconds = int(self.services.features.setting("exe_build", "test_seconds"))
        except (KeyError, LookupError, TypeError, ValueError, CockpitError):
            seconds = settings.test_seconds
        settings = dataclasses.replace(settings, test_seconds=seconds)
        dialog = WizardBuildDialog(self.services, project, settings, self.folder,
                                   self.use_ai and self.ai is not None, self.window)
        dialog.exec()
        self.window.refresh_status([project.id])
        choice = dialog.choice
        if choice == TEST_LATER:
            self.actions.open_branch_exe(project)
            announce(f"Der Branch {exe_branch.BRANCH} bleibt. Wenn die Exe passt, wählen Sie bei "
                     "Exe „Exe-Bau abschließen …“.")
            return None
        if choice in (MERGE_PUBLISH, MERGE_ONLY):
            self.actions.merge_branch(project, publish=choice == MERGE_PUBLISH)
            return None
        if choice == FIX:
            self.error = dialog.error_text
            self.hints = getattr(dialog, "hints", "")  # aus "Mit KI chatten", sonst leer
            return "setup"
        if choice == RETRY:
            return "build"
        if choice == BACK:
            return "summary"
        return self.cancel("build")

    # -- Abbrechen ----------------------------------------------------------------------------
    def cancel(self, back_to: str):
        """Abbrechen. Hat dieser Durchgang den Branch angelegt, wird er nach Rückfrage gelöscht.
        Die sichere Antwort ist "Zurück"."""
        if self.had_branch or not exe_branch.exists(self.project):
            announce("Abgebrochen. Main ist unverändert." if not self.had_branch else
                     f"Abgebrochen. Der Branch {exe_branch.BRANCH} bleibt, wie er war.")
            return None
        if not confirm(self.window, TITLE, f"Den Exe-Bau abbrechen? Der Branch "
                       f"{exe_branch.BRANCH} und eine darin gebaute Exe werden gelöscht. Main "
                       "bleibt, wie es war.", yes="Abbrechen und löschen", no="Zurück"):
            return back_to if back_to != "build" else "summary"
        self.actions.discard_branch(self.project)
        return None
