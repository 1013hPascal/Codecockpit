# Git für Windows installieren

CodeCockpit braucht Git für Windows. Ohne Git kann es keine Änderungen hochladen oder holen.

Git für Windows bringt auch den Git Credential Manager mit. Damit klappt die Anmeldung in Firmen mit Single Sign-On.

Es gibt drei Wege. Nehmen Sie den ersten, der bei Ihnen funktioniert.

Tipp: In CodeCockpit kopiert Strg+C die markierte Zeile. So können Sie die Befehle unten kopieren und in PowerShell mit Strg+V einfügen.


## Weg 1: mit winget

winget ist in Windows 10 und 11 meistens schon vorhanden.

1. Drücken Sie die Windows-Taste, tippen Sie „PowerShell“ und drücken Sie Enter.
2. Geben Sie diesen Befehl ein und drücken Sie Enter:
   `winget install --id Git.Git -e --source winget`
3. Beim ersten Mal fragt winget, ob Sie den Bedingungen zustimmen. Tippen Sie „J“ oder „Y“ und drücken Sie Enter.
4. Windows fragt eventuell, ob das Programm Änderungen vornehmen darf. Wählen Sie „Ja“.
5. Warten Sie, bis „Erfolgreich installiert“ erscheint.
6. Schließen Sie die PowerShell und starten Sie CodeCockpit neu.

Meldet PowerShell, dass winget unbekannt ist, nehmen Sie Weg 2 oder Weg 3.


## Weg 2: mit Chocolatey

Nur wenn Chocolatey schon installiert ist.

1. Drücken Sie die Windows-Taste und tippen Sie „PowerShell“.
2. Drücken Sie Strg+Umschalt+Enter. Damit startet PowerShell als Administrator. Bestätigen Sie die Rückfrage mit „Ja“.
3. Geben Sie diesen Befehl ein und drücken Sie Enter:
   `choco install git -y`
4. Warten Sie, bis die Installation fertig ist.
5. Schließen Sie die PowerShell und starten Sie CodeCockpit neu.


## Weg 3: über die Webseite

1. Öffnen Sie im Browser diese Seite:
   https://git-scm.com/downloads/win
2. Laden Sie den Installer für „64-bit Git for Windows Setup“ herunter.
3. Starten Sie die heruntergeladene Datei und bestätigen Sie die Rückfrage von Windows mit „Ja“.
4. Der Installer hat viele Seiten. Die Voreinstellungen passen. Drücken Sie jeweils Enter für „Next“, am Ende für „Install“ und „Finish“.
5. Starten Sie CodeCockpit neu.


## Prüfen, ob es geklappt hat

1. Öffnen Sie eine neue PowerShell.
2. Geben Sie diesen Befehl ein und drücken Sie Enter:
   `git --version`
3. Erscheint eine Zeile wie „git version 2.55.0.windows.3“, ist Git installiert.

Erscheint eine Fehlermeldung, melden Sie sich bei Windows ab und wieder an. Windows kennt neue Programme manchmal erst danach.
