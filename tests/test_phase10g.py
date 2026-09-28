"""Phase 10g: Exe mit Daten neben der Exe, strengerer Start-Test, Prüfung und KI-Hilfe.

Dazu die Wünsche aus dem Test von 10f: "<Branch> verwalten …" und "Branch auf GitHub hochladen …".
PyInstaller läuft nicht. Die KI ist eine Attrappe. Alle Geheimnisse sind erfunden.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

from cockpit.core import exe
from cockpit.core.errors import CockpitError
from cockpit.features.exe_build import ai_fix, setup_check
from cockpit.features.exe_build.manifest import MANIFEST as EXE_BUILD

windows = pytest.mark.skipif(sys.platform != "win32", reason="nur Windows")

ENGINE = "import csv\n\n\nclass VocabEngine:\n    def __init__(self, base_dir='Meine-Vokabeln'):\n" \
         "        self.base_dir = base_dir\n"
GUI = ("import sys\nfrom PySide6.QtWidgets import QApplication\nfrom engine import VocabEngine\n"
       "\n\ndef main():\n    engine = VocabEngine(\"Meine-Vokabeln\")\n    app = QApplication(sys.argv)\n"
       "\n\nif __name__ == \"__main__\":\n    main()\n")


def vocab_app(root: Path) -> Path:
    """Wie die VokabelApp des Nutzers: engine.py ohne Start, gui.py mit Fenster, .bat startet
    gui.py, Ordner Meine-Vokabeln, keine requirements.txt."""
    code = root / "VokabelApp" / "Code"
    (code / "Meine-Vokabeln" / "Spanisch").mkdir(parents=True)
    (code / "Meine-Vokabeln" / "Spanisch" / "zeit.csv").write_text("hoy;heute\n", encoding="utf-8")
    (code / "engine.py").write_text(ENGINE, encoding="utf-8")
    (code / "gui.py").write_text(GUI, encoding="utf-8")
    (code / "VokabelApp.bat").write_text('@echo off\ncd /d "%~dp0"\npython gui.py\n',
                                         encoding="utf-8")
    return code


# -- Prüfung ----------------------------------------------------------------------------------------
def test_start_file_guess_and_check(tmp_path):
    code = vocab_app(tmp_path)
    assert not setup_check.starts_something(code / "engine.py")
    assert setup_check.starts_something(code / "gui.py")
    assert setup_check.guess_start_file(code) == "gui.py"
    (code / "VokabelApp.bat").unlink()
    assert setup_check.guess_start_file(code) == "gui.py"        # __main__ und Fenster


def test_data_folders_and_relative_paths(tmp_path):
    code = vocab_app(tmp_path)
    assert setup_check.data_folders(code) == ["Meine-Vokabeln"]
    assert ("gui.py", "Meine-Vokabeln") in setup_check.relative_data_paths(code)
    (code / "gui.py").write_text(GUI.replace("import sys\n", "import sys\nBASE = sys.executable\n"),
                                 encoding="utf-8")
    assert ("gui.py", "Meine-Vokabeln") not in setup_check.relative_data_paths(code)


def test_check_names_the_real_problems(tmp_path):
    code = vocab_app(tmp_path)
    settings = exe.BuildSettings("engine.py", "VokabelApp", one_file=False)
    lines = setup_check.check_for(code, settings)
    assert lines[0].startswith("Nicht bereit")
    text = "\n".join(lines)
    assert "Problem: Die Startdatei engine.py startet nichts" in text
    assert "Wahrscheinlich ist gui.py richtig" in text
    assert "Problem: Diese Bibliotheken stehen nicht in requirements.txt und fehlen deshalb in " \
           "der Exe: PySide6." in text
    assert "Warnung: Der Code nutzt den Ordner Meine-Vokabeln" in text


# -- Start-Test -------------------------------------------------------------------------------------
@windows
def test_program_with_window_must_not_end_at_once(tmp_path):
    quick = tmp_path / "quick.bat"
    quick.write_text("@exit /b 0\n")
    assert "ohne Fehler beendet" in exe.start_test(quick, 5)
    with pytest.raises(CockpitError, match="gleich nach dem Start"):
        exe.start_test(quick, 5, windowed=True)


# -- Ordner neben der Exe ---------------------------------------------------------------------------
def project_with_beside(make_services, projects_root, one_file: bool):
    services = make_services([EXE_BUILD])
    code = vocab_app(projects_root)
    services.projects.add(code.parent)
    project = services.projects.all()[0]
    exe.write_settings(project.code_dir, exe.BuildSettings(
        "gui.py", "VokabelApp", one_file=one_file, beside=["Meine-Vokabeln"]))
    return services, project


def built(tmp_path: Path, one_file: bool, text: str) -> Path:
    work = tmp_path / f"bau-{text}"
    if one_file:
        work.mkdir()
        path = work / "VokabelApp.exe"
        path.write_text(text, encoding="utf-8")
        return path
    folder = work / "VokabelApp"
    (folder / "_internal").mkdir(parents=True)
    (folder / "VokabelApp.exe").write_text(text, encoding="utf-8")
    return folder


@pytest.mark.parametrize("one_file", [True, False])
def test_user_data_beside_the_exe_survives_updates(make_services, projects_root, tmp_path,
                                                   one_file):
    services, project = project_with_beside(make_services, projects_root, one_file)
    first = exe.install(project, built(tmp_path, one_file, "1"), "abc")
    home = first.exe.parent
    assert first.placed == ["Meine-Vokabeln"]
    assert (home / "Meine-Vokabeln" / "Spanisch" / "zeit.csv").is_file()
    # Die Nutzer legen eigene Vokabeln an
    (home / "Meine-Vokabeln" / "eigene.csv").write_text("gato;Katze\n", encoding="utf-8")
    second = exe.install(project, built(tmp_path, one_file, "2"), "def")
    assert second.exe.read_text(encoding="utf-8") == "2"
    assert (second.exe.parent / "Meine-Vokabeln" / "eigene.csv").read_text(
        encoding="utf-8") == "gato;Katze\n"


def test_upload_zip_contains_the_folders_from_code(make_services, projects_root, tmp_path):
    services, project = project_with_beside(make_services, projects_root, True)
    result = exe.install(project, built(tmp_path, True, "1"), "abc")
    (result.exe.parent / "Meine-Vokabeln" / "privat.csv").write_text("x\n", encoding="utf-8")
    work = tmp_path / "upload"
    work.mkdir()
    asset = exe.asset_for_upload(project, result.exe, work)
    assert asset.suffix == ".zip"
    names = zipfile.ZipFile(asset).namelist()
    assert "VokabelApp/VokabelApp.exe" in names
    assert "VokabelApp/Meine-Vokabeln/Spanisch/zeit.csv" in names
    assert not any("privat.csv" in n for n in names)                # eigene Daten bleiben hier


def test_change_settings_rewrites_spec_with_backup(make_services, projects_root):
    services, project = project_with_beside(make_services, projects_root, False)
    exe.ensure_spec(project.code_dir, exe.read_settings(project.code_dir))
    settings = exe.read_settings(project.code_dir)
    settings.start_file = "engine.py"
    backup = exe.change_settings(project.code_dir, project.name, settings)
    assert (backup / "VokabelApp.spec").is_file()
    assert "'engine.py'" in (project.code_dir / "VokabelApp.spec").read_text(encoding="utf-8")
    assert exe.read_settings(project.code_dir).beside == ["Meine-Vokabeln"]


# -- KI-Hilfe ---------------------------------------------------------------------------------------
ANSWER = """ZUSAMMENFASSUNG: Die Vokabeln liegen neben der Exe.

AENDERUNG: gui.py
GRUND: Den Ordner über die Exe bestimmen.
ALT:
<<<
    engine = VocabEngine("Meine-Vokabeln")
>>>
NEU:
<<<
    engine = VocabEngine(str(app_dir() / "Meine-Vokabeln"))
>>>

AENDERUNG: gui.py
GRUND: Gibt es nicht.
ALT:
<<<
    gibt_es_nicht()
>>>
NEU:
<<<
    x()
>>>
"""


class FakeAI:
    max_chars = 8000

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.prompts: list[str] = []

    def ask(self, prompt, system="", cancel=None, max_tokens=None):
        self.prompts.append(prompt)
        return self.answer


def test_fixed_part_without_ai(tmp_path):
    code = vocab_app(tmp_path)
    proposal = ai_fix.ask(None, "VokabelApp", code,
                          exe.BuildSettings("engine.py", "VokabelApp"), "")
    assert proposal.settings.start_file == "gui.py"
    assert proposal.settings.beside == ["Meine-Vokabeln"]
    assert [c.file for c in proposal.usable] == ["requirements.txt"]
    assert proposal.usable[0].new == "PySide6\n"


def test_ai_proposal_is_checked_and_applied_with_backup(tmp_path, home):
    code = vocab_app(tmp_path)
    ai = FakeAI(ANSWER)
    proposal = ai_fix.ask(ai, "VokabelApp", code, exe.BuildSettings("gui.py", "VokabelApp"),
                          "Die Vokabeln sollen neben der Exe liegen.")
    assert "Die Vokabeln sollen neben der Exe liegen." in ai.prompts[0]
    assert 'engine = VocabEngine("Meine-Vokabeln")' in ai.prompts[0]
    assert proposal.summary == "Die Vokabeln liegen neben der Exe."
    lines = [c.line() for c in proposal.changes]
    assert "gui.py: Gibt es nicht. Nicht übernehmbar: Der alte Text steht nicht in der Datei." \
        in lines
    assert len(proposal.usable) == 2                       # requirements.txt und gui.py
    folder = ai_fix.apply("VokabelApp", code, proposal)
    assert 'VocabEngine(str(app_dir() / "Meine-Vokabeln"))' in (code / "gui.py").read_text(
        encoding="utf-8")
    assert (code / "requirements.txt").read_text(encoding="utf-8") == "PySide6\n"
    assert 'VocabEngine("Meine-Vokabeln")' in (folder / "gui.py").read_text(encoding="utf-8")
    assert exe.read_settings(code).beside == ["Meine-Vokabeln"]


def test_ai_may_not_touch_files_outside(tmp_path):
    code = vocab_app(tmp_path)
    proposal = ai_fix.parse("AENDERUNG: ../../boese.py\nGRUND: x\nALT:\n<<<\n>>>\nNEU:\n<<<\n"
                            "print(1)\n>>>\n")
    ai_fix.check_changes(code, proposal)
    assert proposal.changes[0].problem == "Die Datei liegt nicht im Ordner Code."
    assert proposal.usable == []


# -- Wünsche aus dem Test von 10f -----------------------------------------------------------------
def test_branch_row_has_manage_and_publish(qtbot, tmp_path, projects_root, make_services):
    from cockpit.core import git, project_status, worktrees
    from cockpit.core.actions import Target
    from tests.test_phase10f import structured, window
    if git.find_git() is None:
        pytest.skip("Git ist nicht installiert")
    services, project, other = structured(tmp_path, projects_root, make_services)
    worktrees.create(project, "neue-funktion")
    win = window(qtbot, services)
    win.project_list.update_status(project_status.compute(project), project)
    assert win.project_list.select(Target.BRANCH, project.id, "neue-funktion")
    labels = [e.label for e in win.current_entries()]
    assert labels[0] == "neue-funktion verwalten …"
    assert "Branch auf GitHub hochladen …" in labels
    assert "Änderungen hochladen …" not in labels and "Branches …" not in labels
    win.project_list.select(Target.CODE, project.id)
    win.project_list.setCurrentRow(win.project_list.row_of(Target.CODE, project.id))
    labels = [e.label for e in win.current_entries()]
    assert "Branches …" in labels and "Änderungen hochladen …" in labels


def test_overview_names_folders_instead_of_current(qtbot, tmp_path, projects_root,
                                                   make_services):
    from cockpit.core import branches, git, worktrees
    from cockpit.ui.branch_dialogs import BranchesDialog
    from tests.test_phase10f import structured
    if git.find_git() is None:
        pytest.skip("Git ist nicht installiert")
    services, project, other = structured(tmp_path, projects_root, make_services)
    tree = worktrees.open_branch(project, "suche")
    dialog = BranchesDialog(project, branches.list_branches(project.code_dir),
                            folders={"suche": tree.folder})
    qtbot.addWidget(dialog)
    lines = [dialog.list.item(r).text() for r in range(dialog.list.count())]
    assert lines[0].startswith("main, Ordner Code\\main, Haupt-Branch")
    assert not any("aktueller Branch" in line for line in lines)
    assert any(line.startswith("suche, Ordner Code\\suche") for line in lines)
    assert any(line.startswith("design, ohne Ordner") for line in lines)
    single = BranchesDialog(project, [b for b in branches.list_branches(project.code_dir)
                                      if b.name == "suche"],
                            folders={"suche": tree.folder}, single=True)
    qtbot.addWidget(single)
    assert single.windowTitle() == "suche verwalten"
    single.delete_current()
    assert single.delete_request == "suche"
