"""Die Seiten des Einrichtungs-Assistenten.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget)
from pathlib import Path

from cockpit import APP_NAME
from cockpit.core import git, paths
from cockpit.core.features.manifest import AI_SERVICES, FeatureManifest
from cockpit.core.settings import setting_fields
from cockpit.core.text import count
from cockpit.ui import look, vault_ui, videos
from cockpit.ui.announcer import announce
from cockpit.ui.common import label_for, name_widget
from cockpit.ui.error_dialog import show_error
from cockpit.ui.form_builder import FormError, SettingsForm
from cockpit.ui.tasks import Task
from cockpit.ui.text_dialog import TextDialog


FEATURES = [
    "Die wichtigsten Aktionen für Ihre Code-Projekte, ganz ohne Terminal",
    "Volle Funktionalität mit integriertem Terminal und intelligenter Unterstützung",
    "Hochladen und Herunterladen mit GitHub",
    "Branches, Pull Requests, Issues und Zusammenführen, mit Hilfe bei Konflikten",
    "Versionen, Releases und Exe-Dateien",
    "Neuigkeiten nach dem Start: was andere an Ihren Projekten getan haben",
    "Aktivität: Aufrufe, Downloads und Sterne Ihrer Projekte",
    "Übersicht der Pakete, die Ihre Projekte nutzen",
    "README in mehreren Sprachen",
    "Spracheingabe",
    "KI-Hilfe bei Fragen zur Bedienung",
    "Alles per Tastatur, gemacht für Screenreader und Braillezeile",
]


VIDEO_CREDIT = "Videos: erstellt mit Google NotebookLM"


def feature_group(services, manifest: FeatureManifest) -> str:
    """Wo die Einrichtung ein Feature zeigt: "ai" auf der Seite KI, "platform" bei den
    Code-Plattformen, "free" auf der Seite Features wählen. "other" braucht einen anderen Dienst
    wie Automation und erscheint in der Einrichtung nicht. Benötigte Features zählen mit."""
    registry = services.registry
    chain = [manifest] + [registry.get(d) for d in registry.dependencies(manifest.id)
                          if d in registry]
    needed = {s for m in chain for s in m.requires_services}
    if needed & set(AI_SERVICES):
        return "ai"
    if any(m.requires_capabilities for m in chain):
        return "platform"
    return "other" if needed else "free"


def features_in(services, group: str) -> list[FeatureManifest]:
    return [m for m in services.registry.all() if feature_group(services, m) == group]


def feature_line(manifest: FeatureManifest) -> str:
    return f"{manifest.name}: {manifest.description}"


def _lines(name: str, lines: list[str]) -> QListWidget:
    """Erklärung als Liste: eine Zeile pro Satz, gut lesbar auf der Braillezeile."""
    widget = QListWidget()
    name_widget(widget, name)
    widget.setWordWrap(True)
    widget.addItems(lines)
    widget.setCurrentRow(0)
    look.mark_explanation(widget)            # sieht aus wie Text (PLAN-OPTIK.md, Schritt 5)
    return widget


def _button_row(*buttons: QPushButton) -> QHBoxLayout:
    row = QHBoxLayout()
    for button in buttons:
        row.addWidget(button)
    row.addStretch(1)
    return row


class Page(QWidget):
    title = ""
    intro = ""                       # kurze Ansage beim Öffnen der Seite
    can_skip = True
    in_summary = True                # erscheint in der Zusammenfassung
    done_text = ""                   # für die Zusammenfassung, leer: übersprungen
    later = ""                       # wo man es nachholen kann

    def __init__(self, wizard: "SetupWizard") -> None:
        super().__init__()
        self.wizard = wizard
        self.services = wizard.services
        self.layout_ = QVBoxLayout(self)

    def first_focus(self) -> QWidget | None:
        return None

    def needed(self) -> bool:
        """False: Der Assistent lässt die Seite aus."""
        return True

    def next_text(self) -> str:
        """Beschriftung des Knopfs Weiter auf dieser Seite."""
        return "&Weiter"

    def on_show(self) -> None:
        """Beim Öffnen der Seite, zum Beispiel um den Zustand neu zu prüfen."""

    def accept_page(self) -> bool:
        """Bei "Weiter": prüfen und speichern. False bleibt auf der Seite."""
        return True


class WelcomePage(Page):
    title = "Willkommen"
    intro = f"Willkommen bei {APP_NAME}."
    can_skip = False
    in_summary = False

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        # Wunsch des Nutzers: erst der Text, mit Tab der Knopf für das Video, dann Weiter
        self.text = _lines("Willkommen", [
            f"Willkommen bei {APP_NAME}.",
            "Das Cockpit hilft Ihnen, Ihre Code-Projekte zu verwalten: Stände speichern, "
            "hochladen, Versionen und Exe-Dateien erstellen. Sie brauchen dafür kein Terminal "
            "und keine Git-Befehle.",
            "In diesem Programm erwartet Sie:",
            *FEATURES,
            "Dieser Assistent richtet das Wichtigste dafür ein. Ohne den Download einer KI dauert "
            "das etwa 5 bis 10 Minuten.",
            "Die Schritte: Zugangsdaten schützen, Git, Code-Plattformen wie GitHub, "
            "Projekte-Hauptordner, Features und KI. Am Ende sehen Sie eine Zusammenfassung.",
            "Nur der Schutz Ihrer Zugangsdaten ist Pflicht. Alles andere können Sie überspringen "
            "und später über die Menüs ändern.",
            "Mit Tab kommen Sie zur kurzen Einführung als Video.",
            VIDEO_CREDIT,
        ])
        self.video_button = QPushButton("Kurze &Einführung anschauen")
        self.video_button.clicked.connect(self.show_video)
        self.layout_.addWidget(self.text)
        self.layout_.addLayout(_button_row(self.video_button))

    def show_video(self) -> None:
        videos.open_video(self.wizard, videos.INTRO, "Kurze Einführung")
        self.video_button.setFocus()

    def first_focus(self):
        return self.text


class VaultPage(Page):
    title = "Zugangsdaten schützen"
    intro = "Wählen Sie, wo Ihre Zugangsdaten gespeichert werden. Dieser Schritt ist Pflicht."
    can_skip = False
    later = "Menü Konten, Tresor-Einstellungen"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.text = _lines("Erklärung", [
            "Für GitHub und für eine externe KI braucht das Cockpit Zugangsdaten, zum Beispiel "
            "einen geheimen Schlüssel. Sie richten beides in den nächsten Schritten ein.",
            "Mit diesen Zugangsdaten kann jemand in Ihrem Namen Code ändern oder löschen und "
            "Dienste nutzen, die Geld kosten. Deshalb speichert das Cockpit sie nie offen, "
            "sondern immer geschützt.",
            "Sie wählen jetzt, wo die Zugangsdaten liegen. Dieser Schritt ist Pflicht, auch wenn "
            "Sie noch keine Zugangsdaten haben. Es gibt zwei Möglichkeiten.",
            "Erstens: Windows-Anmeldeinformationsverwaltung, empfohlen. Windows schützt die "
            "Zugangsdaten mit Ihrer Windows-Anmeldung. Sie brauchen kein zusätzliches Passwort.",
            "Zweitens: Verschlüsselte Tresordatei. Sie schützen sie mit einem eigenen "
            "Master-Passwort. Sinnvoll, wenn mehrere Personen Ihr Windows-Konto nutzen.",
            "Das Master-Passwort fragt das Cockpit beim Start ab. Geht es verloren, müssen Sie "
            "alle Zugangsdaten neu eingeben.",
            "Gesperrt heißt bei der Tresordatei: Die Zugangsdaten sind nicht lesbar. Alles ohne "
            "Zugangsdaten funktioniert weiter. Braucht eine Aktion einen Zugang, fragt das "
            "Cockpit nach dem Master-Passwort.",
            "Die Speicherart lässt sich später wechseln, ohne etwas neu einzugeben.",
            "Mit Tab kommen Sie zur Auswahl der Speicherart.",
        ])
        # Auswahl als Liste statt Auswahlschaltern: Im Test sagte NVDA bei beiden Schaltern
        # "markiert". Eine Liste mit einem markierten Eintrag ist eindeutig.
        self.choice = QListWidget()
        self.choice.addItems(["Windows-Anmeldeinformationsverwaltung (empfohlen)",
                              "Verschlüsselte Tresordatei mit Master-Passwort"])
        self.choice.setCurrentRow(1 if self.services.vault.kind == "vault_file" else 0)
        self.choice.itemActivated.connect(lambda item: wizard.next())
        self.layout_.addWidget(self.text, 3)
        self.layout_.addWidget(label_for(self.choice, "&Speicherart:"))
        self.layout_.addWidget(self.choice, 1)

    def chosen_kind(self) -> str:
        return "vault_file" if self.choice.currentRow() == 1 else "windows"

    def first_focus(self):
        return self.text                            # zuerst die Erklärung, dann mit Tab die Wahl

    def accept_page(self) -> bool:
        if not vault_ui.switch_vault(self.services, self.chosen_kind(), self.wizard):
            return False
        self.done_text = f"Zugangsdaten: {self.services.vault.display_name}."
        return True


GIT_LINES = [
    "Git ist ein kostenloses Programm, das sich jeden gespeicherten Stand Ihres Codes merkt. So "
    "kommen Sie zu jedem früheren Stand zurück und sehen, was sich geändert hat.",
    "Das Cockpit braucht Git für fast alles, was es mit Ihren Projekten macht.",
]


class GitPage(Page):
    title = "Git"
    later = "Menü Hilfe, Git installieren"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.state = _lines("Git", [])
        self.guide_button = QPushButton("&Anleitung anzeigen …")
        self.guide_button.clicked.connect(self.show_guide)
        self.check_button = QPushButton("&Erneut prüfen")
        self.check_button.clicked.connect(self.recheck)
        self.layout_.addWidget(self.state)
        self.layout_.addLayout(_button_row(self.guide_button, self.check_button))

    def on_show(self) -> None:
        found = git.find_git()
        self.state.clear()
        if found:
            self.intro = "Git ist installiert."
            self.done_text = "Git ist installiert."
            self.state.addItems(["Git ist installiert.", *GIT_LINES,
                                 f"Gefundenes Git-Programm: {found}"])
        else:
            self.intro = "Git wurde nicht gefunden."
            self.done_text = ""
            self.state.addItems([
                "Git wurde nicht gefunden.",
                *GIT_LINES,
                "Ohne Git kann das Cockpit keine Stände speichern und nichts hochladen.",
                "Die Anleitung zeigt drei Wege zur Installation.",
                "Nach der Installation wählen Sie Erneut prüfen.",
            ])
        self.state.setCurrentRow(0)
        self.guide_button.setVisible(found is None)
        self.check_button.setVisible(found is None)

    def recheck(self) -> None:
        self.on_show()
        announce(self.intro)
        self.state.setFocus()

    def show_guide(self) -> None:
        try:
            text = (paths.resource_dir() / git.GUIDE).read_text(encoding="utf-8")
        except OSError as exc:
            show_error(self, "Git installieren", "Die Anleitung wurde nicht gefunden.", str(exc))
            return
        TextDialog("Git installieren", text, "Anleitung Git installieren", self).exec()
        self.guide_button.setFocus()

    def first_focus(self):
        return self.state


def platform_types() -> list:
    """Alle Code-Plattformen, für die es einen Adapter gibt. Zurzeit GitHub, später auch GitLab
    und andere (Phase 16). Neue Adapter erscheinen hier von selbst."""
    from cockpit.core.accounts import account_types
    return [t for t in account_types() if t.kind == "platform"]


class PlatformChoicePage(Page):
    """Wunsch des Nutzers: erst die Git-Systeme wählen, dann einrichten."""
    title = "Code-Plattformen wählen"
    intro = "Wählen Sie, ob Sie eine Code-Plattform wie GitHub nutzen möchten."
    in_summary = False

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.types = platform_types()
        features = features_in(self.services, "platform")
        lines = [
            "Eine Code-Plattform bewahrt Ihren Code im Internet auf. Das ist eine Sicherung, "
            "Sie können den Code teilen und mit anderen daran arbeiten.",
            "Die bekannteste Code-Plattform ist GitHub. Ein Konto dort ist kostenlos.",
            "Mit einem Konto laden Sie Ihren Code hoch und herunter.",
        ]
        if features:
            lines.append("Dazu kommen diese Features:")
            lines += [feature_line(m) for m in features]
        lines += [
            "Ohne Code-Plattform arbeiten Sie nur auf Ihrem Rechner. Dann überspringen Sie "
            "diesen Schritt.",
            "Weitere Code-Plattformen wie GitLab folgen später.",
            "Mit Tab kommen Sie zur Auswahl. Mit der Leertaste haken Sie an oder ab.",
        ]
        self.text = _lines("Erklärung", lines)
        self.list = QListWidget()
        existing = {a.adapter for a in self.services.accounts.all() if a.kind == "platform"}
        for account_type in self.types:
            item = QListWidgetItem(account_type.display_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = account_type.adapter in existing or len(self.types) == 1
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        self.list.itemActivated.connect(lambda item: wizard.next())
        self.layout_.addWidget(self.text, 3)
        self.layout_.addWidget(label_for(self.list, "&Code-Plattformen:"))
        self.layout_.addWidget(self.list, 1)

    def chosen(self) -> list:
        return [t for row, t in enumerate(self.types)
                if self.list.item(row).checkState() == Qt.CheckState.Checked]

    def first_focus(self):
        return self.text                            # zuerst die Erklärung, dann mit Tab die Wahl


class PlatformSetupPage(Page):
    title = "Code-Plattformen einrichten"
    intro = "Nun können Sie Ihre Code-Plattformen einrichten."
    can_skip = False
    later = "Menü Konten, Kontenverwaltung"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.text = _lines("Erklärung", [
            "Jetzt verbinden Sie das Cockpit mit Ihrem Konto. Das geht mit der Anmeldung im "
            "Browser oder mit einem geheimen Schlüssel, einem sogenannten Token.",
            "Das Cockpit speichert den Zugang geschützt, so wie Sie es vorhin gewählt haben.",
            "Danach tragen Sie Ihren Namen und Ihre E-Mail-Adresse für Git ein. Git schreibt sie "
            "zu jeder Ihrer Änderungen, damit man sieht, wer sie gemacht hat. Statt Ihrer "
            "eigenen E-Mail-Adresse können Sie eine anonyme Adresse von GitHub nehmen.",
            "Haben Sie noch kein Konto, legen Sie es bei der Anmeldung im Browser an.",
            "Mit Tab kommen Sie zur Liste. Enter auf einer Plattform öffnet die Einrichtung.",
        ])
        self.list = QListWidget()
        self.list.itemActivated.connect(lambda item: self.setup_current())
        self.setup_button = QPushButton("Plattform &einrichten …")
        self.setup_button.clicked.connect(self.setup_current)
        self.chosen: list = []
        self.layout_.addWidget(self.text, 3)
        self.layout_.addWidget(label_for(self.list, "&Plattformen:"))
        self.layout_.addWidget(self.list, 1)
        self.layout_.addLayout(_button_row(self.setup_button))

    def choice_page(self) -> PlatformChoicePage:
        return next(p for p in self.wizard.pages if isinstance(p, PlatformChoicePage))

    def needed(self) -> bool:
        return bool(self.choice_page().chosen())

    def accounts_of(self, account_type) -> list:
        return [a for a in self.services.accounts.all()
                if a.kind == "platform" and a.adapter == account_type.adapter]

    def missing(self) -> int:
        return sum(1 for t in self.chosen if not self.accounts_of(t))

    def next_text(self) -> str:
        missing = self.missing()
        return f"&Weiter ({missing} nicht eingerichtet)" if missing else "&Weiter"

    def on_show(self) -> None:
        self.chosen = self.choice_page().chosen()
        row = max(0, self.list.currentRow())
        self.list.clear()
        done = []
        for account_type in self.chosen:
            accounts = self.accounts_of(account_type)
            if accounts:
                names = ", ".join(f"{a.display_name}, {a.username}" for a in accounts)
                self.list.addItem(f"{account_type.display_name}, eingerichtet: {names}")
                done.append(f"{account_type.display_name}-Konto: {names}.")
            else:
                self.list.addItem(f"{account_type.display_name}, noch nicht eingerichtet")
        self.list.setCurrentRow(min(row, self.list.count() - 1))
        settings = self.services.settings.load()
        if done and settings.git_name and settings.git_email:
            done.append(f"Git-Identität: {settings.git_name}, {settings.git_email}.")
        self.done_text = " ".join(done)

    def setup_current(self) -> None:
        from cockpit.ui.accounts_dialog import AccountEditDialog
        row = self.list.currentRow()
        if not 0 <= row < len(self.chosen):
            return
        dialog = AccountEditDialog(self.services, self.chosen[row], None, self.wizard,
                                   with_identity=True)
        if dialog.exec():
            self.on_show()
            self.wizard.update_next_text()
            announce(f"Konto {dialog.saved.display_name} angelegt.")
        self.list.setFocus()

    def first_focus(self):
        return self.text


class FolderPage(Page):
    title = "Projekte-Hauptordner"
    intro = "In diesem Ordner legt das Cockpit neue Projekte an und findet vorhandene."
    later = "Menü Einstellungen, Grundeinstellungen"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.text = _lines("Erklärung", [
            "In diesem Ordner liegen Ihre Code-Projekte, jedes in einem eigenen Unterordner.",
            "Das Cockpit findet die Projekte, die schon dort liegen, und zeigt sie in der "
            "Projektliste. Neue Projekte legt es ebenfalls hier an.",
            "Mit Tab kommen Sie zum Feld für den Ordner.",
        ])
        field = next(f for f in setting_fields() if f.key == "projects_root")
        self.form = SettingsForm([field], {"projects_root":
                                           self.services.settings.load().projects_root})
        self.layout_.addWidget(self.text, 1)
        self.layout_.addWidget(self.form)
        self.layout_.addStretch(1)

    def first_focus(self):
        return self.text

    def accept_page(self) -> bool:
        try:
            root = self.form.values()["projects_root"]
        except FormError as exc:
            show_error(self.wizard, self.title, exc.message)
            self.form.focus_field(exc.key)
            return False
        self.services.settings.update(projects_root=root)
        self.services.projects.scan(Path(root))
        number = len(self.services.projects.all())
        self.done_text = f"Projekte-Hauptordner: {root}, {count(number, 'Projekt', 'Projekte')} gefunden."
        return True


class FeaturePage(Page):
    """Wunsch des Nutzers (22.10.2026): Features ohne weitere Einrichtung als Liste, alle
    angehakt. Abhaken schaltet ein Feature überall aus. Pro Projekt ändert man es später."""
    title = "Features wählen"
    intro = "Wählen Sie, welche Features Sie nutzen möchten. Alle sind angehakt."
    later = "Menü Features, Feature-Verwaltung"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.features = features_in(self.services, "free")
        self.in_summary = bool(self.features)
        self.text = _lines("Erklärung", [
            "Features sind Zusatzfunktionen des Cockpits. Die Features hier brauchen keine "
            "weitere Einrichtung.",
            "Alle sind angehakt. Mit der Leertaste haken Sie ein Feature ab oder wieder an.",
            "Abgehakte Features sind überall aus. Angehakte sind in allen Projekten an.",
            "Für ein einzelnes Projekt ändern Sie das später in der Projektliste mit Features "
            "dieses Projekts. Für alle Projekte im Menü Features, Feature-Verwaltung.",
            "Features mit GitHub standen bei den Code-Plattformen, Features mit KI kommen auf "
            "der nächsten Seite.",
            "Mit Tab kommen Sie zur Liste der Features.",
        ])
        self.list = QListWidget()
        self.list.setWordWrap(True)
        for manifest in self.features:
            item = QListWidgetItem(feature_line(manifest))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            on = self.services.features.globally_enabled(manifest.id)
            item.setCheckState(Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        self.list.itemActivated.connect(lambda item: wizard.next())
        self.layout_.addWidget(self.text, 2)
        self.layout_.addWidget(label_for(self.list, "&Features:"))
        self.layout_.addWidget(self.list, 2)

    def needed(self) -> bool:
        return bool(self.features)

    def chosen(self) -> set[str]:
        return {m.id for row, m in enumerate(self.features)
                if self.list.item(row).checkState() == Qt.CheckState.Checked}

    def first_focus(self):
        return self.text

    def accept_page(self) -> bool:
        features = self.services.features
        chosen = self.chosen()
        for manifest in self.features:
            features.set_globally_enabled(manifest.id, manifest.id in chosen)
        # Angehakte Features sollen in den Projekten an sein, auch wenn sie es sonst nicht sind
        defaults = features.default_features()
        if not chosen <= defaults:
            features.set_default_features(defaults | chosen)
        self.done_text = (f"Features: {len(chosen)} von {len(self.features)} eingeschaltet.")
        return True


AI_INTRO = "Eine KI kann Ihnen im Cockpit viel Arbeit abnehmen. Sie ist freiwillig."


AI_LINES = [
    "Die Text-KI schlägt zum Beispiel Commit-Nachrichten vor, erklärt Fehlermeldungen im "
    "Terminal und beantwortet Fragen zur Bedienung.",
    "Die Sprach-KI wandelt Gesprochenes in Text um. Damit diktieren Sie, statt zu tippen.",
    "Es gibt zwei Wege.",
    "Lokale KI: Sie läuft auf Ihrem Rechner. Ihre Daten bleiben bei Ihnen, und sie kostet "
    "nichts. Dafür laden Sie ein Modell herunter, oft mehrere GB groß, und Ihr Rechner braucht "
    "genug Arbeitsspeicher. Passende Modelle schlägt Ihnen das Cockpit vor.",
    "Externe KI oder Firmen-KI: Sie läuft im Internet und ist meist schneller. Dafür gehen Ihre "
    "Texte an den Anbieter, und es kann Geld kosten. Sie brauchen einen Zugangsschlüssel.",
    "Ohne KI funktioniert das Programm auch. Die Features mit KI sind dann aus.",
    "Die KI können Sie auch später einrichten: Menü KI, KI-Verwaltung.",
]

AI_TAB = "Mit Tab kommen Sie zu KI einrichten."


class AIPage(Page):
    """Seite KI (Konzept 8.7, Teilschritt 8b): Rechner und Ollama prüfen, KI einrichten."""
    title = "KI"
    intro = "Eine KI kann Ihnen viel Arbeit abnehmen. Sie ist freiwillig."
    later = "Menü KI, KI-Verwaltung"

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.text = _lines("KI", [])
        self.setup_button = QPushButton("KI &einrichten …")
        self.setup_button.clicked.connect(self.setup_ai)
        self.task = None
        self.layout_.addWidget(self.text)
        self.layout_.addLayout(_button_row(self.setup_button))

    def on_show(self) -> None:
        tool = self.services.ai_tools.default()
        self.done_text = f"Text-KI: {self.services.ai_tools.label(tool, False)}." if tool else ""
        self.show_lines([])
        if self.task is None:
            self.check()

    def show_lines(self, extra: list[str]) -> None:
        tool = self.services.ai_tools.default()
        lines = [AI_INTRO]
        lines.append(f"Eingerichtet: {self.services.ai_tools.label(tool, False)}." if tool
                     else "Es ist noch keine KI eingerichtet.")
        features = features_in(self.services, "ai")
        if features:
            lines.append("Mit KI nutzen Sie diese Features:")
            lines += [feature_line(m) for m in features]
        lines += AI_LINES
        lines += extra or ["Rechner und Ollama werden geprüft …"]
        lines.append(AI_TAB)
        row = max(0, self.text.currentRow())
        self.text.clear()
        self.text.addItems(lines)
        self.text.setCurrentRow(min(row, self.text.count() - 1))

    def check(self) -> None:
        from cockpit.ai import ollama
        from cockpit.core import hardware
        from cockpit.ui.ai_dialogs import (manual_ram, recommendation_line,
                                           speech_recommendation_line)
        manual = manual_ram(self.services)

        def work(task):
            machine = hardware.detect(manual)
            return machine.lines()[:1] + [recommendation_line(machine.ram_gb),
                                          speech_recommendation_line(machine.ram_gb),
                                          ollama.state()]

        self.task = Task(work, self)
        self.task.result.connect(self.show_lines)
        self.task.error.connect(lambda message, details: self.show_lines([message]))
        self.task.finished.connect(self._checked)
        self.task.start()

    def _checked(self) -> None:
        task, self.task = self.task, None
        if task is not None:
            task.wait()                      # Thread ganz beendet, sonst bricht Qt ab
            task.deleteLater()

    def setup_ai(self) -> None:
        from cockpit.ui.ai_dialogs import AIManagerDialog
        AIManagerDialog(self.services, self.wizard, for_setup=True).exec()
        self.on_show()
        self.setup_button.setFocus()

    def first_focus(self):
        return self.text


TIPS = [
    "Für einen perfekten Start hier noch ein paar Tipps.",
    "Bei eingeschalteter Text-KI steht Ihnen der Hilfe-Assistent zur Verfügung. Er beantwortet "
    "Ihre Fragen zum Programm.",
    "Zum Beispiel: Wo finde ich welches Menü?",
    "Oder: Wie lautet noch mal der Git-Befehl für einen neuen Branch?",
    "Sie öffnen den Hilfe-Assistenten mit Umschalt+F1 oder im Menü Hilfe, KI-Hilfe.",
    "Brauchen Sie noch eine kleine Auffrischung für einen gelungenen Umgang mit "
    "Code-Plattformen? Dann schauen Sie sich das Video Git für Anfänger an. Mit Tab kommen Sie "
    "zum Knopf.",
    VIDEO_CREDIT,
]


class SummaryPage(Page):
    title = "Zusammenfassung"
    intro = "Die Einrichtung ist fertig. Die Liste zeigt, was eingerichtet wurde."
    can_skip = False
    in_summary = False

    def __init__(self, wizard) -> None:
        super().__init__(wizard)
        self.list = _lines("Zusammenfassung", [])
        self.tips = _lines("Tipps für den Start", TIPS)
        self.video_button = QPushButton("Video Git für &Anfänger anschauen")
        self.video_button.clicked.connect(self.show_video)
        self.layout_.addWidget(self.list, 2)
        self.layout_.addWidget(label_for(self.tips, "&Tipps für den Start:"))
        self.layout_.addWidget(self.tips, 2)
        self.layout_.addLayout(_button_row(self.video_button))

    def next_text(self) -> str:
        return "&Fertig"

    def on_show(self) -> None:
        lines = ["Die Einrichtung ist fertig. Hier sehen Sie, was eingerichtet ist und was nicht."]
        for page in self.wizard.pages:
            if not page.in_summary:
                continue
            if page.done_text and page.needed():
                lines.append(f"Eingerichtet: {page.done_text}")
            else:
                lines.append(f"Übersprungen: {page.title}. Nachholen: {page.later}.")
        lines.append("Mit Fertig öffnen Sie das Cockpit. Dort sehen Sie die Liste Ihrer Projekte.")
        lines.append("F1 öffnet die Hilfe mit Kurzanleitungen für die wichtigsten Aufgaben.")
        lines.append("Mit Tab gelangen Sie zu den Tipps, zum Video und zu Fertig.")
        self.list.clear()
        self.list.addItems(lines)
        self.list.setCurrentRow(0)

    def show_video(self) -> None:
        videos.open_video(self.wizard, videos.GIT_BASICS, "Git für Anfänger")
        self.video_button.setFocus()

    def first_focus(self):
        return self.list
