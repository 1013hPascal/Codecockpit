"""Der Behälter, über den Features und Oberfläche an Kern-Dienste und Adapter kommen.

Features importieren keine konkreten Adapter, sondern fragen hier. In Tests wird der Behälter mit
Attrappen gefüllt.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from cockpit.adapters import registry as adapter_registry
from cockpit.core import paths
from cockpit.core.accounts import AccountStore
from cockpit.core.ai_tools import TEXT, AITool, AIToolStore, TextAI
from cockpit.core.availability import Availability
from cockpit.core.database import Database
from cockpit.core.errors import CockpitError
from cockpit.core.features.manager import FeatureManager
from cockpit.core.features.registry import FeatureRegistry
from cockpit.core.flows.engine import FlowEngine
from cockpit.core.projects import Project, ProjectStore
from cockpit.core.remote_repos import RemoteRepoStore
from cockpit.core.settings import SettingsStore
from cockpit.core.vault_service import NameIndex, VaultService, create_vault

if TYPE_CHECKING:
    from cockpit.core.pull_requests import PullRequestCache
    from cockpit.ai.base import AIProvider
    from cockpit.automation.base import Automation
    from cockpit.email.base import EmailSender
    from cockpit.platforms.base import Capability, Platform
    from cockpit.vault.base import Vault

NO_AI = "Es ist keine Text-KI eingerichtet. Das geht im Menü KI, KI-Verwaltung."
LOCAL_ONLY = ("Die Grundeinstellungen erlauben nur KI auf diesem Rechner oder im eigenen Netz. "
              "Die gewählte KI läuft außerhalb.")
NO_AUTOMATION = "Es ist keine Automation eingerichtet."
NO_EMAIL = "Es ist kein E-Mail-Konto eingerichtet."


@dataclass
class Services:
    database: Database
    settings: SettingsStore
    projects: ProjectStore
    registry: FeatureRegistry
    vault: "VaultService | Vault | None" = None
    vault_service_name: str = "CodeCockpit"          # Name in der Windows-Anmeldeinformationsverwaltung
    platforms: dict[int, "Platform"] = field(default_factory=dict)      # Konto -> Plattform
    ai: "AIProvider | None" = None
    automation: "Automation | None" = None
    email: "EmailSender | None" = None
    accounts: AccountStore = field(init=False)
    ai_tools: AIToolStore = field(init=False)
    remote_repos: RemoteRepoStore = field(init=False)
    pull_request_cache: "PullRequestCache" = field(init=False)
    features: FeatureManager = field(init=False)
    flows: FlowEngine = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.vault, VaultService):
            self.vault = VaultService(self.vault or self._configured_vault(),
                                      NameIndex(self.database))
        self.accounts = AccountStore(self.database, self.vault)
        self.ai_tools = AIToolStore(self.database, self.accounts)
        self.remote_repos = RemoteRepoStore(self.database)
        from cockpit.core.pull_requests import PullRequestCache
        self.pull_request_cache = PullRequestCache(self.database)
        if self.automation is None:
            self.automation = adapter_registry.adapter_class("automation", "none")()
        self.features = FeatureManager(self.registry, self.database, self.projects,
                                       self.settings, self.service_availability,
                                       self.capabilities_for)
        self.flows = FlowEngine(self.features)

    @classmethod
    def create(cls, database_path: Path, registry: FeatureRegistry | None = None,
               vault_service_name: str = "CodeCockpit") -> "Services":
        database = Database(database_path)
        return cls(database=database, settings=SettingsStore(database),
                   projects=ProjectStore(database),
                   registry=registry if registry is not None else FeatureRegistry.discover(),
                   vault_service_name=vault_service_name)

    # -- Tresor ---------------------------------------------------------------------------
    def _configured_vault(self) -> "Vault | None":
        kind = self.settings.load().vault_kind
        return self.make_vault(kind) if kind else None

    def make_vault(self, kind: str) -> "Vault":
        """Adapter für eine Speicherart, ohne ihn schon zu verwenden."""
        return create_vault(kind, self.database, paths.data_dir(), self.vault_service_name)

    def use_vault(self, vault: "Vault") -> None:
        """Speicherart übernehmen und in den Einstellungen merken."""
        self.vault.vault = vault
        self.settings.update(vault_kind=vault.kind)

    def close(self) -> None:
        self.database.close()

    # -- Dienste für Features -------------------------------------------------------------
    def service_availability(self, name: str) -> Availability:
        if name == "ai":
            problem = self.ai_problem()
            return Availability.no(problem) if problem else Availability.yes()
        if name == "automation":
            configured = self.automation is not None and self.automation.configured
            return Availability.yes() if configured else Availability.no(NO_AUTOMATION)
        if name == "email":
            return Availability.yes() if self.email is not None else Availability.no(NO_EMAIL)
        raise KeyError(name)

    def platform_for(self, project: Project) -> "Platform | None":
        """Plattform des Projekts. Ohne zugeordnetes Konto das Konto zur Adresse des Projekts."""
        account_id = project.account_id
        if account_id is None and project.remote is not None:
            account = self.account_for_host(project.remote.host)
            account_id = account.id if account else None
        return self.platform(account_id) if account_id is not None else None

    def platform_accounts(self) -> list:
        """Alle Konten bei Code-Plattformen."""
        return [a for a in self.accounts.all() if a.kind == "platform"]

    def account_for_host(self, host: str):
        """Erstes Plattform-Konto, dessen Serveradresse zum Rechnernamen passt."""
        from urllib.parse import urlparse
        host = host.lower()
        for account in self.platform_accounts():
            account_host = (urlparse(account.url or "https://github.com").hostname or "").lower()
            if account_host in (host, f"www.{host}") or host == f"www.{account_host}":
                return account
        return None

    def platform(self, account_id: int) -> "Platform | None":
        """Plattform-Adapter eines Kontos, beim ersten Mal mit dem Zugang aus dem Tresor gebaut.
        Der Tresor muss dafür offen sein (sonst VaultLocked)."""
        if account_id in self.platforms:
            return self.platforms[account_id]
        account = self.accounts.get(account_id)
        if account is None or account.kind != "platform":
            return None
        platform = self.accounts.adapter_for(account)
        self.platforms[account_id] = platform
        return platform

    def forget_platforms(self) -> None:
        """Nach Änderungen an Konten: Adapter beim nächsten Gebrauch neu bauen."""
        self.platforms.clear()

    def capabilities_for(self, project: Project) -> "set[Capability] | None":
        platform = self.platform_for(project)
        return platform.capabilities() if platform is not None else None

    def text_tool(self, tool_id: int | None = None) -> "AITool | None":
        """Werkzeug für Text-KI: das gewählte, sonst das Standard-Werkzeug."""
        return (self.ai_tools.get(tool_id) if tool_id else None) or self.ai_tools.default(TEXT)

    def ai_problem(self, tool_id: int | None = None) -> str:
        """Warum es keine Text-KI gibt, leer wenn es eine gibt (ohne Tresor)."""
        if self.ai is not None:
            local = self.ai.is_local
        else:
            tool = self.text_tool(tool_id)
            if tool is None:
                return NO_AI
            local = self.ai_tools.is_local(tool)
        if self.settings.load().ai_local_only and not local:
            return LOCAL_ONLY
        return ""

    def ai_for(self, task: str, project: Project | None = None,
               tool_id: int | None = None) -> "TextAI | None":
        """Text-KI für eine Aufgabe, None wenn es keine gibt oder die Datenschutz-Regel sie
        sperrt. Bei einem KI-Konto muss der Tresor offen sein (sonst VaultLocked)."""
        settings = self.settings.load()
        if self.ai is not None:                       # Tests und fest vorgegebene KI
            provider, model, name = self.ai, "", self.ai.display_name
            try:
                model = (self.ai.models() or [""])[0]
            except CockpitError:
                pass
        else:
            tool = self.text_tool(tool_id)
            if tool is None:
                return None
            provider = self.ai_tools.provider(tool)
            model, name = tool.model, self.ai_tools.label(tool, mark_default=False)
        if settings.ai_local_only and not provider.is_local:
            return None
        return TextAI(provider, model, name, settings.ai_max_chars)
