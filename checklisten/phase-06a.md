# Checkliste Phase 6a: Pull Requests

Stand: 26.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- Bei Code gibt es „Pull Requests …“ und, wenn Sie nicht auf main sind, „Pull Request erstellen …“.
- Die Liste zeigt die offenen Pull Requests. Oben wählen Sie auch geschlossene oder alle.
- Die Details zeigen Angaben, geänderte Dateien und Kommentare. Dort können Sie kommentieren, einen Entwurf zum Prüfen freigeben, schließen und wieder öffnen.
- Code und die Übersicht Branches nennen offene Pull Requests.


## Vorbereitung

Pull Requests gibt es nur auf GitHub. Deshalb legen Sie wieder ein privates Test-Repository „codecockpit-test“ auf Ihrem echten Konto an. Es wird am Ende von Phase 6 gelöscht.

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten: Windows-Anmeldeinformationsverwaltung, Anmeldung bei GitHub im Browser mit Ihrem echten Konto, noreply-Adresse übernehmen.
3. „Projekt vom Rechner hinzufügen“, den Ordner `Testdaten\Andere Ordner\Wetter` wählen. Auf „Jetzt hochladen?“ mit „Jetzt hochladen …“ antworten.
4. Im Fenster zum Hochladen den Namen in `codecockpit-test` ändern, privat lassen, hochladen.
5. Danach steht in der Liste „Wetter“. Auf GitHub heißt es codecockpit-test.


## A. Erster Pull Request

[ ] 1. Aktionen bei Code
Tasten: Zu Code von Wetter, Tab, durch die Aktionen.
Erwartet: „Pull Requests …“ steht nach „Branches …“. „Pull Request erstellen …“ gibt es nicht, weil Sie auf main sind.
Ergebnis:

[ ] 2. Branch mit einer Änderung
Tasten: „Branches …“, „Neuer Branch …“, Name `groessere-schrift`, Enter, Escape. Dann im Explorer die Datei `Wetter\Code\wetter.py` öffnen, eine Zeile `print('Größer')` anhängen, speichern. Zurück im Cockpit bei Code „Änderungen hochladen …“, als Nachricht `Größere Schrift`, „Hochladen“.
Erwartet: NVDA sagt am Ende „Fertig. Commit „Größere Schrift“. Branch groessere-schrift ist hochgeladen.“ Die Zeile Code nennt „Branch groessere-schrift“.
Ergebnis:

[ ] 3. Pull Request erstellen
Tasten: Bei Code „Pull Request erstellen …“, Enter. Mit Tab durch das Fenster, dann „Erstellen“.
Erwartet: Das Fenster heißt „Pull Request erstellen: von groessere-schrift“. Der Fokus steht im Feld „Titel“ mit „Größere Schrift“. Danach kommen „Beschreibung“, „Ziel-Branch, dahin sollen die Änderungen aus groessere-schrift“ mit main, „Prüfer, freiwillig“ und „Als Entwurf erstellen“, nicht angekreuzt. Ohne Mitarbeiter steht bei den Prüfern „Keine Mitarbeiter, die prüfen könnten.“ Nach „Erstellen“ sagt NVDA „Pull Request wird erstellt.“ und „Pull Request Nr. 1 erstellt.“
Ergebnis:

[ ] 4. Anzeige bei Code und Branches
Tasten: Die Zeile Code lesen. Dann „Branches …“ und die Zeile von groessere-schrift lesen, Escape.
Erwartet: Code endet mit „1 offener Pull Request“. In den Branches steht bei groessere-schrift ebenfalls „1 offener Pull Request“.
Ergebnis:


## B. Liste und Details

[ ] 5. Liste
Tasten: Bei Code „Pull Requests …“, Enter. Die Liste lesen. Umschalt+Tab zu „Anzeigen“ und mit den Pfeiltasten die Auswahl lesen, zurück auf „offene“.
Erwartet: NVDA sagt „Pull Requests werden abgefragt.“ Das Fenster heißt „Pull Requests von codecockpit-test: 1 Pull Request, offene“. Der Fokus steht auf „Nr. 1: Größere Schrift, von groessere-schrift nach main, von …“ mit Ihrem Benutzernamen. Die Auswahl bietet „offene“, „geschlossene“ und „alle“.
Ergebnis:

[ ] 6. Details
Tasten: Auf Nr. 1 Enter. Die Liste Angaben lesen, dann mit Tab zu Dateien, Kommentaren, dem Feld „Neuer Kommentar“ und den Knöpfen.
Erwartet: Die Angaben beginnen mit „Nr. 1: Größere Schrift“, „Offen“, „Von groessere-schrift nach main“ und „Erstellt von … am …“. Die Dateien zeigen „wetter.py, geändert, 1 Zeile dazu“. Die Kommentare sagen „Noch keine Kommentare.“ Die Knöpfe sind „Kommentar senden“, „Pull Request schließen …“, „Im Browser öffnen“ und „Schließen“.
Ergebnis:

[ ] 7. Kommentieren
Tasten: Im Feld „Neuer Kommentar“ `Bitte prüfen` schreiben. Tab zu „Kommentar senden“, Enter.
Erwartet: NVDA sagt „Kommentar gesendet.“ Der Fokus steht in der Liste der Kommentare auf „…, <heutiges Datum>: Bitte prüfen“ mit Ihrem Namen vorne. Das Feld ist wieder leer.
Ergebnis:

[ ] 8. Im Browser
Tasten: „Im Browser öffnen“, Enter. Im Browser den Kommentar suchen. Zurück ins Cockpit.
Erwartet: GitHub zeigt den Pull Request Nr. 1 mit Ihrem Kommentar.
Ergebnis:

[ ] 9. Schließen und wieder öffnen
Tasten: „Pull Request schließen …“, die Frage lesen, „Schließen“. Dann „Wieder öffnen“.
Erwartet: Die Frage sagt, dass Nr. 1 geschlossen wird, ohne übernommen zu werden, und der Branch erhalten bleibt. Vorgabe ist „Abbrechen“. NVDA sagt „Nr. 1 ist geschlossen.“ Der Knopf heißt dann „Wieder öffnen“. Danach sagt NVDA „Nr. 1 ist wieder offen.“
Ergebnis:


## C. Entwurf mit Hochladen vorher

[ ] 10. Hochladen beim Erstellen
Tasten: Alle Fenster bis zur Aktionsliste schließen. „Branches …“, „Neuer Branch …“, Name `entwurf`, Escape. In wetter.py noch eine Zeile `print('Entwurf')` anhängen und speichern. Bei Code „Pull Request erstellen …“. Die Frage lesen, „Hochladen und weiter“. Im Fenster zum Hochladen `Entwurf` schreiben, „Hochladen“.
Erwartet: Die Frage sagt „Der Branch entwurf ist noch nicht auf GitHub. Das Cockpit lädt den Branch zuerst hoch …“. Vorgabe ist „Abbrechen“. Nach dem Hochladen öffnet sich gleich „Pull Request erstellen: von entwurf“ mit dem Titel „Entwurf“.
Ergebnis:

[ ] 11. Als Entwurf erstellen
Tasten: Mit Tab zu „Als Entwurf erstellen“, Leertaste, dann „Erstellen“.
Erwartet: NVDA sagt „Pull Request Nr. 2 erstellt als Entwurf.“
Ergebnis:

[ ] 12. Entwurf freigeben
Tasten: „Pull Requests …“, auf Nr. 2 Enter. Die Angaben lesen. Tab bis „Zum Prüfen freigeben“, Enter, „Freigeben“.
Erwartet: Die Zeile in der Liste endet mit „Entwurf“. Die Angaben sagen „Offen, Entwurf“. Die Frage hat die Vorgabe „Abbrechen“. Danach sagt NVDA „Zum Prüfen freigegeben.“ Der Knopf verschwindet, die Angaben sagen nur noch „Offen“.
Ergebnis:

[ ] 13. Geschlossene anzeigen
Tasten: Nr. 2 schließen wie in Punkt 9. Escape zur Liste. Umschalt+Tab zu „Anzeigen“, „geschlossene“ wählen, Tab in die Liste.
Erwartet: In der Liste der offenen steht nur noch Nr. 1. Bei „geschlossene“ steht „Nr. 2: Entwurf, von entwurf nach main, von …, geschlossen“.
Ergebnis:


## D. Auf main

[ ] 14. Auf main gibt es kein Erstellen
Tasten: „Branches …“, auf main Enter (Wechseln), Escape. Bei Code die Aktionen lesen. Dann „Pull Requests …“, Tab zu „Neuer Pull Request …“, Enter.
Erwartet: „Pull Request erstellen …“ steht nicht in der Aktionsliste. Im Fenster Pull Requests sagt „Neuer Pull Request …“: „Sie sind auf main. Ein Pull Request bringt die Änderungen aus einem anderen Branch nach main. …“
Ergebnis:

Das Repository codecockpit-test bleibt für 6b bestehen. Dort übernehmen Sie Nr. 1 in main.
