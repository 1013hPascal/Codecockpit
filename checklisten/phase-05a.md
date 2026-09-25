# Checkliste Phase 5a: Git, Projekte hinzufügen, Stand in der Projektliste

Stand: 25.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.

Hinweis: Ansagen in Dialogen sind noch ein offener Punkt (TODO.md). Die Ansagen in dieser Checkliste kommen fast alle im Hauptfenster, nachdem ein Fenster geschlossen ist.


## Vorbereitung

1. Schließen Sie alle Fenster von CodeCockpit und starten Sie `start_testdaten.bat`.
2. Im Einrichtungsassistenten:
   - Wählen Sie die Windows-Anmeldeinformationsverwaltung als Tresor.
   - Melden Sie sich auf der Seite „GitHub-Konto“ im Browser mit Ihrem echten Konto an.
   - Tragen Sie auf der Seite „Git-Identität“ Ihren Namen und Ihre E-Mail-Adresse ein.
3. Alles passiert im Ordner der Testdaten `%LOCALAPPDATA%\CodeCockpit\Testdaten`. Ihre echten Projekte bleiben unberührt.
4. In dieser Phase lädt das Cockpit nichts auf GitHub hoch und ändert dort nichts. Es liest nur die Liste Ihrer Repositories und lädt höchstens eines herunter.
5. Die Ordner für Abschnitt C liegen in `%LOCALAPPDATA%\CodeCockpit\Testdaten\Andere Ordner`. Im Fenster „Ordner auswählen“ von Windows können Sie diesen Pfad in das Feld „Ordner“ tippen und dann Enter drücken.


## A. Stand in der Projektliste

[x] 1. Zeilen der Projekte
Tasten: Nach dem Start Pfeiltasten in der Projektliste. Warten Sie vorher ein paar Sekunden.
Erwartet: Es gibt diese Zeilen:
- „Tagebuch, aktualisiert am“ mit dem heutigen Datum, dann „1 Datei noch nicht hochgeladen, virtuelle Umgebung muss neu angelegt werden“.
- „PDF-Chat, aktualisiert am“ mit dem heutigen Datum.
- „Bildbeschreiber, noch nicht auf GitHub“.
- „Notizen, Ordner nicht gefunden“.
- Ihre Repositories auf GitHub, zum Beispiel „Tagebuch, nur auf GitHub, aktualisiert am …“. Sie stehen nach Datum zwischen den anderen Projekten.
Ergebnis:

[x] 2. Zeile Code
Tasten: Auf „PDF-Chat“ Pfeil rechts, dann Pfeil runter. Danach dasselbe bei „Tagebuch“.
Erwartet: Bei PDF-Chat heißt die Zeile „Code, alles hochgeladen“. Bei Tagebuch heißt sie „Code, 1 Datei noch nicht hochgeladen“.
Ergebnis:

[x] 3. Neu einlesen ohne Sprung
Tasten: Markieren Sie „Code“ unter Tagebuch. Drücken Sie Strg+R und warten Sie kurz.
Erwartet: NVDA sagt „Projekte neu eingelesen“ und die Zahl der Projekte. Der Fokus bleibt auf der Zeile „Code“ von Tagebuch. Danach kommen keine weiteren Ansagen.
Ergebnis:


## B. Repositories, die nur auf GitHub liegen

Wählen Sie für diesen Abschnitt ein kleines Repository aus Ihrer Liste.

[x] 4. Aktionen
Tasten: Pfeiltasten bis zu einer Zeile „…, nur auf GitHub, …“, dann Tab.
Erwartet: Die Aktionen heißen „Herunterladen“ und „Auf GitHub öffnen“.
Ergebnis:

[x] 5. Auf GitHub öffnen
Tasten: In den Aktionen „Auf GitHub öffnen“, Enter.
Erwartet: Der Browser zeigt die Seite des Repositories auf GitHub. NVDA sagt „Wird im Browser geöffnet.“
Ergebnis:

[x] 6. Herunterladen mit Enter
Tasten: Zurück ins Cockpit, Umschalt+Tab zur Projektliste, Enter auf der Zeile „…, nur auf GitHub, …“.
Erwartet: NVDA sagt „… wird heruntergeladen.“ und nach einer Weile „… heruntergeladen.“ Der Fokus steht auf dem Projekt. Die Zeile heißt jetzt „Name, aktualisiert am …“ ohne „nur auf GitHub“. Mit Pfeil rechts und Pfeil runter kommt „Code, alles hochgeladen“.
Ergebnis:

[?] 7. Git-Identität im heruntergeladenen Projekt
Tasten: Öffnen Sie im Explorer `%LOCALAPPDATA%\CodeCockpit\Testdaten\Projekte\<Name>\Code\.git\config` mit dem Editor.
Erwartet: Unter `[user]` stehen Ihr Name und Ihre E-Mail-Adresse aus dem Einrichtungsassistenten.
Ergebnis: fWarum kann man das nicht auch bei projekt mit tab bei Aktionen, das wor zur projektdatein acuh der diese Infos, sondren in der Datei, oder ist das nich treelvant., odrer kommt das später noch?

Antwort von Claude: Gute Idee, ist eingebaut. Bei „Code“ gibt es jetzt die Aktion „Git-Identität …“. Sie zeigt die Identität des Projekts. Weicht sie von den Grundeinstellungen ab oder fehlt sie, fragt sie, ob die aus den Grundeinstellungen übernommen werden soll. Bitte prüfen Sie Punkt 7a statt Punkt 7. Dafür das Cockpit neu starten.

[ ] 7a. Aktion Git-Identität
Tasten: „Code“ unter dem heruntergeladenen Projekt, Tab, „Git-Identität …“, Enter. Danach dasselbe bei „Code“ unter Bildbeschreiber.
Erwartet: Beim heruntergeladenen Projekt ein Meldungsfenster: Ihr Name und Ihre E-Mail-Adresse, dann „Das ist die Identität aus den Grundeinstellungen.“ Bei Bildbeschreiber gibt es die Aktion nicht, weil es noch kein Git-Repository ist.
Ergebnis:


## C. Vorhandenes Projekt hinzufügen

[ ] 8. Projektordner mit Code
Tasten: Alt+D, „Vorhandenes Projekt hinzufügen …“, Ordner `…\Andere Ordner\Wetter` wählen.
Erwartet: NVDA sagt „Wetter hinzugefügt.“ Der Fokus steht auf „Wetter, noch nicht auf GitHub“.
Ergebnis: Check nicht was du hier willst. wo soll ichhin, woher soll ein orndre hinzugefügt werden? von wo anders vom rechner in diesn Explorer, und damit dan auf GitHub?

Antwort von Claude: Es geht um Projekte, die nicht im Projekte-Hauptordner liegen, zum Beispiel auf einem anderen Laufwerk oder ein Repository der Firma. Mit „Vorhandenes Projekt hinzufügen“ kommen sie in die Projektliste des Cockpits. Auf GitHub passiert dabei nichts, hochgeladen wird erst in 5b. Für den Test habe ich solche Ordner in den Testdaten vorbereitet. So geht es:
1. Alt+D, „Vorhandenes Projekt hinzufügen …“. Es öffnet sich das Fenster „Ordner auswählen“ von Windows.
2. Tippen Sie in das Feld „Ordner“ diesen Pfad: `C:\Users\pasca\AppData\Local\CodeCockpit\Testdaten\Andere Ordner\Wetter`
3. Drücken Sie Enter. Falls das Fenster noch offen ist, wählen Sie den Knopf „Ordner auswählen“.
Für die Punkte 9 bis 13 und 14 ist es genauso, nur der letzte Teil des Pfads ändert sich, zum Beispiel `…\Andere Ordner\Rechner`.

[ ] 9. Schon in der Liste
Tasten: Dasselbe noch einmal mit `Wetter`.
Erwartet: NVDA sagt „Wetter ist schon in der Liste.“ Der Fokus steht auf Wetter. Es gibt Wetter nur einmal.
Ergebnis:

[ ] 10. Ordner ohne Code: Rückfrage und Escape
Tasten: „Vorhandenes Projekt hinzufügen …“ mit dem Ordner `Rechner`. Lesen Sie die Frage. Dann Escape.
Erwartet: Die Frage beginnt mit „Der Ordner Rechner hat keinen Unterordner Code.“ und erklärt Umstellen und Nur verknüpfen. Mit Tab erreichbar: „Umstellen …“, „Nur verknüpfen …“, „Abbrechen“. Vorgabe ist „Abbrechen“. Nach Escape passiert nichts.
Ergebnis:

[ ] 11. Umstellen
Tasten: Noch einmal mit `Rechner`, diesmal „Umstellen …“. Lesen Sie die zweite Frage und wählen Sie „Umstellen“.
Erwartet: Die zweite Frage sagt, dass der Ordner nach `…\Testdaten\Projekte\Rechner\Code` verschoben wird und sein Inhalt unverändert bleibt. Danach sagt NVDA „Rechner hinzugefügt.“ Im Ordner `Andere Ordner` gibt es Rechner nicht mehr.
Ergebnis:

[ ] 12. Nur verknüpfen
Tasten: „Vorhandenes Projekt hinzufügen …“ mit dem Ordner `Firmenprojekt`, „Nur verknüpfen …“. Bei der Frage nach dem Exe-Ordner „Ohne Exe-Ordner“.
Erwartet: NVDA sagt „Firmenprojekt hinzugefügt.“ Der Ordner bleibt in `Andere Ordner`. Beim Ausklappen gibt es nur „Code, noch nicht auf GitHub“.
Ergebnis:

[ ] 13. Andere Git-Identität
Tasten: „Vorhandenes Projekt hinzufügen …“ mit dem Ordner `Vereinsseite`. Lesen Sie die Frage, dann Escape.
Erwartet: Die Frage lautet „Vereinsseite hat eine andere Git-Identität: Alter Name, alt@example.org. In den Grundeinstellungen steht: …“. Die Knöpfe heißen „Grundeinstellungen übernehmen“ und „Vorhandene behalten“. Vorgabe ist „Vorhandene behalten“. Nach Escape sagt NVDA „Vereinsseite hinzugefügt.“
Ergebnis:


## D. Neuer Ort und Reparatur

[ ] 14. Neuen Ort angeben
Tasten: Auf „Notizen, Ordner nicht gefunden“ Tab. Die erste Aktion ist „Neuen Ort angeben …“. Enter und den Ordner `…\Andere Ordner\Notizen` wählen.
Erwartet: NVDA sagt „Neuer Ort für Notizen gespeichert.“ Die Zeile heißt jetzt „Notizen, noch nicht auf GitHub“. Bei PDF-Chat gibt es die Aktion „Neuen Ort angeben …“ nicht.
Ergebnis:

[ ] 15. Virtuelle Umgebung neu anlegen
Tasten: „Code“ unter Tagebuch, Tab, „Virtuelle Umgebung neu anlegen …“, Enter. Frage lesen, „Neu anlegen“.
Erwartet: Die Frage nennt den Grund „Das Projekt wurde verschoben.“ und sagt, dass die alte Umgebung als Sicherheitskopie in den Ordner backups kommt. Danach sagt NVDA „Schritt 1 von 2: Alte Umgebung wird gesichert …“, „Schritt 2 von 2: Neue Umgebung wird angelegt …“ und „Virtuelle Umgebung von Tagebuch neu angelegt.“ In der Zeile von Tagebuch steht nichts mehr von der virtuellen Umgebung.
Ergebnis:

[ ] 16. Mit vorhandenem Repository verbinden
Tasten: „Code“ unter Bildbeschreiber, Tab, „Mit vorhandenem Repository verbinden …“, Enter.
Erwartet: Eine Liste „Repositories“ mit Ihren Repositories, zum Beispiel „Tagebuch, 1013hPascal“. Der letzte Eintrag heißt „Adresse eingeben …“. Escape schließt, ohne etwas zu ändern.
Ergebnis:

[ ] 17. Verbinden ausführen
Tasten: Wie in Punkt 16, diesmal ein kleines Repository wählen, Enter, in der Frage „Verbinden“.
Erwartet: Die Frage sagt, dass die Dateien unverändert bleiben. NVDA sagt „Bildbeschreiber wird verbunden.“ und dann „Bildbeschreiber ist verbunden, Branch main.“ (oder der Name des Haupt-Branches). Die Zeile nennt jetzt Dateien, die noch nicht hochgeladen sind. Auf GitHub ändert sich nichts.
Ergebnis:


## E. Einstellungen und Hilfe

[ ] 18. Neue Repositories automatisch herunterladen
Tasten: Alt+E, „Grundeinstellungen …“, mit Tab durch das Formular.
Erwartet: Es gibt das Kontrollkästchen „Neue Repositories automatisch herunterladen“. Es ist nicht aktiviert.
Ergebnis:

[ ] 19. Tastenkürzel
Tasten: F1.
Erwartet: Die Liste enthält „Repository herunterladen, das nur auf GitHub liegt, Enter“ und „Projekte neu einlesen und Stand abfragen, Strg+R“.
Ergebnis:
