# Fragen zu Phase 10: Exe

Stand: 27.09.2026. Das überarbeitete Konzept steht in KONZEPT.md unter 10.4 und 8.3.

So beantworten Sie die Fragen:

- Jede Frage beginnt mit [ ].
- Passt mein Vorschlag, schreiben Sie ein x in die Klammer: [x].
- Wollen Sie etwas anderes, schreiben Sie ein Ausrufezeichen hinein: [!]. Schreiben Sie Ihre Antwort hinter „Antwort:“.
- Ist etwas unklar, schreiben Sie ein Fragezeichen hinein: [?].

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Kurz: das neue Konzept

- Auf der Projektzeile gibt es „Exe hinzufügen …“. Danach steht „Exe“ unter „Code“.
- Die Zeile „Exe“ sagt, ob es schon eine Exe gibt, woher sie kommt und ob sie älter als der Code ist.
- Mit Tab kommen die Aktionen: Exe starten, Exe aus dem Code erstellen bzw. aktualisieren, Exe-Datei wählen, Exe veröffentlichen, Exe aus dem Release holen, Exe-Einrichtung prüfen, Exe-Ordner öffnen, Wie funktioniert die Exe?
- Das Cockpit merkt sich in cockpit.toml, woher die Exe kommt und aus welchem Stand des Codes sie gebaut wurde.
- PyInstaller kommt erst beim ersten Bauen in die virtuelle Umgebung des Projekts. Es steckt nicht im Cockpit.


## Fragen

[ ] 1. Aufteilung
Frage: Wie teilen wir Phase 10 auf?
Vorschlag: Vier Teilschritte mit eigener Checkliste.
- 10a: Eintrag Exe, Exe hinzufügen, Exe-Datei wählen, Zustand in cockpit.toml, Anleitung.
- 10b: Exe aus dem Code erstellen und aktualisieren, mit Start-Test und Sicherheitskopie.
- 10c: Exe veröffentlichen und aus dem Release holen.
- 10d: Die eigene Exe des Cockpits, mit Austausch beim Neustart, und Exe-Einrichtung prüfen.
Externe Ressourcen, Lizenzprüfung und Signieren kommen später. 8d, 8e und Phase 9 auch.
Antwort:

[ ] 2. Was ist Kern, was ist Feature?
Frage: Welche Teile kann man ausschalten?
Vorschlag: Eintrag Exe, Exe starten, Exe-Datei wählen, Exe aus dem Release holen und Exe-Ordner öffnen gehören zum Kern, sie brauchen nichts. Das Bauen ist das Feature „Exe-Erstellung“, für neue Projekte eingeschaltet. Veröffentlichen gehört ebenfalls zum Feature, weil man dafür eine gebaute Exe braucht. Wer nie baut, schaltet das Feature aus und hat trotzdem den Eintrag Exe.
Antwort:

[ ] 3. Python auf dem Rechner
Frage: Zum Bauen braucht das Cockpit Python, auch wenn es selbst als Exe läuft. Was, wenn Python fehlt?
Vorschlag: Wie bei Git: eine Anleitung „Python installieren“ im Menü Hilfe, mit dem Befehl für winget. „Exe aus dem Code erstellen“ sagt dann, warum es nicht geht, und bietet die Anleitung an. Auf Ihrem Rechner ist Python schon da.
Antwort:

[ ] 4. PyInstaller
Frage: Nach der Regel „keine neuen Bibliotheken ohne Rückfrage“: Darf PyInstaller dazukommen?
Vorschlag: Ja. Für Ihre Projekte installiert das Cockpit PyInstaller in die virtuelle Umgebung des Projekts (`Code\.venv`), nicht ins Cockpit. Für die eigene Exe des Cockpits (10d) kommt PyInstaller in die Umgebung des Cockpits, nur zum Bauen. Die .venv steht in .gitignore und wird nie hochgeladen.
Antwort:

[ ] 5. Erster Bau
Frage: Was fragt das Cockpit beim ersten Bauen?
Vorschlag: Ein kurzes Formular: Startdatei (Vorschlag main.py), Name der Exe (Vorschlag: Projektname), Bauart (eine Datei oder Programmordner, Vorgabe eine Datei), Programm ohne Konsolenfenster (Vorgabe ja), Symbol (freiwillig). Daraus entsteht die .spec-Datei im Code-Ordner. Später fragt es nicht mehr.
Antwort:

[ ] 6. Exe-Datei wählen
Frage: Was passiert, wenn Sie eine Exe von woanders wählen?
Vorschlag: Sie wird in den Ordner Exe kopiert, nicht verschoben. Eine bisherige Exe kommt vorher als Sicherheitskopie in den Ordner backups. Das Cockpit merkt sich „von Hand hinzugefügt am …“. Bei einem Programmordner wählen Sie den ganzen Ordner.
Antwort:

[ ] 7. Ist die Exe veraltet?
Frage: Wann sagt die Zeile „älter als der Code“?
Vorschlag: Nur bei Exe-Dateien, die das Cockpit selbst gebaut hat. Es vergleicht den Commit beim Bau mit dem jetzigen Stand. Bei Exe-Dateien von Hand oder aus einem Release nennt die Zeile nur Herkunft und Datum, weil das Cockpit dort nicht weiß, aus welchem Code sie stammen.
Antwort:

[ ] 8. Versionsnummer beim Veröffentlichen
Frage: Ein Release braucht eine Versionsnummer. Das Feature Versionen (Phase 9) kommt aber erst später. Woher kommt sie?
Vorschlag: „Exe veröffentlichen …“ fragt nach der Nummer und schlägt die nächste vor: nach 1.3.0 kommt 1.3.1, beim ersten Mal 1.0.0. Daraus wird der Git-Tag v1.3.1. Die Versionshinweise schreiben Sie selbst oder lassen sie mit „Vorschlag der KI“ schreiben. Phase 9 ersetzt die Frage später durch „Kleine Korrektur, Neue Funktion, Große Änderung“.
Antwort:

[ ] 9. Test nach dem Bau
Frage: Wie prüft das Cockpit die neue Exe?
Vorschlag: Zuerst nur der Start-Test: Die Exe startet, läuft sie nach 10 Sekunden noch, ist der Test bestanden, und das Cockpit beendet sie. Die Wartezeit ist in den Einstellungen des Features änderbar. Der Selbsttest mit --selbsttest kommt mit der Exe-Einrichtungsprüfung in 10d.
Antwort:

[ ] 10. Die eigene Exe des Cockpits
Frage: Wo liegt sie, und wie starten Sie sie?
Vorschlag: In `Codecockpit\Exe\CodeCockpit.exe`, wie bei jedem Projekt. start.bat und start_testdaten.bat bleiben zum Testen. Die Exe startet mit Ihren echten Daten. Mit `--testdaten` startet sie mit den Testdaten.
Antwort:

[ ] 11. Exe wieder entfernen
Frage: Braucht es eine Aktion, die den Ordner Exe wieder entfernt?
Vorschlag: Nein, vorerst nicht. Wer den Ordner nicht mehr will, löscht ihn im Explorer. Dann verschwindet der Eintrag Exe nach „Projekte neu einlesen“ (Strg+R).
Antwort:
