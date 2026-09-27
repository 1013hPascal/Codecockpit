"""Vorschläge des KI-Assistenten (Konzept 10.1). Alles blockiert, also im Hintergrund aufrufen.

Die KI antwortet mit einer ersten Zeile (Zusammenfassung oder Titel), einer Leerzeile und der
Beschreibung. Markdown, Anführungszeichen und Vorsätze wie "Titel:" werden entfernt.
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from pathlib import Path

from cockpit.ai import prompt_files
from cockpit.core.ai_tools import TextAI, plain_text
from cockpit.features.ai_assistant import context

MAX_ANSWER_TOKENS = 500
MAX_SUMMARY = 100                    # Zeichen für Zusammenfassung und Titel
MAX_DESCRIPTION = 350                # GitHub erlaubt etwa 350 Zeichen
_LABEL = re.compile(r"(?i)^(?:zusammenfassung|titel|title|summary|beschreibung|description|"
                    r"commit-nachricht|commit message|kurzbeschreibung)\s*:\s*")
_QUOTES = "\"'„“”«»"


@dataclass
class Suggestion:
    summary: str
    details: str = ""


def _strip(line: str) -> str:
    return _LABEL.sub("", line.strip()).strip(_QUOTES).strip()


def parse(answer: str, max_summary: int = MAX_SUMMARY) -> Suggestion:
    lines = [_strip(line) for line in plain_text(answer).splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return Suggestion("")
    summary = lines[0][:max_summary].rstrip()
    return Suggestion(summary, "\n".join(lines[1:]))


def _system(language: str) -> str:
    return prompt_files.fill(prompt_files.load("ai_assistant_system"), sprache=language)


def commit(ai: TextAI, code_dir: Path, language: str,
           cancel: threading.Event | None = None) -> Suggestion:
    changes = context.commit_context(code_dir, ai.max_chars)
    request = prompt_files.fill(prompt_files.load("ai_assistant_commit"), aenderungen=changes)
    return parse(ai.ask(request, _system(language), cancel, MAX_ANSWER_TOKENS))


def pull_request(ai: TextAI, code_dir: Path, head: str, base: str, language: str,
                 cancel: threading.Event | None = None) -> Suggestion:
    changes = context.pull_request_context(code_dir, head, base, ai.max_chars)
    request = prompt_files.fill(prompt_files.load("ai_assistant_pull_request"),
                                aenderungen=changes)
    return parse(ai.ask(request, _system(language), cancel, MAX_ANSWER_TOKENS))


def description(ai: TextAI, code_dir: Path, name: str, language: str,
                cancel: threading.Event | None = None) -> Suggestion:
    """Ein Satz. Mehrere Zeilen werden zu einem Absatz."""
    overview = context.project_context(code_dir, name, ai.max_chars)
    request = prompt_files.fill(prompt_files.load("ai_assistant_description"), projekt=overview)
    found = parse(ai.ask(request, _system(language), cancel, 200), MAX_DESCRIPTION)
    text = " ".join(p for p in (found.summary, found.details.replace("\n", " ")) if p)
    return Suggestion(text[:MAX_DESCRIPTION].rstrip())


def release_notes(ai: TextAI, code_dir: Path, last_tag: str, language: str,
                  cancel: threading.Event | None = None) -> Suggestion:
    """Versionshinweise aus den Commit-Nachrichten seit dem letzten Release (Phase 10)."""
    request = prompt_files.fill(prompt_files.load("ai_assistant_release"),
                                aenderungen=context.release_context(code_dir, last_tag,
                                                                    ai.max_chars))
    return parse(ai.ask(request, _system(language), cancel, MAX_ANSWER_TOKENS))
