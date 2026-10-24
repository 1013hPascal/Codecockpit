"""Neuigkeiten und Aktivität auf GitHub: Issues, Kommentare, Sterne, Forks, Releases, fehlgeschlagene
Läufe, Aufrufe und Klone (Wunsch des Nutzers vom 22.10.2026).

Teil von GitHubPlatform (github.py). Jeder Bereich ist eine eigene Anfrage. Fehlt für einen Bereich
das Recht oder gibt es ihn nicht (zum Beispiel keine Actions), fehlt nur dieser Bereich.
"""
from __future__ import annotations

import logging

from cockpit.platforms.activity import (
    COMMENT, FORK, ISSUE, PULL, RELEASE, REVIEW, RUN_FAILED, STAR, DayCount, NewsItem,
    PopularItem, RepoStats, Traffic)
from cockpit.platforms.base import Capability, NotFound, PermissionMissing, RepoRef

log = logging.getLogger(__name__)

STAR_JSON = "application/vnd.github.star+json"       # Sterne mit Zeitpunkt


def _login(item: dict | None) -> str:
    return (item or {}).get("login", "")


def _number(url: str) -> int:
    tail = (url or "").rstrip("/").rpartition("/")[2]
    return int(tail) if tail.isdigit() else 0


def _days(items: list) -> tuple[DayCount, ...]:
    return tuple(DayCount((i.get("timestamp") or "")[:10], int(i.get("count") or 0),
                          int(i.get("uniques") or 0)) for i in items or [])


class GitHubActivity:
    """Neuigkeiten und Zahlen zur Beliebtheit."""

    def _activity_get(self, path: str, action: str, **kwargs):
        return self.request("GET", path, action, Capability.ACTIVITY, **kwargs).json()

    def _section(self, name: str, read) -> list[NewsItem]:
        try:
            return read()
        except (NotFound, PermissionMissing) as exc:
            log.info("Neuigkeiten, %s: %s", name, exc.message)
            return []

    def news_since(self, repo: RepoRef, since: str, me: str = "") -> list[NewsItem]:
        base = f"/repos/{repo.owner}/{repo.name}"
        me = me.lower()

        def others(login: str) -> bool:
            return not me or login.lower() != me

        def issues() -> list[NewsItem]:
            items = self._activity_get(f"{base}/issues", "Neue Issues lesen", params={
                "state": "all", "since": since, "sort": "created", "direction": "desc",
                "per_page": 100})
            return [NewsItem(PULL if "pull_request" in i else ISSUE, i.get("created_at", ""),
                             _login(i.get("user")), int(i.get("number") or 0),
                             i.get("title", ""), i.get("html_url", ""), "pull_request" in i)
                    for i in items if i.get("created_at", "") >= since
                    and others(_login(i.get("user")))]

        def comments() -> list[NewsItem]:
            items = self._activity_get(f"{base}/issues/comments", "Neue Kommentare lesen",
                                       params={"since": since, "sort": "created",
                                               "direction": "desc", "per_page": 100})
            return [NewsItem(COMMENT, c.get("created_at", ""), _login(c.get("user")),
                             _number(c.get("issue_url", "")), "", c.get("html_url", ""),
                             "/pull/" in c.get("html_url", ""))
                    for c in items if c.get("created_at", "") >= since
                    and others(_login(c.get("user")))]

        def reviews() -> list[NewsItem]:
            items = self._activity_get(f"{base}/pulls/comments", "Neue Reviews lesen",
                                       params={"since": since, "sort": "created",
                                               "direction": "desc", "per_page": 100})
            return [NewsItem(REVIEW, c.get("created_at", ""), _login(c.get("user")),
                             _number(c.get("pull_request_url", "")), "",
                             c.get("html_url", ""), True)
                    for c in items if c.get("created_at", "") >= since
                    and others(_login(c.get("user")))]

        def stars() -> list[NewsItem]:
            total = self.repo_stats(repo).stars
            if not total:
                return []
            last = (total - 1) // 100 + 1                # GitHub liefert die ältesten zuerst
            items = self._activity_get(f"{base}/stargazers", "Sterne lesen",
                                       params={"per_page": 100, "page": last},
                                       headers_extra={"Accept": STAR_JSON})
            return [NewsItem(STAR, s.get("starred_at", ""), _login(s.get("user")))
                    for s in items if s.get("starred_at", "") >= since
                    and others(_login(s.get("user")))]

        def forks() -> list[NewsItem]:
            items = self._activity_get(f"{base}/forks", "Forks lesen",
                                       params={"sort": "newest", "per_page": 30})
            return [NewsItem(FORK, f.get("created_at", ""), _login(f.get("owner")),
                             title=f.get("full_name", ""), url=f.get("html_url", ""))
                    for f in items if f.get("created_at", "") >= since
                    and others(_login(f.get("owner")))]

        def releases() -> list[NewsItem]:
            items = self._activity_get(f"{base}/releases", "Releases lesen",
                                       params={"per_page": 10})
            return [NewsItem(RELEASE, r.get("published_at") or "", _login(r.get("author")),
                             title=r.get("name") or r.get("tag_name", ""),
                             url=r.get("html_url", ""))
                    for r in items if (r.get("published_at") or "") >= since
                    and others(_login(r.get("author")))]

        def failed_runs() -> list[NewsItem]:
            # Auch eigene: Ein fehlgeschlagener Lauf ist neu, selbst wenn man ihn ausgelöst hat
            data = self._activity_get(f"{base}/actions/runs", "Läufe lesen", params={
                "status": "failure", "created": f">={since}", "per_page": 20})
            return [NewsItem(RUN_FAILED, r.get("created_at", ""), _login(r.get("actor")),
                             int(r.get("run_number") or 0), r.get("name", ""),
                             r.get("html_url", ""))
                    for r in (data or {}).get("workflow_runs", [])
                    if r.get("created_at", "") >= since]

        found: list[NewsItem] = []
        for name, read in (("Issues", issues), ("Kommentare", comments), ("Reviews", reviews),
                           ("Sterne", stars), ("Forks", forks), ("Releases", releases),
                           ("Actions", failed_runs)):
            found.extend(self._section(name, read))
        return sorted(found, key=lambda item: item.created, reverse=True)

    def traffic(self, repo: RepoRef) -> Traffic:
        base = f"/repos/{repo.owner}/{repo.name}/traffic"
        views = self._activity_get(f"{base}/views", "Aufrufe lesen")
        clones = self._activity_get(f"{base}/clones", "Klone lesen")
        paths = self._activity_get(f"{base}/popular/paths", "Meistbesuchte Seiten lesen")
        referrers = self._activity_get(f"{base}/popular/referrers", "Herkunft lesen")
        return Traffic(
            _days((views or {}).get("views")), _days((clones or {}).get("clones")),
            tuple(PopularItem(p.get("title") or p.get("path", ""), int(p.get("count") or 0),
                              int(p.get("uniques") or 0)) for p in paths or []),
            tuple(PopularItem(r.get("referrer", ""), int(r.get("count") or 0),
                              int(r.get("uniques") or 0)) for r in referrers or []))

    def repo_stats(self, repo: RepoRef) -> RepoStats:
        data = self._activity_get(f"/repos/{repo.owner}/{repo.name}", "Kennzahlen lesen")
        return RepoStats(int(data.get("stargazers_count") or 0),
                         int(data.get("forks_count") or 0),
                         int(data.get("subscribers_count") or 0),
                         int(data.get("open_issues_count") or 0))
