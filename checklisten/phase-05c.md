# Checkliste Phase 5c: Änderungen hochladen und holen

Stand: 25.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- Bei Code gibt es „Änderungen hochladen …“ (Enter) und „Änderungen von GitHub holen …“.
- Holen funktioniert wie in GitHub Desktop: Die neuen Commits werden mit Ihrem Stand zusammengeführt. Vorher kommen die betroffenen Dateien als Sicherheitskopie in den Ordner backups.
- Stören Ihre Änderungen, die noch nicht hochgeladen sind, legt das Cockpit sie nach Rückfrage beiseite (Stash) und danach wieder zurück.
- Bei einem Konflikt wählen Sie pro Datei: „Meine Fassung behalten“, „Fassung von GitHub übernehmen“ oder „Im Editor öffnen“. „Zusammenführen abbrechen“ führt zurück zum Stand vor dem Holen.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten:
   - Wählen Sie die Windows-Anmeldeinformationsverwaltung.
   - Melden Sie sich auf der Seite „GitHub-Konto“ im Browser mit Ihrem echten Konto an. Das brauchen Sie erst in Abschnitt G.
   - Übernehmen Sie auf der Seite „Git-Identität“ die noreply-Adresse von GitHub.
3. In den Testdaten hat ein „anderer Rechner“ schon Änderungen hochgeladen: zu PDF-Chat, Tagebuch und Rezepte. Die „Plattform“ dieser drei Projekte ist ein Ordner auf Ihrem Rechner. Die Texte sagen trotzdem „GitHub“.


## A. Liste und Aktionen

[x] 1. Stand in der Liste
Tasten: In der Projektliste mit den Pfeiltasten zu PDF-Chat, Tagebuch und Rezepte.
Erwartet: Die Zeilen sagen unter anderem:
- „PDF-Chat, aktualisiert am …, 1 Änderung auf GitHub noch nicht geholt“
- „Tagebuch, aktualisiert am …, 1 Datei noch nicht hochgeladen, 1 Änderung auf GitHub noch nicht geholt“, dazu der Hinweis auf die virtuelle Umgebung
- „Rezepte, aktualisiert am …, 1 Datei noch nicht hochgeladen, 1 Änderung auf GitHub noch nicht geholt“
Ergebnis:

[x] 2. Aktionen bei Code
Tasten: Auf PDF-Chat Pfeil rechts, dann Pfeil runter zu „Code, alles hochgeladen“. Tab.
Erwartet: Die Aktionsliste beginnt mit „Änderungen hochladen …“ und „Änderungen von GitHub holen …“. „Auf GitHub hochladen …“ steht nicht in der Liste. Umschalt+Tab führt zurück auf Code.
Ergebnis:


## B. Hochladen, wenn GitHub schon weiter ist (PDF-Chat)

Hier ist GitHub einen Commit weiter. Das Cockpit lädt dann nicht einfach hoch, sondern bietet an, zuerst zu holen. So macht es auch GitHub Desktop.

[x] 3. Datei ändern
Tasten: Bei Code von PDF-Chat die Aktion „Code-Ordner öffnen“. Die Datei README.md im Editor öffnen, eine Zeile anhängen, speichern, Editor schließen. Zurück ins Cockpit, Strg+R.
Erwartet: Die Zeile heißt jetzt „Code, 1 Datei noch nicht hochgeladen“. Der Fokus bleibt auf Code.
Ergebnis:

[x] 4. Fenster Änderungen hochladen
Tasten: Auf Code Enter. Dann mehrmals Tab.
Erwartet: Das Fenster heißt „Änderungen hochladen: 1 Datei geändert“. Der Fokus steht im Feld „Was haben Sie geändert?“. Mit Tab folgen „Beschreibung, freiwillig“, die Liste „Änderungen“ mit „README.md, geändert“, dann „Hochladen“ und „Abbrechen“.
Ergebnis:

[!] 5. Leere Nachricht
Tasten: Zurück ins Feld „Was haben Sie geändert?“ (Alt+W). Das Feld leer lassen, Enter.
Erwartet: Eine Meldung sagt „Bitte schreiben Sie kurz, was Sie geändert haben.“ Nach OK steht der Fokus wieder im Feld.
Ergebnis: Funktioiiert super, aber wenn ich ändrungen hochladen ankicke, und zum eirsten mal im texfeld lande, liest sprachausgabe vor, freeiwliig ändreung Was haben sie geändrt. und danach ist es pflicht. dann bitte, das freiwilig weglassen. Muss ich aber nicht mehr testen, nur ändern.
Odder bei was haben sie geändert, pflichtfeld, b
und Beschreibung wie jetzt, freiwilig. 

Antwort von Claude: Geändert. Das zweite Feld heißt jetzt nur „Beschreibung“. So hört man „freiwillig“ nicht mehr, bevor man im Pflichtfeld „Was haben Sie geändert?“ landet.


[x] 6. GitHub ist weiter
Tasten: „README ergänzt“ eintippen, Enter. Warten. Die Frage lesen, dann Escape.
Erwartet: NVDA sagt nacheinander „Schritt 1 von 3: Sicherheitsprüfung …“, „Schritt 2 von 3: Commit wird erstellt …“, „Schritt 3 von 3: Wird hochgeladen …“. Dann kommt die Frage: „Ihr Commit ist gespeichert, aber noch nicht hochgeladen. Auf GitHub gibt es 1 neuen Commit, die hier noch fehlen. Jetzt holen und danach hochladen?“. Die Knöpfe heißen „Holen und hochladen …“ und „Später“. Vorgabe ist „Später“. Nach Escape passiert nichts weiter.
Ergebnis:

[x] 7. Nur den Commit hochladen
Tasten: Auf Code Enter. Die Frage lesen, dann „Hochladen“.
Erwartet: Es kommt kein Fenster für die Nachricht, weil es keine neuen Änderungen gibt. Die Frage heißt „1 Commit ist noch nicht auf GitHub. Jetzt hochladen?“, Vorgabe ist „Abbrechen“. Nach „Hochladen“ kommt wieder die Frage aus Punkt 6.
Ergebnis:

[x] 8. Holen und hochladen
Tasten: In der Frage aus Punkt 6 „Holen und hochladen …“. Dann die nächste Frage lesen, „Holen“.
Erwartet: Die zweite Frage heißt „Auf GitHub gibt es 1 neuen Commit, sie ändern 1 Datei. Das Cockpit führt sie mit Ihrem Stand zusammen, wie git pull. Vorher kommen die betroffenen Dateien als Sicherheitskopie in den Ordner backups im Datenordner. Holen?“. Vorgabe ist „Abbrechen“. Nach „Holen“ sagt NVDA „Wird zusammengeführt.“, dann „Geholt: 1 neuer Commit von GitHub.“ und am Ende „Fertig. Branch main ist hochgeladen.“ Es gibt keine dritte Frage. Die Zeile heißt „Code, alles hochgeladen“. Der Fokus bleibt auf Code.
Ergebnis:

[x] 9. Nichts mehr zu holen
Tasten: Tab, „Änderungen von GitHub holen …“, Enter.
Erwartet: NVDA sagt „Wird geholt.“ und danach „Keine neuen Änderungen auf GitHub.“ Es kommt keine Frage.
Ergebnis:

[x] 10. Nichts hochzuladen
Tasten: Umschalt+Tab zurück auf Code, Enter.
Erwartet: NVDA sagt „Es gibt nichts zum Hochladen. Alles ist hochgeladen.“ Es kommt kein Fenster.
Ergebnis:


## C. Sicherheitsprüfung beim Hochladen (PDF-Chat)

[x] 11. Passwort in einer neuen Datei
Tasten: Im Code-Ordner von PDF-Chat eine neue Datei `zugang.py` anlegen mit der Zeile `password = "Sommer2026!"`. Speichern. Im Cockpit auf Code Enter, „Zugang ergänzt“ eintippen, Enter.
Erwartet: Das Fenster „Sicherheitsprüfung“ aus Phase 5b öffnet sich mit dem Fund „Geheimnis: zugang.py, Zeile 1, Passwort oder Schlüssel im Code. Stoppt das Hochladen“. Nur diese neue Datei wird geprüft, nicht der ganze Ordner.
Ergebnis:

[x] 12. In .gitignore aufnehmen und hochladen
Tasten: „In .gitignore aufnehmen“, dann „Weiter“.
Erwartet: Das Hochladen läuft durch und endet mit „Fertig. Commit „Zugang ergänzt“. Branch main ist hochgeladen.“ Hochgeladen wurde nur die geänderte Datei .gitignore. Die Datei zugang.py bleibt auf Ihrem Rechner.
Ergebnis:


## D. Beiseitelegen und Konflikt (Tagebuch)

In Tagebuch ist main.py hier geändert und auf GitHub anders geändert.

[x] 13. Frage nach Beiseitelegen
Tasten: Zu Code von Tagebuch. Tab, „Änderungen von GitHub holen …“, Enter. Die Frage lesen, dann Escape.
Erwartet: Die Frage sagt, dass es auf GitHub 1 neuen Commit gibt, und: „In main.py haben Sie auch Änderungen, die noch nicht hochgeladen sind.“ Sie erklärt das Beiseitelegen (Stash) und die Sicherheitskopie. Die Knöpfe heißen „Beiseitelegen und holen“ und „Abbrechen“. Vorgabe ist „Abbrechen“. Nach Escape passiert nichts.
Ergebnis:

[!] 14. Fenster Konflikte
Tasten: Noch einmal holen, diesmal „Beiseitelegen und holen“. Warten. Pfeiltasten in der Liste, dann Enter in der Liste, dann mehrmals Tab.
Erwartet: NVDA sagt „Wird zusammengeführt.“ Dann öffnet sich das Fenster „Konflikte beim Zusammenführen: 1 Konflikt offen“. Die Liste „Dateien mit Konflikt“ enthält „main.py, Konflikt“. Enter in der Liste tut nichts. Mit Tab folgen „Meine Fassung behalten“, „Fassung von GitHub übernehmen“, „Im Editor öffnen“, „Erneut prüfen“, „Zusammenführen abbrechen“. „Zusammenführen abschließen“ ist noch nicht verfügbar.
Ergebnis: Im Editor öffnet sollte sagen welche der beiden er öffnet, GitHub oder meine

Antwort von Claude: Siehe Punkt 18. Der Knopf heißt jetzt „Konflikt im Editor anzeigen“. Er öffnet immer die eine Datei, in der beide Fassungen stehen, und die Abschnitte sind jetzt beschriftet.


[x] 15. Abbrechen
Tasten: Escape.
Erwartet: NVDA sagt „Zusammenführen abgebrochen. Alles ist wie vor dem Holen.“ In main.py steht wieder Ihre Fassung „Tagebuch, geändert“. Die Zeile von Tagebuch nennt weiter 1 Änderung auf GitHub, die noch nicht geholt ist.
Ergebnis: Warum sagt er bei code nicht auch, das nichts geholt ist, denn schließlich könnte es ja auch eine exe geben, und dan weiß man ja nicht, bei welchem von beidne man was hohlen muss. der hinweiß vom projekt, wie tagebur´ch müsste auch bie code, exe und allen andere unterordnen sein.

Antwort von Claude: Bei Code steht es jetzt auch, zum Beispiel „Code, 1 Datei noch nicht hochgeladen, 1 Änderung auf GitHub noch nicht geholt“. Bei Exe habe ich es bewusst nicht ergänzt: Holen geht nur bei Code, und die Exe ändert sich durch Holen nicht. Stünde der Hinweis auch bei Exe, sähe es so aus, als müsste man dort etwas tun. Wenn Sie es trotzdem bei Exe möchten, sagen Sie es mir.

[x] 16. Meine Fassung behalten
Tasten: Wie in Punkt 14 holen und „Beiseitelegen und holen“. Im Fenster Konflikte Tab zu „Meine Fassung behalten“, Enter. Dann Tab bis „Zusammenführen abschließen“, Enter.
Erwartet: Nach „Meine Fassung behalten“ sagt NVDA „main.py: Ihre Fassung. Alle Konflikte gelöst.“ Der Fokus steht in der Liste auf „main.py, gelöst: Ihre Fassung“. Der Titel heißt „Konflikte beim Zusammenführen: alle Konflikte gelöst“. Nach „Zusammenführen abschließen“ sagt NVDA „Zusammenführen abgeschlossen.“ In main.py steht Ihre Fassung. Die Zeile heißt „Code, 1 Datei noch nicht hochgeladen“.
Ergebnis:


## E. Konflikt beim Zusammenführen, im Editor lösen (Rezepte)

In Rezepte gibt es hier einen Commit und auf GitHub einen anderen, beide ändern dieselbe Zeile.

[x] 17. Holen mit Konflikt
Tasten: Zu Code von Rezepte. Tab, „Änderungen von GitHub holen …“, Enter, „Holen“.
Erwartet: Es kommt keine Frage nach Beiseitelegen, weil alle Änderungen schon im Commit sind. Dann öffnet sich das Fenster „Konflikte beim Zusammenführen: 1 Konflikt offen“ mit „rezepte.py, Konflikt“.
Ergebnis:

[ ] 18. Im Editor öffnen
Tasten: „Im Editor öffnen“. Die Datei im Editor lesen, ohne Änderung schließen. Zurück im Fenster Konflikte „Erneut prüfen“.
Erwartet: Im Editor stehen beide Fassungen zwischen Zeilen mit <<<<<<<, ======= und >>>>>>>. Die Liste zeigt „rezepte.py, im Editor geöffnet, noch Konfliktmarken“. „Erneut prüfen“ sagt „Keine Änderung. Noch 1 Konflikt.“
Ergebnis: ok, vergiss das vonoben mit im edijtor anzeigen.nenne das irgendwie so. Konflikt im Editor anzeigen.
Und hier müsssen icht nur die beiden zeilen stehen, sondern oberhalb. meine Verson und Github verion. oder lokale Version und Github Version, das klar ist, welcher coeabschnitt zu was gehört. am besten noch die Zeile bei beiden im code. also lokale Version main.py Zeile 7 und Github Version main.py Zeile 7.
Also hier mpsste ja die selbe ziele sein. im Beispiel oben, wo es andfere fcode sachen warn, dann die jeweiligen zeilen. 
jetzzt mit dem nächsten Checklisten schritt bin ich verwirrt. so ist das auf jeden falln icht intitiv. 

Antwort von Claude: Umgesetzt. Der Knopf heißt „Konflikt im Editor anzeigen“. Vor dem Öffnen beschriftet das Cockpit die Marken in der Datei. Statt „<<<<<<< HEAD“ steht dort zum Beispiel „<<<<<<< Meine Fassung, rezepte.py Zeile 1“, statt „=======“ steht „======= Fassung von GitHub, rezepte.py Zeile 1“, und am Ende „>>>>>>> Ende des Konflikts“. Die Zeilennummer gilt in der jeweiligen Fassung der Datei. Nur diese Markenzeilen ändern sich, Ihr Code nicht. Die Checkliste war hier auch unklar, das tut mir leid. Bitte im Nachtest Punkt 28 prüfen.

[x] 19. Im Editor lösen
Tasten: „Im Editor öffnen“. Alle Zeilen löschen und nur `REZEPT = 'Kartoffelsuppe und Apfelstrudel'` hineinschreiben. Speichern, schließen. „Erneut prüfen“.
Erwartet: NVDA sagt „Gelöst: rezepte.py. Alle Konflikte gelöst.“ Die Liste zeigt „rezepte.py, gelöst: im Editor bearbeitet“.
Ergebnis:

[!] 20. Abschließen und hochladen
Tasten: „Zusammenführen abschließen“. Dann auf Code Enter, die Frage lesen, „Hochladen“.
Erwartet: NVDA sagt „Zusammenführen abgeschlossen.“ Die Frage heißt „2 Commits sind noch nicht auf GitHub. Jetzt hochladen?“. Das sind Ihr Commit und der Commit, der beide Fassungen zusammenführt. Danach „Fertig. Branch main ist hochgeladen.“
Ergebnis: du hast gesagt, zusammenführen abschließen geht noch nicht, weiter oben, daher wurde es abgebrochen.

Antwort von Claude: Das war ein Fehler in der Bedienung, nicht bei Ihnen. Der Knopf war ausgegraut, solange noch ein Konflikt offen war. Ausgegraute Knöpfe überspringt Tab, deshalb fand man ihn nicht. Jetzt ist „Zusammenführen abschließen“ immer erreichbar. Ist noch etwas offen, sagt er „Noch nicht fertig. Noch 1 Konflikt.“ und setzt den Fokus auf die offene Datei. Ist der letzte Konflikt gelöst, springt der Fokus von selbst auf „Zusammenführen abschließen“. Bitte im Nachtest Punkt 29 prüfen.


## F. Sicherheitskopie

[ ] 21. Ordner backups
Tasten: Im Explorer den Ordner `C:\Users\pasca\AppData\Local\CodeCockpit\Testdaten\Daten\backups` öffnen.
Erwartet: Es gibt Ordner mit Datum, Uhrzeit, Projekt und „vor dem Holen“, zum Beispiel „… Tagebuch vor dem Holen“. Darin liegen main.py mit Ihrer Fassung und eine Datei Stand.txt mit dem Commit vor dem Holen.
Ergebnis: Füge das als menü bei Datei hinzu, das man da direkt den backups ordner sieht und die nötigen Aktionen ausführen kann. also dateine oder so als liste etc. 

Antwort von Claude: Umgesetzt: Menü Datei, „Sicherheitskopien …“ (Alt+D, S). Die Liste zeigt jede Kopie mit Datum, Projekt, Anlass und Anzahl der Dateien. Dazu gibt es „Dateien anzeigen …“, „Im Explorer öffnen“ und „Löschen …“. Bei den Dateien gibt es „Datei öffnen“ und „Wiederherstellen …“. Vor dem Wiederherstellen kommt die jetzige Datei selbst in eine neue Sicherheitskopie. Die Angaben zu Projekt und Commit stehen jetzt in der Datei Sicherheitskopie.txt, nicht mehr in Stand.txt. Bitte im Nachtest Punkt 31 prüfen.


## G. Mit dem echten GitHub (codecockpit-test)

Hier prüfen Sie, ob Hochladen und Holen auch mit Ihrem echten Konto klappen.

[x] 22. Herunterladen
Tasten: In der Projektliste „Projekt von GitHub herunterladen …“, Enter. In der Liste „codecockpit-test“ wählen, Enter.
Erwartet: NVDA sagt „codecockpit-test heruntergeladen.“ Das Projekt steht in der Liste.
Ergebnis:

[x] 23. Änderung hochladen
Tasten: Im Code-Ordner von codecockpit-test die Datei main.py im Editor ändern, speichern. Im Cockpit Strg+R, dann auf Code Enter. „Test aus Phase 5c“ eintippen, Enter.
Erwartet: „Fertig. Commit „Test aus Phase 5c“. Branch main ist hochgeladen.“ Auf github.com steht der Commit im Repository codecockpit-test. Es erschien kein Fenster, das nach Benutzername oder Passwort fragt.
Ergebnis:

[x] 24. Holen
Tasten: Tab, „Änderungen von GitHub holen …“, Enter.
Erwartet: „Keine neuen Änderungen auf GitHub.“
Ergebnis:


## H. Nachtest

Bitte `start_testdaten.bat` neu starten. Dann sind PDF-Chat, Tagebuch und Rezepte wieder im Ausgangszustand.

Ihr Wunsch zu „Projekt neu einlesen“ ist auch umgesetzt. Bei Projekt, Code und Exe steht die Aktion jetzt ganz oben in der Aktionsliste, in der Einzahl. Im Menü Datei heißt es weiter „Projekte neu einlesen“. Neu ist auch: Nach einer Aktion bleibt die Markierung in der Aktionsliste auf dieser Aktion und springt nicht mehr nach oben.

[x] 25. Projekt neu einlesen
Tasten: Auf PDF-Chat Tab. Umschalt+Tab, Pfeil rechts, Pfeil runter auf Code, Tab. Dasselbe bei Exe. Auf Code „Projekt neu einlesen“ mit Enter.
Erwartet: Bei Projekt, Code und Exe ist „Projekt neu einlesen“ der erste Eintrag. Enter auf Code führt weiter „Änderungen hochladen …“ aus, nicht das Neueinlesen. Nach Enter auf „Projekt neu einlesen“ sagt NVDA „PDF-Chat neu eingelesen.“ Die Markierung bleibt auf „Projekt neu einlesen“.
Ergebnis:

[x] 26. Hinweis bei Code
Tasten: Zu Code von Tagebuch.
Erwartet: Die Zeile heißt „Code, 1 Datei noch nicht hochgeladen, 1 Änderung auf GitHub noch nicht geholt“.
Ergebnis:

[x] 27. Beschriftung bei einem Konflikt in Tagebuch
Tasten: Bei Code von Tagebuch holen, „Beiseitelegen und holen“. Im Fenster Konflikte „Konflikt im Editor anzeigen“. Die Datei lesen, ohne Änderung schließen. Dann Escape.
Erwartet: Im Editor steht:
- „<<<<<<< Fassung von GitHub, main.py Zeile 1“
- „print('Tagebuch vom anderen Rechner')“
- „======= Meine Fassung, main.py Zeile 1“
- „print('Tagebuch, geändert')“
- „>>>>>>> Ende des Konflikts“
Hier steht die Fassung von GitHub oben, weil Ihre Änderungen nach dem Holen zurückgelegt werden. Nach Escape sagt NVDA „Zusammenführen abgebrochen. Alles ist wie vor dem Holen.“, und in main.py steht wieder nur Ihre Fassung.
Ergebnis:

[ ] 28. Beschriftung bei einem Konflikt in Rezepte
Tasten: Bei Code von Rezepte holen, „Holen“. Im Fenster Konflikte „Konflikt im Editor anzeigen“. Die Datei lesen.
Erwartet: Oben steht „<<<<<<< Meine Fassung, rezepte.py Zeile 1“ mit „REZEPT = 'Kartoffelsuppe'“. Dann „======= Fassung von GitHub, rezepte.py Zeile 1“ mit „REZEPT = 'Apfelstrudel'“. Am Ende „>>>>>>> Ende des Konflikts“. Die Liste zeigt „rezepte.py, im Editor angezeigt, noch Konfliktmarken“. Lassen Sie den Editor offen.
Ergebnis:

[x] 29. Zusammenführen abschließen
Tasten: Im Fenster Konflikte mit Tab zu „Zusammenführen abschließen“, Enter. Dann im Editor alle Zeilen durch `REZEPT = 'Kartoffelsuppe und Apfelstrudel'` ersetzen, speichern, schließen. Im Fenster Konflikte „Erneut prüfen“. Dann Enter.
Erwartet: Das erste Enter sagt „Noch nicht fertig. Noch 1 Konflikt.“, der Fokus geht in die Liste auf rezepte.py. „Erneut prüfen“ sagt „Gelöst: rezepte.py. Alle Konflikte gelöst.“, und der Fokus steht auf „Zusammenführen abschließen“. Enter schließt ab, NVDA sagt „Zusammenführen abgeschlossen.“
Ergebnis:

[x] 30. Hochladen nach dem Zusammenführen
Tasten: Auf Code von Rezepte Enter, „Hochladen“.
Erwartet: Die Frage heißt „2 Commits sind noch nicht auf GitHub. Jetzt hochladen?“. Danach „Fertig. Branch main ist hochgeladen.“
Ergebnis:

[x] 31. Sicherheitskopien
Tasten: Alt+D, dann S. Pfeiltasten in der Liste. Tab zu „Dateien anzeigen …“, Enter. In der Liste der Dateien Tab zu „Datei öffnen“, Enter, Editor wieder schließen. Dann „Wiederherstellen …“, die Frage lesen, Escape. Mit Escape zurück in die Liste der Kopien.
Erwartet: Das Fenster heißt „Sicherheitskopien: …“ mit der Anzahl. Die Zeilen beginnen mit Datum und Uhrzeit, dann Projekt, Anlass und Anzahl, zum Beispiel „25.09.2026 15:10, Tagebuch, vor dem Holen, 1 Datei“. Die neueste steht oben. Das Fenster der Dateien nennt im Titel die Kopie und den Ordner, aus dem die Dateien kommen. „Datei öffnen“ zeigt die gesicherte Fassung. Die Frage beim Wiederherstellen sagt, wohin die Datei kommt und dass die jetzige Datei vorher gesichert wird. Vorgabe ist „Abbrechen“, Escape ändert nichts.
Ergebnis:

[x] 32. Wiederherstellen und Löschen
Tasten: Bei einer Kopie von Tagebuch „Dateien anzeigen …“, dann „Wiederherstellen …“ und „Wiederherstellen“. Escape. Dann in der Liste der Kopien „Löschen …“ auf der obersten Kopie, „Löschen“.
Erwartet: NVDA sagt „main.py wiederhergestellt.“ In der Liste steht oben eine neue Kopie „…, Tagebuch, vor dem Wiederherstellen, 1 Datei“ mit der Fassung von vorher. Nach dem Löschen sagt NVDA „Sicherheitskopie gelöscht.“, und die Kopie ist weg. Der Fokus bleibt in der Liste.
Ergebnis:
