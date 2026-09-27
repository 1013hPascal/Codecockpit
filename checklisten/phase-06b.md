# Checkliste Phase 6b: Prüfen, Änderungen ansehen, Übernehmen

Stand: 27.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- In der Liste der Pull Requests gibt es „Prüfen …“ und „In main übernehmen …“. Beide erscheinen bei offenen Pull Requests, die kein Entwurf sind.
- Die Liste nennt Genehmigungen, zum Beispiel „1 Genehmigung“ oder „Änderungen angefordert“.
- Die Details nennen, ob GitHub übernehmen kann. Enter auf einer Datei zeigt ihre Änderungen lesbar: „Neu Zeile 12: …“ und „Weg Zeile 8: …“.
- Die Kommentare zeigen auch die Reviews.
- Nach dem Übernehmen bietet das Cockpit an aufzuräumen: zu main wechseln, holen, den Branch löschen.

Genehmigen und Änderungen anfordern prüfen nur die automatischen Tests. Bei Ihrem eigenen Pull Request erlaubt GitHub das nicht, und ein zweites Konto gibt es nicht.


## Vorbereitung

1. Sie brauchen den Stand nach 6a: das Projekt Wetter mit dem Repository codecockpit-test, der offene Pull Request Nr. 1 und Sie auf main.
2. Haben Sie die Testdaten seitdem neu gestartet, gehen Sie zuerst die Vorbereitung und die Punkte 2 und 3 aus `checklisten\phase-06a.md` noch einmal durch. Das Repository auf GitHub gibt es dann schon. Laden Sie in diesem Fall unter einem anderen Namen hoch, zum Beispiel `codecockpit-test-2`.


## A. Liste und Details

[ ] 1. Knöpfe in der Liste
Tasten: Bei Code von Wetter „Pull Requests …“. Auf Nr. 1 mit Tab durch die Knöpfe.
Erwartet: Die Knöpfe sind „Details …“, „Kommentare …“, „Prüfen …“, „In main übernehmen …“, „Pull Request schließen …“, „Neuer Pull Request …“, „Im Browser öffnen“ und „Schließen“.
Ergebnis:

[ ] 2. Stand in den Details
Tasten: Auf Nr. 1 Enter. Die Angaben lesen.
Erwartet: Nach „Offen“ steht „Kann übernommen werden“. Gibt GitHub den Stand noch nicht an, fehlt diese Zeile. Dann nach einigen Sekunden die Details neu öffnen.
Ergebnis:

[ ] 3. Änderungen einer Datei
Tasten: Tab in die Liste Dateien, auf „wetter.py, geändert, 1 Zeile dazu“ Enter. Lesen, Escape.
Erwartet: Das Fenster heißt „Änderungen in wetter.py: 1 Zeile“. Die Zeile heißt „Neu Zeile …: print('Größer')“ mit der Nummer der Zeile. Escape führt zurück zur Liste der Dateien.
Ergebnis:


## B. Prüfen

[ ] 4. Eigener Pull Request
Tasten: Zurück in der Liste auf Nr. 1 „Prüfen …“, Enter. Den Hinweis lesen, dann mit Tab zu „Ergebnis“ und mit den Pfeiltasten lesen.
Erwartet: Das Fenster heißt „Prüfen: Nr. 1: Größere Schrift“. Der Hinweis sagt, dass GitHub bei Ihrem eigenen Pull Request nur einen Kommentar erlaubt. „Ergebnis“ bietet deshalb nur „Nur kommentieren“.
Ergebnis:

[ ] 5. Review abgeben
Tasten: Ohne Kommentar „Review abgeben“. Nach der Meldung im Feld „Kommentar zum Review“ `Sieht gut aus` schreiben, „Review abgeben“.
Erwartet: Ohne Kommentar sagt eine Meldung „Bitte schreiben Sie dazu einen Kommentar. Nur beim Genehmigen darf er fehlen.“ Danach sagt NVDA „Review abgegeben.“
Ergebnis:

[ ] 6. Review bei den Kommentaren
Tasten: „Kommentare …“, die Liste lesen, Escape.
Erwartet: Unten steht „… Review, <heutiges Datum>: Sieht gut aus“ mit Ihrem Namen vorne.
Ergebnis:


## C. Übernehmen

[ ] 7. Übernehmen, erst abbrechen
Tasten: „In main übernehmen …“, Enter. Die Liste „Stand“ lesen, Tab zu „Art des Übernehmens“ und mit den Pfeiltasten lesen. Dann Escape.
Erwartet: Das Fenster heißt „In main übernehmen: Nr. 1: Größere Schrift“. Der Stand sagt, dass die Änderungen aus groessere-schrift nach main kommen und sich das nicht einfach rückgängig machen lässt. Die Arten sind „Merge-Commit: …“, „Squash: …“ und „Rebase: …“, jede mit einem kurzen Satz. Vorgabe beim Knopf ist „Abbrechen“. Nach Escape ist nichts passiert.
Ergebnis:

[ ] 8. Übernehmen
Tasten: Noch einmal „In main übernehmen …“. „Merge-Commit“ lassen, Tab zu „Übernehmen“, Enter.
Erwartet: NVDA sagt „Nr. 1 ist in main übernommen.“ Dann fragt das Cockpit, ob es zu main wechseln, die Änderungen holen und den Branch groessere-schrift hier und auf GitHub löschen soll. Die Knöpfe sind „Aufräumen“ und „Später“. Vorgabe ist „Später“.
Ergebnis:

[ ] 9. Aufräumen
Tasten: „Aufräumen“.
Erwartet: NVDA sagt „Wird aufgeräumt.“ und danach „Die Änderungen von main sind geholt. Der Branch groessere-schrift ist gelöscht.“ Sind Sie vorher nicht auf main gewesen, beginnt es mit „Sie sind auf main.“
Ergebnis:

[ ] 10. Nach dem Übernehmen
Tasten: In der Liste „Anzeigen“ auf „alle“. Nr. 1 markieren, mit Tab durch die Knöpfe. Dann Fenster schließen, Code lesen, „Branches …“ lesen. Im Explorer wetter.py öffnen.
Erwartet: Nr. 1 endet mit „übernommen“. Bei ihr gibt es weder „Prüfen …“ noch „In main übernehmen …“ noch „Pull Request schließen …“. Code nennt keinen offenen Pull Request mehr. In den Branches fehlt groessere-schrift. wetter.py enthält die Zeile `print('Größer')`.
Ergebnis:

Das Repository codecockpit-test bleibt für 6c bestehen.
