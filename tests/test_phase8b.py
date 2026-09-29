"""Phase 8b: Menü KI, KI-Verwaltung, lokale KI passend zum Rechner, Feature Terminal-Erklärung.

Keine echte KI: Ollama und die OpenAI-kompatible Schnittstelle antworten über httpx.MockTransport.
Alle Schlüssel sind erfunden.
"""
from __future__ import annotations

import json
import sys
import threading

import httpx
import pytest

from cockpit.ai import models as tiers
from cockpit.ai import ollama, prompt_files
from cockpit.ai.base import AIError
from cockpit.ai.openai_compatible import OpenAICompatibleProvider
from cockpit.core import hardware, terminal
from cockpit.core.accounts import find_type
from cockpit.core.ai_tools import ACCOUNT, OLLAMA, SHORTENED, TEXT, TextAI, limit_text
from cockpit.core.errors import Cancelled
from cockpit.core.features.registry import FeatureRegistry
from cockpit.core.secret import Secret
from cockpit.core.services import LOCAL_ONLY, NO_AI
from tests.conftest import FakeAI, FakeVault, said

FAKE_KEY = "sk-ErfundenerSchluesselNurFuerTests123456"


# -- Modellstufen ---------------------------------------------------------------------------------
def test_tiers_follow_the_memory():
    assert tiers.recommended(tiers.TEXT_TIERS, 31.7).model == "gemma4:12b"   # Windows: 31,7
    assert tiers.recommended(tiers.TEXT_TIERS, 15.8).model == "gemma4:e4b"
    assert tiers.recommended(tiers.TEXT_TIERS, 64).model == "gemma4:26b"
    assert tiers.recommended(tiers.TEXT_TIERS, 8) is None
    assert tiers.recommended(tiers.TEXT_TIERS, None) is None
    assert tiers.recommended(tiers.SPEECH_TIERS, 32).model == "medium"


def test_suggestion_lines():
    line = tiers.suggestion_line(tiers.TEXT_TIERS[1], 32, ["gemma4:12b"])
    assert line == ("gemma4:12b, ab 32 GB Arbeitsspeicher, etwa 8 GB, empfohlen für Ihren "
                    "Rechner, installiert")
    assert tiers.suggestion_line(tiers.TEXT_TIERS[2], 32, []).endswith(
        "zu groß für Ihren Rechner, nicht installiert")
    assert tiers.is_installed("gemma4", ["gemma4:latest"])
    assert tiers.pull_command("gemma4:12b") == "ollama pull gemma4:12b"


# -- Ollama ---------------------------------------------------------------------------------------
def ollama_transport(seen: list | None = None, chat_lines: list | None = None, status=200):
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "gemma4:12b"},
                                                        {"name": "gemma4:e4b"}]})
        if request.url.path == "/api/chat":
            if status != 200:
                return httpx.Response(status, json={"error": "model 'x' not found"})
            lines = chat_lines or [{"message": {"content": "Hallo "}},
                                   {"message": {"content": "Welt."}, "done": True}]
            return httpx.Response(200, text="\n".join(json.dumps(x) for x in lines))
        return httpx.Response(404)
    return httpx.MockTransport(handler)


def test_ollama_models_and_answer():
    seen = []
    provider = ollama.OllamaProvider("http://ollama.test", ollama_transport(seen))
    assert provider.is_local and not provider.manage_server
    assert provider.models() == ["gemma4:12b", "gemma4:e4b"]
    answer = provider.complete([{"role": "user", "content": "Hi"}], model="gemma4:12b",
                               system="Kurz.", max_tokens=50)
    assert answer == "Hallo Welt."
    body = json.loads(seen[-1].content)
    assert body["messages"][0] == {"role": "system", "content": "Kurz."}
    assert body["options"] == {"num_predict": 50} and body["stream"] is True


def test_ollama_without_thinking_and_fallback():
    """Test von 8b mit gemma4:12b: Mit Nachdenken blieb die Antwort leer."""
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        if "think" in body:
            return httpx.Response(400, json={"error": "\"alt\" does not support thinking"})
        return httpx.Response(200, text=json.dumps({"message": {"content": "Ja."}, "done": True}))
    provider = ollama.OllamaProvider("http://ollama.test", httpx.MockTransport(handler))
    assert provider.complete([{"role": "user", "content": "?"}], model="alt") == "Ja."
    assert bodies[0]["think"] is False and "think" not in bodies[1]
    provider.complete([{"role": "user", "content": "?"}], model="alt")
    assert len(bodies) == 3                                      # gemerkt: gleich ohne


def test_ollama_errors_are_explained():
    provider = ollama.OllamaProvider("http://ollama.test", ollama_transport(status=404))
    with pytest.raises(AIError, match="abgelehnt") as info:
        provider.complete([{"role": "user", "content": "Hi"}], model="x")
    assert "not found" in info.value.details

    def refuse(request):
        raise httpx.ConnectError("verweigert")
    offline = ollama.OllamaProvider("http://ollama.test", httpx.MockTransport(refuse))
    with pytest.raises(AIError, match="nicht erreichbar"):
        offline.models()
    assert not offline.test_connection().ok


def test_ollama_cancel():
    cancel = threading.Event()
    cancel.set()
    provider = ollama.OllamaProvider("http://ollama.test", ollama_transport())
    with pytest.raises(Cancelled):
        provider.complete([{"role": "user", "content": "Hi"}], model="x", cancel=cancel)


def test_ollama_server_only_stops_what_it_started(monkeypatch):
    server = ollama.OllamaServer("http://ollama.test")
    monkeypatch.setattr(server, "is_running", lambda: True)
    server.start()                                  # läuft schon: mitbenutzen
    assert not server.owned
    server.stop()                                   # nichts zu beenden
    monkeypatch.setattr(server, "is_running", lambda: False)
    monkeypatch.setattr(ollama, "find_exe", lambda: None)
    with pytest.raises(AIError, match="nicht installiert"):
        server.start()


# -- OpenAI-kompatibel ---------------------------------------------------------------------------
def openai_transport(seen: list, key_ok: bool = True):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if not key_ok:
            return httpx.Response(401, json={"error": {"message": "Incorrect API key"}})
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "gpt-b"}, {"id": "gpt-a"}]})
        if request.url.path == "/v1/chat/completions":
            chunks = [{"choices": [{"delta": {"content": "Guten "}}]},
                      {"choices": [{"delta": {"content": "Tag."}}]}]
            text = "".join(f"data: {json.dumps(c)}\n\n" for c in chunks) + "data: [DONE]\n\n"
            return httpx.Response(200, text=text)
        return httpx.Response(404)
    return httpx.MockTransport(handler)


def test_openai_compatible_models_and_answer():
    seen = []
    provider = OpenAICompatibleProvider("https://ki.example/v1", Secret(FAKE_KEY), False,
                                        openai_transport(seen))
    assert not provider.is_local
    assert provider.models() == ["gpt-a", "gpt-b"]
    assert seen[0].headers["Authorization"] == f"Bearer {FAKE_KEY}"
    assert provider.complete([{"role": "user", "content": "Hi"}], model="gpt-a") == "Guten Tag."
    assert json.loads(seen[-1].content)["model"] == "gpt-a"


def test_openai_compatible_rejected_key_without_secret_in_details():
    seen = []
    provider = OpenAICompatibleProvider("https://ki.example/v1", Secret(FAKE_KEY), True,
                                        openai_transport(seen, key_ok=False))
    assert provider.is_local                        # im eigenen Netz
    result = provider.test_connection()
    assert not result.ok and result.text == "Der API-Schlüssel wurde abgelehnt."
    assert FAKE_KEY not in result.details


# -- Konto mit Kästchen "im eigenen Netz" ----------------------------------------------------------
def ai_account(services, name="Firmen-KI", in_network=False):
    services.vault.vault = FakeVault()
    account_type = find_type("ai", "openai_compatible")
    return services.accounts.create(account_type, name, {
        "url": "https://ki.example/v1", "api_key": Secret(FAKE_KEY), "in_network": in_network})


def test_account_with_yes_no_field(make_services):
    services = make_services()
    account = ai_account(services, in_network=True)
    assert account.extra["in_network"] == "ja"
    values = services.accounts.values(account)
    assert values["in_network"] is True and values["api_key"].reveal() == FAKE_KEY
    assert FAKE_KEY not in json.dumps(account.extra)
    adapter = services.accounts.adapter_for(account)
    assert isinstance(adapter, OpenAICompatibleProvider) and adapter.is_local
    from cockpit.core.accounts import account_types
    assert "Ollama" not in [t.display_name for t in account_types()]   # braucht kein Konto


# -- Werkzeuge -------------------------------------------------------------------------------------
def test_tools_default_label_and_remove(make_services):
    services = make_services()
    tools = services.ai_tools
    assert tools.default() is None
    first = tools.add(TEXT, OLLAMA, "gemma4:12b")
    assert tools.default().id == first.id
    assert tools.label(first) == "Ollama auf diesem Rechner, gemma4:12b, Standard"
    account = ai_account(services)
    second = tools.add(TEXT, ACCOUNT, "gpt-a", account.id)
    assert tools.label(second) == "Firmen-KI, gpt-a"
    tools.set_default(second.id)
    assert tools.default().id == second.id and tools.label(first).endswith("gemma4:12b")
    tools.set_model(first.id, "gemma4:e4b")
    assert tools.get(first.id).model == "gemma4:e4b"
    services.accounts.delete(account)
    assert [t.id for t in tools.all()] == [first.id]         # Konto weg: Werkzeug weg
    assert tools.default().id == first.id
    tools.remove(first.id)
    assert tools.all() == []


def test_ai_for_uses_tools_and_privacy_rule(make_services):
    services = make_services()
    assert services.ai_problem() == NO_AI and not services.service_availability("ai")
    assert services.ai_for("x") is None
    local = services.ai_tools.add(TEXT, OLLAMA, "gemma4:12b")
    ai = services.ai_for("terminal_explain")
    assert ai.model == "gemma4:12b" and ai.is_local and ai.max_chars == 8000
    account = ai_account(services)
    cloud = services.ai_tools.add(TEXT, ACCOUNT, "gpt-a", account.id)
    assert services.ai_for("x", tool_id=cloud.id).name == "Firmen-KI, gpt-a"
    services.settings.update(ai_local_only=True)
    assert services.ai_for("x", tool_id=cloud.id) is None
    assert services.ai_problem(cloud.id) == LOCAL_ONLY
    assert services.ai_for("x", tool_id=local.id) is not None
    services.ai_tools.set_default(cloud.id)
    assert not services.service_availability("ai")


def test_consent_is_remembered(make_services):
    tools = make_services().ai_tools
    assert not tools.consent_given("terminal_explain", "Firmen-KI, gpt-a")
    tools.give_consent("terminal_explain", "Firmen-KI, gpt-a")
    assert tools.consent_given("terminal_explain", "Firmen-KI, gpt-a")
    assert not tools.consent_given("commit_message", "Firmen-KI, gpt-a")


def test_limit_text_also_for_local_ai():
    assert limit_text("kurz", 100) == "kurz"
    cut = limit_text("a" * 50 + "ENDE", 30, keep_end=True)
    assert len(cut) <= 30 and cut.startswith(SHORTENED) and cut.endswith("ENDE")
    assert limit_text("ANFANG" + "b" * 50, 30).startswith("ANFANG")

    class Recorder(FakeAI):
        def complete(self, messages, **kwargs):
            self.sent = messages[0]["content"]
            return " Antwort "
    provider = Recorder()
    ai = TextAI(provider, "m", "Test", 20)
    assert ai.ask("x" * 100) == "Antwort"
    assert len(provider.sent) <= 20


