"""Pull Requests (Konzept 10.14, Phase 6).

Pull Requests liegen auf der Plattform. Das Gespräch damit läuft über die Schnittstelle
SupportsPullRequests. Hier steht, was ohne Oberfläche geht:

- ein Zwischenspeicher der offenen Pull Requests pro Repository. Er wird beim Abfragen der
  Repositories (Start, Strg+R) und beim Öffnen der Liste aufgefrischt. So können Code und die
  Übersicht Branches "1 offener Pull Request" zeigen, ohne jedes Mal GitHub zu fragen.
- die Zeilen für Listen, das Wichtigste vorne.
- Vorschläge für Titel und Beschreibung aus den Commit-Nachrichten.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from cockpit.core import git
from cockpit.core.database import Database
from cockpit.core.git import RemoteAddress
from cockpit.core.text import count
from cockpit.platforms.base import PullRequest, PullRequestComment, PullRequestFile

log = logging.getLogger(__name__)

STATES = {"open": "offen", "closed": "geschlossen", "merged": "übernommen"}
FILE_STATES = {"added": "neu", "modified": "geändert", "removed": "gelöscht",
               "renamed": "umbenannt", "changed": "geändert", "copied": "kopiert"}


# -- Zwischenspeicher der offenen Pull Requests ---------------------------------------------------
class PullRequestCache:
    def __init__(self, database: Database) -> None:
        self.database = database

    def replace(self, address: RemoteAddress, pulls: list[PullRequest]) -> None:
        """Die offenen Pull Requests eines Repositories durch die aktuellen ersetzen."""
        with self.database.transaction() as conn:
            conn.execute("DELETE FROM pull_request_cache WHERE repo = ?", (address.key,))
            for pull in pulls:
                if pull.state != "open":
                    continue
                conn.execute("INSERT OR REPLACE INTO pull_request_cache (repo, number, head, "
                             "base, title, author, draft) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (address.key, pull.number, pull.head, pull.base, pull.title,
                              pull.author, int(pull.draft)))

    def open_pulls(self, address: RemoteAddress | None) -> list[PullRequest]:
        if address is None:
            return []
        rows = self.database.query("SELECT * FROM pull_request_cache WHERE repo = ? "
                                   "ORDER BY number DESC", (address.key,))
        return [PullRequest(r["number"], r["title"], r["head"], r["base"], r["author"],
                            "open", bool(r["draft"])) for r in rows]

    def count_for_branch(self, address: RemoteAddress | None, branch: str) -> int:
        """Offene Pull Requests, deren Änderungen aus diesem Branch kommen."""
        return len([p for p in self.open_pulls(address) if p.head == branch])


# -- Zeilen für Listen ---------------------------------------------------------------------------
def _day(iso: str) -> str:
    try:
        return f"{datetime.fromisoformat(iso.replace('Z', '+00:00')):%d.%m.%Y}" if iso else ""
    except ValueError:
        return ""


def pull_line(pull: PullRequest) -> str:
    """"Nr. 12: Suche in PDFs, von design nach main, von Anna, Entwurf"."""
    parts = [f"Nr. {pull.number}: {pull.title}", f"von {pull.head} nach {pull.base}",
             f"von {pull.author}"]
    if pull.draft:
        parts.append("Entwurf")
    if pull.state != "open":
        parts.append(STATES.get(pull.state, pull.state))
    return ", ".join(parts)


def pull_details(pull: PullRequest) -> list[str]:
    """Angaben zu einem Pull Request als Zeilen, das Wichtigste vorne."""
    state = STATES.get(pull.state, pull.state)
    lines = [f"Nr. {pull.number}: {pull.title}",
             f"{state.capitalize()}{', Entwurf' if pull.draft else ''}",
             f"Von {pull.head} nach {pull.base}",
             f"Erstellt von {pull.author}" + (f" am {_day(pull.created)}" if pull.created else "")]
    if pull.reviewers:
        lines.append(f"Prüfer angefragt: {', '.join(pull.reviewers)}")
    body = [line.strip() for line in pull.body.splitlines() if line.strip()]
    if body:
        lines.append("Beschreibung:")
        lines.extend(body)
    return lines


def file_line(changed: PullRequestFile) -> str:
    """"main.py, geändert, 5 Zeilen dazu, 2 weg"."""
    parts = [changed.path, FILE_STATES.get(changed.status, changed.status)]
    if changed.additions:
        parts.append(f"{count(changed.additions, 'Zeile', 'Zeilen')} dazu")
    if changed.deletions:
        parts.append(f"{count(changed.deletions, 'Zeile', 'Zeilen')} weg")
    return ", ".join(parts)


def comment_line(comment: PullRequestComment) -> str:
    """"Anna, 24.09.2026: Sieht gut aus" oder "Ben zu main.py Zeile 12, 24.09.2026: …"."""
    who = comment.author
    if comment.path:
        who += f" zu {comment.path}" + (f" Zeile {comment.line}" if comment.line else "")
    day = _day(comment.created)
    text = " ".join(comment.body.split())
    return f"{who}, {day}: {text}" if day else f"{who}: {text}"


# -- Vorschläge aus den Commits ------------------------------------------------------------------
def _base_ref(code_dir: Path, base: str) -> str:
    for ref in (f"origin/{base}", base):
        if git.run(["rev-parse", "-q", "--verify", ref], code_dir, check=False).returncode == 0:
            return ref
    return base


def commit_subjects(code_dir: Path, head: str, base: str) -> list[str]:
    """Commit-Nachrichten, die head gegenüber base mitbringt, älteste zuerst."""
    result = git.run(["log", "--reverse", "--format=%s", f"{_base_ref(code_dir, base)}..{head}"],
                     code_dir, check=False)
    return [line for line in result.stdout.splitlines() if line.strip()]


def suggest(code_dir: Path, head: str, base: str) -> tuple[str, str]:
    """Vorschlag für Titel und Beschreibung. Ein Commit: seine Nachricht. Mehrere: der Name des
    Branches als Titel und die Nachrichten als Liste."""
    subjects = commit_subjects(code_dir, head, base)
    if len(subjects) == 1:
        body = git.run(["log", "-1", "--format=%b", head], code_dir, check=False).stdout.strip()
        return subjects[0], body
    title = head.replace("-", " ").replace("_", " ").strip()
    title = title[:1].upper() + title[1:]
    return title, "\n".join(f"- {s}" for s in subjects)


def upload_needed(code_dir: Path, branch: str) -> int:
    """Wie viele Commits von branch noch nicht auf der Plattform sind. -1: Der Branch ist noch gar
    nicht dort."""
    remote = f"origin/{branch}"
    if git.run(["rev-parse", "-q", "--verify", remote], code_dir, check=False).returncode != 0:
        return -1
    result = git.run(["rev-list", "--count", f"{remote}..{branch}"], code_dir, check=False)
    try:
        return int(result.stdout.strip() or 0)
    except ValueError:
        return 0
