# Aufräumrunde der Aktionen

Stand 20.10.2026. Hier stehen alle Aktionen des Cockpits, geordnet nach der Zeile im Projektbaum, auf der sie stehen.

## So füllen Sie die Liste aus

Jede Aktion hat eine Zeile „Ihre Wahl:“. Schreiben Sie dahinter eins dieser Wörter:

* **behalten**: bleibt, wie es ist.
* **umbenennen in …**: mit dem neuen Namen.
* **verschieben nach …**: auf eine andere Zeile oder ins Untermenü „Weitere“.
* **weg**: Die Aktion soll verschwinden.
* **Vorschlag**: Sie übernehmen meinen Vorschlag.

Lassen Sie die Zeile leer, bleibt alles, wie es ist. Mein Vorschlag steht jeweils darüber, wenn ich einen habe.

Meine Grundidee: Auf jeder Zeile stehen oben die häufigen Aktionen. Seltene kommen in ein Untermenü „Weitere …“. Gleiches heißt überall gleich.



## Zeile des Projekts (zum Beispiel „Würfelsimulator“)

\[ ] Projekt verwalten …
Ihre Wahl:

\[ ] Projektordner öffnen
Ihre Wahl:

\[ ] Terminal …
Mein Vorschlag: nach „Weitere …“. Es gibt „Terminal …“ auf sechs Zeilen.
Ihre Wahl: vorschlag

\[ ] Features dieses Projekts …
Mein Vorschlag: nach „Weitere …“.
Ihre Wahl: vorschlag

\[ ] Repository auf GitHub anlegen und hochladen …
Erscheint nur, wenn es noch kein Repository gibt.
Ihre Wahl:

\[ ] Neuen Ort angeben …
Erscheint nur, wenn der Ordner fehlt.
Ihre Wahl:

\[ ] Exe hinzufügen …
Erscheint nur, wenn es noch keinen Ordner Release gibt.
Ihre Wahl:

\[ ] Ordner in Repository und Release umbenennen …
Mein Vorschlag: nach „Weitere …“. Es wird nur einmal gebraucht.
Ihre Wahl: vorschlag

\[ ] Ordnernamen zurücksetzen …
Mein Vorschlag: nach „Weitere …“.
Ihre Wahl: vorschlag



## Zeile „Repository“

\[ ] README …
Ihre Wahl:

\[ ] Branches anzeigen …
Mein Vorschlag: mit „Branches verwalten …“ zusammenlegen. Zwei Aktionen mit fast gleichem Namen verwirren.
Ihre Wahl: vorschlag

\[ ] Branches verwalten …
Ihre Wahl:

\[ ] Repository-Ordner öffnen
Ihre Wahl:

\[ ] Auf GitHub öffnen
Ihre Wahl:

\[ ] Links …
Ihre Wahl:

\[ ] GitHub Actions …
Erscheint nur, wenn es Workflows gibt.
Ihre Wahl:

\[ ] Repository verwalten …
Ihre Wahl:

\[ ] Repository-Identität …
Mein Vorschlag: umbenennen in „Git-Name und E-Mail …“, so steht es auch in den Grundeinstellungen. Dann nach „Weitere …“.
Ihre Wahl: vorschlag

\[ ] Terminal …
Mein Vorschlag: nach „Weitere …“.
Ihre Wahl: vorschlag



## Zeile eines Branches (zum Beispiel „main“)

Hier stehen die meisten Aktionen. Mein Vorschlag für die Reihenfolge: Hochladen, Holen, Verlauf, dann der Rest.

\[ ] Änderungen auf GitHub hochladen …
Ihre Wahl:

\[ ] Änderungen von GitHub holen …
Ihre Wahl:

\[ ] Branch auf GitHub hochladen …
Erscheint nur bei einem neuen Branch.
Ihre Wahl:

\[ ] Auf GitHub hochladen …
Erscheint nur, wenn das Projekt noch nicht auf GitHub ist. Mein Vorschlag: umbenennen in „Erstmals auf GitHub hochladen …“, damit es sich von „Änderungen auf GitHub hochladen …“ unterscheidet.
Ihre Wahl:

\[ ] Konflikte lösen …
Erscheint nur bei Konflikten.
Ihre Wahl:

\[ ] Pull Request erstellen …
Ihre Wahl:

\[ ] Pull Requests …
Mein Vorschlag: mit „Pull-Requests-Übersicht …“ zusammenlegen. Die beiden Namen unterscheiden sich kaum.
Ihre Wahl: vorschlag

\[ ] Pull-Requests-Übersicht …
Ihre Wahl:

\[ ] Verlauf …
Ihre Wahl:

\[ ] Hochladeverlauf …
Mein Vorschlag: nach „Weitere …“.
Ihre Wahl: vorschlag

\[ ] Änderungen beiseitelegen …
Mein Vorschlag: nach „Weitere …“.
Ihre Wahl: vorschlag

\[ ] Beiseitegelegte Änderungen …
Mein Vorschlag: nach „Weitere …“.
Ihre Wahl: vorschlag

\[ ] Änderungen verwerfen …
Ihre Wahl:

\[ ] Branch-Ordner öffnen
Ihre Wahl:

\[ ] Ordner für Branches einrichten …
Erscheint nur einmal pro Projekt. Mein Vorschlag: nach „Weitere …“.
Ihre Wahl:

\[ ] Mit vorhandenem Repository verbinden …
Mein Vorschlag: nach „Weitere …“.
Ihre Wahl: vorschlag

\[ ] Virtuelle Umgebung neu anlegen …
Mein Vorschlag: nach „Weitere …“.
Ihre Wahl: vorschlag

\[ ] Exe aus diesem Branch erstellen …
Mein Vorschlag: umbenennen in „Exe aus dem Branch erstellen …“, so heißt es auch auf der Release-Zeile.
Ihre Wahl: vorschlag

\[ ] In main überführen oder verwerfen, Exe-Bau abschließen …
Erscheint nur beim Branch Cockpit-exe-bauen. Mein Vorschlag: umbenennen in „Exe-Bau abschließen …“, wie auf der Exe-Zeile.
Ihre Wahl:

\[ ] Terminal …
Mein Vorschlag: nach „Weitere …“.
Ihre Wahl: vorschlag



## Zeile „Exe“ (die Exe aus main)

\[ ] Exe starten
Ihre Wahl:

\[ ] Exe aus dem Code erstellen …
Ihre Wahl:

\[ ] Exe-Bau abschließen …
Erscheint nur, wenn ein Exe-Bau offen ist.
Ihre Wahl:

\[ ] Exe veröffentlichen …
Ihre Wahl:

\[ ] Exe-Ordner öffnen
Ihre Wahl:

\[ ] Exe-Einstellungen …
Ihre Wahl:

\[ ] Release einlesen …
Mein Vorschlag: umbenennen in „Exe aus einem Release holen …“. „Einlesen“ sagt nicht, was passiert.
Ihre Wahl: vorschlag

\[ ] Links der Exe …
Ihre Wahl:

\[ ] Wie funktioniert die Exe? …
Mein Vorschlag: nach „Weitere …“ oder in die Hilfe (F1).
Ihre Wahl: vorschlag

\[ ] Terminal …
Mein Vorschlag: weg. Im Ordner einer Exe braucht man selten ein Terminal.
Ihre Wahl: zu weitere



## Zeile „Release“ (alle Releases des Projekts)

\[ ] Releases auf GitHub …
Ihre Wahl:

\[ ] Release-Ordner öffnen
Ihre Wahl:

\[ ] Release für Branch aus Repository erstellen …
Mein Vorschlag: umbenennen in „Exe für einen Branch erstellen …“. Der jetzige Name ist schwer zu verstehen.
Ihre Wahl: vorschlag

\[ ] Release veröffentlichen …
Ihre Wahl:

\[ ] Release entfernen …
Ihre Wahl:

\[ ] Terminal …
Mein Vorschlag: weg.
Ihre Wahl: vorschlag



## Zeile eines einzelnen Releases (zum Beispiel ein Branch mit Exe)

\[ ] Exe starten
Ihre Wahl:

\[ ] Exe-Ordner öffnen
Ihre Wahl:

\[ ] Exe aus dem Branch erstellen …
Ihre Wahl:

\[ ] In main überführen oder verwerfen, Exe-Bau abschließen …
Erscheint nur beim Branch Cockpit-exe-bauen. Mein Vorschlag: umbenennen in „Exe-Bau abschließen …“.
Ihre Wahl:

\[ ] Release entfernen …
Mein Vorschlag: umbenennen in „Dieses Release entfernen …“, damit es sich von dem auf der Zeile „Release“ unterscheidet.
Ihre Wahl: vorshclag

\[ ] Terminal …
Mein Vorschlag: weg.
Ihre Wahl: vorschlag



## Projekte nur auf GitHub (noch nicht heruntergeladen)

\[ ] Herunterladen
Ihre Wahl:

\[ ] Auf GitHub öffnen
Ihre Wahl:

\[ ] Aus der Liste entfernen …
Ihre Wahl:

\[ ] Repository löschen …
Ihre Wahl:



## Branches nur auf GitHub

\[ ] Herunterladen
Ihre Wahl:

\[ ] Auf GitHub öffnen
Ihre Wahl:



## Oberste Einträge der Projektliste

\[ ] Projekt vom Rechner hinzufügen …
Ihre Wahl:

\[ ] Projekt von GitHub herunterladen …
Ihre Wahl:

\[ ] Anzeigen …
Mein Vorschlag: umbenennen in „Liste filtern …“.
Ihre Wahl: vorschlag



## Projektsammlungen

\[ ] Neue Projektsammlung …
Ihre Wahl:

\[ ] Projekte für die Sammlung …
Ihre Wahl:

\[ ] Projektsammlung umbenennen …
Ihre Wahl:

\[ ] Projektsammlung auflösen …
Ihre Wahl:



## Was Ihnen sonst auffällt

Hier ist Platz für alles andere: Reihenfolge, fehlende Aktionen, Menüs, Tastenkürzel.

Ihre Anmerkungen:



Also mein Programm soll ja den Vorteil haben, dass man schnelaktionen hat, aber überall noch das terminal. was den pfad dorthin hat, wo man sich gerade befindet, repository, release etc. und bei release bauen, kann man ja auch mit terminal machen. ich habe bei terminal immer orschlag ausgewählt. bin mir aber nicht sicher, bei exe bauen oder so, wäre es vllt. noch ganz nützlich. und bei repository ja auch. denn gerade dort decke ich ja nur Grundfunktionen ab. oder?
was meinst du? ich will das terminal ja auch nicht mal bei weitere und mal direkt dort haben. deswegen hätte ich gedacht, einfach immer in die liste ganz oben packen oder so. denn das macht mien Programm ja aus, die felxiilität. und wer das terminal lieber mag, aber gerne diese übersicht von dem Programm, der kann das auch nutzen, ohne noch immer weitere zu suchen etc. 

