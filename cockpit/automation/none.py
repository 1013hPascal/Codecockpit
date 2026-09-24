"""Adapter "Keine Automation": Kern und lokale Features funktionieren ohne n8n."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from cockpit.adapters.base import TestResult
from cockpit.automation.base import Automation, WorkflowStatus
from cockpit.core.errors import CockpitError

NOT_CONFIGURED = "Es ist keine Automation eingerichtet."


class NoAutomation(Automation):
    kind = "none"
    display_name = "Keine Automation"
    configured = False

    def test_connection(self) -> TestResult:
        return TestResult(False, NOT_CONFIGURED)

    def is_running(self) -> bool:
        return False

    def install_workflows(self, feature_id: str, files: list[Path]) -> None:
        raise CockpitError(NOT_CONFIGURED)

    def set_workflows_active(self, feature_id: str, active: bool) -> None:
        """Ohne Automation gibt es nichts zu schalten."""

    def call_webhook(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        raise CockpitError(NOT_CONFIGURED)

    def workflow_status(self) -> list[WorkflowStatus]:
        return []
