"""Gemeinsame Teile für GitHub: Adressen, Rechte bei der Anmeldung, Texte für Fehler.
"""
from __future__ import annotations

from urllib.parse import urlparse

import httpx


# Rechte bei der Anmeldung im Browser. delete_repo fehlt bewusst: Löschen fragt es eigens an.
SCOPES = "repo read:org workflow"


# Zweite Anmeldung nur zum Löschen (ENTSCHEIDUNGEN.md). Der Zugang wird nicht gespeichert.
DELETE_SCOPES = "repo delete_repo"


# Rechte beim Einladen: Wert der Anzeige -> Wert der API
INVITE_PERMISSIONS = {"read": "pull", "triage": "triage", "write": "push",
                      "maintain": "maintain", "admin": "admin"}


DEFAULT_URL = "https://github.com"


NO_CONNECTION = "GitHub ist nicht erreichbar. Bitte prüfen Sie die Internetverbindung."


TOKEN_REJECTED = "Der Token wurde abgelehnt. Er ist abgelaufen, widerrufen oder falsch kopiert."


SSO_REQUIRED = ("Die Organisation verlangt Single Sign-On. Der Token muss auf GitHub für die "
                "Organisation freigegeben werden.")


def _host(url: str) -> str:
    return (urlparse(url or DEFAULT_URL).hostname or "github.com").lower()


def is_github_com(url: str) -> bool:
    return _host(url) in ("github.com", "www.github.com")


def web_base(url: str) -> str:
    if is_github_com(url):
        return DEFAULT_URL
    return (url or DEFAULT_URL).rstrip("/")


def api_base(url: str) -> str:
    """github.com: api.github.com. GitHub Enterprise Server: <Serveradresse>/api/v3."""
    if is_github_com(url):
        return "https://api.github.com"
    return web_base(url) + "/api/v3"


def graphql_url(url: str) -> str:
    """github.com: api.github.com/graphql. GitHub Enterprise Server: <Server>/api/graphql."""
    if is_github_com(url):
        return "https://api.github.com/graphql"
    return web_base(url) + "/api/graphql"


def noreply_domain(url: str) -> str:
    return "users.noreply.github.com" if is_github_com(url) else f"users.noreply.{_host(url)}"


def _message(response: httpx.Response) -> str:
    try:
        return str(response.json().get("message", ""))
    except ValueError:
        return response.text[:200]
