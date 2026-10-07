"""Starttest der KI und das Fenster „KI ist eingestellt auf diesen Rechner …“ (07.10.2026).

Nach dem Start misst das Cockpit im Hintergrund, wie schnell die Standard-Text-KI liest und
schreibt (ai_tuning.measure). Das Cockpit ist sofort benutzbar, bis dahin gelten Standardwerte.
Danach steht im Menü KI „KI ist eingestellt auf diesen Rechner …“. Das Fenster dazu erklärt die
Werte. Tab führt zur Auswahl „Ergebnisse nicht genau genug bei:“ (Pfeiltasten) und weiter zur Stufe
von +3 bis -3. Gemessen wird nur eine KI auf dem Rechner oder im eigenen Netz.
"""
from __future__ import annotations

import logging

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QDialogButtonBox, QListWidget, QVBoxLayout, QWidget

from cockpit.core import ai_tuning
from cockpit.core.ai_tuning import COMPLEX, LEVEL_NAMES, LEVELS, PURPOSES, TEXT_FIELDS
from cockpit.core.errors import CockpitError
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, PlainEdit, label_for
from cockpit.ui.tasks import Task

log = logging.getLogger(__name__)

NONE, RUNNING, DONE, FAILED, REMOTE = "none", "running", "done", "failed", "remote"
MENU_TEXTS = {NONE: "KI &einstellen …",
              RUNNING: "KI wird auf den Rechner &eingestellt …",
              DONE: "KI ist &eingestellt auf diesen Rechner …",
              FAILED: "KI nicht gemessen, Standardwerte &einstellen …",
              REMOTE: "KI außerhalb des Rechners, &einstellen …"}


class Calibrator(QObject):
    """Misst die Standard-Text-KI einmal pro Start im Hintergrund."""

    def __init__(self, services, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.state = NONE
        self.name = ""
        self.task: Task | None = None

    def _tool(self):
        tool = self.services.text_tool(None)
        if tool is None or not tool.model:
            return None
        return tool

    def start(self) -> None:
        tool = self._tool()
        if tool is None:
            self.state = NONE
            return
        self.name = self.services.ai_tools.label(tool, mark_default=False)
        if not self.services.ai_tools.is_local(tool):
            self.state = REMOTE              # nichts ohne Zustimmung nach draußen senden
            return
        try:
            provider = self.services.ai_tools.provider(tool)
        except CockpitError as exc:
            log.warning("KI für den Starttest nicht verfügbar: %s", exc.message)
            self.state = FAILED
            return
        self.state = RUNNING

        def ask(prompt: str, max_tokens: int) -> str:
            return str(provider.complete([{"role": "user", "content": prompt}],
                                         model=tool.model, max_tokens=max_tokens))

        def work(task: Task):
            provider.start()
            return ai_tuning.measure(ask, task.cancel_event)

        self.task = Task(work, self)
        self.task.result.connect(self._measured)
        self.task.error.connect(self._failed)
        self.task.start()

    def _measured(self, calibration) -> None:
        self.services.tunings.save_calibration(self.name, calibration)
        self.state = DONE
        log.info("KI eingestellt: %s, liest %s, schreibt %s Token pro Sekunde", self.name,
                 calibration.read_tps, calibration.write_tps)

    def _failed(self, message: str, details: str) -> None:
        log.warning("Starttest der KI: %s %s", message, details)
        self.state = FAILED

    def stop(self) -> None:
        if self.task is not None and self.task.isRunning():
            self.task.cancel()
            self.task.wait(5000)

    @property
    def menu_text(self) -> str:
        return MENU_TEXTS[self.state]


def _words(tps: float) -> int:
    return max(1, round(tps * 0.75))


def explanation(services, name: str, state: str, levels: dict[str, int]) -> str:
    """Erklärung im Fenster, das Wichtigste vorne."""
    limit = services.settings.load().ai_max_chars
    calibration = services.tunings.calibration(name) if name else None
    lines = []
    if state == NONE:
        lines.append("Es ist noch keine Text-KI mit Modell eingerichtet. Das geht im Menü KI, "
                     "KI-Verwaltung.")
    elif state == REMOTE:
        lines.append(f"{name} läuft außerhalb Ihres Rechners. Dorthin sendet das Cockpit nichts "
                     "für einen Test, deshalb gelten feste Werte.")
    elif state == RUNNING:
        lines.append(f"{name} wird gerade gemessen. Bis dahin gelten Standardwerte.")
    elif calibration is not None:
        lines.append(f"{name} ist auf diesen Rechner eingestellt. Gemessen am "
                     f"{calibration.day}: Sie liest etwa {_words(calibration.read_tps)} Wörter "
                     f"und schreibt etwa {_words(calibration.write_tps)} Wörter pro Sekunde.")
    else:
        lines.append(f"{name} ließ sich nicht messen. Es gelten Standardwerte.")
    for purpose, title in PURPOSES.items():
        level = levels.get(purpose, 0)
        tuned = ai_tuning.tuning(purpose, level, calibration, limit)
        target = round(ai_tuning.TARGET_SECONDS[purpose] * ai_tuning.STEP ** level)
        think = " Die KI denkt dabei nach." if tuned.think else ""
        lines.append(f"{title}: Stufe {level:+d}. Die KI bekommt bis zu {tuned.max_chars} "
                     f"Zeichen, Ziel etwa {target} Sekunden.{think}")
    lines.append("Sind die Ergebnisse nicht genau genug, wählen Sie unten die Art und eine "
                 "höhere Stufe. Höher heißt genauer, aber langsamer. Die Stufe 0 bei Textfeldern "
                 "ist schon knapper als die Stufe 0 bei Code.")
    return "\n".join(lines)


class AITuningDialog(FocusDialog):
    def __init__(self, services, name: str, state: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services, self.name, self.state = services, name, state
        self.levels = {p: services.tunings.level(p) for p in PURPOSES}
        self.setWindowTitle("KI einstellen")
        self.text = PlainEdit()
        self.text.setReadOnly(True)
        text_label = label_for(self.text, "&Erklärung:")
        self.purposes = QListWidget()
        self.purposes.addItems(list(PURPOSES.values()))
        purposes_label = label_for(self.purposes, "Ergebnisse nicht &genau genug bei:")
        self.scale = QListWidget()
        self.scale.addItems([LEVEL_NAMES[level] for level in LEVELS])
        scale_label = label_for(self.scale, "&Stufe:")
        buttons = QDialogButtonBox()
        buttons.addButton("Speichern", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Abbrechen", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        for widget in (text_label, self.text, purposes_label, self.purposes, scale_label,
                       self.scale, buttons):
            layout.addWidget(widget)
        self.purposes.currentRowChanged.connect(self._show_level)
        self.scale.currentRowChanged.connect(self._level_chosen)
        self.purposes.setCurrentRow(0)
        self._refresh()
        self.resize(640, 520)
        self.initial_focus_widget = self.text

    @property
    def purpose(self) -> str:
        return list(PURPOSES)[max(0, self.purposes.currentRow())]

    def _show_level(self, _row: int) -> None:
        self.scale.blockSignals(True)
        self.scale.setCurrentRow(LEVELS.index(self.levels[self.purpose]))
        self.scale.blockSignals(False)

    def _level_chosen(self, row: int) -> None:
        if row >= 0:
            self.levels[self.purpose] = LEVELS[row]
            self._refresh()

    def _refresh(self) -> None:
        self.text.setPlainText(explanation(self.services, self.name, self.state, self.levels))

    def save(self) -> None:
        for purpose, level in self.levels.items():
            self.services.tunings.set_level(purpose, level)
        announce("Gespeichert.")
        self.accept()


__all__ = ["AITuningDialog", "Calibrator", "COMPLEX", "TEXT_FIELDS"]
