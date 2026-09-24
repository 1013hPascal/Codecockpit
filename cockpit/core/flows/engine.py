"""Der Ablauf-Motor (Konzept 3.3 und 9.2).

Ein Ablauf wie "Änderungen hochladen" besteht aus den Schritten des Kerns und den Schritten aller
Features, die für das Projekt aktiv sind. Der Motor

1. sammelt und sortiert die Schritte nach Einhängepunkt und Reihenfolge,
2. zählt nur die aktiven Schritte ("Schritt 3 von 5: Exe wird erstellt"),
3. bricht bei einem Fehler bis einschließlich des Hochladens ab,
4. macht nach dem Hochladen trotz Fehlern weiter und nennt die Fehler in der Zusammenfassung.

run() blockiert und läuft deshalb in einem Hintergrund-Thread (ui/tasks.py). Pro Projekt läuft
immer nur ein Ablauf gleichzeitig.
"""
from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Iterator

from cockpit.core.errors import Cancelled, CockpitError
from cockpit.core.flows.questions import Asker, Question
from cockpit.core.flows.step import Step, StepResult

if TYPE_CHECKING:
    from cockpit.core.features.manager import FeatureManager
    from cockpit.core.projects import Project
    from cockpit.core.services import Services

log = logging.getLogger(__name__)


class ProjectBusy(CockpitError):
    def __init__(self, project_name: str) -> None:
        super().__init__(f"Für {project_name} läuft schon ein Vorgang. "
                         "Bitte warten Sie, bis er fertig ist.")


@dataclass(frozen=True)
class Flow:
    id: str                        # "push_changes"
    title: str                     # "Änderungen hochladen"
    core_steps: tuple[Step, ...] = ()


@dataclass
class FlowContext:
    """Alles, was ein Schritt braucht. data ist ein gemeinsamer Notizzettel der Schritte,
    zum Beispiel für die Commit-Nachricht oder die neue Versionsnummer."""
    services: "Services | None"
    project: "Project | None"
    asker: Asker
    cancel_event: threading.Event = field(default_factory=threading.Event)
    data: dict[str, Any] = field(default_factory=dict)
    status: Callable[[str], None] = lambda text: None

    def check_cancelled(self) -> None:
        if self.cancel_event.is_set():
            raise Cancelled()

    def ask(self, question: Question) -> Any:
        self.check_cancelled()
        answer = self.asker.ask(question)
        self.check_cancelled()
        return answer


@dataclass
class FlowSummary:
    flow: Flow
    total: int
    results: list[tuple[Step, StepResult]] = field(default_factory=list)
    aborted_at: Step | None = None
    cancelled: bool = False

    @property
    def completed(self) -> bool:
        return self.aborted_at is None and not self.cancelled

    @property
    def failures(self) -> list[tuple[Step, StepResult]]:
        return [(s, r) for s, r in self.results if not r.ok]

    def text(self) -> str:
        """Kurze Zusammenfassung, das Wichtigste vorne."""
        if self.cancelled:
            return f"Abgebrochen. {self.flow.title} wurde nicht fertig."
        if self.aborted_at is not None:
            number = len(self.results)
            result = self.results[-1][1]
            text = (f"Nicht fertig. Schritt {number} von {self.total} ist fehlgeschlagen: "
                    f"{self.aborted_at.title}.")
            return f"{text} {result.text}".strip()
        parts = [r.text for _, r in self.results if r.ok and r.text]
        failures = self.failures
        if failures:
            head = ("Fertig, aber ein Schritt hat nicht geklappt:" if len(failures) == 1
                    else f"Fertig, aber {len(failures)} Schritte haben nicht geklappt:")
            failed = " ".join(f"{s.title}. {r.text}".strip() for s, r in failures)
            return " ".join([head, failed, *parts])
        return " ".join(["Fertig.", *parts])


class FlowEngine:
    def __init__(self, features: "FeatureManager") -> None:
        self.features = features
        self._busy: set[int] = set()
        self._lock = threading.Lock()

    def steps_for(self, flow: Flow, project: "Project | None") -> list[Step]:
        """Die aktiven Schritte in der Reihenfolge der Ausführung."""
        steps = list(flow.core_steps)
        if project is not None:
            for manifest in self.features.active_features(project):
                steps.extend(s for s in manifest.steps if not s.flows or flow.id in s.flows)
        return sorted(steps, key=lambda s: (s.hook, s.order, s.id))

    def is_busy(self, project: "Project") -> bool:
        with self._lock:
            return project.id in self._busy

    @contextmanager
    def _reserve(self, project: "Project | None") -> Iterator[None]:
        if project is None:
            yield
            return
        with self._lock:
            if project.id in self._busy:
                raise ProjectBusy(project.name)
            self._busy.add(project.id)
        try:
            yield
        finally:
            with self._lock:
                self._busy.discard(project.id)

    def run(self, flow: Flow, context: FlowContext,
            on_progress: Callable[[int, int, str], None] = lambda n, total, text: None
            ) -> FlowSummary:
        """Führt den Ablauf aus. on_progress bekommt Nummer, Anzahl und den Text
        "Schritt 3 von 5: …"."""
        with self._reserve(context.project):
            steps = self.steps_for(flow, context.project)
            summary = FlowSummary(flow, len(steps))
            for number, step in enumerate(steps, start=1):
                if context.cancel_event.is_set():
                    summary.cancelled = True
                    break
                on_progress(number, len(steps),
                            f"Schritt {number} von {len(steps)}: {step.title}")
                try:
                    result = step.run(context)
                except Cancelled:
                    summary.cancelled = True
                    break
                except CockpitError as exc:
                    result = StepResult(False, exc.message, exc.details)
                except Exception as exc:             # ein Feature darf den Ablauf nie still beenden
                    log.exception("Unerwarteter Fehler in Schritt %s", step.id)
                    result = StepResult(False, "Unerwarteter Fehler.", repr(exc))
                summary.results.append((step, result))
                if not result.ok:
                    log.warning("Schritt %s fehlgeschlagen: %s %s", step.id, result.text,
                                result.details)
                    if step.hook.aborts_on_failure:
                        summary.aborted_at = step
                        break
            log.info("Ablauf %s: %s", flow.id, summary.text())
            return summary
