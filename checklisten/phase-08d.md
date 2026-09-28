# Checkliste 8d: Spracheingabe

Tragen Sie bei jedem Punkt \[x] für OK oder \[!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Zum Testen starten Sie das Cockpit aus dem Branch-Ordner Spracheingabe oder mit einer Exe aus diesem Branch. Ein Mikrofon muss angeschlossen sein.



## Einrichten

\[!] 1. Feature in der Feature-Verwaltung
Tasten: Alt+F, Feature-Verwaltung, auf „KI“, Tab in die Liste der KI-Features.
Ansage: Unter den KI-Features steht „Spracheingabe“, eingeschaltet.
Fokus: In der Liste der KI-Features.
Ergebnis: irgendwie komisch, man muss bei text ki ganz oft tab drücken, bis man zu spracheingabe kommt. eigentlich sollte man das ja mit pfei runter auswählen können.
Antwort von Claude: Geändert. Von „KI“ führt jetzt ein einziges Tab in die Liste „KI-Features“, dort geht es mit Pfeil runter weiter. Vorher lag die Liste in der Tab-Reihenfolge hinter anderen Teilen des Fensters. Bitte noch einmal prüfen.



\[!] 2. Sprach-KI in der KI-Verwaltung
Tasten: Alt+K, KI-Verwaltung, dann Alt+K für „Sprach-KI …“.
Ansage: Fenster „Sprach-KI“, Liste „Whisper-Modelle auf diesem Rechner“, zum Beispiel „medium, gewählt, ab 32 GB Arbeitsspeicher, etwa 1,5 GB, empfohlen für Ihren Rechner, nicht heruntergeladen“.
Fokus: In der Liste.
Ergebnis: ich müsste doch schon eines heruntergeladne haben und trotdem sagt er bei allen drei, das ich das nicht habe, aber vom Tagebuch her müsste es doch auf dem rechner sein.
Antwort von Claude: Stimmt. Das Tagebuch hat small und medium im Zwischenspeicher von Hugging Face (Ordner .cache\huggingface in Ihrem Benutzerordner). Das Cockpit kannte nur seinen eigenen Ordner. Jetzt findet es auch diese Modelle und nutzt sie, ohne neu herunterzuladen. Die Zeile nennt dann „heruntergeladen, aus dem Zwischenspeicher von Hugging Face“. Löschen geht dort nicht, weil das Tagebuch sie auch braucht.



\[!] 3. Modell wählen
Tasten: Pfeil auf „small“, Enter.
Ansage: „small gewählt.“ Die Zeile nennt jetzt „small, gewählt, …“.
Fokus: Bleibt in der Liste.
Ergebnis: Also das geht schon, aber warum hier keine checkmarkliste machen? und dann mit tab auf herunterladen. hier bei herunterladen und schließen geht gerade nur mit Leertaste, nicht mit enter, bitte ändern.
Antwort von Claude: Geändert. Die Liste hat jetzt Kontrollkästchen. Das angehakte Modell ist das gewählte, Leertaste oder Enter haken an. Es ist immer genau eines angehakt. Mit Tab kommen Herunterladen, Löschen und Schließen, und die gehen jetzt auch mit Enter. Bitte noch einmal prüfen.



## Diktieren

\[x] 4. Erstes Diktieren lädt das Modell
Tasten: Eine Commit-Nachricht öffnen, zum Beispiel über „Änderungen hochladen …“, im Textfeld Strg+D.
Ansage: Rückfrage „Für die Spracheingabe braucht das Cockpit das Whisper-Modell …, etwa … MB …“. Vorgabe ist „Abbrechen“. Nach „Herunterladen“: „Whisper-Modell wird heruntergeladen.“, leise Fortschritt in der Statuszeile, am Ende „Whisper-Modell heruntergeladen.“
Fokus: Bleibt im Textfeld.
Ergebnis:

\[x] 5. Aufnahme und Einfügen
Tasten: Im Textfeld Strg+D, einen Satz sprechen, noch einmal Strg+D.
Ansage: „Aufnahme läuft.“, dann „Wird umgewandelt.“, dann „Text eingefügt.“
Fokus: Im Textfeld, der Text steht an der Schreibmarke.
Ergebnis:

\[x] 6. Abbrechen
Tasten: Strg+D, etwas sagen, dann Strg+Umschalt+D.
Ansage: „Aufnahme abgebrochen.“ Es wird nichts eingefügt.
Fokus: Im Textfeld.
Ergebnis:

\[x] 7. Einzeiliges Feld
Tasten: Im Feld für den Titel eines Pull Requests Strg+D, zwei Sätze mit Pause sprechen, Strg+D.
Ansage: „Text eingefügt.“ Der Text steht in einer Zeile. Stand vorher schon Text, ist ein Leerzeichen dazwischen.
Fokus: Im Feld.
Ergebnis:

\[x] 8. Außerhalb eines Textfelds
Tasten: In der Projektliste Strg+D.
Ansage: „Diktieren geht nur in einem Textfeld.“
Fokus: Bleibt in der Projektliste.
Ergebnis:

\[x] 9. Feld wechseln während der Umwandlung
Tasten: Strg+D, sprechen, Strg+D, gleich danach das Fenster mit Escape schließen.
Ansage: „Wird umgewandelt.“, dann „Text in der Zwischenablage.“
Fokus: Dort, wo Escape ihn hinbringt.
Ergebnis:

\[x] 10. Terminal
Tasten: Terminal öffnen, im Befehlsfeld Strg+D, „git status“ sagen, Strg+D.
Ansage: „Text eingefügt.“ Im Befehlsfeld steht der erkannte Text. Er läuft erst mit Enter.
Fokus: Im Befehlsfeld.
Ergebnis:



## Einstellungen

\[x] 11. Sprache und Dauer
Tasten: Feature-Verwaltung, Spracheingabe, Einstellungen. Sprache auf „Englisch“, Dauer auf 1 Minute. Dann diktieren und eine Minute warten.
Ansage: Nach einer Minute „Aufnahme nach 1 Minuten beendet. Wird umgewandelt.“ Englisch wird erkannt.
Fokus: Im Textfeld.
Ergebnis:

\[x] 12. Ausgeschaltet
Tasten: Spracheingabe in der Feature-Verwaltung ausschalten, dann in einem Textfeld Strg+D.
Ansage: „Spracheingabe ist ausgeschaltet.“
Fokus: Im Textfeld.
Ergebnis:

\[x] 13. Hilfe
Tasten: F1.
Ansage: In der Liste stehen „Diktieren starten und beenden, in einem Textfeld, Strg+D“ und „Diktieren abbrechen, Strg+Umschalt+D“.
Fokus: In der Liste der Tastenkürzel.
Ergebnis:

\[ ] 14. Modell löschen
Tasten: KI-Verwaltung, Sprach-KI, auf dem heruntergeladenen Modell Alt+L.
Ansage: Rückfrage mit „Abbrechen“ als Vorgabe. Nach „Löschen“: „small gelöscht.“ Die Zeile nennt „nicht heruntergeladen“.
Fokus: In der Liste.
Ergebnis:

