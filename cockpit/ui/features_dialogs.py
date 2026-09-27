"""Feature-Verwaltung (Konzept 8.4 und 8.5, Phase 7).

GlobalFeaturesDialog (Menü Features): alle Features als Liste mit Kontrollkästchen, zum Beispiel
"Branches und Pull Requests, eingeschaltet, in 2 Projekten aktiv". Mit Tab die Beschreibung des
markierten Features und "Für neue Projekte einschalten". Knöpfe: "Einführung …", "Einstellungen …"
(nur, wenn das Feature welche hat), "Speichern", "Abbrechen".

ProjectFeaturesDialog (Projektzeile, "Features dieses Projekts …"): dieselbe Bedienung für ein
Projekt. Global ausgeschaltete Features erscheinen nicht. Beim Speichern nennt die Rückfrage
Abhängigkeiten und dass die Auswahl in cockpit.toml steht.

Die Leertaste schaltet um, Enter in den Listen tut nichts. Die Einführung eines Features erscheint
beim allerersten Einschalten (ENTSCHEIDUNGEN.md).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout, QWidget)

from cockpit.core.errors import CockpitError
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.text import count, join_words
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, label_for, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import _is_enter, button_row

if TYPE_CHECKING:
    from cockpit.core.projects import Project
    from cockpit.core.services import Services

NO_INTRODUCTION = "Für dieses Feature gibt es keine Einführung."


def show_introduction(services: "Services", manifest: FeatureManifest,
                      parent: QWidget | None = None) -> None:
    """Einführung als Liste, eine Zeile pro Satz (wie die Anleitungen im Menü Hilfe)."""
    from cockpit.core.text import one_sentence_per_line
    from cockpit.ui.text_dialog import TextDialog
    text = one_sentence_per_line(manifest.introduction_text()) or NO_INTRODUCTION
    TextDialog(f"Einführung: {manifest.name}", text, f"Einführung {manifest.name}",
               parent).exec()
    services.features.mark_intro_seen(manifest.id)


def show_new_introductions(services: "Services", feature_ids, parent=None) -> None:
    """Nach dem Einschalten: Einführungen, die noch nie erschienen sind."""
    for feature_id in sorted(feature_ids):
        if feature_id in services.registry and not services.features.intro_seen(feature_id):
            show_introduction(services, services.registry.get(feature_id), parent)


class _FeatureListDialog(FocusDialog):
    """Gemeinsamer Aufbau: Liste mit Kontrollkästchen, Beschreibung, Knöpfe."""

    def __init__(self, services: "Services", manifests: list[FeatureManifest],
                 checked: set[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.manifests = sorted(manifests, key=lambda m: m.name.lower())
        self.original = {m.id for m in self.manifests if m.id in checked}
        self.list = QListWidget()
        name_widget(self.list, "Features")
        self.list.installEventFilter(self)
        for manifest in self.manifests:
            item = QListWidgetItem()
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if manifest.id in checked
                               else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        if not self.manifests:
            self.list.addItem("Keine Features.")
        self.list.setCurrentRow(0)
        self.info = QListWidget()
        name_widget(self.info, "Beschreibung")
        self.info.setWordWrap(True)
        self.info.installEventFilter(self)
        self.intro_button = QPushButton("&Einführung …")
        self.intro_button.clicked.connect(self.show_intro)
        self.save_button = QPushButton("&Speichern")
        self.save_button.clicked.connect(self.save)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        self.cancel_button = cancel
        self.list.itemChanged.connect(lambda _item: self.refresh_lines())
        self.list.currentRowChanged.connect(lambda _row: self.refresh_info())
        self.initial_focus_widget = self.list

    def eventFilter(self, watched, event) -> bool:
        if watched in (self.list, self.info) and _is_enter(event):
            return True
        return super().eventFilter(watched, event)

    def checked(self) -> set[str]:
        return {m.id for row, m in enumerate(self.manifests)
                if self.list.item(row).checkState() == Qt.CheckState.Checked}

    def current(self) -> FeatureManifest | None:
        row = self.list.currentRow()
        return self.manifests[row] if 0 <= row < len(self.manifests) else None

    def refresh_lines(self) -> None:
        self.list.blockSignals(True)
        checked = self.checked()
        for row, manifest in enumerate(self.manifests):
            self.list.item(row).setText(self.line(manifest, manifest.id in checked))
        self.list.blockSignals(False)
        self.refresh_info()

    def refresh_info(self) -> None:
        manifest = self.current()
        self.info.clear()
        if manifest is None:
            return
        needs = self.services.features.needs(manifest.id)
        lines = [manifest.description.strip(),
                 f"Braucht: {join_words(needs)}." if needs else "Braucht nichts weiter."]
        lines += self.extra_info(manifest)
        self.info.addItems([line for line in lines if line])
        self.info.setCurrentRow(0)

    def show_intro(self) -> None:
        manifest = self.current()
        if manifest is not None:
            show_introduction(self.services, manifest, self)
            self.list.setFocus()

    # In den Unterklassen
    def line(self, manifest: FeatureManifest, checked: bool) -> str:
        raise NotImplementedError

    def extra_info(self, manifest: FeatureManifest) -> list[str]:
        return []

    def save(self) -> None:
        raise NotImplementedError


class GlobalFeaturesDialog(_FeatureListDialog):
    """Feature-Verwaltung für alle Projekte. changed nach dem Speichern."""

    def __init__(self, services: "Services", parent: QWidget | None = None) -> None:
        features = services.features
        manifests = services.registry.all()
        super().__init__(services, manifests,
                         {m.id for m in manifests if features.globally_enabled(m.id)}, parent)
        self.changed = False
        self.defaults = features.default_features()
        self.counts = {m.id: features.project_count(m.id) for m in manifests}
        self.setWindowTitle(f"Feature-Verwaltung: {count(len(manifests), 'Feature', 'Features')}")
        self.default_box = QCheckBox("Für &neue Projekte einschalten")
        self.default_box.toggled.connect(self.toggle_default)
        self.settings_button = QPushButton("E&instellungen …")
        self.settings_button.clicked.connect(self.edit_settings)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 2)
        layout.addWidget(label_for(self.info, "Beschreibung:"))
        layout.addWidget(self.info, 1)
        layout.addWidget(self.default_box)
        layout.addLayout(button_row(self.intro_button, self.settings_button, None,
                                    self.save_button, self.cancel_button))
        self.resize(700, 480)
        # Tab in der Reihenfolge auf dem Bildschirm, nicht in der Reihenfolge der Erstellung
        order = [self.list, self.info, self.default_box, self.intro_button,
                 self.settings_button, self.save_button, self.cancel_button]
        for first, second in zip(order, order[1:]):
            self.setTabOrder(first, second)
        self.refresh_lines()

    def line(self, manifest: FeatureManifest, checked: bool) -> str:
        parts = [manifest.name, "eingeschaltet" if checked else "ausgeschaltet"]
        active = self.counts.get(manifest.id, 0)
        if checked and active:
            parts.append(f"in {count(active, 'Projekt', 'Projekten')} aktiv")
        if checked:
            state = self.services.features.availability_without_switch(manifest.id)
            if not state.available:
                parts.append(f"nicht verfügbar: {state.reason}")
        return ", ".join(parts)

    def extra_info(self, manifest: FeatureManifest) -> list[str]:
        new = "eingeschaltet" if manifest.id in self.defaults else "aus"
        return [f"Für neue Projekte: {new}.",
                f"In {count(self.counts.get(manifest.id, 0), 'Projekt', 'Projekten')} "
                "eingeschaltet."]

    def refresh_info(self) -> None:
        super().refresh_info()
        manifest = self.current()
        if not hasattr(self, "default_box"):
            return
        self.default_box.blockSignals(True)
        self.default_box.setChecked(manifest is not None and manifest.id in self.defaults)
        self.default_box.blockSignals(False)
        self.settings_button.setVisible(manifest is not None and bool(manifest.settings))

    def toggle_default(self, on: bool) -> None:
        manifest = self.current()
        if manifest is None:
            return
        (self.defaults.add if on else self.defaults.discard)(manifest.id)
        self.refresh_info()

    def edit_settings(self) -> None:
        manifest = self.current()
        if manifest is not None and manifest.settings:
            FeatureSettingsDialog(self.services, manifest, self).exec()
            self.settings_button.setFocus()

    def save(self) -> None:
        features = self.services.features
        checked = self.checked()
        switched_on = checked - self.original
        for manifest in self.manifests:
            features.set_globally_enabled(manifest.id, manifest.id in checked)
        features.set_default_features(self.defaults)
        self.changed = True
        self.accept()
        announce("Feature-Verwaltung gespeichert.")
        show_new_introductions(self.services, switched_on, self.parentWidget())


class ProjectFeaturesDialog(_FeatureListDialog):
    """Features eines Projekts. changed nach dem Speichern."""

    def __init__(self, services: "Services", project: "Project",
                 parent: QWidget | None = None) -> None:
        features = services.features
        super().__init__(services, features.visible_features(),
                         features.project_features(project), parent)
        self.project = project
        self.changed = False
        follows = features.follows_default(project)
        self.setWindowTitle(f"Features von {project.name}: "
                            f"{'folgt der Vorauswahl' if follows else 'eigene Auswahl'}")
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 2)
        layout.addWidget(label_for(self.info, "Beschreibung:"))
        layout.addWidget(self.info, 1)
        layout.addLayout(button_row(self.intro_button, None, self.save_button,
                                    self.cancel_button))
        self.resize(640, 420)
        self.refresh_lines()

    def line(self, manifest: FeatureManifest, checked: bool) -> str:
        if not checked:
            return f"{manifest.name}, aus"
        state = self.services.features.availability(manifest.id, self.project)
        if not state.available:
            return f"{manifest.name}, eingeschaltet, aber nicht verfügbar: {state.reason}"
        return f"{manifest.name}, aktiv"

    def extra_info(self, manifest: FeatureManifest) -> list[str]:
        state = self.services.features.availability(manifest.id, self.project)
        return [] if state.available else [f"Zurzeit nicht verfügbar: {state.reason}"]

    def plan(self) -> tuple[set[str], list[str]]:
        """Neue Auswahl mit Abhängigkeiten und die Sätze dazu für die Rückfrage."""
        registry = self.services.registry
        chosen = self.checked()
        sentences: list[str] = []
        for feature_id in sorted(chosen - self.original):
            missing = [d for d in registry.dependencies(feature_id) if d not in chosen]
            if missing:
                names = join_words(registry.get(d).name for d in missing)
                verb = "ist" if len(missing) == 1 else "sind"
                sentences.append(f"{registry.get(feature_id).name} benötigt {names}. {names} "
                                 f"{verb} für dieses Projekt ausgeschaltet und wird mit "
                                 "eingeschaltet." if len(missing) == 1 else
                                 f"{registry.get(feature_id).name} benötigt {names}. {names} "
                                 f"{verb} für dieses Projekt ausgeschaltet und werden mit "
                                 "eingeschaltet.")
                chosen |= set(missing)
        for feature_id in sorted(self.original - chosen):
            dependents = [d for d in registry.dependents(feature_id) if d in chosen]
            if dependents:
                names = join_words(registry.get(d).name for d in dependents)
                sentences.append(f"Ohne {registry.get(feature_id).name} geht auch {names} aus.")
                chosen -= set(dependents)
        return chosen, sentences

    def save(self) -> None:
        chosen, sentences = self.plan()
        if chosen == self.original:
            announce("Nichts geändert.")
            self.reject()
            return
        text = " ".join(sentences + ["Die Auswahl steht danach in der Datei cockpit.toml im "
                                     "Ordner Code und wird mit hochgeladen. Speichern?"])
        if not confirm(self, "Features speichern", text, yes="Speichern", no="Abbrechen"):
            return
        features = self.services.features
        hidden = features.project_features(self.project) - {m.id for m in self.manifests}
        try:
            features.set_project_features(self.project, chosen | hidden)
        except CockpitError as exc:
            show_error(self, "Features speichern", exc.message, exc.details)
            return
        self.changed = True
        self.accept()
        announce(f"Features von {self.project.name} gespeichert.")
        show_new_introductions(self.services, chosen - self.original, self.parentWidget())


class FeatureSettingsDialog(FocusDialog):
    """Einstellungen eines Features als Formular (Konzept 3.2)."""

    def __init__(self, services: "Services", manifest: FeatureManifest,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from cockpit.ui.form_builder import SettingsForm
        self.services = services
        self.manifest = manifest
        self.setWindowTitle(f"Einstellungen: {manifest.name}")
        values = {f.key: services.features.setting(manifest.id, f.key) for f in manifest.settings}
        self.form = SettingsForm(list(manifest.settings), values)
        save = QPushButton("&Speichern")
        save.setDefault(True)
        save.clicked.connect(self.save)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.form)
        layout.addLayout(button_row(None, save, cancel))
        self.resize(520, 260)
        self.initial_focus_widget = self.form.first_focus()

    def save(self) -> None:
        from cockpit.ui.form_builder import FormError
        try:
            values = self.form.values()
            for key, value in values.items():
                self.services.features.set_setting(self.manifest.id, key, value)
        except FormError as exc:
            show_error(self, self.windowTitle(), exc.message)
            self.form.focus_field(exc.key)
            return
        except ValueError as exc:
            show_error(self, self.windowTitle(), str(exc))
            return
        self.accept()
        announce(f"Einstellungen für {self.manifest.name} gespeichert.")
