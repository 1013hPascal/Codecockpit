"""Modell wählen und Arbeitsspeicher angeben.
"""
from __future__ import annotations

from PySide6.QtWidgets import QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget
from pathlib import Path

from cockpit.ai import models as model_tiers
from cockpit.core import hardware
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, click_focused_button, confirm, label_for, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row
from cockpit.ui.tasks import Task


LOADING = "Wird geladen …"


def manual_ram(services) -> float | None:
    value = services.database.get_value(hardware.MANUAL_KEY, None)
    return float(value) if isinstance(value, (int, float)) and value > 0 else None


def current_ram(services) -> float | None:
    """Schnell, ohne PowerShell: von Hand eingegeben, sonst von Windows."""
    return manual_ram(services) or hardware.ram_gb()


def recommendation_line(ram_gb: float | None) -> str:
    tier = model_tiers.recommended(model_tiers.TEXT_TIERS, ram_gb)
    if tier is not None:
        return (f"Empfehlung für Text-KI mit Ollama: {tier.model}, ab {tier.min_ram_gb} GB "
                f"Arbeitsspeicher, {tier.size}.")
    if ram_gb is None:
        return "Empfehlung: nicht möglich, weil der Arbeitsspeicher unbekannt ist."
    return ("Für eine lokale KI ist der Arbeitsspeicher knapp. Nehmen Sie ein kleines Modell oder "
            "eine KI im Firmennetz.")


class ModelDialog(FocusDialog):
    """Modell wählen. chosen nach "Übernehmen"."""

    def __init__(self, services, provider, is_ollama: bool, current: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.provider = provider
        self.is_ollama = is_ollama
        self.installed: list[str] = []
        self.chosen = ""
        self.task: Task | None = None
        self.ram = current_ram(services)
        self.setWindowTitle(f"Modell wählen: {provider.display_name}")
        self.installed_list = QListWidget()
        installed_label = label_for(self.installed_list, "&Installierte Modelle:")
        self.installed_list.installEventFilter(self)
        self.installed_list.itemActivated.connect(lambda _item: self.take_installed())
        self.installed_list.currentRowChanged.connect(lambda _row: self.copy_name())
        self.suggested: QListWidget | None = None
        self.edit = QLineEdit(current)
        edit_label = label_for(self.edit, "Modell&name:")
        self.edit.returnPressed.connect(self.take)
        take = QPushButton("&Übernehmen")
        take.clicked.connect(self.take)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        for button in (take, cancel):
            button.setAutoDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(installed_label)
        layout.addWidget(self.installed_list, 2)
        order: list[QWidget] = [self.installed_list]
        if is_ollama:
            self.suggested = QListWidget()
            suggested_label = label_for(self.suggested, "&Vorgeschlagene Modelle:")
            self.suggested.installEventFilter(self)
            self.suggested.itemActivated.connect(lambda _item: self.take_suggested())
            layout.addWidget(suggested_label)
            layout.addWidget(self.suggested, 1)
            order.append(self.suggested)
        layout.addWidget(edit_label)
        layout.addWidget(self.edit)
        layout.addLayout(button_row(None, take, cancel))
        order += [self.edit, take, cancel]
        for first, second in zip(order, order[1:]):
            self.setTabOrder(first, second)
        self.resize(640, 480)
        self.fill_suggestions()
        self.load()
        self.initial_focus_widget = self.installed_list

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)

    def eventFilter(self, watched, event) -> bool:
        if _is_enter(event):
            if watched is self.installed_list:
                self.take_installed()
                return True
            if watched is self.suggested:
                self.take_suggested()
                return True
        return super().eventFilter(watched, event)

    # -- Laden ------------------------------------------------------------------------------
    def load(self) -> None:
        """Installierte Modelle im Hintergrund. Ollama startet dabei bei Bedarf."""
        self.installed = []
        self.installed_list.clear()
        self.installed_list.addItem(LOADING)
        self.installed_list.setCurrentRow(0)
        provider = self.provider

        def work(task: Task) -> list[str]:
            provider.start()
            return provider.models()

        task = Task(work, self)
        task.result.connect(self.loaded)
        task.error.connect(self.load_failed)
        task.finished.connect(self._load_done)
        self.task = task
        task.start()

    def loaded(self, found: list[str]) -> None:
        self.installed = list(found)
        self.installed_list.blockSignals(True)
        self.installed_list.clear()
        if found:
            self.installed_list.addItems(found)
            current = self.edit.text().strip()
            self.installed_list.setCurrentRow(found.index(current) if current in found else 0)
        else:
            self.installed_list.addItem("Keine Modelle installiert." + (
                " Mit Tab kommen Sie zu den vorgeschlagenen." if self.is_ollama else ""))
            self.installed_list.setCurrentRow(0)
        self.installed_list.blockSignals(False)
        self.fill_suggestions()

    def load_failed(self, message: str, details: str) -> None:
        self.installed_list.clear()
        self.installed_list.addItem(f"Nicht geladen. {message}")
        self.installed_list.setCurrentRow(0)
        announce(f"Modelle nicht geladen. {message}")

    def _load_done(self) -> None:
        task, self.task = self.task, None
        if task is not None:
            task.wait()                      # Thread ganz beendet, sonst bricht Qt ab
            task.deleteLater()

    def fill_suggestions(self) -> None:
        if self.suggested is None:
            return
        row = self.suggested.currentRow()
        if row < 0:                                  # beim ersten Mal auf die Empfehlung
            best = model_tiers.recommended(model_tiers.TEXT_TIERS, self.ram)
            row = model_tiers.TEXT_TIERS.index(best) if best is not None else 0
        self.suggested.clear()
        self.suggested.addItems([model_tiers.suggestion_line(t, self.ram, self.installed)
                                 for t in model_tiers.TEXT_TIERS])
        self.suggested.setCurrentRow(row)

    # -- Wählen -----------------------------------------------------------------------------
    def copy_name(self) -> None:
        row = self.installed_list.currentRow()
        if 0 <= row < len(self.installed):
            self.edit.setText(self.installed[row])

    def take_installed(self) -> None:
        row = self.installed_list.currentRow()
        if 0 <= row < len(self.installed):
            self.edit.setText(self.installed[row])
            self.take()

    def take_suggested(self) -> None:
        if self.suggested is None:
            return
        row = self.suggested.currentRow()
        if not 0 <= row < len(model_tiers.TEXT_TIERS):
            return
        model = model_tiers.TEXT_TIERS[row].model
        if model_tiers.is_installed(model, self.installed):
            self.edit.setText(model)
            self.take()
            return
        self.download(model)

    def download(self, model: str) -> None:
        """Terminal mit dem Befehl im Befehlsfeld. Er läuft erst mit Enter."""
        from cockpit.ui.terminal_dialog import open_terminal
        open_terminal(self.services, self, Path.home(), f"Modell {model} herunterladen",
                      command=model_tiers.pull_command(model))
        self.edit.setText(model)
        self.load()
        if self.suggested is not None:
            self.suggested.setFocus()

    def take(self) -> None:
        name = self.edit.text().strip()
        if not name:
            show_error(self, self.windowTitle(), "Bitte ein Modell wählen oder den Namen "
                       "eingeben.")
            self.installed_list.setFocus()
            return
        if self.installed and name not in self.installed \
                and not model_tiers.is_installed(name, self.installed):
            if not confirm(self, self.windowTitle(), f"Das Modell {name} ist nicht installiert. "
                           "Trotzdem übernehmen?", yes="Übernehmen", no="Abbrechen"):
                self.edit.setFocus()
                return
        self.chosen = name
        self.accept()

    def done(self, code: int) -> None:
        from cockpit.ui.accounts_dialog import wait_for
        wait_for(self.task)
        super().done(code)


class RamDialog(FocusDialog):
    """Arbeitsspeicher von Hand eingeben, wenn Windows ihn nicht meldet. 0: wieder automatisch."""

    def __init__(self, current: float | None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from PySide6.QtWidgets import QSpinBox
        self.setWindowTitle("Arbeitsspeicher eingeben")
        self.value = 0
        self.hint = QListWidget()
        name_widget(self.hint, "Hinweis")
        self.hint.setWordWrap(True)
        self.hint.addItems([hardware.WHERE_TO_LOOK,
                            "Geben Sie die Zahl in GB ein. 0 heißt: wieder von Windows lesen."])
        self.hint.setCurrentRow(0)
        self.spin = QSpinBox()
        self.spin.setRange(0, 1024)
        self.spin.setValue(int(current or 0))
        spin_label = label_for(self.spin, "Arbeitsspeicher in &GB:")
        save = QPushButton("&Speichern")
        save.setDefault(True)
        save.clicked.connect(self.save)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.hint)
        layout.addWidget(spin_label)
        layout.addWidget(self.spin)
        layout.addLayout(button_row(None, save, cancel))
        self.resize(480, 260)
        self.initial_focus_widget = self.spin

    def save(self) -> None:
        self.value = self.spin.value()
        self.accept()
