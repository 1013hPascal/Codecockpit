"""KI-Verwaltung (Menü KI, Konzept 11.1, Teilschritt 8b).

AIManagerDialog: Liste "Text-KI und Sprach-KI", oben "Neue Text-KI einrichten …", darunter
"Neue Sprach-KI einrichten …" (Wunsch des Nutzers, 29.09.2026), dann die Werkzeuge, zum Beispiel
"Ollama auf diesem Rechner, gemma4:12b, Standard". Im Einrichtungsassistenten heißt der letzte
Knopf "KI-Einstellungen speichern" statt "Schließen". Enter wählt das Modell bzw. richtet eine neue
KI ein, Entf entfernt. Mit Tab: "Rechner und Empfehlung" (Arbeitsspeicher, Prozessor, Grafikkarte,
Empfehlung, Zustand von Ollama), dann die Knöpfe. Knöpfe, die für die markierte Zeile nicht passen,
sind ausgeblendet (Wunsch des Nutzers).

ModelDialog: Liste "Installierte Modelle", mit Tab bei Ollama "Vorgeschlagene Modelle", dann das
Feld "Modellname". Enter auf einem vorgeschlagenen, noch nicht installierten Modell öffnet das
Terminal mit "ollama pull …" im Befehlsfeld. Es läuft erst mit Enter.
"""
from __future__ import annotations


from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import hardware
from cockpit.core.ai_tools import ACCOUNT, OLLAMA, TEXT, AITool
from cockpit.core.errors import CockpitError
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import (
    FocusDialog, choose_from_list, click_focused_button, confirm, label_for, make_copyable)
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row
from cockpit.ui.tasks import Task
# Aufgeteilt am 22.10.2026: Teile stehen in ai_model_dialogs.py, ai_speech_dialogs.py. Die Namen bleiben hier erreichbar.
from cockpit.ui.ai_model_dialogs import (  # noqa: F401
    LOADING, ModelDialog, RamDialog, current_ram, manual_ram, recommendation_line)
from cockpit.ui.ai_speech_dialogs import NEW_SPEECH, SpeechDialog, speech_recommendation_line  # noqa: F401

NEW_TOOL = "Neue Text-KI einrichten …"
FIRST_TOOL_ROW = 2                 # davor stehen die beiden Einträge zum Einrichten
LOCAL_CHOICE = "Lokal: Ollama auf diesem Rechner"
NEW_ACCOUNT_CHOICE = "Extern: neues KI-Konto einrichten …"


class AIManagerDialog(FocusDialog):
    def __init__(self, services, parent: QWidget | None = None, for_setup: bool = False) -> None:
        super().__init__(parent)
        self.services = services
        self.tools: list[AITool] = []
        self.task: Task | None = None
        self.ollama_installed = True
        self.setWindowTitle("KI-Verwaltung")
        self.list = QListWidget()
        list_label = label_for(self.list, "&Text-KI und Sprach-KI:")
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
        # Die Sprach-KI steht jetzt als Eintrag in der Liste (Wunsch des Nutzers, 29.09.2026)
        close = QPushButton("&KI-Einstellungen speichern" if for_setup else "&Schließen")
        close.clicked.connect(self.accept)
        self.close_button = close
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
        self.list.addItem(NEW_SPEECH)
        self.list.addItems([tools.label(t) for t in self.tools])
        if select_id is not None:
            row = next((i + FIRST_TOOL_ROW for i, t in enumerate(self.tools)
                        if t.id == select_id), 0)
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))
        self.update_buttons()

    def current(self) -> AITool | None:
        index = self.list.currentRow() - FIRST_TOOL_ROW
        return self.tools[index] if 0 <= index < len(self.tools) else None

    def update_buttons(self) -> None:
        tool = self.current()
        default = self.services.ai_tools.default(TEXT)
        for button in (self.model_button, self.test_button, self.remove_button):
            button.setVisible(tool is not None)
        self.default_button.setVisible(tool is not None and default is not None
                                       and default.id != tool.id)

    def open_current(self) -> None:
        if self.list.currentRow() == 1:
            self.new_speech()
        elif self.current() is None:
            self.new_tool()
        else:
            self.choose_model()

    def new_speech(self) -> None:
        """Sprach-KI: Whisper-Modelle wählen und herunterladen (8d)."""
        SpeechDialog(self.services, self).exec()
        self.list.setFocus()

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
        lines = machine.lines() + [recommendation_line(machine.ram_gb),
                                   speech_recommendation_line(machine.ram_gb), ollama_state]
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


def show_guide(parent: QWidget, relative_path: str, title: str) -> None:
    from cockpit.core import paths
    from cockpit.ui.text_dialog import TextDialog
    try:
        text = (paths.resource_dir() / relative_path).read_text(encoding="utf-8")
    except OSError as exc:
        show_error(parent, title, "Die Anleitung wurde nicht gefunden.", str(exc))
        return
    TextDialog(title, text, f"Anleitung {title}", parent).exec()

