# Wie funktioniert die Exe?

## Wozu eine Exe?

Eine Exe ist Ihr Programm als eine einzige Datei für Windows. Andere starten sie mit einem Doppelklick oder mit Enter, ohne Python zu installieren.

Im Cockpit hat ein Projekt dafür neben „Code“ den Eintrag „Exe“. Er gehört zum Ordner Exe im Projektordner.

## Den Eintrag Exe bekommen

Fehlt der Eintrag, wählen Sie auf der Projektzeile „Exe hinzufügen …“. Das Cockpit legt den Ordner Exe an. Danach steht „Exe“ unter „Code“.

## Woher die Exe kommt

Es gibt drei Wege. Die Zeile Exe nennt, welcher es war.

1. Vom Cockpit erstellt: „Exe aus dem Code erstellen …“ baut die Exe mit PyInstaller. Dafür braucht es das Feature Exe-Erstellung und Python auf dem Rechner. Zuerst wählen Sie „Exe mit KI einrichten …“ oder „Exe ohne KI einrichten …“. Danach sehen Sie das Ergebnis und wählen „Exe erstellen“ oder „Abbrechen“.
2. Extern erstellt: „Exe einlesen …“, dann „Exe-Datei wählen …“ übernimmt eine Exe, die Sie woanders gebaut oder bekommen haben. Das Cockpit kopiert sie in den Ordner Exe.
3. Aus dem Release: „Exe einlesen …“, dann „Exe aus einem Release wählen …“ lädt die Exe des neuesten Releases auf GitHub herunter. Praktisch bei Projekten anderer Personen.

## Einrichten mit KI

Die KI ändert nie direkt main. Ihre Änderungen kommen in den Branch „Cockpit-exe-bauen“. Das Cockpit baut die Exe aus diesem Branch und legt sie als eigene Datei neben die normale Exe. Klappt der Test, wählen Sie: selbst testen und später in main übernehmen, jetzt übernehmen und den Branch behalten, oder jetzt übernehmen und den Branch löschen. So geht main nie kaputt.

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

„Exe veröffentlichen …“ legt auf GitHub ein Release an, zum Beispiel Version 1.0.1, und hängt die Exe an. Das Cockpit schlägt die nächste Nummer vor. Die Versionshinweise schreiben Sie selbst oder mit „Vorschlag der KI“.

„Links der Exe …“ zeigt danach den Link zum Release und den Link zum Herunterladen der Exe. Enter kopiert den markierten Link.

## Warnung von Windows

Exe-Dateien ohne digitale Signatur lösen bei anderen oft die Warnung „Der Computer wurde durch Windows geschützt“ aus. Man startet sie mit „Weitere Informationen“ und dann „Trotzdem ausführen“.

## Exe ohne KI einrichten

Diese Einrichtung prüft, ob sich die Exe künftig ohne Handarbeit bauen lässt: ob die .spec-Datei und die Startdatei da sind, ob alle Bibliotheken in requirements.txt stehen, ob die Versionen fest sind und ob die Exe zu groß ist.

## Lange Pfade

Windows erlaubt ohne Zusatzeinstellung nur Pfade bis 260 Zeichen. Einige Bibliotheken wie PySide6 haben sehr tief verschachtelte Dateien. Liegt ein Projekt tief, scheitert dann das Installieren. Das Cockpit bietet in diesem Fall an, lange Pfade einzuschalten. Windows fragt dafür einmal nach Administratorrechten.

Von Hand geht es so: Windows-Taste, „PowerShell“ eingeben, „Als Administrator ausführen“. Dann diesen Befehl eingeben und mit Enter bestätigen:

New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name LongPathsEnabled -Value 1 -PropertyType DWORD -Force
