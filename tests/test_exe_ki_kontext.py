"""Mehr Kontext für die KI beim Exe-Bau (Rückmeldung des Nutzers vom 14.10.2026).

Beim Zug-um-Zug-Streckenfinder meldete die Exe "CSV-Datei nicht gefunden: ..._internal\\strecken.csv".
Die Meldung kam aus engine.py, die KI sah aber nur gui.py und änderte dort etwas Wirkungsloses.
1. Die KI bekommt den ganzen Code, wenn er passt, sonst die Stellen aus der Fehlermeldung.
2. Auch der Chat bekommt den Code und das Ende der Ausgabe mit der Meldung der Exe.
3. Nach "Problem mit KI lösen" sagt die Zusammenfassung zuerst, was beim letzten Versuch das
   Problem war, und dann, wie die KI es löst.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

from cockpit.core import exe
from cockpit.core.projects import Project
from cockpit.features.exe_build import ai_fix
from cockpit.ui import exe_wizard
from cockpit.ui.exe_chat import ExeChat

ENGINE = '''import sys
from pathlib import Path


def resource_path(rel_path):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / rel_path


def build_graph_from_csv(csv_datei=None):
    csv_path = Path(csv_datei) if csv_datei else resource_path("strecken.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV-Datei nicht gefunden: {csv_path}")
'''
GUI = "from engine import build_graph_from_csv\n\nG = build_graph_from_csv()\n"
ERROR = ("Die Exe ist gebaut, hat den Test aber nicht bestanden.\n"
         "FileNotFoundError: CSV-Datei nicht gefunden: C:\\Release\\_internal\\strecken.csv")


def streckenfinder(tmp_path) -> Path:
    code = tmp_path / "Repository" / "main"
    code.mkdir(parents=True)
    (code / "engine.py").write_text(ENGINE, encoding="utf-8")
    (code / "gui.py").write_text(GUI, encoding="utf-8")
    (code / "strecken.csv").write_text("a;b\n", encoding="utf-8")
    return code


# -- 1. Code für die KI -------------------------------------------------------------------------
def test_small_projects_go_whole_start_file_first(tmp_path):
    code = streckenfinder(tmp_path)
    said = []
    text, files = ai_fix.code_for_ai(code, "gui.py", ERROR, 20000, said.append)
    assert files == ["gui.py", "engine.py"]
    assert text.startswith("--- gui.py ---\n") and "--- engine.py ---" in text
    assert 'raise FileNotFoundError(f"CSV-Datei nicht gefunden: {csv_path}")' in text
    assert said == ["Für die KI gelesen: gui.py", "Für die KI gelesen: engine.py"]


def test_secrets_never_go_along(tmp_path):
    code = streckenfinder(tmp_path)
    fake = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"           # erfunden
    (code / "gui.py").write_text(f'TOKEN = "{fake}"\n' + GUI, encoding="utf-8")
    text, _files = ai_fix.code_for_ai(code, "gui.py", "", 20000)
    assert fake not in text and "build_graph_from_csv()" in text


def test_the_message_finds_its_line_without_traceback(tmp_path):
    code = streckenfinder(tmp_path)
    found = ai_fix.message_excerpts(code, ERROR)
    assert {name for name, _text in found} == {"engine.py"}
    assert "CSV-Datei nicht gefunden" in found[0][1]
    assert ai_fix.message_excerpts(code, "") == []
    assert ai_fix.message_excerpts(code, "ganz anderer Fehler") == []


def test_big_files_come_as_excerpts(tmp_path):
    code = streckenfinder(tmp_path)
    filler = "".join(f"# Zeile {n}\n" for n in range(400))
    (code / "engine.py").write_text(filler + ENGINE + filler, encoding="utf-8")
    text, files = ai_fix.code_for_ai(code, "gui.py", ERROR, 1500)
    assert files == ["gui.py", "engine.py"]
    assert "--- engine.py, Stelle aus der Fehlermeldung ---" in text
    assert "CSV-Datei nicht gefunden" in text and len(text) <= 1500


class FixAI:
    max_chars = 40000
    name = "Test-KI"

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.prompts: list[str] = []

    def ask(self, prompt, system="", cancel=None, max_tokens=None):
        self.prompts.append(prompt)
        self.system = system
        return self.answer


ANSWER = """PROBLEM: engine.py sucht strecken.csv über sys._MEIPASS im Ordner _internal.
ZUSAMMENFASSUNG: engine.py sucht die Datei jetzt neben der Exe.

