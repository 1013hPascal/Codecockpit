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

[ ] 1. Ordner wählen
Tasten: In der Projektliste ganz oben „Neues Projekt hochladen“, Enter. Im Fenster „Ordner mit dem Code wählen“ den Pfad aus der Vorbereitung eintippen, Enter.
Erwartet: Ein Fenster „Neues Projekt hochladen“ öffnet sich. Der Fokus steht im Feld „Name auf GitHub“ mit „codecockpit-test“.
Ergebnis:

[ ] 2. Felder
Tasten: Mehrmals Tab.
Erwartet: Es folgen „Kurzbeschreibung“, „Sichtbarkeit“ mit „Privat“, „Lizenz“ mit „MIT“, „Ziel“ mit „Eigenes Konto 1013hPascal“ (und Ihren Organisationen, falls Sie welche haben), dann „Weiter …“ und „Abbrechen“.
Ergebnis:

[ ] 3. Ungültiger Name
Tasten: Im Feld „Name auf GitHub“ „Mein Test“ eintippen, Alt+W.
Erwartet: Eine Meldung sagt, dass der Name nur Buchstaben ohne Umlaute, Ziffern, Punkt, Bindestrich und Unterstrich enthalten darf. Nach OK steht der Fokus wieder im Feld „Name auf GitHub“. Tragen Sie danach wieder „codecockpit-test“ ein.
Ergebnis:

[ ] 4. Öffentlich wird erklärt
Tasten: „Sichtbarkeit“ auf „Öffentlich“ stellen, Alt+W. Die Frage lesen, dann Escape.
Erwartet: Die Frage endet mit „Öffentlich heißt: Jeder im Internet kann den Code sehen. Hochladen?“. Vorgabe ist „Abbrechen“. Nach Escape passiert nichts, auch im Ordner Projekte entsteht nichts.
Ergebnis:


## B. Sicherheitsprüfung

[ ] 5. Rückfrage vor dem Hochladen
Tasten: Wie in Punkt 1, diesmal „Privat“ lassen, Alt+W. Die Frage lesen.
Erwartet: Die Frage sagt: Das Cockpit kopiert den Ordner nach `…\Testdaten\Projekte\codecockpit-test\Code`. Die virtuelle Umgebung und Caches kommen nicht mit. Der alte Ordner bleibt unverändert. Es prüft auf Geheimnisse, legt das private Repository 1013hPascal/codecockpit-test an und lädt alles hoch. Die Knöpfe heißen „Hochladen“ und „Abbrechen“.
Ergebnis:

[ ] 6. Fenster Sicherheitsprüfung
Tasten: „Hochladen“. Warten, bis ein neues Fenster kommt. Pfeiltasten in der Liste.
Erwartet: NVDA sagt „Wird vorbereitet.“ Das Fenster heißt „Sicherheitsprüfung: 3 Funde stoppen das Hochladen, 1 Warnung“. Die Liste „Funde“ enthält:
- „Geheimnis: .env, Datei mit Zugangsdaten. Stoppt das Hochladen“
- „Geheimnis: config.py, Zeile 1, GitHub-Token. Stoppt das Hochladen“
- „Geheimnis: config.py, Zeile 2, Passwort oder Schlüssel im Code. Stoppt das Hochladen“
- „Private Daten: daten.db, Datenbank. Kommt in .gitignore“
Kein Eintrag nennt den Token oder das Passwort selbst.
Ergebnis:

[ ] 7. Weiter ist gesperrt, Escape bricht ab
Tasten: Tab durch die Knöpfe, dann Escape.
Erwartet: Die Knöpfe heißen „In .gitignore aufnehmen“, „Kein Geheimnis“, „Trotzdem hochladen“, „Datei öffnen“, „Erneut prüfen“, „Weiter“ und „Abbrechen“. „Weiter“ ist nicht verfügbar. Nach Escape sagt NVDA „Hochladen abgebrochen. codecockpit-test ist in der Liste. Mit Auf GitHub hochladen geht es später weiter.“ In der Projektliste steht „codecockpit-test, noch nicht auf GitHub“.
Ergebnis:

[ ] 8. Auf GitHub hochladen
Tasten: codecockpit-test ausklappen, auf „Code“ Tab.
Erwartet: Die erste Aktion heißt „Auf GitHub hochladen …“. Enter auf der Zeile „Code“ in der Projektliste startet sie ebenfalls. Es kommt wieder das Fenster mit den Angaben, dann die Rückfrage. Diesmal steht dort nichts vom Kopieren. Wählen Sie „Hochladen“.
Ergebnis:

[ ] 9. .env in .gitignore aufnehmen
Tasten: Im Fenster Sicherheitsprüfung auf der Zeile mit .env Alt+G („In .gitignore aufnehmen“).
Erwartet: NVDA sagt „.env kommt in .gitignore und wird nicht hochgeladen.“ Die Zeile verschwindet. Der Fokus steht wieder in der Liste.
Ergebnis:

[ ] 10. Token in der Datei entfernen
Tasten: Auf der Zeile „config.py, Zeile 1, GitHub-Token“ Alt+F („Datei öffnen“). Im Editor die erste Zeile löschen, speichern, Editor schließen. Zurück im Cockpit Alt+E („Erneut prüfen“).
Erwartet: NVDA sagt „Geprüft: 1 Fund stoppt das Hochladen, 1 Warnung“. Die Zeile mit dem Token ist weg.
Ergebnis:

[ ] 11. Kein Geheimnis
Tasten: Auf der Zeile „config.py, Zeile 2, Passwort oder Schlüssel im Code“ Alt+K („Kein Geheimnis“).
Erwartet: NVDA sagt „Als kein Geheimnis markiert.“ Die Zeile verschwindet. Das Fenster heißt jetzt „Sicherheitsprüfung: 1 Warnung“. „Weiter“ ist verfügbar.
Ergebnis:

[ ] 12. Hochladen
Tasten: Alt+W („Weiter“) und warten.
Erwartet: NVDA sagt nacheinander „Schritt 1 von 4: Sicherheitsprüfung …“, „Schritt 2 von 4: Commit wird erstellt …“, „Schritt 3 von 4: Repository wird angelegt …“ und „Schritt 4 von 4: Wird hochgeladen …“. Dann kommt eine Meldung mit OK: „Fertig. Neues privates Repository 1013hPascal/codecockpit-test. Branch main ist hochgeladen. Der Link https://github.com/1013hPascal/codecockpit-test ist in der Zwischenablage.“
Ergebnis:


## C. Ergebnis prüfen

[ ] 13. Projektliste
Tasten: Nach OK die Projektliste ansehen, codecockpit-test ausklappen.
Erwartet: „codecockpit-test, aktualisiert am“ mit dem heutigen Datum. Darunter „Code, alles hochgeladen“. Es gibt keine zweite Zeile „codecockpit-test, nur auf GitHub“.
Ergebnis:

[ ] 14. Auf GitHub
Tasten: Im Browser den Link aus der Zwischenablage öffnen.
Erwartet: Das Repository ist privat. Es enthält main.py, config.py, LICENSE, .gitignore und cockpit.toml. Es enthält nicht .env und nicht daten.db. Der Commit heißt „Erste Version“ und ist von Ihnen. LICENSE ist die MIT-Lizenz mit Ihrem Namen und dem Jahr 2026.
Ergebnis:

[ ] 15. Alter Ordner unverändert
Tasten: Im Explorer den Ordner aus der Vorbereitung öffnen.
Erwartet: Dort liegen noch alle vier Dateien, auch .env und daten.db. config.py hat dort noch beide Zeilen, denn Sie haben die Kopie im Ordner Projekte bearbeitet.
Ergebnis:


## D. Sonderfälle

[ ] 16. Ordner, der schon ein Projekt ist
Tasten: „Neues Projekt hochladen“, Ordner `C:\Users\pasca\AppData\Local\CodeCockpit\Testdaten\Projekte\PDF-Chat` wählen.
Erwartet: Eine Meldung: „Der Ordner gehört schon zum Projekt PDF-Chat. Wählen Sie dort bei Code die Aktion Auf GitHub hochladen.“ Danach steht der Fokus auf PDF-Chat.
Ergebnis:
