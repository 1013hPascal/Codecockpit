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


@contextmanager
def ai_working() -> Iterator[None]:
    """Für die Dauer einer Anfrage an die KI."""
    global _ai_requests
    with _lock:
        _ai_requests += 1
    try:
        yield
    finally:
        with _lock:
            _ai_requests -= 1


def ai_busy() -> bool:
    with _lock:
        return _ai_requests > 0
