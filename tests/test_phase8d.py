"""Teilschritt 8d: Spracheingabe mit Whisper.

Mikrofon und Whisper sind Attrappen. Es wird nichts aufgenommen und kein Modell geladen.
"""
from __future__ import annotations

import numpy
import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from cockpit.ai import models, whisper
from cockpit.ai.recording import Recording
from cockpit.core.features.manifest import AI_SERVICES
from cockpit.features.dictation.manifest import FEATURE_ID, MANIFEST
from cockpit.ui import dictation as dictation_ui
from tests.conftest import said


class FakeRecording:
    def __init__(self, max_seconds: int) -> None:
        self.max_seconds = max_seconds
        self.full = False
        self.started = self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self):
        self.stopped = True
        return numpy.ones(16000, dtype=numpy.float32)


def fake_model(name: str = "small") -> None:
    folder = whisper.model_dir(name)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "model.bin").write_bytes(b"x" * 1024)


class Window(QWidget):
    """Kleines Fenster mit zwei Textfeldern und einem Knopf, statt des Hauptfensters."""

    def __init__(self, services) -> None:
        super().__init__()
        self.services = services
        self.line = QLineEdit("Titel:")
        self.text = QPlainTextEdit()
        self.button = QPushButton("Knopf")
        layout = QVBoxLayout(self)
        for widget in (self.line, self.text, self.button):
            layout.addWidget(widget)


@pytest.fixture
def setup(qtbot, make_services):
    services = make_services([MANIFEST])
    services.database.set_value(whisper.MODEL_KEY, "small")
    window = Window(services)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    controller = dictation_ui.Dictation(window)
    controller.recording_factory = FakeRecording
    heard = []

    def transcribe(audio, name, language):
        heard.append((audio.size, name, language))
        return "hallo Welt\nzweite Zeile"

    controller.transcribe = transcribe
    yield services, window, controller, heard
    controller.shutdown()


# -- Kern -----------------------------------------------------------------------------------------
def test_libraries_and_service():
    assert whisper.problem() == ""
    assert "speech" in AI_SERVICES and MANIFEST.requires_services == ("speech",)
    assert MANIFEST.problems() == []


def test_model_choice_and_download_state(make_services):
    services = make_services([])
    assert whisper.chosen_model(services.database, 8) == "small"
    assert whisper.chosen_model(services.database, 31.7) == "medium"
    assert whisper.chosen_model(services.database, 64) == "large-v3-turbo"
    services.database.set_value(whisper.MODEL_KEY, "small")
    assert whisper.chosen_model(services.database, 64) == "small"
    assert not whisper.is_downloaded("small")
    fake_model()
    assert whisper.is_downloaded("small") and whisper.downloaded() == ["small"]
    assert whisper.folder_mb("small") == 0
    whisper.delete("small")
    assert not whisper.model_dir("small").exists()
    assert [t.model for t in models.SPEECH_TIERS] == list(whisper.SIZES_MB)


def test_transcribe_needs_the_model():
    assert whisper.transcribe(numpy.zeros(0, dtype=numpy.float32), "small") == ""
    from cockpit.core.errors import CockpitError
    with pytest.raises(CockpitError, match="nicht heruntergeladen"):
        whisper.transcribe(numpy.ones(10, dtype=numpy.float32), "small")


def test_recording_keeps_audio_in_memory_and_stops_when_full():
    recording = Recording(1)
    block = numpy.ones((8000, 1), dtype=numpy.float32)
    recording._callback(block, 8000, None, None)
    assert not recording.full
    recording._callback(block, 8000, None, None)
    assert recording.full
    recording._callback(block, 8000, None, None)            # danach nichts mehr
    assert recording.stop().size == 16000
    assert Recording(1).stop().size == 0


# -- Einfügen -------------------------------------------------------------------------------------
def test_insert_text(qtbot):
    line = QLineEdit("Titel:")
    qtbot.addWidget(line)
    dictation_ui.insert_text(line, " neue\nSuche ")
    assert line.text() == "Titel: neue Suche"
    text = QPlainTextEdit("Erste Zeile")
    qtbot.addWidget(text)
    cursor = text.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    text.setTextCursor(cursor)
    dictation_ui.insert_text(text, "und mehr\nnoch mehr")
    assert text.toPlainText() == "Erste Zeile und mehr\nnoch mehr"
    read_only = QLineEdit()
    qtbot.addWidget(read_only)
    read_only.setReadOnly(True)
    assert dictation_ui.text_field(read_only) is None


