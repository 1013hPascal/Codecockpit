# Checkliste Phase 8b: Menü KI, KI-Verwaltung, Terminal-Erklärung

Stand: 27.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Gibt es eine Frage, schreiben Sie ein Fragezeichen hinein: [?].
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Was neu ist

- Neues Menü „KI“ (Alt+K) mit „KI-Verwaltung …“ und „KI-Features …“.
- In der KI-Verwaltung richten Sie eine Text-KI ein: Ollama auf Ihrem Rechner oder ein KI-Konto, jeweils mit Modell.
- Das Cockpit liest Arbeitsspeicher, Prozessor und Grafikkarte aus und empfiehlt ein Modell.
- Neues Feature „Terminal-Erklärung“: Schlägt im Terminal ein Befehl fehl, erklärt die KI den Fehler.
- Der Einrichtungsassistent hat die Seite „KI“. Die Grundeinstellungen haben die Grenze für die Zeichen an die KI.
- Das Cockpit startet Ollama selbst und beendet es beim Schließen wieder, wenn es Ollama selbst gestartet hat.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit. Beenden Sie Ollama, falls es läuft.
2. Starten Sie `start_testdaten.bat`.


## A. Einrichtungsassistent

[x] 1. Seite KI
Tasten: Im Assistenten Weiter bis „Schritt 7 von 8: KI“. Die Seiten davor dürfen Sie überspringen, nur der Tresor ist Pflicht.
Erwartet: NVDA sagt „Schritt 7 von 8: KI. Eine KI kann Ihnen helfen, …“. Der Fokus steht in der Liste „KI“. Zeile 1: „Es ist noch keine KI eingerichtet.“ Nach ein bis zwei Sekunden stehen darunter Ihr Arbeitsspeicher, die Empfehlung (bei 32 GB „gemma4:12b“) und „Ollama ist installiert und startet bei Bedarf.“ Mit Tab kommt „KI einrichten …“.
Ergebnis:

[x] 2. Überspringen und Zusammenfassung
Tasten: Alt+B für Überspringen.
Erwartet: Die Zusammenfassung nennt „Übersprungen: KI. Nachholen: Menü KI, KI-Verwaltung.“ Mit Alt+F für Fertig öffnet sich das Cockpit.
Ergebnis:


## B. KI-Verwaltung

[x] 3. Menü KI
Tasten: Alt+K.
Erwartet: Das Menü „KI“ öffnet sich mit „KI-Verwaltung …“ und „KI-Features …“. In F1 stehen „Features, Alt+F“ und „KI, Alt+K“.
Ergebnis:

[x] 4. Fenster KI-Verwaltung
Tasten: Im Menü KI Enter auf „KI-Verwaltung …“. Dann Tab, lesen, Tab durch die Knöpfe.
Erwartet: Titel „KI-Verwaltung“. Der Fokus steht in der Liste „Text-KI“ auf „Neue Text-KI einrichten …“. Mit Tab kommt „Rechner und Empfehlung“ mit Arbeitsspeicher, Prozessor, Grafikkarte, Empfehlung und Zustand von Ollama, jeweils eine Zeile. Danach nur die Knöpfe „Arbeitsspeicher eingeben …“ und „Schließen“. Die anderen Knöpfe passen nicht zur Zeile „Neu“ und sind ausgeblendet.
Ergebnis:

[x] 5. Ollama einrichten
Tasten: Zurück in die Liste „Text-KI“, Enter auf „Neue Text-KI einrichten …“. In der Liste „Art der KI“ Enter auf „Lokal: Ollama auf diesem Rechner“.
Erwartet: Es öffnet sich „Modell wählen: Ollama“. In „Installierte Modelle“ steht kurz „Wird geladen …“. Das Cockpit startet dabei Ollama, das kann bis zu 30 Sekunden dauern. Danach stehen Ihre Modelle da, zum Beispiel „bge-m3:latest“, „gemma4:12b“ und „qwen2.5vl:7b“. Der Fokus bleibt in der Liste.
Ergebnis:

[x] 6. Vorgeschlagene Modelle
Tasten: Tab, die Liste lesen.
Erwartet: Die Liste heißt „Vorgeschlagene Modelle“ und hat drei Zeilen. Markiert ist die Empfehlung, bei 32 GB: „gemma4:12b, ab 32 GB Arbeitsspeicher, etwa 8 GB, empfohlen für Ihren Rechner, installiert“. Die anderen: „gemma4:e4b, …, nicht installiert“ und „gemma4:26b, ab 64 GB …, zu groß für Ihren Rechner, nicht installiert“.
Ergebnis:

[x] 7. Modell übernehmen
Tasten: Auf „gemma4:12b, …, installiert“ Enter.
Erwartet: Das Fenster schließt sich. NVDA sagt „Text-KI eingerichtet: Ollama auf diesem Rechner, gemma4:12b, Standard.“ In der Liste steht diese Zeile, sie ist markiert.
Ergebnis:

[!] 8. Knöpfe und Verbindungstest
Tasten: Tab, Tab zu den Knöpfen, „Verbindung testen“.
Erwartet: Jetzt gibt es „Modell wählen …“, „Verbindung testen“ und „Entfernen“. „Als Standard“ fehlt, weil es schon Standard ist. Der Test meldet „Ollama läuft. Installierte Modelle: 3.“ (oder Ihre Anzahl).
Ergebnis: Eigentlich super, nur man kannhier die schalter nicht mit enter anklicken, dass änndern, muss ich aber nicht normal testen.

Antwort von Claude: Behoben. In der KI-Verwaltung und bei „Modell wählen“ drückt Enter jetzt den Knopf, der den Fokus hat. Ein Test prüft das mit einem echten Tastendruck.

[x] 9. Modell herunterladen (nur ansehen)
Tasten: In der Liste auf der Ollama-Zeile Enter. Tab zu „Vorgeschlagene Modelle“, auf „gemma4:e4b, …, nicht installiert“ Enter.
Erwartet: Eventuell kommt zuerst einmal der Hinweis zum Terminal. Dann öffnet sich „Terminal: Modell gemma4:e4b herunterladen“. Im Feld „Befehl“ steht schon „ollama pull gemma4:e4b“. Nichts läuft, bevor Sie Enter drücken. Bitte nicht Enter drücken, das Modell ist etwa 10 GB groß. Escape schließt das Terminal, Sie sind wieder in „Modell wählen“. Escape schließt auch das. Das Modell bleibt gemma4:12b.
Ergebnis:


## C. Terminal-Erklärung

[x] 10. KI-Features
Tasten: KI-Verwaltung schließen. Alt+K, „KI-Features …“.
Erwartet: Die Feature-Verwaltung öffnet sich. Markiert ist „Terminal-Erklärung, eingeschaltet, in … Projekten aktiv“, ohne „nicht verfügbar“. Mit Tab steht in der Beschreibung „Schlägt im Terminal ein Befehl fehl, erklärt die KI, …“ und „Braucht: KI.“
Ergebnis:

[x] 11. Einstellung der Terminal-Erklärung
Tasten: Tab bis „Einstellungen …“, Enter.
Erwartet: „Einstellungen: Terminal-Erklärung“ mit dem Auswahlfeld „KI für Erklärungen“. Gewählt ist „Standard-Werkzeug (Ollama auf diesem Rechner, gemma4:12b)“. Mit Pfeil runter gibt es auch „Ollama auf diesem Rechner, gemma4:12b“. Escape, dann in der Feature-Verwaltung Abbrechen.
Ergebnis:

[x] 12. Feld im Terminal
Tasten: Zu Code von PDF-Chat, „Terminal …“. Im Feld Befehl Tab.
Erwartet: Nach dem Befehlsfeld kommt die Liste „Erklärung der KI“ mit „Noch keine Erklärung.“ und „Sie erscheint, wenn ein Befehl fehlschlägt.“ Umschalt+Tab führt zurück ins Befehlsfeld.
Ergebnis:

[x] 13. Fehler erklären lassen
Tasten: `git checkout gibt-es-nicht` eintippen, Enter. Warten. Dann Tab.
Erwartet: Zuerst „Fehler, Rückgabewert 1. …“. Nach einigen Sekunden, beim ersten Mal bis etwa 20, sagt NVDA „Erklärung der KI bereit.“ Der Fokus bleibt im Befehlsfeld. Mit Tab steht die Erklärung in der Liste, ein Satz pro Zeile, ohne Sternchen oder Aufzählungszeichen. Sie spricht zum Beispiel von einem Tippfehler im Branch-Namen und nennt „git branch“ in einer eigenen Zeile.
Ergebnis:

[x] 14. Neuer Befehl leert die Erklärung
Tasten: Zurück ins Befehlsfeld, `git status` eintippen, Enter. Tab.
Erwartet: Nach „Fertig.“ steht in der Erklärung wieder „Noch keine Erklärung.“ Bei Erfolg fragt das Cockpit die KI nicht.
Ergebnis:

[x] 15. Mehrere Zeilen der Erklärung kopieren
Tasten: Nach einem neuen Fehler in der Erklärung Strg+A, Strg+C, in einem Editor einfügen.
Erwartet: NVDA sagt „N Zeilen kopiert.“ Im Editor steht die ganze Erklärung.
Ergebnis:

[x] 16. Ohne das Feature
Tasten: Terminal schließen. Auf der Projektzeile PDF-Chat „Features dieses Projekts …“. Terminal-Erklärung mit der Leertaste ausschalten, Speichern, bestätigen. Dann bei Code „Terminal …“, im Befehlsfeld Tab.
Erwartet: Nach dem Befehlsfeld kommt gleich „Abbrechen“ bzw. „Schließen“, das Feld „Erklärung der KI“ gibt es nicht. Danach das Feature wieder einschalten.
Ergebnis:


## D. Einstellungen und Beenden

[x] 17. Grenze für die Zeichen
Tasten: Alt+E, Grundeinstellungen. Tab bis zum neuen Feld.
Erwartet: Nach „Code-Auszüge nur an lokale oder firmeninterne KI senden“ kommt „Höchstens so viele Zeichen an die KI senden“ mit 8000. Escape.
Ergebnis:

[x] 18. Ollama beim Beenden
Tasten: Das Cockpit mit Strg+Q beenden. Dann in einer PowerShell `ollama list` eingeben.
Erwartet: Ollama läuft nicht mehr, weil das Cockpit es selbst gestartet hatte. Die Meldung sagt, dass keine Verbindung möglich ist. Lief Ollama schon vor dem Start des Cockpits, läuft es weiter.
Ergebnis:


## E. Externe KI (freiwillig)

[ ] 19. Konto für eine externe KI
Tasten: Nur wenn Sie LM Studio, einen Firmen-Server oder einen Schlüssel für OpenAI haben. KI-Verwaltung, „Neue Text-KI einrichten …“, „Extern: neues KI-Konto einrichten …“.
Erwartet: Es öffnet sich „Neues Konto: OpenAI-kompatibel“ mit einer Erklärung, den Feldern „Adresse“ und „API-Schlüssel“ und dem Kästchen „Läuft im eigenen Netz oder in der Firma“. Nach dem Speichern kommt „Modell wählen“ mit den Modellen des Anbieters, aber ohne vorgeschlagene Modelle. Ist das Kästchen nicht angekreuzt und diese KI Standard, fragt das Cockpit beim ersten Fehler im Terminal, ob Befehl und Ausgabe an diese KI gehen dürfen. Vorgabe ist „Nicht senden“.
Ergebnis: Will ich nicht testen, irgendwnn spjäter, aber ist ok so. 
