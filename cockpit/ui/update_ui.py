"""Updates der Exe des Cockpits: Prüfung bei jedem Start, Rückfrage, Austausch.

Wunsch des Nutzers vom 03.10.2026: Die Suche läuft einmal bei jedem Start des Programms, nicht mehr
nur einmal am Tag.

Die Prüfung läuft still im Hintergrund. Nur wenn es eine neue Version gibt, kommt eine Rückfrage.
Fehler der automatischen Prüfung landen nur im Log. Hilfe, Nach Updates suchen prüft sofort und
meldet auch „aktuell“ und Fehler.
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from cockpit.core import exe, update
from cockpit.core.errors import CockpitError
from cockpit.ui.announcer import announce
from cockpit.ui.common import confirm, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

log = logging.getLogger(__name__)

FIRST_CHECK_MS = 10_000                  # nach dem Start, damit das Fenster erst in Ruhe aufbaut
TIMER_MS = 60 * 60 * 1000                # früher: stündlich nachsehen (bis 03.10.2026)
RETRY_MS = 60_000                        # Rückfrage verschieben, solange ein Dialog offen ist
TITLE = "Update"

UPDATE, NOTES, SKIP, LATER = "update", "notes", "skip", "later"


class Updater(QObject):
    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self.window = window
        self.services = window.services
        self.task: Task | None = None
        self.waiting: update.Update | None = None     # heruntergeladen, Austausch beim Beenden
        self.exe_path = update.own_exe()
        self.timer = QTimer(self)
        self.timer.setInterval(TIMER_MS)
        self.timer.timeout.connect(self.auto_check)

    def start(self) -> None:
        """Nur in der Exe und nicht mit Testdaten."""
        if self.exe_path is None or self.window.testdata:
            return
        QTimer.singleShot(FIRST_CHECK_MS, self.check_at_start)

    def check_at_start(self) -> None:
        if self.waiting is None and self.services.settings.load().update_check:
            self.run(manual=False)

    # -- Prüfen -----------------------------------------------------------------------------
    def auto_check(self) -> None:
        if self.waiting is not None or not self.services.settings.load().update_check:
            return
        last = self.services.database.get_value(update.LAST_CHECK_KEY, 0)
        if isinstance(last, (int, float)) and time.time() - last < update.CHECK_EVERY:
            return
        self.run(manual=False)

    def check_now(self) -> None:
        """Hilfe, Nach Updates suchen."""
        if self.exe_path is None:
            show_info(self.window, TITLE, "Updates gibt es nur für die Exe. Sie haben CodeCockpit "
                      "aus dem Code gestartet. Neuerungen holen Sie dort mit Git.")
            return
        if self.waiting is not None:
            self.offer_restart(self.waiting)
            return
        announce("Suche nach Updates.")
        self.run(manual=True)

    def run(self, manual: bool) -> None:
        if self.task is not None:
            return
        self.services.database.set_value(update.LAST_CHECK_KEY, time.time())
        skipped = "" if manual else self.services.database.get_value(update.SKIPPED_KEY, "")
        exe_path = self.exe_path
        self._start_task(lambda task: update.check(exe_path, skipped or ""),
                         lambda found: self.found(found, manual),
                         "Nach Updates suchen" if manual else None)

    def _start_task(self, work, done, failed_title: str | None) -> None:
        task = Task(work, self)
        self.task = task

        def finished() -> None:
            self.task = None

        def failed(message: str, details: str) -> None:
            log.warning("Update: %s %s", message, details)
            if failed_title is not None:
                show_error(self.window, failed_title, message, details)

        task.result.connect(done)
        task.error.connect(failed)
        task.finished.connect(finished)
        task.start()

    def found(self, found: update.Update | None, manual: bool) -> None:
        if found is None:
            if manual:
                show_info(self.window, TITLE, "CodeCockpit ist aktuell.")
            return
        if not manual and QApplication.activeModalWidget() is not None:
            QTimer.singleShot(RETRY_MS, lambda: self.found(found, manual))
            return
        self.ask(found)

    # -- Rückfrage --------------------------------------------------------------------------
    def ask(self, found: update.Update) -> None:
        while True:
            answer = ask_update(self.window, found)
            if answer == NOTES:
                from cockpit.ui.text_dialog import TextDialog
                TextDialog(f"Versionshinweise {found.version}", found.notes.splitlines(),
                           "Versionshinweise", self.window).exec()
                continue
            break
        if answer == SKIP:
            self.services.database.set_value(update.SKIPPED_KEY, found.tag)
            announce(f"Version {found.version} wird übersprungen.")
        elif answer == UPDATE:
            self.download(found)

    def download(self, found: update.Update) -> None:
        exe_path = self.exe_path
        announce("Update wird heruntergeladen.")
        self._start_task(lambda task: update.download(found, exe_path, task.cancel_event),
                         lambda _path: self.downloaded(found), "Update herunterladen")

    def downloaded(self, found: update.Update) -> None:
        self.waiting = found
        self.offer_restart(found)

    def offer_restart(self, found: update.Update) -> None:
        if not confirm(self.window, TITLE, f"Version {found.version} ist heruntergeladen und "
                       "geprüft. Zum Übernehmen startet CodeCockpit neu. Jetzt neu starten?",
                       yes="Neu starten", no="Später"):
            announce("Das Update wird beim Beenden übernommen.")
            return
        if self._swap(start=True):
            self.window.close()

    # -- Austausch --------------------------------------------------------------------------
    def _swap(self, start: bool) -> bool:
        found, exe_path = self.waiting, self.exe_path
        if found is None or exe_path is None or not update.is_waiting(exe_path):
            return False
        try:
            script = update.swap(exe_path, found.version, start)
        except (CockpitError, OSError) as exc:
            log.warning("Update-Austausch: %s", exc)
            if start:
                show_error(self.window, TITLE, getattr(exc, "message", str(exc)))
            return False
        self._remember(found)
        self.waiting = None
        exe.launch_restart(script)
        return True

    def _remember(self, found: update.Update) -> None:
        """Ist die laufende Exe die des Cockpit-Projekts, steht sie danach als Release da."""
        folder = self.exe_path.parent.resolve()
        for project in self.services.projects.all():
            try:
                if project.exe_dir is not None and exe.is_cockpit(project) and \
                        project.exe_dir.resolve() == folder:
                    exe.write_record(project.code_dir, exe.ExeRecord(
                        "release", exe.now(), "", found.version))
            except OSError as exc:
                log.warning("Exe-Vermerk nach dem Update: %s", exc)

    def shutdown(self) -> None:
        """Beim Beenden: laufende Prüfung abbrechen, wartendes Update übernehmen."""
        self.timer.stop()
        if self.task is not None:
            self.task.cancel()
            self.task.wait(5000)
        if self.waiting is not None:
            self._swap(start=False)


def ask_update(parent, found: update.Update) -> str:
    """Rückfrage mit Aktualisieren, Versionshinweise, Überspringen und Später (Vorgabe)."""
    box = QMessageBox(QMessageBox.Icon.Question, "Update verfügbar",
                      f"Version {found.version} von CodeCockpit ist verfügbar ({found.size_text}). "
                      "Einstellungen, Konten und Projekte bleiben erhalten. Die bisherige Exe "
                      "kommt in die Sicherheitskopien. Jetzt aktualisieren?",
                      QMessageBox.StandardButton.NoButton, parent)
    buttons = {box.addButton("&Aktualisieren", QMessageBox.ButtonRole.AcceptRole): UPDATE}
    if found.notes.strip():
        buttons[box.addButton("&Versionshinweise", QMessageBox.ButtonRole.ActionRole)] = NOTES
    buttons[box.addButton("Diese Version ü&berspringen", QMessageBox.ButtonRole.DestructiveRole)] \
        = SKIP
    later = box.addButton("&Später", QMessageBox.ButtonRole.RejectRole)
    buttons[later] = LATER
    box.setDefaultButton(later)
    box.setEscapeButton(later)
    box.exec()
    return buttons.get(box.clickedButton(), LATER)
