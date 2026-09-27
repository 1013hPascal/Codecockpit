"""Knopf "Vorschlag der KI" (Feature KI-Assistent, Konzept 10.1, Teilschritt 8c).

- Alt+V. Der Name sagt, dass die KI den Vorschlag macht (Frage 11 zu Phase 8).
- Vor dem Senden: Tresor und Rückfrage bei KI außerhalb des Rechners (ui/ai_ui.py).
- Die KI arbeitet im Hintergrund. Das Fenster bleibt bedienbar. Escape bricht den Vorschlag ab,
  erst ein zweites Escape schließt das Fenster.
- Danach: "Vorschlag eingefügt." und der Fokus geht in das erste Feld.

Den Knopf gibt es nur, wenn das Feature im Projekt aktiv ist (Quelle nicht None).
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QPushButton, QWidget

from cockpit.core.ai_tools import TextAI
from cockpit.ui.announcer import announce
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

BUTTON_TEXT = "&Vorschlag der KI"
WORKING = "Die KI schreibt einen Vorschlag …"
INSERTED = "Vorschlag eingefügt."
CANCELLED = "Vorschlag abgebrochen."
WHAT = {"commit": "die Liste der geänderten Dateien und die geänderten Zeilen",
        "pull_request": "die Commit-Nachrichten und die geänderten Zeilen",
        "description": "die Dateiliste, der Anfang der README und die Imports"}


@dataclass
class SuggestionSource:
    """prepare: im Vordergrund, gibt TextAI oder den Grund zurück. make: im Hintergrund."""
    prepare: Callable[[QWidget], "TextAI | str"]
    make: Callable[[TextAI, threading.Event], object]


class SuggestButton(QPushButton):
    """apply bekommt den Vorschlag (features.ai_assistant.suggest.Suggestion) und setzt die
    Felder. first_field bekommt danach den Fokus."""

    def __init__(self, dialog: QWidget, source: SuggestionSource,
                 apply: Callable[[object], None], first_field: QWidget) -> None:
        super().__init__(BUTTON_TEXT, dialog)
        self.dialog = dialog
        self.source = source
        self.apply = apply
        self.first_field = first_field
        self.task: Task | None = None
        self.clicked.connect(self.start)

    @property
    def busy(self) -> bool:
        return self.task is not None

    def start(self) -> None:
        if self.busy:
            announce(WORKING)
            return
        ai = self.source.prepare(self.dialog)
        if isinstance(ai, str):
            show_error(self.dialog, "Vorschlag der KI", ai)
            self.setFocus()
            return
        make = self.source.make

        def work(task: Task):
            return make(ai, task.cancel_event)

        task = Task(work, self)
        task.result.connect(self.done)
        task.error.connect(self.failed)
        task.finished.connect(self._finished)
        self.task = task
        announce(WORKING)
        task.start()

    def done(self, suggestion) -> None:
        if not getattr(suggestion, "summary", ""):
            self.failed("Die KI hat keinen Vorschlag geliefert.", "")
            return
        self.apply(suggestion)
        announce(INSERTED)
        self.first_field.setFocus()

    def failed(self, message: str, details: str) -> None:
        announce(f"Kein Vorschlag. {message}", urgent=True, speak=False)
        show_error(self.dialog, "Vorschlag der KI", message, details)
        self.setFocus()

    def _finished(self) -> None:
        task, self.task = self.task, None
        if task is not None:
            task.deleteLater()

    def cancel(self) -> None:
        """Escape während die KI schreibt."""
        task = self.task
        if task is None:
            return
        task.cancel()
        try:
            task.result.disconnect(self.done)
            task.error.disconnect(self.failed)
        except (RuntimeError, TypeError):
            pass
        announce(CANCELLED)

    def wait(self, ms: int = 5000) -> None:
        task = self.task
        if task is not None:
            task.cancel()
            try:
                task.wait(ms)
            except RuntimeError:
                pass


def handle_escape(button: "SuggestButton | None") -> bool:
    """Für reject() der Fenster: True, wenn Escape nur den Vorschlag abgebrochen hat."""
    if button is not None and button.busy:
        button.cancel()
        return True
    return False


# -- Quellen ------------------------------------------------------------------------------------
def _assistant(services, project):
    """(Einstellung für Werkzeug, Sprache) wenn das Feature im Projekt aktiv ist, sonst None."""
    from cockpit.features.ai_assistant.manifest import FEATURE_ID
    if FEATURE_ID not in services.registry:
        return None
    features = services.features
    try:
        if not features.active(FEATURE_ID, project):
            return None
    except Exception:                                   # zum Beispiel Plattform nicht erreichbar
        return None
    return (features.setting(FEATURE_ID, "tool") or None,
            features.setting(FEATURE_ID, "language"))


def _source(services, project, what: str, make) -> SuggestionSource | None:
    from cockpit.features.ai_assistant.manifest import FEATURE_ID
    from cockpit.ui import ai_ui
    found = _assistant(services, project)
    if found is None:
        return None
    tool_id, language = found
    return SuggestionSource(
        lambda parent: ai_ui.prepare(services, parent, FEATURE_ID, WHAT[what], tool_id),
        lambda ai, cancel: make(ai, language, cancel))


def for_commit(services, project) -> SuggestionSource | None:
    from cockpit.features.ai_assistant import suggest
    code_dir = project.code_dir
    return _source(services, project, "commit",
                   lambda ai, language, cancel: suggest.commit(ai, code_dir, language, cancel))


def for_pull_request(services, project, head: str, base: Callable[[], str]
                     ) -> SuggestionSource | None:
    """base: gibt den gerade gewählten Ziel-Branch zurück."""
    from cockpit.features.ai_assistant import suggest
    code_dir = project.code_dir
    source = _source(services, project, "pull_request",
                     lambda ai, language, cancel: suggest.pull_request(
                         ai, code_dir, head, target, language, cancel))
    if source is None:
        return None
    target = ""
    prepare = source.prepare

    def prepare_with_base(parent):
        nonlocal target
        target = base()                  # im Vordergrund lesen, nicht aus dem Hintergrund
        return prepare(parent)
    source.prepare = prepare_with_base
    return source


def for_description(services, project) -> SuggestionSource | None:
    from cockpit.features.ai_assistant import suggest
    code_dir, name = project.code_dir, project.name
    return _source(services, project, "description",
                   lambda ai, language, cancel: suggest.description(ai, code_dir, name,
                                                                    language, cancel))
