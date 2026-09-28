# Checkliste 10g: Exe mit Daten, Prüfung und KI-Hilfe

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Zum Testen eignet sich die VokabelApp. Ich habe sie dafür absichtlich nicht von Hand repariert.


## Branch-Zeilen (Wünsche aus dem Test von 10f)

[ ] 1. Branch verwalten
Tasten: Beim Cockpit auf die Zeile „Branch Exe-bauen-intelligent, …“, Tab.
Ansage: Die erste Aktion ist „Exe-bauen-intelligent verwalten …“. „Branches …“ fehlt.
Fokus: In der Aktionsliste.
Ergebnis:

[ ] 2. Fenster „… verwalten“
Tasten: Enter auf „Exe-bauen-intelligent verwalten …“.
Ansage: Titel „Exe-bauen-intelligent verwalten“. Die Liste hat nur diesen Branch. Die Zeile beginnt mit „Exe-bauen-intelligent, Ordner Code\Exe-bauen-intelligent, …“. Per Tab: In main übernehmen, Umbenennen, Branch-Ordner entfernen, Löschen, Schließen.
Fokus: In der Liste.
Ergebnis:

[ ] 3. Branch auf GitHub hochladen
Tasten: Auf einer Branch-Zeile, deren Branch noch nicht auf GitHub ist, Tab.
Ansage: „Branch auf GitHub hochladen …“ statt „Änderungen hochladen …“. Enter fragt „Der Branch … ist noch nicht auf GitHub. Jetzt hochladen?“ oder, bei Änderungen, nach der Commit-Nachricht.
Fokus: Nach dem Hochladen auf der Branch-Zeile. Sie nennt danach „alles hochgeladen“.
Ergebnis:

[ ] 4. Übersicht Branches auf main
Tasten: Auf „Code, main“ die Aktion „Branches …“.
Ansage: Keine Zeile sagt „aktueller Branch“. Jede nennt ihren Ordner, zum Beispiel „main, Ordner Code\main, Haupt-Branch, …“ oder „design, ohne Ordner, …“.
Fokus: In der Liste.
Ergebnis:


## Prüfung

[ ] 5. Exe-Einrichtung prüfen bei der VokabelApp
Tasten: Bei der VokabelApp auf „Exe“, Aktion „Exe-Einrichtung prüfen“.
Ansage: „Nicht bereit: …“. In der Liste unter anderem: „Problem: Die Startdatei engine.py startet nichts … Wahrscheinlich ist gui.py richtig.“, „Problem: Diese Bibliotheken stehen nicht in requirements.txt und fehlen deshalb in der Exe: PySide6.“, „Warnung: Der Code nutzt den Ordner Meine-Vokabeln …“ und „Warnung: gui.py sucht Meine-Vokabeln im Startordner …“.
Fokus: In der Liste.
Ergebnis:

[ ] 6. Strengerer Start-Test
Tasten: Bei der VokabelApp noch einmal „Exe aus dem Code aktualisieren …“, ohne vorher etwas zu ändern.
Ansage: Am Ende „Fehler: Die neue Exe hat sich gleich nach dem Start ohne Fenster beendet …“. Die bisherige Exe bleibt.
Fokus: In der Ausgabe.
Ergebnis:


## Exe mit KI einrichten

[ ] 7. Start
Tasten: Bei der VokabelApp auf „Exe“, Aktion „Exe mit KI einrichten …“.
Ansage: Läuft die KI außerhalb Ihres Rechners, erst die Rückfrage zum Senden. Dann das Fenster mit dem Feld „Was soll die Exe können? Freiwillig“.
Fokus: Im Textfeld.
Ergebnis:

[ ] 8. Wunsch und Vorschlag
Tasten: Schreiben Sie zum Beispiel „Der Ordner Meine-Vokabeln soll neben der Exe liegen, und Nutzer sollen dort Vokabeln hinzufügen können.“ Dann Alt+W.
Ansage: „Die KI sieht sich den Code an.“, dann „Vorschlag da.“ und ein Fenster „Vorschlag für die Exe von VokabelApp: … Änderungen“.
Fokus: In der Liste des Vorschlags.
Ergebnis:

[ ] 9. Vorschlag lesen
Tasten: Mit den Pfeiltasten durch die Liste, Enter auf einer Änderung.
Ansage: Zeilen wie „Einstellung: Startdatei: gui.py statt engine.py.“, „Einstellung: Ordner neben der Exe: Meine-Vokabeln.“, „requirements.txt: Bibliotheken ergänzen …“, „gui.py: …“. Enter zeigt „Bisher:“ und „Neu:“. Passt eine Änderung nicht, steht „Nicht übernehmbar: …“ dahinter.
Fokus: Im Textfenster, nach Escape zurück in der Liste.
Ergebnis:

[ ] 10. Übernehmen und testen
Tasten: Alt+B, dann „Übernehmen“, dann „Bauen und testen“.
Ansage: „Änderungen übernommen.“, dann der Bau mit den Schritten. Am Ende „Exe erstellt, getestet und übernommen: VokabelApp.exe. Neu neben der Exe: Meine-Vokabeln.“
Im Explorer: Im Ordner Exe\VokabelApp liegt der Ordner Meine-Vokabeln. In den Sicherheitskopien steht „VokabelApp vor den Änderungen für die Exe“.
Ergebnis:

[ ] 11. Die Exe selbst
Tasten: Exe starten, eine Lektion öffnen.
Ansage: Die Kurse aus Meine-Vokabeln erscheinen.
Ergebnis:


## Daten der Nutzer bleiben

[ ] 12. Eigene Vokabeln bleiben beim nächsten Bau
Tasten: Im Explorer eine eigene CSV-Datei in Exe\VokabelApp\Meine-Vokabeln anlegen. Dann „Exe aus dem Code aktualisieren …“.
Ansage: Wie beim Bau.
Im Explorer: Die eigene Datei ist noch da.
Ergebnis:

[ ] 13. Exe-Einstellungen ändern
Tasten: Auf „Exe“, Aktion „Exe-Einstellungen …“.
Ansage: Das Formular mit den bisherigen Werten, unten „Ordner neben der Exe, mit Komma getrennt …“. Nach Weiter die Rückfrage zum Speichern, dann „Soll die Exe jetzt mit den neuen Einstellungen gebaut werden?“ mit „Später“ als Vorgabe.
Fokus: Im ersten Feld des Formulars.
Ergebnis:

[ ] 14. Veröffentlichen mit Daten
Tasten: „Exe veröffentlichen …“ bei der VokabelApp.
Ansage: Die Rückfrage nennt eine ZIP-Datei.
Auf GitHub: In der ZIP-Datei liegen der Programmordner und Meine-Vokabeln so, wie sie im Ordner Code stehen, ohne Ihre eigenen Dateien aus dem Ordner Exe.
Ergebnis:
