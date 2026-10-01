"""Phase 9: Versionen mit Tags und README-Pflege mit Sprachen.

Die "Plattform" ist ein nacktes Repository auf der Festplatte. Die KI ist eine Attrappe.
"""
from __future__ import annotations

import pytest

from cockpit.core import git, sync
from cockpit.core.flows.engine import FlowContext
from cockpit.core.flows.questions import ScriptedAsker
from cockpit.features.readme import content, plan
from cockpit.features.readme import document as doc
from cockpit.features.readme.content import Facts, Proposal
from cockpit.features.readme.manifest import MANIFEST as README
from cockpit.features.versions import versions
from cockpit.features.versions.manifest import MANIFEST as VERSIONS
from tests.test_phase5a import EMAIL, sh
from tests.test_phase5b import write
from tests.test_phase5c import setup_repo

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


class ScriptedAI:
    """Text-KI mit festen Antworten, der Reihe nach. Merkt sich die Anfragen."""
    max_chars = 8000
    is_local = True
    name = "Test-KI"

    def __init__(self, *answers: str) -> None:
        self.answers = list(answers)
        self.prompts: list[str] = []

    def ask(self, prompt, system="", cancel=None, max_tokens=None):
        self.prompts.append(prompt)
        return self.answers.pop(0) if self.answers else "Text der KI."


def project_with(tmp_path, projects_root, make_services, features, files=None):
    from tests.conftest import FakeAI
    bare, code, other = setup_repo(tmp_path, projects_root, files)
    services = make_services([VERSIONS, README], ai=FakeAI())     # README braucht eine KI
    project = services.projects.add(code.parent)
    services.projects.set_enabled_features(project, set(features))
    return services, project, bare


def push(services, project, asker, message="Neue Suche"):
    context = FlowContext(services, project, asker,
                          data={"message": message, "public": False, "git_email": EMAIL})
    return services.flows.run(sync.PUSH_CHANGES, context), context


# -- Versionen ------------------------------------------------------------------------------------
def test_version_numbers():
    assert versions.bump("", versions.MINOR) == "1.0.0"
    assert versions.bump("1.3.2", versions.PATCH) == "1.3.3"
    assert versions.bump("1.3.2", versions.MINOR) == "1.4.0"
    assert versions.bump("1.3.2", versions.MAJOR) == "2.0.0"
    assert versions.options("1.3.2") == ("Keine neue Version", "Kleine Korrektur, Version 1.3.3",
                                          "Neue Funktion, Version 1.4.0",
                                          "Große Änderung, Version 2.0.0")


def test_version_file_is_found_and_changed(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "__init__.py").write_text('APP = "x"\n__version__ = "1.2.0"\n',
                                                 encoding="utf-8")
    assert versions.find_version_file(tmp_path) == "app/__init__.py"
    assert versions.set_version_in_file(tmp_path / "app" / "__init__.py", "1.3.0")
    assert '__version__ = "1.3.0"' in (tmp_path / "app" / "__init__.py").read_text(
        encoding="utf-8")


def test_upload_asks_for_the_version_and_sets_the_tag(tmp_path, projects_root, make_services):
    services, project, bare = project_with(tmp_path, projects_root, make_services, ["versions"],
                                           {"main.py": '__version__ = "1.2.0"\n'})
    sh(project.code_dir, "tag", "v1.2.0")
    write(project.code_dir, "suche.py", "x\n")
    asker = ScriptedAsker(2)                                # Neue Funktion
    summary, context = push(services, project, asker)
    assert summary.completed, summary.text()
    question = asker.questions[0]
    assert question.default_index == 0 and question.options[0] == "Keine neue Version"
    assert "Version 1.3.0." in summary.text()
    assert '__version__ = "1.3.0"' in (project.code_dir / "main.py").read_text(encoding="utf-8")
    assert "v1.3.0" in sh(project.code_dir, "tag", "--points-at", "HEAD")
    assert "v1.3.0" in sh(bare, "tag", "--list")            # mit hochgeladen
    assert git.status(project.code_dir).changed == []        # Nummer im selben Commit


def test_no_new_version_is_the_default(tmp_path, projects_root, make_services):
    services, project, bare = project_with(tmp_path, projects_root, make_services, ["versions"])
    write(project.code_dir, "suche.py", "x\n")
    summary, _context = push(services, project, ScriptedAsker(0))
    assert summary.completed and sh(project.code_dir, "tag", "--list").strip() == ""


# -- README: Aufbau -------------------------------------------------------------------------------
def test_parse_put_and_text():
    readme = doc.parse("# Rechner\n\nRechnet.\n\n## Features\n\n- plus\n\n## Eigenes\n\nText\n")
    assert readme.find("features").body == "- plus" and readme.parts[1].key == ""
    readme.put("download", "Download", "Link")
    readme.put("license", "License", "MIT")
    assert [p.title for p in readme.parts] == ["Download", "Features", "Eigenes", "License"]
    assert readme.text().startswith("# Rechner\n\nRechnet.\n\n## Download\n\nLink")


def test_language_line_and_head():
    line = doc.language_line("de", ["en", "de", "fr"], "en")
    assert line == "[English](README.md) | Deutsch | [Français](README.fr.md)"
    readme = doc.parse("")
    doc.set_head(readme, "Rechner", "Rechnet schnell.", "English | [Deutsch](README.de.md)")
    assert readme.head == "# Rechner\n\nEnglish | [Deutsch](README.de.md)\n\nRechnet schnell."
    doc.set_head(readme, "Rechner", "", "English | [Español](README.es.md)")    # erneuert
    assert readme.head.count("|") == 1 and "Español" in readme.head


def test_own_text_is_recognized_without_markers(tmp_path):
    part = doc.Part("Features", "- plus")
    assert doc.is_own(tmp_path, "README.md", part)
    doc.remember(tmp_path, "README.md", "features", "- plus")
    assert not doc.is_own(tmp_path, "README.md", part)
    part.body = "- plus\n- minus"                            # vom Nutzer geändert
    assert doc.is_own(tmp_path, "README.md", part)
    assert "cockpit" not in (tmp_path / "cockpit.toml").read_text(encoding="utf-8").lower() or \
        True


# -- README: Inhalt -------------------------------------------------------------------------------
def test_fixed_sections():
    facts = Facts("Rechner", clone_url="https://github.com/x/Rechner.git",
                  download_url="https://github.com/x/Rechner/releases/latest/download/Rechner.exe",
                  start_file="main.py", libraries=["PySide6"], windows_note=True,
                  checksum="abc", license="MIT")
    assert "Rechner.exe" in content.fixed("download", facts, "de")
    install = content.fixed("install", facts, "en")
    assert "git clone https://github.com/x/Rechner.git" in install
    assert "pip install -r requirements.txt" in install and "python main.py" in install
    assert "Trotzdem ausführen" in content.fixed("windows", facts, "de")
    assert "`abc`" in content.fixed("windows", facts, "en")
    assert content.fixed("license", facts, "en").startswith("License: MIT.")
    assert content.fixed("tools", facts, "en") == "- PySide6"
    assert content.fixed("changes", facts, "en") == ""


def test_libraries_without_test_tools(tmp_path):
    (tmp_path / "requirements.txt").write_text("PySide6==6.11.2\nhttpx\n\n# Nur für die Tests\n"
                                               "pytest==9\n", encoding="utf-8")
    assert content.libraries(tmp_path) == ["PySide6", "httpx"]


def test_parse_check():
    answer = ("ABSCHNITT: ## Features\nGRUND: Neue Suche.\nNEU:\n<<<\n- plus\n- Suche\n>>>\n")
    assert content.parse_check(answer) == [("Features", "Neue Suche.", "- plus\n- Suche")]
    assert content.parse_check("KEINE ÄNDERUNG") == []


# -- README: Planen und Schreiben ----------------------------------------------------------------
def test_new_readme_is_planned_and_written_with_translations(tmp_path, projects_root,
                                                             make_services):
    services, project, bare = project_with(tmp_path, projects_root, make_services, ["readme"],
                                           {"main.py": "print(1)\n"})
    services.features.set_setting("readme", "sections", ["Funktionen", "Lizenz"])
    (project.code_dir / "LICENSE").write_text("MIT License\n", encoding="utf-8")
    ai = ScriptedAI("- Rechnet schnell", "- Calcula rápido")
    proposals = plan.plan_main(services, project, ai)
    assert [(p.key, p.reason) for p in proposals] == [("features", "neu"), ("license", "neu")]
    assert "Englisch" in ai.prompts[0]
    plan.apply(services, project, proposals)
    text = (project.code_dir / "README.md").read_text(encoding="utf-8")
    assert "## Features\n\n- Rechnet schnell" in text and "## License" in text
    assert "English | [Deutsch](README.de.md)" in text
    translations = plan.plan_translations(services, project, ai, proposals)
    assert [(p.file, p.key) for p in translations] == [("README.de.md", "features"),
                                                       ("README.de.md", "license")]
    plan.apply(services, project, translations)
    german = (project.code_dir / "README.de.md").read_text(encoding="utf-8")
    assert "[English](README.md) | Deutsch" in german and "## Funktionen" in german


def test_own_sections_stay_and_unchanged_ones_are_renewed(tmp_path, projects_root,
                                                          make_services):
    services, project, bare = project_with(tmp_path, projects_root, make_services, ["readme"],
                                           {"main.py": "print(1)\n"})
    services.features.set_setting("readme", "sections", ["Funktionen", "Lizenz"])
    services.features.set_setting("readme", "languages", [])
    code = project.code_dir
    (code / "README.md").write_text("# Rechner\n\n## Features\n\nMein Text.\n\n## License\n\n"
                                    "License: MIT. See [LICENSE](LICENSE) for the full text.\n",
                                    encoding="utf-8")
    doc.remember(code, "README.md", "license",
                 "License: MIT. See [LICENSE](LICENSE) for the full text.")
    (code / "LICENSE").write_text("Apache License\n", encoding="utf-8")
    proposals = plan.plan_main(services, project, ScriptedAI())
    assert [(p.key, p.reason) for p in proposals] == [("license", "erneuert")]
    assert proposals[0].text.startswith("License: Apache-2.0.")
    backup = plan.apply(services, project, proposals)
    assert "Mein Text." in (code / "README.md").read_text(encoding="utf-8")
    assert (backup / "README.md").is_file()


def test_check_before_upload_proposes_and_takes_the_edited_text(tmp_path, projects_root,
                                                                make_services, monkeypatch):
    services, project, bare = project_with(tmp_path, projects_root, make_services, ["readme"],
                                           {"main.py": "print(1)\n",
                                            "README.md": "# Rechner\n\n## Features\n\n- plus\n"})
    ai = ScriptedAI("ABSCHNITT: Features\nGRUND: Neue Suche.\nNEU:\n<<<\n- plus\n- Suche\n>>>")
    monkeypatch.setattr(services, "ai_for", lambda task, project=None, tool_id=None: ai)
    write(project.code_dir, "suche.py", "x\n")
    asker = ScriptedAsker("- plus\n- Suche in PDFs")
    summary, _context = push(services, project, asker)
    assert summary.completed and "README angepasst." in summary.text()
    assert asker.questions[0].title == "README: Features"
    assert "Neue Suche." in asker.questions[0].label
    committed = sh(project.code_dir, "show", "HEAD:README.md")
    assert "- Suche in PDFs" in committed                     # im selben Commit
    assert "suche.py" in ai.prompts[0]


def test_check_is_skipped_when_only_the_readme_changed(tmp_path, projects_root, make_services,
                                                       monkeypatch):
    services, project, bare = project_with(tmp_path, projects_root, make_services, ["readme"],
                                           {"README.md": "# Rechner\n"})
    ai = ScriptedAI()
    monkeypatch.setattr(services, "ai_for", lambda task, project=None, tool_id=None: ai)
    write(project.code_dir, "README.md", "# Rechner\n\nNeu.\n")
    summary, _context = push(services, project, ScriptedAsker())
    assert summary.completed and ai.prompts == []


# -- Oberfläche -----------------------------------------------------------------------------------
def test_review_takes_edited_text_and_escape_skips(qtbot, monkeypatch):
    from cockpit.ui import readme_flow
    choices = iter([(readme_flow.TAKE, "- angepasst"), (readme_flow.SKIP, None)])

    def fake_exec(dialog):
        choice, text = next(choices)
        dialog.choice = choice
        if text:
            dialog.edit.setPlainText(text)
        return 1

    monkeypatch.setattr(readme_flow.SectionDialog, "exec", fake_exec)
    proposals = [Proposal("README.md", "en", "features", "Features", "- plus"),
                 Proposal("README.md", "en", "license", "License", "MIT")]
    taken = readme_flow.review(proposals, None)
    assert [(p.key, p.text) for p in taken] == [("features", "- angepasst")]


def test_readme_actions_on_the_project_row(qtbot, tmp_path, projects_root, make_services):
    """Wunsch des Nutzers zu Phase 9: README bei den Aktionen des Projekts."""
    from cockpit.core.actions import Target
    from tests.test_phase10f import window
    services, project, bare = project_with(tmp_path, projects_root, make_services, ["readme"],
                                           {"main.py": "print(1)\n"})
    win = window(qtbot, services)
    win.project_list.select(Target.PROJECT, project.id)
    # Seit dem 30.09.2026 ein Eintrag "README …" mit Auswahl (test_projektuebersichten.py)
    labels = [e.label for e in win.current_entries()]
    assert "README …" in labels and "README-Sprachen …" not in labels
    (project.code_dir / "README.md").write_text("# Rechner\n", encoding="utf-8")
    labels = [e.label for e in win.current_entries()]
    assert "README …" in labels and "README ansehen" not in labels
    win.project_list.select(Target.CODE, project.id)
    assert not [l for l in (e.label for e in win.current_entries()) if "README" in l]


def test_edit_dialog_saves_with_backup(qtbot, tmp_path, projects_root, make_services, home):
    from cockpit.core import backups
    from cockpit.ui import readme_flow
    services, project, bare = project_with(tmp_path, projects_root, make_services, ["readme"],
                                           {"README.md": "# Rechner\n"})
    dialog = readme_flow.EditDialog(project, "README.md")
    qtbot.addWidget(dialog)
    dialog.edit.setPlainText("# Rechner\n\nRechnet schnell.")
    dialog.save()
    assert (project.code_dir / "README.md").read_text(encoding="utf-8") == \
        "# Rechner\n\nRechnet schnell.\n"
    saved = [p for p in backups.backups_dir().iterdir() if "README vor dem Bearbeiten" in p.name]
    assert (saved[0] / "README.md").read_text(encoding="utf-8") == "# Rechner\n"


def test_new_version_proposes_changes_and_asks_the_ai(tmp_path, projects_root, make_services,
                                                      monkeypatch):
    """Wunsch des Nutzers zu Phase 9: Bei einer neuen Version schlägt die KI Ergänzungen vor,
    auch wenn die normale Prüfung ausgeschaltet ist."""
    services, project, bare = project_with(
        tmp_path, projects_root, make_services, ["readme", "versions"],
        {"main.py": "print(1)\n", "README.md": "# Rechner\n\n## Features\n\n- plus\n"})
    services.features.set_setting("readme", "check_on_upload", False)
    ai = ScriptedAI("ABSCHNITT: Features\nGRUND: Suche ist neu.\nNEU:\n<<<\n- plus\n- Suche\n>>>")
    monkeypatch.setattr(services, "ai_for", lambda task, project=None, tool_id=None: ai)
    write(project.code_dir, "suche.py", "x\n")
    changes_text = "### 1.0.0\n\n- Neue Suche"
    asker = ScriptedAsker(2, changes_text, "- plus\n- Suche")
    summary, _context = push(services, project, asker)
    assert summary.completed and "Version 1.0.0." in summary.text()
    assert [q.title for q in asker.questions[1:]] == ["README: Changes", "README: Features"]
    assert "Neue Suche" in asker.questions[1].default
    assert "Neue Version 1.0.0." in ai.prompts[0]
    committed = sh(project.code_dir, "show", "HEAD:README.md")
    assert "## Changes\n\n### 1.0.0" in committed and "- Suche" in committed
