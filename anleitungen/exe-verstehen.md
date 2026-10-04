# Wie funktioniert die Exe?

## Wozu eine Exe?

Eine Exe ist Ihr Programm als Datei für Windows. Andere starten sie mit einem Doppelklick oder mit Enter, ohne Python zu installieren.

Im Cockpit hat ein Projekt dafür neben „Code“ den Eintrag „Exe“. Er gehört zum Ordner Exe im Projektordner.

## Den Eintrag Exe bekommen

Fehlt der Eintrag, wählen Sie auf der Projektzeile „Exe hinzufügen …“. Das Cockpit legt den Ordner Exe an. Danach steht „Exe“ unter „Code“.

## Woher die Exe kommt

Es gibt drei Wege. Die Zeile Exe nennt, welcher es war.

1. Vom Cockpit erstellt: „Exe aus dem Code erstellen …“ baut die Exe mit PyInstaller. Dafür braucht es das Feature Exe-Erstellung und Python auf dem Rechner. Wie das geht, steht unten unter „Exe aus dem Code erstellen“.
2. Extern erstellt: „Exe einlesen …“, dann „Exe-Datei wählen …“ übernimmt eine Exe, die Sie woanders gebaut oder bekommen haben. Das Cockpit kopiert sie in den Ordner Exe.
3. Aus dem Release: „Exe einlesen …“, dann „Exe aus einem Release wählen …“ lädt die Exe des neuesten Releases auf GitHub herunter. Praktisch bei Projekten anderer Personen.

## Exe aus dem Code erstellen

Das Cockpit führt Sie Schritt für Schritt. Jeder Schritt hat „Zurück“ und „Abbrechen“.

1. Dateien neben der Exe: Sie wählen, welche Ordner und Dateien neben der Exe liegen sollen. Was der Code unbedingt braucht, ist angehakt. README und Lizenz kommen immer mit.
2. Mit oder ohne KI: Das kommt nur, wenn eine Text-KI eingerichtet ist. Empfohlen ist mit KI, weil die KI versuchen kann, Probleme zu lösen.
3. Einrichtung: Das Cockpit legt den Branch „Cockpit-exe-bauen“ an und speichert dort die Einstellungen. Main bleibt unverändert. Mit KI liest die KI den Code und schlägt Änderungen vor.
4. Zusammenfassung: Hier steht, was passiert. Mit „Mit KI schreiben“ öffnen Sie ein Feld für Fragen an die KI. Die KI antwortet erst in Sätzen und zeigt danach Code, wenn er hilft. „Exe erstellen“ startet den Bau.
5. Der Bau: Die Ausgabe steht Zeile für Zeile im Fenster.
6. Ergebnis: Klappt etwas nicht, wählen Sie „Problem mit KI lösen“ (nur mit KI), „Neuer Versuch, Exe zu bauen“, „Zurück“ oder „Abbrechen“. Klappt alles, wählen Sie „Erst testen, später in main überführen und Release veröffentlichen“, „Jetzt in main überführen und Release veröffentlichen“ oder „Jetzt in main überführen, später veröffentlichen“.

„Erst testen“ öffnet den Ordner der neuen Exe im Explorer. Wenn sie passt, wählen Sie bei Exe „Exe-Bau abschließen …“. Dort überführen Sie den Branch in main oder verwerfen ihn.

„Abbrechen“ löscht den Branch wieder. Main bleibt dann, wie es war.

Fehlen README oder Lizenz, warnt das Cockpit vor dem Bau und vor dem Veröffentlichen. „Jetzt hinzufügen“ springt beim Projekt zur Aktion „README …“ oder „Lizenz …“.

## Ordner neben der Exe

Jede Exe hat im Ordner Exe einen eigenen Ordner, zum Beispiel Exe\VokabelApp. Die Exe aus dem Branch liegt in Exe\VokabelApp_branch_Cockpit-exe-bauen. Darin liegen die Exe, README, Lizenz und die Ordner neben der Exe.

Manche Programme brauchen Ordner neben der Exe, zum Beispiel Meine-Vokabeln. Sie wählen sie im ersten Schritt oder in „Exe-Einstellungen …“ in der Liste „Ordner und Dateien neben der Exe“. Was der Code benutzt, ist angehakt. Einen neuen Ordner fügen Sie mit „Neuer Ordner neben der Exe“ hinzu. Er wird neben der Exe leer angelegt. Beim Bau kopiert das Cockpit die gewählten Ordner neben die Exe. Ein Ordner, in dem schon Daten liegen, bleibt, wie er ist. So bleiben zum Beispiel eigene Vokabellisten erhalten. README und Lizenz sind dagegen immer die aktuellen aus dem Code.

Mit „Mit den Hinweisen wiederholen“ führt die KI die Einrichtung mit dem Gespräch noch einmal aus.

## Was die Zeile Exe sagt

- „noch keine Exe-Datei“: Der Ordner ist leer.
- „aktuell“: Das Cockpit hat die Exe aus dem jetzigen Stand des Codes gebaut.
- „älter als der Code“: Seit dem Bau gibt es neue Commits. Mit „Exe aus dem Code erstellen …“ bauen Sie neu.

## Was beim Bauen passiert

1. Das Cockpit legt eine eigene virtuelle Umgebung zum Bauen an und installiert die Bibliotheken aus requirements.txt und PyInstaller. Sie liegt nicht im Projekt, sondern an einem kurzen Ort unter %LOCALAPPDATA%\CodeCockpit\venvs. So bleiben die Pfade kurz. Ein Branch nutzt die Umgebung von main mit, wenn seine requirements.txt gleich ist.
2. PyInstaller baut die Exe in einem temporären Ordner. Die Ausgabe steht Zeile für Zeile im Fenster.
3. Das Cockpit startet die neue Exe zum Test. Läuft sie 10 Sekunden ohne Absturz, ist der Test bestanden.
4. Erst dann kommt die bisherige Exe in die Sicherheitskopien (Menü Datei, Sicherheitskopien), und die neue ersetzt sie.

Klappt etwas nicht, bleibt die bisherige Exe, wie sie war.

In die Exe kommt nur, was Ihre Startdatei wirklich importiert, dazu Dateien, die Sie in der .spec-Datei angeben. Tests und Beispieldaten bleiben draußen.

## Veröffentlichen

„Exe veröffentlichen …“ legt auf GitHub ein Release an, zum Beispiel Version 1.0.1. Das Cockpit schlägt die nächste Nummer vor. Die Versionshinweise schreiben Sie selbst oder mit „Vorschlag der KI“.

Hochgeladen wird der ganze Ordner der Exe als ZIP-Datei mit festem Namen, zum Beispiel VokabelApp.zip. Darin liegt der Ordner mit der Versionsnummer, zum Beispiel VokabelApp-1.0.1. So überschreibt beim Auspacken keine Version eine andere, und der Link auf die neueste Version bleibt immer gleich. README und Lizenz hängen zusätzlich einzeln am Release.

„Links der Exe …“ zeigt danach den Link zum Release und den Link zum Herunterladen der Exe. Enter kopiert den markierten Link.

## Warnung von Windows

Exe-Dateien ohne digitale Signatur lösen bei anderen oft die Warnung „Der Computer wurde durch Windows geschützt“ aus. Man startet sie mit „Weitere Informationen“ und dann „Trotzdem ausführen“.

## Einrichtung ohne KI

Diese Einrichtung prüft, ob sich die Exe künftig ohne Handarbeit bauen lässt: ob die .spec-Datei und die Startdatei da sind, ob alle Bibliotheken in requirements.txt stehen, ob die Versionen fest sind und ob die Exe zu groß ist.

## Lange Pfade

Windows erlaubt ohne Zusatzeinstellung nur Pfade bis 260 Zeichen. Einige Bibliotheken wie PySide6 haben sehr tief verschachtelte Dateien. Liegt ein Projekt tief, scheitert dann das Installieren. Das Cockpit bietet in diesem Fall an, lange Pfade einzuschalten. Windows fragt dafür einmal nach Administratorrechten.

Von Hand geht es so: Windows-Taste, „PowerShell“ eingeben, „Als Administrator ausführen“. Dann diesen Befehl eingeben und mit Enter bestätigen:

New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name LongPathsEnabled -Value 1 -PropertyType DWORD -Force
