"""Erklärung eines fehlgeschlagenen Befehls durch die KI (Konzept 10.16)."""
from __future__ import annotations

import re
import threading

from cockpit.ai import prompt_files
from cockpit.core.ai_tools import TextAI, limit_text
from cockpit.core.logging_setup import mask_secrets

MAX_ANSWER_TOKENS = 600

_MARKDOWN = re.compile(r"^\s*(?:#+\s*|[-*•]\s+|\d+[.)]\s+)")


def prompt(command: str, code: int, lines: list[str], max_chars: int) -> tuple[str, str]:
    """System-Prompt und Anfrage. Von der Ausgabe bleibt das Ende, dort steht meist der Fehler."""
    system = prompt_files.load("terminal_explain_system")
    template = prompt_files.load("terminal_explain")
    room = max(500, max_chars - len(template) - len(command) - 50)
    output = limit_text(mask_secrets("\n".join(lines)), room, keep_end=True) or "(keine Ausgabe)"
    request = prompt_files.fill(template, befehl=mask_secrets(command),
                                rueckgabewert=str(code), ausgabe=output)
    return system, request


def clean(answer: str) -> str:
    """Markdown entfernen, das auf der Braillezeile stört: Sternchen, Rauten, Aufzählungszeichen."""
    lines = []
    for line in answer.replace("**", "").replace("`", "").splitlines():
        line = _MARKDOWN.sub("", line).strip()
        if line:
            lines.append(line)
    return mask_secrets("\n".join(lines))


def explain(ai: TextAI, command: str, code: int, lines: list[str],
            cancel: threading.Event | None = None) -> str:
    """Blockiert, also im Hintergrund aufrufen. Wirft AIError oder Cancelled."""
    system, request = prompt(command, code, lines, ai.max_chars)
    return clean(ai.ask(request, system, cancel, MAX_ANSWER_TOKENS))
