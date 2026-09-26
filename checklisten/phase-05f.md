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

[x] 1. Neue Aktionen
Tasten: Zu Code von PDF-Chat, Tab, durch die Aktionen. Dann zu Code von Rezepte, die Zeile lesen, Tab, durch die Aktionen.
Erwartet: Bei PDF-Chat steht „Branches …“ nach „Änderungen von GitHub holen …“. Dazu gibt es „Änderungen beiseitelegen …“. Die Zeile Code von Rezepte endet mit „Änderungen beiseitegelegt“, und dort gibt es „Beiseitegelegte Änderungen …“.
Ergebnis:


## B. Branches

[?] 2. Übersicht
Tasten: Code von PDF-Chat, „Branches …“, Enter. Die Liste lesen, dann mit Tab durch die Knöpfe.
Erwartet: Das Fenster heißt „Branches von PDF-Chat: 3 Branches“. Oben steht „main, aktueller Branch, Haupt-Branch, 1 Commit auf GitHub noch nicht geholt“. Danach „suche-pdfs, 2 Commits vor main“ und „neues-design, 2 Commits vor main, nur auf GitHub“. Die Knöpfe sind „Wechseln“, „Neuer Branch …“, „In main übernehmen …“, „Umbenennen …“, „Löschen …“ und „Schließen“.
Ergebnis: beim main branch, muss in main übernehmen eigentlich nicht sein de rschalter oder? Ansonsten super!

Antwort von Claude: Stimmt. Umgesetzt: Die Knöpfe richten sich jetzt nach der markierten Zeile. Beim Haupt-Branch main gibt es „In main übernehmen …“, „Umbenennen …“ und „Löschen …“ nicht. Beim aktuellen Branch fehlt „Löschen …“. Die Knöpfe verschwinden, statt ausgegraut zu sein, weil Tab ausgegraute Knöpfe überspringt.

[x] 3. Wechseln mit Änderungen, erst abbrechen
Tasten: Auf „suche-pdfs“ Enter. Die Frage lesen, Escape.
Erwartet: Die Frage beginnt mit „Sie haben Änderungen ohne Commit: 1 Datei geändert, 1 neue Datei.“ Sie erklärt Beiseitelegen und Mitnehmen. Die Knöpfe sind „Beiseitelegen und wechseln“, „Mitnehmen und wechseln“ und „Abbrechen“. Vorgabe ist „Abbrechen“. Nach Escape ist main weiter der aktuelle Branch.
Ergebnis:

[x] 4. Beiseitelegen und wechseln
Tasten: Noch einmal Enter auf „suche-pdfs“, dann „Beiseitelegen und wechseln“.
Erwartet: NVDA sagt „Gewechselt zu suche-pdfs.“ Oben steht „suche-pdfs, aktueller Branch, 2 Commits vor main“, der Fokus steht darauf. Im Ordner Code liegt jetzt pdf_suche.py, und versuch.py ist weg.
Ergebnis:

[x] 5. Zurück und zurückholen
Tasten: Auf „main“ Enter. Die Frage lesen, „Zurückholen“.
Erwartet: NVDA sagt „Gewechselt zu main.“ Dann fragt das Cockpit: „Auf main haben Sie am … Änderungen beiseitegelegt: 2 Dateien. Jetzt zurückholen?“ Vorgabe ist „Später“. Nach „Zurückholen“ sagt NVDA „Änderungen zurückgeholt.“ versuch.py ist wieder da.
Ergebnis:

[x] 6. Mitnehmen zu einem Branch, den es nur auf GitHub gibt
Tasten: Auf „neues-design“ Enter, „Mitnehmen und wechseln“.
Erwartet: NVDA sagt „Gewechselt zu neues-design.“ Die Zeile heißt jetzt „neues-design, aktueller Branch, …“, ohne „nur auf GitHub“. Im Ordner liegt design.css, und versuch.py ist noch da.
Ergebnis:

[x] 7. Neuer Branch
Tasten: Tab zu „Neuer Branch …“, Enter. Den Hinweis lesen. `mein test` eintippen, Enter. Nach der Meldung den Namen in `mein-test` ändern, Enter.
Erwartet: Das Feld heißt „Name des Branches“. Der Hinweis sagt: „Er beginnt bei neues-design. Ihre Änderungen ohne Commit kommen mit.“ Bei „mein test“ kommt „Der Name darf keine Leerzeichen enthalten …“, danach steht der Fokus wieder im Feld. Dann sagt NVDA „Branch mein-test angelegt. Sie sind jetzt auf mein-test.“ Die Zeile endet mit „noch nicht auf GitHub“.
Ergebnis:

[x] 8. Umbenennen, nur hier
Tasten: Auf „mein-test“ Tab zu „Umbenennen …“. Den Namen in `mein-versuch` ändern, Enter.
Erwartet: Das Feld ist mit „mein-test“ vorbelegt. Es gibt keine Rückfrage, weil der Branch nur auf diesem Rechner liegt. NVDA sagt „mein-test heißt jetzt mein-versuch.“
Ergebnis:

[?] 9. Löschen, nur hier
Tasten: Auf „main“ Enter, „Mitnehmen und wechseln“. Dann auf „mein-versuch“, „Löschen …“, die Frage lesen, „Löschen“.
Erwartet: Die Frage heißt „mein-versuch wird auf diesem Rechner gelöscht. Löschen?“ Vorgabe ist „Abbrechen“. Danach sagt NVDA „mein-versuch gelöscht.“ Den aktuellen Branch main kann man nicht löschen: Das sagt eine Meldung, wenn Sie es auf „main“ versuchen.
Ergebnis: Also main war aktuell ausgewählt. ich hab bei mein-versuch tab gedrück auf löschen, und das ging auch. War das so richtig. 
Ich check nicht, soll man nur branches löschen können, die man gerade aktiviert hat oder immer?

Antwort von Claude: Ja, genau so ist es richtig. Löschen geht bei jedem Branch außer dem, auf dem Sie gerade sind, und außer main. Man markiert den Branch in der Liste, man muss ihn nicht erst aktivieren. Den Branch, auf dem man gerade ist, kann man nicht löschen, weil die Dateien im Ordner ja gerade seinen Stand zeigen. Das steht jetzt auch in der neuen Anleitung.

[x] 10. In main übernehmen
Tasten: Auf „suche-pdfs“, Tab zu „In main übernehmen …“, Enter. Die Meldung lesen. Escape bis zur Aktionsliste. „Änderungen beiseitelegen …“, die Frage lesen, „Beiseitelegen“. Dann wieder „Branches …“, auf „suche-pdfs“, „In main übernehmen …“, „Übernehmen“.
Erwartet: Zuerst sagt eine Meldung, dass es Änderungen ohne Commit gibt. Die Frage beim Beiseitelegen nennt die Änderungen und die Sicherheitskopie, danach sagt NVDA „Änderungen beiseitegelegt.“ Beim Übernehmen fragt das Cockpit: „Die 2 Commits aus suche-pdfs kommen in main, wie git merge …“. Vorgabe ist „Abbrechen“. Danach sagt NVDA „suche-pdfs ist in main übernommen. main ist noch nicht hochgeladen.“ Die Zeile von suche-pdfs sagt jetzt „gleich wie main“.
Ergebnis:

[x] 11. Umbenennen auch auf GitHub
Tasten: Auf „suche-pdfs“, „Umbenennen …“, `pdf-suche` eintippen, Enter. Die Frage lesen, „Umbenennen“.
Erwartet: Die Frage sagt, dass es suche-pdfs auch auf GitHub gibt, dass das Cockpit ihn dort unter dem neuen Namen hochlädt und den alten löscht, und dass offene Pull Requests zum alten Namen dabei geschlossen werden. NVDA sagt „Wird umbenannt.“ und danach „suche-pdfs heißt jetzt pdf-suche, auch auf GitHub.“
Ergebnis:, ok, ich verstehe nicht ganz, wie wo pdf-suche auf GitHub war, war das im selben projekt auch?

Antwort von Claude: Ja, im selben Projekt. Jedes Repository auf GitHub hat seine eigenen Branches. suche-pdfs war ein Branch des Repositories PDF-Chat, auf Ihrem Rechner und auf GitHub. In den Testdaten ist „GitHub“ der Ordner Testdaten\Plattform\PDF-Chat.git. Beim Umbenennen hat das Cockpit den Branch dort unter pdf-suche hochgeladen und suche-pdfs gelöscht.

[?] 12. Löschen hier und auf GitHub
Tasten: Auf „pdf-suche“, „Löschen …“, „Hier und auf GitHub“.
Erwartet: Die Knöpfe sind „Nur auf diesem Rechner“, „Hier und auf GitHub“ und „Abbrechen“. Vorgabe ist „Abbrechen“. NVDA sagt „Wird gelöscht.“ und danach „pdf-suche gelöscht, auch auf GitHub.“ Die Zeile ist weg.
Ergebnis: Warum kann man nicht nur auf GitHub entfernen, sondern nur auf dem rechner oder beides?

Antwort von Claude: Gute Idee, umgesetzt. Liegt ein Branch an beiden Orten, gibt es jetzt „Nur auf diesem Rechner“, „Nur auf GitHub“, „Hier und auf GitHub“ und „Abbrechen“. Vorgabe ist „Abbrechen“.


## C. Beiseitegelegte Änderungen

[x] 13. Zurückholen
Tasten: Fenster Branches schließen. Bei Code von PDF-Chat „Beiseitegelegte Änderungen …“, Enter. Die Liste lesen. Tab zu „Zurückholen …“, Enter, „Zurückholen“.
Erwartet: Das Fenster heißt „Beiseitegelegte Änderungen von PDF-Chat: 1 Eintrag“. Die Zeile beginnt mit Datum und Uhrzeit, dann „auf main, 2 Dateien: main.py und versuch.py“. Die Frage nennt die Dateien, Vorgabe ist „Abbrechen“. Danach sagt NVDA „Änderungen zurückgeholt.“ Die Liste sagt „Nichts beiseitegelegt.“
Ergebnis:

[x] 14. Löschen abbrechen, dann als neuen Branch zurückholen
Tasten: Bei Code von Rezepte „Beiseitegelegte Änderungen …“. „Löschen …“, die Frage lesen, Escape. Dann „Als neuen Branch zurückholen …“, den vorgeschlagenen Namen lesen, Enter.
Erwartet: Die Zeile nennt „auf main, 1 Datei: notiz.txt“. Die Frage beim Löschen sagt, dass die Dateien vorher als Sicherheitskopie in den Ordner backups kommen. Vorgabe ist „Abbrechen“. Der vorgeschlagene Name beginnt mit „beiseitegelegt-“ und dem heutigen Datum. Danach sagt NVDA „Zurückgeholt in den neuen Branch … Sie sind jetzt dort.“ notiz.txt liegt wieder im Ordner. Code von Rezepte nennt jetzt den neuen Branch.
Ergebnis:

Anmerkung von mir:
Also ansich geht das, aber ich habe selber noch nicht so viel mit GitHub gearbeitet, deswegen sind mir manche abläufe icht ganz bewusst. 
Also ich checke das soweit. 
Man hat eine Code Datei, und prinzipiell ist die erstmal main auf GitHub. 
und dann kann man das auch runterladen. und dann kann man auch einen neuen branch aufmachen, wo der selbe code ist. und wenn man dann dort da sdesign mahc,t dann nennt manihn z.B. design. 
und wenn man dann fertig ist, kann man das mit andern teilen die rüber schauen und die sagen, passt und dann kannst du das in das main überführen und dann werden alle Dateien, die anders sind überführt oder?
oder kann man dann einzelne Dateien überführen, das ist mir nich tganz klar. denn wenn jemand z.B. Barrierefreiheit gemacht hat, will ich ja nur meine design Dateien dort aktualisiern und nicht die barrierfreiheitsdatein, weil jemand anders die schon hat. 
also das ist mir etwas unklar. 
aber der branch bleibt ja eigentlich oder. und die branch Ansicht sagt ja nur, in welchem branch ich mich befinde. 
also ist jeder branch erstmal eine opie vom main und dann kann ich einzelne Dateien überführen?
Aber dann sollte ich doch bei den einzelnen branches dielöschen könne und nicht, wenn main aktiviert ist. 
das versthe ich nicht noch nicht ganz.
daher, mache das so, wie für GitHub logishcist und höre nicht zu sehr auf meine Kommentare. 
und erstelle auf hilfe eine Anleitung, die das Prinzip von GitHub Branche serklärt und wann man was macht und wo man dann was löschen darf und umbenennen und was nur auf GitHub passiert und was auch bei sich selbst, z.B. umbennnen. 
einmal so einen überblick. viellciht auch an beispieln Name x machht das, du kompiert, machst branch z, und etc...

Antwort von Claude: Ihr Verständnis stimmt fast ganz. Ein wichtiger Punkt: Beim Übernehmen in main kopiert Git nicht alle Dateien, die anders aussehen. Es bringt nur die Änderungen, die in diesem Branch gemacht wurden. Hat jemand anderes schon die Barrierefreiheit in main übernommen, bleibt die erhalten, und aus Ihrem Branch kommen nur Ihre Design-Änderungen dazu. Einzelne Dateien übernimmt man nicht. Deshalb macht man pro Aufgabe einen eigenen Branch. Das Cockpit macht es so, wie es in Git und GitHub üblich ist. Die Anleitung steht jetzt im Menü Hilfe unter „Branches verstehen …“, mit einem Beispiel mit Anna und Ben, was wo passiert und was man wann löschen darf.
