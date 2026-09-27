# Fragen zu Phase 8: KI-Anbieter und KI-Assistent

Stand: 27.09.2026.

So beantworten Sie die Fragen:

- Jede Frage beginnt mit [ ].
- Passt mein Vorschlag, schreiben Sie ein x in die Klammer: [x].
- Wollen Sie etwas anderes, schreiben Sie ein Ausrufezeichen hinein: [!]. Schreiben Sie Ihre Antwort hinter „Antwort:“.
- Ist etwas unklar, schreiben Sie ein Fragezeichen hinein: [?]. Ich erkläre es dann genauer.
- Mit der Suche nach [ ] finden Sie die Fragen, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Worum es geht

Phase 8 bindet eine KI an. Zuerst zwei Arten:
- Ollama auf Ihrem Rechner. Dabei verlässt nichts den Rechner.
- Eine OpenAI-kompatible Schnittstelle mit eigener Adresse, zum Beispiel LM Studio, ein Firmen-Server oder OpenAI selbst.

Dazu kommt das Feature „KI-Assistent“. Es schlägt Commit-Nachrichten und Kurzbeschreibungen vor. Die KI ist immer nur ein Vorschlag, Sie entscheiden.

Azure OpenAI, Anthropic und Gemini kommen in Phase 15.


## A. Ablauf

[ ] 1. Zwei Teilschritte
Frage: Soll Phase 8 wieder aufgeteilt werden?
Vorschlag: Ja, in zwei Teilschritte:
- 8a: KI-Anbieter einrichten, Verbindung testen, Modell wählen, Seite „KI“ im Einrichtungsassistenten, Hinweis zum Datenschutz.
- 8b: Feature „KI-Assistent“ mit Vorschlägen für Commit-Nachricht, Pull Request und Kurzbeschreibung.
Antwort:

[ ] 2. Ihre KI zum Testen
Frage: Womit testen Sie? Haben Sie Ollama installiert, und welches Modell nutzen Sie?
Vorschlag: Sie testen mit Ihrem Ollama und einem Modell, das schon installiert ist. Schreiben Sie unten den Namen dazu, zum Beispiel gemma3:12b. Die automatischen Tests brauchen keine KI, sie arbeiten mit einem nachgebauten Server.
Antwort:


## B. KI-Anbieter einrichten

[ ] 3. Wo richtet man sie ein?
Frage: Das Konzept nennt „Einstellungen, KI-Anbieter“. Die Kontenverwaltung kennt aber schon die Art „KI“. Wo sollen KI-Anbieter stehen?
Vorschlag: In der Kontenverwaltung, wie Plattform-Konten, mit Name, Art, Adresse, Modell und bei Bedarf API-Schlüssel im Tresor. Im Menü Einstellungen gibt es zusätzlich „KI-Anbieter …“. Es öffnet die Kontenverwaltung gleich bei den KI-Anbietern. So gibt es einen Ort für alle Zugänge.
Antwort:

[ ] 4. Mehrere Anbieter
Frage: Man kann mehrere KI-Anbieter einrichten. Welcher wird benutzt?
Vorschlag: In den Grundeinstellungen wählen Sie den Standard-Anbieter. Das Feature KI-Assistent hat eine eigene Einstellung „KI-Anbieter für Vorschläge“ mit der Vorgabe „Standard“. So kann man für einzelne Aufgaben einen anderen nehmen, wie im Konzept.
Antwort:

[ ] 5. Modell wählen
Frage: Wie wählen Sie das Modell?
Vorschlag: Nach „Verbindung testen“ fragt das Cockpit die verfügbaren Modelle ab und zeigt sie als Auswahl. Ist bei Ollama noch kein Modell installiert, erklärt es den Befehl, zum Beispiel `ollama pull gemma3:4b`. Das Cockpit lädt keine Modelle selbst herunter.
Antwort:

[ ] 6. Ollama starten
Frage: Was, wenn Ollama installiert ist, aber nicht läuft?
Vorschlag: Wie im Chatbot: Das Cockpit startet Ollama bei Bedarf selbst. Läuft es schon, wird es mitbenutzt. Beim Beenden stoppt das Cockpit nur ein Ollama, das es selbst gestartet hat.
Antwort:

[ ] 7. Einrichtungsassistent
Frage: Laut Konzept 8.7 hat der Assistent eine Seite „KI“. Soll sie jetzt kommen?
Vorschlag: Ja. Die Seite prüft, ob Ollama läuft, und listet die Modelle. Sie können dort ein Modell wählen, einen anderen Anbieter einrichten oder ohne KI weitermachen.
Antwort:


## C. Datenschutz

[ ] 8. Was bekommt die KI?
Frage: Für eine Commit-Nachricht braucht die KI die Änderungen. Was genau wird gesendet?
Vorschlag:
- Die Liste der geänderten Dateien und die geänderten Zeilen, höchstens etwa 8000 Zeichen. Nie der ganze Code.
- Dateien, die die Sicherheitsprüfung als Geheimnis erkennt, zum Beispiel `.env`, gehen nie mit.
- Zeilen mit einem gefundenen Geheimnis werden vor dem Senden durch „[entfernt]“ ersetzt.
Antwort:

[ ] 9. Anbieter außerhalb des Rechners
Frage: Geht etwas an einen Anbieter außerhalb Ihres Rechners, zum Beispiel OpenAI, soll das Cockpit einmal nachfragen. Wie genau?
Vorschlag: Beim ersten Vorschlag pro Anbieter und Aufgabe fragt es: „Für Commit-Vorschläge werden Auszüge aus Ihrem Code an OpenAI gesendet. Einverstanden?“ Vorgabe ist „Nein“. Die Antwort merkt es sich. Die Grundeinstellung „Code-Auszüge nur an lokale oder firmeninterne KI senden“ gibt es schon, sie sperrt solche Anbieter ganz.
Antwort:

[ ] 10. Firmeninterne Anbieter
Frage: Ein Firmen-Server ist nicht auf Ihrem Rechner, gilt aber als sicher. Woran erkennt das Cockpit das?
Vorschlag: Beim OpenAI-kompatiblen Anbieter gibt es das Kästchen „Läuft im eigenen Netz oder in der Firma“. Ist es angekreuzt, gilt er wie ein lokaler Anbieter.
Antwort:


## D. KI-Assistent

[ ] 11. Commit-Nachricht vorschlagen
Frage: Wie kommt der Vorschlag ins Fenster „Änderungen hochladen“?
Vorschlag: Das Fenster bekommt den Knopf „Vorschlag erstellen lassen“ (Alt+V). Er füllt „Was haben Sie geändert?“ und „Beschreibung“. NVDA sagt „Vorschlag eingefügt.“, und der Fokus geht in das erste Feld. Sie können alles ändern. Solange die KI arbeitet, bleibt das Fenster bedienbar, und Escape bricht den Vorschlag ab.
Antwort:

[ ] 12. Weitere Vorschläge
Frage: Wo soll die KI sonst noch helfen?
Vorschlag: Beim Pull Request für Titel und Beschreibung und beim ersten Hochladen für die Kurzbeschreibung. Jeweils mit demselben Knopf „Vorschlag erstellen lassen“.
Antwort:

[ ] 13. Sprache
Frage: In welcher Sprache sollen die Vorschläge sein?
Vorschlag: Das Feature hat die Einstellung „Sprache der Vorschläge“ mit Deutsch als Vorgabe und Englisch als Alternative. Viele öffentliche Projekte schreiben Commit-Nachrichten auf Englisch.
Antwort:

[ ] 14. Prompts
Frage: Laut Konzept liegen die Prompts in eigenen Dateien und lassen sich anpassen. Wie?
Vorschlag: Die Prompts liegen als Textdateien beim Cockpit. Legen Sie eine Datei mit demselben Namen in den Ordner „prompts“ im Datenordner, nimmt das Cockpit Ihre Fassung. Eine eigene Oberfläche dafür gibt es vorerst nicht.
Antwort:
