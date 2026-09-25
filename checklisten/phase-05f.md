# Checkliste Phase 5f: Branches und beiseitegelegte Änderungen

Stand: 26.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- Bei Code gibt es „Branches …“: alle Branches mit ihrem Stand. Enter wechselt. Per Tab: „Neuer Branch …“, „In main übernehmen …“, „Umbenennen …“, „Löschen …“.
- Bei Code gibt es „Änderungen beiseitelegen …“ und, wenn etwas beiseitegelegt ist, „Beiseitegelegte Änderungen …“.
- Wechseln mit Änderungen ohne Commit fragt vorher: beiseitelegen, mitnehmen oder abbrechen.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten wählen Sie die Windows-Anmeldeinformationsverwaltung. Ein GitHub-Konto brauchen Sie nicht. Übernehmen Sie eine Git-Identität.
3. In den Testdaten hat PDF-Chat den Branch „suche-pdfs“ mit 2 Commits. Auf der „Plattform“ gibt es zusätzlich „neues-design“. In PDF-Chat sind main.py geändert und versuch.py neu. In Rezepte ist die Datei notiz.txt beiseitegelegt.
4. Die „Plattform“ ist ein Ordner auf Ihrem Rechner. Die Texte sagen trotzdem „GitHub“.

Bitte gehen Sie die Punkte der Reihe nach durch. Spätere Punkte bauen auf früheren auf.


## A. Aktionen bei Code

[ ] 1. Neue Aktionen
Tasten: Zu Code von PDF-Chat, Tab, durch die Aktionen. Dann zu Code von Rezepte, die Zeile lesen, Tab, durch die Aktionen.
Erwartet: Bei PDF-Chat steht „Branches …“ nach „Änderungen von GitHub holen …“. Dazu gibt es „Änderungen beiseitelegen …“. Die Zeile Code von Rezepte endet mit „Änderungen beiseitegelegt“, und dort gibt es „Beiseitegelegte Änderungen …“.
Ergebnis:


## B. Branches

[ ] 2. Übersicht
Tasten: Code von PDF-Chat, „Branches …“, Enter. Die Liste lesen, dann mit Tab durch die Knöpfe.
Erwartet: Das Fenster heißt „Branches von PDF-Chat: 3 Branches“. Oben steht „main, aktueller Branch, Haupt-Branch, 1 Commit auf GitHub noch nicht geholt“. Danach „suche-pdfs, 2 Commits vor main“ und „neues-design, 2 Commits vor main, nur auf GitHub“. Die Knöpfe sind „Wechseln“, „Neuer Branch …“, „In main übernehmen …“, „Umbenennen …“, „Löschen …“ und „Schließen“.
Ergebnis:

[ ] 3. Wechseln mit Änderungen, erst abbrechen
Tasten: Auf „suche-pdfs“ Enter. Die Frage lesen, Escape.
Erwartet: Die Frage beginnt mit „Sie haben Änderungen ohne Commit: 1 Datei geändert, 1 neue Datei.“ Sie erklärt Beiseitelegen und Mitnehmen. Die Knöpfe sind „Beiseitelegen und wechseln“, „Mitnehmen und wechseln“ und „Abbrechen“. Vorgabe ist „Abbrechen“. Nach Escape ist main weiter der aktuelle Branch.
Ergebnis:

[ ] 4. Beiseitelegen und wechseln
Tasten: Noch einmal Enter auf „suche-pdfs“, dann „Beiseitelegen und wechseln“.
Erwartet: NVDA sagt „Gewechselt zu suche-pdfs.“ Oben steht „suche-pdfs, aktueller Branch, 2 Commits vor main“, der Fokus steht darauf. Im Ordner Code liegt jetzt pdf_suche.py, und versuch.py ist weg.
Ergebnis:

[ ] 5. Zurück und zurückholen
Tasten: Auf „main“ Enter. Die Frage lesen, „Zurückholen“.
Erwartet: NVDA sagt „Gewechselt zu main.“ Dann fragt das Cockpit: „Auf main haben Sie am … Änderungen beiseitegelegt: 2 Dateien. Jetzt zurückholen?“ Vorgabe ist „Später“. Nach „Zurückholen“ sagt NVDA „Änderungen zurückgeholt.“ versuch.py ist wieder da.
Ergebnis:

[ ] 6. Mitnehmen zu einem Branch, den es nur auf GitHub gibt
Tasten: Auf „neues-design“ Enter, „Mitnehmen und wechseln“.
Erwartet: NVDA sagt „Gewechselt zu neues-design.“ Die Zeile heißt jetzt „neues-design, aktueller Branch, …“, ohne „nur auf GitHub“. Im Ordner liegt design.css, und versuch.py ist noch da.
Ergebnis:

[ ] 7. Neuer Branch
Tasten: Tab zu „Neuer Branch …“, Enter. Den Hinweis lesen. `mein test` eintippen, Enter. Nach der Meldung den Namen in `mein-test` ändern, Enter.
Erwartet: Das Feld heißt „Name des Branches“. Der Hinweis sagt: „Er beginnt bei neues-design. Ihre Änderungen ohne Commit kommen mit.“ Bei „mein test“ kommt „Der Name darf keine Leerzeichen enthalten …“, danach steht der Fokus wieder im Feld. Dann sagt NVDA „Branch mein-test angelegt. Sie sind jetzt auf mein-test.“ Die Zeile endet mit „noch nicht auf GitHub“.
Ergebnis:

[ ] 8. Umbenennen, nur hier
Tasten: Auf „mein-test“ Tab zu „Umbenennen …“. Den Namen in `mein-versuch` ändern, Enter.
Erwartet: Das Feld ist mit „mein-test“ vorbelegt. Es gibt keine Rückfrage, weil der Branch nur auf diesem Rechner liegt. NVDA sagt „mein-test heißt jetzt mein-versuch.“
Ergebnis:

[ ] 9. Löschen, nur hier
Tasten: Auf „main“ Enter, „Mitnehmen und wechseln“. Dann auf „mein-versuch“, „Löschen …“, die Frage lesen, „Löschen“.
Erwartet: Die Frage heißt „mein-versuch wird auf diesem Rechner gelöscht. Löschen?“ Vorgabe ist „Abbrechen“. Danach sagt NVDA „mein-versuch gelöscht.“ Den aktuellen Branch main kann man nicht löschen: Das sagt eine Meldung, wenn Sie es auf „main“ versuchen.
Ergebnis:

[ ] 10. In main übernehmen
Tasten: Auf „suche-pdfs“, Tab zu „In main übernehmen …“, Enter. Die Meldung lesen. Escape bis zur Aktionsliste. „Änderungen beiseitelegen …“, die Frage lesen, „Beiseitelegen“. Dann wieder „Branches …“, auf „suche-pdfs“, „In main übernehmen …“, „Übernehmen“.
Erwartet: Zuerst sagt eine Meldung, dass es Änderungen ohne Commit gibt. Die Frage beim Beiseitelegen nennt die Änderungen und die Sicherheitskopie, danach sagt NVDA „Änderungen beiseitegelegt.“ Beim Übernehmen fragt das Cockpit: „Die 2 Commits aus suche-pdfs kommen in main, wie git merge …“. Vorgabe ist „Abbrechen“. Danach sagt NVDA „suche-pdfs ist in main übernommen. main ist noch nicht hochgeladen.“ Die Zeile von suche-pdfs sagt jetzt „gleich wie main“.
Ergebnis:

[ ] 11. Umbenennen auch auf GitHub
Tasten: Auf „suche-pdfs“, „Umbenennen …“, `pdf-suche` eintippen, Enter. Die Frage lesen, „Umbenennen“.
Erwartet: Die Frage sagt, dass es suche-pdfs auch auf GitHub gibt, dass das Cockpit ihn dort unter dem neuen Namen hochlädt und den alten löscht, und dass offene Pull Requests zum alten Namen dabei geschlossen werden. NVDA sagt „Wird umbenannt.“ und danach „suche-pdfs heißt jetzt pdf-suche, auch auf GitHub.“
Ergebnis:

[ ] 12. Löschen hier und auf GitHub
Tasten: Auf „pdf-suche“, „Löschen …“, „Hier und auf GitHub“.
Erwartet: Die Knöpfe sind „Nur auf diesem Rechner“, „Hier und auf GitHub“ und „Abbrechen“. Vorgabe ist „Abbrechen“. NVDA sagt „Wird gelöscht.“ und danach „pdf-suche gelöscht, auch auf GitHub.“ Die Zeile ist weg.
Ergebnis:


## C. Beiseitegelegte Änderungen

[ ] 13. Zurückholen
Tasten: Fenster Branches schließen. Bei Code von PDF-Chat „Beiseitegelegte Änderungen …“, Enter. Die Liste lesen. Tab zu „Zurückholen …“, Enter, „Zurückholen“.
Erwartet: Das Fenster heißt „Beiseitegelegte Änderungen von PDF-Chat: 1 Eintrag“. Die Zeile beginnt mit Datum und Uhrzeit, dann „auf main, 2 Dateien: main.py und versuch.py“. Die Frage nennt die Dateien, Vorgabe ist „Abbrechen“. Danach sagt NVDA „Änderungen zurückgeholt.“ Die Liste sagt „Nichts beiseitegelegt.“
Ergebnis:

[ ] 14. Löschen abbrechen, dann als neuen Branch zurückholen
Tasten: Bei Code von Rezepte „Beiseitegelegte Änderungen …“. „Löschen …“, die Frage lesen, Escape. Dann „Als neuen Branch zurückholen …“, den vorgeschlagenen Namen lesen, Enter.
Erwartet: Die Zeile nennt „auf main, 1 Datei: notiz.txt“. Die Frage beim Löschen sagt, dass die Dateien vorher als Sicherheitskopie in den Ordner backups kommen. Vorgabe ist „Abbrechen“. Der vorgeschlagene Name beginnt mit „beiseitegelegt-“ und dem heutigen Datum. Danach sagt NVDA „Zurückgeholt in den neuen Branch … Sie sind jetzt dort.“ notiz.txt liegt wieder im Ordner. Code von Rezepte nennt jetzt den neuen Branch.
Ergebnis:
