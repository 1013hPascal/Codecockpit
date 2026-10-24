"""Neuigkeiten seit dem letzten Start, ohne Qt (Wunsch des Nutzers vom 22.10.2026).

- Beim Abfragen der Repositories holt das Cockpit die Neuigkeiten der letzten 30 Tage und
  speichert sie in der Tabelle news. So sind sie auch ohne Internet da.
- Der Zeitpunkt des letzten Starts steht unter news.last_seen. Er wird erst beim Beenden neu
  gesetzt, damit bei einem Absturz nichts verloren geht.
- Jede Zeile beginnt mit dem Projekt, dann was passiert ist, dann wer und wann.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from cockpit.core.errors import CockpitError
from cockpit.core.text import count
from cockpit.platforms.activity import (
    COMMENT, FORK, ISSUE, PULL, RELEASE, REVIEW, RUN_FAILED, STAR, NewsItem, SupportsActivity)

log = logging.getLogger(__name__)

FEATURE_ID = "news"
LAST_SEEN_KEY = "news.last_seen"
DAYS_KEPT = 30

SINCE_START = "start"
WEEK = "7"
MONTH = "30"
PERIODS = [(SINCE_START, "Seit dem letzten Start"), (WEEK, "Letzte 7 Tage"),
           (MONTH, "Letzte 30 Tage")]
DISCUSSION = (ISSUE, PULL, COMMENT, REVIEW)       # für "Kommentare und Issues"


@dataclass(frozen=True)
class Entry:
    project_id: int
    project_name: str
    item: NewsItem


# -- Zeit --------------------------------------------------------------------------------------------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(moment: datetime) -> str:
    """Wie GitHub: 2026-10-22T14:05:00Z. So lassen sich die Texte direkt vergleichen."""
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(text: str) -> datetime | None:
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def last_seen(database) -> str | None:
    value = database.get_value(LAST_SEEN_KEY)
    return value if isinstance(value, str) and parse(value) is not None else None


def mark_seen(database, moment: datetime | None = None) -> None:
    database.set_value(LAST_SEEN_KEY, iso(moment or now_utc()))


def since_for(period: str, previous: str | None, now: datetime | None = None) -> str:
    """Beginn des Zeitraums. Gab es noch keinen Start, gilt "seit dem letzten Start" als 7 Tage."""
    now = now or now_utc()
    if period == SINCE_START and previous:
        return previous
    days = 30 if period == MONTH else 7
    return iso(now - timedelta(days=days))


# -- Abfragen und Speichern ------------------------------------------------------------------------
def refresh(services, platform, projects, cancel=None, now: datetime | None = None) -> int:
    """Neuigkeiten der letzten 30 Tage holen und speichern, im Hintergrund. Fehler bei einem
    Projekt stören die anderen nicht. Gibt die Zahl der abgefragten Projekte zurück."""
    from cockpit.core import repo_admin
    if not isinstance(platform, SupportsActivity) or not enabled(services):
        return 0
    now = now or now_utc()
    since = iso(now - timedelta(days=DAYS_KEPT))
    me = getattr(platform, "username", "") or ""
    done = 0
    for project in projects:
        if cancel is not None and cancel.is_set():
            break
        if project.remote is None:
            continue
        try:
            items = platform.news_since(repo_admin.repo_ref(project), since, me)
        except CockpitError as exc:
            log.warning("Neuigkeiten von %s: %s", project.name, exc.message)
            continue
        store(services.database, project.id, items, since)
        done += 1
    return done


def enabled(services) -> bool:
    try:
        return (FEATURE_ID in services.registry
                and services.features.availability(FEATURE_ID).available)
    except CockpitError:
        return False


def store(database, project_id: int, items: list[NewsItem], cutoff: str) -> None:
    """Neue Einträge dazu, Einträge vor cutoff weg. Doppelte zählen einmal."""
    with database.transaction() as conn:
        conn.execute("DELETE FROM news WHERE project_id = ? AND created < ?",
                     (project_id, cutoff))
        conn.executemany(
            "INSERT OR IGNORE INTO news (project_id, key, kind, created, author, number, title, "
            "url, on_pull) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(project_id, i.key, i.kind, i.created, i.author, i.number, i.title, i.url,
              int(i.on_pull)) for i in items])


def stored(services, since: str, project_id: int | None = None,
           kinds: tuple[str, ...] | None = None) -> list[Entry]:
    """Gespeicherte Neuigkeiten ab since, neueste zuerst."""
    sql = ("SELECT project_id, kind, created, author, number, title, url, on_pull FROM news "
           "WHERE created >= ?")
    params: list = [since]
    if project_id is not None:
        sql += " AND project_id = ?"
        params.append(project_id)
    rows = services.database.query(sql + " ORDER BY created DESC", tuple(params))
    names = {p.id: p.name for p in services.projects.all()}
    return [Entry(row["project_id"], names.get(row["project_id"], ""),
                  NewsItem(row["kind"], row["created"], row["author"], row["number"],
                           row["title"], row["url"], bool(row["on_pull"])))
            for row in rows if row["project_id"] in names
            and (kinds is None or row["kind"] in kinds)]


# -- Texte ---------------------------------------------------------------------------------------
def what(item: NewsItem) -> str:
    """Was passiert ist, zum Beispiel "neuer Kommentar zu Issue 12"."""
    target = f"Pull Request {item.number}" if item.on_pull else f"Issue {item.number}"
    title = f": {item.title}" if item.title else ""
    if item.kind == ISSUE:
        return f"neues Issue {item.number}{title}"
    if item.kind == PULL:
        return f"neuer Pull Request {item.number}{title}"
    if item.kind == COMMENT:
        return f"neuer Kommentar zu {target}"
    if item.kind == REVIEW:
        return f"neuer Review-Kommentar zu Pull Request {item.number}"
    if item.kind == STAR:
        return "neuer Stern"
    if item.kind == FORK:
        return f"neuer Fork{' ' + item.title if item.title else ''}"
    if item.kind == RELEASE:
        return f"neues Release{' ' + item.title if item.title else ''}"
    if item.kind == RUN_FAILED:
        return f"GitHub Actions fehlgeschlagen{title}"
    return "Neuigkeit"


def when(created: str, now: datetime | None = None) -> str:
    """"heute 14:05", "gestern 14:05" oder "20.10. 14:05", in der Zeit des Rechners."""
    moment = parse(created)
    if moment is None:
        return ""
    local = moment.astimezone()
    today = (now or now_utc()).astimezone().date()
    if local.date() == today:
        return f"heute {local:%H:%M}"
    if local.date() == today - timedelta(days=1):
        return f"gestern {local:%H:%M}"
    return f"{local:%d.%m.} {local:%H:%M}"


def line(entry: Entry, now: datetime | None = None) -> str:
    """Zum Beispiel "Tagebuch: neuer Kommentar zu Issue 12, von anna, gestern 14:05"."""
    parts = [f"{entry.project_name}: {what(entry.item)}"]
    if entry.item.author:
        parts.append(f"von {entry.item.author}")
    if when(entry.item.created, now):
        parts.append(when(entry.item.created, now))
    return ", ".join(parts)


def summary(entries: list[Entry], previous: str | None) -> str:
    """Ansage nach dem Start. Leer, wenn es nichts Neues gibt oder noch keinen Start gab."""
    moment = parse(previous) if previous else None
    if moment is None or not entries:
        return ""
    projects = len({e.project_id for e in entries})
    return (f"Seit Ihrem letzten Besuch am {moment.astimezone():%d.%m.}: "
            f"{count(len(entries), 'Neuigkeit', 'Neuigkeiten')} in "
            f"{count(projects, 'Projekt', 'Projekten')}.")


def shows_in_cockpit(item: NewsItem) -> bool:
    """Issues und Pull Requests öffnet das Cockpit selbst, den Rest der Browser."""
    return item.kind in DISCUSSION and item.number > 0
