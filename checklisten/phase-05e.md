# Checkliste Phase 5e: Links, Repository verwalten, Aus der Liste entfernen

Stand: 26.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- Beim Projekt gibt es „Links …“, „Repository verwalten …“ und „Aus der Liste entfernen …“.
- „Repository verwalten“ kann öffentlich oder privat machen, Mitarbeiter einladen und entfernen, archivieren, die Archivierung aufheben und löschen.
- Zum Löschen holt das Cockpit mit einer zweiten, kurzen Anmeldung im Browser nur das Recht zum Löschen. Der Zugang daraus wird nicht gespeichert.
- Bei „nur auf GitHub“ gibt es ebenfalls „Aus der Liste entfernen …“.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten wählen Sie die Windows-Anmeldeinformationsverwaltung. Melden Sie sich auf der Seite „GitHub-Konto“ im Browser mit Ihrem echten Konto an. Übernehmen Sie die noreply-Adresse.
3. Geprüft wird mit Ihrem privaten Repository „codecockpit-test“ aus Phase 5b. Am Ende von Abschnitt E löschen Sie es.
4. Die Beispielprojekte PDF-Chat, Tagebuch und Rezepte haben keine echte Adresse auf GitHub. Bei ihnen gibt es deshalb weder „Links“ noch „Repository verwalten“.


## A. Projekt holen

[ ] 1. codecockpit-test herunterladen
Tasten: In der Projektliste zu „codecockpit-test, nur auf GitHub“. Enter.
Erwartet: NVDA sagt „codecockpit-test wird heruntergeladen.“ und danach „codecockpit-test heruntergeladen.“ In der Liste steht jetzt das Projekt codecockpit-test.
Ergebnis:

[ ] 2. Aktionen beim Projekt
Tasten: Auf der Zeile codecockpit-test selbst Tab, nicht auf Code. Ist das Projekt ausgeklappt, führt Pfeil links von Code zurück zum Projekt. Dann mit den Pfeiltasten durch die Aktionen.
Erwartet: Unter anderem stehen dort in dieser Reihenfolge „Projekt neu einlesen“, „Links …“, „Repository verwalten …“, „Projektordner öffnen“ und ganz unten „Aus der Liste entfernen …“.
Ergebnis:


## B. Links

[ ] 3. Links anzeigen und kopieren
Tasten: „Links …“, Enter. Mit den Pfeiltasten lesen. Auf der ersten Zeile Enter.
Erwartet: Das Fenster heißt „Links von codecockpit-test“. Die Zeilen sind „Projektseite: https://github.com/1013hPascal/codecockpit-test“ und „README: …#readme“. Enter sagt „Link zu Projektseite kopiert.“ Der Link liegt in der Zwischenablage.
Ergebnis:

[ ] 4. Link öffnen
Tasten: Tab zu „Im Browser öffnen“, Enter. Zurück ins Cockpit, Escape.
Erwartet: Die Seite des Repositories öffnet sich im Browser. Escape schließt das Fenster Links.
Ergebnis:


## C. Repository verwalten

[ ] 5. Angaben
Tasten: „Repository verwalten …“, Enter. Die Liste lesen, dann mit Tab durch die Knöpfe.
Erwartet: NVDA sagt „Repository wird abgefragt.“ Das Fenster heißt „Repository verwalten: codecockpit-test“. Die Angaben sind „1013hPascal/codecockpit-test auf GitHub“, „Privat, nur Sie und Ihre Mitarbeiter sehen den Code“ und „Adresse: …“. Die Knöpfe sind „Öffentlich machen …“, „Mitarbeiter …“, „Archivieren …“, „Löschen …“ und „Schließen“.
Ergebnis:

[ ] 6. Öffentlich machen, abbrechen
Tasten: „Öffentlich machen …“, Enter. Die Meldung oder Frage lesen. Gibt es eine Frage, Escape.
Erwartet: NVDA sagt „Sicherheitsprüfung läuft.“ Danach kommt eines von beiden:
- Findet die Prüfung ein Geheimnis, sagt eine Meldung, dass das Cockpit codecockpit-test nicht öffentlich macht. Das Geheimnis selbst steht nicht in der Meldung.
- Sonst fragt das Cockpit: „codecockpit-test wird öffentlich. Jeder im Internet kann danach den Code und den ganzen Verlauf sehen. Öffentlich machen?“, eventuell mit Warnungen davor. Vorgabe ist „Abbrechen“.
In beiden Fällen bleibt das Repository privat.
Ergebnis:


## D. Mitarbeiter und Archivieren

[ ] 7. Mitarbeiter anzeigen
Tasten: „Mitarbeiter …“, Enter. Die Liste lesen.
Erwartet: Das Fenster heißt „Mitarbeiter von codecockpit-test: …“. Ohne Mitarbeiter steht dort „Noch keine Mitarbeiter.“ Die Knöpfe sind „Einladen …“, „Entfernen …“ und „Schließen“.
Ergebnis:

[ ] 8. Unbekannten Benutzer einladen
Tasten: „Einladen …“. Im Feld „Benutzername auf GitHub“ zum Beispiel `gibt-es-sicher-nicht-4711` eintippen. Tab zu „Recht“, mit den Pfeiltasten lesen. Enter.
Erwartet: Das Feld „Recht“ bietet „lesen“, „schreiben“ und „verwalten“. Vorgabe ist „schreiben“. Danach kommt eine Meldung: „Den Benutzer gibt-es-sicher-nicht-4711 gibt es auf GitHub nicht …“.
Ergebnis:

[ ] 9. Einladen und zurückziehen (freiwillig)
Tasten: Nur, wenn Sie ein zweites GitHub-Konto haben oder jemanden kennen, der eine Einladung bekommen darf. „Einladen …“ mit diesem Namen. Danach auf die neue Zeile, „Entfernen …“, „Zurückziehen“.
Erwartet: NVDA sagt „Einladung an … verschickt.“ Die Zeile heißt „…, eingeladen, schreiben“. Nach dem Zurückziehen sagt NVDA „Einladung an … zurückgezogen.“ und die Zeile ist weg.
Ergebnis:

[ ] 10. Archivieren
Tasten: Escape zurück zu „Repository verwalten“. „Archivieren …“, Frage lesen, „Archivieren“. Die Angaben lesen.
Erwartet: Die Frage sagt, dass das Repository schreibgeschützt wird, erhalten bleibt und die Archivierung sich jederzeit aufheben lässt. Vorgabe ist „Abbrechen“. Danach sagt NVDA „codecockpit-test ist archiviert.“ Die Angaben enthalten „Archiviert, schreibgeschützt“. Der Knopf heißt jetzt „Archivierung aufheben …“.
Ergebnis:

[ ] 11. Archivierung aufheben
Tasten: „Archivierung aufheben …“, „Archivierung aufheben“.
Erwartet: NVDA sagt „Archivierung von codecockpit-test aufgehoben.“ Die Zeile „Archiviert“ ist weg.
Ergebnis:


## E. Löschen

[ ] 12. Löschen, erst abbrechen
Tasten: „Löschen …“, Enter. Die Frage lesen, Escape.
Erwartet: Die Frage sagt, dass Löschen sich nicht rückgängig machen lässt, dass der Ordner auf Ihrem Rechner immer erhalten bleibt und dass Archivieren sanfter ist. Die Knöpfe sind „Weiter zum Löschen …“, „Stattdessen archivieren …“ und „Abbrechen“. Vorgabe ist „Abbrechen“.
Ergebnis:

[ ] 13. Falscher Name
Tasten: „Löschen …“, „Weiter zum Löschen …“. Im Feld `codecockpit` eintippen (ohne „-test“). Tab zu „Endgültig löschen“, Enter.
Erwartet: Das Fenster heißt „codecockpit-test endgültig löschen“, das Feld „Zur Bestätigung den Namen eintippen: codecockpit-test“. Vorgabe ist „Abbrechen“, Enter im Feld löscht also nicht. Nach „Endgültig löschen“ kommt „Der eingetippte Name stimmt nicht. Es wurde nichts gelöscht.“ Danach steht der Fokus wieder im Feld.
Ergebnis:

[ ] 14. Zweite Anmeldung
Tasten: Den Namen richtig eintippen: `codecockpit-test`. „Endgültig löschen“. Die Frage lesen, „Im Browser bestätigen …“. Im Browser den Code einfügen, Continue. Die Seite von GitHub lesen, Authorize.
Erwartet: Die Frage sagt, dass das Cockpit ein zusätzliches Recht braucht und der Zugang nur für dieses eine Löschen benutzt und nicht gespeichert wird. Vorgabe ist „Abbrechen“. Das Fenster „Recht zum Löschen holen“ zeigt den Code wie bei der ersten Anmeldung. Auf GitHub steht beim Bestätigen, dass CodeCockpit Repositories löschen darf.
Ergebnis:

[ ] 15. Gelöscht, nur lokal behalten
Tasten: Nach dem Authorize zurück ins Cockpit. Die Frage lesen, „Nur lokal behalten“.
Erwartet: NVDA sagt „Angemeldet als …“, dann „Wird gelöscht.“ und „codecockpit-test ist auf GitHub gelöscht.“ Die Frage nennt den Ordner auf Ihrem Rechner und die zwei Möglichkeiten. Vorgabe ist „Nur lokal behalten“. Danach steht in der Liste „codecockpit-test, noch nicht auf GitHub“. Auf github.com gibt es das Repository nicht mehr.
Ergebnis:


## F. Aus der Liste entfernen

[ ] 16. Projekt entfernen, erst abbrechen
Tasten: Auf codecockpit-test Tab, „Aus der Liste entfernen …“, Enter. Die Frage lesen, Escape.
Erwartet: Die Frage sagt, dass codecockpit-test nur aus der Liste des Cockpits entfernt wird, der Ordner unverändert bleibt und das Projekt mit „Projekt vom Rechner hinzufügen“ jederzeit zurückkommt. Vorgabe ist „Abbrechen“.
Ergebnis:

[ ] 17. Projekt entfernen
Tasten: Noch einmal, dann „Entfernen“. Danach Strg+R.
Erwartet: NVDA sagt „codecockpit-test aus der Liste entfernt.“ Das Projekt fehlt in der Liste und kommt auch nach Strg+R nicht wieder. Der Ordner liegt weiter unter `Testdaten\Projekte\codecockpit-test`.
Ergebnis:

[ ] 18. Wieder hinzufügen
Tasten: „Projekt vom Rechner hinzufügen“, den Ordner `Testdaten\Projekte\codecockpit-test` wählen.
Erwartet: NVDA sagt „codecockpit-test hinzugefügt.“ Das Projekt steht wieder in der Liste. Die Frage „Jetzt hochladen?“ beantworten Sie mit „Später“.
Ergebnis:

[ ] 19. „Nur auf GitHub“ entfernen
Tasten: Zu einem anderen Ihrer Repositories mit „nur auf GitHub“. Tab, „Aus der Liste entfernen …“, „Entfernen“. Danach „Projekt von GitHub herunterladen“ öffnen und die Liste lesen, Escape.
Erwartet: Die Frage sagt, dass auf GitHub nichts geändert wird. NVDA sagt „… aus der Liste entfernt.“ Die Zeile ist weg. In der Liste beim Herunterladen steht das Repository weiter zur Wahl.
Ergebnis:
