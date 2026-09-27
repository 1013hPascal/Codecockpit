"""Antworten der KI Stück für Stück lesen, mit Abbruch (Muster aus dem Chatbot).

Die KI schickt ihre Antwort als Strom von Zeilen. Wird abgebrochen, schließt ein Wächter die
Verbindung, damit das Warten sofort endet.
"""
from __future__ import annotations

import threading
from typing import Iterator

import httpx

from cockpit.ai.base import AIError
from cockpit.core.errors import Cancelled


def stream_lines(client: httpx.Client, url: str, payload: dict, unreachable: str,
                 cancel: threading.Event | None = None) -> Iterator[str]:
    """POST mit JSON, dann jede nicht leere Zeile der Antwort. Wirft AIError oder Cancelled."""
    done = threading.Event()
    try:
        with client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                response.read()
                raise AIError("Die KI hat die Anfrage abgelehnt.", error_text(response))
            if cancel is not None:
                threading.Thread(target=_close_on_cancel, args=(cancel, done, response),
                                 daemon=True).start()
            try:
                for line in response.iter_lines():
                    if cancel is not None and cancel.is_set():
                        raise Cancelled()
                    if line.strip():
                        yield line
            finally:
                done.set()
    except httpx.ConnectError as exc:
        raise AIError(unreachable, repr(exc)) from None
    except httpx.TimeoutException as exc:
        raise AIError("Die KI hat zu lange nicht geantwortet.", repr(exc)) from None
    except httpx.HTTPError as exc:
        if cancel is not None and cancel.is_set():
            raise Cancelled() from None
        raise AIError("Die Verbindung zur KI ist abgebrochen.", repr(exc)) from None
    if cancel is not None and cancel.is_set():
        raise Cancelled()


def _close_on_cancel(cancel: threading.Event, done: threading.Event,
                     response: httpx.Response) -> None:
    while not done.is_set():
        if cancel.wait(0.1):
            response.close()
            return


def error_text(response: httpx.Response) -> str:
    """Fehlermeldung des Servers, ohne Kopfzeilen (dort könnte ein Schlüssel stehen)."""
    try:
        data = response.json()
    except ValueError:
        return f"HTTP {response.status_code}: {response.text[:500]}"
    error = data.get("error", data) if isinstance(data, dict) else data
    if isinstance(error, dict):
        error = error.get("message", error)
    return f"HTTP {response.status_code}: {error}"