# -- Rechner ---------------------------------------------------------------------------------------
@pytest.mark.skipif(sys.platform != "win32", reason="nur Windows")
def test_memory_is_read_from_windows():
    assert hardware.ram_gb() > 1
    assert hardware.cpu_name()


def test_machine_lines():
    assert hardware.Machine(31.7, "Ryzen", ["Radeon"]).lines() == [
        "Arbeitsspeicher Ihres Computers: 31,7 GB", "Prozessor: Ryzen", "Grafikkarte: Radeon"]
    lines = hardware.Machine(None).lines()
    assert lines[0].startswith("Arbeitsspeicher Ihres Computers: nicht erkannt. Den "
                               "Arbeitsspeicher finden Sie")
    assert hardware.Machine(32.0, manual=True).lines()[0] == \
        "Arbeitsspeicher Ihres Computers: 32 GB, von Ihnen eingegeben"


def test_manual_memory_wins(monkeypatch):
    monkeypatch.setattr(hardware, "gpu_names", lambda: [])
    assert hardware.detect(16).ram_gb == 16 and hardware.detect(16).manual


# -- Prompts und Erklärung --------------------------------------------------------------------------
def test_prompt_can_be_overridden_in_data_folder(home):
    assert "Braillezeile" in prompt_files.load("terminal_explain_system")
    (home / "prompts").mkdir(parents=True)
    (home / "prompts" / "terminal_explain_system.txt").write_text("Eigene Fassung.",
                                                                  encoding="utf-8")
    assert prompt_files.load("terminal_explain_system") == "Eigene Fassung."
    assert prompt_files.fill("A <<x>> {y}", x="1") == "A 1 {y}"


def test_explanation_prompt_and_cleaning():
    from cockpit.features.terminal_explain import explain
    lines = [f"Zeile {i}" for i in range(2000)] + [f"Fehler mit {FAKE_KEY}"]
    system, request = explain.prompt("git push", 1, lines, 3000)
    assert "Befehl: git push" in request and "Rückgabewert: 1" in request
    assert "Zeile 1999" in request and "Zeile 0\n" not in request      # das Ende bleibt
    assert FAKE_KEY not in request and len(request) < 3200
    assert explain.clean("**Grund:** kaputt.\n- Tun Sie `git pull`.\n\n# Ende") == \
        "Grund: kaputt.\nTun Sie git pull.\nEnde"
    ai = TextAI(FakeAI(answers=["Der Branch fehlt. Holen Sie ihn."]), "m", "Test", 8000)
    assert explain.explain(ai, "git checkout x", 1, ["error"]) == \
        "Der Branch fehlt. Holen Sie ihn."


def test_clean_terminal_lines():
    assert terminal.clean_line("pulling 10%\rpulling 55%\rpulling 100%\r\n") == "pulling 100%"
    assert terminal.clean_line("\x1b[32mgrün\x1b[0m\n") == "grün"
    assert terminal.clean_line("\r\n") == ""


def test_feature_is_found_and_needs_ai(make_services):
    registry = FeatureRegistry.discover()
    manifest = registry.get("terminal_explain")
    assert manifest.requires_services == ("ai",) and manifest.enabled_by_default
    assert manifest.introduction_text().startswith("# Terminal-Erklärung")
    assert not manifest.problems()


# -- Terminal mit Erklärung ------------------------------------------------------------------------
windows = pytest.mark.skipif(sys.platform != "win32", reason="Terminal nutzt PowerShell")


def rows(listing) -> list[str]:
    return [listing.item(i).text() for i in range(listing.count())]


@windows
def test_terminal_explains_a_failed_command(qtbot, tmp_path):
    from cockpit.ui import terminal_dialog as td
    ai = TextAI(FakeAI(answers=["Der Befehl hat einen Tippfehler. Prüfen Sie ihn."]),
                "m", "Test", 8000)
    asked = []
    dialog = td.TerminalDialog(tmp_path, "T", explainer=lambda parent: asked.append(1) or ai)
    qtbot.addWidget(dialog)
    assert dialog.explanation.accessibleName() == "Erklärung der KI"
    assert " ".join(rows(dialog.explanation)) == td.NO_EXPLANATION_YET    # ein Satz pro Zeile
    dialog.edit.setText("echo gut")
    dialog.run_command()
    qtbot.waitUntil(lambda: not dialog.running, timeout=20000)
    assert asked == []                                           # Erfolg: keine Erklärung
    dialog.edit.setText("exit 3")
    dialog.run_command()
    qtbot.waitUntil(lambda: dialog.explain_task is None and not dialog.running
                    and rows(dialog.explanation)[0] != td.EXPLAINING, timeout=20000)
    assert rows(dialog.explanation) == ["Der Befehl hat einen Tippfehler.", "Prüfen Sie ihn."]
    assert said(td.READY)


@windows
def test_terminal_says_why_there_is_no_explanation(qtbot, tmp_path):
    from cockpit.ui import terminal_dialog as td
    dialog = td.TerminalDialog(tmp_path, "T", explainer=lambda parent: NO_AI)
    qtbot.addWidget(dialog)
    dialog.edit.setText("exit 1")
    dialog.run_command()
    qtbot.waitUntil(lambda: not dialog.running, timeout=20000)
    assert rows(dialog.explanation) == ["Keine Erklärung.", NO_AI.split(". ")[0] + ".",
                                        "Das geht im Menü KI, KI-Verwaltung."]


def test_terminal_without_feature_and_with_command(qtbot, tmp_path):
    from cockpit.ui import terminal_dialog as td
    dialog = td.TerminalDialog(tmp_path, "T", command="ollama pull gemma4:12b")
    qtbot.addWidget(dialog)
    assert dialog.explanation is None
    assert dialog.edit.text() == "ollama pull gemma4:12b"


def test_explainer_only_when_feature_is_active(make_services, projects_root):
    from cockpit.features.terminal_explain.manifest import MANIFEST
    from cockpit.ui.terminal_dialog import explainer_for
    from tests.conftest import make_project
    services = make_services([MANIFEST])
    services.projects.add(make_project(projects_root, "Tagebuch"))
    project = services.projects.all()[0]
    assert explainer_for(services, project) is None              # keine KI eingerichtet
    services.ai_tools.add(TEXT, OLLAMA, "gemma4:12b")
    assert explainer_for(services, project) is not None
    assert explainer_for(services, None) is not None
    services.features.disable("terminal_explain", project)
    assert explainer_for(services, project) is None
    services.features.set_globally_enabled("terminal_explain", False)
    assert explainer_for(services, None) is None


# -- Datenschutz-Rückfrage -------------------------------------------------------------------------
def test_consent_question_for_external_ai(qtbot, make_services, monkeypatch):
    from cockpit.ui import ai_ui
    services = make_services()
    questions, answers = [], [False, True]
    monkeypatch.setattr(ai_ui, "confirm", lambda parent, title, text, **kw:
                        questions.append(text) or answers.pop(0))
    account = ai_account(services)
    services.ai_tools.add(TEXT, ACCOUNT, "gpt-a", account.id)
    assert ai_ui.prepare(services, None, "terminal_explain", "der Befehl") == ai_ui.DECLINED
    assert questions[0] == ("Für Erklärungen im Terminal werden der Befehl an Firmen-KI, gpt-a "
                            "gesendet. Diese KI läuft außerhalb Ihres Rechners. Einverstanden?")
    assert isinstance(ai_ui.prepare(services, None, "terminal_explain", "der Befehl"), TextAI)
    assert isinstance(ai_ui.prepare(services, None, "terminal_explain", "der Befehl"), TextAI)
    assert len(questions) == 2                                    # Ja wird gemerkt


def test_no_question_for_local_ai(make_services, monkeypatch):
    from cockpit.ui import ai_ui
    services = make_services()
    monkeypatch.setattr(ai_ui, "confirm", lambda *a, **k: pytest.fail("keine Rückfrage"))
    services.ai_tools.add(TEXT, OLLAMA, "gemma4:12b")
    assert isinstance(ai_ui.prepare(services, None, "terminal_explain", "x"), TextAI)
    services.ai_tools.add(TEXT, OLLAMA, "")
    services.ai_tools.set_default(2)
    assert "noch kein Modell" in ai_ui.prepare(services, None, "terminal_explain", "x")


# -- KI-Verwaltung ---------------------------------------------------------------------------------
@pytest.fixture
def quiet_machine(monkeypatch):
    """Kein PowerShell und kein Ollama in den Fenster-Tests."""
    monkeypatch.setattr(hardware, "detect",
                        lambda manual=None: hardware.Machine(manual or 32.0, "Test-CPU",
                                                             ["Test-GPU"], bool(manual)))
    monkeypatch.setattr(hardware, "ram_gb", lambda: 32.0)
    monkeypatch.setattr(ollama, "state", lambda: "Ollama läuft.")
    monkeypatch.setattr(ollama, "find_exe", lambda: None)


def manager(qtbot, services):
    from cockpit.ui.ai_dialogs import AIManagerDialog
    dialog = AIManagerDialog(services)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10000)
    return dialog


def test_manager_shows_machine_and_recommendation(qtbot, make_services, quiet_machine):
    from cockpit.ui import ai_dialogs
    services = make_services()
    dialog = manager(qtbot, services)
    assert dialog.windowTitle() == "KI-Verwaltung"
    assert dialog.list.accessibleName() == "Text-KI und Sprach-KI"
    assert rows(dialog.list) == [ai_dialogs.NEW_TOOL, ai_dialogs.NEW_SPEECH]
    assert rows(dialog.info) == [
        "Arbeitsspeicher Ihres Computers: 32 GB", "Prozessor: Test-CPU", "Grafikkarte: Test-GPU",
        "Empfehlung für Text-KI mit Ollama: gemma4:12b, ab 32 GB Arbeitsspeicher, etwa 8 GB.",
        "Empfehlung für Sprach-KI mit Whisper: medium, ab 32 GB Arbeitsspeicher, etwa 1,5 GB.",
        "Ollama läuft."]
    for button in (dialog.model_button, dialog.default_button, dialog.test_button,
                   dialog.remove_button):
        assert button.isHidden()                               # passt nicht zur Zeile "Neu"
    assert not dialog.install_button.isHidden()                # find_exe: nicht installiert


def test_manager_adds_local_tool_and_changes_default(qtbot, make_services, quiet_machine,
                                                     monkeypatch):
    from cockpit.ui import ai_dialogs
    services = make_services()
    dialog = manager(qtbot, services)
    monkeypatch.setattr(ai_dialogs, "choose_from_list", lambda *a, **k: 0)
    monkeypatch.setattr(ai_dialogs.AIManagerDialog, "pick_model",
                        lambda self, provider, is_ollama, current: "gemma4:12b")
    dialog.open_current()
    assert rows(dialog.list)[2] == "Ollama auf diesem Rechner, gemma4:12b, Standard"
    assert said("Text-KI eingerichtet: Ollama auf diesem Rechner, gemma4:12b, Standard.")
    assert not dialog.model_button.isHidden() and dialog.default_button.isHidden()
    services.ai_tools.add(TEXT, OLLAMA, "gemma4:e4b")
    dialog.refresh(2)
    assert not dialog.default_button.isHidden()
    dialog.make_default()
    assert services.ai_tools.default().model == "gemma4:e4b"
    monkeypatch.setattr(ai_dialogs, "confirm", lambda *a, **k: True)
    dialog.remove_current()
    assert [t.model for t in services.ai_tools.all()] == ["gemma4:12b"]


def test_manager_adds_existing_ai_account(qtbot, make_services, quiet_machine, monkeypatch):
    from cockpit.ui import ai_dialogs
    services = make_services()
    ai_account(services)
    dialog = manager(qtbot, services)
    monkeypatch.setattr(ai_dialogs, "choose_from_list", lambda parent, title, name, options:
                        options.index("Extern: Firmen-KI"))
    picked = []
    monkeypatch.setattr(ai_dialogs.AIManagerDialog, "pick_model",
                        lambda self, provider, is_ollama, current:
                        picked.append((type(provider).__name__, is_ollama)) or "gpt-a")
    dialog.new_tool()
    assert picked == [("OpenAICompatibleProvider", False)]
    assert rows(dialog.list)[2] == "Firmen-KI, gpt-a, Standard"


def test_manual_memory(qtbot, make_services, quiet_machine, monkeypatch):
    from cockpit.ui import ai_dialogs
    services = make_services()
    dialog = manager(qtbot, services)

    class FakeRam:
        def __init__(self, current, parent):
            self.value = 16

        def exec(self):
            return 1
    monkeypatch.setattr(ai_dialogs, "RamDialog", FakeRam)
    dialog.enter_ram()
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10000)
    assert rows(dialog.info)[0] == "Arbeitsspeicher Ihres Computers: 16 GB, von Ihnen eingegeben"
    assert "gemma4:e4b" in rows(dialog.info)[3]
    assert ai_dialogs.current_ram(services) == 16


def model_dialog(qtbot, services, provider, is_ollama, current=""):
    from cockpit.ui.ai_dialogs import ModelDialog
    dialog = ModelDialog(services, provider, is_ollama, current)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10000)
    return dialog


def test_model_dialog_lists_installed_and_suggested(qtbot, make_services, quiet_machine):
    provider = ollama.OllamaProvider("http://ollama.test", ollama_transport())
    dialog = model_dialog(qtbot, make_services(), provider, True)
    assert dialog.installed_list.accessibleName() == "Installierte Modelle"
    assert rows(dialog.installed_list) == ["gemma4:12b", "gemma4:e4b"]
    assert dialog.suggested.accessibleName() == "Vorgeschlagene Modelle"
    assert rows(dialog.suggested)[1] == ("gemma4:12b, ab 32 GB Arbeitsspeicher, etwa 8 GB, "
                                         "empfohlen für Ihren Rechner, installiert")
    assert dialog.suggested.currentRow() == 1                  # die Empfehlung
    dialog.installed_list.setCurrentRow(1)
    dialog.take_installed()
    assert dialog.chosen == "gemma4:e4b"


def test_suggested_model_opens_terminal_with_pull(qtbot, make_services, quiet_machine,
                                                  monkeypatch):
    from cockpit.ui import terminal_dialog
    opened = []
    monkeypatch.setattr(terminal_dialog, "open_terminal",
                        lambda services, parent, folder, title, project=None, command="":
                        opened.append((title, command)))
    provider = ollama.OllamaProvider("http://ollama.test", ollama_transport())
    dialog = model_dialog(qtbot, make_services(), provider, True)
    dialog.suggested.setCurrentRow(2)                          # gemma4:26b, nicht installiert
    dialog.take_suggested()
    assert opened == [("Modell gemma4:26b herunterladen", "ollama pull gemma4:26b")]
    assert dialog.chosen == "" and dialog.edit.text() == "gemma4:26b"
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10000)


def test_model_dialog_for_external_ai_has_no_suggestions(qtbot, make_services):
    dialog = model_dialog(qtbot, make_services(), FakeAI(), False, "eigenes-modell")
    assert dialog.suggested is None
    assert rows(dialog.installed_list) == ["testmodell"]
    assert dialog.edit.text() == "eigenes-modell"


def test_feature_settings_offer_the_tools(qtbot, make_services):
    from cockpit.features.terminal_explain.manifest import MANIFEST
    from cockpit.ui.features_dialogs import FeatureSettingsDialog
    services = make_services([MANIFEST])
    services.ai_tools.add(TEXT, OLLAMA, "gemma4:12b")
    second = services.ai_tools.add(TEXT, OLLAMA, "gemma4:e4b")
    dialog = FeatureSettingsDialog(services, MANIFEST)
    qtbot.addWidget(dialog)
    combo = dialog.form.fields["tool"].focus
    assert [combo.itemText(i) for i in range(combo.count())] == [
        "Standard-Werkzeug (Ollama auf diesem Rechner, gemma4:12b)",
        "Ollama auf diesem Rechner, gemma4:12b", "Ollama auf diesem Rechner, gemma4:e4b"]
    assert combo.accessibleName() == "KI für Erklärungen"
    combo.setCurrentIndex(2)
    dialog.save()
    assert services.features.setting("terminal_explain", "tool") == second.id


def test_menu_ai(qtbot, make_services, quiet_machine, monkeypatch):
    from cockpit.features.terminal_explain.manifest import MANIFEST
    from cockpit.ui import features_dialogs
    from cockpit.ui.main_window import MainWindow
    services = make_services([MANIFEST])
    win = MainWindow(services)
    qtbot.addWidget(win)
    menu = next(a.menu() for a in win.menuBar().actions() if a.text() == "&KI")
    assert [a.text() for a in menu.actions()] == ["KI-&Verwaltung …", "KI-&Features …"]
    selected = []
    monkeypatch.setattr(features_dialogs.GlobalFeaturesDialog, "exec",
                        lambda self: selected.append(self.current().id))
    win.open_ai_features()
    assert selected == ["terminal_explain"]


def test_wizard_page_ai(qtbot, make_services, quiet_machine):
    from cockpit.ui.setup_wizard import AIPage, SetupWizard
    services = make_services()
    wizard = SetupWizard(services)
    qtbot.addWidget(wizard)
    page = next(p for p in wizard.pages if isinstance(p, AIPage))
    page.on_show()
    qtbot.waitUntil(lambda: page.task is None, timeout=10000)
    lines = rows(page.text)
    assert lines[0].startswith("Um Ihren Alltag zu vereinfachen, gibt es mehrere KI-Features.")
    assert lines[1] == "Es ist noch keine KI eingerichtet."
    assert lines[2] == "Arbeitsspeicher Ihres Computers: 32 GB"
    assert lines[3].startswith("Empfehlung für Text-KI mit Ollama: gemma4:12b")
    assert lines[4].startswith("Empfehlung für Sprach-KI mit Whisper: medium")
    assert page.done_text == ""
    services.ai_tools.add(TEXT, OLLAMA, "gemma4:12b")
    page.on_show()
    qtbot.waitUntil(lambda: page.task is None, timeout=10000)
    assert page.done_text == "Text-KI: Ollama auf diesem Rechner, gemma4:12b."


def test_enter_clicks_the_focused_button(qtbot, make_services, quiet_machine, monkeypatch):
    """Test von 8b: Enter auf "Verbindung testen" tat nichts."""
    from PySide6.QtCore import Qt
    from cockpit.ui import ai_dialogs
    services = make_services()
    services.ai_tools.add(TEXT, OLLAMA, "gemma4:12b")
    dialog = manager(qtbot, services)
    clicked = []
    monkeypatch.setattr(ai_dialogs.AIManagerDialog, "test_current",
                        lambda self: clicked.append("test"))
    dialog.test_button.clicked.disconnect()
    dialog.test_button.clicked.connect(dialog.test_current)
    dialog.show()
    dialog.list.setCurrentRow(2)
    dialog.test_button.setFocus()
    qtbot.keyClick(dialog.test_button, Qt.Key.Key_Return)
    assert clicked == ["test"]
    assert dialog.isVisible()                                   # kein anderer Knopf ausgelöst
