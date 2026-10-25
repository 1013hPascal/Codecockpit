"""Oberfläche des Features Erklärungen (Wunsch des Nutzers vom 25.10.2026).

- Projektliste: ganz oben die Zeile "Erklärung: Projektliste", nur auf der obersten Ebene.
- Aktionen: ganz oben "Erklärung: Aktionen". Sie erklärt die Aktionen, die gerade dastehen, auch
  die unter "Weitere …". Die Markierung startet auf der ersten Aktion, die Erklärung steht darüber.
- Menüs: erster Eintrag "Erklärung …", auch im Kontextmenü und in "Weitere".
- Fenster: zuletzt der Knopf "Erklärung …", nur bei Fenstern mit Text in texts.DIALOGS.

Die Erklärung erscheint als Liste, ein Absatz pro Zeile. Darunter stehen "Diese Erklärung nicht
mehr anzeigen", "Einstellungen für Erklärungen …" und "Schließen".

Ein Fehler hier darf nie die Bedienung stören: Jede Abfrage fängt Fehler ab und zeigt dann eben
keine Erklärung.
"""
from __future__ import annotations

import logging
import weakref
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QBoxLayout, QGridLayout, QHBoxLayout, QListWidget, QPushButton,
                               QVBoxLayout, QWidget)

from cockpit.core.actions import ActionEntry, Target, shown_entries
from cockpit.features.explanations import texts
from cockpit.features.explanations.manifest import FEATURE_ID, SHOWN
from cockpit.ui import common, menus
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, make_copyable, name_widget

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

log = logging.getLogger(__name__)

ACTION_MENUS = ("Aktionen", "Weitere")       # Kontextmenü und "Weitere …" der Aktionen


class ExplanationDialog(FocusDialog):
    def __init__(self, explainer: "Explainer", title: str, paragraphs: list[str],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from cockpit.ui import look
        from cockpit.ui.repo_dialogs import button_row
        self.explainer = explainer
        self.title = title
        self.setWindowTitle(f"Erklärung: {title}")
        self.list = QListWidget()
        name_widget(self.list, "Erklärung")
        self.list.setWordWrap(True)
        self.list.addItems([p for p in paragraphs if p] + [texts.CLOSING])
        self.list.setCurrentRow(0)
        make_copyable(self.list)
        look.mark_explanation(self.list)          # sieht aus wie Text, nur für das Auge
        self.hide_button = QPushButton(texts.HIDE_TEXT)
        self.hide_button.clicked.connect(self.hide_this)
        self.settings_button = QPushButton(texts.SETTINGS_TEXT)
        self.settings_button.clicked.connect(self.open_settings)
        self.close_button = QPushButton("&Schließen")
        self.close_button.setDefault(True)
        self.close_button.clicked.connect(self.accept)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(self.hide_button, self.settings_button, None,
                                    self.close_button))
        self.resize(640, 460)
        self.initial_focus_widget = self.list

    def hide_this(self) -> None:
        self.explainer.hide(self.title)
        self.accept()
        announce(texts.HIDDEN_SAID)

    def open_settings(self) -> None:
        self.explainer.open_settings(self)
        self.settings_button.setFocus()


class Explainer:
    """Verbindet das Feature mit Hauptfenster, Menüs und Fenstern."""

    def __init__(self, window: "MainWindow") -> None:
        self._window = weakref.ref(window)
        self.services = window.services
        menus.SHOW_HOOKS.append(self.on_menu)
        common.SHOW_HOOKS.append(self.on_dialog)

    def shutdown(self) -> None:
        for hooks, hook in ((menus.SHOW_HOOKS, self.on_menu), (common.SHOW_HOOKS, self.on_dialog)):
            if hook in hooks:
                hooks.remove(hook)

    # -- Zustand ---------------------------------------------------------------------------
    def enabled(self) -> bool:
        try:
            return (FEATURE_ID in self.services.registry
                    and self.services.features.availability(FEATURE_ID).available)
        except Exception:                          # noqa: BLE001 (zum Beispiel beim Beenden)
            return False

    def shown(self) -> set[str]:
        try:
            return set(self.services.features.setting(FEATURE_ID, SHOWN) or ())
        except Exception:                          # noqa: BLE001
            return set()

    def active(self, title: str) -> bool:
        return self.enabled() and title in self.shown()

    def hide(self, title: str) -> None:
        """Eine Erklärung ausblenden ("Diese Erklärung nicht mehr anzeigen")."""
        shown = self.shown() - {title}
        try:
            self.services.features.set_setting(
                FEATURE_ID, SHOWN, [t for t in texts.ALL_TITLES if t in shown])
        except Exception:                          # noqa: BLE001
            log.exception("Erklärung %s nicht ausgeblendet", title)
        self.changed()

    def open_settings(self, parent: QWidget) -> None:
        from cockpit.ui.features_dialogs import FeatureSettingsDialog
        manifest = self.services.registry.get(FEATURE_ID)
        if FeatureSettingsDialog(self.services, manifest, parent).exec():
            self.changed()

    def changed(self) -> None:
        window = self._window()
        if window is not None:
            window.refresh_explanations()

    # -- Zeilen in den Listen ----------------------------------------------------------------
    def project_row(self) -> str:
        return texts.ROW_TEXT if self.active(texts.PROJECT_LIST) else ""

    def action_row(self, target: Target) -> str:
        if target not in texts.TARGET_TITLES:
            return ""
        return texts.ACTIONS_ROW if self.active(texts.actions_title(target)) else ""

    # -- Anzeigen ----------------------------------------------------------------------------
    def show(self, title: str, paragraphs: list[str], parent: QWidget | None = None) -> None:
        window = self._window()
        ExplanationDialog(self, title, paragraphs, parent or window).exec()

    def show_project_list(self) -> None:
        self.show(texts.PROJECT_LIST, list(texts.PROJECT_LIST_TEXT))
        window = self._window()
        if window is not None:
            window.project_list.setFocus()

    def show_actions(self, parent: QWidget | None = None) -> None:
        window = self._window()
        if window is None:
            return
        target = window.action_context().target
        self.show(texts.actions_title(target),
                  action_paragraphs(target, window.current_entries()), parent)

    # -- Menüs -------------------------------------------------------------------------------
    def menu_explanation(self, name: str) -> tuple[str, list[str]] | None:
        """Titel und Absätze für ein Menü, None ohne Erklärung."""
        window = self._window()
        if name in ACTION_MENUS and window is not None:
            target = window.action_context().target
            if target not in texts.TARGET_TITLES:
                return None
            return (texts.actions_title(target),
                    action_paragraphs(target, window.current_entries()))
        key = "Schnellnavigation" if name.startswith("Schnellnavigation") else name
        if key not in texts.MENUS:
            return None
        return texts.menu_title(key), list(texts.MENUS[key])

    def on_menu(self, menu) -> None:
        """Vor dem Öffnen: "Erklärung …" ganz oben einfügen oder ausblenden."""
        if self._window() is None:
            return
        found = self.menu_explanation(menu.accessibleName())
        wanted = found is not None and self.active(found[0])
        action = getattr(menu, "_explanation_action", None)
        if action is None:
            if not wanted:
                return
            first = menu.actions()[0] if menu.actions() else None
            action = QAction(texts.ENTRY_TEXT, menu)
            # Der Inhalt wird erst beim Auslösen bestimmt, damit er zur Zeile passt
            action.triggered.connect(lambda checked=False, m=menu: self.show_menu(m))
            separator = QAction(menu)
            separator.setSeparator(True)
            menu.insertAction(first, action)
            menu.insertAction(first, separator)
            menu._explanation_action = action
            menu._explanation_separator = separator
        action.setVisible(wanted)
        menu._explanation_separator.setVisible(wanted)

    def show_menu(self, menu) -> None:
        found = self.menu_explanation(menu.accessibleName())
        if found is not None:
            self.show(found[0], found[1])

    # -- Fenster -----------------------------------------------------------------------------
    def on_dialog(self, dialog: QWidget) -> None:
        """Beim ersten Anzeigen: Knopf "Erklärung …" ganz unten, zuletzt in der Tab-Folge."""
        if self._window() is None:
            return
        name = next((c.__name__ for c in type(dialog).__mro__ if c.__name__ in texts.DIALOGS),
                    None)
        if name is None:
            return
        title = texts.dialog_title(name)
        if not self.active(title):
            return
        layout = dialog.layout()
        if not isinstance(layout, (QBoxLayout, QGridLayout)):
            return
        last = _last_in_tab_order(dialog)
        button = QPushButton(texts.ENTRY_TEXT, dialog)
        button.setAutoDefault(False)              # Enter bleibt beim Standardknopf des Fensters
        if last is not None:
            QWidget.setTabOrder(last, button)     # zuletzt, auch nach eigener Tab-Folge
        paragraphs = list(texts.DIALOGS[name][1])
        button.clicked.connect(lambda: (self.show(title, paragraphs, dialog), button.setFocus()))
        if isinstance(layout, QBoxLayout):
            row = QHBoxLayout()
            row.addWidget(button)
            row.addStretch(1)
            layout.addLayout(row)
        else:
            layout.addWidget(button, layout.rowCount(), 0)
        button.show()                             # das Fenster ist schon sichtbar
        dialog.explanation_button = button


def _last_in_tab_order(dialog: QWidget) -> QWidget | None:
    """Letztes Element, das Tab im Fenster erreicht."""
    from PySide6.QtCore import Qt
    last, widget, steps = None, dialog.nextInFocusChain(), 0
    while widget is not dialog and steps < 500:
        if widget.focusPolicy() & Qt.FocusPolicy.TabFocus and widget.isVisibleTo(dialog):
            last = widget
        widget, steps = widget.nextInFocusChain(), steps + 1
    return last


def action_paragraphs(target: Target, entries: list[ActionEntry]) -> list[str]:
    """Erklärung der Aktionen: Einleitung, jede Aktion mit zwei bis drei Sätzen, zuletzt die
    seltenen unter "Weitere …" und die Tasten."""
    paragraphs = [texts.TARGET_INTROS.get(target, "")]
    rare: list[ActionEntry] = []
    for entry in shown_entries(entries):
        if entry.children:
            names = ", ".join(_name(child) for child in entry.children)
            paragraphs.append(f"{_name(entry)}: {texts.MORE_TEXT} {names}.")
            rare += entry.children
            continue
        paragraphs.append(_line(entry))
    paragraphs += [_line(entry) for entry in rare]
    paragraphs += texts.ACTIONS_END
    return [p for p in paragraphs if p]


def _name(entry: ActionEntry) -> str:
    return entry.text.removesuffix(" …")


def _line(entry: ActionEntry) -> str:
    text = texts.action_text(entry.action.id)
    line = f"{_name(entry)}: {text}" if text else f"{_name(entry)}."
    if not entry.availability.available:
        line += f" Zurzeit nicht verfügbar: {entry.availability.reason}"
    return line
