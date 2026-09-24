# Git für Windows installieren

CodeCockpit braucht Git für Windows. Ohne Git kann es keine Änderungen hochladen oder holen.

Git für Windows bringt auch den Git Credential Manager mit. Damit klappt die Anmeldung in Firmen mit Single Sign-On.

Es gibt drei Wege. Nimm den ersten, der bei dir funktioniert.


## Weg 1: mit winget

winget ist in Windows 10 und 11 meistens schon vorhanden.

1. Drücke die Windows-Taste, tippe „PowerShell“ und drücke Enter.
2. Tippe diesen Befehl und drücke Enter:
   `winget install --id Git.Git -e --source winget`
3. Beim ersten Mal fragt winget, ob du den Bedingungen zustimmst. Tippe „J“ oder „Y“ und drücke Enter.
4. Windows fragt eventuell, ob das Programm Änderungen vornehmen darf. Wähle „Ja“.
5. Warte, bis „Erfolgreich installiert“ erscheint.
6. Schließe die PowerShell und starte CodeCockpit neu.

Meldet PowerShell, dass winget unbekannt ist, nimm Weg 2 oder Weg 3.


## Weg 2: mit Chocolatey

Nur wenn Chocolatey schon installiert ist.

1. Drücke die Windows-Taste und tippe „PowerShell“.
2. Drücke Strg+Umschalt+Enter. Damit startet PowerShell als Administrator. Bestätige die Rückfrage mit „Ja“.
3. Tippe diesen Befehl und drücke Enter:
   `choco install git -y`
4. Warte, bis die Installation fertig ist.
5. Schließe die PowerShell und starte CodeCockpit neu.


## Weg 3: über die Webseite

1. Öffne im Browser die Seite https://git-scm.com/downloads/win
2. Lade den Installer für „64-bit Git for Windows Setup“ herunter.
3. Starte die heruntergeladene Datei und bestätige die Rückfrage von Windows mit „Ja“.
4. Der Installer hat viele Seiten. Die Voreinstellungen passen. Drücke jeweils Enter für „Next“, am Ende „Install“ und „Finish“.
5. Starte CodeCockpit neu.


## Prüfen, ob es geklappt hat

1. Öffne eine neue PowerShell.
2. Tippe `git --version` und drücke Enter.
3. Erscheint eine Zeile wie „git version 2.51.0.windows.1“, ist Git installiert.

Erscheint eine Fehlermeldung, melde dich ab und wieder an. Windows kennt neue Programme manchmal erst danach.
