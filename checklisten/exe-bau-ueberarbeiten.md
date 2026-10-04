# Checkliste: Exe bauen in Schritten, Ordner je Exe, Lizenz, Update, Branch löschen

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\exe-bau-ueberarbeiten. Nehmen Sie für die Exe die Vokabel-App.


## Lizenz

[ ] 1. Lizenz auf der Projektzeile
Tasten: Projektzeile der Vokabel-App, Tab in die Aktionen.
Ansage: Nach „README …“ steht „Lizenz …, MIT“ oder „Lizenz …, noch keine Lizenz“.
Ergebnis:

[ ] 2. Ohne Lizenz
Tasten: Bei einem Projekt ohne Lizenz „Lizenz …“, Enter.
Ansage: Liste „Lizenz“ mit „Lizenz auswählen …“ und „Lizenz aus Ordner hochladen …“.
Ergebnis:

[ ] 3. Lizenz auswählen
Tasten: „Lizenz auswählen …“, zum Beispiel MIT, Enter.
Ansage: Rückfrage „Die Lizenz MIT wird als LICENSE in den Ordner Code geschrieben, mit dem Namen … und dem Jahr 2026. Schreiben?“, Vorgabe „Abbrechen“. Nach „Schreiben“: „Lizenz gespeichert: MIT.“ Der Eintrag heißt jetzt „Lizenz …, MIT“.
Ergebnis:

[ ] 4. Mit Lizenz
Tasten: „Lizenz …“, Enter.
Ansage: Liste mit „Lizenz ansehen“ und „Lizenz ändern …“. „Lizenz ansehen“ zeigt den Text. „Lizenz ändern …“ bietet wieder Auswählen und Hochladen an, die bisherige kommt in die Sicherheitskopien.
Ergebnis:


## Exe aus dem Code erstellen

[ ] 5. Warnung bei fehlender README oder Lizenz
Tasten: Bei einem Projekt ohne Lizenz „Exe aus dem Code erstellen …“.
Ansage: „Bei … fehlt Lizenz. README und Lizenz gehören neben die Exe und ins Repository.“ Knöpfe „Jetzt hinzufügen“ (Vorgabe), „Ignorieren und weiter“, „Abbrechen“ (Escape). „Jetzt hinzufügen“ schließt die Frage, die Projektzeile ist markiert und der Fokus steht in den Aktionen auf „Lizenz …“.
Ergebnis:

[ ] 6. Schritt 1: Dateien neben der Exe
Tasten: Bei der Vokabel-App „Exe aus dem Code erstellen …“.
Ansage: Titel „Exe aus dem Code erstellen: VokabelApp, Schritt 1: Dateien neben der Exe“. Fokus in der Liste. Oben „Meine-Vokabeln, unbedingt nötig, vom Code benutzt“, angehakt. Unten „README.md, kommt immer mit“ und „LICENSE, kommt immer mit“, ohne Kästchen.
Ergebnis:

[ ] 7. Schritt 2: Mit oder ohne KI
Tasten: Weiter.
Ansage: Titel „…, Schritt 2: Mit oder ohne KI“. NVDA liest „Sie können den Vorgang der Exe-Erstellung mit oder ohne KI durchführen. …“. Liste „Exe bauen“ mit „Mit KI-Unterstützung die Exe bauen“ oben und „Ohne KI die Exe bauen“. Knöpfe „Zurück“, „Weiter“, „Abbrechen“. „Zurück“ führt zu Schritt 1, Ihre Auswahl ist noch da.
Ergebnis:

[ ] 8. Schritt 3: Einrichtung
Tasten: „Mit KI-Unterstützung die Exe bauen“, Weiter.
Ansage: Titel „…, Schritt 3: Einrichtung“. Liste „Fortschritt“ mit „Branch Cockpit-exe-bauen wird vorbereitet.“ und den gelesenen Dateien. Keine Rückfrage zum Branch. Knöpfe „Zurück“ und „Abbrechen“.
Ergebnis:

[ ] 9. Main bleibt unverändert
Tasten: Nach Schritt 3 bei Code „Änderungen auf GitHub hochladen …“ ansehen (nicht hochladen) oder die Zeile von main lesen.
Ansage: Main hat keine neuen Änderungen, auch cockpit.toml ist nicht geändert. Die Einstellungen stehen im Branch Cockpit-exe-bauen.
Ergebnis:

[ ] 10. Schritt 4: Zusammenfassung
Tasten: Abwarten.
Ansage: Titel „…, Schritt 4: Zusammenfassung“. Die erste Zeile wird angesagt. Liste „Zusammenfassung“: was die KI vorschlägt, „Gebaut wird im Branch Cockpit-exe-bauen …“, was neben die Exe kommt, und „Die neue Exe kommt in den Ordner Exe\VokabelApp_branch_Cockpit-exe-bauen …“. Enter auf einer Änderung zeigt alten und neuen Text. Ein Feld für Fragen gibt es noch nicht.
Ergebnis:

[ ] 11. Mit KI schreiben
Tasten: Tab bis „Mit KI schreiben“, Enter.
Ansage: Der Fokus steht im Feld „Frage an die KI“. Darunter die Liste „Gespräch mit der KI“, dazu der Knopf „Mit den Hinweisen wiederholen“. „Mit KI schreiben“ ist verschwunden.
Ergebnis:

[ ] 12. Antwort erst in Sätzen
Tasten: Eine Frage stellen, zum Beispiel „Wie liest der Code den Ordner Meine-Vokabeln?“, Enter.
Ansage: „Antwort da.“ In der Liste zuerst verständliche Sätze, je Satz eine Zeile. Wenn die KI Code zeigt, kommt danach eine Zeile „Code:“ und dann der Code Zeile für Zeile. Nie nur Code.
Ergebnis:

[ ] 13. Schritte 5 und 6: Bau und Ergebnis
Tasten: „Exe erstellen“.
Ansage: Titel „…, Schritt 5: Exe wird gebaut“, die Schritte 1 bis 4 werden angesagt. Danach Titel „…, Schritt 6: Ergebnis“ und „Exe aus dem Branch erstellt und getestet: Ordner Exe\VokabelApp_branch_Cockpit-exe-bauen.“ Knöpfe „Erst testen, später in main überführen und Release veröffentlichen“, „Jetzt in main überführen und Release veröffentlichen“, „Jetzt in main überführen, später veröffentlichen“.
Ergebnis:

[ ] 14. Eigener Ordner der Exe
Tasten: Im Explorer den Ordner Exe der Vokabel-App ansehen.
Ansage: Es gibt den Ordner VokabelApp_branch_Cockpit-exe-bauen mit VokabelApp.exe, README.md, LICENSE und Meine-Vokabeln.
Ergebnis:

[ ] 15. Erst testen
Tasten: „Erst testen, später …“.
Ansage: Der Explorer öffnet den Ordner der neuen Exe. Ansage „Der Branch Cockpit-exe-bauen bleibt. Wenn die Exe passt, wählen Sie bei Exe „Exe-Bau abschließen …“.“
Ergebnis:

[ ] 16. Exe-Bau abschließen
Tasten: Bei Exe „Exe-Bau abschließen …“.
Ansage: Liste „Wie geht es weiter?“ mit „Jetzt in main überführen und Release veröffentlichen“, „Jetzt in main überführen, später veröffentlichen“, „Ordner der neuen Exe im Explorer öffnen“ und „Exe-Bau verwerfen …“.
Ergebnis:

[ ] 17. In main überführen
Tasten: „Jetzt in main überführen, später veröffentlichen“.
Ansage: „Cockpit-exe-bauen ist in main überführt. Main ist noch nicht hochgeladen. Die Exe aus dem Branch ist jetzt die normale Exe. Der Branch Cockpit-exe-bauen ist gelöscht.“ Im Ordner Exe liegt jetzt Exe\VokabelApp mit der neuen Exe. Ihre eigenen Vokabellisten in Meine-Vokabeln sind noch da. „Exe-Bau abschließen …“ ist verschwunden.
Ergebnis:

[ ] 18. Fehler beim Bau
Tasten: Einen Bau scheitern lassen, zum Beispiel mit einer falschen Startdatei in Schritt 1.
Ansage: In Schritt 6 „Fehler: …“ und die Knöpfe „Problem mit KI lösen“ (nur mit KI), „Neuer Versuch, Exe zu bauen“, „Zurück“, „Abbrechen“. „Problem mit KI lösen“ führt zu Schritt 3 („Die KI versucht, das Problem zu lösen“) und dann zur Zusammenfassung mit dem Knopf „Neuer Versuch, Exe zu bauen“.
Ergebnis:

[ ] 19. Abbrechen
Tasten: In einem neuen Durchgang in Schritt 4 „Abbrechen“.
Ansage: Rückfrage „Den Exe-Bau abbrechen? Der Branch Cockpit-exe-bauen und eine darin gebaute Exe werden gelöscht. Main bleibt, wie es war.“ Vorgabe und Escape „Zurück“. Nach „Abbrechen und löschen“: „Exe-Bau verworfen. Main ist, wie es war.“ Main hat keine Änderungen.
Ergebnis:

[ ] 20. Ohne KI
Tasten: „Exe aus dem Code erstellen …“, in Schritt 2 „Ohne KI die Exe bauen“.
Ansage: Gleiche Schritte, aber ohne „Mit KI schreiben“ und ohne „Problem mit KI lösen“. Gebaut wird auch hier im Branch Cockpit-exe-bauen.
Ergebnis:


## Veröffentlichen

[ ] 21. Release mit Ordner und Version
Tasten: „Jetzt in main überführen und Release veröffentlichen“ oder „Exe veröffentlichen …“, Version eingeben, Veröffentlichen.
Ansage: Die Rückfrage nennt „Angehängt wird VokabelApp.zip (… MB) mit dem ganzen Ordner der Exe, darin der Ordner VokabelApp-1.x.y. Dazu einzeln: LICENSE, README.md.“ Auf GitHub hängen VokabelApp.zip, README.md und LICENSE am Release. In der ZIP-Datei liegt der Ordner VokabelApp-1.x.y mit Exe, README, Lizenz und Meine-Vokabeln.
Ergebnis:


## Update des Cockpits

[ ] 22. Suche bei jedem Start
Tasten: Das Cockpit als Exe zweimal hintereinander starten.
Ansage: Gibt es eine neue Version, kommt die Frage nach dem Update bei jedem Start, nicht nur einmal am Tag.
Ergebnis:

[ ] 23. README und Lizenz beim Update
Tasten: Ein Update installieren.
Ansage: Neben der neuen Exe liegen danach die README und die Lizenz aus dem Release. Andere Dateien neben der Exe sind unverändert.
Ergebnis:


## Branches

[ ] 24. Kein „Branch-Ordner entfernen“ mehr
Tasten: „Branches verwalten“ oder „<Branch> verwalten …“, einen Branch markieren, Tab durch die Knöpfe.
Ansage: „In main übernehmen …“, „Umbenennen …“, „Löschen …“. „Branch-Ordner entfernen …“ gibt es nicht mehr.
Ergebnis:

[ ] 25. Löschen bringt nichts nach main
Tasten: In einem Branch etwas ändern, ohne Commit. Dann den Branch löschen.
Ansage: Die Rückfrage sagt, dass Änderungen verworfen werden und nicht nach main kommen. Danach zeigt main keine neuen Änderungen.
Ergebnis:
