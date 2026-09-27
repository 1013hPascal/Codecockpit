"""Links, Repository verwalten und Mitarbeiter (Konzept 9.5, Teilschritt 5e).

LinksDialog: Projektseite und README als Liste. Enter kopiert den markierten Link.
ManageRepoDialog: Angaben zum Repository, dazu "Öffentlich machen …" oder "Privat machen …",
"Mitarbeiter …", "Archivieren …" oder "Archivierung aufheben …" und "Löschen …".
CollaboratorsDialog: Mitarbeiter und offene Einladungen. "Einladen …" und "Entfernen …".

Alles, was mit der Plattform spricht, läuft im Hintergrund. Rückfragen haben die sichere Antwort
als Vorgabe. Löschen fragt zweimal: erst mit dem Angebot, stattdessen zu archivieren, dann muss der
Name des Repositories eingetippt werden. Fehlt dem Zugang das Recht zum Löschen, holt eine zweite,
kurze Anmeldung im Browser nur dieses Recht (ENTSCHEIDUNGEN.md). Der Zugang daraus wird nicht
gespeichert. Das Cockpit führt nie einen force push aus, und der Ordner auf dem Rechner bleibt immer.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QLineEdit, QListWidget,
                               QPushButton, QVBoxLayout, QWidget)

from cockpit.core import repo_admin
from cockpit.core.errors import CockpitError
from cockpit.core.text import count, join_words
from cockpit.platforms.base import (PERMISSION_NAMES, BranchProtection, Capability,
                                    Collaborator, PermissionMissing, RepoInfo,
                                    SupportsBranchProtection, SupportsCollaborators)
from cockpit.ui import browser_login_dialog
from cockpit.ui.announcer import announce
from cockpit.ui.common import (FocusDialog, ask_buttons, confirm, label_for, make_copyable,
                               name_widget)
from cockpit.ui.error_dialog import show_error
from cockpit.ui.tasks import Task

if TYPE_CHECKING:
    from cockpit.core.projects import Project

# Rechte beim Einladen, in dieser Reihenfolge im Auswahlfeld. Vorgabe ist "schreiben".
INVITE_CHOICES = ["read", "write", "admin"]
NAME_MISMATCH = "Der eingetippte Name stimmt nicht. Es wurde nichts gelöscht."


def _is_enter(event) -> bool:
    return event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return,
                                                                    Qt.Key.Key_Enter)


class _Worker:
    """Eine Hintergrund-Aufgabe zur Zeit für ein Fenster. Fehler kommen als Meldung im Fenster."""

    def __init__(self, dialog: QWidget, title: str) -> None:
        self.dialog = dialog
        self.title = title
        self.task: Task | None = None

    @property
    def busy(self) -> bool:
        return self.task is not None

    def run(self, work: Callable[[], object], done: Callable[[object], None],
            speak: str = "") -> None:
        if self.task is not None:
            announce("Das läuft schon.")
            return
        if speak:
            announce(speak)
        task = Task(lambda _task: work(), self.dialog)
        self.task = task

        def on_result(value) -> None:
            self.task = None
            done(value)

        def on_error(message: str, details: str) -> None:
            self.task = None
            announce(message, urgent=True)
            show_error(self.dialog, self.title, message, details)

        task.result.connect(on_result)
        task.error.connect(on_error)
        task.finished.connect(task.deleteLater)
        task.start()

    def wait(self) -> None:
        try:
            if self.task is not None and self.task.isRunning():
                self.task.cancel()
                self.task.wait(10000)          # nie einen laufenden Thread zerstören
        except RuntimeError:
            pass


def _buttons(*widgets) -> QHBoxLayout:
    row = QHBoxLayout()
    for widget in widgets:
        if widget is None:
            row.addStretch(1)
        else:
            row.addWidget(widget)
    return row


# -- Links ------------------------------------------------------------------------------------
class LinksDialog(FocusDialog):
    def __init__(self, project_name: str, links: list[tuple[str, str]],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.links = links
        self.setWindowTitle(f"Links von {project_name}")
        self.list = QListWidget()
        name_widget(self.list, "Links")
        self.list.addItems([f"{label}: {url}" for label, url in links])
        self.list.setCurrentRow(0)
        self.list.itemActivated.connect(lambda _item: self.copy_current())
        copy = QPushButton("&Kopieren")
        copy.clicked.connect(self.copy_current)
        open_button = QPushButton("Im &Browser öffnen")
        open_button.clicked.connect(self.open_current)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(_buttons(copy, open_button, None, close))
        self.resize(640, 260)
        self.initial_focus_widget = self.list

    def current(self) -> tuple[str, str] | None:
        row = self.list.currentRow()
        return self.links[row] if 0 <= row < len(self.links) else None

    def copy_current(self) -> None:
        link = self.current()
        if link is not None:
            QGuiApplication.clipboard().setText(link[1])
            announce(f"Link zu {link[0]} kopiert.")

    def open_current(self) -> None:
        link = self.current()
        if link is not None:
            browser_login_dialog.open_url(link[1])
            announce("Wird im Browser geöffnet.")


# -- Repository verwalten ------------------------------------------------------------------
class ManageRepoDialog(FocusDialog):
    """Nach dem Schließen: changed (Sichtbarkeit oder Archiv geändert), deleted (gelöscht) und
    removed (danach auch aus der Liste entfernt)."""

    def __init__(self, services, project: "Project", platform, info: RepoInfo,
                 platform_name: str = "GitHub", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.services = services
        self.project = project
        self.platform = platform
        self.info = info
        self.ref = info.ref
        self.platform_name = platform_name
        self.changed = self.deleted = self.removed = False
        self.worker = _Worker(self, "Repository verwalten")
        self.setWindowTitle(f"Repository verwalten: {info.ref.name}")
        self.list = QListWidget()
        name_widget(self.list, "Angaben")
        make_copyable(self.list)
        self.list.installEventFilter(self)
        self.visibility_button = QPushButton()
        self.visibility_button.clicked.connect(self.change_visibility)
        self.people_button = QPushButton("&Mitarbeiter …")
        self.people_button.clicked.connect(self.show_collaborators)
        self.rules_button = QPushButton(
            f"&Schutzregeln für {info.default_branch.replace('&', '&&')} …")
        self.rules_button.clicked.connect(self.show_protection)
        self.archive_button = QPushButton()
        self.archive_button.clicked.connect(self.change_archive)
        self.delete_button = QPushButton("&Löschen …")
        self.delete_button.clicked.connect(self.delete)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(_buttons(self.visibility_button, self.people_button,
                                  self.rules_button, self.archive_button, self.delete_button,
                                  None, close))
        self.resize(720, 300)
        self.initial_focus_widget = self.list
        self.fill()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            return True
        return super().eventFilter(watched, event)

    def fill(self) -> None:
        info = self.info
        lines = [f"{info.ref.owner}/{info.ref.name} auf {self.platform_name}",
                 "Öffentlich, jeder im Internet kann den Code sehen" if not info.private
                 else "Privat, nur Sie und Ihre Mitarbeiter sehen den Code"]
        if info.archived:
            lines.append("Archiviert, schreibgeschützt")
        lines.append(f"Adresse: {info.web_url}")
        self.list.clear()
        self.list.addItems(lines)
        self.list.setCurrentRow(0)
        self.visibility_button.setText("Ö&ffentlich machen …" if info.private
                                       else "&Privat machen …")
        self.archive_button.setText("Archivierung &aufheben …" if info.archived
                                    else "&Archivieren …")

    def _update(self, **changes) -> None:
        self.info = RepoInfo(**{**self.info.__dict__, **changes})
        self.changed = True
        self.fill()

    def done(self, code: int) -> None:
        self.worker.wait()
        super().done(code)

    # -- Sichtbarkeit ------------------------------------------------------------------------
    def change_visibility(self) -> None:
        name = self.ref.name
        if not self.info.private:
            text = (f"{name} wird privat. Danach sehen nur Sie und Ihre Mitarbeiter den Code. "
                    f"Sterne und Beobachter von anderen gehen dabei auf {self.platform_name} "
                    "verloren. Privat machen?")
            if confirm(self, "Privat machen", text, yes="Privat machen", no="Abbrechen"):
                self._set_private(True)
            return
        code_dir = self.project.code_dir
        self.worker.run(lambda: repo_admin.public_scan(code_dir), self._public_checked,
                        speak="Sicherheitsprüfung läuft.")

    def _public_checked(self, report) -> None:
        name = self.ref.name
        if report.blocking:
            texts = [f.text for f in report.blocking]
            show_error(self, "Öffentlich machen",
                       f"Die Sicherheitsprüfung hat {count(len(texts), 'Geheimnis', 'Geheimnisse')}"
                       f" gefunden, zum Beispiel: {texts[0]}. Solange es in den Dateien oder im "
                       f"Verlauf steht, macht das Cockpit {name} nicht öffentlich. Es wurde "
                       "nichts geändert. Ändern Sie das Passwort oder den Schlüssel beim "
                       "Anbieter, dann ist das alte Geheimnis wertlos.", "\n".join(texts))
            return
        warning = ""
        if report.warnings:
            texts = [f.text for f in report.warnings]
            warning = (f"Die Sicherheitsprüfung warnt: {join_words(texts[:3])}"
                       f"{' und weitere' if len(texts) > 3 else ''}. ")
        text = (f"{warning}{name} wird öffentlich. Jeder im Internet kann danach den Code und den "
                "ganzen Verlauf sehen. Öffentlich machen?")
        yes = "Trotzdem öffentlich machen" if warning else "Öffentlich machen"
        if confirm(self, "Öffentlich machen", text, yes=yes, no="Abbrechen"):
            self._set_private(False)

    def _set_private(self, private: bool) -> None:
        platform, ref = self.platform, self.ref

        def done(_value) -> None:
            self.services.remote_repos.set_private(self._address(), private)
            self._update(private=private)
            self.visibility_button.setFocus()
            announce(f"{ref.name} ist jetzt {'privat' if private else 'öffentlich'}.")

        self.worker.run(lambda: platform.set_visibility(ref, private), done)

    def _address(self):
        from cockpit.core.git import RemoteAddress
        host = self.project.remote.host if self.project.remote else ""
        return RemoteAddress(host, self.ref.owner, self.ref.name)

    # -- Mitarbeiter -------------------------------------------------------------------------
    def show_collaborators(self) -> None:
        if not isinstance(self.platform, SupportsCollaborators):
            show_error(self, "Mitarbeiter", f"{self.platform_name} kennt keine Mitarbeiter.")
            return
        CollaboratorsDialog(self.platform, self.ref, self.platform_name, self).exec()
        self.people_button.setFocus()

    # -- Schutzregeln (Phase 6c) ------------------------------------------------------------------
    def show_protection(self) -> None:
        branch = self.info.default_branch
        if not isinstance(self.platform, SupportsBranchProtection):
            show_error(self, "Schutzregeln", f"{self.platform_name} kennt keine Schutzregeln.")
            return
        platform, ref = self.platform, self.ref

        def edit(rules) -> None:
            dialog = ProtectionDialog(branch, rules, self)
            if not dialog.exec():
                self.rules_button.setFocus()
                return
            new = dialog.rules
            text = protection_summary(branch, new)
            if not confirm(self, "Schutzregeln", f"{text} Speichern?", yes="Speichern",
                           no="Abbrechen"):
                self.rules_button.setFocus()
                return

            def saved(_value) -> None:
                self.rules_button.setFocus()
                announce(f"Schutzregeln für {branch} gespeichert." if not new.empty
                         else f"{branch} ist nicht mehr geschützt.")

            self.worker.run(lambda: platform.set_branch_protection(ref, branch, new), saved)

        self.worker.run(lambda: platform.branch_protection(ref, branch), edit,
                        speak="Schutzregeln werden abgefragt.")

    # -- Archivieren -------------------------------------------------------------------------
    def change_archive(self) -> None:
        name = self.ref.name
        if self.info.archived:
            text = (f"{name} ist danach wieder beschreibbar. Sie und Ihre Mitarbeiter können wieder "
                    "hochladen. Archivierung aufheben?")
            if confirm(self, "Archivierung aufheben", text, yes="Archivierung aufheben",
                       no="Abbrechen"):
                self._set_archived(False)
            return
        if self.archive():
            return

    def archive(self) -> bool:
        """Mit Rückfrage archivieren. True, wenn bestätigt."""
        text = (f"{self.ref.name} wird schreibgeschützt. Niemand kann mehr hochladen, auch Sie "
                f"nicht. Das Repository bleibt auf {self.platform_name} erhalten, und die "
                "Archivierung lässt sich jederzeit wieder aufheben. Archivieren?")
        if not confirm(self, "Archivieren", text, yes="Archivieren", no="Abbrechen"):
            return False
        self._set_archived(True)
        return True

    def _set_archived(self, archived: bool) -> None:
        platform, ref = self.platform, self.ref

        def work() -> None:
            (platform.archive if archived else platform.unarchive)(ref)

        def done(_value) -> None:
            self._update(archived=archived)
            self.archive_button.setFocus()
            announce(f"{ref.name} ist archiviert." if archived
                     else f"Archivierung von {ref.name} aufgehoben.")

        self.worker.run(work, done)

    # -- Löschen -----------------------------------------------------------------------------
    def delete(self) -> None:
        name = self.ref.name
        text = (f"Löschen lässt sich nicht rückgängig machen. {name} ist danach mit Verlauf, "
                f"Issues und allen Einstellungen auf {self.platform_name} weg. Der Ordner auf "
                "Ihrem Rechner bleibt immer erhalten.")
        options = ["Weiter zum Löschen …"]
        if not self.info.archived:
            text += (" Sanfter ist Archivieren: Das Repository wird schreibgeschützt und bleibt "
                     "erhalten.")
            options.append("Stattdessen archivieren …")
        options.append("Abbrechen")
        cancel = len(options) - 1
        choice = ask_buttons(self, "Löschen", text, options, default=cancel, escape=cancel)
        if choice == cancel:
            return
        if choice == 1:
            self.archive()
            return
        dialog = TypeNameDialog(name, self)
        if not dialog.exec():
            return
        allowed = self.platform.permissions().get(Capability.DELETE_REPO)
        if allowed is not None and not allowed.available:
            self._delete_with_second_login()
            return
        platform, ref = self.platform, self.ref

        def work() -> bool:
            try:
                platform.delete(ref)
            except PermissionMissing:
                return False                      # Recht fehlt: zweite Anmeldung anbieten
            return True

        def done(ok: bool) -> None:
            if ok:
                self._deleted()
            else:
                self._delete_with_second_login()

        self.worker.run(work, done, speak="Wird gelöscht.")

    def _delete_with_second_login(self) -> None:
        cls = type(self.platform)
        url = getattr(self.platform, "url", "")
        scopes = getattr(cls, "delete_login_scopes", "")
        available = getattr(cls, "browser_login_available", lambda url="": False)(url)
        name = self.ref.name
        if not scopes or not available:
            show_error(self, "Löschen",
                       f"Dem Zugang fehlt das Recht zum Löschen (delete_repo). Es wurde nichts "
                       f"gelöscht. Sie können in der Kontenverwaltung einen Token mit diesem Recht "
                       f"eintragen oder {name} auf {self.platform_name} selbst löschen.")
            page = self.platform.settings_url(self.ref)
            if page and confirm(self, "Löschen", "Einstellungen des Repositories im Browser "
                                "öffnen? Dort steht Löschen ganz unten.", yes="Im Browser öffnen",
                                no="Abbrechen"):
                browser_login_dialog.open_url(page)
            return
        text = (f"Zum Löschen braucht das Cockpit ein zusätzliches Recht von {self.platform_name}. "
                "Dafür melden Sie sich im Browser noch einmal kurz an und bestätigen das Recht zum "
                "Löschen. Der Zugang wird nur für dieses eine Löschen benutzt und nicht "
                "gespeichert. Weiter?")
        if not confirm(self, "Löschen", text, yes="Im Browser bestätigen …", no="Abbrechen"):
            return
        login = browser_login_dialog.BrowserLoginDialog(
            cls, url, self, scopes=scopes, title="Recht zum Löschen holen",
            confirm_line=f"Auf der nächsten Seite fragt {self.platform_name}, ob CodeCockpit "
                         "Repositories löschen darf. Bestätigen Sie mit Authorize.")
        if not login.exec() or login.token is None:
            return
        own = (getattr(self.platform, "username", "") or "").lower()
        if own and login.username.lower() != own:
            show_error(self, "Löschen", f"Sie haben sich als {login.username} angemeldet, das "
                       f"Konto im Cockpit ist {own}. Es wurde nichts gelöscht.")
            return
        temporary = cls(url, login.token)          # nur für dieses Löschen, nicht gespeichert
        login.token = None
        ref = self.ref

        def done(_value) -> None:
            temporary.token = None
            self._deleted()

        self.worker.run(lambda: temporary.delete(ref), done, speak="Wird gelöscht.")

    def _deleted(self) -> None:
        self.deleted = True
        self.services.remote_repos.forget(self._address())
        name = self.ref.name
        announce(f"{name} ist auf {self.platform_name} gelöscht.")
        folder = self.project.code_dir
        text = (f"{name} ist auf {self.platform_name} gelöscht. Der Ordner auf Ihrem Rechner ist "
                f"unverändert: {folder}. Nur lokal behalten: Das Projekt bleibt in der Liste und "
                f"heißt „noch nicht auf {self.platform_name}“. Aus der Liste entfernen: Das "
                "Cockpit vergisst das Projekt, der Ordner bleibt trotzdem.")
        choice = ask_buttons(self, "Gelöscht", text, ["Nur lokal behalten",
                                                      "Aus der Liste entfernen"],
                             default=0, escape=0)
        try:
            if choice == 1:
                self.services.projects.remove(self.project.id)
                self.removed = True
            else:
                repo_admin.disconnect(self.project.code_dir)
                self.services.projects.set_remote(self.project, None, None)
        except CockpitError as exc:
            show_error(self, "Gelöscht", exc.message, exc.details)
        self.accept()


class TypeNameDialog(FocusDialog):
    """Zur Bestätigung den Namen des Repositories eintippen (Konzept 9.5)."""

    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.name = name
        self.setWindowTitle(f"{name} endgültig löschen")
        self.edit = QLineEdit()
        label = label_for(self.edit, f"Zur Bestätigung den &Namen eintippen: {name}")
        self.ok_button = QPushButton("Endgültig löschen")
        self.ok_button.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.setDefault(True)
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.edit)
        layout.addLayout(_buttons(None, self.ok_button, cancel))
        self.initial_focus_widget = self.edit

    def check(self) -> None:
        if self.edit.text().strip() != self.name:
            show_error(self, self.windowTitle(), NAME_MISMATCH)
            self.edit.setFocus()
            return
        self.accept()


# -- Mitarbeiter ---------------------------------------------------------------------------
def collaborator_line(person: Collaborator) -> str:
    right = PERMISSION_NAMES.get(person.permission, person.permission)
    return f"{person.login}, eingeladen, {right}" if person.invited else f"{person.login}, {right}"


class CollaboratorsDialog(FocusDialog):
    """Wunsch aus dem Test von 5e: Oben in der Liste steht "Einladen …", darunter die Mitarbeiter.
    Tab führt zum Recht des markierten Mitarbeiters, dann zu "Zugriffsrecht ändern" und
    "Entfernen …". Enter auf "Einladen …" lädt ein, Enter auf einem Mitarbeiter tut nichts."""

    INVITE_ROW = "Einladen …"

    def __init__(self, platform, ref, platform_name: str = "GitHub",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.platform = platform
        self.ref = ref
        self.platform_name = platform_name
        self.people: list[Collaborator] = []
        self.worker = _Worker(self, "Mitarbeiter")
        self.setWindowTitle(f"Mitarbeiter von {ref.name}")
        self.list = QListWidget()
        name_widget(self.list, "Mitarbeiter")
        self.list.addItems([self.INVITE_ROW, "Wird geladen …"])
        self.list.setCurrentRow(0)
        self.list.installEventFilter(self)
        self.list.currentRowChanged.connect(lambda _row: self.show_right())
        self.rights = QComboBox()
        name_widget(self.rights, "Recht")
        self.change_button = QPushButton("Zugriffsrecht ä&ndern")
        self.change_button.clicked.connect(self.change_right)
        self.remove_button = QPushButton("&Entfernen …")
        self.remove_button.clicked.connect(self.remove_current)
        close = QPushButton("Schließen")
        close.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(_buttons(self.rights, self.change_button, self.remove_button, None,
                                  close))
        self.resize(560, 360)
        self.initial_focus_widget = self.list
        self.show_right()
        self.load()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.list and _is_enter(event):
            if self.list.currentRow() == 0:
                self.invite()
            return True
        return super().eventFilter(watched, event)

    def done(self, code: int) -> None:
        self.worker.wait()
        super().done(code)

    def load(self, then: str = "", select: str = "") -> None:
        platform, ref = self.platform, self.ref

        def done(people) -> None:
            self.fill(people, select)
            if then:
                announce(then)

        self.worker.run(lambda: platform.collaborators(ref), done)

    def fill(self, people: list[Collaborator], select: str = "") -> None:
        row = max(0, self.list.currentRow())
        self.people = people
        self.setWindowTitle(f"Mitarbeiter von {self.ref.name}: "
                            f"{count(len(people), 'Eintrag', 'Einträge')}")
        self.list.clear()
        self.list.addItem(self.INVITE_ROW)
        self.list.addItems([collaborator_line(p) for p in people] or ["Noch keine Mitarbeiter."])
        logins = [p.login.lower() for p in people]
        if select.lower() in logins:
            row = logins.index(select.lower()) + 1
        self.list.setCurrentRow(min(row, self.list.count() - 1))
        self.show_right()

    def current(self) -> Collaborator | None:
        row = self.list.currentRow() - 1               # Zeile 0 ist "Einladen …"
        return self.people[row] if 0 <= row < len(self.people) else None

    def show_right(self) -> None:
        """Das Feld Recht zeigt das Recht des markierten Mitarbeiters."""
        person = self.current()
        choices = list(INVITE_CHOICES)
        if person is not None and person.permission not in choices:
            choices.append(person.permission)          # zum Beispiel "pflegen" von GitHub
        self.rights.blockSignals(True)
        self.rights.clear()
        self.rights.addItems([PERMISSION_NAMES.get(c, c) for c in choices])
        self.rights.setCurrentIndex(choices.index(person.permission) if person else
                                    choices.index("write"))
        self.rights.blockSignals(False)
        self._choices = choices

    def _need_person(self) -> Collaborator | None:
        person = self.current()
        if person is None:
            announce("Bitte wählen Sie in der Liste zuerst einen Mitarbeiter.")
            self.list.setFocus()
        return person

    def invite(self) -> None:
        dialog = InviteDialog(self.platform_name, self)
        if not dialog.exec():
            return
        login, permission = dialog.login, dialog.permission
        platform, ref = self.platform, self.ref

        def done(invited: bool) -> None:
            self.list.setFocus()
            self.load(f"Einladung an {login} verschickt." if invited
                      else f"{login} ist jetzt Mitarbeiter.", select=login)

        self.worker.run(lambda: platform.invite(ref, login, permission), done)

    def change_right(self) -> None:
        person = self._need_person()
        if person is None:
            return
        permission = self._choices[self.rights.currentIndex()]
        name = PERMISSION_NAMES.get(permission, permission)
        if permission == person.permission:
            announce(f"{person.login} hat schon das Recht {name}.")
            return
        platform, ref = self.platform, self.ref

        def done(_value) -> None:
            self.load(f"Recht von {person.login}: {name}.", select=person.login)
            self.change_button.setFocus()

        self.worker.run(lambda: platform.change_permission(ref, person, permission), done)

    def remove_current(self) -> None:
        person = self._need_person()
        if person is None:
            return
        platform, ref = self.platform, self.ref
        if person.invited:
            if not confirm(self, "Einladung zurückziehen",
                           f"Die Einladung an {person.login} wird zurückgezogen. Zurückziehen?",
                           yes="Zurückziehen", no="Abbrechen"):
                return
            work = lambda: platform.cancel_invitation(ref, person.invitation_id)  # noqa: E731
            said = f"Einladung an {person.login} zurückgezogen."
        else:
            if not confirm(self, "Mitarbeiter entfernen",
                           f"{person.login} wird als Mitarbeiter entfernt und hat danach keinen "
                           f"Zugriff mehr, solange {ref.name} privat ist. Entfernen?",
                           yes="Entfernen", no="Abbrechen"):
                return
            work = lambda: platform.remove_collaborator(ref, person.login)  # noqa: E731
            said = f"{person.login} entfernt."
        self.worker.run(work, lambda _value: (self.list.setFocus(), self.load(said)))


class InviteDialog(FocusDialog):
    def __init__(self, platform_name: str = "GitHub", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.login = ""
        self.permission = "write"
        self.setWindowTitle("Mitarbeiter einladen")
        self.edit = QLineEdit()
        edit_label = label_for(self.edit, f"&Benutzername auf {platform_name}:")
        self.rights = QComboBox()
        rights_label = label_for(self.rights, "&Recht:")
        self.rights.addItems([PERMISSION_NAMES[p] for p in INVITE_CHOICES])
        self.rights.setCurrentIndex(INVITE_CHOICES.index("write"))
        ok = QPushButton("&Einladen")
        ok.setDefault(True)
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        for widget in (edit_label, self.edit, rights_label, self.rights):
            layout.addWidget(widget)
        layout.addLayout(_buttons(None, ok, cancel))
        self.initial_focus_widget = self.edit

    def check(self) -> None:
        login = self.edit.text().strip().lstrip("@")
        if not login or " " in login:
            show_error(self, self.windowTitle(), "Bitte tragen Sie den Benutzernamen ein, ohne "
                       "Leerzeichen.")
            self.edit.setFocus()
            return
        self.login = login
        self.permission = INVITE_CHOICES[self.rights.currentIndex()]
        self.accept()


# -- Schutzregeln (Phase 6c) --------------------------------------------------------------------
APPROVAL_CHOICES = [0, 1, 2, 3]


def protection_summary(branch: str, rules: BranchProtection) -> str:
    """Was die Regeln bedeuten, in einfachen Sätzen, für die Rückfrage vor dem Speichern."""
    if rules.empty:
        return f"{branch} wird nicht mehr geschützt. Jeder mit Schreibrecht kann direkt hochladen."
    parts = []
    if rules.pull_request_required:
        need = (f" mit mindestens {count(rules.approvals, 'Genehmigung', 'Genehmigungen')}"
                if rules.approvals else "")
        parts.append(f"Änderungen kommen nur über einen Pull Request{need} in {branch}.")
        if rules.dismiss_stale and rules.approvals:
            parts.append("Genehmigungen verfallen, wenn neue Commits dazukommen.")
    if rules.enforce_admins:
        parts.append("Das gilt auch für Administratoren, also auch für Sie.")
    if rules.prevent_deletion:
        parts.append(f"{branch} darf nicht gelöscht werden.")
    parts.append("Force push bleibt immer verboten.")
    return " ".join(parts)


class ProtectionDialog(FocusDialog):
    """Schutzregeln als Kontrollkästchen. Nach accept() stehen sie in rules."""

    def __init__(self, branch: str, rules: BranchProtection | None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        current = rules or BranchProtection(prevent_deletion=False)
        self.rules = current
        self.setWindowTitle(f"Schutzregeln für {branch}: "
                            f"{'geschützt' if rules is not None else 'nicht geschützt'}")
        self.pull_box = QCheckBox(f"Nur über &Pull Request in {branch}")
        self.pull_box.setChecked(current.pull_request_required)
        self.approvals = QComboBox()
        approvals_label = label_for(self.approvals, "&Mindestens so viele Genehmigungen:")
        self.approvals.addItems([str(n) for n in APPROVAL_CHOICES])
        self.approvals.setCurrentIndex(min(current.approvals, APPROVAL_CHOICES[-1]))
        self.stale_box = QCheckBox("Genehmigungen &verfallen, wenn neue Commits dazukommen")
        self.stale_box.setChecked(current.dismiss_stale)
        self.admins_box = QCheckBox("Regeln gelten auch für &Administratoren")
        self.admins_box.setChecked(current.enforce_admins)
        self.delete_box = QCheckBox(f"{branch} darf nicht &gelöscht werden")
        self.delete_box.setChecked(current.prevent_deletion)
        ok = QPushButton("&Weiter …")
        ok.setDefault(True)
        ok.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        for widget in (self.pull_box, approvals_label, self.approvals, self.stale_box,
                       self.admins_box, self.delete_box):
            layout.addWidget(widget)
        layout.addLayout(_buttons(None, ok, cancel))
        self.resize(520, 320)
        self.initial_focus_widget = self.pull_box

    def check(self) -> None:
        required = self.pull_box.isChecked()
        self.rules = BranchProtection(
            required, APPROVAL_CHOICES[self.approvals.currentIndex()] if required else 0,
            required and self.stale_box.isChecked(), self.admins_box.isChecked(),
            self.delete_box.isChecked())
        self.accept()


# Auch für andere Fenster mit Hintergrund-Arbeit (Branches, Phase 5f)
DialogWorker = _Worker
button_row = _buttons
