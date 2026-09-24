"""Hülle für Geheimnisse (Tokens, API-Schlüssel, Passwörter).

Ein Secret gibt sich bei str() und repr() nie preis. Den echten Wert liefert nur reveal(). Jeder
Wert wird außerdem beim Log-Filter angemeldet, damit er auch dann nicht im Log landet, wenn er
irgendwo doch als Klartext durchrutscht.
"""
from __future__ import annotations

import hmac
import threading

_MIN_LENGTH_TO_MASK = 4          # sehr kurze Werte würden sonst normale Wörter im Log ersetzen

_known_values: set[str] = set()
_lock = threading.Lock()


def known_values() -> list[str]:
    """Alle bisher angemeldeten Geheimnisse, längste zuerst (für den Log-Filter)."""
    with _lock:
        return sorted(_known_values, key=len, reverse=True)


def register(value: str) -> None:
    if len(value) >= _MIN_LENGTH_TO_MASK:
        with _lock:
            _known_values.add(value)


class Secret:
    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Ein Geheimnis muss ein Text sein.")
        self._value = value
        register(value)

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "Secret('***')"

    __str__ = __repr__

    def __format__(self, spec: str) -> str:
        return repr(self)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Secret):
            return NotImplemented
        return hmac.compare_digest(self._value.encode("utf-8"), other._value.encode("utf-8"))

    def __hash__(self) -> int:
        return hash(("Secret", len(self._value)))

    def __reduce__(self):
        raise TypeError("Geheimnisse lassen sich nicht serialisieren.")
