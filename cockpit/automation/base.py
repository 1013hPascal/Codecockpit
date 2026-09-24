"""Schnittstelle für Automationsdienste wie n8n (Konzept 12). Umsetzung ab Phase 10."""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from cockpit.adapters.base import Adapter


@dataclass(frozen=True)
class WorkflowStatus:
    name: str
    active: bool
    last_run: str = ""            # Datum und Uhrzeit als Text, leer wenn nie gelaufen
    last_error: str = ""


class Automation(Adapter):
    configured: ClassVar[bool] = True       # False nur bei "Keine Automation"

    @abstractmethod
    def is_running(self) -> bool: ...

    def start(self) -> None:
        """Nur bei einer lokalen Instanz: starten, falls sie nicht läuft."""

    @abstractmethod
    def install_workflows(self, feature_id: str, files: list[Path]) -> None: ...

    @abstractmethod
    def set_workflows_active(self, feature_id: str, active: bool) -> None: ...

    @abstractmethod
    def call_webhook(self, name: str, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def workflow_status(self) -> list[WorkflowStatus]: ...
