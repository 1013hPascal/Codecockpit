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
from cockpit.core.secret import Secret


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
    COLLABORATORS = auto()


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
    Capability.COLLABORATORS: "Mitarbeiter",
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
class RemoteRepo:
    """Ein Repository in der Liste der Plattform (für die Projektliste und das Herunterladen)."""
    ref: RepoRef
    private: bool
    clone_url: str               # Adresse für git clone, ohne Zugangsdaten
    web_url: str
    pushed_at: str = ""          # letztes Hochladen, ISO
    archived: bool = False


@dataclass(frozen=True)
class RepoLinks:
    project_page: str
    readme: str
    latest_download: str = ""


@dataclass(frozen=True)
class Collaborator:
    """Mitarbeiter eines Repositories oder eine offene Einladung."""
    login: str
    permission: str                 # "read", "triage", "write", "maintain", "admin"
    invitation_id: int = 0          # nicht 0: Einladung, noch nicht angenommen

    @property
    def invited(self) -> bool:
        return self.invitation_id != 0


# Rechte beim Einladen: Anzeige und Wert für die Plattform (ENTSCHEIDUNGEN.md, Phase 5e)
PERMISSION_NAMES = {"read": "lesen", "triage": "sichten", "write": "schreiben",
                    "maintain": "pflegen", "admin": "verwalten"}


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
    def repositories(self, owner: str = "") -> list[RemoteRepo]:
        """Repositories, neueste oben. owner leer: die eigenen des Kontos, sonst die der
        Organisation owner."""

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

    def unarchive(self, repo: RepoRef) -> None:
        """Archivierung aufheben. Plattformen, die das nicht können, melden es."""
        raise PlatformError("Die Plattform kann die Archivierung nicht aufheben.")

    def settings_url(self, repo: RepoRef) -> str:
        """Seite mit den Einstellungen des Repositories im Browser, leer wenn unbekannt."""
        return ""

    @abstractmethod
    def links(self, repo: RepoRef) -> RepoLinks: ...

    @abstractmethod
    def clone_url(self, repo: RepoRef) -> str:
        """Adresse für Git (clone, push), ohne Zugangsdaten."""

    def license_text(self, spdx: str, holder: str, year: int) -> str | None:
        """Text einer Lizenz mit Name und Jahr, None wenn die Plattform keine Vorlagen hat."""
        return None

    @abstractmethod
    def git_credentials(self) -> GitCredentials: ...


class SupportsCollaborators:
    """Zusatz-Schnittstelle: Mitarbeiter einladen und entfernen (Konzept 9.5)."""

    def collaborators(self, repo: RepoRef) -> list[Collaborator]:
        """Direkte Mitarbeiter und offene Einladungen."""
        raise NotImplementedError

    def invite(self, repo: RepoRef, login: str, permission: str) -> bool:
        """Einladen. True: Es ging eine Einladung hinaus, False: sofort Mitarbeiter (zum
        Beispiel Mitglieder derselben Organisation)."""
        raise NotImplementedError

    def change_permission(self, repo: RepoRef, person: Collaborator, permission: str) -> None:
        """Recht eines Mitarbeiters oder einer offenen Einladung ändern."""
        raise NotImplementedError

    def remove_collaborator(self, repo: RepoRef, login: str) -> None:
        raise NotImplementedError

    def cancel_invitation(self, repo: RepoRef, invitation_id: int) -> None:
        raise NotImplementedError


# -- Anmeldung im Browser (Device Flow, Konzept 6.1) ----------------------------------------
@dataclass(frozen=True)
class BrowserLogin:
    """Laufende Anmeldung im Browser: Der Nutzer gibt user_code auf verification_uri ein."""
    user_code: str
    verification_uri: str
    device_code: str
    interval: int                  # Sekunden zwischen zwei Nachfragen
    expires_in: int                # Sekunden, bis der Code verfällt


class SupportsBrowserLogin:
    """Zusatz-Schnittstelle für Plattformen mit Anmeldung im Browser.

    Ablauf: start_browser_login() liefert den Code. Die Oberfläche zeigt ihn an und öffnet den
    Browser. wait_for_browser_login() fragt im Hintergrund nach, bis der Nutzer bestätigt hat, und
    gibt dann den Token zurück."""

    @classmethod
    def browser_login_available(cls, url: str = "") -> bool:
        return False

    # Rechte für eine zweite, kurze Anmeldung nur zum Löschen. Leer: gibt es nicht.
    delete_login_scopes = ""

    @classmethod
    def start_browser_login(cls, url: str = "", scopes: str = "") -> BrowserLogin:
        """scopes leer: die Rechte der normalen Anmeldung."""
        raise NotImplementedError

    @classmethod
    def wait_for_browser_login(cls, login: BrowserLogin, url: str = "",
                               cancel=None) -> "Secret":
        raise NotImplementedError


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
