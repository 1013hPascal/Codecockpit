# Checkliste: README überarbeitet

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\Readme-ueberarbeiten. Nehmen Sie ein Testprojekt ohne README, bei dem das Feature README-Pflege eingeschaltet ist.


[ ] 1. Auswahl ohne README
Tasten: Auf der Projektzeile „README …“, Enter.
Ansage: Die Liste „README“ mit „README-Einstellungen …“, „README aus Ordner hochladen …“ und „README mit KI schreiben …“. Der Fokus steht auf dem ersten Eintrag.
Ergebnis:

[ ] 2. README aus Ordner hochladen, Abbrechen
Tasten: „README aus Ordner hochladen …“, im Dialog von Windows eine .md-Datei wählen, dann Escape bei der Rückfrage.
Ansage: Rückfrage „Name.md wird als README.md in den Ordner Code kopiert. Übernehmen?“ mit „Übernehmen“ und „Abbrechen“ (Vorgabe). Nach Escape gibt es keine README.md.
Ergebnis:

[ ] 3. README aus Ordner hochladen, Übernehmen
Tasten: Wie Punkt 2, aber „Übernehmen“.
Ansage: „README.md übernommen.“ Die Datei liegt im Ordner Code. „Änderungen auf GitHub hochladen …“ zeigt README.md als neu.
Ergebnis:

[ ] 4. Auswahl mit README
Tasten: Wieder „README …“, Enter.
Ansage: Die Liste hat jetzt „README-Einstellungen …“ und „README bearbeiten …“.
Ergebnis:

[ ] 5. README mit KI schreiben, Aufbau
Tasten: README.md im Ordner Code löschen. „README …“, „README mit KI schreiben …“. Dann Tab durch den Dialog.
Ansage: Fokus in der Liste „Dateien mit Infos zum Programm“. Mit Tab: „Datei hinzufügen …“, „Datei entfernen“, „Infos für die README“, „Von KI verfassen lassen“, „README ist fertig so“, „Abbrechen“. Die Felder für den Text und die Vorschläge gibt es noch nicht.
Ergebnis:

[ ] 6. Dateien hinzufügen und entfernen
Tasten: „Datei hinzufügen …“, eine oder mehrere Textdateien wählen. Dann eine in der Liste markieren und „Datei entfernen“.
Ansage: „Datei hinzugefügt.“ oder „2 Dateien hinzugefügt.“ Die Liste zeigt die Dateinamen. Danach „Name entfernt.“
Ergebnis:

[ ] 7. Fertig ohne Text
Tasten: „README ist fertig so“, bevor die KI etwas geschrieben hat.
Ansage: „Es gibt noch keinen Text für die README.“ Der Dialog bleibt offen.
Ergebnis:

[ ] 8. Von KI verfassen lassen
Tasten: Etwas in „Infos für die README“ schreiben, dann „Von KI verfassen lassen“.
Ansage: „Die KI schreibt die README.“ Wenn sie fertig ist: Der Fokus steht im Feld „README-Text“ am Anfang, dann „Die README von der KI ist da.“ Die README nutzt Ihre Infos und den Inhalt Ihrer Dateien.
Ergebnis:

[ ] 9. Verbesserungsvorschläge
Tasten: Tab vom Feld „README-Text“ in „Verbesserungsvorschläge für die KI“, einen Wunsch schreiben, dann „Von KI verfassen lassen“.
Ansage: „Die KI überarbeitet die README.“ Danach steht der überarbeitete Text im Feld, das Feld für die Vorschläge ist leer.
Ergebnis:

[ ] 10. README ist fertig so
Tasten: Im Text selbst etwas ändern, dann „README ist fertig so“.
Ansage: „README.md gespeichert.“ Die Datei enthält genau Ihren Text.
Ergebnis:

[ ] 11. Übersetzung
Tasten: Vorher unter „README-Einstellungen …“ Deutsch als weitere Sprache anhaken. Dann wie Punkt 8 bis 10.
Ansage: Nach dem Speichern „Die KI übersetzt die README.“ Dann ein Fenster „README übersetzt, Deutsch: 1 von 1“ mit dem Text im Feld. „Übernehmen“ sagt „Übersetzung gespeichert: README.de.md.“ Oben in README.md und README.de.md stehen die Links zu beiden Sprachen.
Ergebnis:

[ ] 12. Übersetzung überspringen
Tasten: Im Fenster der Übersetzung Escape.
Ansage: „Keine Übersetzung übernommen.“ README.de.md bleibt, wie sie war.
Ergebnis:

[ ] 13. README bearbeiten, Aufbau
Tasten: „README …“, „README bearbeiten …“. Dann Tab durch den Dialog.
Ansage: Fokus im Feld „README-Text“ mit der README. Mit Tab: „Anweisungen an die KI zur Überarbeitung“, „Von KI überarbeiten lassen“, „Die README ist fertig so“, „Abbrechen“.
Ergebnis:

[ ] 14. Überarbeiten ohne Anweisungen
Tasten: Ohne Text im Feld für die Anweisungen „Von KI überarbeiten lassen“.
Ansage: „Bitte schreiben Sie zuerst Anweisungen an die KI.“ Es wird nichts gesendet.
Ergebnis:

[ ] 15. Von KI überarbeiten lassen
Tasten: Eine Anweisung schreiben, zum Beispiel „Schreibe den Abschnitt Bedienung kürzer.“, dann „Von KI überarbeiten lassen“.
Ansage: „Die KI überarbeitet die README.“ Danach Fokus im Text, „Die README von der KI ist da.“ Nur das Gewünschte ist geändert.
Ergebnis:

[ ] 16. Speichern mit Sicherheitskopie
Tasten: „Die README ist fertig so“.
Ansage: „README.md gespeichert. Die alte steht in den Sicherheitskopien.“ Bei weiteren Sprachen folgt die Übersetzung wie in Punkt 11.
Ergebnis:

[ ] 17. Abbrechen mit Änderungen
Tasten: „README bearbeiten …“, etwas ändern, dann Escape.
Ansage: Rückfrage „Der Text der README ist nicht gespeichert. Verwerfen?“ mit „Verwerfen“ und „Zurück“ (Vorgabe, auch mit Escape). „Zurück“ lässt Sie weiter bearbeiten.
Ergebnis:

[ ] 18. Geheimnisse bleiben weg
Tasten: Bei „README mit KI schreiben …“ eine Datei .env oder ein Bild hinzufügen, dann „Von KI verfassen lassen“.
Ansage: Am Ende „Die README von der KI ist da. Nicht an die KI gesendet: .env.“ (oder der Name des Bildes).
Ergebnis:
