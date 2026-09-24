# Checkliste Phase 2: Grundgerüst und Projektbaum

Stand: 24.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid. Ich lese die Ergebnisse dann hier nach.

Falls NVDA etwas nicht vorliest: Jede Ansage steht auch im Log. Bei den Testdaten liegt es in `%LOCALAPPDATA%\CodeCockpit\Testdaten\Daten\logs\app.log`. Steht die Ansage dort, wurde sie ausgelöst, und es liegt an der Weitergabe an NVDA.


## Vorbereitung

1. Öffnen Sie im Explorer den Ordner `Codecockpit\Code`.
2. Starten Sie `start_testdaten.bat` mit Enter.

Die Testdaten liegen in einem eigenen Ordner. Ihre echten Einstellungen werden dabei nicht berührt. Bei jedem Start werden die Testdaten neu angelegt.

Die Testdaten enthalten vier Projekte:

- PDF-Chat mit Code und Exe. Die Exe ist absichtlich keine echte Exe. Damit testen Sie das Fehlerfenster.
- Tagebuch nur mit Code.
- Bildbeschreiber mit Code und einem leeren Ordner Exe.
- Notizen, dessen Ordner fehlt.


## A. Start

[ ] 1. Start und erste Ansage
Tasten: keine, nur starten.
Erwartet: Das Fenster öffnet maximiert. Der Titel lautet „CodeCockpit (Testdaten)“. Der Fokus steht im Projektbaum auf „Neues Projekt hochladen“. Nach etwa einer halben Sekunde sagt NVDA „CodeCockpit mit Testdaten bereit. 4 Projekte.“
Ergebnis:

[ ] 2. Name des Baums
Tasten: NVDA+Tab (aktuellen Fokus ansagen).
Erwartet: NVDA nennt „Projekte“, dann eine Baumansicht und den Eintrag „Neues Projekt hochladen“, möglicherweise mit „Ebene 1“.
Ergebnis:


## B. Projektbaum

[ ] 3. Reihenfolge
Tasten: Pfeil runter, mehrmals.
Erwartet: „PDF-Chat“, „Tagebuch“, „Bildbeschreiber“, „Notizen, Ordner nicht gefunden“. NVDA sagt bei Projekten mit Unterordnern „reduziert“ oder „zugeklappt“. Bei Notizen gibt es keinen solchen Hinweis, weil es keine Unterordner hat.
Ergebnis:

[ ] 4. Ausklappen mit Pfeil rechts
Tasten: auf „PDF-Chat“ Pfeil rechts.
Erwartet: NVDA sagt „erweitert“ oder „ausgeklappt“. Der Fokus bleibt auf PDF-Chat.
Ergebnis:

[ ] 5. In die Unterordner
Tasten: noch einmal Pfeil rechts, dann Pfeil runter.
Erwartet: Zuerst „Code“, dann „Exe, PDF-Chat.exe, erstellt am“ mit dem heutigen Datum. NVDA nennt dabei Ebene 2.
Ergebnis:

[ ] 6. Zurück zum Projekt
Tasten: auf „Code“ oder „Exe“ Pfeil links.
Erwartet: Der Fokus springt zurück auf „PDF-Chat“. Das Projekt bleibt ausgeklappt.
Ergebnis:

[ ] 7. Automatisches Zuklappen
Tasten: Pfeil runter bis „Tagebuch“, dann Pfeil rechts.
Erwartet: Tagebuch klappt aus, NVDA sagt „erweitert“. Der Fokus bleibt auf Tagebuch. PDF-Chat ist jetzt zugeklappt: Mit Pfeil hoch kommen Sie direkt auf „PDF-Chat“, nicht auf dessen Exe.
Ergebnis:

[ ] 8. Zuklappen mit Pfeil links
Tasten: auf dem ausgeklappten „Tagebuch“ Pfeil links.
Erwartet: NVDA sagt „reduziert“ oder „zugeklappt“.
Ergebnis:

[ ] 9. Enter auf einem Projekt
Tasten: auf „Bildbeschreiber“ zweimal Enter.
Erwartet: Beim ersten Enter klappt das Projekt aus, beim zweiten wieder zu. Beim Bildbeschreiber heißt der zweite Unterordner „Exe, leer“.
Ergebnis:
Aslo klappt noch nicht perfekt. 
also enter drauf klappt. und liest auch vor. bei Pfeiltasten sagt er nicht ausgeklappt und auch nicht eingeklappt. 
außerdem wenn man es einklappt, verschwindet das projetk drunter oder dürüber. wird nicht mehr mit pfieltasten ereichbar. 
ich hätte gerne, das man auf einem projekt lertaste drück oder Pfeiltaste, oder enter, dann klappt es sich auf. und wenn man dort ist, ob auf code oder exe und man Pfeiltaste links drückt, soll er das wieder schließen. und die normale liste wieder anzeigen. und dann alle einträge anzeigen.


## C. Aktionen

[ ] 10. Tab in die Aktionen und zurück
Tasten: auf „PDF-Chat“ Tab, dann Umschalt+Tab.
Erwartet: Tab führt in die Liste „Aktionen“ mit dem Eintrag „Projektordner öffnen“. Umschalt+Tab führt zurück in den Baum genau auf „PDF-Chat“. Ein zweites Tab aus den Aktionen führt ebenfalls in den Baum.
Ergebnis: Das funktioniert

[ ] 11. Aktionen hängen von der Auswahl ab
Tasten: im Baum auf „Exe“ von PDF-Chat gehen, dann Tab und Pfeil runter.
Erwartet: „Exe starten“ und „Exe-Ordner öffnen“. Bei „Exe, leer“ vom Bildbeschreiber lautet der erste Eintrag „Exe starten, nicht verfügbar: Im Ordner Exe liegt keine Exe.“
Ergebnis: das funtktioniert.

[ ] 12. Nicht verfügbare Aktion
Tasten: im Baum ganz nach oben auf „Neues Projekt hochladen“, Tab, Enter.
Erwartet: NVDA sagt „Neues Projekt hochladen ist nicht verfügbar. Diese Funktion kommt in Phase 5.“
Ergebnis: funktioniert

[ ] 13. Ordner öffnen
Tasten: auf „PDF-Chat“ Tab, Enter.
Erwartet: NVDA sagt „Projektordner wird geöffnet.“, und der Explorer zeigt den Ordner PDF-Chat mit Code und Exe. Schließen Sie den Explorer mit Alt+F4 und kehren Sie ins Cockpit zurück.
Ergebnis: funktioniert

[ ] 14. Fehlerfenster
Tasten: im Baum auf „Exe“ von PDF-Chat, Enter.
Erwartet: Ein Fenster „Exe starten“ öffnet sich. NVDA liest „Exe starten hat nicht geklappt.“ Der Fokus steht im Feld „Meldung“.
Ergebnis: funktioniert

[ ] 15. Details im Fehlerfenster
Tasten: Tab bis „Details anzeigen“, Enter.
Erwartet: Das Feld „Details“ erscheint, und der Fokus steht darin. Es enthält eine technische Meldung von Windows, etwa „WinError 193“. Mit Pfeiltasten lesbar. Escape schließt das Fenster, der Fokus ist danach wieder im Baum.
Ergebnis: funktioiniert

[ ] 16. Kontextmenü
Tasten: auf „Exe“ von PDF-Chat die Menütaste oder Umschalt+F10.
Erwartet: Ein Menü mit „Exe starten“ und „Exe-Ordner öffnen“. NVDA nennt sofort den ersten Eintrag. Escape schließt, der Fokus ist wieder im Baum auf „Exe“.
Ergebnis: funktioniert

[ ] 17. Bereiche wechseln
Tasten: Strg+2, Strg+1, dann F6 und Umschalt+F6.
Erwartet: Strg+2 springt in die Aktionen, Strg+1 in den Baum. F6 und Umschalt+F6 wechseln zwischen beiden.
Ergebnis: funktioniert


## D. Meldungen

[ ] 18. Letzte Meldung wiederholen
Tasten: Strg+Umschalt+M.
Erwartet: NVDA wiederholt die letzte Meldung, zum Beispiel „Projektordner wird geöffnet.“
Ergebnis: funktioniert

[ ] 19. Liste der Meldungen
Tasten: Strg+Umschalt+L, Pfeiltasten, Escape.
Erwartet: Fenster „Meldungen“ mit einer Liste. Die neueste Meldung steht oben, am Ende jeder Zeile die Uhrzeit. Escape schließt, der Fokus kehrt zurück.
Ergebnis: funktioniert

[ ] 20. Statuszeile
Tasten: NVDA+Ende (Statuszeile vorlesen).
Erwartet: NVDA liest die letzte Meldung aus der Statuszeile.
Ergebnis: geht nicht, bitte andern tastenbefehl oder ist drer von ´nvda? ist aber auch nicht so wichtig oder?


## E. Menüs

[ ] 21. Menüleiste
Tasten: Alt, dann Pfeil rechts und links.
Erwartet: Drei Menüs: Datei, Einstellungen, Hilfe. Beim Öffnen nennt NVDA gleich den ersten Eintrag, nicht nur den Programmnamen.
Ergebnis: klappt.

[ ] 22. Menü Datei
Tasten: Alt+D.
Erwartet: „Projekte neu einlesen, Strg+R“ und „Beenden, Strg+Q“.
Ergebnis: funktioniertr

[ ] 23. Tastenkürzel
Tasten: F1.
Erwartet: Fenster „Tastenkürzel“, der Fokus steht im Text. Mit Pfeil runter liest man Zeile für Zeile. Tab führt zu „Schließen“, Escape schließt.
Ergebnis: tab funktioniert und schließen auch. die liste der Tastenbefehle ist schlecht man sieht nur afubau des fenster.s. das kannst du besser. einfach eine liste machen odrer so. 

[ ] 24. Git-Anleitung
Tasten: Alt+H, dann „Git installieren“ wählen, Enter.
Erwartet: Die Anleitung mit drei Wegen: winget, Chocolatey und Webseite. Gut lesbar mit Pfeiltasten.
Ergebnis: tap funktioniert schließen auch. wie eben, die liste geht nicht. 

[ ] 25. Über CodeCockpit
Tasten: Alt+H, „Über CodeCockpit“, Enter.
Erwartet: Version 0.2.0 und der Datenordner.
Ergebnis: auch hier tab und schließen geht. aber Inhalt sehe ich nur Version aber nicht Datei rdner. also hier auch wieder Darstellungsweise schlecht.


## F. Grundeinstellungen

[ ] 26. Dialog öffnen
Tasten: Alt+E, Enter auf „Grundeinstellungen …“.
Erwartet: Fenster „Grundeinstellungen“. Der Fokus steht im Feld „Projekte-Hauptordner“. Bei den Testdaten steht dort der Testordner.
Ergebnis: funktioniert



[ ] 27. Felder mit Tab
Tasten: Tab, mehrmals.
Erwartet in dieser Reihenfolge: Projekte-Hauptordner, Ordner wählen, Git-Name für Commits, Git-E-Mail-Adresse für Commits, Kontrollkästchen „Neue Repositories privat anlegen“ (aktiviert), Auswahl „Standard-Lizenz für neue Projekte“ (MIT), Kontrollkästchen „Code-Auszüge nur an lokale oder firmeninterne KI senden“, Kontrollkästchen „Neue Projekte mit Branches und Pull Requests“, Speichern, Abbrechen. NVDA liest bei jedem Feld den Namen, auf der Braillezeile stehen nur Name und Art.
Ergebnis: funktioniert

[ ] 28. Falsche Eingabe
Tasten: bei „Git-E-Mail-Adresse“ nur „test“ eintippen, dann Alt+S.
Erwartet: Ein Fenster „Eingabe prüfen“ mit „Bitte eine gültige E-Mail-Adresse eingeben.“ Nach Enter steht der Fokus wieder im Feld Git-E-Mail-Adresse, und der Text ist markiert.
Ergebnis: funktioniert

[ ] 29. Speichern
Tasten: Git-Name „1013hPascal“, Git-E-Mail-Adresse `94653295+1013hPascal@users.noreply.github.com` eintragen, Alt+S.
Erwartet: Das Fenster schließt. NVDA sagt „Grundeinstellungen gespeichert.“ Beim erneuten Öffnen stehen die Werte noch da.
Ergebnis: funktioniert

[ ] 30. Abbrechen
Tasten: Dialog öffnen, etwas ändern, Escape.
Erwartet: Das Fenster schließt ohne Speichern.
Ergebnis: funktioiinert


## G. Neu einlesen und Beenden

[ ] 31. Neues Projekt finden
Tasten: Im Explorer im Testordner `%LOCALAPPDATA%\CodeCockpit\Testdaten\Projekte` einen Ordner „Neu“ mit einem Unterordner „Code“ anlegen. Dann im Cockpit Strg+R.
Erwartet: NVDA sagt „Projekte neu eingelesen. 5 Projekte. Neu: Neu.“ Der Fokus bleibt auf dem Eintrag, auf dem er vorher war.
Ergebnis: funktioniert

[ ] 32. Beenden
Tasten: Strg+Q.
Erwartet: Das Programm schließt ohne Rückfrage und ohne Fehlermeldung.
Ergebnis: funktioniert.

Kommentar von mir:
Also das einzige was nicht so gut klappt sind die listen. und Meldungen sind bei dir auch in eingabefeldern eingabaut, weiß nicht ob das so typisch ist. auch tastenbefehle kannst du ja in eine liste machen. 
Das ein und ausklappen der liste klappt noch nicht so gut auf der hauptebene, weil dann sachen komisch werden. weiß icht, ob die komisch egealdn werden. bei den refeerenzprojekten war das auch schon manchmal der fall. 


## H. Echter Start

[ ] 33. Ohne Testdaten
Tasten: `start.bat` starten.
Erwartet: Titel „CodeCockpit“. NVDA sagt „CodeCockpit bereit. 1 Projekt.“ Im Baum steht „Codecockpit“ mit dem Unterordner „Code“. Es kommt keine Warnung zu Git.
Ergebnis:

[ ] 34. Hochkontrast
Tasten: Windows-Hochkontrast einschalten (linke Alt+linke Umschalt+Druck), Cockpit ansehen, wieder ausschalten.
Erwartet: Alle Texte und die Markierung im Baum sind sichtbar. Dieser Punkt ist nur wichtig, wenn Sie selbst oder eine sehende Person mitprüft.
Ergebnis:


## I. Nachtest nach dem Umbau (25.09.2026)

Nach Ihrem ersten Test habe ich zwei Dinge umgebaut. Der Projektbaum ist jetzt eine Projektliste. Tastenkürzel, Anleitungen, „Über“ und die Fehlerdetails sind jetzt Listen statt Textfelder. Bitte starten Sie `start_testdaten.bat` neu und prüfen Sie die folgenden Punkte. Die Punkte 33 und 34 oben sind auch noch offen.

[ ] 35. Projektliste zugeklappt
Tasten: Pfeil runter, mehrmals, bis ganz unten, dann Pfeil hoch bis ganz oben.
Erwartet: „Neues Projekt hochladen“, „PDF-Chat“, „Tagebuch“, „Bildbeschreiber“, „Notizen, Ordner nicht gefunden“. Keine Unterordner dazwischen. NVDA nennt „Liste“ und die Position, zum Beispiel „2 von 5“.
Ergebnis:

[ ] 36. Ausklappen mit Pfeil rechts
Tasten: auf „PDF-Chat“ Pfeil rechts.
Erwartet: NVDA sagt „Ausgeklappt, 2 Unterordner.“ Der Fokus bleibt auf dem Projekt, es heißt jetzt „PDF-Chat, ausgeklappt“.
Ergebnis:

[ ] 37. In die Unterordner
Tasten: Pfeil rechts, dann Pfeil runter.
Erwartet: „Code“, dann „Exe, PDF-Chat.exe, erstellt am“ mit Datum. Danach mit Pfeil runter „Tagebuch“.
Ergebnis:

[ ] 38. Zuklappen mit Pfeil links
Tasten: auf „Code“ oder „Exe“ Pfeil links.
Erwartet: NVDA sagt „PDF-Chat“ und „Zugeklappt.“ Code und Exe sind aus der Liste verschwunden. Alle Projekte sind mit Pfeil hoch und runter erreichbar.
Ergebnis:

[ ] 39. Leertaste und Enter
Tasten: auf „Tagebuch“ Leertaste, dann noch einmal Leertaste. Danach dasselbe mit Enter.
Erwartet: Beim ersten Druck „Ausgeklappt, 1 Unterordner.“, beim zweiten „Zugeklappt.“ Der Fokus bleibt immer auf Tagebuch.
Ergebnis:

[ ] 40. Nur ein Projekt offen
Tasten: „PDF-Chat“ ausklappen, dann zu „Tagebuch“ gehen und ausklappen.
Erwartet: PDF-Chat klappt dabei zu. In der Liste gibt es nur einmal „Code“, und zwar unter Tagebuch.
Ergebnis:

[ ] 41. Projekt ohne Ordner
Tasten: auf „Notizen, Ordner nicht gefunden“ Enter.
Erwartet: NVDA sagt „Der Ordner wurde nicht gefunden.“ Der Fokus bleibt in der Liste.
Ergebnis:

[ ] 42. Aktionen und Enter auf Exe
Tasten: PDF-Chat ausklappen, auf „Exe“ gehen, Tab, dann Umschalt+Tab, dann Enter.
Erwartet: Tab führt in die Aktionen mit „Exe starten“ und „Exe-Ordner öffnen“. Umschalt+Tab führt zurück auf „Exe“. Enter öffnet das Fehlerfenster, weil die Test-Exe keine echte Exe ist.
Ergebnis:

[ ] 43. Fehlerfenster
Tasten: im Fehlerfenster nichts drücken, dann Tab, Enter auf „Details anzeigen“, Pfeiltasten, Escape.
Erwartet: Beim Öffnen liest NVDA „Exe starten hat nicht geklappt.“ Der Fokus steht auf „OK“. Nach „Details anzeigen“ steht der Fokus in der Liste „Details“, jede Zeile ist mit Pfeiltasten lesbar. Escape schließt, der Fokus ist wieder in der Projektliste.
Ergebnis:

[ ] 44. Tastenkürzel als Liste
Tasten: F1, Pfeil runter mehrmals, Escape.
Erwartet: Eine Liste, jede Zeile mit Funktion und Taste, zum Beispiel „Projekt ausklappen, Pfeil rechts, Leertaste oder Enter“. Alle Zeilen lesbar.
Ergebnis:

[ ] 45. Git-Anleitung als Liste und Kopieren
Tasten: Alt+H, „Git installieren“, Pfeil runter bis zur Zeile mit „winget install“, dann Strg+C.
Erwartet: Jede Zeile der Anleitung ist ein Listeneintrag. Nach Strg+C sagt NVDA „Zeile kopiert.“ In einem Editor lässt sich der Befehl mit Strg+V einfügen.
Ergebnis:

[ ] 46. Über CodeCockpit
Tasten: Alt+H, „Über CodeCockpit“, Pfeil runter.
Erwartet: „CodeCockpit Version 0.2.0“, dann „Datenordner:“ mit dem Pfad, dann zwei Sätze zum Programm.
Ergebnis:

Platz für Ihren Kommentar:
