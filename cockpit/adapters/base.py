"""Basisklasse für alle Adapter.

Jeder Adapter beschreibt sich selbst: Art, Anzeigename und welche Angaben ein Konto braucht. Daraus
entstehen später die Dialoge der Kontenverwaltung automatisch.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Mapping


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
    link: str = ""           # Seite, die weiterhilft, zum Beispiel die Freigabe für Single Sign-On
    link_text: str = ""      # Frage zum Öffnen, zum Beispiel "Freigabeseite im Browser öffnen?"


class Adapter(ABC):
    kind: ClassVar[str] = ""                 # "github", "ollama", "windows" ...
    display_name: ClassVar[str] = ""         # "GitHub", "Ollama" ...
    account_fields: ClassVar[tuple[AccountField, ...]] = ()
    # Anleitung, woher man die Zugangsdaten bekommt (Pfad unter anleitungen/), leer: keine
    account_guide: ClassVar[str] = ""
    account_guide_title: ClassVar[str] = ""

    @abstractmethod
    def test_connection(self) -> TestResult:
        """Prüft Verbindung und Zugangsdaten. Wirft keine Ausnahme, sondern meldet im Ergebnis."""

    @classmethod
    def account_explanation(cls, browser_login: bool) -> list[str]:
        """Erklärung oben im Konto-Fenster, eine Zeile pro Satz. Leer: keine Erklärung.
        browser_login sagt, ob die Anmeldung im Browser angeboten wird."""
        return []

    @classmethod
    def from_account(cls, values: Mapping[str, Any]) -> "Adapter":
        """Adapter mit den Angaben eines Kontos erzeugen. Geheimnisse kommen als Secret.
        Jeder Adapter mit account_fields muss das umsetzen."""
        raise NotImplementedError(f"{cls.__name__} unterstützt keine Konten.")
