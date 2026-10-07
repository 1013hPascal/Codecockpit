"""KI schneller und auf den Rechner eingestellt (Wunsch des Nutzers vom 07.10.2026).

Keine echte KI: Die Messung bekommt eine erfundene Uhr, Ollama einen nachgebauten Server.
"""
from __future__ import annotations

import json
import threading

import httpx
import pytest

from cockpit.ai.ollama import OllamaProvider
from cockpit.core import ai_tuning
from cockpit.core.ai_tools import TextAI
from cockpit.core.ai_tuning import COMPLEX, TEXT_FIELDS, Calibration, tuning
from cockpit.features.ai_assistant.context import spread
from cockpit.ui import ai_tuning_ui
from tests.conftest import FakeAI, said

FAST = Calibration(read_tps=2000.0, write_tps=60.0, date="2026-10-07T10:00:00")
SLOW = Calibration(read_tps=40.0, write_tps=4.0, date="2026-10-07T10:00:00")


# -- Budget je Art und Stufe ---------------------------------------------------------------------
def test_without_measurement_text_fields_get_less():
    assert tuning(TEXT_FIELDS, 0, None, 8000).max_chars == 3000
    assert tuning(COMPLEX, 0, None, 8000).max_chars == 8000
    assert tuning(TEXT_FIELDS, -3, None, 8000).max_chars < 3000
    assert tuning(TEXT_FIELDS, 3, None, 8000).max_chars == 8000          # nie über der Grenze


def test_measurement_sets_the_budget():
    slow = tuning(TEXT_FIELDS, 0, SLOW, 8000)
    assert slow.max_chars == ai_tuning.MIN_CHARS[TEXT_FIELDS]          # langsamer Rechner
    assert tuning(TEXT_FIELDS, 0, FAST, 8000).max_chars == 8000        # schneller Rechner
    middle = Calibration(300.0, 20.0, "")
    text = tuning(TEXT_FIELDS, 0, middle, 100_000).max_chars
    code = tuning(COMPLEX, 0, middle, 100_000).max_chars
    assert text < code                                                 # 0 ist nicht gleich 0
    assert tuning(TEXT_FIELDS, 1, middle, 100_000).max_chars > text
    assert tuning(TEXT_FIELDS, -1, middle, 100_000).max_chars < text


def test_thinking_only_for_complex_from_plus_two():
    assert not tuning(COMPLEX, 1, FAST, 8000).think
    assert tuning(COMPLEX, 2, FAST, 8000).think
    assert not tuning(TEXT_FIELDS, 3, FAST, 8000).think
    assert tuning(TEXT_FIELDS, 2, None, 8000).answer_factor > 1
    assert tuning(TEXT_FIELDS, -2, None, 8000).answer_factor < 1


def test_tasks_belong_to_a_purpose():
    assert ai_tuning.purpose_of("ai_assistant") == TEXT_FIELDS
    assert ai_tuning.purpose_of("terminal_explain") == TEXT_FIELDS
    assert ai_tuning.purpose_of("exe_fix") == COMPLEX
    assert ai_tuning.purpose_of("readme") == COMPLEX


# -- Messung -------------------------------------------------------------------------------------
def test_measure_reads_and_writes_speed():
    now = [0.0]
    asked = []

    def clock():
        return now[0]

    def ask(prompt, max_tokens):
        asked.append(max_tokens)
        if max_tokens == 120:
            now[0] += 2.0                                    # schreibt 40 Token in 2 Sekunden
            return "x" * 160
        if len(prompt) > 1000:
            now[0] += 1.25                                   # liest den langen Text
        return "OK"

    calibration = ai_tuning.measure(ask, clock=clock)
    assert asked == [5, 120, 5]                              # zuerst aufwärmen
    assert calibration.write_tps == 20.0
    assert calibration.read_tps > 500


def test_measure_stops_when_cancelled():
    from cockpit.core.errors import Cancelled
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(Cancelled):
        ai_tuning.measure(lambda prompt, n: "OK", cancel)


def test_store_keeps_measurement_and_levels(make_services):
    store = make_services().tunings
    assert store.calibration("Ollama, m") is None and store.level(TEXT_FIELDS) == 0
    store.save_calibration("Ollama, m", SLOW)
    assert store.calibration("Ollama, m") == SLOW
    store.set_level(COMPLEX, 7)
    assert store.level(COMPLEX) == 3                          # höchstens +3


# -- Anwendung -----------------------------------------------------------------------------------
def test_ai_for_uses_the_budget_of_the_task(make_services):
    services = make_services(ai=FakeAI())
    assert services.ai_for("ai_assistant").max_chars == 3000
    assert services.ai_for("exe_fix").max_chars == services.settings.load().ai_max_chars
    services.tunings.save_calibration("Test-KI", SLOW)
    assert services.ai_for("ai_assistant").max_chars == ai_tuning.MIN_CHARS[TEXT_FIELDS]


class Recorder(FakeAI):
    supports_think = True

    def __init__(self):
        super().__init__()
        self.calls = []

    def complete(self, messages, *, model, system="", schema=None, max_tokens=None,
                 cancel=None, think=False):
        self.calls.append((max_tokens, think))
        return "Antwort"


def test_text_ai_scales_answer_and_thinks_only_when_supported():
    recorder = Recorder()
    TextAI(recorder, "m", "KI", 8000, answer_factor=2.0, think=True).ask("Frage", max_tokens=100)
    assert recorder.calls == [(200, True)]
    plain = FakeAI()                                           # kann nicht nachdenken
    assert TextAI(plain, "m", "KI", 8000, think=True).ask("Frage") == "Antwort"


def test_ollama_keeps_the_model_loaded_and_thinks_on_request():
    sent = []

    def handler(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, text=json.dumps({"message": {"content": "ok"},
                                                    "done": True}) + "\n")

    provider = OllamaProvider(transport=httpx.MockTransport(handler))
    provider.complete([{"role": "user", "content": "Hallo"}], model="m")
    provider.complete([{"role": "user", "content": "Hallo"}], model="m", think=True)
    assert sent[0]["keep_alive"] == ai_tuning.KEEP_ALIVE and sent[0]["think"] is False
    assert sent[1]["think"] is True


# -- Weniger senden ------------------------------------------------------------------------------
def test_spread_gives_every_file_a_share():
    diff = "\n".join(f"diff --git a/{n}.py b/{n}.py\nindex 1..2\n--- a/{n}.py\n+++ b/{n}.py\n"
                     + "\n".join(f"+zeile {i}" for i in range(200)) for n in ("a", "b", "c"))
    short = spread(diff, 1500)
    assert len(short) < 1800
    assert all(f"diff --git a/{n}.py" in short for n in ("a", "b", "c"))
    assert "index 1..2" not in short
    assert spread("kurz", 1500) == "kurz"


# -- Fenster und Menü ------------------------------------------------------------------------------
def test_dialog_explains_and_saves_levels(qtbot, make_services):
    services = make_services()
    services.tunings.save_calibration("Ollama, m", FAST)
    dialog = ai_tuning_ui.AITuningDialog(services, "Ollama, m", ai_tuning_ui.DONE)
    qtbot.addWidget(dialog)
    assert dialog.text.isReadOnly() and dialog.initial_focus_widget is dialog.text
    text = dialog.text.toPlainText()
    assert text.startswith("Ollama, m ist auf diesen Rechner eingestellt. Gemessen am 07.10.2026")
    assert [dialog.purposes.item(i).text() for i in range(2)] == list(
        ai_tuning.PURPOSES.values())
    assert dialog.scale.count() == 7 and dialog.scale.currentItem().text() == "0 Standard"
    dialog.purposes.setCurrentRow(1)
    dialog.scale.setCurrentRow(ai_tuning.LEVELS.index(2))
    assert "Die KI denkt dabei nach." in dialog.text.toPlainText()
    assert services.tunings.level(COMPLEX) == 0                 # erst Speichern übernimmt
    dialog.save()
    assert services.tunings.level(COMPLEX) == 2 and services.tunings.level(TEXT_FIELDS) == 0
    assert said("Gespeichert.")


def test_menu_says_whether_the_ai_is_tuned(qtbot, make_services):
    from tests.test_phase10f import window
    win = window(qtbot, make_services())
    win.calibrator.start()                                      # keine KI eingerichtet
    assert win.calibrator.state == ai_tuning_ui.NONE
    assert win.calibrator.menu_text == "KI &einstellen …"
    win.calibrator.state = ai_tuning_ui.DONE
    assert win.calibrator.menu_text == "KI ist &eingestellt auf diesen Rechner …"
