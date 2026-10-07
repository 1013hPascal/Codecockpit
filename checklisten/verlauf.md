# Checkliste Verlauf

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\verlauf. Nehmen Sie ein Testprojekt mit mindestens einer Version (Feature Versionen) und einigen Commits.


## Versionsverlauf

[ ] 1. Versionen oben
Tasten: Main-Branch, Tab bis „Verlauf …“, Enter.
Ansage: Das Fenster „Verlauf von …: 2 Versionen, 12 Commits“. Fokus in „Versionen“. Oben „In Arbeit, noch keine Version, … Commits“, wenn seit der letzten Version etwas dazukam, dann „Version 1.1.0 vom …, … Commits“.
Ergebnis:

[ ] 2. Tab in die Commits
Tasten: Eine Version wählen, Tab.
Ansage: „Commits“, Einträge wie „05.10.2026, Pascal: Suche verbessert“. Noch nicht hochgeladene enden mit „noch nicht hochgeladen“.
Ergebnis:

[ ] 3. Enter in den Versionen
Tasten: In „Versionen“ Enter.
Ansage: Der Fokus springt in „Commits“.
Ergebnis:

[ ] 4. Details
Tasten: In „Commits“ Enter.
Ansage: Das Fenster mit „Angaben“ und „Dateien“, dazu „Datei wiederherstellen …“ und „Version rückgängig machen …“, wie bisher.
Ergebnis:

[ ] 5. Ohne Versionen
Tasten: Verlauf bei einem Projekt ohne Versionen öffnen.
Ansage: Statt „Versionen“ heißt die Liste „Tage“, zum Beispiel „23.09.2026, 3 Commits“.
Ergebnis:


## Zu einer Version zurück

[ ] 6. Nicht bei „In Arbeit“
Tasten: „In Arbeit“ markieren, Tab bis zu den Knöpfen.
Ansage: „Zu dieser Version zurück …“ ist nicht verfügbar.
Ergebnis:

[ ] 7. Zurück zu einer Version
Tasten: Eine ältere Version markieren, Tab bis „Zu dieser Version zurück …“, Enter.
Ansage: Die Rückfrage erklärt: alle Dateien auf den Stand der Version, neuer Commit, nichts geht verloren, Sicherheitskopie. Vorgabe und Escape: Abbrechen. Mit „Zurück zur Version“: „Zurück zu Version …. Neuer Commit, noch nicht hochgeladen.“ Oben steht „In Arbeit“ mit einem Commit mehr.
Prüfen: Die Dateien im Ordner haben den alten Stand. Mit „Version rückgängig machen …“ auf dem neuen Commit kommt der vorige Stand zurück.
Ergebnis:

[ ] 8. Mit offenen Änderungen
Tasten: Eine Datei ändern, ohne Commit. Dann Punkt 7 wiederholen.
Ansage: „Es gibt Änderungen ohne Commit. …“ Es wird nichts geändert.
Ergebnis:


## Hochladeverlauf

[ ] 9. Neuer Eintrag
Tasten: Auf dem Main-Branch Tab.
Ansage: Unter „Verlauf …“ steht „Hochladeverlauf …“. Auch bei Branch-Zeilen, wenn sie auf GitHub sind.
Ergebnis:

[ ] 10. Vor dem Aufzeichnen
Tasten: Enter auf „Hochladeverlauf …“, bevor Sie mit dieser Version etwas hochgeladen haben.
Ansage: Das Fenster „Hochladeverlauf von main: …“. Fokus in „Hochgeladen“, Einträge wie „23.09.2026, 3 Commits, vor dem Aufzeichnen“.
Ergebnis:

[ ] 11. Nach einem Hochladen
Tasten: Etwas ändern und hochladen. Dann wieder „Hochladeverlauf …“.
Ansage: Ganz oben zum Beispiel „07.10.2026 10:15, Pascal, 1 Commit nach main“. Tab führt in die Commits, Enter zeigt die Details.
Ergebnis:
