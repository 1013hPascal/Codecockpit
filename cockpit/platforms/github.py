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
from cockpit.platforms.base import (BranchProtection, BrowserLogin, Capability, Collaborator,
                                    GitCredentials, SupportsBranchProtection,
                                    NetworkError, NewRepo, NotAuthenticated, NotFound,
                                    PendingApproval, PermissionMissing, Platform, PlatformError,
                                    MERGE_METHODS, PullRequest, PullRequestComment,
                                    PullRequestFile, Review,
                                    RemoteRepo, RepoInfo, RepoLinks, RepoRef,
                                    SsoAuthorizationRequired, SupportsBrowserLogin,
                                    SupportsCollaborators, SupportsPullRequests, User)

log = logging.getLogger(__name__)

# Öffentliche Client-ID der OAuth-App "CodeCockpit". Leer: Anmeldung im Browser nicht verfügbar.
CLIENT_ID = "Ov23li0mUwBCvUxIX2sT"
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


class GitHubPlatform(Platform, SupportsBrowserLogin, SupportsCollaborators,
                     SupportsPullRequests, SupportsBranchProtection):
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

    def unarchive(self, repo: RepoRef) -> None:
        self.request("PATCH", f"/repos/{repo.owner}/{repo.name}", "Archivierung aufheben",
                     Capability.ARCHIVE, json={"archived": False})

    def settings_url(self, repo: RepoRef) -> str:
        return f"{web_base(self.url)}/{repo.owner}/{repo.name}/settings"

    # -- Mitarbeiter ---------------------------------------------------------------------------
    def collaborators(self, repo: RepoRef) -> list[Collaborator]:
        base = f"/repos/{repo.owner}/{repo.name}"
        people = self.request("GET", f"{base}/collaborators", "Mitarbeiter lesen",
                              Capability.COLLABORATORS,
                              params={"affiliation": "direct", "per_page": 100}).json()
        result = [Collaborator(p.get("login", ""), _role(p)) for p in people]
        invitations = self.request("GET", f"{base}/invitations", "Einladungen lesen",
                                   Capability.COLLABORATORS, params={"per_page": 100}).json()
        result += [Collaborator((i.get("invitee") or {}).get("login", ""),
                                _permission(i.get("permissions", "")), int(i.get("id", 0)))
                   for i in invitations]
        return sorted(result, key=lambda c: c.login.lower())

    def invite(self, repo: RepoRef, login: str, permission: str) -> bool:
        try:
            response = self.request(
                "PUT", f"/repos/{repo.owner}/{repo.name}/collaborators/{login}",
                "Mitarbeiter einladen", Capability.COLLABORATORS,
                json={"permission": INVITE_PERMISSIONS.get(permission, "push")})
        except NotFound as exc:
            raise NotFound(f"Den Benutzer {login} gibt es auf GitHub nicht, oder das "
                           "Repository ist nicht erreichbar.", exc.details) from None
        return response.status_code == 201

    def change_permission(self, repo: RepoRef, person: Collaborator, permission: str) -> None:
        value = INVITE_PERMISSIONS.get(permission, "push")
        base = f"/repos/{repo.owner}/{repo.name}"
        if person.invited:
            # Bei Einladungen heißen die Werte read, write, admin ...
            self.request("PATCH", f"{base}/invitations/{person.invitation_id}",
                         "Recht ändern", Capability.COLLABORATORS,
                         json={"permissions": permission})
            return
        self.request("PUT", f"{base}/collaborators/{person.login}", "Recht ändern",
                     Capability.COLLABORATORS, json={"permission": value})

    def remove_collaborator(self, repo: RepoRef, login: str) -> None:
        self.request("DELETE", f"/repos/{repo.owner}/{repo.name}/collaborators/{login}",
                     "Mitarbeiter entfernen", Capability.COLLABORATORS)

    def cancel_invitation(self, repo: RepoRef, invitation_id: int) -> None:
        self.request("DELETE", f"/repos/{repo.owner}/{repo.name}/invitations/{invitation_id}",
                     "Einladung zurückziehen", Capability.COLLABORATORS)

    # -- Pull Requests ---------------------------------------------------------------------------
    def pull_requests(self, repo: RepoRef, state: str = "open") -> list[PullRequest]:
        path = f"/repos/{repo.owner}/{repo.name}/pulls"
        result: list[PullRequest] = []
        for page in range(1, 11):                        # höchstens 1000
            items = self.request("GET", path, "Pull Requests lesen", Capability.PULL_REQUESTS,
                                 params={"state": state, "sort": "created",
                                         "direction": "desc", "per_page": 100,
                                         "page": page}).json()
            result.extend(_pull(item) for item in items)
            if len(items) < 100:
                break
        return result

    def pull_request(self, repo: RepoRef, number: int) -> PullRequest:
        return _pull(self.request("GET", f"/repos/{repo.owner}/{repo.name}/pulls/{number}",
                                  "Pull Request lesen", Capability.PULL_REQUESTS).json())

    def create_pull_request(self, repo: RepoRef, head: str, base: str, title: str, body: str,
                            draft: bool = False, reviewers: tuple[str, ...] = ()) -> PullRequest:
        base_path = f"/repos/{repo.owner}/{repo.name}/pulls"
        created = _pull(self.request("POST", base_path, "Pull Request erstellen",
                                     Capability.PULL_REQUESTS,
                                     json={"title": title, "head": head, "base": base,
                                           "body": body, "draft": draft}).json())
        if reviewers:
            self.request("POST", f"{base_path}/{created.number}/requested_reviewers",
                         "Prüfer anfragen", Capability.PULL_REQUESTS,
                         json={"reviewers": list(reviewers)})
            created = PullRequest(**{**created.__dict__, "reviewers": tuple(reviewers)})
        return created

    def pull_request_comments(self, repo: RepoRef, number: int) -> list[PullRequestComment]:
        base = f"/repos/{repo.owner}/{repo.name}"
        general = self.request("GET", f"{base}/issues/{number}/comments", "Kommentare lesen",
                               Capability.PULL_REQUESTS, params={"per_page": 100}).json()
        on_lines = self.request("GET", f"{base}/pulls/{number}/comments", "Kommentare lesen",
                                Capability.PULL_REQUESTS, params={"per_page": 100}).json()
        found = [PullRequestComment(_login(c), c.get("created_at", ""), c.get("body") or "")
                 for c in general]
        found += [PullRequestComment(_login(c), c.get("created_at", ""), c.get("body") or "",
                                     c.get("path", ""),
                                     int(c.get("line") or c.get("original_line") or 0))
                  for c in on_lines]
        return sorted(found, key=lambda c: c.created)

    def add_pull_request_comment(self, repo: RepoRef, number: int, body: str) -> None:
        self.request("POST", f"/repos/{repo.owner}/{repo.name}/issues/{number}/comments",
                     "Kommentar schreiben", Capability.PULL_REQUESTS, json={"body": body})

    def pull_request_files(self, repo: RepoRef, number: int) -> list[PullRequestFile]:
        items = self.request("GET", f"/repos/{repo.owner}/{repo.name}/pulls/{number}/files",
                             "Dateien lesen", Capability.PULL_REQUESTS,
                             params={"per_page": 100}).json()
        return [PullRequestFile(f.get("filename", ""), f.get("status", "modified"),
                                int(f.get("additions") or 0), int(f.get("deletions") or 0),
                                f.get("patch") or "") for f in items]

    def set_pull_request_open(self, repo: RepoRef, number: int, open_: bool) -> None:
        self.request("PATCH", f"/repos/{repo.owner}/{repo.name}/pulls/{number}",
                     "Pull Request öffnen" if open_ else "Pull Request schließen",
                     Capability.PULL_REQUESTS, json={"state": "open" if open_ else "closed"})

    def mark_ready_for_review(self, repo: RepoRef, pull: PullRequest) -> None:
        """Geht nur über GraphQL, die REST-Schnittstelle kann das nicht."""
        node_id = pull.node_id or self.pull_request(repo, pull.number).node_id
        query = ("mutation($id: ID!) { markPullRequestReadyForReview(input: "
                 "{pullRequestId: $id}) { pullRequest { isDraft } } }")
        data = self.request("POST", graphql_url(self.url), "Zum Prüfen freigeben",
                            Capability.PULL_REQUESTS,
                            json={"query": query, "variables": {"id": node_id}}).json()
        if data.get("errors"):
            raise PlatformError("GitHub hat die Freigabe abgelehnt.",
                                str(data["errors"][0].get("message", "")))

    def reviews(self, repo: RepoRef, number: int) -> list[Review]:
        items = self.request("GET", f"/repos/{repo.owner}/{repo.name}/pulls/{number}/reviews",
                             "Reviews lesen", Capability.PULL_REQUESTS,
                             params={"per_page": 100}).json()
        return [Review(_login(r), r.get("state", ""), r.get("body") or "",
                       r.get("submitted_at") or "") for r in items]

    def submit_review(self, repo: RepoRef, number: int, event: str, body: str) -> None:
        self.request("POST", f"/repos/{repo.owner}/{repo.name}/pulls/{number}/reviews",
                     "Review abgeben", Capability.PULL_REQUESTS,
                     json={"event": event, "body": body})

    def merge_methods(self, repo: RepoRef) -> list[str]:
        data = self.request("GET", f"/repos/{repo.owner}/{repo.name}", "Repository lesen").json()
        allowed = {"merge": data.get("allow_merge_commit", True),
                   "squash": data.get("allow_squash_merge", True),
                   "rebase": data.get("allow_rebase_merge", True)}
        return [m for m in MERGE_METHODS if allowed[m]]

    def merge_pull_request(self, repo: RepoRef, number: int, method: str) -> None:
        self.request("PUT", f"/repos/{repo.owner}/{repo.name}/pulls/{number}/merge",
                     "Übernehmen", Capability.PULL_REQUESTS, json={"merge_method": method})

    # -- Schutzregeln -----------------------------------------------------------------------------
    def branch_protection(self, repo: RepoRef, branch: str) -> BranchProtection | None:
        try:
            data = self.request("GET", f"/repos/{repo.owner}/{repo.name}/branches/{branch}/"
                                "protection", "Schutzregeln lesen",
                                Capability.BRANCH_PROTECTION).json()
        except NotFound:
            return None                                  # "Branch not protected"
        reviews = data.get("required_pull_request_reviews")
        return BranchProtection(
            reviews is not None,
            int((reviews or {}).get("required_approving_review_count") or 0),
            bool((reviews or {}).get("dismiss_stale_reviews")),
            bool((data.get("enforce_admins") or {}).get("enabled")),
            not bool((data.get("allow_deletions") or {}).get("enabled")))

    def set_branch_protection(self, repo: RepoRef, branch: str,
                              rules: BranchProtection | None) -> None:
        path = f"/repos/{repo.owner}/{repo.name}/branches/{branch}/protection"
        if rules is None or rules.empty:
            try:
                self.request("DELETE", path, "Schutzregeln entfernen",
                             Capability.BRANCH_PROTECTION)
            except NotFound:
                pass                                     # war schon ungeschützt
            return
        reviews = ({"required_approving_review_count": rules.approvals,
                    "dismiss_stale_reviews": rules.dismiss_stale}
                   if rules.pull_request_required else None)
        self.request("PUT", path, "Schutzregeln speichern", Capability.BRANCH_PROTECTION, json={
            "required_status_checks": None,
            "enforce_admins": rules.enforce_admins,
            "required_pull_request_reviews": reviews,
            "restrictions": None,
            "allow_force_pushes": False,             # nie (CLAUDE.md)
            "allow_deletions": not rules.prevent_deletion,
        })

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


def _role(person: dict) -> str:
    """Recht eines Mitarbeiters: role_name, sonst das höchste aus permissions."""
    role = str(person.get("role_name") or "")
    if role:
        return _permission(role)
    permissions = person.get("permissions") or {}
    for name in ("admin", "maintain", "push", "triage", "pull"):
        if permissions.get(name):
            return _permission(name)
    return "read"


def _permission(value: str) -> str:
    """Werte der API ("pull", "push", "write" ...) auf read, triage, write, maintain, admin."""
    return {"pull": "read", "push": "write"}.get(value, value or "read")


def _login(item: dict) -> str:
    return (item.get("user") or {}).get("login", "")


def _pull(data: dict) -> PullRequest:
    """Pull Request aus der Antwort von GitHub."""
    state = "merged" if data.get("merged_at") else data.get("state", "open")
    reviewers = tuple(r.get("login", "") for r in data.get("requested_reviewers") or [])
    return PullRequest(int(data.get("number", 0)), data.get("title", ""),
                       (data.get("head") or {}).get("ref", ""),
                       (data.get("base") or {}).get("ref", ""), _login(data), state,
                       bool(data.get("draft")), data.get("body") or "",
                       data.get("created_at", ""), data.get("html_url", ""), reviewers,
                       data.get("node_id", ""), data.get("mergeable"),
                       data.get("mergeable_state") or "")
