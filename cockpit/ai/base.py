"""Schnittstelle für KI-Anbieter (Konzept 11). Vorbild ist LLMBackend aus dem Chatbot.

Features rufen die KI nie direkt auf. Sie fragen über Services.ai_for() nach einem Anbieter für
eine Aufgabe. Der Kern prüft dabei die Datenschutz-Regel.
"""
from __future__ import annotations

import threading
from abc import abstractmethod
from typing import Any, ClassVar, Sequence

from cockpit.adapters.base import Adapter
from cockpit.core.errors import CockpitError


class AIError(CockpitError):
    """Der Anbieter ist nicht erreichbar oder meldet einen Fehler."""


class AIProvider(Adapter):
    is_local: ClassVar[bool] = False       # True: Daten verlassen den Rechner nicht

    @abstractmethod
    def models(self) -> list[str]:
        """Verfügbare Modelle. Wirft AIError, wenn der Anbieter nicht erreichbar ist."""

    def model_capabilities(self, model: str) -> set[str]:
        """Was ein Modell kann, zum Beispiel "json" und "stream". Unbekannt: nichts sperren."""
        return {"json", "stream"}

    def start(self) -> None:
        """Nur bei lokalen Servern wie Ollama: bei Bedarf starten."""

    def stop(self) -> None:
        """Nur selbst gestartete Server beenden."""

    @abstractmethod
    def complete(self, messages: Sequence[dict], *, model: str, system: str = "",
                 schema: dict | None = None, max_tokens: int | None = None,
                 cancel: threading.Event | None = None) -> str | dict[str, Any]:
        """Antwort als Text, mit schema als geprüftes JSON-Objekt. Wirft Cancelled bei Abbruch."""
