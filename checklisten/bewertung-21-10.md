# Checkliste: Punkte aus der Bewertung vom 21.10.2026

Stand: 21.10.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.

Die genauen Schritte zu jedem Punkt stehen auch in den Kurzanleitungen (F1).


## Vorbereitung

1. Nehmen Sie ein Testprojekt mit GitHub-Konto, nicht ein wichtiges Projekt.
2. Ändern Sie zwei Dateien. In einer Datei ändern Sie zwei Stellen, weit auseinander.


## A. Auswahl beim Commit

[ ] 1. Dateien abhaken
Tasten: Auf dem Main-Branch „Änderungen hochladen“, dann Tab bis „Änderungen“. Leertaste hakt eine Datei ab oder an.
Erwartet: Jede Zeile beginnt mit dem Dateinamen, danach „geändert“ oder „neu“. NVDA sagt den Zustand des Kästchens.
Ergebnis:

[ ] 2. Abschnitte einer Datei wählen
Tasten: Auf der Datei mit zwei Stellen Enter.
Erwartet: Ein Fenster mit den Abschnitten öffnet sich. Nach der Wahl von einem Abschnitt sagt NVDA „1 von 2 Abschnitten gewählt.“ In der Liste steht hinter der Datei „1 von 2 Abschnitten“.
Ergebnis:

[ ] 3. Vorschlag der KI passt zur Auswahl
Tasten: Alt+V, wenn der KI-Assistent im Projekt aktiv ist.
Erwartet: Der Vorschlag beschreibt nur die gewählten Dateien und Abschnitte. Der Fokus geht danach in das Feld „Was haben Sie geändert?“.
Ergebnis:

[ ] 4. Co-Autoren
Tasten: Alt+A für „Co-Autoren …“.
Erwartet: Eine Liste mit Personen aus dem Verlauf. Gibt es keine, sagt NVDA „Im Verlauf gibt es noch keine anderen Personen.“
Ergebnis:


## B. Verlauf: Nachbessern, Übernehmen, Umsortieren, Branch ab hier

[ ] 5. Commit nachbessern
Tasten: Wie in der Kurzanleitung „Commit nachbessern“.
Erwartet: Vorher kommt eine Rückfrage. Die sichere Antwort ist die Vorgabe, Escape bricht ab.
Ergebnis:

[ ] 6. Commit in einen anderen Branch übernehmen
Tasten: Wie in der Kurzanleitung „Commit in einen anderen Branch übernehmen“.
Erwartet: Ist der Commit dort schon, meldet das Cockpit das. Es meldet keinen Konflikt.
Ergebnis:

[ ] 7. Commits umsortieren oder zusammenfassen, Branch ab einem früheren Commit
Tasten: Wie in den beiden Kurzanleitungen.
Erwartet: Jeder Schritt fragt vorher nach und legt eine Sicherheitskopie an.
Ergebnis:


## C. Konflikte und Editor

[ ] 8. Stellen lesen und lösen
Tasten: Im Fenster „Konflikte lösen“ auf einer Datei Enter oder „Stellen lesen und lösen …“.
Erwartet: Eine Liste „Stellen“. Enter auf einer Stelle zeigt beide Fassungen als Text. Die Knöpfe heißen „Meine Fassung“, „Fassung von GitHub“ und „Beide, meine zuerst“. Nach der letzten Stelle gilt die Datei als gelöst.
Ergebnis:

[ ] 9. Konflikt im Editor anzeigen
Tasten: Den Knopf „Konflikt im Editor anzeigen“.
Erwartet: Der Editor öffnet die Datei an der ersten Stelle. Bei VS Code steht der Cursor in dieser Zeile.
Ergebnis:

[ ] 10. Im Editor öffnen
Tasten: Auf einem Branch die Aktion „Im Editor öffnen“.
Erwartet: Der Editor aus den Einstellungen öffnet den Code-Ordner. Ist das Feld leer, sucht das Cockpit VS Code, dann Notepad++, dann Notepad.
Ergebnis:


## D. Pull Requests und Forks

[ ] 11. Checks ansehen
Tasten: In den Details eines Pull Requests Alt+C für „Checks …“.
Erwartet: Jede Zeile beginnt mit dem Namen des Checks, danach der Zustand. Beim Zusammenführen steht der Stand der Checks in der zweiten Zeile.
Ergebnis:

[ ] 12. Fremdes Projekt herunterladen
Tasten: „Projekt von GitHub herunterladen“, dann eine Adresse eines fremden Projekts eingeben.
Erwartet: Eine Rückfrage, ob nur herunterladen oder einen Fork anlegen. Die Vorgabe ist „Abbrechen“, Escape bricht ab.
Ergebnis:

[ ] 13. Vom Original holen
Tasten: Beim Fork auf dem Main-Branch „Vom Original holen …“.
Erwartet: Die Aktion steht nur bei einem Fork. Hat main eigene Commits, kommt eine Fehlermeldung statt einer Änderung.
Ergebnis:


## E. Issues

[ ] 14. Issues ohne KI
Tasten: Auf dem Main-Branch „Issues …“.
Erwartet: Der Titel nennt Projekt, Anzahl und „offene“. Jede Zeile beginnt mit „Nr.“ und dem Titel. Anlegen, Kommentieren, Labels, Zuweisen und Schließen gehen. Schließen fragt nach.
Ergebnis:

[ ] 15. Issues mit KI
Tasten: In den Details eines Issues „Mit KI zusammenfassen“.
Erwartet: Die Zusammenfassung und ein Branch-Name stehen oben in den Angaben. Der Branch-Name beginnt mit der Nummer des Issues.
Ergebnis:

[ ] 16. Branch für ein Issue
Tasten: In der Liste „Branch dafür anlegen …“.
Erwartet: Das Feld zeigt den Namen vorab. Der Branch entsteht wie bei „Neuer Branch“.
Ergebnis:


## F. Exe-Bau

[ ] 17. Probelauf vor dem Bau
Tasten: „Exe aus dem Code erstellen“ in einem Projekt, in dem eine Bibliothek in requirements.txt fehlt.
Erwartet: Nach Schritt 1 steht „Probelauf: Code und Bibliotheken werden geprüft.“ in der Ausgabe. Der Bau hört nach Sekunden auf. Die Meldung nennt die fehlende Bibliothek und rät, sie in requirements.txt einzutragen.
Ergebnis:

[ ] 18. Bau wie bisher
Tasten: Derselbe Bau in einem Projekt ohne Fehler.
Erwartet: In der Ausgabe steht „Probelauf bestanden“ mit der Zahl der Dateien. Danach läuft der Bau wie gewohnt. Die Fenster sehen aus wie vorher.
Ergebnis:


## G. Automatische Tests auf GitHub

[ ] 19. Tests nach dem Hochladen
Tasten: Nach dem nächsten Hochladen die Checks eines Pull Requests von CodeCockpit ansehen.
Erwartet: Ein Check „tests“ läuft und ist am Ende bestanden.
Ergebnis:


## H. Release nach einer neuen Version

[ ] 20. Ohne Exe
Tasten: In einem Projekt mit Exe-Erstellung, aber ohne Exe, Änderungen hochladen und „neue Version“ wählen.
Erwartet: Die Frage sagt „Es gibt noch keine Exe. Möchten Sie eine hinzufügen?“. Die Knöpfe heißen „Exe aus dem Code erstellen …“, „Vorhandene Exe wählen …“, „Release nur mit Quellcode …“ und „Später“. Der Fokus steht auf „Später“, Escape wählt „Später“.
Ergebnis:

[ ] 21. Mit Exe
Tasten: Dasselbe in einem Projekt mit Exe.
Erwartet: Die Frage lautet „Für Version … ein Release mit der Exe auf GitHub anlegen?“. Die Knöpfe heißen „Release mit Exe anlegen“ und „Später“.
Ergebnis:

[ ] 22. Nur Quellcode
Tasten: Bei Punkt 20 „Release nur mit Quellcode …“.
Erwartet: Das Fenster heißt „Release anlegen: …, nur Quellcode“, nicht mehr „Exe veröffentlichen“.
Ergebnis: