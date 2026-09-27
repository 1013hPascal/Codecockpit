# Checkliste Phase 6c: Schutzregeln und Hochladen über Pull Requests

Stand: 27.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- Unter „Repository verwalten“ gibt es „Schutzregeln für main …“.
- Lehnt GitHub das Hochladen in main ab, weil main geschützt ist, bietet das Cockpit an, die Änderungen in einen neuen Branch hochzuladen und einen Pull Request zu erstellen.
- Bei Code gibt es „Hochladen über Pull Requests einschalten …“. Dann fragt „Änderungen hochladen“ auf main, in welchen Branch hochgeladen wird, und bietet danach einen Pull Request an.


## Vorbereitung

1. Sie brauchen das Projekt Wetter mit dem Repository codecockpit-test aus 6a und 6b. Sie sind auf main.
2. Schutzregeln gibt es bei einem kostenlosen GitHub-Konto nur für öffentliche Repositories. In Abschnitt B machen Sie codecockpit-test deshalb kurz öffentlich. Es enthält nur die Beispieldatei wetter.py.


## A. Privates Repository

[ ] 1. Schutzregeln bei privatem Repository
Tasten: Auf der Projektzeile Wetter „Repository verwalten …“. Tab zu „Schutzregeln für main …“, Enter.
Erwartet: NVDA sagt „Schutzregeln werden abgefragt.“ Danach sagt eine Meldung: „Schutzregeln für private Repositories gibt es bei GitHub nur mit GitHub Pro oder in Organisationen mit bezahltem Plan. Für öffentliche Repositories sind sie kostenlos.“ Haben Sie GitHub Pro, öffnet sich stattdessen gleich das Fenster aus Punkt 3.
Ergebnis:


## B. Schutzregeln

[ ] 2. Kurz öffentlich machen
Tasten: „Öffentlich machen …“, die Frage lesen, „Öffentlich machen“.
Erwartet: Die Sicherheitsprüfung läuft, danach fragt das Cockpit. NVDA sagt „codecockpit-test ist jetzt öffentlich.“
Ergebnis:

[ ] 3. Fenster Schutzregeln
Tasten: „Schutzregeln für main …“, Enter. Mit Tab durch das Fenster.
Erwartet: Das Fenster heißt „Schutzregeln für main: nicht geschützt“. Der Fokus steht auf „Nur über Pull Request in main“, nicht angekreuzt. Danach kommen „Mindestens so viele Genehmigungen“ mit 0, „Genehmigungen verfallen, wenn neue Commits dazukommen“, „Regeln gelten auch für Administratoren“, „main darf nicht gelöscht werden“, „Weiter …“ und „Abbrechen“.
Ergebnis:

[ ] 4. main schützen
Tasten: „Nur über Pull Request in main“ und „Regeln gelten auch für Administratoren“ ankreuzen. Genehmigungen auf 0 lassen. „main darf nicht gelöscht werden“ ankreuzen. „Weiter …“, die Frage lesen, „Speichern“.
Erwartet: Die Frage sagt: „Änderungen kommen nur über einen Pull Request in main. Das gilt auch für Administratoren, also auch für Sie. main darf nicht gelöscht werden. Force push bleibt immer verboten. Speichern?“ Vorgabe ist „Abbrechen“. Danach sagt NVDA „Schutzregeln für main gespeichert.“ Öffnen Sie das Fenster noch einmal, heißt es „… geschützt“ und die Kästchen sind wie gewählt.
Ergebnis:

Hinweis: Genehmigungen auf 0 lassen, weil Sie Ihren eigenen Pull Request nicht genehmigen können. Mit 1 könnten Sie ihn sonst nicht mehr übernehmen.


## C. Hochladen, wenn main geschützt ist

[ ] 5. Hochladen wird abgelehnt
Tasten: Alle Fenster schließen. In wetter.py eine Zeile `print('Geschützt')` anhängen, speichern. Bei Code „Änderungen hochladen …“, Nachricht `Test Schutz`, „Hochladen“.
Erwartet: Die Schritte laufen. Dann fragt das Cockpit: „GitHub lässt in main nichts direkt hochladen. Der Branch ist geschützt …“ Die Frage sagt, dass Ihr Commit gespeichert ist, main auf den Stand von GitHub kommt und Ihre Dateien unverändert bleiben. Die Knöpfe sind „In neuen Branch hochladen …“ und „Später“. Vorgabe ist „Später“.
Ergebnis:

[ ] 6. In neuen Branch hochladen
Tasten: „In neuen Branch hochladen …“. Den Namen lesen, Enter.
Erwartet: Der Name ist „test-schutz“ vorbelegt. Danach lädt das Cockpit den Branch hoch, mit „Schritt … von …“. Dann öffnet sich „Pull Request erstellen: von test-schutz“ mit dem Titel „Test Schutz“.
Ergebnis:

[ ] 7. Pull Request und Übernehmen
Tasten: „Erstellen“. Dann „Pull Requests …“, auf dem neuen Pull Request „In main übernehmen …“, „Übernehmen“, „Aufräumen“.
Erwartet: NVDA sagt „Pull Request Nr. 3 erstellt.“ Übernehmen klappt, weil 0 Genehmigungen nötig sind. Nach dem Aufräumen sind Sie auf main, und wetter.py enthält `print('Geschützt')`.
Ergebnis:


## D. Hochladen über Pull Requests

[ ] 8. Einschalten
Tasten: Bei Code „Hochladen über Pull Requests einschalten …“, die Frage lesen, „Einschalten“. Dann die Aktionen lesen.
Erwartet: Die Frage erklärt den Ablauf und sagt, dass die Einstellung in cockpit.toml steht und mit hochgeladen wird. NVDA sagt „Hochladen über Pull Requests eingeschaltet.“ Jetzt steht dort „Hochladen über Pull Requests ausschalten …“. Code nennt 1 Datei, die noch nicht hochgeladen ist: cockpit.toml.
Ergebnis:

[ ] 9. Branch wählen beim Hochladen
Tasten: In wetter.py eine Zeile `print('Mit Feature')` anhängen, speichern. „Änderungen hochladen …“, Nachricht `Mit Feature`, „Hochladen“. Die Liste lesen, auf „Neuer Branch: mit-feature …“ Enter, den Namen bestätigen.
Erwartet: Die Liste heißt „In welchen Branch hochladen?“ mit „Neuer Branch: mit-feature …“ oben, „Vorhandener Branch: entwurf“ aus 6a in der Mitte und „Direkt in main“ unten. Der Hinweis im Namensfenster sagt, dass main bleibt, wie es ist. Danach lädt das Cockpit hoch und fragt „mit-feature ist hochgeladen. Jetzt einen Pull Request erstellen …?“ mit „Pull Request erstellen …“ und „Später“. Vorgabe ist „Später“.
Ergebnis:

[ ] 10. Pull Request anbieten
Tasten: „Pull Request erstellen …“, dann „Erstellen“.
Erwartet: NVDA sagt „Pull Request Nr. 4 erstellt.“ Code nennt „Branch mit-feature“ und „1 offener Pull Request“.
Ergebnis:


## E. Aufräumen

[ ] 11. Zurück zum Ausgangszustand
Tasten: Nr. 4 übernehmen und aufräumen wie in Punkt 7. „Hochladen über Pull Requests ausschalten …“, „Ausschalten“. Unter „Repository verwalten“ die Schutzregeln öffnen, alle Kästchen leeren, „Weiter …“, „Speichern“. Dann „Privat machen …“, „Privat machen“.
Erwartet: Beim Leeren sagt die Frage „main wird nicht mehr geschützt …“. NVDA sagt danach „main ist nicht mehr geschützt.“ und zum Schluss „codecockpit-test ist jetzt privat.“
Ergebnis:

Am Ende von Phase 6 löschen Sie codecockpit-test mit „Repository verwalten“, „Löschen …“, wie in 5e.
