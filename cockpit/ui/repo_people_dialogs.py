"""Mitarbeiter einladen und verwalten, Schutz der Branches.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QLineEdit, QListWidget, QPushButton, QVBoxLayout, QWidget)

from cockpit.core.text import count
from cockpit.platforms.base import BranchProtection, Collaborator, PERMISSION_NAMES
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, confirm, label_for, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.repo_dialog_parts import _Worker, _buttons, _is_enter


# Rechte beim Einladen, in dieser Reihenfolge im Auswahlfeld. Vorgabe ist "schreiben".
INVITE_CHOICES = ["read", "write", "admin"]


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
