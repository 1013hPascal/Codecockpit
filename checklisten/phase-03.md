# Checkliste Phase 3: Tresor, Konten und Einrichtungsassistent

Stand: 25.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Vorbereitung

1. Schließen Sie alle offenen Fenster von CodeCockpit. Von Ihrem letzten Test waren noch zwei Fenster mit Testdaten offen.
2. Starten Sie `start_testdaten.bat`.

Mit Testdaten beginnt die Einrichtung bei jedem Start von vorn. Zugangsdaten landen dabei unter einem eigenen Namen, nie bei Ihren echten Daten. Für die Kontenverwaltung gibt es eine „Testplattform“. Ihr Verbindungstest gelingt nur mit dem Token „richtig“.

Als Master-Passwort für den Test eignet sich zum Beispiel „Testpasswort1“.


## A. Einrichtungsassistent

[x] 1. Willkommen
Tasten: keine, nur starten.
Erwartet: Ein Fenster „CodeCockpit einrichten, Schritt 1 von 6: Willkommen“. Der Fokus steht in der Liste „Willkommen“. Mit Pfeil runter lesen Sie die Zeilen. Tab führt zu „Weiter“ und „Abbrechen“. „Überspringen“ gibt es hier nicht, „Zurück“ ist nicht verfügbar.
Ergebnis: 

[x] 2. Git
Tasten: Alt+W.
Erwartet: NVDA sagt „Schritt 2 von 6: Git. Git ist installiert.“ Der Fokus steht in der Liste mit „Git ist installiert.“ und dem Ort von Git.
Ergebnis:

[!] 3. Tresor-Seite
Tasten: Alt+W, dann Umschalt+Tab und Pfeiltasten in der Erklärung, dann Tab zurück.
Erwartet: NVDA sagt „Schritt 3 von 6: Tresor. Wählen Sie, wo Ihre Zugangsdaten gespeichert werden. Dieser Schritt ist Pflicht.“ Der Fokus steht auf dem Auswahlschalter „Windows-Anmeldeinformationsverwaltung (empfohlen)“, er ist ausgewählt. Die Erklärung hat fünf Zeilen. „Überspringen“ gibt es hier nicht.
Ergebnis: ist es nicht sinnvoll, den vokus auf das erklärfenster zu machen und dann geht man mit tab weiter? jemand der bilnd ist, weiß nicht, dass es ein erklärfenster gibt. und ich finde die Erklärung gut. 
Bei der Auswahl sind beide markiert, die chackboxmarklist funktiniert nicht recht. das hatten wir schon bei den andern Projekten gelöst.


[x] 4. Tresordatei wählen und Passwort festlegen
Tasten: Pfeil runter auf „Verschlüsselte Tresordatei mit Master-Passwort“, dann Alt+W.
Erwartet: Fenster „Master-Passwort festlegen“. Der Fokus steht im Feld „Neues Master-Passwort“. Mit Tab erreichen Sie „Neues Passwort wiederholen“, „Speichern“ und „Abbrechen“.
Ergebnis:

[x] 5. Passwörter stimmen nicht überein
Tasten: in die beiden Felder zwei verschiedene Passwörter tippen, Enter.
Erwartet: Meldung „Die beiden Passwörter stimmen nicht überein.“ Nach Enter sind beide Felder leer, und der Fokus steht wieder im ersten Feld. Probieren Sie auch ein zu kurzes Passwort wie „abc“: Meldung „mindestens 8 Zeichen“.
Ergebnis:

[x] 6. Passwort festlegen
Tasten: zweimal „Testpasswort1“, Enter.
Erwartet: Das Fenster schließt. NVDA sagt „Schritt 4 von 6: Projekte-Hauptordner.“ Im Feld steht der Testordner.
Ergebnis:

[x] 7. Hauptordner und Git-Identität
Tasten: Alt+W. Auf der Seite Git-Identität nur einen Namen eintragen, dann Alt+W.
Erwartet: Meldung „Bitte Name und E-Mail-Adresse eingeben, oder den Schritt überspringen.“ Danach steht der Fokus im leeren Feld.
Ergebnis:

[x] 8. Überspringen
Tasten: Alt+B (Überspringen).
Erwartet: NVDA sagt „Schritt 6 von 6: Zusammenfassung“. Die Liste zeigt zum Beispiel „Eingerichtet: Tresor: Verschlüsselte Tresordatei.“ und „Übersprungen: Git-Identität. Nachholen: Menü Einstellungen, Grundeinstellungen.“ Die Schaltfläche heißt jetzt „Fertig“.
Ergebnis:

[x] 9. Zurück
Tasten: Alt+Z, dann Alt+W.
Erwartet: Alt+Z führt zur vorigen Seite mit Ansage. Alt+W führt wieder zur Zusammenfassung.
Ergebnis:

[f] 10. Fertig
Tasten: Alt+F.
Erwartet: Der Assistent schließt, das Hauptfenster öffnet sich mit „CodeCockpit mit Testdaten bereit. 4 Projekte.“
Ergebnis:


## B. Menü Konten und Tresor sperren

[x] 11. Menü Konten
Tasten: Alt+O.
Erwartet: „Kontenverwaltung …“, „Tresor-Einstellungen …“ und „Tresor sperren“.
Ergebnis:

[x] 12. Tresor sperren
Tasten: Enter auf „Tresor sperren“.
Erwartet: NVDA sagt „Tresor gesperrt.“ Im Menü Konten steht jetzt „Tresor entsperren …“ statt „Tresor sperren“.
Ergebnis:

[?] 13. Tresor entsperren
Tasten: Alt+O, „Tresor entsperren …“, Enter. Erst ein falsches Passwort, dann „Testpasswort1“.
Erwartet: Fenster „Tresor entsperren“, der Fokus steht im Feld „Master-Passwort“. Beim falschen Passwort: „Das Master-Passwort ist falsch.“, danach ist das Feld leer und hat den Fokus. Beim richtigen: NVDA sagt „Tresor entsperrt.“
Ergebnis: wenn ich den Tresor sperre, was bedeutet das, das man keine sache mehr ausführen kann, bis man es endspert?


## C. Kontenverwaltung

[x] 14. Liste der Konten
Tasten: Alt+O, „Kontenverwaltung …“, Enter.
Erwartet: Fenster „Kontenverwaltung“. Der Fokus steht in der Liste „Konten“ auf „Neues Konto anlegen …“. Mit Tab erreichen Sie „Verbindung testen“, „Löschen“ und „Schließen“.
Ergebnis:

[?] 15. Neues Konto
Tasten: Enter auf „Neues Konto anlegen …“.
Erwartet: Fenster „Neues Konto: Testplattform“. Felder in dieser Reihenfolge: Anzeigename (enthält „Testplattform“), Benutzername, Serveradresse (enthält „https://test.example“), Token (verdeckt, NVDA sagt „Passwort“ oder „geschützt“). Dann „Verbindung testen“, „Speichern“ und „Abbrechen“.
Ergebnis:
Zum Verständnis wofür sind die konten?
Falls ich privat und arbeit im selben Programm habe?
hier in diesem Bereich viellciht noch irgendwo eine Erklärung einbauen oder so. 
mir ist das schon nicht ganz klar.

[x] 16. Verbindungstest mit falschem Token
Tasten: Anzeigename „GitHub privat“, Benutzername „pascal“, Token „falsch“, dann Alt+V.
Erwartet: NVDA sagt „Der Token wurde abgelehnt.“ Das Fehlerfenster zeigt „Details anzeigen“ mit „HTTP 401 Unauthorized“.
Ergebnis:

[x] 17. Verbindungstest mit richtigem Token
Tasten: im Feld Token „richtig“ eintragen, Alt+V.
Erwartet: Ein Hinweisfenster „Verbindung in Ordnung. Angemeldet als pascal.“ Enter schließt, der Fokus ist wieder auf „Verbindung testen“.
Ergebnis:

[x] 18. Speichern
Tasten: Alt+S.
Erwartet: NVDA sagt „Konto GitHub privat angelegt.“ In der Liste ist „GitHub privat, Testplattform, Plattform, pascal“ markiert.
Ergebnis:

[x] 19. Konto bearbeiten
Tasten: Enter auf dem Konto, Tab bis zum Feld Token, dann Alt+V.
Erwartet: Das Feld Token ist leer. NVDA liest möglicherweise den Hinweis „Leer lassen: bleibt unverändert“. Der Verbindungstest gelingt trotzdem, weil der gespeicherte Token benutzt wird. Escape schließt ohne Änderung.
Ergebnis:

[x] 20. Verbindung testen aus der Liste
Tasten: in der Liste auf dem Konto, Tab bis „Verbindung testen“, Enter.
Erwartet: „Verbindung in Ordnung. Angemeldet als pascal.“
Ergebnis:

[x] 21. Löschen mit Rückfrage
Tasten: in der Liste auf dem Konto Entf, dann Enter.
Erwartet: Rückfrage „Das Konto GitHub privat und seine Zugangsdaten im Tresor werden gelöscht. Auf der Plattform ändert sich nichts. Löschen?“ Vorgabe ist „Abbrechen“. Enter löscht deshalb nichts.
Ergebnis:

[x] 22. Wirklich löschen
Tasten: Entf, dann Tab auf „Löschen“, Enter.
Erwartet: NVDA sagt „Konto GitHub privat gelöscht.“ Die Liste enthält nur noch „Neues Konto anlegen …“.
Ergebnis:


## D. Tresor-Einstellungen

Legen Sie vorher wie in Punkt 15 bis 18 wieder ein Konto mit dem Token „richtig“ an.

[x] 23. Zustand
Tasten: Alt+O, „Tresor-Einstellungen …“, Enter, Pfeiltasten.
Erwartet: Der Fokus steht in der Liste „Tresor“: „Speicherart: Verschlüsselte Tresordatei“, „Zustand: entsperrt“, „Gespeicherte Zugangsdaten: 1 Eintrag“. Mit Tab: Zahlenfeld „Automatisch sperren nach“ mit „nie“, dann „Wechseln zu Windows-Anmeldeinformationsverwaltung …“, „Master-Passwort ändern …“, „Schließen“.
Ergebnis:

[!] 24. Master-Passwort ändern
Tasten: „Master-Passwort ändern …“. Erst ein falsches bisheriges Passwort, beim zweiten Versuch „Testpasswort1“ und zweimal „Neuespasswort2“.
Erwartet: Beim falschen: „Das bisherige Master-Passwort ist falsch.“ Beim richtigen: „Master-Passwort geändert.“
Ergebnis: Nach masterpassowrt auf speichern klicken, sollte er auf schließen springen der fokus, sonst ist das verwirrend.

[!] 25. Automatisch sperren
Tasten: Im Zahlenfeld mit Pfeil hoch 1 Minute einstellen, Fenster schließen, eine Minute keine Taste drücken.
Erwartet: NVDA sagt „Der Tresor wurde nach 1 Minute ohne Eingabe gesperrt.“ Im Menü Konten steht wieder „Tresor entsperren …“.
Ergebnis: Wei´ß nicht ob es an mir lag, aber er hat ncihts gemacht, aber mein rechner geht auch in standby, also wenn es bei dir gin, vertraue darauf.

[x] 26. Speicherart wechseln
Tasten: Tresor entsperren (Passwort „Neuespasswort2“), Tresor-Einstellungen öffnen, „Wechseln zu Windows-Anmeldeinformationsverwaltung …“, in der Rückfrage „Wechseln“.
Erwartet: Die Rückfrage nennt die Zahl der Einträge und sagt, dass nichts neu eingegeben werden muss. Danach sagt NVDA „Speicherart gewechselt. 1 Eintrag übertragen.“ Die Liste zeigt „Speicherart: Windows-Anmeldeinformationsverwaltung“. „Master-Passwort ändern“ und das Zahlenfeld sind verschwunden.
Ergebnis:

[x] 27. Konto nach dem Wechsel
Tasten: Kontenverwaltung, Konto, „Verbindung testen“.
Erwartet: „Verbindung in Ordnung.“ Der Token wurde also mit übertragen. Im Menü Konten gibt es kein „Tresor sperren“ mehr.
Ergebnis:


## E. Weitere Fälle

[x] 28. Assistent erneut starten
Tasten: Alt+E, „Einrichtungsassistent …“, Enter, dann Escape.
Erwartet: Der Assistent öffnet sich. Escape schließt ihn ohne Rückfrage, weil die Einrichtung schon erledigt ist.
Ergebnis:

[x] 29. Zweites Fenster mit Testdaten
Tasten: Das Cockpit offen lassen und `start_testdaten.bat` noch einmal starten.
Erwartet: Eine Meldung „Die Testdaten werden noch von einem offenen CodeCockpit benutzt. Bitte schließen Sie zuerst alle Fenster von CodeCockpit mit Testdaten.“ Das offene Cockpit arbeitet normal weiter.
Ergebnis:

[x] 30. Einrichtung abbrechen
Tasten: Alle Cockpit-Fenster schließen, `start_testdaten.bat` starten, im Assistenten Escape.
Erwartet: Rückfrage „Einrichtung abbrechen? Das Cockpit wird beendet. …“ Vorgabe ist „Weiter einrichten“: Enter lässt den Assistenten offen. Nochmals Escape, dann „Abbrechen und beenden“: Das Programm schließt.
Ergebnis:


## F. Ihre echte Einrichtung

[ ] 31. Echter Start
Tasten: `start.bat` starten.
Erwartet: Der Assistent erscheint, weil Ihr echtes Cockpit noch nicht eingerichtet ist. Wählen Sie den Tresor, den Sie wirklich nutzen möchten. Empfohlen ist die Windows-Anmeldeinformationsverwaltung. Bei der Git-Identität tragen Sie „1013hPascal“ und `94653295+1013hPascal@users.noreply.github.com` ein. Am Ende öffnet sich das Hauptfenster mit „Codecockpit“.
Ergebnis:

Platz für Ihren Kommentar:
Eine Frage, wofür sind die konen, also nicht entfernen nur erklären. 
Und eine ander Frage, ich habe ja schon ein acount. trotzdem diese mail da eintragen? oder welche mail ist bei mir biher bei den commits von 1013hpascal eingetragen, dass ich die selbe nehme die ich bisher hatte. Sonst gibt das ein durcheinander.

## G. Nachtest nach Ihren Rückmeldungen (25.09.2026)

Bitte alle Cockpit-Fenster schließen und `start_testdaten.bat` neu starten.

[ ] 32. Tresor-Seite: erst die Erklärung
Tasten: im Assistenten zweimal Alt+W.
Erwartet: Der Fokus steht in der Liste „Erklärung“. Sie hat jetzt sieben Zeilen, darunter „Gesperrt heißt: …“ und als letzte „Mit Tab kommen Sie zur Auswahl der Speicherart.“
Ergebnis:

[ ] 33. Speicherart als Liste
Tasten: Tab, dann Pfeil runter und hoch.
Erwartet: Eine Liste „Speicherart“ mit zwei Einträgen. NVDA nennt jeweils nur den Eintrag, auf dem Sie stehen, zum Beispiel „Verschlüsselte Tresordatei mit Master-Passwort, 2 von 2“. Gewählt ist immer der markierte Eintrag. Enter in der Liste wirkt wie Weiter.
Ergebnis:

[ ] 34. Erklärung zu den Konten
Tasten: nach der Einrichtung Alt+O, Kontenverwaltung, Ende-Taste, Enter.
Erwartet: Der letzte Eintrag heißt „Wofür sind Konten? …“. Enter öffnet eine Liste mit der Erklärung. Escape führt zurück in die Kontenliste.
Ergebnis:

[ ] 35. Fokus nach dem Passwortwechsel
Tasten: Tresor-Einstellungen, Master-Passwort ändern, richtig ausfüllen, Speichern.
Erwartet: NVDA sagt „Master-Passwort geändert.“ Der Fokus steht danach auf „Schließen“.
Ergebnis:

[ ] 36. Automatisch sperren, zweiter Versuch
Tasten: Tresor-Einstellungen, „Automatisch sperren nach“ auf 1 Minute, Schließen. Dann etwa eine Minute keine Taste drücken und auch nicht NVDA-Befehle benutzen, die die Tastatur an das Programm schicken.
Erwartet: Spätestens 15 Sekunden nach Ablauf der Minute sagt NVDA „Der Tresor wurde nach 1 Minute ohne Eingabe gesperrt.“ Geht der Rechner in den Standby, wird direkt nach dem Aufwachen gesperrt.
Ergebnis:
