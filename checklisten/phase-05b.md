# Checkliste Phase 5b: Sicherheitsprüfung und Neues Projekt hochladen

Stand: 25.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten:
   - Wählen Sie die Windows-Anmeldeinformationsverwaltung.
   - Melden Sie sich auf der Seite „GitHub-Konto“ im Browser mit Ihrem echten Konto an.
   - Übernehmen Sie auf der Seite „Git-Identität“ die noreply-Adresse von GitHub.
3. In dieser Checkliste legen Sie auf Ihrem echten GitHub-Konto das private Repository „codecockpit-test“ an, wie in den Fragen zu Phase 5 vereinbart. Es bleibt bis Teilschritt 5e bestehen. Dort löschen Sie es mit dem Cockpit.
4. Der Ordner für den Test liegt hier: `C:\Users\pasca\AppData\Local\CodeCockpit\Testdaten\Andere Ordner\codecockpit-test`. Er enthält absichtlich einen erfundenen Token, eine Passwort-Zeile, eine Datei `.env` und eine Datenbank.


## A. Angaben für das neue Repository

[?] 1. Ordner wählen
Tasten: In der Projektliste ganz oben „Neues Projekt hochladen“, Enter. Im Fenster „Ordner mit dem Code wählen“ den Pfad aus der Vorbereitung eintippen, Enter.
Erwartet: Ein Fenster „Neues Projekt hochladen“ öffnet sich. Der Fokus steht im Feld „Name auf GitHub“ mit „codecockpit-test“.
Ergebnis: Was ist, wenn der ordner da bleibe soll wo er ist. z.B. wenn er schon auf der richtigen ebene ist, dort wo auch die exe liegt, mit den Projekten?

Antwort von Claude: Berechtigte Frage. Bisher kopiert „Neues Projekt hochladen“ immer, so steht es in Konzept 9.1. Liegt der Ordner schon richtig, müssten Sie ihn heute erst mit „Vorhandenes Projekt hinzufügen“ aufnehmen und dann „Auf GitHub hochladen“ wählen. Das ist umständlich. Ihr Vorschlag unter Punkt 8 löst genau das, siehe dort.

[x] 2. Felder
Tasten: Mehrmals Tab.
Erwartet: Es folgen „Kurzbeschreibung“, „Sichtbarkeit“ mit „Privat“, „Lizenz“ mit „MIT“, „Ziel“ mit „Eigenes Konto 1013hPascal“ (und Ihren Organisationen, falls Sie welche haben), dann „Weiter …“ und „Abbrechen“.
Ergebnis:

[x] 3. Ungültiger Name
Tasten: Im Feld „Name auf GitHub“ „Mein Test“ eintippen, Alt+W.
Erwartet: Eine Meldung sagt, dass der Name nur Buchstaben ohne Umlaute, Ziffern, Punkt, Bindestrich und Unterstrich enthalten darf. Nach OK steht der Fokus wieder im Feld „Name auf GitHub“. Tragen Sie danach wieder „codecockpit-test“ ein.
Ergebnis:

[x] 4. Öffentlich wird erklärt
Tasten: „Sichtbarkeit“ auf „Öffentlich“ stellen, Alt+W. Die Frage lesen, dann Escape.
Erwartet: Die Frage endet mit „Öffentlich heißt: Jeder im Internet kann den Code sehen. Hochladen?“. Vorgabe ist „Abbrechen“. Nach Escape passiert nichts, auch im Ordner Projekte entsteht nichts.
Ergebnis:


## B. Sicherheitsprüfung

[x] 5. Rückfrage vor dem Hochladen
Tasten: Wie in Punkt 1, diesmal „Privat“ lassen, Alt+W. Die Frage lesen.
Erwartet: Die Frage sagt: Das Cockpit kopiert den Ordner nach `…\Testdaten\Projekte\codecockpit-test\Code`. Die virtuelle Umgebung und Caches kommen nicht mit. Der alte Ordner bleibt unverändert. Es prüft auf Geheimnisse, legt das private Repository 1013hPascal/codecockpit-test an und lädt alles hoch. Die Knöpfe heißen „Hochladen“ und „Abbrechen“.
Ergebnis:

[?] 6. Fenster Sicherheitsprüfung
Tasten: „Hochladen“. Warten, bis ein neues Fenster kommt. Pfeiltasten in der Liste.
Erwartet: NVDA sagt „Wird vorbereitet.“ Das Fenster heißt „Sicherheitsprüfung: 3 Funde stoppen das Hochladen, 1 Warnung“. Die Liste „Funde“ enthält:
- „Geheimnis: .env, Datei mit Zugangsdaten. Stoppt das Hochladen“
- „Geheimnis: config.py, Zeile 1, GitHub-Token. Stoppt das Hochladen“
- „Geheimnis: config.py, Zeile 2, Passwort oder Schlüssel im Code. Stoppt das Hochladen“
- „Private Daten: daten.db, Datenbank. Kommt in .gitignore“
Kein Eintrag nennt den Token oder das Passwort selbst.
Ergebnis: passt, beimir kommen aber nur zwei einträge.
Geheimnis: config.py, Zeile 1, GitHub-Token. Stoppt das Hochladen
Geheimnis: config.py, Zeile 2, Passwort oder Schlüssel im Code. Stoppt das Hochladen
Wenn das richtig ist, dann ist alles super

Antwort von Claude: Ja, das ist richtig. Meine Checkliste war hier falsch. Bevor das Cockpit prüft, legt es die Datei .gitignore an. Dort stehen schon von Anfang an `.env` und `*.db`. Damit werden .env und daten.db gar nicht hochgeladen, und die Prüfung muss sie nicht mehr melden. Das ist das gewünschte sichere Verhalten. Punkt 9 entfällt deshalb.

[x] 7. Weiter ist gesperrt, Escape bricht ab
Tasten: Tab durch die Knöpfe, dann Escape.
Erwartet: Die Knöpfe heißen „In .gitignore aufnehmen“, „Kein Geheimnis“, „Trotzdem hochladen“, „Datei öffnen“, „Erneut prüfen“, „Weiter“ und „Abbrechen“. „Weiter“ ist nicht verfügbar. Nach Escape sagt NVDA „Hochladen abgebrochen. codecockpit-test ist in der Liste. Mit Auf GitHub hochladen geht es später weiter.“ In der Projektliste steht „codecockpit-test, noch nicht auf GitHub“.
Ergebnis:

[x] 8. Auf GitHub hochladen
Tasten: codecockpit-test ausklappen, auf „Code“ Tab.
Erwartet: Die erste Aktion heißt „Auf GitHub hochladen …“. Enter auf der Zeile „Code“ in der Projektliste startet sie ebenfalls. Es kommt wieder das Fenster mit den Angaben, dann die Rückfrage. Diesmal steht dort nichts vom Kopieren. Wählen Sie „Hochladen“.
Ergebnis:

Frage bevor wir weiterachen.
ist des hier nicht sinnvoller, oben zwei möglichkeitne zu habne. Rebository von GitHub hier einbinden. wenn man das gemacht hat, ist es heruntergeladen und erscheint hier. 
Oder man macht Github von REchner einbinden, dann wählt man einen ordner aus und kann entweder den beim aktuellen speiherort lassen oder in diesen ordner hinschiebn. und dann erscheint der in der liste. das projekt neu hochjladen kann dan ja bei den projektatkoinen landen. wenn es nämlich noch nicht auf GitHub liegt. Das fände ich irgendwie intuitiver. 

Antwort von Claude: Ich finde den Vorschlag gut. Er trennt zwei Fragen, die bisher vermischt sind: Wie kommt ein Projekt in die Liste? Und wie kommt es auf GitHub? So würde ich es bauen:

Oben in der Projektliste stehen zwei Einträge statt „Neues Projekt hochladen“:

1. „Projekt vom Rechner hinzufügen …“: Sie wählen einen Ordner.
   - Hat er schon den Aufbau mit dem Unterordner Code, kommt er sofort in die Liste und bleibt, wo er ist.
   - Sonst fragt das Cockpit: „In den Projekte-Hauptordner verschieben“, „Am Ort lassen“ oder „Abbrechen“. Vorgabe ist „Abbrechen“. Verschieben heißt: `<Hauptordner>\<Name>\Code`, wie bisher beim Umstellen. Am Ort lassen heißt: Das Projekt wird nur verknüpft.
   - Ist das Projekt noch nicht auf GitHub, fragt das Cockpit danach: „Jetzt auf GitHub hochladen?“ Vorgabe ist „Später“.
2. „Projekt von GitHub herunterladen …“: eine Liste Ihrer Repositories und der Repositories Ihrer Organisationen, dazu „Adresse eingeben …“. Das war für 5c geplant und kommt jetzt nach vorne. Ihre eigenen Repositories stehen außerdem wie bisher als „nur auf GitHub“ in der Liste.

Das Hochladen ist dann nur noch eine Aktion des Projekts: „Auf GitHub hochladen …“ bei Code. Sie gibt es schon, samt Sicherheitsprüfung.

Was wegfällt:
- „Neues Projekt hochladen“ mit dem Kopieren. Das Kopieren fällt ganz weg. Es gibt dann nie zwei Ausgaben desselben Codes auf dem Rechner.
- Der Menüpunkt „Vorhandenes Projekt hinzufügen“. Im Menü Datei stehen stattdessen dieselben zwei Einträge wie oben in der Liste.

Das weicht von Konzept 7.3 und 9.1 ab. Ich trage es in ENTSCHEIDUNGEN.md ein, sobald Sie zustimmen. Danach passe ich die Checkliste 5b an. Die Punkte 9 bis 16 testen Sie dann mit dem neuen Ablauf.


Antwort von Claude: Umgebaut wie oben beschrieben. Die alten Punkte 9 bis 16 entfallen. Bitte testen Sie stattdessen Abschnitt E.


## E. Neuer Ablauf: Hinzufügen und Hochladen getrennt

Bitte alle Fenster des Cockpits schließen und `start_testdaten.bat` neu starten. Im Assistenten wie in der Vorbereitung oben.

[x] 17. Zwei Einträge oben
Tasten: In der Projektliste Pos1, dann Pfeil runter. Danach Alt+D.
Erwartet: Die ersten Zeilen heißen „Projekt vom Rechner hinzufügen“ und „Projekt von GitHub herunterladen“. „Neues Projekt hochladen“ gibt es nicht mehr. Im Menü Datei stehen „Projekt vom Rechner hinzufügen …“ und „Projekt von GitHub herunterladen …“. „Vorhandenes Projekt hinzufügen“ gibt es nicht mehr.
Ergebnis:

[x] 18. Ordner am Ort lassen
Tasten: Enter auf „Projekt vom Rechner hinzufügen“. Ordner `C:\Users\pasca\AppData\Local\CodeCockpit\Testdaten\Andere Ordner\codecockpit-test` wählen. In der Frage „Am Ort lassen …“, bei der Frage nach dem Exe-Ordner „Ohne Exe-Ordner“.
Erwartet: Die erste Frage hat die Knöpfe „In den Projekte-Hauptordner verschieben …“, „Am Ort lassen …“ und „Abbrechen“. Vorgabe ist „Abbrechen“. Danach sagt NVDA „codecockpit-test hinzugefügt.“
Ergebnis:

[x] 19. Angebot zum Hochladen
Tasten: Die nächste Frage lesen, dann Escape.
Erwartet: Die Frage lautet „codecockpit-test ist noch nicht auf GitHub. Jetzt hochladen? Sie können das auch später bei Code mit der Aktion Auf GitHub hochladen machen.“ Die Knöpfe heißen „Jetzt hochladen …“ und „Später“. Vorgabe ist „Später“. Nach Escape steht der Fokus auf „codecockpit-test, noch nicht auf GitHub“. Der Ordner liegt weiter in `Andere Ordner`.
Ergebnis:

[x] 20. Meldung bei Leerzeichen im Namen
Tasten: codecockpit-test ausklappen, Enter auf „Code“. Im Feld „Name auf GitHub“ „Mein Test“ eintippen, Alt+W.
Erwartet: Die Meldung lautet „Der Name darf keine Leerzeichen enthalten. Nehmen Sie stattdessen einen Bindestrich, zum Beispiel Mein-Test.“ Danach steht der Fokus wieder im Feld. Tragen Sie wieder „codecockpit-test“ ein.
Ergebnis:

[x] 21. Rückfrage ohne Kopieren
Tasten: Alt+W, die Frage lesen, „Hochladen“.
Erwartet: Die Frage beginnt mit „Das Cockpit prüft den Code auf Geheimnisse, legt auf GitHub das private Repository 1013hPascal/codecockpit-test an und lädt alles hoch.“ Vom Kopieren steht nichts darin.
Ergebnis:

[x] 22. Fenster Sicherheitsprüfung
Tasten: Warten, dann Pfeiltasten in der Liste.
Erwartet: Das Fenster heißt „Sicherheitsprüfung: 2 Funde stoppen das Hochladen“. Die Liste enthält „Geheimnis: config.py, Zeile 1, GitHub-Token. Stoppt das Hochladen“ und „Geheimnis: config.py, Zeile 2, Passwort oder Schlüssel im Code. Stoppt das Hochladen“. .env und daten.db fehlen, weil sie schon in .gitignore stehen.
Ergebnis:

[!] 23. Token in der Datei entfernen
Tasten: Auf der Zeile mit dem GitHub-Token Alt+F („Datei öffnen“). Im Editor die erste Zeile löschen, speichern, Editor schließen. Zurück im Cockpit Alt+E („Erneut prüfen“).
Erwartet: NVDA sagt „Geprüft: 1 Fund stoppt das Hochladen“. Übrig ist „Geheimnis: config.py, Zeile 1, Passwort oder Schlüssel im Code“. Es ist jetzt Zeile 1, weil Sie die erste Zeile gelöscht haben.
Ergebnis: Di Schaltflächen hier können gerade nicht mit enter aktiviert werden, bitte ändern. Außerdem, wenn man auf erneut prüfen klickt, soll sprachausgabe sagen, Fehler behoben, oder fehler bleibt besteh. und der Fokus soll auf die liste wechseln. wenn behoben, dann auf den nächsten eintrag in der liste, sonst auf dem selben.

Antwort von Claude: Beides umgesetzt. Enter löst jetzt den Knopf aus, auf dem der Fokus steht. Enter in der Liste selbst tut nichts, damit nicht aus Versehen etwas passiert. „Erneut prüfen“ sagt „Behoben“ oder „Besteht weiter“ und danach, was noch übrig ist. Der Fokus geht in die Liste: bei behoben auf den nächsten Fund, sonst auf denselben. Bitte Punkt 31 prüfen.

[x] 24. Kein Geheimnis
Tasten: Alt+K („Kein Geheimnis“).
Erwartet: NVDA sagt „Als kein Geheimnis markiert.“ Das Fenster heißt „Sicherheitsprüfung: alles in Ordnung“. Die Liste zeigt „Keine Funde mehr.“ „Weiter“ ist verfügbar.
Ergebnis: hier selbiger fehler wie obne beschrieben, kein Geheimnis kann nur mit Leertaste undnicht mit enter ausgewählt werden.

[x] 25. Hochladen
Tasten: Alt+W („Weiter“) und warten.
Erwartet: NVDA sagt nacheinander „Schritt 1 von 4: Sicherheitsprüfung …“ bis „Schritt 4 von 4: Wird hochgeladen …“. Dann kommt eine Meldung mit OK: „Fertig. Neues privates Repository 1013hPascal/codecockpit-test. Branch main ist hochgeladen. Der Link https://github.com/1013hPascal/codecockpit-test ist in der Zwischenablage.“
Ergebnis: Perfekt

[x] 26. Projektliste
Tasten: Nach OK die Projektliste ansehen, codecockpit-test ausklappen.
Erwartet: „codecockpit-test, aktualisiert am“ mit dem heutigen Datum. Darunter „Code, alles hochgeladen“. Es gibt keine zweite Zeile „codecockpit-test, nur auf GitHub“.
Ergebnis:

[x] 27. Auf GitHub
Tasten: Im Browser den Link aus der Zwischenablage öffnen.
Erwartet: Das Repository ist privat. Es enthält main.py, config.py, LICENSE, .gitignore und cockpit.toml, aber nicht .env und nicht daten.db. Der Commit heißt „Erste Version“ und ist von Ihnen. LICENSE ist die MIT-Lizenz mit Ihrem Namen und 2026.
Ergebnis:

[x] 28. Projekt von GitHub herunterladen
Tasten: Enter auf „Projekt von GitHub herunterladen“. Warten, dann Pfeiltasten in der Liste „Repositories“.
Erwartet: NVDA sagt „Repositories werden abgefragt.“ Die Liste zeigt Ihre Repositories und die Ihrer Organisationen, neueste oben, zum Beispiel „Tagebuch, 1013hPascal, privat, aktualisiert am …“. codecockpit-test fehlt, weil es schon in der Liste ist. Der letzte Eintrag heißt „Adresse eingeben …“. Escape schließt, ohne etwas zu tun.
Ergebnis:

[!] 29. Herunterladen aus der Liste
Tasten: Wie in Punkt 28, ein kleines Repository wählen, Enter.
Erwartet: NVDA sagt „… wird heruntergeladen.“ und dann „… heruntergeladen.“ Der Fokus steht auf dem neuen Projekt.
Ergebnis: Adresse eingeben, sollte der oberste eintrag sein,

Antwort von Claude: Geändert. „Adresse eingeben …“ steht jetzt oben, auch in der Liste bei „Mit vorhandenem Repository verbinden …“. Bitte Punkt 32 prüfen.

[x] 30. Herunterladen mit Adresse
Tasten: Wie in Punkt 28, „Adresse eingeben …“, Enter. `https://github.com/octocat/Hello-World` eintippen, Enter.
Erwartet: NVDA sagt „Hello-World wird heruntergeladen.“ und dann „Hello-World heruntergeladen.“ Das ist ein kleines öffentliches Beispiel-Repository von GitHub.
Ergebnis:


## F. Nachtest

Antwort von Claude auf Ihre Meldung: Stimmt, codecockpit-test liegt schon auf GitHub, und nach dem Herunterladen gibt es dort nichts mehr hochzuladen. Für den Nachtest gibt es deshalb in den Testdaten einen eigenen Ordner „sicherheitstest“ mit Token und Passwort. Er wird nie hochgeladen, weil Sie am Ende abbrechen.

Bitte `start_testdaten.bat` neu starten. So kommen Sie zum Fenster Sicherheitsprüfung:
1. „Projekt vom Rechner hinzufügen“, Ordner `C:\Users\pasca\AppData\Local\CodeCockpit\Testdaten\Andere Ordner\sicherheitstest`, „Am Ort lassen …“, „Ohne Exe-Ordner“.
2. Bei „Jetzt hochladen?“ „Jetzt hochladen …“ wählen, den Namen „sicherheitstest“ lassen, Alt+W, „Hochladen“.
Am Ende brechen Sie im Fenster Sicherheitsprüfung mit Escape ab. Dann entsteht auf GitHub nichts.

[x] 31. Enter auf Knöpfen und Erneut prüfen
Tasten: Im Fenster Sicherheitsprüfung auf der Zeile mit dem GitHub-Token Enter. Dann mit Tab zu „Erneut prüfen“, Enter. Danach „Datei öffnen“ mit Tab und Enter, die Zeile mit dem Token im Editor löschen, speichern, schließen. Zurück zu „Erneut prüfen“, Enter. Dann Tab bis „Kein Geheimnis“, Enter. Am Ende Escape.
Erwartet: Enter in der Liste tut nichts. Das erste „Erneut prüfen“ sagt „Besteht weiter. Noch: 2 Funde stoppen das Hochladen“, der Fokus steht in der Liste auf demselben Fund. Das zweite sagt „Behoben. Noch: 1 Fund stoppt das Hochladen“, der Fokus steht auf dem nächsten Fund. „Kein Geheimnis“ mit Enter markiert ihn. Escape bricht ab.
Ergebnis:

[x] 32. Adresse eingeben oben
Tasten: Enter auf „Projekt von GitHub herunterladen“.
Erwartet: Der erste Eintrag der Liste ist „Adresse eingeben …“, danach kommen Ihre Repositories. Escape schließt.
Ergebnis:
