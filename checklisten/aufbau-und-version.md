# Checkliste: Aufbau Code\main und Exe, Exe-Ordner mit Version, Update, Anzeige beim Hochladen

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\projekt-aufbau-und-version.


## Aufbau des Projekts

[ ] 1. Chatbot für Text reparieren
Tasten: Projektzeile „Chatbot für Text“, Aktion „Projekt neu einlesen“.
Ansage: Rückfrage „Bei Chatbot für Text liegt der Code in Code\main, der Git-Ordner .git aber noch direkt in Code. … Verschieben?“ mit „Verschieben“ und „So lassen“ (Vorgabe, auch mit Escape). Nach „Verschieben“: „Der Code liegt jetzt in Code\main.“ In der Liste steht unter dem Projekt jetzt „Code, main“.
Ergebnis:

[ ] 2. Titel beim Hinzufügen
Tasten: „Projekt vom Rechner hinzufügen“, Enter.
Ansage: Der Ordner-Dialog von Windows heißt „Projektordner wählen, darin Code und Exe, in Code der Ordner main“.
Ergebnis:

[ ] 3. Code direkt in Code
Tasten: Einen Projektordner wählen, in dem der Code direkt in Code liegt.
Ansage: Rückfrage „Bei … liegt der Code direkt im Ordner Code. Richtig ist Projektordner, darin Code und Exe, und in Code der Ordner main mit dem Code. …“. Nach dem Bestätigen liegt der Code in Code\main (mit Git: im Ordner, der wie der Branch heißt). „So lassen“ ändert nichts.
Ergebnis:

[ ] 4. Ordner Exe
Tasten: Ein Projekt ohne Ordner Exe hinzufügen.
Ansage: „Ordner Exe angelegt.“ Neben Code gibt es jetzt den Ordner Exe, in der Liste steht „Exe“.
Ergebnis:

[ ] 5. Ordner ohne Code
Tasten: Einen Ordner ohne Unterordner Code wählen, „In den Projekte-Hauptordner verschieben …“.
Ansage: Die Rückfrage nennt den Zielordner …\Code\main und sagt „Daneben entsteht der Ordner …\Exe.“
Ergebnis:


## Exe-Ordner mit Version

[ ] 6. Ordner nach dem Veröffentlichen
Tasten: Bei der Vokabel-App „Exe veröffentlichen …“, Version eingeben, Veröffentlichen.
Ansage: Während des Hochladens steht bei „Exe veröffentlichen …“ „wird gerade hochgeladen“. Danach „Version … veröffentlicht. Link kopiert. Die Exe liegt jetzt in Exe\VokabelApp-v….“ Im Ordner liegt version.txt mit der Nummer.
Ergebnis:

[ ] 7. Release-ZIP
Tasten: Die ZIP-Datei vom Release laden und öffnen.
Ansage: Darin liegt der Ordner VokabelApp-v… mit der Exe, README, Lizenz, Meine-Vokabeln und version.txt.
Ergebnis:

[ ] 8. Neuer Bau neben der alten Version
Tasten: Die Exe neu bauen und in main überführen.
Ansage: Die neue Exe liegt in Exe\VokabelApp, der Ordner Exe\VokabelApp-v… bleibt. Ihre eigenen Vokabellisten sind in der neuen Exe da.
Ergebnis:


## Update

[ ] 9. Keine eigene Version als Update
Tasten: Das Cockpit veröffentlichen und danach die neue Exe starten.
Ansage: Es kommt keine Frage nach einem Update auf dieselbe Version. Hilfe, „Nach Updates suchen“ sagt, dass Sie aktuell sind.
Ergebnis:

[ ] 10. Höhere Version
Tasten: Eine ältere Exe des Cockpits starten, wenn es ein neueres Release gibt.
Ansage: Die Frage nach dem Update kommt. Nach dem Update liegen version.txt, README und Lizenz neu neben der Exe.
Ergebnis:
