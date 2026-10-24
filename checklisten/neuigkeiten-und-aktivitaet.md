# Checkliste Neuigkeiten und Aktivität

Stand: 22.10.2026. Getestet wird mit NVDA und Braillezeile.

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung. Mit der Suche nach [ ] finden Sie die offenen Punkte.

Starten Sie das Cockpit mit `start_testdaten.bat` aus dem Ordner Repository\main. Die Testdaten enthalten erfundene Neuigkeiten und Zahlen für Tagebuch und PDF-Chat. Der „letzte Start“ war für die Testdaten vor zwei Tagen.

Die Punkte 12 bis 14 brauchen ein echtes GitHub-Konto. Starten Sie dafür das Cockpit normal.


## A. Ansage nach dem Start

[ ] 1. Ansage
Tasten: keine, nur starten.
Ansage: Nach „CodeCockpit mit Testdaten bereit. … Projekte.“ kommt „Seit Ihrem letzten Besuch am …: 4 Neuigkeiten in 2 Projekten.“ Das Datum ist vorgestern. Kein Fenster öffnet sich. Der Fokus bleibt in der Projektliste.
Ergebnis:

[ ] 2. Menü
Tasten: Alt+N.
Ansage: Menü „Neuigkeiten“ mit „Neuigkeiten seit dem letzten Start …, Strg+Umschalt+N“ und „Aktivität der Projekte …“.
Ergebnis:


## B. Fenster Neuigkeiten

[ ] 3. Öffnen
Tasten: Escape bis ins Hauptfenster, dann Strg+Umschalt+N.
Ansage: Fenster „Neuigkeiten: 4, Seit dem letzten Start“. Fokus in der Liste „Neuigkeiten“. Erste Zeile: „Tagebuch: neuer Kommentar zu Issue 12, von anna, heute …“.
Ergebnis:

[ ] 4. Zeilen
Tasten: Pfeil runter, mehrmals.
Ansage: „PDF-Chat: GitHub Actions fehlgeschlagen: Tests, von tester, heute …“, „Tagebuch: neues Issue 12: Suche in alten Einträgen, von anna, …“, „Tagebuch: neuer Stern, von carla, gestern …“. Jede Zeile beginnt mit dem Projekt.
Ergebnis:

[ ] 5. Zeitraum
Tasten: Umschalt+Tab bis „Zeitraum“, dann Pfeil runter auf „Letzte 30 Tage“.
Ansage: „Zeitraum, Letzte 30 Tage“. Danach Tab in die Liste: jetzt 6 Zeilen, auch der Pull Request 3 und ein älterer Kommentar zu PDF-Chat. Der Fenstertitel nennt „Neuigkeiten: 6, Letzte 30 Tage“.
Ergebnis:

[ ] 6. Knöpfe
Tasten: In der Liste auf den Kommentar zu Issue 12, dann Tab.
Ansage: „Im Browser öffnen“, dann „Im Cockpit zeigen“, dann „Schließen“. Auf dem Stern gibt es keine dieser beiden Knöpfe, nur „Schließen“.
Ergebnis:

[ ] 7. Im Cockpit zeigen
Tasten: Auf dem Kommentar zu Issue 12 Enter.
Ansage: Das Fenster schließt sich, Tagebuch ist in der Projektliste markiert. Weil die Testdaten kein GitHub-Konto haben, kommt eine Meldung, dass ein Konto fehlt. Mit einem echten Konto öffnet sich die Liste der Issues, das Issue ist markiert.
Ergebnis:

[ ] 8. Zeile kopieren
Tasten: In der Liste Strg+C.
Ansage: Die Zeile liegt in der Zwischenablage.
Ergebnis:


## C. Fenster Aktivität

[ ] 9. Öffnen
Tasten: Alt+N, dann „Aktivität der Projekte …“.
Ansage: Fenster „Aktivität: 2 Projekte, Letzte 7 Tage“. Fokus in „Projekte“. Zeilen wie „PDF-Chat: … Aufrufe, … Klone, 35 Downloads, 9 Sterne, plus 1 seit letzter Woche“ und „Tagebuch: …, 4 Sterne, plus 1 seit letzter Woche“.
Ergebnis:

[ ] 10. Einzelheiten
Tasten: Auf Tagebuch Enter.
Ansage: Fenster „Aktivität von Tagebuch“. Zeilen: „Tagebuch, Letzte 7 Tage“, „Aufrufe: …, Besucher: …“, „Klone: …“, „Sterne: 4, Forks: 1, Beobachter: 2, Downloads: 35“, dann „Pro Tag:“ mit einer Zeile pro Tag, „Downloads pro Release:“, „Meistbesuchte Seiten“ und „Herkunft der Besucher“. Escape schließt.
Ergebnis:

[ ] 11. Kommentare und Issues
Tasten: Auf Tagebuch Tab, dann Enter auf „Kommentare und Issues …“.
Ansage: Fenster „Kommentare und Issues von Tagebuch: 3, Letzte 30 Tage“. Nur Kommentar, Issue und Pull Request, kein Stern. Neueste oben.
Ergebnis:


## D. Mit echtem GitHub-Konto

[ ] 12. Erster Start
Tasten: Cockpit normal starten, Tresor entsperren, falls gefragt.
Ansage: Beim allerersten Start mit diesem Stand gibt es keine Ansage zu Neuigkeiten. Erst ab dem nächsten Start.
Ergebnis:

[ ] 13. Zweiter Start
Tasten: Cockpit beenden, neu starten, kurz warten.
Ansage: Gibt es seitdem etwas Neues von anderen, zum Beispiel einen Kommentar, kommt „Seit Ihrem letzten Besuch am …“. Gibt es nichts, bleibt es still. Eigene Kommentare zählen nicht.
Ergebnis:

[ ] 14. Aktivität eigener Repositories
Tasten: Alt+N, „Aktivität der Projekte …“.
Ansage: Bei eigenen Repositories stehen Aufrufe und Klone. Bei fremden Repositories ohne Schreibrecht steht „Aufrufe nur für Besitzer sichtbar“.
Ergebnis:


## E. Ausschalten

[ ] 15. Feature-Verwaltung
Tasten: Alt+F, Feature-Verwaltung, „Neuigkeiten“ und „Aktivität“ ausschalten, speichern.
Ansage: Das Menü Neuigkeiten ist weg, Alt+N öffnet es nicht mehr. Strg+Umschalt+N tut nichts, wie bei der Paketübersicht. Beim nächsten Start kommt keine Ansage zu Neuigkeiten.
Ergebnis:
