"""KI-Verwaltung (Menü KI, Konzept 11.1, Teilschritt 8b).

AIManagerDialog: Liste "Text-KI", oben "Neue Text-KI einrichten …", dann die Werkzeuge, zum Beispiel
"Ollama auf diesem Rechner, gemma4:12b, Standard". Enter wählt das Modell bzw. richtet eine neue KI
ein, Entf entfernt. Mit Tab: "Rechner und Empfehlung" (Arbeitsspeicher, Prozessor, Grafikkarte,
Empfehlung, Zustand von Ollama), dann die Knöpfe. Knöpfe, die für die markierte Zeile nicht passen,
sind ausgeblendet (Wunsch des Nutzers).

ModelDialog: Liste "Installierte Modelle", mit Tab bei Ollama "Vorgeschlagene Modelle", dann das
Feld "Modellname". Enter auf einem vorgeschlagenen, noch nicht installierten Modell öffnet das
Terminal mit "ollama pull …" im Befehlsfeld. Es läuft erst mit Enter.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.ai import models as model_tiers
from cockpit.core import hardware
from cockpit.core.ai_tools import ACCOUNT, OLLAMA, TEXT, AITool
from cockpit.core.errors import CockpitError
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import (FocusDialog, choose_from_list, click_focused_button, confirm,
                               label_for, make_copyable, name_widget)
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row
from cockpit.ui.tasks import Task

NEW_TOOL = "Neue Text-KI einrichten …"
LOCAL_CHOICE = "Lokal: Ollama auf diesem Rechner"
NEW_ACCOUNT_CHOICE = "Extern: neues KI-Konto einrichten …"
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


class AIManagerDialog(FocusDialog):
    def __init__(self, services, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.tools: list[AITool] = []
        self.task: Task | None = None
        self.ollama_installed = True
        self.setWindowTitle("KI-Verwaltung")
        self.list = QListWidget()
        list_label = label_for(self.list, "&Text-KI:")
        self.list.installEventFilter(self)
        self.list.itemActivated.connect(lambda _item: self.open_current())
        self.list.currentRowChanged.connect(lambda _row: self.update_buttons())
        delete_key = QShortcut(QKeySequence.StandardKey.Delete, self.list)
        delete_key.setContext(Qt.ShortcutContext.WidgetShortcut)
        delete_key.activated.connect(self.remove_current)
        self.info = QListWidget()
        info_label = label_for(self.info, "&Rechner und Empfehlung:")
        self.info.setWordWrap(True)
        make_copyable(self.info)

        self.model_button = QPushButton("&Modell wählen …")
        self.model_button.clicked.connect(self.choose_model)
        self.default_button = QPushButton("Als &Standard")
        self.default_button.clicked.connect(self.make_default)
        self.test_button = QPushButton("&Verbindung testen")
        self.test_button.clicked.connect(self.test_current)
        self.remove_button = QPushButton("&Entfernen")
        self.remove_button.clicked.connect(self.remove_current)
        self.install_button = QPushButton("Ollama &installieren …")
        self.install_button.clicked.connect(self.show_install_guide)
        self.install_button.setVisible(False)
        self.ram_button = QPushButton("&Arbeitsspeicher eingeben …")
        self.ram_button.clicked.connect(self.enter_ram)
        close = QPushButton("&Schließen")
        close.clicked.connect(self.accept)
        buttons = [self.model_button, self.default_button, self.test_button, self.remove_button,
                   self.install_button, self.ram_button, close]
        for button in buttons:
            button.setAutoDefault(False)
        layout = QVBoxLayout(self)
        layout.addWidget(list_label)
        layout.addWidget(self.list, 2)
        layout.addWidget(info_label)
        layout.addWidget(self.info, 2)
        layout.addLayout(button_row(*buttons[:4], None))
        layout.addLayout(button_row(*buttons[4:6], None, close))
        order = [self.list, self.info] + buttons
        for first, second in zip(order, order[1:]):
            self.setTabOrder(first, second)
        self.resize(760, 520)
        self.refresh()
        self.load_info()
        self.initial_focus_widget = self.list

    # -- Liste ------------------------------------------------------------------------------
    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            self.open_current()
            return True
        return super().eventFilter(watched, event)

    def refresh(self, select_id: int | None = None) -> None:
        row = self.list.currentRow()
        tools = self.services.ai_tools
        self.tools = tools.all(TEXT)
        self.list.clear()
        self.list.addItem(NEW_TOOL)
        self.list.addItems([tools.label(t) for t in self.tools])
        if select_id is not None:
            row = next((i + 1 for i, t in enumerate(self.tools) if t.id == select_id), 0)
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))
        self.update_buttons()

    def current(self) -> AITool | None:
        row = self.list.currentRow()
        return self.tools[row - 1] if 1 <= row <= len(self.tools) else None

    def update_buttons(self) -> None:
        tool = self.current()
        default = self.services.ai_tools.default(TEXT)
        for button in (self.model_button, self.test_button, self.remove_button):
            button.setVisible(tool is not None)
        self.default_button.setVisible(tool is not None and default is not None
                                       and default.id != tool.id)

    def open_current(self) -> None:
        if self.current() is None:
            self.new_tool()
        else:
            self.choose_model()

    # -- Rechner und Empfehlung -------------------------------------------------------------
    def load_info(self) -> None:
        """Rechner und Ollama im Hintergrund prüfen (PowerShell braucht etwa eine Sekunde)."""
        from cockpit.ai import ollama
        manual = manual_ram(self.services)
        self.info.clear()
        self.info.addItem(LOADING)
        self.info.setCurrentRow(0)

        def work(task: Task):
            return hardware.detect(manual), ollama.state(), ollama.find_exe() is not None

        task = Task(work, self)
        task.result.connect(self.info_loaded)
        task.error.connect(lambda message, details: self.show_info_lines([message]))
        task.finished.connect(self._info_done)
        self.task = task
        task.start()

    def info_loaded(self, outcome) -> None:
        machine, ollama_state, installed = outcome
        self.ollama_installed = installed
        lines = machine.lines() + [recommendation_line(machine.ram_gb), ollama_state]
        self.show_info_lines(lines)
        self.install_button.setVisible(not installed)

    def show_info_lines(self, lines: list[str]) -> None:
        row = max(0, self.info.currentRow())
        self.info.clear()
        self.info.addItems(lines)
        self.info.setCurrentRow(min(row, self.info.count() - 1))

    def _info_done(self) -> None:
        task, self.task = self.task, None
        if task is not None:
            task.wait()                      # Thread ganz beendet, sonst bricht Qt ab
            task.deleteLater()

    def show_install_guide(self) -> None:
        from cockpit.ai import ollama
        show_guide(self, ollama.GUIDE, "Ollama installieren")
        self.load_info()
        self.list.setFocus()

    def enter_ram(self) -> None:
        dialog = RamDialog(manual_ram(self.services), self)
        if dialog.exec():
            self.services.database.set_value(hardware.MANUAL_KEY, dialog.value or None)
            announce("Arbeitsspeicher gespeichert." if dialog.value
                     else "Arbeitsspeicher wird wieder von Windows gelesen.")
            self.load_info()
        self.ram_button.setFocus()

    # -- Einrichten -------------------------------------------------------------------------
    def ai_accounts(self) -> list:
        return [a for a in self.services.accounts.all() if a.kind == "ai"]

    def new_tool(self) -> None:
        accounts = self.ai_accounts()
        options = [LOCAL_CHOICE] + [f"Extern: {a.display_name}" for a in accounts] + \
            [NEW_ACCOUNT_CHOICE]
        chosen = choose_from_list(self, "Neue Text-KI", "Art der KI", options)
        if chosen is None:
            self.list.setFocus()
            return
        if chosen == 0:
            model = self.pick_model(self.services.ai_tools.ollama(), True, "")
            if model:
                self.added(self.services.ai_tools.add(TEXT, OLLAMA, model))
            return
        account = accounts[chosen - 1] if chosen <= len(accounts) else self.create_account()
        if account is None:
            self.list.setFocus()
            return
        provider = self.account_provider(account)
        if provider is None:
            return
        model = self.pick_model(provider, False, "")
        if model:
            self.added(self.services.ai_tools.add(TEXT, ACCOUNT, model, account.id))

    def create_account(self):
        """Kontenverwaltung bei den KI-Anbietern (Konzept 11.1): gleich ein neues KI-Konto."""
        from cockpit.core.accounts import account_types
        from cockpit.ui.accounts_dialog import AccountEditDialog
        types = [t for t in account_types() if t.kind == "ai"]
        if not types:
            show_error(self, "Neues KI-Konto", "Es gibt keine Art von KI-Konto.")
            return None
        account_type = types[0]
        if len(types) > 1:
            index = choose_from_list(self, "Neues KI-Konto", "Art des Kontos",
                                     [t.display_name for t in types])
            if index is None:
                return None
            account_type = types[index]
        dialog = AccountEditDialog(self.services, account_type, None, self)
        if not dialog.exec():
            return None
        self.services.forget_platforms()
        announce(f"Konto {dialog.saved.display_name} angelegt.")
        return dialog.saved

    def account_provider(self, account):
        if not vault_ui.ensure_unlocked(self.services, self):
            self.list.setFocus()
            return None
        try:
            return self.services.accounts.adapter_for(account)
        except CockpitError as exc:
            show_error(self, "KI-Verwaltung", exc.message, exc.details)
            return None

    def added(self, tool: AITool) -> None:
        self.refresh(tool.id)
        announce(f"Text-KI eingerichtet: {self.services.ai_tools.label(tool)}.")
        self.list.setFocus()

    def pick_model(self, provider, is_ollama: bool, current: str) -> str:
        dialog = ModelDialog(self.services, provider, is_ollama, current, self)
        return dialog.chosen if dialog.exec() else ""

    def provider_for(self, tool: AITool):
        if tool.source == OLLAMA:
            return self.services.ai_tools.ollama()
        account = self.services.accounts.get(tool.account_id or -1)
        return self.account_provider(account) if account is not None else None

    def choose_model(self) -> None:
        tool = self.current()
        if tool is None:
            return
        provider = self.provider_for(tool)
        if provider is None:
            return
        model = self.pick_model(provider, tool.source == OLLAMA, tool.model)
        if model and model != tool.model:
            self.services.ai_tools.set_model(tool.id, model)
            announce(f"Modell {model} gewählt.")
            self.refresh(tool.id)
        self.list.setFocus()

    def make_default(self) -> None:
        tool = self.current()
        if tool is None:
            return
        self.services.ai_tools.set_default(tool.id, TEXT)
        self.refresh(tool.id)
        announce(f"Standard: {self.services.ai_tools.label(tool, mark_default=False)}.")
        self.list.setFocus()

    def remove_current(self) -> None:
        tool = self.current()
        if tool is None:
            return
        label = self.services.ai_tools.label(tool, mark_default=False)
        text = (f"Die Text-KI {label} wird aus der Liste entfernt. Konten und installierte "
                "Modelle bleiben erhalten. Entfernen?")
        if not confirm(self, "Text-KI entfernen", text, yes="Entfernen", no="Abbrechen"):
            self.list.setFocus()
            return
        self.services.ai_tools.remove(tool.id)
        announce(f"{label} entfernt.")
        self.refresh()
        self.list.setFocus()

    def test_current(self) -> None:
        from cockpit.ui.accounts_dialog import run_in_background, show_test_result
        tool = self.current()
        if tool is None:
            return
        provider = self.provider_for(tool)
        if provider is None:
            return
        self.test_task = run_in_background(self, lambda task: provider.test_connection(),
                                           lambda result: show_test_result(self, result),
                                           self.test_button)

    def done(self, code: int) -> None:
        from cockpit.ui.accounts_dialog import wait_for
        for task in (self.task, getattr(self, "test_task", None)):
            wait_for(task)
        super().done(code)


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


def show_guide(parent: QWidget, relative_path: str, title: str) -> None:
    from cockpit.core import paths
    from cockpit.ui.text_dialog import TextDialog
    try:
        text = (paths.resource_dir() / relative_path).read_text(encoding="utf-8")
    except OSError as exc:
        show_error(parent, title, "Die Anleitung wurde nicht gefunden.", str(exc))
        return
    TextDialog(title, text, f"Anleitung {title}", parent).exec()
