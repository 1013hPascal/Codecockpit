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

[x] 1. Zwei Teilschritte
Frage: Soll Phase 8 wieder aufgeteilt werden?
Vorschlag: Ja, in zwei Teilschritte:
- 8a: KI-Anbieter einrichten, Verbindung testen, Modell wählen, Seite „KI“ im Einrichtungsassistenten, Hinweis zum Datenschutz.
- 8b: Feature „KI-Assistent“ mit Vorschlägen für Commit-Nachricht, Pull Request und Kurzbeschreibung.
Antwort: 
also du kannst es shcon in zwei abschnitte machen, enn du meinst.
Also ich will ki später noch für mehr sachen einbinden. z.b. als hilfe, also wenn ich nicht weiß, wie etwas in unserem codecockpit fukioniert, oder wo ich einen shcalter finde, soll es helfen. Außerdem will ich später noch ein integriertes terminal bauen, vielleicht sollten wir das jetzt schon machen. das ist ja eigentlich ein grundfeature. also das progrmam deckt ja nicht alle GitHub Optionen an und das würde ja auch veil zu unübersichtlich werden. deshal würde ich ich bei projekt aktion und bei code aktion oder so, ein terminal einbaue. das soll dan ein Textfeld haben, mit schift tab ein ausgabefeld wo die ausgabe vom terminal kommt. und mit tab, ein Ausgabefled der ki. Die, wenn ich in das Textfeld ein GitHub befehl schreibe und sehe ich wie im nrmalen terminal in der ausgabe was ich eingeeben hab und was der fehler war. hier gerne wieder in listenform zeile für zeile. wenn etwas schief läuft, steht das ja auch da. aber dann soll die lokale ki, in ki ausgabefeld eine prognose schreibne, warum das passiert, und was man machen kann. 
Und, ich würde auch gerne whisper hinzufügen, also das feature spracheingabe mit whisper, lokal oder nicht lokal. Also wir sollten ein menü punkt ki habne, wo man die einschalten kann und wenn man die einschaltet, eine asuwahl haben, lokal, oder extern, wenn lokal möglich ist. bei extern, dann wie im Konzept. Es ist auch wichtig, dass bei lokal das Programm die Konfiguration heruasfindet, ode wenn das schwierig ist, den user sagt, wo er das nachschauen kann und der muss das dann wo eingeben, also ramm, gpu, cpu und die irgendwie müssen wir dann schwellenwerte haben. und Modell auswahlen. am bestten ein lokales Modell für 16 gb ram, 32,gb ram und 64gb oder höher höher anbieten. mehr bauche wir nicht, sonst kann man ja firmeninternes nutzen. 

bei whisper wwäre es cool, dass wnn man in einem eingabefeld ist, mann immer einen tastenbefehl drücken kann, wie ctrl k oder was halt nohc offen ist, und dann kann man diktieren, und mit nochmal ctrl k ode was der befehl ist, kann man das dann stopppen und es wird ins Textfeld geschreiben. und mit crtl shift ka ode rso, kann man die abrechen.
bitte das ins Konzept einarbeiten.  und sagen wie wir weiter machen sollen.
ach und wenn feature ki ausgeschaltet ist, gibt es das terminal, aber das ki ausgabefeld nicht. 

[x] 2. Ihre KI zum Testen
Frage: Womit testen Sie? Haben Sie Ollama installiert, und welches Modell nutzen Sie?
Vorschlag: Sie testen mit Ihrem Ollama und einem Modell, das schon installiert ist. Schreiben Sie unten den Namen dazu, zum Beispiel gemma3:12b. Die automatischen Tests brauchen keine KI, sie arbeiten mit einem nachgebauten Server.
Antwort: ich habe gemma4 12b installiert.


## B. KI-Anbieter einrichten

[ ] 3. Wo richtet man sie ein?
Frage: Das Konzept nennt „Einstellungen, KI-Anbieter“. Die Kontenverwaltung kennt aber schon die Art „KI“. Wo sollen KI-Anbieter stehen?
Vorschlag: In der Kontenverwaltung, wie Plattform-Konten, mit Name, Art, Adresse, Modell und bei Bedarf API-Schlüssel im Tresor. Im Menü Einstellungen gibt es zusätzlich „KI-Anbieter …“. Es öffnet die Kontenverwaltung gleich bei den KI-Anbietern. So gibt es einen Ort für alle Zugänge.
Antwort: als ich würde im menü oben, das menü KI machen. Hie rkann man dann ki feature aktivieren, dann springt man in das menü featur, welches aktiviert ist und landen auf der Schaltfläche ki atkivieren. 
dann gibgt e ses im menü unter ki feature aktivieren, oder deaktiviern, jenach dem, darunter, ki Tools auswählen. dass ist dann, was ich oben gemeint hatte. und wenn man dann eine externe ki auswählt, dann springt er in das menü Kontoverwaltung,wie du es vosrschlägst. 
irgendwie so oder?

[x] 4. Mehrere Anbieter
Frage: Man kann mehrere KI-Anbieter einrichten. Welcher wird benutzt?
Vorschlag: In den Grundeinstellungen wählen Sie den Standard-Anbieter. Das Feature KI-Assistent hat eine eigene Einstellung „KI-Anbieter für Vorschläge“ mit der Vorgabe „Standard“. So kann man für einzelne Aufgaben einen anderen nehmen, wie im Konzept.
Antwort: 
Also in der KI Verwaltung kann man merhere ki Tools aktiviern, lokal oder extern. wobei externe in akkoundverwaltung aktiviert werden. 
unter ki menü kann man auch ki feature aktivieren, wobei man dann in das menü Features springt. aktiviert man dort ki feature, kommt man mit tab in die verschiedenen ki Features, sprache, text ki. und hier kann man dan für sprachki entwder die lokalen oder externen ki auswählen, di man bei ki Tools in abschnitt neü ki aktiviert hat. 
so würde ich das machen.

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


## E. Ihre neuen Ideen (ergänzt am 27.09.2026)

Ihre Ideen stehen jetzt im Konzept: Terminal (9.9), Spracheingabe (10.15), Terminal-Erklärung (10.16), KI-Hilfe (10.17) und KI-Verwaltung mit lokaler KI (11.1). Hier die Einzelheiten, bei denen Sie entscheiden.

[ ] 15. Neue Aufteilung von Phase 8
Frage: Phase 8 wird dadurch deutlich größer. Wie teilen wir sie auf?
Vorschlag: Fünf Teilschritte, jeder mit eigenen Tests und Checkliste. Es bleibt bei 17 Phasen.
- 8a: Menü KI, KI-Verwaltung, Ollama und OpenAI-kompatibel, Rechner auslesen und Modell nach Stufe vorschlagen, Seite KI im Assistenten, Datenschutz.
- 8b: Eingebautes Terminal (Kern) und Feature Terminal-Erklärung.
- 8c: Feature KI-Assistent: Vorschläge für Commit-Nachricht, Pull Request und Kurzbeschreibung.
- 8d: Feature Spracheingabe mit Whisper.
- 8e: Feature KI-Hilfe.
Das Terminal kommt früh, weil es ohne KI funktioniert und Sie es gleich nutzen können.
Antwort:

[ ] 16. Menü KI
Frage: Habe ich Ihre Antwort zu Frage 3 richtig verstanden?
Vorschlag: Neues Menü „KI“ mit zwei Einträgen. „KI-Verwaltung …“ zeigt die Werkzeuge nach Art (Text-KI, Sprach-KI), jedes lokal oder extern. Extern führt in die Kontenverwaltung. „KI-Features …“ öffnet die Feature-Verwaltung und markiert dort das erste KI-Feature. Einen eigenen Eintrag „KI aktivieren“ gibt es nicht, weil das Ein- und Ausschalten schon in der Feature-Verwaltung passiert. So gibt es für jede Sache genau einen Ort.
Antwort:

[ ] 17. Welche Shell im Terminal?
Frage: Das Terminal braucht eine Shell, in der die Befehle laufen. Welche?
Vorschlag: PowerShell, wie in Windows üblich. Befehle wie `git log` oder `git rebase` laufen dort genauso. Das Programm gh von GitHub geht auch, wenn es installiert ist, es ist aber nicht nötig.
Antwort:

[ ] 18. Sicherheit im Terminal
Frage: Im Terminal kann man alles eingeben, auch Befehle, die Dateien löschen. Die Regel „vorher Sicherheitskopie“ lässt sich dort nicht einhalten. Wie gehen wir damit um?
Vorschlag: Beim ersten Öffnen sagt das Cockpit einmal: „Befehle im Terminal laufen ohne Rückfrage und ohne Sicherheitskopie.“ Gesperrt ist nur der force push, wie überall im Cockpit. Sonst ist es Ihr Terminal.
Antwort:

[ ] 19. Neue Bibliotheken für Whisper
Frage: Für die Spracheingabe braucht das Cockpit drei neue Bibliotheken: faster-whisper (Spracherkennung), sounddevice (Mikrofon) und numpy. Das Tagebuch nutzt dieselben. Nach der Regel „keine neuen Bibliotheken ohne Rückfrage“ frage ich Sie. Einverstanden?
Vorschlag: Ja. Das Whisper-Modell lädt das Cockpit beim ersten Diktieren herunter, mit Ansage des Fortschritts. Das Modell „small“ ist etwa 500 MB groß.
Antwort:

[ ] 20. Tastenkürzel für die Spracheingabe
Frage: Strg+K und Strg+Umschalt+K sind im Cockpit noch frei. Passt das?
Vorschlag: Ja: Strg+K startet und beendet die Aufnahme, Strg+Umschalt+K bricht ab. Beide stehen in der Liste der Tastenkürzel (F1).
Antwort:

[ ] 21. Stufen für die lokale KI
Frage: Welche Modelle schlägt das Cockpit für 16, 32 und 64 GB Arbeitsspeicher vor?
Vorschlag: Für Text: ab 16 GB ein kleines Modell mit etwa 4 Milliarden Parametern, ab 32 GB eines mit etwa 12 Milliarden (wie Ihr gemma4:12b), ab 64 GB eines mit etwa 27 Milliarden. Für Whisper: ab 16 GB „small“, ab 32 GB „medium“, ab 64 GB oder mit passender Grafikkarte „large-v3-turbo“. Die genauen Namen prüfe ich beim Bauen gegen das, was es dann bei Ollama gibt. Sie stehen an einer Stelle und lassen sich ändern.
Antwort:

[ ] 22. Grundlage der KI-Hilfe
Frage: Damit die KI-Hilfe richtig antwortet, braucht sie eine Beschreibung des Cockpits. Woher kommt die?
Vorschlag: Aus drei Quellen: den Anleitungen im Menü Hilfe, den Einführungen der Features und einer Liste aller Menüs und Aktionen, die das Cockpit selbst beim Fragen erzeugt. So ist sie immer auf dem aktuellen Stand, auch wenn später Features dazukommen. Weiß die KI etwas nicht, sagt sie das, statt zu raten.
Antwort:
