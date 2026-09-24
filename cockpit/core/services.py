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
from cockpit.core.availability import Availability
from cockpit.core.database import Database
from cockpit.core.features.manager import FeatureManager
from cockpit.core.features.registry import FeatureRegistry
from cockpit.core.flows.engine import FlowEngine
from cockpit.core.projects import Project, ProjectStore
from cockpit.core.settings import SettingsStore
from cockpit.core.vault_service import NameIndex, VaultService, create_vault

if TYPE_CHECKING:
    from cockpit.ai.base import AIProvider
    from cockpit.automation.base import Automation
    from cockpit.email.base import EmailSender
    from cockpit.platforms.base import Capability, Platform
    from cockpit.vault.base import Vault

NO_AI = "Es ist kein KI-Anbieter eingerichtet."
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
    features: FeatureManager = field(init=False)
    flows: FlowEngine = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.vault, VaultService):
            self.vault = VaultService(self.vault or self._configured_vault(),
                                      NameIndex(self.database))
        self.accounts = AccountStore(self.database, self.vault)
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
            return Availability.yes() if self.ai is not None else Availability.no(NO_AI)
        if name == "automation":
            configured = self.automation is not None and self.automation.configured
            return Availability.yes() if configured else Availability.no(NO_AUTOMATION)
        if name == "email":
            return Availability.yes() if self.email is not None else Availability.no(NO_EMAIL)
        raise KeyError(name)

    def platform_for(self, project: Project) -> "Platform | None":
        if project.account_id is None:
            return None
        return self.platforms.get(project.account_id)

    def capabilities_for(self, project: Project) -> "set[Capability] | None":
        platform = self.platform_for(project)
        return platform.capabilities() if platform is not None else None

    def ai_for(self, task: str, project: Project | None = None) -> "AIProvider | None":
        """KI für eine Aufgabe. Die Datenschutz-Regel wird hier geprüft (ab Phase 7)."""
        if self.ai is None:
            return None
        if self.settings.load().ai_local_only and not self.ai.is_local:
            return None
        return self.ai
