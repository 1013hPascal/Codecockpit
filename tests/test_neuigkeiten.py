"""Neuigkeiten und Aktivität (Wunsch des Nutzers vom 22.10.2026).

GitHub ist nachgebaut (FakeGitHub), die Plattform für Kern und Fenster ist erfunden. Alle Namen,
Zahlen und Tokens sind erfunden.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from PySide6.QtCore import Qt

from cockpit.core.git import RemoteAddress
from cockpit.core.secret import Secret
from cockpit.features.activity import activity
from cockpit.features.activity.manifest import MANIFEST as ACTIVITY
from cockpit.features.news import news
from cockpit.features.news.manifest import MANIFEST as NEWS
from cockpit.platforms.activity import (
    COMMENT, FORK, ISSUE, PULL, RELEASE, REVIEW, RUN_FAILED, STAR, DayCount, NewsItem,
    PopularItem, RepoStats, SupportsActivity, Traffic)
from cockpit.platforms.base import (
    Capability, PermissionMissing, Release, ReleaseAsset, RepoRef, SupportsReleases)
from cockpit.platforms.github import GitHubPlatform
from tests.conftest import FakePlatform, make_project, said
from tests.test_github import TOKEN, server  # noqa: F401 (Fixture)

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)
SINCE = "2026-10-20T00:00:00Z"
REPO = "/repos/tester/Tagebuch"


# -- GitHub ----------------------------------------------------------------------------------------
def github() -> GitHubPlatform:
    return GitHubPlatform("https://github.com", Secret(TOKEN), "tester")


def test_github_collects_news_from_others(server):
    from cockpit.platforms.base import RepoRef
    server.route("GET", f"{REPO}/issues", body=[
        {"number": 12, "title": "Suche in PDFs", "user": {"login": "anna"},
         "created_at": "2026-10-21T09:00:00Z", "html_url": "https://github.com/i/12"},
        {"number": 13, "title": "Mein Plan", "user": {"login": "tester"},
         "created_at": "2026-10-21T10:00:00Z"},                       # eigenes zählt nicht
        {"number": 3, "title": "Neue Suche", "user": {"login": "ben"}, "pull_request": {},
         "created_at": "2026-10-21T11:00:00Z"},
        {"number": 2, "title": "Alt", "user": {"login": "ben"},
         "created_at": "2026-10-01T11:00:00Z"},                       # nur geändert, nicht neu
    ])
    server.route("GET", f"{REPO}/issues/comments", body=[
        {"user": {"login": "anna"}, "created_at": "2026-10-21T14:05:00Z",
         "issue_url": "https://api.github.com/repos/tester/Tagebuch/issues/12",
         "html_url": "https://github.com/tester/Tagebuch/issues/12#c1"},
        {"user": {"login": "ben"}, "created_at": "2026-10-21T15:00:00Z",
         "issue_url": "https://api.github.com/repos/tester/Tagebuch/issues/3",
         "html_url": "https://github.com/tester/Tagebuch/pull/3#c2"},
    ])
    server.route("GET", f"{REPO}/pulls/comments", body=[
        {"user": {"login": "ben"}, "created_at": "2026-10-21T16:00:00Z",
         "pull_request_url": "https://api.github.com/repos/tester/Tagebuch/pulls/3"}])
    server.route("GET", REPO, body={"stargazers_count": 101, "forks_count": 2,
                                    "subscribers_count": 3, "open_issues_count": 4})
    server.route("GET", f"{REPO}/stargazers", body=[
        {"user": {"login": "carla"}, "starred_at": "2026-10-21T08:00:00Z"}])
    server.route("GET", f"{REPO}/forks", body=[
        {"owner": {"login": "dora"}, "full_name": "dora/Tagebuch",
         "created_at": "2026-10-21T07:00:00Z"}])
    server.route("GET", f"{REPO}/releases", body=[
        {"name": "1.2", "author": {"login": "tester"}, "published_at": "2026-10-21T06:00:00Z"}])
    server.route("GET", f"{REPO}/actions/runs", body={"workflow_runs": [
        {"name": "Tests", "run_number": 7, "actor": {"login": "tester"},
         "created_at": "2026-10-21T05:00:00Z"}]})
    found = github().news_since(RepoRef("tester", "Tagebuch"), SINCE, "Tester")
    assert [(i.kind, i.number, i.author) for i in found] == [
        (REVIEW, 3, "ben"), (COMMENT, 3, "ben"), (COMMENT, 12, "anna"), (PULL, 3, "ben"),
        (ISSUE, 12, "anna"), (STAR, 0, "carla"), (FORK, 0, "dora"), (RUN_FAILED, 7, "tester")]
    assert found[1].on_pull and not found[2].on_pull
    stars = next(r for r in server.requests if r.url.path.endswith("/stargazers"))
    assert stars.url.params["page"] == "2"                  # die neuesten stehen hinten
    assert stars.headers["Accept"] == "application/vnd.github.star+json"
    assert all(TOKEN not in str(r.url) for r in server.requests)


def test_github_news_skip_missing_sections(server):
    from cockpit.platforms.base import RepoRef
    server.route("GET", f"{REPO}/issues", body=[
        {"number": 12, "title": "Suche", "user": {"login": "anna"},
         "created_at": "2026-10-21T09:00:00Z"}])
    found = github().news_since(RepoRef("tester", "Tagebuch"), SINCE, "tester")
    assert [i.kind for i in found] == [ISSUE]                   # der Rest fehlt (404)


def test_github_traffic_and_stats(server):
    from cockpit.platforms.base import RepoRef
    server.route("GET", f"{REPO}/traffic/views", body={"views": [
        {"timestamp": "2026-10-20T00:00:00Z", "count": 12, "uniques": 4}]})
    server.route("GET", f"{REPO}/traffic/clones", body={"clones": [
        {"timestamp": "2026-10-20T00:00:00Z", "count": 2, "uniques": 1}]})
    server.route("GET", f"{REPO}/traffic/popular/paths", body=[
        {"path": "/tester/Tagebuch", "title": "README", "count": 30, "uniques": 9}])
    server.route("GET", f"{REPO}/traffic/popular/referrers", body=[
        {"referrer": "Google", "count": 12, "uniques": 5}])
    server.route("GET", REPO, body={"stargazers_count": 4, "forks_count": 1,
                                    "subscribers_count": 2, "open_issues_count": 3})
    ref = RepoRef("tester", "Tagebuch")
    traffic = github().traffic(ref)
    assert traffic.views == (DayCount("2026-10-20", 12, 4),)
    assert traffic.clones == (DayCount("2026-10-20", 2, 1),)
    assert traffic.paths == (PopularItem("README", 30, 9),)
    assert traffic.referrers == (PopularItem("Google", 12, 5),)
    assert github().repo_stats(ref) == RepoStats(4, 1, 2, 3)


def test_github_traffic_needs_write_access(server):
    from cockpit.platforms.base import RepoRef
    server.route("GET", f"{REPO}/traffic/views", 403, {"message": "Must have push access"})
    with pytest.raises(PermissionMissing):
        github().traffic(RepoRef("tester", "Tagebuch"))


def test_github_has_the_capability():
    assert Capability.ACTIVITY in github().capabilities()
    assert isinstance(github(), SupportsActivity)


# -- Kern ------------------------------------------------------------------------------------------
class ActivityPlatform(FakePlatform, SupportsActivity):
    """Erfundene Plattform mit Neuigkeiten und Zahlen."""

    def __init__(self) -> None:
        super().__init__()
        self.username = "tester"
        self.news: list[NewsItem] = []
        self.views = Traffic()
        self.stats = RepoStats()
        self.hidden = False
        self.asked: list[str] = []

    def news_since(self, repo, since, me=""):
        self.asked.append(since)
        return list(self.news)

    def traffic(self, repo):
        if self.hidden:
            raise PermissionMissing(Capability.ACTIVITY, "Dem Token fehlt ein Recht.")
        return self.views

    def repo_stats(self, repo):
        return self.stats


class FullPlatform(ActivityPlatform, SupportsReleases):
    """Mit Releases: zusammen 35 Downloads."""

    def releases(self, repo):
        return [Release(1, "v1.2", "1.2", "", "", (ReleaseAsset(1, "Tagebuch.exe", 1, 30),)),
                Release(2, "v1.1", "1.1", "", "", (ReleaseAsset(2, "Tagebuch.exe", 1, 5),))]


def connected(services, projects_root, name: str = "Tagebuch"):
    project = services.projects.add(make_project(projects_root, name))
    services.projects.set_remote(project, RemoteAddress("github.com", "tester", name), None)
    return services.projects.get(project.id)


def item(kind: str, created: str, number: int = 0, author: str = "anna", **kwargs) -> NewsItem:
    return NewsItem(kind, created, author, number, **kwargs)


def test_news_are_stored_once_and_old_ones_go(make_services, projects_root):
    services = make_services([NEWS])
    project = connected(services, projects_root)
    platform = ActivityPlatform()
    platform.news = [item(ISSUE, "2026-10-21T09:00:00Z", 12, title="Suche"),
                     item(COMMENT, "2026-10-21T14:05:00Z", 12)]
    assert news.refresh(services, platform, [project], now=NOW) == 1
    assert platform.asked == ["2026-09-22T12:00:00Z"]                # 30 Tage
    news.refresh(services, platform, [project], now=NOW)
    entries = news.stored(services, SINCE)
    assert [e.item.kind for e in entries] == [COMMENT, ISSUE]          # neueste zuerst, einmal
    news.store(services.database, project.id, [], "2026-10-21T12:00:00Z")
    assert [e.item.kind for e in news.stored(services, SINCE)] == [COMMENT]


def test_news_need_the_feature_and_the_interface(make_services, projects_root):
    services = make_services()
    project = connected(services, projects_root)
    assert news.refresh(services, ActivityPlatform(), [project], now=NOW) == 0
    services = make_services([NEWS])
    project = connected(services, projects_root, "Rechner")
    assert news.refresh(services, FakePlatform(), [project], now=NOW) == 0
    services.features.set_globally_enabled(news.FEATURE_ID, False)
    assert news.refresh(services, ActivityPlatform(), [project], now=NOW) == 0


def test_news_lines_start_with_the_project():
    entry = news.Entry(1, "Tagebuch", item(COMMENT, "2026-10-21T14:05:00Z", 12))
    now = datetime(2026, 10, 22, 12, 0).astimezone()
    text = news.line(entry, now)
    assert text.startswith("Tagebuch: neuer Kommentar zu Issue 12, von anna, gestern ")
    assert news.what(item(PULL, "", 3, title="Neue Suche")) == "neuer Pull Request 3: Neue Suche"
    assert news.what(item(COMMENT, "", 3, on_pull=True)) == "neuer Kommentar zu Pull Request 3"
    assert news.what(item(STAR, "")) == "neuer Stern"
    assert news.what(item(RELEASE, "", title="1.2")) == "neues Release 1.2"
    assert news.what(item(RUN_FAILED, "", 7, title="Tests")) == \
        "GitHub Actions fehlgeschlagen: Tests"
    today = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert news.when(today, now).startswith("heute ")


def test_summary_counts_news_and_projects():
    entries = [news.Entry(1, "Tagebuch", item(ISSUE, "2026-10-21T09:00:00Z", 1)),
               news.Entry(1, "Tagebuch", item(STAR, "2026-10-21T10:00:00Z")),
               news.Entry(2, "Rechner", item(FORK, "2026-10-21T11:00:00Z"))]
    previous = datetime(2026, 10, 20, 12, 0).astimezone()
    text = news.summary(entries, news.iso(previous))
    assert text == "Seit Ihrem letzten Besuch am 20.10.: 3 Neuigkeiten in 2 Projekten."
    assert news.summary(entries[:1], news.iso(previous)).endswith("1 Neuigkeit in 1 Projekt.")
    assert news.summary([], news.iso(previous)) == ""
    assert news.summary(entries, None) == ""                          # erster Start


def test_last_seen_and_periods(make_services):
    services = make_services([NEWS])
    assert news.last_seen(services.database) is None
    news.mark_seen(services.database, NOW)
    assert news.last_seen(services.database) == "2026-10-22T12:00:00Z"
    assert news.since_for(news.SINCE_START, "2026-10-20T08:00:00Z", NOW) == "2026-10-20T08:00:00Z"
    assert news.since_for(news.SINCE_START, None, NOW) == "2026-10-15T12:00:00Z"
    assert news.since_for(news.MONTH, None, NOW) == "2026-09-22T12:00:00Z"


TODAY = date(2026, 10, 22)


def test_activity_is_recorded_once_a_day(make_services, projects_root):
    services = make_services([ACTIVITY])
    project = connected(services, projects_root)
    platform = FullPlatform()
    platform.stats = RepoStats(4, 1, 2, 3)
    platform.views = Traffic((DayCount("2026-10-21", 12, 4), DayCount("2026-10-22", 3, 1)),
                             (DayCount("2026-10-21", 2, 1),),
                             (PopularItem("README", 30, 9),), (PopularItem("Google", 12, 5),))
    assert activity.refresh(services, platform, [project], today=TODAY) == 1
    assert activity.refresh(services, platform, [project], today=TODAY) == 0      # schon heute
    line = activity.project_line(services.database, project, activity.WEEK, TODAY)
    assert line == "Tagebuch: 15 Aufrufe, 2 Klone, 35 Downloads, 4 Sterne"
    # Am nächsten Tag kommt der 22. noch einmal, jetzt vollständig: die größere Zahl gilt
    platform.views = Traffic((DayCount("2026-10-22", 9, 3),))
    activity.record(services.database, platform, project, TODAY + timedelta(days=1))
    rows = activity.daily(services.database, project.id, "2026-10-22")
    assert [(r["day"], r["views"]) for r in rows] == [("2026-10-22", 9)]


def test_star_change_and_owner_only(make_services, projects_root):
    services = make_services([ACTIVITY])
    project = connected(services, projects_root)
    platform = ActivityPlatform()
    platform.stats = RepoStats(3)
    activity.record(services.database, platform, project, TODAY - timedelta(days=8))
    platform.stats = RepoStats(4)
    platform.hidden = True
    activity.record(services.database, platform, project, TODAY)
    line = activity.project_line(services.database, project, activity.WEEK, TODAY)
    assert line == ("Tagebuch: Aufrufe nur für Besitzer sichtbar, 0 Downloads, 4 Sterne, "
                    "plus 1 seit letzter Woche")
    other = connected(services, projects_root, "Rechner")
    assert activity.project_line(services.database, other, activity.WEEK, TODAY) == \
        "Rechner: noch keine Zahlen"


def test_activity_details(make_services, projects_root):
    services = make_services([ACTIVITY])
    project = connected(services, projects_root)
    platform = FullPlatform()
    platform.stats = RepoStats(4, 1, 2, 3)
    platform.views = Traffic((DayCount("2026-10-21", 12, 4),), (DayCount("2026-10-21", 2, 1),),
                             (PopularItem("README", 30, 9),), (PopularItem("Google", 12, 5),))
    activity.record(services.database, platform, project, TODAY)
    lines = activity.details(services.database, project, activity.MONTH, TODAY)
    assert lines[:3] == ["Tagebuch, Letzte 30 Tage", "Aufrufe: 12, Besucher: 4",
                         "Klone: 2, klonende Personen: 1"]
    assert "Sterne: 4, Forks: 1, Beobachter: 2, Downloads: 35" in lines
    assert "21.10.2026: 12 Aufrufe, 2 Klone" in lines
    assert "1.2: 30 Downloads" in lines
    assert "README: 30 Aufrufe, 9 Besucher" in lines
    assert "Google: 12 Aufrufe" in lines


def test_database_has_the_new_tables(make_services):
    names = make_services().database.table_names()
    assert {"news", "activity_daily", "activity_snapshot"} <= set(names)


# -- Fenster ---------------------------------------------------------------------------------------
def news_window(qtbot, make_services, projects_root, previous: str | None = SINCE):
    from tests.test_phase10f import window
    services = make_services([NEWS, ACTIVITY])
    project = connected(services, projects_root)
    if previous:
        services.database.set_value(news.LAST_SEEN_KEY, previous)
    recent = news.iso(datetime.now(timezone.utc) - timedelta(hours=1))
    news.store(services.database, project.id, [
        item(COMMENT, recent, 12, url="https://github.com/tester/Tagebuch/issues/12#c1"),
        item(STAR, recent, author="carla")], "2000-01-01T00:00:00Z")
    win = window(qtbot, services)
    return services, win, project


def test_menu_and_announcement_after_the_start(qtbot, make_services, projects_root):
    from cockpit.ui.announcer import announcer
    services, win, _project = news_window(qtbot, make_services, projects_root)
    texts = [a.text() for a in win.menuBar().actions()]
    assert "&Neuigkeiten" in texts
    win.news.after_refresh()
    assert said("Seit Ihrem letzten Besuch am 20.10.: 2 Neuigkeiten in 1 Projekt.")
    before = len(announcer.messages)
    win.news.after_refresh()                                       # nur einmal pro Sitzung
    assert len(announcer.messages) == before
    win.close()
    assert news.last_seen(services.database) > SINCE                # erst beim Beenden gesetzt


def test_no_announcement_on_the_first_start(qtbot, make_services, projects_root):
    _services, win, _project = news_window(qtbot, make_services, projects_root, previous=None)
    win.news.after_refresh()
    assert not said("Seit Ihrem letzten Besuch")


def test_menu_hides_without_the_features(qtbot, make_services, projects_root):
    from tests.test_phase10f import window
    win = window(qtbot, make_services())
    assert not win.news.menu.menuAction().isVisible()
    win.news.open_news()
    assert said("Die Neuigkeiten sind ausgeschaltet.")


def test_news_dialog_lists_and_shows_in_cockpit(qtbot, make_services, projects_root,
                                                monkeypatch):
    from cockpit.ui import news_dialogs
    services, win, project = news_window(qtbot, make_services, projects_root)
    dialog = news_dialogs.NewsDialog(services, SINCE, win)
    qtbot.addWidget(dialog)
    texts = [dialog.list.item(r).text() for r in range(dialog.list.count())]
    assert texts[0].startswith("Tagebuch: neuer Kommentar zu Issue 12, von anna, heute ")
    assert texts[1].startswith("Tagebuch: neuer Stern, von carla")
    assert dialog.windowTitle() == "Neuigkeiten: 2, Seit dem letzten Start"
    assert [dialog.period.itemText(i) for i in range(dialog.period.count())] == [
        "Seit dem letzten Start", "Letzte 7 Tage", "Letzte 30 Tage"]
    assert not dialog.cockpit_button.isHidden()
    opened = []
    monkeypatch.setattr(news_dialogs.browser_login_dialog, "open_url", opened.append)
    dialog.list.setCurrentRow(1)
    assert dialog.cockpit_button.isHidden()                      # ein Stern hat kein Issue
    dialog.list.setCurrentRow(0)
    dialog.open_browser()
    assert opened == ["https://github.com/tester/Tagebuch/issues/12#c1"]
    shown = []
    from cockpit.ui import issue_flow
    monkeypatch.setattr(issue_flow.IssueRunner, "open_list",
                        lambda self, select=0: shown.append((self.project.id, select)))
    monkeypatch.setattr(news_dialogs.NewsDialog, "exec",
                        lambda self: (self.list.setCurrentRow(0), self.show_in_cockpit()))
    win.news.open_news()
    assert shown == [(project.id, 12)]


def test_news_dialog_says_when_empty(qtbot, make_services, projects_root):
    from cockpit.ui import news_dialogs
    services = make_services([NEWS])
    dialog = news_dialogs.NewsDialog(services, SINCE)
    qtbot.addWidget(dialog)
    assert dialog.list.item(0).text() == "Keine Neuigkeiten."
    assert dialog.cockpit_button.isHidden() and dialog.browser_button.isHidden()


def test_activity_dialog_lines_details_and_discussion(qtbot, make_services, projects_root,
                                                      monkeypatch):
    from cockpit.ui import news_dialogs
    services, win, project = news_window(qtbot, make_services, projects_root)
    platform = ActivityPlatform()
    platform.stats = RepoStats(4)
    activity.record(services.database, platform, project)
    dialog = news_dialogs.ActivityDialog(services, win)
    qtbot.addWidget(dialog)
    assert dialog.list.item(0).text() == "Tagebuch: 0 Aufrufe, 0 Klone, 0 Downloads, 4 Sterne"
    assert dialog.windowTitle() == "Aktivität: 1 Projekt, Letzte 7 Tage"
    shown = []
    monkeypatch.setattr(news_dialogs.TextDialog, "exec", lambda self: shown.append(self.lines))
    dialog.list.setFocus()
    qtbot.keyClick(dialog.list, Qt.Key.Key_Return)
    assert shown and shown[0][0] == "Tagebuch, Letzte 7 Tage"
    listed = []

    def fake_exec(self):
        listed.extend(self.list.item(r).text() for r in range(self.list.count()))
    monkeypatch.setattr(news_dialogs.NewsDialog, "exec", fake_exec)
    dialog.show_discussion()
    assert len(listed) == 1 and listed[0].startswith("Tagebuch: neuer Kommentar zu Issue 12")


def test_remote_refresh_fetches_news_and_activity(make_services, projects_root):
    """Der Aufruf aus window_status: Neuigkeiten und Zahlen kommen zusammen mit den Repositories."""
    from cockpit.ui.window_status import refresh_activity
    services = make_services([NEWS, ACTIVITY])
    project = connected(services, projects_root)
    platform = ActivityPlatform()
    platform.news = [item(ISSUE, news.iso(datetime.now(timezone.utc)), 12)]
    refresh_activity(services, platform, [project])
    assert len(news.stored(services, SINCE)) == 1
    assert activity.snapshot(services.database, project.id) is not None


def test_testdata_bring_news_and_numbers(make_services, projects_root):
    from cockpit import testdata
    services = make_services([NEWS, ACTIVITY])
    tagebuch = services.projects.add(make_project(projects_root, "Tagebuch"))
    services.projects.add(make_project(projects_root, "PDF-Chat"))
    testdata.add_news(services)
    previous = news.last_seen(services.database)
    assert news.summary(news.stored(services, previous), previous).endswith(
        "4 Neuigkeiten in 2 Projekten.")
    line = activity.project_line(services.database, tagebuch, activity.WEEK)
    assert line.startswith("Tagebuch: ") and line.endswith("4 Sterne, plus 1 seit letzter Woche")