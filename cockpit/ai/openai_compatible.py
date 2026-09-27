"""KI-Adapter für OpenAI-kompatible Schnittstellen (Konzept 11).

Passt zu vielen Anbietern: OpenAI selbst, LM Studio, Firmen-Server und KI-Gateways. Die Adresse
ist frei einstellbar. Der API-Schlüssel liegt im Tresor und geht nur im Kopf der Anfrage mit.

Das Kästchen "Läuft im eigenen Netz oder in der Firma" macht den Anbieter für die Datenschutz-Regel
zu einem lokalen Anbieter (ENTSCHEIDUNGEN.md zu Phase 8).
"""
from __future__ import annotations

import json
import threading
from typing import Any, Mapping, Sequence

import httpx

from cockpit.adapters.base import AccountField, TestResult
from cockpit.ai.base import AIError, AIProvider
from cockpit.ai.streaming import error_text, stream_lines
from cockpit.core.errors import CockpitError
from cockpit.core.http import make_client
from cockpit.core.secret import Secret

DEFAULT_URL = "https://api.openai.com/v1"
UNREACHABLE = "Der KI-Anbieter ist nicht erreichbar."
ANSWER_TIMEOUT = 300


class OpenAICompatibleProvider(AIProvider):
    kind = "openai_compatible"
    display_name = "OpenAI-kompatibel"
    is_local = False
    account_fields = (
        AccountField("url", "Adresse", default=DEFAULT_URL),
        AccountField("api_key", "API-Schlüssel", secret=True, required=False),
        AccountField("in_network", "Läuft im eigenen Netz oder in der Firma", required=False,
                     default="nein", yes_no=True),
    )

    def __init__(self, url: str = DEFAULT_URL, api_key: Secret | None = None,
                 in_network: bool = False, transport: httpx.BaseTransport | None = None) -> None:
        self.url = (url or DEFAULT_URL).rstrip("/")
        self.is_local = in_network
        headers = {}
        if api_key is not None and api_key.reveal():
            headers["Authorization"] = f"Bearer {api_key.reveal()}"
        self.client = make_client(self.url + "/", headers, transport)
        self.client.timeout = httpx.Timeout(ANSWER_TIMEOUT, connect=10)

    @classmethod
    def from_account(cls, values: Mapping[str, Any]) -> "OpenAICompatibleProvider":
        return cls(str(values.get("url") or DEFAULT_URL), values.get("api_key"),
                   bool(values.get("in_network")))

    @classmethod
    def account_explanation(cls, browser_login: bool) -> list[str]:
        return [
            "Für OpenAI, LM Studio, einen Firmen-Server oder ein KI-Gateway.",
            "Adresse: die Basisadresse der Schnittstelle, meist mit /v1 am Ende. Bei LM Studio "
            "zum Beispiel http://localhost:1234/v1.",
            "API-Schlüssel: nur, wenn der Anbieter einen verlangt. Er liegt verschlüsselt im "
            "Tresor.",
            "Läuft der Anbieter im eigenen Netz oder in der Firma, kreuzen Sie das Kästchen an. "
            "Dann gilt er für den Datenschutz wie eine KI auf Ihrem Rechner.",
            "Das Modell wählen Sie danach im Menü KI, KI-Verwaltung.",
        ]

    def test_connection(self) -> TestResult:
        try:
            models = self.models()
        except CockpitError as exc:
            return TestResult(False, exc.message, exc.details)
        return TestResult(True, f"Verbindung in Ordnung. Verfügbare Modelle: {len(models)}.")

    def models(self) -> list[str]:
        try:
            response = self.client.get("models", timeout=20)
        except httpx.HTTPError as exc:
            raise AIError(UNREACHABLE, repr(exc)) from None
        if response.status_code in (401, 403):
            raise AIError("Der API-Schlüssel wurde abgelehnt.", error_text(response))
        if response.status_code != 200:
            raise AIError("Der KI-Anbieter hat die Anfrage abgelehnt.", error_text(response))
        try:
            data = response.json()
        except ValueError:
            raise AIError("Die Adresse gehört wohl nicht zu einer KI-Schnittstelle.",
                          response.text[:300]) from None
        return sorted(m["id"] for m in data.get("data", []) if isinstance(m, dict) and m.get("id"))

    def complete(self, messages: Sequence[dict], *, model: str, system: str = "",
                 schema: dict | None = None, max_tokens: int | None = None,
                 cancel: threading.Event | None = None) -> str | dict[str, Any]:
        chat = ([{"role": "system", "content": system}] if system else []) + list(messages)
        payload: dict[str, Any] = {"model": model, "messages": chat, "stream": True}
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if schema is not None:
            payload["response_format"] = {"type": "json_schema", "json_schema": {
                "name": "antwort", "schema": schema}}
        parts: list[str] = []
        for line in stream_lines(self.client, "chat/completions", payload, UNREACHABLE, cancel):
            if not line.startswith("data:"):
                continue
            data_text = line[5:].strip()
            if data_text == "[DONE]":
                break
            try:
                data = json.loads(data_text)
            except ValueError:
                continue
            if data.get("error"):
                raise AIError("Der KI-Anbieter meldet einen Fehler.", str(data["error"]))
            for choice in data.get("choices", []):
                parts.append((choice.get("delta") or {}).get("content") or "")
        text = "".join(parts).strip()
        if schema is None:
            return text
        try:
            return json.loads(text)
        except ValueError:
            raise AIError("Die Antwort der KI war unvollständig.", text[:300]) from None
