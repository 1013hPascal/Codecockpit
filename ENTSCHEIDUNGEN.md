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

### Hinzufügen und Hochladen getrennt (nach dem NVDA-Test von 5b)

- Wunsch des Nutzers. Oben in der Projektliste stehen „Projekt vom Rechner hinzufügen“ und „Projekt von GitHub herunterladen“. Im Menü Datei stehen dieselben zwei Einträge.
- „Projekt vom Rechner hinzufügen“: Ein Ordner mit dem Unterordner Code kommt sofort in die Liste. Sonst wählt man „In den Projekte-Hauptordner verschieben“ oder „Am Ort lassen“ (nur verknüpfen). Vorgabe ist „Abbrechen“.
- Ist das Projekt danach noch nicht auf GitHub, fragt das Cockpit „Jetzt hochladen?“. Vorgabe ist „Später“.
- Hochgeladen wird nur noch mit der Projekt-Aktion „Auf GitHub hochladen …“ bei Code.
- „Neues Projekt hochladen“ mit Kopieren entfällt (Abweichung von Konzept 9.1). So gibt es nie zwei Ausgaben desselben Codes auf dem Rechner. Der Menüpunkt „Vorhandenes Projekt hinzufügen“ entfällt ebenfalls.
- „Projekt von GitHub herunterladen“ kommt aus 5c nach vorne: eigene Repositories und die der Organisationen, neueste oben, ohne die, die schon in der Liste sind, dazu „Adresse eingeben …“.
- Der Name auf GitHub wird mit einer genauen Meldung geprüft, zum Beispiel „Der Name darf keine Leerzeichen enthalten.“


## 25.09.2026: Entscheidungen in Phase 5c

### Änderungen hochladen

- Das Fenster fragt „Was haben Sie geändert?“ und bietet ein zweites Feld „Beschreibung, freiwillig“, wie Zusammenfassung und Beschreibung in GitHub Desktop. Darunter stehen die geänderten Dateien als Liste. Der Titel nennt die Änderungen kurz, zum Beispiel „1 Datei geändert, 1 neue Datei“.
- „Hochladen“ im Fenster ist die Bestätigung. Es gibt keine zweite Rückfrage, weil Commit und Hochladen keine Dateien auf dem Rechner verändern.
- Gibt es keine neuen Änderungen, aber Commits, die noch nicht hochgeladen sind, fragt das Cockpit nur „Jetzt hochladen?“. Vorgabe ist „Abbrechen“.
- Die Sicherheitsprüfung sieht nur die geänderten Dateien und die Commits, die noch nicht hochgeladen sind. Was schon auf der Plattform liegt, prüft sie nicht noch einmal.
- Ob ein Repository öffentlich ist, weiß das Cockpit aus der Liste der Repositories des Kontos. Unbekannt gilt als privat. Das betrifft nur die Warnung zur privaten E-Mail-Adresse.
- Vor jedem Commit trägt das Cockpit die Git-Identität aus den Grundeinstellungen ein, wenn im Repository keine steht. Eine andere Identität bleibt ohne Rückfrage. Sonst käme die Frage vor jedem Hochladen.
- Vor dem Hochladen holt das Cockpit den Stand (git fetch). Ist die Plattform weiter, lädt es nicht hoch. Der Commit bleibt gespeichert. Das Cockpit fragt „Jetzt holen und danach hochladen?“, Vorgabe „Später“. Das entspricht Git und GitHub Desktop, nur ohne Fehlermeldung „rejected“.

### Änderungen holen

- Holen fragt immer vorher, weil es Dateien verändert. Vorgabe ist „Abbrechen“.
- Die Sicherheitskopie enthält nur die Dateien, die das Holen ändern kann, und die eigenen Änderungen. Dazu kommt Stand.txt mit dem Commit vor dem Holen. Eine Kopie des ganzen Ordners wäre mit virtueller Umgebung oft sehr groß.
- Zusammengeführt wird mit git merge, wie git pull und GitHub Desktop. Die Nachricht des Merge-Commits ist die von Git.
- Beiseitelegen (Stash) fragt das Cockpit nur, wenn eigene Änderungen und neue Commits dieselbe Datei betreffen. Sonst führt Git ohne Stash zusammen, wie GitHub Desktop. Der Stash heißt „CodeCockpit: vor dem Holen“.

### Konflikte

- Es gibt zwei Arten: beim Zusammenführen der Commits und beim Zurücklegen der beiseitegelegten Änderungen. Das Fenster ist für beide gleich. „Meine Fassung“ ist immer Ihre Fassung, auch wenn Git dafür intern „ours“ oder „theirs“ sagt.
- „Im Editor öffnen“ öffnet die Datei mit den Konfliktmarken. „Erneut prüfen“ erkennt eine gelöste Datei daran, dass keine Konfliktmarken mehr darin stehen.
- „Zusammenführen abbrechen“ führt in beiden Fällen zurück zum Stand vor dem Holen, samt Ihren Änderungen. Dafür merkt sich das Cockpit den Commit vor dem Holen unter refs/codecockpit/vor-dem-holen.
- Wird das Cockpit mitten im Zusammenführen geschlossen, zeigt Code „1 Konflikt beim Zusammenführen“ oder „Zusammenführen nicht abgeschlossen“. Die Aktion „Konflikte lösen …“ steht dann oben und ist die Vorgabe für Enter.

### Testdaten

- Ein „anderer Rechner“ hat Änderungen zu PDF-Chat, Tagebuch und Rezepte hochgeladen. Das neue Beispielprojekt Rezepte hat einen Konflikt beim Zusammenführen, Tagebuch einen beim Zurücklegen.

### Nach dem NVDA-Test von 5c

- „Projekt neu einlesen“ steht bei Projekt, Code und Exe ganz oben in der Aktionsliste. Es fragt nur den Stand dieses Projekts neu ab und sagt danach „… neu eingelesen.“ Enter auf Code führt weiter die wichtigste Aktion aus. Im Menü Datei bleibt „Projekte neu einlesen“ für alle Projekte.
- Nach einer Aktion bleibt die Markierung in der Aktionsliste auf dieser Aktion. Vorher sprang sie nach oben.
- Das zweite Feld beim Hochladen heißt nur „Beschreibung“. Mit „freiwillig“ klang es beim ersten Vorlesen so, als wäre das Pflichtfeld freiwillig.
- Code nennt auch die Änderungen, die auf GitHub noch nicht geholt sind. Exe nennt sie nicht, weil Holen die Exe nicht betrifft und man dort nichts tun kann.
- „Im Editor öffnen“ heißt jetzt „Konflikt im Editor anzeigen“. Vorher beschriftet das Cockpit die Konfliktmarken in der Datei: „Meine Fassung“ oder „Fassung von GitHub“ mit Dateiname und Zeile, am Ende „Ende des Konflikts“. Nur die Markenzeilen ändern sich, auch schon bearbeiteter Code bleibt.
- „Zusammenführen abschließen“ ist nie ausgegraut, weil Tab ausgegraute Knöpfe überspringt. Ist noch etwas offen, sagt der Knopf, wie viel. Ist der letzte Konflikt gelöst, springt der Fokus auf diesen Knopf.
- Neu im Menü Datei: „Sicherheitskopien …“. Jede Kopie hat die Datei Sicherheitskopie.txt mit Projekt, Anlass und Herkunftsordner. Einzelne Dateien lassen sich öffnen und wiederherstellen. Vor dem Wiederherstellen kommt die jetzige Datei selbst in eine neue Sicherheitskopie. Löschen einer Kopie braucht eine Bestätigung, eine Kopie der Kopie gibt es nicht. Das greift einem Teil von 5d vor.
- Der Anlass der Sicherheitskopie beim Neuanlegen der virtuellen Umgebung heißt jetzt „virtuelle Umgebung“ statt „venv“.


## 25.09.2026: Entscheidungen in Phase 5d

### Verlauf

- „Verlauf …“ ist eine Aktion bei Code. Das Fenster zeigt alle Commits des aktuellen Branches, neueste oben, wie git log. Zum Beispiel „21.09.2026, Version 1.0.0: Hilfe ergänzt“. Die Version kommt aus einem Git-Tag wie v1.0.0.
- Commits, die noch nicht auf der Plattform sind, enden mit „noch nicht hochgeladen“, wie der Pfeil in GitHub Desktop.
- Enter oder „Details anzeigen …“ öffnet die Details. Oben stehen die Angaben als Liste: Nachricht, Autor und Datum, Version, Commit. Darunter die geänderten Dateien. Eine Liste liest sich mit der Braillezeile besser als ein Textfeld.
- Die Schritte der Features pro Commit stehen in der neuen Tabelle commit_steps. Solange es keine Features gibt, bleibt sie leer.

### Rückgängig machen

- „Datei wiederherstellen …“ setzt nur die Datei im Ordner zurück (git restore). Der Verlauf bleibt. Wurde die Datei in dieser Version gelöscht, kommt sie mit dem Stand direkt davor zurück.
- „Version rückgängig machen …“ erstellt einen neuen Commit „Rückgängig: …“ (git revert). Er ist danach noch nicht hochgeladen.
- Geht das nicht von selbst, weil spätere Versionen dieselben Stellen geändert haben, bricht das Cockpit ab und ändert nichts. Es schlägt vor, einzelne Dateien wiederherzustellen. Ein Konfliktfenster wie beim Holen wäre hier verwirrend.
- Ein Zusammenführen (Merge-Commit) und die erste Version lassen sich nicht als Ganzes rückgängig machen. Das Cockpit erklärt das ohne Rückfrage.
- Hat eine betroffene Datei eigene Änderungen ohne Commit, macht das Cockpit nichts und bittet, sie zuerst hochzuladen oder zu verwerfen.
- Neu, wie „Undo“ in GitHub Desktop: „Commit zurücknehmen …“ beim neuesten Commit, solange er nicht hochgeladen ist. Seine Änderungen bleiben in den Dateien und erscheinen wieder als Änderungen ohne Commit. Weil sich keine Datei ändert, gibt es dafür keine Sicherheitskopie.

### Änderungen verwerfen

- Verworfen werden nur Änderungen ohne Commit. Sie kommen auf den Stand des letzten Commits, wie „Discard changes“ in GitHub Desktop. Konzept 9.7 sagt „zuletzt hochgeladener Stand“. Für Commits, die noch nicht hochgeladen sind, gibt es dafür „Commit zurücknehmen“ oder „Version rückgängig machen“ im Verlauf.
- In der Liste ist anfangs nichts ausgewählt. „Alle auswählen“ wählt alles. Ist nichts ausgewählt, sagt „Verwerfen …“, was fehlt.
- Neue Dateien kommen über SHFileOperationW von Windows in den Papierkorb, ohne neue Bibliothek.
- Die Aktion steht immer bei Code, auch ohne Änderungen. Dann ist sie „nicht verfügbar“ mit Grund.

### Sicherheitskopien

- Vor dem Wiederherstellen, Rückgängigmachen und Verwerfen kommen die betroffenen Dateien in eine Sicherheitskopie. Anlass: „vor dem Wiederherstellen“, „vor dem Rückgängigmachen“ oder „vor dem Verwerfen“. Sie erscheinen im Fenster „Sicherheitskopien“ aus 5c.


## 26.09.2026: Entscheidungen in Phase 5e

### Links

- „Links …“ ist eine Aktion beim Projekt. Das Fenster zeigt Projektseite und README als Liste. Enter oder „Kopieren“ kopiert den markierten Link, „Im Browser öffnen“ öffnet ihn. Der Download-Link kommt mit dem Feature Releases.
- Links brauchen keinen Zugang aus dem Tresor. Sie gibt es nur bei Projekten, deren Adresse zu einem Konto passt.

### Repository verwalten

- „Repository verwalten …“ fragt zuerst den Stand bei der Plattform ab. Das Fenster zeigt die Angaben als Liste und die Knöpfe „Öffentlich machen …“ oder „Privat machen …“, „Mitarbeiter …“, „Archivieren …“ oder „Archivierung aufheben …“ und „Löschen …“.
- Vor „Öffentlich machen“ prüft die Sicherheitsprüfung alle Dateien in Git, den ganzen Verlauf und alle E-Mail-Adressen der Commits. Findet sie ein Geheimnis, macht das Cockpit das Repository nicht öffentlich. Auch ein später entferntes Geheimnis bleibt im Verlauf sichtbar. Warnungen nennt die Rückfrage, Vorgabe ist „Abbrechen“.
- Neu gegenüber dem Konzept: „Archivierung aufheben …“. GitHub erlaubt das, und so ist Archivieren wirklich die sanfte Alternative zum Löschen.
- Löschen fragt zweimal. Erst mit dem Hinweis, dass es nicht rückgängig geht, und dem Angebot „Stattdessen archivieren …“. Vorgabe ist „Abbrechen“. Dann muss der Name des Repositories eingetippt werden. Vorgabe ist dort ebenfalls „Abbrechen“.
- Fehlt das Recht zum Löschen und das Konto nutzt die Anmeldung im Browser, fragt das Cockpit nach einer zweiten, kurzen Anmeldung nur mit den Rechten repo und delete_repo. Meldet man sich dabei mit einem anderen Konto an, löscht es nichts. Der Zugang daraus wird nur für dieses Löschen benutzt und nicht gespeichert. Das Recht bleibt bei GitHub für die App CodeCockpit eingetragen. Man kann es dort unter Settings, Applications widerrufen.
- Beim eigenen Token ohne dieses Recht erklärt das Cockpit, was fehlt, und bietet an, die Einstellungen des Repositories im Browser zu öffnen.
- Nach dem Löschen fragt das Cockpit, was mit dem Projekt passiert. Vorgabe ist „Nur lokal behalten“: Die Verbindung origin wird entfernt, Dateien und Verlauf bleiben, das Projekt heißt „noch nicht auf GitHub“. Die andere Wahl ist „Aus der Liste entfernen“. Der Ordner bleibt in beiden Fällen.

### Mitarbeiter

- Die Liste zeigt direkte Mitarbeiter und offene Einladungen, zum Beispiel „erika, schreiben“ und „max, eingeladen, lesen“.
- Beim Einladen wählt man „lesen“, „schreiben“ oder „verwalten“. Vorgabe ist „schreiben“. GitHub kennt noch „sichten“ und „pflegen“. Sie werden angezeigt, aber beim Einladen nicht angeboten, damit die Auswahl kurz bleibt.
- „Entfernen …“ zieht bei einer offenen Einladung die Einladung zurück.
- Nach dem NVDA-Test von 5e: „Einladen …“ steht als oberste Zeile in der Liste, darunter die Mitarbeiter. Enter auf „Einladen …“ lädt ein. Mit Tab folgen das Feld „Recht“ mit dem Recht des markierten Mitarbeiters, „Zugriffsrecht ändern“ und „Entfernen …“. Das Recht ändern geht auch bei offenen Einladungen.

### Aus der Liste entfernen

- Beim Projekt: Das Cockpit merkt sich den Ordner. Beim Durchsuchen des Hauptordners und mit Strg+R kommt er nicht wieder. „Projekt vom Rechner hinzufügen“ hebt das auf. Liegt das Projekt auf GitHub, erscheint es danach auch nicht als „nur auf GitHub“.
- Bei „nur auf GitHub“: Das Repository verschwindet aus der Liste. Bei „Projekt von GitHub herunterladen“ steht es weiter zur Wahl. Nach dem Herunterladen ist es wieder normal in der Liste.


## 26.09.2026: Entscheidungen in Phase 5f

### Übersicht „Branches“

- „Branches …“ ist eine Aktion bei Code, sobald es einen Commit gibt. Beim Öffnen holt das Cockpit den Stand der Plattform (git fetch --prune). Klappt das nicht, zeigt es den letzten bekannten Stand und sagt das kurz an.
- Die Liste zeigt zuerst den aktuellen Branch, dann den Haupt-Branch, dann die übrigen mit dem neuesten Commit zuerst. Jede Zeile nennt den Namen vorne und dann den Stand, zum Beispiel „suche-pdfs, 2 Commits vor main, noch nicht auf GitHub“ oder „design, 1 Commit vor main, nur auf GitHub“.
- Enter wechselt zum markierten Branch, wie ein Klick in GitHub Desktop. Wechseln ohne eigene Änderungen fragt nicht nach, weil dabei nichts verloren geht.
- Gibt es Änderungen ohne Commit, fragt das Cockpit wie GitHub Desktop: „Beiseitelegen und wechseln“, „Mitnehmen und wechseln“ oder „Abbrechen“ (Vorgabe). Passen mitgenommene Änderungen nicht zum anderen Branch, wechselt Git nicht, und nichts ändert sich.
- Beim Zurückwechseln fragt das Cockpit, ob es die dort beiseitegelegten Änderungen zurückholen soll. Vorgabe ist „Später“.
- Ein neuer Branch beginnt beim aktuellen Stand. Änderungen ohne Commit kommen mit, wie bei git switch -c. Hochgeladen wird er mit „Änderungen hochladen“.
- „In main übernehmen …“ wechselt bei Bedarf zu main und führt den markierten Branch dort zusammen (git merge). Vorher gibt es eine Sicherheitskopie. Konflikte löst man im selben Fenster wie beim Holen, die zweite Fassung heißt dort „Fassung von Branch …“. Danach ist main noch nicht hochgeladen.
- Umbenennen auf der Plattform geht wie im Terminal: den neuen Namen hochladen, den alten löschen. Die Rückfrage sagt, dass offene Pull Requests zum alten Namen dabei geschlossen werden. Den Haupt-Branch benennt das Cockpit nicht um.
- Löschen fragt, ob nur hier oder auch auf der Plattform. Vorgabe ist „Abbrechen“. Der aktuelle und der Haupt-Branch lassen sich nicht löschen. Der letzte Commit eines gelöschten Branches bleibt unter refs/codecockpit/geloescht/ erreichbar, damit nichts verloren geht.
- Die Projektliste zeigt bei einem neuen Branch „Branch noch nicht auf GitHub“ statt „alles hochgeladen“.
- Das Holen nennt den Branch, wenn es nicht der Haupt-Branch ist: „Geholt: 1 neuer Commit von GitHub in Branch suche.“
- Branch wechseln bei „Änderungen hochladen“ und Pull Requests kommen mit Phase 6.

### Beiseitegelegte Änderungen (Stash)

- „Änderungen beiseitelegen …“ bei Code legt alle Änderungen ohne Commit beiseite, auch neue Dateien. Die Nachricht nennt den Branch: „CodeCockpit: beiseitegelegt auf main“. Vorher gibt es eine Sicherheitskopie.
- „Beiseitegelegte Änderungen …“ erscheint bei Code nur, wenn es welche gibt. Code zeigt dann „Änderungen beiseitegelegt“.
- Die Zeilen nennen Datum, Branch und Dateien, zum Beispiel „25.09.2026 14:03, auf main, 2 Dateien: main.py und neu.txt“. Was das Holen beiseitegelegt hat, endet mit „vor dem Holen“.
- „Zurückholen …“ geht nur ohne eigene Änderungen. Passen die Änderungen nicht mehr zum Stand, stellt das Cockpit alles wieder her, und sie bleiben beiseitegelegt. Dann hilft „Als neuen Branch zurückholen …“ (git stash branch). Das passt immer, weil der Branch dort beginnt, wo beiseitegelegt wurde.
- „Löschen …“ legt vorher die Dateien als Sicherheitskopie an.

### Nach dem NVDA-Test von 5f

- Die Knöpfe im Fenster Branches richten sich nach der markierten Zeile. Beim Haupt-Branch fehlen „In main übernehmen …“, „Umbenennen …“ und „Löschen …“, beim aktuellen Branch fehlt „Löschen …“. Sie verschwinden, statt ausgegraut zu sein.
- Liegt ein Branch an beiden Orten, bietet Löschen auch „Nur auf GitHub“ an.
- Jede Zeile der Übersicht nennt jetzt Name, Ort, Person und Stand, zum Beispiel „design, hier und auf GitHub, zuletzt von Anna am 24.09.2026, 2 Commits vor main“. Der Ort ist immer ausgeschrieben: „nur hier“, „nur auf GitHub“ oder „hier und auf GitHub“. Git kennt nur, wer die Commits gemacht hat, deshalb heißt es „zuletzt von“.
- Neu im Menü Hilfe: „Branches verstehen …“ (anleitungen/branches-verstehen.md) mit einem Beispiel, was wo passiert und was man wann löschen darf.
- Die Testdaten entstehen schneller: Die drei Git-Projekte werden gleichzeitig angelegt, und jedes lädt so selten wie möglich hoch. Vorher dauerte der Start mit Testdaten etwa 10 Sekunden ohne jedes Fenster, jetzt etwa 4.


## 26.09.2026: Antworten auf die Fragen zu Phase 6

Die Fragen und Antworten stehen in `fragen\phase-06.md`. Alle Vorschläge sind angenommen.

### Ablauf

- Phase 6 kommt in drei Teilschritten mit eigenen Tests und Checklisten `checklisten\phase-06a.md` bis `phase-06c.md`.
- 6a: Pull Requests erstellen, als Liste ansehen, Details, geänderte Dateien und Kommentare lesen, selbst kommentieren, Entwürfe, schließen und wieder öffnen.
- 6b: Reviews, Änderungen einer Datei lesbar ansehen, in main übernehmen, danach aufräumen.
- 6c: Schutzregeln für main, Hochladen in einen Branch, wenn main geschützt ist, und das Feature „Branches und Pull Requests“ für den Ablauf beim Hochladen.
- Getestet wird mit einem neuen privaten Repository „codecockpit-test“ auf dem echten Konto. Es wird am Ende von Phase 6 gelöscht. Für die Schutzregeln wird es kurz öffentlich.
- Es gibt kein zweites GitHub-Konto. Genehmigen und Änderungen anfordern prüfen nur die automatischen Tests. Die Checklisten prüfen Kommentieren und Übernehmen.

### Pull Requests

- Pull Requests ansehen, erstellen, kommentieren, prüfen und übernehmen gehört zum Kern und ist da, sobald ein Projekt auf GitHub liegt und ein Konto passt.
- Das Feature „Branches und Pull Requests“ ändert nur den Ablauf beim Hochladen (6c). Bis Phase 7 schaltet man es mit einer Aktion bei Code ein und aus.
- „Pull Requests …“ bei Code zeigt die offenen, neueste oben. Eine Auswahl oben zeigt auch geschlossene. Die Branches und Code nennen offene Pull Requests. Die Projektliste nicht.
- Erstellen fragt nach Titel, Beschreibung, Ziel-Branch, Prüfern und „Als Entwurf erstellen“. Titel und Beschreibung sind aus den Commit-Nachrichten vorbelegt.
- Kommentare stehen als eine Liste, älteste oben, allgemeine und solche zu einer Zeile. Schreiben kann man allgemeine Kommentare.
- Übernehmen bietet Merge-Commit (Vorgabe), Squash und Rebase an, soweit das Repository sie erlaubt. Danach fragt das Cockpit, ob es zu main wechseln, holen und den Branch aufräumen soll. Vorgabe ist „Später“.

### Schutzregeln

- Unter „Repository verwalten“: nur über Pull Request, Anzahl der Genehmigungen, Genehmigungen verfallen bei neuen Commits, gilt auch für Administratoren, main darf nicht gelöscht werden. Force push auf main bleibt immer verboten.
- Gibt es Schutzregeln für ein privates Repository nur mit GitHub Pro, erklärt das Cockpit das.
- Lehnt GitHub das Hochladen in main ab, bietet das Cockpit an, in einen neuen Branch hochzuladen und einen Pull Request zu erstellen.
- Die Rechte der Anmeldung reichen. Fehlt eines, erklärt das Cockpit, welches.
- Pull Requests laufen über eine eigene Schnittstelle der Plattform. GitLab bringt in Phase 16 seine eigene Umsetzung mit.

### Nach dem NVDA-Test von 6a

- In der Liste der Pull Requests wirken alle Knöpfe direkt auf den markierten Eintrag: „Details …“, „Kommentare …“, „Zum Prüfen freigeben“ (nur bei Entwürfen), „Pull Request schließen …“ oder „Wieder öffnen“, „Neuer Pull Request …“ und „Im Browser öffnen“. Man muss nicht erst die Details öffnen.
- „Details …“ zeigt Angaben und geänderte Dateien. „Kommentare …“ zeigt die Kommentare mit dem Feld für einen neuen Kommentar.
- Der Knopf zum Wechseln in der Übersicht Branches nennt den Branch, zum Beispiel „Zu main wechseln“. Beim aktuellen Branch erscheint er nicht.



## 27.09.2026: Entscheidungen in Phase 6b

- In der Liste der Pull Requests gibt es bei offenen Pull Requests, die kein Entwurf sind, „Prüfen …“ und „In main übernehmen …“. Der Knopf nennt den Ziel-Branch.
- Die Liste nennt Genehmigungen, zum Beispiel „1 Genehmigung“ oder „Änderungen angefordert“. Wie bei GitHub zählt pro Person das letzte Review. Abgefragt werden höchstens 30 offene Pull Requests, damit die Liste schnell kommt.
- Prüfen: „Nur kommentieren“ (Vorgabe), „Genehmigen“ oder „Änderungen anfordern“. Nur beim Genehmigen darf der Kommentar fehlen. Beim eigenen Pull Request bietet das Cockpit nur „Nur kommentieren“ an und sagt warum, weil GitHub mehr nicht erlaubt.
- Die Details nennen die Genehmigungen und ob GitHub übernehmen kann, zum Beispiel „Kann übernommen werden“ oder „Hat Konflikte mit main“. Enter auf einer Datei zeigt ihre Änderungen, eine Zeile pro Änderung: „Neu Zeile 12: …“, „Weg Zeile 8: …“. Unveränderte Zeilen fehlen.
- Die Kommentare zeigen auch Reviews, zum Beispiel „ben hat genehmigt, 24.09.2026: Passt“.
- Übernehmen: Das Fenster nennt den Stand und bietet die Arten an, die das Repository erlaubt. Vorgabe beim Knopf ist „Abbrechen“, weil sich Übernehmen auf GitHub nicht einfach rückgängig machen lässt.
- Danach fragt das Cockpit, ob es aufräumen soll: zu main wechseln, holen, den Branch hier und auf GitHub löschen. Vorgabe ist „Später“. Gibt es Änderungen ohne Commit, räumt es nicht auf und sagt warum.
- Nach dem NVDA-Test von 6b: Wer nach dem Übernehmen „Später“ wählt, findet in der Liste der Pull Requests bei dem übernommenen Pull Request den Knopf „Aufräumen …“. Er erscheint, solange der Branch noch existiert.


## 27.09.2026: Entscheidungen in Phase 6c

- „Repository verwalten“ hat „Schutzregeln für main …“ mit Kontrollkästchen: nur über Pull Request, Anzahl der Genehmigungen (0 bis 3), Genehmigungen verfallen bei neuen Commits, gilt auch für Administratoren, main darf nicht gelöscht werden. Vor dem Speichern sagt eine Rückfrage in Sätzen, was die Regeln bedeuten. Sind alle Kästchen leer, entfernt das Cockpit den Schutz.
- Force push auf main bleibt immer verboten, das Cockpit schickt dafür immer „nein“ an GitHub.
- Lehnt GitHub das Hochladen ab, weil der Branch geschützt ist, verschiebt das Cockpit nach Rückfrage die Commits in einen neuen Branch, lädt ihn hoch und öffnet „Pull Request erstellen“. Der alte Branch kommt auf den Stand von GitHub. Weil sich dabei keine Datei ändert, gibt es keine Sicherheitskopie der Dateien. Der alte Stand bleibt aber unter refs/codecockpit/vor-dem-verschieben/ erreichbar.
- Das Feature „Branches und Pull Requests“ ist das erste Feature-Paket (cockpit/features/branches_prs). Bis Phase 7 schaltet man es bei Code mit „Hochladen über Pull Requests einschalten …“ ein. Die Einstellung steht wie geplant in cockpit.toml im Ordner Code.
- Ein Manifest kann jetzt auf eine Ja-Nein-Grundeinstellung zeigen (default_setting). So gilt „Neue Projekte mit Branches und Pull Requests“ für dieses Feature, ohne dass der Kern den Namen des Features kennt.
- Mit aktivem Feature fragt „Änderungen hochladen“ auf main nach dem Branch: neuer Branch (Name aus der Nachricht), vorhandener Branch oder direkt in main. Gibt es auf main schon Commits, die nicht hochgeladen sind, kommen sie in den neuen Branch, und vorhandene Branches stehen nicht zur Wahl. Nach dem Hochladen eines Branches ohne offenen Pull Request fragt das Cockpit, ob es einen erstellen soll. Vorgabe ist „Später“.


## 27.09.2026: Antworten auf die Fragen zu Phase 7 und Entscheidungen

Die Fragen und Antworten stehen in `fragen\phase-07.md`. Alle Vorschläge sind angenommen.

### Feature-Verwaltung (Menü Features)

- Neues Menü „Features“ nach „Datei“ mit „Feature-Verwaltung …“.
- Liste mit Kontrollkästchen, zum Beispiel „Branches und Pull Requests, eingeschaltet, in 2 Projekten aktiv“. Fehlt einem eingeschalteten Feature ein Dienst wie KI, sagt die Zeile „nicht verfügbar“ und warum.
- Mit Tab: die Beschreibung (was es tut, was es braucht, Vorauswahl, in wie vielen Projekten eingeschaltet), das Kästchen „Für neue Projekte einschalten“, „Einführung …“, „Einstellungen …“ (nur bei Features mit Einstellungen), „Speichern“, „Abbrechen“.
- Global ausgeschaltete Features verschwinden überall. Die Auswahl in den Projekten bleibt in cockpit.toml erhalten.

### Features eines Projekts

- „Features dieses Projekts …“ auf der Projektzeile. Die vorläufige Aktion bei Code aus Phase 6 ist entfallen.
- Der Titel sagt, ob das Projekt der Vorauswahl folgt oder eine eigene Auswahl hat.
- Beim Speichern gibt es eine Rückfrage. Sie nennt Features, die wegen Abhängigkeiten mit ein- oder ausgeschaltet werden, und dass die Auswahl in cockpit.toml steht. Statt zwei Fragen („Beide einschalten?“ und „Speichern?“) gibt es eine, damit es nicht zu viele Fragen hintereinander werden.
- Ohne Änderung schreibt „Speichern“ nichts und sagt „Nichts geändert.“ So folgt ein Projekt weiter der Vorauswahl.

### Vorauswahl

- Sie steht in der Feature-Verwaltung. „Neue Projekte mit Branches und Pull Requests“ ist aus den Grundeinstellungen verschwunden. Ein dort früher gesetztes „Ja“ gilt, bis in der Feature-Verwaltung eine Vorauswahl gespeichert wird.
- Die Vorauswahl gilt für neue Projekte und für alle, bei denen cockpit.toml nichts zu Features festlegt.
- „Auf GitHub hochladen“ hat eine Liste „Features für dieses Projekt“, vorbelegt mit der Vorauswahl. Die Wahl kommt samt benötigten Features in cockpit.toml und damit in die erste Version.

### Einführung

- Erscheint beim allerersten Einschalten, global oder in einem Projekt, als Liste mit einem Satz pro Zeile. Danach mit „Einführung …“.

### Test

- Nur mit `start_testdaten.bat` gibt es „Beispiel Grundlage“ (Einstellungen und die Aktion „Beispiel-Gruß“ bei Code) und „Beispiel Aufbau“ (braucht die Grundlage). Sie liegen in cockpit/testdata_features.


## 27.09.2026: Antworten auf die Fragen zu Phase 8

Die Fragen und Antworten stehen in `fragen\phase-08.md`. Der Nutzer hat das Konzept um Terminal, Spracheingabe, Terminal-Erklärung, KI-Hilfe und KI-Verwaltung ergänzt (Konzept 9.9, 10.15 bis 10.17, 11.1).

### Ablauf

- Phase 8 kommt in fünf Teilschritten. Das Terminal kommt zuerst, weil es keine KI braucht und die KI-Verwaltung es nutzt, um Modelle herunterzuladen:
  - 8a: Eingebautes Terminal (Kern).
  - 8b: Menü KI, KI-Verwaltung mit Ollama und OpenAI-kompatibel, Rechner auslesen, Modellstufen, Seite KI im Assistenten, Datenschutz, Feature Terminal-Erklärung.
  - 8c: Feature KI-Assistent.
  - 8d: Feature Spracheingabe mit Whisper.
  - 8e: Feature KI-Hilfe.
- Getestet wird mit Ollama und gemma4:12b auf dem Rechner des Nutzers.

### KI-Verwaltung und Modelle

- Menü KI mit „KI-Verwaltung …“ und „KI-Features …“. Einen eigenen Schalter „KI aktivieren“ gibt es nicht.
- In der Feature-Verwaltung erscheinen die KI-Features als ein Eintrag „KI“. Mit Tab kommt man zu den einzelnen KI-Features (Assistent, Spracheingabe, Terminal-Erklärung, Hilfe). Umgesetzt, sobald es mehr als ein KI-Feature gibt.
- Modell wählen: eine Liste der installierten Modelle, mit Tab eine Liste vorgeschlagener Modelle, zum Beispiel „gemma4:12b, ab 32 GB Arbeitsspeicher“. Wählt man ein vorgeschlagenes, öffnet sich das Terminal mit dem Befehl zum Herunterladen. Ausgeführt wird er erst mit Enter.
- Auch bei lokaler KI gilt eine Grenze für die Menge an Text, die sie bekommt.

### KI-Assistent

- Der Knopf heißt „Vorschlag der KI“ (Alt+V), damit klar ist, dass die KI ihn macht.

### Spracheingabe

- Strg+D startet und beendet das Diktieren, Strg+Umschalt+D bricht ab. Strg+Umschalt+M ist schon für „Letzte Meldung wiederholen“ belegt.
- Neue Bibliotheken faster-whisper, sounddevice und numpy sind erlaubt.

### Terminal

- PowerShell. Beim ersten Öffnen einmal der Hinweis, dass Befehle ohne Rückfrage und ohne Sicherheitskopie laufen. Gesperrt ist nur der force push.

### Entscheidungen in Phase 8a (Terminal)

- „Terminal …“ auf der Projektzeile (Ordner des Projekts) und bei Code (Ordner Code).
- Fehler von PowerShell kommen als einfacher Text, nur mit der Meldung selbst. Leere Zeilen und Leerzeichen am Zeilenende fallen weg, weil sie auf der Braillezeile stören.
- Jede Ausgabe beginnt mit dem Befehl (seit dem Test: „Anfrage um Uhrzeit: Befehl“) und endet mit „Fertig.“ oder „Fehler, Rückgabewert N.“ Die Ansage nennt dazu die Anzahl der Zeilen. Der Fokus bleibt im Befehlsfeld.
- Git öffnet im Terminal weder Pager noch Editor und fragt nie nach einem Passwort. Befehle bekommen keine Eingabe. So bleibt nichts hängen.
- Tokens und die Zugangsdaten für Git werden in jeder Zeile der Ausgabe durch *** ersetzt. Die Zugangsdaten gibt es nur, wenn der Tresor offen ist. Das Terminal fragt dafür nicht nach dem Master-Passwort.
- Die Ausgabe behält höchstens 5000 Zeilen.
- Nach dem ersten NVDA-Test von 8a: Enter im Befehlsfeld drückt keinen Knopf mehr von selbst. Vorher löste es zugleich „Abbrechen“ aus. Jede Ausgabe beginnt mit „Anfrage um Uhrzeit: Befehl“.
- Wunsch aus dem Test von 8a für alle Textlisten: Umschalt+Pfeil und Strg+Umschalt+Pfeil wählen mehrere Zeilen aus, Strg+A alle, Strg+C kopiert die Auswahl. Gilt für Terminal, Anleitungen, Einführungen, Meldungen und die Listen mit Angaben und Kommentaren. Listen zum Auswählen einer Sache, wie die Projektliste oder die Aktionsliste, bleiben bei einer Auswahl.

### Entscheidungen in Phase 8b (KI-Verwaltung und Terminal-Erklärung)

- Menü „KI“ zwischen Features und Konten, mit Alt+K. „KI-Features …“ öffnet die Feature-Verwaltung und markiert das erste KI-Feature. Die Gruppe „KI“ in der Feature-Verwaltung kommt, sobald es mehr als ein KI-Feature gibt (TODO.md).
- Ein KI-Werkzeug ist eine KI mit Modell: „Ollama auf diesem Rechner, gemma4:12b“ oder ein KI-Konto mit Modell, zum Beispiel „Firmen-KI, gpt-4o“. Man kann mehrere einrichten. Das erste wird Standard. Sprach-KI kommt in 8d.
- Ollama braucht kein Konto. Externe KI ist ein Konto der Art „OpenAI-kompatibel“ mit Adresse, API-Schlüssel im Tresor und dem Kästchen „Läuft im eigenen Netz oder in der Firma“. „Extern: neues KI-Konto einrichten …“ öffnet gleich das Konto-Fenster für diese Art.
- Modellstufen nach Arbeitsspeicher, geprüft gegen die Bibliothek von Ollama: ab 16 GB gemma4:e4b, ab 32 GB gemma4:12b, ab 64 GB gemma4:26b. Für Whisper small, medium, large-v3-turbo. Sie stehen nur in cockpit/ai/models.py. Windows meldet etwas weniger Speicher, deshalb reichen 90 Prozent der Stufe.
- Der Arbeitsspeicher kommt direkt von Windows, der Prozessor aus der Registry, die Grafikkarte über PowerShell im Hintergrund. Man kann den Arbeitsspeicher auch von Hand eingeben. Dann gilt diese Angabe.
- Ein vorgeschlagenes, nicht installiertes Modell öffnet das Terminal im Benutzerordner mit „ollama pull …“ im Befehlsfeld. Das Terminal zeigt bei Fortschrittsanzeigen nur den letzten Stand einer Zeile und entfernt Farbcodes.
- Das Cockpit startet Ollama bei Bedarf und beendet es beim Schließen nur, wenn es Ollama selbst gestartet hat. Die Anleitung „Ollama installieren“ steht im Menü Hilfe.
- Ollama bekommt „think: false“. Test mit gemma4:12b: Mit Nachdenken war die Antwort leer, weil das Nachdenken die ganze Länge verbrauchte. Kennt ein Modell den Schalter nicht, fragt das Cockpit ohne ihn noch einmal.
- Grenze für die Textmenge: neue Grundeinstellung „Höchstens so viele Zeichen an die KI senden“, Vorgabe 8000. Sie gilt auch für lokale KI.
- Datenschutz: Die Rückfrage kommt beim ersten Senden pro Aufgabe und KI, Vorgabe „Nicht senden“. Ein Ja wird gemerkt, ein Nein nicht. So kann man später doch noch zustimmen. Die Grundeinstellung „nur lokale oder firmeninterne KI“ sperrt externe KI ganz.
- Prompts liegen als Textdateien in cockpit/ai/prompts. Eine gleichnamige Datei im Datenordner unter „prompts“ hat Vorrang. Platzhalter stehen in doppelten spitzen Klammern, weil geschweifte Klammern in Befehlen vorkommen.
- Feature „Terminal-Erklärung“: für neue Projekte eingeschaltet. Das Feld „Erklärung der KI“ gibt es nur, wenn das Feature aktiv ist, also eingeschaltet und mit eingerichteter Text-KI. Es ist eine Liste mit einem Satz pro Zeile, mit Tab nach dem Befehlsfeld. Die KI bekommt Befehl, Rückgabewert und das Ende der Ausgabe ohne Geheimnisse. Die Erklärung kommt nur bei einem Fehler, im Hintergrund, mit der Ansage „Erklärung der KI bereit.“ Ein neuer Befehl bricht eine laufende Erklärung ab.
- Die Einstellung „KI für Erklärungen“ wählt ein Werkzeug, Vorgabe ist das Standard-Werkzeug.
- Der Einrichtungsassistent hat die Seite „KI“ nach der Git-Identität. Sie zeigt Rechner, Empfehlung und Zustand von Ollama und öffnet mit „KI einrichten …“ die KI-Verwaltung.
- Nach dem NVDA-Test von 8b: In der KI-Verwaltung und bei „Modell wählen“ drückt Enter den Knopf mit dem Fokus. Vorher tat Enter dort nichts, weil die Knöpfe kein Standardknopf sein dürfen (sonst löst Enter in den Listen einen Knopf aus).

### Entscheidungen in Phase 8c (KI-Assistent)

- Feature „KI-Assistent“, für neue Projekte eingeschaltet. Einstellungen: „KI für Vorschläge“ (Vorgabe: Standard-Werkzeug) und „Sprache der Vorschläge“ (Deutsch oder Englisch).
- Der Knopf heißt „Vorschlag der KI“ (Alt+V) in drei Fenstern: „Änderungen hochladen“ (füllt „Was haben Sie geändert?“ und „Beschreibung“), „Pull Request erstellen“ (Titel und Beschreibung, für den gerade gewählten Ziel-Branch) und „Auf GitHub hochladen“ (Kurzbeschreibung). Er steht jeweils mit Tab direkt nach den Feldern, die er füllt. Ohne aktives Feature gibt es ihn nicht.
- Während die KI schreibt, bleibt das Fenster bedienbar. Escape bricht zuerst den Vorschlag ab, erst ein zweites Escape schließt das Fenster. Danach: „Vorschlag eingefügt.“ und der Fokus im ersten Feld. Klappt es nicht, erklärt ein Meldungsfenster den Grund.
- Die KI bekommt beim Commit die Liste der geänderten Dateien, die geänderten Zeilen (git diff mit zwei Zeilen Umgebung) und von neuen Dateien die ersten 80 Zeilen. Beim Pull Request die Commit-Nachrichten, die Dateiliste und die geänderten Zeilen. Bei der Kurzbeschreibung die Dateiliste, den Anfang der README, die importierten Module und requirements.txt.
- Dateien, die die Sicherheitsprüfung als Geheimnis oder private Daten erkennt, gehen nie mit. Die Übersicht nennt nur ihren Namen. Zeilen mit einem gefundenen Geheimnis werden durch „[entfernt]“ ersetzt. Die Grenze für die Zeichen gilt immer.
- Antworten der KI werden bereinigt: kein Markdown, keine Anführungszeichen um den Vorschlag, keine Vorsätze wie „Titel:“. Die Zusammenfassung hat höchstens 100 Zeichen, die Kurzbeschreibung höchstens 350.
- Test mit gemma4:12b: Ein Vorschlag dauert etwa 30 Sekunden.
- Gruppe „KI“: Ab zwei KI-Features stehen sie in der Feature-Verwaltung und bei „Features dieses Projekts …“ als ein Eintrag, zum Beispiel „KI, 2 von 2 KI-Features eingeschaltet“. Ist er markiert, führt Tab in die Liste „KI-Features“ mit einem Kontrollkästchen pro KI-Feature. Beschreibung, „Einführung …“ und „Einstellungen …“ gelten für das dort markierte Feature. „KI-Features …“ im Menü KI markiert gleich diese Gruppe.


## 27.09.2026: Phase 10 (Exe)

Das Konzept 10.4 ist überarbeitet (Wunsch des Nutzers). Die Fragen und Antworten stehen in `fragen\phase-10.md`. Phase 10 kommt vor 8d, 8e und Phase 9.

- Phase 10 kommt in einem Rutsch mit einer Checkliste, nicht in Teilschritten (Antwort 1: spart Tokens). Externe Ressourcen, Lizenzprüfung und Signieren kommen später.
- Kern: „Exe hinzufügen …“ auf der Projektzeile (bei verknüpften Projekten mit Ordnerwahl), der Eintrag Exe, Exe starten, Exe-Datei wählen, Exe aus dem Release holen, Exe-Ordner öffnen, „Wie funktioniert die Exe? …“. Feature „Exe-Erstellung“ (für neue Projekte eingeschaltet): Exe aus dem Code erstellen bzw. aktualisieren, Exe veröffentlichen, Exe-Einrichtung prüfen.
- Die Zeile Exe nennt die Herkunft: „vom Cockpit erstellt“, „extern erstellt“ (Antwort 7) oder „aus dem Release“, dazu Datum und Version. „aktuell“ oder „älter als der Code“ nur bei Exe-Dateien, die das Cockpit gebaut hat. Ohne Angabe in cockpit.toml: „Herkunft unbekannt“.
- Zustand in cockpit.toml unter [exe], Einstellungen zum Bauen unter [exe.build]. Die .spec-Datei liegt im Ordner Code und wird mit hochgeladen. Eine vorhandene .spec-Datei wird nie überschrieben.
- Bauen: Python vom Rechner (beim Start aus dem Code das eigene, sonst py oder python), eigene .venv im Ordner Code, dort pip install -r requirements.txt und pyinstaller. Der Bau läuft in einem temporären Ordner, die Ausgabe steht im Fenster „Exe erstellen“ Zeile für Zeile, die vier Schritte sagt NVDA an.
- Test: Start-Test mit Wartezeit aus der Einstellung des Features (Vorgabe 10 Sekunden). Beendet sich das Programm vorher mit Rückgabewert 0, gilt der Test auch als bestanden. Mit self_test = true in [exe.build] läuft stattdessen --selbsttest.
- Ersetzen: erst nach bestandenem Test. Die bisherige Exe kommt in die Sicherheitskopien. Lässt sie sich nicht verschieben (läuft sie?), kommt alles zurück, und nichts wird ersetzt.
- Veröffentlichen: Version mit Vorschlag der nächsten Nummer, Tag vVersion auf dem Commit der Exe, wenn er schon auf GitHub ist, sonst auf dem Haupt-Branch. Ein Programmordner wird als ZIP-Datei angehängt. Versionshinweise selbst oder mit „Vorschlag der KI“ (Alt+I, weil Alt+V für Version belegt ist). Der Link kommt in die Zwischenablage.
- Holen: aus dem neuesten Release mit einer Exe- oder ZIP-Datei. Ob es eine gibt, fragt das Cockpit erst beim Ausführen, damit die Aktionsliste ohne Netz auskommt.
- Die eigene Exe des Cockpits: CodeCockpit.spec liegt im Code (mit allen Modulen von cockpit, Anleitungen, Prompts und Einführungen), eine einzelne Datei in Codecockpit\Exe\CodeCockpit.exe (Antwort 10). Läuft das Cockpit selbst als diese Exe, wartet die neue in Exe\_neu, und ein Startskript tauscht sie beim Neustart aus. Abweichung vom Konzept: Startet die neue Version nicht, stellt das Skript die alte nicht selbst wieder her. Sie liegt aber in den Sicherheitskopien (Menü Datei).
- Der Selbsttest (--selbsttest) läuft in einem leeren, eigenen Datenordner und berührt nie die echten Daten. Er prüft zusätzlich, ob Anleitungen, Prompts und Einführungen in der Exe sind.
- Anleitungen „Python installieren“ und „Wie funktioniert die Exe?“ im Menü Hilfe.
- Nach dem ersten echten Bau: Windows (Intelligente App-Steuerung) blockierte den Start der neuen Exe aus der Umgebung von Claude, beim Nutzer startet sie. Wunsch des Nutzers: Kann das Cockpit die Exe nicht selbst starten, fragt es, ob sie trotzdem übernommen werden soll (Vorgabe „Verwerfen“), und bittet den Nutzer, sie selbst zu prüfen. Die Zeile heißt dann „…, nicht geprüft“. Beim nächsten Bau versucht das Cockpit den Test wieder.
- Die Exe enthält keine Daten. Sie nutzt denselben Datenordner wie start.bat. Ein neuer Nutzer ohne diesen Ordner bekommt den Einrichtungsassistenten und eine leere Liste.


## 28.09.2026: Sicherheitsprüfung und erfundene Geheimnisse

- Wunsch des Nutzers vor dem ersten Hochladen des Cockpits: Werte, die ausdrücklich als erfunden gekennzeichnet sind, gelten nicht als Geheimnis. Erkannt werden Wörter wie „Erfunden“, „NurFuerTests“, „Beispiel“ oder „Example“ im Wert. Nur Wörter ab 7 Buchstaben, damit ein echter Token aus Zufallszeichen nie zufällig eines enthält.
- Eine Zeile mit dem Vermerk `pragma: allowlist secret` gilt nicht als Geheimnis (wie beim Prüfprogramm detect-secrets). Für Fehlalarme im Code.
- Die Beispiele, die die Prüfung in den Tests finden muss, enthalten dieses Wort nicht mehr und werden erst beim Testlauf zusammengesetzt. So findet die Prüfung sie nicht in den Test-Dateien selbst.
- Sieben alte Beispiel-Zeilen im Verlauf (Sommer2026!, Winter2026!, abc123def456, secret_history) stehen als „kein Geheimnis“ in cockpit.toml. Danach meldet die Prüfung beim Cockpit selbst nichts mehr, auch nicht im Verlauf.


## 28.09.2026: Updates der Exe des Cockpits (10e)

- Wunsch des Nutzers: Gibt es eine neue Exe, fragt das Programm, ob es aktualisieren soll. Konten und Daten dürfen nicht verloren gehen.
- Quelle ist das neueste Release von 1013hPascal/Codecockpit. Die Abfrage braucht keine Anmeldung, weil das Repository öffentlich ist.
- Wunsch des Nutzers: Die Information, ob eine neue Datei da ist, kommt aus dem Release. Deshalb vergleicht das Cockpit die Prüfsumme (SHA-256), die GitHub zu jeder Datei angibt, mit der laufenden Exe. Eine Versionsnummer in der Exe ist dafür nicht nötig. Ist die eigene Exe jünger als das Release (selbst gebaut), wird nichts angeboten.
- Die heruntergeladene Datei wird gegen die Prüfsumme geprüft. Weicht sie ab, wird sie gelöscht.
- Getauscht wird nur die laufende Exe-Datei, auch wenn sie in einem anderen Ordner liegt, etwa in Downloads. Die bisherige kommt in die Sicherheitskopien. Die Daten in %APPDATA% bleiben unberührt.
- Rückfrage mit „Später“ als Vorgabe. „Diese Version überspringen“ gilt nur für die automatische Prüfung. Hilfe, Nach Updates suchen fragt immer.
- Geprüft wird 10 Sekunden nach dem Start und danach höchstens einmal am Tag. Schalter in den Grundeinstellungen, Vorgabe an. Beim Start aus dem Code gibt es keine Prüfung.
- Die Versionsnummer im Code steht jetzt auf 1.1.0, passend zu den Releases.

## 28.09.2026: Ein Ordner pro Branch (10f)

- Wunsch des Nutzers: Jeder Branch soll auch im Explorer als Ordner zu sehen sein, damit man zum Beispiel mit Claude nur in einem Branch arbeitet. Umgesetzt mit Worktrees von Git: Code enthält Code\main und daneben einen Ordner pro Branch. Antworten stehen in fragen\phase-10f.md.
- Fester Teil des Kerns, kein Feature (Antwort 9). code_dir des Projekts ist der Ordner des Haupt-Branches. So arbeiten Exe-Bau, cockpit.toml und alles andere unverändert. Der Kern erkennt Code\main daran, dass Code selbst kein Git hat, aber ein Unterordner einen Ordner .git.
- In der Projektliste steht jeder Branch-Ordner als eigene Zeile unter „Code, main“ (Antwort 1). Seine Aktionen sind die von Code, nur im Branch-Ordner. Dazu „Branch-Ordner entfernen …“.
- Branches anderer (Kommentar des Nutzers): Zeile „Branches auf GitHub“, Enter zeigt sie zur Auswahl. Der gewählte steht vorübergehend in der Liste, ohne Ordner. „In Liste anpinnen“ legt seinen Ordner an. Die Auswahl wird nicht gespeichert.
- Neuer Branch: bekommt immer einen Ordner und beginnt beim neuesten Stand des Haupt-Branches auf der Plattform. Ohne Verbindung zur Plattform beim lokalen Haupt-Branch. Er folgt nicht origin/main, damit das Hochladen unter eigenem Namen geht.
- In der Übersicht Branches wird mit Branch-Ordnern nicht gewechselt. Der Knopf heißt dann „Ordner für … anlegen“.
- Ordnernamen: Schrägstriche und andere Zeichen, die Windows nicht erlaubt, werden zu Bindestrichen, zum Beispiel feature/login zu feature-login.
- Branch-Ordner entfernen: Der Branch bleibt. Liegt im Ordner etwas, das es sonst nirgends gibt, kommt er vorher in die Sicherheitskopien. Ein Branch, der auf der Plattform gelöscht wurde (meist nach dem Übernehmen), heißt in der Liste „auf GitHub gelöscht“.
- Virtuelle Umgebung: Ein neuer Branch-Ordner bekommt im Hintergrund eine eigene, wenn main eine hat (Antwort 5).
- Exe aus einem Branch (Antwort 6): kommt als <Name>_branch_<Ordner>.exe in den Ordner Exe, neben die normale. Sie zählt nicht als „die Exe“ des Projekts, wird beim Ersetzen der normalen nicht mitgesichert und bekommt keinen Vermerk in cockpit.toml.
- Neue Projekte (Antwort 7): Schalter „Neue Projekte mit einem Ordner pro Branch“ in den Grundeinstellungen, Vorgabe an. Gilt beim Herunterladen von GitHub und beim Hinzufügen eines Ordners mit Git vom Rechner. Ein Ordner ohne Git bekommt die Struktur erst über die Aktion, wenn er Commits hat, weil Branch-Ordner Git brauchen.
- Bestehende Projekte (Antwort 8): Aktion „Ordner für Branches einrichten …“ mit Rückfrage und Sicherheitskopie ohne .venv. Ist eine Datei in Benutzung, wird alles zurückverschoben. Die virtuelle Umgebung wird danach neu angelegt.
- Nur verknüpfte Projekte bleiben wie bisher (Antwort 10).
- Git legt in einem Branch-Ordner statt des Ordners .git eine Datei an. Das Erkennen eines offenen Zusammenführens liest deshalb den echten Git-Ordner (git.git_dir).
- Das Cockpit selbst stellt der Nutzer über die Exe um (Antwort 11). Danach kopiere ich die Einstellungen und Erinnerungen von Claude in den neuen Ordner.
- Version 1.1.1, damit der Nutzer damit das Update aus 10e testen kann (Antwort 12).


## 28.09.2026: Wünsche aus dem Test von 10f

- Eine Branch-Zeile hat ganz oben „<Branch> verwalten …“. Das Fenster zeigt nur diesen Branch: in main übernehmen, umbenennen, Branch-Ordner entfernen, löschen. „Branches …“ gibt es mit Branch-Ordnern nur noch auf „Code, main“, als Übersicht.
- In der Übersicht gibt es mit Branch-Ordnern keinen „aktuellen Branch“ mehr. Jede Zeile nennt stattdessen ihren Ordner oder „ohne Ordner“.
- Ein Branch, den es auf der Plattform noch nicht gibt, hat statt „Änderungen hochladen …“ die Aktion „Branch auf GitHub hochladen …“. Sie lädt ihn hoch, mit den Änderungen, falls es welche gibt. „Änderungen von GitHub holen …“ fehlt dann, weil es noch nichts zu holen gibt.
- Löschen eines Branches mit Ordner entfernt erst den Ordner (mit Sicherheitskopie, falls nötig), dann den Branch. Die Commits bleiben unter einem Sicherungsverweis.
- Fehler aus Hintergrundaufgaben stehen jetzt mit Details im Protokoll. Beim Test von 10f war der Grund für „Die virtuelle Umgebung ließ sich nicht anlegen“ nirgends zu finden.


## 28.09.2026: Exe mit Daten, Prüfung und KI-Hilfe (10g)

Anlass: Die VokabelApp des Nutzers. Ihre Exe startete nicht, und der Ordner Meine-Vokabeln sollte neben der Exe liegen, damit Nutzer dort Vokabeln hinzufügen. Drei Ursachen: Startdatei engine.py statt gui.py (der erste .py-Name im Alphabet), PySide6 fehlte in requirements.txt, und die Daten wurden im Startordner gesucht.

- Ordner neben der Exe: neue Einstellung „Ordner neben der Exe“ (cockpit.toml, [exe.build] beside). Beim ersten Bau kommen sie aus dem Ordner Code neben die Exe. Danach bleiben sie, wie die Nutzer sie haben, auch wenn eine neue Exe den Programmordner ersetzt: Dann kommen sie aus der Sicherheitskopie der alten Exe zurück. Das gilt auch für „Exe aus dem Release holen“ und „Exe-Datei wählen“.
- Beim Veröffentlichen kommen diese Ordner in die ZIP-Datei, so wie sie im Ordner Code stehen, nicht die eigenen Daten aus dem Ordner Exe. Eine einzelne Exe-Datei wird dann ebenfalls als ZIP-Datei hochgeladen.
- Start-Test: Ein Programm mit Fenster, das sich vor Ablauf der Testzeit beendet, gilt als nicht bestanden, auch ohne Fehler. So hätte die VokabelApp den Test nicht bestanden.
- Vorschlag für die Startdatei: erst die Datei, die eine .bat-Datei startet, dann eine mit __main__ und Fenster, dann main.py.
- Exe-Einrichtung prüfen meldet zusätzlich: Startdatei startet nichts (mit Vorschlag), Ordner, die der Code nutzt, aber nicht neben der Exe stehen, und Daten, die im Startordner gesucht werden. Fehlende Bibliotheken in requirements.txt sind jetzt ein Problem statt einer Warnung, weil sie dann in der Exe fehlen.
- Neue Aktion „Exe-Einstellungen …“. Ändert sich die .spec-Datei, kommt die alte vorher in die Sicherheitskopien.
- Neue Aktion „Exe mit KI einrichten …“: Der Nutzer beschreibt freiwillig, was die Exe können soll. Der feste Teil (Startdatei, Ordner neben der Exe, requirements.txt) kommt ohne KI. Die KI schlägt Änderungen am Code vor, im festen Format aus dem Prompt exe_fix. Eine Änderung gilt nur, wenn ihr alter Text genau einmal in der Datei steht und die Datei im Ordner Code liegt. Nichts ändert sich ohne Bestätigung. Vorher kommt eine Sicherheitskopie der betroffenen Dateien und von cockpit.toml. Danach bietet das Cockpit an, die Exe zu bauen und zu testen.
- Ohne KI oder ohne Einverständnis zum Senden bietet die Aktion nur den festen Teil an.
- Die KI bekommt nie den ganzen Code: die Startdatei (bei mehr als 4000 Zeichen nur Anfang und Ende) und Auszüge um die Stellen, an denen Daten im Startordner gesucht werden, zusammen höchstens die Hälfte der Zeichengrenze aus den Grundeinstellungen.
- Der Start-Test prüft nur, dass die Exe startet. Ob die Daten richtig erscheinen, prüft der Nutzer selbst.

## 28.09.2026: Zustand der Exe lokal, Threads sauber beenden (nach dem Test von 10g)

- Wunsch des Nutzers: In main stand nach jedem Bau und Veröffentlichen wieder eine Datei zum Hochladen. Grund: Der Zustand der Exe (Herkunft, Datum, Commit, Version, geprüft) stand in cockpit.toml, und die gehört zum Code. Er liegt jetzt im Git-Ordner des Projekts, Datei codecockpit-exe.toml. Der wird nie hochgeladen, und jeder Rechner hat seinen eigenen Zustand. Ohne Git bleibt er in cockpit.toml. Ein alter Zustand in cockpit.toml wird noch gelesen und beim nächsten Schreiben einmal entfernt. Die Einstellungen zum Bauen ([exe.build]) bleiben in cockpit.toml, weil sie zum Projekt gehören.
- Nach dem Ende einer Hintergrundaufgabe wartet das Cockpit jetzt, bis ihr Thread ganz beendet ist, bevor es sie freigibt. Sonst konnte Qt das Programm abbrechen. So brachen auch Testläufe gelegentlich ab.
- Die Versionsnummer im Code war beim Release 1.1.2 nicht angepasst worden, die Exe meldete deshalb 1.1.1. Sie steht jetzt auf 1.1.3.
- Smart App Control blockiert neue, nicht signierte Exe-Dateien je nach ihrem Ruf, also nicht vorhersehbar. Dauerhaft hilft nur eine Signatur. Bis dahin startet start.bat das Cockpit über Python. Entscheidung zur Signatur weiter offen (TODO.md).

## 29.09.2026: Spracheingabe (8d)

Antworten in fragen\phase-08d.md, alle Vorschläge angenommen.

- Kein Knopf, nur Tasten, wie im Tagebuch des Nutzers: Strg+D startet und beendet, Strg+Umschalt+D bricht ab. Die Tasten gelten im ganzen Programm, auch in Dialogen. Außerhalb eines Textfelds sagt das Cockpit, dass Diktieren nur dort geht.
- Neuer Dienst „Sprach-KI“ (speech) neben „KI“. Er ist da, wenn faster-whisper, sounddevice und numpy geladen werden können. Features mit KI oder Sprach-KI stehen in der Feature-Verwaltung in der Gruppe „KI“.
- Das Feature Spracheingabe gilt für das ganze Cockpit, nicht pro Projekt. Einstellungen: Sprache (Deutsch, Englisch, automatisch) und längste Aufnahme (Vorgabe 10 Minuten).
- Whisper läuft lokal auf dem Prozessor mit int8, wie im Tagebuch. Die Aufnahme bleibt im Arbeitsspeicher und wird nie gespeichert. Eine externe Sprach-KI kommt später.
- Die Modelle liegen im Datenordner unter models\whisper, nicht in der Exe. Das Cockpit lädt eines erst nach Rückfrage, beim ersten Diktieren oder in der KI-Verwaltung unter „Sprach-KI …“. Dort wählt und löscht man Modelle. Ohne Wahl gilt die Empfehlung nach Arbeitsspeicher. Gelöschte Modelle kommen nicht in die Sicherheitskopien, weil man sie jederzeit neu herunterladen kann.
- Die Bibliotheken kommen in die Exe (Antwort 6). Die Exe wird dadurch deutlich größer. Für Releases ist das kein Problem, GitHub erlaubt dort bis 2 GB pro Datei.
- Wechselt man während der Umwandlung das Feld, kommt der Text in das Feld, in dem die Aufnahme begann. Gibt es das nicht mehr, kommt er in die Zwischenablage.
- Version 1.2.0 (Antwort 10).

## 29.09.2026: Rückmeldungen zu 8d und KI-Hilfe (8e)

- Feature-Verwaltung: Von „KI“ führt ein Tab direkt in die Liste „KI-Features“ (Wunsch aus dem Test von 8d).
- Whisper-Modelle im Zwischenspeicher von Hugging Face, zum Beispiel vom Tagebuch, erkennt das Cockpit und nutzt sie ohne neuen Download. Löschen kann es nur seine eigene Kopie im Datenordner, weil andere Programme den Zwischenspeicher mitnutzen.
- Sprach-KI: Liste mit Kontrollkästchen statt Enter zum Wählen. Genau ein Modell ist angehakt. Enter drückt auch dort den Knopf mit dem Fokus.
- KI-Hilfe (8e) nach dem Vorschlag aus Frage 22 zu Phase 8, die offen geblieben war: Wissen aus Anleitungen, Einführungen und einer Beschreibung der Bedienung, die das Cockpit beim Fragen selbst erzeugt (Aufbau, Tastenkürzel, Menüs, Aktionen nach Art der Zeile). Menüs und Tastenkürzel gehen immer mit, von den übrigen Abschnitten die mit den meisten Wörtern aus der Frage, bis zur Zeichengrenze aus den Grundeinstellungen. Weiß die KI etwas nicht, sagt sie das.
- KI-Hilfe über Hilfe, KI-Hilfe oder Umschalt+F1. Die KI bekommt nur die Frage und Auszüge aus der Hilfe, nie Code oder Zugangsdaten. Der Fokus bleibt beim Warten im Feld Frage, NVDA sagt „Antwort da.“.
- Version 1.3.0, weil 1.2.0 mit 8d schon aus main veröffentlicht wird.

## 29.09.2026: Phase 9, Versionen und README-Pflege

Antworten in fragen\phase-09.md: alle Vorschläge angenommen, aber in einem Schritt statt drei, und ohne Markierungen in der README.

- Versionen: Schritt im Ablauf „Änderungen hochladen“ vor dem Commit. Auswahl „Keine neue Version“ (Vorgabe), „Kleine Korrektur“, „Neue Funktion“, „Große Änderung“, jeweils mit der neuen Nummer. Die erste Version ist 1.0.0. Tag v1.2.3 nach dem Commit, hochgeladen nach dem Branch.
- Steht __version__ = "x.y.z" im Code, ändert das Cockpit die Nummer mit, im selben Commit. Die Datei findet es selbst oder sie steht in den Einstellungen des Features.
- „Exe veröffentlichen“ schlägt mit dem Feature die zuletzt gesetzte Version vor, wenn es dazu noch kein Release gibt.
- README ohne Markierungen (Wunsch des Nutzers): Welche Abschnitte vom Cockpit stammen, steht in cockpit.toml als Fingerabdruck des Textes ([readme.managed]). Steht der Text noch so da, darf das Cockpit ihn erneuern. Ist er geändert oder war er nie vom Cockpit, gilt er als Text des Nutzers und wird nie angefasst.
- Jeder vorgeschlagene Abschnitt kommt einzeln (Wunsch des Nutzers): Übernehmen, auch angepasst, Überspringen (auch mit Escape) oder Alle abbrechen.
- Abschnitte ordnet das Cockpit über ihre Überschrift zu, in Englisch, Deutsch, Französisch und Spanisch. Unbekannte Überschriften sind immer Text des Nutzers.
- Selbst geschrieben vom Cockpit: Download, Installation, Änderungen (aus den Versionen), Windows-Warnungen mit Prüfsumme, Lizenz, Liste der Bibliotheken. Von der KI: Funktionen, Bedienung, Systemanforderungen (einmal bestätigt, dann aus cockpit.toml) und die Erklärung der Bibliotheken. Ohne KI nur der feste Teil.
- Sprachen pro Projekt in cockpit.toml über „README-Sprachen …“, sonst aus den Einstellungen des Features. Hauptsprache in README.md, weitere in README.xx.md, oben eine Zeile mit Links zu allen.
- Übersetzt werden die übernommenen Abschnitte und solche, die in einer Übersetzung ganz fehlen. In einer Übersetzung selbst geschriebene Abschnitte bleiben.
- Prüfung vor dem Hochladen: nur wenn sich mehr als README oder cockpit.toml geändert hat. Die KI bekommt Commit-Nachricht, geänderte Dateien, den Überblick der Änderungen ohne vertrauliche Dateien und die README. Jeder Vorschlag kommt als Textfrage: OK übernimmt (auch angepasst), Abbrechen überspringt. Klappt die KI nicht, geht das Hochladen weiter.
- Version 1.4.0.


## 29.09.2026: README auf der Projektzeile, Vorschläge bei neuer Version

- Wunsch des Nutzers: Die README-Aktionen stehen auf der Projektzeile, nicht mehr auf Code: „README erstellen …“, „README ansehen“, „README bearbeiten …“, „README-Sprachen …“.
- „README bearbeiten …“ zeigt die README als Text zum selbst Bearbeiten. Speichern legt vorher eine Sicherheitskopie an. „Vorschläge der KI …“ startet das abschnittsweise Ergänzen, das vorher „README aktualisieren …“ hieß. Selbst geänderte Abschnitte gelten danach als eigener Text.
- Wunsch des Nutzers: Wird beim Hochladen eine neue Version gesetzt, prüft das Cockpit die README immer, auch wenn die normale Prüfung ausgeschaltet ist. Zuerst schlägt es den Abschnitt Änderungen mit der neuen Version und den Commits seit der letzten vor, dann macht die KI Vorschläge für andere Abschnitte. Dafür läuft die Prüfung jetzt nach der Frage nach der Version.


## 29.09.2026: Phase 14, Releases und GitHub Actions

Wunsch des Nutzers: Phase 14 vor den Phasen 11 bis 13, weil danach alle Grundfunktionen da sind. Antworten in fragen\phase-14.md, alle Vorschläge angenommen.

- Neues Feature „Releases“, für neue Projekte an. Es braucht eine Plattform mit Releases.
- Nach dem Hochladen einer neuen Version fragt das Cockpit „Für Version … ein Release auf GitHub anlegen?“, Vorgabe „Später“. Mit aktiver Exe-Erstellung und vorhandener Exe geht es weiter wie „Exe veröffentlichen“, sonst ein Release nur mit dem Quellcode, das an das Tag der Version kommt. Sagt der Nutzer „Später“, kommt wie bisher das Angebot eines Pull Requests.
- Die Versionshinweise schlägt die KI vor wie bei „Exe veröffentlichen“. Das Fenster ist dasselbe.
- „Releases …“ auf der Projektzeile: Liste mit Version, Datum, Downloads und ob eine Exe dabei ist. Versionshinweise ansehen und bearbeiten, Link kopieren, im Browser öffnen, löschen. Beim Löschen bleibt das Tag.
- „GitHub Actions …“ auf der Projektzeile, nur wenn im Ordner .github\workflows ein Workflow liegt. Das prüft das Cockpit lokal, ohne GitHub zu fragen. Liste der letzten 20 Läufe, Fehler lesen, neu starten (bei einem Fehlschlag nur die fehlgeschlagenen Teile), im Browser öffnen, aktualisieren.
- Fehler lesen: die Ausgabe des ersten fehlgeschlagenen Teils, ohne Zeitstempel und Farbcodes, das Ende und davor alle Zeilen mit Fehlern. Die Erklärung der KI kommt wie im Terminal, die KI bekommt nur die Ausgabe.
- Hinweis „GitHub Actions fehlgeschlagen“ in der Projektzeile. Der letzte Lauf wird mit den Repositories und Pull Requests abgefragt und in der Datenbank gemerkt.
- Exe in der Cloud bauen kommt später, zusammen mit dem Signieren (Antwort 7).
- Der Zugang bittet schon seit Phase 4 um das Recht workflow. Fehlt es, meldet GitHub das beim ersten Versuch.
- Version 1.5.0.


## 29.09.2026: Projektsammlungen

Wunsch des Nutzers: Die Projekte sollen sich nach Themen ordnen lassen, zum Beispiel Webseiten, KI-Programme und private Programme. Gebaut im Branch sammlungen.

- Ganz oben in der Projektliste steht „Neue Projektsammlung“. Enter öffnet ein Fenster mit dem Feld „Name“ und OK. Die Sammlung heißt dann „Sammlung Name“.
- Die Sammlungen stehen unter „Projekt von GitHub herunterladen“, nach Namen sortiert, mit der Zahl der Projekte. Danach kommen die Projekte ohne Sammlung und die Repositories, die nur auf GitHub liegen.
- Enter, Leertaste oder Pfeil rechts öffnet eine Sammlung. Dann stehen oben die Sammlung mit „geöffnet“ und darunter nur ihre Projekte. Sie werden bedient wie sonst. So bleibt die Liste flach wie bisher (Entscheidung zu Phase 2), statt drei Ebenen einzurücken.
- Schließen: Enter oder Pfeil links auf der Sammlung, Rücktaste überall darin. Pfeil links auf einem zugeklappten Projekt springt zur Sammlung, wie in einem Baum.
- Aktionen einer Sammlung: „Projekte für die Sammlung …“, „Projektsammlung umbenennen …“, „Projektsammlung auflösen …“.
- „Projekte für die Sammlung …“ zeigt eine Liste mit Kontrollkästchen. Der erste Eintrag ist der Hinweis, wie gewünscht. Projekte anderer Sammlungen heißen „…, in Sammlung …“. Wer sie markiert, nimmt sie dort heraus. Enter in der Liste speichert.
- Ein Projekt ist in höchstens einer Sammlung. Das sichert die Datenbank selbst (Tabelle collection_members mit dem Projekt als Schlüssel).
- Die Sammlungen stehen nur in der Datenbank des Rechners, nicht in cockpit.toml. Sie gehören zur eigenen Ordnung, nicht zum Projekt. Auflösen ändert keine Dateien, deshalb gibt es dafür keine Sicherheitskopie, nur die Rückfrage mit „Abbrechen“ als Vorgabe.
- Nachtrag nach dem Test (Wunsch des Nutzers): Auch Repositories, die nur auf GitHub liegen, kommen in Sammlungen. Die Liste „Projekte für die Sammlung …“ sagt bei jedem Eintrag, wo er liegt: „nur auf dem Rechner“, „auf dem Rechner und auf GitHub“ oder „nur auf GitHub“. Für ein Repository nur auf GitHub merkt sich das Cockpit die Adresse. Nach dem Herunterladen steht das Projekt von selbst in derselben Sammlung.
- Nachtrag nach dem Test (Wunsch des Nutzers): Die Zeile einer Sammlung sagt den Stand, zum Beispiel „Sammlung Web, 3 Projekte, Änderungen offen“ oder „…, nichts offen“. Offen heißt: Dateien noch nicht hochgeladen oder ein Zusammenführen nicht abgeschlossen, auch in Branch-Ordnern. „nichts offen“ steht erst da, wenn der Stand aller Projekte abgefragt ist. Repositories nur auf GitHub haben nichts offen.


## 30.09.2026: Projektübersichten und Aktionsmenüs

Wunsch des Nutzers, gebaut im Branch projektuebersichten. Checkliste in checklisten\projektuebersichten.md.

- Unter einem ausgeklappten Projekt steht zuerst der Haupt-Branch. Mit Branch-Ordnern heißt die Zeile „Main-Branch, …“ statt „Code, main, …“. Ohne Branch-Ordner bleibt „Code, …“, weil die Zeile dann auch einen anderen Branch zeigen kann.
- Direkt darunter steht „Branches verwalten“, sobald das Repository einen Commit hat. Enter öffnet die Übersicht der Branches. Sie ersetzt „Branches …“ im Menü von Code.
- In der Übersicht steht oben „Neuer Branch …“, dann der Haupt-Branch und die Branches. Beim Haupt-Branch kommt mit Tab die Liste „Exe“ mit Version und ob die Exe veröffentlicht ist. Das Cockpit liest das aus seiner eigenen Notiz zur Exe, ohne GitHub zu fragen. Bei einem Branch kommen „In main übernehmen …“, „Umbenennen …“, „Branch-Ordner entfernen …“ und „Löschen …“.
- Menü Main-Branch: Projekt neu einlesen, Terminal, Änderungen auf GitHub hochladen, Änderungen von GitHub holen, Pull Requests, Verlauf, Änderungen verwerfen, Änderungen beiseitelegen, Git-Identität, Code-Ordner öffnen.
- Menü Branch: dasselbe, statt „Pull Requests …“ aber „Pull Request erstellen …“ und „Pull-Requests-Übersicht …“. „… verwalten …“ und „Branch-Ordner entfernen …“ sind in „Branches verwalten“ gewandert.
- Einträge, die nur manchmal passen, bleiben und erscheinen nur dann: Konflikte lösen, Auf GitHub hochladen, Branch auf GitHub hochladen, Beiseitegelegte Änderungen, Mit vorhandenem Repository verbinden, Virtuelle Umgebung neu anlegen, Exe aus diesem Branch erstellen, Ordner für Branches einrichten. Sie stehen nach der gewünschten Reihenfolge, Konflikte lösen ganz oben.
- Menü Exe: Projekt neu einlesen, Exe starten, Exe aus dem Code erstellen, Exe veröffentlichen, Exe einlesen, Exe-Einstellungen, Links der Exe, Exe-Ordner öffnen, Wie funktioniert die Exe?. „Exe starten“ bleibt, weil Enter auf der Zeile Exe es ausführt.
- „Exe aus dem Code erstellen …“ fasst Erstellen, Aktualisieren, Exe-Einrichtung prüfen und Exe mit KI einrichten zusammen: erst die Wahl „Exe mit KI einrichten …“ oder „Exe ohne KI einrichten …“ (mit eingerichteter Text-KI steht „mit KI“ oben), dann das Ergebnis mit „Exe erstellen“ und „Abbrechen“. „Ohne KI“ ist die bisherige Prüfung der Einrichtung.
- „Exe einlesen …“ fasst „Exe-Datei wählen …“ und „Exe aus dem Release holen …“ zusammen.
- „Links der Exe …“ zeigt Release, Download dieser Version und Download der neuesten Version. Den Download-Link bildet das Cockpit nach dem Muster von GitHub aus der Adresse des Releases.
- Menü Projekt: Projekt neu einlesen, Terminal, Projekt verwalten (bisher Repository verwalten), Links, README, Features dieses Projekts, Aus der Liste entfernen, Projektordner öffnen. „Links …“ nennt auch das neueste Release, wenn der Tresor offen ist und es eins gibt.
- „README …“ fragt: „README erstellen …“ (nur ohne README) oder „README bearbeiten …“, dazu „README-Einstellungen …“ (bisher README-Sprachen). „README ansehen“ entfällt, weil Bearbeiten den Text auch zeigt.
- Offen: „Releases …“ und „GitHub Actions …“ standen nicht in der Liste des Nutzers. Sie bleiben vorerst beim Projekt nach README.
- Nachtrag vom 01.10.2026 (Wunsch des Nutzers): Beim Einrichten mit KI bleibt ein Fenster offen, solange das Cockpit liest und die KI arbeitet. Die Liste „Fortschritt“ nennt oben die Zeit seit dem Start, darunter jede gelesene Datei („Datei 3 von 12 gelesen: …“) und was an die KI ging. Wie lange die KI selbst noch braucht, kann das Cockpit nicht wissen, weil sie erst am Ende antwortet. Deshalb steht dort die Zeit, keine Prozentzahl. „Abbrechen“ schließt das Fenster sofort. Die Anfrage läuft dann im Hintergrund aus, ihr Ergebnis wird verworfen.
- Nachtrag vom 01.10.2026 (Wunsch des Nutzers): Die KI ändert beim Einrichten der Exe nie direkt main. Ihre Änderungen kommen in den Branch „Cockpit-exe-bauen“. Er beginnt beim Stand von main auf diesem Rechner, weil der Vorschlag der KI genau zu diesem Stand passt. Mit Branch-Ordnern bekommt er einen eigenen Ordner, ohne Branch-Ordner wechselt der Ordner Code zu ihm. Das Cockpit committet nur die geänderten Dateien, mit „Exe-Einrichtung mit KI“. Die Exe wird aus dem Branch gebaut und liegt als eigene Datei neben der normalen. Nach einem erfolgreichen Test fragt das Cockpit: „Selbst testen, später in main übernehmen“ (Vorgabe), „Jetzt in main übernehmen, Branch behalten“ oder „Jetzt in main übernehmen und Branch löschen“. Übernehmen wirkt nur auf diesem Rechner, hochgeladen wird erst mit „Änderungen auf GitHub hochladen“.
- Nachtrag vom 01.10.2026 (Bau der Vokabel-App scheiterte, Wunsch des Nutzers): Der Pfad einer Datei von PySide6 im Branch-Ordner war 271 Zeichen lang. Windows erlaubt ohne Zusatzeinstellung 260. Deshalb drei Änderungen:
  - Die virtuelle Umgebung zum Bauen liegt nicht mehr im Ordner Code, sondern kurz unter %LOCALAPPDATA%\CodeCockpit\venvs\<Projekt>-<Kennung>. Die eigene .venv des Projekts zum Entwickeln bleibt, wo sie ist, und wird beim Bauen nicht mehr benutzt. Der erste Bau danach installiert die Bibliotheken einmal neu, meist schnell aus dem Zwischenspeicher von pip.
  - Ein Branch nutzt die Umgebung von main mit, wenn seine requirements.txt gleich ist. Sonst bekommt er eine eigene (Kennung mit -b), damit die Umgebung von main sauber bleibt.
  - Scheitert pip an langen Pfaden, bietet das Cockpit an, lange Pfade in Windows einzuschalten. Windows fragt dafür nach Administratorrechten. Die Einrichtung ohne KI warnt, wenn lange Pfade aus sind. Die Anleitung zur Exe beschreibt auch den Weg von Hand.
  - Vorinstallierte Bibliotheken zum Kopieren gibt es nicht: Virtuelle Umgebungen lassen sich nicht zuverlässig verschieben, jedes Projekt braucht andere Versionen, und pip hebt Downloads ohnehin auf.


## 02.10.2026: Problem mit KI lösen, Stand in den Aktionen, Branches anzeigen, Reihenfolge

Wünsche des Nutzers, gebaut im Branch exe-ki-und-branches. Checkliste in checklisten\exe-ki-und-branches.md.

- Scheitert der Bau der Exe, zeigt das Bau-Fenster „Problem mit KI lösen“. Die KI bekommt die Fehlermeldung, das Ende der Ausgabe und die Stellen im Code, die ein Traceback nennt. Das Fenster „Fortschritt“ sagt „Die KI versucht, das Problem zu lösen“ mit der Zeit seit dem Start. Danach wie beim Einrichten: Vorschlag, Branch Cockpit-exe-bauen, „Exe erstellen“. Scheitert der Bau wieder, beginnt der nächste Durchgang. Gibt es den Branch schon, liest die KI dort, damit jeder Versuch auf dem vorigen aufbaut.
- Hinter vielen Aktionen steht der Stand, zum Beispiel „Änderungen auf GitHub hochladen …, 3 Dateien offen“ oder „…, alles aktuell“. Er kommt aus dem schon bekannten Stand des Projekts, ohne neue Abfrage. Pull Requests zählen beim Haupt-Branch alle offenen des Repositories, bei einem Branch die aus diesem Branch. Reviews zählt das Cockpit noch nicht, dafür müsste es sie erst abfragen und speichern.
- „In main übernehmen …“ nennt „2 Commits offen“ oder „alles aktuell“. Die Exe nennt „noch keine Exe“, „Exe aktuell“ oder „Code geändert seit dem letzten Bau“, Veröffentlichen die letzte Version.
- „Branches verwalten“: unter „Neuer Branch …“ die Auswahl „Branches anzeigen“ mit „Die Sie lokal haben“ (Vorgabe), „Die nur auf GitHub sind“ und „Alle“. Leertaste oder Enter öffnet ein Menü. So bleibt die Übersicht klar, auch wenn viele an eigenen Branches arbeiten. Branches nur auf GitHub: „Herunterladen“, „Umbenennen …“, „Löschen …“. Der Titel zählt weiter alle Branches.
- In der Projektliste stehen unter einem Projekt nur die lokalen Branches. „Branches auf GitHub“ und die dort angepinnten Branches entfallen.
- Ganz oben stehen Sammlungen und Projekte ohne Sammlung gemischt, das zuletzt Geänderte oben. Eine Sammlung zählt so neu wie ihr neuestes Projekt. In den Sammlungen bleibt die Reihenfolge, wie sie war.
- Nachtrag (Vokabel-App, Ordner Meine-Vokabeln fehlte neben der Exe): Beim Bau aus einem Branch legte das Cockpit die Ordner neben der Exe gar nicht an. Jetzt kommen sie aus dem Branch mit, wie bei der normalen Exe. Gibt es einen gewählten Ordner im Code nicht, legt das Cockpit ihn neben der Exe leer an. Fehlende Dateien legt es nicht an.
- Nachtrag: In den Exe-Einstellungen sind die Ordner neben der Exe eine Liste mit Kontrollkästchen statt eines Textfelds mit Kommas. Vom Code benutzte Ordner heißen „…, vom Code benutzt“ und sind vorgeschlagen. Mit „Neuer Ordner neben der Exe“ und „Hinzufügen“ kommt ein Ordner dazu, den es im Code noch nicht gibt. Das Fenster vor „Exe erstellen“ nennt, welche Ordner neben die Exe kommen.
- Nachtrag: Die Anweisung an die KI erklärt jetzt, dass das Cockpit die Ordner neben die Exe legt, dass der Code sie über den Ort der Exe finden muss und fehlende Ordner beim Start selbst anlegen soll.
- Nachtrag (Wunsch des Nutzers): Im KI-Modus steht unter dem Vorschlag der KI und unter dem Ergebnis vor „Exe erstellen“ das Feld „Frage an die KI“. Die KI beantwortet Fragen zum Schritt, man kann nachfragen und diskutieren. Sie ändert dabei nichts. Danach „Übernehmen“ bzw. „Exe erstellen“ oder „Mit den Hinweisen wiederholen“. Dann läuft das Lesen und Vorschlagen noch einmal, mit dem Gespräch als Hinweis. Die Hinweise bleiben für weitere Durchgänge erhalten. Ohne KI gibt es das Feld nicht.
- Nachtrag (Wunsch des Nutzers, in einem Rutsch): „Exe aus dem Code erstellen …“ zeigt als ersten Schritt die Exe-Einstellungen mit dem gespeicherten Stand. Der Fokus steht in der Liste der Ordner neben der Exe. Weiter speichert die Einstellungen wie „Exe-Einstellungen …“ (cockpit.toml und .spec-Datei, die bisherige .spec kommt in die Sicherheitskopien). Dann folgen mit oder ohne KI, das Ergebnis und der Bau. Beim Bau aus dem Branch gelten die hier gewählten Ordner, dazu, was die KI im Branch ergänzt hat.
- Nachtrag (Vokabel-App: NameError, sys nicht importiert): Der Start-Test hielt eine Exe mit Fenster für gut, obwohl sie abstürzte. PyInstaller zeigt den Absturz in einem Meldungsfenster, zum Beispiel „Unhandled exception in script“, und das Programm läuft weiter, bis man es schließt. Der Test sucht jetzt jede Sekunde nach so einem Fenster des Programms und seiner Kindprozesse und liest seinen Text. Findet er eins, ist der Test nicht bestanden, und die Fehlermeldung steht in der Ausgabe. Damit greift auch „Problem mit KI lösen“ mit der echten Meldung. Nur Windows, über ctypes.
- Nachtrag (Wunsch des Nutzers): „Selbst testen, später in main übernehmen“ öffnet das Fenster „Exe selbst testen“ mit „Exe starten“, einem Feld für die Fehlermeldung oder eine Beschreibung, „Problem mit KI lösen“, „Funktioniert, in main übernehmen …“ und „Später“. Mit „Problem mit KI lösen“ geht der Text an die KI, und der nächste Durchgang beginnt.
- Nachtrag (Meine-Vokabeln neben der Exe war leer): Die Exe legte den Ordner beim Start-Test selbst leer an, danach galt er als vorhanden und blieb leer. Jetzt zählt ein leerer Ordner nicht als vorhanden. Er wird aus der bisherigen Exe gefüllt, wenn dort etwas lag, sonst aus dem Ordner Code. Ein Ordner mit Inhalt bleibt unangetastet, damit Daten der Nutzer nicht überschrieben werden.
- Nachtrag (Wunsch des Nutzers): In der Auswahl stehen auch Dateien wie README, .bat- oder .ico-Dateien. Ausgenommen sind nur Python-Code, .spec-, .exe-Dateien sowie cockpit.toml, requirements.txt und .gitignore. Eine Datei, die neben der Exe schon liegt, bleibt unverändert.
- Nachtrag (Wunsch des Nutzers): Eine README neben der Exe (README, README.md, README.de.md …) ist immer die aktuelle aus dem Code. Bei jedem Bau wird sie erneuert, wenn sie sich geändert hat. Die bisherige kommt vorher in die Sicherheitskopien. Andere Dateien neben der Exe bleiben unverändert, weil sie Daten der Nutzer sein können.
- Nachtrag (Vokabel-App, zweimal NameError wegen fehlendem import sys): Das Cockpit prüft fehlende Importe jetzt selbst, ohne KI. Benutzt eine Datei sys, os oder Path, ohne es zu importieren, schlägt die Einrichtung die fehlende Zeile als Änderung vor, und die Einrichtung ohne KI nennt es als Problem. Beim Übernehmen ergänzt das Cockpit fehlende Importe in den geänderten Dateien von selbst und nennt das im Ergebnis. Vorher prüft es, ob der neue Code übersetzt. Ist er fehlerhaft, schreibt es gar nichts, und die Meldung nennt Datei und Zeile.
- Nachtrag (Wunsch des Nutzers): Bei Repositories, die nur auf GitHub liegen, steht „Repository löschen …“ bei den Aktionen, vor „Aus der Liste entfernen …“. Man muss sie nicht erst herunterladen. Die Rückfragen sind dieselben wie bei „Projekt verwalten“: Warnung mit „Stattdessen archivieren …“, Abbrechen als Vorgabe, dann den Namen eintippen, bei fehlendem Recht eine kurze zweite Anmeldung im Browser. Die Warnung sagt, dass es auf dem Rechner keine Kopie gibt. Nach dem Löschen verschwindet das Repository aus der Liste.


## 03.10.2026: Eigene Bauanleitung schützen, Unbedingtes in den Exe-Einstellungen

Rückmeldung des Nutzers: Die neue Exe des Cockpits brach beim Start mit „Die Features sind fehlerhaft beschrieben.“ ab. Gebaut im Branch exe-einstellungen, Checkliste in checklisten\exe-einstellungen.md.

- Ursache: Der erste Schritt von „Exe aus dem Code erstellen“ speicherte die Exe-Einstellungen und schrieb dabei die von Hand geschriebene CodeCockpit.spec mit der Standardvorlage neu. Damit fehlten in der Exe die Einführungen der Features, die Anleitungen, die Vorlagen für die KI, die Module und die Teile für Whisper. Die Bauanleitung ist aus Git wiederhergestellt.
- Das Cockpit schreibt eine .spec-Datei nur noch neu, wenn es sie selbst erstellt hat. Das erkennt es an der ersten Zeile „# Erstellt von CodeCockpit.“. Bei einer von Hand geschriebenen ändern sich nur die Einstellungen in cockpit.toml. Das Einstellungsfenster blendet dann Startdatei, Name, Bauart und Symbol aus und sagt, dass sie in der Bauanleitung stehen.
- Wunsch des Nutzers: Was der Code unbedingt braucht, steht oben in der Liste „Ordner und Dateien neben der Exe“, heißt „…, unbedingt nötig, vom Code benutzt“ und ist immer vorab angehakt. Unbedingt nötig ist, was der Code als Ordner oder Datei im Ordner Code benutzt und die .spec-Datei nicht schon in die Exe packt. Wer es abhakt, wird beim Weiter gefragt. Die sichere Antwort „Wieder anhaken“ ist die Vorgabe.
- Nachtrag (Rückmeldung des Nutzers: die Einrichtung wollte erklärvideos neben die Exe legen, obwohl nicht angehakt): Den Vorschlag machte nicht die KI, sondern der feste Teil der Einrichtung. Er kannte die .spec-Datei nicht und übersah, dass sie erklärvideos schon in die Exe packt. Er schlägt jetzt gar keine Ordner neben der Exe mehr vor, denn die wählt man im ersten Schritt, und das Unbedingte ist dort angehakt. Bei einer von Hand geschriebenen .spec-Datei schlägt er auch keine andere Startdatei vor.


## 03.10.2026: Update-Suche findet auch ZIP-Releases

Rückmeldung des Nutzers: Die Suche nach Updates fand keine neue Version mehr. Ursache: Seit Version 1.1.13 liegt LICENSE neben der Exe. Deshalb hängt am Release CodeCockpit.zip statt CodeCockpit.exe, und die Suche kannte nur Exe-Dateien.

- Die Suche nimmt eine Exe am Release, wenn es eine gibt, sonst CodeCockpit.zip. Andere ZIP-Dateien zählen nicht.
- Die ZIP-Datei wird geladen und gegen die Prüfsumme von GitHub geprüft. Dann holt das Cockpit nur die Exe heraus, an einen festen Ort in Exe\_neu, und tauscht sie wie bisher aus. Die übrigen Dateien der ZIP, etwa LICENSE, bleiben, wie sie sind.
- Enthält die ZIP keine passende Exe oder einen Programmordner mit _internal, bricht das Cockpit ab und erklärt es. Die bisherige Version bleibt.


## 03.10.2026: README aus Ordner hochladen, mit KI schreiben und bearbeiten

Wunsch des Nutzers: „README …“ auf der Projektzeile bekommt neue Einträge. Die KI schreibt die ganze README auf einmal, statt jeden Abschnitt einzeln vorzuschlagen. Gebaut im Branch Readme-ueberarbeiten, Checkliste in checklisten\readme-ueberarbeiten.md.

- Ohne README stehen dort „README-Einstellungen …“, „README aus Ordner hochladen …“ und „README mit KI schreiben …“. Mit README stehen dort „README-Einstellungen …“ und „README bearbeiten …“. Die Reihenfolge folgt dem Wunsch des Nutzers.
- „README aus Ordner hochladen …“ kopiert eine gewählte Markdown- oder Textdatei als README.md in den Ordner Code, nach einer Rückfrage. Hochgeladen auf GitHub wird sie nicht sofort, sondern wie jede Änderung (Antwort des Nutzers).
- „README mit KI schreiben …“: Liste „Dateien mit Infos zum Programm“ mit Hinzufügen und Entfernen, Feld „Infos für die README“, Knöpfe „Von KI verfassen lassen“ und „README ist fertig so“. Nach dem ersten Text erscheinen das Feld „README-Text“ und darunter „Verbesserungsvorschläge für die KI“. Mit Vorschlägen überarbeitet die KI den Text, ohne Vorschläge schreibt sie ihn neu. Der Fokus springt auf den Text, wenn er da ist, weil der Nutzer darauf wartet.
- „README bearbeiten …“: Feld „README-Text“, Feld „Anweisungen an die KI zur Überarbeitung“, Knöpfe „Von KI überarbeiten lassen“ und „Die README ist fertig so“. Bearbeitet wird README.md. Die Übersetzungen entstehen danach neu aus ihr.
- Der bisherige Weg mit einzelnen Abschnitten (Übernehmen, Überspringen pro Abschnitt) entfällt ganz (Antwort des Nutzers). Was das Cockpit sicher weiß, geht als fertige Bausteine an die KI. Die Einstellung „Abschnitte“ sagt der KI, welche Abschnitte die README haben soll.
- Infodateien gehen ohne Geheimnisse an die KI. Vertrauliche Dateien wie .env und Dateien, die kein Text sind, bleiben weg. Das Cockpit sagt, welche nicht gesendet wurden.
- Nach „fertig so“ wird README.md gespeichert, die alte kommt vorher in die Sicherheitskopien. Gibt es weitere Sprachen, übersetzt die KI danach die ganze README (Antwort des Nutzers). Jede Übersetzung kommt einzeln zum Lesen und Ändern, Escape überspringt. Erst wenn es mehr als eine Sprachdatei gibt, bekommen alle oben die Zeile mit den Links. Ist beim Bearbeiten nichts geändert, übersetzt die KI nur in Sprachen, für die es noch keine Datei gibt.
- Die Prüfung vor dem Hochladen bleibt, wie sie war.


## 03.10.2026: Exe bauen in Schritten, Ordner je Exe, Lizenz, Update, Branch löschen

Wunsch des Nutzers: „Exe aus dem Code erstellen …“ war durcheinander. Dazu Wünsche zu Release, Lizenz, Update und Branches. Gebaut im Branch exe-bau-ueberarbeiten, Checkliste in checklisten\exe-bau-ueberarbeiten.md. Antworten des Nutzers auf vier Fragen stehen jeweils dabei.

Exe bauen in Schritten (ersetzt die Abschnitte vom 30.09. und 02.10.2026 zu ReadyDialog, „Exe mit KI einrichten …“ und „Exe selbst testen“):
- Schritt 1: Dateien und Ordner neben der Exe. Was der Code braucht, ist angehakt und heißt „unbedingt nötig“. README und Lizenz stehen ohne Kästchen mit „kommt immer mit“ in der Liste.
- Schritt 2, nur mit eingerichteter Text-KI: „Mit KI-Unterstützung die Exe bauen“ (empfohlen, oben) oder „Ohne KI die Exe bauen“.
- Gebaut wird immer im Branch Cockpit-exe-bauen, auch ohne KI (Antwort des Nutzers). Auch die Exe-Einstellungen kommen nur dorthin, als eigener Commit. Grund: Vorher blieb cockpit.toml geändert in main liegen. Das sah nach dem Löschen eines Branches so aus, als wären dessen Änderungen in main gelandet.
- Schritt 3: Einrichtung. Der Branch wird ohne Rückfrage angelegt.
- Schritt 4: Zusammenfassung. „Mit KI schreiben“ klappt erst auf Wunsch Frage und Gespräch auf, dazu „Mit den Hinweisen wiederholen“. Der Wunsch an die KI vorab („Was soll die Exe können?“) entfällt, das Gespräch ersetzt ihn. Die Änderungen der KI kommen mit „Exe erstellen“ ohne eigene Rückfrage in den Branch, vorher in die Sicherheitskopien.
- Schritte 5 und 6 im selben Fenster: Bau, dann Ergebnis. Bei Fehler: „Problem mit KI lösen“ (nur mit KI, führt zurück zu Schritt 3 mit der Fehlermeldung), „Neuer Versuch, Exe zu bauen“, „Zurück“, „Abbrechen“. Bei Erfolg: „Erst testen, später in main überführen und Release veröffentlichen“ (öffnet den Ordner der neuen Exe im Explorer, Vorgabe und Escape), „Jetzt in main überführen und Release veröffentlichen“ (danach öffnet sich „Exe veröffentlichen“), „Jetzt in main überführen, später veröffentlichen“.
- Jeder Schritt hat „Zurück“ und „Abbrechen“. Abbrechen löscht nach Rückfrage den Branch, wenn dieser Durchgang ihn angelegt hat. Die sichere Antwort ist „Zurück“.
- Beim Überführen wird die getestete Exe aus dem Branch zur normalen Exe. Die Ordner der Nutzer neben der Exe kommen von der bisherigen Exe, README und Lizenz aus dem Code. Danach wird der Branch gelöscht.
- Neu bei Exe: „Exe-Bau abschließen …“, solange es den Branch gibt: überführen mit oder ohne Release, Ordner der neuen Exe öffnen, Exe-Bau verwerfen.
- Antworten der KI im Gespräch: zuerst verständliche Sätze, danach Code, wenn er hilft. In der Liste stehen die Sätze einzeln, der Code nach einer Zeile „Code:“ Zeile für Zeile.
- „Exe-Einstellungen …“ fragt nach dem Speichern nicht mehr, ob gleich gebaut werden soll. Gebaut wird über „Exe aus dem Code erstellen …“.

Ordner je Exe (Antwort des Nutzers: nach dem Namen):
- Jede Exe hat im Ordner Exe einen eigenen Ordner, Exe\VokabelApp und Exe\VokabelApp_branch_Cockpit-exe-bauen. Eine Exe in der alten Ablage kommt beim nächsten Bau in die Sicherheitskopien, Daten neben ihr wandern mit.
- README und Lizenz liegen immer neben der Exe und sind immer die aktuellen aus dem Code.

Veröffentlichen (Antwort des Nutzers: fester Name, Ordner mit Version):
- Hochgeladen wird immer der ganze Ordner als Name.zip, darin der Ordner Name-Version. So bleibt der Link auf die neueste Version gleich, und beim Auspacken überschreibt keine Version eine andere. README und Lizenz hängen zusätzlich einzeln am Release. Die README verlinkt immer Name.zip.

README und Lizenz:
- Neu auf der Projektzeile neben „README …“: „Lizenz …“, mit der Lizenz im Eintrag, zum Beispiel „Lizenz …, MIT“ oder „noch keine Lizenz“. Ohne Lizenz: „Lizenz auswählen …“ (Vorlage von GitHub mit Name und Jahr) und „Lizenz aus Ordner hochladen …“. Mit Lizenz: „Lizenz ansehen“ und „Lizenz ändern …“ (Antwort des Nutzers). Die Datei heißt LICENSE, die bisherige kommt in die Sicherheitskopien.
- Vor dem Bauen und Veröffentlichen warnt das Cockpit, wenn README oder Lizenz fehlen: „Jetzt hinzufügen“ (Vorgabe) springt beim Projekt zur Aktion „README …“ bzw. „Lizenz …“, „Ignorieren und weiter“, „Abbrechen“ (Escape).
- Die Prüfung der Einrichtung warnt nicht mehr, wenn der Code README oder Lizenz nur mit Namen öffnet. Sie liegen ja immer neben der Exe.

Update:
- Die Suche läuft bei jedem Start einmal, nicht mehr nur einmal am Tag.
- Hängt am Release eine ZIP-Datei, kommen README und Lizenz daraus mit und ersetzen die neben der Exe. Andere Dateien neben der Exe bleiben, wie sie sind, weil darin eigene Daten liegen können.

Branches:
- „Branch-Ordner entfernen …“ entfällt, weil „Löschen …“ fragt, ob nur hier, nur auf GitHub oder beides.
- Löschen verwirft die Änderungen ohne Commit. Nichts davon kommt nach main. Der aktuelle Branch lässt sich ohne Branch-Ordner jetzt auch löschen: Das Cockpit sichert die Änderungen, wechselt zu main und löscht ihn.


## 04.10.2026: Aufbau Code\main und Exe, Exe-Ordner mit Version, Update nach Versionsnummer

Rückmeldung des Nutzers: Bei „Chatbot für Text“ hatte er den Code von Hand nach Code\main kopiert, das Cockpit zeigte aber weiter Code. Ursache: Der Git-Ordner .git lag noch direkt in Code. Dazu Wünsche zu Update, Versionsordnern und der Anzeige beim Hochladen. Gebaut im Branch projekt-aufbau-und-version, Checkliste in checklisten\aufbau-und-version.md.

Aufbau beim Hinzufügen vom Rechner:
- Richtig ist: Projektordner, darin Code und Exe, in Code der Ordner main mit dem Code. Das steht im Titel des Ordner-Dialogs.
- Liegt der Code in Code\main, .git aber noch in Code, bietet das Cockpit an, .git nach Code\main zu verschieben. Am Code ändert sich nichts.
- Liegt der Code direkt in Code, bietet das Cockpit an, ihn nach Code\main zu verschieben. Mit Git geht das wie „Ordner für Branches einrichten …“ (mit Sicherheitskopie, Ordner nach dem Branch benannt), ohne Git heißt der Ordner main. Nur wenn die Grundeinstellung „Neue Projekte mit einem Ordner pro Branch“ an ist.
- Fehlt der Ordner Exe, legt das Cockpit ihn leer an.
- Dasselbe prüft „Projekt neu einlesen“ und das Hinzufügen eines Projekts, das schon in der Liste ist.
- Ohne Git zählt Code\main als Code-Ordner, wenn in Code sonst nichts liegt. Liegt der Code inzwischen dort, merkt sich das Cockpit den neuen Ort von selbst.
- Ein fremder Ordner ohne Code kommt beim Verschieben ohne Git jetzt auch nach Code\main.

Exe-Ordner mit Version (Antwort des Nutzers: auch im Ordner Exe):
- Nach dem Veröffentlichen heißt der Ordner der Exe zum Beispiel Exe\VokabelApp-v1.2.0, darin liegt version.txt. Ältere veröffentlichte Versionen bleiben liegen. Neu gebaut wird in Exe\VokabelApp, die Daten der Nutzer kommen aus der neuesten Version mit. Läuft die Exe gerade, behält ihr Ordner den Namen.
- Im Release-ZIP heißt der Ordner jetzt VokabelApp-v1.2.0, mit v, und enthält version.txt.

Update:
- Die Suche vergleicht Versionsnummern. Die eigene Version ist die höhere aus version.txt neben der Exe und __version__ im Code. Nur ein Release mit höherer Nummer ist ein Update. Dieselbe Datei ist nie ein Update. Ohne lesbare Nummer gilt der alte Vergleich nach Prüfsumme und Datum.
- Grund: Seit das Release eine ZIP-Datei ist, passte die Prüfsumme nie zur Exe. Das Cockpit bot dann die eigene, gerade veröffentlichte Version als Update an.
- Beim Update kommt version.txt mit, wie README und Lizenz.

Anzeige beim Hochladen:
- Während das Release hochgeladen wird, steht bei „Exe veröffentlichen …“ „wird gerade hochgeladen“ statt „noch nicht veröffentlicht“.


## 04.10.2026: Repository anlegen, wenn es fehlt, Adresse nach dem Löschen entfernen

Rückmeldung des Nutzers: Bei Chatbot-fuer-Text stand in Git noch die Adresse eines Repositorys, das er vorher gelöscht hatte. Das Cockpit hielt das Projekt deshalb für „auf GitHub“ und bot weder das Anlegen noch das Hochladen an. Gebaut im Branch repo-anlegen, Checkliste in checklisten\repo-anlegen.md.

- Das Cockpit prüft im Hintergrund, ob es das eingetragene Repository auf der Plattform gibt: bei „Projekt neu einlesen“, nach dem Hinzufügen und bei „Projekt verwalten …“. Fehlt es, fragt es „Jetzt anlegen und hochladen?“, Vorgabe „Später“.
- Dann steht oben auf der Projektzeile „Repository auf GitHub anlegen und hochladen …“. Bei Code steht „Auf GitHub hochladen …“ statt „Änderungen auf GitHub hochladen …“. Dieselbe Aktion steht auch bei Projekten, die noch gar nicht auf GitHub sind.
- Das erste Hochladen legt das Repository auch dann an, wenn schon eine Adresse eingetragen ist, das Repository aber fehlt. Die Adresse wird danach auf das neue Repository gesetzt. Vorgeschlagen wird der Name aus der Adresse.
- „Projekt neu einlesen“ fragt bei einem Projekt ohne Repository auch, ob es hochgeladen werden soll (Wunsch des Nutzers).
- Sobald das Repository angelegt ist, verschwindet der Eintrag zum Anlegen wieder, auch wenn danach nur das Hochladen scheitert (Rückmeldung des Nutzers).
- Nach dem Löschen eines Repositorys entfernt das Cockpit die Verbindung origin immer, auch wenn das Projekt danach aus der Liste entfernt wird. Beim Löschen eines Repositorys, das nur auf GitHub steht, trennt es alle Projekte mit dieser Adresse, auch aus der Liste entfernte.


## 04.10.2026: Fehlerfenster beim Exe-Bau, „Mit KI chatten“

Rückmeldung des Nutzers: Nach „Exe erstellen“ kam ein Fehler beim Übernehmen der Änderungen der KI. „Details“ zeigte nur noch einmal die Meldung, und es gab nur „OK“.

- „Mit KI schreiben“ heißt jetzt „Mit KI chatten“.
- Fehler unterwegs im Ablauf (Einrichtung, Übernehmen der Änderungen der KI) zeigen ein eigenes Fenster „Schritt …: Fehler“: Meldung, darunter das Feld „Ausgabe“ zum Lesen. Der Text liegt schon in der Zwischenablage.
- Knöpfe: „Problem mit KI lösen“ gibt den Fehler an die KI und wiederholt die Einrichtung. „Mit KI chatten“ klappt das Gespräch auf, seine Hinweise gehen dann mit. Dazu „Zurück“ und als letztes „Abbrechen“. Ohne KI nur „Zurück“ und „Abbrechen“.
- Beim Wiederholen steht im Fortschritt und in der Ansage „Fehler wurde an die KI übergeben“ oder „Fehler und Chat wurden an die KI übergeben“ (Wunsch des Nutzers).
- Ursache für die leeren Details: Es wurde die Meldung statt der Details weitergegeben. Jetzt stehen die Details der KI-Prüfung im Feld.


## 04.10.2026: Exe aus dem Branch übernehmen und veröffentlichen, auch wenn der Branch schon weg ist

Rückmeldung des Nutzers: Bei Chatbot für Text war der Branch Cockpit-exe-bauen schon in main und gelöscht. Die getestete Exe lag noch in Exe\Chatbot-für-Text_branch_Cockpit-exe-bauen. „Exe-Bau abschließen …“ fehlte, und „Exe veröffentlichen …“ fand keine Exe.

- „Exe-Bau abschließen …“ steht da, solange es den Branch oder noch seine Exe gibt. Ist der Branch schon weg: „Exe als normale Exe übernehmen und Release veröffentlichen“, „Exe als normale Exe übernehmen, später veröffentlichen“, „Ordner der neuen Exe im Explorer öffnen“, „Exe aus dem Branch verwerfen …“.
- Release und Repository sind getrennt (Wunsch des Nutzers): „Exe veröffentlichen …“ geht auch mit der Exe aus dem Branch, ohne dass alles in main ist. Gibt es beide Exen, fragt das Cockpit, welche. Die neuere steht oben. Nach dem Veröffentlichen heißt ihr Ordner mit Version, zum Beispiel Exe\Chatbot-für-Text-v1.0.0, und sie gilt als normale Exe.


## 06.10.2026: Neue Projektliste mit Repository, Branches und Releases

Wunsch des Nutzers, gebaut im Branch projektliste-neu. Entwurf mit den Antworten des Nutzers in ENTWURF-PROJEKTLISTE.md, Checkliste in checklisten\projektliste-neu.md.

- Unter einem aufgeklappten Projekt stehen von oben: Repository, Main-Branch, die Branches nach Auswahl, Releases, Exe-main und je Branch-Release eine Zeile wie Exe-neue-funktion.
- Projektzeile: „Projekt verwalten …“ ist ein neues Fenster mit dem derzeitigen Namen, „Projekt umbenennen …“, „Aus der Liste entfernen …“ und „Projekt löschen …“. README, Lizenz, Links und Releases stehen nicht mehr hier.
- Umbenennen ändert alles (Antwort des Nutzers): Name in der Liste, Projektordner und Repository auf GitHub. Danach repariert das Cockpit die Verweise der Branch-Ordner (git worktree repair) und die virtuellen Umgebungen. Lässt sich der Ordner nicht umbenennen, ändert es gar nichts.
- Löschen verschiebt den lokalen Ordner in die Sicherheitskopien und löscht das Repository auf GitHub, mit denselben Rückfragen wie „Repository verwalten“.
- Zeile Repository: Enter öffnet die Auswahl „Nur main“, „main & die Sie lokal haben“ (Vorgabe), „main & die nur auf GitHub sind“, „main & alle“. Die Auswahl gilt pro Projekt und bleibt gespeichert. Hier stehen jetzt Repository verwalten (das bisherige „Projekt verwalten“), Branches verwalten, Links, README, Lizenz, Repository-Identität, Auf GitHub öffnen, GitHub Actions und Repository-Ordner öffnen. Die Zeile „Branches verwalten“ in der Liste entfällt.
- Branches verwalten: Auch main hat „Infos“ und „Umbenennen …“. „Löschen …“ ist bei main nicht verfügbar und nennt den Grund (Antwort des Nutzers). Umbenennen von main ändert den Branch hier und auf GitHub und den Ordner Code\main.
- Branch-Zeilen: „Repository neu einlesen“ oben, „Branch-Ordner öffnen“ ganz unten.
- Releases: Die Exe aus main heißt Exe-main, eine Exe aus einem Branch Exe-<Branch-Ordner>. Auf dem Rechner bleiben die Ordner, wie sie seit Phase 10f sind (Exe\Name und Exe\Name_branch_<Ordner>). Ein Release für einen Branch gibt es nur für lokale Branches. „Release-Ordner lokal anlegen“ legt den leeren Ordner an.
- Ein Branch-Release wird mit dem Tag v<Version>-<Branch> auf dem Stand des Branches veröffentlicht. So kommt es nicht mit den Versionen von main durcheinander. Sein Ordner behält den Namen, nur version.txt kommt hinein. Ist der Branch noch nicht auf GitHub, sagt das Cockpit das vorher.
- „Release entfernen“ fragt: nur lokal, nur auf GitHub oder beides. Vorgabe und Escape: Abbrechen. Lokal kommt der Ordner in die Sicherheitskopien. Auf GitHub wird das Release der zuletzt veröffentlichten Version gelöscht, das Tag bleibt (wie Frage 3 zu Phase 14).
- Jede Zeile hat ein Terminal an ihrem Ort: Projektordner, Ordner Code (Antwort des Nutzers: von dort geht man selbst in die Branches), Branch-Ordner, Ordner Exe und der Ordner des Releases.
- Aktionen können einen Namen haben, der von der Zeile abhängt, etwa „Exe aus neue-funktion erstellen …“ oder „Exe-main-Ordner öffnen“.
- Die Ordner Code und Exe heißen jetzt Repository und Release (Antwort des Nutzers). Neue Projekte bekommen gleich die neuen Namen. Projekte mit den alten Namen funktionieren weiter.
- Beim Start fragt das Cockpit einmal für alle Projekte mit den alten Namen: „Umbenennen“, „Später“ (Vorgabe und Escape, fragt beim nächsten Start wieder) oder „Nicht umbenennen“ (fragt nie mehr). Danach repariert es die Verweise der Branch-Ordner und legt die virtuellen Umgebungen neu an, weil sie feste Pfade enthalten.
- Ohne Sicherheitskopie (Antwort des Nutzers vom 07.10.2026): Nur die Namen ändern sich, nicht der Inhalt. Eine volle Kopie hätte bei großen Exe-Ordnern viel Zeit und Platz gekostet. Dafür gibt es auf der Projektzeile „Ordnernamen zurücksetzen …“. Scheitert ein Ordner, weil er geöffnet ist, benennt das Cockpit den anderen zurück, und es ist nichts geändert.
- Einzeln geht es auf der Projektzeile mit „Ordner in Repository und Release umbenennen …“.
- Das Projekt, aus dem das Cockpit gerade läuft, benennt es nicht um. Seine Ordner sind in Benutzung.
- Meldungen nennen den echten Ordnernamen, zum Beispiel „Repository\suche“ oder bei einem alten Projekt „Code\suche“. Feste Texte nennen die neuen Namen.
- Nachtrag (Fehler beim Testen gefunden): „Neu einlesen“ bei einem Projekt mit dem Code direkt in Code bietet „Ordner für Branches einrichten“ an. Wer das abbrach, bekam gar kein Neu einlesen. Jetzt liest das Cockpit nach dem Abbrechen trotzdem neu ein.


## 07.10.2026: Korrekturen beim Hochladen

Rückmeldung des Nutzers, Punkt 2 aus KONZEPT-NAECHSTE-SCHRITTE.md. Gebaut im Branch hochladen-korrekturen, Checkliste in checklisten\hochladen-korrekturen.md. Der Nutzer sagte „baue los“, ohne die offenen Fragen zu beantworten. Wo eine Antwort fehlte, gilt der Vorschlag aus dem Konzept. Das steht jeweils dabei.

- Versionsfrage (Vorschlag aus dem Konzept): Sie kommt nur noch, wenn auf main hochgeladen wird. Auf einem anderen Branch sagt die Zusammenfassung: „Die Version legen Sie fest, wenn die Änderungen in main hochgeladen werden.“ Nach „In main übernehmen“ ist main noch nicht hochgeladen. Beim Hochladen von main kommt die Frage dann. Gibt es den Haupt-Branch weder hier noch auf GitHub, fragt das Cockpit wie bisher. Gründe, warum die Frage früher mal kam und mal nicht: Das Feature Versionen war nicht bei jedem Projekt an, ohne neuen Commit wurde nicht gefragt, und auf Neben-Branches wurde auch gefragt.
- Textfeld ohne Ausweg: Das war der Vorschlag der KI für die README nach einer neuen Version. Er kam in einem mehrzeiligen Eingabefeld von Qt, in dem Tab ein Tabzeichen schreibt. Jetzt kommt er in ein eigenes Fenster: oben die Erklärung, darunter der Vorschlag als Ausgabefeld zum Lesen und Kopieren, dann „Übernehmen“, „Bearbeiten“ und „Überspringen“. Tab führt zu den Knöpfen, Umschalt+Tab zurück. „Bearbeiten“ macht den Text schreibbar. Vorgabe und Escape: „Überspringen“, die sichere Antwort. Vorher war OK die Vorgabe.
- Schritt 3 und 4 vertauscht: Die genaue Ursache ließ sich nicht nachstellen. Wahrscheinlich: Ansagen warten 500 ms, bis sich der Fokus beruhigt. Öffnet in der Zeit ein Fenster mit einer Frage, liest NVDA zuerst das Fenster. Dazu wurden Schritte ohne Arbeit mitgezählt, zum Beispiel „Version als Tag setzen“ ohne neue Version. Jetzt: Jede Rückfrage nennt im Titel ihren Schritt, zum Beispiel „Version, Schritt 2 von 5: Version festlegen“. Schritte ohne Arbeit werden weder angesagt noch gezählt. Wählt man eine neue Version, kommen ihre Schritte zur Zahl dazu.
- Töne (Vorschlag aus dem Konzept): Beim Hochladen, Holen, Herunterladen eines Projekts, Veröffentlichen eines Releases und Holen einer Exe aus einem Release kommt ein Windows-Ton beim Start, alle 10 Sekunden ein kurzer leiser Ton und am Ende der Ton für fertig oder Fehler. Beim Abbrechen kein Ton. Abschalten in den Grundeinstellungen: „Töne beim Hoch- und Herunterladen“. Die Meldung am Ende gab es schon, sie bleibt.
- Nebenbei: Eine Zeile in project_actions.py war beim letzten Zusammenführen zu einer sehr langen Zeile geworden. Sie ist wieder umbrochen, am Verhalten ändert sich nichts.


## 07.10.2026: KI schneller und auf den Rechner eingestellt

Wunsch des Nutzers, Punkt 8 aus KONZEPT-NAECHSTE-SCHRITTE.md: Vorschläge für Textfelder dauerten 30 Sekunden und mehr. Gebaut im Branch ki-tempo, Checkliste in checklisten\ki-tempo.md.

- Ursache: Das Nachdenken war schon aus. Die Zeit ging beim Lesen des Textes verloren, den die KI bekommt (bis zur Grenze der Grundeinstellung, 8000 Zeichen), und beim ersten Laden des Modells.
- Zwei Arten von Aufgaben: „Vorschläge für Textfelder“ (KI-Assistent: Commit, Pull Request, Kurzbeschreibung, Versionshinweise, und die Erklärungen im Terminal) und „Antworten und Bearbeitung für Code oder komplexe Fragen“ (Exe einrichten, KI-Hilfe, README, GitHub Actions). Jede Art hat eine Zielzeit: Textfelder etwa 6 Sekunden, Code etwa 45 Sekunden.
- Starttest: Nach dem Start misst das Cockpit im Hintergrund mit drei kleinen Anfragen, wie schnell die Standard-Text-KI liest und schreibt. Die erste lädt das Modell und zählt nicht. Daraus folgt, wie viele Zeichen jede Art bekommt, damit die KI in der Zielzeit antwortet. Das Cockpit ist sofort benutzbar, bis dahin gelten Standardwerte (Textfelder 3000 Zeichen, Code die Grenze der Grundeinstellung). Der Test läuft bei jedem Start, weil die Auslastung des Rechners schwankt.
- Gemessen wird nur eine KI auf dem Rechner (Ollama) oder im eigenen Netz. Eine KI außerhalb bekommt nichts ohne Zustimmung, dort gelten die Standardwerte.
- Ollama behält das Modell 30 Minuten geladen (keep_alive). So spart die nächste Frage das Laden.
- Menü KI, ganz oben: „KI ist eingestellt auf diesen Rechner …“ (vorher „KI wird auf den Rechner eingestellt …“). Das Fenster: oben die Erklärung als Ausgabefeld mit den gemessenen Werten und den Budgets. Tab führt zu „Ergebnisse nicht genau genug bei:“ mit den zwei Arten (Pfeiltasten), Tab zur Stufe von „+3 sehr genau, langsamer“ bis „-3 ungenau, am schnellsten“, Vorgabe 0 für beide. Die Erklärung rechnet beim Wählen mit. Speichern übernimmt, Abbrechen und Escape nicht.
- Eine Stufe bedeutet 1,6-mal so viel Zeit und damit mehr Text an die KI, und eine um ein Viertel längere Antwort. Ab +2 darf die KI bei Code und komplexen Fragen nachdenken. Die Stufe 0 bei Textfeldern ist knapper als die 0 bei Code, wie gewünscht.
- Weniger senden: Bei knappem Budget bekommt jede geänderte Datei einen gleichen Anteil an den geänderten Zeilen, statt dass hinten alles abgeschnitten wird. Kopfzeilen von Git ohne Inhalt fallen weg.
- Nebenbei: Der Ton beim Hoch- und Herunterladen kommt jetzt alle 3 Sekunden (Antwort des Nutzers).


## 07.10.2026: Filter über den Projekten und Zeichen für Offenes

Wunsch des Nutzers, Punkte 1 und 6 aus KONZEPT-NAECHSTE-SCHRITTE.md, Antwort auf Frage 4 („ja ok“). Gebaut im Branch listenfilter, Checkliste in checklisten\listenfilter.md.

- Über den Projekten, gleich nach „Projekt von GitHub herunterladen“, steht die Zeile „Anzeigen: Alle Projekte“. Sie steht dort und nicht ganz oben, damit „Neue Projektsammlung“ beim Start weiter der erste Eintrag ist und die Zeile direkt über dem steht, was sie filtert. Enter oder Leertaste öffnet die Auswahl wie bei „Branches anzeigen“. Escape ändert nichts. Die Auswahl bleibt nach einem Neustart.
- Auswahl: „Alle Projekte“, „Mit offenen Sachen“, „Auf GitHub“, „Mit Release“, „Nur auf dem Rechner“ (Antwort des Nutzers: „Auf GitHub“ und „Mit Release“ getrennt).
- Offen heißt: Änderungen ohne Commit, Commits nicht hochgeladen, auf GitHub neuer, Zusammenführen nicht abgeschlossen, offene Pull Requests oder angefragte Reviews, auch in einem Branch-Ordner. Pull Requests und Reviews kommen aus dem Zwischenspeicher, der beim Abfragen der Repositories gefüllt wird. Als Review gilt ein offener Pull Request mit angefragtem Prüfer.
- „Auf GitHub“ zeigt auch die Repositories, die nur auf GitHub liegen. „Mit Release“ heißt: In einem Release-Ordner liegt eine Exe.
- Mit Filter nennt die Zeile die Zahl, zum Beispiel „Anzeigen: Mit offenen Sachen, 3 Projekte“. Sammlungen zeigen nur ihre passenden Projekte und heißen dann zum Beispiel „Sammlung Web, 1 von 2 Projekten“. Sammlungen ohne passendes Projekt fallen weg.
- Ändert sich der Stand eines Projekts, kommt es dazu oder fällt weg. Die Liste wird dann gesammelt neu gefüllt, die Markierung bleibt, wo sie war.
- Die Zeile eines Projekts nennt jetzt auch „2 offene Pull Requests“ und „1 Review angefragt“.
- Zeichen für das Auge: Vor jeder Projektzeile steht ein kleines Bild mit Zeichen: ● Änderungen ohne Commit, ↑ nicht hochgeladen, ↓ auf GitHub neuer, PR offene Pull Requests, R Review angefragt. Die Farbe ist die Textfarbe des Windows-Themas. Der Screenreader liest das Bild nicht, dieselbe Information steht als Text in der Zeile (keine Information nur über Zeichen oder Farbe).
- Aussehen: Qt nutzt unter Windows 11 schon den Stil von Windows 11 mit hellem und dunklem Modus. Ein eigener Stil oder eigene Farben kommen nicht dazu (Regel: keine festen Farben).


## 07.10.2026: Versionsverlauf, Zu einer Version zurück, Hochladeverlauf

Wunsch des Nutzers, Punkt 3 aus KONZEPT-NAECHSTE-SCHRITTE.md. Gebaut im Branch verlauf, Checkliste in checklisten\verlauf.md.

- „Verlauf …“ zeigt oben die Versionen, zuerst „In Arbeit, noch keine Version, 2 Commits“ mit dem, was seit der letzten Version dazukam, dann zum Beispiel „Version 1.0.0 vom 21.09.2026, 2 Commits“. Eine Version umfasst ihren Commit mit dem Tag und alles davor bis zur vorigen Version. Ohne jede Version stehen oben die Tage.
- Tab führt in „Commits“ der gewählten Version. Jeder Commit nennt Datum, Person und Text, zum Beispiel „05.10.2026, Pascal: Suche verbessert“. Enter zeigt die Details mit den Dateien. Dort gibt es wie bisher „Datei wiederherstellen …“, „Version rückgängig machen …“ (ein neuer Commit, der einen Commit aufhebt) und beim neuesten, noch nicht hochgeladenen Commit „Commit zurücknehmen …“.
- Neu: „Zu dieser Version zurück …“. Alle Dateien kommen auf den Stand der gewählten Version, als ein neuer Commit „Zurück zu Version 1.0.0“. Was danach kam, bleibt im Verlauf. Auf GitHub wird nichts umgeschrieben, also nie ein force push. Vorher kommen die betroffenen Dateien in die Sicherheitskopien. Bei Änderungen ohne Commit lehnt das Cockpit ab, damit nichts verloren geht. Das geht auch bei Zusammenführungen dazwischen, anders als mehrere einzelne Rückgängig-Commits.
- Neu an jeder Branch-Zeile und am Main-Branch: „Hochladeverlauf …“. Oben jedes Hochladen, zum Beispiel „06.10.2026 14:12, Pascal, 3 Commits nach main“, Tab führt in die Commits dieses Hochladens, Enter zeigt die Details. Git selbst weiß nicht, wer wann hochgeladen hat. Deshalb merkt sich das Cockpit ab jetzt jedes eigene Hochladen in seiner Datenbank (Branch, Zeit, Name aus den Grundeinstellungen, Stand vorher und nachher, höchstens 200 je Projekt). Was davor auf GitHub kam, steht darunter nach Tagen mit „vor dem Aufzeichnen“, höchstens 300 Commits.
- Noch nicht gebaut: eine geführte Hilfe bei Konflikten. „Konflikte lösen …“ gibt es schon. Ob sie für Neulinge reicht, zeigen die Kurzanleitungen.


## 07.10.2026: Schnellnavigation, Befehlssuche, Tastenhinweise

Wunsch des Nutzers, Punkte 4 und 5 aus KONZEPT-NAECHSTE-SCHRITTE.md, Antworten auf die Fragen 5, 6 und 7. Gebaut im Branch schnellnavigation, Checkliste in checklisten\schnellnavigation.md.

- Schnellnavigation: Ist ein Projekt ausgeklappt, steht im Kontextmenü (Menütaste oder Umschalt+F10) auf dem Projekt und allen Zeilen darunter zuerst das Untermenü „Schnellnavigation Tagebuch“. Darin: „Hilfe, mit der KI chatten …“ (die KI-Hilfe, bis die Kurzanleitungen kommen), „Tastenbefehle …“, „Projekt verwalten …“, „Repository verwalten …“, „Branches verwalten …“ und „Releases verwalten …“. Releases haben kein eigenes Fenster, deshalb springt der Eintrag auf die Zeile Releases und in ihre Aktionen. Geht etwas bei dem Projekt nicht, etwa „Repository verwalten“ ohne GitHub, sagt das Cockpit warum und lässt die Markierung auf der Zeile.
- Befehlssuche mit Strg+K (Antwort auf Frage 5: ja), auch im Menü Hilfe: Suchfeld, darunter die Treffer aus den Aktionen der markierten Zeile und allen Menüs, zum Beispiel „Menü KI: KI-Verwaltung …“. Mehrere Wörter müssen alle vorkommen. Pfeil runter und hoch wählen auch aus dem Suchfeld heraus, Enter führt aus, Escape schließt.
- Tastenhinweise (Antwort auf Frage 7: „was du besser findest“): Strg+F1 sagt für das Element mit dem Fokus kurz an, welche Tasten dort etwas tun, zum Beispiel „Tasten hier: Pfeil rechts oder Enter klappt auf, …“. Strg+F1 wirkt zurzeit nur im Hauptfenster, noch nicht in anderen Fenstern. Sehende sehen denselben Hinweis als Tooltip der Projektliste und der Aktionsliste. Die Regel in CLAUDE.md bleibt: keine Beschreibung am Bedienelement, und Ansagen erklären keine Tasten von selbst, nur auf Wunsch mit Strg+F1.
- „Speichern und hochladen“ (Antwort auf Frage 6: ja): Das gibt es schon. „Änderungen auf GitHub hochladen …“ fragt nach der Commit-Nachricht (mit Vorschlag der KI), macht den Commit, lädt hoch und bietet danach einen Pull Request an. Deshalb kein zweiter Eintrag, der dasselbe tut. Die Kurzanleitungen sollen das klar sagen.
- Die Liste der Tastenkürzel (F1) nennt die neuen Tasten und spricht von „Zeilen unter dem Projekt“ statt von Code und Exe.


## 07.10.2026: Hilfe mit Kurzanleitungen

Wunsch des Nutzers, Punkt 7 aus KONZEPT-NAECHSTE-SCHRITTE.md. Gebaut im Branch hilfe-anleitungen, Checkliste in checklisten\hilfe-anleitungen.md.

- F1 öffnet jetzt das Fenster „Hilfe“ (auch Menü Hilfe, „Hilfe und Kurzanleitungen …“). Die Liste der Tastenkürzel liegt auf Strg+Umschalt+F1 und steht als Anleitung „Alle Tastenkürzel“ auch in der Hilfe. So gilt weiter: Tastenkürzel stehen im Menü und in der Hilfe (F1).
- Das Fenster ist nicht modal. Es bleibt offen, mit Alt+Tab arbeiten Sie im Cockpit weiter. F1 holt es wieder nach vorne. Escape oder „Schließen“ schließt es.
- Von oben: „Suchen“, „KI fragen“, „Anleitungen“, „Schritte“ (Ausgabefeld). Ohne Suche stehen die Anleitungen für die markierte Zeile oben, zum Beispiel bei Releases „Exe erstellen“. Mit Suche die besten oben: Ein passender Titel zählt am meisten, dann Stichwörter, dann der Text. Wortanfänge zählen auch. Enter im Suchfeld springt in die Liste, Enter in der Liste in die Schritte.
- „KI fragen“ nimmt den Text aus dem Suchfeld. Passt eine Anleitung gut, zeigt das Cockpit sie und sagt „Passende Anleitung: …“. Sonst fragt es die KI über das Feature KI-Hilfe. Sie bekommt die Bedienung des Cockpits, alle Anleitungen und die Bitte, Schritte mit Tasten zu schreiben. Die Antwort steht in „Schritte“.
- 32 Kurzanleitungen in anleitungen\kurzanleitungen.md, jede mit Bereich, Aktionen, Stichwörtern und „Schritt 1: …“ mit Tasten. Ein Test prüft, dass jede genannte Aktion im Programm existiert und die Schritte lückenlos nummeriert sind.
- In der Schnellnavigation heißt der erste Eintrag jetzt „Hilfe, Kurzanleitungen und KI fragen …“ und öffnet dieses Fenster.

Was beim Schreiben der Anleitungen auffiel (Vorschläge, noch nicht gebaut):
- „Neuer Branch …“ gibt es nur im Fenster „Branches verwalten“. Ein Eintrag direkt bei der Zeile Repository spart einen Schritt.
- „In main übernehmen …“ steht nur in „Branches verwalten“. Auf der Zeile eines Branches wäre es dort, wo man arbeitet.
- Reviews, die auf Sie warten, findet man nur über „Pull Requests …“ beim Main-Branch. Ein Eintrag „Reviews für mich …“ wäre direkter.
- Der Starttest der KI misst nur beim Start. Nach „KI verknüpfen“ wäre ein Knopf „Jetzt messen“ im Fenster „KI einstellen“ hilfreich.
- Strg+F1 und Strg+K wirken nur im Hauptfenster, nicht in anderen Fenstern.


## 08.10.2026: Überprüfung und Gesamttest nach den Branches vom 07.10.2026

Wunsch des Nutzers: Überprüfung und ganzer Testlauf vor n8n und E-Mail. Gebaut im Branch nacharbeit, Checkliste in checklisten\nacharbeit.md.

- Gefunden im Gesamttest: Der Testlauf brach bei Test 857 von 1026 ohne Meldung ab (Code 127). Ursache: Nach einem Test lief im Hintergrund noch eine Standabfrage, und ihre letzten Nachrichten kamen erst an, als das Fenster schon abgebaut war. Seit dem 06.10.2026 liest die Standabfrage auch die Branches auf GitHub und dauert deshalb etwas länger. Das Cockpit merkt sich jetzt jede laufende Hintergrundaufgabe schon beim Start (Task.wait_all). Die Tests warten darauf, bevor sie die Datenbank schließen. Im Programm selbst wartet das Hauptfenster beim Schließen wie bisher.
- Gefunden in der Überprüfung: Der Filter „Mit Release“ durchsuchte bei jeder Standabfrage alle Release-Ordner mit allen Unterordnern nach Exe-Dateien. Bei Programmordnern mit tausenden Dateien bremst das. Jetzt sucht er höchstens zwei Ebenen tief, und eine Release-Zeile sucht ihre Exe oben und eine Ebene tiefer.
- Im README-Vorschlag beim Hochladen löste Enter im nur lesbaren Text die Vorgabe „Überspringen“ aus. Wer beim Lesen versehentlich Enter drückte, verlor den Vorschlag. Jetzt tut Enter im Text nichts, wie in den anderen Ausgabefeldern.
- Lief im Hilfefenster gerade eine Frage an die KI, während das Cockpit beendet wurde, konnte Qt beim Beenden abstürzen. Das Hilfefenster wird jetzt beim Beenden mit geschlossen und wartet auf die Antwort oder bricht sie ab.
- Hinweis ohne Änderung: Der Starttest der KI startet bei jedem Start Ollama und lädt das Modell, auch wenn Sie die KI in dieser Sitzung nicht nutzen. Ollama behält es 30 Minuten im Speicher. Wenn das stört, kann der Test seltener laufen, zum Beispiel einmal am Tag.


## 11.10.2026: Schritt 1 beim Exe-Bau schien hängen zu bleiben

Rückmeldung des Nutzers: Bei VokabelApp und Tagebuch kam der Exe-Bau nicht über Schritt 1 hinaus. Vor dem Umbau ging es.

- Ursache: Der Name der Bau-Umgebung unter %LOCALAPPDATA%\CodeCockpit\venvs hing am Pfad des Code-Ordners. Nach dem Umbenennen von Code in Repository\main bekam jedes Projekt eine neue, leere Umgebung. Schritt 1 lud dann alles neu herunter. PySide6 6.12 bringt inzwischen Pakete von zusammen über 250 MB mit. Weil pip mit --quiet lief, stand minutenlang nichts in der Ausgabe, und der Bau wurde abgebrochen.
- Der Name der Umgebung hängt jetzt an der Nummer des Projekts, zum Beispiel VokabelApp-p3. Sie übersteht das Umbenennen von Ordnern und Projekt. Eine Umgebung mit dem alten Namen für den jetzigen Pfad wird einmal umbenannt und weiter benutzt.
- pip läuft ohne --quiet. Vorher steht der Hinweis, dass es beim ersten Mal über 10 Minuten dauern kann. Zeilen über schon vorhandene Pakete werden nicht angezeigt, damit die Ausgabe bei jedem Bau kurz bleibt.

## 11.10.2026: Blockierte Exe behalten und Exe-Bau auf den Branch-Zeilen abschließen

Rückmeldung des Nutzers: Windows-Sicherheit blockierte die neue Exe. Im Ergebnis ließ sie sich nicht behalten. Außerdem war unklar, wie der Branch Cockpit-exe-bauen unter Repository und Releases zu main kommt, dort stand nur Hochladen.

- Im Schritt Ergebnis gilt eine Exe, die gebaut ist, aber den Test nicht besteht oder von Windows blockiert wird, nicht mehr als Fehler ohne Ausweg. Die Knöpfe sind dann: Trotzdem behalten (Vorgabe), Problem mit KI lösen, Mit KI chatten (beide nur mit KI), Neuer Versuch, Zurück, Abbrechen. Nach Trotzdem behalten kommen dieselben Knöpfe wie bei Erfolg. Wer nicht behält, dessen Exe wird gelöscht.
- Ein Meldungsfenster der Exe mit Wörtern wie blockiert oder App-Steuerung zählt jetzt als Sperre durch Windows, nicht als Absturz.
- Außerhalb des Assistenten bleibt es, wie es war: Ein nicht bestandener Test ist ein Fehler, bei einer Sperre fragt das Cockpit wie bisher.
- Auf der Zeile Cockpit-exe-bauen unter Repository und auf Exe-Cockpit-exe-bauen unter Releases steht jetzt oben In main überführen oder verwerfen, Exe-Bau abschließen. Es öffnet dieselbe Auswahl wie Exe-Bau abschließen auf Exe-main.
- Neue Kurzanleitung: Exe-Bau abschließen und in main überführen.

## 11.10.2026: Neue Cockpit-Exe blieb in Release\_neu liegen

Rückmeldung des Nutzers: Nach Neu starten lag ein Ordner _neu im Ordner Release, und es startete wieder die alte Version.

- Ursache: Das Cockpit lief aus Release\CodeCockpit-v1.1.23. Das Austausch-Skript wollte auch diesen Ordner einer veröffentlichten Version in die Sicherheitskopien schieben. Das ging nicht, nach 30 Versuchen gab das Skript auf. Da war der Ordner CodeCockpit schon verschoben, die neue Exe lag noch in _neu, und nichts startete.
- Versionsordner bleiben jetzt auch beim Neustart liegen, wie schon beim normalen Übernehmen (04.10.2026).
- Gibt das Skript auf, kommt schon Verschobenes zurück. Es bleibt nichts halb getauscht.
- Überführen eines Branches ohne eigene Commits braucht keinen sauberen Stand in main mehr. Vorher scheiterte es an Änderungen ohne Commit, obwohl es nichts zu überführen gab.

## 14.10.2026: Bericht zum Bau und fehlende Bibliotheken

Rückmeldung des Nutzers: Beim Zug-um-Zug-Streckenfinder lief PyInstaller ohne Fehler durch, aber im Ordner Release kam keine Exe an. Warum, war nicht zu erkennen. Auch Mit KI chatten half nicht.

Ursachen: Es gab keine requirements.txt. Die Bau-Umgebung bekam nur PyInstaller, PySide6 und networkx fehlten in der Exe. Die Exe stürzte beim Start mit No module named 'PySide6' ab. Danach suchte sie strecken.csv über sys._MEIPASS im Ordner _internal statt neben der Exe.

- Im Schritt Einrichtung ergänzt das Cockpit im Branch Cockpit-exe-bauen fehlende Einträge in requirements.txt selbst und legt die Datei notfalls an. Main bleibt unverändert. Die Zusammenfassung nennt die ergänzten Namen.
- Nach PyInstaller liest das Cockpit die Warnliste von PyInstaller. Fehlen Bibliotheken, die der Code oben in einer Datei importiert, steht das sofort in der Ausgabe.
- Geht etwas schief, steht in der Ausgabe ein Bericht zum Bau: jeder Schritt mit Ergebnis, die Meldung der Exe, ob der Ordner Release da ist und ob die Exe dort abgelegt wurde, und warum nicht. Danach Zeilen mit Was tun, zum Beispiel für fehlende Bibliotheken, Dateien im Ordner _internal, zu lange Pfade, gesperrte Dateien und Sperren durch Windows. Der Bericht geht auch an die KI.
- Die Einrichtungsprüfung meldet ein Problem, wenn der Code eine Datei, die neben die Exe kommt, über sys._MEIPASS sucht.
- Die Anweisung an die KI kennt jetzt _MEIPASS, das Laden von Dateien beim Import und fehlende Bibliotheken.

## 14.10.2026: Projekte einbinden, Töne, Fokus im KI-Chat

Wünsche des Nutzers:

- Projekt vom Rechner hinzufügen: Hat der gewählte Ordner Unterordner mit anderen Namen als Code und Exe, gibt es die neue Wahl Hier Repository und Release anlegen. Das Cockpit legt Repository\main und Release leer an, was schon im Ordner liegt, bleibt unverändert. Danach der Hinweis, den Code selbst nach Repository\main zu kopieren und das Projekt neu einzulesen.
- Hat der Ordner noch Code und Exe, fragt das Cockpit gleich beim Hinzufügen, ob es sie in Repository und Release umbenennt. So lassen merkt sich das, beim Start wird dann nicht mehr gefragt. Danach prüft es den Aufbau wie bisher (Code nach Repository\main).
- Liegt eine Exe direkt im Ordner Release, bietet das Cockpit beim Prüfen des Aufbaus an, sie mit allem, was dazugehört, in ihren eigenen Ordner zu verschieben. Dann steht sie als Exe-main unter Releases. Versionen, Branch-Exen und _neu bleiben.
- Töne: Solange ein Ablauf den Nutzer etwas fragt (Branch, Art der Änderung, README-Vorschlag), schweigt der Warteton. Der Warteton ist jetzt ein weicher, leiser Klang statt des Pieptons. Das Cockpit erzeugt ihn selbst als WAV-Datei, ohne neue Bibliothek und ohne fremde Lizenz.
- Neu: ein leiser Warteton aus zwei weichen Tönen, solange die KI schreibt. Erst nach 1,5 Sekunden, kurze Antworten bleiben still. Nicht während einer Frage an den Nutzer und nicht zusätzlich zum Ton beim Hochladen. Abschalten in den Grundeinstellungen: Töne, während die KI schreibt. Der Starttest der KI bleibt still.
- Mit KI chatten: Ist die Antwort da, springt der Fokus in das Gespräch. Abweichung von der Regel, dass Hintergrundarbeit den Fokus nie verschiebt, auf ausdrücklichen Wunsch. Er springt nur, wenn der Fokus noch im Chat steht.

## 14.10.2026: Exe-Bau mit KI bekommt den ganzen Code

- Ändert den Eintrag "Die KI bekommt nie den ganzen Code" für den Exe-Bau. Grund: Beim Streckenfinder kam die Fehlermeldung aus engine.py. Die KI sah nur gui.py und fand den Fehler nicht. Der Nutzer wünschte mehr Kontext.
- Die KI bekommt ganze Python-Dateien, solange sie in die halbe Zeichengrenze passen: zuerst die Startdatei, dann die Dateien aus der Fehlermeldung, dann der Rest. Was nicht passt, kommt als Auszug um die Stellen aus der Fehlermeldung.
- Die Stelle wird auch ohne Traceback gefunden: Steht ein fester Text aus dem Code, etwa "CSV-Datei nicht gefunden", in der Meldung, geht diese Stelle mit.
- Vertrauliche Dateien gehen nie mit. Zeilen mit Geheimnissen werden entfernt.
- Auch der Chat beim Exe-Bau bekommt den Code und das Ende der Ausgabe statt des Anfangs.
- Nach "Problem mit KI lösen" nennt die Zusammenfassung zuerst "Problem beim letzten Versuch" und dann "So löst die KI es". Die KI liefert dazu die Zeile PROBLEM.
- Dateien und Ordner, die neben die Exe kommen, liegen jetzt schon beim Start-Test neben der gebauten Exe (stage_beside). Grund: Der Streckenfinder sucht strecken.csv richtig neben der Exe, fand sie im Test aber nicht, weil sie erst nach dem Test dorthin kam. Nach dem Test werden die Kopien wieder entfernt. So bleiben die Daten der Nutzer aus der bisherigen Exe erhalten, die place_beside danach dorthin legt.

## 14.10.2026: requirements.txt beim Exe-Bau berichtigen

- Im Schritt Einrichtung berichtigt das Cockpit im Branch Einträge, die sich nicht installieren lassen (repair_requirements). Grund: Beim Waagenzähler standen pygame und win32com in requirements.txt. pygame gibt es für Python 3.14 nicht als fertiges Paket, pip scheiterte beim Übersetzen. win32com ist nur der Name zum Importieren, das Paket heißt pywin32.
- Der Name zum Importieren wird durch den Paketnamen ersetzt (PACKAGE_NAMES, jetzt mit allen win32-Modulen). Für Pakete ohne fertige Version gibt es eine feste Liste mit gleichwertigem Ersatz und derselben Import-Zeile: pygame wird ab Python 3.14 zu pygame-ce. Die Zusammenfassung nennt jede Ersetzung mit Grund.
- Der Bericht zum Bau erkennt ein gescheitertes Übersetzen ("Failed to build") und rät nicht mehr, ein Modul aus der Ausgabe von pip wie distutils einzutragen.
- Ordner hinter einem Ordner der Anwendung, etwa BASE_DIR / "sound" oder Path(sys.executable).parent / "sound", gelten jetzt als nötig neben der Exe.

## 20.10.2026: Nach einem Update schließt sich CodeCockpit nur

- Nach dem Herunterladen eines Updates fragt das Cockpit jetzt: Zum Übernehmen schließen Sie CodeCockpit und starten es danach selbst wieder. Jetzt schließen? Die Knöpfe heißen CodeCockpit schließen und Später. Beim Beenden wird die neue Version übernommen, sie startet aber nicht von selbst. Grund: Nach Neu starten kam beim Nutzer immer eine Fehlermeldung. Er wünschte, das Programm selbst zu starten.
- Vermutliche Ursache: Das Austausch-Skript erbte die Variablen der laufenden Exe von PyInstaller (_PYI_...). Die neu gestartete Exe hielt sich dann für einen Teil der alten. launch_restart startet das Skript jetzt mit einer bereinigten Umgebung und PYINSTALLER_RESET_ENVIRONMENT=1. Das hilft auch beim Neustart nach dem Bau der Cockpit-Exe.

## 20.10.2026: Warteton beim Exe-Bau und Pling am Ende

- Das Fenster für den Exe-Bau spielt denselben Warteton wie das Hochladen, nicht den Ton der KI. Er hängt an der Einstellung „Töne beim Hoch- und Herunterladen und beim Exe-Bau“. Besteht die Exe den Test nicht, kommt der Fehlerton.
- Ist etwas erfolgreich fertig, kommt statt des Windows-Tons ein kurzes, helles Pling (selbst erzeugt, g'' und c'''). Das gilt für Übertragungen, den Exe-Bau und die KI. Bei der KI nur, wenn vorher ein Warteton kam und die Anfrage nicht gescheitert ist. Grund: Wunsch des Nutzers, zu hören, dass etwas erfolgreich durchgelaufen ist.

## 20.10.2026: Fester Ordner für die aktuelle Exe

- Ersetzt den Eintrag vom 04.10.2026, nach dem der Ordner schon beim Veröffentlichen Name-vVersion hieß. Grund: Im Ordner Release des Cockpits lagen am Ende nur noch CodeCockpit-v1.1.27 bis v1.1.30. Das Update tauschte die Exe in dem Ordner, aus dem sie lief, der Name stimmte also nicht mehr. Welchen Ordner man starten soll, war unklar.
- Die aktuelle Exe liegt immer im festen Ordner, zum Beispiel Release\CodeCockpit. Beim Veröffentlichen kommt nur version.txt dazu.
- Ersetzt eine neue Exe eine veröffentlichte, heißt deren Ordner danach Name-vVersion (retire_home). Eine nicht veröffentlichte kommt wie bisher in die Sicherheitskopien.
- Die letzten zwei alten Versionen bleiben im Ordner Release, ältere kommen in die Sicherheitskopien (prune_versions). Ein Ordner, aus dem das Cockpit gerade läuft, bleibt. Das Cockpit räumt beim Start der Exe auf.
- Das Update lädt die neue Version nach Release\_neu und legt sie in Release\CodeCockpit, auch wenn das Cockpit noch aus einem alten Versionsordner läuft. Die Rückfrage nennt den Ordner, aus dem man danach startet.
- Als aktuelle Exe gilt die im festen Ordner, die Versionsordner daneben nicht.

## 20.10.2026: Python für den Bau wählen, Bibliotheken vorher prüfen

- Neue Exe-Einstellung „Python für den Bau“: „Automatisch (empfohlen)“ oder eine installierte Version. Gefunden werden die Versionen über den Python-Starter (py -0p).
- Vor dem Installieren prüft das Cockpit mit pip install --dry-run --only-binary=:all:, ob es alle Bibliotheken aus requirements.txt fertig gibt. Das dauert wenige Sekunden und installiert nichts. Das Ergebnis wird je Python und requirements.txt gemerkt. Ohne Internet gilt die Prüfung als nicht möglich, und es geht weiter wie bisher.
- Automatisch nimmt das Cockpit das neueste Python, für das es alle Bibliotheken fertig gibt. Gibt es keins, das neueste, mit einem Hinweis, was fehlt und was hilft. Passt die Bau-Umgebung nicht zur gewählten Version, wird sie neu angelegt.
- Der Assistent macht die Prüfung schon im Schritt Einrichtung. Die Zusammenfassung nennt die Python-Version. Die Berichtigung von requirements.txt richtet sich nach dieser Version.
- Grund: Beim Waagenzähler scheiterte pip erst nach Minuten, weil es pygame für Python 3.14 nicht fertig gab.

## 20.10.2026: Ansagen in Dialogen gelten als gelöst

- Der Punkt „Sprachausgabe in Dialogen“ aus Phase 3 ist aus TODO.md gestrichen. Grund: Der Nutzer hört Ansagen in Dialogen heute meistens. Geholfen haben die verzögerte Ansage (AFTER_FOCUS_MS) und das Senden an das Steuerelement mit dem Fokus. Fehlt eine einzelne Ansage, wird sie als eigener Fehler gemeldet.

## 20.10.2026: Aufräumrunde der Aktionen

Grundlage ist die Liste des Nutzers in checklisten\aktionen-aufraeumen.md.
- „Terminal …“ steht auf jeder Zeile ganz unten (TERMINAL_ORDER) und nie unter „Weitere“. Strg+T öffnet es direkt im Ordner der markierten Zeile, das Kürzel steht im Menü Datei. Grund: Der Nutzer sieht das Terminal als Kern des Cockpits. Wer lieber selbst Befehle eingibt, soll es überall an derselben Stelle finden.
- Seltene Aktionen stehen im Untermenü „Weitere …“ direkt über dem Terminal (Action.more): Features dieses Projekts, Ordner umbenennen und zurücksetzen, Git-Name und E-Mail, Hochladeverlauf, Änderungen beiseitelegen, Beiseitegelegte Änderungen, Mit vorhandenem Repository verbinden, Virtuelle Umgebung neu anlegen, Wie funktioniert die Exe?.
- „Branches anzeigen …“ heißt „Branches …“. Die Auswahl hat ganz unten „Branches verwalten …“. Die eigene Aktion „Branches verwalten …“ entfällt, die Schnellnavigation öffnet das Fenster weiter direkt.
- Umbenannt: „Pull-Requests-Übersicht …“ in „Pull Requests …“, „Repository-Identität …“ in „Git-Name und E-Mail …“, „Release einlesen …“ in „Exe aus einem Release holen …“, „Release für Branch aus Repository erstellen …“ in „Exe für einen Branch erstellen …“, „Release entfernen …“ beim einzelnen Release in „Dieses Release entfernen …“, „Anzeigen …“ in „Liste filtern …“. „Exe aus diesem Branch erstellen …“ heißt wie auf der Release-Zeile „Exe aus <Branch> erstellen …“.

## 21.10.2026: Auswählen, was in den Commit kommt

- Im Fenster „Änderungen hochladen“ hat die Liste „Änderungen“ Kontrollkästchen, alle angehakt. Leertaste nimmt eine Datei aus dem Commit. Enter auf einer geänderten Datei öffnet „Abschnitte von …“, jeder Abschnitt mit Kästchen, zum Beispiel „Zeile 1 bis 6, 1 neu, 1 entfernt“. Enter auf einem Abschnitt liest ihn vor, jede Zeile mit „Neu:“, „Entfernt:“ oder „Gleich:“ vorne. Bei neuen Dateien zeigt Enter den Inhalt.
- Einzelne Zeilen sind nicht wählbar, nur Dateien und Abschnitte (Antwort des Nutzers: sonst zu viel Pfeilarbeit mit Screenreader).
- Ist alles angehakt, läuft der Commit wie bisher mit git add -A. Sonst nimmt das Cockpit erst alles aus dem Index und bringt dann ganze Dateien mit git add und Abschnitte mit git apply --cached hinein (cockpit\core\staging.py). Die Dateien auf der Festplatte ändern sich nie. Bei umbenannten Dateien kommt der alte Name mit.
- Die Sicherheitsprüfung prüft dann nur die gewählten Dateien, denn nur sie gehen hoch.
- Grund: Vorher kam immer alles in den Commit. Das war die größte Lücke im Vergleich zu GitHub Desktop.

## 21.10.2026: Commits nachbessern, übernehmen, umsortieren und zusammenfassen

Wunsch des Nutzers nach dem Vergleich mit GitHub Desktop.

- Nachbessern (amend) geht nur beim neuesten Commit und nur, solange er nicht hochgeladen ist. Wahlweise nur die Nachricht oder mit den Änderungen ohne Commit.
- Übernehmen in einen anderen Branch (cherry-pick -x). Mit Branch-Ordnern geschieht das im Ordner des Ziel-Branches. Bei einem Konflikt bricht das Cockpit ab, und alles bleibt, wie es war. Hat das Ziel die Änderung schon, sagt das Cockpit das.
- Umsortieren und Zusammenfassen nur bei Commits, die noch nicht hochgeladen sind, ohne Zusammenführungen und ohne Änderungen ohne Commit. Statt eines interaktiven Rebase mit Editor baut das Cockpit die Commits in der neuen Reihenfolge neu auf. Bei einem Konflikt kommt der alte Stand zurück.
- Neuer Branch ab einem früheren Commit, mit Branch-Ordnern in einem eigenen Ordner.
- Co-Autoren beim Commit als Zeile „Co-authored-by:“. Die Auswahl kommt aus den Personen im Verlauf.
- Grund für die Grenzen: Es gibt nie einen force push. Vor jeder Änderung merkt sich das Cockpit den alten Stand unter refs/codecockpit/vorher/. Das ist die Sicherheitskopie.

## 21.10.2026: Konfliktstellen vorlesen und im Editor öffnen

Wunsch des Nutzers nach dem Vergleich mit GitHub Desktop.

- Im Fenster Konflikte öffnet Enter auf einer Datei ihre Konfliktstellen. Jede Stelle nennt Zeile und Umfang. Enter liest sie vor, erst meine Fassung, dann die der Plattform. Pro Stelle gilt meine Fassung, die der Plattform oder beide.
- Ist keine Stelle mehr offen, gilt die Datei als gelöst.
- „Alle Stellen zurückholen“ holt die Konfliktmarken der Datei zurück (git checkout -m). Vorher kommt die Datei in eine Sicherheitskopie.
- Neue Aktion „Im Editor öffnen“ beim Main-Branch und bei jedem Branch. Sie öffnet den Ordner des Branches.
- Der Editor kommt aus den Grundeinstellungen („Editor-Programm“). Ist dort nichts eingetragen, sucht das Cockpit Visual Studio Code, dann Notepad++, dann den Windows-Editor.
- „Konflikt im Editor anzeigen“ heißt weiter so, wie der Nutzer es sich gewünscht hat. Der Knopf öffnet die Datei jetzt im Editor statt mit dem Programm, das Windows für die Endung kennt. Bei .py-Dateien könnte das sonst Python sein, dann liefe die Datei. Visual Studio Code und Notepad++ springen gleich zur ersten Konfliktstelle.

## 21.10.2026: Checks bei Pull Requests und Forks

Wunsch des Nutzers nach dem Vergleich mit GitHub Desktop.

Checks:
- Die Details eines Pull Requests nennen den Stand der Checks, zum Beispiel „Checks: 1 fehlgeschlagen (Tests), 2 erfolgreich“. Das Schlechteste steht vorne.
- Der Knopf „Checks …“ zeigt jeden Check einzeln, fehlgeschlagene zuerst.
- Das Fenster „Übernehmen“ nennt die Checks gleich nach dem ersten Satz.
- Gelesen werden die Check-Läufe (zum Beispiel GitHub Actions) und die älteren Statusmeldungen anderer Dienste.
- In der Liste der Pull Requests stehen die Checks noch nicht. Das wären zwei Anfragen mehr pro Pull Request.

Forks:
- Beim Herunterladen über eine Adresse prüft das Cockpit, ob das Konto dort hochladen darf. Wenn nicht, bietet es einen Fork an. Vorgabe ist „Abbrechen“, weil ein Fork etwas im Konto anlegt.
- Heruntergeladen wird der Fork. Das Original steht in Git als upstream.
- „Vom Original holen …“ beim Main-Branch zieht main nur vorwärts nach (fast-forward). Hat main eigene Commits, bricht das Cockpit ab und erklärt, dass die Arbeit in einen Branch gehört. So geht nie etwas verloren, und es braucht nie einen force push.
- „Pull Request erstellen …“ fragt bei einem Fork, ob er an das Original oder in den Fork gehen soll. Beim Original gibt es keine Prüfer zur Auswahl, weil nur das Original sie anfragen kann.
- Die Liste der Pull Requests zeigt weiter die des Forks. Die Pull Requests im Original sieht man auf GitHub.

## 21.10.2026: Issues, mit und ohne KI

Wunsch des Nutzers nach dem Vergleich mit GitHub Desktop: „Issue soll normal gehen und mit KI, also beides möglich.“

- Neue Aktion „Issues …“ beim Main-Branch. Sie zeigt offene, geschlossene oder alle Issues. Pull Requests, die GitHub dort mitliefert, fehlen in der Liste.
- Ohne KI geht alles: lesen, anlegen, kommentieren, schließen und wieder öffnen, Labels setzen und Personen zuweisen.
- Mit KI-Assistent im Projekt gibt es in den Details „Mit KI zusammenfassen“. Die KI bekommt Titel, Labels, Beschreibung und Kommentare. Zeilen mit Geheimnissen werden vorher entfernt, wie bei den anderen Vorschlägen. Vorher fragt das Cockpit wie immer, wenn die KI außerhalb des Rechners läuft.
- Die KI schlägt auch einen Branch-Namen vor. Er beginnt immer mit der Nummer des Issues. Ohne KI entsteht er aus Nummer und Titel.
- „Branch dafür anlegen …“ arbeitet wie „Neuer Branch“: mit Branch-Ordnern in einem eigenen Ordner.
- Schließen fragt nach, Wieder öffnen nicht, weil es nichts verliert.

## 21.10.2026: Probelauf vor dem Exe-Bau

Punkt aus der Bewertung: Der Exe-Bau soll Fehler früher melden.

- Nach dem Einrichten der virtuellen Umgebung prüft ein kurzer Probelauf den Code. Er braucht Sekunden statt der Minuten von PyInstaller.
- Er geht von der Startdatei aus den eigenen Imports nach. Er meldet Syntaxfehler und fremde Bibliotheken, die in der virtuellen Umgebung fehlen.
- Geprüft werden nur Imports ganz oben in einer Datei. Imports in Funktionen oder in try dürfen oft mit Absicht fehlen.
- Findet er etwas, baut das Cockpit nicht. Die Meldung nennt die Datei, die Zeile und die fehlenden Bibliotheken und rät, sie in requirements.txt einzutragen.
- Klappt der Probelauf selbst nicht, ist das kein Fehler des Projekts. Dann läuft der Bau wie bisher.

## 21.10.2026: Automatische Tests auf GitHub

Punkt aus der Bewertung: Die Tests sollen nicht nur auf dem eigenen Rechner laufen.

- Neue Datei .github/workflows/tests.yml. GitHub führt alle Tests bei jedem Hochladen auf main und bei jedem Pull Request auf main aus.
- Es läuft auf Windows mit Python 3.14, wie auf dem Rechner des Nutzers. Die Bibliotheken kommen aus requirements.txt, dort stehen auch pytest und pytest-qt.
- Fenster laufen ohne Bildschirm (QT_QPA_PLATFORM=offscreen).
- Der Workflow braucht keine Geheimnisse und darf das Repository nur lesen.
- Das Ergebnis zeigt das Cockpit bei Pull Requests unter „Checks …“.

## 21.10.2026: Vorschlag der KI passt zur Auswahl beim Commit

- Sind im Commit-Fenster nicht alle Dateien oder Abschnitte gewählt, sieht die KI nur die gewählten. So beschreibt die Nachricht genau das, was in den Commit kommt.
- Die Auswahl wird beim Drücken von „Vorschlag der KI“ gelesen. Wer danach die Auswahl ändert, kann den Vorschlag neu holen.

## 21.10.2026: Große Dateien aufgeteilt

Punkt aus der Bewertung, vom Nutzer freigegeben: Drei Dateien waren sehr groß. Der Code ist nur verschoben, am Verhalten ändert sich nichts.

- cockpit/core/exe.py: Der Bericht bei Fehlern steht jetzt in exe_report.py, Versionen und Veröffentlichen in exe_publish.py.
- cockpit/ui/exe_flow.py: Die Fenster (Exe-Einstellungen, Bau, Veröffentlichen) stehen jetzt in exe_dialogs.py.
- cockpit/ui/project_actions.py: Stand und Bedingungen hinter den Aktionen stehen jetzt in action_conditions.py.
- Alle alten Namen bleiben über die bisherigen Dateien erreichbar. Die neuen Dateien holen Teile aus exe.py erst beim Aufruf, so gibt es keinen Kreis beim Import.
- Tests, die eine Rückfrage in einem Fenster ersetzen, ersetzen sie jetzt in exe_dialogs.
- Die Klasse ProjectController bleibt in einem Stück. Sie aufzuteilen wäre ein echter Umbau.

## 21.10.2026: Release nach einer neuen Version, mit oder ohne Exe

Rückmeldung des Nutzers: Das Cockpit fragte nach dem Veröffentlichen einer Exe, obwohl es noch keine gab.

- Gibt es eine Exe: „Für Version 1.4.0 ein Release mit der Exe auf GitHub anlegen?“ Danach geht es weiter wie bei „Exe veröffentlichen“.
- Gibt es keine Exe: Das Cockpit bietet an, eine hinzuzufügen. Die Knöpfe heißen „Exe aus dem Code erstellen …“, „Vorhandene Exe wählen …“, „Release nur mit Quellcode …“ und „Später“. Vorgabe und Escape sind „Später“.
- Nach dem Erstellen oder Wählen der Exe veröffentlicht der Nutzer sie selbst mit „Exe veröffentlichen …“. So entscheidet er nach dem Test der Exe.
- Ohne das Feature Exe-Erstellung bleibt die Frage wie bisher.
- Das Fenster für ein Release nur mit Quellcode heißt jetzt „Release anlegen“ statt „Exe veröffentlichen“.
## 21.10.2026: Paketübersicht

Wunsch des Nutzers: Pakete und Sprachmodelle auf dem Rechner und in den Projekten an einer Stelle sehen und pflegen. Der Plan steht in PLAN-PAKETUEBERSICHT.md.

- Die Paketübersicht ist ein Feature („packages“) und ist von Anfang an an. Die Logik liegt in cockpit/features/packages, nicht im Kern. So bleibt die Regel „Der Kern importiert keine Features“.
- Das Menü heißt „Pakete“ und steht nach „Features“. Alt+A öffnet es, weil Alt+P schon belegt ist. Strg+Umschalt+P öffnet die Übersicht direkt.
- Quellen sind pip, winget, Chocolatey und Sprachmodelle (Hugging Face, Ollama, eigene Modelle des Cockpits, Modelldateien in gewählten Ordnern).
- Ein Filter zeigt alles, nur die Cockpit-Projekte oder nur den übrigen Rechner.
- Chocolatey braucht für Änderungen Administratorrechte. Das Cockpit fragt dann über Windows nach, nur für diesen einen Befehl.
- Vor dem Löschen von Paketen und Modellen kommt eine Liste in die Sicherheitskopien, keine Kopie der Dateien. Die Liste nennt Name, Version, Quelle und den Befehl zum Wiederherstellen. Grund: Modelle sind oft viele Gigabyte groß. Der Nutzer hat diese Ausnahme gewählt.
- Bei Modellen bleibt die alte Fassung neben der neuen liegen, bis der Nutzer sie entfernt.
- Bibliotheken und Modelle in Projekten tauscht das Cockpit immer in einem eigenen Branch: „Cockpit-pakete-aktualisieren“ und „Cockpit-modell-tauschen“. Nach dem Tausch laufen die Tests des Projekts.
- Nachfolger für ein Modell schlägt die KI nur auf Wunsch vor. Die Vorschläge sind deutlich als Vorschlag gekennzeichnet.
- Sicherheitslücken kommen aus der freien Datenbank OSV. Gesendet werden nur Name und Version der Pakete.
- Springt die erste Stelle der Version, warnt die Zeile. Dann kann sich vieles ändern.
- „Aufräumen“ hakt Modelle ohne bekannten Benutzer nicht vorab an. Ein Programm außerhalb der Projekte kann sie trotzdem brauchen.
## 22.10.2026: Große Dateien aufgeteilt

Auf Wunsch des Nutzers ist der Code stärker in Module geteilt. Ziel: Dateien mit höchstens etwa 500 Zeilen. Das spart beim Suchen Zeit und Tokens.

- Nur verschoben, am Verhalten ändert sich nichts.
- Die alten Namen bleiben im alten Modul erreichbar (Import mit "noqa: F401").
- Große Klassen sind in Mixins geteilt: ProjectController, GitHubPlatform und MainWindow. Die Mixins haben kein eigenes __init__.
- Dialog-Dateien sind nach Klassen geteilt, zum Beispiel repo_people_dialogs.py und history_edit_dialogs.py.
- Tests ersetzen Namen dort, wo sie aufgerufen werden. Dafür gibt es in tests/conftest.py die Helfer patch_split, patch_controller und patch_running_from.
- cockpit/MODULE.md nennt jede Datei mit einer Zeile.
- Noch über 500 Zeilen: exe_flow.py (eine große Klasse), project_list.py, branch_dialogs.py, package_dialogs.py, platforms/base.py und einige Dateien im Kern. Sie sind in sich geschlossen.

## 22.10.2026: Neuigkeiten und Aktivität

Wunsch des Nutzers, Plan in PLAN-NEUIGKEITEN-UND-MODULE.md, Teil A und B.

- Zwei neue Features, beide abschaltbar und vorausgewählt: „Neuigkeiten“ (cockpit/features/news) und „Aktivität“ (cockpit/features/activity). Beide wirken für alle Projekte, wie die Paketübersicht. Sie werden nur global ein- und ausgeschaltet.
- Neues Menü „&Neuigkeiten“ (Alt+N) mit „Neuigkeiten seit dem letzten Start …“ (Strg+Umschalt+N) und „Aktivität der Projekte …“.
- Die Schnittstelle SupportsActivity steht in einer eigenen Datei, cockpit/platforms/activity.py, nicht in base.py. Grund: base.py hat schon über 600 Zeilen. Die GitHub-Umsetzung steht in github_activity.py. Neu ist auch die Fähigkeit Capability.ACTIVITY.
- Abgefragt wird zusammen mit den Repositories im Hintergrund. Die Neuigkeiten der letzten 30 Tage und die Zahlen kommen in die Datenbank (Tabellen news, activity_daily, activity_snapshot). Die Fenster lesen nur aus der Datenbank, deshalb gehen sie auch ohne Internet.
- Der Zeitpunkt des letzten Starts (news.last_seen) wird erst beim Beenden gesetzt. Beim allerersten Start gibt es keine Ansage.
- Die Zahlen der Aktivität holt das Cockpit höchstens einmal am Tag. Läuft es über Mitternacht, prüft ein Zeitgeber stündlich, ob ein neuer Tag begonnen hat.
- Eigene Beiträge zählen nicht als Neuigkeit. Ausnahme: fehlgeschlagene GitHub Actions, auch wenn man den Lauf selbst ausgelöst hat.
- „Im Cockpit zeigen“ öffnet die Issues des Projekts mit dem Issue markiert. Bei Pull Requests öffnet es die Liste der offenen Pull Requests, noch ohne Markierung.
- Ist ein Feature ausgeschaltet, ist auch sein Tastenkürzel weg, wie bei der Paketübersicht.
- Die Testdaten enthalten erfundene Neuigkeiten und Zahlen für Tagebuch und PDF-Chat.

## 22.10.2026: Einrichtung überarbeitet, neue Seite „Features wählen“

Wunsch des Nutzers: Die Einrichtung soll auch für Neulinge klar sein. Features ohne weitere Einrichtung stehen als Liste, alle angehakt.

- Jede Seite sagt zuerst, wozu der Schritt gut ist: was Git und GitHub sind, warum Zugangsdaten geschützt werden, was die KI konkret tut, lokal oder extern. Die Bewertung steht in BEWERTUNG-EINRICHTUNG.md.
- Neue Seite „Features wählen“ nach dem Projekte-Hauptordner. Sie zeigt alle Features, die weder KI noch Plattform noch einen anderen Dienst brauchen, auch über benötigte Features. Alle sind angehakt. Abhaken schaltet das Feature global aus. Angehakte kommen in die Vorauswahl für Projekte, auch Versionen, das sonst aus ist. Überspringen ändert nichts.
- Features mit KI stehen als Erklärung auf der Seite KI, Features mit Plattform auf der Seite Code-Plattformen wählen. Grund: Man sieht, wozu man das einrichtet.
- Neuigkeiten und Aktivität brauchen jetzt die Fähigkeit „Aktivität“ der Plattform. Grund: Ihre Daten kommen von GitHub. Die Prüfung ohne Projekt bleibt gleich.
- Die Zusammenfassung beginnt nicht mehr mit „Perfekt, Sie haben eingerichtet“, weil oft auch Übersprungenes folgt.
## 22.10.2026: Optik für Sehende (PLAN-OPTIK.md)

Wunsch des Nutzers: einen Plan für die Optik des ganzen Programms und ihn umsetzen. Regel: Was NVDA ansagt und die Braillezeile zeigt, bleibt gleich. Alles Neue ist nur für das Auge und nutzt nur Farben aus der Palette des Windows-Themas.

- Projektliste: Zeilen unter einem Projekt und Projekte in einer geöffneten Sammlung sind eingerückt. Vor Projekten und Sammlungen steht ein Pfeil (▸ zu, ▾ auf). Der Name ist fett, Datum und „ausgeklappt“ sind gedämpft. Das macht ein Zeichner (Delegate), der Text der Zeilen ändert sich nicht.
- Dieselben zwei Textebenen in den Fenstern Neuigkeiten und Aktivität. Passt eine Zeile dort nicht in eine Zeile, zeichnet Qt sie wie bisher mit Umbruch.
- Die Aktionen sind schmaler, ein Drittel der Breite, lange Einträge brechen um. Darunter steht der Bereich „Stand“ mit den Angaben der markierten Zeile untereinander. Er ist kein Tab-Stopp und sagt nichts an. Grund: Für Screenreader und Braillezeile steht alles schon in der Zeile (Nutzer: „was du besser findest“). Im Bereich darf nie etwas stehen, das nicht auch in der Zeile steht.
- Listen mit Fokus haben einen Rahmen von 2 Pixeln in der Hervorhebungsfarbe (Stylesheet mit palette(highlight)).
- Erklärungen in der Einrichtung und die Beschreibung in der Feature-Verwaltung sehen aus wie Text: kein Rahmen, Hintergrund des Fensters. Für den Screenreader bleiben es Listen.
- Die Gruppe „KI“ in der Feature-Verwaltung ist fett.
- Programmsymbol „CC“ auf der Akzentfarbe, mit Qt gemalt. Einige Menüeinträge haben Symbole aus dem Windows-Stil. Die Exe bekommt das Symbol erst, wenn es eine .ico-Datei gibt.
- Geprüft mit Bildern, die unsichtbar entstehen: hell, dunkel und mit 150 Prozent.
## Signaltöne zur Wahl und gespeicherte Paketliste (24.10.2026)

Wunsch des Nutzers. Neues Fenster „Signaltöne“ im Menü Einstellungen. Oben „Alle Signaltöne aus“. Darunter je eine Auswahl für „Programm arbeitet“, „KI arbeitet“ und „Erfolg“. Jede Art hat eigene Töne, auch Melodien und einen Dreiklang. Kein Ton kommt in zwei Arten vor, so klingen die Arten nie gleich. Die Vorgaben sind tiefer und weicher, weil der Nutzer die alten hohen Töne nervig fand. Die alten bleiben als „wie früher“ wählbar. Beim Wechsel in der Auswahl erklingt der Ton zum Anhören. Die Töne erzeugt das Cockpit weiter selbst, ohne neue Bibliothek. Die Schalter in den Grundeinstellungen für Töne beim Hochladen und während die KI schreibt bleiben. „Alle Signaltöne aus“ gilt zusätzlich für alles.

Paketübersicht: oben der Knopf „Aktualisieren“, darunter der Knopf „Filtern“ mit „Alle“, „Nur im Cockpit“ und „Nur auf dem Rechner, nicht im Cockpit“. Die Vorgabe ist bei jedem Öffnen „Alle“. Die gelesene Liste wird in der Datenbank gespeichert (Schlüssel packages.cache) und beim nächsten Öffnen, auch nach einem Neustart, sofort gezeigt. Die erste Zeile nennt den Stand. Neu gelesen wird nur mit „Aktualisieren“, beim allerersten Öffnen und nach einer Änderung an einem Paket, dann nur diese Quelle. Gespeichert wird nur eine vollständige Liste, damit ein Abbruch die alte Liste nicht überschreibt. Aktualisieren, Löschen und „Alle aktualisieren“ spielen den Warteton „Programm arbeitet“ und am Ende den Erfolgs- oder Fehlerton. Sie folgen dem Schalter für Töne beim Hochladen.
Nachtrag: Die Liste wird erst gespeichert, wenn der Hintergrund-Thread ganz zu Ende ist, nie beim Schließen des Fensters. Schreiben in die Datenbank, während der Thread gerade endet, brach in Tests Qt ab. Der Hintergrund-Helfer der Dialoge (DialogWorker) kann dafür „after“ aufrufen, und bei Fehlern „failed“, für den Fehlerton.
## Feature Erklärungen (25.10.2026)

Wunsch des Nutzers: Ganz oben in Listen und Menüs steht eine Erklärung, in Fenstern ein Knopf. Sie sagt in kurzen Absätzen, was man dort machen kann.

- Es ist ein normales Feature „Erklärungen“ in der Feature-Verwaltung, von Anfang an eingeschaltet. Ausschalten dort schaltet alle Erklärungen aus.
- Einzelne Erklärungen hakt man in den Einstellungen des Features ab (Liste „Erklärungen anzeigen für“) oder mit „Diese Erklärung nicht mehr anzeigen“. Gespeichert wird die Liste der gezeigten Titel.
- Projektliste: Zeile „Erklärung: Projektliste“ ganz oben, nur auf der obersten Ebene, nicht in Sammlungen. Dafür gibt es im Kern das neue Ziel Target.EXPLANATION ohne Aktionen. Das ist eine kleine Ergänzung am Kern, ohne PySide6.
- Aktionen: Zeile „Erklärung: Aktionen“ ganz oben. Die Erklärung entsteht aus den Aktionen, die gerade dastehen, mit zwei bis drei Sätzen pro Aktion.
- In beiden Listen startet die Markierung auf dem ersten echten Eintrag, die Erklärung steht darüber. Grund: Sonst landet jedes Tab und jeder Start auf der Erklärung, und Enter würde sie statt der Aktion öffnen.
- Menüs: erster Eintrag „Erklärung …“, auch im Kontextmenü und unter „Weitere“. In Menüs ist er beim Öffnen markiert, wie der Nutzer es beschrieben hat.
- Fenster: Knopf „Erklärung …“ ganz unten, zuletzt in der Tab-Folge, nicht Standardknopf. Nur Fenster mit eigenem Text bekommen ihn. Kurze Rückfragen, Fehlermeldungen und Textfenster bekommen keinen.
- Die Einrichtung zeigt auf „Features wählen“ jetzt alle Features, zuerst die ohne weitere Einrichtung, bei den anderen „Braucht: …“ (Wunsch des Nutzers vom selben Tag).

## Paketübersicht und Update-Austausch (26.10.2026)

Wünsche des Nutzers:

- Die Paketübersicht liest nur noch, wenn man „Paketübersicht aktualisieren“ wählt. Das ist jetzt die oberste Zeile der Liste, der Knopf „Aktualisieren“ oben ist weg. Auch beim allerersten Öffnen wird nichts von selbst gelesen. Nach einer Änderung an einem Paket liest das Cockpit nur diese eine Quelle neu, sonst wäre die Zeile falsch.
- Unter dem Speicherplatz steht die Zeile „Kritisch“ mit allen Bibliotheken, die eine bekannte Sicherheitslücke haben. Enter öffnet sie im selben Fenster wie eine Quelle.
- In den Paketen einer Quelle steht ganz oben „Anzeigen: Alle“ oder „Nur veraltete“. Vorgabe ist immer „Alle“.
- Beim Update bleibt der Ordner Release\CodeCockpit stehen. Nur sein Inhalt wird getauscht. Der Inhalt der bisherigen Version kommt in einen neuen Ordner CodeCockpit-vVersion. Grund: Vorher wurde der Ordner umbenannt. Ein offenes Explorer-Fenster folgte dem umbenannten Ordner, und der Nutzer startete daraus wieder die alte Version. Der Neustart nach dem Bauen der eigenen Exe arbeitet noch wie bisher.
- Nachtrag: Auf Wunsch des Nutzers arbeitet auch der Neustart nach dem Bauen der eigenen Exe so. Liegt in Release\_neu ein Ordner mit demselben Namen wie der bisherige, zum Beispiel CodeCockpit, bleibt der bisherige Ordner stehen. Sein Inhalt kommt nach CodeCockpit-vVersion oder in die Sicherheitskopien, der neue Inhalt in den Ordner.