# Checkliste neue Projektliste

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\projektliste-neu. Nehmen Sie für Umbenennen und Löschen ein Testprojekt, nicht das Cockpit selbst.


## Projektzeile

[ ] 1. Aktionen des Projekts
Tasten: Auf einer Projektzeile Tab.
Ansage: „Projekt neu einlesen“, „Terminal …“, „Projekt verwalten …“, „Features dieses Projekts …“ und ganz unten „Projektordner öffnen“. README, Lizenz, Links und Releases stehen hier nicht mehr.
Fokus: In der Aktionsliste.
Ergebnis:

[ ] 2. Terminal im Projektordner
Tasten: Enter auf „Terminal …“, dann „cd“ eingeben und Enter.
Ansage: Der oberste Ordner des Projekts, zum Beispiel …\Github\Tagebuch.
Ergebnis:

[ ] 3. Projekt verwalten
Tasten: Enter auf „Projekt verwalten …“, dann Tab durch das Fenster.
Ansage: „Derzeitiger Name“ mit dem Namen, nur lesbar. Dann „Projekt umbenennen …“, „Aus der Liste entfernen …“, „Projekt löschen …, lokaler Ordner auf dem Rechner, Repository und Release werden gelöscht“ und „Schließen“. Ohne GitHub fehlt „Repository und Release“.
Fokus: Zuerst im Feld „Derzeitiger Name“.
Ergebnis:

[ ] 4. Projekt umbenennen
Tasten: „Projekt umbenennen …“, einen neuen Namen eingeben, Enter. Die Rückfrage mit „Umbenennen“ bestätigen.
Ansage: Zuerst die Rückfrage, was umbenannt wird: Name, Ordner und Repository auf GitHub. Danach die Schritte und am Ende „Projekt heißt jetzt …“. Branch-Ordner und virtuelle Umgebung funktionieren danach weiter.
Fokus: Auf der umbenannten Projektzeile.
Ergebnis:

[ ] 5. Umbenennen mit ungültigem Namen
Tasten: Einen Namen mit Doppelpunkt eingeben, danach den Namen eines vorhandenen Ordners.
Ansage: „Zeichen“ bzw. „gibt es schon“. Es wird nichts geändert.
Ergebnis:

[ ] 6. Ordner in Benutzung
Tasten: Einen Explorer oder ein Terminal im Projektordner offen lassen und umbenennen.
Ansage: Eine Meldung, dass der Ordner in Benutzung ist und nichts geändert wurde.
Ergebnis:

[ ] 7. Projekt löschen
Tasten: „Projekt löschen …“, beide Rückfragen bestätigen und den Namen eintippen.
Ansage: Vorher wird gesagt, was gelöscht wird. Escape bricht bei jeder Rückfrage ab. Am Ende verschwindet das Projekt aus der Liste. Der lokale Ordner liegt in den Sicherheitskopien.
Ergebnis:


## Zeile Repository

[ ] 8. Zeile Repository
Tasten: Ein Projekt mit Pfeil rechts aufklappen, Pfeil runter.
Ansage: „Repository, Branches: main & die Sie lokal haben“.
Ergebnis:

[ ] 9. Branches anzeigen
Tasten: Enter auf der Zeile Repository, mit Pfeil runter „Nur main“ wählen, Enter.
Ansage: Ein Menü mit „Nur main“, „main & die Sie lokal haben“, „main & die nur auf GitHub sind“ und „main & alle“, die aktuelle Auswahl ist angehakt. Danach stehen unter dem Repository nur noch Main-Branch und Releases. Nach einem Neustart bleibt die Auswahl.
Fokus: Wieder auf der Zeile Repository.
Ergebnis:

[ ] 10. Escape im Menü
Tasten: Enter auf der Zeile Repository, dann Escape.
Ansage: Nichts ändert sich.
Ergebnis:

[ ] 11. Aktionen des Repositorys
Tasten: Auf der Zeile Repository Tab.
Ansage: Unter anderem „Repository neu einlesen“, „Terminal …“, „Repository verwalten …“, „Branches verwalten …“, „Links …“, „README …“, „Lizenz …“, „Repository-Identität …“, „Auf GitHub öffnen“ und „Repository-Ordner öffnen“.
Ergebnis:

[ ] 12. Terminal im Repository
Tasten: Enter auf „Terminal …“, dann „cd“ eingeben.
Ansage: Der Ordner Code des Projekts, nicht main. Von dort wechseln Sie selbst in main oder einen Branch.
Ergebnis:


## Branches verwalten und Haupt-Branch

[ ] 13. Infos zu main
Tasten: „Branches verwalten …“, main markieren, Tab bis „Infos“.
Ansage: Name und Ort, „Angelegt von … am …“, „Zuletzt geändert von …“, die Zahl der Commits und der Stand zu GitHub.
Ergebnis:

[ ] 14. main löschen
Tasten: Weiter Tab bis „Löschen …, nicht verfügbar“, Enter.
Ansage: „… ist der Haupt-Branch und kann nicht gelöscht werden. Alle anderen Branches bauen auf ihm auf.“
Ergebnis:

[ ] 15. main umbenennen
Tasten: „Umbenennen …“ bei main, zum Beispiel in haupt, bestätigen. Am besten in einem Testprojekt.
Ansage: Die Rückfrage nennt, was passiert: Branch hier und auf GitHub, Ordner Code\main. Danach „… heißt jetzt haupt“. Die Zeile heißt „Main-Branch haupt“.
Ergebnis:


## Branch-Zeilen

[ ] 16. Aktionen eines Branches
Tasten: Auf einer Branch-Zeile Tab.
Ansage: Oben „Repository neu einlesen“, ganz unten „Branch-Ordner öffnen“.
Ergebnis:

[ ] 17. Terminal im Branch
Tasten: Enter auf „Terminal …“, „cd“ eingeben.
Ansage: Der Ordner dieses Branches, zum Beispiel Code\neue-funktion.
Ergebnis:


## Releases

[ ] 18. Zeile Releases
Tasten: Unter dem letzten Branch Pfeil runter.
Ansage: „Releases, 1 Release“ oder mehr. Darunter „Exe-main, …“ und je Branch-Release eine Zeile wie „Exe-neue-funktion, noch keine Exe-Datei“.
Ergebnis:

[ ] 19. Aktionen von Releases
Tasten: Auf „Releases, …“ Tab.
Ansage: „Releases neu einlesen“, „Terminal …“, „Release für Branch aus Repository erstellen …“, „Release veröffentlichen …“ (nur mit GitHub), „Release entfernen …“, „Releases auf GitHub …“ und ganz unten „Release-Ordner öffnen“.
Ergebnis:

[ ] 20. Release für Branch erstellen
Tasten: Enter auf „Release für Branch aus Repository erstellen …“. Einen Branch wählen, Tab, Enter auf „Release-Ordner lokal anlegen“.
Ansage: Oben „Releases können nur für Branches erstellt werden, die lokal auf dem Rechner sind.“ Darunter die Liste „Lokale Branches“. Danach „Release Exe-… angelegt.“
Fokus: Auf der neuen Zeile „Exe-…, noch keine Exe-Datei“.
Ergebnis:

[ ] 21. Kein Branch frei
Tasten: Noch einmal „Release für Branch …“, wenn alle lokalen Branches schon ein Release haben.
Ansage: Eine Meldung mit demselben Hinweis, ohne Liste.
Ergebnis:

[ ] 22. Release-Zeile eines Branches
Tasten: Auf „Exe-neue-funktion“ Tab.
Ansage: „Releases neu einlesen“, „Terminal …“, „Exe starten“ (ohne Exe nicht verfügbar mit Grund), „Exe aus neue-funktion erstellen …“, „Release entfernen …“ und ganz unten „Exe-neue-funktion-Ordner öffnen“.
Ergebnis:

[ ] 23. Exe aus dem Branch erstellen
Tasten: Enter auf „Exe aus neue-funktion erstellen …“, bestätigen.
Ansage: Wie bisher beim Bau aus einem Branch. Danach heißt die Zeile „Exe-neue-funktion, vom …“.
Ergebnis:

[ ] 24. Zeile Exe-main
Tasten: Auf „Exe-main, …“ Tab.
Ansage: „Releases neu einlesen“, „Terminal …“, „Exe starten“, „Exe aus main erstellen …“, die übrigen Exe-Aktionen wie bisher, „Release einlesen …“ statt „Exe einlesen …“ und ganz unten „Exe-main-Ordner öffnen“. Das Terminal öffnet im Ordner der Exe.
Ergebnis:

[ ] 25. Release veröffentlichen
Tasten: Auf Releases „Release veröffentlichen …“.
Ansage: Liste „Releases“, oben Exe-main, jede Zeile mit „zuletzt Version … am …“ oder „noch nicht veröffentlicht“. Tab führt zu „Veröffentlichen“. Bei Exe-main geht es weiter wie bisher. Bei einem Branch heißt das Tag zum Beispiel v1.0.0-neue-funktion. Ist der Branch noch nicht auf GitHub, sagt das Cockpit das.
Ergebnis:

[ ] 26. Release entfernen
Tasten: Auf einer Release-Zeile „Release entfernen …“.
Ansage: Die Rückfrage nennt, was passiert: lokal in die Sicherheitskopien, auf GitHub das Release der letzten Version, das Tag bleibt. Knöpfe „Nur lokal auf dem Rechner“, „Nur auf GitHub“, „Beides“ und „Abbrechen“, je nachdem, was es gibt. Vorgabe und Escape: Abbrechen.
Ergebnis:


## Nachtrag

[ ] 27. Neu einlesen nach Abbrechen
Tasten: Bei einem Projekt, dessen Code noch direkt im Ordner Code liegt, „Repository neu einlesen“. Die Frage „Ordner für Branches einrichten“ mit Abbrechen beantworten.
Ansage: „… neu eingelesen.“ Vorher kam danach gar nichts.
Ergebnis:
