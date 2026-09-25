"""GitHub und GitHub Enterprise Server (Konzept 6).

Anmeldung auf zwei Wegen:
1. Im Browser (Device Flow einer OAuth-App): Das Cockpit zeigt einen Code, der Nutzer bestätigt ihn
   auf github.com. Dafür braucht es die öffentliche Client-ID der registrierten OAuth-App
   (CLIENT_ID, siehe anleitungen/github-oauth-app-registrieren.md). Ein Client Secret gibt es nicht.
2. Mit einem selbst erstellten Token (siehe anleitungen/github-token-erstellen.md).

Fehler von GitHub werden in verständliche Meldungen übersetzt, besonders die typischen Fälle in
Firmen: Single Sign-On (Freigabe für die Organisation fehlt), Token wartet auf Genehmigung, fehlende
Rechte. Der Token steht nie in einer Adresse, einer Meldung oder im Log.
"""
from __future__ import annotations

import base64
import logging
import threading
import time
from typing import Any, Mapping
from urllib.parse import urlparse

import httpx

from cockpit.adapters.base import AccountField, TestResult
from cockpit.core import http
from cockpit.core.availability import Availability
from cockpit.core.errors import Cancelled, CockpitError
from cockpit.core.secret import Secret
from cockpit.core.text import join_words
from cockpit.platforms.base import (BrowserLogin, Capability, GitCredentials, NetworkError,
                                    NewRepo, NotAuthenticated, NotFound, PendingApproval,
                                    PermissionMissing, Platform, PlatformError, RemoteRepo,
                                    RepoInfo, RepoLinks, RepoRef, SsoAuthorizationRequired,
                                    SupportsBrowserLogin, User)

log = logging.getLogger(__name__)

# Öffentliche Client-ID der OAuth-App "CodeCockpit". Leer: Anmeldung im Browser nicht verfügbar.
CLIENT_ID = "Ov23li0mUwBCvUxIX2sT"
# Rechte bei der Anmeldung im Browser. delete_repo fehlt bewusst: Löschen fragt es eigens an.
SCOPES = "repo read:org workflow"
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


def noreply_domain(url: str) -> str:
    return "users.noreply.github.com" if is_github_com(url) else f"users.noreply.{_host(url)}"


def _message(response: httpx.Response) -> str:
    try:
        return str(response.json().get("message", ""))
    except ValueError:
        return response.text[:200]


class GitHubPlatform(Platform, SupportsBrowserLogin):
    kind = "github"
    display_name = "GitHub"
    account_fields = (
        AccountField("username", "Benutzername", required=False, auto=True),
        AccountField("url", "Serveradresse", required=False, default=DEFAULT_URL),
        AccountField("token", "Token", secret=True),
    )
    account_guide = "anleitungen/github-token-erstellen.md"
    account_guide_title = "GitHub-Token erstellen"

    @classmethod
    def account_explanation(cls, browser_login: bool) -> list[str]:
        lines = ["So verbinden Sie das Cockpit mit Ihrem GitHub-Konto."]
        if browser_login:
            lines += [
                "Es gibt zwei Wege. Mit Tab kommen Sie zu den beiden Knöpfen.",
                "Im Browser anmelden, empfohlen: GitHub öffnet sich, Sie geben einen Code ein und "
                "bestätigen. Das Cockpit trägt alles selbst ein.",
                "Mit Token anmelden: Sie erstellen auf GitHub selbst einen Token und fügen ihn "
                "ein. Nötig zum Beispiel für einen GitHub-Server Ihrer Firma. Eine Anleitung "
                "erklärt jeden Schritt.",
            ]
        else:
            lines.append("Sie erstellen auf GitHub selbst einen Token und fügen ihn ein. Die "
                         "Anleitung für den Token erklärt jeden Schritt.")
        lines += [
            "Ihren Benutzernamen müssen Sie nicht eintragen. Das Cockpit holt ihn von GitHub.",
            "Der Zugang liegt verschlüsselt im Tresor.",
        ]
        return lines

    # In Tests ersetzbar: httpx.MockTransport und eine Warte-Funktion ohne echtes Warten
    transport: httpx.BaseTransport | None = None
    sleep = staticmethod(time.sleep)

    def __init__(self, url: str = DEFAULT_URL, token: Secret | None = None,
                 username: str = "") -> None:
        self.url = url or DEFAULT_URL
        self.token = token or Secret("")
        self.username = username
        self.scopes: set[str] | None = None        # None: Fine-grained Token, Rechte unbekannt
        self._client: httpx.Client | None = None

    @classmethod
    def from_account(cls, values: Mapping[str, Any]) -> "GitHubPlatform":
        return cls(values.get("url") or DEFAULT_URL, values.get("token"),
                   values.get("username") or "")

    # -- HTTP ------------------------------------------------------------------------------
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = http.make_client(api_base(self.url), {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }, transport=type(self).transport)
        return self._client

    def request(self, method: str, path: str, action: str = "",
                capability: Capability | None = None, **kwargs) -> httpx.Response:
        """Anfrage an die GitHub-API. Wirft PlatformError-Unterklassen mit einfachem Text."""
        if not self.token.reveal():
            raise NotAuthenticated("Es ist kein Token eingetragen.")
        headers = {"Authorization": f"Bearer {self.token.reveal()}"}
        try:
            response = self.client().request(method, path, headers=headers, **kwargs)
        except httpx.TimeoutException as exc:
            raise NetworkError("GitHub antwortet nicht. Bitte später erneut versuchen.",
                               repr(exc)) from None
        except httpx.HTTPError as exc:
            raise NetworkError(NO_CONNECTION, repr(exc)) from None
        if "X-OAuth-Scopes" in response.headers:
            self.scopes = {s.strip() for s in response.headers["X-OAuth-Scopes"].split(",")
                           if s.strip()}
        if response.status_code >= 400:
            raise self._error(response, method, path, action, capability)
        return response

    def _error(self, response: httpx.Response, method: str, path: str, action: str,
               capability: Capability | None) -> PlatformError:
        status = response.status_code
        message = _message(response)
        details = f"HTTP {status} bei {method} {path}: {message}"
        doing = f" ({action})" if action else ""
        if status == 401:
            return NotAuthenticated(TOKEN_REJECTED, details)
        sso = response.headers.get("X-GitHub-SSO", "")
        if status == 403 and sso.startswith("required"):
            url = sso.partition("url=")[2].strip()
            return SsoAuthorizationRequired(url, SSO_REQUIRED, details)
        if status in (403, 429) and response.headers.get("X-RateLimit-Remaining") == "0":
            reset = response.headers.get("X-RateLimit-Reset", "")
            when = time.strftime("%H:%M", time.localtime(int(reset))) if reset.isdigit() else ""
            text = "GitHub hat zu viele Anfragen gezählt. Bitte später erneut versuchen"
            return PlatformError(f"{text}, ab {when} Uhr." if when else f"{text}.", details)
        lowered = message.lower()
        if status == 403 and ("approv" in lowered or "pending" in lowered):
            return PendingApproval("Der Token wartet auf die Genehmigung durch die "
                                   "Organisation. Das erledigt dort ein Administrator.", details)
        if status == 403:
            return PermissionMissing(capability, f"Dem Token fehlt ein Recht für diese "
                                     f"Aktion{doing}.", details)
        if status == 404:
            return NotFound(f"Nicht gefunden{doing}. Möglicherweise fehlt dem Token der "
                            "Zugriff auf dieses Repository.", details)
        if status == 422 and "already exists" in response.text:
            return PlatformError("Ein Repository mit diesem Namen gibt es schon.", details)
        return PlatformError(f"GitHub meldet einen Fehler{doing}.", details)

    # -- Verbindung und Konto ---------------------------------------------------------------
    def test_connection(self) -> TestResult:
        try:
            user = self.current_user()
        except SsoAuthorizationRequired as exc:
            return TestResult(False, exc.message, exc.details, link=exc.url,
                              link_text="Freigabeseite im Browser öffnen?")
        except CockpitError as exc:
            return TestResult(False, exc.message, exc.details)
        parts = [f"Verbindung in Ordnung. Angemeldet als {user.login}."]
        try:
            organizations = self.organizations()
        except CockpitError:
            organizations = []
        if organizations:
            parts.append(f"Organisationen: {join_words(organizations)}.")
        missing = self.missing_scopes()
        if missing:
            parts.append(f"Dem Token fehlen Rechte: {join_words(missing)}.")
        return TestResult(True, " ".join(parts))

    def missing_scopes(self) -> list[str]:
        """Fehlende Rechte bei Tokens mit Scopes (Anmeldung im Browser, klassische Tokens).
        Bei Fine-grained Tokens meldet GitHub keine Scopes, dann leer."""
        if self.scopes is None:
            return []
        needed = [s for s in ("repo", "workflow") if s not in self.scopes]
        return needed

    def current_user(self) -> User:
        data = self.request("GET", "/user", "Konto lesen").json()
        self.username = data.get("login", "")
        return User(data.get("login", ""), str(data.get("id", "")), data.get("name") or "")

    def organizations(self) -> list[str]:
        response = self.request("GET", "/user/orgs", "Organisationen lesen",
                                Capability.ORGANIZATIONS, params={"per_page": 100})
        return [o.get("login", "") for o in response.json()]

    def noreply_email(self) -> str | None:
        user = self.current_user()
        return f"{user.id}+{user.login}@{noreply_domain(self.url)}"

    # -- Fähigkeiten -------------------------------------------------------------------------
    def capabilities(self) -> set[Capability]:
        return set(Capability)

    def permissions(self) -> dict[Capability, Availability]:
        result = {c: Availability.yes() for c in self.capabilities()}
        if self.scopes is None:
            return result                                # Fine-grained: zeigt sich beim Versuch
        if "repo" not in self.scopes:
            reason = Availability.no("Dem Token fehlt das Recht repo.")
            for c in (Capability.CREATE_REPO, Capability.CHANGE_VISIBILITY, Capability.ARCHIVE,
                      Capability.RELEASES, Capability.ISSUES, Capability.PULL_REQUESTS):
                result[c] = reason
        if "delete_repo" not in self.scopes:
            result[Capability.DELETE_REPO] = Availability.no(
                "Dem Token fehlt das Recht zum Löschen. Das Cockpit fragt es beim Löschen an.")
        if "read:org" not in self.scopes and "admin:org" not in self.scopes:
            result[Capability.ORGANIZATIONS] = Availability.no(
                "Dem Token fehlt das Recht read:org.")
        return result

    # -- Repositories ------------------------------------------------------------------------
    def repositories(self, owner: str = "") -> list[RemoteRepo]:
        if owner:
            path, params = f"/orgs/{owner}/repos", {"sort": "pushed", "type": "all"}
        else:
            path, params = "/user/repos", {"sort": "pushed", "affiliation": "owner"}
        result: list[RemoteRepo] = []
        for page in range(1, 51):                        # höchstens 5000 Repositories
            items = self.request("GET", path, "Repositories lesen", params={
                **params, "per_page": 100, "page": page}).json()
            for data in items:
                result.append(RemoteRepo(
                    RepoRef(data["owner"]["login"], data["name"]), bool(data.get("private")),
                    data.get("clone_url", ""), data.get("html_url", ""),
                    data.get("pushed_at") or "", bool(data.get("archived"))))
            if len(items) < 100:
                break
        return sorted(result, key=lambda r: r.pushed_at, reverse=True)

    def create_repo(self, spec: NewRepo) -> RepoRef:
        path = f"/orgs/{spec.organization}/repos" if spec.organization else "/user/repos"
        data = self.request("POST", path, "Repository anlegen", Capability.CREATE_REPO,
                            json={"name": spec.name, "description": spec.description,
                                  "private": spec.private, "auto_init": False}).json()
        return RepoRef(data["owner"]["login"], data["name"])

    def repo_info(self, repo: RepoRef) -> RepoInfo:
        data = self.request("GET", f"/repos/{repo.owner}/{repo.name}", "Repository lesen").json()
        return RepoInfo(RepoRef(data["owner"]["login"], data["name"]), bool(data["private"]),
                        bool(data.get("archived")), data.get("default_branch", "main"),
                        data.get("html_url", ""))

    def set_visibility(self, repo: RepoRef, private: bool) -> None:
        self.request("PATCH", f"/repos/{repo.owner}/{repo.name}", "Sichtbarkeit ändern",
                     Capability.CHANGE_VISIBILITY, json={"private": private})

    def archive(self, repo: RepoRef) -> None:
        self.request("PATCH", f"/repos/{repo.owner}/{repo.name}", "Archivieren",
                     Capability.ARCHIVE, json={"archived": True})

    def delete(self, repo: RepoRef) -> None:
        self.request("DELETE", f"/repos/{repo.owner}/{repo.name}", "Löschen",
                     Capability.DELETE_REPO)

    def links(self, repo: RepoRef) -> RepoLinks:
        page = f"{web_base(self.url)}/{repo.owner}/{repo.name}"
        return RepoLinks(page, f"{page}#readme", f"{page}/releases/latest")

    def clone_url(self, repo: RepoRef) -> str:
        return f"{web_base(self.url)}/{repo.owner}/{repo.name}.git"

    def license_text(self, spdx: str, holder: str, year: int) -> str | None:
        """Lizenztext aus den Vorlagen von GitHub, mit Name und Jahr (Konzept 9.1)."""
        try:
            body = self.request("GET", f"/licenses/{spdx.lower()}", "Lizenztext lesen").json()
        except NotFound:
            return None
        text = str(body.get("body", ""))
        for placeholder in ("[year]", "[yyyy]"):
            text = text.replace(placeholder, str(year))
        for placeholder in ("[fullname]", "[name of copyright owner]"):
            text = text.replace(placeholder, holder)
        return text or None

    def git_credentials(self) -> GitCredentials:
        """Token für Git über Umgebungsvariablen, nie über die Befehlszeile (CLAUDE.md)."""
        basic = base64.b64encode(f"x-access-token:{self.token.reveal()}".encode()).decode()
        return GitCredentials(False, {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": f"http.{web_base(self.url)}/.extraheader",
            "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic}",
        })

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
    def start_browser_login(cls, url: str = "") -> BrowserLogin:
        try:
            with cls._login_client() as client:
                response = client.post("/login/device/code",
                                       data={"client_id": CLIENT_ID, "scope": SCOPES})
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
