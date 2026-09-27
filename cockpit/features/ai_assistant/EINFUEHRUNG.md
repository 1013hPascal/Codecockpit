# KI-Assistent

Der KI-Assistent schlägt Texte vor: die Nachricht beim Hochladen von Änderungen, Titel und Beschreibung eines Pull Requests und die Kurzbeschreibung eines neuen Projekts.

Dafür brauchen Sie eine Text-KI. Die richten Sie im Menü KI unter KI-Verwaltung ein. Am einfachsten ist Ollama auf Ihrem Rechner, dann verlässt nichts den Rechner.

In diesen Fenstern gibt es den Knopf „Vorschlag der KI“, erreichbar mit Alt+V. Die KI füllt die Felder, NVDA sagt „Vorschlag eingefügt.“ und der Fokus geht in das erste Feld. Sie können alles ändern, bevor Sie hochladen.

Solange die KI schreibt, bleibt das Fenster bedienbar. Escape bricht den Vorschlag ab, ein zweites Escape schließt das Fenster.

Die KI bekommt nie den ganzen Code. Sie bekommt die Liste der geänderten Dateien und die geänderten Zeilen. Dateien mit Geheimnissen, zum Beispiel .env, gehen nie mit. Zeilen mit einem gefundenen Geheimnis werden vorher durch „[entfernt]“ ersetzt. Wie viele Zeichen die KI höchstens bekommt, steht in den Grundeinstellungen.

In der Feature-Verwaltung unter Einstellungen wählen Sie die Sprache der Vorschläge, Deutsch oder Englisch, und welche KI sie schreibt.
