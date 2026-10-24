# Plan: Optik des Cockpits

Stand: 22.10.2026. Ziel: Sehende finden sich schnell zurecht, ohne dass sich für Screenreader und Braillezeile etwas verschlechtert.

Umsetzung: Alle acht Schritte sind gebaut (22.10.2026). Tests stehen in tests/test_optik.py, die Checkliste in checklisten/optik.md. Offen ist nur das Symbol der Exe: Dafür braucht es eine .ico-Datei.

## Grundregeln

- Barrierefreiheit hat Vorrang. Was NVDA ansagt und die Braillezeile zeigt, bleibt genau gleich. Alles Neue ist nur zusätzlich für das Auge.
- Keine festen Farben. Alle Farben kommen aus dem Windows-Thema, also aus der Palette von Qt, hell und dunkel.
- Keine Information nur über Farbe oder Zeichen. Was ein Zeichen zeigt, steht auch im Text.
- Keine neue Bibliothek. Alles geht mit Qt.
- Wenige Bilder zum Prüfen: nur dort, wo sich etwas sichtbar ändert. Die Bilder entstehen unsichtbar, ohne Fenster auf dem Bildschirm.

## Was die Bilder zeigen (Bestand)

Ich habe fünf Bilder gemacht: das Hauptfenster, das Hauptfenster mit aufgeklapptem Projekt, die Einrichtung, die Feature-Verwaltung und die Neuigkeiten.

Gut ist:

- Der Stil von Windows 11 wirkt modern und ruhig. Kästchen, Knöpfe und Auswahlfelder sehen sauber aus.
- Die Schrift ist gut lesbar, und die Zeilen haben genug Abstand.
- Die Knöpfe stehen überall gleich: nach vorn links, Schließen oder Abbrechen rechts.

Probleme:

1. **Hauptfenster ohne Gliederung.** Die Zeilen unter einem Projekt (Repository, Code und so weiter) stehen genauso weit links wie die Projekte. Sehende erkennen nicht, was zu Tagebuch gehört und was das nächste Projekt ist. „ausgeklappt“ steht nur als Wort da, ein Pfeil fehlt.
2. **Die Aktionen sind so breit wie die Projekte.** Rechts bleibt viel leere weiße Fläche.
3. **Alles in einer Zeile, alles gleich stark.** Projektname, Zustand und Zeit sehen gleich aus. Bei den Neuigkeiten springt der Projektname nicht ins Auge.
4. **Der Fokus ist schwach zu sehen.** Nur ein dünner blauer Strich links und ein hellgrauer Hintergrund. Hat ein anderes Fenster den Fokus, ist die Markierung kaum zu erkennen.
5. **Erklärungen sehen aus wie Auswahllisten.** In der Einrichtung wirkt der Text wie eine Liste zum Anklicken, mit Rahmen und hervorgehobener Zeile. Für die Braillezeile ist die Liste richtig, für das Auge wirkt sie verwirrend.
6. **Gruppen sind nicht als Gruppen zu erkennen.** In der Feature-Verwaltung steht „KI, 5 von 5 KI-Features eingeschaltet“ zwischen den Features und sieht fast gleich aus.
7. **Keine Symbole.** Menüs, Aktionen und Knöpfe haben keine Bilder. Das Programm hat kein eigenes Programmsymbol in der Taskleiste.

## Schritte

Jeder Schritt hat eigene Tests und einen Punkt in der Checkliste. Nach jedem Schritt mache ich höchstens ein bis zwei Bilder.

### Schritt 1: Gliederung im Hauptfenster

- Zeilen unter einem Projekt werden eingerückt, je Ebene etwa 24 Pixel.
- Vor jedem Projekt steht ein Pfeil: nach rechts für zugeklappt, nach unten für ausgeklappt. Er wird gemalt, die Ansage bleibt „Tagebuch, ausgeklappt“.
- Projekte erscheinen fett, die Zeilen darunter normal.
- Umsetzung: ein eigener Zeichner (QStyledItemDelegate) für die Projektliste. Der Text der Zeile und ihr Accessible Name ändern sich nicht.

### Schritt 2: Schmalere Aktionen und Bereich „Stand“ nur für das Auge

- Die Aktionen werden schmaler, etwa ein Drittel der Breite. Die Projektliste bekommt mehr Platz für ihre langen Zeilen.
- Unter den Aktionen steht der Bereich „Stand“. Er zeigt genau die Angaben der Projektzeile, eine pro Zeile, zum Beispiel „aktualisiert am 18.09.2026“ und „3 Dateien noch nicht hochgeladen“.
- Entscheidung (Nutzer: „was du besser findest“, 22.10.2026): nur für das Auge. Tab überspringt den Bereich, es gibt keine Ansage. Grund: Für Screenreader und Braillezeile steht alles schon in der Projektzeile. Es gibt nichts, was nur im Bereich steht. Neue Angaben kommen zuerst in die Projektzeile.
- Hinweis zu den Bildern: Dort fehlte der Stand, weil er im Hintergrund ermittelt wird. Für die nächsten Bilder warte ich darauf.

### Schritt 3: Zweite Textebene in Listen

- Im Zeichner wird der erste Teil einer Zeile fett, zum Beispiel der Projektname bei den Neuigkeiten.
- Der Teil nach dem letzten Komma wird in der gedämpften Farbe des Themas gezeigt, zum Beispiel die Zeit „heute 18:03“.
- Der Text bleibt dieselbe eine Zeile, Ansage und Braillezeile ändern sich nicht.
- Erst in der Projektliste, bei den Neuigkeiten und in der Aktivität, dann in den anderen Listen.

### Schritt 4: Deutlicher Fokus

- Die markierte Zeile bekommt die Hervorhebungsfarbe des Themas und einen Rahmen von 2 Pixeln, auch wenn das Fenster nicht aktiv ist.
- Knöpfe, Felder und Kästchen bekommen mit Fokus einen deutlichen Rahmen in der Akzentfarbe.
- Umsetzung über ein kleines Stylesheet, das nur Farben aus der Palette nutzt (palette(highlight)).

### Schritt 5: Erklärungen sehen aus wie Text

- Listen mit Erklärungen (Einrichtung, Einzelheiten, Hilfe) bekommen keinen Rahmen und den Hintergrund des Fensters. Die markierte Zeile ist nur dezent hervorgehoben.
- Für den Screenreader bleibt es eine Liste mit einer Zeile pro Satz.

### Schritt 6: Gruppen und Überschriften

- Gruppenzeilen wie „KI, 5 von 5 KI-Features eingeschaltet“ werden fett und haben oben mehr Abstand.
- Dasselbe gilt für Sammlungen in der Projektliste.

### Schritt 7: Symbole

- Es kommt ein Programmsymbol für Fenster und Taskleiste dazu, auch in der Exe.
- Einige Symbole stammen aus dem Windows-Stil (QStyle.standardIcon), zum Beispiel Ordner öffnen, Hilfe, Warnung und Neu laden. Sie kosten nichts und passen zum hellen und dunklen Thema.
- Symbole bekommen keinen eigenen Namen für den Screenreader.
- Programmsymbol: vorerst die Buchstaben CC, gemalt mit Qt. Es lässt sich später leicht austauschen.

### Schritt 8: Dunkles Thema und große Schrift prüfen

- Je ein Bild im dunklen Thema und mit 150 Prozent Skalierung.
- Ich prüfe, ob Text abgeschnitten wird, ob Kontraste reichen und ob Rahmen zu sehen sind.

## Wie ich prüfe

- Automatische Tests prüfen, dass Texte und Accessible Names gleich bleiben. Sie prüfen auch, dass keine feste Farbe im Code steht.
- Die Bilder entstehen mit einem Skript im Scratchpad, unsichtbar. Insgesamt etwa 10 bis 15 Bilder, nicht mehr.
- Die Checkliste für NVDA prüft vor allem, dass sich nichts verändert hat.
- Ideal wäre, wenn eine sehende Person am Schluss einmal draufschaut.

## Reihenfolge und Aufwand

Die Schritte 1, 2, 4 und 5 bringen am meisten und sind klein. Danach folgen 3, 6, 7 und 8.
