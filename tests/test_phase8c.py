"""Phase 8c: Feature KI-Assistent und die Gruppe "KI" in der Feature-Verwaltung.

Keine echte KI: FakeAI antwortet mit festen Texten. Alle Geheimnisse sind erfunden.
"""
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from cockpit.core import sync
from cockpit.core.ai_tools import OLLAMA, TEXT, TextAI
from cockpit.features.ai_assistant import context, suggest
from cockpit.features.ai_assistant.manifest import MANIFEST as ASSISTANT
from cockpit.features.terminal_explain.manifest import MANIFEST as EXPLAIN
from tests.conftest import FakeAI, make_project, said
from tests.test_phase5a import sh
from tests.test_phase5b import write

FAKE_TOKEN = "ghp_ErfundenFuerDenKiAssistenten0123456789"


class Recorder(FakeAI):
    """Merkt sich, was die KI bekommt."""

    def complete(self, messages, *, model, system="", schema=None, max_tokens=None,
                 cancel=None):
        self.system, self.request = system, messages[0]["content"]
        return super().complete(messages, model=model)


def repo(tmp_path: Path) -> Path:
    code = tmp_path / "Projekt" / "Code"
    code.mkdir(parents=True)
    sh(code, "init", "-q")
    write(code, "main.py", "import os\nfrom pathlib import Path\nprint('alt')\n")
    write(code, "README.md", "# Projekt\n\nLiest PDF-Dateien vor.\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Anfang")
    return code


# -- Antwort lesen --------------------------------------------------------------------------------
def test_parse_removes_labels_quotes_and_markdown():
    found = suggest.parse('**Zusammenfassung:** „Suche ergänzt“\n\n- Neue Suche.\n- Schneller.')
    assert found.summary == "Suche ergänzt" and found.details == "Neue Suche.\nSchneller."
    assert suggest.parse("").summary == ""
    assert len(suggest.parse("x" * 300).summary) == suggest.MAX_SUMMARY


# -- Was die KI bekommt ---------------------------------------------------------------------------
def test_commit_context_hides_secrets(tmp_path):
    code = repo(tmp_path)
    write(code, "main.py", f"import os\nTOKEN = '{FAKE_TOKEN}'\nprint('neu')\n")
    write(code, ".env", "PASSWORT=geheim12345\n")
    write(code, "suche.py", "def suche():\n    return 1\n")
    text = context.commit_context(code, 8000)
    assert "Geänderte Dateien:" in text and "main.py, geändert" in text
    assert "+print('neu')" in text and context.REMOVED in text
    assert FAKE_TOKEN not in text
    assert "geheim12345" not in text and "Neue Datei .env: Inhalt nicht gesendet" in text
    assert "Neue Datei suche.py:\ndef suche():" in text


def test_commit_context_respects_the_limit(tmp_path):
    code = repo(tmp_path)
    write(code, "gross.py", "x = 1\n" * 5000)
    assert len(context.commit_context(code, 1500)) <= 1500


def test_filter_diff_drops_confidential_files():
    diff = ("diff --git a/.env b/.env\n+KEY=1\ndiff --git a/a.py b/a.py\n+print(1)\n"
            "diff --git a/daten.db b/daten.db\nBinary")
    assert context.filter_diff(diff) == ("Datei .env: Inhalt nicht gesendet, vertraulich.\n"
                                         "diff --git a/a.py b/a.py\n+print(1)\n"
                                         "Datei daten.db: Inhalt nicht gesendet, vertraulich.")


def test_pull_request_context(tmp_path):
    code = repo(tmp_path)
    sh(code, "switch", "-q", "-c", "suche")
    write(code, "suche.py", "def suche():\n    return 1\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Suche ergänzt")
    text = context.pull_request_context(code, "suche", "main", 8000)
    assert text.startswith("Branch suche soll nach main.")
    assert "Suche ergänzt" in text and "A\tsuche.py" in text and "+def suche():" in text


def test_project_context(tmp_path):
    code = repo(tmp_path)
    write(code, ".env", "KEY=1\n")
    write(code, "requirements.txt", "PySide6==6.11.2\n")
    text = context.project_context(code, "PDF-Leser", 8000)
    assert text.startswith("Projekt: PDF-Leser")
    assert "Liest PDF-Dateien vor." in text and "Importierte Module: os, pathlib" in text
    assert "PySide6==6.11.2" in text and ".env" not in text


# -- Vorschläge -----------------------------------------------------------------------------------
def test_commit_suggestion_in_the_chosen_language(tmp_path):
    code = repo(tmp_path)
    write(code, "main.py", "print('neu')\n")
    provider = Recorder(answers=["Ausgabe geändert\n\nMain gibt jetzt neu aus."])
    found = suggest.commit(TextAI(provider, "m", "Test", 8000), code, "Englisch")
    assert (found.summary, found.details) == ("Ausgabe geändert", "Main gibt jetzt neu aus.")
    assert "Schreiben Sie den Vorschlag auf Englisch." in provider.system
    assert "main.py, geändert" in provider.request


def test_description_is_one_short_sentence(tmp_path):
    code = repo(tmp_path)
    answer = "Ein Programm, das PDF-Dateien vorliest.\nFür blinde Menschen."
    found = suggest.description(TextAI(FakeAI(answers=[answer]), "m", "T", 8000), code, "P",
                                "Deutsch")
    assert found.summary == "Ein Programm, das PDF-Dateien vorliest. Für blinde Menschen."
    long = TextAI(FakeAI(answers=["Wort " * 200]), "m", "T", 8000)
    assert len(suggest.description(long, code, "P", "Deutsch").summary) <= 350


def test_feature_manifest():
    assert ASSISTANT.requires_services == ("ai",) and ASSISTANT.enabled_by_default
    assert [s.key for s in ASSISTANT.settings] == ["tool", "language"]
    from cockpit.core.features.registry import FeatureRegistry
    found = FeatureRegistry.discover().get("ai_assistant")
    assert found.introduction_text().startswith("# KI-Assistent")
    assert not ASSISTANT.problems()


# -- Knopf "Vorschlag der KI" ---------------------------------------------------------------------
def with_assistant(make_services, projects_root):
    services = make_services([ASSISTANT, EXPLAIN])
    services.projects.add(make_project(projects_root, "Tagebuch"))
    return services, services.projects.all()[0]


def test_source_only_with_active_feature(make_services, projects_root):
    from cockpit.ui import ai_suggest
    services, project = with_assistant(make_services, projects_root)
    assert ai_suggest.for_commit(services, project) is None          # keine KI eingerichtet
    services.ai_tools.add(TEXT, OLLAMA, "gemma4:12b")
    assert ai_suggest.for_commit(services, project) is not None
    services.features.disable("ai_assistant", project)
    assert ai_suggest.for_commit(services, project) is None


def fixed_source(answer: str = "Suche ergänzt\n\nNeue Suche in PDFs.", gate=None):
    from cockpit.ui.ai_suggest import SuggestionSource
    ai = TextAI(FakeAI(), "m", "Test", 8000)

    def make(ai, cancel):
        if gate is not None:
            gate.wait(10)
            if cancel.is_set():
                from cockpit.core.errors import Cancelled
                raise Cancelled()
        return suggest.parse(answer)
    return SuggestionSource(lambda parent: ai, make)


def commit_dialog(qtbot, source, tmp_path):
    from cockpit.ui.sync_dialogs import CommitDialog
    dialog = CommitDialog("Änderungen hochladen", sync.Changes(modified=["main.py"]), None,
                          source=source)
    qtbot.addWidget(dialog)
    return dialog


def test_commit_dialog_fills_the_fields(qtbot, tmp_path):
    from cockpit.ui import ai_suggest
    dialog = commit_dialog(qtbot, fixed_source(), tmp_path)
    button = dialog.suggest_button
    assert button.text() == "&Vorschlag der KI"
    dialog.show()
    button.click()
    qtbot.waitUntil(lambda: not button.busy, timeout=10000)
    assert dialog.summary.text() == "Suche ergänzt"
    assert dialog.details.toPlainText() == "Neue Suche in PDFs."
    assert said(ai_suggest.WORKING) and said(ai_suggest.INSERTED)
    assert dialog.focusWidget() is dialog.summary


def test_commit_dialog_tab_order(qtbot, tmp_path):
    from PySide6.QtCore import Qt
    dialog = commit_dialog(qtbot, fixed_source(), tmp_path)
    dialog.show()
    dialog.activateWindow()
    dialog.details.setFocus()
    qtbot.keyClick(dialog.details, Qt.Key.Key_Tab)
    assert dialog.focusWidget() is dialog.suggest_button
    assert commit_dialog(qtbot, None, tmp_path).suggest_button is None


def test_escape_cancels_the_suggestion_first(qtbot, tmp_path):
    from cockpit.ui import ai_suggest
    gate = threading.Event()
    dialog = commit_dialog(qtbot, fixed_source(gate=gate), tmp_path)
    dialog.show()
    dialog.suggest_button.click()
    assert dialog.suggest_button.busy
    dialog.reject()                                              # Escape
    assert dialog.isVisible() and said(ai_suggest.CANCELLED)
    gate.set()
    qtbot.waitUntil(lambda: not dialog.suggest_button.busy, timeout=10000)
    assert dialog.summary.text() == ""                           # nichts eingefügt
    dialog.reject()
    assert not dialog.isVisible()


def test_reason_when_no_suggestion_is_possible(qtbot, tmp_path, monkeypatch):
    from cockpit.ui import ai_suggest
    from cockpit.ui.ai_suggest import SuggestionSource
    errors = []
    monkeypatch.setattr(ai_suggest, "show_error", lambda parent, title, text, details="":
                        errors.append(text))
    source = SuggestionSource(lambda parent: "Es ist keine Text-KI eingerichtet.",
                              lambda ai, cancel: None)
    dialog = commit_dialog(qtbot, source, tmp_path)
    dialog.suggest_button.click()
    assert errors == ["Es ist keine Text-KI eingerichtet."]
    assert not dialog.suggest_button.busy


def test_pull_request_dialog_uses_the_chosen_base(qtbot, make_services, projects_root,
                                                  monkeypatch):
    from cockpit.ui import ai_suggest
    from cockpit.ui.pull_request_dialogs import CreatePullRequestDialog
    services, project = with_assistant(make_services, projects_root)
    services.ai_tools.add(TEXT, OLLAMA, "gemma4:12b")
    seen = []
    monkeypatch.setattr(suggest, "pull_request", lambda ai, code_dir, head, base, language,
                        cancel: seen.append((head, base, language)) or
                        suggest.Suggestion("Titel", "Text."))
    monkeypatch.setattr(services.ai_tools, "provider", lambda tool: FakeAI())
    holder = []
    source = ai_suggest.for_pull_request(services, project, "suche",
                                         lambda: holder[0].base_box.currentText())
    dialog = CreatePullRequestDialog("suche", ["main", "test"], "main", "", "", [], "", None,
                                     source=source)
    holder.append(dialog)
    qtbot.addWidget(dialog)
    dialog.base_box.setCurrentIndex(1)
    dialog.suggest_button.click()
    qtbot.waitUntil(lambda: not dialog.suggest_button.busy, timeout=10000)
    assert seen == [("suche", "test", "Deutsch")]
    assert dialog.title_edit.text() == "Titel" and dialog.body_edit.toPlainText() == "Text."


def test_upload_dialog_fills_the_short_description(qtbot):
    from cockpit.ui.upload_dialogs import UploadDialog
    dialog = UploadDialog("Hochladen", "pdf", "GitHub", "tester", [], True, "MIT",
                          source=fixed_source("Liest PDF-Dateien vor."))
    qtbot.addWidget(dialog)
    from PySide6.QtCore import Qt
    description = dialog.form.fields["description"].focus
    dialog.show()
    dialog.activateWindow()
    description.setFocus()
    qtbot.keyClick(description, Qt.Key.Key_Tab)
    assert dialog.focusWidget() is dialog.suggest_button
    dialog.suggest_button.click()
    qtbot.waitUntil(lambda: not dialog.suggest_button.busy, timeout=10000)
    assert dialog.form.fields["description"].get() == "Liest PDF-Dateien vor."


# -- Gruppe KI in der Feature-Verwaltung ----------------------------------------------------------
def rows(listing) -> list[str]:
    return [listing.item(i).text() for i in range(listing.count())]


def test_ai_features_are_grouped(qtbot, make_services, projects_root):
    from cockpit.features.branches_prs.manifest import MANIFEST as BRANCHES
    from cockpit.ui.features_dialogs import GlobalFeaturesDialog
    services = make_services([ASSISTANT, EXPLAIN, BRANCHES])
    dialog = GlobalFeaturesDialog(services)
    qtbot.addWidget(dialog)
    lines = rows(dialog.list)
    assert lines[0].startswith("Branches und Pull Requests, eingeschaltet")
    assert lines[1] == "KI, 2 von 2 KI-Features eingeschaltet"
    assert dialog.sub.isHidden()
    dialog.list.setCurrentRow(1)
    assert not dialog.sub.isHidden() and dialog.sub.accessibleName() == "KI-Features"
    assert rows(dialog.sub)[0].startswith("KI-Assistent, eingeschaltet")
    assert rows(dialog.info)[0] == "KI-Feature KI-Assistent."
    dialog.sub.setCurrentRow(1)
    assert rows(dialog.info)[0] == "KI-Feature Terminal-Erklärung."
    from PySide6.QtCore import Qt
    dialog.sub.item(1).setCheckState(Qt.CheckState.Unchecked)
    assert rows(dialog.list)[1] == "KI, 1 von 2 KI-Features eingeschaltet"
    assert rows(dialog.sub)[1] == "Terminal-Erklärung, ausgeschaltet"
    dialog.save()
    assert not services.features.globally_enabled("terminal_explain")
    assert services.features.globally_enabled("ai_assistant")


def test_select_ai_feature_opens_the_group(qtbot, make_services):
    from cockpit.ui.features_dialogs import GlobalFeaturesDialog
    services = make_services([ASSISTANT, EXPLAIN])
    dialog = GlobalFeaturesDialog(services)
    qtbot.addWidget(dialog)
    dialog.select("terminal_explain")
    assert dialog.group_selected() and dialog.current().id == "terminal_explain"


def test_project_features_are_grouped_too(qtbot, make_services, projects_root, monkeypatch):
    from PySide6.QtCore import Qt
    from cockpit.ui import features_dialogs
    services, project = with_assistant(make_services, projects_root)
    services.ai_tools.add(TEXT, OLLAMA, "gemma4:12b")
    dialog = features_dialogs.ProjectFeaturesDialog(services, project)
    qtbot.addWidget(dialog)
    assert rows(dialog.list) == ["KI, 2 von 2 KI-Features eingeschaltet"]
    assert rows(dialog.sub) == ["KI-Assistent, aktiv", "Terminal-Erklärung, aktiv"]
    dialog.sub.item(0).setCheckState(Qt.CheckState.Unchecked)
    monkeypatch.setattr(features_dialogs, "confirm", lambda *a, **k: True)
    dialog.save()
    assert services.features.project_features(project) == {"terminal_explain"}


def test_single_ai_feature_is_not_grouped(qtbot, make_services):
    from cockpit.ui.features_dialogs import GlobalFeaturesDialog
    dialog = GlobalFeaturesDialog(make_services([EXPLAIN]))
    qtbot.addWidget(dialog)
    assert rows(dialog.list)[0].startswith("Terminal-Erklärung")
    assert dialog.sub.count() == 0


@pytest.mark.parametrize("language", ["Deutsch", "Englisch"])
def test_language_setting(make_services, language):
    services = make_services([ASSISTANT])
    services.features.set_setting("ai_assistant", "language", language)
    assert services.features.setting("ai_assistant", "language") == language
