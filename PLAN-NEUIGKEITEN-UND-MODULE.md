# Plan: Neuigkeiten, Aktivität und bessere Aufteilung des Codes

Stand: 22.10.2026. Wunsch des Nutzers in dieser Reihenfolge:

1. Die neuen Ideen in diesen Plan schreiben.
2. Den Code stärker in Module aufteilen, so wie es ein guter Programmierer macht.
3. Den Gesamttest machen.
4. Die neuen Ideen umsetzen.

## Teil A: Neuigkeiten beim Start

Wunsch: Nach dem Start sagt das Cockpit, was sich seit der letzten Benutzung geändert hat. Zum Beispiel: „Bei Projekt Tagebuch: ein neuer Pull Request, ein Kommentar, ein Issue.“

### Bedienung

- Ist das Cockpit bereit und der Stand von GitHub geholt, kommt eine kurze Ansage. Zum Beispiel: „Seit Ihrem letzten Besuch am 20.10.: 5 Neuigkeiten in 2 Projekten.“ Gibt es nichts Neues, kommt keine Ansage.
- Ein Fenster „Neuigkeiten“ öffnet sich nicht von selbst. Es verschiebt so nie den Fokus. Es öffnet sich über das Menü oder mit einer Taste.
- Neues Menü „&Neuigkeiten“ (Alt+N) mit „Neuigkeiten seit dem letzten Start …“ (Strg+Umschalt+N) und „Aktivität der Projekte …“ (Teil B).
- Im Fenster eine Liste. Jede Zeile beginnt mit dem Projekt, dann was passiert ist, dann wer und wann. Zum Beispiel: „Tagebuch: neuer Kommentar zu Issue 12, von anna, gestern 14:05“.
- Tab führt zu den Knöpfen: „Im Browser öffnen“, „Im Cockpit zeigen“ (springt zum Issue oder Pull Request) und „Schließen“.
- Eine Auswahl oben: „Seit dem letzten Start“, „Letzte 7 Tage“, „Letzte 30 Tage“. Das deckt auch den Wochenüberblick aus dem Konzept ab.

### Was zählt als Neuigkeit

- Neue Issues und Pull Requests, auch geschlossene und übernommene.
- Neue Kommentare zu Issues und Pull Requests, auch Reviews.
- Neue Sterne, neue Forks, neue Releases.
- Fehlgeschlagene GitHub Actions.
- Eigene Beiträge zählen nicht. Was Sie selbst geschrieben haben, wissen Sie schon.

### Technik

- Das Cockpit merkt sich den Zeitpunkt des letzten Starts in den Einstellungen („news.last_seen“). Er wird erst beim Beenden neu gesetzt. So gehen Neuigkeiten bei einem Absturz nicht verloren.
- GitHub kann Issues und Kommentare „seit“ einem Zeitpunkt liefern. Pro Projekt sind das wenige Anfragen im Hintergrund.
- Neue Schnittstelle in platforms/base.py: „SupportsActivity“. GitHub erfüllt sie. Andere Plattformen kommen später dazu, ohne Änderung am Kern.
- Eigenes Feature „Neuigkeiten“, abschaltbar. Die Logik liegt in cockpit/features/news und kennt kein Qt.
- Die Neuigkeiten kommen in die Datenbank. So sind sie auch ohne Internet da.

## Teil B: Aktivität der Projekte

Wunsch: Zahlen, die zeigen, wie beliebt ein Programm ist. Dazu die Kommentare und Issues.

### Was GitHub liefert

- Aufrufe der Seite und Besucher, Klone und klonende Personen. GitHub gibt diese Zahlen nur für die letzten 14 Tage und nur Besitzern mit Schreibrecht.
- Die meistbesuchten Seiten, höchstens zehn. Daraus lässt sich ablesen, wie oft die README angesehen wurde. Eine eigene Zählung für die README gibt es bei GitHub nicht.
- Downloads jeder Datei eines Releases, genau und für immer.
- Sterne, Forks, Beobachter, offene Issues und Pull Requests.
- Woher die Besucher kommen, zum Beispiel Google oder eine andere Seite.
- Kommentare direkt auf der Seite gibt es bei GitHub nicht. Kommentare stehen in Issues, Pull Requests und Diskussionen.

### Speichern

- Damit eine Statistik über 14 Tage hinaus entsteht, holt das Cockpit die Zahlen beim Start und dann einmal am Tag. Es speichert sie in der Datenbank, eine Zeile pro Projekt und Tag.
- Neue Tabellen: „activity_daily“ (Projekt, Tag, Aufrufe, Besucher, Klone, klonende Personen) und „activity_snapshot“ (Projekt, Tag, Sterne, Forks, Beobachter, Downloads).
- Die Zahlen sind keine Geheimnisse. Der Token bleibt im Tresor.

### Bedienung

- Fenster „Aktivität“. Oben die Auswahl des Zeitraums: „Letzte 7 Tage“, „Letzte 30 Tage“, „Seit Beginn der Aufzeichnung“.
- Liste der Projekte. Jede Zeile beginnt mit dem Projekt, dann die wichtigsten Zahlen. Zum Beispiel: „Tagebuch: 120 Aufrufe, 8 Klone, 35 Downloads, 4 Sterne, plus 1 seit letzter Woche“.
- Enter auf einem Projekt öffnet die Einzelheiten. Sie stehen als Text mit kurzen Zeilen: Zahlen pro Tag, Downloads pro Release, meistbesuchte Seiten, Herkunft der Besucher.
- Tab führt zu „Kommentare und Issues …“. Das zeigt die letzten Kommentare, Issues und Pull Requests des Projekts, neueste zuerst. Enter öffnet sie im Cockpit.
- Hat der Token kein Schreibrecht, steht in der Zeile „Aufrufe nur für Besitzer sichtbar“ statt einer Zahl.

### Technik

- Dieselbe Schnittstelle „SupportsActivity“ wie in Teil A, mit Traffic, Downloads und Kennzahlen.
- Eigenes Feature „Aktivität“, abschaltbar. Logik in cockpit/features/activity.
- Später kann der Wochenbericht per E-Mail (Phase 12) dieselben Zahlen nutzen.

## Teil C: Code stärker aufteilen

Ziel: Keine Datei hat mehr als etwa 500 Zeilen. Jede Datei hat eine klare Aufgabe. Ich finde schneller, was ich suche, und muss weniger lesen.

### Regeln

- Nur verschieben. Am Verhalten ändert sich nichts.
- Alte Namen bleiben über die bisherige Datei erreichbar, wo andere Dateien sie brauchen.
- Tests, die eine Funktion ersetzen, ersetzen sie dort, wo sie jetzt liegt.
- Nach jeder Datei laufen die Tests, die diese Datei betreffen.

### Reihenfolge

1. cockpit/core/exe.py, etwa 1500 Zeilen. Aufteilen in: Zustand und Einstellungen, Exe-Ordner und Dateien daneben, Python und Umgebung, spec-Datei, Bauen und Ersetzen, Austausch beim Neustart. exe.py behält build() und reicht die Namen weiter.
2. cockpit/ui/project_actions.py, etwa 1200 Zeilen. Die Klasse ProjectController wird aus Teilen zusammengesetzt: Projekte hinzufügen, Verbindung zu GitHub, Git-Aktionen, Verwalten. Jeder Teil in einer eigenen Datei.
3. cockpit/platforms/github.py, etwa 900 Zeilen. Teile: Repositories und Mitarbeiter, Pull Requests, Issues, Releases und Actions, Anmeldung im Browser.
4. cockpit/ui/main_window.py, etwa 870 Zeilen. Menüs, Abgleich des Stands und Tresor in eigene Dateien.
5. Die Fenster-Dateien mit 600 bis 700 Zeilen, wo es eine klare Grenze gibt: branch_dialogs, repo_dialogs, project_list, ai_dialogs, pull_request_dialogs, exe_flow, history_dialogs, exe_wizard, accounts_dialog, package_dialogs.
6. Eine Karte des Codes: Datei MODULE.md im Ordner cockpit. Eine Zeile pro Datei mit ihrer Aufgabe. So muss ich nicht suchen.
7. Eintrag in ENTSCHEIDUNGEN.md.

## Teil D: Gesamttest

- Alle Tests einmal ganz. Das Ergebnis melde ich ehrlich.
- Fehler behebe ich, bevor es mit Teil A weitergeht.

## Teil E: Umsetzen der neuen Ideen

1. Schnittstelle „SupportsActivity“ und die Umsetzung für GitHub, mit Tests gegen eine erfundene GitHub-Antwort.
2. Feature „Neuigkeiten“: Logik, Datenbank, Ansage beim Start, Fenster, Menü.
3. Feature „Aktivität“: tägliches Speichern, Fenster, Einzelheiten, Kommentare und Issues.
4. Tests, Kurzanleitungen, Einträge in ENTSCHEIDUNGEN.md.
5. Checkliste checklisten\neuigkeiten-und-aktivitaet.md.
6. Danach nur die neuen Tests. Den nächsten Gesamttest gibt es erst, wenn Sie es sagen.
