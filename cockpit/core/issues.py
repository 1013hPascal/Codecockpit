"""Issues: Zeilen für Listen, Branch-Namen und die Angaben für die KI (Wunsch des Nutzers vom
21.10.2026).

Alles geht ohne KI. Die KI kommt nur dazu, wenn der KI-Assistent im Projekt aktiv ist: Sie fasst
ein Issue zusammen und schlägt einen Branch-Namen vor. Ohne KI entsteht der Branch-Name aus
Nummer und Titel, zum Beispiel "12-suche-in-pdfs".
"""
from __future__ import annotations

import re

from cockpit.core.branches import suggest_name
from cockpit.core.pull_requests import _day
from cockpit.core.text import count

STATES = {"open": "offen", "closed": "geschlossen"}
MAX_BRANCH = 50


def issue_line(issue) -> str:
    """"Nr. 12: Suche in PDFs, von Anna, Fehler, zugewiesen an Ben, 3 Kommentare"."""
    parts = [f"Nr. {issue.number}: {issue.title}", f"von {issue.author}"]
    if issue.labels:
        parts.append(", ".join(issue.labels))
    if issue.assignees:
        parts.append(f"zugewiesen an {', '.join(issue.assignees)}")
    if issue.comments:
        parts.append(count(issue.comments, "Kommentar", "Kommentare"))
    if issue.state != "open":
        parts.append(STATES.get(issue.state, issue.state))
    return ", ".join(parts)


def issue_details(issue) -> list[str]:
    """Angaben als Zeilen, das Wichtigste vorne."""
    lines = [f"Nr. {issue.number}: {issue.title}",
             STATES.get(issue.state, issue.state).capitalize(),
             f"Erstellt von {issue.author}" + (f" am {_day(issue.created)}"
                                               if issue.created else "")]
    lines.append(f"Labels: {', '.join(issue.labels)}" if issue.labels else "Keine Labels")
    lines.append(f"Zugewiesen an {', '.join(issue.assignees)}" if issue.assignees
                 else "Niemandem zugewiesen")
    body = [line.strip() for line in issue.body.splitlines() if line.strip()]
    if body:
        lines.append("Beschreibung:")
        lines.extend(body)
    return lines


def comment_line(comment) -> str:
    day = _day(comment.created)
    text = " ".join(comment.body.split())
    return f"{comment.author}, {day}: {text}" if day else f"{comment.author}: {text}"


def branch_name(issue) -> str:
    """Ohne KI: "12-suche-in-pdfs"."""
    return clean_branch_name(f"{issue.number}-{suggest_name(issue.title)}") or str(issue.number)


def clean_branch_name(text: str, number: int | None = None) -> str:
    """Vorschlag der KI in einen gültigen Branch-Namen bringen. Fehlt die Nummer vorne, kommt
    sie dazu."""
    text = re.sub(r"(?i)^\s*(?:branch-name|branchname|branch|name)\s*:\s*", "", text)
    name = suggest_name(text.strip().strip("`'\""))
    name = re.sub(r"-{2,}", "-", name).strip("-")
    if number is not None and not name.startswith(f"{number}-") and name != str(number):
        name = f"{number}-{name}" if name else str(number)
    return name[:MAX_BRANCH].rstrip("-")


def issue_context(issue, comments) -> str:
    """Was die KI bekommt: Titel, Labels, Beschreibung und Kommentare. Geheimnisse entfernt der
    Aufrufer (ai_assistant.context.redact)."""
    parts = [f"Issue Nr. {issue.number}: {issue.title}"]
    if issue.labels:
        parts.append(f"Labels: {', '.join(issue.labels)}")
    parts += ["Beschreibung:", issue.body.strip() or "(keine)"]
    for comment in comments:
        parts += [f"Kommentar von {comment.author}:", comment.body.strip()]
    return "\n".join(parts)
