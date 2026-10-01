# Checkliste Projektübersichten und Aktionsmenüs

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\projektuebersichten. Nehmen Sie ein Projekt mit Ordnern für Branches, zum Beispiel CodeCockpit selbst.


## Projektliste

[ ] 1. Main-Branch und Branches verwalten
Tasten: Auf einem Projekt Pfeil rechts, dann Pfeil runter.
Ansage: Zuerst „Main-Branch, …“ mit dem Stand, zum Beispiel „alles hochgeladen“. Darunter „Branches verwalten“. Danach die Branch-Ordner, „Branches auf GitHub“ und „Exe, …“.
Ergebnis:

[ ] 2. Projekt ohne Branch-Ordner
Tasten: Ein Projekt ohne Branch-Ordner ausklappen.
Ansage: Zuerst „Code, …“, darunter „Branches verwalten“. Bei einem Projekt ohne Commit fehlt „Branches verwalten“.
Ergebnis:


## Branches verwalten

[ ] 3. Fenster öffnen
Tasten: Auf „Branches verwalten“ Enter.
Ansage: Fenster „Branches von …“. Der Fokus steht auf „Neuer Branch …“, dem ersten Eintrag der Liste.
Ergebnis:

[ ] 4. Neuer Branch
Tasten: Enter auf „Neuer Branch …“.
Ansage: Fenster „Neuer Branch“ mit dem Namensfeld. Mit Escape zurück.
Ergebnis:

[ ] 5. Main mit Stand der Exe
Tasten: Pfeil runter auf den Haupt-Branch, zum Beispiel „main, …“. Dann Tab.
Ansage: Die Zeile nennt wie bisher den Stand. Mit Tab kommt die Liste „Exe“ mit dem Stand der Exe, zum Beispiel „Exe, Version 1.1.7, …“, und darunter „Veröffentlicht als Version …“ oder „Noch nicht veröffentlicht.“ Knöpfe zum Übernehmen, Umbenennen oder Löschen gibt es bei main nicht.
Ergebnis:

[ ] 6. Ein Branch mit Aktionen
Tasten: Umschalt+Tab zurück in die Liste, Pfeil runter auf einen Branch mit Ordner, Tab durch die Knöpfe.
Ansage: „In main übernehmen …“, „Umbenennen …“, „Branch-Ordner entfernen …“, „Löschen …“, „Schließen“. Die Liste „Exe“ kommt hier nicht.
Ergebnis:

[ ] 7. Branch ohne Ordner
Tasten: Pfeil auf einen Branch ohne Ordner, Tab.
Ansage: „Ordner für … anlegen“ statt „Branch-Ordner entfernen …“.
Ergebnis:

[ ] 8. Branch-Ordner entfernen
Tasten: Nur zum Ausprobieren mit einem Test-Branch: „Branch-Ordner entfernen …“.
Ansage: Die gewohnte Rückfrage „Der Ordner Code\… wird gelöscht. Der Branch … bleibt.“ Mit „Behalten“ passiert nichts.
Ergebnis:


## Aktionen beim Main-Branch

[ ] 9. Reihenfolge
Tasten: Auf „Main-Branch“ Tab, dann mit Pfeil runter durch die Aktionen.
Ansage: „Projekt neu einlesen“, „Terminal …“, „Änderungen auf GitHub hochladen …“, „Änderungen von GitHub holen …“, „Pull Requests …“, „Verlauf …“, „Änderungen verwerfen …“, „Änderungen beiseitelegen …“, „Git-Identität …“, „Code-Ordner öffnen“. „Branches …“ und „Neuer Branch …“ stehen hier nicht mehr. Nur bei Bedarf kommen Einträge wie „Konflikte lösen …“ oder „Beiseitegelegte Änderungen …“ dazu.
Ergebnis:


## Aktionen bei einem Branch

[ ] 10. Reihenfolge
Tasten: Auf einem Branch-Ordner Tab, mit Pfeil runter.
Ansage: Wie beim Main-Branch, aber statt „Pull Requests …“ zuerst „Pull Request erstellen …“ und dann „Pull-Requests-Übersicht …“. „… verwalten …“ und „Branch-Ordner entfernen …“ stehen hier nicht mehr. Am Ende steht, wenn es passt, „Exe aus diesem Branch erstellen …“.
Ergebnis:


## Aktionen bei Exe

[ ] 11. Reihenfolge
Tasten: Auf „Exe, …“ Tab, mit Pfeil runter.
Ansage: „Projekt neu einlesen“, „Exe starten“, „Exe aus dem Code erstellen …“, „Exe veröffentlichen …“, „Exe einlesen …“, „Exe-Einstellungen …“, „Links der Exe …“, „Exe-Ordner öffnen“, „Wie funktioniert die Exe? …“. „Exe starten“ bleibt, weil Enter auf der Zeile Exe die Exe startet.
Ergebnis:

[ ] 12. Exe aus dem Code erstellen
Tasten: Enter auf „Exe aus dem Code erstellen …“.
Ansage: Auswahl „Einrichtung“. Mit eingerichteter Text-KI steht „Exe mit KI einrichten …“ oben und hat den Fokus, sonst „Exe ohne KI einrichten …“.
Ergebnis:

[ ] 13. Ohne KI einrichten
Tasten: „Exe ohne KI einrichten …“ wählen.
Ansage: Nach kurzer Prüfung das Fenster „Exe aus dem Code erstellen: …“ mit der Liste „Ergebnis der Einrichtung“. Mit Tab „Exe erstellen“ und „Abbrechen“.
Ergebnis:

[ ] 14. Exe erstellen
Tasten: Enter auf „Exe erstellen“.
Ansage: Die gewohnte Rückfrage und danach der Bau in vier Schritten, wie bisher.
Ergebnis:

[ ] 15. Mit KI einrichten
Tasten: Noch einmal, diesmal „Exe mit KI einrichten …“.
Ansage: Der gewohnte Ablauf mit Wunsch und Vorschlag. Am Ende statt der Frage „Soll die Exe jetzt gebaut werden?“ das Fenster mit dem Ergebnis und „Exe erstellen“.
Ergebnis:

[ ] 15a. Fortschritt, während die KI arbeitet
Tasten: Nach dem Wunsch „Weiter“. Dann mit Pfeil runter lesen.
Ansage: „Die KI liest den Code.“ Das Fenster „Exe mit KI einrichten: …, läuft“ bleibt offen. Die Liste „Fortschritt“ hat oben „Die KI liest den Code. Läuft seit … Sekunden.“ Die Zeit wird alle 5 Sekunden erneuert. Darunter „Datei 1 von … gelesen: …“ für jede Datei und „An die KI gesendet: …“. Dabei sagt NVDA einmal „Der Code ist gelesen. Die KI arbeitet.“ Ist die KI fertig, schließt sich das Fenster, und der Vorschlag öffnet sich.
Ergebnis:

[ ] 15b. Abbrechen
Tasten: Noch einmal starten, während die KI arbeitet Tab auf „Abbrechen“, Enter. Escape geht auch.
Ansage: „Abgebrochen. Nichts geändert.“ Das Fenster schließt sofort. Ein neuer Start geht gleich wieder, ohne „Das läuft schon.“
Ergebnis:

[ ] 16. Exe einlesen
Tasten: Enter auf „Exe einlesen …“.
Ansage: Auswahl „Woher kommt die Exe?“ mit „Exe-Datei wählen …“ und „Exe aus einem Release wählen …“. Danach geht es weiter wie bisher bei den beiden alten Einträgen.
Ergebnis:

[ ] 17. Links der Exe
Tasten: Enter auf „Links der Exe …“.
Ansage: Fenster „Links von …, Exe“ mit „Release v…“, „Download der Exe v…“ und „Download der neuesten Exe“. Enter kopiert den markierten Link: „Link zu … kopiert.“ Ohne Release kommt eine Meldung.
Ergebnis:


## Aktionen beim Projekt

[ ] 18. Reihenfolge
Tasten: Auf der Projektzeile Tab, mit Pfeil runter.
Ansage: „Projekt neu einlesen“, „Terminal …“, „Projekt verwalten …“, „Links …“, „README …“, „Releases …“, „GitHub Actions …“, „Features dieses Projekts …“, „Aus der Liste entfernen …“, „Projektordner öffnen“. README, Releases und GitHub Actions nur, wenn das Feature an ist.
Ergebnis:

[ ] 19. Projekt verwalten
Tasten: Enter auf „Projekt verwalten …“.
Ansage: Fenster „Projekt verwalten: …“ mit den bisherigen Einstellungen des Repositories.
Ergebnis:

[ ] 20. Links mit Release
Tasten: Enter auf „Links …“ bei einem Projekt mit Release.
Ansage: Nach „Projektseite“ und „README“ auch „Neuestes Release v…“.
Ergebnis:

[ ] 21. README
Tasten: Enter auf „README …“.
Ansage: Auswahl mit „README erstellen …“ (ohne README) oder „README bearbeiten …“, dazu „README-Einstellungen …“. „README-Einstellungen …“ öffnet das Fenster für die Sprachen.
Ergebnis:
