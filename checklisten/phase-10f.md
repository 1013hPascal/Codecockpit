# Checkliste 10f: Ein Ordner pro Branch

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Zum Testen eignet sich ein Projekt mit mindestens einem Branch auf GitHub. Das Cockpit selbst stellen Sie am besten erst ganz am Schluss um (Punkt 12).


## Einrichten

[ ] 1. Aktion auf Code in der alten Struktur
Tasten: Projekt ausklappen, auf Code, Tab in die Aktionen.
Ansage: Unter den Aktionen steht „Ordner für Branches einrichten …“.
Fokus: In der Aktionsliste.
Ergebnis:

[ ] 2. Einrichten
Tasten: Enter auf „Ordner für Branches einrichten …“, dann „Einrichten“.
Ansage: Vorher eine Rückfrage, die nennt, wohin der Code wandert, und dass eine Sicherheitskopie entsteht. Danach „Ordner für Branches eingerichtet. Der Code liegt jetzt in Code\main.“
Fokus: Auf der Zeile „Code, main, …“.
Im Explorer: Im Ordner Code liegt nur noch der Ordner main.
Ergebnis:

[ ] 3. Ordner in Benutzung
Tasten: Den Ordner Code eines anderen Projekts im Explorer oder im Terminal öffnen und eine Datei darin in einem Editor offen lassen. Dann einrichten.
Ansage: Fehlermeldung „… Ist der Ordner noch in einem anderen Programm geöffnet …? Es wurde nichts geändert.“
Fokus: Nach OK zurück in der Aktionsliste. Im Ordner Code ist alles wie vorher.
Ergebnis:


## Branches

[ ] 4. Neuer Branch
Tasten: Auf „Code, main“, Aktion „Neuer Branch …“, Name eingeben, Enter.
Ansage: „Branch … wird angelegt.“, dann „Branch … angelegt, im Ordner Code\….“ Gibt es in main eine virtuelle Umgebung, später leise im Meldungsverlauf: „Virtuelle Umgebung für … angelegt.“
Fokus: Auf der neuen Zeile „Branch …, Branch noch nicht auf GitHub“.
Im Explorer: Neben main liegt ein Ordner mit dem Namen des Branches.
Ergebnis:

[ ] 5. Arbeiten im Branch-Ordner
Tasten: Im Branch-Ordner eine Datei ändern, Strg+R. Dann auf der Zeile des Branches Enter.
Ansage: Die Zeile nennt „1 Datei noch nicht hochgeladen“. Enter startet das Hochladen für diesen Branch. Die Zeile „Code, main“ bleibt unverändert.
Fokus: Nach dem Hochladen wieder auf der Zeile des Branches.
Ergebnis:

[ ] 6. Aktionen im Branch-Ordner
Tasten: Auf der Zeile des Branches Tab.
Ansage: Die Aktionen wie bei Code, dazu „Branch-Ordner entfernen …“ und, wenn die Exe eingerichtet ist, „Exe aus diesem Branch erstellen …“. „Ordner für Branches einrichten …“ fehlt.
Fokus: In der Aktionsliste.
Ergebnis:

[ ] 7. Übersicht Branches
Tasten: Auf „Code, main“ die Aktion „Branches …“. Einen Branch ohne Ordner markieren.
Ansage: Statt „Zu … wechseln“ gibt es den Knopf „Ordner für … anlegen“. Bei Branches mit Ordner fehlt er. „Neuer Branch …“ legt einen Branch mit Ordner an.
Fokus: In der Liste der Branches.
Ergebnis:

[ ] 8. Branches auf GitHub
Tasten: Auf der Zeile „Branches auf GitHub“ Enter.
Ansage: „Branches auf GitHub werden abgefragt.“, dann eine Auswahl mit den Branches anderer, zum Beispiel „design, nur auf GitHub, zuletzt von …“. Enter wählt.
Fokus: Danach auf der neuen Zeile „Branch design, nur auf GitHub, …“.
Ergebnis:

[ ] 9. Anpinnen
Tasten: Auf dieser Zeile Enter („In Liste anpinnen“).
Ansage: „design wird heruntergeladen.“, dann „design angepinnt, im Ordner Code\design.“
Fokus: Auf der Zeile „Branch design, …“, jetzt mit eigenem Ordner.
Ergebnis:

[ ] 10. Branch-Ordner entfernen
Tasten: Auf einer Branch-Zeile die Aktion „Branch-Ordner entfernen …“.
Ansage: Rückfrage mit „Behalten“ als Vorgabe. Gibt es nicht hochgeladene Änderungen, nennt sie die Sicherheitskopie. Nach „Entfernen“: „Ordner … entfernt.“
Fokus: Auf „Code, main“. Der Branch selbst steht weiter in der Übersicht Branches.
Ergebnis:


## Exe und neue Projekte

[ ] 11. Exe aus einem Branch
Tasten: Auf einer Branch-Zeile „Exe aus diesem Branch erstellen …“, dann „Starten“.
Ansage: Die Schritte wie beim normalen Bau, am Ende „Exe aus dem Branch erstellt und abgelegt: CodeCockpit_branch_….exe.“
Fokus: In der Ausgabe.
Im Explorer: Im Ordner Exe liegen die normale Exe und die Branch-Exe. Die Zeile „Exe, …“ meint weiter die normale.
Ergebnis:

[ ] 12. Das Cockpit selbst umstellen
Tasten: Claude und start.bat beenden. In der Exe beim Cockpit „Ordner für Branches einrichten …“.
Ansage: Wie bei Punkt 2.
Danach: Sagen Sie mir Bescheid. Ich kopiere die Einstellungen und Erinnerungen von Claude, dann starten Sie Claude im Ordner `Code\main`.
Ergebnis:

[ ] 13. Neues Projekt von GitHub
Tasten: Ein Repository herunterladen, das nur auf GitHub liegt.
Ansage: Wie bisher.
Im Explorer: Der Code liegt in `Code\main`.
Ergebnis:

[ ] 14. Schalter in den Grundeinstellungen
Tasten: Alt+E, G, zum Kontrollkästchen „Neue Projekte mit einem Ordner pro Branch“.
Ansage: Kontrollkästchen, aktiviert. Ausgeschaltet kommen neue Projekte wie bisher direkt in Code.
Fokus: Auf dem Kontrollkästchen.
Ergebnis:
