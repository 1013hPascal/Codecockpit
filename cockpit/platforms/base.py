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
from pathlib import Path

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
    BRANCH_PROTECTION = auto()


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
    Capability.BRANCH_PROTECTION: "Schutzregeln",
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


# -- Pull Requests (Konzept 10.14, Phase 6) ----------------------------------------------------
@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    head: str                        # Branch mit den Änderungen, zum Beispiel "design"
    base: str                        # Ziel, zum Beispiel "main"
    author: str
    state: str = "open"              # "open", "closed" oder "merged"
    draft: bool = False
    body: str = ""
    created: str = ""                # ISO
    url: str = ""
    reviewers: tuple[str, ...] = ()  # angefragte Prüfer
    node_id: str = ""                # für GraphQL (Entwurf freigeben)
    mergeable: bool | None = None    # None: GitHub rechnet noch
    mergeable_state: str = ""        # "clean", "dirty" (Konflikte), "blocked", "behind" ...


@dataclass(frozen=True)
class PullRequestComment:
    author: str
    created: str                     # ISO
    body: str
    path: str = ""                   # Kommentar zu einer Zeile: Datei
    line: int = 0                    # und Zeile


@dataclass(frozen=True)
class Review:
    author: str
    state: str                       # "APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"
    body: str = ""
    submitted: str = ""              # ISO


# Art des Übernehmens: Wert der Plattform
MERGE_METHODS = ("merge", "squash", "rebase")


@dataclass(frozen=True)
class PullRequestFile:
    path: str
    status: str                      # "added", "modified", "removed", "renamed"
    additions: int = 0
    deletions: int = 0
    patch: str = ""                  # Änderungen im Format von git diff


class SupportsPullRequests:
    """Zusatz-Schnittstelle: Pull Requests (bei GitLab später Merge Requests)."""

    def pull_requests(self, repo: RepoRef, state: str = "open") -> list[PullRequest]:
        """state: "open", "closed" oder "all". Neueste zuerst."""
        raise NotImplementedError

    def pull_request(self, repo: RepoRef, number: int) -> PullRequest:
        raise NotImplementedError

    def create_pull_request(self, repo: RepoRef, head: str, base: str, title: str, body: str,
                            draft: bool = False, reviewers: tuple[str, ...] = ()) -> PullRequest:
        raise NotImplementedError

    def pull_request_comments(self, repo: RepoRef, number: int) -> list[PullRequestComment]:
        """Allgemeine Kommentare und solche zu einer Zeile, älteste zuerst."""
        raise NotImplementedError

    def add_pull_request_comment(self, repo: RepoRef, number: int, body: str) -> None:
        raise NotImplementedError

    def pull_request_files(self, repo: RepoRef, number: int) -> list[PullRequestFile]:
        raise NotImplementedError

    def set_pull_request_open(self, repo: RepoRef, number: int, open_: bool) -> None:
        """Schließen (False) oder wieder öffnen (True)."""
        raise NotImplementedError

    def mark_ready_for_review(self, repo: RepoRef, pull: PullRequest) -> None:
        """Entwurf zum Prüfen freigeben."""
        raise NotImplementedError

    # -- Phase 6b ------------------------------------------------------------------------------
    def reviews(self, repo: RepoRef, number: int) -> list[Review]:
        """Alle Reviews, älteste zuerst."""
        raise NotImplementedError

    def submit_review(self, repo: RepoRef, number: int, event: str, body: str) -> None:
        """event: "APPROVE", "REQUEST_CHANGES" oder "COMMENT"."""
        raise NotImplementedError

    def merge_methods(self, repo: RepoRef) -> list[str]:
        """Erlaubte Arten des Übernehmens aus MERGE_METHODS, in dieser Reihenfolge."""
        raise NotImplementedError

    def merge_pull_request(self, repo: RepoRef, number: int, method: str) -> None:
        raise NotImplementedError


# -- Schutzregeln (Phase 6c) --------------------------------------------------------------------
@dataclass(frozen=True)
class BranchProtection:
    """Schutzregeln für einen Branch, zum Beispiel main. Force push bleibt immer verboten."""
    pull_request_required: bool = False      # nur über Pull Request
    approvals: int = 0                       # so viele Genehmigungen sind nötig
    dismiss_stale: bool = False              # Genehmigungen verfallen bei neuen Commits
    enforce_admins: bool = False             # gilt auch für Administratoren
    prevent_deletion: bool = True            # der Branch darf nicht gelöscht werden

    @property
    def empty(self) -> bool:
        return not (self.pull_request_required or self.enforce_admins or self.prevent_deletion)


class SupportsBranchProtection:
    def branch_protection(self, repo: RepoRef, branch: str) -> BranchProtection | None:
        """Die Schutzregeln, None wenn der Branch keine hat."""
        raise NotImplementedError

    def set_branch_protection(self, repo: RepoRef, branch: str,
                              rules: BranchProtection | None) -> None:
        """Schutzregeln setzen. None oder leere Regeln: Schutz entfernen."""
        raise NotImplementedError


# -- Releases (Phase 10, Konzept 10.4 und 10.5) ----------------------------------------------------
@dataclass(frozen=True)
class ReleaseAsset:
    id: int
    name: str
    size: int                                # Bytes


@dataclass(frozen=True)
class Release:
    id: int
    tag: str                                 # "v1.3.0"
    name: str
    url: str                                 # Seite des Releases
    published: str                           # ISO-Datum
    assets: tuple[ReleaseAsset, ...] = ()
    upload_url: str = ""                     # nur für upload_asset


class SupportsReleases:
    def releases(self, repo: RepoRef) -> list[Release]:
        """Veröffentlichte Releases, das neueste zuerst."""
        raise NotImplementedError

    def create_release(self, repo: RepoRef, tag: str, name: str, body: str,
                       target: str) -> Release:
        """Release mit neuem Tag auf dem Commit oder Branch target anlegen."""
        raise NotImplementedError

    def upload_asset(self, repo: RepoRef, release: Release, path: Path) -> ReleaseAsset:
        raise NotImplementedError

    def download_asset(self, repo: RepoRef, asset: ReleaseAsset, target: Path,
                       cancel=None) -> None:
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
