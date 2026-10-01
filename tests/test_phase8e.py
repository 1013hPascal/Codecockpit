"""Teilschritt 8e: KI-Hilfe. Die KI ist eine Attrappe."""
from __future__ import annotations

from cockpit.core import paths
from cockpit.features.ai_help import knowledge
from cockpit.features.ai_help.manifest import MANIFEST
from cockpit.features.dictation.manifest import MANIFEST as DICTATION
from tests.conftest import FakeAI, said

GUIDE = """# Branches verstehen

Einleitung zu Branches.

## Neuer Branch

Auf Code, main die Aktion Neuer Branch wählen.

## Pull Requests

Pull Requests stehen unter Code.
"""


class CapturingAI:
    max_chars = 8000

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.prompts: list[tuple[str, str]] = []

    def ask(self, prompt, system="", cancel=None, max_tokens=None):
        self.prompts.append((prompt, system))
        return self.answer


# -- Wissen ---------------------------------------------------------------------------------------
def test_guides_are_split_into_sections(tmp_path):
    (tmp_path / "branches.md").write_text(GUIDE, encoding="utf-8")
    sections = knowledge.guide_sections(tmp_path)
    assert [s.title for s in sections] == ["Anleitung Branches verstehen",
                                           "Anleitung Branches verstehen, Neuer Branch",
                                           "Anleitung Branches verstehen, Pull Requests"]


def test_select_prefers_matching_sections_within_the_limit():
    sections = [knowledge.Section("Tastenkürzel", "F1 zeigt die Liste.", always=True),
                knowledge.Section("Exe", "Exe aus dem Code erstellen."),
                knowledge.Section("Branch", "Neuer Branch auf Code, main."),
                knowledge.Section("Groß", "Branch " * 2000)]
    chosen = knowledge.select("Wie lege ich einen neuen Branch an?", sections, 500)
    assert [s.title for s in chosen] == ["Tastenkürzel", "Branch"]   # Groß passt nicht hinein


def test_ask_sends_question_and_knowledge_and_cleans_the_answer():
    ai = CapturingAI("**Schritt 1:** Wählen Sie `Neuer Branch`.")
    sections = [knowledge.Section("Branch", "Neuer Branch auf Code, main.")]
    answer = knowledge.ask(ai, "Wie lege ich einen Branch an?", sections)
    prompt, system = ai.prompts[0]
    assert "Wie lege ich einen Branch an?" in prompt and "Neuer Branch auf Code" in prompt
    assert "Erfinde nichts." in system
    assert answer == "Schritt 1: Wählen Sie Neuer Branch."


def test_introductions_are_part_of_the_knowledge():
    sections = knowledge.intro_sections([DICTATION, MANIFEST])
    assert sections[0].title == "Feature Spracheingabe" and "Strg+D" in sections[0].text
    assert "Im Menü Hilfe unter KI-Hilfe" in sections[1].text
    assert (paths.resource_dir() / "anleitungen").is_dir()


# -- Oberfläche -----------------------------------------------------------------------------------
def window(qtbot, services):
    from tests.test_phase10f import window as make_window
    return make_window(qtbot, services)


def test_ui_sections_describe_menus_and_actions(qtbot, make_services):
    from cockpit.ui.ai_help_dialog import ui_sections
    win = window(qtbot, make_services([MANIFEST]))
    sections = {s.title: s for s in ui_sections(win)}
    assert "KI-Hilfe … (Shift+F1)" in sections["Menüs"].text
    assert sections["Menüs"].always and sections["Tastenkürzel (F1)"].always
    code = sections["Aktionen auf Code bzw. Main-Branch und auf einer Branch-Zeile"].text
    assert "Verlauf …" in code and "Änderungen auf GitHub hochladen …" in code


def test_dialog_asks_and_shows_one_sentence_per_line(qtbot, make_services):
    from PySide6.QtCore import Qt
    from cockpit.ui.ai_help_dialog import AIHelpDialog
    services = make_services([MANIFEST], ai=FakeAI(answers=[
        "Wählen Sie auf Code die Aktion **Branches**. Dann Tab bis Neuer Branch."]))
    win = window(qtbot, services)
    dialog = AIHelpDialog(win)
    qtbot.addWidget(dialog)
    dialog.question.setText("Wie lege ich einen Branch an?")
    qtbot.keyClick(dialog.question, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: dialog.task is None, timeout=5000)
    lines = [dialog.answer.item(r).text() for r in range(dialog.answer.count())]
    assert lines == ["Wählen Sie auf Code die Aktion Branches.", "Dann Tab bis Neuer Branch."]
    assert said("Antwort da.")


def test_help_without_ai_says_why(qtbot, make_services, monkeypatch):
    from cockpit.ui import ai_help_dialog
    shown = []
    monkeypatch.setattr(ai_help_dialog, "show_error", lambda parent, title, text, *a:
                        shown.append(text))
    win = window(qtbot, make_services([MANIFEST]))
    ai_help_dialog.open_help(win)
    assert shown and "KI" in shown[0]
