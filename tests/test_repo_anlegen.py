"""Repository anlegen, wenn es auf der Plattform fehlt, und Adresse nach dem Löschen entfernen
(Rückmeldung des Nutzers vom 04.10.2026: Chatbot-fuer-Text hatte die Adresse eines gelöschten
Repositorys, das Cockpit bot das Anlegen nicht an). Die Plattform ist eine Attrappe."""
from __future__ import annotations

import dataclasses
from types import SimpleNamespace

import pytest

from cockpit.core import git, repo_admin, upload
from cockpit.core.actions import ActionContext, Target
from cockpit.core.git import RemoteAddress
from cockpit.platforms.base import NotFound, RepoInfo, RepoRef
from tests.conftest import said
from tests.test_phase5a import sh
from tests.test_phase5c import setup_repo

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

URL = "https://github.com/tester/Chatbot-fuer-Text.git"


class FakePlatform:
    def __init__(self, exists: bool) -> None:
        self.exists = exists
        self.created: list[str] = []

    def repo_info(self, ref):
        if not self.exists:
            raise NotFound("Nicht gefunden.")
        return RepoInfo(ref, True, False, "main", f"https://github.com/{ref.owner}/{ref.name}")

    def create_repo(self, new):
        self.created.append(new.name)
        return RepoRef("tester", new.name)

    def clone_url(self, ref):
        return f"https://github.com/{ref.owner}/{ref.name}.git"


def chatbot(tmp_path, projects_root, make_services):
    _bare, code, _other = setup_repo(tmp_path, projects_root)
    sh(code, "remote", "set-url", "origin", URL)
    services = make_services([])
    project = services.projects.add(code.parent)
    return services, project, code


# -- Kern -------------------------------------------------------------------------------------------
def test_missing_repo_is_found(tmp_path, projects_root, make_services):
    services, project, code = chatbot(tmp_path, projects_root, make_services)
    assert upload.repo_missing(FakePlatform(False), code)
    assert not upload.repo_missing(FakePlatform(True), code)
    sh(code, "remote", "remove", "origin")
    assert not upload.repo_missing(FakePlatform(False), code)          # ohne Adresse: nein


def test_create_step_makes_the_missing_repo(tmp_path, projects_root, make_services):
    services, project, code = chatbot(tmp_path, projects_root, make_services)
    platform = FakePlatform(False)
    spec = upload.UploadSpec("Chatbot-neu", "Chat", True, "MIT")
    context = SimpleNamespace(project=project, data={"spec": spec, "platform": platform})
    result = upload._step_create(context)
    assert result.ok and platform.created == ["Chatbot-neu"]
    assert git.config_get(code, "remote.origin.url") == "https://github.com/tester/Chatbot-neu.git"
    platform = FakePlatform(True)                                        # gibt es: nichts anlegen
    context.data["platform"] = platform
    assert upload._step_create(context).ok and platform.created == []


def test_repo_missing_through_the_account(tmp_path, projects_root, make_services, monkeypatch):
    services, project, code = chatbot(tmp_path, projects_root, make_services)
    monkeypatch.setattr(services, "account_for_host", lambda host: SimpleNamespace(id=7))
    monkeypatch.setattr(services, "platform", lambda account_id: FakePlatform(False))
    assert repo_admin.repo_missing(services, project)


def test_forget_address_also_for_removed_projects(tmp_path, projects_root, make_services,
                                                  home):
    services, project, code = chatbot(tmp_path, projects_root, make_services)
    services.projects.remove(project.id)                       # aus der Liste entfernt
    cut = repo_admin.forget_address(services, RemoteAddress("github.com", "tester",
                                                            "Chatbot-fuer-Text"))
    assert cut == ["Tagebuch"] and git.config_get(code, "remote.origin.url") == ""


# -- Oberfläche --------------------------------------------------------------------------------------
def test_missing_repo_shows_the_create_action(qtbot, tmp_path, projects_root, make_services):
    from cockpit.core import project_status
    from tests.test_phase10f import window
    services, project, code = chatbot(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    controller = win.controller
    project = dataclasses.replace(project, remote=RemoteAddress("github.com", "tester",
                                                                "Chatbot-fuer-Text"))
    status = project_status.compute(project)
    labels = lambda target: [e.action.text for e in controller_entries(win, project, target,  # noqa
                                                                         status)]
    assert "Repository auf GitHub anlegen und hochladen …" not in labels(Target.PROJECT)
    assert "Änderungen auf GitHub hochladen …" in labels(Target.CODE)
    controller.missing_repos.add(project.id)
    assert "Repository auf GitHub anlegen und hochladen …" in labels(Target.PROJECT)
    assert "Auf GitHub hochladen …" in labels(Target.CODE)
    assert "Änderungen auf GitHub hochladen …" not in labels(Target.CODE)


def controller_entries(win, project, target, status):
    from cockpit.core import core_actions
    from cockpit.core.actions import entries_for
    context = ActionContext(win.services, project, target, status=status)
    return entries_for(core_actions.all_actions(context) + win.controller.actions(), context)


def test_manage_offers_to_create_when_missing(qtbot, tmp_path, projects_root, make_services,
                                             monkeypatch):
    from cockpit.ui import project_actions, vault_ui
    from tests.test_phase10f import window
    services, project, code = chatbot(tmp_path, projects_root, make_services)
    project = dataclasses.replace(project, remote=RemoteAddress("github.com", "tester",
                                                                "Chatbot-fuer-Text"))
    win = window(qtbot, services)
    monkeypatch.setattr(vault_ui, "ensure_unlocked", lambda *a: True)
    monkeypatch.setattr(services, "platform_for", lambda p: FakePlatform(False))
    asked = []
    monkeypatch.setattr(project_actions, "confirm",
                        lambda parent, title, text, **k: asked.append(text) or False)
    win.controller.manage_action(ActionContext(services, project, Target.PROJECT))
    qtbot.waitUntil(lambda: bool(asked), timeout=10000)
    assert asked[0].startswith("Das Repository tester/Chatbot-fuer-Text gibt es auf GitHub "
                               "noch nicht. Jetzt anlegen und hochladen?")
    assert project.id in win.controller.missing_repos


@pytest.mark.parametrize("choice", [0, 1])
def test_deleting_the_repo_always_removes_the_address(qtbot, tmp_path, projects_root,
                                                      make_services, monkeypatch, choice):
    from cockpit.ui import repo_dialogs
    services, project, code = chatbot(tmp_path, projects_root, make_services)
    info = RepoInfo(RepoRef("tester", "Chatbot-fuer-Text"), True, False, "main", URL)
    dialog = repo_dialogs.ManageRepoDialog(services, project, FakePlatform(True), info)
    qtbot.addWidget(dialog)
    monkeypatch.setattr(repo_dialogs, "ask_buttons", lambda *a, **k: choice)
    dialog._deleted()
    assert git.config_get(code, "remote.origin.url") == ""
    assert said("Chatbot-fuer-Text ist auf GitHub gelöscht.")
