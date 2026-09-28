# CodeCockpit

## Kurzbeschreibung

Barrierefreies Cockpit für Windows, das Code-Projekte auf GitHub verwaltet: hochladen, holen, Branches, Pull Requests, Exe bauen und veröffentlichen. Vollständig per Tastatur, entwickelt für Screenreader und Braillezeile.


## Worum es geht

CodeCockpit ist ein Programm für Windows, mit dem man eigene Code-Projekte verwaltet, ohne ein Terminal oder die Webseite von GitHub zu brauchen.

Es richtet sich an Menschen, die mit Screenreader und Braillezeile arbeiten. Viele Werkzeuge für Git und GitHub sind damit schwer zu bedienen. CodeCockpit ist von Anfang an so gebaut, dass alles per Tastatur geht und jede Rückmeldung als kurzer, klarer Text kommt.

Das Programm ist in Python mit PySide6 geschrieben und wird mit NVDA getestet.


## Grundsätze

- Barrierefreiheit geht vor Aussehen. Jedes Steuerelement hat einen kurzen Namen, jede Liste nennt das Wichtigste zuerst.
- Alles per Tastatur. Tastenkürzel stehen im Menü und in der Hilfe (F1).
- Nichts passiert ohne Rückfrage. Aktionen, die Dateien verändern, beschreiben vorher, was passiert, und legen eine Sicherheitskopie an.
- Sicherheit: Zugangsdaten liegen nur verschlüsselt im Tresor. Ein force push wird nie ausgeführt.
- Modular: Zusatzfunktionen sind Features, die man global oder pro Projekt ein- und ausschaltet.


## Was CodeCockpit heute kann

### Projekte

- Projektliste als Baum: Projekt, darunter Code und Exe. Die Zeilen nennen den Stand, zum Beispiel „3 Dateien noch nicht hochgeladen“.
- Projekte vom Rechner hinzufügen oder von GitHub herunterladen.
- Einrichtungsassistent beim ersten Start: Tresor, GitHub-Konto, Projekte-Ordner, Git-Identität, KI.

### GitHub und Git

- Anmeldung bei GitHub im Browser oder mit Token, auch für Organisationen.
- Neues Projekt auf GitHub hochladen, mit Sicherheitsprüfung auf Geheimnisse, große Dateien und private E-Mail-Adressen.
- Änderungen hochladen und holen, Konflikte Datei für Datei lösen.
- Verlauf ansehen, Änderungen rückgängig machen oder verwerfen, immer mit Sicherheitskopie.
- Repository verwalten: Sichtbarkeit, Mitarbeiter, Schutzregeln, Archivieren, Löschen.
- Branches, beiseitegelegte Änderungen (Stash) und Pull Requests mit Reviews.
- Eingebautes Terminal mit PowerShell, dessen Ausgabe Zeile für Zeile lesbar ist.

### Exe

- Eigener Eintrag „Exe“ im Projekt.
- Exe aus dem Code bauen (PyInstaller), testen und erst danach die alte ersetzen.
- Exe auf GitHub als Release veröffentlichen oder aus einem Release holen.
- Prüfung, ob sich die Exe ohne Handarbeit bauen lässt.
- CodeCockpit baut und aktualisiert auch seine eigene Exe.

### KI (freiwillig)

- Lokale KI mit Ollama, passend zum Arbeitsspeicher des Rechners, oder eine KI im Firmennetz oder im Internet.
- KI-Assistent: Vorschläge für Commit-Nachrichten, Pull Requests, Kurzbeschreibungen und Versionshinweise.
- Terminal-Erklärung: Schlägt ein Befehl fehl, erklärt die KI den Fehler in einfachen Sätzen.
- Datenschutz: Die KI bekommt nie den ganzen Code und nie Geheimnisse. Bei KI außerhalb des Rechners fragt das Cockpit vorher.


## Was noch kommt

- Automatische Updates des Cockpits.
- Spracheingabe mit Whisper in jedes Eingabefeld (Strg+D).
- KI-Hilfe zur Bedienung des Cockpits.
- README-Pflege und Versionsnummern.
- Rückmeldungen, Wochenbericht und Benachrichtigungen per E-Mail mit n8n.
- Weitere Plattformen wie GitLab und weitere KI-Anbieter.


## Voraussetzungen

- Windows 10 oder 11.
- Git für Windows.
- Ein GitHub-Konto.
- Zum Bauen von Exe-Dateien: Python.
- Für die lokale KI: Ollama. Freiwillig.


## Starten

- Mit der Exe: `CodeCockpit.exe` starten. Python ist dafür nicht nötig.
- Aus dem Code: `start.bat` im Ordner Code. Mit `start_testdaten.bat` startet das Cockpit mit Beispielprojekten in einem eigenen Datenordner. Die echten Daten bleiben dabei unberührt.


## Daten und Sicherheit

- Einstellungen und Projektliste liegen in `%APPDATA%\CodeCockpit`. Eine neue Version liest dieselben Daten, nichts geht verloren.
- Zugangsdaten liegen nur im Tresor: in der Windows-Anmeldeinformationsverwaltung oder in einer verschlüsselten Tresordatei mit Master-Passwort.
- Tokens erscheinen nie in Logs, Meldungen oder der Ausgabe des Terminals.


## Entwicklung

- Python 3.11 oder neuer, PySide6.
- Automatische Tests mit pytest und pytest-qt, dazu eine Checkliste für NVDA und Braillezeile pro Entwicklungsschritt.
- Das Konzept steht in KONZEPT.md, der Fortschritt in PLAN.md, getroffene Entscheidungen in ENTSCHEIDUNGEN.md.
