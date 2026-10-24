"""Sprache: Spracherkennung und Vorlesen einrichten.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from cockpit.ai import models as model_tiers
from cockpit.ui.ai_model_dialogs import current_ram
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, click_focused_button, confirm, label_for
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row
from cockpit.ui.tasks import Task


NEW_SPEECH = "Neue Sprach-KI einrichten …"


_BACKGROUND: list = []            # Downloads der Sprach-KI, die nach dem Schließen weiterlaufen


def speech_recommendation_line(ram_gb: float | None) -> str:
    """Empfehlung für die Sprach-KI (Whisper), wie für die Text-KI (Wunsch des Nutzers)."""
    tier = model_tiers.recommended(model_tiers.SPEECH_TIERS, ram_gb)
    if tier is not None:
        return (f"Empfehlung für Sprach-KI mit Whisper: {tier.model}, ab {tier.min_ram_gb} GB "
                f"Arbeitsspeicher, {tier.size}.")
    if ram_gb is None:
        return "Empfehlung für Sprach-KI: nicht möglich, weil der Arbeitsspeicher unbekannt ist."
    smallest = model_tiers.SPEECH_TIERS[0]
    return (f"Für die Sprach-KI ist der Arbeitsspeicher knapp. Am ehesten geht {smallest.model}, "
            f"{smallest.size}.")


class SpeechDialog(FocusDialog):
    """Sprach-KI (Teilschritt 8d): Whisper-Modelle auf diesem Rechner, mit Kontrollkästchen.
    Das angehakte Modell ist das gewählte (Wunsch aus dem Test von 8d). Leertaste oder Enter
    haken an. Knöpfe, die zur Zeile nicht passen, sind ausgeblendet, und Enter drückt den Knopf
    mit dem Fokus."""

    def __init__(self, services, parent: QWidget | None = None) -> None:
        from cockpit.ai import whisper
        super().__init__(parent)
        self.services = services
        self.task: Task | None = None
        self.setWindowTitle("Sprach-KI")
        self.list = QListWidget()
        label = label_for(self.list, "&Whisper-Modelle auf diesem Rechner:")
        self.list.installEventFilter(self)
        self.list.currentRowChanged.connect(lambda _row: self.update_buttons())
        self.list.itemChanged.connect(self.item_changed)
        self.choose_button = QPushButton("&Wählen")          # nur noch für die Tests sichtbar
        self.choose_button.clicked.connect(self.choose_current)
        self.choose_button.setVisible(False)
        self.download_button = QPushButton("&Herunterladen")
        self.download_button.clicked.connect(self.download_current)
        self.delete_button = QPushButton("&Löschen …")
        self.delete_button.clicked.connect(self.delete_current)
        close = QPushButton("&Schließen")
        close.clicked.connect(self.accept)
        for button in (self.choose_button, self.download_button, self.delete_button, close):
            button.setAutoDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(self.download_button, self.delete_button, None, close))
        self.problem = whisper.problem()
        self.resize(700, 320)
        self.initial_focus_widget = self.list
        self.fill()

    def tiers(self):
        return list(model_tiers.SPEECH_TIERS)

    def fill(self, row: int | None = None) -> None:
        from cockpit.ai import whisper
        row = self.list.currentRow() if row is None else row
        ram = current_ram(self.services)
        chosen = whisper.chosen_model(self.services.database, ram)
        installed = whisper.downloaded()
        self.list.blockSignals(True)
        self.list.clear()
        for tier in self.tiers():
            line = model_tiers.suggestion_line(tier, ram, installed).replace(
                "nicht installiert", "nicht heruntergeladen").replace(
                "installiert", "heruntergeladen")
            if tier.model in installed and not whisper.own_copy(tier.model):
                line += ", aus dem Zwischenspeicher von Hugging Face"
            item = QListWidgetItem(line)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if tier.model == chosen
                               else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        if self.problem:
            self.list.addItem(self.problem)
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))
        self.list.blockSignals(False)
        self.update_buttons()

    def item_changed(self, item) -> None:
        """Angehakt: dieses Modell wählen. Das gewählte lässt sich nicht einfach abhaken."""
        row = self.list.row(item)
        if not 0 <= row < len(self.tiers()):
            return
        self.list.setCurrentRow(row)
        self.choose_current()

    def current(self):
        row = self.list.currentRow()
        tiers = self.tiers()
        return tiers[row] if 0 <= row < len(tiers) else None

    def update_buttons(self) -> None:
        from cockpit.ai import whisper
        tier = self.current()
        downloaded = tier is not None and whisper.is_downloaded(tier.model)
        busy = self.task is not None
        self.download_button.setVisible(tier is not None and not downloaded and not busy
                                        and not self.problem)
        self.delete_button.setVisible(tier is not None and whisper.own_copy(tier.model)
                                      and not busy)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            self.choose_current()
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        # Wunsch aus dem Test von 8d: Enter drückt den Knopf mit dem Fokus, nicht nur Leertaste
        if not click_focused_button(self, event):
            super().keyPressEvent(event)

    def choose_current(self) -> None:
        from cockpit.ai import whisper
        tier = self.current()
        if tier is None:
            return
        self.services.database.set_value(whisper.MODEL_KEY, tier.model)
        self.fill(self.list.currentRow())
        announce(f"{tier.model} gewählt.")

    def download_current(self) -> None:
        from cockpit.ai import whisper
        tier = self.current()
        if tier is None or self.task is not None:
            return
        if not confirm(self, "Sprach-KI", f"Das Whisper-Modell {tier.model}, {tier.size}, kommt "
                       "aus dem Internet von Hugging Face in den Datenordner des Cockpits. "
                       "Herunterladen?", yes="Herunterladen", no="Abbrechen"):
            return
        task = Task(lambda t: whisper.download(tier.model), self)
        self.task = task

        def done(_value) -> None:
            announce(f"Whisper-Modell {tier.model} heruntergeladen.")

        def failed(message: str, details: str) -> None:
            try:
                show_error(self, "Sprach-KI", message, details)
            except RuntimeError:                        # Fenster schon geschlossen
                announce(message, urgent=True)

        def finished() -> None:
            task.wait()
            if task in _BACKGROUND:
                _BACKGROUND.remove(task)
            task.deleteLater()
            try:
                self.task = None
                self.fill()
            except RuntimeError:                        # Fenster schon geschlossen
                pass

        task.result.connect(done)
        task.error.connect(failed)
        task.finished.connect(finished)
        announce(f"Whisper-Modell {tier.model} wird heruntergeladen.")
        task.start()
        self.update_buttons()

    def delete_current(self) -> None:
        from cockpit.ai import whisper
        tier = self.current()
        if tier is None or not whisper.is_downloaded(tier.model):
            return
        if not confirm(self, "Sprach-KI", f"Das Whisper-Modell {tier.model} wird von diesem "
                       "Rechner gelöscht. Sie können es jederzeit wieder herunterladen. Löschen?",
                       yes="Löschen", no="Abbrechen"):
            return
        whisper.delete(tier.model)
        self.fill()
        announce(f"{tier.model} gelöscht.")

    def done(self, code: int) -> None:
        if self.task is not None:
            announce("Das Herunterladen läuft im Hintergrund weiter.", speak=False)
            self.task.setParent(None)                   # läuft weiter, auch ohne Fenster
            _BACKGROUND.append(self.task)               # hält den Thread am Leben
            self.task = None
        super().done(code)
