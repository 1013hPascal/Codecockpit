# Fragen zu Phase 7: Feature-Verwaltung

Stand: 27.09.2026.

So beantworten Sie die Fragen:

- Jede Frage beginnt mit [ ].
- Passt mein Vorschlag, schreiben Sie ein x in die Klammer: [x].
- Wollen Sie etwas anderes, schreiben Sie ein Ausrufezeichen hinein: [!]. Schreiben Sie Ihre Antwort hinter „Antwort:“.
- Ist etwas unklar, schreiben Sie ein Fragezeichen hinein: [?]. Ich erkläre es dann genauer.
- Mit der Suche nach [ ] finden Sie die Fragen, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Worum es geht

Features sind Zusatzfunktionen, die man ein- und ausschalten kann, zum Beispiel später die Exe-Erstellung oder die README-Pflege. Bisher gibt es ein Feature: „Branches und Pull Requests“.

Phase 7 baut zwei Fenster:
- Die Feature-Verwaltung für alle Projekte (Konzept 8.5).
- „Features dieses Projekts“ für ein einzelnes Projekt (Konzept 8.4).

Dazu kommt die Einführung, die beim ersten Einschalten eines Features erscheint.


## A. Ablauf

[ ] 1. Eine Phase ohne Teilschritte
Frage: Phase 7 ist kleiner als 5 und 6. Reicht ein Durchgang mit einer Checkliste?
Vorschlag: Ja, eine Checkliste `checklisten\phase-07.md`.
Antwort:

[ ] 2. Beispiel-Features für den Test
Frage: Mit nur einem Feature lassen sich Abhängigkeiten („A braucht B“) und eigene Einstellungen nicht prüfen. Wie testen wir das?
Vorschlag: Nur beim Start mit `start_testdaten.bat` gibt es zwei Beispiel-Features: „Beispiel Grundlage“ mit einer Einstellung und „Beispiel Aufbau“, das die Grundlage braucht. Mit dem normalen Start sieht man sie nie.
Antwort:


## B. Feature-Verwaltung für alle Projekte

[ ] 3. Wo steht sie?
Frage: Wo finden Sie die Feature-Verwaltung?
Vorschlag: Neues Menü „Features“ (Alt+F) nach „Datei“, wie im Konzept, mit dem Eintrag „Feature-Verwaltung …“.
Antwort:

[ ] 4. Aufbau des Fensters
Frage: Wie sieht das Fenster aus?
Vorschlag:
- Eine Liste mit Kontrollkästchen, eine Zeile pro Feature, zum Beispiel „Branches und Pull Requests, eingeschaltet, in 2 Projekten aktiv“. Die Leertaste schaltet um.
- Kann ein Feature gerade nicht laufen, sagt die Zeile warum, zum Beispiel „README-Pflege, nicht verfügbar: benötigt KI“.
- Mit Tab folgt eine Liste „Beschreibung“ zum markierten Feature: was es tut, was es braucht, bei wie vielen Projekten es aktiv ist.
- Dann die Knöpfe „Einführung …“, „Einstellungen …“ (nur, wenn das Feature welche hat), „Speichern“ und „Abbrechen“.
Antwort:

[ ] 5. Global ausschalten
Frage: Was passiert, wenn Sie ein Feature global ausschalten?
Vorschlag: Wie im Konzept: Es verschwindet überall, auch aus Menüs und Aktionslisten. Die Einstellungen der Projekte bleiben aber gespeichert. Schalten Sie es wieder ein, ist es in denselben Projekten wieder aktiv wie vorher.
Antwort:


## C. Features eines Projekts

[ ] 6. Wo steht das?
Frage: Wo schalten Sie Features für ein einzelnes Projekt?
Vorschlag: Aktion „Features dieses Projekts …“ auf der Projektzeile. Die vorläufige Aktion „Hochladen über Pull Requests einschalten“ bei Code aus Phase 6 fällt dafür weg.
Antwort:

[ ] 7. Aufbau
Frage: Wie sieht das Fenster aus?
Vorschlag: Wie die Feature-Verwaltung, nur für dieses Projekt: Liste mit Kontrollkästchen, zum Beispiel „Branches und Pull Requests, aktiv“. Global ausgeschaltete Features erscheinen nicht. Mit Tab die Beschreibung, dann „Einführung …“, „Speichern“, „Abbrechen“.
Antwort:

[ ] 8. Abhängigkeiten
Frage: Was passiert, wenn ein Feature ein anderes braucht, das aus ist?
Vorschlag: Wie im Konzept: Beim Speichern fragt das Cockpit zum Beispiel „Beispiel Aufbau benötigt Beispiel Grundlage. Beispiel Grundlage ist für dieses Projekt ausgeschaltet. Beide einschalten?“ Vorgabe ist „Abbrechen“. Umgekehrt: Schalten Sie eine Grundlage aus, nennt das Cockpit die Features, die dann mit ausgehen, und fragt nach.
Antwort:

[ ] 9. Wo wird es gespeichert?
Frage: Die Features eines Projekts stehen in der Datei cockpit.toml im Ordner Code. Sie wird mit hochgeladen. So haben alle, die am Projekt arbeiten, dieselben Features. Passt das?
Vorschlag: Ja, so bleibt es. Die Frage beim Speichern erwähnt das kurz.
Antwort:


## D. Vorauswahl für neue Projekte

[ ] 10. Wo stellt man sie ein?
Frage: Welche Features sollen neue Projekte bekommen? In den Grundeinstellungen gibt es bisher nur „Neue Projekte mit Branches und Pull Requests“.
Vorschlag: Die Vorauswahl steht in der Feature-Verwaltung: In der Beschreibung jedes Features gibt es das Kontrollkästchen „Für neue Projekte einschalten“. Der Eintrag in den Grundeinstellungen fällt dafür weg, sonst gäbe es zwei Orte für dasselbe.
Antwort:

[ ] 11. Für welche Projekte gilt die Vorauswahl?
Frage: Bei vielen Projekten steht in cockpit.toml noch nichts zu Features. Was gilt dort?
Vorschlag: Die Vorauswahl. Sobald Sie bei einem Projekt etwas ändern, steht es fest in cockpit.toml und die Vorauswahl gilt dort nicht mehr. Das Fenster „Features dieses Projekts“ sagt oben, ob das Projekt der Vorauswahl folgt oder eigene Features hat.
Antwort:

[ ] 12. Beim Hochladen eines neuen Projekts
Frage: Laut Konzept 9.1 wählt man beim ersten Hochladen auch die Features. Das wurde in Phase 5b auf Phase 7 verschoben. Soll das jetzt kommen?
Vorschlag: Ja. Das Fenster „Auf GitHub hochladen“ bekommt eine Liste „Features“ mit Kontrollkästchen, vorbelegt mit der Vorauswahl. Die Wahl kommt in cockpit.toml.
Antwort:


## E. Einführung

[ ] 13. Wann erscheint sie?
Frage: Jedes Feature hat eine kurze Einführung. Wann soll sie erscheinen?
Vorschlag: Beim allerersten Einschalten eines Features, egal ob global oder bei einem Projekt. Danach nicht mehr von selbst, aber jederzeit mit „Einführung …“ in beiden Fenstern. Das Cockpit merkt sich pro Feature, dass Sie sie gesehen haben.
Antwort:

[ ] 14. Wie sieht sie aus?
Frage: Wie wird die Einführung angezeigt?
Vorschlag: Wie die Anleitungen im Menü Hilfe: eine Liste, eine Zeile pro Satz, Escape schließt.
Antwort:
