# Fragen zu 8d: Spracheingabe

Stand: 29.09.2026. Grundlage: Konzept 10.15 und ENTSCHEIDUNGEN.md, Abschnitt Spracheingabe.

So beantworten Sie die Fragen:

* Jede Frage beginnt mit \[ ].
* Passt mein Vorschlag, schreiben Sie ein x in die Klammer: \[x].
* Wollen Sie etwas anderes, schreiben Sie ein Ausrufezeichen hinein: \[!]. Schreiben Sie Ihre Antwort hinter „Antwort:“.
* Ist etwas unklar, schreiben Sie ein Fragezeichen hinein: \[?].

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.



## Kurz: was schon feststeht

* Wie im Tagebuch, nur ohne Knopf: Strg+D startet das Diktieren, noch einmal Strg+D beendet es. Strg+Umschalt+D bricht ab, ohne etwas einzufügen.
* Der Text kommt an der Schreibmarke in das Feld, in dem Sie gerade sind.
* Ansagen: „Aufnahme läuft.“, „Text eingefügt.“, „Aufnahme abgebrochen.“
* Wie im Tagebuch: faster-whisper auf dem Prozessor, Aufnahme mit sounddevice. Die Aufnahme bleibt nur im Arbeitsspeicher und wird nie gespeichert.



## Fragen

\[x] 1. Wo man diktieren kann
Frage: In welchen Feldern geht Strg+D?
Vorschlag: In jedem Textfeld des Cockpits, einzeilig und mehrzeilig, auch in der Eingabezeile des Terminals. Außerhalb eines Textfelds sagt Strg+D: „Diktieren geht nur in einem Textfeld.“
Antwort:

\[x] 2. Zwischenschritt beim Beenden
Frage: Das Umwandeln dauert je nach Länge einige Sekunden. Was hören Sie in der Zeit?
Vorschlag: Nach dem zweiten Strg+D die Ansage „Wird umgewandelt.“, dann „Text eingefügt.“ Wechseln Sie in der Zeit das Feld, kommt der Text trotzdem in das Feld, in dem Sie angefangen haben. Gibt es das Feld nicht mehr, kommt er in die Zwischenablage, mit der Ansage „Text in der Zwischenablage.“
Antwort:

\[x] 3. Längste Aufnahme
Frage: Wann endet eine Aufnahme von selbst?
Vorschlag: Nach 10 Minuten wie im Tagebuch, mit der Ansage „Aufnahme nach 10 Minuten beendet.“ Einstellbar in den Einstellungen des Features.
Antwort:

\[x] 4. Sprache
Frage: In welcher Sprache wird erkannt?
Vorschlag: Deutsch als Vorgabe. In den Einstellungen des Features wählbar: Deutsch, Englisch oder automatisch erkennen.
Antwort:

\[x] 5. Modell und Herunterladen
Frage: Wann kommt das Whisper-Modell auf den Rechner?
Vorschlag: In der KI-Verwaltung gibt es neben der Text-KI jetzt auch die Sprach-KI, „Whisper, lokal“. Das Cockpit empfiehlt das Modell nach Ihrem Arbeitsspeicher: ab 16 GB small (etwa 500 MB), ab 32 GB medium (etwa 1,5 GB), ab 64 GB large-v3-turbo (etwa 1,6 GB). Beim ersten Diktieren fragt es, ob das Modell jetzt heruntergeladen werden soll, und nennt die Größe. Der Fortschritt kommt als leise Meldung in der Statuszeile. Die Modelle liegen im Datenordner des Cockpits, nicht in der Exe.
Antwort:

\[x] 6. Größe der Exe
Frage: Die drei Bibliotheken faster-whisper, sounddevice und numpy machen die Exe größer, geschätzt von 60 MB auf etwa 150 MB. Ohne sie geht die Spracheingabe in der Exe nicht, weil die Exe kein eigenes Python mitbringt, um sie später nachzuinstallieren. Einverstanden?
Vorschlag: Ja, die Bibliotheken kommen in die Exe. Die Modelle bleiben außerhalb (Frage 5).
Antwort:

\[x] 7. Externe Sprach-KI
Frage: Soll es gleich auch eine Spracherkennung über einen Anbieter im Internet geben, zum Beispiel OpenAI?
Vorschlag: Noch nicht. Zuerst nur Whisper lokal. Die externe Sprach-KI kommt später. Dann fragt das Cockpit vorher, ob die Aufnahme an den Anbieter gehen darf.
Antwort:

\[x] 8. Einzeilige Felder
Frage: Was passiert mit Absätzen im diktierten Text, wenn das Feld nur eine Zeile hat, zum Beispiel der Titel eines Pull Requests?
Vorschlag: Zeilenumbrüche werden dort zu Leerzeichen. Steht vor der Schreibmarke schon Text ohne Leerzeichen am Ende, setzt das Cockpit eines davor.
Antwort:

\[x] 9. Grafikkarte
Frage: Soll Whisper eine Grafikkarte nutzen, wenn eine da ist?
Vorschlag: Vorerst nicht. Wie im Tagebuch rechnet es auf dem Prozessor. Das klappt auf jedem Rechner. Die Grafikkarte kommt später, wenn Sie das wollen.
Antwort:

\[x] 10. Updater danach
Frage: Sie wollen danach das Update testen. Soll 8d dafür als Version 1.2.0 kommen?
Vorschlag: Ja. Eine neue Funktion erhöht die mittlere Stelle.
Antwort:

