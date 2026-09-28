# CodeCockpit

## Kurzbeschreibung

Cockpit für Windows, das Code-Projekte auf GitHub verwaltet, von KI unterstützt und mit automatisierten Abläufen: hochladen, Branches, Pull Requests, Exe bauen und veröffentlichen, Rückmeldungen im Blick behalten. Es ist barrierefrei vollständig mit der Tastatur bedienbar.


## Worum es geht

CodeCockpit bündelt alles, was nach dem Programmieren anfällt, in einem Programm: Code sichern und hochladen, Änderungen prüfen, Versionen veröffentlichen, Rückmeldungen beantworten. Statt vieler einzelner Werkzeuge, Befehle und Webseiten gibt es eine Projektliste und zu jedem Eintrag die passenden Aktionen.

Zwei Dinge machen CodeCockpit aus:

- **KI-Unterstützung:** Eine KI schlägt Texte vor, erklärt Fehler und hilft bei Routinearbeit. Sie läuft auf Wunsch ganz lokal auf dem eigenen Rechner.
- **Automatisierte Abläufe:** Wiederkehrende Schritte wie Prüfen, Bauen, Testen und Veröffentlichen laufen als festgelegter Ablauf, Schritt für Schritt und mit klarer Rückmeldung.

CodeCockpit ist barrierefrei und vollständig per Tastatur bedienbar.

Das Programm ist in Python mit PySide6 geschrieben.


## KI-Unterstützung

- **KI-Assistent:** Vorschläge für Commit-Nachrichten, Titel und Beschreibung von Pull Requests, die Kurzbeschreibung neuer Projekte und Versionshinweise. Die KI macht nur Vorschläge, entschieden wird immer selbst.
- **Terminal-Erklärung:** Schlägt im eingebauten Terminal ein Befehl fehl, erklärt die KI, warum, und was man tun kann.
- **Lokal oder extern:** Ollama auf dem eigenen Rechner, mit einem Modell passend zum Arbeitsspeicher, oder eine KI im Firmennetz oder im Internet über eine OpenAI-kompatible Schnittstelle.
- **Datenschutz:** Die KI bekommt nie den ganzen Code und nie Geheimnisse. Geht etwas an eine KI außerhalb des Rechners, fragt das Cockpit vorher.
- **Geplant:** Spracheingabe mit Whisper, eine KI-Hilfe zur Bedienung, Antwortentwürfe für Issues und die Pflege der README in mehreren Sprachen.


## Automatisierte Abläufe

- **Hochladen als Ablauf:** Sicherheitsprüfung auf Geheimnisse und große Dateien, Commit, Hochladen. Features hängen sich mit eigenen Schritten ein, zum Beispiel Exe bauen oder Release anlegen.
- **Exe-Erstellung:** Die Exe wird aus dem Code gebaut, getestet und ersetzt die alte erst danach. Mit einem Schritt kommt sie als Release auf GitHub.
- **Branches und Pull Requests:** Auf Wunsch geht jede Änderung über einen eigenen Branch und einen Pull Request mit Prüfung.
- **Geplant mit n8n:** Rückmeldungen wie Sterne, Issues und Downloads täglich sammeln, Wochenbericht und Benachrichtigungen per E-Mail, Hinweise auf veraltete Bibliotheken und auf Änderungen, die zu lange nicht hochgeladen wurden. Die Workflows gehören zu den Features und werden vom Cockpit selbst eingespielt.


## Was CodeCockpit außerdem kann

- Projektliste mit Code und Exe, die Zeilen nennen den Stand, zum Beispiel „3 Dateien noch nicht hochgeladen“.
- Projekte vom Rechner hinzufügen oder von GitHub herunterladen.
- Anmeldung bei GitHub im Browser oder mit Token, auch für Organisationen.
- Änderungen holen und Konflikte Datei für Datei lösen.
- Verlauf ansehen, Änderungen rückgängig machen oder verwerfen, immer mit Sicherheitskopie.
- Repository verwalten: Sichtbarkeit, Mitarbeiter, Schutzregeln, Archivieren, Löschen.
- Eingebautes Terminal mit PowerShell für alles, was es noch nicht als Aktion gibt.
- Features global oder pro Projekt ein- und ausschalten.
- Einrichtungsassistent beim ersten Start.


## Sicherheit

- Zugangsdaten liegen nur verschlüsselt im Tresor: in der Windows-Anmeldeinformationsverwaltung oder in einer Tresordatei mit Master-Passwort.
- Tokens erscheinen nie in Logs, Meldungen oder der Ausgabe des Terminals.
- Aktionen, die Dateien verändern, fragen vorher und legen eine Sicherheitskopie an.
- Ein force push wird nie ausgeführt.


## Voraussetzungen

- Windows 10 oder 11.
- Git für Windows und ein GitHub-Konto.
- Zum Bauen von Exe-Dateien: Python.
- Für die lokale KI: Ollama. Freiwillig.
- Für die geplanten Automatisierungen: n8n. Freiwillig.


## Starten

- Mit der Exe: `CodeCockpit.exe` starten. Python ist dafür nicht nötig.
- Aus dem Code: `start.bat` im Ordner Code. Mit `start_testdaten.bat` startet das Cockpit mit Beispielprojekten in einem eigenen Datenordner. Die echten Daten bleiben dabei unberührt.
- Einstellungen und Projektliste liegen in `%APPDATA%\CodeCockpit`. Eine neue Version liest dieselben Daten, nichts geht verloren.


## Entwicklung

- Python 3.11 oder neuer, PySide6.
- Automatische Tests mit pytest und pytest-qt.
- Das Konzept steht in KONZEPT.md, der Fortschritt in PLAN.md, getroffene Entscheidungen in ENTSCHEIDUNGEN.md.
