# Checkliste Optik

Stand: 22.10.2026. Getestet wird mit NVDA und Braillezeile.

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung. Mit der Suche nach [ ] finden Sie die offenen Punkte.

Alles Neue ist nur für das Auge. Teil A prüft deshalb vor allem, dass sich für NVDA und die Braillezeile nichts verändert hat. Teil B ist für eine sehende Person gedacht, falls jemand mitschauen kann.

Starten Sie das Cockpit mit `start_testdaten.bat` aus dem Ordner Repository\main.


## A. Mit NVDA und Braillezeile: nichts verändert

[ ] 1. Projektliste
Tasten: Pfeil runter durch die Projekte, Pfeil rechts auf Tagebuch, dann Pfeil runter.
Ansage: Wie bisher, zum Beispiel „Tagebuch, …, ausgeklappt“ und darunter „Repository, …“ und „Code, …“. Keine Pfeile oder Zeichen in der Ansage oder auf der Braillezeile.
Ergebnis:

[ ] 2. Tab-Kreis
Tasten: In der Projektliste Tab, dann noch einmal Tab.
Ansage: Erst die Aktionen, dann wieder die Projektliste. Der neue Bereich „Stand“ rechts unten wird übersprungen.
Ergebnis:

[ ] 3. Keine neuen Ansagen
Tasten: In der Projektliste mehrmals Pfeil runter und hoch, Strg+R für den Stand.
Ansage: Nur die Zeilen, wie bisher. Kein „Stand“ und keine Ansage, wenn sich der Bereich „Stand“ ändert.
Ergebnis:

[ ] 4. Lange Aktionen
Tasten: Tab in die Aktionen, mit Pfeil runter durch alle Aktionen.
Ansage: Jede Aktion wird ganz vorgelesen, auch lange wie „Repository auf GitHub anlegen und hochladen …, nicht verfügbar: …“. Für Sehende brechen sie jetzt um.
Ergebnis:

[ ] 5. Neuigkeiten
Tasten: Strg+Umschalt+N, Pfeil runter.
Ansage: Wie bisher, zum Beispiel „Tagebuch: neuer Kommentar zu Issue 12, von anna, heute …“.
Ergebnis:

[ ] 6. Einrichtung
Tasten: Menü Einstellungen, Einrichtungsassistent, dann Pfeil runter durch die Erklärung.
Ansage: Die Erklärung ist weiter eine Liste, eine Zeile pro Satz. NVDA sagt „Liste“ wie bisher.
Ergebnis:

[ ] 7. Feature-Verwaltung
Tasten: Menü Features, Feature-Verwaltung, Pfeil runter bis „KI, …“.
Ansage: Wie bisher, „KI, 5 von 5 KI-Features eingeschaltet“. Tab führt in die KI-Features.
Ergebnis:

[ ] 8. Menüs
Tasten: Alt+D für Datei, Alt+H für Hilfe, mit Pfeil runter durch die Einträge.
Ansage: Die Einträge wie bisher. Die neuen Symbole vor einigen Einträgen haben keine Ansage.
Ergebnis:


## B. Für eine sehende Person

[ ] 9. Gliederung
Tasten: Tagebuch ausklappen.
Ansage: Vor jedem Projekt steht ein Pfeil, bei Tagebuch zeigt er nach unten. Die Zeilen darunter sind eingerückt. Projektnamen sind fett, „ausgeklappt“ und Datumsangaben sind blasser.
Ergebnis:

[ ] 10. Stand
Tasten: Ein Projekt mit offenen Sachen markieren.
Ansage: Rechts unten steht der Name fett, darunter die Angaben der Zeile untereinander. Auf „Neue Projektsammlung“ ist der Bereich leer.
Ergebnis:

[ ] 11. Fokus
Tasten: Mit Tab zwischen Projektliste und Aktionen wechseln.
Ansage: Die Liste mit dem Fokus hat einen deutlichen Rahmen in der Akzentfarbe.
Ergebnis:

[ ] 12. Programmsymbol
Tasten: keine.
Ansage: In der Taskleiste und oben links im Fenster steht ein Symbol mit „CC“ in der Akzentfarbe von Windows.
Ergebnis:

[ ] 13. Dunkles Thema
Tasten: Windows auf dunklen Modus stellen (Einstellungen, Personalisierung, Farben), Cockpit neu starten.
Ansage: Alles ist dunkel und gut lesbar, auch die blassen Teile und der Bereich „Stand“.
Ergebnis:
