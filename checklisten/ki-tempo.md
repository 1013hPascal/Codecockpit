# Checkliste KI schneller und eingestellt

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\ki-tempo. Es braucht eine Text-KI mit Ollama und einem Modell (Menü KI, KI-Verwaltung). Am besten notieren Sie vorher, wie lange ein Vorschlag für die Commit-Nachricht heute dauert.


## Starttest

[ ] 1. Sofort benutzbar
Tasten: Cockpit starten und gleich in der Projektliste arbeiten.
Ansage: Wie immer. Der Test läuft im Hintergrund und sagt nichts an.
Ergebnis:

[ ] 2. Menü KI während des Tests
Tasten: In den ersten Sekunden Alt, dann zum Menü KI.
Ansage: Oben „KI wird auf den Rechner eingestellt …“.
Ergebnis:

[ ] 3. Menü KI nach dem Test
Tasten: Nach etwa einer Minute wieder ins Menü KI.
Ansage: Oben „KI ist eingestellt auf diesen Rechner …“. Ist Ollama nicht erreichbar: „KI nicht gemessen, Standardwerte einstellen …“.
Ergebnis:


## Fenster „KI einstellen“

[ ] 4. Erklärung
Tasten: Enter auf „KI ist eingestellt auf diesen Rechner …“.
Ansage: Das Fenster „KI einstellen“, Fokus im Feld „Erklärung“. Die erste Zeile nennt die KI, das Datum und wie viele Wörter sie pro Sekunde liest und schreibt. Danach je eine Zeile für Textfelder und für Code mit Stufe, Zeichen und Zielzeit. Der Text lässt sich lesen, aber nicht ändern.
Ergebnis:

[ ] 5. Art wählen
Tasten: Tab, dann Pfeil runter und hoch.
Ansage: „Ergebnisse nicht genau genug bei:“, „Vorschläge für Textfelder“ und „Antworten und Bearbeitung für Code oder komplexe Fragen“.
Ergebnis:

[ ] 6. Stufe wählen
Tasten: Tab, dann mit den Pfeiltasten eine Stufe wählen. Mit Umschalt+Tab zurück in die Erklärung.
Ansage: „Stufe“, die Einträge von „+3 sehr genau, langsamer“ bis „-3 ungenau, am schnellsten“. Markiert ist „0 Standard“. In der Erklärung ändern sich Zeichen und Zielzeit. Bei Code ab +2 steht dort „Die KI denkt dabei nach.“
Ergebnis:

[ ] 7. Speichern und Abbrechen
Tasten: Eine Stufe ändern, Escape. Fenster wieder öffnen. Dann ändern und „Speichern“.
Ansage: Nach Escape ist die alte Stufe noch da. Nach Speichern „Gespeichert.“, und beim nächsten Öffnen steht die neue Stufe.
Ergebnis:


## Tempo

[ ] 8. Vorschlag für die Commit-Nachricht
Tasten: Etwas ändern, „Änderungen auf GitHub hochladen …“, im Feld für die Nachricht „Vorschlag der KI“.
Ansage: Der Vorschlag kommt deutlich schneller als vorher. Bitte die Sekunden notieren.
Ergebnis:

[ ] 9. Zweite Frage gleich danach
Tasten: Gleich noch einmal einen Vorschlag holen.
Ansage: Noch schneller, weil das Modell geladen bleibt.
Ergebnis:

[ ] 10. Genauer stellen
Tasten: Im Fenster „KI einstellen“ für Textfelder +2 wählen und speichern. Wieder einen Vorschlag holen.
Ansage: Es dauert länger, der Vorschlag sollte genauer sein.
Ergebnis:

[ ] 11. Code bleibt gründlich
Tasten: „Exe aus main erstellen …“ mit KI oder die KI-Hilfe (Umschalt+F1) fragen.
Ansage: Gleich gute Antworten wie vorher.
Ergebnis:


## Töne

[ ] 12. Ton alle 3 Sekunden
Tasten: Etwas hochladen, das einige Sekunden dauert.
Ansage: Beim Start ein Ton, dann alle 3 Sekunden ein kurzer leiser Ton, am Ende der Ton für fertig.
Ergebnis:
