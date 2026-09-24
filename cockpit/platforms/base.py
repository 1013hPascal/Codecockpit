"""Schnittstelle für Code-Plattformen (Konzept 6.3).

Nicht jede Plattform kann alles. Jeder Adapter meldet deshalb seine Fähigkeiten, und für das
angemeldete Konto zusätzlich, was es davon darf. Features, die eine fehlende Fähigkeit brauchen,
erscheinen als "nicht verfügbar" mit Begründung.

Spätere Phasen ergänzen eigene kleine Schnittstellen wie SupportsReleases oder
SupportsPullRequests. Ein Adapter erbt nur die, die er erfüllt.
"""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

from cockpit.adapters.base import Adapter
from cockpit.core.availability import Availability
from cockpit.core.errors import CockpitError


class Capability(Enum):
    CREATE_REPO = auto()
    DELETE_REPO = auto()
    ARCHIVE = auto()
    CHANGE_VISIBILITY = auto()
    ORGANIZATIONS = auto()
    NOREPLY_EMAIL = auto()
    RELEASES = auto()
    STARS = auto()
    FORKS = auto()
    ISSUES = auto()
    COMMENTS = auto()
    DOWNLOAD_COUNTS = auto()
    PULL_REQUESTS = auto()
    SECURITY_ALERTS = auto()


# Deutsche Namen für Begründungen ("Die Plattform kennt keine Releases.")
CAPABILITY_NAMES = {
    Capability.CREATE_REPO: "Repositories anlegen",
    Capability.DELETE_REPO: "Repositories löschen",
    Capability.ARCHIVE: "Archivieren",
    Capability.CHANGE_VISIBILITY: "Sichtbarkeit ändern",
    Capability.ORGANIZATIONS: "Organisationen",
    Capability.NOREPLY_EMAIL: "anonyme E-Mail-Adresse",
    Capability.RELEASES: "Releases",
    Capability.STARS: "Sterne",
    Capability.FORKS: "Forks",
    Capability.ISSUES: "Issues",
    Capability.COMMENTS: "Kommentare",
    Capability.DOWNLOAD_COUNTS: "Download-Zahlen",
    Capability.PULL_REQUESTS: "Pull Requests",
    Capability.SECURITY_ALERTS: "Sicherheitswarnungen",
}


@dataclass(frozen=True)
class User:
    login: str
    id: str
    name: str = ""


@dataclass(frozen=True)
class RepoRef:
    owner: str
    name: str


@dataclass(frozen=True)
class NewRepo:
    name: str
    description: str = ""
    private: bool = True
    organization: str = ""          # leer: eigenes Konto
    license: str = ""


@dataclass(frozen=True)
class RepoInfo:
    ref: RepoRef
    private: bool
    archived: bool
    default_branch: str
    web_url: str


@dataclass(frozen=True)
class RepoLinks:
    project_page: str
    readme: str
    latest_download: str = ""


@dataclass(frozen=True)
class GitCredentials:
    """Wie Git sich anmeldet. Geheimnisse gehen nur über Umgebungsvariablen an Git, nie über die
    Befehlszeile."""
    use_credential_manager: bool
    environment: dict[str, str]


class Platform(Adapter):
    @abstractmethod
    def capabilities(self) -> set[Capability]:
        """Was die Plattform grundsätzlich kann."""

    @abstractmethod
    def permissions(self) -> dict[Capability, Availability]:
        """Was dieses Konto mit seinem Zugang darf, mit Begründung bei fehlenden Rechten."""

    @abstractmethod
    def current_user(self) -> User: ...

    @abstractmethod
    def organizations(self) -> list[str]: ...

    @abstractmethod
    def noreply_email(self) -> str | None: ...

    @abstractmethod
    def create_repo(self, spec: NewRepo) -> RepoRef: ...

    @abstractmethod
    def repo_info(self, repo: RepoRef) -> RepoInfo: ...

    @abstractmethod
    def set_visibility(self, repo: RepoRef, private: bool) -> None: ...

    @abstractmethod
    def archive(self, repo: RepoRef) -> None: ...

    @abstractmethod
    def delete(self, repo: RepoRef) -> None: ...

    @abstractmethod
    def links(self, repo: RepoRef) -> RepoLinks: ...

    @abstractmethod
    def git_credentials(self) -> GitCredentials: ...


# -- Fehler der Plattform ----------------------------------------------------------------
class PlatformError(CockpitError):
    pass


class NotAuthenticated(PlatformError):
    """Zugang fehlt, ist abgelaufen oder widerrufen."""


class PermissionMissing(PlatformError):
    def __init__(self, capability: Capability, message: str, details: str = "") -> None:
        super().__init__(message, details)
        self.capability = capability


class SsoAuthorizationRequired(PlatformError):
    def __init__(self, url: str, message: str, details: str = "") -> None:
        super().__init__(message, details)
        self.url = url


class PendingApproval(PlatformError):
    pass


class ProtectedBranch(PlatformError):
    pass


class NotFound(PlatformError):
    pass


class NetworkError(PlatformError):
    pass
