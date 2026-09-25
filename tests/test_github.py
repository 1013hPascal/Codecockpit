"""GitHub-Adapter gegen einen nachgebauten Server (httpx.MockTransport). Kein echtes Netz."""
from __future__ import annotations

import json
import threading

import httpx
import pytest

from cockpit.core.accounts import find_type
from cockpit.core.errors import Cancelled, CockpitError
from cockpit.core.logging_setup import mask_secrets
from cockpit.core.secret import Secret
from cockpit.platforms import github
from cockpit.platforms.base import (BrowserLogin, Capability, NetworkError, NewRepo,
                                    NotAuthenticated, NotFound, PendingApproval,
                                    PermissionMissing, PlatformError, RepoRef,
                                    SsoAuthorizationRequired)
from cockpit.platforms.github import GitHubPlatform

TOKEN = "gho_ErfundenerTestTokenFuerGitHub12345"


class FakeGitHub:
    """Nachgebauter GitHub-Server. routes: (Methode, Pfad) -> (Status, JSON, Header)."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.routes: dict[tuple[str, str], tuple[int, object, dict]] = {
            ("GET", "/user"): (200, {"login": "1013hPascal", "id": 94653295, "name": "Pascal"},
                               {"X-OAuth-Scopes": "repo, read:org, workflow"}),
            ("GET", "/user/orgs"): (200, [{"login": "verein"}], {}),
        }

    def route(self, method: str, path: str, status: int = 200, body: object = None,
              headers: dict | None = None) -> None:
        self.routes[(method, path)] = (status, body if body is not None else {}, headers or {})

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        status, body, headers = self.routes.get((request.method, request.url.path),
                                                (404, {"message": "Not Found"}, {}))
        return httpx.Response(status, json=body, headers=headers)


@pytest.fixture
def server(monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setattr(GitHubPlatform, "transport", httpx.MockTransport(fake.handler))
    monkeypatch.setattr(GitHubPlatform, "sleep", staticmethod(lambda seconds: None))
    return fake


def platform(url: str = "https://github.com") -> GitHubPlatform:
    return GitHubPlatform(url, Secret(TOKEN))


# -- Adressen -------------------------------------------------------------------------------
def test_addresses_for_github_com_and_enterprise():
    assert github.api_base("https://github.com") == "https://api.github.com"
    assert github.api_base("") == "https://api.github.com"
    assert github.api_base("https://git.firma.de/") == "https://git.firma.de/api/v3"
    assert github.noreply_domain("https://github.com") == "users.noreply.github.com"
    assert github.noreply_domain("https://git.firma.de") == "users.noreply.git.firma.de"


def test_github_is_an_account_type():
    account_type = find_type("platform", "github")
    assert account_type.label == "GitHub, Plattform"
    assert [f.key for f in account_type.fields] == ["username", "url", "token"]
    assert [f.secret for f in account_type.fields] == [False, False, True]


# -- Verbindung -----------------------------------------------------------------------------
def test_connection_names_user_and_organizations(server):
    result = platform().test_connection()
    assert result.ok
    assert result.text == ("Verbindung in Ordnung. Angemeldet als 1013hPascal. "
                           "Organisationen: verein.")
    request = server.requests[0]
    assert request.url.host == "api.github.com"
    assert request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert TOKEN not in str(request.url)                    # nie in der Adresse


def test_connection_warns_about_missing_scopes(server):
    server.route("GET", "/user", body={"login": "a", "id": 1},
                 headers={"X-OAuth-Scopes": "read:org"})
    result = platform().test_connection()
    assert result.ok and result.text.endswith("Dem Token fehlen Rechte: repo und workflow.")


def test_rejected_token(server):
    server.route("GET", "/user", 401, {"message": "Bad credentials"})
    result = platform().test_connection()
    assert not result.ok
    assert result.text == github.TOKEN_REJECTED
    assert "HTTP 401" in result.details and TOKEN not in result.details


def test_sso_needs_authorization_with_link(server):
    link = "https://github.com/orgs/firma/sso?authorization_request=abc"
    server.route("GET", "/user", 403, {"message": "Resource protected by SAML"},
                 {"X-GitHub-SSO": f"required; url={link}"})
    result = platform().test_connection()
    assert not result.ok and result.text == github.SSO_REQUIRED
    assert result.link == link
    assert result.link_text == "Freigabeseite im Browser öffnen?"


def test_pending_approval(server):
    server.route("GET", "/user", 403, {"message": "Token is pending approval by the org"})
    with pytest.raises(PendingApproval, match="wartet auf die Genehmigung"):
        platform().current_user()


def test_rate_limit(server):
    server.route("GET", "/user", 403, {"message": "API rate limit exceeded"},
                 {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1790000000"})
    with pytest.raises(PlatformError, match="zu viele Anfragen"):
        platform().current_user()


def test_missing_permission_names_the_action(server):
    server.route("DELETE", "/repos/a/b", 403, {"message": "Must have admin rights"})
    with pytest.raises(PermissionMissing) as info:
        platform().delete(RepoRef("a", "b"))
    assert info.value.capability is Capability.DELETE_REPO
    assert "(Löschen)" in info.value.message


def test_not_found(server):
    with pytest.raises(NotFound, match="Repository lesen"):
        platform().repo_info(RepoRef("a", "fehlt"))


def test_no_network(monkeypatch):
    def broken(request):
        raise httpx.ConnectError("keine Verbindung")
    monkeypatch.setattr(GitHubPlatform, "transport", httpx.MockTransport(broken))
    with pytest.raises(NetworkError, match="nicht erreichbar"):
        platform().current_user()


def test_missing_token():
    with pytest.raises(NotAuthenticated, match="kein Token"):
        GitHubPlatform().current_user()


def test_enterprise_uses_its_own_api(server):
    server.route("GET", "/api/v3/user", body={"login": "mitarbeiter", "id": 7})
    assert platform("https://git.firma.de").current_user().login == "mitarbeiter"
    assert server.requests[0].url.host == "git.firma.de"
    assert server.requests[0].url.path == "/api/v3/user"


# -- Rechte ---------------------------------------------------------------------------------
def test_permissions_from_scopes(server):
    gh = platform()
    gh.current_user()
    permissions = gh.permissions()
    assert permissions[Capability.CREATE_REPO]
    assert not permissions[Capability.DELETE_REPO]
    assert "Löschen" in permissions[Capability.DELETE_REPO].reason


def test_fine_grained_token_has_unknown_but_allowed_permissions(server):
    server.route("GET", "/user", body={"login": "a", "id": 1})       # kein Scope-Header
    gh = platform()
    gh.current_user()
    assert all(gh.permissions().values())
    assert gh.missing_scopes() == []


def test_noreply_email(server):
    assert platform().noreply_email() == "94653295+1013hPascal@users.noreply.github.com"


# -- Repositories ---------------------------------------------------------------------------
def test_create_repo_in_own_account_and_organization(server):
    server.route("POST", "/user/repos", 201, {"name": "PDF-Chat", "owner": {"login": "me"}})
    server.route("POST", "/orgs/verein/repos", 201, {"name": "Web", "owner": {"login": "verein"}})
    assert platform().create_repo(NewRepo("PDF-Chat", "Chat mit PDFs")) == RepoRef("me", "PDF-Chat")
    body = json.loads(server.requests[-1].content)
    assert body == {"name": "PDF-Chat", "description": "Chat mit PDFs", "private": True,
                    "auto_init": False}
    assert platform().create_repo(NewRepo("Web", organization="verein")) == RepoRef("verein", "Web")


def test_create_existing_repo_is_explained(server):
    server.route("POST", "/user/repos", 422,
                 {"message": "Repository creation failed.",
                  "errors": [{"message": "name already exists on this account"}]})
    with pytest.raises(PlatformError, match="gibt es schon"):
        platform().create_repo(NewRepo("PDF-Chat"))


def test_repo_changes(server):
    for method in ("PATCH", "DELETE"):
        server.route(method, "/repos/me/x", 200 if method == "PATCH" else 204, {})
    server.route("GET", "/repos/me/x", body={"name": "x", "owner": {"login": "me"},
                                               "private": True, "archived": False,
                                               "default_branch": "main",
                                               "html_url": "https://github.com/me/x"})
    gh = platform()
    ref = RepoRef("me", "x")
    info = gh.repo_info(ref)
    assert info.private and info.default_branch == "main"
    gh.set_visibility(ref, False)
    assert json.loads(server.requests[-1].content) == {"private": False}
    gh.archive(ref)
    assert json.loads(server.requests[-1].content) == {"archived": True}
    gh.delete(ref)
    assert server.requests[-1].method == "DELETE"


def test_links():
    links = platform().links(RepoRef("me", "PDF-Chat"))
    assert links.project_page == "https://github.com/me/PDF-Chat"
    assert links.latest_download == "https://github.com/me/PDF-Chat/releases/latest"


def test_git_credentials_keep_token_out_of_command_line_and_log():
    credentials = platform().git_credentials()
    env = credentials.environment
    assert env["GIT_CONFIG_KEY_0"] == "http.https://github.com/.extraheader"
    assert TOKEN not in json.dumps(env)                      # nur verschlüsselt kodiert
    assert "***" in mask_secrets(env["GIT_CONFIG_VALUE_0"])
    assert env["GIT_CONFIG_VALUE_0"].split()[-1] not in mask_secrets(env["GIT_CONFIG_VALUE_0"])


# -- Anmeldung im Browser -------------------------------------------------------------------
def test_browser_login_needs_client_id_and_github_com(monkeypatch):
    monkeypatch.setattr(github, "CLIENT_ID", "")
    assert not GitHubPlatform.browser_login_available()
    monkeypatch.setattr(github, "CLIENT_ID", "Ov23Test")
    assert GitHubPlatform.browser_login_available("https://github.com")
    assert not GitHubPlatform.browser_login_available("https://git.firma.de")


def test_browser_login_start(server, monkeypatch):
    monkeypatch.setattr(github, "CLIENT_ID", "Ov23Test")
    server.route("POST", "/login/device/code", body={
        "device_code": "geraet", "user_code": "ABCD-1234",
        "verification_uri": "https://github.com/login/device", "interval": 5,
        "expires_in": 900})
    login = GitHubPlatform.start_browser_login()
    assert login.user_code == "ABCD-1234" and login.interval == 5
    assert b"client_id=Ov23Test" in server.requests[-1].content
    assert b"scope=repo+read%3Aorg+workflow" in server.requests[-1].content


def test_browser_login_disabled_is_explained(server, monkeypatch):
    monkeypatch.setattr(github, "CLIENT_ID", "Ov23Test")
    server.route("POST", "/login/device/code", 400, {"error": "device_flow_disabled"})
    with pytest.raises(CockpitError, match="Enable Device Flow"):
        GitHubPlatform.start_browser_login()


def login_answers(server, *answers) -> None:
    queue = list(answers)
    original = server.handler

    def handler(request):
        if request.url.path == "/login/oauth/access_token":
            server.requests.append(request)
            return httpx.Response(200, json=queue.pop(0))
        return original(request)

    GitHubPlatform.transport = httpx.MockTransport(handler)


LOGIN = BrowserLogin("ABCD-1234", "https://github.com/login/device", "geraet", 5, 900)


def test_browser_login_waits_until_confirmed(server):
    login_answers(server, {"error": "authorization_pending"}, {"error": "slow_down",
                                                                "interval": 10},
                  {"access_token": TOKEN, "scope": "repo,read:org,workflow"})
    token = GitHubPlatform.wait_for_browser_login(LOGIN, cancel=threading.Event())
    assert token.reveal() == TOKEN
    assert len([r for r in server.requests if r.url.path.endswith("access_token")]) == 3


@pytest.mark.parametrize("error, text", [("access_denied", "abgelehnt"),
                                         ("expired_token", "abgelaufen")])
def test_browser_login_denied_or_expired(server, error, text):
    login_answers(server, {"error": error})
    with pytest.raises(CockpitError, match=text):
        GitHubPlatform.wait_for_browser_login(LOGIN, cancel=threading.Event())


def test_browser_login_can_be_cancelled(monkeypatch):
    monkeypatch.setattr(GitHubPlatform, "sleep", staticmethod(__import__("time").sleep))
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(Cancelled):
        GitHubPlatform.wait_for_browser_login(LOGIN, cancel=cancel)
