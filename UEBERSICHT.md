# Übersicht über die Phasen

Stand: 27.09.2026. Pro Phase das Wichtigste in wenigen Stichpunkten. Die genaue Liste zum Abhaken steht in PLAN.md.

Fertig sind die Phasen 1 bis 6. Offen sind die Phasen 7 bis 17.


## Fertig

### Phase 1: Analyse und Plan
- Die Projekte Chatbot und Tagebuch untersucht und bewährte Bausteine übernommen.
- Plan mit 17 Phasen und Regeln für die Arbeit.
- Keine Profile, eine Sammlung von Einstellungen.

### Phase 2: Grundgerüst
- Hauptfenster mit Projektliste, Aktionsliste und Menüs, ganz per Tastatur.
- Feature-System und Schnittstellen für Plattformen, KI, E-Mail und Automation.
- Grundeinstellungen, Tastenkürzel, Ansagen für NVDA.

### Phase 3: Tresor und Konten
- Tresor in der Windows-Anmeldeinformationsverwaltung oder als verschlüsselte Datei.
- Kontenverwaltung für alle Dienste.
- Einrichtungsassistent beim ersten Start.

### Phase 4: GitHub-Anbindung
- Anmeldung im Browser mit Code oder mit eigenem Token.
- Verbindungstest und Organisationen.
- Verständliche Hinweise, zum Beispiel bei Single Sign-On in Firmen.

### Phase 5: Grundfunktionen
- 5a: Projekte hinzufügen, Git-Identität, Stand in der Projektliste.
- 5b: Sicherheitsprüfung gegen Geheimnisse, Projekt auf GitHub hochladen.
- 5c: Änderungen hochladen und holen, Konflikte lösen, Sicherheitskopien.
- 5d: Verlauf, Rückgängig machen, Änderungen verwerfen.
- 5e: Links, Repository verwalten mit Mitarbeitern, öffentlich oder privat, löschen.
- 5f: Branches und beiseitegelegte Änderungen, Anleitung „Branches verstehen“.

### Phase 6: Pull Requests
- 6a: Pull Requests erstellen, ansehen, kommentieren, Entwürfe.
- 6b: Prüfen, Änderungen ansehen, in main übernehmen und aufräumen.
- 6c: Schutzregeln für main, geschütztes main beim Hochladen, Hochladen über Pull Requests.


## Offen

### Phase 7: Feature-Verwaltung
- Features global und pro Projekt ein- und ausschalten, als Liste mit Kontrollkästchen.
- Abhängigkeiten zwischen Features erklären.
- Einführung beim ersten Einschalten. Der Schalter „Hochladen über Pull Requests“ wandert hierher.

### Phase 8: KI
- Anbindung an Ollama auf dem eigenen Rechner und an OpenAI-kompatible Dienste.
- KI-Assistent: Vorschlag für Commit-Nachrichten und Kurzbeschreibungen.
- Die KI bekommt nie den ganzen Code, nur eine vorbereitete Übersicht.

### Phase 9: README und Versionen
- README erstellen und pflegen, auch in mehreren Sprachen.
- Versionsnummern berechnen.
- Versionen als Tags auf GitHub.

### Phase 10: Exe-Erstellung
- Exe eines Projekts bauen und vorher prüfen, ob alles eingerichtet ist.
- Hinweise zu Warnungen von Windows, Selbstaktualisierung.
- Große Dateien und Modelle auslagern, Lizenzen der Bibliotheken prüfen.

### Phase 11: Automation und Rückmeldungen
- n8n einrichten und Workflows einspielen.
- Ansicht der Automatisierungen.
- Rückmeldungen von GitHub: Sterne, Issues, Kommentare, als Liste im Cockpit.

### Phase 12: E-Mail
- E-Mail-Konten und Test-E-Mail.
- Benachrichtigungen über neue Issues und Kommentare.
- Wochenbericht mit dem Stand aller Projekte.

### Phase 13: Antworten und Wächter
- Antwortentwürfe der KI für Issues, nie automatisch gesendet.
- Abhängigkeiten-Wächter: neue Versionen und Sicherheitswarnungen.
- Erinnerung an Änderungen, die lange nicht hochgeladen wurden.

### Phase 14: Releases
- Releases auf GitHub mit der Exe zum Herunterladen.
- Stabiler Download-Link auf die neueste Version.
- GitHub Actions: Läufe ansehen, Fehler lesen, neu starten.

### Phase 15: Weitere KI-Anbieter
- Azure OpenAI.
- Anthropic.
- Gemini.

### Phase 16: Weitere Plattformen
- GitLab mit Merge Requests.
- Azure DevOps.
- Dieselbe Bedienung, wo die Plattform es kann.

### Phase 17: Sicherung und Feinschliff
- Sicherung und Wiederherstellung, zum Beispiel für einen neuen Rechner.
- Export und Import von Einstellungen, Signieren der Exe.
- Alle Einführungen prüfen und Feinschliff.


## Eine Exe von CodeCockpit selbst

Das ist nicht Teil des Konzepts, sondern ein Wunsch für die eigene Nutzung.

### Wann ist es sinnvoll?

Entschieden am 27.09.2026: Wir warten bis Phase 10. Dort baut das Cockpit Exe-Dateien selbst. Die Exe von CodeCockpit ist dann der erste echte Test für dieses Feature.

Die Überlegung davor:

Jetzt, zwischen Phase 6 und Phase 7. Die Grundfunktionen für Git und GitHub sind fertig und getestet. Damit können Sie Ihre Projekte schon im Alltag verwalten.

Später kommen nur Features dazu. Ihre Daten liegen im Datenordner des Cockpits, nicht in der Exe. Sie bleiben also erhalten, wenn Sie später eine neue Exe nehmen. Das gilt auch für den Tresor und die Konten.

### Wie?

- Einfacher Weg jetzt: Ich baue die Exe mit PyInstaller. Das ist ein zusätzliches Werkzeug nur zum Bauen, das Programm selbst braucht es nicht. Nach der Regel „keine neuen Bibliotheken ohne Rückfrage“ frage ich Sie vorher.
- Nach jeder Phase kann ich eine neue Exe bauen, wenn Sie möchten.
- Ab Phase 10 baut das Cockpit Exe-Dateien selbst. Dann kann es auch sich selbst bauen.

### Worauf achten?

- Windows warnt beim ersten Start einer selbst gebauten Exe (SmartScreen), weil sie nicht signiert ist. Das Signieren kommt in Phase 17.
- Die Exe braucht Git für Windows auf dem Rechner, wie jetzt auch.
- Bitte nicht gleichzeitig die Exe und die Testdaten-Version mit denselben Daten öffnen. Die Testdaten haben ihren eigenen Ordner, das passt also.
