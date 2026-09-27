"""Fenster für das erste Hochladen (Konzept 9.1 und 9.6).

UploadDialog: Angaben für das neue Repository. Der Fokus beginnt im Feld "Name auf GitHub".
SafetyDialog: Funde der Sicherheitsprüfung als Liste. Für den markierten Fund gibt es Knöpfe:
"In .gitignore aufnehmen", "Kein Geheimnis", "Trotzdem hochladen", "Datei öffnen". "Weiter" geht
erst, wenn kein Fund mehr das Hochladen stoppt und private E-Mail-Adressen bestätigt sind. Warnungen, bei denen nichts gewählt wurde, kommen
beim Weiter in .gitignore (sichere Vorgabe). Escape bricht ab.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QHBoxLayout, QListWidget, QPushButton, QVBoxLayout, QWidget

from cockpit.core import core_actions, safety_check, upload
from cockpit.core.errors import CockpitError
from cockpit.core.features import settings_fields as sf
from cockpit.core.safety_check import Finding, Kind, Report
from cockpit.core.settings import LICENSES
from cockpit.core.text import count
from cockpit.core.upload import UploadSpec
from cockpit.ui.announcer import announce
from cockpit.ui.common import FocusDialog, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.form_builder import FormError, SettingsForm

PRIVATE, PUBLIC = "Privat", "Öffentlich"


class UploadDialog(FocusDialog):
    def __init__(self, title: str, name: str, platform_name: str, user: str,
                 organizations: list[str], private: bool, license: str,
                 parent: QWidget | None = None,
                 features: list[tuple[str, str]] | None = None,
                 chosen: set[str] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.spec: UploadSpec | None = None
        self.targets = [f"Eigenes Konto {user}".strip(), *organizations]
        self.organizations = organizations
        self.features = features or []           # (Kennung, Name), Phase 7
        fields = [
            sf.Text("name", f"Name auf {platform_name}", name, required=True),
            sf.Text("description", "Kurzbeschreibung", ""),
            sf.Choice("visibility", "Sichtbarkeit", PRIVATE if private else PUBLIC,
                      options=(PRIVATE, PUBLIC)),
            sf.Choice("license", "Lizenz", license, options=LICENSES),
            sf.Choice("target", "Ziel", self.targets[0], options=tuple(self.targets)),
        ]
        if self.features:
            names = [n for _, n in self.features]
            fields.append(sf.MultiChoice(
                "features", "Features für dieses Projekt",
                [n for f, n in self.features if f in (chosen or set())], options=tuple(names)))
        self.form = SettingsForm(fields, {"features": [n for f, n in self.features
                                                        if f in (chosen or set())]}
                                 if self.features else None)
        self.ok_button = QPushButton("&Weiter …")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.check)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.ok_button)
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(self.form)
        layout.addLayout(buttons)
        self.resize(560, 300)
        self.initial_focus_widget = self.form.first_focus()
        self.initial_focus_widget.setFocus()

    def check(self) -> None:
        try:
            values = self.form.values()
        except FormError as exc:
            show_error(self, self.windowTitle(), exc.message)
            self.form.focus_field(exc.key)
            return
        problem = upload.name_problem(values["name"])
        if problem:
            show_error(self, self.windowTitle(), problem)
            self.form.focus_field("name")
            return
        index = self.targets.index(values["target"])
        self.spec = UploadSpec(values["name"], values["description"],
                               values["visibility"] == PRIVATE, values["license"],
                               self.organizations[index - 1] if index > 0 else "")
        if self.features:
            by_name = {n: f for f, n in self.features}
            self.spec.features = {by_name[n] for n in values.get("features", []) if n in by_name}
        self.accept()


class SafetyDialog(FocusDialog):
    """Funde der Sicherheitsprüfung. Nach accept() ist alles erledigt oder bestätigt."""

    def __init__(self, report: Report, code_dir: Path, spec: UploadSpec, git_email: str,
                 rescan=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.code_dir = code_dir
        self.spec = spec
        self.git_email = git_email
        self.rescan = rescan
        self.report = report
        self.accepted: set[tuple[str, str, str]] = set()      # "Trotzdem hochladen"

        self.list = QListWidget()
        name_widget(self.list, "Funde")
        self.list.currentRowChanged.connect(lambda _row: self.update_buttons())
        self.ignore_button = QPushButton("In .&gitignore aufnehmen")
        self.ignore_button.clicked.connect(self.ignore_current)
        self.not_secret_button = QPushButton("&Kein Geheimnis")
        self.not_secret_button.clicked.connect(self.mark_current)
        self.accept_button = QPushButton("&Trotzdem hochladen")
        self.accept_button.clicked.connect(self.accept_current)
        self.open_button = QPushButton("Datei ö&ffnen")
        self.open_button.clicked.connect(self.open_current)
        self.recheck_button = QPushButton("&Erneut prüfen")
        self.recheck_button.clicked.connect(self.recheck)
        self.continue_button = QPushButton("&Weiter")
        self.continue_button.clicked.connect(self.finish)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        actions = QHBoxLayout()
        for button in (self.ignore_button, self.not_secret_button, self.accept_button,
                       self.open_button, self.recheck_button):
            actions.addWidget(button)
        actions.addStretch(1)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(self.continue_button)
        bottom.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addLayout(actions)
        layout.addLayout(bottom)
        self.resize(760, 400)
        self.initial_focus_widget = self.list
        # Enter in der Liste löst keinen Knopf aus. Auf einem Knopf löst Enter genau diesen
        # aus (Rückmeldung aus dem Test von 5b), dafür sorgt autoDefault der Knöpfe.
        self.list.installEventFilter(self)
        self.fill()

    # -- Anzeige ---------------------------------------------------------------------------
    @staticmethod
    def _key(finding: Finding) -> tuple[str, str, str]:
        return finding.kind.value, finding.path, finding.rule

    def line(self, finding: Finding) -> str:
        if finding.kind.blocking:
            return f"{finding.text}. Stoppt das Hochladen"
        if self._key(finding) in self.accepted:
            return f"{finding.text}. Wird trotzdem hochgeladen"
        if finding.kind is Kind.PRIVATE_EMAIL:
            return (f"{finding.text}. Sie wird im öffentlichen Repository sichtbar. Besser ist die "
                    "noreply-Adresse von GitHub in den Grundeinstellungen. Sonst Trotzdem "
                    "hochladen wählen")
        return f"{finding.text}. Kommt in .gitignore"

    def fill(self, row: int = 0) -> None:
        findings = self.report.findings
        blocking = len(self.report.blocking)
        warnings = len(findings) - blocking
        parts = []
        if blocking:
            parts.append(count(blocking, "Fund stoppt das Hochladen",
                               "Funde stoppen das Hochladen"))
        if warnings:
            parts.append(count(warnings, "Warnung", "Warnungen"))
        self.setWindowTitle("Sicherheitsprüfung: " + (", ".join(parts) or "alles in Ordnung"))
        self.list.clear()
        self.list.addItems([self.line(f) for f in findings] or ["Keine Funde mehr."])
        self.list.setCurrentRow(min(row, self.list.count() - 1))
        self.update_buttons()

    def current(self) -> Finding | None:
        row = self.list.currentRow()
        findings = self.report.findings
        return findings[row] if 0 <= row < len(findings) else None

    def update_buttons(self) -> None:
        finding = self.current()
        self.ignore_button.setEnabled(finding is not None and finding.whole_file)
        self.not_secret_button.setEnabled(finding is not None and finding.kind in (
            Kind.SECRET, Kind.SECRET_IN_HISTORY) and bool(finding.fingerprint))
        self.accept_button.setEnabled(finding is not None and not finding.kind.blocking)
        self.open_button.setEnabled(finding is not None and bool(finding.path)
                                    and finding.kind is not Kind.SECRET_IN_HISTORY)
        self.continue_button.setEnabled(not self.open_findings())

    def open_findings(self) -> list[Finding]:
        """Funde, die "Weiter" verhindern: alles, was stoppt, und private E-Mail-Adressen, die
        nicht ausdrücklich bestätigt sind."""
        return [f for f in self.report.findings if f.kind.blocking or (
            f.kind is Kind.PRIVATE_EMAIL and self._key(f) not in self.accepted)]

    # -- Knöpfe ----------------------------------------------------------------------------
    def _after_change(self, text: str) -> None:
        row = self.list.currentRow()
        self.recheck(speak=False)
        announce(text)
        self.fill(row)
        self.list.setFocus()

    def ignore_current(self) -> None:
        finding = self.current()
        if finding is None:
            return
        try:
            safety_check.ignore_file(self.code_dir, finding.path)
        except CockpitError as exc:
            show_error(self, "Sicherheitsprüfung", exc.message, exc.details)
            return
        self._after_change(f"{finding.path} kommt in .gitignore und wird nicht hochgeladen.")

    def mark_current(self) -> None:
        finding = self.current()
        if finding is None:
            return
        safety_check.mark_not_secret(self.code_dir, finding)
        self._after_change("Als kein Geheimnis markiert.")

    def accept_current(self) -> None:
        finding = self.current()
        if finding is None or finding.kind.blocking:
            return
        self.accepted.add(self._key(finding))
        row = self.list.currentRow()
        self.fill(row)
        announce("Wird trotzdem hochgeladen.")
        self.list.setFocus()

    def open_current(self) -> None:
        finding = self.current()
        if finding is not None and finding.path:
            core_actions.open_path(self.code_dir / finding.path)

    def eventFilter(self, watched, event) -> bool:
        from PySide6.QtCore import QEvent, Qt
        if watched is self.list and event.type() == QEvent.Type.KeyPress and event.key() in (
                Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return True
        return super().eventFilter(watched, event)

    def recheck(self, speak: bool = True) -> None:
        """Erneut prüfen. Sagt, ob der markierte Fund behoben ist. Der Fokus geht in die Liste:
        bei behoben auf den nächsten Fund, sonst auf denselben."""
        before = self.current()
        row = self.list.currentRow()
        if self.rescan is not None:
            self.report = self.rescan()
        def same(finding: Finding) -> tuple:
            return finding.kind, finding.path, finding.rule, finding.fingerprint

        keys = [same(f) for f in self.report.findings]
        still = before is not None and same(before) in keys
        self.fill(keys.index(same(before)) if still else max(row, 0))
        self.list.setFocus()
        if speak:
            summary = self.windowTitle().replace("Sicherheitsprüfung: ", "")
            if before is None:
                announce(f"Geprüft: {summary}")
            else:
                announce(f"{'Besteht weiter' if still else 'Behoben'}. Noch: {summary}"
                         if self.report.findings else "Behoben. Keine Funde mehr.")

    def finish(self) -> None:
        """Weiter: Warnungen ohne Entscheidung kommen in .gitignore (sichere Vorgabe)."""
        if self.open_findings():
            return
        for finding in self.report.warnings:
            if self._key(finding) not in self.accepted and finding.whole_file:
                safety_check.ignore_file(self.code_dir, finding.path)
        self.accept()
