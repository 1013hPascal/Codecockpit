"""Aufbau Projektordner\\Code\\main und Exe, Ordner mit Version, Anzeige beim Hochladen
(Rückmeldung des Nutzers vom 04.10.2026)."""
from __future__ import annotations

import pytest

from cockpit.core import exe, projects
from cockpit.core.actions import ActionContext, Target
from cockpit.core.projects import FLAT, GIT_OUTSIDE


def files(folder, names):
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / name).write_text("x\n", encoding="utf-8")


# -- Aufbau -------------------------------------------------------------------------------------
def test_git_outside_is_found_and_fixed(tmp_path):
    """So sah Chatbot für Text aus: der Code in Code\\main, .git noch in Code."""
    code = tmp_path / "Chatbot" / "Code"
    (code / ".git").mkdir(parents=True)
    files(code / "main", ["app.py"])
    assert projects.layout_problem(code) == GIT_OUTSIDE
    assert projects.main_code_dir(code) == code
    assert projects.fix_git_outside(code) == code / "main"
    assert (code / "main" / ".git").is_dir() and not (code / ".git").exists()
    assert projects.layout_problem(code) == ""
    assert projects.main_code_dir(code) == code / "main"


def test_flat_code_is_nested_into_main(tmp_path):
    code = tmp_path / "Rechner" / "Code"
    files(code, ["main.py", "README.md"])
    files(code / "daten", ["a.csv"])
    assert projects.layout_problem(code) == FLAT
    target = projects.nest_code(code)
    assert target == code / "main" and (target / "daten" / "a.csv").is_file()
    assert sorted(p.name for p in code.iterdir()) == ["main"]
    assert projects.layout_problem(code) == "" and projects.main_code_dir(code) == target


def test_main_without_git_counts_only_when_alone(tmp_path):
    code = tmp_path / "Code"
    files(code / "main", ["app.py"])
    assert projects.main_code_dir(code) == code / "main"
    files(code, ["start.py"])                                 # ein Paket namens main im Code
    assert projects.main_code_dir(code) == code


def test_store_follows_the_code_into_main(make_services, projects_root):
    files(projects_root / "Rechner" / "Code", ["main.py"])
    services = make_services([])
    project = services.projects.add(projects_root / "Rechner")
    assert project.code_dir.name == "Code"
    projects.nest_code(project.code_dir)                      # zum Beispiel von Hand verschoben
    found = next(p for p in services.projects.all() if p.id == project.id)
    assert found.code_dir == projects_root / "Rechner" / "Code" / "main"
    assert found.has_branch_folders


def test_check_layout_offers_the_fix_and_adds_exe(qtbot, make_services, projects_root,
                                                  monkeypatch):
    from cockpit.ui import project_actions
    from tests.test_phase10f import window
    code = projects_root / "Chatbot" / "Code"
    (code / ".git").mkdir(parents=True)
    files(code / "main", ["app.py"])
    services = make_services([])
    project = services.projects.add(code.parent)
    win = window(qtbot, services)
    asked = []
    monkeypatch.setattr(project_actions, "confirm",
                        lambda parent, title, text, **k: asked.append(text) or True)
    got = []
    assert win.controller.check_layout(project, got.append)
    assert "der Git-Ordner .git aber noch direkt in Code" in asked[0]
    assert got[0].code_dir == code / "main" and (code / "main" / ".git").is_dir()
    assert (projects_root / "Chatbot" / "Exe").is_dir()


def test_check_layout_keeps_it_when_declined(qtbot, make_services, projects_root, monkeypatch):
    from cockpit.ui import project_actions
    from tests.test_phase10f import window
    code = projects_root / "Rechner" / "Code"
    files(code, ["main.py"])
    services = make_services([])
    project = services.projects.add(code.parent)
    win = window(qtbot, services)
    monkeypatch.setattr(project_actions, "confirm", lambda *a, **k: False)
    got = []
    win.controller.check_layout(project, got.append)
    assert got[0].code_dir == code and (code / "main.py").is_file()


# -- Ordner mit Version -------------------------------------------------------------------------
def vokabel_project(make_services, projects_root):
    files(projects_root / "VokabelApp" / "Code", ["main.py"])
    (projects_root / "VokabelApp" / "Exe").mkdir()
    services = make_services([])
    project = services.projects.add(projects_root / "VokabelApp")
    settings = exe.BuildSettings("main.py", "VokabelApp", beside=["Meine-Vokabeln"])
    exe.write_settings(project.code_dir, settings)
    files(project.code_dir / "Meine-Vokabeln", ["start.csv"])
    return project


def built(tmp_path, text):
    folder = tmp_path / f"dist-{text}"
    files(folder, [])
    (folder / "VokabelApp.exe").write_text(text, encoding="utf-8")
    return folder / "VokabelApp.exe"


def test_published_folder_gets_the_version_and_stays(make_services, projects_root, tmp_path,
                                                     home):
    project = vokabel_project(make_services, projects_root)
    first = exe.install(project, built(tmp_path, "1"), "abc")
    (first.exe.parent / "Meine-Vokabeln" / "eigene.csv").write_text("gato\n", encoding="utf-8")
    # Seit dem 20.10.2026 bleibt der feste Ordner, erst beim Ersetzen kommt die Version dazu
    moved = exe.mark_published(project, first.exe, "1.2.0")
    assert moved == first.exe == project.exe_dir / "VokabelApp" / "VokabelApp.exe"
    assert (first.exe.parent / exe.VERSION_FILE).read_text(encoding="utf-8") == "1.2.0\n"
    second = exe.install(project, built(tmp_path, "2"), "def")
    folder = project.exe_dir / "VokabelApp-v1.2.0"
    assert second.exe == project.exe_dir / "VokabelApp" / "VokabelApp.exe"
    assert (folder / exe.VERSION_FILE).is_file()             # die Version bleibt liegen
    assert (folder / "VokabelApp.exe").read_text(encoding="utf-8") == "1"
    assert (second.exe.parent / "Meine-Vokabeln" / "eigene.csv").is_file()   # Daten kommen mit
    assert not (second.exe.parent / exe.VERSION_FILE).exists()   # neu gebaut, nicht veröffentlicht
    assert exe.current_exe(project) == second.exe


def test_running_exe_keeps_its_folder_name(make_services, projects_root, tmp_path, monkeypatch):
    project = vokabel_project(make_services, projects_root)
    first = exe.install(project, built(tmp_path, "1"), "abc")
    monkeypatch.setattr(exe, "running_from", lambda folder: True)
    assert exe.mark_published(project, first.exe, "1.2.0") == first.exe
    assert (first.exe.parent / exe.VERSION_FILE).is_file()


# -- Anzeige beim Hochladen ---------------------------------------------------------------------
def test_publish_says_while_uploading(qtbot, make_services, projects_root):
    from tests.test_phase10f import window
    files(projects_root / "VokabelApp" / "Code", ["main.py"])
    services = make_services([])
    project = services.projects.add(projects_root / "VokabelApp")
    win = window(qtbot, services)
    actions = win.controller.exe
    context = ActionContext(services, project, Target.EXE)
    assert actions._publish_detail(context) == "noch nicht veröffentlicht"
    actions.uploading.add(project.id)
    assert actions._publish_detail(context) == "wird gerade hochgeladen"
