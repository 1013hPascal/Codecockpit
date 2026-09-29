# Releases

Ein Release ist eine veröffentlichte Version Ihres Projekts auf GitHub, mit Versionshinweisen und auf Wunsch mit einer Exe zum Herunterladen.

Setzen Sie beim Hochladen eine neue Version, fragt das Cockpit danach: „Für Version 1.4.0 ein Release auf GitHub anlegen?“ Vorgabe ist „Später“. Ist die Exe-Erstellung aktiv, kommt die Exe mit. Sonst hängt GitHub nur den Quellcode als ZIP-Datei an. Die Versionshinweise schlägt die KI aus den Commits vor, Sie können sie vorher ändern.

Auf der Projektzeile steht „Releases …“. Die Liste zeigt Ihre Releases, neueste oben, mit Datum und Downloads. Mit Tab kommen Sie zu Versionshinweise ansehen, bearbeiten, Link kopieren, im Browser öffnen und löschen. Beim Löschen bleibt das Tag im Code.

Hat das Repository GitHub Actions, steht auf der Projektzeile auch „GitHub Actions …“. GitHub Actions sind kleine Programme, die GitHub selbst ausführt, zum Beispiel Tests nach jedem Hochladen. Die Liste zeigt die letzten Läufe. Bei einem fehlgeschlagenen Lauf zeigt „Fehler lesen“ das Ende der Ausgabe und eine Erklärung der KI. „Neu starten“ startet ihn noch einmal.

Ist der letzte Lauf fehlgeschlagen, steht das am Ende der Projektzeile.
