"""Text-KI für eine Aufgabe vorbereiten (Konzept 11, ENTSCHEIDUNGEN.md zu Phase 8).

Vor dem Senden, im Vordergrund:
- Bei einem KI-Konto muss der Tresor offen sein, weil der API-Schlüssel dort liegt.
- Läuft die KI außerhalb des Rechners, fragt das Cockpit beim ersten Mal pro Aufgabe und KI nach.
  Vorgabe und Escape ist "Nicht senden". Ein Einverständnis wird gemerkt.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget

from cockpit.core.ai_tools import ACCOUNT, TextAI
from cockpit.core.errors import CockpitError
from cockpit.ui import vault_ui
from cockpit.ui.common import confirm

TASK_NAMES = {"terminal_explain": "Erklärungen im Terminal"}
DECLINED = "Nicht gesendet. Sie haben der KI außerhalb Ihres Rechners nicht zugestimmt."


def prepare(services, parent: QWidget | None, task: str, what: str,
            tool_id: int | None = None) -> TextAI | str:
    """TextAI zum Fragen, oder ein Satz, warum es nicht geht. what sagt, was gesendet wird, zum
    Beispiel "der Befehl und die Ausgabe"."""
    problem = services.ai_problem(tool_id)
    if problem:
        return problem
    tool = services.text_tool(tool_id) if services.ai is None else None
    if tool is not None and tool.source == ACCOUNT \
            and not vault_ui.ensure_unlocked(services, parent):
        return "Der Tresor ist gesperrt. Die KI braucht den Schlüssel aus dem Tresor."
    try:
        ai = services.ai_for(task, tool_id=tool_id)
    except CockpitError as exc:
        return exc.message
    if ai is None:
        return services.ai_problem(tool_id) or "Es ist keine Text-KI verfügbar."
    if not ai.model:
        return "Für diese KI ist noch kein Modell gewählt. Das geht im Menü KI, KI-Verwaltung."
    if not ai.is_local and not services.ai_tools.consent_given(task, ai.name):
        name = TASK_NAMES.get(task, task)
        text = (f"Für {name} werden {what} an {ai.name} gesendet. Diese KI läuft außerhalb "
                "Ihres Rechners. Einverstanden?")
        if not confirm(parent, "KI außerhalb Ihres Rechners", text, yes="Einverstanden",
                       no="Nicht senden"):
            return DECLINED
        services.ai_tools.give_consent(task, ai.name)
    return ai
