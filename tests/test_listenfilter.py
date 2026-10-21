"""Filter „Anzeigen:“ über den Projekten und Zeichen für Offenes (Wunsch des Nutzers vom 07.10.2026).

Die Projekte sind kleine Ordner ohne Git. Ihren Stand bekommt die Liste direkt, wie aus dem
Hintergrund. Keine echte Plattform.
"""
from __future__ import annotations

import dataclasses

from cockpit.core import list_filter
from cockpit.core.actions import Target
from cockpit.core.git import RemoteAddress, RepoStatus
from cockpit.core.project_status import ProjectStatus, project_line
from cockpit.core.worktrees import Worktree
from tests.conftest import make_project, said

REMOTE_URL = "https://github.com/tester/Tagebuch.git"


def status(project_id, **values) -> ProjectStatus:
    repo = RepoStatus(is_repo=True, branch="main", upstream="origin/main",
                      remote_url=values.pop("remote_url", REMOTE_URL), has_commits=True)
    for key in ("changed", "ahead", "behind"):
        if key in values:
            setattr(repo, key, values.pop(key))
    return ProjectStatus(project_id, repo=repo, **values)


def local_status(project_id) -> ProjectStatus:
    return status(project_id, remote_url="")


# -- Kern ----------------------------------------------------------------------------------------
def test_open_things_count(make_services, projects_root):
    project = make_services().projects.add(make_project(projects_root, "Tagebuch"))
    assert not list_filter.is_open(status(project.id))
    assert list_filter.is_open(status(project.id, changed=["a.py"]))
    assert list_filter.is_open(status(project.id, ahead=2))
    assert list_filter.is_open(status(project.id, behind=1))
    assert list_filter.is_open(status(project.id, repo_pulls=1))
    assert list_filter.is_open(status(project.id, review_requests=1))
    tree = Worktree(project.code_dir, "suche", "suche")
    inner = status(project.id, ahead=1)
    assert list_filter.is_open(status(project.id, worktrees=[(tree, inner)]))
    assert not list_filter.is_open(None)                       # Stand noch unbekannt


def test_matches_each_kind(make_services, projects_root):
    project = make_services().projects.add(make_project(projects_root, "Tagebuch"))
    online = status(project.id, has_release=True)
    offline = local_status(project.id)
    assert list_filter.matches(project, online, list_filter.GITHUB)
    assert not list_filter.matches(project, offline, list_filter.GITHUB)
    assert list_filter.matches(project, offline, list_filter.LOCAL)
    assert list_filter.matches(project, online, list_filter.RELEASE)
    assert not list_filter.matches(project, offline, list_filter.RELEASE)
    remembered = dataclasses.replace(project, remote=RemoteAddress("github.com", "t", "x"))
    assert list_filter.matches(remembered, None, list_filter.GITHUB)    # vor dem Stand
    assert list_filter.matches_remote(list_filter.GITHUB)
    assert not list_filter.matches_remote(list_filter.LOCAL)


def test_markers_and_text(make_services, projects_root):
    project = make_services().projects.add(make_project(projects_root, "Tagebuch"))
    busy = status(project.id, changed=["a.py"], ahead=1, behind=2, repo_pulls=2,
                  review_requests=1, pending=1)
    assert list_filter.markers(busy) == "● ↑ ↓ PR R"
    assert list_filter.markers(status(project.id)) == ""
    line = project_line(project, busy)
    assert line.endswith("2 offene Pull Requests, 1 Review angefragt")
    assert list_filter.row_text(list_filter.ALL) == "Anzeigen: Alle Projekte"
    assert list_filter.row_text(list_filter.OPEN, shown=0) == ("Anzeigen: Mit offenen Sachen, "
                                                              "keine Projekte")


# -- Liste ---------------------------------------------------------------------------------------
def three_projects(qtbot, make_services, projects_root):
    from tests.test_phase10f import window
    services = make_services()
    projects = {name: services.projects.add(make_project(projects_root, name))
                for name in ("Tagebuch", "Rechner", "Notizen")}
    web = services.collections.create("Web")
    services.collections.set_members(web.id, {projects["Rechner"].id, projects["Notizen"].id})
    win = window(qtbot, services)
    listing = win.project_list
    listing.update_status(status(projects["Tagebuch"].id, ahead=1, pending=1),
                          projects["Tagebuch"])
    listing.update_status(status(projects["Rechner"].id), projects["Rechner"])
    listing.update_status(local_status(projects["Notizen"].id), projects["Notizen"])
    return services, win, projects


def project_rows(listing):
    return [t for t in listing.texts() if t.split(",")[0] in ("Tagebuch", "Rechner", "Notizen")]


def test_filter_row_sits_above_the_projects(qtbot, make_services, projects_root):
    _services, win, _projects = three_projects(qtbot, make_services, projects_root)
    texts = win.project_list.texts()
    assert texts[:4] == ["Neue Projektsammlung", "Projekt vom Rechner hinzufügen",
                         "Projekt von GitHub herunterladen", "Anzeigen: Alle Projekte"]
    assert win.project_list.select(Target.LIST_FILTER, None)
    assert [e.label for e in win.current_entries()] == ["Liste filtern …, Alle Projekte"]


def test_open_filter_hides_the_rest_and_counts_in_collections(qtbot, make_services,
                                                              projects_root):
    services, win, projects = three_projects(qtbot, make_services, projects_root)
    listing = win.project_list
    listing.set_filter(list_filter.OPEN, speak=True)
    assert said("Mit offenen Sachen, 1 Projekt.")
    assert "Anzeigen: Mit offenen Sachen, 1 Projekt" in listing.texts()
    assert [t.split(",")[0] for t in project_rows(listing)] == ["Tagebuch"]
    assert not any(t.startswith("Sammlung Web") for t in listing.texts())     # nichts Passendes darin
    assert listing.current_target() == (Target.LIST_FILTER, None)
    assert services.database.get_value(list_filter.FILTER_KEY) == list_filter.OPEN
    listing.set_filter(list_filter.GITHUB)
    web = next(t for t in listing.texts() if t.startswith("Sammlung Web"))
    assert web.startswith("Sammlung Web, 1 von 2 Projekten")
    listing.open_collection(services.collections.all()[0].id, speak=False)
    assert [t.split(",")[0] for t in project_rows(listing)] == ["Rechner"]


def test_rows_come_and_go_with_the_status(qtbot, make_services, projects_root):
    _services, win, projects = three_projects(qtbot, make_services, projects_root)
    listing = win.project_list
    listing.set_filter(list_filter.OPEN)
    rechner = projects["Rechner"]
    listing.update_status(status(rechner.id, behind=3), rechner)
    qtbot.waitUntil(lambda: any(t.startswith("Sammlung Web, 1 von 2") for t in listing.texts()),
                    timeout=2000)
    assert "Anzeigen: Mit offenen Sachen, 2 Projekte" in listing.texts()


def test_markers_follow_the_status(qtbot, make_services, projects_root):
    _services, win, projects = three_projects(qtbot, make_services, projects_root)
    listing = win.project_list
    tagebuch = projects["Tagebuch"].id
    assert listing.marker_of(tagebuch) == "↑"
    row = listing.row_of(Target.PROJECT, tagebuch)
    assert not listing.item(row).icon().isNull()
    listing.update_status(status(tagebuch), projects["Tagebuch"])
    assert listing.item(row).icon().isNull()


def test_filter_is_restored_at_start(qtbot, make_services, projects_root):
    from tests.test_phase10f import window
    services = make_services()
    services.projects.add(make_project(projects_root, "Tagebuch"))
    services.database.set_value(list_filter.FILTER_KEY, list_filter.LOCAL)
    win = window(qtbot, services)
    assert win.project_list.filter_kind == list_filter.LOCAL
    assert "Anzeigen: Nur auf dem Rechner, 1 Projekt" in win.project_list.texts()


def test_enter_on_the_filter_row_opens_the_choice(qtbot, make_services, projects_root,
                                                  monkeypatch):
    from PySide6.QtCore import Qt
    from cockpit.ui import project_list as listing_module
    _services, win, _projects = three_projects(qtbot, make_services, projects_root)
    offered = []
    monkeypatch.setattr(listing_module, "pick_filter", lambda widget, names, current:
                        offered.append((list(names.values()), current)) or list_filter.LOCAL)
    win.project_list.select(Target.LIST_FILTER, None)
    win.project_list.setFocus()
    qtbot.keyClick(win.project_list, Qt.Key.Key_Return)
    assert offered == [(["Alle Projekte", "Mit offenen Sachen", "Auf GitHub", "Mit Release",
                         "Nur auf dem Rechner"], list_filter.ALL)]
    assert win.project_list.filter_kind == list_filter.LOCAL
    assert said("Nur auf dem Rechner, 1 Projekt.")
