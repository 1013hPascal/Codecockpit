# Checkliste Phase 8c: KI-Assistent

Stand: 27.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- Neues Feature „KI-Assistent“. Der Knopf „Vorschlag der KI“ (Alt+V) füllt Felder mit einem Vorschlag: beim Hochladen von Änderungen, beim Pull Request und beim ersten Hochladen die Kurzbeschreibung.
- Escape bricht einen laufenden Vorschlag ab, ein zweites Escape schließt das Fenster.
- Die KI bekommt nur die Dateiliste und die geänderten Zeilen, ohne Geheimnisse.
- In der Feature-Verwaltung stehen die KI-Features jetzt als ein Eintrag „KI“. Mit Tab kommen Sie zu den einzelnen KI-Features.
- Ein Vorschlag dauert mit gemma4:12b etwa 30 Sekunden.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten reicht die Windows-Anmeldeinformationsverwaltung. Auf der Seite KI wählen Sie „KI einrichten …“ und richten Ollama mit gemma4:12b ein, wie in 8b.


## A. Feature-Verwaltung mit der Gruppe KI

[ ] 1. Eintrag KI
Tasten: Alt+F, Feature-Verwaltung. Mit Pfeil runter durch die Liste.
Erwartet: Es gibt eine Zeile „KI, 2 von 2 KI-Features eingeschaltet“. Sie hat kein Kontrollkästchen. KI-Assistent und Terminal-Erklärung stehen nicht mehr einzeln in der Liste.
Ergebnis:

[ ] 2. Die einzelnen KI-Features
Tasten: Auf der Zeile KI Tab.
Erwartet: Die Liste „KI-Features“ mit „KI-Assistent, eingeschaltet, …“ und „Terminal-Erklärung, eingeschaltet, …“, jeweils mit Kontrollkästchen. Mit Tab kommt die Beschreibung, sie beginnt mit „KI-Feature KI-Assistent.“ Auf einer anderen Zeile der Hauptliste gibt es die Liste „KI-Features“ nicht, Tab geht dann gleich zur Beschreibung.
Ergebnis:

[ ] 3. KI-Feature ausschalten
Tasten: In „KI-Features“ auf Terminal-Erklärung Leertaste. Umschalt+Tab zurück in die Hauptliste.
Erwartet: Die Zeile heißt jetzt „Terminal-Erklärung, ausgeschaltet“, die Hauptliste „KI, 1 von 2 KI-Features eingeschaltet“. Abbrechen, damit nichts gespeichert wird.
Ergebnis:

[ ] 4. Einstellungen des KI-Assistenten
Tasten: Alt+K, „KI-Features …“. Tab in „KI-Features“, auf KI-Assistent. Tab bis „Einstellungen …“, Enter.
Erwartet: Die Feature-Verwaltung steht gleich auf der Zeile KI. Das Fenster „Einstellungen: KI-Assistent“ hat „KI für Vorschläge“ mit „Standard-Werkzeug (Ollama auf diesem Rechner, gemma4:12b)“ und „Sprache der Vorschläge“ mit „Deutsch“. Escape, dann Abbrechen.
Ergebnis:

[ ] 5. Features eines Projekts
Tasten: Auf der Projektzeile PDF-Chat „Features dieses Projekts …“.
Erwartet: Auch hier eine Zeile „KI, 2 von 2 KI-Features eingeschaltet“, mit Tab „KI-Features“ mit „KI-Assistent, aktiv“ und „Terminal-Erklärung, aktiv“. Abbrechen.
Ergebnis:


## B. Commit-Nachricht vorschlagen

[ ] 6. Knopf im Fenster
Tasten: Ändern Sie eine Datei im Ordner Code von PDF-Chat, zum Beispiel main.py, und speichern Sie. Im Cockpit bei Code von PDF-Chat „Änderungen hochladen“. Im Feld „Was haben Sie geändert?“ Tab, Tab.
Erwartet: Nach „Beschreibung“ kommt der Knopf „Vorschlag der KI“. Danach „Änderungen“.
Ergebnis:

[ ] 7. Vorschlag einfügen
Tasten: Alt+V. Warten, ohne etwas zu drücken.
Erwartet: NVDA sagt „Die KI schreibt einen Vorschlag …“. Nach etwa 30 Sekunden „Vorschlag eingefügt.“ Der Fokus steht in „Was haben Sie geändert?“ mit einer kurzen Zusammenfassung Ihrer Änderung. In „Beschreibung“ stehen zwei bis vier Sätze, ohne Sternchen oder Aufzählungszeichen.
Ergebnis:

[ ] 8. Vorschlag abbrechen
Tasten: Alt+V, nach ein paar Sekunden Escape. Dann noch einmal Escape.
Erwartet: Das erste Escape sagt „Vorschlag abgebrochen.“, das Fenster bleibt offen, die Felder bleiben, wie sie waren. Das zweite Escape schließt das Fenster. Hochgeladen wird nichts.
Ergebnis:

[ ] 9. Englisch
Tasten: In den Einstellungen des KI-Assistenten „Sprache der Vorschläge“ auf Englisch, Speichern. Dann wieder „Änderungen hochladen“, Alt+V.
Erwartet: Der Vorschlag ist auf Englisch. Danach die Sprache wieder auf Deutsch stellen.
Ergebnis:

[ ] 10. Geheimnisse bleiben draußen (freiwillig)
Tasten: Schreiben Sie in main.py eine Zeile wie `api_key = "sk-ErfundenFuerDenTest1234567890abcdef"` und legen Sie eine Datei .env mit `PASSWORT=test123456` an. Dann „Änderungen hochladen“, Alt+V. Danach die Zeile und die Datei wieder löschen.
Erwartet: Der Vorschlag erwähnt weder den Schlüssel noch das Passwort. Hochladen würde die Sicherheitsprüfung ohnehin stoppen.
Ergebnis:


## C. Pull Request und erstes Hochladen

[ ] 11. Pull Request
Tasten: Bei einem Projekt mit einem eigenen Branch, der Commits hat, „Pull Requests …“, „Neuer Pull Request …“. Im Feld Beschreibung Tab.
Erwartet: Nach „Beschreibung“ kommt „Vorschlag der KI“. Alt+V füllt „Titel“ und „Beschreibung“ passend zu den Commits. Der Fokus steht danach in „Titel“.
Ergebnis:

[ ] 12. Kurzbeschreibung beim ersten Hochladen
Tasten: Bei einem Projekt, das noch nicht auf GitHub ist, „Auf GitHub hochladen …“. Im Feld „Kurzbeschreibung“ Tab.
Erwartet: Nach „Kurzbeschreibung“ kommt „Vorschlag der KI“. Alt+V schreibt einen Satz in die Kurzbeschreibung, der Fokus steht dort. Danach Abbrechen, damit nichts hochgeladen wird.
Ergebnis:


## D. Ohne KI-Assistent

[ ] 13. Knopf verschwindet
Tasten: Bei „Features dieses Projekts …“ von PDF-Chat in „KI-Features“ den KI-Assistenten ausschalten und speichern. Dann „Änderungen hochladen“.
Erwartet: Der Knopf „Vorschlag der KI“ fehlt, nach „Beschreibung“ kommt gleich „Änderungen“. Danach den KI-Assistenten wieder einschalten.
Ergebnis:
