# Kurzanleitungen

Schritt für Schritt, mit den Tasten. Jede Anleitung nennt ihren Bereich (start, projekt, repository, branch, releases) und die Aktionen, die sie benutzt. Ein Test prüft, dass es diese Aktionen gibt.

## Projektordner hinzufügen
Bereich: start
Aktionen: add_local
Stichwörter: Ordner, hinzufügen, neues Projekt, aufnehmen
Schritt 1: Drücken Sie Strg+1 und Pos1. Sie sind ganz oben in der Projektliste.
Schritt 2: Drücken Sie einmal Pfeil runter auf „Projekt vom Rechner hinzufügen“ und dann Enter.
Schritt 3: Wählen Sie im Fenster von Windows den Projektordner. Darin liegen Repository und Release oder einfach Ihr Code. Bestätigen Sie mit „Ordner auswählen“.
Schritt 4: Passt der Aufbau nicht, fragt das Cockpit, ob es den Ordner umstellt. Lesen Sie die Rückfrage und wählen Sie mit Tab „Verschieben“ oder „Abbrechen“.
Schritt 5: Das Projekt steht danach in der Liste und ist markiert.

## Verschobenen Ordner wieder in die Liste bringen
Bereich: start
Aktionen: relocate
Stichwörter: verschoben, Ordner nicht gefunden, neuer Ort, umgezogen
Schritt 1: Gehen Sie in der Projektliste auf das Projekt. Die Zeile sagt „Ordner nicht gefunden“.
Schritt 2: Drücken Sie Tab. Sie sind in den Aktionen.
Schritt 3: Wählen Sie mit Pfeil runter „Neuen Ort angeben …“ und drücken Sie Enter.
Schritt 4: Wählen Sie den neuen Ort des Projektordners und bestätigen Sie. Das Projekt behält seine Einstellungen.

## Projektsammlung erstellen
Bereich: start
Aktionen: new_collection, collection_members
Stichwörter: Sammlung, Gruppe, ordnen, Ordner für Projekte
Schritt 1: Drücken Sie Strg+1 und Pos1 auf „Neue Projektsammlung“ und dann Enter.
Schritt 2: Geben Sie einen Namen ein, zum Beispiel Webseiten, und drücken Sie Enter.
Schritt 3: Die neue Sammlung ist markiert. Drücken Sie Tab, dann Enter auf „Projekte für die Sammlung …“.
Schritt 4: Haken Sie die Projekte mit der Leertaste an und bestätigen Sie mit „OK“.
Schritt 5: Pfeil rechts auf der Sammlung öffnet sie, Pfeil links schließt sie wieder.

## Projekt von GitHub herunterladen
Bereich: start
Aktionen: add_remote, download
Stichwörter: klonen, herunterladen, clone, GitHub, holen
Schritt 1: Drücken Sie Strg+1 und Pos1, dann zweimal Pfeil runter auf „Projekt von GitHub herunterladen“ und Enter.
Schritt 2: Wählen Sie das Repository mit den Pfeiltasten und drücken Sie Enter.
Schritt 3: Repositories, die nur auf GitHub liegen, stehen auch direkt in der Liste mit „nur auf GitHub“. Dort lädt Enter sie herunter.

## Projekte filtern
Bereich: start
Aktionen: list_filter
Stichwörter: Filter, anzeigen, offen, nur lokal, Release, ausblenden
Schritt 1: Drücken Sie Strg+1 und Pos1, dann dreimal Pfeil runter auf „Anzeigen: Alle Projekte“.
Schritt 2: Drücken Sie Enter. Ein Menü öffnet sich.
Schritt 3: Wählen Sie mit den Pfeiltasten, zum Beispiel „Mit offenen Sachen“, und drücken Sie Enter.
Schritt 4: Die Liste zeigt nur noch die passenden Projekte. Zurück geht es mit „Alle Projekte“.

## Befehl schnell finden
Bereich: alle
Aktionen:
Stichwörter: suchen, Befehl, Strg+K, finden, wo ist
Schritt 1: Markieren Sie die Zeile, um die es geht, zum Beispiel ein Projekt.
Schritt 2: Drücken Sie Strg+K.
Schritt 3: Tippen Sie einen Teil des Namens, zum Beispiel „hoch“.
Schritt 4: Wählen Sie mit Pfeil runter und hoch und drücken Sie Enter.

## Änderungen hochladen und Commit erstellen
Bereich: branch
Aktionen: push_changes
Stichwörter: hochladen, Commit, speichern, push, committen, Nachricht
Schritt 1: Klappen Sie das Projekt mit Pfeil rechts auf und gehen Sie auf den Main-Branch oder auf die Zeile Ihres Branches.
Schritt 2: Drücken Sie Tab. Oben steht „Änderungen auf GitHub hochladen …“. Drücken Sie Enter.
Schritt 3: Schreiben Sie, was Sie geändert haben, oder holen Sie mit „Vorschlag der KI“ einen Vorschlag. Das ist die Commit-Nachricht.
Schritt 4: Bestätigen Sie. Das Cockpit macht den Commit und lädt hoch. Sie hören Töne, solange es läuft.
Schritt 5: Auf einem Branch bietet das Cockpit danach an, einen Pull Request zu stellen.

## Änderungen von GitHub holen
Bereich: branch
Aktionen: pull_changes
Stichwörter: herunterladen, holen, pull, aktualisieren, neuer Stand
Schritt 1: Gehen Sie auf den Main-Branch oder die Zeile des Branches.
Schritt 2: Drücken Sie Tab und wählen Sie „Änderungen von GitHub holen …“, dann Enter.
Schritt 3: Das Cockpit sagt, was neu ist, und fragt, ob es zusammenführen soll. Bestätigen Sie.

## Branch erstellen
Bereich: repository
Aktionen: branches
Stichwörter: Branch, neuer Branch, abzweigen, Zweig
Schritt 1: Klappen Sie das Projekt mit Pfeil rechts auf. Pfeil runter führt auf die Zeile Repository.
Schritt 2: Drücken Sie Tab und wählen Sie „Branches verwalten …“, dann Enter.
Schritt 3: Drücken Sie Tab bis „Neuer Branch …“ und Enter.
Schritt 4: Geben Sie den Namen ein, zum Beispiel neue-funktion, und drücken Sie Enter. Der Branch bekommt einen eigenen Ordner und steht in der Liste.

## Branch in main übernehmen
Bereich: repository
Aktionen: branches
Stichwörter: übernehmen, merge, zusammenführen, in main, fertig
Schritt 1: Gehen Sie auf die Zeile Repository und öffnen Sie mit Tab „Branches verwalten …“.
Schritt 2: Wählen Sie den Branch mit den Pfeiltasten.
Schritt 3: Drücken Sie Tab bis „In main übernehmen …“ und Enter. Lesen Sie die Rückfrage und bestätigen Sie mit „Übernehmen“.
Schritt 4: Danach ist main noch nicht hochgeladen. Laden Sie main wie gewohnt hoch. Dabei fragt das Cockpit nach einer neuen Version.

## Pull Request stellen
Bereich: branch
Aktionen: create_pull
Stichwörter: Pull Request, PR, prüfen lassen, Review anfragen
Schritt 1: Laden Sie zuerst Ihre Änderungen auf dem Branch hoch.
Schritt 2: Gehen Sie auf die Zeile des Branches, drücken Sie Tab und wählen Sie „Pull Request erstellen …“.
Schritt 3: Prüfen Sie Titel und Beschreibung. Mit Tab kommen Sie zum Ziel-Branch und zu „Prüfer, freiwillig“. Wählen Sie dort Personen für ein Review.
Schritt 4: Drücken Sie Tab bis „Erstellen“ und Enter.

## Review abgeben, abhaken oder Änderungen anfordern
Bereich: branch
Aktionen: pull_requests
Stichwörter: Review, prüfen, genehmigen, abhaken, Änderungen anfordern
Schritt 1: Gehen Sie auf den Main-Branch, drücken Sie Tab und öffnen Sie „Pull Requests …“.
Schritt 2: Wählen Sie den Pull Request mit den Pfeiltasten und drücken Sie Tab bis „Prüfen …“, dann Enter.
Schritt 3: Wählen Sie bei „Ergebnis“ mit den Pfeiltasten „Genehmigen“, „Änderungen anfordern“ oder „Nur kommentieren“.
Schritt 4: Schreiben Sie bei Bedarf einen Kommentar und drücken Sie Tab bis „Review abgeben“.

## Auf ein Review antworten
Bereich: branch
Aktionen: pull_requests
Stichwörter: antworten, Kommentar, Review beantworten, Rückfrage
Schritt 1: Öffnen Sie „Pull Requests …“ und wählen Sie den Pull Request.
Schritt 2: Drücken Sie Tab bis „Kommentare …“ und Enter. Sie hören alle Kommentare und Reviews.
Schritt 3: Drücken Sie Tab bis „Neuer Kommentar“, schreiben Sie Ihre Antwort und wählen Sie „Kommentar senden“.

## Pull Request übernehmen
Bereich: branch
Aktionen: pull_requests
Stichwörter: Pull Request übernehmen, mergen, annehmen, zusammenführen
Schritt 1: Öffnen Sie auf dem Main-Branch „Pull Requests …“ und wählen Sie den Pull Request.
Schritt 2: Drücken Sie Tab bis „In main übernehmen …“ und Enter.
Schritt 3: Wählen Sie bei „Art des Übernehmens“ mit den Pfeiltasten und bestätigen Sie mit „Übernehmen“.
Schritt 4: Holen Sie danach auf dem Main-Branch die Änderungen von GitHub.

## Commit zurücknehmen oder rückgängig machen
Bereich: branch
Aktionen: history
Stichwörter: Commit entfernen, rückgängig, zurücknehmen, Fehler, undo, revert
Schritt 1: Gehen Sie auf den Main-Branch oder den Branch, drücken Sie Tab und öffnen Sie „Verlauf …“.
Schritt 2: Wählen Sie oben die Version, drücken Sie Tab in die Commits und wählen Sie den Commit.
Schritt 3: Drücken Sie Enter für die Details.
Schritt 4: Ist der Commit noch nicht hochgeladen, wählen Sie „Commit zurücknehmen …“. Die Änderungen bleiben in den Dateien.
Schritt 5: Ist er schon hochgeladen, wählen Sie „Version rückgängig machen …“. Das Cockpit macht dafür einen neuen Commit, nichts geht verloren.

## Zu einer früheren Version zurück
Bereich: branch
Aktionen: history
Stichwörter: Version, zurück, alter Stand, wiederherstellen
Schritt 1: Öffnen Sie „Verlauf …“ auf dem Main-Branch.
Schritt 2: Wählen Sie oben die Version mit den Pfeiltasten.
Schritt 3: Drücken Sie Tab bis „Zu dieser Version zurück …“ und Enter. Bestätigen Sie mit „Zurück zur Version“.
Schritt 4: Laden Sie danach wie gewohnt hoch.

## Wer hat wann hochgeladen
Bereich: branch
Aktionen: upload_history
Stichwörter: Hochladeverlauf, wer, wann, Push, Verlauf
Schritt 1: Gehen Sie auf den Main-Branch oder die Zeile des Branches.
Schritt 2: Drücken Sie Tab und öffnen Sie „Hochladeverlauf …“.
Schritt 3: Wählen Sie ein Hochladen und drücken Sie Tab. Sie hören die Commits dieses Hochladens. Enter zeigt die Details.

## Änderungen verwerfen
Bereich: branch
Aktionen: discard
Stichwörter: verwerfen, zurücksetzen, Änderung löschen, rückgängig
Schritt 1: Gehen Sie auf den Main-Branch oder den Branch, drücken Sie Tab und wählen Sie „Änderungen verwerfen …“.
Schritt 2: Haken Sie die Dateien mit der Leertaste an.
Schritt 3: Wählen Sie „Verwerfen …“ und bestätigen Sie. Vorher kommen die Dateien in die Sicherheitskopien.

## Konflikte lösen
Bereich: branch
Aktionen: resolve_conflicts
Stichwörter: Konflikt, zusammenführen, gleiche Stelle, merge conflict
Schritt 1: Die Zeile des Branches sagt „Konflikte beim Zusammenführen“. Drücken Sie dort Enter oder Tab und „Konflikte lösen …“.
Schritt 2: Wählen Sie für jede Datei, welche Fassung gilt.
Schritt 3: Bestätigen Sie. Danach laden Sie wie gewohnt hoch.

## README erstellen oder bearbeiten
Bereich: repository
Aktionen: readme
Stichwörter: README, Beschreibung, Anleitung zum Projekt
Schritt 1: Gehen Sie auf die Zeile Repository, drücken Sie Tab und wählen Sie „README …“.
Schritt 2: Wählen Sie „README mit KI schreiben …“, „README aus Ordner hochladen …“ oder bei einer vorhandenen README „README bearbeiten …“.
Schritt 3: Folgen Sie dem Fenster. Mit „README ist fertig so“ speichern Sie. Hochgeladen wird sie wie jede Änderung.

## Lizenz hinzufügen
Bereich: repository
Aktionen: license
Stichwörter: Lizenz, MIT, LICENSE, Rechte
Schritt 1: Gehen Sie auf die Zeile Repository, drücken Sie Tab und wählen Sie „Lizenz …“.
Schritt 2: Wählen Sie eine Lizenz mit den Pfeiltasten, zum Beispiel MIT, und bestätigen Sie.
Schritt 3: Die Datei LICENSE kommt in den Ordner Repository und wird wie jede Änderung hochgeladen.

## Repository verwalten oder löschen
Bereich: repository
Aktionen: manage_repo
Stichwörter: Repository, öffentlich, privat, archivieren, löschen, Mitarbeiter
Schritt 1: Gehen Sie auf die Zeile Repository, drücken Sie Tab und wählen Sie „Repository verwalten …“.
Schritt 2: Wählen Sie mit Tab: öffentlich oder privat, Mitarbeiter, archivieren oder „Repository löschen …“.
Schritt 3: Beim Löschen fragt das Cockpit zweimal, und Sie tippen den Namen ein. Escape bricht immer ab.

## Branch umbenennen oder löschen
Bereich: repository
Aktionen: branches
Stichwörter: Branch löschen, umbenennen, entfernen
Schritt 1: Gehen Sie auf die Zeile Repository und öffnen Sie „Branches verwalten …“.
Schritt 2: Wählen Sie den Branch und drücken Sie Tab bis „Umbenennen …“ oder „Löschen …“.
Schritt 3: Beim Löschen wählen Sie: nur hier, nur auf GitHub oder beides. main lässt sich nicht löschen.

## Projekt verwalten, umbenennen oder löschen
Bereich: projekt
Aktionen: manage_project
Stichwörter: Projekt löschen, umbenennen, entfernen, aus der Liste
Schritt 1: Gehen Sie auf die Projektzeile, drücken Sie Tab und wählen Sie „Projekt verwalten …“.
Schritt 2: Wählen Sie mit Tab „Projekt umbenennen …“, „Aus der Liste entfernen …“ oder „Projekt löschen …“.
Schritt 3: Lesen Sie die Rückfrage genau. Beim Löschen kommt der Ordner in die Sicherheitskopien.

## Exe erstellen
Bereich: releases
Aktionen: build_exe
Stichwörter: Exe, Programm bauen, erstellen, kompilieren, PyInstaller
Schritt 1: Klappen Sie das Projekt auf und gehen Sie mit Pfeil runter auf „Exe-main“.
Schritt 2: Drücken Sie Tab und wählen Sie „Exe aus main erstellen …“.
Schritt 3: Folgen Sie den Schritten: Dateien neben der Exe, mit oder ohne KI, Zusammenfassung, Bau.
Schritt 4: Am Ende testen Sie die Exe und übernehmen sie in main.

## Exe-Bau abschließen und in main überführen
Bereich: releases
Aktionen: finish_exe, finish_exe_branch, finish_exe_release
Stichwörter: Cockpit-exe-bauen, in main überführen, übernehmen, Branch zu main, Exe-Bau abschließen, verwerfen, trotzdem behalten
Schritt 1: Gehen Sie auf die Zeile „Cockpit-exe-bauen“ unter Repository oder auf „Exe-Cockpit-exe-bauen“ unter Releases.
Schritt 2: Drücken Sie Tab und wählen Sie „In main überführen oder verwerfen, Exe-Bau abschließen …“. Auf „Exe-main“ heißt es „Exe-Bau abschließen …“.
Schritt 3: Wählen Sie „Jetzt in main überführen und Release veröffentlichen“ oder „Jetzt in main überführen, später veröffentlichen“.
Schritt 4: Das Cockpit überführt den Branch in main, macht seine Exe zur normalen Exe und löscht den Branch. Beide Zeilen verschwinden dann.

## Release für einen Branch erstellen
Bereich: releases
Aktionen: create_release
Stichwörter: Release, Branch, Exe für Branch, anlegen
Schritt 1: Gehen Sie auf die Zeile Releases, drücken Sie Tab und wählen Sie „Release für Branch aus Repository erstellen …“.
Schritt 2: Wählen Sie den lokalen Branch, drücken Sie Tab bis „Release-Ordner lokal anlegen“ und Enter.
Schritt 3: Auf der neuen Zeile, zum Beispiel „Exe-neue-funktion“, wählen Sie „Exe aus neue-funktion erstellen …“.

## Release veröffentlichen
Bereich: releases
Aktionen: publish_release
Stichwörter: veröffentlichen, Release, Download, GitHub Release
Schritt 1: Gehen Sie auf die Zeile Releases, drücken Sie Tab und wählen Sie „Release veröffentlichen …“.
Schritt 2: Wählen Sie das Release, drücken Sie Tab bis „Veröffentlichen“ und Enter.
Schritt 3: Geben Sie die Version ein und bestätigen Sie. Der Link kommt in die Zwischenablage.

## Release entfernen
Bereich: releases
Aktionen: remove_release
Stichwörter: Release löschen, entfernen
Schritt 1: Gehen Sie auf die Zeile Releases oder auf ein Release und wählen Sie „Release entfernen …“.
Schritt 2: Wählen Sie: nur lokal, nur auf GitHub oder beides. Abbrechen ist die Vorgabe.

## KI verknüpfen
Bereich: alle
Aktionen:
Stichwörter: KI, Ollama, künstliche Intelligenz, verbinden, Modell
Schritt 1: Öffnen Sie mit Alt das Menü und gehen Sie zu KI, dann „KI-Verwaltung …“.
Schritt 2: Fügen Sie Ollama auf diesem Rechner oder ein KI-Konto hinzu und wählen Sie ein Modell.
Schritt 3: Nach dem nächsten Start misst das Cockpit die KI. Im Menü KI steht dann „KI ist eingestellt auf diesen Rechner …“.

## Git und GitHub verknüpfen
Bereich: alle
Aktionen:
Stichwörter: GitHub, Konto, anmelden, Git, Token, verbinden
Schritt 1: Ist Git nicht installiert, folgen Sie im Menü Hilfe „Git installieren …“.
Schritt 2: Öffnen Sie im Menü Konten die „Kontenverwaltung …“ und fügen Sie ein GitHub-Konto hinzu.
Schritt 3: Melden Sie sich im Browser an. Danach stehen Ihre Repositories in der Liste.

## Alle Tastenkürzel
Bereich: alle
Aktionen:
Stichwörter: Tasten, Tastenkürzel, Tastatur, Shortcut
Schritt 1: Im Menü Hilfe zeigt „Tastenkürzel“ die ganze Liste. Das geht auch mit Strg+Umschalt+F1.
Schritt 2: Strg+F1 sagt an, welche Tasten beim Element mit dem Fokus etwas tun.
Schritt 3: Strg+K sucht einen Befehl, die Menütaste öffnet die Aktionen als Kontextmenü.
