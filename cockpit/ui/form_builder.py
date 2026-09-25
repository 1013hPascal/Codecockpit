"""Baut aus Einstellungsfeldern (core/features/settings_fields.py) ein barrierefreies Formular.

Jedes Feld bekommt ein sichtbares Label mit Buddy und einen kurzen Accessible Name. Kontrollkästchen
tragen ihre Beschriftung selbst. Mehrfachauswahl ist eine Liste mit Kontrollkästchen, die Leertaste
schaltet um (Konzept 8.4).
"""
from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout,
                               QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSpinBox,
                               QWidget)

from cockpit.core.features import settings_fields as sf
from cockpit.ui.common import label_for, name_widget


class FormError(ValueError):
    def __init__(self, key: str, message: str) -> None:
        super().__init__(message)
        self.key = key
        self.message = message


class _Field:
    """Ein Feld im Formular: das Steuerelement plus Lesen und Schreiben des Werts."""

    def __init__(self, spec: sf.SettingField, widget: QWidget, focus: QWidget,
                 get: Callable[[], Any], set_: Callable[[Any], None]) -> None:
        self.spec = spec
        self.widget = widget          # was ins Layout kommt
        self.focus = focus            # was den Fokus bekommt
        self.get = get
        self.set = set_


class SettingsForm(QWidget):
    def __init__(self, fields: list[sf.SettingField], values: dict[str, Any] | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout_ = QFormLayout(self)
        self.fields: dict[str, _Field] = {}
        self._order: list[QWidget] = []
        for spec in fields:
            entry = self._build(spec)
            self.fields[spec.key] = entry
            if isinstance(spec, sf.YesNo):
                self.layout_.addRow(entry.widget)
            else:
                self.layout_.addRow(label_for(entry.focus, spec.label + ":"), entry.widget)
            value = (values or {}).get(spec.key, spec.default)
            entry.set(value)
        for first, second in zip(self._order, self._order[1:]):
            QWidget.setTabOrder(first, second)

    # -- Aufbau ---------------------------------------------------------------------------
    def _build(self, spec: sf.SettingField) -> _Field:
        if isinstance(spec, sf.YesNo):
            box = QCheckBox(spec.label)
            name_widget(box, spec.label)
            self._order.append(box)
            return _Field(spec, box, box, box.isChecked, lambda v: box.setChecked(bool(v)))
        if isinstance(spec, sf.Choice):
            combo = QComboBox()
            combo.addItems(list(spec.options))
            self._order.append(combo)
            return _Field(spec, combo, combo, combo.currentText,
                          lambda v: combo.setCurrentIndex(max(0, combo.findText(str(v)))))
        if isinstance(spec, sf.Number):
            spin = QSpinBox()
            spin.setRange(spec.minimum if spec.minimum is not None else -1_000_000,
                          spec.maximum if spec.maximum is not None else 1_000_000)
            self._order.append(spin)
            return _Field(spec, spin, spin, spin.value, lambda v: spin.setValue(int(v or 0)))
        if isinstance(spec, sf.MultiChoice):
            listing = QListWidget()
            for option in spec.options:
                item = QListWidgetItem(option)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                listing.addItem(item)
            listing.setCurrentRow(0)
            self._order.append(listing)

            def get_checked() -> list[str]:
                return [listing.item(r).text() for r in range(listing.count())
                        if listing.item(r).checkState() == Qt.CheckState.Checked]

            def set_checked(values: Any) -> None:
                chosen = set(values or [])
                for r in range(listing.count()):
                    item = listing.item(r)
                    item.setCheckState(Qt.CheckState.Checked if item.text() in chosen
                                       else Qt.CheckState.Unchecked)

            return _Field(spec, listing, listing, get_checked, set_checked)
        if isinstance(spec, sf.Folder):
            edit = QLineEdit()
            button = QPushButton("&Ordner wählen …")
            name_widget(button, "Ordner wählen")
            button.clicked.connect(lambda: self._choose_folder(edit, spec.label))
            row = QWidget()
            box = QHBoxLayout(row)
            box.setContentsMargins(0, 0, 0, 0)
            box.addWidget(edit, 1)
            box.addWidget(button)
            self._order += [edit, button]
            return _Field(spec, row, edit, edit.text, lambda v: edit.setText(str(v or "")))
        if isinstance(spec, sf.SecretText):
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            if spec.keep_if_empty:
                edit.setPlaceholderText("Leer lassen: bleibt unverändert")
            self._order.append(edit)
            # Geheimnisse werden nie ins Feld geschrieben, nur neu eingegeben
            return _Field(spec, edit, edit, edit.text, lambda v: None)
        edit = QLineEdit()                              # Text, Email, TimeOfDay
        self._order.append(edit)
        return _Field(spec, edit, edit, edit.text, lambda v: edit.setText(str(v or "")))

    def _choose_folder(self, edit: QLineEdit, label: str) -> None:
        chosen = QFileDialog.getExistingDirectory(self, label, edit.text())
        if chosen:
            edit.setText(chosen.replace("/", "\\"))
        edit.setFocus()

    # -- Werte ----------------------------------------------------------------------------
    def raw_values(self) -> dict[str, Any]:
        return {key: entry.get() for key, entry in self.fields.items()}

    def values(self, skip: set[str] | frozenset[str] = frozenset()) -> dict[str, Any]:
        """Geprüfte Werte. Wirft FormError mit der Kennung des ersten fehlerhaften Felds.
        Felder in skip werden nicht geprüft (zum Beispiel ein Token aus der Anmeldung im
        Browser, der gar nicht im Feld steht)."""
        result = {}
        for key, entry in self.fields.items():
            if key in skip:
                continue
            try:
                result[key] = entry.spec.check(entry.get())
            except ValueError as exc:
                raise FormError(key, str(exc)) from None
        return result

    def focus_field(self, key: str) -> None:
        widget = self.fields[key].focus
        widget.setFocus()
        if isinstance(widget, QLineEdit):
            widget.selectAll()

    def first_focus(self) -> QWidget | None:
        return self._order[0] if self._order else None
