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
- KI-Features in der Feature-Verwaltung als ein Eintrag „KI“ mit Unterpunkten, sobald es mehr als ein KI-Feature gibt (ab 8c).
- Sprach-KI in der KI-Verwaltung kommt mit der Spracheingabe in 8d.


## Geheimnis in einem früheren Commit (aus Phase 5b)

Findet die Sicherheitsprüfung ein Geheimnis in einem Commit, der noch nicht hochgeladen ist, stoppt sie das Hochladen. Bereinigen geht bisher nur im Terminal. Idee für später: die noch nicht hochgeladenen Commits zu einem neuen Commit ohne das Geheimnis zusammenfassen. Das ist erlaubt, weil diese Commits noch nicht auf der Plattform sind. Es ist kein force push.
