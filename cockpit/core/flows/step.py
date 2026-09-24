"""Ein Schritt eines Ablaufs und sein Ergebnis."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from cockpit.core.flows.hooks import Hook

if TYPE_CHECKING:
    from cockpit.core.flows.engine import FlowContext


@dataclass
class StepResult:
    ok: bool
    text: str = ""            # kurzer Satz für die Zusammenfassung
    details: str = ""         # technische Meldung, ohne Geheimnisse


@dataclass(frozen=True)
class Step:
    id: str
    title: str                                     # "Exe wird erstellt"
    hook: Hook
    run: Callable[["FlowContext"], StepResult]
    order: int = 100
    feature_id: str = ""                           # leer: Schritt des Kerns
    flows: tuple[str, ...] = ()                    # Kennungen der Abläufe, leer: alle
