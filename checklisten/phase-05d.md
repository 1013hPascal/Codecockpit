# Checkliste Phase 5d: Verlauf und Rückgängig machen

Stand: 25.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- Bei Code gibt es „Verlauf …“ und „Änderungen verwerfen …“.
- Im Verlauf zeigt Enter die Details einer Version. Dort gibt es „Datei wiederherstellen …“ und „Version rückgängig machen …“.
- Beim neuesten Commit, solange er noch nicht hochgeladen ist, gibt es zusätzlich „Commit zurücknehmen …“. Das ist wie „Undo“ in GitHub Desktop.
- Vor allem, was Dateien verändert, kommt eine Sicherheitskopie in den Ordner backups. Sie finden sie im Menü Datei unter „Sicherheitskopien …“.
- Neue Dateien löscht das Cockpit beim Verwerfen nicht, sondern verschiebt sie in den Papierkorb von Windows.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten wählen Sie die Windows-Anmeldeinformationsverwaltung. Ein GitHub-Konto brauchen Sie für diese Checkliste nicht. Übernehmen Sie aber eine Git-Identität, zum Beispiel die noreply-Adresse.
3. In den Testdaten hat PDF-Chat jetzt einen Verlauf mit fünf Versionen. Dazu sind main.py geändert und versuch.py neu, beides noch nicht hochgeladen. In Rezepte gibt es den Commit „Rezept geändert“, der noch nicht hochgeladen ist.

Bitte gehen Sie die Punkte der Reihe nach durch. Spätere Punkte bauen auf früheren auf.


## A. Aktionen bei Code

[ ] 1. Aktionen bei PDF-Chat
Tasten: In der Projektliste zu PDF-Chat, Pfeil rechts, Pfeil runter auf Code. Dann Tab und mit den Pfeiltasten durch die Aktionen.
Erwartet: Die Zeile heißt „Code, 2 Dateien noch nicht hochgeladen, 1 Änderung auf GitHub noch nicht geholt“. Die Aktionen beginnen mit „Projekt neu einlesen“, „Änderungen hochladen …“, „Änderungen von GitHub holen …“, „Verlauf …“, „Änderungen verwerfen …“.
Ergebnis:

[ ] 2. Verwerfen nicht verfügbar
Tasten: Zu Code von Rezepte, Tab, zu „Änderungen verwerfen“.
Erwartet: Die Zeile heißt „Änderungen verwerfen …, nicht verfügbar: Es gibt keine Änderungen ohne Commit.“ Enter sagt dasselbe und ändert nichts.
Ergebnis:


## B. Verlauf

[ ] 3. Verlauf öffnen
Tasten: Zu Code von PDF-Chat, Tab, „Verlauf …“, Enter.
Erwartet: Das Fenster heißt „Verlauf von PDF-Chat: 5 Versionen“. Der Fokus steht in der Liste auf der obersten Zeile. Die Zeilen von oben:
- „23.09.2026: Hilfetext geändert“
- „22.09.2026: Alte Datei entfernt“
- „21.09.2026: Einstellungen ergänzt“
- „20.09.2026, Version 1.0.0: Hilfe ergänzt“
- „19.09.2026: Erste Version“
Ergebnis:

[ ] 4. Details einer Version
Tasten: Auf „21.09.2026: Einstellungen ergänzt“ Enter. In der Liste Angaben mit den Pfeiltasten lesen. Dann Tab, die Liste der Dateien lesen. Dann weiter mit Tab durch die Knöpfe. Escape.
Erwartet: Das Fenster heißt wie die Zeile. Der Fokus steht in der Liste „Angaben“ auf „Nachricht: Einstellungen ergänzt“. Darunter „Von Testdaten am 21.09.2026 um 11:30 Uhr“ und „Commit“ mit einer kurzen Kennung. Die zweite Liste heißt „Dateien, 1 Datei geändert, 1 neue Datei“ mit „main.py, geändert“ und „einstellungen.py, neu“. Die Knöpfe sind „Datei wiederherstellen …“, „Version rückgängig machen …“ und „Schließen“. „Commit zurücknehmen“ gibt es hier nicht. Escape führt zurück in den Verlauf, der Fokus steht wieder auf „Einstellungen ergänzt“.
Ergebnis:

[ ] 5. Details mit dem Knopf
Tasten: Im Verlauf Tab zu „Details anzeigen …“, Enter. Dann Escape.
Erwartet: Es öffnen sich die Details der markierten Version, wie in Punkt 4.
Ergebnis:


## C. Datei wiederherstellen

[ ] 6. Gelöschte Datei, erst abbrechen
Tasten: Im Verlauf auf „Alte Datei entfernt“ Enter. Tab zur Liste der Dateien, dort steht „alt.py, gelöscht“. Tab zu „Datei wiederherstellen …“, Enter. Die Frage lesen, dann Escape.
Erwartet: Die Frage sagt: „alt.py wurde in der Version vom 22.09.2026 „Alte Datei entfernt“ gelöscht. Die Datei kommt mit dem Stand direkt davor zurück. Danach ist das eine normale Änderung, die Sie wie gewohnt hochladen. Wiederherstellen?“ Vorgabe ist „Abbrechen“. Nach Escape ist nichts passiert.
Ergebnis:

[ ] 7. Gelöschte Datei wiederherstellen
Tasten: Noch einmal „Datei wiederherstellen …“, dann „Wiederherstellen“.
Erwartet: NVDA sagt „alt.py wiederhergestellt.“ Der Fokus steht in der Liste der Dateien. Im Ordner Code von PDF-Chat liegt wieder alt.py.
Ergebnis:

[ ] 8. Vorhandene Datei wiederherstellen
Tasten: Escape zurück in den Verlauf. Auf „Erste Version“ Enter. In der Liste der Dateien zu „main.py, neu“. „Datei wiederherstellen …“, „Wiederherstellen“. Dann Escape, noch einmal Escape.
Erwartet: Die Frage sagt zusätzlich: „Die jetzige Datei kommt vorher als Sicherheitskopie in den Ordner backups.“ Danach sagt NVDA „main.py wiederhergestellt.“ In main.py steht wieder `print('PDF-Chat')`.
Ergebnis:


## D. Version rückgängig machen

[ ] 9. Geht nicht von selbst
Tasten: Verlauf von PDF-Chat öffnen. Auf „Version 1.0.0: Hilfe ergänzt“ Enter. „Version rückgängig machen …“, „Rückgängig machen“.
Erwartet: Die Frage beginnt mit „Das Cockpit erstellt einen neuen Commit „Rückgängig: Hilfe ergänzt“.“ Danach kommt eine Meldung: Die Version lässt sich nicht von selbst rückgängig machen, weil spätere Versionen dieselben Stellen geändert haben. Es wurde nichts verändert. Der Verlauf hat weiter 5 Versionen.
Ergebnis:

[ ] 10. Eigene Änderungen im Weg
Tasten: Details von „Einstellungen ergänzt“. „Version rückgängig machen …“, „Rückgängig machen“.
Erwartet: Eine Meldung sagt: „In main.py gibt es Änderungen ohne Commit. Bitte laden Sie sie zuerst hoch oder verwerfen Sie sie.“ Es wurde nichts verändert.
Ergebnis:

[ ] 11. Erste Version
Tasten: Details von „Erste Version“. „Version rückgängig machen …“.
Erwartet: Ohne Rückfrage kommt die Meldung „Das ist die erste Version. Sie lässt sich nicht rückgängig machen.“
Ergebnis:

[ ] 12. Version rückgängig machen
Tasten: Details von „Hilfetext geändert“. „Version rückgängig machen …“, die Frage lesen, „Rückgängig machen“.
Erwartet: Die Frage sagt, dass ein neuer Commit „Rückgängig: Hilfetext geändert“ entsteht, der Verlauf vollständig erhalten bleibt, vorher eine Sicherheitskopie entsteht und der neue Commit noch nicht hochgeladen ist. Vorgabe ist „Abbrechen“. Danach schließen sich die Details. NVDA sagt „Rückgängig gemacht. Neuer Commit „Rückgängig: Hilfetext geändert“.“ Der Verlauf heißt jetzt „… 6 Versionen“. Oben steht „25.09.2026: Rückgängig: Hilfetext geändert, noch nicht hochgeladen“, der Fokus steht darauf. In hilfe.py steht wieder `print('Hilfe')`.
Ergebnis:


## E. Commit zurücknehmen

[ ] 13. Commit zurücknehmen in Rezepte
Tasten: Verlauf schließen. Zu Code von Rezepte, „Verlauf …“. Oben steht „…: Rezept geändert, noch nicht hochgeladen“. Enter, dann mit Tab zu „Commit zurücknehmen …“, Enter, „Zurücknehmen“.
Erwartet: Die Frage sagt, dass der Commit zurückgenommen wird, die Änderungen in den Dateien bleiben und keine Datei verändert wird. Vorgabe ist „Abbrechen“. Danach sagt NVDA „Commit zurückgenommen. Die Änderungen sind noch da, ohne Commit.“ Im Verlauf steht oben jetzt „Erste Version“. Nach dem Schließen heißt Code von Rezepte „Code, 1 Datei noch nicht hochgeladen, …“.
Ergebnis:

[ ] 14. Kein Zurücknehmen bei hochgeladenen Commits
Tasten: Verlauf von PDF-Chat, Details von „Alte Datei entfernt“, mit Tab durch die Knöpfe.
Erwartet: „Commit zurücknehmen …“ gibt es nicht, weil die Version schon hochgeladen ist. Bei „Rückgängig: Hilfetext geändert“ ganz oben gibt es den Knopf.
Ergebnis:


## F. Änderungen verwerfen

[ ] 15. Liste mit Kontrollkästchen
Tasten: Zu Code von PDF-Chat, „Änderungen verwerfen …“, Enter. Mit den Pfeiltasten lesen. Auf einer Zeile Leertaste, dann noch einmal Leertaste.
Erwartet: Das Fenster heißt „Änderungen verwerfen in PDF-Chat: 3 Änderungen“. Die Zeilen sind „alt.py, neu“, „main.py, geändert“ und „versuch.py, neu“. Alle sind „nicht aktiviert“. Die Leertaste schaltet um.
Ergebnis:

[ ] 16. Nichts ausgewählt
Tasten: Alle Kästchen leer lassen. Tab zu „Verwerfen …“, Enter.
Erwartet: Eine Meldung sagt „Bitte wählen Sie mit der Leertaste mindestens eine Datei aus.“ Nach OK steht der Fokus in der Liste.
Ergebnis:

[ ] 17. Alle auswählen
Tasten: Tab zu „Alle auswählen“, Enter. Zurück in die Liste und lesen. Dann „Alle abwählen“.
Erwartet: Alle Zeilen sind „aktiviert“. Der Knopf heißt danach „Alle abwählen“. Damit sind wieder alle leer.
Ergebnis:

[ ] 18. Verwerfen, erst abbrechen
Tasten: main.py und versuch.py mit der Leertaste auswählen. „Verwerfen …“, die Frage lesen, Escape.
Erwartet: Die Frage sagt: „1 Datei kommt auf den Stand des letzten Commits zurück: main.py. 1 neue Datei kommt in den Papierkorb: versuch.py. Vorher kommen die Dateien als Sicherheitskopie in den Ordner backups. Verwerfen?“ Vorgabe ist „Abbrechen“. Nach Escape ist das Fenster noch offen und nichts ist verändert.
Ergebnis:

[ ] 19. Verwerfen
Tasten: Noch einmal „Verwerfen …“, dann „Verwerfen“.
Erwartet: Das Fenster schließt sich. NVDA sagt „2 Änderungen verworfen.“ versuch.py liegt im Papierkorb von Windows. main.py hat wieder den Stand des letzten Commits. Code von PDF-Chat nennt jetzt nur noch alt.py als nicht hochgeladen: „Code, 2 Dateien noch nicht hochgeladen, …“. Die zweite Datei ist der Commit „Rückgängig: Hilfetext geändert“, der noch nicht hochgeladen ist.
Ergebnis:


## G. Sicherheitskopien

[ ] 20. Neue Sicherheitskopien
Tasten: Alt+D, dann S. Die obersten Zeilen lesen.
Erwartet: Oben stehen Kopien zu PDF-Chat mit den Anlässen „vor dem Verwerfen, 2 Dateien“, „vor dem Rückgängigmachen, 1 Datei“ und „vor dem Wiederherstellen, 1 Datei“.
Ergebnis:

[ ] 21. Verworfene Datei zurückholen
Tasten: Auf „vor dem Verwerfen“ „Dateien anzeigen …“. Auf versuch.py „Wiederherstellen …“, „Wiederherstellen“.
Erwartet: NVDA sagt „versuch.py wiederhergestellt.“ Die Datei liegt wieder im Ordner Code von PDF-Chat.
Ergebnis:
