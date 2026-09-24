"""Gemeinsame Test-Hilfen: temporäre Datenordner, Attrappen für alle Adapter-Arten, Test-Features.

Alle Geheimnisse in den Tests sind erfunden.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cockpit.adapters.base import TestResult  # noqa: E402
from cockpit.ai.base import AIProvider  # noqa: E402
from cockpit.automation.base import Automation, WorkflowStatus  # noqa: E402
from cockpit.core.availability import Availability  # noqa: E402
from cockpit.core.features.manifest import FeatureManifest  # noqa: E402
from cockpit.core.features.registry import FeatureRegistry  # noqa: E402
from cockpit.core.secret import Secret  # noqa: E402
from cockpit.core.services import Services  # noqa: E402
from cockpit.email.base import EmailSender  # noqa: E402
from cockpit.platforms.base import (Capability, GitCredentials, NewRepo, Platform,  # noqa: E402
                                    RepoInfo, RepoLinks, RepoRef, User)
from cockpit.vault.base import Vault  # noqa: E402

FAKE_TOKEN = "ghp_ErfundenerTestTokenNurFuerTests1234"


# -- Attrappen für jede Adapter-Art ---------------------------------------------------------
class FakePlatform(Platform):
    kind = "fake"
    display_name = "Testplattform"

    def __init__(self, capabilities: set[Capability] | None = None) -> None:
        self.caps = set(Capability) if capabilities is None else capabilities
        self.repos: dict[RepoRef, RepoInfo] = {}

    def test_connection(self) -> TestResult:
        return TestResult(True, "Verbindung in Ordnung.")

    def capabilities(self) -> set[Capability]:
        return set(self.caps)

    def permissions(self) -> dict[Capability, Availability]:
        return {c: Availability.yes() for c in self.caps}

    def current_user(self) -> User:
        return User("tester", "1")

    def organizations(self) -> list[str]:
        return []

    def noreply_email(self) -> str | None:
        return "1+tester@users.noreply.example"

    def create_repo(self, spec: NewRepo) -> RepoRef:
        ref = RepoRef("tester", spec.name)
        self.repos[ref] = RepoInfo(ref, spec.private, False, "main", f"https://x/{spec.name}")
        return ref

    def repo_info(self, repo: RepoRef) -> RepoInfo:
        return self.repos[repo]

    def set_visibility(self, repo: RepoRef, private: bool) -> None: ...
    def archive(self, repo: RepoRef) -> None: ...
    def delete(self, repo: RepoRef) -> None: ...

    def links(self, repo: RepoRef) -> RepoLinks:
        return RepoLinks(f"https://x/{repo.name}", f"https://x/{repo.name}#readme")

    def git_credentials(self) -> GitCredentials:
        return GitCredentials(False, {})


class FakeAI(AIProvider):
    kind = "fake_ai"
    display_name = "Test-KI"

    def __init__(self, is_local: bool = True, answers: list | None = None) -> None:
        self.is_local = is_local
        self.answers = list(answers or [])

    def test_connection(self) -> TestResult:
        return TestResult(True, "KI erreichbar.")

    def models(self) -> list[str]:
        return ["testmodell"]

    def complete(self, messages, *, model, system="", schema=None, max_tokens=None,
                 cancel: threading.Event | None = None):
        return self.answers.pop(0) if self.answers else "Antwort"


class FakeVault(Vault):
    kind = "fake_vault"
    display_name = "Test-Tresor"

    def __init__(self) -> None:
        self.entries: dict[str, Secret] = {}

    def test_connection(self) -> TestResult:
        return TestResult(True, "Tresor bereit.")

    def read(self, name: str) -> Secret | None:
        return self.entries.get(name)

    def write(self, name: str, value: Secret) -> None:
        self.entries[name] = value

    def delete(self, name: str) -> None:
        self.entries.pop(name, None)

    def names(self) -> list[str]:
        return sorted(self.entries)


class FakeAutomation(Automation):
    kind = "fake_automation"
    display_name = "Test-Automation"

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def test_connection(self) -> TestResult:
        return TestResult(True, "Automation läuft.")

    def is_running(self) -> bool:
        return True

    def install_workflows(self, feature_id, files) -> None: ...
    def set_workflows_active(self, feature_id, active) -> None: ...

    def call_webhook(self, name, data):
        self.calls.append((name, data))
        return {}

    def workflow_status(self) -> list[WorkflowStatus]:
        return []


class FakeEmail(EmailSender):
    kind = "fake_email"
    display_name = "Test-E-Mail"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    def test_connection(self) -> TestResult:
        return TestResult(True, "E-Mail in Ordnung.")

    def send_test_email(self, recipient: str) -> None:
        self.sent.append((recipient, "Test", ""))

    def send(self, recipient: str, subject: str, body: str) -> None:
        self.sent.append((recipient, subject, body))


# -- Test-Features ------------------------------------------------------------------------
def manifest(id: str, name: str | None = None, **kwargs) -> FeatureManifest:
    return FeatureManifest(id=id, name=name or id.capitalize(),
                           description=f"Test-Feature {id}.", **kwargs)


# -- Fixtures ---------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch) -> Path:
    """Jeder Test bekommt einen eigenen Datenordner."""
    path = tmp_path / "home"
    monkeypatch.setenv("CODECOCKPIT_HOME", str(path))
    return path


@pytest.fixture(autouse=True)
def _reset_announcer():
    """Der Announcer ist ein Modul-Singleton. Ohne Zurücksetzen zeigt target auf ein Fenster,
    das Qt am Testende zerstört hat, und der nächste Test stürzt ab (Erfahrung aus dem Tagebuch)."""
    from cockpit.ui.announcer import announcer
    announcer.reset()
    yield
    announcer.reset()


@pytest.fixture
def projects_root(tmp_path) -> Path:
    root = tmp_path / "Projekte"
    root.mkdir()
    return root


def make_project(root: Path, name: str, exe: bool = False) -> Path:
    code = root / name / "Code"
    code.mkdir(parents=True)
    (code / "main.py").write_text("print('hallo')\n", encoding="utf-8")
    if exe:
        (root / name / "Exe").mkdir()
    return root / name


@pytest.fixture
def make_services(tmp_path, projects_root):
    created = []

    def factory(manifests: list[FeatureManifest] | None = None, **kwargs) -> Services:
        from cockpit.core.database import Database
        from cockpit.core.projects import ProjectStore
        from cockpit.core.settings import SettingsStore
        database = Database(tmp_path / f"cockpit{len(created)}.db")
        services = Services(database=database, settings=SettingsStore(database),
                            projects=ProjectStore(database),
                            registry=FeatureRegistry(manifests or []), **kwargs)
        services.settings.update(projects_root=str(projects_root))
        created.append(services)
        return services

    yield factory
    for services in created:
        services.close()


def said(text: str) -> bool:
    from cockpit.ui.announcer import announcer
    return any(text in m.text for m in announcer.messages)


# -- Phase 3: Tresor und Konten ---------------------------------------------------------------
import keyring  # noqa: E402
from keyring.backend import KeyringBackend  # noqa: E402
from keyring.errors import PasswordDeleteError  # noqa: E402

from cockpit.adapters import registry as adapter_registry  # noqa: E402
from cockpit.adapters.base import AccountField  # noqa: E402
from cockpit.vault import crypto  # noqa: E402

FAST_KDF = crypto.KdfParameters(n=2 ** 10, r=8, p=1)     # schnell, nur für Tests


class MemoryKeyring(KeyringBackend):
    """Ersetzt die Windows-Anmeldeinformationsverwaltung in allen Tests."""
    priority = 1

    def __init__(self) -> None:
        super().__init__()
        self.entries: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self.entries.get((service, username))

    def set_password(self, service, username, password):
        self.entries[(service, username)] = password

    def delete_password(self, service, username):
        if self.entries.pop((service, username), None) is None:
            raise PasswordDeleteError("nicht vorhanden")


@pytest.fixture(autouse=True)
def memory_keyring():
    """Kein Test berührt die echte Windows-Anmeldeinformationsverwaltung."""
    previous = keyring.get_keyring()
    backend = MemoryKeyring()
    keyring.set_keyring(backend)
    yield backend
    keyring.set_keyring(previous)


@pytest.fixture(autouse=True)
def fast_vault_file(monkeypatch):
    """Schnelle Schlüsselableitung für neue Tresordateien in Tests."""
    from cockpit.vault import vault_file
    monkeypatch.setattr(vault_file, "DEFAULT_KDF", FAST_KDF)


class AccountPlatform(FakePlatform):
    """Testplattform mit Kontofeldern: Benutzername, Serveradresse, Team (extra), Token."""
    kind = "konto_test"
    display_name = "Kontotest"
    account_fields = (AccountField("username", "Benutzername"),
                      AccountField("url", "Serveradresse", required=False,
                                   default="https://git.example"),
                      AccountField("team", "Team", required=False),
                      AccountField("token", "Token", secret=True))

    def __init__(self, values=None) -> None:
        super().__init__()
        self.values = dict(values or {})

    @classmethod
    def from_account(cls, values):
        return cls(values)

    def test_connection(self) -> TestResult:
        token = self.values.get("token")
        if token is not None and token.reveal() == FAKE_TOKEN:
            return TestResult(True, f"Angemeldet als {self.values.get('username')}.")
        return TestResult(False, "Der Token wurde abgelehnt.", "HTTP 401")


@pytest.fixture
def account_adapter():
    adapter_registry.register("platform", AccountPlatform.kind, AccountPlatform)
    yield AccountPlatform
    adapter_registry.unregister("platform", AccountPlatform.kind)
