# Checkliste 8d: Spracheingabe

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Zum Testen starten Sie das Cockpit aus dem Branch-Ordner Spracheingabe oder mit einer Exe aus diesem Branch. Ein Mikrofon muss angeschlossen sein.


## Einrichten

[ ] 1. Feature in der Feature-Verwaltung
Tasten: Alt+F, Feature-Verwaltung, auf „KI“, Tab in die Liste der KI-Features.
Ansage: Unter den KI-Features steht „Spracheingabe“, eingeschaltet.
Fokus: In der Liste der KI-Features.
Ergebnis:

[ ] 2. Sprach-KI in der KI-Verwaltung
Tasten: Alt+K, KI-Verwaltung, dann Alt+K für „Sprach-KI …“.
Ansage: Fenster „Sprach-KI“, Liste „Whisper-Modelle auf diesem Rechner“, zum Beispiel „medium, gewählt, ab 32 GB Arbeitsspeicher, etwa 1,5 GB, empfohlen für Ihren Rechner, nicht heruntergeladen“.
Fokus: In der Liste.
Ergebnis:

[ ] 3. Modell wählen
Tasten: Pfeil auf „small“, Enter.
Ansage: „small gewählt.“ Die Zeile nennt jetzt „small, gewählt, …“.
Fokus: Bleibt in der Liste.
Ergebnis:


## Diktieren

[ ] 4. Erstes Diktieren lädt das Modell
Tasten: Eine Commit-Nachricht öffnen, zum Beispiel über „Änderungen hochladen …“, im Textfeld Strg+D.
Ansage: Rückfrage „Für die Spracheingabe braucht das Cockpit das Whisper-Modell …, etwa … MB …“. Vorgabe ist „Abbrechen“. Nach „Herunterladen“: „Whisper-Modell wird heruntergeladen.“, leise Fortschritt in der Statuszeile, am Ende „Whisper-Modell heruntergeladen.“
Fokus: Bleibt im Textfeld.
Ergebnis:

[ ] 5. Aufnahme und Einfügen
Tasten: Im Textfeld Strg+D, einen Satz sprechen, noch einmal Strg+D.
Ansage: „Aufnahme läuft.“, dann „Wird umgewandelt.“, dann „Text eingefügt.“
Fokus: Im Textfeld, der Text steht an der Schreibmarke.
Ergebnis:

[ ] 6. Abbrechen
Tasten: Strg+D, etwas sagen, dann Strg+Umschalt+D.
Ansage: „Aufnahme abgebrochen.“ Es wird nichts eingefügt.
Fokus: Im Textfeld.
Ergebnis:

[ ] 7. Einzeiliges Feld
Tasten: Im Feld für den Titel eines Pull Requests Strg+D, zwei Sätze mit Pause sprechen, Strg+D.
Ansage: „Text eingefügt.“ Der Text steht in einer Zeile. Stand vorher schon Text, ist ein Leerzeichen dazwischen.
Fokus: Im Feld.
Ergebnis:

[ ] 8. Außerhalb eines Textfelds
Tasten: In der Projektliste Strg+D.
Ansage: „Diktieren geht nur in einem Textfeld.“
Fokus: Bleibt in der Projektliste.
Ergebnis:

[ ] 9. Feld wechseln während der Umwandlung
Tasten: Strg+D, sprechen, Strg+D, gleich danach das Fenster mit Escape schließen.
Ansage: „Wird umgewandelt.“, dann „Text in der Zwischenablage.“
Fokus: Dort, wo Escape ihn hinbringt.
Ergebnis:

[ ] 10. Terminal
Tasten: Terminal öffnen, im Befehlsfeld Strg+D, „git status“ sagen, Strg+D.
Ansage: „Text eingefügt.“ Im Befehlsfeld steht der erkannte Text. Er läuft erst mit Enter.
Fokus: Im Befehlsfeld.
Ergebnis:


## Einstellungen

[ ] 11. Sprache und Dauer
Tasten: Feature-Verwaltung, Spracheingabe, Einstellungen. Sprache auf „Englisch“, Dauer auf 1 Minute. Dann diktieren und eine Minute warten.
Ansage: Nach einer Minute „Aufnahme nach 1 Minuten beendet. Wird umgewandelt.“ Englisch wird erkannt.
Fokus: Im Textfeld.
Ergebnis:

[ ] 12. Ausgeschaltet
Tasten: Spracheingabe in der Feature-Verwaltung ausschalten, dann in einem Textfeld Strg+D.
Ansage: „Spracheingabe ist ausgeschaltet.“
Fokus: Im Textfeld.
Ergebnis:

[ ] 13. Hilfe
Tasten: F1.
Ansage: In der Liste stehen „Diktieren starten und beenden, in einem Textfeld, Strg+D“ und „Diktieren abbrechen, Strg+Umschalt+D“.
Fokus: In der Liste der Tastenkürzel.
Ergebnis:

[ ] 14. Modell löschen
Tasten: KI-Verwaltung, Sprach-KI, auf dem heruntergeladenen Modell Alt+L.
Ansage: Rückfrage mit „Abbrechen“ als Vorgabe. Nach „Löschen“: „small gelöscht.“ Die Zeile nennt „nicht heruntergeladen“.
Fokus: In der Liste.
Ergebnis:
