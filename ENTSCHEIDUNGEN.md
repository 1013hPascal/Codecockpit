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