AENDERUNG: engine.py
GRUND: Die Datei liegt neben der Exe.
ALT:
<<<
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
>>>
NEU:
<<<
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
>>>
"""


def test_ask_sends_all_files_and_reads_the_problem(tmp_path):
    code = streckenfinder(tmp_path)
    ai = FixAI(ANSWER)
    proposal = ai_fix.ask(ai, "Streckenfinder", code, exe.BuildSettings("gui.py", "Zug"), "",
                          error=ERROR)
    assert "--- engine.py ---" in ai.prompts[0] and "PROBLEM:" in ai.system
    assert proposal.problem.startswith("engine.py sucht strecken.csv")
    assert proposal.summary == "engine.py sucht die Datei jetzt neben der Exe."
    assert [c.file for c in proposal.usable] == ["engine.py"]
    plain = ai_fix.ask(ai, "Streckenfinder", code, exe.BuildSettings("gui.py", "Zug"), "")
    assert plain.problem == ""                      # ohne Fehler kein Problem


# -- 2. Chat ------------------------------------------------------------------------------------
def test_chat_prompt_has_code_and_the_end_of_the_output():
    ai = FixAI("Die Datei fehlt.")
    content = [f"pip Zeile {n}" for n in range(800)] + ["CSV-Datei nicht gefunden"]
    ai_fix.ask_chat(ai, "Zug", "Test nicht bestanden", content, [], "Warum?", code="--- x ---")
    prompt = ai.prompts[0]
    assert "CSV-Datei nicht gefunden" in prompt and "pip Zeile 0\n" not in prompt
    assert "Code des Projekts" in prompt and "--- x ---" in prompt
    assert "Code des Projekts" in ai.system


def test_chat_widget_sends_the_code(qtbot, tmp_path, monkeypatch, make_services):
    code = streckenfinder(tmp_path)
    ai = FixAI("In engine.py steht _MEIPASS.")
    widget = ExeChat(make_services(), "Zug", "Test nicht bestanden", lambda: ERROR.splitlines(),
                     None, code, "gui.py")
    qtbot.addWidget(widget)
    monkeypatch.setattr(widget, "_prepare_ai", lambda: ai)
    widget.question.setText("Siehst du den Code?")
    qtbot.keyClick(widget.question, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: widget.task is None and bool(widget.history), timeout=5000)
    assert "--- engine.py ---" in ai.prompts[0] and "--- gui.py ---" in ai.prompts[0]


# -- 3. Problem und Lösung in der Zusammenfassung -------------------------------------------------
def wizard_with(tmp_path, proposal, error):
    code = streckenfinder(tmp_path)
    wizard = exe_wizard.ExeWizard.__new__(exe_wizard.ExeWizard)
    wizard.project = Project(1, "Zug", tmp_path, code, tmp_path / "Release")
    wizard.settings = exe.BuildSettings("gui.py", "Zug")
    wizard.folder, wizard.proposal, wizard.lines, wizard.error = code, proposal, [], error
    return wizard


def test_summary_names_problem_and_solution(tmp_path):
    proposal = ai_fix.Proposal(summary="engine.py sucht die Datei jetzt neben der Exe.",
                               problem="engine.py sucht strecken.csv im Ordner _internal.",
                               changes=[ai_fix.Change("engine.py", "Grund", "alt", "neu")])
    lines, changes = wizard_with(tmp_path, proposal, ERROR).summary_lines()
    assert lines[0] == ("Problem beim letzten Versuch: engine.py sucht strecken.csv im Ordner "
                        "_internal.")
    assert lines[1] == ("So löst die KI es: engine.py sucht die Datei jetzt neben der Exe. Die KI "
                        "schlägt 1 Änderung vor. Sie kommen mit „Neuer Versuch, Exe zu bauen“ in "
                        "den Branch.")
    assert changes[:3] == [None, None, proposal.changes[0]]


def test_summary_without_ai_problem_uses_the_error_line(tmp_path):
    lines, _ = wizard_with(tmp_path, ai_fix.Proposal(summary="Keine Änderung am Code nötig."),
                           ERROR).summary_lines()
    assert lines[0] == ("Problem beim letzten Versuch: FileNotFoundError: CSV-Datei nicht "
                        "gefunden: C:\\Release\\_internal\\strecken.csv")
    assert lines[1] == ("Die KI findet keine Änderung, die das Problem löst. Keine Änderung am "
                        "Code nötig.")


def test_first_run_summary_is_unchanged(tmp_path):
    proposal = ai_fix.Proposal(summary="Pfad angepasst.",
                               changes=[ai_fix.Change("engine.py", "Grund", "alt", "neu")])
    lines, _ = wizard_with(tmp_path, proposal, "").summary_lines()
    assert lines[0] == ("Die KI schlägt 1 Änderung vor. Sie kommen mit „Exe erstellen“ in den "
                        "Branch. Pfad angepasst.")


def test_summary_chat_sees_the_last_error(qtbot, make_services, tmp_path):
    project = Project(1, "Zug", tmp_path, tmp_path, None)
    dialog = exe_wizard.SummaryDialog(project, 4, ["Bereit."], [None], make_services([]),
                                      error=ERROR)
    qtbot.addWidget(dialog)
    assert dialog.lines() == ["Bereit.", "Fehler beim letzten Versuch:"] + ERROR.splitlines()
