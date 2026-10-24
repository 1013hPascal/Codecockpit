"""Aktivität der Projekte, ohne Qt (Wunsch des Nutzers vom 22.10.2026).

GitHub gibt Aufrufe und Klone nur für die letzten 14 Tage. Damit eine längere Statistik entsteht,
holt das Cockpit die Zahlen einmal am Tag und speichert sie:
- activity_daily: Aufrufe, Besucher, Klone und klonende Personen pro Projekt und Tag.
- activity_snapshot: Sterne, Forks, Beobachter und Downloads pro Projekt und Tag.
Die meistbesuchten Seiten, die Herkunft der Besucher und die Downloads pro Release gibt es nur als
letzten Stand (activity.extra.<Projekt>). Die Zahlen sind keine Geheimnisse.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from cockpit.core.errors import CockpitError
from cockpit.core.text import count
from cockpit.platforms.activity import SupportsActivity, Traffic
from cockpit.platforms.base import PermissionMissing, SupportsReleases

log = logging.getLogger(__name__)

FEATURE_ID = "activity"
LAST_DAY_KEY = "activity.last_day"
NO_TRAFFIC_KEY = "activity.no_traffic"           # Projekte, deren Aufrufe nur Besitzer sehen
EXTRA_KEY = "activity.extra.{}"

WEEK = "7"
MONTH = "30"
ALL = "all"
PERIODS = [(WEEK, "Letzte 7 Tage"), (MONTH, "Letzte 30 Tage"),
           (ALL, "Seit Beginn der Aufzeichnung")]
OWNERS_ONLY = "Aufrufe nur für Besitzer sichtbar"


def today_text(today: date | None = None) -> str:
    return (today or date.today()).isoformat()


def start_of(period: str, today: date | None = None) -> str:
    """Erster Tag des Zeitraums. "Seit Beginn" ist der kleinste mögliche Tag."""
    today = today or date.today()
    if period == ALL:
        return "0000-00-00"
    return (today - timedelta(days=(30 if period == MONTH else 7) - 1)).isoformat()


def enabled(services) -> bool:
    try:
        return (FEATURE_ID in services.registry
                and services.features.availability(FEATURE_ID).available)
    except CockpitError:
        return False


def due(database, today: date | None = None) -> bool:
    """Einmal am Tag."""
    return database.get_value(LAST_DAY_KEY) != today_text(today)


# -- Abfragen und Speichern ------------------------------------------------------------------------
def refresh(services, platform, projects, cancel=None, today: date | None = None) -> int:
    """Zahlen aller Projekte dieser Plattform holen, höchstens einmal am Tag. Im Hintergrund.
    Gibt die Zahl der Projekte mit neuen Zahlen zurück."""
    if not isinstance(platform, SupportsActivity) or not enabled(services) \
            or not due(services.database, today):
        return 0
    done = 0
    for project in projects:
        if cancel is not None and cancel.is_set():
            return done
        if project.remote is None:
            continue
        try:
            record(services.database, platform, project, today)
        except CockpitError as exc:
            log.warning("Aktivität von %s: %s", project.name, exc.message)
            continue
        done += 1
    services.database.set_value(LAST_DAY_KEY, today_text(today))
    return done


def record(database, platform, project, today: date | None = None) -> None:
    from cockpit.core import repo_admin
    ref = repo_admin.repo_ref(project)
    stats = platform.repo_stats(ref)
    releases: list[tuple[str, int]] = []
    if isinstance(platform, SupportsReleases):
        try:
            releases = [(r.tag.lstrip("v") or r.name, r.downloads)
                        for r in platform.releases(ref)]
        except CockpitError as exc:
            log.info("Downloads von %s: %s", project.name, exc.message)
    database.execute(
        "INSERT INTO activity_snapshot (project_id, day, stars, forks, watchers, downloads) "
        "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(project_id, day) DO UPDATE SET "
        "stars = excluded.stars, forks = excluded.forks, watchers = excluded.watchers, "
        "downloads = excluded.downloads",
        (project.id, today_text(today), stats.stars, stats.forks, stats.watchers,
         sum(n for _, n in releases)))
    hidden = set(database.get_value(NO_TRAFFIC_KEY, []) or [])
    traffic = Traffic()
    try:
        traffic = platform.traffic(ref)
        hidden.discard(project.id)
    except PermissionMissing:
        hidden.add(project.id)
    database.set_value(NO_TRAFFIC_KEY, sorted(hidden))
    store_traffic(database, project.id, traffic)
    extra = {"paths": [[p.name, p.count, p.uniques] for p in traffic.paths],
             "referrers": [[r.name, r.count, r.uniques] for r in traffic.referrers],
             "releases": [list(r) for r in releases]}
    old = database.get_value(EXTRA_KEY.format(project.id), {}) or {}
    if project.id in hidden:                  # ohne Recht: den letzten bekannten Stand behalten
        extra["paths"], extra["referrers"] = old.get("paths", []), old.get("referrers", [])
    database.set_value(EXTRA_KEY.format(project.id), extra)


def store_traffic(database, project_id: int, traffic: Traffic) -> None:
    """Ein Tag kann mehrmals kommen (14 Tage überlappen). Die größere Zahl gilt, denn der heutige
    Tag ist beim ersten Abfragen noch nicht vorbei."""
    days: dict[str, list[int]] = {}
    for day in traffic.views:
        days.setdefault(day.day, [0, 0, 0, 0])[0:2] = [day.count, day.uniques]
    for day in traffic.clones:
        days.setdefault(day.day, [0, 0, 0, 0])[2:4] = [day.count, day.uniques]
    with database.transaction() as conn:
        conn.executemany(
            "INSERT INTO activity_daily (project_id, day, views, visitors, clones, cloners) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(project_id, day) DO UPDATE SET "
            "views = MAX(views, excluded.views), visitors = MAX(visitors, excluded.visitors), "
            "clones = MAX(clones, excluded.clones), cloners = MAX(cloners, excluded.cloners)",
            [(project_id, day, *numbers) for day, numbers in days.items() if day])


# -- Lesen -----------------------------------------------------------------------------------------
def daily(database, project_id: int, since: str) -> list:
    return database.query("SELECT day, views, visitors, clones, cloners FROM activity_daily "
                          "WHERE project_id = ? AND day >= ? ORDER BY day DESC",
                          (project_id, since))


def snapshot(database, project_id: int, on_or_before: str = "9999-99-99"):
    return database.query_one("SELECT day, stars, forks, watchers, downloads "
                              "FROM activity_snapshot WHERE project_id = ? AND day <= ? "
                              "ORDER BY day DESC LIMIT 1", (project_id, on_or_before))


def traffic_hidden(database, project_id: int) -> bool:
    return project_id in set(database.get_value(NO_TRAFFIC_KEY, []) or [])


def extra(database, project_id: int) -> dict:
    return database.get_value(EXTRA_KEY.format(project_id), {}) or {}


def star_change(database, project_id: int, today: date | None = None) -> int:
    """Sterne heute minus Sterne vor einer Woche. 0, wenn es noch keinen älteren Stand gibt."""
    now = snapshot(database, project_id)
    week_ago = ((today or date.today()) - timedelta(days=7)).isoformat()
    before = snapshot(database, project_id, week_ago)
    if now is None or before is None:
        return 0
    return now["stars"] - before["stars"]


def _sums(rows) -> tuple[int, int, int, int]:
    return (sum(r["views"] for r in rows), sum(r["visitors"] for r in rows),
            sum(r["clones"] for r in rows), sum(r["cloners"] for r in rows))


def project_line(database, project, period: str, today: date | None = None) -> str:
    """Zum Beispiel "Tagebuch: 120 Aufrufe, 8 Klone, 35 Downloads, 4 Sterne, plus 1 seit letzter
    Woche"."""
    latest = snapshot(database, project.id)
    rows = daily(database, project.id, start_of(period, today))
    if latest is None and not rows:
        return f"{project.name}: noch keine Zahlen"
    parts = []
    if traffic_hidden(database, project.id) and not rows:
        parts.append(OWNERS_ONLY)
    else:
        views, _visitors, clones, _cloners = _sums(rows)
        parts += [count(views, "Aufruf", "Aufrufe"), count(clones, "Klon", "Klone")]
    if latest is not None:
        parts += [count(latest["downloads"], "Download", "Downloads"),
                  count(latest["stars"], "Stern", "Sterne")]
        change = star_change(database, project.id, today)
        if change:
            parts.append(f"{'plus' if change > 0 else 'minus'} {abs(change)} seit letzter Woche")
    return f"{project.name}: {', '.join(parts)}"


def _day(text: str) -> str:
    try:
        return f"{date.fromisoformat(text):%d.%m.%Y}"
    except ValueError:
        return text


def details(database, project, period: str, today: date | None = None) -> list[str]:
    """Einzelheiten als kurze Zeilen, das Wichtigste vorne."""
    name = dict(PERIODS).get(period, "")
    lines = [f"{project.name}, {name}"]
    rows = daily(database, project.id, start_of(period, today))
    views, visitors, clones, cloners = _sums(rows)
    if traffic_hidden(database, project.id) and not rows:
        lines.append(f"{OWNERS_ONLY}.")
    else:
        lines.append(f"Aufrufe: {views}, Besucher: {visitors}")
        lines.append(f"Klone: {clones}, klonende Personen: {cloners}")
    latest = snapshot(database, project.id)
    if latest is not None:
        lines.append(f"Sterne: {latest['stars']}, Forks: {latest['forks']}, "
                     f"Beobachter: {latest['watchers']}, Downloads: {latest['downloads']}")
        lines.append(f"Stand vom {_day(latest['day'])}")
    if rows:
        lines.append("Pro Tag:")
        lines += [f"{_day(r['day'])}: {count(r['views'], 'Aufruf', 'Aufrufe')}, "
                  f"{count(r['clones'], 'Klon', 'Klone')}" for r in rows]
    more = extra(database, project.id)
    if more.get("releases"):
        lines.append("Downloads pro Release:")
        lines += [f"{tag}: {count(n, 'Download', 'Downloads')}" for tag, n in more["releases"]]
    if more.get("paths"):
        lines.append("Meistbesuchte Seiten, letzte 14 Tage:")
        lines += [f"{page}: {count(n, 'Aufruf', 'Aufrufe')}, {count(u, 'Besucher', 'Besucher')}"
                  for page, n, u in more["paths"]]
    if more.get("referrers"):
        lines.append("Herkunft der Besucher, letzte 14 Tage:")
        lines += [f"{source}: {count(n, 'Aufruf', 'Aufrufe')}" for source, n, _u in
                  more["referrers"]]
    return lines
