# Python installieren

Zum Bauen einer Exe braucht das Cockpit Python auf Ihrem Rechner. Die fertige Exe braucht später kein Python mehr.

## Weg 1: mit winget

1. Öffnen Sie im Cockpit ein Terminal, zum Beispiel mit „Terminal …“ auf einer Projektzeile.
2. Geben Sie ein: winget install Python.Python.3.12
3. Drücken Sie Enter und warten Sie, bis „Fertig.“ kommt.
4. Starten Sie das Cockpit neu.

## Weg 2: von der Webseite

1. Öffnen Sie im Browser die Seite python.org/downloads.
2. Laden Sie die Version für Windows herunter und starten Sie sie.
3. Wichtig: Kreuzen Sie im ersten Fenster „Add python.exe to PATH“ an.
4. Wählen Sie „Install Now“.

## Prüfen

Im Terminal des Cockpits: py --version

Kommt eine Versionsnummer wie „Python 3.12.7“, ist alles bereit.
