# Offene Punkte

Hier stehen Dinge, die bewusst auf später verschoben wurden. Erledigte Punkte werden gelöscht.


## Sprachausgabe in Dialogen (aus Phase 3, Stand 25.09.2026)

Problem: Ansagen aus Dialogen kommen bei NVDA nicht an. Im Hauptfenster funktionieren sie, zum Beispiel „Ausgeklappt, 2 Unterordner.“ Meldungsfenster mit OK werden zuverlässig vorgelesen.

Offene Prüfpunkte in `checklisten\phase-03.md`:

- 42: Automatisch sperren mit Meldung
- 43: Ansage beim Entsperren
- 44: Ansagen in anderen Dialogen, zum Beispiel „Konto gelöscht“
- 45 bis 47: Nachtest zur letzten Änderung, noch nicht getestet

Bisher versucht:

1. Ansage an das Steuerelement mit dem Fokus statt fest an das Hauptfenster. Ergebnis: weiter stumm.
2. Jede Ansage etwa eine halbe Sekunde verzögert, damit ein Fokuswechsel sie nicht abbricht. Noch nicht getestet (Punkte 45 bis 47).

Ideen für später:

- Mit dem NVDA-Log oder der NVDA-Python-Konsole prüfen, ob die UIA-Benachrichtigung überhaupt ankommt.
- Wichtige Rückmeldungen in Dialogen als Meldungsfenster mit OK, das funktioniert sicher.
- Alternative: Text in ein Statusfeld im Dialog schreiben, das NVDA als Live-Region liest.


## KI (aus Phase 8b)

- Zusätzliche Header für Firmen-Gateways beim OpenAI-kompatiblen Konto (Konzept 11). Kommen, sobald jemand sie braucht, spätestens in Phase 15.
- Sprach-KI in der KI-Verwaltung: mit 8d gebaut (Whisper lokal). Externe Sprach-KI fehlt noch.


## Exe (aus Phase 10)

- Intelligente App-Steuerung (Smart App Control) von Windows 11 blockiert selbst gebaute Exe-Dateien ohne Signatur, auch bei anderen Nutzern. Auf dem Rechner des Nutzers ist sie an. Lösungen: sie ausschalten (lässt sich danach nicht wieder einschalten, ohne Windows neu aufzusetzen) oder die Exe signieren (Zertifikat nötig). Entscheidung des Nutzers offen.
  - Recherche vom 02.10.2026, Möglichkeiten zum Signieren: Microsoft Artifact Signing (früher Trusted Signing, 9,99 Dollar im Monat) gibt es für Privatpersonen nur in den USA und Kanada, für den Nutzer also nicht. SignPath Foundation signiert Open-Source-Projekte kostenlos: öffentliches Repository, Bau über GitHub Actions, Seite „Code signing policy“ mit Datenschutzerklärung, Zwei-Faktor-Anmeldung, Freigabe jedes Releases, ein Antrag pro Projekt, Herausgeber ist „SignPath Foundation“. Certum Open Source Code Signing für etwa 50 Dollar im Jahr, mit eigenem Namen, nur für Open Source. Normales OV-Zertifikat für etwa 200 bis 300 Dollar im Jahr, auch für private Programme.
  - Smart App Control prüft auch die mitgepackten DLLs. Ob eine signierte Exe von PyInstaller mit PySide6 ganz durchgeht, erst mit der ersten Signatur ausprobieren.
  - Ein anderes Werkzeug statt PyInstaller (Nuitka, cx_Freeze) hilft dagegen nicht, auch deren Exe ist unsigniert.
- Bauart „Programmordner mit Python“ (Idee vom 02.10.2026): statt einer Exe die offizielle, signierte Python-Version zum Mitliefern (embeddable package), die Bibliotheken und den Code in einen Ordner, gestartet über eine Verknüpfung auf pythonw.exe. Läuft ohne eigene Signatur auch mit Smart App Control, wie heute start.bat beim Cockpit. Zuerst an der Vokabel-App ausprobieren.
- Installer mit NSIS (Nullsoft Scriptable Install System, Idee vom 02.10.2026, Hinweis eines Bekannten des Nutzers): baut eine setup.exe mit Installation unter „Programme“, Startmenü, Desktop-Verknüpfung und Deinstallation in den Windows-Einstellungen. Hilft allein nicht gegen Smart App Control, weil auch der Installer unsigniert ist. Sinnvoll zusammen mit einer Signatur oder für die Bauart „Programmordner mit Python“.
- Updater (10e, Rückmeldung des Nutzers vom 29.09.2026): Der Neustart nach dem Update klappte nicht. Das Austausch-Skript hatte doppelte Zeilenenden, startete ohne Konsole (daher das leere Fenster mit dem Titel find) und gab bei gesperrter Exe sofort auf. Im Branch Spracheingabe behoben, mit echtem Test. 10e erst abhaken, wenn der Nutzer es bestätigt.
- Zweite Runde für die Oberfläche (Wunsch des Nutzers vom 29.09.2026): Nach den weiteren Features alle Knöpfe und Aktionen durchgehen. Viele sind unintuitiv benannt oder stehen in einer seltsamen Reihenfolge.
- Test-Absturz (28.09.2026): tests/test_phase10.py::test_build_dialog_asks_when_blocked[True] bricht manchmal mit „Fatal Python error: Aborted“ in Qt ab, etwa bei jedem zweiten Lauf. Die übrigen Tests laufen durch. Das Warten auf den Thread vor deleteLater hat es nicht behoben. Ursache noch suchen. Beim Gesamttest vom 03.10.2026 brach auch tests/test_exe_ki_und_branches.py einmal so ab, fünf Wiederholungen danach liefen durch. Vermutlich dieselbe Ursache: ein Bau-Fenster mit Aufgabe im Hintergrund wird beim Testende aufgeräumt.
- Externe Ressourcen, Lizenzprüfung und Signieren.
- GitHub Actions (Phase 14, 29.09.2026): Für die Prüfpunkte 9 bis 13 in checklisten\phase-14.md braucht ein Projekt einen Workflow. Später einen kleinen Test-Workflow für das Cockpit schreiben, der bei jedem Hochladen die Tests laufen lässt. Bis dahin sind diese Punkte nicht geprüft. Zusammen mit dem Signieren kann dort später auch die Exe in der Cloud gebaut werden.
- Nach dem Austausch der eigenen Exe: alte Version selbst wiederherstellen, wenn die neue nicht startet.


## Geheimnis in einem früheren Commit (aus Phase 5b)

Findet die Sicherheitsprüfung ein Geheimnis in einem Commit, der noch nicht hochgeladen ist, stoppt sie das Hochladen. Bereinigen geht bisher nur im Terminal. Idee für später: die noch nicht hochgeladenen Commits zu einem neuen Commit ohne das Geheimnis zusammenfassen. Das ist erlaubt, weil diese Commits noch nicht auf der Plattform sind. Es ist kein force push.
