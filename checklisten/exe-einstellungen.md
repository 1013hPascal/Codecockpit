# Checkliste: Eigene Bauanleitung schützen, Unbedingtes in den Exe-Einstellungen

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\exe-einstellungen.


[ ] 1. Exe des Cockpits startet wieder
Tasten: Beim Cockpit „Exe aus dem Code erstellen …“ bis zum Bau.
Ansage: Der Start-Test besteht. Die neue Exe startet ohne „Die Features sind fehlerhaft beschrieben.“
Ergebnis:

[ ] 2. Eigene Bauanleitung beim Cockpit
Tasten: Beim Cockpit „Exe-Einstellungen …“ öffnen.
Ansage: „Die Bauanleitung CodeCockpit.spec ist von Hand geschrieben. Startdatei, Name, Bauart und Symbol stehen dort. …“ Der Fokus steht in der Liste „Ordner und Dateien neben der Exe“. Felder für Startdatei, Name und Bauart gibt es hier nicht.
Ergebnis:

[ ] 3. Bauanleitung bleibt unverändert
Tasten: Weiter, Speichern.
Ansage: Die Rückfrage sagt „Die von Hand geschriebene Datei CodeCockpit.spec bleibt unverändert.“ Danach zeigt „Änderungen auf GitHub hochladen …“ höchstens cockpit.toml als geändert, nicht CodeCockpit.spec.
Ergebnis:

[ ] 4. Unbedingt nötig bei der Vokabel-App
Tasten: Bei der Vokabel-App „Exe aus dem Code erstellen …“.
Ansage: In der Liste steht oben „Meine-Vokabeln, unbedingt nötig, vom Code benutzt“, angehakt. Die übrigen Einträge folgen darunter.
Ergebnis:

[ ] 5. Abhaken wird nachgefragt
Tasten: Auf „Meine-Vokabeln“ Leertaste, dann Weiter.
Ansage: Rückfrage „Meine-Vokabeln ist unbedingt nötig, der Code benutzt es. …“ mit „Trotzdem weglassen“ und „Wieder anhaken“ (Vorgabe, auch mit Escape). Bei „Wieder anhaken“ ist der Eintrag wieder angehakt, der Fokus steht in der Liste.
Ergebnis:
