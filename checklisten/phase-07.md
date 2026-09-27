# Checkliste Phase 7: Feature-Verwaltung

Stand: 27.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- Menü „Features“ mit der „Feature-Verwaltung …“ für alle Projekte.
- Auf der Projektzeile „Features dieses Projekts …“. Die Aktion „Hochladen über Pull Requests einschalten“ bei Code gibt es nicht mehr.
- Die Einführung eines Features erscheint beim allerersten Einschalten.
- Die Vorauswahl für neue Projekte steht in der Feature-Verwaltung, nicht mehr in den Grundeinstellungen.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten reicht die Windows-Anmeldeinformationsverwaltung. Ein GitHub-Konto brauchen Sie nur für den freiwilligen Punkt 14.
3. Mit den Testdaten gibt es zwei Beispiel-Features: „Beispiel Grundlage“ bringt eine Einstellung und die Aktion „Beispiel-Gruß“ bei Code mit. „Beispiel Aufbau“ braucht die Grundlage. Beim normalen Start gibt es sie nicht.

Bitte gehen Sie die Punkte der Reihe nach durch.


## A. Feature-Verwaltung

[ ] 1. Menü und Liste
Tasten: Alt+F, Enter auf „Feature-Verwaltung …“. Die Liste lesen.
Erwartet: Das Fenster heißt „Feature-Verwaltung: 3 Features“. Der Fokus steht in der Liste. Die Zeilen sind „Beispiel Aufbau, eingeschaltet“, „Beispiel Grundlage, eingeschaltet“ und „Branches und Pull Requests, eingeschaltet“. NVDA sagt bei jeder Zeile, dass sie angekreuzt ist.
Ergebnis:

[ ] 2. Beschreibung und Knöpfe
Tasten: Auf „Beispiel Aufbau“ Tab, die Beschreibung lesen. Weiter mit Tab. Dann mit Umschalt+Tab zurück in die Liste, auf „Beispiel Grundlage“ und wieder mit Tab durch alles.
Erwartet: Bei Beispiel Aufbau steht „Nur zum Testen. Braucht das Feature „Beispiel Grundlage“.“, „Braucht: Beispiel Grundlage.“, „Für neue Projekte: aus.“ und „In 0 Projekten eingeschaltet.“ Danach kommen „Für neue Projekte einschalten“ (nicht angekreuzt), „Einführung …“, „Speichern“ und „Abbrechen“. Bei Beispiel Grundlage gibt es zusätzlich „Einstellungen …“.
Ergebnis:

[ ] 3. Einführung
Tasten: Auf „Beispiel Grundlage“ „Einführung …“. Lesen, Escape.
Erwartet: Das Fenster heißt „Einführung: Beispiel Grundlage“. Jede Zeile ist ein Satz. Escape führt zurück.
Ergebnis:

[ ] 4. Einstellungen eines Features
Tasten: „Einstellungen …“. Im Feld „Gruß“ `Moin` eintippen, „Mit Ausrufezeichen“ ankreuzen, „Speichern“. Dann „Abbrechen“ in der Feature-Verwaltung.
Erwartet: Das Fenster heißt „Einstellungen: Beispiel Grundlage“ mit den Feldern „Gruß“ und „Mit Ausrufezeichen“. NVDA sagt „Einstellungen für Beispiel Grundlage gespeichert.“
Ergebnis:


## B. Features eines Projekts

[ ] 5. Fenster öffnen
Tasten: In der Projektliste auf „PDF-Chat“ Tab, „Features dieses Projekts …“, Enter.
Erwartet: Das Fenster heißt „Features von PDF-Chat: folgt der Vorauswahl“. Die Zeilen sind „Beispiel Aufbau, aus“, „Beispiel Grundlage, aus“ und „Branches und Pull Requests, aus“.
Ergebnis:

[ ] 6. Mit Abhängigkeit einschalten
Tasten: Auf „Beispiel Aufbau“ Leertaste. Die Zeile lesen. Tab bis „Speichern“, Enter. Die Frage lesen, „Speichern“. Die Einführung lesen, Escape.
Erwartet: Nach der Leertaste heißt die Zeile „Beispiel Aufbau, eingeschaltet, aber nicht verfügbar: Benötigt Beispiel Grundlage. …“. Die Frage sagt: „Beispiel Aufbau benötigt Beispiel Grundlage. Beispiel Grundlage ist für dieses Projekt ausgeschaltet und wird mit eingeschaltet. Die Auswahl steht danach in der Datei cockpit.toml im Ordner Code und wird mit hochgeladen. Speichern?“ Vorgabe ist „Abbrechen“. Danach sagt NVDA „Features von PDF-Chat gespeichert.“, und es erscheint „Einführung: Beispiel Aufbau“. Die Einführung der Grundlage kommt nicht, weil Sie sie in Punkt 3 schon gelesen haben.
Ergebnis:

[ ] 7. Aktion des Features
Tasten: Zu Code von PDF-Chat, Tab, zu „Beispiel-Gruß“, Enter.
Erwartet: „Beispiel-Gruß“ steht in der Aktionsliste. NVDA sagt „Moin!“. Die Zeile Code nennt jetzt eine Datei mehr, die noch nicht hochgeladen ist: cockpit.toml.
Ergebnis:

[ ] 8. Mit Abhängigen ausschalten
Tasten: Auf PDF-Chat „Features dieses Projekts …“. Auf „Beispiel Grundlage“ Leertaste, „Speichern“, die Frage lesen, „Speichern“.
Erwartet: Der Titel sagt jetzt „eigene Auswahl“. Die Frage beginnt mit „Ohne Beispiel Grundlage geht auch Beispiel Aufbau aus.“ Danach fehlt „Beispiel-Gruß“ bei Code.
Ergebnis:

[ ] 9. Nichts geändert
Tasten: Noch einmal „Features dieses Projekts …“, gleich „Speichern“.
Erwartet: Es gibt keine Frage. NVDA sagt „Nichts geändert.“
Ergebnis:


## C. Global und Vorauswahl

[ ] 10. Vorauswahl für neue Projekte
Tasten: Alt+F, „Feature-Verwaltung …“. Auf „Beispiel Grundlage“ mit Tab zu „Für neue Projekte einschalten“, Leertaste. Zurück in die Liste, die Beschreibung lesen. „Speichern“.
Erwartet: In der Beschreibung steht jetzt „Für neue Projekte: eingeschaltet.“ NVDA sagt „Feature-Verwaltung gespeichert.“
Ergebnis:

[ ] 11. Vorauswahl bei einem Projekt
Tasten: Auf „Tagebuch“ „Features dieses Projekts …“, lesen, Escape. Dann zu Code von Tagebuch und die Aktionen lesen.
Erwartet: Der Titel heißt „Features von Tagebuch: folgt der Vorauswahl“. „Beispiel Grundlage“ heißt „aktiv“. Bei Code steht „Beispiel-Gruß“. In PDF-Chat bleibt die Grundlage aus, weil PDF-Chat eine eigene Auswahl hat.
Ergebnis:

[ ] 12. Global ausschalten
Tasten: Feature-Verwaltung, auf „Beispiel Grundlage“ Leertaste, „Speichern“. Dann Code von Tagebuch, Aktionen lesen. Dann „Features dieses Projekts …“ bei Tagebuch lesen, Escape.
Erwartet: Die Zeile in der Feature-Verwaltung heißt „Beispiel Grundlage, ausgeschaltet“. Danach fehlt „Beispiel-Gruß“ bei Code. In „Features dieses Projekts“ steht die Grundlage gar nicht mehr.
Ergebnis:

[ ] 13. Global wieder einschalten
Tasten: Feature-Verwaltung, „Beispiel Grundlage“ wieder ankreuzen, „Speichern“. Code von Tagebuch, Aktionen lesen.
Erwartet: „Beispiel-Gruß“ ist wieder da. Die Einführung erscheint nicht noch einmal, weil Sie sie schon kennen.
Ergebnis:


## D. Hochladen (freiwillig, nur mit GitHub-Konto)

[ ] 14. Features beim ersten Hochladen
Tasten: Nur, wenn Sie im Assistenten ein GitHub-Konto eingerichtet haben. Bei Code von Bildbeschreiber „Auf GitHub hochladen …“. Im Fenster mit Tab bis „Features für dieses Projekt“, lesen. Dann Escape, es wird nichts hochgeladen.
Erwartet: Die Liste „Features für dieses Projekt“ zeigt alle drei Features als Kontrollkästchen. „Beispiel Grundlage“ ist angekreuzt, weil es zur Vorauswahl gehört.
Ergebnis:
