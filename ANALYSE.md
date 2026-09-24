# Analyse der bestehenden Projekte (Phase 1)

Stand: 24.09.2026.

Untersucht wurden zwei Projekte im Ordner `Bestehende Projekte zum anschauen`:

- **Chatbot für Text**: lokaler Schreibassistent mit Ollama, Internetsuche, PDFs und Projekten.
- **Tagebuch**: verschlüsseltes Sprach-Tagebuch mit Ollama-Zusammenfassungen und Whisper.

Das Tagebuch hat viele Muster aus dem Chatbot übernommen und an einigen Stellen verbessert. Wo beide sich unterscheiden, steht unten, welche Variante das Cockpit nimmt.

Ich habe außerdem die Umgebung auf diesem Rechner geprüft. Die Ergebnisse stehen am Ende.


## 1. Aufbau

### Was ich gefunden habe

- Beide Projekte trennen **Logik** und **Oberfläche**. Beim Chatbot heißen die Pakete `core` und `ui`. Beim Tagebuch heißen sie `kern`, `ki`, `sprache` und `ui`.
- Die Logik importiert nie PySide6. Deshalb lässt sie sich ohne Oberfläche testen.
- Es gibt eine kurze Startdatei (`app.py` bzw. `main.py`). Sie richtet das Log ein, lädt die Einstellungen, baut das Hauptfenster und ruft danach `initial_focus()` auf.
- Das Fenster startet maximiert.
- Jedes Projekt hat eine Datei für Entscheidungen (`DECISIONS.md`) oder ein Konzept und eine Datei mit Tests für Barrierefreiheit (`ACCESSIBILITY_TESTS.md`).
- Die Modellnamen stehen an genau einer Stelle im Code (`config.py`).
- Der Chatbot hat eine klare Schnittstelle zum Sprachmodell (`core/llm.py`, Klasse `LLMBackend`) und eine Liste der Backends (`BACKENDS`). Das ist schon ein kleines Adapter-System.

### Was ich übernehme

- Trennung in Logik ohne Qt und Oberfläche mit Qt.
- Kurze Startdatei mit Log, Einstellungen, Hauptfenster und Anfangsfokus.
- Modellnamen und andere Standardwerte an einer Stelle.
- Die Idee aus `core/llm.py`: eine abstrakte Klasse, dazu eine Tabelle mit Namen und Fabriken. Im Cockpit gilt das für alle Adapter-Arten, nicht nur für die KI.
- Eine Datei für Entscheidungen, die ich laufend pflege (`ENTSCHEIDUNGEN.md`).

### Was ich anders mache und warum

- **Englische Namen im Code** wie beim Chatbot, mit deutschen Kommentaren und Texten. So hat es der Nutzer am 24.09.2026 entschieden, siehe ENTSCHEIDUNGEN.md.
- **Ein gemeinsames Paket `cockpit`** statt loser Pakete im Projektordner. So gibt es keine Namenskonflikte, und PyInstaller findet alles leichter.
- **Einstellungen nicht im Projektordner.** Das Tagebuch speichert `config.toml` neben dem Code. Bei einer Exe geht das nicht gut, weil der Exe-Ordner bei jedem Build ersetzt wird. Das Cockpit speichert seine Einstellungen deshalb im Benutzerdatenordner. Nur die Projekteinstellungen stehen im jeweiligen Projekt in `cockpit.toml`, so wie es das Konzept vorsieht.
- **Datenbank mit Versionsnummer.** Beide Projekte legen die Tabellen einfach an. Das Cockpit wird über viele Phasen wachsen. Deshalb bekommt die Datenbank eine Versionsnummer und kleine Umbau-Schritte (Migrationen).


## 2. Tastaturbedienung

### Was ich gefunden habe

- **Wenige Tab-Stopps.** Der Chatbot hat genau vier Bereiche im Kreis: Frage, Antwort, Aktionen, Verlauf. Schaltflächen wurden bewusst zu Listen, damit jeder Bereich nur einen Tab-Stopp braucht.
- **Aktionen als Liste.** Enter führt aus, Entf entfernt. Einträge erscheinen nur, wenn sie passen.
- **Bereiche direkt anspringen** mit Strg+1 bis Strg+4 und mit F6 und Umschalt+F6.
- **Menüs mit Alt-Kürzeln.** Ein Test prüft, dass kein Alt-Kürzel doppelt belegt ist. Tastenkürzel gelten auch bei geschlossenem Menü.
- **Kontextmenü** mit Menütaste und Umschalt+F10. Der Chatbot hat dafür eine eigene Menüklasse gebaut, weil Windows beide Tasten unterschiedlich meldet. Doppelte Ereignisse werden ausgefiltert.
- **Escape** bricht ab oder führt zurück. Im Tagebuch führt Escape aus jeder Unteransicht zurück zur Übersicht. Der Fokus landet dann auf dem Eintrag, von dem man kam.
- **Oberster Listeneintrag ist die wichtigste neue Aktion**, zum Beispiel „Was ich zu erzählen habe“ oder „Neuer Chat“.
- **Rückfragen:** Die sichere Antwort ist die Vorgabe. Escape wählt immer die sichere Antwort.
- **Umschalt+Enter** fügt im Chatbot einen echten Zeilenumbruch ein. Qt würde sonst ein unsichtbares Sonderzeichen einfügen, das auf der Braillezeile keine neue Zeile ergibt.
- **Tab in mehrzeiligen Feldern** wechselt im Tagebuch den Fokus, statt ein Tabzeichen einzufügen.
- **Hilfefenster mit F1** listet alle Tastenkürzel in einem lesbaren Textfeld.

### Was ich übernehme

- Wenige Tab-Stopps im Hauptfenster: Projektbaum und Aktionsliste. Das passt genau zum Konzept (Abschnitt 8.3).
- Aktionen als Liste mit Enter. Nicht verfügbare Aktionen bleiben aber sichtbar und nennen den Grund, so wie es das Konzept verlangt.
- F6 und Umschalt+F6 zum Wechseln der Bereiche, dazu Strg+1 und Strg+2.
- Menüs mit Alt-Kürzeln und den Test gegen doppelte Kürzel.
- Die Kontextmenü-Klasse aus dem Chatbot. Im Projektbaum öffnet die Menütaste die Aktionen des markierten Eintrags als Kontextmenü. So gibt es einen zweiten Weg zu denselben Aktionen.
- Escape führt zurück, und der Fokus landet auf dem Eintrag, von dem man kam.
- „Neues Projekt hochladen“ als oberster Eintrag im Baum.
- Rückfragen mit sicherer Vorgabe. Beim Löschen eines Repositories kommt die Eingabe des Namens dazu (Konzept 9.5).
- Das Textfeld aus dem Chatbot mit echtem Zeilenumbruch bei Umschalt+Enter. Dazu die Einstellung aus dem Tagebuch, dass Tab den Fokus wechselt.
- Hilfefenster mit F1.

### Was ich anders mache und warum

- **Zwei Fassungen des Textfelds werden eine.** Der Chatbot fängt Umschalt+Enter ab. Das Tagebuch fängt es bewusst nicht ab, weil es dort Nebenwirkungen auf die Pfeiltasten gab. Im Cockpit schreibt man vor allem Commit-Nachrichten und Antworten auf Issues. Ich nehme die Chatbot-Fassung, weil dort der Fehler mit dem Sonderzeichen belegt ist. Ein Test prüft die Pfeiltasten. Wenn du Probleme merkst, stelle ich um.
- **Aktionen nicht wegfallen lassen.** Im Chatbot verschwinden Aktionen, die gerade nicht passen. Das Konzept will, dass fehlende Rechte erklärt werden. Deshalb steht dann zum Beispiel „Repository löschen, nicht verfügbar: Dem Token fehlt das Recht zum Löschen“. Enter sagt den Grund noch einmal an.
- **Deutsche Standard-Schaltflächen.** Das Tagebuch benutzt an einer Stelle die Qt-Schaltfläche „Cancel“. Ohne deutsche Qt-Übersetzung steht dort englischer Text. Das Cockpit lädt die deutsche Qt-Übersetzung und beschriftet wichtige Schaltflächen selbst.


## 3. Barrierefreiheit

### Was ich gefunden habe

- **Nur Accessible Name, keine Beschreibung.** Die Funktion `name_widget` setzt bewusst keine Beschreibung. Grund aus deiner Rückmeldung: Die Braillezeile zeigt sonst Name, Rolle und Beschreibung, und das ist zu lang. Ein Test prüft, dass kein Steuerelement eine Beschreibung hat.
- **Beschriftungen mit Buddy.** Im Tagebuch hat jedes Eingabefeld ein Label mit `setBuddy` und zusätzlich einen Accessible Name.
- **Ansagen über echte Qt-Ereignisse.** Die Klasse `Announcer` sendet ab Qt 6.8 ein `QAccessibleAnnouncementEvent`. Es gibt zwei Stufen: höflich und dringend. Der Fokus wird dabei nicht verschoben. Jede Ansage steht zusätzlich im Log. So lässt sich prüfen, ob sie ausgelöst wurde.
- **Barrierefreie Menüs.** Ohne eigenen Namen sagt NVDA beim Öffnen nur den Programmnamen. Die Klasse `AccessibleMenu` setzt einen Namen, markiert den ersten Eintrag und meldet ihn nach 200 Millisekunden noch einmal. Chatbot und Tagebuch haben dafür zwei leicht verschiedene Fassungen.
- **Kurze Texte.** Ansagen und Namen erklären keine Tasten. Die Erklärungen stehen nur in der Hilfe.
- **Das Wichtigste vorne.** Zum Beispiel „Eintrag vom 21.09.2026“ oder „Suchergebnisse für X: 3 Treffer“.
- **Lange Texte in Zeilen.** Der Chatbot schreibt Antworten mit einem Satz pro Zeile und bricht nach 70 Zeichen um. So bewegen die Pfeiltasten Zeile für Zeile.
- **Keine festen Farben.** Ein Test prüft, dass kein Stylesheet Farben setzt. So bleibt der Hochkontrast wirksam.
- **Hintergrund stört nicht.** Das Tagebuch sagt eine fertige Zusammenfassung nur an, wenn man sie gerade ansieht. Sonst würden viele Ansagen beim Start stören.
- **Statuszeile lesbar.** Im Tagebuch ist die Statuszeile per Tastatur auswählbar und hat einen Namen.
- **Zwei Test-Ebenen.** Automatische Tests prüfen Namen, Tab-Reihenfolge, Menüs und Ansagen. Eine Checkliste für NVDA prüft den Rest mit echter Sprachausgabe.

### Was ich übernehme

- `name_widget` ohne Beschreibung und den Test dazu.
- Label mit Buddy plus Accessible Name bei jedem Eingabefeld.
- Den `Announcer` mit zwei Stufen und Eintrag im Log.
- `AccessibleMenu`. Ich führe die beiden Fassungen zusammen: Name setzen, ersten Eintrag beim Öffnen markieren, Fokusmeldung mit genauem Eintrag wiederholen.
- Kurze Namen und Ansagen, Erklärungen nur in der Hilfe.
- Das Wichtigste vorne in jeder Zeile. Das verlangt auch das Konzept.
- Einen Satz pro Zeile bei langen Texten, zum Beispiel bei Fehlerdetails und bei der Prüfung der Exe-Einrichtung.
- Den Test gegen feste Farben.
- Die Regel, dass Hintergrundarbeit weder den Fokus verschiebt noch viele Ansagen auslöst.
- Automatische Tests plus eine Testanleitung für NVDA in jeder Phase.

### Was ich anders mache und warum

- **Ein eigenes Fehlerfenster.** Das Konzept will einfache Fehlertexte und „Details anzeigen“. Das Qt-Meldungsfenster hat dafür einen Knopf, der aber schwer zu bedienen ist. Ich baue ein kleines Fenster: oben der einfache Text als lesbares Feld, darunter „Details anzeigen“. Der Knopf öffnet ein zweites Feld und setzt den Fokus dorthin.
- **Letzte Meldungen wiederholen.** Ansagen sind schnell weg. Ich schlage ein Tastenkürzel vor, das die letzte Meldung noch einmal ansagt, und eine Liste der letzten Meldungen. Dazu habe ich eine Frage in PLAN.md.
- **Der Projektbaum ist neu.** Keines der beiden Projekte benutzt einen Baum. Beide arbeiten mit Listen und Menüs. Der Baum mit automatischem Zuklappen ist deshalb das größte Risiko für die Barrierefreiheit. Ich schlage vor, ihn schon in Phase 2 als Probe mit Beispieldaten zu bauen. Dann kannst du ihn früh mit NVDA testen.
- **Fortschritt als Text.** Das Konzept will „Schritt 3 von 5“. Die Projekte kennen nur einzelne Statusmeldungen. Das Cockpit bekommt eine gemeinsame Fortschrittsanzeige für alle Abläufe. Sie sagt jeden Schritt höflich an und das Ende als Zusammenfassung.


## 4. Anbindung an Ollama

### Was ich gefunden habe

- **Eigener HTTP-Client mit `httpx`**, kein Ollama-Paket. Kurze Wartezeit für den Verbindungsaufbau (5 Sekunden), lange für die Antwort.
- **Ollama wird bei Bedarf selbst gestartet** (`OllamaServer`). Läuft es schon, wird es mitbenutzt und beim Beenden nicht angetastet. Beim Beenden werden auch die Kindprozesse beendet, sonst bleibt Arbeitsspeicher belegt.
- **Fähigkeiten je Modell** fragt der Chatbot über `/api/show` ab (Werkzeuge, Denken, Bilder). Fehlt eine Fähigkeit, sagt die App das an.
- **Strukturierte Antworten.** Das Tagebuch lässt Ollama JSON nach einem Schema liefern (`format`). Das ist robust für Vorschläge.
- **Abbruch** über ein `threading.Event`. Der Chatbot schließt dazu die laufende Verbindung.
- **Verständliche Fehler** über eigene Fehlerklassen (`LLMError`, `OllamaFehler`).
- **Test-Attrappe.** Der Chatbot hat ein `FakeBackend`, das vorbereitete Antworten liefert.
- **Fehlendes Modell** wird mit dem genauen Befehl gemeldet („ollama pull …“).

### Was ich übernehme

- `httpx` statt `requests`. Beide Projekte nutzen es schon, und es kann Streaming und genaue Wartezeiten. Das Konzept nennt `requests`. Ich weiche bewusst ab und schreibe das in die Entscheidungen.
- Das Starten und Mitbenutzen von Ollama, samt Beenden der Kindprozesse.
- Die Abfrage der Fähigkeiten, verallgemeinert für alle KI-Anbieter.
- JSON-Antworten mit Schema für alle Vorschläge (Commit-Nachricht, README-Vorschläge).
- Abbruch über `threading.Event`.
- Eigene Fehlerklassen mit einfachem Text.
- Test-Attrappen für jede Adapter-Art.

### Was ich anders mache und warum

- **KI ist nur ein Adapter unter mehreren.** Der Chatbot kennt nur Ollama. Das Cockpit braucht fünf KI-Anbieter und zusätzlich Plattform, Tresor, Automation und E-Mail. Alle folgen demselben Muster.
- **Keine GPU-Einstellungen.** Der Chatbot stellt Vulkan, Flash Attention und Prioritäten ein. Das braucht das Cockpit nicht. Es nutzt Ollama so, wie es läuft. Das Tagebuch hat diese Einstellungen aus demselben Grund weggelassen.
- **KI darf fehlen.** Der Chatbot kann ohne Modell nicht arbeiten. Im Cockpit ist KI ein Zusatz. Fehlt Ollama, sagt das Cockpit das einmal und arbeitet ohne KI weiter. Das entspricht dem Tagebuch.
- **Datenschutz-Prüfung vor jeder Anfrage.** Neu im Cockpit: Bevor Code-Auszüge an einen Anbieter außerhalb des Rechners gehen, prüft der Kern die Regel des Profils und fragt beim ersten Mal nach (Konzept Abschnitt 11).


## 5. Hintergrundverarbeitung

### Was ich gefunden habe

- **Eine Klasse `Task` auf Basis von `QThread`.** Sie führt eine Funktion aus und meldet Fortschritt, Ergebnis, Fehler und Abbruch über Signale. Kein Fehler geht still verloren. Unerwartete Fehler kommen ins Log und als Meldung an die Oberfläche.
- **Warteschlange im Tagebuch.** Aufträge laufen nacheinander. Ist Ollama nicht erreichbar, wird das einmal gemeldet, und die Warteschlange hält an.
- **Sauberes Beenden.** Das Tagebuch wartet beim Schließen auf laufende Aufgaben, weil ein zerstörter Thread das Programm abstürzen lässt. Das Warten passiert nur einmal.
- **Eingabe bleibt erhalten.** Bei Abbruch oder Fehler kommt die Frage im Chatbot zurück ins Feld.

### Was ich übernehme

- Die Klasse `Task` fast unverändert.
- Die Warteschlange. Im Cockpit läuft pro Projekt immer nur ein Git-Vorgang gleichzeitig. Ein zweiter Auftrag für dasselbe Projekt wartet oder wird mit Erklärung abgelehnt.
- Das saubere Beenden mit Warten auf laufende Aufgaben.
- Eingaben gehen bei Fehlern nie verloren, zum Beispiel die Commit-Nachricht.

### Was ich anders mache und warum

- **Rückfragen mitten im Ablauf.** Ein Ablauf wie „Änderungen hochladen“ läuft im Hintergrund, braucht aber manchmal eine Entscheidung, zum Beispiel bei einem README-Vorschlag. Die Projekte kennen das nicht. Ich baue eine kleine Brücke: Der Hintergrund-Schritt stellt eine Frage, die Oberfläche zeigt einen Dialog, und der Schritt wartet auf die Antwort. In Tests beantwortet eine Attrappe die Fragen.
- **Gemeinsamer Ablauf-Motor.** Statt jede Aufgabe einzeln zu verdrahten, gibt es einen Motor, der die aktiven Schritte sammelt, zählt, ansagt und Fehler richtig behandelt (Konzept 3.3 und 9.2).


## 6. Einstellungen

### Was ich gefunden habe

- **Eine Dataclass `Config`** mit Standardwerten. Unbekannte oder falsch getippte Werte werden beim Laden ignoriert. So startet das Programm auch mit einer kaputten Datei.
- **Chatbot:** JSON in `%APPDATA%\TextChat\config.json`. Schalter im Menü mit Häkchen, jede Änderung wird sofort gespeichert und angesagt.
- **Tagebuch:** TOML-Datei `config.toml` im Projektordner, Änderungen erst beim nächsten Start.
- **Datenordner** mit Umgebungsvariable überschreibbar (`TEXTCHAT_HOME`, `TAGEBUCH_HOME`). Das nutzen die Tests.
- **Tavily-Schlüssel im Klartext** in der `config.json` des Chatbots.
- **Verschlüsselung im Tagebuch:** Scrypt und AES-GCM mit eigener Nonce pro Feld, Prüftext zum Erkennen eines falschen Passworts. Der Schlüssel liegt nur im Arbeitsspeicher.

### Was ich übernehme

- Dataclasses mit Standardwerten und nachsichtigem Laden.
- Datenordner in `%APPDATA%\CodeCockpit`, überschreibbar mit `CODECOCKPIT_HOME` für Tests.
- Sofort speichern und ansagen bei Schaltern im Menü.
- Die Verschlüsselung aus dem Tagebuch (`krypto.py`) für die Tresordatei und die Sicherung. Das Konzept verlangt genau dieses Verfahren.
- TOML für `cockpit.toml` in jedem Projekt, weil es gut lesbar ist.

### Was ich anders mache und warum

- **Nie Geheimnisse in Einstellungen.** Der Tavily-Schlüssel im Klartext wäre im Cockpit ein Verstoß gegen das Konzept. Alle Geheimnisse liegen im Tresor. Die Einstellungen enthalten nur einen Verweis.
- **Einstellungen in SQLite.** Profile, Konten, KI-Anbieter und Feature-Einstellungen hängen voneinander ab. Das Konzept sieht dafür SQLite vor. Eine einzelne Datei reicht dafür nicht.
- **Einstellungsformulare werden erzeugt.** Features beschreiben ihre Einstellungen, und der Einstellungsdialog baut daraus ein barrierefreies Formular (Konzept 3.2). Jedes Feld bekommt automatisch Label, Buddy und Namen.
- **Schreiben von TOML.** Das Tagebuch schreibt TOML mit einer eigenen kleinen Funktion. Für `cockpit.toml` mit Abschnitten reicht das nicht. Ich nehme dafür die kleine Bibliothek `tomli-w`.
- **Schutz im Log.** Ein Filter im Log ersetzt bekannte Geheimnisse und typische Token-Muster durch Sternchen, bevor etwas geschrieben wird. Die Projekte brauchten das nicht, das Cockpit schon.


## 7. Tests

### Was ich gefunden habe

- `pytest` mit `pytest-qt`, ohne Bildschirm (`QT_QPA_PLATFORM=offscreen`).
- Chatbot 120 schnelle Tests, Tagebuch 154 Tests.
- Temporäre Datenordner pro Test.
- Das Tagebuch setzt nach jedem Test den `Announcer` zurück. Ohne das stürzt der nächste Test ab, weil das alte Fenster schon zerstört ist.
- Tests prüfen gesendete Ansagen über den Verlauf im `Announcer`.

### Was ich übernehme

Alles davon. Dazu kommen Attrappen für jede Adapter-Art und Tests für Tresor, Sicherheitsprüfung, Feature-Abhängigkeiten, Versionsberechnung, Rückgängig-Funktionen und Lizenzeinordnung, wie im Konzept verlangt.


## 8. Umgebung auf diesem Rechner

- Python 3.14.6 in `C:\Python314`.
- PySide6 6.11.1. Das reicht für die Ansagen über `QAccessibleAnnouncementEvent` (ab Qt 6.8).
- `cryptography` und `httpx` sind installiert, `keyring` noch nicht.
- Ollama ist installiert.
- Node.js ist installiert, n8n habe ich nicht gefunden.
- Git fehlte zunächst. Am 24.09.2026 wurde Git für Windows 2.55.0 mit winget installiert, samt Git Credential Manager.
- Chatbot und Tagebuch liegen seit dem 24.09.2026 in `Codecockpit\Referenz`, außerhalb des Repositories.
