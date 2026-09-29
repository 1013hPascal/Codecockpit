"""Einrichtungsassistent beim ersten Start (Konzept 8.7, ohne Profile).

Eigene Umsetzung statt QWizard, damit Fokus und Ansagen verlässlich sind. Jede Seite ist ein
einfaches Formular. Unten stehen erst die Knöpfe nach vorn, dann die nach hinten (Wunsch des
Nutzers, 29.09.2026): "Weiter" bzw. "Fertig", "Überspringen" (wo erlaubt), "Zurück", dann
"Abbrechen". Beim Seitenwechsel sagt das Cockpit "Schritt 2 von 8: Zugangsdaten schützen" und eine
kurze Erklärung an, der Fokus steht im ersten Feld der Seite.

Seiten: Willkommen, Zugangsdaten schützen (Pflicht), Git, Code-Plattformen wählen, Code-Plattformen
einrichten (mit Git-Identität im Konto-Fenster), Projekte-Hauptordner, KI und die Zusammenfassung.
Seiten, die nicht nötig sind, lässt der Assistent aus, zum Beispiel "Code-Plattformen einrichten",
wenn keine Plattform gewählt ist.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
                               QStackedWidget, QVBoxLayout, QWidget)

from cockpit import APP_NAME
from cockpit.core import git, paths
from cockpit.core.services import Services
from cockpit.core.settings import setting_fields
from cockpit.core.text import count
from cockpit.ui import vault_ui, videos
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, announce_focus, confirm, label_for, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.form_builder import FormError, SettingsForm
from cockpit.ui.tasks import Task
from cockpit.ui.text_dialog import TextDialog

FEATURES = [
    "Die wichtigsten Aktionen für Ihre Code-Projekte, ganz ohne Terminal",
    "Volle Funktionalität mit integriertem Terminal und intelligenter Unterstützung",
    "Hochladen und Herunterladen mit GitHub",
    "Branches, Pull Requests und Zusammenführen",
    "Versionen, Releases und Exe-Dateien",
    "README in mehreren Sprachen",
    "Spracheingabe",
    "KI-Hilfe bei Fragen zur Bedienung",
    "Alles per Tastatur, gemacht für Screenreader und Braillezeile",
]


VIDEO_CREDIT = "Videos: erstellt mit Google NotebookLM"


def _lines(name: str, lines: list[str]) -> QListWidget:
    """Erklärung als Liste: eine Zeile pro Satz, gut lesbar auf der Braillezeile."""
    widget = QListWidget()
    name_widget(widget, name)
    widget.setWordWrap(True)
    widget.addItems(lines)
    widget.setCurrentRow(0)
    return widget


def _button_row(*buttons: QPushButton) -> QHBoxLayout:
    row = QHBoxLayout()
    for button in buttons:
        row.addWidget(button)
    row.addStretch(1)
    return row


class Page(QWidget):
    title = ""
    intro = ""                       # kurze Ansage beim Öffnen der Seite
    can_skip = True
    in_summary = True                # erscheint in der Zusammenfassung
    done_text = ""                   # für die Zusammenfassung, leer: übersprungen
    later = ""                       # wo man es nachholen kann

    def __init__(self, wizard: "SetupWizard") -> None:
        super().__init__()
        self.wizard = wizard
        self.services = wizard.services
        self.layout_ = QVBoxLayout(self)

    def first_focus(self) -> QWidget | None:
        return None

    def needed(self) -> bool:
        """False: Der Assistent lässt die Seite aus."""
        return True

    def next_text(self) -> str:
        """Beschriftung des Knopfs Weiter auf dieser Seite."""
        return "&Weiter"

    def on_show(self) -> None:
        """Beim Öffnen der Seite, zum Beispiel um den Zustand neu zu prüfen."""

    def accept_page(self) -> bool:
        """Bei "Weiter": prüfen und speichern. False bleibt auf der Seite."""
        return True


class WelcomePage(Page):
    title = "Willkommen"
    intro = f"Willkommen bei {APP_NAME}."
    can_skip = False
    in_summary = False

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        # Wunsch des Nutzers: erst der Text, mit Tab der Knopf für das Video, dann Weiter
        self.text = _lines("Willkommen", [
            f"Willkommen bei {APP_NAME}.",
            "In diesem Programm erwartet Sie:",
            *FEATURES,
            "Dieser Assistent richtet das Wichtigste dafür ein.",
            "Nur der Schutz Ihrer Zugangsdaten ist Pflicht. Alles andere können Sie überspringen "
            "und später über die Menüs ändern.",
            "Mit Tab kommen Sie zur kurzen Einführung als Video.",
            VIDEO_CREDIT,
        ])
        self.video_button = QPushButton("Kurze &Einführung anschauen")
        self.video_button.clicked.connect(self.show_video)
        self.layout_.addWidget(self.text)
        self.layout_.addLayout(_button_row(self.video_button))

    def show_video(self) -> None:
        videos.open_video(self.wizard, videos.INTRO, "Kurze Einführung")
        self.video_button.setFocus()

    def first_focus(self):
        return self.text


class VaultPage(Page):
    title = "Zugangsdaten schützen"
    intro = "Wählen Sie, wo Ihre Zugangsdaten gespeichert werden. Dieser Schritt ist Pflicht."
    can_skip = False
    later = "Menü Konten, Tresor-Einstellungen"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.text = _lines("Erklärung", [
            "In den folgenden Schritten richten Sie Ihr Git-Programm ein und weitere Dienste wie "
            "KI und Automatisierung. Sie vereinfachen Ihren Arbeitsalltag.",
            "Für diese Dienste braucht das Cockpit Zugangsdaten. Zum Beispiel den Zugang zu "
            "GitHub, den Schlüssel für eine externe KI oder das Passwort für ein E-Mail-Konto.",
            "Mit diesen Zugangsdaten kann jemand in Ihrem Namen Code ändern oder löschen und "
            "Dienste nutzen, die Geld kosten. Deshalb speichert das Cockpit sie nie offen, "
            "sondern immer geschützt.",
            "Sie wählen jetzt, wo die Zugangsdaten liegen. Es gibt zwei Möglichkeiten.",
            "Erstens: Windows-Anmeldeinformationsverwaltung, empfohlen. Windows schützt die "
            "Zugangsdaten mit Ihrer Windows-Anmeldung. Sie brauchen kein zusätzliches Passwort.",
            "Zweitens: Verschlüsselte Tresordatei. Sie schützen sie mit einem eigenen "
            "Master-Passwort. Sinnvoll, wenn mehrere Personen Ihr Windows-Konto nutzen.",
            "Das Master-Passwort fragt das Cockpit beim Start ab. Geht es verloren, müssen Sie "
            "alle Zugangsdaten neu eingeben.",
            "Gesperrt heißt bei der Tresordatei: Die Zugangsdaten sind nicht lesbar. Alles ohne "
            "Zugangsdaten funktioniert weiter. Braucht eine Aktion einen Zugang, fragt das "
            "Cockpit nach dem Master-Passwort.",
            "Die Speicherart lässt sich später wechseln, ohne etwas neu einzugeben.",
            "Mit Tab kommen Sie zur Auswahl der Speicherart.",
        ])
        # Auswahl als Liste statt Auswahlschaltern: Im Test sagte NVDA bei beiden Schaltern
        # "markiert". Eine Liste mit einem markierten Eintrag ist eindeutig.
        self.choice = QListWidget()
        self.choice.addItems(["Windows-Anmeldeinformationsverwaltung (empfohlen)",
                              "Verschlüsselte Tresordatei mit Master-Passwort"])
        self.choice.setCurrentRow(1 if self.services.vault.kind == "vault_file" else 0)
        self.choice.itemActivated.connect(lambda item: wizard.next())
        self.layout_.addWidget(self.text, 3)
        self.layout_.addWidget(label_for(self.choice, "&Speicherart:"))
        self.layout_.addWidget(self.choice, 1)

    def chosen_kind(self) -> str:
        return "vault_file" if self.choice.currentRow() == 1 else "windows"

    def first_focus(self):
        return self.text                            # zuerst die Erklärung, dann mit Tab die Wahl

    def accept_page(self) -> bool:
        if not vault_ui.switch_vault(self.services, self.chosen_kind(), self.wizard):
            return False
        self.done_text = f"Zugangsdaten: {self.services.vault.display_name}."
        return True


class GitPage(Page):
    title = "Git"
    later = "Menü Hilfe, Git installieren"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.state = _lines("Git", [])
        self.guide_button = QPushButton("&Anleitung anzeigen …")
        self.guide_button.clicked.connect(self.show_guide)
        self.check_button = QPushButton("&Erneut prüfen")
        self.check_button.clicked.connect(self.recheck)
        self.layout_.addWidget(self.state)
        self.layout_.addLayout(_button_row(self.guide_button, self.check_button))

    def on_show(self) -> None:
        found = git.find_git()
        self.state.clear()
        if found:
            self.intro = "Git ist installiert."
            self.done_text = "Git ist installiert."
            self.state.addItems(["Git ist installiert.", f"Gefundenes Git-Programm: {found}"])
        else:
            self.intro = "Git wurde nicht gefunden."
            self.done_text = ""
            self.state.addItems([
                "Git wurde nicht gefunden.",
                "Ohne Git kann das Cockpit keine Änderungen hochladen.",
                "Die Anleitung zeigt drei Wege zur Installation.",
                "Nach der Installation wählen Sie Erneut prüfen.",
            ])
        self.state.setCurrentRow(0)
        self.guide_button.setVisible(found is None)
        self.check_button.setVisible(found is None)

    def recheck(self) -> None:
        self.on_show()
        announce(self.intro)
        self.state.setFocus()

    def show_guide(self) -> None:
        try:
            text = (paths.resource_dir() / git.GUIDE).read_text(encoding="utf-8")
        except OSError as exc:
            show_error(self, "Git installieren", "Die Anleitung wurde nicht gefunden.", str(exc))
            return
        TextDialog("Git installieren", text, "Anleitung Git installieren", self).exec()
        self.guide_button.setFocus()

    def first_focus(self):
        return self.state


def platform_types() -> list:
    """Alle Code-Plattformen, für die es einen Adapter gibt. Zurzeit GitHub, später auch GitLab
    und andere (Phase 16). Neue Adapter erscheinen hier von selbst."""
    from cockpit.core.accounts import account_types
    return [t for t in account_types() if t.kind == "platform"]


class PlatformChoicePage(Page):
    """Wunsch des Nutzers: erst die Git-Systeme wählen, dann einrichten."""
    title = "Code-Plattformen wählen"
    intro = "Wählen Sie Ihr Git-System aus, das Sie verwenden möchten."
    in_summary = False

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.types = platform_types()
        text = QLabel("Wählen Sie Ihr Git-System aus, das Sie verwenden möchten. Mit der "
                      "Leertaste haken Sie an. Weitere Systeme wie GitLab folgen später.")
        text.setWordWrap(True)
        self.list = QListWidget()
        existing = {a.adapter for a in self.services.accounts.all() if a.kind == "platform"}
        for account_type in self.types:
            item = QListWidgetItem(account_type.display_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = account_type.adapter in existing or len(self.types) == 1
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        self.list.itemActivated.connect(lambda item: wizard.next())
        self.layout_.addWidget(text)
        self.layout_.addWidget(label_for(self.list, "&Git-Systeme:"))
        self.layout_.addWidget(self.list, 1)

    def chosen(self) -> list:
        return [t for row, t in enumerate(self.types)
                if self.list.item(row).checkState() == Qt.CheckState.Checked]

    def first_focus(self):
        return self.list


class PlatformSetupPage(Page):
    title = "Code-Plattformen einrichten"
    intro = "Nun können Sie Ihre Code-Plattformen einrichten."
    can_skip = False
    later = "Menü Konten, Kontenverwaltung"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        text = QLabel("Nun können Sie Ihre Code-Plattformen einrichten. Enter auf einer Plattform "
                      "öffnet die Einrichtung.")
        text.setWordWrap(True)
        self.list = QListWidget()
        self.list.itemActivated.connect(lambda item: self.setup_current())
        self.setup_button = QPushButton("Plattform &einrichten …")
        self.setup_button.clicked.connect(self.setup_current)
        self.chosen: list = []
        self.layout_.addWidget(text)
        self.layout_.addWidget(label_for(self.list, "&Plattformen:"))
        self.layout_.addWidget(self.list, 1)
        self.layout_.addLayout(_button_row(self.setup_button))

    def choice_page(self) -> PlatformChoicePage:
        return next(p for p in self.wizard.pages if isinstance(p, PlatformChoicePage))

    def needed(self) -> bool:
        return bool(self.choice_page().chosen())

    def accounts_of(self, account_type) -> list:
        return [a for a in self.services.accounts.all()
                if a.kind == "platform" and a.adapter == account_type.adapter]

    def missing(self) -> int:
        return sum(1 for t in self.chosen if not self.accounts_of(t))

    def next_text(self) -> str:
        missing = self.missing()
        return f"&Weiter ({missing} nicht eingerichtet)" if missing else "&Weiter"

    def on_show(self) -> None:
        self.chosen = self.choice_page().chosen()
        row = max(0, self.list.currentRow())
        self.list.clear()
        done = []
        for account_type in self.chosen:
            accounts = self.accounts_of(account_type)
            if accounts:
                names = ", ".join(f"{a.display_name}, {a.username}" for a in accounts)
                self.list.addItem(f"{account_type.display_name}, eingerichtet: {names}")
                done.append(f"{account_type.display_name}-Konto: {names}.")
            else:
                self.list.addItem(f"{account_type.display_name}, noch nicht eingerichtet")
        self.list.setCurrentRow(min(row, self.list.count() - 1))
        settings = self.services.settings.load()
        if done and settings.git_name and settings.git_email:
            done.append(f"Git-Identität: {settings.git_name}, {settings.git_email}.")
        self.done_text = " ".join(done)

    def setup_current(self) -> None:
        from cockpit.ui.accounts_dialog import AccountEditDialog
        row = self.list.currentRow()
        if not 0 <= row < len(self.chosen):
            return
        dialog = AccountEditDialog(self.services, self.chosen[row], None, self.wizard,
                                   with_identity=True)
        if dialog.exec():
            self.on_show()
            self.wizard.update_next_text()
            announce(f"Konto {dialog.saved.display_name} angelegt.")
        self.list.setFocus()

    def first_focus(self):
        return self.list


class FolderPage(Page):
    title = "Projekte-Hauptordner"
    intro = "In diesem Ordner legt das Cockpit neue Projekte an und findet vorhandene."
    later = "Menü Einstellungen, Grundeinstellungen"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        field = next(f for f in setting_fields() if f.key == "projects_root")
        self.form = SettingsForm([field], {"projects_root":
                                           self.services.settings.load().projects_root})
        self.layout_.addWidget(self.form)
        self.layout_.addStretch(1)

    def first_focus(self):
        return self.form.first_focus()

    def accept_page(self) -> bool:
        try:
            root = self.form.values()["projects_root"]
        except FormError as exc:
            show_error(self.wizard, self.title, exc.message)
            self.form.focus_field(exc.key)
            return False
        self.services.settings.update(projects_root=root)
        self.services.projects.scan(Path(root))
        number = len(self.services.projects.all())
        self.done_text = f"Projekte-Hauptordner: {root}, {count(number, 'Projekt', 'Projekte')} gefunden."
        return True


AI_INTRO = ("Um Ihren Alltag zu vereinfachen, gibt es mehrere KI-Features. Dafür brauchen Sie eine "
            "Text-KI und eine Sprach-KI. Beide können Sie im Folgenden einrichten.")
AI_LINES = [
    "Sie können eine lokale KI auf Ihrem Rechner verwenden. Passende Modelle schlägt Ihnen das "
    "Cockpit vor.",
    "Sie können aber auch eine externe KI oder eine Firmen-KI einbinden.",
    "Ohne KI funktioniert das Programm auch. Die Features, die das Programm auf ein anderes Level "
    "bringen, sind dann aber nicht verfügbar.",
    "Die KI können Sie auch später noch einrichten und anpassen.",
    "Mit Tab kommen Sie zu KI einrichten.",
]


class AIPage(Page):
    """Seite KI (Konzept 8.7, Teilschritt 8b): Rechner und Ollama prüfen, KI einrichten."""
    title = "KI"
    intro = "Für die KI-Features brauchen Sie eine Text-KI und eine Sprach-KI. Sie sind freiwillig."
    later = "Menü KI, KI-Verwaltung"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.text = _lines("KI", [])
        self.setup_button = QPushButton("KI &einrichten …")
        self.setup_button.clicked.connect(self.setup_ai)
        self.task = None
        self.layout_.addWidget(self.text)
        self.layout_.addLayout(_button_row(self.setup_button))

    def on_show(self) -> None:
        tool = self.services.ai_tools.default()
        self.done_text = f"Text-KI: {self.services.ai_tools.label(tool, False)}." if tool else ""
        self.show_lines([])
        if self.task is None:
            self.check()

    def show_lines(self, extra: list[str]) -> None:
        tool = self.services.ai_tools.default()
        lines = [AI_INTRO]
        lines.append(f"Eingerichtet: {self.services.ai_tools.label(tool, False)}." if tool
                     else "Es ist noch keine KI eingerichtet.")
        lines += extra or ["Rechner und Ollama werden geprüft …"]
        lines += AI_LINES
        row = max(0, self.text.currentRow())
        self.text.clear()
        self.text.addItems(lines)
        self.text.setCurrentRow(min(row, self.text.count() - 1))

    def check(self) -> None:
        from cockpit.ai import ollama
        from cockpit.core import hardware
        from cockpit.ui.ai_dialogs import (manual_ram, recommendation_line,
                                           speech_recommendation_line)
        manual = manual_ram(self.services)

        def work(task):
            machine = hardware.detect(manual)
            return machine.lines()[:1] + [recommendation_line(machine.ram_gb),
                                          speech_recommendation_line(machine.ram_gb),
                                          ollama.state()]

        self.task = Task(work, self)
        self.task.result.connect(self.show_lines)
        self.task.error.connect(lambda message, details: self.show_lines([message]))
        self.task.finished.connect(self._checked)
        self.task.start()

    def _checked(self) -> None:
        task, self.task = self.task, None
        if task is not None:
            task.wait()                      # Thread ganz beendet, sonst bricht Qt ab
            task.deleteLater()

    def setup_ai(self) -> None:
        from cockpit.ui.ai_dialogs import AIManagerDialog
        AIManagerDialog(self.services, self.wizard, for_setup=True).exec()
        self.on_show()
        self.setup_button.setFocus()

    def first_focus(self):
        return self.text


TIPS = [
    "Für einen perfekten Start hier noch ein paar Tipps.",
    "Bei eingeschalteter Text-KI steht Ihnen der Hilfe-Assistent zur Verfügung. Er beantwortet "
    "Ihre Fragen zum Programm.",
    "Zum Beispiel: Wo finde ich welches Menü?",
    "Oder: Wie lautet noch mal der Git-Befehl für einen neuen Branch?",
    "Sie öffnen den Hilfe-Assistenten mit Umschalt+F1 oder im Menü Hilfe, KI-Hilfe.",
    "Brauchen Sie noch eine kleine Auffrischung für einen gelungenen Umgang mit "
    "Code-Plattformen? Dann schauen Sie sich das Video Git für Anfänger an. Mit Tab kommen Sie "
    "zum Knopf.",
    VIDEO_CREDIT,
]


class SummaryPage(Page):
    title = "Zusammenfassung"
    intro = "Die Einrichtung ist fertig. Die Liste zeigt, was eingerichtet wurde."
    can_skip = False
    in_summary = False

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.list = _lines("Zusammenfassung", [])
        self.tips = _lines("Tipps für den Start", TIPS)
        self.video_button = QPushButton("Video Git für &Anfänger anschauen")
        self.video_button.clicked.connect(self.show_video)
        self.layout_.addWidget(self.list, 2)
        self.layout_.addWidget(label_for(self.tips, "&Tipps für den Start:"))
        self.layout_.addWidget(self.tips, 2)
        self.layout_.addLayout(_button_row(self.video_button))

    def next_text(self) -> str:
        return "&Fertig"

    def on_show(self) -> None:
        lines = ["Perfekt, Sie haben folgende Tools eingerichtet:"]
        for page in self.wizard.pages:
            if not page.in_summary:
                continue
            if page.done_text and page.needed():
                lines.append(f"Eingerichtet: {page.done_text}")
            else:
                lines.append(f"Übersprungen: {page.title}. Nachholen: {page.later}.")
        lines.append("Mit Fertig öffnen Sie das Cockpit.")
        lines.append("Mit Tab gelangen Sie zu den Tipps, zum Video und zu Fertig.")
        self.list.clear()
        self.list.addItems(lines)
        self.list.setCurrentRow(0)

    def show_video(self) -> None:
        videos.open_video(self.wizard, videos.GIT_BASICS, "Git für Anfänger")
        self.video_button.setFocus()

    def first_focus(self):
        return self.list


class SetupWizard(FocusDialog):
    def __init__(self, services: Services, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.setWindowTitle(f"{APP_NAME} einrichten")
        self.pages: list[Page] = [WelcomePage(self), VaultPage(self), GitPage(self),
                                  PlatformChoicePage(self), PlatformSetupPage(self),
                                  FolderPage(self), AIPage(self), SummaryPage(self)]
        self.stack = QStackedWidget()
        for page in self.pages:
            self.stack.addWidget(page)
        self.heading = QLabel()

        # Wunsch des Nutzers: erst die Knöpfe nach vorn, dann Zurück
        self.next_button = QPushButton("&Weiter")
        self.skip_button = QPushButton("Ü&berspringen")
        self.back_button = QPushButton("&Zurück")
        self.cancel_button = QPushButton("Abbrechen")
        self.next_button.clicked.connect(self.next)
        self.skip_button.clicked.connect(self.skip)
        self.back_button.clicked.connect(self.back)
        self.cancel_button.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        for button in (self.next_button, self.skip_button, self.back_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.heading)
        layout.addWidget(self.stack, 1)
        layout.addLayout(buttons)
        self.resize(760, 560)
        self.index = 0
        self.show_page(0, speak=False)

    @property
    def page(self) -> Page:
        return self.pages[self.index]

    def visible_pages(self) -> list[Page]:
        return [p for p in self.pages if p.needed()]

    def update_next_text(self) -> None:
        self.next_button.setText(self.page.next_text())

    def show_page(self, index: int, speak: bool = True) -> None:
        self.index = index
        page = self.page
        page.on_show()
        self.stack.setCurrentWidget(page)
        visible = self.visible_pages()
        step = f"Schritt {visible.index(page) + 1} von {len(visible)}: {page.title}"
        self.heading.setText(step)
        self.setWindowTitle(f"{APP_NAME} einrichten, {step}")
        self.back_button.setVisible(index > 0)
        self.skip_button.setVisible(page.can_skip)
        self.update_next_text()
        self.next_button.setDefault(True)
        self.initial_focus_widget = page.first_focus() or self.next_button
        self.initial_focus_widget.setFocus()
        if speak:
            announce(f"{step}. {page.intro}")
            QTimer.singleShot(0, lambda: announce_focus(self.initial_focus_widget))

    def _step(self, direction: int) -> int | None:
        """Nächste nötige Seite in dieser Richtung."""
        index = self.index + direction
        while 0 <= index < len(self.pages):
            if self.pages[index].needed():
                return index
            index += direction
        return None

    def next(self) -> None:
        if not self.page.accept_page():
            return
        if self.index == len(self.pages) - 1:
            self.services.settings.update(setup_done=True)
            self.accept()
            return
        self.show_page(self._step(1))

    def skip(self) -> None:
        self.page.done_text = ""
        if isinstance(self.page, PlatformChoicePage):
            for row in range(self.page.list.count()):      # übersprungen: keine Plattform
                self.page.list.item(row).setCheckState(Qt.CheckState.Unchecked)
        self.show_page(self._step(1))

    def back(self) -> None:
        index = self._step(-1)
        if index is not None:
            self.show_page(index)

    def done(self, code: int) -> None:
        from cockpit.ui.accounts_dialog import wait_for
        for page in self.pages:
            wait_for(getattr(page, "task", None))      # laufende Prüfungen nicht zerstören
        super().done(code)

    def reject(self) -> None:
        if self.services.settings.load().setup_done:
            super().reject()                        # später erneut gestartet: einfach schließen
            return
        if confirm(self, "Einrichtung abbrechen",
                   "Einrichtung abbrechen? Das Cockpit wird beendet. Beim nächsten Start beginnt "
                   "die Einrichtung von vorn.", yes="Abbrechen und beenden", no="Weiter einrichten"):
            super().reject()
