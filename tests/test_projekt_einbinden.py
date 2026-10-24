"""Projekte einbinden (Wunsch des Nutzers vom 14.10.2026).

- Unterordner mit anderen Namen als Code und Exe: Das Cockpit legt Repository\\main und Release an,
  den Code kopiert der Nutzer selbst.
- Code und Exe: gleich beim Hinzufügen fragen, ob sie umbenannt werden.
- Liegt die Exe direkt im Ordner Release, kommt sie nach Exe-main, also in ihren eigenen Ordner.
"""
from __future__ import annotations

import pytest

from cockpit.core import exe
from cockpit.core.errors import CockpitError
from cockpit.ui import folder_rename_flow, project_actions
from tests.conftest import said, patch_controller


def files(folder, names):
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / name).write_text("x\n", encoding="utf-8")


# -- Repository und Release anlegen ---------------------------------------------------------------
def test_create_layout_keeps_what_is_there(tmp_path, make_services):
    folder = tmp_path / "Zug um Zug-Waagenzähler"
    files(folder / "Waagenfinder-code", ["main.py"])
    services = make_services([])
    project = services.projects.create_layout(folder)
    assert project.code_dir == folder / "Repository" / "main" and project.code_dir.is_dir()
    assert (folder / "Release").is_dir()
    assert (folder / "Waagenfinder-code" / "main.py").is_file()           # bleibt, wie es ist
    with pytest.raises(CockpitError):
        services.projects.create_layout(folder)                           # gibt es schon


def test_add_other_creates_layout_and_says_where_the_code_goes(qtbot, tmp_path, make_services,
                                                               monkeypatch):
    from tests.test_phase10f import window
    folder = tmp_path / "Waagen"
    files(folder / "Waagenfinder-code", ["main.py"])
    services = make_services([])
    win = window(qtbot, services)
    patch_controller(monkeypatch, "pick_folder", lambda *a: folder)
    patch_controller(monkeypatch, "ask_buttons", lambda *a, **k: 0)
    patch_controller(monkeypatch, "confirm", lambda *a, **k: True)
    infos = []
    patch_controller(monkeypatch, "show_info",
                        lambda parent, title, text: infos.append(text))
    win.controller.add_local()
    project = services.projects.find_by_dir(folder)
    assert project is not None and project.code_dir == folder / "Repository" / "main"
    assert "Kopieren Sie jetzt Ihren Code in den Ordner Repository\\main" in infos[0]
    assert "Im Projektordner liegen schon: Waagenfinder-code." in infos[0]
    assert said("Waagen hinzugefügt.")


# -- Code und Exe gleich umbenennen ---------------------------------------------------------------
def test_adding_code_and_exe_offers_the_rename(qtbot, tmp_path, make_services, monkeypatch):
    from tests.test_phase10f import window
    folder = tmp_path / "Rechner"
    files(folder / "Code", ["main.py"])
    files(folder / "Exe", ["Rechner.exe"])
    services = make_services([])
    win = window(qtbot, services)
    patch_controller(monkeypatch, "pick_folder", lambda *a: folder)
    monkeypatch.setattr(folder_rename_flow, "confirm", lambda *a, **k: True)
    patch_controller(monkeypatch, "confirm", lambda *a, **k: True)
    monkeypatch.setattr(project_actions.ProjectController, "offer_upload", lambda self, p: None)
    win.controller.add_local()
    qtbot.waitUntil(lambda: (folder / "Repository").is_dir() and said("Rechner hinzugefügt."),
                    timeout=10000)
    project = services.projects.find_by_dir(folder)
    assert project.code_dir == folder / "Repository" / "main"           # danach nach main
    assert (project.code_dir / "main.py").is_file()
    assert (folder / "Release" / "Rechner" / "Rechner.exe").is_file()     # Exe-main


def test_declined_rename_is_not_asked_at_start(qtbot, tmp_path, make_services, monkeypatch):
    from tests.test_phase10f import window
    folder = tmp_path / "Rechner"
    files(folder / "Code", ["main.py"])
    services = make_services([])
    win = window(qtbot, services)
    monkeypatch.setattr(folder_rename_flow, "confirm", lambda *a, **k: False)
    project = services.projects.add(folder)
    got = []
    win.controller.folder_renamer.offer_one(project, got.append)
    assert got == [project] and (folder / "Code").is_dir()
    assert project not in win.controller.folder_renamer.candidates()


# -- Lose Exe nach Exe-main -----------------------------------------------------------------------
def release_project(tmp_path, make_services):
    files(tmp_path / "Rechner" / "Repository" / "main", ["main.py"])
    services = make_services([])
    return services.projects.add(tmp_path / "Rechner")


def test_loose_exe_moves_into_its_own_folder(tmp_path, make_services):
    project = release_project(tmp_path, make_services)
    release = tmp_path / "Rechner" / "Release"
    files(release, ["Rechner.exe", "LICENSE"])
    files(release / "_internal", ["python.dll"])
    files(release / "Rechner-v1.0.0", ["Rechner.exe"])                  # Version bleibt
    files(release / "Rechner_branch_neu", ["Rechner.exe"])               # Branch-Exe bleibt
    assert [p.name for p in exe.loose_items(project)] == ["_internal", "LICENSE", "Rechner.exe"]
    home = exe.tidy_release(project)
    assert home == release / "Rechner"
    assert sorted(p.name.lower() for p in home.iterdir()) == ["_internal", "license",
                                                              "rechner.exe"]
    assert sorted(p.name for p in release.iterdir()) == ["Rechner", "Rechner-v1.0.0",
                                                         "Rechner_branch_neu"]
    assert exe.loose_items(project) == []


def test_without_a_loose_exe_nothing_moves(tmp_path, make_services):
    project = release_project(tmp_path, make_services)
    files(tmp_path / "Rechner" / "Release", ["notiz.txt"])
    assert exe.loose_items(project) == []
