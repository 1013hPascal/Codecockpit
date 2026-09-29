"""Phase 14: Releases und GitHub Actions.

GitHub wird mit httpx.MockTransport ersetzt. Alle Geheimnisse sind erfunden.
"""
from __future__ import annotations

import json

import httpx
import pytest

from cockpit.core.git import RemoteAddress
from cockpit.core.project_status import ProjectStatus, project_line
from cockpit.features.releases import runs
from cockpit.features.releases.manifest import MANIFEST
from cockpit.platforms.base import RepoRef, Release, ReleaseAsset, WorkflowRun
from tests.conftest import make_project, said
from tests.test_phase10 import _reset_transport, github  # noqa: F401

REF = RepoRef("tester", "Rechner")
RUN = {"id": 7, "name": "Tests", "status": "completed", "conclusion": "failure",
       "head_branch": "main", "created_at": "2026-09-29T12:10:00Z", "display_title": "Neue Suche",
       "html_url": "https://github.com/tester/Rechner/actions/runs/7"}


# -- GitHub -------------------------------------------------------------------------------------
def test_releases_with_downloads_notes_update_and_delete():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        if request.method == "GET":
            return httpx.Response(200, json=[{
                "id": 1, "tag_name": "v1.4.0", "name": "Version 1.4.0", "body": "Neu: Suche.",
                "html_url": "https://github.com/tester/Rechner/releases/tag/v1.4.0",
                "published_at": "2026-09-29T10:00:00Z", "upload_url": "",
                "assets": [{"id": 5, "name": "Rechner.exe", "size": 10, "download_count": 12}]}])
        if request.method == "PATCH":
            body = json.loads(request.content)
            return httpx.Response(200, json={"id": 1, "tag_name": "v1.4.0", "body": body["body"],
                                             "assets": []})
        return httpx.Response(204)

    platform = github(handler)
    release = platform.releases(REF)[0]
    assert release.body == "Neu: Suche." and release.downloads == 12
    assert runs.release_line(release) == "1.4.0, 29.09.2026, 12 Downloads, mit Exe"
    assert platform.update_release_notes(REF, release, "Neu: Suche in PDFs.").body == \
        "Neu: Suche in PDFs."
    platform.delete_release(REF, release)
    assert seen[-1] == ("DELETE", "/repos/tester/Rechner/releases/1")


def test_workflow_runs_jobs_log_and_rerun():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.host, request.url.path))
        path = request.url.path
        if path.endswith("/actions/runs"):
            return httpx.Response(200, json={"workflow_runs": [RUN]})
        if path.endswith("/runs/7/jobs"):
            return httpx.Response(200, json={"jobs": [{
                "id": 9, "name": "test", "conclusion": "failure",
                "steps": [{"name": "Checkout", "conclusion": "success"},
                          {"name": "pytest", "conclusion": "failure"}]}]})
        if path.endswith("/jobs/9/logs"):
            return httpx.Response(302, headers={"Location": "https://logs.example.com/9.txt"})
        if request.url.host == "logs.example.com":
            assert "Authorization" not in request.headers         # Token geht nicht mit
            return httpx.Response(200, text="2026-09-29T12:10:01.1Z ##[error]Test fehlgeschlagen\n")
        if path.endswith("/actions/workflows"):
            return httpx.Response(200, json={"total_count": 2})
        return httpx.Response(201)

    platform = github(handler)
    run = platform.workflow_runs(REF)[0]
    assert run.failed and run.title == "Neue Suche"
    assert runs.run_line(run).startswith("Fehlgeschlagen: Tests, Branch main, 29.09.2026")
    job = platform.run_jobs(REF, 7)[0]
    assert job.failed_steps == ("pytest",)
    assert runs.readable_log(platform.job_log(REF, 9)) == ["Fehler: Test fehlgeschlagen"]
    platform.rerun(REF, run)
    assert seen[-1][2] == "/repos/tester/Rechner/actions/runs/7/rerun-failed-jobs"
    assert platform.has_workflows(REF)


# -- Hilfen -------------------------------------------------------------------------------------
def test_readable_log_keeps_errors_and_the_end():
    text = "\n".join([f"2026-09-29T12:00:0{i % 10}.0Z Zeile {i}" for i in range(100)]
                     + ["2026-09-29T12:00:00.0Z \x1b[31m##[error]Kaputt\x1b[0m"])
    text = text.replace("Zeile 3\n", "##[error]Früher Fehler\n", 1)
    lines = runs.readable_log(text, lines=5)
    assert lines[0] == "Fehler: Früher Fehler" and lines[-1] == "Fehler: Kaputt"
    assert len(lines) == 6


def test_failed_state_in_the_project_line(tmp_path, make_services, projects_root):
    services = make_services([MANIFEST])
    remote = RemoteAddress("github.com", "tester", "Rechner")
    runs.remember_failed(services.database, remote.key, True)
    assert runs.last_failed(services.database, remote.key)
    services.projects.add(make_project(projects_root, "Rechner"))
    project = services.projects.all()[0]
    status = ProjectStatus(project.id, actions_failed=True)
    assert project_line(project, status).endswith("GitHub Actions fehlgeschlagen")
    runs.remember_failed(services.database, remote.key, False)
    assert not runs.last_failed(services.database, remote.key)


# -- Oberfläche -----------------------------------------------------------------------------------
def test_releases_dialog_buttons_and_notes(qtbot, make_services, projects_root):
    from cockpit.ui import releases_flow
    services = make_services([MANIFEST])
    services.projects.add(make_project(projects_root, "Rechner"))
    project = services.projects.all()[0]
    release = Release(1, "v1.4.0", "Version 1.4.0", "https://example.com/r", "2026-09-29T10:00Z",
                      (ReleaseAsset(5, "Rechner.zip", 10, 3),), body="Neu.")
    dialog = releases_flow.ReleasesDialog(None, project, [release])
    qtbot.addWidget(dialog)
    assert dialog.list.item(0).text() == "1.4.0, 29.09.2026, 3 Downloads, mit ZIP-Datei"
    assert dialog.delete_button.isVisibleTo(dialog)
    empty = releases_flow.ReleasesDialog(None, project, [])
    qtbot.addWidget(empty)
    assert empty.list.item(0).text() == "Noch keine Releases."
    assert not empty.delete_button.isVisibleTo(empty)


def test_actions_dialog_offers_error_only_for_failed_runs(qtbot, make_services, projects_root):
    from cockpit.ui import releases_flow
    services = make_services([MANIFEST])
    services.projects.add(make_project(projects_root, "Rechner"))
    project = services.projects.all()[0]
    ok = WorkflowRun(1, "Tests", "completed", "success", "main", "2026-09-29T12:00:00Z", "a", "u")
    bad = WorkflowRun(2, "Tests", "completed", "failure", "main", "2026-09-29T13:00:00Z", "b", "u")
    dialog = releases_flow.ActionsDialog(None, project, [bad, ok])
    qtbot.addWidget(dialog)
    assert dialog.error_button.isVisibleTo(dialog)
    dialog.list.setCurrentRow(1)
    assert not dialog.error_button.isVisibleTo(dialog)
    assert dialog.list.item(1).text().startswith("Erfolgreich: Tests")


def test_release_after_new_version(qtbot, make_services, projects_root, monkeypatch):
    from cockpit.ui import releases_flow
    from tests.test_phase10f import window
    services = make_services([MANIFEST])
    services.projects.add(make_project(projects_root, "Rechner"))
    win = window(qtbot, services)
    flow = win.controller.releases
    project = services.projects.all()[0]
    monkeypatch.setattr(flow, "active", lambda p: True)
    answers = []
    monkeypatch.setattr(releases_flow, "confirm", lambda parent, title, text, **kw:
                        answers.append(text) or False)
    assert not flow.offer_after_version(project, "1.4.0")         # Später: Pull Request geht vor
    assert answers[0] == "Für Version 1.4.0 ein Release auf GitHub anlegen?"
    published = []
    monkeypatch.setattr(releases_flow, "confirm", lambda parent, title, text, **kw: True)
    monkeypatch.setattr(flow, "publish_source", lambda p, v: published.append(v))
    assert flow.offer_after_version(project, "1.4.0") and published == ["1.4.0"]


def test_actions_entry_only_with_workflows(tmp_path, make_services, projects_root):
    from cockpit.ui.releases_flow import ReleasesActions
    services = make_services([MANIFEST])
    services.projects.add(make_project(projects_root, "Rechner"))
    project = services.projects.all()[0]
    assert not ReleasesActions.has_workflows(project)
    (project.code_dir / ".github" / "workflows").mkdir(parents=True)
    (project.code_dir / ".github" / "workflows" / "tests.yml").write_text("on: push\n",
                                                                            encoding="utf-8")
    assert ReleasesActions.has_workflows(project)
