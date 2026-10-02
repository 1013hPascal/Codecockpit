# Checkliste: Problem mit KI lösen, Stand in den Aktionen, Branches anzeigen, Reihenfolge

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\exe-ki-und-branches.


## Problem mit KI lösen

[ ] 1. Knopf nach einem Fehler
Tasten: Bei einem Projekt, dessen Exe nicht klappt, „Exe aus dem Code erstellen …“ und dann „Exe erstellen“.
Ansage: Nach dem Fehler „Fehler: …“. Im Bau-Fenster gibt es jetzt den Knopf „Problem mit KI lösen“. Er hat den Fokus.
Ergebnis:

[ ] 2. Die KI arbeitet
Tasten: Enter auf „Problem mit KI lösen“.
Ansage: „Die KI versucht, das Problem zu lösen.“ Das Fenster mit der Liste „Fortschritt“ zeigt oben „Die KI versucht, das Problem zu lösen. Läuft seit … Sekunden.“, darunter die gelesenen Dateien, „Die Fehlermeldung wird gelesen.“ und „Stelle aus der Fehlermeldung gelesen: …“, wenn der Fehler eine Datei nennt.
Ergebnis:

[ ] 3. Vorschlag und Branch
Tasten: Den Vorschlag lesen, „Übernehmen“.
Ansage: Wie beim Einrichten: Die Änderungen kommen in den Branch Cockpit-exe-bauen, nicht in main. Danach das Fenster mit dem Ergebnis und „Exe erstellen“.
Ergebnis:

[ ] 4. Mehrere Durchgänge
Tasten: „Exe erstellen“. Scheitert der Bau wieder, noch einmal „Problem mit KI lösen“.
Ansage: Derselbe Ablauf. Die KI liest jetzt im Branch Cockpit-exe-bauen weiter, mit dem Stand des vorigen Versuchs. Klappt der Bau, kommt die Frage „Wie geht es weiter?“.
Ergebnis:


## Stand in den Aktionen

[ ] 5. Main-Branch
Tasten: Auf „Main-Branch“ Tab, mit Pfeil runter.
Ansage: Zum Beispiel „Änderungen auf GitHub hochladen …, 3 Dateien offen“ oder „…, nichts offen“, „Änderungen von GitHub holen …, 2 neue Änderungen“ oder „…, alles aktuell“, „Pull Requests …, 2 offen“ oder „…, keine offen“, „Änderungen verwerfen …, 1 Datei geändert“, „Änderungen beiseitelegen …, nichts geändert“.
Ergebnis:

[ ] 6. Branch
Tasten: Auf einer Branch-Zeile Tab, mit Pfeil runter.
Ansage: Dieselben Angaben. „Pull-Requests-Übersicht …“ nennt die offenen Pull Requests aus diesem Branch.
Ergebnis:

[ ] 7. Exe
Tasten: Auf „Exe, …“ Tab, mit Pfeil runter.
Ansage: „Exe aus dem Code erstellen …, Code geändert seit dem letzten Bau“, „…, Exe aktuell“ oder „…, noch keine Exe“. „Exe veröffentlichen …, zuletzt Version …“ oder „…, noch nicht veröffentlicht“.
Ergebnis:

[ ] 8. In main übernehmen
Tasten: „Branches verwalten“, einen Branch wählen, Tab bis zum Knopf.
Ansage: „In main übernehmen …, 2 Commits offen“ oder „…, alles aktuell“.
Ergebnis:


## Branches anzeigen

[ ] 9. Auswahl unter „Neuer Branch …“
Tasten: „Branches verwalten“ öffnen, Pfeil runter.
Ansage: „Branches anzeigen: Die Sie lokal haben“. Darunter nur die Branches, die Sie lokal haben.
Ergebnis:

[ ] 10. Menü
Tasten: Leertaste oder Enter auf „Branches anzeigen“. Mit Pfeil hoch und runter wählen, Enter.
Ansage: Ein Menü mit „Die Sie lokal haben“ (angehakt), „Die nur auf GitHub sind“ und „Alle“. Nach der Wahl zum Beispiel „Die nur auf GitHub sind: 3 Branches.“ Escape lässt alles, wie es ist.
Ergebnis:

[ ] 11. Branch nur auf GitHub
Tasten: „Die nur auf GitHub sind“ wählen, einen Branch markieren, Tab durch die Knöpfe.
Ansage: „Herunterladen“, „Umbenennen …“, „Löschen …“. „In main übernehmen …“ gibt es hier nicht.
Ergebnis:


## Projektliste

[ ] 12. Nur lokale Branches
Tasten: Ein Projekt mit Branch-Ordnern ausklappen.
Ansage: „Main-Branch …“, „Branches verwalten“, die Branch-Ordner, „Exe …“. „Branches auf GitHub“ steht dort nicht mehr.
Ergebnis:

[ ] 13. Reihenfolge ganz oben
Tasten: In der Projektliste nach den drei obersten Einträgen mit Pfeil runter lesen.
Ansage: Sammlungen und einzelne Projekte stehen gemischt, das zuletzt Geänderte oben. Eine Sammlung steht so weit oben wie ihr neuestes Projekt. In einer geöffneten Sammlung bleibt alles wie bisher.
Ergebnis:


## Ordner neben der Exe

[ ] 14. Auswahl in den Exe-Einstellungen
Tasten: Bei der Vokabel-App auf „Exe, …“ „Exe-Einstellungen …“, mit Tab bis zur Liste.
Ansage: Liste „Ordner und Dateien neben der Exe“ mit Kontrollkästchen, zum Beispiel „Meine-Vokabeln, vom Code benutzt“, angehakt, und „config.csv“. Leertaste hakt an oder ab.
Ergebnis:

[ ] 15. Neuer leerer Ordner
Tasten: Tab bis „Neuer Ordner neben der Exe“, einen Namen eingeben, Alt+H für „Hinzufügen“.
Ansage: „… kommt neben die Exe.“ In der Liste steht „…, wird neben der Exe leer angelegt“, angehakt.
Ergebnis:

[ ] 16. Meine-Vokabeln kommt mit
Tasten: „Exe aus dem Code erstellen …“ mit KI bis „Exe erstellen“.
Ansage: Das Ergebnis nennt „Neben die Exe kommen: Meine-Vokabeln.“ Nach dem Bau steht im Ordner Exe neben der VokabelApp.exe der Ordner Meine-Vokabeln mit Ihren Vokabeln. Das Bau-Fenster nennt „Neu neben der Exe: Meine-Vokabeln.“
Ergebnis:


## Fragen an die KI nach einem Schritt

[ ] 17. Frage zum Vorschlag
Tasten: Im Fenster mit dem Vorschlag der KI mit Tab zu „Frage an die KI“, eine Frage schreiben, Enter.
Ansage: „Die KI antwortet.“, dann „Antwort da.“ In der Liste „Gespräch mit der KI“ stehen „Sie: …“ und „KI: …“, ein Satz pro Zeile. Das Feld ist wieder leer für die nächste Frage.
Ergebnis:

[ ] 18. Mit den Hinweisen wiederholen
Tasten: Nach einer Antwort Tab bis „Mit den Hinweisen wiederholen“, Enter.
Ansage: „Der letzte Schritt wird mit den Hinweisen wiederholt.“ Das Fenster „Fortschritt“ kommt wieder, danach ein neuer Vorschlag. Ohne vorherige Frage sagt das Cockpit, dass Sie zuerst fragen sollen.
Ergebnis:

[ ] 19. Frage vor „Exe erstellen“
Tasten: Im Fenster „Exe aus dem Code erstellen: …“ nach dem Übernehmen eine Frage stellen, zum Beispiel „Kommt Meine-Vokabeln mit?“.
Ansage: Die KI antwortet wie in Punkt 17. Danach „Exe erstellen“ oder „Mit den Hinweisen wiederholen“.
Ergebnis:
