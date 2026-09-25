# Entscheidungen

Hier steht alles, was vom Konzept abweicht oder es ergänzt, jeweils mit Grund.

**Wo diese Datei und KONZEPT.md sich widersprechen, gilt diese Datei.**

Neue Einträge kommen ans Ende.


## 24.09.2026: Antworten auf die Fragen aus Phase 1

### Keine Profile

- Entscheidung: Es gibt keine Profile „Privat“ und „Beruflich“. Eine Installation ist ein Einsatzbereich.
- Grund: Beruflich läuft das Cockpit auf einem anderen Rechner. Die Trennung entsteht durch die getrennte Installation.
- Folgen für das Konzept:
  - Abschnitt 4 (Profile) entfällt.
  - Alles, was dort pro Profil stand, ist eine Einstellung der Installation: Plattform-Konto, KI-Anbieter, Automation, E-Mail-Konto und Empfänger, Projekte-Hauptordner, Standardwerte für neue Projekte, Git-Identität, Datenschutz-Regel für die KI, Branches und Pull Requests als Standard.
  - Die Datenschutz-Regel für die KI (Konzept 11) und die Vorgabe für Branches und Pull Requests (Konzept 10.14) sind normale Einstellungen. Auf einem Firmenrechner stellt man sie einmal ein.
  - Das Menü Ansicht mit der Wahl des Profils entfällt.
  - Im Projektbaum wird kein Profil genannt.
  - Der Wochenbericht (Konzept 10.9) ist ein einziger Bericht für alle Projekte.
  - Im Einrichtungsassistenten (Konzept 8.7) entfällt die Seite „Profil“.
  - Mehrere Konten gleicher Art bleiben möglich, zum Beispiel zwei GitHub-Konten. Jedes Projekt merkt sich sein Konto.
  - Export und Import der Einstellungen (Konzept 13.1) bleiben. So kann ein Team mit gleichen Einstellungen starten.

### Anrede „Sie“

- Entscheidung: Die Oberfläche sagt „Sie“.
- Grund: Das Cockpit ist ein Werkzeug für die Arbeit und soll auch in Firmen passen.
- Folge: Beispieltexte im Konzept mit „du“ werden umgestellt, zum Beispiel „Was haben Sie geändert?“.

### Englische Namen im Code

- Entscheidung: Pakete, Module, Klassen, Funktionen und Variablen haben englische Namen. Texte in der Oberfläche sind deutsch. Kommentare und Docstrings sind deutsch.
- Grund: Englische Namen sind üblich, besonders bei Code, der auf GitHub veröffentlicht wird und in Firmen gepflegt werden soll. Die deutschen Kommentare bleiben gut lesbar für den Nutzer.
- Folge: Die Paketstruktur in Konzept 14 wird übersetzt, siehe PLAN.md.

### Git für Windows

- Git wurde am 24.09.2026 mit winget installiert.
- Für andere Nutzer gibt es die Anleitung `anleitungen\git-installieren.md` mit winget, Chocolatey und der Webseite.
- Das Cockpit prüft beim Start, ob Git da ist. Fehlt es, zeigt es diese Anleitung. Umsetzung in Phase 3 im Einrichtungsassistenten.

### Referenz-Projekte außerhalb des Repositories

- Chatbot und Tagebuch liegen jetzt in `Codecockpit\Referenz`, nicht mehr im Ordner Code.
- Grund: Sie sollen nie im Repository des Cockpits landen. Der Nutzer löscht den Ordner, wenn das Cockpit fertig ist.

### Eigene virtuelle Umgebung

- Das Cockpit bekommt eine eigene Umgebung `Code\.venv` mit Python 3.14. Die Mindestversion bleibt 3.11.
- Die fertige Exe braucht kein installiertes Python. PyInstaller packt Python und alle Bibliotheken aus der Umgebung in die Exe.
- Die anderen Projekte müssen dafür nicht angepasst werden. Wenn sie später mit dem Cockpit eine Exe bekommen, legt das Feature Exe-Erstellung für jedes Projekt eine eigene Umgebung an (Konzept 10.4).

### Menüs wachsen mit den Phasen

- Ein Menüpunkt erscheint erst, wenn er funktioniert.

### Früher Test des Projektbaums

- Der Projektbaum wird schon in Phase 2 mit einem Testprojekt gebaut, damit er früh mit NVDA geprüft werden kann.

### Meldungen wiederholen

- Strg+Umschalt+M sagt die letzte Meldung noch einmal an.
- Strg+Umschalt+L öffnet eine Liste der letzten 50 Meldungen, neueste oben.
- Die Statuszeile ist kein eigener Tab-Stopp. Tab wechselt zwischen Projektbaum und Aktionsliste.
- Im Menü Hilfe steht „Tastenkürzel“ (F1) mit der Liste aller Tastenbefehle. Beide neuen Befehle stehen auch als Einträge im Menü Hilfe.

### Nur NVDA

- Getestet wird mit NVDA und Braillezeile. Die Testanleitungen beschreiben nur NVDA.

### httpx statt requests

- Für HTTP nimmt das Cockpit `httpx` statt `requests` (Konzept 14).
- Grund: Chatbot und Tagebuch nutzen es schon. Es kann Streaming und genaue Wartezeiten.

### Einführung für jedes Feature

- Jedes Feature bringt eine kurze Schritt-für-Schritt-Einführung mit. Sie erscheint, wenn man das Feature zum ersten Mal einschaltet, und ist danach über die Feature-Verwaltung erreichbar.
- Sie erklärt, was man vorher einrichten muss und wo man das im Cockpit macht, zum Beispiel ein Konto oder einen KI-Anbieter.
- Grund: Wunsch des Nutzers. Am Ende soll jeder Nutzer ohne fremde Hilfe zurechtkommen.
- Das Manifest jedes Features bekommt dafür ein eigenes Feld. In Phase 17 werden alle Einführungen noch einmal geprüft.


## 24.09.2026: Antworten auf die offenen Fragen A bis D

### Git-Identität für das Repository des Cockpits

- Name: `1013hPascal`
- E-Mail-Adresse: `94653295+1013hPascal@users.noreply.github.com`, die anonyme noreply-Adresse von GitHub. Die Nummer stammt aus der öffentlichen GitHub-Schnittstelle.
- Grund: Die private E-Mail-Adresse erscheint so nie öffentlich (Konzept 9.8).
- Die Identität wird nur im Repository des Cockpits gesetzt, nicht global für alle Repositories auf dem Rechner.

### Projekte-Hauptordner

- Standard: `C:\Users\pasca\Documents\ComputerProgrammieren\Github`.

### Anmeldung bei GitHub

- Beide Wege werden angeboten: Anmeldung im Browser über eine OAuth-App (Device Flow) als Standard und selbst erstellter Fine-grained Token als zweiter Weg.
- Die OAuth-App wird in Phase 4 gemeinsam registriert. Für den Token gibt es eine eigene Schritt-für-Schritt-Anleitung.
- Das Recht zum Löschen von Repositories wird erst abgefragt, wenn der Nutzer wirklich löschen will.

### Paketmanager

- Der Paketmanager für pip, winget und Chocolatey wird ein eigenes Programm, nicht Teil des Cockpits.
- Er entsteht irgendwann nach Phase 7 und übernimmt dann Bausteine des Cockpits.
- Vorschläge der KI für Installationsbefehle muss er gegen die echten Paketquellen prüfen, weil KI-Modelle Paketnamen erfinden können.


## 24.09.2026: Entscheidungen in Phase 2

### Einhängepunkt für das Hochladen selbst

- Neben den vier Einhängepunkten aus Konzept 3.3 gibt es den Punkt PUSH. Dort sitzt der Schritt des Kerns, der wirklich hochlädt.
- Bis einschließlich PUSH bricht ein Fehler den Ablauf ab. Danach laufen die übrigen Schritte weiter (Konzept 9.2).
- Schritte können auf bestimmte Abläufe beschränkt werden, zum Beispiel nur „Neues Projekt hochladen“.

### „Neues Projekt hochladen“ schon im Baum

- Der oberste Eintrag des Baums ist schon da, damit der Projektbaum vollständig getestet werden kann. Enter sagt an: „Diese Funktion kommt in Phase 5.“
- Das ist eine bewusste Ausnahme von „Menüpunkte erst, wenn sie funktionieren“.

### Projekte neu einlesen

- Menü Datei, „Projekte neu einlesen“ mit Strg+R. F5 bleibt für „Rückmeldungen jetzt abfragen“ reserviert (Konzept 8.1).

### Reihenfolge im Baum

- Bis Phase 5 gibt es kein Datum des letzten Hochladens. Bis dahin stehen die Projekte mit der jüngsten Änderung im Ordner Code oben.

### Aktionen im Kontextmenü

- Die Menütaste im Baum zeigt dieselben Aktionen wie die Aktionsliste. So gibt es zwei Wege zu jeder Aktion.

### Selbsttest und Testdaten

- `main.py --selbsttest` startet das Cockpit, lässt es kurz laufen und beendet es mit Code 0 (Konzept 10.4). Das braucht später die Exe-Erstellung für das Cockpit selbst.
- `start_testdaten.bat` startet mit Beispielprojekten in einem eigenen Ordner. Die echten Daten bleiben unberührt.

### Einstellungsfelder

- Einstellungsfelder werden so geschrieben: Kennung, Beschriftung, Standardwert, alles Weitere mit Namen. Beispiel: `Choice("test_mode", "Testart", "Start-Test", options=(...))`.
- Das Feld „KI-Anbieter wählen“ kommt erst in Phase 7, wenn es KI-Anbieter gibt.


## 25.09.2026: Änderungen nach dem NVDA-Test von Phase 2

### Projektliste statt Projektbaum

- Der Qt-Baum (QTreeView) hat den Test nicht bestanden: NVDA sagte bei Pfeiltasten nicht „ausgeklappt“ oder „zugeklappt“, und nach dem Zuklappen waren Projekte darüber oder darunter nicht mehr erreichbar.
- Ersatz: eine normale Liste. Beim Ausklappen werden Code und Exe als eigene Zeilen unter dem Projekt eingefügt. Das Projekt heißt dann „PDF-Chat, ausgeklappt“. Beim Aus- und Zuklappen kommt eine kurze Ansage.
- Bedienung nach Wunsch des Nutzers: Pfeil rechts, Leertaste oder Enter klappt ein Projekt auf. Pfeil links auf Code oder Exe klappt zu und führt zurück zum Projekt. Leertaste oder Enter auf einem offenen Projekt klappt es zu.
- Weiter gilt: Es ist immer höchstens ein Projekt offen.

### Listen statt schreibgeschützter Textfelder

- Tastenkürzel, Anleitungen, „Über CodeCockpit“ und die Details im Fehlerfenster sind Listen mit einer Zeile pro Eintrag. In den schreibgeschützten Textfeldern gab es keinen Cursor, NVDA las nur die erste Zeile.
- Strg+C kopiert in diesen Listen die markierte Zeile, zum Beispiel einen Befehl aus einer Anleitung.
- Das Fehlerfenster zeigt die Meldung wie ein normales Windows-Meldungsfenster als Text, der Fokus steht auf „OK“. Die Meldung wird zusätzlich angesagt.
- Tastenkürzel stehen als „Funktion, Taste“, zum Beispiel „Projekte neu einlesen, Strg+R“, so wie NVDA es aus Menüs kennt.

### Statuszeile

- NVDA+Ende (Laptop-Belegung: NVDA+Umschalt+Ende) ist ein Befehl von NVDA. Die Statuszeile von Qt erkennt NVDA damit nicht. Das ist nicht wichtig, weil Strg+Umschalt+M die letzte Meldung wiederholt. Der Prüfpunkt entfällt.

### Fokus nach dem Öffnen eines Fensters

- Alle Fenster (Anleitungen, Tastenkürzel, Meldungen, Fehler, Grundeinstellungen) setzen ihren Fokus kurz nach dem Öffnen noch einmal und senden NVDA ein Fokus-Ereignis, bei Listen für die markierte Zeile.
- Grund: Beim Öffnen aus einem Menü zeigte die Braillezeile sonst noch den alten Fokus im Hauptfenster. Baustein dafür: FocusDialog in cockpit/ui/common.py. Neue Fenster nutzen ihn ebenfalls.


## 25.09.2026: Entscheidungen in Phase 3

### Bibliotheken

- `keyring` für die Windows-Anmeldeinformationsverwaltung und `cryptography` für die Tresordatei, wie in Konzept 14. Der Nutzer hat zugestimmt.

### Tresordatei

- Verfahren wie im Tagebuch: Scrypt und AES-GCM. Scrypt mit n = 2 hoch 15, etwa 32 MB Speicher, unter einer Sekunde.
- Auch die Namen der Einträge sind verschlüsselt. Lesbar ist nur der Kopf mit den Parametern, und der ist in die Verschlüsselung eingebunden.
- Mindestlänge des Master-Passworts: 8 Zeichen.
- Wird beim Start das Master-Passwort abgebrochen, startet das Cockpit mit gesperrtem Tresor. Entsperren geht über das Menü Konten.
- Automatisch sperren nach Inaktivität ist einstellbar, Standard „nie“. Es gilt nur für die Tresordatei.

### Wechsel der Speicherart

- Alle Einträge werden kopiert und zurückgelesen. Erst wenn alles stimmt, werden sie in der alten Speicherart gelöscht. Die alte Tresordatei wird danach gelöscht.

### Einrichtungsassistent

- Eigene Umsetzung statt QWizard, damit Fokus und Ansagen verlässlich sind.
- Seiten in Phase 3: Willkommen, Git, Tresor, Projekte-Hauptordner, Git-Identität, Zusammenfassung. Die Seite „Profil“ entfällt (keine Profile). Die Seiten für Plattform-Konto, KI, Automation, E-Mail und Features kommen in den jeweiligen Phasen dazu.
- Neu gegenüber dem Konzept ist die Seite „Git“: Sie prüft, ob Git installiert ist, und zeigt sonst die Anleitung.
- Der Assistent lässt sich über Einstellungen, „Einrichtungsassistent …“ erneut starten.

### Menü Konten

- Alt+O, weil Alt+K schon zur Beschriftung „Aktionen“ gehört.
- „Tresor sperren“ und „Tresor entsperren …“ erscheinen nur bei der Tresordatei.

### Testplattform

- Bis zur echten GitHub-Anbindung gibt es in den Testdaten eine „Testplattform“, damit die Kontenverwaltung mit NVDA getestet werden kann. Sie erscheint nur mit `start_testdaten.bat`.
- Test-Zugangsdaten in der Windows-Anmeldeinformationsverwaltung stehen unter dem Namen „CodeCockpit Testdaten“ und werden beim nächsten Start mit Testdaten gelöscht.
- Ein zweiter Start mit Testdaten, während noch ein Cockpit mit Testdaten offen ist, meldet das verständlich und löscht nichts.

### Hinweis auf Sicherung

- Konzept 5.6 verlangt nach Änderungen an Konten oder Tresor einen Hinweis auf eine neue Sicherung. Die Sicherung kommt in Phase 17, der Hinweis deshalb auch.

### Nach dem NVDA-Test von Phase 3

- Auf der Tresor-Seite des Assistenten steht der Fokus zuerst in der Erklärung. Mit Tab geht es zur Auswahl.
- Die Auswahl der Speicherart ist eine Liste statt zweier Auswahlschalter. NVDA meldete bei den Auswahlschaltern beide als „markiert“. Grundsatz ab jetzt: einfache Auswahl als Liste, wie in den Referenz-Projekten.
- Nach einer erledigten Aktion in einem Einstellungsfenster springt der Fokus auf „Schließen“.
- Die Kontenverwaltung hat am Ende der Liste den Eintrag „Wofür sind Konten? …“ mit einer Erklärung.
- Automatisches Sperren prüft alle 15 Sekunden die Zeit seit der letzten Eingabe. So zählt auch Standby mit.
- E-Mail-Adresse für Commits: Der Nutzer nimmt künftig die noreply-Adresse von GitHub. Seine bisherigen öffentlichen Commits tragen noch die private Adresse. Sie bleiben unverändert, denn Commits umzuschreiben würde die Geschichte auf der Plattform ändern (Konzept 9.7).
- Master-Passwort erst bei Bedarf: Anders als in Konzept 5.2 wird das Master-Passwort nicht beim Start abgefragt, sondern erst, wenn Zugangsdaten gebraucht werden. Wunsch des Nutzers. Die Kontenliste lässt sich ohne Passwort ansehen.
- Ansagen nach einem Fokuswechsel kommen mit kurzer Verzögerung (announce_after_focus), sonst übertönt NVDA sie.
- Ansagen hängen am Steuerelement mit dem Fokus, nicht mehr fest am Hauptfenster. NVDA liest nur Ansagen aus dem Fenster, das vorne ist. Aus Dialogen kam deshalb vorher nichts an. Ansagen, während das Cockpit nicht vorne ist, werden beim Zurückkehren nachgeholt.
- Wichtige Bestätigungen kommen als Meldung mit OK: Master-Passwort geändert, Speicherart gewechselt, Tresor automatisch gesperrt. Wunsch des Nutzers.
- Jede Ansage wird etwa eine halbe Sekunde verzögert gesendet, an das Steuerelement, das dann den Fokus hat. Ein Fokuswechsel direkt nach einer Ansage hat sie in NVDA sonst abgebrochen.


## 25.09.2026: Entscheidungen in Phase 4

### Bibliotheken

- `httpx` für alle Verbindungen, wie schon festgelegt. `truststore`, damit Zertifikate aus dem Windows-Zertifikatsspeicher gelten (Konzept 6.2).

### Anmeldung im Browser

- Device Flow einer OAuth-App mit öffentlicher Client-ID, ohne Client Secret. Anleitung zur Registrierung: `anleitungen\github-oauth-app-registrieren.md`.
- Rechte bei der Anmeldung: repo, read:org und workflow. Das Recht zum Löschen (delete_repo) fragt das Cockpit erst an, wenn wirklich gelöscht werden soll (Phase 5).
- Nur für github.com. GitHub Enterprise Server bräuchte eine eigene OAuth-App auf dem Firmenserver. Dort bleibt der selbst erstellte Token.
- Der Token aus dem Browser erscheint nie im Eingabefeld. Er geht direkt in den Tresor.

### Selbst erstellter Token

- Empfohlen ist ein Fine-grained Token. Anleitung mit den nötigen Rechten: `anleitungen\github-token-erstellen.md`, auch im Menü Hilfe.
- Bei Fine-grained Tokens meldet GitHub keine Rechte im Voraus. Das Cockpit erklärt fehlende Rechte deshalb erst beim ersten Versuch.

### Verbindungstest

- Läuft im Hintergrund, die Oberfläche bleibt bedienbar. Das Ergebnis erscheint als Meldungsfenster, weil Ansagen in Dialogen noch nicht zuverlässig sind (TODO.md).
- Nennt Benutzername und Organisationen und trägt den Benutzernamen selbst ein.
- Bei Single Sign-On bietet das Cockpit an, die Freigabeseite im Browser zu öffnen.

### Einrichtungsassistent

- Neue Seite „GitHub-Konto“ nach dem Tresor. Die Seite Git-Identität kann die anonyme noreply-Adresse vom GitHub-Konto übernehmen.

### Git und Token

- Git bekommt den Token später über Umgebungsvariablen (GIT_CONFIG_COUNT und http.extraheader), nie über die Befehlszeile. Der Log-Filter maskiert auch diese kodierte Form.
- Konto-Fenster nach dem NVDA-Test: zuerst eine Erklärung als Liste, dann „Im Browser anmelden …“, dann die Felder für den Weg mit Token samt „Anleitung für den Token …“. Gleich im Assistenten und in der Kontenverwaltung. Beim Bearbeiten eines vorhandenen Kontos beginnt der Fokus im ersten Feld. Jeder Adapter kann seine Erklärung mitbringen (account_explanation).
- Konto-Fenster, zweite Fassung nach dem NVDA-Test: Nach der Erklärung wählt man zwischen „Im Browser anmelden …“ und „Mit Token anmelden …“. Jeder Weg zeigt danach nur seine Felder. Felder, die das Cockpit selbst füllt (auto, bei GitHub der Benutzername), erscheinen nie. Beim Speichern mit neuem Token testet das Cockpit erst die Verbindung und speichert nur, wenn sie klappt.


## 25.09.2026: Antworten auf die Fragen zu Phase 5

Die Fragen und Antworten stehen in `fragen\phase-05.md`.

### Grundsatz: wie Git und GitHub

- Das Cockpit macht alles so, wie es Git im Terminal und GitHub Desktop machen. Es nutzt dieselben Git-Befehle und dieselben Voreinstellungen.
- Weicht es davon ab, steht der Grund in dieser Datei. Die feste Ausnahme: nie ein force push.
- Ziel: Man braucht für die Arbeit mit Git und GitHub kein Terminal mehr.

### Aufteilung von Phase 5

- Phase 5 kommt in sechs Teilschritten, jeder mit eigenen Tests und eigener Checkliste `checklisten\phase-05a.md` bis `phase-05f.md`.
- 5a: Git-Grundlage, Git-Identität, Projekte hinzufügen, Umstellen oder Verknüpfen, Reparatur nach dem Verschieben, Stand der Projekte in der Projektliste, Repositories des Kontos in der Liste.
- 5b: Sicherheitsprüfung und .gitignore, Neues Projekt hochladen, Auf GitHub hochladen.
- 5c: Änderungen hochladen, Änderungen holen, Projekt von der Plattform herunterladen.
- 5d: Verlauf und Rückgängig machen, mit Sicherheitskopien.
- 5e: Links, Repository verwalten mit Mitarbeitern, Aus der Liste entfernen.
- 5f: Übersicht „Branches“ und Stash.
- Getestet wird mit einem privaten Repository „codecockpit-test“ auf dem echten Konto. Es wird in 5e mit dem Cockpit gelöscht. Die automatischen Tests arbeiten nur mit einer Attrappe.

### Git und Projekte

- Git-Identität: Das Cockpit trägt Name und E-Mail-Adresse nur im Repository ein, nie global. Hat ein Repository schon eine andere Identität, fragt es nach. Vorgabe: „Vorhandene behalten“.
- Projekte ohne Verbindung zur Plattform heißen in der Liste „noch nicht auf GitHub“ und haben bei „Code“ die Aktion „Auf GitHub hochladen“.
- Der Haupt-Branch neuer Repositories heißt „main“.
- Den Stand der Projekte fragt das Cockpit im Hintergrund ab: beim Start, nach jeder Aktion am Projekt und mit Strg+R. Ohne Ansage, der Fokus bleibt.
- Alle Repositories des eigenen Kontos erscheinen von selbst in der Projektliste. Liegt eines nicht auf dem Rechner, heißt es „nur auf GitHub“. Enter lädt es herunter. Repositories von Organisationen kommen über „Projekt von der Plattform herunterladen“. Die Einstellung „Neue Repositories automatisch herunterladen“ ist anfangs aus. „Aus der Liste entfernen“ merkt sich das Cockpit.

### Sicherheitsprüfung

- Eigene Regeln ohne neue Bibliothek für typische Tokens, Schlüssel, private Schlüssel, Passwort-Zeilen und `.env`-Dateien.
- „Kein Geheimnis“-Markierungen stehen in `cockpit.toml`: nur Dateiname und Fingerabdruck der Zeile, nie der Wert.
- Große Dateien: ab 50 MB Rückfrage mit der Vorgabe „In .gitignore aufnehmen“. Ab 100 MB stoppt das Cockpit, weil GitHub die Datei ablehnt.
- Private Daten wie Datenbanken und Logs: Rückfrage mit der Vorgabe „In .gitignore aufnehmen“.

### Hochladen und Holen

- Hochgeladen werden alle Änderungen, die die Sicherheitsprüfung durchlassen. Es gibt keine Auswahl einzelner Dateien.
- Die Datei `LICENSE` legt das Cockpit selbst an, mit dem Text von GitHub, Name und Jahr. Eine vorhandene bleibt unverändert.
- Holen wie GitHub Desktop mit Merge. Abweichung von Konzept 9.3, dort wurde nie zusammengeführt. Bei Konflikten pro Datei: „Meine Fassung behalten“, „Fassung von GitHub übernehmen“ oder „Im Editor öffnen“. Dazu „Zusammenführen abbrechen“ als sichere Vorgabe. Stören noch nicht hochgeladene Änderungen, fragt das Cockpit nach Stash. Vorgabe: „Abbrechen“. Vorher gibt es eine Sicherheitskopie.
- Herunterladen: Liste der eigenen Repositories und der Repositories der Organisationen, neueste oben, dazu „Adresse eingeben …“.

### Verlauf und Repository verwalten

- Die ausgeführten Feature-Schritte eines Commits stehen in der Datenbank, nur für Commits aus dem Cockpit.
- Löschen: Bei der Anmeldung im Browser holt das Cockpit mit einer zweiten Anmeldung das Recht delete_repo. Der Zugang wird nur dafür benutzt und danach verworfen. Beim eigenen Token erklärt das Cockpit, welches Recht fehlt.
- Neue Dateien beim Verwerfen kommen über eine Funktion von Windows in den Papierkorb, ohne neue Bibliothek.

### Branches und weitere GitHub-Funktionen

- Konzept 10.14 ist erweitert. Die Grundfunktionen für Branches gehören zum Kern (Teilschritt 5f).
- Pull Requests, Reviews und Schutzregeln kommen als Phase 6 direkt nach Phase 5, statt in Phase 15. Die Phasen 6 bis 14 rücken um eins nach hinten. Es bleiben 17 Phasen.
- Neu im Konzept: Tags beim Feature Versionen, GitHub Actions beim Feature Releases, Mitarbeiter bei „Repository verwalten“.


## 25.09.2026: Entscheidungen in Phase 5a

### Umstellen verschiebt nur

- Umstellen verschiebt den Ordner auf demselben Laufwerk nur an einen neuen Ort. Der Inhalt bleibt unverändert. Deshalb gibt es dafür keine Sicherheitskopie.
- Liegt der Ordner auf einem anderen Laufwerk, kopiert das Cockpit ihn. Der alte Ordner bleibt dann unverändert, der Nutzer löscht ihn später selbst.

### Verbinden ohne Git-Ordner

- Fehlt der Git-Ordner, bietet „Code“ die Aktion „Mit vorhandenem Repository verbinden …“. Das Cockpit holt den Verlauf von der Plattform und setzt nur den Index von Git. Die Dateien bleiben unverändert. Unterschiede erscheinen als Änderungen, die noch nicht hochgeladen sind.

### Virtuelle Umgebung

- Die alte Umgebung wandert vor dem Neuanlegen als Sicherheitskopie in den Ordner `backups` im Datenordner. Das Cockpit löscht Sicherheitskopien nach 30 Tagen.
- Neu angelegt wird mit demselben Python wie vorher, sonst mit dem Python-Starter `py` und derselben Version.

### Git-Identität

- Das Cockpit trägt die Identität ein, wenn ein Projekt hinzugefügt, heruntergeladen oder verbunden wird. Ab Phase 5c prüft es sie zusätzlich vor jedem Commit.

### Aktionen nur, wenn sie passen

- Manche Aktionen erscheinen nur, wenn sie gebraucht werden: „Neuen Ort angeben …“ bei fehlendem Ordner, „Mit vorhandenem Repository verbinden …“ ohne Git-Ordner, „Virtuelle Umgebung neu anlegen …“ bei kaputter Umgebung. Andere Aktionen stehen weiter mit Grund als „nicht verfügbar“ in der Liste.

### Liste der Repositories

- Das Cockpit fragt die Repositories beim Start, mit Strg+R und nach der Kontenverwaltung ab. Ist die Tresordatei gesperrt, bleibt es bei der gemerkten Liste. Fehler erscheinen nur in der Statuszeile und in der Liste der Meldungen, ohne Ansage.
- Aktualisiert der Hintergrund den Stand, ändert das Cockpit nur die betroffenen Zeilen. Auswahl und Fokus bleiben, und es gibt keine Ansage.

### Testdaten

- Die Testdaten haben jetzt Git-Repositories mit einer „Plattform“ aus Ordnern, eine kaputte virtuelle Umgebung und einen Ordner `Andere Ordner` zum Hinzufügen.


## 25.09.2026: Entscheidungen in Phase 5b

### Neues Projekt hochladen

- Das Fenster fragt nach Name, Kurzbeschreibung, Sichtbarkeit, Lizenz und Ziel. Die Auswahl der Features für das Projekt (Konzept 9.1) kommt mit der Feature-Verwaltung in Phase 7, weil es vorher keine Features gibt.
- Beim Kopieren bleiben die virtuelle Umgebung und Caches weg (.venv, venv, __pycache__ und ähnliche). Eine virtuelle Umgebung funktioniert nach dem Kopieren ohnehin nicht mehr.
- Der Namensvorschlag ersetzt Leerzeichen durch Bindestriche und schreibt Umlaute um, zum Beispiel „Mein Übersetzer“ zu „Mein-Uebersetzer“.
- Ist die Sichtbarkeit „Öffentlich“, sagt die Rückfrage ausdrücklich: „Jeder im Internet kann den Code sehen.“
- Das Ergebnis kommt als Meldung mit OK, der Link liegt in der Zwischenablage.
- Bricht etwas ab, bleibt das Projekt in der Liste. „Auf GitHub hochladen“ setzt dort wieder an. Ein schon angelegtes Repository wird nicht noch einmal angelegt.
- Hat ein Projekt schon Commits, aber noch keinen Upload, und gibt es offene Änderungen, heißt der zusätzliche Commit „Änderungen vor dem ersten Hochladen“.

### Sicherheitsprüfung

- Geheimnisse, Schlüsseldateien, `.env`-Dateien und Dateien ab 100 MB stoppen das Hochladen. Gelöst wird das mit „In .gitignore aufnehmen“, „Kein Geheimnis“ oder durch Bearbeiten der Datei und „Erneut prüfen“.
- Warnungen (private Daten, Dateien ab 50 MB) kommen beim Weiter in .gitignore, wenn nicht „Trotzdem hochladen“ gewählt wurde. Das ist die sichere Vorgabe aus den Fragen zu Phase 5.
- Eine private E-Mail-Adresse in einem öffentlichen Repository lässt sich nicht mit .gitignore lösen. „Weiter“ geht dann erst nach „Trotzdem hochladen“.
- Die Prüfung sieht auch in Commits, die noch nicht hochgeladen sind. Ein Geheimnis dort stoppt das Hochladen, auch wenn die Datei es heute nicht mehr enthält. Einen bequemen Weg, solche Commits zu bereinigen, gibt es noch nicht (TODO.md).
- „In .gitignore aufnehmen“ nimmt eine Datei, die schon in Git ist, dort heraus (git rm --cached). Die Datei bleibt auf der Festplatte.
- Platzhalter wie „changeme“, „<…>“ oder Werte, die mit „test“ oder „example“ beginnen, gelten nicht als Passwort.
