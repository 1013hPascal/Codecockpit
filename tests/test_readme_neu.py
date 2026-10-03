"""README mit KI schreiben, bearbeiten, übersetzen und aus einer Datei übernehmen (Wunsch des
Nutzers vom 03.10.2026). Die KI ist eine Attrappe, alle Geheimnisse sind erfunden."""
from __future__ import annotations

import pytest

from cockpit.core import backups, git
from cockpit.core.actions import ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.features.readme import plan
from tests.test_phase9 import ScriptedAI, project_with

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

DRAFT = "# Rechner\n\nRechnet schnell.\n\n## Features\n\n- plus"
FAKE_TOKEN = "ghp_" + "Erfunden" + "a" * 30          # erfunden, nur für den Test


def readme_project(tmp_path, projects_root, make_services, files=None, languages=()):
    services, project, _bare = project_with(tmp_path, projects_root, make_services, ["readme"],
                                            {"main.py": "print(1)\n", **(files or {})})
    services.features.set_setting("readme", "languages", list(languages))
    return services, project


def read(project, name="README.md"):
    return (project.code_dir / name).read_text(encoding="utf-8")


# -- Kern -----------------------------------------------------------------------------------------
def test_compose_writes_the_whole_readme(tmp_path, projects_root, make_services):
    services, project = readme_project(tmp_path, projects_root, make_services)
    services.features.set_setting("readme", "sections", ["Funktionen", "Lizenz"])
    (project.code_dir / "LICENSE").write_text("MIT License\n", encoding="utf-8")
    ai = ScriptedAI("```markdown\n" + DRAFT + "\n```")
    text = plan.compose(services, project, ai, notes="Für blinde Nutzer.",
                        info="Datei notizen.txt:\nRechnet auch Brüche.")
    assert text == DRAFT                                  # Code-Zaun entfernt
    prompt = ai.prompts[0]
    assert "- Features\n- License" in prompt and "Englisch" in prompt
    assert "License: MIT. See [LICENSE](LICENSE)" in prompt          # fertiger Baustein
    assert "Für blinde Nutzer." in prompt and "Rechnet auch Brüche." in prompt
    assert "main.py" in prompt                                        # Auszüge aus dem Code


def test_compose_revises_with_the_wishes(tmp_path, projects_root, make_services):
    services, project = readme_project(tmp_path, projects_root, make_services)
    ai = ScriptedAI("# Rechner\n\nRechnet sehr schnell.")
    text = plan.compose(services, project, ai, current=DRAFT, wishes="Kürzer bitte.")
    assert text == "# Rechner\n\nRechnet sehr schnell."
    assert "Kürzer bitte." in ai.prompts[0] and "Bisherige README:\n" + DRAFT in ai.prompts[0]


def test_compose_without_answer_is_an_error(tmp_path, projects_root, make_services):
    services, project = readme_project(tmp_path, projects_root, make_services)
    with pytest.raises(CockpitError):
        plan.compose(services, project, ScriptedAI("  "))


def test_info_files_without_secrets(tmp_path):
    notes = tmp_path / "notizen.txt"
    notes.write_text(f"Rechnet Brüche.\ntoken = {FAKE_TOKEN}\n", encoding="utf-8")
    env = tmp_path / ".env"
    env.write_text("KEY=1\n", encoding="utf-8")
    image = tmp_path / "bild.png"
    image.write_bytes(b"\x89PNG\0\0\0")
    text, skipped = plan.info_text([notes, env, image, tmp_path / "fehlt.txt"], 4000)
    assert "Datei notizen.txt:\nRechnet Brüche." in text
    assert FAKE_TOKEN not in text and "KEY=1" not in text
    assert skipped == [".env", "bild.png", "fehlt.txt"]


def test_save_with_one_language_keeps_the_text_and_makes_a_backup(tmp_path, projects_root,
                                                                   make_services, home):
    services, project = readme_project(tmp_path, projects_root, make_services,
                                       {"README.md": "# Alt\n"})
    backup = plan.save_files(services, project, {"README.md": DRAFT})
    assert read(project) == DRAFT + "\n"
    assert (backup / "README.md").read_text(encoding="utf-8") == "# Alt\n"
    assert "README vor dem Speichern" in backup.name
    assert plan.save_files(services, project, {"README.md": DRAFT}) is None   # unverändert


def test_translations_get_language_links(tmp_path, projects_root, make_services, home):
    services, project = readme_project(tmp_path, projects_root, make_services,
                                       languages=["Deutsch"])
    plan.save_files(services, project, {"README.md": DRAFT})
    assert read(project) == DRAFT + "\n"                  # noch keine Übersetzung: keine Links
    assert plan.missing_translations(services, project) == ["de"]
    ai = ScriptedAI("```\n# Rechner\n\nRechnet schnell.\n\n## Funktionen\n\n- plus\n```")
    translations = plan.translate(services, project, ai, read(project))
    assert translations == [("README.de.md", "de",
                             "# Rechner\n\nRechnet schnell.\n\n## Funktionen\n\n- plus")]
    assert "Deutsch" in ai.prompts[0] and DRAFT in ai.prompts[0]
    backup = plan.save_files(services, project, {"README.de.md": translations[0][2]})
    assert read(project).startswith("# Rechner\n\nEnglish | [Deutsch](README.de.md)\n\n"
                                    "Rechnet schnell.\n\n## Features")
    assert "[English](README.md) | Deutsch" in read(project, "README.de.md")
    assert (backup / "README.md").is_file() and not (backup / "README.de.md").exists()
    assert plan.missing_translations(services, project) == []
    again = ScriptedAI("# Rechner")
    plan.translate(services, project, again, read(project))
    assert "English |" not in again.prompts[0]           # Links gehen nicht mit zur KI
    assert plan.translate(services, project, again, read(project), only=["fr"]) == []


def test_import_file(tmp_path, projects_root, make_services, home):
    services, project = readme_project(tmp_path, projects_root, make_services)
    source = tmp_path / "Beschreibung.md"
    source.write_bytes("﻿# Rechner\r\n\r\nRechnet.\r\n".encode("utf-8"))
    assert plan.import_file(services, project, source) is None
    assert read(project) == "# Rechner\n\nRechnet.\n"
    (tmp_path / "bild.png").write_bytes(b"\x89PNG\0")
    (tmp_path / "alt.txt").write_bytes("Größe".encode("cp1252"))
    for name in ("bild.png", "alt.txt", "fehlt.md"):
        with pytest.raises(CockpitError):
            plan.import_file(services, project, tmp_path / name)
    assert read(project) == "# Rechner\n\nRechnet.\n"


# -- Dialoge --------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def no_boxes(monkeypatch):
    """Keine echten Meldungsfenster. Beim Schließen eines geänderten Dialogs fragt das Cockpit
    "Verwerfen?", das würde den Test anhalten. Fehlermeldungen lassen den Test scheitern."""
    from cockpit.ui import readme_flow

    def error(parent, title, message, details=""):
        raise AssertionError(f"{title}: {message} {details}")

    monkeypatch.setattr(readme_flow, "show_error", error)
    monkeypatch.setattr(readme_flow, "confirm", lambda *args, **kwargs: True)


@pytest.fixture
def scripted(monkeypatch):
    """ai_ui.prepare gibt die Attrappe zurück."""
    from cockpit.ui import ai_ui
    holder = {}

    def use(*answers):
        holder["ai"] = ScriptedAI(*answers)
        monkeypatch.setattr(ai_ui, "prepare", lambda *args, **kwargs: holder["ai"])
        return holder["ai"]
    return use


def test_write_dialog_drafts_revises_and_finishes(qtbot, tmp_path, projects_root, make_services,
                                                  scripted):
    from cockpit.ui import readme_flow
    services, project = readme_project(tmp_path, projects_root, make_services)
    ai = scripted(DRAFT, "# Rechner\n\nKürzer.")
    notes = tmp_path / "notizen.txt"
    notes.write_text("Rechnet Brüche.", encoding="utf-8")
    dialog = readme_flow.WriteDialog(services, project)
    qtbot.addWidget(dialog)
    dialog.show()
    assert not dialog.text.isVisible() and not dialog.wishes.isVisible()
    assert dialog.files.accessibleName() == "Dateien mit Infos zum Programm"
    dialog.finish()
    assert dialog.result() == 0                          # ohne Text bleibt der Dialog offen
    dialog.add_files([str(notes), str(notes)])
    assert dialog.files.count() == 1
    dialog.notes.setPlainText("Für blinde Nutzer.")
    dialog.ai_button.click()
    qtbot.waitUntil(lambda: dialog.task is None and bool(dialog.readme_text), timeout=10000)
    assert dialog.readme_text == DRAFT and dialog.text.isVisible() and dialog.wishes.isVisible()
    assert "Rechnet Brüche." in ai.prompts[0] and "Für blinde Nutzer." in ai.prompts[0]
    assert dialog.wishes.accessibleName() == "Verbesserungsvorschläge für die KI"
    dialog.wishes.setPlainText("Kürzer.")
    dialog.ai_button.click()
    qtbot.waitUntil(lambda: dialog.task is None and "Kürzer." in dialog.readme_text,
                    timeout=10000)
    assert "Bisherige README:\n" + DRAFT in ai.prompts[1]
    assert dialog.wishes.toPlainText() == ""
    dialog.finish()
    assert dialog.result() == 1


def test_write_dialog_removes_a_file(qtbot, tmp_path, projects_root, make_services):
    from cockpit.ui import readme_flow
    services, project = readme_project(tmp_path, projects_root, make_services)
    dialog = readme_flow.WriteDialog(services, project)
    qtbot.addWidget(dialog)
    dialog.add_files([str(tmp_path / "a.txt"), str(tmp_path / "b.txt")])
    dialog.files.setCurrentRow(0)
    dialog.remove_file()
    assert [p.name for p in dialog.paths()] == ["b.txt"]


def test_edit_dialog_needs_instructions(qtbot, tmp_path, projects_root, make_services, scripted):
    from cockpit.ui import readme_flow
    services, project = readme_project(tmp_path, projects_root, make_services,
                                       {"README.md": DRAFT + "\n"})
    ai = scripted("# Rechner\n\nNeu.")
    dialog = readme_flow.EditDialog(services, project)
    qtbot.addWidget(dialog)
    assert dialog.readme_text == DRAFT and not dialog.changed()
    assert dialog.wishes.accessibleName() == "Anweisungen an die KI zur Überarbeitung"
    dialog.ai_button.click()
    assert dialog.task is None and ai.prompts == []      # ohne Anweisungen nichts gesendet
    dialog.wishes.setPlainText("Kürzer.")
    dialog.ai_button.click()
    qtbot.waitUntil(lambda: dialog.task is None and dialog.readme_text != DRAFT, timeout=10000)
    assert dialog.readme_text == "# Rechner\n\nNeu." and dialog.changed()
    assert "Kürzer." in ai.prompts[0]


def test_translation_review_takes_edited_text_and_escape_skips(qtbot, monkeypatch):
    from cockpit.ui import readme_flow
    choices = iter([(readme_flow.TAKE, "# Angepasst"), (readme_flow.SKIP, None)])

    def fake_exec(dialog):
        choice, text = next(choices)
        dialog.choice = choice
        if text:
            dialog.edit.setPlainText(text)
        return 1

    monkeypatch.setattr(readme_flow.TranslationDialog, "exec", fake_exec)
    taken = readme_flow.review([("README.de.md", "de", "# A"), ("README.fr.md", "fr", "# B")],
                               None)
    assert taken == {"README.de.md": "# Angepasst"}
    dialog = readme_flow.TranslationDialog("README.de.md", "de", "# A", 1, 2)
    qtbot.addWidget(dialog)
    assert dialog.choice == readme_flow.SKIP              # Vorgabe, auch bei Escape
    assert dialog.windowTitle() == "README übersetzt, Deutsch: 1 von 2"


# -- Abläufe auf der Projektzeile ----------------------------------------------------------------
def actions(qtbot, services):
    from tests.test_phase10f import window
    win = window(qtbot, services)
    return win, win.controller.readme


def test_write_saves_and_translates(qtbot, tmp_path, projects_root, make_services, scripted,
                                    monkeypatch, home):
    from cockpit.ui import readme_flow
    services, project = readme_project(tmp_path, projects_root, make_services,
                                       languages=["Deutsch"])
    scripted("# Rechner\n\nRechnet schnell.")              # die Übersetzung
    win, readme = actions(qtbot, services)

    def fake_exec(dialog):
        dialog.text.setPlainText(DRAFT)
        return 1

    monkeypatch.setattr(readme_flow.WriteDialog, "exec", fake_exec)
    monkeypatch.setattr(readme_flow.TranslationDialog, "exec",
                        lambda dialog: setattr(dialog, "choice", readme_flow.TAKE) or 1)
    readme.write(ActionContext(services, project, Target.PROJECT))
    assert read(project) == DRAFT + "\n"
    qtbot.waitUntil(lambda: (project.code_dir / "README.de.md").is_file(), timeout=10000)
    assert "[English](README.md) | Deutsch" in read(project, "README.de.md")
    assert "English | [Deutsch](README.de.md)" in read(project)


def test_edit_unchanged_translates_only_missing_languages(qtbot, tmp_path, projects_root,
                                                          make_services, scripted, monkeypatch):
    from cockpit.ui import readme_flow
    services, project = readme_project(tmp_path, projects_root, make_services,
                                       {"README.md": DRAFT + "\n"}, languages=[])
    ai = scripted()
    win, readme = actions(qtbot, services)
    monkeypatch.setattr(readme_flow.EditDialog, "exec", lambda dialog: 1)
    readme.edit(ActionContext(services, project, Target.PROJECT))
    assert ai.prompts == [] and read(project) == DRAFT + "\n"     # nichts geändert, nichts fehlt
    services.features.set_setting("readme", "languages", ["Deutsch"])
    calls = []
    monkeypatch.setattr(type(readme), "_translate",
                        lambda self, project, text, ai, only: calls.append(only))
    readme.edit(ActionContext(services, project, Target.PROJECT))
    assert calls == [["de"]]


def test_import_action_asks_first(qtbot, tmp_path, projects_root, make_services, monkeypatch):
    from cockpit.ui import readme_flow
    services, project = readme_project(tmp_path, projects_root, make_services)
    source = tmp_path / "Beschreibung.md"
    source.write_text("# Rechner\n", encoding="utf-8")
    win, readme = actions(qtbot, services)
    monkeypatch.setattr(readme_flow.QFileDialog, "getOpenFileName",
                        lambda *args, **kwargs: (str(source), ""))
    asked = []
    monkeypatch.setattr(readme_flow, "confirm",
                        lambda parent, title, text, **kw: asked.append(text) or False)
    context = ActionContext(services, project, Target.PROJECT)
    readme.import_file(context)
    assert asked == ["Beschreibung.md wird als README.md in den Ordner Code kopiert. "
                     "Übernehmen?"]
    assert not (project.code_dir / "README.md").exists()          # Abbrechen ist die Vorgabe
    monkeypatch.setattr(readme_flow, "confirm", lambda *args, **kw: True)
    readme.import_file(context)
    assert read(project) == "# Rechner\n"
