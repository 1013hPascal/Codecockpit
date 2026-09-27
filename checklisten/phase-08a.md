# Checkliste Phase 8a: Eingebautes Terminal

Stand: 27.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- Auf der Projektzeile und bei Code gibt es „Terminal …“. Befehle laufen in PowerShell im Projektordner bzw. im Ordner Code.
- Der Fokus beginnt im Feld „Befehl“. Umschalt+Tab führt in die „Ausgabe“, eine Liste mit einer Zeile pro Zeile.
- Pfeil hoch und runter holen frühere Befehle zurück. Escape bricht einen laufenden Befehl ab, sonst schließt es das Fenster.
- Ein force push ist gesperrt. Git bekommt die Zugangsdaten des Kontos, ohne dass Tokens in der Ausgabe erscheinen.
- Das Feld mit der Erklärung der KI kommt in 8b.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten reicht die Windows-Anmeldeinformationsverwaltung.


## A. Öffnen

[ ] 1. Hinweis beim ersten Öffnen
Tasten: Zu Code von PDF-Chat, Tab, zu „Terminal …“, Enter.
Erwartet: Zuerst eine Meldung: „Befehle im Terminal laufen ohne Rückfrage und ohne Sicherheitskopie. Gesperrt ist nur der force push.“ Nach OK öffnet sich „Terminal: PDF-Chat, Code“. Der Fokus steht im Feld „Befehl“.
Ergebnis:

[ ] 2. Ausgabe lesen
Tasten: Umschalt+Tab in die Ausgabe, lesen. Tab zurück ins Befehlsfeld.
Erwartet: Die Ausgabe heißt „Ausgabe“ und enthält die Zeile „Ordner: …\PDF-Chat\Code“.
Ergebnis:


## B. Befehle

[ ] 3. Ein Git-Befehl
Tasten: `git log --oneline -3` eintippen, Enter. Dann Umschalt+Tab und die Ausgabe lesen.
Erwartet: NVDA sagt „Läuft.“ und danach „Fertig. 3 Zeilen Ausgabe.“ Der Fokus bleibt im Befehlsfeld, das wieder leer ist. In der Ausgabe stehen „> git log --oneline -3“, drei Zeilen mit Commits (die neueste zuerst, „Hilfetext geändert“) und „Fertig.“ Die Markierung steht auf der letzten Zeile.
Ergebnis:

[ ] 4. Ein Fehler
Tasten: Im Befehlsfeld `git checkout gibt-es-nicht` eintippen, Enter. Ausgabe lesen.
Erwartet: NVDA sagt „Fehler, Rückgabewert 1. …“. In der Ausgabe steht die Meldung von Git, zum Beispiel „error: pathspec 'gibt-es-nicht' did not match …“, und „Fehler, Rückgabewert 1.“
Ergebnis:

[ ] 5. Frühere Befehle
Tasten: Im Befehlsfeld Pfeil hoch, Pfeil hoch, Pfeil runter.
Erwartet: Das Feld zeigt nacheinander „git checkout gibt-es-nicht“, „git log --oneline -3“ und wieder „git checkout gibt-es-nicht“.
Ergebnis:

[ ] 6. Zeile kopieren
Tasten: In der Ausgabe auf eine Commit-Zeile, Strg+C. In einem Editor einfügen.
Erwartet: NVDA sagt „Zeile kopiert.“ Im Editor steht genau diese Zeile.
Ergebnis:

[ ] 7. PowerShell-Befehl und Umlaute
Tasten: `Get-ChildItem -Name` eintippen, Enter. Dann `echo 'Grüße aus dem Terminal'`, Enter.
Erwartet: Die Ausgabe listet die Dateien im Ordner Code, eine pro Zeile, ohne leere Zeilen. Danach steht „Grüße aus dem Terminal“ mit richtigen Umlauten.
Ergebnis:


## C. Abbrechen und Sperren

[ ] 8. Laufenden Befehl abbrechen
Tasten: `Start-Sleep -Seconds 60` eintippen, Enter. Nach ein paar Sekunden Escape. Dann noch einmal Escape.
Erwartet: Während der Befehl läuft, gibt es den Knopf „Abbrechen“. Das erste Escape sagt „Wird abgebrochen.“ und danach „Abgebrochen.“, das Fenster bleibt offen. Das zweite Escape schließt das Terminal.
Ergebnis:

[ ] 9. Force push gesperrt
Tasten: Terminal wieder öffnen (kein Hinweis mehr). `git push --force` eintippen, Enter.
Erwartet: Es kommt kein Hinweis mehr wie in Punkt 1. NVDA sagt „Gesperrt. Ein force push überschreibt die Geschichte auf der Plattform …“. Nichts wird ausgeführt.
Ergebnis:

[ ] 10. Terminal beim Projekt
Tasten: Escape. Auf der Projektzeile PDF-Chat „Terminal …“. `Get-ChildItem -Name` eintippen, Enter.
Erwartet: Das Fenster heißt „Terminal: PDF-Chat“. Die Ausgabe nennt die Ordner Code und Exe.
Ergebnis:


## D. Mit GitHub (freiwillig)

[ ] 11. Holen mit Zugangsdaten
Tasten: Nur mit einem Projekt auf Ihrem echten GitHub-Konto, zum Beispiel Wetter aus Phase 6, falls noch vorhanden. Terminal bei Code, `git fetch --dry-run -v` eintippen, Enter.
Erwartet: Git holt ohne Nachfrage nach Benutzer oder Passwort. In der Ausgabe steht kein Token.
Ergebnis:
