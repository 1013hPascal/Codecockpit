# Checkliste Korrekturen beim Hochladen

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\hochladen-korrekturen. Nehmen Sie ein Testprojekt auf GitHub, bei dem die Features Versionen und README eingeschaltet sind (Projektzeile, „Features dieses Projekts …“). Es braucht einen Branch neben main, zum Beispiel „test“.


## Versionsfrage

[ ] 1. Auf einem Branch: keine Frage
Tasten: Im Ordner des Branches eine Datei ändern. Auf der Branch-Zeile „Änderungen auf GitHub hochladen …“, Commit-Nachricht eingeben.
Ansage: Keine Frage nach der Version. Am Ende in der Zusammenfassung: „Die Version legen Sie fest, wenn die Änderungen in main hochgeladen werden.“
Ergebnis:

[ ] 2. Auf main: Frage kommt
Tasten: Den Branch in main übernehmen (Repository, „Branches verwalten …“, „In main übernehmen …“). Dann auf dem Main-Branch „Änderungen auf GitHub hochladen …“.
Ansage: Das Fenster „Version, Schritt … von …: Version festlegen“ mit „Ist das eine neue Version?“. Vorgabe „Keine neue Version“.
Ergebnis:

[ ] 3. Nichts Neues: keine Frage
Tasten: Auf main noch einmal hochladen, ohne etwas zu ändern.
Ansage: Keine Versionsfrage.
Ergebnis:


## Schritte

[ ] 4. Zählung ohne neue Version
Tasten: Auf main etwas ändern und hochladen. Bei der Version „Keine neue Version“ wählen.
Ansage: Die Schritte zählen lückenlos hoch, zum Beispiel „Schritt 1 von 5“ bis „Schritt 5 von 5“. „Version als Tag setzen“ und „Version hochladen“ kommen nicht vor.
Ergebnis:

[ ] 5. Zählung mit neuer Version
Tasten: Wie 4, aber „Kleine Korrektur“ wählen.
Ansage: Nach der Versionsfrage wird die Gesamtzahl größer, zum Beispiel „Schritt 4 von 7: Version als Tag setzen“. Die Nummern gehen nie zurück.
Ergebnis:

[ ] 6. Rückfragen nennen ihren Schritt
Tasten: Bei jeder Rückfrage während des Hochladens auf den Fenstertitel achten (NVDA+T liest ihn).
Ansage: Der Titel endet mit dem Schritt, zum Beispiel „README: Änderungen, Schritt 3 von 6: README wird geprüft“.
Ergebnis:


## README-Vorschlag

[ ] 7. Fenster mit Vorschlag
Tasten: Wie 5. Nach der Versionsfrage kommt der Vorschlag für den Abschnitt Änderungen.
Ansage: Das Fenster „README: Änderungen, Schritt …“. Der Fokus steht im Feld „Vorschlag“. Der Text lässt sich mit den Pfeiltasten lesen, aber nicht ändern.
Ergebnis:

[ ] 8. Tab führt heraus
Tasten: Im Vorschlag Tab, Tab, Tab. Dann Umschalt+Tab bis zurück in den Text.
Ansage: „Übernehmen“, „Bearbeiten“, „Überspringen“, dann rückwärts wieder bis „Vorschlag“. Kein Tabzeichen im Text.
Ergebnis:

[ ] 9. Kopieren
Tasten: Im Vorschlag Strg+A, Strg+C, dann in einem Editor einfügen.
Ansage: Der Text kommt im Editor an.
Ergebnis:

[ ] 10. Bearbeiten und übernehmen
Tasten: Tab bis „Bearbeiten“, Enter. Etwas ändern. Tab bis „Übernehmen“, Enter.
Ansage: „Text bearbeitbar.“, der Fokus springt in den Text. Danach geht das Hochladen weiter. Die README enthält Ihre Änderung.
Ergebnis:

[ ] 11. Escape überspringt
Tasten: Beim nächsten Vorschlag Escape.
Ansage: Das Fenster schließt, die README bleibt, wie sie ist, das Hochladen geht weiter.
Ergebnis:


## Töne

[ ] 12. Töne beim Hochladen
Tasten: Etwas ändern und hochladen, bei einem größeren Projekt, damit es länger als 10 Sekunden dauert.
Ansage: Beim Start ein Windows-Ton, alle 10 Sekunden ein kurzer leiser Ton, am Ende der Ton für fertig und die Zusammenfassung.
Ergebnis:

[ ] 13. Töne beim Holen und Herunterladen
Tasten: „Änderungen von GitHub holen …“, danach ein Projekt von GitHub herunterladen.
Ansage: Dieselben Töne.
Ergebnis:

[ ] 14. Fehler
Tasten: Netzwerk trennen und hochladen.
Ansage: Am Ende der Windows-Fehlerton und die Fehlermeldung.
Ergebnis:

[ ] 15. Töne ausschalten
Tasten: Menü Einstellungen, Grundeinstellungen, „Töne beim Hoch- und Herunterladen“ abhaken, speichern. Dann hochladen.
Ansage: Keine Töne mehr, die Ansagen bleiben.
Ergebnis:
