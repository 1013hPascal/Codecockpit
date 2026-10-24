"""Einrichtungsassistent beim ersten Start (Konzept 8.7, ohne Profile).

Eigene Umsetzung statt QWizard, damit Fokus und Ansagen verlässlich sind. Jede Seite ist ein
einfaches Formular. Unten stehen erst die Knöpfe nach vorn, dann die nach hinten (Wunsch des
Nutzers, 29.09.2026): "Weiter" bzw. "Fertig", "Überspringen" (wo erlaubt), "Zurück", dann
"Abbrechen". Beim Seitenwechsel sagt das Cockpit "Schritt 2 von 8: Zugangsdaten schützen" und eine
kurze Erklärung an, der Fokus steht im ersten Feld der Seite.

Seiten: Willkommen, Zugangsdaten schützen (Pflicht), Git, Code-Plattformen wählen, Code-Plattformen
einrichten (mit Git-Identität im Konto-Fenster), Projekte-Hauptordner, Features wählen, KI und die
Zusammenfassung. Seiten, die nicht nötig sind, lässt der Assistent aus, zum Beispiel
"Code-Plattformen einrichten", wenn keine Plattform gewählt ist.

Überarbeitet am 22.10.2026 (BEWERTUNG-EINRICHTUNG.md): Jede Seite sagt zuerst, wozu der Schritt
gut ist. Features stehen dort, wo man einrichtet, was sie brauchen.
"""
from __future__ import annotations


from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget)

from cockpit import APP_NAME
from cockpit.core.services import Services
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, announce_focus, confirm
# Aufgeteilt am 22.10.2026: Teile stehen in setup_pages.py. Die Namen bleiben hier erreichbar.
from cockpit.ui.setup_pages import (  # noqa: F401
    AI_INTRO, AI_LINES, AI_TAB, FEATURES, GIT_LINES, TIPS, VIDEO_CREDIT, AIPage, FeaturePage,
    FolderPage, GitPage, Page, PlatformChoicePage, PlatformSetupPage, SummaryPage, VaultPage,
    WelcomePage, feature_group, features_in, git, platform_types)


class SetupWizard(FocusDialog):
    def __init__(self, services: Services, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.setWindowTitle(f"{APP_NAME} einrichten")
        self.pages: list[Page] = [WelcomePage(self), VaultPage(self), GitPage(self),
                                  PlatformChoicePage(self), PlatformSetupPage(self),
                                  FolderPage(self), FeaturePage(self), AIPage(self),
                                  SummaryPage(self)]
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
