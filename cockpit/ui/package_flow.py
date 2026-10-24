"""Menü Pakete und die Abläufe der Paketübersicht (Wunsch des Nutzers vom 21.10.2026).

Menü "P&akete" (Alt+A, Alt+P bleibt für die Liste "Projekte"):
- Paketübersicht … (Strg+Umschalt+P)
- Aufräumen …
- Ordner nach Modellen durchsuchen …
- Liste für einen neuen Rechner speichern … und Liste einlesen und installieren …
Das Menü gibt es nur, wenn das Feature Paketübersicht eingeschaltet ist.

Tauschen in Projekten passiert immer in einem eigenen Branch (project_update.py). Vorher sieht
der Nutzer jede Änderung in einer Liste mit Kästchen und bestätigt.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from PySide6.QtWidgets import QFileDialog, QWidget

from cockpit.core.errors import CockpitError
from cockpit.core.text import count
from cockpit.features.packages import base, catalog, cleanup, models, project_update, record
from cockpit.features.packages import transfer, usage
from cockpit.features.packages.base import MODEL, PIP, Package
from cockpit.features.packages.manifest import FEATURE_ID
from cockpit.ui.menus import AccessibleMenu
from cockpit.ui.announcer import announce
from cockpit.ui.common import ask_buttons, choose_from_list, confirm, pick_folder, show_info
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.ui.main_window import MainWindow

log = logging.getLogger(__name__)

LIST_FILTER = "Liste der Paketübersicht (*.json)"


def run_in_background(parent: QWidget, title: str, work: Callable[[Task], object],
                      done: Callable[[object], None], speak: str = "") -> Task:
    """Eine Aufgabe im Hintergrund mit Fehlerfenster. Der Fokus bleibt, wo er ist."""
    if speak:
        announce(speak)
    task = Task(work, parent)
    task.result.connect(done)
    task.error.connect(lambda message, details: (announce(message, urgent=True, speak=False),
                                                 show_error(parent, title, message, details)))

    def finished() -> None:
        task.wait()
        task.deleteLater()
        tasks.discard(task)
    task.finished.connect(finished)
    tasks.add(task)
    task.start()
    return task


tasks: set[Task] = set()                 # hält laufende Aufgaben, bis sie fertig sind


class PackageMenu:
    def __init__(self, window: "MainWindow") -> None:
        self.window = window
        self.services = window.services
        self.menu: AccessibleMenu | None = None

    def build(self) -> AccessibleMenu:
        menu = AccessibleMenu("P&akete", self.window)
        self.window._action(menu, "&Paketübersicht …", self.open_overview, "Ctrl+Shift+P")
        self.window._action(menu, "&Aufräumen …", lambda: self.cleanup(self.window))
        self.window._action(menu, "Ordner nach &Modellen durchsuchen …",
                            lambda: self.scan_folder(self.window))
        menu.addSeparator()
        self.window._action(menu, "Liste für einen neuen Rechner &speichern …",
                            lambda: self.save_list(self.window))
        self.window._action(menu, "Liste &einlesen und installieren …",
                            lambda: self.read_list(self.window))
        self.menu = menu
        self.update_menu()
        return menu

    def active(self) -> bool:
        try:
            return (FEATURE_ID in self.services.registry
                    and self.services.features.availability(FEATURE_ID).available)
        except CockpitError:
            return False

    def update_menu(self) -> None:
        if self.menu is not None:
            self.menu.menuAction().setVisible(self.active())

    def open_overview(self) -> None:
        if not self.active():
            announce("Die Paketübersicht ist ausgeschaltet. Sie schalten sie in der "
                     "Feature-Verwaltung ein.")
            return
        from cockpit.ui.package_dialogs import SourcesDialog
        SourcesDialog(self.services, self.window, flow=self).exec()

    # -- Aufräumen ---------------------------------------------------------------------------
    def cleanup(self, parent: QWidget, model_packages: list[Package] | None = None) -> None:
        services = self.services
        projects = services.projects.all()

        def work(task: Task):
            found = model_packages
            if found is None:
                found = models.all_models(record.scan_folders(services.database))
                usage.mark(MODEL, found, projects, services)
            return cleanup.candidates(projects, found)

        run_in_background(parent, "Aufräumen", work, lambda found: self._ask_cleanup(parent,
                                                                                    found),
                          "Es wird gesucht, wo Platz frei werden kann.")

    def _ask_cleanup(self, parent: QWidget, found: list[cleanup.Candidate]) -> None:
        from cockpit.ui.sync_dialogs import CheckListDialog
        if not found:
            show_info(parent, "Aufräumen", "Es gibt nichts aufzuräumen.")
            return
        total = sum(c.size for c in found)
        lines = [c.line() for c in found]
        dialog = CheckListDialog(f"Aufräumen: bis zu {base.size_text(total)} frei",
                                 "&Was soll weg?", lines, set(), parent)
        if not dialog.exec() or not dialog.chosen:
            return
        chosen = [found[lines.index(text)] for text in dialog.chosen]
        size = base.size_text(sum(c.size for c in chosen))
        if not confirm(parent, "Aufräumen", f"{count(len(chosen), 'Eintrag wird', 'Einträge werden')}"
                       f" gelöscht, etwa {size} werden frei. Eine Kopie der Dateien gibt es "
                       "nicht. Was sich neu holen lässt, steht vorher in einer Liste in den "
                       "Sicherheitskopien. Aufräumen?", yes="Aufräumen", no="Abbrechen"):
            return

        def done(outcome) -> None:
            freed, failed = outcome
            text = f"Aufgeräumt, etwa {base.size_text(freed)} frei."
            announce(text)
            if failed:
                show_error(parent, "Aufräumen", f"{text} {len(failed)} ließen sich nicht "
                           "löschen.", "\n".join(failed))
        run_in_background(parent, "Aufräumen", lambda task: cleanup.apply(chosen), done,
                          "Wird aufgeräumt.")

    # -- Ordner durchsuchen -----------------------------------------------------------------
    def scan_folder(self, parent: QWidget, after: Callable[[], None] | None = None) -> None:
        folder = pick_folder(parent, "Ordner nach Modellen durchsuchen", str(Path.home()))
        if folder is None:
            return
        database = self.services.database

        def work(task: Task):
            return models.scan_folder(folder, f"Ordner {folder}", task.cancel_event,
                                      skip=(models.hf_cache(), models.ollama_dir()))

        def done(found: list[Package]) -> None:
            if found:
                record.add_scan_folder(database, folder)
            size = base.size_text(sum(p.size or 0 for p in found))
            announce(f"{count(len(found), 'Modelldatei', 'Modelldateien')} gefunden, {size}."
                     + (" Sie stehen jetzt bei den Sprachmodellen." if found else ""))
            if after is not None:
                after()
        run_in_background(parent, "Ordner durchsuchen", work, done, "Der Ordner wird durchsucht.")

    # -- Liste für einen neuen Rechner ------------------------------------------------------
    def _load_for_list(self, task: Task, global_pip_only: bool = True) -> dict:
        from cockpit.features.packages import pip_source
        by_source: dict[str, list[Package]] = {}
        for info in catalog.sources():
            if not info.available or task.cancel_event.is_set():
                continue
            if info.source == PIP and global_pip_only:
                found = []
                for env in pip_source.environments([]):
                    found += pip_source.list_packages(env, task.cancel_event)
                by_source[PIP] = found
            else:
                by_source[info.source] = catalog.load(info.source, [], self.services.database,
                                                      task.cancel_event)
        return by_source

    def save_list(self, parent: QWidget) -> None:
        name, _ = QFileDialog.getSaveFileName(parent, "Liste speichern",
                                              str(Path.home() / "Pakete.json"), LIST_FILTER)
        if not name:
            return
        path = Path(name)

        def work(task: Task):
            return transfer.save(path, self._load_for_list(task))
        run_in_background(parent, "Liste speichern", work,
                          lambda number: announce(f"Liste gespeichert, "
                                                  f"{count(number, 'Eintrag', 'Einträge')}."),
                          "Die Liste wird zusammengestellt.")

    def read_list(self, parent: QWidget) -> None:
        name, _ = QFileDialog.getOpenFileName(parent, "Liste einlesen", str(Path.home()),
                                              LIST_FILTER)
        if not name:
            return
        path = Path(name)

        def work(task: Task):
            wanted = transfer.read(path)
            return transfer.missing(wanted, self._load_for_list(task))
        run_in_background(parent, "Liste einlesen", work,
                          lambda found: self._ask_install(parent, found),
                          "Die Liste wird mit diesem Rechner verglichen.")

    def _ask_install(self, parent: QWidget, found: list[transfer.Wanted]) -> None:
        from cockpit.ui.sync_dialogs import CheckListDialog
        if not found:
            show_info(parent, "Liste einlesen", "Alles aus der Liste ist schon da.")
            return
        lines = [w.line() for w in found]
        dialog = CheckListDialog(f"Fehlt hier: {count(len(found), 'Eintrag', 'Einträge')}",
                                 "&Was soll installiert werden?", lines, set(lines), parent)
        if not dialog.exec() or not dialog.chosen:
            return
        chosen = [found[lines.index(text)] for text in dialog.chosen]
        choice = ask_buttons(parent, "Installieren",
                             f"{count(len(chosen), 'Eintrag wird', 'Einträge werden')} "
                             "installiert. Modelle können Gigabyte brauchen. Bei Chocolatey "
                             "fragt Windows nach Administratorrechten. Welche Versionen?",
                             ["Gespeicherte Versionen", "Jeweils die neueste", "Abbrechen"],
                             default=2, escape=2)
        if choice == 2:
            return
        with_version = choice == 0
        from cockpit.core import exe
        pythons = exe.find_pythons()
        python = Path(pythons[0].command[0]) if pythons else None

        def work(task: Task):
            report = []
            for item in chosen:
                if task.cancel_event.is_set():
                    break
                try:
                    transfer.install(item, python, with_version, task.cancel_event)
                    report.append(f"Installiert: {item.line()}")
                except CockpitError as exc:
                    report.append(f"Nicht installiert: {item.line()}: {exc.message}")
            return report

        def done(report: list[str]) -> None:
            from cockpit.ui.text_dialog import TextDialog
            failed = sum(1 for line in report if line.startswith("Nicht"))
            announce(f"Fertig. {count(len(report) - failed, 'Eintrag', 'Einträge')} installiert"
                     + (f", {failed} nicht." if failed else "."))
            TextDialog("Ergebnis", report, "Ergebnis", parent).exec()
        run_in_background(parent, "Installieren", work, done, "Wird installiert.")

    # -- Bibliotheken in Projekten ----------------------------------------------------------
    def update_project_libraries(self, parent: QWidget, pip_packages: list[Package],
                                 only: str = "") -> None:
        """Projekte mit einer festen, älteren Version in requirements.txt. only: nur diese
        Bibliothek."""
        projects = [p for p in self.services.projects.all() if p.folder_found]
        latest = project_update.latest_versions(pip_packages)

        def work(task: Task):
            from cockpit.features.packages import pip_source
            names = {n for p in projects
                     for n in project_update.pinned(p.code_dir / "requirements.txt")}
            for name in names - set(latest):
                if only and name != usage.normalize(only):
                    continue
                try:
                    found = pip_source.versions(name)
                    if found:
                        latest[name] = found[0]
                except CockpitError:
                    continue
            changes = project_update.outdated_in_projects(projects, latest)
            return [c for c in changes if not only or c.name == usage.normalize(only)]

        run_in_background(parent, "Bibliotheken in Projekten", work,
                          lambda changes: self._ask_libraries(parent, changes),
                          "Die Projekte werden geprüft.")

    def _ask_libraries(self, parent: QWidget, changes: list) -> None:
        from cockpit.ui.sync_dialogs import CheckListDialog
        if not changes:
            show_info(parent, "Bibliotheken in Projekten", "Kein Projekt hat eine feste, ältere "
                      "Version in requirements.txt.")
            return
        lines = [c.line() for c in changes]
        dialog = CheckListDialog("Neuere Bibliotheken in Projekten", "&Was soll getauscht "
                                 "werden?", lines, set(), parent)
        if not dialog.exec() or not dialog.chosen:
            return
        chosen = [changes[lines.index(t)] for t in dialog.chosen]
        by_project: dict[int, list] = {}
        for change in chosen:
            by_project.setdefault(change.project.id, []).append(change)
        jumps = [c.line() for c in chosen if base.major_jump(c.old, c.new)]
        text = (f"Für {count(len(by_project), 'Projekt', 'Projekte')} legt das Cockpit den "
                f"Branch {project_update.LIBRARY_BRANCH} an oder nimmt ihn weiter. Dort ändert es "
                "requirements.txt, installiert neu und startet die Tests des Projekts. Main "
                "bleibt unverändert. Ohne Branch-Ordner wechselt der Ordner Repository in den "
                "Branch und nutzt die Umgebung von main mit.")
        if jumps:
            text += (" Achtung, die erste Stelle der Version ändert sich bei: "
                     f"{'; '.join(jumps[:4])}.")
        if not confirm(parent, "Bibliotheken tauschen", text + " Starten?", yes="Starten",
                       no="Abbrechen"):
            return

        def work(task: Task):
            report = []
            for items in by_project.values():
                project = items[0].project
                report.append(f"Projekt {project.name}:")
                try:
                    report += project_update.update_libraries(project, items, task.cancel_event)
                except CockpitError as exc:
                    report.append(f"Nicht geklappt: {exc.message}")
            return report
        run_in_background(parent, "Bibliotheken tauschen", work,
                          lambda report: self._report(parent, report),
                          "Die Bibliotheken werden getauscht. Das kann dauern.")

    def _report(self, parent: QWidget, report: list[str]) -> None:
        from cockpit.ui.text_dialog import TextDialog
        announce("Fertig. Der Bericht ist da.")
        TextDialog("Bericht", report, "Bericht", parent).exec()
        self.window.refresh_status()

    # -- Modelle in Projekten ---------------------------------------------------------------
    def replace_model(self, parent: QWidget, package: Package) -> None:
        if not package.used_by:
            show_info(parent, "Modell tauschen", f"{package.name} wird von keinem bekannten "
                      "Projekt benutzt.")
            return
        choice = ask_buttons(parent, "Modell tauschen", f"Durch welches Modell soll "
                             f"{package.name} in den Projekten ersetzt werden?",
                             ["Namen eingeben …", "Vorschlag der KI …", "Abbrechen"],
                             default=2, escape=2)
        if choice == 0:
            self._ask_new_name(parent, package, "")
        elif choice == 1:
            self._ask_ai(parent, package)

    def _ask_ai(self, parent: QWidget, package: Package) -> None:
        from cockpit.ui import ai_ui
        tool = self.services.features.setting(FEATURE_ID, "tool") or None
        ai = ai_ui.prepare(self.services, parent, FEATURE_ID, "der Name des Modells", tool)
        if isinstance(ai, str):
            show_error(parent, "Vorschlag der KI", ai)
            return
        prompt = project_update.successor_prompt(package)

        def work(task: Task):
            return project_update.parse_successors(ai.ask(
                prompt, "Antworten Sie auf Deutsch, kurz und sachlich.", task.cancel_event, 400))

        def done(found: list[str]) -> None:
            if not found:
                show_info(parent, "Vorschlag der KI", "Die KI kennt kein passendes neueres "
                          "Modell.")
                return
            index = choose_from_list(parent, "Vorschläge der KI, bitte prüfen", "Vorschläge",
                                     found)
            if index is not None:
                self._ask_new_name(parent, package, found[index].split(": ", 1)[0].strip())
        run_in_background(parent, "Vorschlag der KI", work, done, "Die KI sucht Vorschläge.")

    def _ask_new_name(self, parent: QWidget, package: Package, suggestion: str) -> None:
        from cockpit.ui.package_dialogs import TextInputDialog
        dialog = TextInputDialog("Neues Modell", "&Name des neuen Modells:", suggestion, parent)
        if not dialog.exec():
            return
        new = dialog.value
        projects = [p for p in self.services.projects.all() if p.name in package.used_by]
        names = usage.model_names(package)
        run_in_background(parent, "Modell tauschen",
                          lambda task: project_update.find_places(projects, names),
                          lambda places: self._ask_places(parent, package, names, new, places),
                          "Die Stellen im Code werden gesucht.")

    def _ask_places(self, parent: QWidget, package: Package, names: list[str], new: str,
                    places: list) -> None:
        from cockpit.ui.sync_dialogs import CheckListDialog
        if not places:
            show_info(parent, "Modell tauschen", "Im Code steht der Name des Modells nirgends.")
            return
        lines = [p.line() for p in places]
        dialog = CheckListDialog(f"{package.name} durch {new} ersetzen", "&Stellen:", lines,
                                 set(lines), parent)
        if not dialog.exec() or not dialog.chosen:
            return
        chosen = [places[lines.index(t)] for t in dialog.chosen]
        by_project: dict[int, list] = {}
        for place in chosen:
            by_project.setdefault(place.project.id, []).append(place)
        if not confirm(parent, "Modell tauschen", f"{count(len(chosen), 'Stelle wird', 'Stellen werden')} "
                       f"geändert, in {count(len(by_project), 'Projekt', 'Projekten')}. Das "
                       f"passiert im Branch {project_update.MODEL_BRANCH}, main bleibt "
                       "unverändert. Das neue Modell laden Sie danach selbst herunter, falls es "
                       "noch fehlt. Ändern?", yes="Ändern", no="Abbrechen"):
            return

        def work(task: Task):
            report = []
            for items in by_project.values():
                project = items[0].project
                report.append(f"Projekt {project.name}:")
                try:
                    report += project_update.replace_model(project, items, names, new)
                except CockpitError as exc:
                    report.append(f"Nicht geklappt: {exc.message}")
            return report
        run_in_background(parent, "Modell tauschen", work,
                          lambda report: self._report(parent, report), "Wird geändert.")
