"""Testplattform für die Testdaten (nur mit start_testdaten.bat).

Damit lässt sich die Kontenverwaltung schon vor der echten GitHub-Anbindung (Phase 4) mit NVDA
testen. Der Verbindungstest gelingt, wenn der Token "richtig" lautet.
"""
from __future__ import annotations

from typing import Any, Mapping

from cockpit.adapters import registry as adapter_registry
from cockpit.adapters.base import AccountField, TestResult
from cockpit.core.availability import Availability
from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret
from cockpit.platforms.base import (Capability, GitCredentials, NewRepo, Platform, RepoInfo,
                                    RepoLinks, RepoRef, User)

GOOD_TOKEN = "richtig"
_NOT_REAL = "Die Testplattform kann das nicht."


class TestPlatform(Platform):
    kind = "testplattform"
    display_name = "Testplattform"
    account_fields = (
        AccountField("username", "Benutzername"),
        AccountField("url", "Serveradresse", required=False, default="https://test.example"),
        AccountField("token", "Token", secret=True),
    )

    def __init__(self, username: str = "", url: str = "", token: Secret | None = None) -> None:
        self.username = username
        self.url = url
        self.token = token or Secret("")

    @classmethod
    def from_account(cls, values: Mapping[str, Any]) -> "TestPlatform":
        return cls(values.get("username", ""), values.get("url", ""), values.get("token"))

    def test_connection(self) -> TestResult:
        if self.token.reveal() == GOOD_TOKEN:
            return TestResult(True, f"Verbindung in Ordnung. Angemeldet als {self.username}.")
        return TestResult(False, "Der Token wurde abgelehnt.",
                          f"HTTP 401 Unauthorized von {self.url} (Testdaten)")

    def capabilities(self) -> set[Capability]:
        return {Capability.CREATE_REPO}

    def permissions(self) -> dict[Capability, Availability]:
        return {Capability.CREATE_REPO: Availability.yes()}

    def current_user(self) -> User:
        return User(self.username, "0")

    def organizations(self) -> list[str]:
        return []

    def noreply_email(self) -> str | None:
        return None

    def create_repo(self, spec: NewRepo) -> RepoRef:
        raise CockpitError(_NOT_REAL)

    def repo_info(self, repo: RepoRef) -> RepoInfo:
        raise CockpitError(_NOT_REAL)

    def set_visibility(self, repo: RepoRef, private: bool) -> None:
        raise CockpitError(_NOT_REAL)

    def archive(self, repo: RepoRef) -> None:
        raise CockpitError(_NOT_REAL)

    def delete(self, repo: RepoRef) -> None:
        raise CockpitError(_NOT_REAL)

    def links(self, repo: RepoRef) -> RepoLinks:
        raise CockpitError(_NOT_REAL)

    def git_credentials(self) -> GitCredentials:
        return GitCredentials(False, {})


def register() -> None:
    adapter_registry.register("platform", TestPlatform.kind, TestPlatform)
