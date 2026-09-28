"""Spracheingabe in der Oberfläche (Konzept 10.15, Teilschritt 8d).

Kein Knopf, nur Tasten (Wunsch des Nutzers, wie im Tagebuch): Strg+D startet und beendet die
Aufnahme, Strg+Umschalt+D bricht ab. Das geht in jedem Textfeld des Cockpits, auch in Dialogen,
weil die Tasten für das ganze Programm abgefangen werden.

Ablauf: "Aufnahme läuft." – Strg+D – "Wird umgewandelt." – "Text eingefügt." Der Text kommt in das
Feld, in dem die Aufnahme begann. Gibt es das nicht mehr, kommt er in die Zwischenablage.
Beim ersten Diktieren fragt das Cockpit, ob es das Whisper-Modell herunterladen darf.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QTextEdit, QWidget

from cockpit.ai import whisper
from cockpit.ai.recording import Recording
from cockpit.core import hardware
from cockpit.core.errors import CockpitError
from cockpit.features.dictation.manifest import FEATURE_ID
from cockpit.ui.announcer import announce
from cockpit.ui.common import confirm
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

log = logging.getLogger(__name__)

IDLE, RECORDING, CONVERTING, DOWNLOADING = "idle", "recording", "converting", "downloading"
CHECK_MS = 500


def text_field(widget: QWidget | None) -> QWidget | None:
    """Das Textfeld, in das diktiert werden kann, sonst None (auch bei schreibgeschützten)."""
    if isinstance(widget, (QLineEdit, QPlainTextEdit, QTextEdit)) and not widget.isReadOnly():
        return widget
    return None


def insert_text(widget: QWidget, text: str) -> None:
    """An der Schreibmarke einfügen. Einzeilige Felder bekommen keine Zeilenumbrüche (Frage 8).
    Steht davor Text ohne Leerzeichen am Ende, kommt eines dazwischen."""
    text = text.strip()
    if isinstance(widget, QLineEdit):
        text = " ".join(text.split())
        before = widget.text()[:widget.cursorPosition()]
        if before and not before[-1].isspace():
            text = " " + text
        widget.insert(text)
        return
    cursor = widget.textCursor()
    before = cursor.block().text()[:cursor.positionInBlock()]
    if before and not before[-1].isspace():
        text = " " + text
    cursor.insertText(text)
    widget.setTextCursor(cursor)


class Dictation(QObject):
    """Fängt Strg+D und Strg+Umschalt+D im ganzen Programm ab."""

    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self.window = window
        self.services = window.services
        self.state = IDLE
        self.recording: Recording | None = None
        self.target: QWidget | None = None
        self.discard = False
        self.task: Task | None = None
        self.max_minutes = 10
        # Nahtstellen für die Tests
        self.recording_factory: Callable[[int], Recording] = Recording
        self.transcribe: Callable = whisper.transcribe
        self.download: Callable[[str], object] = whisper.download
        self.timer = QTimer(self)
        self.timer.setInterval(CHECK_MS)
        self.timer.timeout.connect(self._check)
        QApplication.instance().installEventFilter(self)

    # -- Tasten -----------------------------------------------------------------------------
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.Type.KeyPress or event.key() != Qt.Key.Key_D:
            return False
        modifiers = event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            self.toggle()
            return True
        if modifiers == (Qt.KeyboardModifier.ControlModifier
                         | Qt.KeyboardModifier.ShiftModifier):
            self.cancel()
            return True
        return False

    # -- Zustand ----------------------------------------------------------------------------
    def available(self) -> str:
        """Leer, wenn diktiert werden kann, sonst ein Satz, warum nicht."""
        registry = self.services.registry
        if FEATURE_ID not in registry:
            return "Die Spracheingabe gibt es in dieser Fassung nicht."
        state = self.services.features.availability(FEATURE_ID)
        return "" if state.available else state.reason

    def model(self) -> str:
        database = self.services.database
        manual = database.get_value(hardware.MANUAL_KEY, None)
        ram = float(manual) if manual else hardware.ram_gb()
        return whisper.chosen_model(database, ram)

    def language(self) -> str | None:
        name = self.services.features.setting(FEATURE_ID, "language") or "Deutsch"
        return whisper.LANGUAGES.get(name, "de")

    # -- Starten und beenden ----------------------------------------------------------------
    def toggle(self) -> None:
        if self.state == RECORDING:
            self.stop()
            return
        if self.state == CONVERTING:
            announce("Die Umwandlung läuft noch.")
            return
        if self.state == DOWNLOADING:
            announce("Das Whisper-Modell wird noch heruntergeladen.")
            return
        field = text_field(QApplication.focusWidget())
        if field is None:
            announce("Diktieren geht nur in einem Textfeld.")
            return
        problem = self.available()
        if problem:
            announce(problem)
            return
        name = self.model()
        if not whisper.is_downloaded(name):
            self.offer_download(name, field)
            return
        self.start(field)

    def start(self, field: QWidget) -> None:
        try:
            self.max_minutes = int(self.services.features.setting(FEATURE_ID, "max_minutes")
                                   or 10)
        except (TypeError, ValueError):
            self.max_minutes = 10
        recording = self.recording_factory(self.max_minutes * 60)
        try:
            recording.start()
        except CockpitError as exc:
            announce(exc.message, urgent=True)
            return
        self.recording, self.target, self.discard = recording, field, False
        field.destroyed.connect(self._target_gone)
        self.state = RECORDING
        self.timer.start()
        announce("Aufnahme läuft.")

    def _target_gone(self, *_args) -> None:
        self.target = None

    def _check(self) -> None:
        if self.recording is not None and self.recording.full:
            self.stop(automatic=True)

    def stop(self, automatic: bool = False) -> None:
        self.timer.stop()
        recording, self.recording = self.recording, None
        if recording is None:
            return
        try:
            audio = recording.stop()
        except Exception as exc:                        # Treiber
            log.warning("Aufnahme beenden: %r", exc)
            self.state = IDLE
            announce("Die Aufnahme ließ sich nicht beenden.", urgent=True)
            return
        self.state = CONVERTING
        announce(f"Aufnahme nach {self.max_minutes} Minuten beendet. Wird umgewandelt."
                 if automatic else "Wird umgewandelt.")
        name, language, transcribe = self.model(), self.language(), self.transcribe
        self._run(lambda task: transcribe(audio, name, language), self._converted,
                  "Spracheingabe")

    def _converted(self, text: str) -> None:
        self.state = IDLE
        if self.discard:
            return
        if not text:
            announce("Es wurde nichts erkannt.")
            return
        target, self.target = self.target, None
        if target is not None:
            try:
                insert_text(target, text)
                announce("Text eingefügt.")
                return
            except RuntimeError:                        # Feld inzwischen zerstört
                pass
        QGuiApplication.clipboard().setText(text)
        announce("Text in der Zwischenablage.")

    def cancel(self) -> None:
        if self.state == RECORDING:
            self.timer.stop()
            recording, self.recording = self.recording, None
            try:
                recording.stop()                        # Aufnahme verwerfen
            except Exception as exc:
                log.warning("Aufnahme abbrechen: %r", exc)
            self.state, self.target = IDLE, None
            announce("Aufnahme abgebrochen.")
        elif self.state == CONVERTING:
            self.discard, self.target = True, None
            announce("Aufnahme abgebrochen.")
        else:
            announce("Es läuft keine Aufnahme.")

    # -- Modell herunterladen ---------------------------------------------------------------
    def offer_download(self, name: str, field: QWidget) -> None:
        text = (f"Für die Spracheingabe braucht das Cockpit das Whisper-Modell {name}, "
                f"{whisper.size_text(name)}. Es kommt aus dem Internet von Hugging Face und liegt "
                "danach im Datenordner des Cockpits. Jetzt herunterladen?")
        if not confirm(self.window, "Spracheingabe", text, yes="Herunterladen", no="Abbrechen"):
            return
        self.state = DOWNLOADING
        total = whisper.SIZES_MB.get(name, 0)
        progress = QTimer(self)
        progress.setInterval(5000)

        def show_progress() -> None:
            if total:
                percent = min(99, round(whisper.folder_mb(name) * 100 / total))
                announce(f"Whisper-Modell: {percent} Prozent heruntergeladen.", speak=False)

        progress.timeout.connect(show_progress)
        progress.start()
        announce("Whisper-Modell wird heruntergeladen.")
        download = self.download

        def done(_value) -> None:
            progress.stop()
            self.state = IDLE
            announce("Whisper-Modell heruntergeladen.")

        def failed() -> None:
            progress.stop()
            self.state = IDLE

        self._run(lambda task: download(name), done, "Whisper-Modell herunterladen",
                  on_failed=failed)

    # -- Hintergrund ------------------------------------------------------------------------
    def _run(self, work, done, title: str, on_failed: Callable[[], None] | None = None) -> None:
        task = Task(work, self)
        self.task = task

        def failed(message: str, details: str) -> None:
            log.warning("%s: %s %s", title, message, details)
            self.state = IDLE
            if on_failed is not None:
                on_failed()
            if not self.discard:
                show_error(self.window, title, message, details)

        def finished() -> None:
            if self.task is task:
                self.task = None
            task.wait()
            task.deleteLater()

        task.result.connect(done)
        task.error.connect(failed)
        task.finished.connect(finished)
        task.start()

    def shutdown(self) -> None:
        """Beim Beenden: laufende Aufnahme verwerfen, auf die Umwandlung warten."""
        QApplication.instance().removeEventFilter(self)
        self.timer.stop()
        if self.recording is not None:
            try:
                self.recording.stop()
            except Exception:
                pass
            self.recording = None
        if self.task is not None:
            self.discard = True
            self.task.wait(30000)
