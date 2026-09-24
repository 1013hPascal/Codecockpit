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
