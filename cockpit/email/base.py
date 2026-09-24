"""Schnittstelle für den E-Mail-Versand (Konzept 5.5). Umsetzung in Phase 11."""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

from cockpit.adapters.base import Adapter


@dataclass(frozen=True)
class ProviderTemplate:
    """Vorlage für einen Anbieter mit vorausgefülltem Server (zum Beispiel Gmail)."""
    name: str
    server: str
    port: int
    hint: str                   # was vorher im Postfach einzustellen ist


class EmailSender(Adapter):
    @abstractmethod
    def send_test_email(self, recipient: str) -> None:
        """Verschickt eine Test-E-Mail. Wirft CockpitError mit verständlichem Text."""

    @abstractmethod
    def send(self, recipient: str, subject: str, body: str) -> None: ...
