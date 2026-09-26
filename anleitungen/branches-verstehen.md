# Branches verstehen

Diese Anleitung erklärt, was Branches sind, wann man sie braucht und was dabei wo passiert.

Tipp: Mit den Pfeiltasten lesen Sie Zeile für Zeile. Escape schließt die Anleitung.


## Was ist ein Branch?

Ein Branch ist eine eigene Arbeitslinie in einem Projekt.

Der Haupt-Branch heißt meistens main. Er enthält den Stand, der gilt.

Ein neuer Branch beginnt mit genau dem Stand, auf dem Sie gerade sind.

Danach können Sie in ihm arbeiten, ohne main zu verändern.

Git speichert in einem Branch keine Kopie aller Dateien, sondern Ihre Änderungen. Jede Änderung ist ein Commit.


## Wozu braucht man Branches?

Sie probieren etwas aus und wissen noch nicht, ob es bleibt.

Mehrere Personen arbeiten gleichzeitig an verschiedenen Dingen.

Jemand soll Ihre Änderung prüfen, bevor sie in main kommt. Das geht später mit einem Pull Request, siehe unten.

Für kleine Projekte, an denen nur Sie arbeiten, reicht oft main allein.


## Ein Beispiel mit zwei Personen

Anna und Ben arbeiten am Projekt Tagebuch.

1. Anna legt den Branch design an. Sie ändert dort nur die Datei style.css.
2. Ben legt den Branch barrierefreiheit an. Er ändert dort nur main.py.
3. Beide laden ihren Branch mit „Änderungen hochladen“ auf GitHub hoch.
4. Ben ist zuerst fertig. Er übernimmt barrierefreiheit in main. Jetzt enthält main seine Änderung an main.py.
5. Danach übernimmt Anna design in main.

Wichtig: Beim Übernehmen bringt Git nur die Änderungen, die in diesem Branch gemacht wurden.

Anna bringt also nur ihre Änderung an style.css nach main.

Bens Änderung an main.py bleibt erhalten, obwohl Annas Branch sie nie gesehen hat.

Git kopiert also nicht einfach alle Dateien, die anders aussehen.

Nur wenn beide dieselbe Stelle derselben Datei geändert haben, gibt es einen Konflikt. Dann wählen Sie wie beim Holen, welche Fassung gilt.


## Kann man einzelne Dateien übernehmen?

Nein. Übernommen wird immer alles, was in dem Branch geändert wurde.

Deshalb gehört in einen Branch nur, was zusammengehört. Für das Design ein Branch, für die Barrierefreiheit ein anderer.

So ist es auch auf GitHub.


## Was steht in der Übersicht Branches?

Jede Zeile nennt zuerst den Namen, dann den Ort, dann, wer zuletzt daran gearbeitet hat, und dann den Stand.

Beispiel: „design, hier und auf GitHub, zuletzt von Anna am 24.09.2026, 2 Commits vor main“.

Git merkt sich nicht, wer einen Branch angelegt hat, sondern wer die Commits gemacht hat. Deshalb steht dort, wer zuletzt daran gearbeitet hat. Meist ist das dieselbe Person.


## Hier und auf GitHub

Ein Branch kann an zwei Orten liegen: auf Ihrem Rechner und auf GitHub.

„nur hier“ heißt: Der Branch liegt nur bei Ihnen. „Änderungen hochladen“ bringt ihn auf GitHub.

„nur auf GitHub“ heißt: Jemand anderes hat ihn angelegt, oder Sie haben ihn hier gelöscht. Wechseln holt ihn auf Ihren Rechner.

„hier und auf GitHub“ heißt: Er liegt an beiden Orten. Die Zeile sagt dann auch, ob etwas noch nicht hochgeladen oder noch nicht geholt ist.

Den Ort wählen Sie nicht in einem Auswahlfeld. Er ergibt sich aus dem, was Sie tun: Neuer Branch legt ihn hier an, Hochladen bringt ihn auf GitHub, Wechseln holt ihn von GitHub, Löschen fragt, wo.


## Was macht Wechseln?

Wechseln legt fest, an welchem Branch Sie gerade arbeiten.

Der Ordner Code zeigt danach die Dateien dieses Branches. Hochladen und Holen gelten dann für ihn.

Wechseln geht zu jedem Branch der Liste, nicht nur zu main.

Wechseln ist keine Wahl zwischen Ihrem Rechner und GitHub. Liegt der Branch nur auf GitHub, holt Wechseln ihn nebenbei auf Ihren Rechner.


## Was mache ich wo?

Im Fenster Branches: wechseln, neuen Branch anlegen, in main übernehmen, umbenennen, löschen.

In der Aktionsliste bei Code: Änderungen hochladen und holen, immer für den aktuellen Branch.

Leute ins Repository holen gehört nicht zu Branches. Das ist „Mitarbeiter …“ beim Projekt unter „Repository verwalten …“.


## Wo bin ich gerade?

Sind Sie nicht auf main, nennt die Zeile Code den Branch, zum Beispiel „Code, Branch design“.

In der Übersicht Branches steht beim aktuellen Branch „aktueller Branch“.

Hochladen und Holen arbeiten immer mit dem aktuellen Branch.


## Was passiert wo?

Wechseln: nur auf Ihrem Rechner. Die Dateien im Ordner Code zeigen danach den Stand dieses Branches.

Neuer Branch: zuerst nur auf Ihrem Rechner. Auf GitHub kommt er mit „Änderungen hochladen“.

In main übernehmen: zuerst nur auf Ihrem Rechner. Das Cockpit wechselt dazu zu main. Auf GitHub kommt es mit „Änderungen hochladen“ auf main.

Umbenennen: auf Ihrem Rechner. Liegt der Branch auch auf GitHub, benennt das Cockpit ihn dort ebenfalls um.

Löschen: Sie wählen, ob nur auf Ihrem Rechner, nur auf GitHub oder an beiden Orten.


## Welche Branches darf ich löschen?

Jeden Branch außer dem, auf dem Sie gerade sind, und außer main.

Sie müssen einen Branch nicht erst aktivieren, um ihn zu löschen. Markieren Sie ihn in der Liste und wählen Sie „Löschen …“.

Den Branch, auf dem Sie sind, löschen Sie erst, nachdem Sie zu einem anderen gewechselt haben. Der Grund: Ihr Ordner Code zeigt gerade seine Dateien. Den Boden, auf dem man steht, kann man nicht wegnehmen. So ist es auch in Git und GitHub Desktop.

Meist löscht man einen Branch, nachdem er in main übernommen wurde. Dann steht seine Arbeit ja in main.

Nur hier löschen: Sie brauchen ihn auf Ihrem Rechner nicht mehr, andere arbeiten auf GitHub vielleicht noch damit.

Nur auf GitHub löschen: Die anderen brauchen ihn nicht mehr, Sie behalten ihn für sich.

Das Cockpit hebt die Commits eines gelöschten Branches auf. Es geht also nichts verloren.


## Ein typischer Ablauf

1. Code, „Branches …“, „Neuer Branch …“, Name design.
2. Im Ordner Code die Dateien ändern.
3. „Änderungen hochladen“. Das legt einen Commit an und bringt den Branch auf GitHub.
4. Andere schauen sich den Branch auf GitHub an.
5. Passt alles: In der Übersicht Branches design markieren, „In main übernehmen …“.
6. Sie sind jetzt auf main. „Änderungen hochladen“ bringt das Ergebnis auf GitHub.
7. design wird nicht mehr gebraucht: markieren, „Löschen …“, „Hier und auf GitHub“.


## Beiseitelegen

Haben Sie Änderungen ohne Commit und wollen kurz zu einem anderen Branch, legen Sie die Änderungen beiseite.

Beim Zurückwechseln bietet das Cockpit an, sie zurückzuholen.

Unter Code, „Beiseitegelegte Änderungen …“ sehen Sie alles, was beiseitegelegt ist.


## Pull Requests kommen später

In Firmen darf man oft nicht selbst in main übernehmen.

Man stellt dann auf GitHub einen Antrag, einen Pull Request. Andere prüfen ihn und übernehmen ihn in main.

Das Cockpit lernt Pull Requests in Phase 6.
