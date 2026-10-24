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
import time
from typing import Any, Mapping

import httpx

from cockpit.adapters.base import AccountField, TestResult
from cockpit.core import http
from cockpit.core.availability import Availability
from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret
from cockpit.core.text import join_words
from cockpit.platforms.base import (
    Capability, GitCredentials, NetworkError, NotAuthenticated, NotFound, PendingApproval,
    PermissionMissing, Platform, PlatformError, SsoAuthorizationRequired, SupportsActions,
    SupportsBranchProtection, SupportsBrowserLogin, SupportsCollaborators, SupportsForks,
    SupportsIssues, SupportsPullRequests, SupportsReleases, User)
# Aufgeteilt am 22.10.2026: Adressen und Texte stehen in github_common.py, die Bereiche der API in
# eigenen Dateien. Die Namen bleiben hier erreichbar.
from cockpit.platforms.github_common import (  # noqa: F401
    DEFAULT_URL, DELETE_SCOPES, INVITE_PERMISSIONS, NO_CONNECTION, SCOPES, SSO_REQUIRED,
    TOKEN_REJECTED, _message, api_base, graphql_url, is_github_com, noreply_domain, web_base)
# Die Bereiche der API stehen in eigenen Dateien. GitHubPlatform setzt sie zusammen.
from cockpit.platforms.github_login import CLIENT_ID, GitHubLogin  # noqa: F401
from cockpit.platforms.github_repos import GitHubRepos
from cockpit.platforms.github_issues import GitHubIssues
from cockpit.platforms.github_pulls import GitHubPulls
from cockpit.platforms.github_releases import GitHubReleases
from cockpit.platforms.github_activity import GitHubActivity
from cockpit.platforms.activity import SupportsActivity

log = logging.getLogger(__name__)


class GitHubPlatform(GitHubLogin, GitHubRepos, GitHubIssues, GitHubPulls, GitHubReleases,
                     GitHubActivity, Platform, SupportsBrowserLogin, SupportsCollaborators,
                     SupportsPullRequests, SupportsBranchProtection, SupportsReleases,
                     SupportsActions, SupportsForks, SupportsIssues, SupportsActivity):
    kind = "github"
    display_name = "GitHub"
    account_fields = (
        AccountField("username", "Benutzername", required=False, auto=True),
        AccountField("url", "Serveradresse", required=False, default=DEFAULT_URL),
        AccountField("token", "Token", secret=True),
    )
    account_guide = "anleitungen/github-token-erstellen.md"
    account_guide_title = "GitHub-Token erstellen"
    delete_login_scopes = DELETE_SCOPES

    @classmethod
    def account_explanation(cls, browser_login: bool) -> list[str]:
        lines = ["So verbinden Sie das Cockpit mit Ihrem GitHub-Konto."]
        if browser_login:
            lines += [
                "Es gibt zwei Wege. Mit Tab kommen Sie zu den beiden Knöpfen.",
                "Im Browser anmelden, empfohlen. So geht es:",
                "1. Im Browser mit GitHub anmelden.",
                "2. Bei der Code-Verifizierung den Code mit Strg+V einfügen. Er liegt schon in "
                "der Zwischenablage.",
                "3. Ganz unten auf Autorisieren klicken, auf Englisch Authorize.",
                "Danach trägt das Cockpit alles selbst ein.",
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
        headers.update(kwargs.pop("headers_extra", None) or {})
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
        if status == 403 and "upgrade to github pro" in lowered:
            return PlatformError("Schutzregeln für private Repositories gibt es bei GitHub nur mit "
                                 "GitHub Pro oder in Organisationen mit bezahltem Plan. Für "
                                 "öffentliche Repositories sind sie kostenlos.", details)
        if status == 403 and capability is Capability.BRANCH_PROTECTION:
            return PermissionMissing(capability, "Schutzregeln darf nur ändern, wer Administrator "
                                     "des Repositories ist.", details)
        if status == 403:
            return PermissionMissing(capability, f"Dem Token fehlt ein Recht für diese "
                                     f"Aktion{doing}.", details)
        if status == 404:
            return NotFound(f"Nicht gefunden{doing}. Möglicherweise fehlt dem Token der "
                            "Zugriff auf dieses Repository.", details)
        if status in (405, 409) and capability is Capability.PULL_REQUESTS:
            return PlatformError(f"GitHub kann den Pull Request so nicht übernehmen: {message}",
                                 details)
        if status == 422 and capability is Capability.PULL_REQUESTS and "own pull request" in \
                response.text.lower():
            return PlatformError("Den eigenen Pull Request können Sie nicht genehmigen und keine "
                                 "Änderungen anfordern. Das geht nur mit einem Kommentar.",
                                 details)
        if status == 422 and capability is Capability.PULL_REQUESTS:
            text = response.text.lower()             # die Gründe stehen unter "errors"
            if "no commits between" in text:
                return PlatformError("Zwischen den beiden Branches gibt es keinen Unterschied. "
                                     "Ein Pull Request braucht mindestens einen Commit.", details)
            if "already exists" in text:
                return PlatformError("Für diesen Branch gibt es schon einen offenen Pull "
                                     "Request.", details)
            return PlatformError(f"GitHub hat den Pull Request abgelehnt: {message}", details)
        if status == 422 and capability is Capability.COLLABORATORS:
            return PlatformError(f"GitHub hat die Einladung abgelehnt: {message}", details)
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

    def git_credentials(self) -> GitCredentials:
        """Token für Git über Umgebungsvariablen, nie über die Befehlszeile (CLAUDE.md)."""
        basic = base64.b64encode(f"x-access-token:{self.token.reveal()}".encode()).decode()
        return GitCredentials(False, {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": f"http.{web_base(self.url)}/.extraheader",
            "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic}",
        })


