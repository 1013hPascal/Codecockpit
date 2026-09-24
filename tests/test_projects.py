"""Projekte finden, auflisten und cockpit.toml."""
from __future__ import annotations

import os
import shutil
import time

import pytest

from cockpit.core.errors import CockpitError
from cockpit.core.projects import read_config
from tests.conftest import make_project


def test_scan_finds_folders_with_code(make_services, projects_root):
    make_project(projects_root, "PDF-Chat", exe=True)
    make_project(projects_root, "Tagebuch")
    (projects_root / "Kein Projekt").mkdir()
    services = make_services()
    found = services.projects.scan(projects_root)
    assert sorted(p.name for p in found) == ["PDF-Chat", "Tagebuch"]
    assert services.projects.scan(projects_root) == []          # zweites Mal nichts Neues
    projects = {p.name: p for p in services.projects.all()}
    assert projects["PDF-Chat"].has_exe_dir
    assert not projects["Tagebuch"].has_exe_dir


def test_newest_project_is_listed_first(make_services, projects_root):
    old = make_project(projects_root, "Alt")
    new = make_project(projects_root, "Neu")
    now = time.time()
    os.utime(old / "Code", (now - 1000, now - 1000))
    os.utime(new / "Code", (now, now))
    services = make_services()
    services.projects.scan(projects_root)
    assert [p.name for p in services.projects.all()] == ["Neu", "Alt"]


def test_missing_folder_stays_in_list(make_services, projects_root):
    folder = make_project(projects_root, "Notizen")
    services = make_services()
    services.projects.scan(projects_root)
    shutil.rmtree(folder)
    project = services.projects.all()[0]
    assert project.name == "Notizen"
    assert not project.folder_found


def test_add_requires_code_folder(make_services, projects_root):
    (projects_root / "Leer").mkdir()
    with pytest.raises(CockpitError, match="keinen Unterordner Code"):
        make_services().projects.add(projects_root / "Leer")


def test_remove_only_forgets_the_project(make_services, projects_root):
    folder = make_project(projects_root, "A")
    services = make_services()
    project = services.projects.add(folder)
    services.projects.remove(project.id)
    assert services.projects.all() == []
    assert folder.is_dir()


def test_newest_exe(make_services, projects_root):
    folder = make_project(projects_root, "A", exe=True)
    services = make_services()
    project = services.projects.add(folder)
    assert project.newest_exe() is None
    (folder / "Exe" / "A.exe").write_text("x")
    assert project.newest_exe().name == "A.exe"


def test_features_are_stored_in_cockpit_toml(make_services, projects_root):
    folder = make_project(projects_root, "A")
    (folder / "Code" / "cockpit.toml").write_text('is_cockpit = true\n', encoding="utf-8")
    services = make_services()
    project = services.projects.add(folder)
    assert services.projects.enabled_features(project) is None
    services.projects.set_enabled_features(project, {"exe", "readme"})
    assert services.projects.enabled_features(project) == {"exe", "readme"}
    config = read_config(folder / "Code")
    assert config["is_cockpit"] is True                  # andere Einträge bleiben erhalten
    assert config["features"]["enabled"] == ["exe", "readme"]


def test_broken_cockpit_toml_does_not_crash(make_services, projects_root):
    folder = make_project(projects_root, "A")
    (folder / "Code" / "cockpit.toml").write_text("das ist [kein toml", encoding="utf-8")
    services = make_services()
    project = services.projects.add(folder)
    assert services.projects.enabled_features(project) is None
