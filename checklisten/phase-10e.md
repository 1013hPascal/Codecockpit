# Checkliste 10e: Updates der Exe

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

## Vorbereitung

Die Prüfung läuft nur in der Exe, nicht beim Start aus dem Code. So testen Sie:

1. Veröffentlichen Sie die neue Exe als Version 1.1.0. Nutzen Sie dafür „Exe veröffentlichen“ im Eintrag Exe des Cockpits.
2. Legen Sie die alte Exe 1.0.0 in einen Testordner, zum Beispiel `Downloads\Test`. Sie finden sie im Release 1.0.0 oder in den Sicherheitskopien.
3. Starten Sie die alte Exe dort. Die alte Exe hat die Prüfung noch nicht. Deshalb geht der erste echte Test erst ab der Version nach 1.1.0: Bauen Sie später eine 1.1.1, veröffentlichen Sie sie und starten Sie dann die 1.1.0 aus dem Testordner.

## Prüfpunkte

[ ] 1. Menüpunkt beim Start aus dem Code
Tasten: Alt+H, dann U.
Ansage: Meldung „Updates gibt es nur für die Exe …“ mit OK.
Fokus: Nach OK wieder in der Projektliste.
Ergebnis:

[ ] 2. Automatische Rückfrage in der Exe
Tasten: Die ältere Exe starten und etwa 10 Sekunden warten.
Ansage: „Update verfügbar“, dann „Version … von CodeCockpit ist verfügbar (… MB). Einstellungen, Konten und Projekte bleiben erhalten. …“. Vorgabe ist „Später“.
Fokus: Auf „Später“.
Ergebnis:

[ ] 3. Versionshinweise
Tasten: Alt+V in der Rückfrage.
Ansage: Fenster „Versionshinweise …“ mit dem Text des Releases. Nach dem Schließen kommt die Rückfrage wieder.
Fokus: Im Text, danach wieder in der Rückfrage.
Ergebnis:

[ ] 4. Escape wählt Später
Tasten: Escape in der Rückfrage.
Ansage: Nichts weiter. Heute wird nicht noch einmal gefragt. Alt+H, U fragt sofort erneut.
Fokus: Zurück im Hauptfenster.
Ergebnis:

[ ] 5. Aktualisieren und neu starten
Tasten: Alt+H, U, dann Alt+A, später Enter auf „Neu starten“.
Ansage: „Update wird heruntergeladen.“, dann „Version … ist heruntergeladen und geprüft. … Jetzt neu starten?“. Danach schließt sich das Cockpit und startet mit der neuen Version.
Fokus: Nach dem Neustart in der Projektliste. Ihre Konten und Projekte sind noch da.
Ergebnis:

[ ] 6. Sicherheitskopie der alten Exe
Tasten: Alt+D, dann „Sicherheitskopien“.
Ansage: Ein Eintrag „CodeCockpit Exe vor dem Update auf … ersetzt“.
Fokus: In der Liste der Sicherheitskopien.
Ergebnis:

[ ] 7. Später übernimmt beim Beenden
Tasten: Wie Punkt 5, aber bei „Jetzt neu starten?“ Escape. Dann Strg+Q.
Ansage: „Das Update wird beim Beenden übernommen.“ Nach dem Beenden liegt im Ordner die neue Exe. Sie startet nicht von selbst.
Fokus: Kein Fokus, das Cockpit ist beendet.
Ergebnis:

[ ] 8. Diese Version überspringen
Tasten: In der Rückfrage Alt+B.
Ansage: „Version … wird übersprungen.“ Die automatische Prüfung fragt nach dieser Version nicht mehr. Alt+H, U bietet sie trotzdem an.
Fokus: Zurück im Hauptfenster.
Ergebnis:

[ ] 9. Schalter in den Grundeinstellungen
Tasten: Alt+E, G, zum Kontrollkästchen „Täglich nach Updates für CodeCockpit suchen“.
Ansage: Kontrollkästchen, aktiviert. Ausgeschaltet kommt beim Start keine Rückfrage mehr.
Fokus: Auf dem Kontrollkästchen.
Ergebnis:
