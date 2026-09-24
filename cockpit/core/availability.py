"""Ob etwas verfügbar ist, und wenn nicht, warum."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Availability:
    available: bool
    reason: str = ""            # einfacher Satz, zum Beispiel "Dem Token fehlt das Recht zum Löschen."

    @classmethod
    def yes(cls) -> "Availability":
        return cls(True)

    @classmethod
    def no(cls, reason: str) -> "Availability":
        return cls(False, reason)

    def __bool__(self) -> bool:
        return self.available
