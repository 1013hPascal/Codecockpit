# Fragen zu Phase 5: Grundfunktionen

Stand: 25.09.2026.

So beantworten Sie die Fragen:

- Jede Frage beginnt mit [ ].
- Passt mein Vorschlag, schreiben Sie ein x in die Klammer: [x].
- Wollen Sie etwas anderes, schreiben Sie ein Ausrufezeichen hinein: [!]. Schreiben Sie Ihre Antwort hinter „Antwort:“.
- Ist etwas unklar, schreiben Sie ein Fragezeichen hinein: [?]. Ich erkläre es dann genauer.
- Mit der Suche nach [ ] finden Sie die Fragen, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## A. Ablauf der Phase

[x] 1. Phase 5 in Teilschritte aufteilen
Frage: Phase 5 ist sehr groß. Soll ich sie in fünf Teilschritte aufteilen? Jeder Teilschritt bekommt eigene Tests und eine eigene Checkliste, zum Beispiel `checklisten\phase-05a.md`.
Vorschlag: Ja, in dieser Reihenfolge:
- 5a: Git-Grundlage, Git-Identität, Projekte hinzufügen, Umstellen oder Verknüpfen, Reparatur nach dem Verschieben, Stand der Projekte in der Projektliste.
- 5b: Sicherheitsprüfung und .gitignore, Neues Projekt hochladen.
- 5c: Änderungen hochladen, Änderungen holen, Projekt von der Plattform herunterladen.
- 5d: Verlauf und Rückgängig machen, mit Sicherheitskopien.
- 5e: Links, Repository verwalten, Aus der Liste entfernen.
Antwort:

[x] 2. Test mit Ihrem echten GitHub-Konto
Frage: Ab 5b muss ich echte Repositories anlegen, damit Sie das Hochladen prüfen können. Darf die Checkliste Sie ein privates Test-Repository anlegen lassen?
Vorschlag: Ja. Es heißt „codecockpit-test“, ist privat und wird in 5e mit dem Cockpit wieder gelöscht. Die automatischen Tests arbeiten nie mit GitHub, nur mit einer Attrappe.
Antwort:


## B. Git und Projekte

[x] 3. Git-Identität in jedem Projekt
Frage: Das Cockpit trägt Name und E-Mail-Adresse aus den Grundeinstellungen in jedes Projekt ein, nur für dieses Repository, nicht für den ganzen Rechner. Was passiert, wenn ein Projekt schon eine andere Identität hat?
Vorschlag: Das Cockpit fragt nach. Die sichere Vorgabe ist „Vorhandene behalten“.
Antwort:

[x] 4. Projekte, die noch nicht auf der Plattform sind
Frage: Ein Projekt liegt schon im Projekte-Hauptordner, ist aber noch nicht auf GitHub. Wie kommt es hoch?
Vorschlag: Bei „Code“ gibt es dann die Aktion „Auf GitHub hochladen“. Sie läuft wie „Neues Projekt hochladen“, nur ohne das Kopieren. In der Projektliste steht „noch nicht auf GitHub“.
Antwort:

[x] 5. Name des Haupt-Branches
Frage: Wie soll der Haupt-Branch neuer Repositories heißen?
Vorschlag: „main“, wie es GitHub heute vorgibt.
Antwort:

[x] 6. Stand in der Projektliste
Frage: Die Projektliste soll zeigen, wie viele Dateien noch nicht hochgeladen sind. Dafür fragt das Cockpit Git bei jedem Projekt. Wann soll das passieren?
Vorschlag: Im Hintergrund beim Start, nach jeder Aktion am Projekt und mit Strg+R. Es gibt dabei keine Ansage und der Fokus bleibt, wo er ist.
Antwort:


## C. Sicherheitsprüfung

[x] 7. Wie Geheimnisse gefunden werden
Frage: Es gibt fertige Programme, die Geheimnisse im Code finden, zum Beispiel gitleaks. Das wäre ein zusätzliches Programm. Oder das Cockpit bringt eigene Regeln mit.
Vorschlag: Eigene Regeln, ohne neue Bibliothek. Sie erkennen typische Tokens und Schlüssel, zum Beispiel von GitHub, OpenAI, Anthropic, AWS und Azure, dazu private Schlüssel, Zeilen wie `password = "..."` und `.env`-Dateien. Weitere Regeln lassen sich später ergänzen.
Antwort:

[x] 8. Funde als „kein Geheimnis“ markieren
Frage: Wo merkt sich das Cockpit, dass ein Fund kein Geheimnis ist?
Vorschlag: In `cockpit.toml` des Projekts. Dort steht nur der Dateiname und ein Fingerabdruck der Zeile, nie der Wert selbst. So gilt die Markierung auch auf einem anderen Rechner.
Antwort:

[x] 9. Große Dateien
Frage: Das Konzept warnt ab 50 MB. GitHub lehnt Dateien über 100 MB ab.
Vorschlag: Ab 50 MB eine Warnung mit Rückfrage. Die Vorgabe ist „In .gitignore aufnehmen“. Ab 100 MB stoppt das Cockpit, weil GitHub die Datei sowieso ablehnen würde.
Antwort:

[x] 10. Private Daten
Frage: Was passiert bei Datenbanken, Logdateien und ähnlichen Dateien?
Vorschlag: Eine Warnung mit Rückfrage. Die Vorgabe ist „In .gitignore aufnehmen“. Die andere Wahl ist „Trotzdem hochladen“.
Antwort:


## D. Hochladen und Holen

[x] 11. Welche Dateien hochgeladen werden
Frage: Soll man vor dem Hochladen einzelne Dateien auswählen können?
Vorschlag: Nein. Es werden alle Änderungen hochgeladen, die die Sicherheitsprüfung durchlassen. Was nicht hoch soll, kommt in `.gitignore`. Das hält den Ablauf einfach.
Antwort:

[x] 12. Lizenzdatei
Frage: Beim neuen Projekt wählt man eine Lizenz. Soll das Cockpit die Datei `LICENSE` selbst anlegen?
Vorschlag: Ja. Den Lizenztext holt es von GitHub und trägt Ihren Namen und das Jahr ein. Bei „Keine Lizenz / firmenintern“ entsteht keine Datei. Liegt schon eine `LICENSE` im Ordner, bleibt sie unverändert.
Antwort:

[?] 13. Holen, wenn auch hier etwas geändert wurde
Frage: Auf GitHub und hier auf dem Rechner gibt es neue Änderungen. Was macht „Änderungen holen“?
Vorschlag: Betreffen die Änderungen verschiedene Dateien, führt Git sie zusammen. Betreffen sie dieselbe Stelle, macht das Cockpit nichts, stellt den alten Stand wieder her und nennt die betroffenen Dateien (Konzept 9.3).
Antwort: wie ist das denn im terminal, wenn ich git pull mache, was sieht GitHub das vor, mache das so wie GitHub das machen würde.

Antwort von Claude: So ist es im Terminal und in GitHub Desktop, dem Programm von GitHub selbst:
- `git pull` holt die neuen Commits von GitHub und führt sie mit Ihren zusammen. Das heißt „Merge“. GitHub Desktop macht es genauso.
- Betreffen die Änderungen verschiedene Stellen, klappt das von selbst. Git legt dabei einen zusätzlichen Commit „Merge“ an.
- Betreffen sie dieselbe Stelle, gibt es einen Konflikt. Git schreibt dann beide Fassungen mit Markierungen wie `<<<<<<<` in die Datei. Im Terminal muss man die Datei von Hand bereinigen. GitHub Desktop zeigt stattdessen eine Liste der Dateien mit Konflikt. Pro Datei kann man seine eigene Fassung behalten, die Fassung von GitHub nehmen oder die Datei im Editor öffnen. Man kann das Zusammenführen auch abbrechen, dann ist alles wie vorher.
- Gibt es hier Änderungen, die noch nicht hochgeladen sind, und würde das Holen sie überschreiben, weigert sich Git. GitHub Desktop bietet dann an, die Änderungen kurz beiseitezulegen und danach zurückzuholen. Das heißt „Stash“.

[x] 13a. Neuer Vorschlag zum Holen
Vorschlag: Das Cockpit macht es wie GitHub Desktop:
- Zusammenführen mit Merge, wie `git pull`.
- Bei einem Konflikt erscheint eine Liste der betroffenen Dateien. Pro Datei wählen Sie: „Meine Fassung behalten“, „Fassung von GitHub übernehmen“ oder „Im Editor öffnen“. Dazu gibt es „Zusammenführen abbrechen“. Das ist die sichere Vorgabe, Escape wählt sie.
- Stören Änderungen, die noch nicht hochgeladen sind, fragt das Cockpit: „Beiseitelegen und danach zurückholen“ oder „Abbrechen“. Die Vorgabe ist „Abbrechen“.
- Vorher legt das Cockpit eine Sicherheitskopie an.
Das weicht von Konzept 9.3 ab, weil es dort heißt, dass nichts automatisch zusammengeführt wird. Ich trage es in ENTSCHEIDUNGEN.md ein.
Antwort:

[x] 14. Projekt von der Plattform herunterladen
Frage: Wie wählt man das Repository aus?
Vorschlag: Eine Liste Ihrer Repositories und der Repositories Ihrer Organisationen, neueste oben. Als letzter Eintrag „Adresse eingeben …“ für fremde Repositories.
Antwort:


## E. Verlauf und Repository verwalten

[x] 15. Ausgeführte Feature-Schritte im Verlauf
Frage: Das Konzept zeigt in den Details eines Commits auch die ausgeführten Feature-Schritte. Wo werden sie gespeichert?
Vorschlag: In der Datenbank des Cockpits, nur für Commits, die mit dem Cockpit hochgeladen wurden. Andere Commits zeigen nur Autor und Dateien.
Antwort:

[x] 16. Recht zum Löschen eines Repositories
Frage: Das Recht zum Löschen fragt das Cockpit erst beim Löschen an (Entscheidung aus Phase 4). Wie genau?
Vorschlag: Bei Anmeldung im Browser startet das Cockpit eine zweite Anmeldung im Browser mit diesem Recht. Der neue Zugang wird nur für das Löschen benutzt und danach verworfen. Bei einem selbst erstellten Token erklärt das Cockpit, welches Recht Sie auf GitHub ergänzen müssen.
Antwort:

[x] 17. Neue Dateien beim Verwerfen
Frage: Beim Verwerfen von Änderungen kommen neue Dateien in den Papierkorb (Konzept 9.7). Dafür gibt es die Bibliothek send2trash oder eine Funktion von Windows.
Vorschlag: Die Funktion von Windows, ohne neue Bibliothek. Zusätzlich legt das Cockpit wie immer vorher eine Sicherheitskopie an.
Antwort:


Meine Kommentare:
ERstens, halte dich möglichst an abläufe an, die GitHub auch selbst machen würde, wenn du das terminal benutzen würdest. 
Hier wichtig, ich will Projekte von mir in einer liste sehen und zu meinem Projekten hinzufügen könne, oder alle vonmeinem repository werden direkt zu meinen Projekten hinzugefügt, das fände ich am ienfachsten. 
Außerdem, da bin ich aber noch nicht so ganz drinne, mit den branches. man soll sachen in mian und unter branches verschieben, pushen und pullen können, also alle standardfunktionien mit branches ausführen können, die es auf GitHub gibt. hier bitte, eine gute übersicht finden, dass man immer den überblick hat, wo man gerade ist und das man Aktionen ausführen kann, wie in main hinzufügne. etc. und auch sowas wie in main brang´ch authoriseren, als admin etc. also wirklich alles von GitHub einbinden, so das man kein terminal mehr braucht. Hier viellecht noch das Konzept anpassen.

Antwort von Claude: Danke. Zu Ihren drei Punkten habe ich unten neue Fragen gestellt.


## F. Neue Fragen zu Ihren Kommentaren

[x] 18. Grundsatz: Abläufe wie bei Git und GitHub
Vorschlag: Ich nehme als Grundsatz in ENTSCHEIDUNGEN.md auf: Das Cockpit macht alles so, wie es Git im Terminal und GitHub Desktop machen. Es nutzt dieselben Git-Befehle und dieselben Voreinstellungen. Weicht es davon ab, steht der Grund in ENTSCHEIDUNGEN.md. Die Ausnahme bleibt: Nie ein force push.
Antwort:

[x] 19. Ihre Repositories automatisch in der Projektliste
Frage: Sollen alle Repositories Ihres Kontos gleich heruntergeladen werden?
Vorschlag: Alle Repositories Ihres GitHub-Kontos erscheinen von selbst in der Projektliste. Liegt eines noch nicht auf dem Rechner, steht dort zum Beispiel „Tagebuch, nur auf GitHub“. Enter lädt es in den Projekte-Hauptordner herunter. Es wird nicht alles sofort heruntergeladen, weil das viel Platz und Zeit kosten kann. In Firmen gibt es oft Hunderte Repositories.
Dazu:
- Repositories von Organisationen erscheinen nicht von selbst. Sie holen sie über „Projekt von der Plattform herunterladen“ (Frage 14).
- In den Grundeinstellungen gibt es „Neue Repositories automatisch herunterladen“. Die Vorgabe ist aus.
- Wollen Sie ein Repository nicht in der Liste sehen, wählen Sie „Aus der Liste entfernen“. Das Cockpit merkt sich das.
Antwort:

[x] 20. Branches: Umfang
Frage: Sie möchten mit Branches alles machen können, was GitHub kann, ohne Terminal. Im Konzept steht bisher nur ein kleiner Teil davon (Konzept 10.14).
Vorschlag: Ich erweitere Konzept 10.14. Ein Projekt bekommt eine Übersicht „Branches“ mit diesen Möglichkeiten:
- Immer sichtbar, wo man gerade ist: In der Projektliste steht „Code, Branch suche-pdfs“, wenn Sie nicht auf main sind. Jede Ansage beim Hochladen und Holen nennt den Branch.
- Liste aller Branches, lokal und auf GitHub, mit Stand: zum Beispiel „suche-pdfs, 2 Commits vor main, 1 offener Pull Request“.
- Branch anlegen, wechseln, umbenennen, löschen.
- Hochladen und Holen für den aktuellen Branch.
- In main übernehmen: direkt zusammenführen oder über einen Pull Request.
- Pull Requests: erstellen, ansehen, Kommentare lesen und schreiben, prüfen (Review mit „genehmigen“ oder „Änderungen anfordern“), übernehmen, schließen.
- Schutzregeln für main, wenn Sie Admin sind: zum Beispiel „Nur über Pull Request“ oder „Mindestens eine Genehmigung“.
- Änderungen beiseitelegen und zurückholen (Stash), zum Beispiel vor dem Wechsel des Branches.
Antwort:

[x] 21. Branches: Zeitpunkt
Frage: Laut Plan kommt das Feature Branches und Pull Requests erst in Phase 15. Wann soll es kommen?
Vorschlag: Aufteilen:
- In Phase 5 ist der Kern schon auf Branches vorbereitet: Hochladen und Holen arbeiten mit dem aktuellen Branch, und die Projektliste nennt ihn. Dazu kommt Teilschritt 5f mit der Übersicht „Branches“: anlegen, wechseln, umbenennen, löschen, in main zusammenführen und Stash.
- Pull Requests, Reviews und Schutzregeln kommen als eigene Phase direkt nach Phase 5, statt erst in Phase 15. Die Nummern der späteren Phasen verschieben sich dann um eins nach hinten.
Antwort:

[x] 22. Weitere Funktionen von GitHub
Frage: Damit man kein Terminal mehr braucht, fehlen im Konzept noch einige Funktionen von GitHub. Welche davon wollen Sie?
Vorschlag: Diese nehme ich ins Konzept auf und ordne sie Phasen zu:
- Tags, also Versionsmarken. Sie passen zum Feature Versionen (Phase 8).
- GitHub Actions: Läufe ansehen, Fehler lesen, neu starten. Passt zur Exe-Erstellung und zu Releases.
- Mitarbeiter zu einem Repository einladen und entfernen. Passt zu „Repository verwalten“.
- Issues sind schon im Feature Rückmeldungen enthalten.
Schreiben Sie gerne dazu, was Ihnen noch fehlt.
Antwort: