"""Exe bauen in Schritten, eigener Ordner je Exe, Lizenz, Branch löschen (Wunsch des Nutzers vom
03.10.2026). Die Plattform ist ein nacktes Repository, der Bau eine Attrappe."""
from __future__ import annotations

import pytest

from cockpit.core import backups, branches, exe, git, licenses
from cockpit.core.actions import ActionContext, Target
from cockpit.core.errors import CockpitError
from cockpit.features.exe_build import exe_branch
from cockpit.features.exe_build.manifest import MANIFEST as EXE
from cockpit.ui import exe_flow, exe_wizard
from tests.conftest import said
from tests.test_phase10f import structured, window
from tests.test_phase5a import sh
from tests.test_phase5c import setup_repo

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

FILES = {"main.py": "print(1)\n", "README.md": "# Tagebuch\n", "LICENSE": "MIT License\n"}


def plain_project(tmp_path, projects_root, make_services):
    """Ohne Branch-Ordner: der Ordner Code wechselt selbst auf den Branch."""
    _bare, code, _other = setup_repo(tmp_path, projects_root, dict(FILES))
    (code.parent / "Exe").mkdir()
    services = make_services([EXE])
    return services, services.projects.add(code.parent)


def folders_project(tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    for name, text in FILES.items():
        (project.code_dir / name).write_text(text, encoding="utf-8")
    sh(project.code_dir, "add", "-A")
    sh(project.code_dir, "commit", "-q", "-m", "Dateien")
    project.exe_dir.mkdir(parents=True, exist_ok=True)
    return services, project


def fake_exe(folder, name="Tagebuch.exe", text="neu"):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(text, encoding="utf-8")
    return folder / name


def clean(code_dir) -> bool:
    return git.run(["status", "--porcelain"], code_dir).stdout.strip() == ""


# -- Kern: Ordner je Exe, README und Lizenz -------------------------------------------------------
def test_missing_docs(tmp_path):
    assert exe.missing_docs(tmp_path) == ["README", "Lizenz"]
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    assert exe.missing_docs(tmp_path) == ["Lizenz"]
    (tmp_path / "LICENSE").write_text("x", encoding="utf-8")
    assert exe.missing_docs(tmp_path) == []
    assert exe.doc_files(tmp_path) == ["LICENSE", "README.md"]


def test_install_puts_the_exe_in_its_own_folder_with_the_docs(tmp_path, projects_root,
                                                              make_services):
    services, project = plain_project(tmp_path, projects_root, make_services)
    exe.write_settings(project.code_dir, exe.BuildSettings("main.py", "Tagebuch"))
    fake_exe(project.exe_dir, "Alt.exe", "alt")                       # alte Ablage
    result = exe.install(project, fake_exe(tmp_path / "dist"), "abc")
    home = project.exe_dir / "Tagebuch"
    assert result.exe == home / "Tagebuch.exe"
    assert (home / "LICENSE").is_file() and (home / "README.md").is_file()
    assert not (project.exe_dir / "Alt.exe").exists()
    assert (result.backup / "Alt.exe").read_text(encoding="utf-8") == "alt"


def test_promote_branch_keeps_user_data(tmp_path, projects_root, make_services):
    services, project = plain_project(tmp_path, projects_root, make_services)
    settings = exe.BuildSettings("main.py", "Tagebuch", beside=["Daten"])
    exe.write_settings(project.code_dir, settings)
    (project.code_dir / "Daten").mkdir()
    (project.code_dir / "Daten" / "start.txt").write_text("aus dem Code", encoding="utf-8")
    old = fake_exe(project.exe_dir / "Tagebuch", text="alt")
    (old.parent / "Daten").mkdir()
    (old.parent / "Daten" / "eigene.txt").write_text("vom Nutzer", encoding="utf-8")
    branch = project.exe_dir / exe.branch_exe_name("Tagebuch", exe_branch.BRANCH)
    fake_exe(branch)
    (branch / "Daten").mkdir()
    (branch / "Daten" / "start.txt").write_text("aus dem Code", encoding="utf-8")
    result = exe.promote_branch(project, exe_branch.BRANCH, "abc")
    home = project.exe_dir / "Tagebuch"
    assert result.exe == home / "Tagebuch.exe" and result.exe.read_text() == "neu"
    assert (home / "Daten" / "eigene.txt").read_text(encoding="utf-8") == "vom Nutzer"
    assert (home / "LICENSE").is_file() and not branch.exists()
    assert exe.read_record(project.code_dir).commit == "abc"
    assert exe.branch_home(project, exe_branch.BRANCH) is None
    with pytest.raises(CockpitError):
        exe.promote_branch(project, exe_branch.BRANCH, "abc")


def test_branch_exe_gets_its_own_folder(tmp_path, projects_root, make_services):
    services, project = plain_project(tmp_path, projects_root, make_services)
    settings = exe.BuildSettings("main.py", "Tagebuch")
    result = exe.install_branch(project, fake_exe(tmp_path / "dist"), "suche", settings)
    assert result.exe == project.exe_dir / "Tagebuch_branch_suche" / "Tagebuch.exe"
    assert (result.exe.parent / "README.md").is_file()
    assert exe.current_exe(project) is None                    # zählt nicht als normale Exe


# -- Lizenz ---------------------------------------------------------------------------------------
def test_license_name_write_and_backup(tmp_path, home):
    assert licenses.state(tmp_path) == "noch keine Lizenz"
    assert licenses.write("Tagebuch", tmp_path, "MIT License\n\nPermission ...") is None
    assert licenses.name(tmp_path) == "MIT"
    (tmp_path / "LICENSE").rename(tmp_path / "LICENSE.md")
    backup = licenses.write("Tagebuch", tmp_path, "Apache License\nVersion 2.0")
    assert licenses.name(tmp_path) == "Apache-2.0" and not (tmp_path / "LICENSE.md").exists()
    assert (backup / "LICENSE.md").is_file()
    with pytest.raises(CockpitError):
        licenses.write("Tagebuch", tmp_path, "  ")
    (tmp_path / "bild.png").write_bytes(b"\x89PNG\0")
    with pytest.raises(CockpitError):
        licenses.read_file(tmp_path / "bild.png")


def test_license_action_offers_what_fits(qtbot, tmp_path, projects_root, make_services,
                                         monkeypatch):
    from cockpit.ui import license_flow
    services, project = plain_project(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    asked = []
    monkeypatch.setattr(license_flow, "choose_from_list",
                        lambda parent, title, name, items, *a: asked.append(list(items)))
    flow = win.controller.licenses
    context = ActionContext(services, project, Target.PROJECT)
    flow.choose(context)
    assert asked[-1] == [license_flow.SHOW, license_flow.CHANGE]
    (project.code_dir / "LICENSE").unlink()
    flow.choose(context)
    assert asked[-1] == [license_flow.CHOOSE, license_flow.IMPORT]


def test_license_from_file_asks_and_writes(qtbot, tmp_path, projects_root, make_services,
                                           monkeypatch, home):
    from cockpit.ui import license_flow
    services, project = plain_project(tmp_path, projects_root, make_services)
    (project.code_dir / "LICENSE").unlink()
    source = tmp_path / "meine-lizenz.txt"
    source.write_text("MIT License\n", encoding="utf-8")
    win = window(qtbot, services)
    monkeypatch.setattr(license_flow.QFileDialog, "getOpenFileName",
                        lambda *a, **k: (str(source), ""))
    asked = []
    monkeypatch.setattr(license_flow, "confirm",
                        lambda parent, title, text, **k: asked.append(text) or True)
    win.controller.licenses.from_file(project)
    assert asked == ["meine-lizenz.txt wird als LICENSE in den Ordner Code kopiert. "
                     "Übernehmen?"]
    assert (project.code_dir / "LICENSE").read_text(encoding="utf-8") == "MIT License\n"
    assert said("Lizenz gespeichert: MIT.")


def test_license_entry_on_the_project_row(qtbot, tmp_path, projects_root, make_services):
    services, project = plain_project(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    win.project_list.select(Target.PROJECT, project.id)
    labels = [e.label for e in win.current_entries()]
    assert "Lizenz …, MIT" in labels
    assert win.focus_action(project.id, "license")
    assert win.actions_list.current_entry().action.id == "license"


# -- README und Lizenz fehlen ----------------------------------------------------------------------
@pytest.mark.parametrize("answer, expected", [(0, False), (1, True), (2, False)])
def test_docs_check_before_building(qtbot, tmp_path, projects_root, make_services, monkeypatch,
                                    answer, expected):
    services, project = plain_project(tmp_path, projects_root, make_services)
    (project.code_dir / "LICENSE").unlink()
    win = window(qtbot, services)
    asked, jumped = [], []
    monkeypatch.setattr(exe_flow, "ask_buttons", lambda parent, title, text, buttons, default,
                        escape: asked.append((text, buttons, default, escape)) or answer)
    monkeypatch.setattr(type(win), "focus_action",
                        lambda self, pid, action: jumped.append(action) or True)
    assert win.controller.exe.docs_ok(project, "Exe aus dem Code erstellen") is expected
    text, buttons, default, escape = asked[0]
    assert text.startswith("Bei Tagebuch fehlt Lizenz.")
    assert buttons == [exe_flow.ADD_NOW, exe_flow.IGNORE, "Abbrechen"] and escape == 2
    assert jumped == (["license"] if answer == 0 else [])


# -- Ablauf in Schritten ----------------------------------------------------------------------------
class Recorder:
    """Ersetzt die Fenster des Ablaufs. Jedes Fenster nimmt die nächste Antwort."""

    def __init__(self, monkeypatch, settings, summary=(), build=()):
        self.summaries: list[list[str]] = []
        self.summary_choices = list(summary)
        self.build_choices = list(build)
        recorder = self

        class Files:
            def __init__(self, *args, **kwargs):
                self.settings = settings

            def exec(self):
                return 1

        class Summary:
            def __init__(self, project, number, lines, changes, services=None, next_text="",
                         parent=None):
                recorder.summaries.append(lines)
                self.choice = recorder.summary_choices.pop(0)
                self.hints = "Hinweis"

            def exec(self):
                return 1

        class Build:
            def __init__(self, services, project, settings_, folder, with_ai, parent=None):
                recorder.folder = folder
                self.choice = recorder.build_choices.pop(0)
                self.error_text = "Fehler beim Bau"

            def exec(self):
                return 1

        monkeypatch.setattr(exe_wizard, "BuildSettingsDialog", Files)
        monkeypatch.setattr(exe_wizard, "SummaryDialog", Summary)
        monkeypatch.setattr(exe_wizard, "WizardBuildDialog", Build)


def wizard_setup(qtbot, services, project, monkeypatch):
    monkeypatch.setattr(services, "ai_problem", lambda tool_id=None: "Keine KI.")
    win = window(qtbot, services)
    return win, exe_wizard.ExeWizard(win.controller.exe, project)


def test_wizard_without_folders_keeps_main_clean(qtbot, tmp_path, projects_root, make_services,
                                                 monkeypatch):
    """Wunsch des Nutzers: Die Einstellungen kommen in den Branch, nie nach main."""
    services, project = plain_project(tmp_path, projects_root, make_services)
    settings = exe.BuildSettings("main.py", "Tagebuch")
    recorder = Recorder(monkeypatch, settings, summary=[exe_wizard.NEXT],
                        build=[exe_wizard.TEST_LATER])
    opened = []
    monkeypatch.setattr(exe_flow.ExeActions, "open_branch_exe",
                        lambda self, p: opened.append(p.name))
    win, wizard = wizard_setup(qtbot, services, project, monkeypatch)
    wizard.run()
    code = project.code_dir
    assert git.status(code).branch == exe_branch.BRANCH and recorder.folder == code
    assert "Exe-Einstellungen" in sh(code, "log", "-1", "--format=%s")
    assert exe.read_settings(code).name == "Tagebuch" and clean(code)
    assert git.run(["show", "main:cockpit.toml"], code, check=False).returncode != 0
    lines = recorder.summaries[0]
    assert any(l.startswith("Gebaut wird im Branch Cockpit-exe-bauen") for l in lines)
    assert any("Exe\\Tagebuch_branch_Cockpit-exe-bauen" in l for l in lines)
    assert opened == ["Tagebuch"]


def test_wizard_cancel_deletes_the_new_branch(qtbot, tmp_path, projects_root, make_services,
                                              monkeypatch):
    services, project = folders_project(tmp_path, projects_root, make_services)
    settings = exe.BuildSettings("main.py", "Tagebuch")
    Recorder(monkeypatch, settings, summary=[exe_wizard.CANCEL, exe_wizard.CANCEL])
    answers = [False, True]                       # erst "Zurück", dann wirklich abbrechen
    monkeypatch.setattr(exe_wizard, "confirm", lambda *a, **k: answers.pop(0))
    win, wizard = wizard_setup(qtbot, services, project, monkeypatch)
    wizard.run()
    assert not exe_branch.exists(project) and answers == []
    assert clean(project.code_dir) and not (project.code_dir / "cockpit.toml").exists()
    assert said("Exe-Bau verworfen. Main ist, wie es war.")


def test_wizard_retry_and_fix_go_back_to_the_right_step(qtbot, tmp_path, projects_root,
                                                        make_services, monkeypatch):
    services, project = folders_project(tmp_path, projects_root, make_services)
    settings = exe.BuildSettings("main.py", "Tagebuch")
    recorder = Recorder(monkeypatch, settings,
                        summary=[exe_wizard.NEXT, exe_wizard.NEXT],
                        build=[exe_wizard.RETRY, exe_wizard.FIX, exe_wizard.MERGE_ONLY])
    merged = []
    monkeypatch.setattr(exe_flow.ExeActions, "merge_branch",
                        lambda self, p, publish: merged.append(publish))
    win, wizard = wizard_setup(qtbot, services, project, monkeypatch)
    wizard.run()
    # Neuer Versuch baut gleich wieder, "Problem mit KI lösen" richtet erst neu ein
    assert len(recorder.summaries) == 2 and wizard.error == "Fehler beim Bau"
    assert merged == [False]


def test_mode_step_only_with_ai(qtbot, tmp_path, projects_root, make_services, monkeypatch):
    services, project = folders_project(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    monkeypatch.setattr(services, "ai_problem", lambda tool_id=None: "")
    wizard = exe_wizard.ExeWizard(win.controller.exe, project)
    assert wizard._number("summary") == 4
    dialog = exe_wizard.ModeDialog(project, 2, True)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == ("Exe aus dem Code erstellen: Tagebuch, Schritt 2: Mit oder "
                                    "ohne KI")
    assert [dialog.list.item(r).text() for r in range(2)] == [exe_wizard.WITH_AI,
                                                              exe_wizard.WITHOUT_AI]
    assert dialog.with_ai and dialog.back_button.isVisibleTo(dialog)
    monkeypatch.setattr(services, "ai_problem", lambda tool_id=None: "Keine KI.")
    assert exe_wizard.ExeWizard(win.controller.exe, project)._number("summary") == 3


def test_summary_opens_the_chat_only_on_request(qtbot, make_services):
    from cockpit.core.projects import Project
    from pathlib import Path
    project = Project(1, "Tagebuch", Path("x"), Path("x/Code"), None)
    dialog = exe_wizard.SummaryDialog(project, 4, ["Bereit."], [None], make_services([]))
    qtbot.addWidget(dialog)
    dialog.show()
    assert not dialog.chat.isVisible() and not dialog.repeat_button.isVisible()
    assert dialog.next_button.text() == "Exe e&rstellen"
    dialog.chat_button.click()
    assert dialog.chat.isVisible() and dialog.repeat_button.isVisible()
    assert not dialog.chat_button.isVisible()
    dialog.repeat_button.click()                          # ohne Gespräch: nichts
    assert dialog.choice == exe_wizard.CANCEL and dialog.isVisible()
    without = exe_wizard.SummaryDialog(project, 3, ["Bereit."], [None], None,
                                       "&Neuer Versuch, Exe zu bauen")
    qtbot.addWidget(without)
    assert without.chat_button is None and "Neuer Versuch" in without.next_button.text()


@pytest.mark.parametrize("works", [True, False])
def test_build_window_shows_the_next_steps(qtbot, tmp_path, monkeypatch, works):
    from cockpit.core.projects import Project
    project = Project(1, "Tagebuch", tmp_path, tmp_path / "Code", None)
    built = tmp_path / "Exe" / "Tagebuch_branch_Cockpit-exe-bauen" / "Tagebuch.exe"

    def fake_build(project, settings, on_status, on_line, cancel, branch_dir=None,
                   branch_name=""):
        if not works:
            raise CockpitError("PyInstaller hat die Exe nicht gebaut.")
        return exe.BuildResult(built, branch=branch_name)

    monkeypatch.setattr(exe, "build", fake_build)
    dialog = exe_wizard.WizardBuildDialog(None, project, exe.BuildSettings("main.py", "T"),
                                          tmp_path / "Code", with_ai=True)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.running and bool(dialog.result_buttons), timeout=5000)
    texts = [b.text() for b in dialog.result_buttons]
    assert dialog.windowTitle().endswith("Schritt 6: Ergebnis")
    if works:
        assert texts == [exe_wizard.TEST_LATER_TEXT, exe_wizard.MERGE_PUBLISH_TEXT,
                         exe_wizard.MERGE_ONLY_TEXT]
        assert dialog.choice == exe_wizard.TEST_LATER            # Escape: nichts überführen
    else:
        assert texts == ["Problem mit &KI lösen", "&Neuer Versuch, Exe zu bauen", "&Zurück"]
        assert dialog.error_text.startswith("PyInstaller hat die Exe nicht gebaut.")
        assert dialog.choice == exe_wizard.CANCEL


def test_merge_branch_makes_the_branch_exe_the_normal_one(qtbot, tmp_path, projects_root,
                                                          make_services):
    services, project = folders_project(tmp_path, projects_root, make_services)
    folder = exe_branch.prepare(project)
    exe.write_settings(folder, exe.BuildSettings("main.py", "Tagebuch"))
    exe_branch.commit(folder, ["cockpit.toml"], "Exe-Einstellungen")
    fake_exe(project.exe_dir / exe.branch_exe_name("Tagebuch", exe_branch.BRANCH))
    win = window(qtbot, services)
    win.controller.exe.merge_branch(project, publish=False)
    assert (project.exe_dir / "Tagebuch" / "Tagebuch.exe").read_text() == "neu"
    assert exe.read_settings(project.code_dir).name == "Tagebuch"
    assert not exe_branch.exists(project) and not folder.exists()
    assert said("Die Exe aus dem Branch ist jetzt die normale Exe. Der Branch "
                "Cockpit-exe-bauen ist gelöscht.")


def test_finish_menu_only_while_the_branch_exists(qtbot, tmp_path, projects_root,
                                                  make_services, monkeypatch):
    services, project = folders_project(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    actions = win.controller.exe
    monkeypatch.setattr(exe_flow.ExeActions, "_building", lambda self, c: True)
    context = ActionContext(services, project, Target.EXE)
    assert not actions._branch_open(context)
    exe_branch.prepare(project)
    assert actions._branch_open(context)


# -- Branch löschen ohne main ------------------------------------------------------------------------
def test_leave_discarding_saves_and_removes_the_changes(tmp_path, projects_root, home):
    _bare, code, _other = setup_repo(tmp_path, projects_root, dict(FILES))
    sh(code, "switch", "-q", "-c", "versuch")
    (code / "main.py").write_text("geändert\n", encoding="utf-8")
    (code / "neu.txt").write_text("neu\n", encoding="utf-8")
    backup = branches.leave_discarding(code, "Tagebuch", "main")
    assert git.status(code).branch == "main" and clean(code)
    assert not (code / "neu.txt").exists()
    assert (code / "main.py").read_text(encoding="utf-8") == "print(1)\n"
    assert (backup / "neu.txt").is_file() and (backup / "main.py").is_file()


def test_deleting_the_current_branch_keeps_main_clean(qtbot, tmp_path, projects_root,
                                                      make_services, monkeypatch, home):
    from cockpit.ui import branch_dialogs
    services, project = plain_project(tmp_path, projects_root, make_services)
    code = project.code_dir
    sh(code, "switch", "-q", "-c", "versuch")
    (code / "neu.txt").write_text("neu\n", encoding="utf-8")
    dialog = branch_dialogs.BranchesDialog(project, branches.list_branches(code))
    qtbot.addWidget(dialog)
    asked = []
    monkeypatch.setattr(branch_dialogs, "confirm",
                        lambda parent, title, text, **k: asked.append(text) or True)
    dialog.set_show(branch_dialogs.ALL)
    dialog.list.setCurrentRow(dialog.row_of("versuch"))
    assert dialog.delete_button.isVisibleTo(dialog)
    dialog.delete_current()
    assert "kommen nicht nach main" in asked[0]
    assert git.status(code).branch == "main" and clean(code)
    assert "versuch" not in sh(code, "branch", "--list")


def test_abandon_switches_back_to_main(tmp_path, projects_root, make_services):
    services, project = plain_project(tmp_path, projects_root, make_services)
    exe_branch.prepare(project)
    assert git.status(project.code_dir).branch == exe_branch.BRANCH
    exe_branch.abandon(project)
    assert git.status(project.code_dir).branch == "main" and not exe_branch.exists(project)


# -- Antworten der KI: erst Sätze, dann Code ------------------------------------------------------
def test_chat_answer_has_sentences_before_code():
    from cockpit.ui.exe_chat import answer_lines
    answer = ("Die Startdatei fehlt. Tragen Sie sie ein.\n\n```python\nimport sys\n"
              "print(sys.argv)\n```\nDanach geht es.")
    assert answer_lines(answer) == ["Die Startdatei fehlt.", "Tragen Sie sie ein.", "Code:",
                                    "import sys", "print(sys.argv)", "Danach geht es."]
    from cockpit.ai import prompt_files
    assert "Antworte nie nur mit Code." in prompt_files.load("exe_chat_system")


# -- Fehler unterwegs (Wunsch des Nutzers vom 04.10.2026) ------------------------------------------
def test_problem_window_shows_the_output_and_copies_it(qtbot, make_services):
    from pathlib import Path
    from PySide6.QtGui import QGuiApplication
    from cockpit.core.projects import Project
    project = Project(1, "Tagebuch", Path("x"), Path("x/Code"), None)
    dialog = exe_wizard.ProblemDialog(project, 3, "Die Änderungen ergeben fehlerhaften Code.",
                                      "gui.py, Zeile 3: NameError", make_services([]))
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.windowTitle().endswith("Schritt 3: Fehler")
    assert dialog.output.isReadOnly() and "Zeile 3: NameError" in dialog.output.toPlainText()
    assert QGuiApplication.clipboard().text() == dialog.text
    assert dialog.next_button.text() == exe_wizard.FIX_TEXT and dialog.next_button.isVisible()
    assert dialog.chat_button.text() == "Mit KI &chatten" and not dialog.chat.isVisible()
    dialog.chat_button.click()
    assert dialog.chat.isVisible()
    order = [dialog.button_layout.itemAt(i).widget() for i in range(dialog.button_layout.count())]
    assert [w for w in order if w is not None][-1] is dialog.cancel_button   # Abbrechen zuletzt
    without = exe_wizard.ProblemDialog(project, 3, "Fehler.", "", None)
    qtbot.addWidget(without)
    assert without.chat_button is None and not without.next_button.isVisibleTo(without)


def test_fix_after_a_problem_hands_error_and_chat_to_the_ai(qtbot, tmp_path, projects_root,
                                                            make_services, monkeypatch):
    from cockpit.features.exe_build.ai_fix import Proposal
    from cockpit.ui import exe_ai
    services, project = folders_project(tmp_path, projects_root, make_services)
    settings = exe.BuildSettings("main.py", "Tagebuch")
    Recorder(monkeypatch, settings, summary=[exe_wizard.NEXT, exe_wizard.CANCEL])
    monkeypatch.setattr(exe_wizard, "confirm", lambda *a, **k: True)
    whats = []

    class Work:
        def __init__(self, project_, work, with_ai, parent=None, what="", title=""):
            whats.append(what)
            self.result_value = (project.code_dir, Proposal(), [])
            self.failure, self.back_requested = None, False

        def exec(self):
            return 1

    class Problem:
        def __init__(self, project_, number, message, details, services_=None, parent=None):
            self.choice, self.hints, self.text = exe_wizard.FIX, "Hinweis aus dem Chat", message

        def exec(self):
            return 1

    monkeypatch.setattr(exe_ai, "WorkDialog", Work)
    monkeypatch.setattr(exe_wizard, "ProblemDialog", Problem)
    failures = [("Fehlerhafter Code.", "Zeile 3")]
    monkeypatch.setattr(exe_wizard.ExeWizard, "apply_proposal",
                        lambda self: failures.pop(0) if failures else None)
    monkeypatch.setattr(services, "ai_problem", lambda tool_id=None: "")
    win = window(qtbot, services)
    wizard = exe_wizard.ExeWizard(win.controller.exe, project)
    wizard.ai = object()
    monkeypatch.setattr(exe_wizard.ExeWizard, "step_mode", lambda self: "setup")
    wizard.run()
    assert whats[0] == "Die KI liest den Code"
    assert whats[1] == ("Die KI versucht, das Problem zu lösen. Fehler und Chat wurden an die "
                        "KI übergeben")
    assert wizard.error == "Fehlerhafter Code."


def test_real_fix_button_goes_to_step_three_with_error_and_chat(qtbot, tmp_path, projects_root,
                                                                make_services, monkeypatch):
    """Rückmeldung des Nutzers (04.10.2026): "Problem mit KI lösen" fragte nach dem Abbrechen,
    statt mit Fehler und Chat zu Schritt 3 zu gehen. Hier mit dem echten Fenster und Knopf."""
    from cockpit.features.exe_build.ai_fix import Proposal
    from cockpit.ui import exe_ai
    services, project = folders_project(tmp_path, projects_root, make_services)
    settings = exe.BuildSettings("main.py", "Tagebuch")
    Recorder(monkeypatch, settings, summary=[exe_wizard.NEXT, exe_wizard.CANCEL])
    asked = []
    monkeypatch.setattr(exe_wizard, "confirm", lambda *a, **k: asked.append(a) or True)
    whats = []

    class Work:
        def __init__(self, project_, work, with_ai, parent=None, what="", title=""):
            whats.append(what)
            self.result_value = (project.code_dir, Proposal(), [])
            self.failure, self.back_requested = None, False

        def exec(self):
            return 1

    def press_fix(dialog):
        dialog.chat.history.append(("Warum?", "Es fehlt import sys."))     # gechattet
        dialog.next_button.click()
        return 1

    monkeypatch.setattr(exe_ai, "WorkDialog", Work)
    monkeypatch.setattr(exe_wizard.ProblemDialog, "exec", press_fix)
    failures = [("Fehlerhafter Code.", "NameError: sys")]
    monkeypatch.setattr(exe_wizard.ExeWizard, "apply_proposal",
                        lambda self: failures.pop(0) if failures else None)
    monkeypatch.setattr(services, "ai_problem", lambda tool_id=None: "")
    monkeypatch.setattr(exe_wizard.ExeWizard, "step_mode", lambda self: "setup")
    win = window(qtbot, services)
    wizard = exe_wizard.ExeWizard(win.controller.exe, project)
    wizard.ai = object()
    wizard.run()
    assert whats[1] == ("Die KI versucht, das Problem zu lösen. Fehler und Chat wurden an die "
                        "KI übergeben")
    assert "NameError: sys" in wizard.error and "import sys" in wizard.hints
    assert asked == []                        # keine Frage nach dem Abbrechen


# -- Branch schon in main, die Exe aus ihm liegt noch da (Rückmeldung vom 04.10.2026) -----------
def orphan_branch_exe(tmp_path, projects_root, make_services, monkeypatch):
    services, project = folders_project(tmp_path, projects_root, make_services)
    exe.write_settings(project.code_dir, exe.BuildSettings("main.py", "Tagebuch"))
    branch_exe = fake_exe(project.exe_dir / exe.branch_exe_name("Tagebuch", exe_branch.BRANCH))
    monkeypatch.setattr(exe_flow.ExeActions, "_building", lambda self, c: True)
    return services, project, branch_exe


def test_finish_is_offered_for_the_leftover_branch_exe(qtbot, tmp_path, projects_root,
                                                       make_services, monkeypatch):
    services, project, branch_exe = orphan_branch_exe(tmp_path, projects_root, make_services,
                                                      monkeypatch)
    win = window(qtbot, services)
    actions = win.controller.exe
    context = ActionContext(services, project, Target.EXE)
    assert not exe_branch.exists(project) and actions._branch_open(context)
    asked = []
    monkeypatch.setattr(exe_flow, "choose_from_list",
                        lambda parent, title, name, items: asked.append(list(items)) or 1)
    actions.finish_menu(context)
    assert asked[0] == [exe_flow.ADOPT_PUBLISH, exe_flow.ADOPT_ONLY, exe_flow.OPEN_TEST,
                        exe_flow.DISCARD_EXE]
    assert (project.exe_dir / "Tagebuch" / "Tagebuch.exe").read_text() == "neu"   # übernommen
    assert not branch_exe.parent.exists() and not actions._branch_open(context)
    assert said("Cockpit-exe-bauen ist schon in main. Die Exe aus dem Branch ist jetzt die "
                "normale Exe.")


def test_branch_exe_can_be_published(qtbot, tmp_path, projects_root, make_services,
                                     monkeypatch):
    """Release und Repository sind getrennt: Veröffentlichen geht auch mit der Exe aus dem
    Branch. Danach heißt ihr Ordner mit Version und gilt als normale Exe."""
    services, project, branch_exe = orphan_branch_exe(tmp_path, projects_root, make_services,
                                                      monkeypatch)
    win = window(qtbot, services)
    assert win.controller.exe._publishable(project) == [branch_exe]
    moved = exe.mark_published(project, branch_exe, "1.0.0")
    assert moved == project.exe_dir / "Tagebuch-v1.0.0" / "Tagebuch.exe"
    assert exe.current_exe(project) == moved and exe.branch_home(project, "x") is None
