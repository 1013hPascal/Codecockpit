# Plan für CodeCockpit

Stand: 25.09.2026, nach den Antworten zu Phase 5.

Grundlage sind KONZEPT.md, ENTSCHEIDUNGEN.md und ANALYSE.md. Wo ENTSCHEIDUNGEN.md vom Konzept abweicht, gilt ENTSCHEIDUNGEN.md. Die wichtigste Abweichung: Es gibt keine Profile.

Abschnittsnummern wie „Konzept 3.3“ beziehen sich auf KONZEPT.md.

Inhalt:

1. Fortschritt der 17 Phasen
2. Ordner- und Paketstruktur
3. Technischer Entwurf für Phase 2
4. Was Phase 2 liefert
5. Offene Fragen an Sie #pascal
6. Beantwortete Fragen aus Phase 1


## 1. Fortschritt der 17 Phasen

- [x] Phase 1: Analyse der bestehenden Projekte, Plan, Regeln für Claude Code
- [x] Phase 2: Grundgerüst mit Kern, Feature-System, Adapter-Schnittstellen, Menüleiste, Grundeinstellungen, Projektliste. Abgeschlossen am 25.09.2026: 105 Tests bestanden, NVDA-Test mit checklisten\phase-02.md bestanden
- [x] Phase 3: Tresor mit beiden Speicherarten und Wechsel, Kontenverwaltung, Einrichtungsassistent mit Prüfung auf Git. Abgeschlossen am 25.09.2026, außer der Sprachausgabe in Dialogen (siehe TODO.md)
- [x] Phase 4: GitHub-Anbindung mit Anmeldung im Browser und per Token, Verbindungstest, Organisationen, Hinweise zu Single Sign-On. Abgeschlossen am 25.09.2026: 213 Tests bestanden, NVDA-Test mit checklisten\phase-04.md bestanden
- [x] Phase 5: Grundfunktionen in sechs Teilschritten (siehe unten und ENTSCHEIDUNGEN.md). Abgeschlossen am 26.09.2026
  - [x] 5a: Git-Grundlage, Git-Identität, Projekte hinzufügen, Umstellen oder Verknüpfen, Reparatur nach dem Verschieben, Stand in der Projektliste, Repositories des Kontos in der Liste
  - [x] 5b: Sicherheitsprüfung und .gitignore, Neues Projekt hochladen, Auf GitHub hochladen
  - [x] 5c: Änderungen hochladen, Änderungen holen mit Konflikten und Beiseitelegen (Herunterladen kam schon in 5b)
  - [x] 5d: Verlauf und Rückgängig machen, mit Sicherheitskopien
  - [x] 5e: Links, Repository verwalten mit Mitarbeitern, Aus der Liste entfernen
  - [x] 5f: Übersicht „Branches“ und Stash
- [x] Phase 6: Feature Branches und Pull Requests mit Reviews und Schutzregeln (vorgezogen). Abgeschlossen am 27.09.2026
  - [x] 6a: Pull Requests erstellen, ansehen, kommentieren, Entwürfe, schließen und wieder öffnen
  - [x] 6b: Reviews, Änderungen ansehen, in main übernehmen und aufräumen
  - [x] 6c: Schutzregeln, Hochladen in einen Branch bei geschütztem main, Feature für den Ablauf beim Hochladen
- [x] Phase 7: Feature-Verwaltung global und pro Projekt, mit Einführung beim ersten Einschalten. Abgeschlossen am 27.09.2026
- [ ] Phase 8: KI-Adapter Ollama und OpenAI-kompatibel, KI-Verwaltung, Terminal, KI-Features (ergänzt am 27.09.2026)
  - [x] 8a: Eingebautes Terminal
  - [x] 8b: Menü KI, KI-Verwaltung, lokale KI passend zum Rechner, Feature Terminal-Erklärung
  - [x] 8c: Feature KI-Assistent
  - [ ] 8d: Feature Spracheingabe mit Whisper (verschoben, erst nach Phase 10, gebaut am 29.09.2026)
  - [ ] 8e: Feature KI-Hilfe (verschoben, erst nach Phase 10, gebaut am 29.09.2026)
- [ ] Phase 9: Features README-Pflege mit Sprachen und Versionen mit Tags (verschoben, erst nach Phase 10, gebaut am 29.09.2026)
- [ ] Phase 10: Exe (überarbeitet am 27.09.2026, vorgezogen vor 8d, 8e und 9)
  - [ ] 10a: Eintrag Exe, Exe hinzufügen, Exe-Datei wählen, Zustand in cockpit.toml, Anleitung
  - [ ] 10b: Exe aus dem Code erstellen und aktualisieren mit PyInstaller, Start-Test, Ersetzen mit Sicherheitskopie
  - [ ] 10c: Exe veröffentlichen und aus dem Release holen
  - [ ] 10d: Die eigene Exe des Cockpits mit Aktualisierung beim Neustart, Exe-Einrichtung prüfen
  - [ ] 10e: Updates der Exe des Cockpits aus dem neuesten Release (ergänzt am 28.09.2026)
  - [ ] 10f: Ein Ordner pro Branch mit Worktrees, Branch-Exe (ergänzt am 28.09.2026)
  - [ ] 10g: Ordner neben der Exe, strengerer Start-Test, bessere Prüfung, Exe mit KI einrichten (ergänzt am 28.09.2026)
  - [ ] Später: Externe Ressourcen, Lizenzprüfung, Signieren
- [ ] Phase 11: n8n-Grundlagen, Einspielen von Workflows, Ansicht Automatisierungen, Feature Rückmeldungen
- [ ] Phase 12: E-Mail-Konten, Test-E-Mail, Features E-Mail-Benachrichtigungen und Wochenbericht
- [ ] Phase 13: Features Antwortentwürfe, Abhängigkeiten-Wächter, Erinnerung
- [ ] Phase 14: Feature Releases mit GitHub Actions (vorgezogen vor 11 bis 13, gebaut am 29.09.2026)
- [ ] Projektsammlungen in der Projektliste (Wunsch vom 29.09.2026, gebaut am 29.09.2026, Checkliste checklisten\sammlungen.md)
- [ ] Phase 15: Weitere KI-Adapter: Azure OpenAI, Anthropic, Gemini
- [ ] Phase 16: Weitere Plattform-Adapter: GitLab und Azure DevOps
- [ ] Exe bauen in Schritten, eigener Ordner je Exe, Release als ZIP mit Versionsordner, Lizenz auf der Projektzeile, Update bei jedem Start, Branch löschen ohne main (Wunsch vom 03.10.2026, Checkliste checklisten\exe-bau-ueberarbeiten.md)
- [ ] Eigene Bauanleitung schützen, Unbedingtes in den Exe-Einstellungen (Rückmeldung vom 03.10.2026, Checkliste checklisten\exe-einstellungen.md)
- [ ] Problem mit KI lösen, Stand in den Aktionen, Branches anzeigen, Reihenfolge der Projektliste (Wunsch vom 02.10.2026, Checkliste checklisten\exe-ki-und-branches.md)
- [ ] Projektübersichten und Aktionsmenüs: Main-Branch, Branches verwalten, Menüs von Main, Branch, Exe und Projekt (Wunsch vom 30.09.2026, gebaut am 30.09.2026, Checkliste checklisten\projektuebersichten.md)
- [ ] Einrichtungsassistent überarbeitet: Knöpfe, Zugangsdaten, Code-Plattformen, Videos und Tipps (Wunsch vom 29.09.2026, gebaut am 29.09.2026, Checkliste checklisten\einrichtung.md)
- [ ] Phase 17: Sicherung und Wiederherstellung, Export und Import von Einstellungen, Signieren der Exe, Prüfung aller Feature-Einführungen, Feinschliff

Jede Phase endet mit automatischen Tests und einer Testanleitung für NVDA und Braillezeile. Eine Phase gilt erst als fertig, wenn Sie die Testanleitung durchgegangen sind.


## 2. Ordner- und Paketstruktur

### 2.1 Ordner auf der Festplatte

- `Codecockpit\Code`: der Quellcode, das Git-Repository.
- `Codecockpit\Exe`: die fertige `CodeCockpit.exe`, ab Phase 9.
- `Codecockpit\Referenz`: Chatbot und Tagebuch zum Nachschauen. Nicht im Repository, wird am Ende gelöscht.
- `%APPDATA%\CodeCockpit`: Daten des Programms, nicht im Repository.
  - `cockpit.db`: SQLite-Datenbank mit Einstellungen, Konten ohne Geheimnisse, Projekten und Feature-Zuständen.
  - `vault.bin`: die verschlüsselte Tresordatei, nur wenn diese Speicherart gewählt ist.
  - `logs\app.log`: das Log, ohne Geheimnisse.
  - `backups\`: Sicherheitskopien vor dem Zurücksetzen, 30 Tage lang (Konzept 9.7).
- `%LOCALAPPDATA%\CodeCockpit`: große Dateien und Zwischenspeicher, zum Beispiel temporäre Build-Ordner.

Für Tests lässt sich der Datenordner mit der Umgebungsvariable `CODECOCKPIT_HOME` umlenken.

### 2.2 Dateien im Ordner Code

- `main.py`: Startdatei. Richtet das Log ein, prüft die Voraussetzungen, öffnet das Hauptfenster.
- `requirements.txt`: Bibliotheken mit festen Versionsnummern.
- `pytest.ini`, `.gitignore`, `start.bat`
- `cockpit.toml`: Projekteinstellungen des Cockpits selbst, mit `is_cockpit = true` (Konzept 10.4).
- `README.md`: auf Englisch, ab Phase 8 vom Cockpit selbst gepflegt.
- `KONZEPT.md`, `PLAN.md`, `ANALYSE.md`, `ENTSCHEIDUNGEN.md`, `CLAUDE.md`
- `anleitungen\`: Anleitungen für Nutzer, zum Beispiel `git-installieren.md`. Das Cockpit zeigt sie auch selbst an.
- `checklisten\`: eine Checkliste pro Phase zum Ausfüllen, zum Beispiel `phase-02.md`.
- `cockpit\`: das Programm als Python-Paket.
- `tests\`: die automatischen Tests.

### 2.3 Das Paket cockpit

Die Namen im Code sind englisch, Kommentare und Texte deutsch.

- `cockpit\core\`: der Kern ohne Qt.
  - `paths.py`: Datenordner und Log-Ordner.
  - `logging_setup.py`: Einrichtung des Logs mit Geheimnis-Filter.
  - `secret.py`: die Klasse `Secret`, die sich nie selbst ausgibt.
  - `database.py`: SQLite mit Versionsnummer und Migrationen.
  - `settings.py`: die Einstellungen der Installation.
  - `projects.py`: Projekte, Speicherorte und `cockpit.toml`. Ausgebaut in Phase 5.
  - `accounts.py`: Konten ohne Geheimnisse. Ausgebaut in Phase 3.
  - `services.py`: der Behälter, über den Features an Adapter und Kern-Dienste kommen.
  - `errors.py`: gemeinsame Fehlerklassen mit einfachem Text und Details.
  - `features\`: das Feature-System.
    - `manifest.py`: Beschreibung eines Features.
    - `settings_fields.py`: Beschreibung von Einstellungsfeldern.
    - `registry.py`: findet und lädt alle Features.
    - `manager.py`: welches Feature wo aktiv ist, Abhängigkeiten, Verfügbarkeit.
  - `flows\`: der Ablauf-Motor.
    - `hooks.py`: die festen Einhängepunkte.
    - `step.py`: Beschreibung eines Schritts und seines Ergebnisses.
    - `engine.py`: sammelt die aktiven Schritte und führt sie aus.
    - `questions.py`: Rückfragen vom Hintergrund an die Oberfläche.
  - `actions.py`: Beschreibung einer Aktion für die Aktionsliste.
  - `git.py`: Aufruf von Git. Ausgebaut in Phase 5.
  - `safety_check.py`: die Sicherheitsprüfung, ab Phase 5.
  - `sync.py`: Änderungen hochladen und holen, Konflikte, ab Phase 5c.
  - `history.py`: Verlauf, Rückgängig machen und Änderungen verwerfen, ab Phase 5d.
  - `trash.py`: Dateien in den Papierkorb von Windows, ab Phase 5d.
  - `repo_admin.py`: Links, Sicherheitsprüfung vor dem Veröffentlichen, Verbindung lösen nach dem Löschen, ab Phase 5e.
  - `branches.py`: Branches und beiseitegelegte Änderungen, ab Phase 5f.
  - `pull_requests.py`: Pull Requests, Reviews und Aufräumen, ab Phase 6.
- `cockpit\adapters\`: gemeinsame Grundlagen aller Adapter.
  - `base.py`: Basisklasse, Kontofelder, Testergebnis.
  - `registry.py`: Tabelle aller Adapter pro Art.
- `cockpit\vault\`: Tresor-Schnittstelle und Adapter `windows.py` und `vault_file.py`, dazu `crypto.py` nach dem Vorbild aus dem Tagebuch.
- `cockpit\platforms\`: Plattform-Schnittstelle, Fähigkeiten und Adapter `github.py`, später `gitlab.py` und `azure_devops.py`.
- `cockpit\ai\`: KI-Schnittstelle und Adapter `ollama.py`, `openai_compatible.py`, später `azure_openai.py`, `anthropic.py`, `gemini.py`. Dazu `prompts\` mit anpassbaren Textdateien.
- `cockpit\automation\`: Schnittstelle, Adapter `none.py` und später `n8n.py`.
- `cockpit\email\`: Schnittstelle, später `smtp.py` und `microsoft365.py`.
- `cockpit\features\`: ein Unterpaket pro Feature, zum Beispiel `ai_assistant\`, `readme\`, `versions\`, `exe\`. Jedes enthält `manifest.py`, den eigenen Code, die Einführung `EINFUEHRUNG.md` und bei Bedarf `n8n_workflows\` mit JSON-Dateien und `BESCHREIBUNG.md`.
- `cockpit\ui\`: die Oberfläche.
  - `announcer.py`: der Announcer aus den Referenz-Projekten, mit Speicher der letzten 50 Meldungen.
  - `tasks.py`: die Klasse `Task` und die Warteschlange pro Projekt.
  - `menus.py`: `AccessibleMenu` und `ContextMenu`.
  - `common.py`: `name_widget`, Rückfragen, Textfeld mit echtem Zeilenumbruch.
  - `error_dialog.py`: einfacher Text plus „Details anzeigen“.
  - `form_builder.py`: baut aus Einstellungsfeldern ein barrierefreies Formular.
  - `main_window.py`: Menüleiste, Projektbaum, Aktionsliste, Statuszeile.
  - `project_tree.py`: der Baum mit automatischem Zuklappen.
  - `action_list.py`
  - `progress.py`: „Schritt 3 von 5“ als Text und Ansage.
  - `dialogs\`: ein Modul pro Dialog, zum Beispiel `settings.py`, `shortcuts.py`, `messages.py`.
- `tests\`: `conftest.py` mit Attrappen für alle Adapter-Arten, dann Tests nach Bereichen.


## 3. Technischer Entwurf für Phase 2

Alles in diesem Abschnitt ist ein Entwurf. Die Code-Beispiele zeigen nur die Form, nicht den fertigen Code.

### 3.1 Grundregeln

- Der Kern importiert nie PySide6. Er ist ohne Oberfläche testbar.
- Features und Adapter sprechen nur mit Schnittstellen. Sie bekommen alles, was sie brauchen, über den Behälter `Services`. Sie importieren keine konkreten Adapter.
- Neue Features und neue Adapter kommen dazu, ohne dass der Kern geändert wird. Ein neues Feature ist ein neues Unterpaket in `cockpit\features`. Ein neuer Adapter ist ein neues Modul mit einem Eintrag im Adapter-Register.
- Jede Fehlerklasse hat einen einfachen deutschen Text und getrennt davon die technischen Details.

### 3.2 Geheimnisse

- Die Klasse `Secret` umhüllt jeden Token, jeden Schlüssel und jedes Passwort. Bei `str()` und `repr()` gibt sie nur Sternchen aus. Den echten Wert bekommt man nur über die Methode `reveal()`. So landet ein Geheimnis nicht aus Versehen im Log oder in einer Fehlermeldung.
- Der Log-Filter ersetzt zusätzlich alle Werte, die in dieser Sitzung aus dem Tresor gelesen wurden, und typische Muster wie `ghp_…`, `github_pat_…`, `sk-…` und `Bearer …`.
- Git bekommt Tokens nie über die Befehlszeile, weil andere Programme die Befehlszeile sehen können. Stattdessen über Umgebungsvariablen für Git (`GIT_CONFIG_COUNT` und Verwandte) oder über den Git Credential Manager.
- Ein Test prüft nach jedem Testlauf, dass im Log keines der Test-Geheimnisse steht.

### 3.3 Adapter allgemein

Jede Adapter-Art hat eine abstrakte Basisklasse. Jeder Adapter beschreibt sich selbst, damit Dialoge automatisch entstehen können.

```python
@dataclass(frozen=True)
class AccountField:
    key: str               # zum Beispiel "url" oder "token"
    label: str             # "Serveradresse"
    secret: bool = False   # True: landet im Tresor, nie in der Datenbank
    required: bool = True
    default: str = ""

@dataclass(frozen=True)
class TestResult:
    ok: bool
    text: str              # einfaches Deutsch, das Wichtigste vorne
    details: str = ""      # technische Meldung, ohne Geheimnisse

class Adapter(ABC):
    kind: ClassVar[str]              # "github", "ollama", "windows" ...
    display_name: ClassVar[str]      # "GitHub", "Ollama" ...
    account_fields: ClassVar[list[AccountField]]

    @abstractmethod
    def test_connection(self) -> TestResult: ...
```

Das Register ordnet jeder Adapter-Art ihre Adapter zu. Adapter werden erst beim ersten Gebrauch importiert. So bleiben optionale Bibliotheken optional, wie bei `BACKENDS` im Chatbot.

```python
ADAPTERS = {
    "platform": {"github": "cockpit.platforms.github:GitHubPlatform"},
    "ai": {"ollama": "cockpit.ai.ollama:OllamaProvider"},
    "vault": {"windows": "...", "vault_file": "..."},
    "automation": {"none": "cockpit.automation.none:NoAutomation"},
    "email": {},
}
```

### 3.4 Plattform-Adapter

Das Wichtigste ist die Abfrage der Fähigkeiten (Konzept 6.3).

```python
class Capability(Enum):
    CREATE_REPO = auto()
    DELETE_REPO = auto()
    ARCHIVE = auto()
    CHANGE_VISIBILITY = auto()
    ORGANIZATIONS = auto()
    NOREPLY_EMAIL = auto()
    RELEASES = auto()
    STARS = auto()
    FORKS = auto()
    ISSUES = auto()
    COMMENTS = auto()
    DOWNLOAD_COUNTS = auto()
    PULL_REQUESTS = auto()
    SECURITY_ALERTS = auto()

@dataclass(frozen=True)
class Availability:
    available: bool
    reason: str = ""     # "Dem Token fehlt das Recht zum Löschen."

class Platform(Adapter):
    def capabilities(self) -> set[Capability]: ...
        # was die Plattform grundsätzlich kann
    def permissions(self) -> dict[Capability, Availability]: ...
        # was dieses Konto mit diesem Token darf
    def current_user(self) -> User: ...
    def organizations(self) -> list[str]: ...
    def noreply_email(self) -> str | None: ...
    def create_repo(self, spec: NewRepo) -> RepoRef: ...
    def repo_info(self, repo: RepoRef) -> RepoInfo: ...
    def set_visibility(self, repo, private: bool) -> None: ...
    def archive(self, repo) -> None: ...
    def delete(self, repo) -> None: ...
    def links(self, repo) -> RepoLinks: ...
    def git_credentials(self) -> GitCredentials: ...
```

Erweiterungen für spätere Phasen kommen als eigene kleine Schnittstellen dazu, zum Beispiel `SupportsReleases`, `SupportsIssues` und `SupportsPullRequests`. Ein Adapter erbt nur die, die er erfüllt. Die Fähigkeiten sagen dem Kern, welche davon da sind.

Fehler der Plattform:

- `NotAuthenticated`: Token fehlt, ist abgelaufen oder widerrufen.
- `PermissionMissing`: mit der fehlenden Fähigkeit.
- `SsoAuthorizationRequired`: mit dem Link zur Freigabeseite (Konzept 6.2).
- `PendingApproval`
- `ProtectedBranch`
- `NotFound`
- `NetworkError`

### 3.5 KI-Adapter

Aufgebaut wie `LLMBackend` im Chatbot, aber allgemeiner.

```python
class AIProvider(Adapter):
    is_local: ClassVar[bool]           # für die Datenschutz-Regel
    def models(self) -> list[str]: ...
    def model_capabilities(self, model: str) -> set[str]: ...   # "json", "stream"
    def start(self) -> None: ...       # nur Ollama: Server bei Bedarf starten
    def stop(self) -> None: ...        # nur selbst gestartete Server
    def complete(self, messages, *, model, system="",
                 schema: dict | None = None, max_tokens=None,
                 cancel: threading.Event | None = None) -> str | dict: ...
```

Features rufen die KI nie direkt. Sie fragen den Kern nach einer KI für eine Aufgabe: `services.ai_for("commit_message", project)`. Der Kern wählt den Anbieter aus den Einstellungen und der Feature-Einstellung, prüft die Datenschutz-Regel und fragt beim ersten Mal nach (Konzept 11).

### 3.6 Tresor-Adapter

```python
class Vault(Adapter):
    needs_unlock: ClassVar[bool]       # True bei der Tresordatei
    def is_unlocked(self) -> bool: ...
    def unlock(self, password: Secret) -> None: ...
    def lock(self) -> None: ...
    def read(self, name: str) -> Secret | None: ...
    def write(self, name: str, value: Secret) -> None: ...
    def delete(self, name: str) -> None: ...
    def names(self) -> list[str]: ...
```

- Namen haben die Form `codecockpit/account/<Nummer>/<Feld>`.
- Die Windows-Anmeldeinformationsverwaltung kann ihre Einträge nicht auflisten. Deshalb führt die Datenbank eine Liste der Namen, ohne die Werte.
- Der Wechsel der Speicherart (Konzept 5.2) ist eine Funktion im Kern: alles kopieren, jeden Wert zurücklesen und vergleichen, erst dann in der alten Speicherart löschen.
- In Phase 2 gibt es nur die Schnittstelle und eine Attrappe für Tests. Die echten Adapter kommen in Phase 3.

### 3.7 Automation und E-Mail

- `Automation`: Verbindung testen, prüfen ob die Instanz läuft, starten (nur lokal), Workflows einspielen, aktivieren und deaktivieren, Zugangsdaten in n8n anlegen, Webhook aufrufen, Status der Workflows. In Phase 2 gibt es nur die Schnittstelle und den Adapter „Keine Automation“.
- `EmailSender`: Test-E-Mail senden, Kontofelder, Vorlagen für Anbieter. In Phase 2 nur die Schnittstelle.

### 3.8 Das Feature-System

Jedes Feature beschreibt sich in seiner Datei `manifest.py`. Das Manifest ist Python und kein JSON, weil es auf Funktionen für Aktionen und Schritte verweist.

```python
MANIFEST = FeatureManifest(
    id="exe",
    name="Exe-Erstellung",
    description="Baut, testet und ersetzt die Exe des Projekts.",
    requires_features=[],                    # zum Beispiel ["versions"]
    requires_services=[],                    # "ai", "automation", "email"
    requires_capabilities=[],                # zum Beispiel [Capability.RELEASES]
    settings=[
        Choice("test_mode", "Testart", ["Start-Test", "Selbsttest"], "Start-Test"),
        Number("wait_seconds", "Wartezeit beim Start-Test in Sekunden", 10, min=3, max=120),
    ],
    actions=[Action("run_exe", "Exe starten", target=Target.EXE, ...)],
    steps=[Step("build_exe", "Exe wird erstellt", hook=Hook.AFTER_PUSH, ...)],
    introduction="EINFUEHRUNG.md",           # Schritt-für-Schritt-Einführung
    n8n_workflows="n8n_workflows",           # Ordner, falls vorhanden
    enabled_by_default=True,
)
```

Einstellungsfelder gibt es als `Text`, `Number`, `YesNo`, `Choice`, `MultiChoice`, `TimeOfDay`, `Weekday` und `AIProviderChoice`. Jedes Feld kennt seine deutsche Beschriftung, seinen Standardwert und seine Grenzen. Der Formular-Baukasten in der Oberfläche macht daraus Eingabefelder mit Label, Buddy und Accessible Name. Listen mit mehreren Kontrollkästchen werden als Liste mit Leertaste gebaut, wie in Konzept 8.4.

**Einführung:** Die Datei `EINFUEHRUNG.md` erklärt in kurzen Schritten, was man vor dem Einschalten einrichten muss und wo man das im Cockpit findet. Das Cockpit zeigt sie beim ersten Einschalten in einem lesbaren Textfeld. Ein Test prüft, dass jedes Feature eine Einführung hat.

**Finden der Features:** Das Register durchsucht das Paket `cockpit.features` und lädt aus jedem Unterpaket `MANIFEST`. Für die Exe sorgt die `.spec`-Datei dafür, dass alle Unterpakete eingebunden werden. Ein Test prüft, dass jedes Manifest gültig ist und keine Kennung doppelt vorkommt.

**Verwaltung:** Die Klasse `FeatureManager` beantwortet alle Fragen zum Zustand.

```python
class FeatureManager:
    def globally_enabled(self, feature_id) -> bool: ...
    def active(self, feature_id, project) -> bool: ...
        # global an, im Projekt an, und alle Voraussetzungen erfüllt
    def availability(self, feature_id, project) -> Availability: ...
        # mit Grund: "Benötigt Automation. Es ist keine eingerichtet."
    def missing_requirements(self, feature_id, project) -> list[Requirement]: ...
        # für die Frage "Beide einschalten?" aus Konzept 8.4
    def enable(self, feature_id, project, with_dependencies=False) -> None: ...
    def disable(self, feature_id, project) -> list[str]: ...
        # gibt zurück, welche anderen Features dadurch ausfallen
```

- Global an oder aus steht in der Datenbank.
- Pro Projekt steht die Liste der aktiven Features in `cockpit.toml` unter `[features]`. So wandert sie mit dem Projekt auf einen anderen Rechner (Konzept 7.1).
- Die Vorauswahl für neue Projekte ist eine Einstellung der Installation.
- Kreise in den Abhängigkeiten werden beim Laden erkannt und als Fehler gemeldet.

### 3.9 Aktionen

```python
@dataclass(frozen=True)
class Action:
    id: str
    text: str                                   # "Exe neu erstellen"
    target: Target                              # PROJECT, CODE oder EXE
    run: Callable[[ActionContext], None]
    availability: Callable[[ActionContext], Availability] | None = None
    is_default: bool = False                    # für Enter im Baum
    order: int = 100
```

Die Aktionsliste fragt Kern und aktive Features nach allen Aktionen für den markierten Eintrag. Nicht verfügbare Aktionen stehen mit Grund in der Liste. Der Kern bringt seine eigenen Aktionen auf demselben Weg ein, zum Beispiel „Änderungen hochladen“.

### 3.10 Der Ablauf-Motor

Die Einhängepunkte aus Konzept 3.3:

```python
class Hook(Enum):
    BEFORE_COMMIT_MESSAGE = 1
    COMMIT_MESSAGE = 2
    BEFORE_PUSH = 3
    AFTER_PUSH = 4
```

Ein Schritt:

```python
@dataclass(frozen=True)
class Step:
    id: str
    title: str                   # "Exe wird erstellt"
    hook: Hook
    run: Callable[[FlowContext], StepResult]
    order: int = 100

@dataclass
class StepResult:
    ok: bool
    text: str = ""               # für die Zusammenfassung am Ende
    details: str = ""
```

So arbeitet der Motor:

1. Er sammelt die Schritte des Kerns und aller für dieses Projekt aktiven Features und sortiert sie nach Einhängepunkt und Reihenfolge.
2. Er zählt nur die aktiven Schritte. Daraus entsteht „Schritt 3 von 5: Exe wird erstellt“.
3. Er führt die Schritte in einem Hintergrund-Thread aus. Jeder Schritt meldet Fortschritt und prüft das Abbruch-Signal.
4. Schlägt ein Schritt vor dem Hochladen fehl, bricht der Ablauf ab, und nichts wird hochgeladen.
5. Schlägt ein Schritt nach dem Hochladen fehl, laufen die anderen weiter. Die Zusammenfassung sagt klar, was nicht geklappt hat (Konzept 9.2).
6. Am Ende steht eine kurze Zusammenfassung als Text und Ansage.

**Rückfragen:** Ein Schritt kann über den Kontext eine Frage stellen, zum Beispiel `context.ask(ChoiceQuestion("README-Vorschlag", ["Übernehmen", "Bearbeiten", "Überspringen"]))`. Der Hintergrund-Thread wartet, bis die Oberfläche geantwortet hat. In Tests beantwortet eine Attrappe die Fragen.

**Sperre pro Projekt:** Pro Projekt läuft immer nur ein Ablauf. Ein zweiter wird mit Erklärung abgelehnt.

### 3.11 Der Behälter Services

```python
@dataclass
class Services:
    database: Database
    settings: Settings
    vault: Vault
    projects: ProjectStore
    accounts: AccountStore
    features: FeatureManager
    def platform_for(self, project) -> Platform: ...
    def ai_for(self, task: str, project) -> AIProvider | None: ...
    def automation(self) -> Automation: ...
    def email(self) -> EmailSender | None: ...
```

In Tests wird der Behälter mit Attrappen gefüllt.

### 3.12 Datenbank

- SQLite in `%APPDATA%\CodeCockpit\cockpit.db`.
- Die Versionsnummer steht in `PRAGMA user_version`. Jede Änderung am Aufbau ist ein nummerierter Umbau-Schritt.
- Tabellen in Phase 2: `settings`, `projects`, `accounts`, `vault_names`, `features_global`, `feature_settings`.
- Keine Tabelle enthält Geheimnisse. Ein Test prüft das mit Test-Geheimnissen.
- Zugriff aus mehreren Threads über eine Sperre, wie im Tagebuch.

### 3.13 Grundeinstellungen

Da es keine Profile gibt, hat die Installation eine einzige Sammlung von Einstellungen. In Phase 2 sind das:

- Projekte-Hauptordner
- Git-Name und Git-E-Mail-Adresse
- Standard-Sichtbarkeit neuer Repositories (Standard: privat)
- Standard-Lizenz (Standard: MIT)
- Vorauswahl der Features für neue Projekte
- Datenschutz-Regel: Code-Auszüge nur an lokale oder firmeninterne KI
- Branches und Pull Requests als Standard für neue Projekte (Standard: aus)

Einstellungen für Konten, KI-Anbieter, Automation und E-Mail kommen in den Phasen dazu, in denen es diese Dinge gibt. Der Dialog ist ein einfaches Formular mit „Speichern“ und „Abbrechen“.


## 4. Was Phase 2 liefert

Nach Phase 2 lässt sich das Cockpit starten und bedienen, kann aber noch keine Projekte hochladen.

Zuerst richte ich ein:

- die virtuelle Umgebung `Code\.venv`
- das lokale Git-Repository mit `.gitignore`
- die Umbenennung der Beispieltexte auf „Sie“

Dann baue ich:

- Das Hauptfenster mit Menüleiste. Es erscheinen nur Menüpunkte, die funktionieren.
- Das Menü Einstellungen mit den Grundeinstellungen.
- Das Menü Hilfe mit „Tastenkürzel“ (F1), „Letzte Meldung wiederholen“ (Strg+Umschalt+M), „Meldungen“ (Strg+Umschalt+L) und „Über CodeCockpit“.
- Den Projektbaum mit einem Testprojekt, damit Sie Ausklappen, automatisches Zuklappen und die Ansagen früh mit NVDA prüfen können.
- Die Aktionsliste mit Tab und Umschalt+Tab, zunächst mit Beispielaktionen.
- Das Feature-System, den Ablauf-Motor und alle Adapter-Schnittstellen, geprüft mit Test-Features und Attrappen.
- Automatische Tests und `checklisten\phase-02.md`.


## 5. Offene Fragen an Sie #pascal

Zurzeit gibt es keine offenen Fragen. Neue Fragen kommen hierher und sind mit #pascal markiert.

## 6. Beantwortete Fragen aus Phase 1

Die Antworten stehen mit Grund in ENTSCHEIDUNGEN.md. Kurz:

1. Git: mit winget installiert. Anleitung für andere Nutzer in `anleitungen\git-installieren.md`.
2. Referenz-Projekte: nach `Codecockpit\Referenz` verschoben.
3. Konzeptdatei: heißt jetzt `KONZEPT.md`.
4. Anrede: „Sie“.
5. Namen im Code: englisch, Kommentare und Texte deutsch.
6. Eigene virtuelle Umgebung `Code\.venv`. Die Exe braucht später kein installiertes Python. Die anderen Projekte müssen nicht angepasst werden.
7. Menüpunkte erscheinen erst, wenn sie funktionieren.
8. Projektbaum mit Testprojekt schon in Phase 2.
9. Strg+Umschalt+M wiederholt die letzte Meldung, Strg+Umschalt+L zeigt die Liste. Tastenkürzel im Menü Hilfe.
10. Getestet wird nur mit NVDA.
11. Keine Profile. Eine Installation ist ein Einsatzbereich.
12. Lokales Git-Repository zu Beginn von Phase 2.
13. Anmeldung bei GitHub: siehe Frage C.

Antworten auf die Fragen A bis D vom 24.09.2026:

- A: Commits des Cockpits mit dem Namen 1013hPascal und der noreply-Adresse von GitHub.
- B: Projekte-Hauptordner ist `C:\Users\pasca\Documents\ComputerProgrammieren\Github`.
- C: Beide Wege der Anmeldung werden angeboten, die Anmeldung im Browser als Standard.
- D: Der Paketmanager wird später ein eigenes Programm.
