"""Neuigkeiten und Aktivität auf einer Code-Plattform (Wunsch des Nutzers vom 22.10.2026).

Eigene kleine Schnittstelle wie SupportsIssues. Ein Adapter erbt sie nur, wenn er sie erfüllt.
- news_since: was andere seit einem Zeitpunkt getan haben, zum Beispiel neue Issues, Kommentare,
  Sterne. Eigene Beiträge kommen nicht mit.
- traffic: Aufrufe und Klone der letzten Tage. Bei GitHub nur mit Schreibrecht, sonst
  PermissionMissing.
- repo_stats: Sterne, Forks, Beobachter und offene Issues.
Die Downloads kommen aus den Releases (SupportsReleases).
"""
from __future__ import annotations

from dataclasses import dataclass

from cockpit.platforms.base import RepoRef

# Arten von Neuigkeiten
ISSUE = "issue"
PULL = "pull"
COMMENT = "comment"
REVIEW = "review"
STAR = "star"
FORK = "fork"
RELEASE = "release"
RUN_FAILED = "run_failed"
KINDS = (ISSUE, PULL, COMMENT, REVIEW, STAR, FORK, RELEASE, RUN_FAILED)


@dataclass(frozen=True)
class NewsItem:
    kind: str                        # eine der Arten oben
    created: str                     # ISO, UTC
    author: str = ""
    number: int = 0                  # Issue, Pull Request oder Lauf
    title: str = ""
    url: str = ""
    on_pull: bool = False            # Kommentar zu einem Pull Request statt zu einem Issue

    @property
    def key(self) -> str:
        """Eindeutig pro Repository, damit nichts doppelt gespeichert wird."""
        return f"{self.kind}:{self.number}:{self.created}:{self.author}"


@dataclass(frozen=True)
class DayCount:
    day: str                         # JJJJ-MM-TT
    count: int
    uniques: int


@dataclass(frozen=True)
class PopularItem:
    name: str                        # Seite oder Herkunft
    count: int
    uniques: int


@dataclass(frozen=True)
class Traffic:
    views: tuple[DayCount, ...] = ()
    clones: tuple[DayCount, ...] = ()
    paths: tuple[PopularItem, ...] = ()
    referrers: tuple[PopularItem, ...] = ()


@dataclass(frozen=True)
class RepoStats:
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0


class SupportsActivity:
    """Neuigkeiten und Zahlen zur Beliebtheit eines Repositories."""

    def news_since(self, repo: RepoRef, since: str, me: str = "") -> list[NewsItem]:
        """Neuigkeiten seit since (ISO, UTC), neueste zuerst. me: eigener Benutzername, dessen
        Beiträge nicht mitkommen."""
        raise NotImplementedError

    def traffic(self, repo: RepoRef) -> Traffic:
        """Aufrufe und Klone pro Tag, meistbesuchte Seiten und Herkunft der Besucher."""
        raise NotImplementedError

    def repo_stats(self, repo: RepoRef) -> RepoStats:
        raise NotImplementedError
