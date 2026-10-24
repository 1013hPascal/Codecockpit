# Checkliste Paketübersicht

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Für die Punkte zu Chocolatey fragt Windows nach Administratorrechten. Für das Tauschen in Projekten brauchen Sie ein Projekt mit requirements.txt und Tests. Probieren Sie Löschen und Tauschen mit etwas, das Sie nicht brauchen.


## Menü und Übersicht

[ ] 1. Menü Pakete
Tasten: Alt+A.
Ansage: Das Menü „Pakete“ mit „Paketübersicht … Strg+Umschalt+P“, „Aufräumen …“, „Ordner nach Modellen durchsuchen …“, „Liste für einen neuen Rechner speichern …“ und „Liste einlesen und installieren …“.
Ergebnis:

[ ] 2. Übersicht öffnen
Tasten: Escape, dann Strg+Umschalt+P.
Ansage: Fenster „Paketübersicht“, Liste „Quellen“. Die erste Zeile nennt den Speicherplatz.
Fokus: In der Liste auf der ersten Quelle.
Ergebnis:

[ ] 3. Lesen und Prüfen im Hintergrund
Tasten: Nichts drücken, kurz warten.
Ansage: Ohne Sprache auf der Braillezeile „Pakete gelesen. Die Prüfung läuft noch.“ Später „Prüfung fertig: … veraltet.“ oder „Prüfung fertig: alles aktuell.“
Fokus: Bleibt, wo er war.
Ergebnis:

[ ] 4. Zeilen der Quellen
Tasten: Pfeil runter durch die Liste.
Ansage: Jede Zeile beginnt mit dem Namen der Quelle, dann die Anzahl und wie viele veraltet sind. Fehlt ein Programm, steht „nicht verfügbar“ mit dem Grund.
Ergebnis:

[ ] 5. Filter
Tasten: Alt+Z, dann Pfeil runter.
Ansage: „Alles“, „Nur Cockpit-Projekte“, „Nur übriger Rechner“. Die Zahlen in der Liste ändern sich.
Ergebnis:

[ ] 6. Verlauf
Tasten: Alt+V.
Ansage: Fenster „Verlauf der Paketübersicht“. Am Anfang „Noch keine Änderungen.“
Ergebnis:


## Pakete einer Quelle

[ ] 7. Quelle öffnen
Tasten: Auf pip Enter.
Ansage: Fenster mit dem Namen der Quelle, Liste „Pakete“. Neueste zuerst. Jede Zeile beginnt mit dem Namen, dann Version und „aktuell“ oder „veraltet“. Eine Lizenz steht in der Zeile, wenn sie bekannt ist.
Ergebnis:

[ ] 8. Suchen
Tasten: Alt+C, ein paar Buchstaben tippen.
Ansage: Die Liste zeigt nur passende Pakete.
Ergebnis:

[ ] 9. Aktionen mit Tab
Tasten: In der Liste Tab.
Ansage: „Aktualisieren …“, „Version wählen …“, „Festhalten“, „Zurück …“ und so weiter. Was nicht passt, ist ausgegraut oder fehlt.
Ergebnis:

[ ] 10. Version wählen
Tasten: „Version wählen …“.
Ansage: Liste der Versionen, neueste zuerst, auch ältere. Abbrechen ändert nichts.
Ergebnis:

[ ] 11. Aktualisieren und Zurück
Tasten: Auf einem veralteten Paket „Aktualisieren …“, bestätigen. Danach „Zurück zu … “.
Ansage: Vorher eine Rückfrage, Vorgabe ist die sichere Antwort. Danach „aktuell“. Nach „Zurück“ wieder die alte Version. Beides steht im Verlauf.
Ergebnis:

[ ] 12. Festhalten
Tasten: „Festhalten“.
Ansage: Die Zeile sagt „festgehalten“. „Alle veralteten aktualisieren …“ lässt das Paket aus.
Ergebnis:

[ ] 13. Warnungen
Tasten: Pakete mit großem Versionssprung oder bekannter Sicherheitslücke suchen.
Ansage: Die Zeile warnt, zum Beispiel „Sicherheitslücke bekannt, behoben in …“.
Ergebnis:

[ ] 14. Löschen
Tasten: Auf einem unwichtigen Paket „Löschen …“.
Ansage: Rückfrage, Vorgabe und Escape sind „Abbrechen“. Nach dem Löschen liegt in den Sicherheitskopien „Paketübersicht“ eine Liste mit dem Befehl zum Wiederherstellen.
Ergebnis:

[ ] 15. winget und Chocolatey
Tasten: Escape, die Quellen winget und Chocolatey öffnen.
Ansage: Wie bei pip. Bei Chocolatey fragt Windows nach Administratorrechten, bevor etwas geändert wird.
Ergebnis:


## Sprachmodelle

[ ] 16. Modelle
Tasten: Quelle Sprachmodelle öffnen.
Ansage: Modelle von Hugging Face, Ollama und die des Cockpits. Die Zeile nennt Größe und „benutzt von …“, wenn ein Projekt oder das Cockpit das Modell braucht.
Ergebnis:

[ ] 17. Neue Fassung, alte bleibt
Tasten: Auf einem veralteten Modell „Aktualisieren …“.
Ansage: Die alte Fassung bleibt liegen. Danach ist „Alte Fassungen entfernen …“ möglich.
Ergebnis:

[ ] 18. Ordner nach Modellen durchsuchen
Tasten: Escape, Alt+M, einen Ordner mit Modelldateien wählen.
Ansage: „… Modelldateien gefunden, …“. Sie stehen danach bei den Sprachmodellen.
Ergebnis:


## Aufräumen

[ ] 19. Aufräumen
Tasten: Alt+A im Fenster Paketübersicht.
Ansage: Liste mit Kontrollkästchen, „Was soll weg?“. Nichts ist angehakt. Jede Zeile nennt zuerst, was es ist, dann die Größe.
Ergebnis:

[ ] 20. Aufräumen bestätigen
Tasten: Etwas mit der Leertaste anhaken, OK.
Ansage: Rückfrage mit der Anzahl und dem Platz. Nach dem Bestätigen, wie viel frei geworden ist.
Ergebnis:


## In Projekten tauschen

[ ] 21. Bibliotheken in Projekten
Tasten: Alt+J im Fenster Paketübersicht, nach dem Ende der Prüfung.
Ansage: Liste „Neuere Bibliotheken in Projekten“, nichts angehakt. Nach dem Bestätigen: „Fertig. Der Bericht ist da.“ und ein Bericht mit Branch und Ergebnis der Tests.
Auf dem Rechner: Im Projekt gibt es den Branch „Cockpit-pakete-aktualisieren“. main ist unverändert.
Ergebnis:

[ ] 22. Modell tauschen mit Vorschlag der KI
Tasten: Bei einem Modell „In Projekten tauschen …“, dann „Vorschlag der KI …“.
Ansage: Die Vorschläge sind als Vorschlag gekennzeichnet. Dann die Liste „Stellen“ und eine Rückfrage. Die Änderung kommt in den Branch „Cockpit-modell-tauschen“.
Ergebnis:


## Neuer Rechner

[ ] 23. Liste speichern
Tasten: Menü Pakete, „Liste für einen neuen Rechner speichern …“, Ort wählen.
Ansage: „Liste gespeichert, … Einträge.“
Ergebnis:

[ ] 24. Liste einlesen
Tasten: Menü Pakete, „Liste einlesen und installieren …“, dieselbe Datei.
Ansage: Auf demselben Rechner fehlt nichts. Auf einem anderen Rechner eine Liste „Was soll installiert werden?“, alles angehakt.
Ergebnis:


## Feature ausschalten

[ ] 25. Ohne das Feature
Tasten: Feature-Verwaltung, Paketübersicht ausschalten, dann Strg+Umschalt+P.
Ansage: „Die Paketübersicht ist ausgeschaltet. Sie schalten sie in der Feature-Verwaltung ein.“
Ergebnis:
