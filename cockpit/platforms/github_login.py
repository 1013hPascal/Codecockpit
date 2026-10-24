"""Anmeldung bei GitHub im Browser (Device Flow einer OAuth-App).

Teil von GitHubPlatform (github.py). Ein Client Secret gibt es nicht.
"""
from __future__ import annotations

import logging
import threading
import time

import httpx

from cockpit.core import http
from cockpit.core.errors import Cancelled, CockpitError
from cockpit.core.secret import Secret
from cockpit.platforms.base import BrowserLogin, NetworkError
from cockpit.platforms.github_common import DEFAULT_URL, NO_CONNECTION, SCOPES, is_github_com

log = logging.getLogger(__name__)


# Öffentliche Client-ID der OAuth-App "CodeCockpit". Leer: Anmeldung im Browser nicht verfügbar.
CLIENT_ID = "Ov23li0mUwBCvUxIX2sT"


class GitHubLogin:
    """Anmeldung im Browser."""

    # -- Anmeldung im Browser (Device Flow) ------------------------------------------------
    @classmethod
    def browser_login_available(cls, url: str = "") -> bool:
        """Nur für github.com und nur, wenn die OAuth-App registriert ist. Firmenserver brauchen
        eine eigene App, dort bleibt der selbst erstellte Token."""
        return bool(CLIENT_ID) and is_github_com(url or DEFAULT_URL)

    @classmethod
    def _login_client(cls) -> httpx.Client:
        return http.make_client(DEFAULT_URL, {"Accept": "application/json"},
                                transport=cls.transport)

    @classmethod
    def start_browser_login(cls, url: str = "", scopes: str = "") -> BrowserLogin:
        try:
            with cls._login_client() as client:
                response = client.post("/login/device/code",
                                       data={"client_id": CLIENT_ID, "scope": scopes or SCOPES})
        except httpx.HTTPError as exc:
            raise NetworkError(NO_CONNECTION, repr(exc)) from None
        data = response.json() if response.content else {}
        if response.status_code >= 400 or "device_code" not in data:
            error = data.get("error", "")
            if error == "device_flow_disabled":
                raise CockpitError("Die Anmeldung im Browser ist bei der OAuth-App nicht "
                                   "eingeschaltet (Enable Device Flow).", error)
            raise CockpitError("Die Anmeldung im Browser ließ sich nicht starten.",
                               f"HTTP {response.status_code}: {error}")
        return BrowserLogin(data["user_code"], data["verification_uri"], data["device_code"],
                            int(data.get("interval", 5)), int(data.get("expires_in", 900)))

    @classmethod
    def wait_for_browser_login(cls, login: BrowserLogin, url: str = "",
                               cancel: threading.Event | None = None) -> Secret:
        """Fragt im vorgegebenen Abstand nach, bis der Nutzer bestätigt. Blockiert, also nur im
        Hintergrund aufrufen. Wirft Cancelled bei Abbruch, CockpitError bei Ablehnung."""
        interval = login.interval
        deadline = time.monotonic() + login.expires_in
        with cls._login_client() as client:
            while time.monotonic() < deadline:
                cls._wait(interval, cancel)
                try:
                    response = client.post("/login/oauth/access_token", data={
                        "client_id": CLIENT_ID, "device_code": login.device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"})
                    data = response.json()
                except (httpx.HTTPError, ValueError) as exc:
                    log.warning("Anmeldung im Browser: Nachfrage fehlgeschlagen: %r", exc)
                    continue                             # beim nächsten Mal erneut versuchen
                if data.get("access_token"):
                    return Secret(data["access_token"])
                error = data.get("error", "")
                if error == "authorization_pending":
                    continue
                if error == "slow_down":
                    interval = int(data.get("interval", interval + 5))
                    continue
                if error == "access_denied":
                    raise CockpitError("Die Anmeldung wurde im Browser abgelehnt.")
                if error == "expired_token":
                    break
                raise CockpitError("Die Anmeldung im Browser ist fehlgeschlagen.", error)
        raise CockpitError("Der Code ist abgelaufen. Bitte starten Sie die Anmeldung neu.")

    @classmethod
    def _wait(cls, seconds: float, cancel: threading.Event | None) -> None:
        """Warten, dabei auf Abbruch achten."""
        if cancel is None:
            cls.sleep(seconds)
            return
        if cls.sleep is not time.sleep:                 # Tests: nicht wirklich warten
            cls.sleep(seconds)
        elif cancel.wait(seconds):
            raise Cancelled()
        if cancel.is_set():
            raise Cancelled()
