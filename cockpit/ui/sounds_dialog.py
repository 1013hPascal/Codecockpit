"""Fenster "Signaltöne" im Menü Einstellungen (Wunsch des Nutzers vom 24.10.2026).

Oben "Alle Signaltöne aus". Darunter je eine Auswahl für "Programm arbeitet", "KI arbeitet" und
"Erfolg". Beim Wechsel in einer Auswahl erklingt der Ton gleich zum Anhören, auch wenn die
Signaltöne aus sind. Jede Art hat eigene Töne (sounds.CHOICES), so klingen sie nie gleich.
Gespeichert wird erst mit "Speichern". Escape und "Abbrechen" ändern nichts.
"""
from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QPushButton, QVBoxLayout, QWidget

from cockpit.ui import sounds
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, label_for
from cockpit.ui.repo_dialogs import button_row

LABELS = {sounds.TICK: "&Programm arbeitet:", sounds.AI_TICK: "&KI arbeitet:",
          sounds.DONE: "&Erfolg:"}
SETTING = {sounds.TICK: "sound_work", sounds.AI_TICK: "sound_ai", sounds.DONE: "sound_done"}


class SoundsDialog(FocusDialog):
    def __init__(self, services, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.setWindowTitle("Signaltöne")
        settings = services.settings.load()
        self.off = QCheckBox("Alle Signaltöne &aus")
        self.off.setChecked(settings.sounds_off)
        layout = QVBoxLayout(self)
        layout.addWidget(self.off)
        self.boxes: dict[str, QComboBox] = {}
        for kind, text in LABELS.items():
            box = QComboBox()
            options = sounds.CHOICES[kind]
            box.addItems([c.name for c in options])
            current = getattr(settings, SETTING[kind]) or sounds.DEFAULTS[kind]
            ids = [c.id for c in options]
            box.setCurrentIndex(ids.index(current) if current in ids else 0)
            # Erst nach dem Setzen verbinden: Beim Öffnen soll noch nichts erklingen
            box.currentIndexChanged.connect(lambda index, k=kind: self.listen(k, index))
            self.boxes[kind] = box
            layout.addWidget(label_for(box, text))
            layout.addWidget(box)
        save = QPushButton("&Speichern")
        save.setDefault(True)
        save.clicked.connect(self.save)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout.addStretch(1)
        layout.addLayout(button_row(save, None, cancel))
        self.resize(460, 320)
        self.initial_focus_widget = self.off

    def chosen(self, kind: str) -> str:
        return sounds.CHOICES[kind][self.boxes[kind].currentIndex()].id

    def listen(self, kind: str, index: int) -> None:
        if 0 <= index < len(sounds.CHOICES[kind]):
            sounds.preview(sounds.CHOICES[kind][index].id)

    def save(self) -> None:
        settings = self.services.settings.update(
            sounds_off=self.off.isChecked(),
            **{SETTING[kind]: self.chosen(kind) for kind in LABELS})
        sounds.configure_from(settings)
        announce("Signaltöne aus." if settings.sounds_off else "Signaltöne gespeichert.")
        self.accept()
