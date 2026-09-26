# Fragen zu Phase 6: Pull Requests, Reviews und Schutzregeln

Stand: 26.09.2026.

So beantworten Sie die Fragen:

- Jede Frage beginnt mit [ ].
- Passt mein Vorschlag, schreiben Sie ein x in die Klammer: [x].
- Wollen Sie etwas anderes, schreiben Sie ein Ausrufezeichen hinein: [!]. Schreiben Sie Ihre Antwort hinter „Antwort:“.
- Ist etwas unklar, schreiben Sie ein Fragezeichen hinein: [?]. Ich erkläre es dann genauer.
- Mit der Suche nach [ ] finden Sie die Fragen, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Worum es geht

Ein Pull Request ist ein Antrag auf GitHub: „Bitte übernehmt meinen Branch in main.“

Andere lesen die Änderungen, schreiben Kommentare und geben ein Review ab: genehmigen oder Änderungen anfordern. Danach übernimmt jemand den Pull Request in main.

Schutzregeln legen fest, was für main gilt, zum Beispiel „Nur über Pull Request“ oder „Mindestens eine Genehmigung“.

Das alles passiert auf GitHub, nicht auf Ihrem Rechner. Das Cockpit spricht dafür mit GitHub.


## A. Ablauf der Phase

[ ] 1. Phase 6 in Teilschritte aufteilen
Frage: Phase 6 ist groß. Soll ich sie wieder aufteilen, jeder Teil mit eigenen Tests und eigener Checkliste?
Vorschlag: Ja, in drei Teilschritte:
- 6a: Pull Requests erstellen, als Liste ansehen, Details und Kommentare lesen, selbst kommentieren, schließen und wieder öffnen.
- 6b: Reviews (genehmigen, Änderungen anfordern, Kommentar), in main übernehmen, danach aufräumen: zu main wechseln, holen, Branch löschen.
- 6c: Schutzregeln für main, verständliche Erklärung, wenn GitHub das Hochladen in main ablehnt, und Hochladen in einen Branch mit Namensvorschlag.
Antwort:

[ ] 2. Test mit Ihrem echten GitHub-Konto
Frage: Pull Requests gibt es nur auf GitHub. Die „Plattform“ der Testdaten ist ein Ordner und kennt keine Pull Requests. Wie prüfen Sie das?
Vorschlag: Die Checklisten lassen Sie wieder ein privates Repository „codecockpit-test“ anlegen, diesmal mit dem Cockpit selbst. Am Ende von Phase 6 löschen Sie es wieder. Die automatischen Tests arbeiten nur mit einem nachgebauten GitHub.
Antwort:

[ ] 3. Zweites GitHub-Konto für Reviews
Frage: GitHub erlaubt nicht, den eigenen Pull Request zu genehmigen oder Änderungen anzufordern. Kommentieren und Übernehmen geht auch allein. Haben Sie ein zweites Konto oder jemanden, der kurz mitmacht?
Vorschlag: Wenn nicht, prüfen Sie in 6b nur Kommentare und Übernehmen. Das Genehmigen prüfen die automatischen Tests. Die Checkliste sagt dann ehrlich, dass dieser Teil nur automatisch geprüft ist.
Antwort:


## B. Einschalten

[ ] 4. Wie wird Pull Requests eingeschaltet?
Frage: Laut Konzept ist „Branches und Pull Requests“ ein Feature, das man pro Projekt einschaltet. Die Feature-Verwaltung zum Ein- und Ausschalten kommt aber erst in Phase 7. Wie soll es in Phase 6 gehen?
Vorschlag: Aufteilen wie bei den Branches:
- Pull Requests ansehen, erstellen, kommentieren, prüfen und übernehmen ist immer da, sobald ein Projekt auf GitHub liegt. Man braucht es schon, wenn Kollegen einen Pull Request stellen, auch ohne eigenes Feature.
- Das Feature ändert nur den Ablauf beim Hochladen: Es fragt, in welchen Branch hochgeladen wird, und bietet danach gleich „Pull Request erstellen“ an. So steht es im Konzept.
- Bis Phase 7 schaltet man das Feature pro Projekt mit einer einfachen Aktion bei Code ein und aus: „Hochladen über Pull Requests einschalten“. In Phase 7 wandert das in die Feature-Verwaltung. Die Grundeinstellung „Neue Projekte mit Branches und Pull Requests“ gibt es schon, sie gilt dann für neue Projekte.
Antwort:


## C. Pull Requests

[ ] 5. Wo stehen die Pull Requests?
Frage: Wo finden Sie die Pull Requests eines Projekts?
Vorschlag:
- Neue Aktion bei Code: „Pull Requests …“. Das Fenster zeigt die offenen Pull Requests, neueste oben, zum Beispiel „Nr. 12: Suche in PDFs, von design nach main, von Anna, 1 Genehmigung“. Mit einer Auswahl oben sehen Sie auch die geschlossenen.
- In der Übersicht Branches steht bei einem Branch „1 offener Pull Request“.
- Code zeigt „1 offener Pull Request“, wenn es einen für den aktuellen Branch gibt.
- In der Projektliste steht nichts dazu, damit die Zeile kurz bleibt. Die Rückmeldungen aus Phase 11 melden neue Pull Requests später zusätzlich.
Antwort:

[ ] 6. Pull Request erstellen
Frage: Was fragt das Cockpit beim Erstellen?
Vorschlag: Ein Fenster mit Titel, Beschreibung, Ziel-Branch (Vorgabe main) und Prüfern (freiwillig, als Liste mit Kontrollkästchen aus den Mitarbeitern). Titel und Beschreibung sind aus den Commit-Nachrichten des Branches vorbelegt. Mit KI-Vorschlag erst ab Phase 8. Ist der Branch noch nicht auf GitHub, lädt das Cockpit ihn vorher hoch.
Antwort:

[ ] 7. Entwürfe
Frage: GitHub kennt Pull Requests als Entwurf (Draft): Sie sind sichtbar, aber noch nicht zum Prüfen gedacht. Brauchen Sie das?
Vorschlag: Ja, als Kontrollkästchen „Als Entwurf erstellen“ im selben Fenster, Vorgabe aus. Dazu die Aktion „Zum Prüfen freigeben“.
Antwort:

[ ] 8. Kommentare
Frage: Auf GitHub gibt es zwei Arten Kommentare: allgemeine zum ganzen Pull Request und solche zu einer bestimmten Zeile einer Datei. Wie sollen die erscheinen?
Vorschlag: Beide als eine Liste, älteste oben, zum Beispiel „Anna, 24.09.2026: Sieht gut aus“ und „Ben zu main.py Zeile 12: Hier fehlt ein Test“. Mit Tab gibt es ein Feld zum Antworten. Schreiben kann man in 6a nur allgemeine Kommentare. Kommentare zu einer Zeile schreiben ist mit Screenreader schwer zu bedienen. Das schlage ich erst später vor, wenn Sie es brauchen.
Antwort:

[ ] 9. Geänderte Dateien ansehen
Frage: Beim Prüfen will man sehen, was sich geändert hat. Wie?
Vorschlag: In den Details eine Liste der Dateien, zum Beispiel „main.py, geändert, 5 Zeilen dazu, 2 weg“. Enter zeigt die Änderungen der Datei als Liste, eine Zeile pro Änderung: „Neu Zeile 12: …“ und „Weg Zeile 8: …“. Das ist lesbarer als das übliche Format mit Plus und Minus.
Antwort:


## D. Übernehmen

[ ] 10. Wie wird übernommen?
Frage: GitHub kann auf drei Arten übernehmen: mit einem Merge-Commit (Vorgabe von GitHub), alles zu einem Commit zusammengefasst (Squash) oder die Commits einzeln oben drauf gesetzt (Rebase). Was soll das Cockpit anbieten?
Vorschlag: Alle drei, soweit das Repository sie erlaubt. Vorgabe ist die Vorgabe von GitHub, „Merge-Commit“. Jede Art hat einen kurzen Satz zur Erklärung.
Antwort:

[ ] 11. Nach dem Übernehmen
Frage: Was passiert, wenn der Pull Request übernommen ist?
Vorschlag: Wie im Konzept: Das Cockpit fragt „Zu main wechseln, die Änderungen holen und den Branch aufräumen?“. Aufräumen löscht den Branch hier und auf GitHub. Vorgabe ist „Später“. Der Branch bleibt dann, wie er ist.
Antwort:


## E. Schutzregeln

[ ] 12. Welche Schutzregeln?
Frage: GitHub hat sehr viele Schutzregeln. Welche soll das Cockpit anbieten?
Vorschlag: Die wichtigsten als Liste mit Kontrollkästchen, unter „Repository verwalten“, Knopf „Schutzregeln für main …“:
- Nur über Pull Request in main
- Mindestens so viele Genehmigungen: 1, 2 oder 3
- Genehmigungen verfallen, wenn neue Commits dazukommen
- Regeln gelten auch für Administratoren
- main darf nicht gelöscht werden
Force push auf main bleibt immer verboten. Das Cockpit schaltet es nie ein.
Antwort:

[ ] 13. Schutzregeln bei privaten Repositories
Frage: Bei einem kostenlosen GitHub-Konto gibt es Schutzregeln nur für öffentliche Repositories. Für private braucht man GitHub Pro oder ein Firmenkonto. Was soll das Cockpit dann tun?
Vorschlag: Es erklärt das in einfachen Worten, statt eine Fehlermeldung zu zeigen: „Schutzregeln für private Repositories gibt es nur mit GitHub Pro oder in Organisationen mit bezahltem Plan.“ Für Ihren Test in 6c heißt das: Sie brauchen dafür ein öffentliches Test-Repository oder ein Repository einer Firma. Wir schalten codecockpit-test dafür kurz auf öffentlich. Es enthält nur Testdaten ohne Geheimnisse.
Antwort:

[ ] 14. Hochladen, wenn main geschützt ist
Frage: Lehnt GitHub das Hochladen in main ab, weil main geschützt ist, was dann?
Vorschlag: Wie im Konzept: Das Cockpit erklärt es und bietet an, die Änderungen in einen neuen Branch hochzuladen und einen Pull Request zu erstellen. Der Name wird aus der Commit-Nachricht vorgeschlagen, zum Beispiel „suche-in-pdfs“. Die Commits bleiben dabei erhalten, main auf Ihrem Rechner wird danach auf den Stand von GitHub zurückgesetzt. Vorher gibt es eine Sicherheitskopie.
Antwort:


## F. Sonstiges

[ ] 15. Rechte
Frage: Die Anmeldung im Browser hat schon das Recht repo. Damit gehen Pull Requests, Reviews und Kommentare. Für Schutzregeln muss man Administrator des Repositories sein. Reicht das?
Vorschlag: Ja. Fehlt ein Recht, erklärt das Cockpit, welches, wie beim Löschen. Eine zusätzliche Anmeldung wie beim Löschen braucht es hier nicht.
Antwort:

[ ] 16. GitLab
Frage: Bei GitLab heißen Pull Requests Merge Requests. GitLab kommt erst in Phase 16. Soll ich jetzt schon darauf achten?
Vorschlag: Ja, aber nur im Aufbau: Die Pull Requests laufen über eine eigene Schnittstelle der Plattform. GitLab bringt später seine eigene Umsetzung und seine eigenen Wörter mit. Sichtbar ist in Phase 6 nur GitHub.
Antwort:
