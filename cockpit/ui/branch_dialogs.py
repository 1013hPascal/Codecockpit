"""Übersicht "Branches" und beiseitegelegte Änderungen (Konzept 10.14, Teilschritt 5f).

BranchesDialog ("Branches verwalten"): oben "Neuer Branch …", darunter "Branches anzeigen: Die Sie
lokal haben" (Wunsch des Nutzers, 02.10.2026). Leertaste oder Enter öffnet dort ein Menü mit
"Die Sie lokal haben" (Vorgabe), "Die nur auf GitHub sind" und "Alle". So behält man den
Überblick, auch wenn viele Leute an eigenen Branches arbeiten. Darunter die Branches, zum Beispiel
"design, hier und auf GitHub, zuletzt von Anna am 24.09.2026, 2 Commits vor main". Enter wechselt
zum markierten Branch. Per Tab beim Haupt-Branch: "Exe" mit Version und Veröffentlichung. Bei einem
Branch: "In main übernehmen …, 2 Commits offen" bzw. "…, alles aktuell", "Umbenennen …",
"Branch-Ordner entfernen …", "Löschen …". Bei einem Branch nur auf GitHub: "Herunterladen",
"Umbenennen …", "Löschen …".
StashDialog: beiseitegelegte Änderungen. "Zurückholen …", "Als neuen Branch zurückholen …",
"Löschen …".

Wechseln mit Änderungen ohne Commit fragt vorher, wie GitHub Desktop: beiseitelegen, mitnehmen
oder abbrechen (Vorgabe). Beim Zurückwechseln bietet das Cockpit an, beiseitegelegte Änderungen
zurückzuholen. Was mit der Plattform spricht, läuft im Hintergrund. Nie ein force push.
"""
from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import QLineEdit, QListWidget, QMenu, QPushButton, QVBoxLayout, QWidget

from cockpit.core import branches, exe, sync
from cockpit.core.branches import Branch, Stash
from cockpit.core.errors import CockpitError
from cockpit.core.sync import ConflictKind
from cockpit.core.text import count
from cockpit.ui import sync_dialogs
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, ask_buttons, confirm, label_for, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialogs import DialogWorker, _is_enter, button_row

if TYPE_CHECKING:
    from cockpit.core.projects import Project

NEW_BRANCH_TEXT = "Neuer Branch …"
SHOW_PREFIX = "Branches anzeigen: "
LOCAL, REMOTE, ALL = "local", "remote", "all"


def filter_names(platform_name: str = "GitHub") -> dict[str, str]:
    return {LOCAL: "Die Sie lokal haben", REMOTE: f"Die nur auf {platform_name} sind",
            ALL: "Alle"}


def filtered(items: list[Branch], kind: str) -> list[Branch]:
    if kind == LOCAL:
        return [b for b in items if b.local]
    if kind == REMOTE:
        return [b for b in items if not b.local]
    return list(items)


def exe_lines(project: "Project") -> list[str]:
    """Stand der Exe für den Haupt-Branch: Version und ob sie veröffentlicht ist."""
    if not project.has_exe_dir:
        return ["Exe: Dieses Projekt hat keinen Ordner Exe."]
    lines = [exe.status_line(project)]
    record = exe.read_record(project.code_dir) if project.folder_found else None
    if record is not None and record.version:
        lines.append(f"Veröffentlicht als Version {record.version}.")
    elif exe.current_exe(project) is not None:
        lines.append("Noch nicht veröffentlicht.")
    return lines


class BranchesDialog(FocusDialog):
    """Nach dem Schließen ist changed True, wenn sich Branch oder Dateien geändert haben."""

    def __init__(self, project: "Project", items: list[Branch], env: dict[str, str] | None = None,
                 platform_name: str = "GitHub", parent: QWidget | None = None,
                 folders: dict[str, str] | None = None, single: bool = False) -> None:
        super().__init__(parent)
        # single (Wunsch aus dem Test von 10f): nur ein Branch-Ordner, "<Name> verwalten"
        self.single = single
        self.single_name = items[0].name if single and items else ""
        self.remove_request = False
        self.remove_name = ""                         # Branch, dessen Ordner weg soll
        self.delete_request = ""
        self.offset = 0 if single else 2              # oben "Neuer Branch …" und die Auswahl
        self.project = project
        self.code_dir = project.code_dir
        self.show_kind = LOCAL
        self.all_items = items
        self.items = items if single else filtered(items, LOCAL)
        self.env = env or {}
        self.platform_name = platform_name
        self.main = branches.default_branch(self.code_dir)
        self.changed = False
        # Phase 10f: Mit einem Ordner pro Branch wird nicht gewechselt. "Wechseln" legt dann den
        # Ordner an, "Neuer Branch" einen Branch mit Ordner. Beides erledigt nach dem Schließen
        # der Aufrufer (WorktreeActions), weil es im Hintergrund holt.
        self.structured = project.has_branch_folders
        self.folders = folders or {}                  # Branch: Ordnername
        self.new_request = ""
        self.open_request = ""
        self.worker = DialogWorker(self, "Branches")
        self.list = QListWidget()
        name_widget(self.list, "Branches")
        self.list.installEventFilter(self)
        switch = QPushButton("&Wechseln")
        switch.clicked.connect(self.switch_current)
        self.switch_button = switch
        new = QPushButton("&Neuer Branch …")
        new.clicked.connect(self.new_branch)
        self.merge_button = QPushButton(f"In &{self.main} übernehmen …")
        self.merge_button.clicked.connect(self.merge_current)
        rename = QPushButton("&Umbenennen …")
        rename.clicked.connect(self.rename_current)
        delete = QPushButton("&Löschen …")
        delete.clicked.connect(self.delete_current)
        self.rename_button, self.delete_button = rename, delete
        remove = QPushButton("Branch-&Ordner entfernen …")
        remove.clicked.connect(self.remove_folder)
        self.remove_button = remove
        remove.setVisible(single)
        new.setVisible(False)                         # steht jetzt oben in der Liste
        self.new_button = new
        # Beim Haupt-Branch mit Tab: Stand der Exe (Wunsch des Nutzers, 30.09.2026)
        self.exe_info = QListWidget()
        self.exe_label = label_for(self.exe_info, "&Exe:")
        self.exe_info.addItems(exe_lines(project))
        self.exe_info.setCurrentRow(0)
        self.list.currentRowChanged.connect(lambda _row: self.update_buttons())
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.exe_label)
        layout.addWidget(self.exe_info)
        layout.addLayout(button_row(switch, new, self.merge_button, rename, remove, delete, None,
                                    close))
        self.resize(760, 420)
        self.initial_focus_widget = self.list
        self.fill()

    # -- Anzeige ---------------------------------------------------------------------------
    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            if self.on_new_row():
                self.new_branch()
            elif self.on_show_row():
                self.choose_show()
            else:
                self.switch_current()                   # Enter wechselt (Konzept 10.14)
            return True
        if (watched is self.list and event.type() == event.Type.KeyPress
                and event.key() == Qt.Key.Key_Space and self.on_show_row()):
            self.choose_show()
            return True
        return super().eventFilter(watched, event)

    def on_new_row(self) -> bool:
        return self.offset > 0 and self.list.currentRow() == 0

    def on_show_row(self) -> bool:
        return self.offset > 1 and self.list.currentRow() == 1

    def show_text(self) -> str:
        return SHOW_PREFIX + filter_names(self.platform_name)[self.show_kind]

    def choose_show(self) -> None:
        """Menü mit den drei Möglichkeiten. Pfeil hoch und runter, Enter oder Leertaste wählt,
        Escape lässt alles, wie es ist."""
        menu = QMenu(self.list)
        name_widget(menu, "Branches anzeigen")
        group = QActionGroup(menu)
        chosen = {}
        for key, label in filter_names(self.platform_name).items():
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(key == self.show_kind)
            group.addAction(action)
            chosen[action] = key
        current = next(a for a, k in chosen.items() if k == self.show_kind)
        menu.setActiveAction(current)
        rect = self.list.visualItemRect(self.list.currentItem())
        picked = menu.exec(self.list.viewport().mapToGlobal(rect.bottomLeft()), current)
        if picked is not None:
            self.set_show(chosen[picked])
        self.list.setFocus()

    def set_show(self, kind: str) -> None:
        self.show_kind = kind
        self.items = filtered(self.all_items, kind)
        self.fill()
        self.list.setCurrentRow(1)
        announce(f"{filter_names(self.platform_name)[kind]}: "
                 f"{count(len(self.items), 'Branch', 'Branches')}.")

    def row_of(self, name: str) -> int:
        """Zeile eines Branches in der Liste."""
        return [b.name for b in self.items].index(name) + self.offset

    def done(self, code: int) -> None:
        self.worker.wait()
        super().done(code)

    def fill(self, select: str = "") -> None:
        row = max(0, self.list.currentRow())
        if self.single:
            self.setWindowTitle(f"{self.single_name} verwalten")
        else:
            # Der Titel zählt alle Branches, auch die gerade nicht angezeigten
            self.setWindowTitle(f"Branches von {self.project.name}: "
                                f"{count(len(self.all_items), 'Branch', 'Branches')}")
        self.list.clear()
        if self.offset:
            self.list.addItem(NEW_BRANCH_TEXT)
            self.list.addItem(self.show_text())
        empty = "Noch keine Branches." if self.single or self.show_kind == ALL else \
            "Hier gibt es keine Branches. Mit „Branches anzeigen“ sehen Sie die anderen."
        self.list.addItems([self.line(b) for b in self.items] or [empty])
        names = [b.name for b in self.items]
        if select in names:
            row = names.index(select) + self.offset
        self.list.setCurrentRow(min(row, self.list.count() - 1))
        self.update_buttons()

    def line(self, branch: Branch) -> str:
        """Mit Branch-Ordnern gibt es keinen "aktuellen Branch". Die Zeile nennt stattdessen den
        Ordner (Wunsch aus dem Test von 10f)."""
        if not self.structured:
            return branch.line(self.main, self.platform_name)
        text = dataclasses.replace(branch, current=False).line(self.main, self.platform_name)
        if branch.default:
            where = f"Ordner Code\\{self.code_dir.name}"
        elif branch.name in self.folders:
            where = f"Ordner Code\\{self.folders[branch.name]}"
        else:
            where = "ohne Ordner"
        name, _, rest = text.partition(", ")
        return f"{name}, {where}, {rest}" if rest else f"{name}, {where}"

    def remove_folder(self) -> None:
        branch = self.current()
        if branch is None:
            return
        self.remove_request = True
        self.remove_name = branch.name
        self.accept()

    def update_buttons(self) -> None:
        """Wunsch aus dem Test von 5f: Beim Haupt-Branch gibt es kein "In main übernehmen …" und
        kein "Umbenennen …", beim aktuellen und beim Haupt-Branch kein "Löschen …". Die Knöpfe
        verschwinden dann, statt ausgegraut zu sein, weil Tab ausgegraute Knöpfe überspringt
        und man sonst nicht weiß, warum."""
        row = self.list.currentRow() - self.offset
        branch = self.items[row] if 0 <= row < len(self.items) else None
        main = branch is not None and branch.default
        self.exe_label.setVisible(main and not self.single)
        self.exe_info.setVisible(main and not self.single)
        self.remove_button.setVisible(branch is not None and self.structured
                                      and not branch.default
                                      and (self.single or branch.name in self.folders))
        # Wunsch aus dem Test von 6a: Der Knopf nennt das Ziel, zum Beispiel "Zu main wechseln"
        if self.structured:
            self.switch_button.setVisible(branch is not None and not branch.default
                                          and branch.name not in self.folders
                                          and not self.single)
            if branch is not None:
                self.switch_button.setText(f"&Ordner für {branch.name.replace('&', '&&')} "
                                           "anlegen")
        else:
            self.switch_button.setVisible(branch is not None and not branch.current)
            if branch is not None:
                self.switch_button.setText(f"Zu {branch.name.replace('&', '&&')} &wechseln")
        if branch is not None and not branch.local:
            # Wunsch des Nutzers (02.10.2026): nur auf GitHub heißt das Holen "Herunterladen"
            self.switch_button.setVisible(not self.single)
            self.switch_button.setText("&Herunterladen")
        main = self.main.replace("&", "&&")
        if branch is not None and not branch.default:
            state = (f"{count(branch.ahead_main, 'Commit', 'Commits')} offen"
                     if branch.ahead_main else "alles aktuell")
            self.merge_button.setText(f"In &{main} übernehmen …, {state}")
        self.merge_button.setVisible(branch is not None and not branch.default
                                     and branch.local)
        self.rename_button.setVisible(branch is not None and not branch.default)
        self.delete_button.setVisible(branch is not None and not branch.default
                                      and (not branch.current or self.structured))

    def reload(self, select: str = "") -> None:
        try:
            self.all_items = branches.list_branches(self.code_dir)
        except CockpitError as exc:
            show_error(self, "Branches", exc.message, exc.details)
        if self.single:
            self.single_name = select or self.single_name
            self.items = [b for b in self.all_items if b.name == self.single_name]
        else:
            self.items = filtered(self.all_items, self.show_kind)
            if select and select not in [b.name for b in self.items]:
                self.show_kind = ALL                     # der gewählte Branch soll sichtbar bleiben
                self.items = list(self.all_items)
        self.fill(select)
        self.list.setFocus()

    def current(self) -> Branch | None:
        row = self.list.currentRow() - self.offset
        if 0 <= row < len(self.items):
            return self.items[row]
        if not self.on_new_row() and not self.on_show_row():
            announce("Es gibt keinen Branch.")
        return None

    def _current_name(self) -> str:
        return next((b.name for b in self.all_items if b.current), "")

    # -- Wechseln ----------------------------------------------------------------------------
    def switch_current(self) -> None:
        branch = self.current()
        if branch is None:
            return
        if self.structured:
            if branch.default:
                announce(f"{branch.name} liegt im Ordner Code\\{self.code_dir.name}.")
            elif branch.name in self.folders:
                announce(f"{branch.name} hat schon einen Ordner: "
                         f"Code\\{self.folders[branch.name]}.")
            else:
                self.open_request = branch.name
                self.accept()
            return
        if branch.current:
            announce(f"Sie sind schon auf {branch.name}.")
            return
        here = self._current_name() or "dem aktuellen Stand"
        changes = sync.changes(self.code_dir)
        stash = False
        if changes:
            text = (f"Sie haben Änderungen ohne Commit: {changes.summary()}. Beiseitelegen: Die "
                    f"Änderungen bleiben bei {here}. Wenn Sie zurückwechseln, bietet das Cockpit "
                    f"an, sie zurückzuholen. Mitnehmen: Die Änderungen kommen mit nach "
                    f"{branch.name}.")
            choice = ask_buttons(self, "Branch wechseln", text,
                                 ["Beiseitelegen und wechseln", "Mitnehmen und wechseln",
                                  "Abbrechen"], default=2, escape=2)
            if choice == 2:
                return
            stash = choice == 0
        try:
            if stash:
                branches.stash_push(self.code_dir, self.project.name)
                self.changed = True
            branches.switch(self.code_dir, branch.name)
        except CockpitError as exc:
            if stash:
                exc = CockpitError(f"{exc.message} Ihre Änderungen liegen beiseitegelegt und "
                                   "lassen sich über „Beiseitegelegte Änderungen“ zurückholen.",
                                   exc.details)
            show_error(self, "Branch wechseln", exc.message, exc.details)
            self.reload(branch.name)
            return
        self.changed = True
        self.reload(branch.name)
        announce(f"Gewechselt zu {branch.name}.")
        self.offer_restore(branch.name)

    def offer_restore(self, name: str) -> None:
        """Gibt es für diesen Branch beiseitegelegte Änderungen, das Zurückholen anbieten."""
        stash = branches.stash_for_branch(self.code_dir, name)
        if stash is None or sync.changes(self.code_dir):
            return
        when = f" am {stash.date:%d.%m.%Y um %H:%M}" if stash.date else ""
        if not confirm(self, "Beiseitegelegte Änderungen",
                       f"Auf {name} haben Sie{when} Änderungen beiseitegelegt: "
                       f"{count(len(stash.files), 'Datei', 'Dateien')}. Jetzt zurückholen?",
                       yes="Zurückholen", no="Später"):
            return
        try:
            branches.stash_restore(self.code_dir, stash)
        except CockpitError as exc:
            show_error(self, "Zurückholen", exc.message, exc.details)
            return
        self.reload(name)
        announce("Änderungen zurückgeholt.")

    # -- Neuer Branch ------------------------------------------------------------------------
    def new_branch(self) -> None:
        if self.structured:
            dialog = BranchNameDialog("Neuer Branch", f"Er bekommt einen eigenen Ordner im Ordner "
                                      f"Code und beginnt beim neuesten Stand von {self.main} auf "
                                      f"{self.platform_name}.", self.code_dir, parent=self)
            if dialog.exec():
                self.new_request = dialog.name
                self.accept()
            return
        here = self._current_name() or "dem aktuellen Stand"
        dialog = BranchNameDialog("Neuer Branch", f"Er beginnt bei {here}. Ihre Änderungen ohne "
                                  "Commit kommen mit.", self.code_dir, parent=self)
        if not dialog.exec():
            return
        try:
            branches.create(self.code_dir, dialog.name)
        except CockpitError as exc:
            show_error(self, "Neuer Branch", exc.message, exc.details)
            return
        self.changed = True
        self.reload(dialog.name)
        announce(f"Branch {dialog.name} angelegt. Sie sind jetzt auf {dialog.name}.")

    # -- In den Haupt-Branch übernehmen -----------------------------------------------------
    def merge_current(self) -> None:
        branch = self.current()
        if branch is None:
            return
        main = self.main
        title = f"In {main} übernehmen"
        if branch.default:
            show_error(self, title, f"{main} ist selbst der Haupt-Branch. Wählen Sie den Branch, "
                       f"dessen Änderungen in {main} kommen sollen.")
            return
        if not branch.ahead_main:
            announce(f"{branch.name} hat keine Commits, die in {main} fehlen.")
            return
        source = branch.name if branch.local else f"origin/{branch.name}"
        # Nur Änderungen, die beim Übernehmen stören. Die Meldung nennt Ordner und Dateien
        # (Rückmeldung zum Test von 8e: gemeint war main, nicht der Branch).
        blocking = sync.blocking_merge(self.code_dir, source)
        if blocking:
            names = ", ".join(blocking[:3]) + (" und weitere" if len(blocking) > 3 else "")
            show_error(self, title, f"In {main} (Ordner {self.code_dir.name}) gibt es "
                       f"Änderungen ohne Commit, die beim Übernehmen stören: {names}. Laden Sie "
                       f"sie in {main} zuerst hoch oder legen Sie sie beiseite.")
            return
        # Mit Branch-Ordnern ist main immer der eigene Ordner, gewechselt wird nie (10f)
        switch = "" if self.structured or self._current_name() == main \
            else f"Das Cockpit wechselt zu {main}. "
        text = (f"{switch}Die {count(branch.ahead_main, 'Commit', 'Commits')} aus {branch.name} "
                f"kommen in {main}, wie git merge. Vorher kommen die betroffenen Dateien als "
                f"Sicherheitskopie in den Ordner backups. Danach ist {main} noch nicht "
                "hochgeladen. Übernehmen?")
        if not confirm(self, title, text, yes="Übernehmen", no="Abbrechen"):
            return
        try:
            if switch:
                branches.switch(self.code_dir, main)
                self.changed = True
            outcome = branches.merge_into_current(self.code_dir, self.project.name, source)
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            self.reload(branch.name)
            return
        self.changed = True
        if outcome.kind is not ConflictKind.NONE:
            self.resolve(outcome.kind, branch.name)
            return
        self.reload(main)
        announce(f"{branch.name} ist in {main} übernommen. {main} ist noch nicht hochgeladen.")

    def resolve(self, kind: ConflictKind, name: str) -> None:
        announce(f"Konflikte beim Übernehmen von {name}.")
        dialog = sync_dialogs.ConflictDialog(self.code_dir, kind, f"Branch {name}", self)
        try:
            if dialog.exec():
                sync.finish(self.code_dir, kind)
                announce(f"{name} ist in {self.main} übernommen. {self.main} ist noch nicht "
                         "hochgeladen.")
            else:
                sync.abort(self.code_dir, kind)
                announce(f"Übernehmen abgebrochen. {self.main} ist wie vorher.")
        except CockpitError as exc:
            show_error(self, "Übernehmen", exc.message, exc.details)
        self.reload(self.main)

    # -- Umbenennen --------------------------------------------------------------------------
    def rename_current(self) -> None:
        branch = self.current()
        if branch is None:
            return
        if branch.default:
            show_error(self, "Umbenennen", f"{branch.name} ist der Haupt-Branch. Er lässt sich "
                       "hier nicht umbenennen.")
            return
        dialog = BranchNameDialog(f"{branch.name} umbenennen", "", self.code_dir, branch.name,
                                  self)
        if not dialog.exec():
            return
        new = dialog.name
        if branch.remote and not confirm(
                self, "Umbenennen",
                f"{branch.name} gibt es auch auf {self.platform_name}. Das Cockpit lädt ihn dort "
                f"unter dem Namen {new} hoch und löscht den alten Namen. Offene Pull Requests zum "
                "alten Namen werden dabei geschlossen. Umbenennen?",
                yes="Umbenennen", no="Abbrechen"):
            return
        try:
            if branch.local:
                branches.rename_local(self.code_dir, branch.name, new)
        except CockpitError as exc:
            show_error(self, "Umbenennen", exc.message, exc.details)
            return
        self.changed = True
        if not branch.remote:
            self.reload(new)
            announce(f"{branch.name} heißt jetzt {new}.")
            return
        code_dir, env, old, local = self.code_dir, self.env, branch.name, branch.local

        def done(_value) -> None:
            self.reload(new)
            announce(f"{old} heißt jetzt {new}, auch auf {self.platform_name}.")

        self.worker.run(lambda: branches.rename_remote(code_dir, old, new, env, local), done,
                        speak="Wird umbenannt.")

    # -- Löschen -----------------------------------------------------------------------------
    def delete_current(self) -> None:
        branch = self.current()
        if branch is None:
            return
        title = "Branch löschen"
        if self.structured and branch.name in self.folders and not branch.default:
            self.delete_request = branch.name       # mit Ordner, erledigt WorktreeActions
            self.accept()
            return
        if branch.current or branch.default:
            what = "der aktuelle Branch. Wechseln Sie zuerst zu einem anderen" if branch.current \
                else "der Haupt-Branch. Er lässt sich hier nicht löschen"
            show_error(self, title, f"{branch.name} ist {what}.")
            return
        local = remote = False
        if branch.local and branch.remote:
            choice = ask_buttons(self, title,
                                 f"{branch.name} gibt es auf diesem Rechner und auf "
                                 f"{self.platform_name}. Wo soll er gelöscht werden?",
                                 ["Nur auf diesem Rechner", f"Nur auf {self.platform_name}",
                                  f"Hier und auf {self.platform_name}", "Abbrechen"],
                                 default=3, escape=3)
            if choice == 3:
                return
            local, remote = choice in (0, 2), choice in (1, 2)
        elif branch.local:
            extra = ""
            lost = branches.unmerged(self.code_dir, branch.name)
            if lost:
                extra = (f" Er enthält {count(lost, 'Commit', 'Commits')}, die es sonst nirgends "
                         "gibt. Das Cockpit hebt sie unter einem Sicherungsverweis auf, sie sind "
                         "also nicht verloren.")
            if not confirm(self, title, f"{branch.name} wird auf diesem Rechner gelöscht.{extra}"
                           " Löschen?", yes="Löschen", no="Abbrechen"):
                return
            local = True
        else:
            if not confirm(self, title, f"{branch.name} wird auf {self.platform_name} gelöscht. "
                           "Auf diesem Rechner gibt es ihn nicht. Löschen?", yes="Löschen",
                           no="Abbrechen"):
                return
            remote = True
        try:
            if local:
                branches.delete_local(self.code_dir, branch.name)
        except CockpitError as exc:
            show_error(self, title, exc.message, exc.details)
            return
        self.changed = True
        if not remote:
            self.reload()
            announce(f"{branch.name} gelöscht.")
            return
        code_dir, env, name = self.code_dir, self.env, branch.name
        where = "auch auf" if local else "auf"

        def done(_value) -> None:
            self.reload(name if not local else "")
            announce(f"{name} gelöscht, {where} {self.platform_name}.")

        self.worker.run(lambda: branches.delete_remote(code_dir, name, env), done,
                        speak="Wird gelöscht.")


class BranchNameDialog(FocusDialog):
    """Name für einen neuen oder umbenannten Branch. Prüft den Namen wie Git."""

    def __init__(self, title: str, hint: str, code_dir, current: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.code_dir = code_dir
        self.name = ""
        self.setWindowTitle(title)
        self.edit = QLineEdit(current)
        label = label_for(self.edit, "&Name des Branches:")
        ok = QPushButton("OK")
        ok.setDefault(True)
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.edit)
        if hint:
            info = QListWidget()
            name_widget(info, "Hinweis")
            info.addItem(hint)
            info.setMaximumHeight(60)
            layout.addWidget(info)
        layout.addLayout(button_row(None, ok, cancel))
        self.resize(480, 180)
        self.initial_focus_widget = self.edit

    def check(self) -> None:
        name = self.edit.text().strip()
        problem = branches.name_problem(self.code_dir, name)
        if problem:
            show_error(self, self.windowTitle(), problem)
            self.edit.setFocus()
            return
        self.name = name
        self.accept()


class StashDialog(FocusDialog):
    """Beiseitegelegte Änderungen. changed: Dateien oder Branch haben sich geändert."""

    def __init__(self, project: "Project", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project = project
        self.code_dir = project.code_dir
        self.items: list[Stash] = []
        self.changed = False
        self.list = QListWidget()
        name_widget(self.list, "Beiseitegelegte Änderungen")
        self.list.installEventFilter(self)
        restore = QPushButton("&Zurückholen …")
        restore.clicked.connect(self.restore_current)
        as_branch = QPushButton("Als neuen &Branch zurückholen …")
        as_branch.clicked.connect(self.branch_current)
        delete = QPushButton("&Löschen …")
        delete.clicked.connect(self.delete_current)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(button_row(restore, as_branch, delete, None, close))
        self.resize(720, 360)
        self.initial_focus_widget = self.list
        self.fill()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            return True
        return super().eventFilter(watched, event)

    def fill(self) -> None:
        row = max(0, self.list.currentRow())
        self.items = branches.stashes(self.code_dir)
        self.setWindowTitle(f"Beiseitegelegte Änderungen von {self.project.name}: "
                            f"{count(len(self.items), 'Eintrag', 'Einträge')}")
        self.list.clear()
        self.list.addItems([s.line() for s in self.items] or ["Nichts beiseitegelegt."])
        self.list.setCurrentRow(min(row, self.list.count() - 1))

    def current(self) -> Stash | None:
        row = self.list.currentRow()
        if 0 <= row < len(self.items):
            return self.items[row]
        announce("Es ist nichts beiseitegelegt.")
        return None

    def _done(self, text: str) -> None:
        self.changed = True
        self.fill()
        self.list.setFocus()
        announce(text)

    def restore_current(self) -> None:
        stash = self.current()
        if stash is None:
            return
        where = f" Sie wurden auf {stash.branch} beiseitegelegt." if stash.branch else ""
        if not confirm(self, "Zurückholen",
                       f"Die Änderungen kommen zurück in Ihre Dateien: "
                       f"{count(len(stash.files), 'Datei', 'Dateien')}.{where} Zurückholen?",
                       yes="Zurückholen", no="Abbrechen"):
            return
        try:
            branches.stash_restore(self.code_dir, stash)
        except CockpitError as exc:
            show_error(self, "Zurückholen", exc.message, exc.details)
            return
        self._done("Änderungen zurückgeholt.")

    def branch_current(self) -> None:
        stash = self.current()
        if stash is None:
            return
        suggestion = f"beiseitegelegt-{stash.date:%Y-%m-%d}" if stash.date else "beiseitegelegt"
        dialog = BranchNameDialog("Als neuen Branch zurückholen",
                                  "Der Branch beginnt dort, wo die Änderungen beiseitegelegt "
                                  "wurden. So passen sie immer. Sie wechseln dabei zu ihm.",
                                  self.code_dir, suggestion, self)
        if not dialog.exec():
            return
        try:
            branches.stash_to_branch(self.code_dir, stash, dialog.name)
        except CockpitError as exc:
            show_error(self, "Als neuen Branch zurückholen", exc.message, exc.details)
            return
        self._done(f"Zurückgeholt in den neuen Branch {dialog.name}. Sie sind jetzt dort.")

    def delete_current(self) -> None:
        stash = self.current()
        if stash is None:
            return
        if not confirm(self, "Löschen",
                       f"Die beiseitegelegten Änderungen vom "
                       f"{stash.date:%d.%m.%Y %H:%M} werden gelöscht. Ihre Dateien kommen vorher "
                       "als Sicherheitskopie in den Ordner backups. Löschen?"
                       if stash.date else "Die beiseitegelegten Änderungen werden gelöscht. "
                       "Ihre Dateien kommen vorher als Sicherheitskopie in den Ordner backups. "
                       "Löschen?", yes="Löschen", no="Abbrechen"):
            return
        try:
            branches.stash_drop(self.code_dir, self.project.name, stash)
        except CockpitError as exc:
            show_error(self, "Löschen", exc.message, exc.details)
            return
        self._done("Beiseitegelegte Änderungen gelöscht.")
