# Kurzanleitungen

Schritt für Schritt, mit den Tasten. Jede Anleitung nennt ihren Bereich (start, projekt, repository, branch, releases) und die Aktionen, die sie benutzt. Ein Test prüft, dass es diese Aktionen gibt.

## Projektordner hinzufügen
Bereich: start
Aktionen: add_local
Stichwörter: Ordner, hinzufügen, neues Projekt, aufnehmen
Schritt 1: Drücken Sie Strg+1 und Pos1. Sie sind ganz oben in der Projektliste.
Schritt 2: Drücken Sie einmal Pfeil runter auf „Projekt vom Rechner hinzufügen“ und dann Enter.
Schritt 3: Wählen Sie im Fenster von Windows den Projektordner. Darin liegen Repository und Release oder einfach Ihr Code. Bestätigen Sie mit „Ordner auswählen“.
Schritt 4: Passt der Aufbau nicht, fragt das Cockpit, ob es den Ordner umstellt. Heißen die Ordner noch Code und Exe, bietet es „Umbenennen“ an. Liegt der Code direkt in Repository, verschiebt es ihn nach Repository\main. Eine Exe direkt in Release kommt in ihren eigenen Ordner. Lesen Sie jede Rückfrage und wählen Sie mit Tab.
Schritt 5: Heißen die Unterordner ganz anders, wählen Sie „Hier Repository und Release anlegen …“. Kopieren Sie danach Ihren Code in Repository\main und wählen Sie auf der Projektzeile „Projekt neu einlesen“.
Schritt 6: Das Projekt steht danach in der Liste und ist markiert.

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
Schritt 4: In der Liste „Änderungen“ ist jede Datei angehakt. Mit der Leertaste nehmen Sie eine Datei aus dem Commit. Enter auf einer Datei zeigt ihre Abschnitte: Dort haken Sie ab, was noch nicht mit soll, und Enter liest einen Abschnitt vor. Was nicht angehakt ist, bleibt in der Datei für später. Mit „Co-Autoren …“ nennen Sie Personen, die mitgearbeitet haben.
Schritt 5: Bestätigen Sie. Das Cockpit macht den Commit und lädt hoch. Sie hören Töne, solange es läuft.
Schritt 6: Auf einem Branch bietet das Cockpit danach an, einen Pull Request zu stellen.

## Änderungen von GitHub holen
Bereich: branch
Aktionen: pull_changes
Stichwörter: herunterladen, holen, pull, aktualisieren, neuer Stand
Schritt 1: Gehen Sie auf den Main-Branch oder die Zeile des Branches.
Schritt 2: Drücken Sie Tab und wählen Sie „Änderungen von GitHub holen …“, dann Enter.
Schritt 3: Das Cockpit sagt, was neu ist, und fragt, ob es zusammenführen soll. Bestätigen Sie.

## Branch erstellen
Bereich: repository
Aktionen: branch_show
Stichwörter: Branch, neuer Branch, abzweigen, Zweig
Schritt 1: Klappen Sie das Projekt mit Pfeil rechts auf. Pfeil runter führt auf die Zeile Repository.
Schritt 2: Drücken Sie Enter. Es öffnet sich die Auswahl „Branches“. Wählen Sie ganz unten „Branches verwalten …“.
Schritt 3: Drücken Sie Tab bis „Neuer Branch …“ und Enter.
Schritt 4: Geben Sie den Namen ein, zum Beispiel neue-funktion, und drücken Sie Enter. Der Branch bekommt einen eigenen Ordner und steht in der Liste.

## Branch in main übernehmen
Bereich: repository
Aktionen: branch_show
Stichwörter: übernehmen, merge, zusammenführen, in main, fertig
Schritt 1: Gehen Sie auf die Zeile Repository, drücken Sie Enter und wählen Sie ganz unten „Branches verwalten …“.
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

## Checks eines Pull Requests ansehen
Bereich: branch
Aktionen: pull_requests
Stichwörter: Checks, Prüfungen, Tests, Actions, fehlgeschlagen, CI
Schritt 1: Öffnen Sie „Pull Requests …“ und drücken Sie Enter auf dem Pull Request.
Schritt 2: In den Angaben steht zum Beispiel „Checks: 1 fehlgeschlagen (Tests), 2 erfolgreich“.
Schritt 3: Drücken Sie Tab bis „Checks …“. Dort steht jeder Check mit seinem Ergebnis, fehlgeschlagene zuerst.
Schritt 4: Beim Übernehmen steht der Stand der Checks gleich nach dem ersten Satz.

## Zu einem fremden Projekt beitragen (Fork)
Bereich: start
Aktionen: add_remote
Stichwörter: Fork, fremdes Projekt, beitragen, Original, upstream
Schritt 1: Wählen Sie „Projekt von GitHub herunterladen“, dann „Adresse eingeben …“, und geben Sie die Adresse des Projekts ein.
Schritt 2: Dürfen Sie dort nicht hochladen, fragt das Cockpit nach einem Fork. Wählen Sie „Fork anlegen und herunterladen“.
Schritt 3: Arbeiten Sie in einem eigenen Branch und laden Sie wie gewohnt hoch. Das landet in Ihrem Fork.
Schritt 4: Bei „Pull Request erstellen …“ wählen Sie „An das Original“.
Schritt 5: Neues aus dem Original holen Sie beim Main-Branch mit „Vom Original holen …“. Danach laden Sie main hoch.

## Issues lesen und anlegen
Bereich: branch
Aktionen: issues
Stichwörter: Issue, Fehlermeldung, Aufgabe, Ticket, Label, zuweisen, Bug
Schritt 1: Gehen Sie auf den Main-Branch, drücken Sie Tab und öffnen Sie „Issues …“.
Schritt 2: Die Liste zeigt die offenen Issues. Bei „Anzeigen“ wählen Sie auch geschlossene oder alle.
Schritt 3: Enter öffnet die Details mit allen Kommentaren. Dort schreiben Sie bei „Neuer Kommentar“ und wählen „Kommentar senden“.
Schritt 4: Mit „Neues Issue …“ legen Sie eines an, auf Wunsch mit Labels und Personen.
Schritt 5: „Labels …“, „Zuweisen …“ und „Issue schließen …“ wirken auf das markierte Issue.

## Issue mit KI zusammenfassen und Branch anlegen
Bereich: branch
Aktionen: issues
Stichwörter: Issue, KI, zusammenfassen, Branch-Name, Vorschlag
Schritt 1: Öffnen Sie „Issues …“ und drücken Sie Enter auf dem Issue.
Schritt 2: Ist der KI-Assistent im Projekt aktiv, gibt es „Mit KI zusammenfassen“. Die Zusammenfassung und ein Branch-Name stehen danach oben in den Angaben.
Schritt 3: Schließen Sie die Details und wählen Sie „Branch dafür anlegen …“. Der Name der KI ist schon eingetragen. Ohne KI steht dort die Nummer mit dem Titel, zum Beispiel 12-suche-in-pdfs.

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

## Commit nachbessern
Bereich: branch
Aktionen: history
Stichwörter: nachbessern, amend, Nachricht ändern, vergessen, korrigieren
Schritt 1: Öffnen Sie „Verlauf …“ und wählen Sie den neuesten Commit. Drücken Sie Enter für die Details.
Schritt 2: Wählen Sie „Commit nachbessern …“. Das geht nur, solange der Commit noch nicht hochgeladen ist.
Schritt 3: Ändern Sie Nachricht und Beschreibung. Haken Sie „Änderungen ohne Commit mit hineinnehmen“ an, wenn vergessene Dateien mit sollen.
Schritt 4: Bestätigen Sie. Der alte Stand bleibt gesichert.

## Commit in einen anderen Branch übernehmen
Bereich: branch
Aktionen: history
Stichwörter: übernehmen, cherry-pick, kopieren, anderer Branch
Schritt 1: Öffnen Sie „Verlauf …“, wählen Sie den Commit und drücken Sie Enter.
Schritt 2: Wählen Sie „In anderen Branch übernehmen …“ und dann den Ziel-Branch.
Schritt 3: Bestätigen Sie. Passt der Commit nicht ohne Konflikt, bleibt alles, wie es war.

## Commits umsortieren oder zusammenfassen
Bereich: branch
Aktionen: history
Stichwörter: umsortieren, zusammenfassen, squash, Reihenfolge, rebase
Schritt 1: Öffnen Sie „Verlauf …“ und drücken Sie Tab bis „Reihenfolge und Zusammenfassen …“. Der Knopf erscheint, wenn mindestens zwei Commits noch nicht hochgeladen sind.
Schritt 2: Die neueste Zeile steht oben. Mit Strg und Pfeil hoch oder runter verschieben Sie einen Commit.
Schritt 3: Mit „Mit dem darunter zusammenfassen“ kommt ein Commit mit dem darunter zusammen.
Schritt 4: Wählen Sie „Übernehmen“ und bestätigen Sie. Hochgeladene Commits bleiben immer, wie sie sind.

## Branch ab einem früheren Commit
Bereich: branch
Aktionen: history
Stichwörter: Branch ab hier, früherer Stand, abzweigen, alter Commit
Schritt 1: Öffnen Sie „Verlauf …“, wählen Sie den Commit und drücken Sie Enter.
Schritt 2: Wählen Sie „Neuer Branch ab hier …“ und geben Sie den Namen ein.
Schritt 3: Mit Branch-Ordnern bekommt der Branch einen eigenen Ordner. Sonst bleiben Sie auf Ihrem Branch.

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
Schritt 2: Wählen Sie für jede Datei, welche Fassung gilt. Oder drücken Sie Enter auf der Datei: Dann hören Sie jede Konfliktstelle einzeln.
Schritt 3: Bei den Stellen liest Enter vor, erst Ihre Fassung, dann die von GitHub. Wählen Sie dann „Meine Fassung“, „Fassung von GitHub“ oder „Beide, meine zuerst“. „Stelle im Editor anzeigen“ springt im Editor zur Zeile.
Schritt 4: Wählen Sie „Zusammenführen abschließen“. Danach laden Sie wie gewohnt hoch.

## Im Editor öffnen
Bereich: branch
Aktionen: open_in_editor
Stichwörter: Editor, Visual Studio Code, VS Code, Notepad++, bearbeiten, öffnen
Schritt 1: Gehen Sie auf den Main-Branch oder die Zeile Ihres Branches.
Schritt 2: Drücken Sie Tab und wählen Sie „Im Editor öffnen“. Der Ordner des Branches öffnet sich im Editor.
Schritt 3: Das Cockpit nimmt Visual Studio Code, Notepad++ oder den Windows-Editor, je nachdem, was es findet. Einen anderen Editor tragen Sie in den Grundeinstellungen bei „Editor-Programm“ ein.

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
Aktionen: branch_show
Stichwörter: Branch löschen, umbenennen, entfernen
Schritt 1: Gehen Sie auf die Zeile Repository, drücken Sie Enter und wählen Sie ganz unten „Branches verwalten …“.
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
Schritt 1: Gehen Sie auf die Zeile Releases, drücken Sie Tab und wählen Sie „Exe für einen Branch erstellen …“.
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


## Pakete und Modelle verwalten
Bereich: alle
Aktionen:
Stichwörter: Pakete, Modelle, Bibliotheken, pip, winget, Chocolatey, veraltet, aktualisieren, Version, Paketübersicht
Schritt 1: Drücken Sie Strg+Umschalt+P. Oder öffnen Sie mit Alt+A das Menü Pakete und wählen Sie „Paketübersicht …“.
Schritt 2: Sie sind in der Liste der Quellen. Die erste Zeile nennt den Speicherplatz. Jede Quelle sagt, wie viele Pakete veraltet sind. Die Prüfung läuft im Hintergrund.
Schritt 3: Mit „Zeigen“ wählen Sie: alles, nur die Cockpit-Projekte oder nur den übrigen Rechner.
Schritt 4: Gehen Sie auf eine Quelle und drücken Sie Enter. Die Pakete stehen neueste zuerst, mit „aktuell“ oder „veraltet“.
Schritt 5: Drücken Sie Tab. Sie sind bei den Aktionen, zum Beispiel „Aktualisieren …“, „Version wählen …“, „Festhalten“ und „Zurück …“.
Schritt 6: Vor jeder Änderung fragt das Cockpit. Vorgabe und Escape sind die sichere Antwort.

## Pakete und Modelle aufräumen
Bereich: alle
Aktionen:
Stichwörter: aufräumen, Speicherplatz, Platz, löschen, alte Fassungen, Zwischenspeicher, Modelle
Schritt 1: Öffnen Sie mit Alt+A das Menü Pakete und wählen Sie „Aufräumen …“.
Schritt 2: Die Liste nennt, was weg kann, und wie viel Platz das bringt. Haken Sie mit der Leertaste an, was weg soll.
Schritt 3: Nichts ist vorab angehakt. Bei Modellen ohne bekannten Benutzer prüfen Sie selbst, ob ein anderes Programm sie braucht.
Schritt 4: Bestätigen Sie. Vorher kommt eine Liste mit dem Befehl zum Wiederherstellen in die Sicherheitskopien.

## Bibliotheken oder Modell in Projekten tauschen
Bereich: alle
Aktionen:
Stichwörter: tauschen, Bibliotheken, Projekte, requirements, Modell ersetzen, Nachfolger, Branch
Schritt 1: Öffnen Sie die Paketübersicht mit Strg+Umschalt+P.
Schritt 2: Für Bibliotheken wählen Sie „Bibliotheken in Projekten …“. Für ein Modell öffnen Sie die Quelle Sprachmodelle, gehen auf das Modell und wählen „In Projekten tauschen …“.
Schritt 3: Beim Modell geben Sie den neuen Namen ein oder holen einen Vorschlag der KI. Ein Vorschlag ist nur ein Vorschlag, prüfen Sie ihn.
Schritt 4: Das Cockpit ändert die Projekte in einem eigenen Branch und lässt danach die Tests laufen. In main ändert sich nichts.

## Liste der Pakete für einen neuen Rechner
Bereich: alle
Aktionen:
Stichwörter: neuer Rechner, Liste speichern, einlesen, installieren, umziehen
Schritt 1: Öffnen Sie mit Alt+A das Menü Pakete und wählen Sie „Liste für einen neuen Rechner speichern …“. Wählen Sie einen Ort für die Datei.
Schritt 2: Auf dem neuen Rechner wählen Sie „Liste einlesen und installieren …“ und dann die Datei.
Schritt 3: Das Cockpit zeigt, was fehlt. Alles ist angehakt. Nehmen Sie mit der Leertaste den Haken weg, wo Sie nichts installieren wollen, und bestätigen Sie.

## Ordner nach Modellen durchsuchen
Bereich: alle
Aktionen:
Stichwörter: Modelle suchen, Ordner, Modelldateien, gguf, durchsuchen
Schritt 1: Öffnen Sie mit Alt+A das Menü Pakete und wählen Sie „Ordner nach Modellen durchsuchen …“.
Schritt 2: Wählen Sie den Ordner. Das Cockpit merkt ihn sich.
Schritt 3: Gefundene Modelldateien stehen danach in der Quelle Sprachmodelle.
## Neuigkeiten seit dem letzten Start lesen
Bereich: alle
Stichwörter: Neuigkeiten, neu, Kommentare, Issues, Pull Requests, Sterne, was ist passiert, Wochenüberblick
Schritt 1: Drücken Sie Strg+Umschalt+N. Oder öffnen Sie mit Alt+N das Menü Neuigkeiten und wählen Sie „Neuigkeiten seit dem letzten Start“.
Schritt 2: Sie sind in der Liste. Jede Zeile beginnt mit dem Projekt, dann was passiert ist, dann wer und wann.
Schritt 3: Für einen anderen Zeitraum drücken Sie Umschalt+Tab bis „Zeitraum“ und wählen mit Pfeil runter „Letzte 7 Tage“ oder „Letzte 30 Tage“.
Schritt 4: Enter auf einer Zeile zeigt das Issue oder den Pull Request im Cockpit. Mit Tab kommen Sie zu „Im Browser öffnen“.

## Aktivität der Projekte ansehen
Bereich: alle
Stichwörter: Aktivität, Aufrufe, Besucher, Klone, Downloads, Sterne, Statistik, beliebt, README
Schritt 1: Öffnen Sie mit Alt+N das Menü Neuigkeiten und wählen Sie „Aktivität der Projekte“.
Schritt 2: Sie sind in der Liste der Projekte. Jede Zeile nennt Aufrufe, Klone, Downloads und Sterne.
Schritt 3: Enter auf einem Projekt zeigt die Einzelheiten: Zahlen pro Tag, Downloads pro Release, meistbesuchte Seiten und Herkunft der Besucher.
Schritt 4: Mit Tab kommen Sie zu „Kommentare und Issues“. Dort stehen die letzten Kommentare, Issues und Pull Requests des Projekts.
