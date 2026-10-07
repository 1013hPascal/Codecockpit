# Entwurf: neue Projektliste

So habe ich Ihren Wunsch vom 06.10.2026 verstanden. Bitte sagen Sie, was nicht stimmt.

## Ihre Antworten vom 06.10.2026

- Projekt umbenennen benennt alles um: Name in der Liste, Ordner auf dem Rechner und Repository auf GitHub.
- Löschen bei main ist nicht verfügbar, mit Grund: Main ist der Hauptbranch.
- Die Ordner werden umbenannt: Code heißt dann Repository, Exe heißt Release. Das Cockpit macht das bei jedem Projekt mit Bestätigung und Sicherheitskopie.
- Das Terminal beim Repository öffnet im Ordner Repository. Von dort geht man selbst in main oder einen Branch.

## Aufbau der Liste

Ein ausgeklapptes Projekt sieht dann so aus, von oben nach unten:

- Projekt, ausgeklappt
- Repository, zeigt: main und die Branches, die Sie lokal haben
- Main-Branch, mit seinem Stand wie bisher
- die anderen Branches, je nach Auswahl beim Repository
- Releases
- je ein Release pro Branch, zum Beispiel „Exe-main“ und „Exe-neue-funktion“

## Die Projektzeile

Aktionen:

- Projekt neu einlesen
- Terminal, im obersten Projektordner
- Projekt verwalten …
- Projektordner öffnen, wirklich der oberste Ordner des Projekts
- Features dieses Projekts …
- wie bisher, wenn es passt: Repository anlegen und hochladen, Exe hinzufügen, Neuen Ort angeben

„Releases …“, „Links“, „README“ und „Lizenz“ wandern weg von hier.

„Projekt verwalten …“ ist ein neues Fenster. Oben steht der derzeitige Name. Mit Tab: „Projekt umbenennen …“, „Aus der Liste entfernen …“, „Projekt löschen …“. Beim Löschen steht: Lokaler Ordner auf dem Rechner, Repository und Release werden gelöscht. Vorher fragt das Cockpit zweimal, und Sie tippen den Namen ein, wie heute beim Repository. Der lokale Ordner kommt vorher in die Sicherheitskopien.

## Die Zeile Repository

Enter oder Leertaste öffnet ein Auswahlmenü, wie heute „Branches anzeigen“:

- Nur main
- main und die Sie lokal haben, das ist die Vorgabe
- main und die nur auf GitHub sind
- main und alle

Main steht immer in der Liste. Branches nur auf GitHub stehen wie heute „angepinnte“ Branches darin, mit „Herunterladen“, „Auf GitHub öffnen“.

Aktionen mit Tab:

- Repository neu einlesen
- Terminal, im Repository-Ordner
- Repository verwalten …, das ist das bisherige „Projekt verwalten …“ (öffentlich, privat, Mitarbeiter, archivieren, löschen)
- Branches verwalten …, das bisherige Fenster aus der Liste
- Links …
- README …
- Lizenz …
- Repository-Identität …, bisher „Git-Identität“ beim Main-Branch
- Auf GitHub öffnen, der Link zum Repository
- GitHub Actions …
- Repository-Ordner öffnen

Die Zeile „Branches verwalten“ in der Liste fällt weg.

## Branches verwalten

Jetzt auch für main: Tab zu „Infos“, „Umbenennen …“, „Löschen …“. Löschen ist bei main nicht verfügbar und nennt den Grund.

Infos zeigt: wer den Branch angelegt hat, wann, letzte Änderung von wem und wann, Anzahl der Commits, ob er auf GitHub ist und ob er geschützt ist.

Bei den anderen Branches bleibt alles wie heute. „Branch-Ordner löschen“ gibt es dort schon nicht mehr. „Löschen …“ fragt: nur hier, nur auf GitHub oder beides.

## Die Branch-Zeilen und der Main-Branch

Alle Aktionen wie heute. Nur:

- „Projekt neu einlesen“ heißt dort „Repository neu einlesen“.
- Ganz unten neu: „Branch-Ordner öffnen“.
- Terminal öffnet im Ordner dieses Branches.

## Die Zeile Releases

Aktionen:

- Releases neu einlesen
- Terminal, im Release-Ordner
- Release für Branch aus Repository erstellen …
- Release veröffentlichen …
- Release entfernen …
- Releases auf GitHub …, die bisherige Liste „Releases …“
- Release-Ordner öffnen

„Release für Branch erstellen …“: Oben steht „Releases können nur für Branches erstellt werden, die lokal auf dem Rechner sind.“ Darunter die lokalen Branches. Tab führt zu „Release-Ordner lokal anlegen“. Danach steht „Exe-Branchname“ unter Releases in der Liste.

„Release veröffentlichen …“: eine Liste der Releases, oben immer das von main. Jede Zeile sagt, wann es zuletzt veröffentlicht wurde, oder „noch nicht veröffentlicht“. Tab führt zu „Veröffentlichen“.

„Release entfernen …“: dieselbe Liste. Tab führt zu „Release entfernen“. Dann wählen Sie: nur lokal auf dem Rechner, nur auf GitHub oder beides. Lokal kommt der Ordner vorher in die Sicherheitskopien.

## Eine Release-Zeile, zum Beispiel Exe-main

Die Exe-Aktionen wie heute. Geändert:

- „Exe einlesen …“ heißt „Release einlesen …“, dazu kommt „Terminal“ im Ordner dieses Releases.
- „Exe aus dem Code erstellen …“ heißt „Exe aus main erstellen …“, bei einem Branch „Exe aus neue-funktion erstellen …“.
- „Exe-Ordner öffnen“ heißt „Exe-main-Ordner öffnen“.

Für main baut das Cockpit wie heute über den Assistenten und den Branch Cockpit-exe-bauen. Für einen anderen Branch baut es direkt aus dessen Ordner, wie heute „Exe aus diesem Branch erstellen“.

## Terminal

Jedes Terminal öffnet dort, wo die Zeile hingehört:

- Projekt: oberster Projektordner
- Repository: Repository-Ordner
- Branch: Ordner des Branches
- Releases: Release-Ordner
- ein Release: Ordner dieses Releases

## Vorschlag zur Reihenfolge

Der Umbau ist groß. Ich schlage fünf Teilschritte vor, jeder mit Tests und Checkliste. Sie können nach jedem Schritt prüfen.

1. Projektzeile und „Projekt verwalten …“
2. Zeile Repository mit Auswahl und Aktionen, „Branches verwalten“ mit main
3. Branch-Zeilen
4. Releases und Release-Zeilen
5. Terminal überall
6. Ordner Code in Repository und Exe in Release umbenennen

## Meine Annahmen, bitte prüfen

- „Bitte keine Projekte anzeigen“ beim Repository verstehe ich als „Nur main“, also keine weiteren Branches.
- „Link zum Repository, Repository-Identität, Repository-Ordner“ verstehe ich als Aktionen, die vom Main-Branch zur Zeile Repository wandern.
- „Releases …“ (die Liste auf GitHub) und „GitHub Actions …“ wandern von der Projektzeile weg. Releases zu Releases, GitHub Actions zu Repository.
- Ein Release für einen anderen Branch als main wird auf GitHub als Vorabversion veröffentlicht. So sieht niemand es als die neue Hauptversion an.
