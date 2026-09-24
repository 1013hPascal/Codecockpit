"""Basisklasse für alle Adapter.

Jeder Adapter beschreibt sich selbst: Art, Anzeigename und welche Angaben ein Konto braucht. Daraus
entstehen später die Dialoge der Kontenverwaltung automatisch.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class AccountField:
    key: str                 # zum Beispiel "url" oder "token"
    label: str               # Beschriftung im Dialog, zum Beispiel "Serveradresse"
    secret: bool = False     # True: landet im Tresor, nie in der Datenbank
    required: bool = True
    default: str = ""


@dataclass(frozen=True)
class TestResult:
    ok: bool
    text: str                # einfaches Deutsch, das Wichtigste vorne
    details: str = ""        # technische Meldung, ohne Geheimnisse


class Adapter(ABC):
    kind: ClassVar[str] = ""                 # "github", "ollama", "windows" ...
    display_name: ClassVar[str] = ""         # "GitHub", "Ollama" ...
    account_fields: ClassVar[tuple[AccountField, ...]] = ()

    @abstractmethod
    def test_connection(self) -> TestResult:
        """Prüft Verbindung und Zugangsdaten. Wirft keine Ausnahme, sondern meldet im Ergebnis."""
