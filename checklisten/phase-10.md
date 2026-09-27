# Checkliste Phase 10: Exe

Stand: 27.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- „Exe hinzufügen …“ auf der Projektzeile, danach der Eintrag Exe unter Code.
- Die Zeile Exe nennt Herkunft, Datum und ob die Exe älter als der Code ist.
- Bei Exe: Exe aus dem Code erstellen bzw. aktualisieren, Exe-Datei wählen, Exe veröffentlichen, Exe aus dem Release holen, Exe-Einrichtung prüfen, Wie funktioniert die Exe?
- Das Cockpit hat jetzt eine eigene Exe: `Codecockpit\Exe\CodeCockpit.exe`.
- Im Menü Hilfe: „Python installieren …“ und „Wie funktioniert die Exe? …“.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten reicht die Windows-Anmeldeinformationsverwaltung.


## A. Exe hinzufügen

[ ] 1. Aktion auf der Projektzeile
Tasten: Auf ein Projekt ohne Exe gehen, zum Beispiel Tagebuch. Tab in die Aktionen.
Erwartet: Es gibt „Exe hinzufügen …“. Bei Projekten mit Exe gibt es sie nicht.
Ergebnis:

[ ] 2. Ordner anlegen
Tasten: Enter auf „Exe hinzufügen …“, dann „Anlegen“.
Erwartet: Die Rückfrage nennt den Ordner Exe im Projektordner. Danach sagt NVDA „Ordner Exe angelegt.“ Der Fokus steht in der Projektliste auf „Exe, noch keine Exe-Datei“ unter Code.
Ergebnis:

[ ] 3. Aktionen bei Exe
Tasten: Tab.
Erwartet: „Exe starten, nicht verfügbar: Im Ordner Exe liegt keine Exe.“, „Exe aus dem Code erstellen …“, „Exe-Datei wählen …“, „Exe-Einrichtung prüfen“, „Exe-Ordner öffnen“, „Wie funktioniert die Exe? …“. Aktionen, die nicht passen, fehlen.
Ergebnis:


## B. Exe-Datei wählen

[ ] 4. Eine Exe übernehmen
Tasten: „Exe-Datei wählen …“, „Eine Exe-Datei …“. Wählen Sie eine beliebige Exe, zum Beispiel C:\Windows\notepad.exe. Dann „Übernehmen“.
Erwartet: Die Rückfrage sagt, dass die Datei in den Ordner Exe kopiert wird. Danach „Exe übernommen: notepad.exe.“ Die Zeile heißt „Exe, extern erstellt am …“ mit dem heutigen Datum. „Exe starten“ öffnet den Editor.
Ergebnis:

[ ] 5. Noch einmal wählen
Tasten: Noch einmal eine Exe wählen, zum Beispiel C:\Windows\System32\calc.exe.
Erwartet: Die Rückfrage sagt zusätzlich, dass die bisherige Exe in die Sicherheitskopien kommt. Danach steht sie unter Datei, Sicherheitskopien.
Ergebnis:


## C. Exe aus dem Code erstellen

[ ] 6. Erster Bau: Einstellungen
Tasten: Bei Exe von Tagebuch „Exe aus dem Code aktualisieren …“ (oder „erstellen“).
Erwartet: Das Fenster „Exe einrichten: Tagebuch“ mit Startdatei main.py, Name der Exe Tagebuch, Bauart „Eine Exe-Datei“, dem Kästchen „Ohne Konsolenfenster“ und dem Feld für das Symbol. Weiter führt zu einer Rückfrage, die den Ablauf beschreibt. „Starten“.
Ergebnis:

[ ] 7. Der Bau
Tasten: Warten. Mit Pfeiltasten in der Ausgabe lesen.
Erwartet: Das Fenster „Exe erstellen: Tagebuch“, der Fokus in der Liste „Ausgabe“. NVDA sagt die Schritte an, zum Beispiel „Schritt 2 von 4: Exe wird gebaut“. Beim ersten Mal lädt das Cockpit PyInstaller, das dauert einige Minuten. Am Ende: „Exe erstellt, getestet und übernommen: Tagebuch.exe. Die bisherige Exe steht in den Sicherheitskopien.“
Ergebnis:

[ ] 8. Zeile und Veraltet
Tasten: Fenster schließen. Die Zeile Exe lesen. Dann eine Datei im Code von Tagebuch ändern, hochladen und die Zeile Exe noch einmal lesen (Strg+R liest neu ein).
Erwartet: Zuerst „Exe, vom Cockpit erstellt am …, aktuell“. Nach dem neuen Commit „…, älter als der Code“. Im Ordner Code gibt es jetzt Tagebuch.spec.
Ergebnis:

[ ] 9. Abbrechen
Tasten: „Exe aus dem Code aktualisieren …“, Starten, nach ein paar Sekunden Escape. Dann noch einmal Escape.
Erwartet: Das erste Escape sagt „Wird abgebrochen.“ und dann „Abgebrochen. Die bisherige Exe bleibt.“ Das zweite schließt das Fenster. Die Exe ist unverändert.
Ergebnis:

[ ] 10. Einrichtung prüfen
Tasten: „Exe-Einrichtung prüfen“.
Erwartet: NVDA sagt die Gesamtbewertung, zum Beispiel „Bereit, mit 1 Warnung.“ Die Liste zeigt jede Prüfung mit dem Ergebnis vorne, zum Beispiel „In Ordnung: Tagebuch.spec ist da.“
Ergebnis:

[ ] 11. Anleitungen
Tasten: „Wie funktioniert die Exe? …“. Dann im Menü Hilfe „Python installieren …“.
Erwartet: Beide Anleitungen öffnen sich als Liste mit einem Satz pro Zeile.
Ergebnis:


## D. Die eigene Exe des Cockpits

Wichtig: Auf Ihrem Rechner ist die Intelligente App-Steuerung von Windows eingeschaltet. Sie blockiert jede selbst gebaute Exe ohne Signatur. Solange sie an ist, schlagen der Test in Punkt 7 und die Punkte 12 und 13 fehl, mit der Meldung „Windows hat die Exe blockiert …“. Dann tragen Sie bitte ein, ob diese Meldung verständlich war.

[ ] 12. Exe starten
Tasten: Schließen Sie das Cockpit. Starten Sie im Explorer `Codecockpit\Exe\CodeCockpit.exe`.
Erwartet: Das Cockpit startet mit Ihren echten Daten, wie mit start.bat. Der Start dauert ein paar Sekunden länger, weil die Exe sich entpackt. Menüs, Anleitungen (F1, Menü Hilfe) und die Einführungen der Features funktionieren.
Ergebnis:

[ ] 13. Windows-Warnung (falls sie kommt)
Erwartet: Kommt „Der Computer wurde durch Windows geschützt“, geht es mit „Weitere Informationen“ und „Trotzdem ausführen“ weiter. Das steht so in der Anleitung.
Ergebnis:


## E. Mit GitHub (freiwillig)

[ ] 14. Exe veröffentlichen
Tasten: Nur bei einem eigenen Test-Repository auf GitHub mit Exe. Bei Exe „Exe veröffentlichen …“.
Erwartet: Das Fenster hat „Version“ mit Vorschlag 1.0.0 (oder der nächsten Nummer), „Versionshinweise“ und „Vorschlag der KI“ (Alt+I). Die Rückfrage nennt Release, Tag und Größe. Danach „Version 1.0.0 veröffentlicht. Link kopiert.“ Die Zeile Exe nennt die Version.
Ergebnis:

[ ] 15. Exe aus dem Release holen
Tasten: Bei einem Projekt, dessen Repository ein Release mit Exe hat, „Exe aus dem Release holen …“.
Erwartet: Die Rückfrage nennt Datei, Größe und Release. Danach „Exe aus dem Release v1.0.0 übernommen.“ und die Zeile „Exe, Version 1.0.0, aus dem Release am …“.
Ergebnis:
