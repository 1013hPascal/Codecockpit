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
