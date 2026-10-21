"""Arbeitet die KI gerade? (Wunsch des Nutzers vom 14.10.2026)

Jede Anfrage an eine Text-KI läuft über TextAI.ask und meldet sich hier an und ab. Die Oberfläche
fragt regelmäßig nach und spielt dann einen leisen Warteton. Der Kern kennt keine Töne und kein Qt.
"""
from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator

_lock = threading.Lock()
_ai_requests = 0
_ai_failures = 0          # gescheiterte oder abgebrochene Anfragen, für den Erfolgston (20.10.)


@contextmanager
def ai_working() -> Iterator[None]:
    """Für die Dauer einer Anfrage an die KI."""
    global _ai_requests, _ai_failures
    with _lock:
        _ai_requests += 1
    try:
        yield
    except BaseException:
        with _lock:
            _ai_failures += 1
        raise
    finally:
        with _lock:
            _ai_requests -= 1


def ai_failures() -> int:
    """Zähler der gescheiterten Anfragen. Ändert er sich während einer Anfrage, kein Erfolgston."""
    with _lock:
        return _ai_failures


def ai_busy() -> bool:
    with _lock:
        return _ai_requests > 0
