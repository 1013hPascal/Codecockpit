# Regeln für Claude Code im Projekt CodeCockpit

Diese Regeln gelten in jeder Sitzung.

## Grundlage

- Lies zu Beginn jeder Sitzung KONZEPT.md, ENTSCHEIDUNGEN.md und PLAN.md. Sie sind die Grundlage für alle Arbeiten.
- Wo ENTSCHEIDUNGEN.md vom Konzept abweicht, gilt ENTSCHEIDUNGEN.md. Wichtig: Es gibt keine Profile.
- Die Oberfläche spricht den Nutzer mit „Sie“ an.
- Getestet wird mit NVDA und Braillezeile.
- Die Referenz-Projekte Chatbot und Tagebuch liegen in `..\Referenz`. Sie gehören nicht ins Repository.
- ANALYSE.md beschreibt, welche Muster aus den Projekten Chatbot und Tagebuch übernommen werden.
- PLAN.md enthält die Häkchen-Liste der 17 Phasen. Hake eine Phase erst ab, wenn Tests und Testanleitung fertig sind und der Nutzer die Testanleitung durchgegangen ist.
- Entscheidungen, die vom Konzept abweichen oder es ergänzen, trägst du mit Grund in ENTSCHEIDUNGEN.md ein.
- Weicht etwas vom Konzept ab, fragst du vorher nach. Rückmeldungen des Nutzers haben Vorrang vor Annahmen.

## Sprache und Antwortstil

- Der Nutzer arbeitet mit Screenreader und Braillezeile.
- Antworte im Terminal auf Deutsch, kurz und in einfachen Sätzen.
- Im Terminal keine Tabellen, keine ASCII-Grafiken und keine langen Aufzählungen.
- Längere Inhalte schreibst du in Dateien und nennst im Terminal nur den Dateinamen und das Wichtigste.
- Auch in Dateien: klare Überschriften, kurze Sätze, das Wichtigste vorne. Tabellen und Grafiken nur, wenn es nicht anders geht.

## Barrierefreiheit hat Vorrang

- Barrierefreiheit geht vor Aussehen, Tempo und Bequemlichkeit beim Programmieren.
- Alles muss per Tastatur bedienbar sein.
- Jedes Steuerelement bekommt einen kurzen Accessible Name. Keine Accessible Description, weil sie die Braillezeile überlädt. Eingabefelder bekommen ein Label mit Buddy.
- Das Wichtigste steht vorne in jeder Zeile, jedem Listeneintrag und jeder Ansage.
- Ansagen über den Announcer, kurz, ohne Erklärungen zu Tasten. Tastenkürzel stehen im Menü und in der Hilfe (F1).
- Hintergrundarbeit verschiebt nie den Fokus und löst keine Flut von Ansagen aus.
- Rückfragen haben die sichere Antwort als Vorgabe. Escape wählt immer die sichere Antwort.
- Keine festen Farben. Keine Information nur über Farbe.
- Nutze die bewährten Bausteine aus ANALYSE.md: Announcer, AccessibleMenu, ContextMenu, name_widget, Textfeld mit echtem Zeilenumbruch, Task.

## Sicherheit

- Keine Geheimnisse in Dateien, Logs, Fehlermeldungen, Tests, Commits oder der Datenbank. Geheimnisse sind Tokens, API-Schlüssel und Passwörter.
- Geheimnisse liegen nur im Tresor und werden im Code mit der Klasse Geheimnis umhüllt.
- Tokens nie über die Befehlszeile an Git oder andere Programme übergeben.
- Tests benutzen nur erfundene Geheimnisse.
- Aktionen, die Dateien verändern oder löschen, beschreiben vorher, was passiert, brauchen eine Bestätigung und legen vorher eine Sicherheitskopie an.
- Nie einen force push ausführen.

## Jede Phase abschließen

Jede Phase endet mit:

1. Automatischen Tests mit pytest und pytest-qt. Alle Tests müssen bestehen. Das Ergebnis meldest du ehrlich.
2. Einer Testanleitung für Screenreader und Braillezeile in `testanleitungen\phase-NN.md`. Sie sagt für jeden Prüfpunkt: welche Tasten, was angesagt werden soll und wo der Fokus landen soll. Neben jedem Prüfpunkt ist Platz für das Ergebnis.
3. Einem Häkchen in PLAN.md erst nach der Rückmeldung des Nutzers.

Besonders gründlich testen: Tresor, Sicherheitsprüfung, Feature-Abhängigkeiten, Versionsberechnung, Rückgängig-Funktionen, Lizenzeinordnung, Projektbaum, Listen mit Kontrollkästchen und alle Dialoge.

## Technik

- Python 3.11 oder neuer, PySide6.
- Namen im Code sind englisch. Kommentare, Docstrings und Texte der Oberfläche sind deutsch.
- Git liegt in `C:\Program Files\Git\cmd\git.exe`. Ist `git` im Suchpfad noch unbekannt, diesen Pfad nutzen.
- Der Kern importiert nie PySide6.
- Features und Adapter sprechen nur mit Schnittstellen. Neue Features und Adapter kommen ohne Änderung am Kern dazu.
- Keine großen Umbauten und keine neuen Bibliotheken ohne Rückfrage.
