"""Abfragen im Internet für die Paketübersicht: PyPI, Hugging Face, Ollama und OSV.

Ohne Anmeldung und ohne Geheimnisse. Tests setzen transport auf httpx.MockTransport.
"""
from __future__ import annotations

import logging

import httpx

from cockpit.core import http

log = logging.getLogger(__name__)

transport: httpx.BaseTransport | None = None


def client() -> httpx.Client:
    return http.make_client(transport=transport)


def get_json(url: str, session: httpx.Client | None = None, headers: dict | None = None):
    """JSON einer Adresse, None bei Fehlern (kein Internet, nicht gefunden)."""
    own = session is None
    session = session or client()
    try:
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            return None
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        log.info("Abfrage %s: %r", url, exc)
        return None
    finally:
        if own:
            session.close()


def post_json(url: str, body: dict, session: httpx.Client | None = None):
    own = session is None
    session = session or client()
    try:
        response = session.post(url, json=body)
        if response.status_code != 200:
            return None
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        log.info("Abfrage %s: %r", url, exc)
        return None
    finally:
        if own:
            session.close()


def get_response(url: str, headers: dict | None = None) -> httpx.Response | None:
    with client() as session:
        try:
            return session.get(url, headers=headers)
        except httpx.HTTPError as exc:
            log.info("Abfrage %s: %r", url, exc)
            return None