# -- Ablauf ---------------------------------------------------------------------------------------
def test_ctrl_d_records_and_inserts(qtbot, setup):
    services, window, controller, heard = setup
    fake_model()
    window.line.setFocus()
    window.line.setCursorPosition(len(window.line.text()))
    qtbot.keyClick(window.line, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)
    assert controller.state == dictation_ui.RECORDING and said("Aufnahme läuft.")
    assert controller.recording.max_seconds == 600
    qtbot.keyClick(window.line, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier)
    assert said("Wird umgewandelt.")
    qtbot.waitUntil(lambda: controller.state == dictation_ui.IDLE, timeout=5000)
    assert window.line.text() == "Titel: hallo Welt zweite Zeile"
    assert heard == [(16000, "small", "de")] and said("Text eingefügt.")


def test_cancel_inserts_nothing(qtbot, setup):
    services, window, controller, heard = setup
    fake_model()
    window.text.setFocus()
    controller.toggle()
    qtbot.keyClick(window.text, Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier
                   | Qt.KeyboardModifier.ShiftModifier)
    assert controller.state == dictation_ui.IDLE and said("Aufnahme abgebrochen.")
    assert window.text.toPlainText() == "" and heard == []
    controller.cancel()
    assert said("Es läuft keine Aufnahme.")


def test_only_in_text_fields(qtbot, setup):
    services, window, controller, heard = setup
    window.button.setFocus()
    controller.toggle()
    assert controller.state == dictation_ui.IDLE
    assert said("Diktieren geht nur in einem Textfeld.")


def test_switched_off(qtbot, setup):
    services, window, controller, heard = setup
    services.features.set_globally_enabled(FEATURE_ID, False)
    window.line.setFocus()
    controller.toggle()
    assert controller.state == dictation_ui.IDLE and said("Spracheingabe ist ausgeschaltet.")


def test_settings_language_and_length(qtbot, setup):
    services, window, controller, heard = setup
    fake_model()
    services.features.set_setting(FEATURE_ID, "language", "Automatisch erkennen")
    services.features.set_setting(FEATURE_ID, "max_minutes", 2)
    window.text.setFocus()
    controller.toggle()
    assert controller.recording.max_seconds == 120
    controller.recording.full = True
    controller._check()                                     # endet von selbst
    assert said("Aufnahme nach 2 Minuten beendet. Wird umgewandelt.")
    qtbot.waitUntil(lambda: controller.state == dictation_ui.IDLE, timeout=5000)
    assert heard[0][2] is None
    assert window.text.toPlainText() == "hallo Welt\nzweite Zeile"


def test_field_gone_goes_to_clipboard(qtbot, setup):
    services, window, controller, heard = setup
    fake_model()
    field = QLineEdit(window)
    field.show()
    field.setFocus()
    controller.toggle()
    controller.target = None                                # Feld inzwischen geschlossen
    controller.stop()
    qtbot.waitUntil(lambda: controller.state == dictation_ui.IDLE, timeout=5000)
    assert QGuiApplication.clipboard().text() == "hallo Welt\nzweite Zeile"
    assert said("Text in der Zwischenablage.")


def test_first_dictation_offers_the_download(qtbot, setup, monkeypatch):
    services, window, controller, heard = setup
    questions = []
    monkeypatch.setattr(dictation_ui, "confirm", lambda parent, title, text, **kw:
                        questions.append(text) or True)
    controller.download = lambda name: fake_model(name)
    window.line.setFocus()
    controller.toggle()
    assert "Whisper-Modell small, etwa 500 MB" in questions[0]
    qtbot.waitUntil(lambda: controller.state == dictation_ui.IDLE, timeout=5000)
    assert whisper.is_downloaded("small") and said("Whisper-Modell heruntergeladen.")
    assert controller.recording is None                     # Aufnahme erst mit Strg+D


# -- Sprach-KI in der KI-Verwaltung ---------------------------------------------------------------
def test_speech_dialog(qtbot, make_services, monkeypatch):
    from cockpit.ui import ai_dialogs
    services = make_services([MANIFEST])
    monkeypatch.setattr(ai_dialogs, "current_ram", lambda s: 32)
    fake_model("small")
    dialog = ai_dialogs.SpeechDialog(services)
    qtbot.addWidget(dialog)
    lines = [dialog.list.item(r).text() for r in range(dialog.list.count())]
    assert lines[0].startswith("small, ab 16 GB") and lines[0].endswith("heruntergeladen")
    assert lines[1].startswith("medium, gewählt, ab 32 GB")
    assert "empfohlen für Ihren Rechner" in lines[1] and "nicht heruntergeladen" in lines[1]
    dialog.list.setCurrentRow(0)
    assert dialog.delete_button.isVisibleTo(dialog)
    assert not dialog.download_button.isVisibleTo(dialog)
    dialog.choose_current()
    assert services.database.get_value(whisper.MODEL_KEY) == "small"
    dialog.list.setCurrentRow(1)
    assert dialog.download_button.isVisibleTo(dialog)
