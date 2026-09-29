# Checkliste Phase 14: Releases und GitHub Actions

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Testen Sie mit einem Projekt auf GitHub, bei dem die Features Versionen und Releases an sind. Für die Punkte zu GitHub Actions braucht das Repository einen Workflow im Ordner .github\workflows. Ein kleiner Test-Workflow genügt, ich kann Ihnen einen schreiben.


## Release nach einer neuen Version

[ ] 1. Angebot nach dem Hochladen
Tasten: Etwas ändern, „Änderungen hochladen …“, bei der Version „Neue Funktion“.
Ansage: Nach „Fertig. …“ die Frage „Für Version … ein Release auf GitHub anlegen?“. Vorgabe ist „Später“.
Fokus: Auf „Später“.
Ergebnis:

[ ] 2. Später
Tasten: Escape.
Ansage: Nichts weiter, oder wie bisher das Angebot eines Pull Requests, wenn Sie in einem Branch sind.
Ergebnis:

[ ] 3. Release nur mit Quellcode
Tasten: Bei einem Projekt ohne Exe-Erstellung „Release anlegen“.
Ansage: Das Fenster „Exe veröffentlichen: …, nur Quellcode“ mit der Version und dem Feld Versionshinweise. Alt+I holt einen Vorschlag der KI. Nach „Veröffentlichen“: „Release … angelegt. Link kopiert.“
Auf GitHub: Das Release hat den Quellcode als ZIP-Datei.
Ergebnis:

[ ] 4. Release mit Exe
Tasten: Bei einem Projekt mit Exe-Erstellung „Release anlegen“.
Ansage: Wie bei „Exe veröffentlichen“, die Version ist schon eingetragen.
Ergebnis:


## Übersicht der Releases

[ ] 5. Liste
Tasten: Auf der Projektzeile „Releases …“.
Ansage: „Releases werden abgefragt.“, dann die Liste, zum Beispiel „1.4.0, 29.09.2026, 12 Downloads, mit Exe“. Neueste oben.
Fokus: In der Liste.
Ergebnis:

[ ] 6. Versionshinweise ansehen und bearbeiten
Tasten: Enter auf einem Release. Dann Escape, Alt+B, Text ändern, Alt+S.
Ansage: Enter zeigt die Versionshinweise, ein Satz pro Zeile. Nach dem Speichern „Versionshinweise gespeichert.“
Fokus: Zurück in der Liste.
Ergebnis:

[ ] 7. Link kopieren und im Browser öffnen
Tasten: Alt+L, dann Alt+R.
Ansage: „Link kopiert.“, dann „Wird im Browser geöffnet.“
Ergebnis:

[ ] 8. Release löschen
Tasten: Alt+Ö für „Release löschen …“.
Ansage: Rückfrage „Das Release … wird auf GitHub gelöscht … Das Tag im Code bleibt.“ Vorgabe „Abbrechen“. Nach „Löschen“: „Release … gelöscht.“
Ergebnis:


## GitHub Actions

[ ] 9. Aktion nur mit Workflows
Tasten: Auf der Projektzeile Tab, bei einem Projekt ohne und einem mit Workflow.
Ansage: „GitHub Actions …“ steht nur beim Projekt mit Workflow.
Ergebnis:

[ ] 10. Liste der Läufe
Tasten: Enter auf „GitHub Actions …“.
Ansage: „Läufe werden abgefragt.“, dann zum Beispiel „Fehlgeschlagen: Tests, Branch main, 29.09.2026 14:10, Neue Suche“.
Fokus: In der Liste.
Ergebnis:

[ ] 11. Fehler lesen
Tasten: Enter auf einem fehlgeschlagenen Lauf.
Ansage: „Die Ausgabe wird geholt.“, dann Fenster „Fehler: Tests, …, Schritt …“. Liste Ausgabe mit dem Ende der Ausgabe, Zeilen mit Fehlern beginnen mit „Fehler:“. Später „Erklärung der KI bereit.“ Mit Tab zur Erklärung.
Fokus: In der Ausgabe, auf der letzten Zeile.
Ergebnis:

[ ] 12. Neu starten und aktualisieren
Tasten: Alt+N, später Alt+A.
Ansage: „Tests wird neu gestartet.“ Nach Alt+A „Aktualisiert.“, der Lauf steht als „Läuft“ oder „Wartet“ oben.
Ergebnis:

[ ] 13. Hinweis in der Projektliste
Tasten: Ist der letzte Lauf fehlgeschlagen, Strg+R.
Ansage: Am Ende der Projektzeile „…, GitHub Actions fehlgeschlagen“. Nach einem erfolgreichen Lauf verschwindet der Hinweis.
Ergebnis:
