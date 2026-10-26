"""Fenster der Paketübersicht (Wunsch des Nutzers vom 21.10.2026, PLAN-PAKETUEBERSICHT.md).

SourcesDialog: oben "Filtern: Alle" mit Alle, Nur im Cockpit und Nur auf dem Rechner (24.10.2026).
Darunter die Liste (Wunsch des Nutzers vom 26.10.2026):
- "Paketübersicht aktualisieren": Enter liest alle Quellen neu und prüft sie.
- Speicherplatz und Stand.
- "Kritisch": Bibliotheken mit bekannter Sicherheitslücke. Enter öffnet sie.
- eine Zeile pro Quelle. Enter öffnet die Pakete der Quelle.
Die Liste ist gespeichert (cache.py). Gelesen wird nur mit "Paketübersicht aktualisieren" und nach
einer Änderung (nur diese Quelle), danach geprüft, was veraltet ist. Ansagen gibt es nur zweimal:
wenn alles gelesen ist und wenn die Prüfung fertig ist.

PackagesDialog: die Pakete einer Quelle, neueste oben. Ganz oben "Anzeigen: Alle" oder "Nur
veraltete" (26.10.2026). Tab führt zu den Knöpfen. Knöpfe, die zum markierten Paket nicht passen,
sind ausgeblendet. Alles, was ändert, fragt vorher nach. Vorgabe und Escape sind immer die sichere
Antwort.
"""
from __future__ import annotations

import logging
import webbrowser
from typing import Callable

from PySide6.QtWidgets import (QLineEdit, QListWidget, QPushButton, QVBoxLayout,
                               QWidget)

from cockpit.core.errors import CockpitError
from cockpit.features.packages import base, cache, catalog, models, record
from cockpit.features.packages.base import MODEL, PIP, SOURCE_NAMES, Package
from cockpit.core.text import count
from cockpit.ui.announcer import announce
from cockpit.ui.common import (FocusDialog, ask_buttons, choose_from_list, click_focused_button,
                               confirm, label_for)
from cockpit.ui import sounds
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import DialogWorker, _is_enter, button_row
from cockpit.ui.tasks import Task

log = logging.getLogger(__name__)

TITLE = "Paketübersicht"
LOADING = "wird gelesen …"
NOT_READ = "noch nicht gelesen"
REFRESH_TEXT = "Paketübersicht aktualisieren"
# Zeilen der Liste vor den Quellen (26.10.2026)
REFRESH_ROW, SPACE_ROW, CRITICAL_ROW = 0, 1, 2
FIRST_SOURCE_ROW = 3


class TextInputDialog(FocusDialog):
    """Ein Feld mit Label, OK und Abbrechen. Nach accept() steht der Text in value."""

    def __init__(self, title: str, label: str, text: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.value = ""
        self.edit = QLineEdit(text)
        field_label = label_for(self.edit, label)
        ok = QPushButton("OK")
        ok.setDefault(True)
        ok.clicked.connect(self.take)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(field_label)
        layout.addWidget(self.edit)
        layout.addLayout(button_row(None, ok, cancel))
        self.resize(480, 140)
        self.initial_focus_widget = self.edit

    def take(self) -> None:
        self.value = self.edit.text().strip()
        if self.value:
            self.accept()


def save_list(database, data, checked, now) -> bool:
    """Die gespeicherte Liste ist nur Zusatz, ein Fehler stört nie."""
    try:
        cache.save(database, data, checked, now)
    except Exception as exc:                          # noqa: BLE001
        log.warning("Paketliste nicht gespeichert: %r", exc)
        return False
    return True


# -- Quellen -------------------------------------------------------------------------------------
class SourcesDialog(FocusDialog):
    def __init__(self, services, parent: QWidget | None = None, flow=None) -> None:
        """flow: PackageMenu aus package_flow.py für Aufräumen und Tauschen, None in Tests."""
        super().__init__(parent)
        self.services = services
        self.flow = flow
        self.setWindowTitle(TITLE)
        self.infos = catalog.sources()
        self.data: dict[str, list[Package] | None] = {i.source: None for i in self.infos}
        self.checked: set[str] = set()
        # Wunsch des Nutzers vom 26.10.2026: Aktualisieren ist die oberste Zeile der Liste. Die
        # Liste bleibt gespeichert und wird nur dort neu gelesen.
        self.filter_value = base.ALL                    # Vorgabe immer "Alle"
        self.filter = QPushButton()
        self.filter.clicked.connect(self.choose_filter)
        self.saved_at = None
        self.store_pending = False
        self.list = QListWidget()
        list_label = label_for(self.list, "&Quellen:")
        self.list.installEventFilter(self)
        self.open_button = QPushButton("Ö&ffnen")
        self.open_button.clicked.connect(self.open_current)
        self.history_button = QPushButton("&Verlauf …")
        self.history_button.clicked.connect(self.show_history)
        self.cleanup_button = QPushButton("A&ufräumen …")
        self.cleanup_button.clicked.connect(self.cleanup)
        self.scan_button = QPushButton("Ordner nach &Modellen durchsuchen …")
        self.scan_button.clicked.connect(self.scan_folder)
        self.projects_button = QPushButton("Bibliotheken in Pro&jekten …")
        self.projects_button.clicked.connect(self.project_libraries)
        close = QPushButton("&Schließen")
        close.clicked.connect(self.reject)
        for button in (self.filter, self.open_button, self.history_button,
                       self.cleanup_button, self.scan_button, self.projects_button, close):
            button.setAutoDefault(False)
        for button in (self.cleanup_button, self.scan_button, self.projects_button):
            button.setVisible(flow is not None)
        layout = QVBoxLayout(self)
        layout.addLayout(button_row(self.filter, None))
        layout.addWidget(list_label)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(self.open_button, self.history_button, self.cleanup_button,
                                    None))
        layout.addLayout(button_row(self.scan_button, self.projects_button, None, close))
        self.resize(760, 460)
        self.initial_focus_widget = self.list
        self.task: Task | None = None
        self.wanted: list[str] = []                     # Quellen, die gerade gelesen werden
        self.update_filter_button()
        stored, checked, self.saved_at = cache.load(services.database)
        for source in self.data:
            if source in stored:
                self.data[source] = stored[source]
        self.checked = checked & {s for s in self.data if self.data[s] is not None}
        self.fill()
        # Ohne gespeicherte Liste steht die Markierung auf "Paketübersicht aktualisieren", sonst
        # auf der ersten Quelle. Gelesen wird nur auf Wunsch (26.10.2026).
        has_data = any(v is not None for v in self.data.values())
        self.list.setCurrentRow(FIRST_SOURCE_ROW if has_data and self.infos else REFRESH_ROW)

    # -- Anzeige ---------------------------------------------------------------------------
    @property
    def chosen_filter(self) -> str:
        return self.filter_value

    def missing(self) -> list[str]:
        """Verfügbare Quellen ohne gespeicherte Liste."""
        return [i.source for i in self.infos if i.available and self.data.get(i.source) is None]

    def update_filter_button(self) -> None:
        self.filter.setText(f"&Filtern: {self.filter_value}")
        self.filter.setAccessibleName(f"Filtern: {self.filter_value}")

    def set_filter(self, value: str) -> None:
        self.filter_value = value
        self.update_filter_button()
        self.fill()
        for dialog in self.findChildren(PackagesDialog):
            dialog.refresh(quiet=True)

    def choose_filter(self) -> None:
        options = list(base.FILTERS)
        index = choose_from_list(self, "Filtern", "Zeigen", options,
                                 options.index(self.filter_value))
        if index is not None:
            self.set_filter(options[index])
            announce(f"Filter: {self.filter_value}.")
        self.filter.setFocus()

    def refresh_all(self) -> None:
        """Alle Quellen neu lesen und prüfen (Knopf Aktualisieren)."""
        if self.task is not None:
            announce("Wird schon gelesen.")
            return
        for source in self.data:
            self.data[source] = None
        self.checked.clear()
        announce("Pakete werden neu gelesen.")
        self.load()
        self.fill()

    def visible(self, source: str) -> list[Package]:
        return base.apply_filter(self.data.get(source) or [], self.chosen_filter)

    def row_text(self, info: catalog.SourceInfo) -> str:
        if not info.available:
            return f"{info.name}, nicht verfügbar: {info.reason}"
        packages = self.data.get(info.source)
        if packages is None:
            return f"{info.name}, {LOADING if self.reading(info.source) else NOT_READ}"
        text = catalog.summary(info.source, self.visible(info.source))
        if info.source not in self.checked:
            text += ", wird geprüft …"
        return text

    def fill(self) -> None:
        row = self.list.currentRow()
        self.list.clear()
        shown = {s: self.visible(s) for s in self.data if self.data[s] is not None}
        line = catalog.space_line(shown)
        if self.saved_at is not None and self.task is None:
            line += f". Stand: {self.saved_at:%d.%m.%Y %H:%M}"
        self.list.addItem(REFRESH_TEXT + (", läuft …" if self.task is not None else ""))
        self.list.addItem(line)
        self.list.addItem(self.critical_text())
        for info in self.infos:
            self.list.addItem(self.row_text(info))
        self.list.setCurrentRow(max(0, min(row, self.list.count() - 1)))

    def reading(self, source: str) -> bool:
        return self.task is not None and source in self.wanted

    def critical(self) -> list[Package]:
        """Alle Pakete mit bekannter Sicherheitslücke, nach dem Filter oben."""
        return [p for source in self.data for p in self.visible(source) if base.is_critical(p)]

    def critical_text(self) -> str:
        if self.data.get(PIP) is None:
            return f"Kritisch, {LOADING if self.reading(PIP) else NOT_READ}"
        if PIP not in self.checked:
            return "Kritisch, wird geprüft …"
        found = len(self.critical())
        if not found:
            return "Kritisch: keine bekannte Sicherheitslücke"
        return f"Kritisch: {count(found, 'Bibliothek', 'Bibliotheken')} mit Sicherheitslücke"

    def current_info(self) -> catalog.SourceInfo | None:
        row = self.list.currentRow() - FIRST_SOURCE_ROW
        return self.infos[row] if 0 <= row < len(self.infos) else None

    # -- Lesen und prüfen im Hintergrund ---------------------------------------------------------
    def load(self, only: str | None = None) -> None:
        """Alle Quellen lesen, dann prüfen. only: nur diese eine noch einmal."""
        if self.task is not None:
            return
        services, data = self.services, self.data
        wanted = [i.source for i in self.infos if i.available and (only is None
                                                                   or i.source == only)]
        if only is not None:
            self.checked.discard(only)
        self.wanted = wanted
        projects = services.projects.all()

        def work(task: Task):
            for source in wanted:
                if task.cancel_event.is_set():
                    return None
                try:
                    data[source] = catalog.load(source, projects, services.database,
                                                task.cancel_event)
                except CockpitError as exc:
                    log.warning("Paketübersicht %s: %s", source, exc.message)
                    data[source] = []
                self.after_load(source, data[source], projects)
                task.status.emit(source)
            if only is None:
                task.status.emit("gelesen")
            for source in wanted:
                if task.cancel_event.is_set():
                    return None
                try:
                    catalog.check(source, data[source], projects, task.cancel_event)
                except CockpitError as exc:
                    log.warning("Prüfung %s: %s", source, exc.message)
                task.status.emit("geprüft:" + source)
            return wanted

        task = Task(work, self)
        task.status.connect(self.progress)
        task.result.connect(self.loaded)
        task.error.connect(lambda message, details: show_error(self, TITLE, message, details))
        task.finished.connect(self._finished)
        self.task = task
        task.start()

    def after_load(self, source: str, packages: list[Package], projects) -> None:
        """Im Hintergrund nach dem Lesen einer Quelle. Stufe 2 ergänzt hier "benutzt von"."""
        from cockpit.features.packages import usage
        try:
            usage.mark(source, packages, projects, self.services)
        except Exception as exc:                  # nie das Lesen daran scheitern lassen
            log.warning("Benutzt von, %s: %r", source, exc)

    def progress(self, text: str) -> None:
        if text == "gelesen":
            announce("Pakete gelesen. Die Prüfung läuft noch.", speak=False)
        elif text.startswith("geprüft:"):
            self.checked.add(text.split(":", 1)[1])
        self.fill()
        for dialog in self.findChildren(PackagesDialog):
            dialog.refresh(quiet=True)

    def loaded(self, wanted) -> None:
        if not wanted:
            return
        self.store_pending = True                       # erst, wenn der Thread ganz fertig ist
        old = sum(1 for s in wanted for p in self.visible(s) if p.outdated)
        announce(f"Prüfung fertig: {count(old, 'Paket ist', 'Pakete sind')} veraltet." if old
                 else "Prüfung fertig: alles aktuell.")

    def store(self) -> None:
        """Liste speichern, nur wenn alle verfügbaren Quellen gelesen sind. So überschreibt ein
        abgebrochenes Lesen nie die letzte vollständige Liste. Nie beim Schließen: Dann kann
        die Datenbank schon zu sein."""
        if self.missing() or self.task is not None:
            return
        from datetime import datetime
        now = datetime.now()
        if save_list(self.services.database, self.data, self.checked, now):
            self.saved_at = now

    def _finished(self) -> None:
        task, self.task = self.task, None
        if task is not None:
            task.wait()
            task.deleteLater()
        if self.store_pending:
            self.store_pending = False
            self.store()
        self.fill()                                     # mit "Stand:" in der ersten Zeile

    # -- Bedienung -------------------------------------------------------------------------
    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            self.open_current()
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)

    def open_current(self) -> None:
        row = self.list.currentRow()
        if row == REFRESH_ROW:
            self.refresh_all()
            return
        if row == CRITICAL_ROW:
            self.open_critical()
            return
        info = self.current_info()
        if info is None:
            announce(self.list.currentItem().text() if self.list.currentItem() else "")
            return
        if not info.available:
            announce(f"Nicht verfügbar: {info.reason}.")
            return
        if self.data.get(info.source) is None:
            announce("Wird noch gelesen.")
            return
        PackagesDialog(self, info.source).exec()
        self.fill()

    def open_critical(self) -> None:
        if self.data.get(PIP) is None or PIP not in self.checked:
            announce("Die Bibliotheken sind noch nicht geprüft. Wählen Sie oben Paketübersicht "
                     "aktualisieren.")
            return
        PackagesDialog(self, base.CRITICAL).exec()
        self.fill()

    def show_history(self) -> None:
        from cockpit.ui.text_dialog import TextDialog
        lines = record.history(self.services.database) or ["Noch keine Änderungen."]
        TextDialog("Verlauf der Paketübersicht", lines, "Verlauf", self).exec()

    def cleanup(self) -> None:
        if self.flow is None:
            return
        self.flow.cleanup(self, self.data.get(MODEL))      # None: liest die Modelle selbst

    def scan_folder(self) -> None:
        if self.flow is not None:
            self.flow.scan_folder(self, after=lambda: self.reload(MODEL))

    def project_libraries(self, only: str = "") -> None:
        if self.flow is None:
            return
        if PIP not in self.checked:
            announce("Die Bibliotheken werden noch geprüft. Bitte gleich noch einmal.")
            return
        self.flow.update_project_libraries(self, self.data.get(PIP) or [], only)

    def reload(self, source: str) -> None:
        self.data[source] = None
        self.fill()
        self.load(source)

    def reject(self) -> None:
        if self.task is not None:
            self.task.cancel()
        super().reject()

    def done(self, code: int) -> None:
        if self.task is not None:
            self.task.cancel()
            self.task.wait(15000)
        super().done(code)


# -- Pakete einer Quelle --------------------------------------------------------------------------
class PackagesDialog(FocusDialog):
    def __init__(self, sources: SourcesDialog, source: str) -> None:
        super().__init__(sources)
        self.sources = sources
        self.source = source                    # eine Quelle oder base.CRITICAL
        # Bei "Kritisch" sind es Bibliotheken: Nach einer Änderung wird pip neu gelesen
        self.data_source = PIP if source == base.CRITICAL else source
        self.name = base.CRITICAL_NAME if source == base.CRITICAL else SOURCE_NAMES[source]
        self.services = sources.services
        self.database = sources.services.database
        self.shown: list[Package] = []
        # Wunsch des Nutzers vom 26.10.2026: oben "Anzeigen: Alle" oder "Nur veraltete"
        self.show_value = base.SHOW_ALL
        self.show_button = QPushButton()
        self.show_button.setAutoDefault(False)
        self.show_button.clicked.connect(self.choose_show)
        self.update_show_button()
        self.search = QLineEdit()
        search_label = label_for(self.search, "Su&chen:")
        self.search.textChanged.connect(lambda _t: self.refresh(quiet=True))
        self.list = QListWidget()
        list_label = label_for(self.list, "&Pakete:")
        self.list.installEventFilter(self)
        self.list.currentRowChanged.connect(lambda _row: self.update_buttons())
        self.worker = DialogWorker(self, self.name)
        made = [
            ("update_button", "&Aktualisieren …", self.update_current),
            ("version_button", "&Version wählen …", self.choose_version),
            ("pin_button", "&Festhalten", self.toggle_pin),
            ("back_button", "&Zurück …", self.go_back),
            ("old_button", "Alte Fassungen &entfernen …", self.remove_old),
            ("changes_button", "Änderungen a&nsehen", self.show_changes),
            ("swap_button", "In Projekten &tauschen …", self.swap_in_projects),
            ("delete_button", "&Löschen …", self.delete_current),
            ("all_button", "Alle veralteten akt&ualisieren …", self.update_all),
        ]
        self.action_buttons: list[QPushButton] = []
        for attribute, text, slot in made:
            button = QPushButton(text)
            button.setAutoDefault(False)
            button.clicked.connect(slot)
            setattr(self, attribute, button)
            self.action_buttons.append(button)
        close = QPushButton("&Schließen")
        close.setAutoDefault(False)
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(button_row(self.show_button, None))
        layout.addWidget(search_label)
        layout.addWidget(self.search)
        layout.addWidget(list_label)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(*self.action_buttons[:4], None))
        layout.addLayout(button_row(*self.action_buttons[4:], None, close))
        self.resize(900, 560)
        self.initial_focus_widget = self.list
        self.refresh(quiet=True)
        self.list.setCurrentRow(0)

    # -- Anzeige ---------------------------------------------------------------------------
    def update_show_button(self) -> None:
        self.show_button.setText(f"Anzei&gen: {self.show_value}")
        self.show_button.setAccessibleName(f"Anzeigen: {self.show_value}")

    def choose_show(self) -> None:
        options = list(base.SHOWS)
        index = choose_from_list(self, "Anzeigen", "Anzeigen", options,
                                 options.index(self.show_value))
        if index is not None:
            self.set_show(options[index])
            announce(f"Anzeigen: {self.show_value}, "
                     f"{count(len(self.shown), 'Eintrag', 'Einträge')}.")
        self.show_button.setFocus()

    def set_show(self, value: str) -> None:
        self.show_value = value
        self.update_show_button()
        self.refresh(quiet=True)

    def packages(self) -> list[Package]:
        if self.source == base.CRITICAL:
            return self.sources.critical()
        return base.apply_filter(self.sources.data.get(self.source) or [],
                                 self.sources.chosen_filter)

    def refresh(self, quiet: bool = False) -> None:
        current = self.current()
        words = self.search.text().strip().lower()
        shown = base.newest_first(self.packages())
        if self.show_value == base.SHOW_OUTDATED:
            shown = [p for p in shown if p.outdated]
        if words:
            shown = [p for p in shown if words in p.line().lower()]
        self.shown = shown
        self.setWindowTitle(f"{self.name}: {count(len(shown), 'Eintrag', 'Einträge')}"
                            + (", wird gelesen …" if self.sources.data.get(self.data_source)
                               is None else ""))
        self.list.clear()
        self.list.addItems([p.line() for p in shown] or ["Keine Einträge."])
        row = 0
        if current is not None:
            row = next((i for i, p in enumerate(shown) if p.id == current.id
                        and p.place == current.place), 0)
        self.list.setCurrentRow(row)
        self.update_buttons()
        if not quiet:
            announce(f"{count(len(shown), 'Eintrag', 'Einträge')}.")

    def current(self) -> Package | None:
        row = self.list.currentRow()
        return self.shown[row] if 0 <= row < len(self.shown) else None

    def update_buttons(self) -> None:
        package = self.current()
        present = package is not None
        self.update_button.setVisible(present and catalog.can_update(package)
                                      and (package.outdated or package.source == MODEL))
        self.version_button.setVisible(present and catalog.can_choose_version(package))
        self.pin_button.setVisible(present and catalog.can_pin(package))
        if present:
            self.pin_button.setText("Nicht mehr &festhalten" if package.pinned else "&Festhalten")
        back = record.previous_version(self.database, package) if present and \
            package.source != MODEL else ""
        self.back_button.setVisible(bool(back))
        self.back_button.setText(f"&Zurück zu {back} …")
        self.old_button.setVisible(present and package.kind == models.HF
                                   and bool(models.hf_old_revisions(package)))
        self.changes_button.setVisible(present and package.source == PIP)
        self.swap_button.setVisible(present and self.sources.flow is not None and (
            (package.source == PIP and package.outdated)
            or (package.source == MODEL and bool(package.used_by)
                and package.used_by != ("KI-Verwaltung des Cockpits",))))
        self.delete_button.setVisible(present)
        self.all_button.setVisible(any(p.outdated and not p.pinned and p.source != MODEL
                                       for p in self.shown))

    # -- Bedienung -------------------------------------------------------------------------
    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            self.show_details()
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if not click_focused_button(self, event):
            super().keyPressEvent(event)

    def show_details(self) -> None:
        from cockpit.ui.text_dialog import TextDialog
        package = self.current()
        if package is None:
            return
        TextDialog(f"Angaben zu {package.name}", details(package), "Angaben", self).exec()

    def run(self, work: Callable[[], str], speak: str) -> None:
        """Im Hintergrund, danach die Quelle neu lesen. Solange es läuft, kommt der Warteton
        "Programm arbeitet" (Wunsch des Nutzers vom 24.10.2026), am Ende der Erfolgston."""
        sound = sounds.TransferSound(self.services.settings.load().transfer_sounds, self)

        def done(text) -> None:
            sound.finish(True)
            announce(text)
            self.sources.reload(self.data_source)
            self.refresh(quiet=True)
        sound.start()
        if not self.worker.run(work, done, speak, failed=lambda: sound.finish(False)):
            sound.stop()                                # es lief schon etwas

    def update_current(self) -> None:
        package = self.current()
        if package is None:
            return
        if package.source == MODEL:
            self._update_model(package)
            return
        text = (f"{package.name} wird von {package.version} auf {package.latest or 'die neueste'}"
                f" aktualisiert, {package.place}.")
        if package.source == "choco":
            text += " Windows fragt nach Administratorrechten."
        buttons = ["Aktualisieren", "Abbrechen"]
        if base.major_jump(package.version, package.latest):
            text += (" Achtung: Die erste Stelle der Version ändert sich. Dann ändert sich oft "
                     "Grundlegendes, und Programme, die es benutzen, laufen vielleicht nicht "
                     "mehr.")
            if package.source == PIP:
                buttons = ["Aktualisieren", "Änderungen ansehen", "Abbrechen"]
        choice = ask_buttons(self, "Aktualisieren", text + " Aktualisieren?", buttons,
                             default=len(buttons) - 1, escape=len(buttons) - 1)
        if buttons[choice] == "Änderungen ansehen":
            self.show_changes()
            return
        if buttons[choice] != "Aktualisieren":
            return
        database = self.database
        self.run(lambda: catalog.upgrade(database, package), f"{package.name} wird aktualisiert.")

    def _update_model(self, package: Package) -> None:
        database = self.database
        if package.kind == models.HF:
            if not confirm(self, "Neue Fassung", f"Die neueste Fassung von {package.name} wird "
                           "heruntergeladen. Die bisherige bleibt liegen, bis Sie „Alte "
                           "Fassungen entfernen“ wählen. Das kann Gigabyte brauchen. "
                           "Herunterladen?", yes="Herunterladen", no="Abbrechen"):
                return
            self.run(lambda: catalog.upgrade(database, package), "Wird heruntergeladen.")
            return
        choice = ask_buttons(self, "Neue Fassung",
                             f"Die neueste Fassung von {package.name} wird geholt. Soll die "
                             f"bisherige bleiben? Sie heißt dann "
                             f"{models.ollama_keep_name(package)}.",
                             ["Neue holen, alte behalten", "Neue holen, alte ersetzen",
                              "Abbrechen"], default=2, escape=2)
        if choice == 2:
            return
        keep = choice == 0
        self.run(lambda: catalog.upgrade(database, package, keep_old=keep),
                 "Wird heruntergeladen.")

    def choose_version(self) -> None:
        package = self.current()
        if package is None:
            return
        database = self.database
        if package.source == MODEL:
            what = "Fassung, Branch oder Commit" if package.kind == models.HF else "Tag"
            example = "main" if package.kind == models.HF else "latest"
            dialog = TextInputDialog(f"Andere Fassung von {package.name}", f"&{what}:", example,
                                     self)
            if not dialog.exec():
                return
            wanted = dialog.value
            if not confirm(self, "Andere Fassung", f"{package.name}: Die Fassung {wanted} wird "
                           "zusätzlich heruntergeladen. Die bisherige bleibt. Herunterladen?",
                           yes="Herunterladen", no="Abbrechen"):
                return
            self.run(lambda: catalog.install_version(database, package, wanted),
                     "Wird heruntergeladen.")
            return

        def show(found: list[str]) -> None:
            if not found:
                announce("Keine Versionen gefunden.", urgent=True)
                return
            current = found.index(package.version) if package.version in found else 0
            index = choose_from_list(self, f"Version von {package.name}", "Versionen",
                                     [v + (", installiert" if v == package.version else "")
                                      for v in found], current)
            if index is None or found[index] == package.version:
                return
            chosen = found[index]
            text = f"{package.name} bekommt Version {chosen} statt {package.version}, " \
                   f"{package.place}."
            if package.source == PIP:
                text += " In einer Umgebung gibt es immer nur eine Version."
            if package.source == "choco":
                text += " Windows fragt nach Administratorrechten."
            if not confirm(self, "Version wählen", text + " Installieren?", yes="Installieren",
                           no="Abbrechen"):
                return
            self.run(lambda: catalog.install_version(database, package, chosen),
                     f"Version {chosen} wird installiert.")

        self.worker.run(lambda: catalog.versions(package), show, "Versionen werden abgefragt.")

    def go_back(self) -> None:
        package = self.current()
        back = record.previous_version(self.database, package) if package else ""
        if not back:
            return
        if not confirm(self, "Zurück zur vorherigen Version", f"{package.name} bekommt wieder "
                       f"Version {back} statt {package.version}, {package.place}. Zurück?",
                       yes="Zurück", no="Abbrechen"):
            return
        database = self.database
        self.run(lambda: catalog.install_version(database, package, back),
                 f"Version {back} wird installiert.")

    def toggle_pin(self) -> None:
        package = self.current()
        if package is None:
            return
        on = not package.pinned
        database = self.database
        if package.source == "choco":
            announce("Windows fragt nach Administratorrechten.")
        self.worker.run(lambda: catalog.set_pinned(database, package, on),
                        lambda text: (announce(text), self.refresh(quiet=True)),
                        after=self.sources.store)       # "festgehalten" auch gespeichert

    def remove_old(self) -> None:
        package = self.current()
        if package is None:
            return
        old = models.hf_old_revisions(package)
        if not confirm(self, "Alte Fassungen entfernen", f"Bei {package.name} werden "
                       f"{count(len(old), 'alte Fassung', 'alte Fassungen')} gelöscht. Die "
                       "aktuelle bleibt. Eine Liste kommt in die Sicherheitskopien. Entfernen?",
                       yes="Entfernen", no="Abbrechen"):
            return

        def work() -> str:
            record.save_list([package], "vor dem Entfernen alter Fassungen")
            freed = models.hf_remove_old(package)
            return f"Alte Fassungen entfernt, {base.size_text(freed)} frei."
        self.run(work, "Alte Fassungen werden entfernt.")

    def show_changes(self) -> None:
        package = self.current()
        if package is None or package.source != PIP:
            return
        from cockpit.features.packages import pip_source

        def opened(url: str) -> None:
            webbrowser.open(url)
            announce("Liste der Änderungen wird im Browser geöffnet.")
        self.worker.run(lambda: pip_source.change_log(package.id), opened)

    def swap_in_projects(self) -> None:
        """Neuere Bibliothek oder anderes Modell in den Projekten, immer in einem Branch."""
        package = self.current()
        if package is None or self.sources.flow is None:
            return
        if package.source == PIP:
            self.sources.project_libraries(only=package.name)
        else:
            self.sources.flow.replace_model(self, package)

    def delete_current(self) -> None:
        package = self.current()
        if package is None:
            return
        text = f"{package.name} {package.version}".strip() + f" wird gelöscht, {package.place}."
        if package.size:
            text += f" Es werden {base.size_text(package.size)} frei."
        if package.used_by:
            text += f" Achtung: Es wird benutzt von {', '.join(package.used_by)}."
        if package.source == "choco":
            text += " Windows fragt nach Administratorrechten."
        text += (" Eine Kopie der Dateien gibt es nicht, nur eine Liste in den Sicherheitskopien, "
                 "mit der Sie es neu holen können.")
        if not confirm(self, "Löschen", text + " Löschen?", yes="Löschen", no="Abbrechen"):
            return
        database = self.database
        self.run(lambda: catalog.uninstall(database, [package]), f"{package.name} wird gelöscht.")

    def update_all(self) -> None:
        wanted = [p for p in self.shown if p.outdated and not p.pinned and p.source != MODEL]
        if not wanted:
            return
        names = ", ".join(p.name for p in wanted[:8]) + (" und weitere" if len(wanted) > 8
                                                         else "")
        jumps = [p.name for p in wanted if base.major_jump(p.version, p.latest)]
        text = f"{count(len(wanted), 'Paket wird', 'Pakete werden')} aktualisiert: {names}."
        if jumps:
            text += (f" Bei {', '.join(jumps[:5])} ändert sich die erste Stelle der Version. "
                     "Dann ändert sich oft Grundlegendes.")
        text += " Festgehaltene bleiben, wie sie sind."
        if not confirm(self, "Alle aktualisieren", text + " Aktualisieren?", yes="Aktualisieren",
                       no="Abbrechen"):
            return
        database = self.database
        self.run(lambda: catalog.upgrade_all(database, wanted), "Wird aktualisiert.")

    def reject(self) -> None:
        if self.worker.busy:
            announce("Das läuft noch. Bitte warten Sie, bis es fertig ist.")
            return
        super().reject()

    def done(self, code: int) -> None:
        self.worker.wait()
        super().done(code)


def details(package: Package) -> list[str]:
    lines = [f"{package.name} {package.version}".strip(), f"Zustand: {package.state()}",
             f"Quelle: {SOURCE_NAMES.get(package.source, package.source)}"]
    if package.place:
        lines.append(f"Ort: {package.place}")
    if package.location is not None:
        lines.append(f"Pfad: {package.location}")
    lines.append(f"Größe: {base.size_text(package.size)}")
    if package.added is not None:
        lines.append(f"Hinzugefügt: {package.added:%d.%m.%Y %H:%M}")
    if package.owner:
        lines.append(f"Gehört zu: {package.owner}")
    lines.append("Benutzt von: " + (", ".join(package.used_by) if package.used_by
                                    else "keinem bekannten Projekt"))
    if package.license:
        lines.append(f"Lizenz: {package.license}")
    if package.pinned:
        lines.append("Festgehalten: Alle aktualisieren lässt es aus.")
    if package.warning:
        lines.append(f"Hinweis: {package.warning}")
    revisions = package.extra.get("revisions")
    if revisions:
        lines.append(f"Fassungen: {', '.join(r[:7] for r in revisions)}")
    return lines
