"""KI-Werkzeuge (Konzept 11.1, Teilschritt 8b).

Ein Werkzeug ist eine KI mit einem Modell, zum Beispiel "Ollama auf diesem Rechner, gemma4:12b"
oder "Firmen-KI, gpt-4o" (ein KI-Konto aus der Kontenverwaltung). Man kann mehrere einrichten. Pro
Art (zurzeit nur Text-KI, ab 8d auch Sprach-KI) ist eines das Standard-Werkzeug. KI-Features wählen
in ihren Einstellungen ein Werkzeug, Vorgabe ist das Standard-Werkzeug.

Die Werkzeuge stehen in der Datenbank, ohne Geheimnisse. Den API-Schlüssel eines Kontos gibt es nur
im Tresor.

Datenschutz (ENTSCHEIDUNGEN.md zu Phase 8):
- Auch lokale KI bekommt höchstens so viele Zeichen, wie die Grundeinstellung erlaubt.
- Geht etwas an eine KI außerhalb des Rechners, fragt die Oberfläche beim ersten Mal pro Aufgabe
  und Werkzeug nach. Ein Ja wird gemerkt.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cockpit.adapters import registry as adapter_registry
from cockpit.core.database import Database

if TYPE_CHECKING:
    from cockpit.ai.base import AIProvider
    from cockpit.core.accounts import AccountStore

TEXT = "text"
KINDS = {TEXT: "Text-KI"}
OLLAMA = "ollama"
ACCOUNT = "account"

_TOOLS_KEY = "ai.tools"
_DEFAULT_KEY = "ai.default."
_CONSENT_KEY = "ai.consent"
SHORTENED = "[gekürzt]"


@dataclass(frozen=True)
class AITool:
    id: int
    kind: str                     # "text"
    source: str                   # "ollama" oder "account"
    model: str
    account_id: int | None = None


def limit_text(text: str, max_chars: int, keep_end: bool = False) -> str:
    """Text auf höchstens max_chars Zeichen kürzen. keep_end: das Ende behalten (Ausgaben)."""
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    room = max(0, max_chars - len(SHORTENED) - 1)
    return f"{SHORTENED}\n{text[-room:]}" if keep_end else f"{text[:room]}\n{SHORTENED}"


class AIToolStore:
    def __init__(self, database: Database, accounts: "AccountStore") -> None:
        self.database = database
        self.accounts = accounts
        self._ollama: "AIProvider | None" = None

    # -- Lesen ------------------------------------------------------------------------------
    def _raw(self) -> list[dict]:
        return list(self.database.get_value(_TOOLS_KEY, []) or [])

    def all(self, kind: str = TEXT) -> list[AITool]:
        """Werkzeuge einer Art. Werkzeuge gelöschter Konten fallen weg."""
        tools = []
        for item in self._raw():
            try:
                tool = AITool(int(item["id"]), item["kind"], item["source"], item["model"],
                              item.get("account_id"))
            except (KeyError, TypeError, ValueError):
                continue
            if tool.kind != kind:
                continue
            if tool.source == ACCOUNT and self.accounts.get(tool.account_id or -1) is None:
                continue
            tools.append(tool)
        return tools

    def get(self, tool_id: int | None) -> AITool | None:
        for kind in KINDS:
            for tool in self.all(kind):
                if tool.id == tool_id:
                    return tool
        return None

    def default(self, kind: str = TEXT) -> AITool | None:
        tools = self.all(kind)
        chosen = self.database.get_value(_DEFAULT_KEY + kind, None)
        return next((t for t in tools if t.id == chosen), tools[0] if tools else None)

    def label(self, tool: AITool, mark_default: bool = True) -> str:
        """Zum Beispiel "Ollama auf diesem Rechner, gemma4:12b, Standard"."""
        if tool.source == OLLAMA:
            name = "Ollama auf diesem Rechner"
        else:
            account = self.accounts.get(tool.account_id or -1)
            name = account.display_name if account else "Konto fehlt"
        parts = [name, tool.model or "kein Modell gewählt"]
        default = self.default(tool.kind)
        if mark_default and default is not None and default.id == tool.id:
            parts.append("Standard")
        return ", ".join(parts)

    # -- Ändern -----------------------------------------------------------------------------
    def _save(self, items: list[dict]) -> None:
        self.database.set_value(_TOOLS_KEY, items)

    def add(self, kind: str, source: str, model: str, account_id: int | None = None) -> AITool:
        items = self._raw()
        new_id = max([int(i.get("id", 0)) for i in items] + [0]) + 1
        items.append({"id": new_id, "kind": kind, "source": source, "model": model.strip(),
                      "account_id": account_id})
        self._save(items)
        if len(self.all(kind)) == 1:
            self.set_default(new_id, kind)
        return self.get(new_id)

    def set_model(self, tool_id: int, model: str) -> None:
        items = self._raw()
        for item in items:
            if item.get("id") == tool_id:
                item["model"] = model.strip()
        self._save(items)

    def remove(self, tool_id: int) -> None:
        self._save([i for i in self._raw() if i.get("id") != tool_id])

    def set_default(self, tool_id: int, kind: str = TEXT) -> None:
        self.database.set_value(_DEFAULT_KEY + kind, tool_id)

    # -- Anbieter ---------------------------------------------------------------------------
    def ollama(self) -> "AIProvider":
        """Ein gemeinsamer Adapter für Ollama auf diesem Rechner."""
        if self._ollama is None:
            self._ollama = adapter_registry.adapter_class("ai", OLLAMA)()
        return self._ollama

    def provider(self, tool: AITool) -> "AIProvider":
        """Anbieter des Werkzeugs. Bei einem Konto muss der Tresor offen sein (sonst
        VaultLocked), weil der API-Schlüssel dort liegt."""
        if tool.source == OLLAMA:
            return self.ollama()
        account = self.accounts.get(tool.account_id or -1)
        if account is None:
            from cockpit.core.errors import CockpitError
            raise CockpitError("Das Konto dieser KI gibt es nicht mehr.")
        return self.accounts.adapter_for(account)

    def is_local(self, tool: AITool) -> bool:
        """Ohne Tresor: Ollama ist lokal, ein Konto nur mit "im eigenen Netz"."""
        if tool.source == OLLAMA:
            return True
        account = self.accounts.get(tool.account_id or -1)
        if account is None:
            return False
        return bool(self.accounts.values(account, with_secrets=False).get("in_network"))

    # -- Datenschutz ------------------------------------------------------------------------
    def consent_given(self, task: str, name: str) -> bool:
        return f"{task}|{name}" in (self.database.get_value(_CONSENT_KEY, []) or [])

    def give_consent(self, task: str, name: str) -> None:
        given = set(self.database.get_value(_CONSENT_KEY, []) or [])
        self.database.set_value(_CONSENT_KEY, sorted(given | {f"{task}|{name}"}))


@dataclass
class TextAI:
    """Eine Text-KI, fertig zum Fragen: Anbieter, Modell und Grenze für die Textmenge."""
    provider: "AIProvider"
    model: str
    name: str                     # für Rückfragen und Meldungen, zum Beispiel "Ollama, gemma4:12b"
    max_chars: int

    @property
    def is_local(self) -> bool:
        return bool(self.provider.is_local)

    def ask(self, prompt: str, system: str = "", cancel: threading.Event | None = None,
            max_tokens: int | None = None) -> str:
        """Blockiert, also im Hintergrund aufrufen. Wirft AIError oder Cancelled."""
        self.provider.start()
        answer = self.provider.complete([{"role": "user",
                                          "content": limit_text(prompt, self.max_chars)}],
                                        model=self.model, system=system, max_tokens=max_tokens,
                                        cancel=cancel)
        return str(answer).strip()
