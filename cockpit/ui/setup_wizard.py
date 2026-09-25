"""Einrichtungsassistent beim ersten Start (Konzept 8.7, ohne Profile).

Eigene Umsetzung statt QWizard, damit Fokus und Ansagen verlässlich sind. Jede Seite ist ein
einfaches Formular. Unten: "Zurück", "Überspringen" (wo erlaubt), "Weiter" bzw. "Fertig" und
"Abbrechen". Beim Seitenwechsel sagt das Cockpit "Schritt 2 von 6: Git" und eine kurze Erklärung
an, der Fokus steht im ersten Feld der Seite.

Seiten: Willkommen, Git, Tresor (Pflicht), GitHub-Konto (seit Phase 4), Projekte-Hauptordner,
Git-Identität und die Zusammenfassung. Spätere Phasen fügen Seiten hinzu (Plattform-Konto, KI, Automation, E-Mail,
Features).
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)

from cockpit import APP_NAME
from cockpit.core import git, paths
from cockpit.core.services import Services
from cockpit.core.settings import setting_fields
from cockpit.core.text import count
from cockpit.core.vault_service import KINDS
from cockpit.ui import vault_ui
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, announce_focus, confirm, label_for, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.form_builder import FormError, SettingsForm
from cockpit.ui.tasks import Task
from cockpit.ui.text_dialog import TextDialog


def _lines(name: str, lines: list[str]) -> QListWidget:
    """Erklärung als Liste: eine Zeile pro Satz, gut lesbar auf der Braillezeile."""
    widget = QListWidget()
    name_widget(widget, name)
    widget.addItems(lines)
    widget.setCurrentRow(0)
    return widget


class Page(QWidget):
    title = ""
    intro = ""                       # kurze Ansage beim Öffnen der Seite
    can_skip = True
    done_text = ""                   # für die Zusammenfassung, leer: übersprungen
    later = ""                       # wo man es nachholen kann

    def __init__(self, wizard: "SetupWizard") -> None:
        super().__init__()
        self.wizard = wizard
        self.services = wizard.services
        self.layout_ = QVBoxLayout(self)

    def first_focus(self) -> QWidget | None:
        return None

    def on_show(self) -> None:
        """Beim Öffnen der Seite, zum Beispiel um den Zustand neu zu prüfen."""

    def accept_page(self) -> bool:
        """Bei "Weiter": prüfen und speichern. False bleibt auf der Seite."""
        return True


class WelcomePage(Page):
    title = "Willkommen"
    intro = "Der Assistent richtet das Cockpit in wenigen Schritten ein."
    can_skip = False

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.text = _lines("Willkommen", [
            f"Willkommen bei {APP_NAME}.",
            "Das Cockpit verwaltet Ihre Code-Projekte ohne Terminal.",
            "Dieser Assistent richtet das Wichtigste ein.",
            "Nur die Wahl des Tresors ist Pflicht. Alles andere können Sie überspringen.",
            "Alles lässt sich später über die Menüs ändern.",
            "Weiter mit Alt+W, zurück mit Alt+Z.",
        ])
        self.layout_.addWidget(self.text)

    def first_focus(self):
        return self.text


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
        row = QHBoxLayout()
        row.addWidget(self.guide_button)
        row.addWidget(self.check_button)
        row.addStretch(1)
        self.layout_.addWidget(self.state)
        self.layout_.addLayout(row)

    def on_show(self) -> None:
        found = git.find_git()
        self.state.clear()
        if found:
            self.intro = "Git ist installiert."
            self.done_text = "Git ist installiert."
            self.state.addItems(["Git ist installiert.", f"Ort: {found}"])
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


class VaultPage(Page):
    title = "Tresor"
    intro = "Wählen Sie, wo Ihre Zugangsdaten gespeichert werden. Dieser Schritt ist Pflicht."
    can_skip = False
    later = "Menü Konten, Tresor-Einstellungen"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.text = _lines("Erklärung", [
            "Zugangsdaten wie Tokens liegen immer verschlüsselt im Tresor.",
            "Windows-Anmeldeinformationsverwaltung: geschützt durch Ihre Windows-Anmeldung. "
            "Kein zusätzliches Passwort. Empfohlen für die private Nutzung.",
            "Verschlüsselte Tresordatei: geschützt durch ein eigenes Master-Passwort. "
            "Sinnvoll, wenn mehrere Personen den Rechner nutzen.",
            "Das Master-Passwort wird beim Start abgefragt. Geht es verloren, müssen Sie alle "
            "Zugangsdaten neu eingeben.",
            "Gesperrt heißt: Die Zugangsdaten sind nicht lesbar. Alles ohne Zugangsdaten "
            "funktioniert weiter. Braucht eine Aktion einen Zugang, fragt das Cockpit nach dem "
            "Master-Passwort.",
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
        self.done_text = f"Tresor: {self.services.vault.display_name}."
        return True


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


class PlatformPage(Page):
    title = "GitHub-Konto"
    intro = "Mit einem GitHub-Konto kann das Cockpit Ihren Code hochladen."
    later = "Menü Konten, Kontenverwaltung"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.text = _lines("Erklärung", [
            "Das Cockpit braucht Zugang zu Ihrem GitHub-Konto, um Code hochzuladen und "
            "Repositories anzulegen.",
            "Im nächsten Fenster wählen Sie den Weg: Im Browser anmelden, empfohlen, oder Mit "
            "Token anmelden.",
            "Ihr Passwort gibt das Cockpit nie weiter. Den Benutzernamen holt es selbst.",
            "Der Zugang liegt verschlüsselt im Tresor.",
            "Mit Tab kommen Sie zu GitHub-Konto einrichten.",
        ])
        self.setup_button = QPushButton("GitHub-Konto &einrichten …")
        self.setup_button.clicked.connect(self.setup_account)
        row = QHBoxLayout()
        row.addWidget(self.setup_button)
        row.addStretch(1)
        self.layout_.addWidget(self.text)
        self.layout_.addLayout(row)

    def github_accounts(self) -> list:
        return [a for a in self.services.accounts.all() if a.adapter == "github"]

    def on_show(self) -> None:
        accounts = self.github_accounts()
        self.done_text = (f"GitHub-Konto: {accounts[0].display_name}, {accounts[0].username}."
                          if accounts else "")

    def setup_account(self) -> None:
        from cockpit.core.accounts import find_type
        from cockpit.ui.accounts_dialog import AccountEditDialog
        account_type = find_type("platform", "github")
        dialog = AccountEditDialog(self.services, account_type, None, self.wizard)
        if dialog.exec():
            self.on_show()
            announce(f"Konto {dialog.saved.display_name} angelegt.")
            self.wizard.next_button.setFocus()
        else:
            self.setup_button.setFocus()

    def first_focus(self):
        return self.text

    def accept_page(self) -> bool:
        if not self.github_accounts():
            show_error(self.wizard, self.title, "Es ist noch kein GitHub-Konto eingerichtet. "
                       "Wählen Sie GitHub-Konto einrichten oder überspringen Sie den Schritt.")
            self.setup_button.setFocus()
            return False
        return True


class IdentityPage(Page):
    title = "Git-Identität"
    intro = ("Name und E-Mail-Adresse stehen in jedem Commit. Bei öffentlichen Repositories "
             "kann sie jeder sehen.")
    later = "Menü Einstellungen, Grundeinstellungen"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        fields = [f for f in setting_fields() if f.key in ("git_name", "git_email")]
        settings = self.services.settings.load()
        self.form = SettingsForm(fields, {"git_name": settings.git_name,
                                          "git_email": settings.git_email})
        hint = QLabel("Tipp: GitHub bietet eine anonyme noreply-Adresse. Dann erscheint Ihre "
                      "private Adresse nie öffentlich.")
        hint.setWordWrap(True)
        self.noreply_button = QPushButton("&Anonyme GitHub-Adresse übernehmen")
        self.noreply_button.clicked.connect(self.take_noreply)
        self.task = None
        row = QHBoxLayout()
        row.addWidget(self.noreply_button)
        row.addStretch(1)
        self.layout_.addWidget(self.form)
        self.layout_.addLayout(row)
        self.layout_.addWidget(hint)
        self.layout_.addStretch(1)

    def github_account(self):
        return next((a for a in self.services.accounts.all() if a.adapter == "github"), None)

    def on_show(self) -> None:
        self.noreply_button.setVisible(self.github_account() is not None)

    def take_noreply(self) -> None:
        """Name und anonyme Adresse vom GitHub-Konto übernehmen (Konzept 9.8)."""
        account = self.github_account()
        if account is None or not vault_ui.ensure_unlocked(self.services, self.wizard):
            return
        accounts = self.services.accounts

        def work(task):
            adapter = accounts.adapter_for(account)
            return adapter.noreply_email(), adapter.username

        self.noreply_button.setEnabled(False)
        self.task = Task(work, self)
        self.task.result.connect(self.noreply_received)
        self.task.error.connect(self.noreply_failed)
        self.task.finished.connect(lambda: self.noreply_button.setEnabled(True))
        self.task.start()

    def noreply_received(self, result) -> None:
        email, login = result
        if not self.form.fields["git_name"].get():
            self.form.fields["git_name"].set(login)
        self.form.fields["git_email"].set(email)
        announce(f"Adresse übernommen: {email}")
        self.form.focus_field("git_email")

    def noreply_failed(self, message: str, details: str) -> None:
        show_error(self.wizard, self.title, message, details)
        self.noreply_button.setFocus()

    def first_focus(self):
        return self.form.first_focus()

    def accept_page(self) -> bool:
        try:
            values = self.form.values()
        except FormError as exc:
            show_error(self.wizard, self.title, exc.message)
            self.form.focus_field(exc.key)
            return False
        if not values["git_name"] or not values["git_email"]:
            show_error(self.wizard, self.title, "Bitte Name und E-Mail-Adresse eingeben, "
                       "oder den Schritt überspringen.")
            self.form.focus_field("git_name" if not values["git_name"] else "git_email")
            return False
        self.services.settings.update(**values)
        self.done_text = f"Git-Identität: {values['git_name']}, {values['git_email']}."
        return True


class SummaryPage(Page):
    title = "Zusammenfassung"
    intro = "Die Einrichtung ist fertig. Die Liste zeigt, was eingerichtet wurde."
    can_skip = False

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.list = _lines("Zusammenfassung", [])
        self.layout_.addWidget(self.list)

    def on_show(self) -> None:
        lines = []
        for page in self.wizard.pages:
            if page in (self, self.wizard.pages[0]):
                continue
            if page.done_text:
                lines.append(f"Eingerichtet: {page.done_text}")
            else:
                lines.append(f"Übersprungen: {page.title}. Nachholen: {page.later}.")
        lines.append("Mit Fertig öffnen Sie das Cockpit.")
        self.list.clear()
        self.list.addItems(lines)
        self.list.setCurrentRow(0)

    def first_focus(self):
        return self.list


class SetupWizard(FocusDialog):
    def __init__(self, services: Services, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.setWindowTitle(f"{APP_NAME} einrichten")
        self.pages: list[Page] = [WelcomePage(self), GitPage(self), VaultPage(self),
                                  PlatformPage(self), FolderPage(self), IdentityPage(self),
                                  SummaryPage(self)]
        self.stack = QStackedWidget()
        for page in self.pages:
            self.stack.addWidget(page)
        self.heading = QLabel()

        self.back_button = QPushButton("&Zurück")
        self.skip_button = QPushButton("Ü&berspringen")
        self.next_button = QPushButton("&Weiter")
        self.cancel_button = QPushButton("Abbrechen")
        self.back_button.clicked.connect(self.back)
        self.skip_button.clicked.connect(self.skip)
        self.next_button.clicked.connect(self.next)
        self.cancel_button.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(self.back_button)
        buttons.addStretch(1)
        for button in (self.skip_button, self.next_button, self.cancel_button):
            buttons.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.heading)
        layout.addWidget(self.stack, 1)
        layout.addLayout(buttons)
        self.resize(760, 520)
        self.index = 0
        self.show_page(0, speak=False)

    @property
    def page(self) -> Page:
        return self.pages[self.index]

    def show_page(self, index: int, speak: bool = True) -> None:
        self.index = index
        page = self.page
        page.on_show()
        self.stack.setCurrentWidget(page)
        step = f"Schritt {index + 1} von {len(self.pages)}: {page.title}"
        self.heading.setText(step)
        self.setWindowTitle(f"{APP_NAME} einrichten, {step}")
        last = index == len(self.pages) - 1
        self.back_button.setEnabled(index > 0)
        self.skip_button.setVisible(page.can_skip)
        self.next_button.setText("&Fertig" if last else "&Weiter")
        self.next_button.setDefault(True)
        self.initial_focus_widget = page.first_focus() or self.next_button
        self.initial_focus_widget.setFocus()
        if speak:
            announce(f"{step}. {page.intro}")
            QTimer.singleShot(0, lambda: announce_focus(self.initial_focus_widget))

    def next(self) -> None:
        if not self.page.accept_page():
            return
        if self.index == len(self.pages) - 1:
            self.services.settings.update(setup_done=True)
            self.accept()
            return
        self.show_page(self.index + 1)

    def skip(self) -> None:
        self.page.done_text = ""
        self.show_page(self.index + 1)

    def back(self) -> None:
        if self.index > 0:
            self.show_page(self.index - 1)

    def reject(self) -> None:
        if self.services.settings.load().setup_done:
            super().reject()                        # später erneut gestartet: einfach schließen
            return
        if confirm(self, "Einrichtung abbrechen",
                   "Einrichtung abbrechen? Das Cockpit wird beendet. Beim nächsten Start beginnt "
                   "die Einrichtung von vorn.", yes="Abbrechen und beenden", no="Weiter einrichten"):
            super().reject()
