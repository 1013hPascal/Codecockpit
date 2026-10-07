# Konzept: Was vor n8n und E-Mail noch fertig werden sollte

Stand 07.10.2026. Grundlage ist dein Wunschzettel mit den Punkten 1 bis 8. Ich habe dafür den
Code an den betroffenen Stellen gelesen. Fragen an dich stehen ganz unten.

## 0. Was noch offen ist: die neue Projektliste (Branch projektliste-neu)

Die Schritte 1 bis 3 sind fertig, aber noch nicht committet:

- Projekt verwalten, mit Umbenennen und Löschen;
- die Zeile Repository mit der Auswahl der Branches;
- Infos und Umbenennen beim Haupt-Branch.

Diese Tests sind grün: test_projektliste_neu (10 Tests), test_phase5e, test_phase5f,
test_projektuebersichten, test_exe_ki_und_branches, test_phase10f und test_phase10g.
Noch nicht geprüft: test_ui, test_phase5a, test_phase5d, test_phase9, test_phase14,
test_exe_bau_neu, test_repo_loeschen und test_phase8a.

Noch offen:

- Schritt 4: die Zeile Releases mit den Release-Zeilen;
- Schritt 5: Terminal in der Zeile Releases;
- Schritt 6: die Ordner umbenennen, Code wird zu Repository und Exe wird zu Release.

**Vorschlag:** Diesen Branch zuerst fertig machen und nach deinem Test in main überführen. Alle
neuen Punkte bauen auf der neuen Liste auf. Sonst arbeiten zwei Branches an denselben Dateien,
und das gibt beim Zusammenführen Konflikte.

## Reihenfolge und Branches

Jeder Branch ist klein genug, dass du ihn einzeln testen kannst:

1. `projektliste-neu` fertig machen (siehe 0).
2. `hochladen-korrekturen`: Versionsfrage, Textfeld-Falle, Schrittzählung, Töne und Meldungen
   (Punkt 2). Das sind Fehler, deshalb zuerst.
3. `ki-tempo`: schnellere KI, Denktiefe, Starttest und Einstellung (Punkt 8). Das merkst du
   jeden Tag.
4. `listenfilter`: das Auswahlmenü ganz oben und die Markierungen für Offenes (Punkte 1 und 6).
5. `verlauf`: Commits pro Version, Push-Verlauf pro Branch, Rückgängig (Punkt 3).
6. `schnellnavigation`: Schnellnavigation im Kontextmenü und die Tastenhinweise (Punkte 4
   und 5).
7. `hilfe-anleitungen`: das Hilfefenster mit Suche, KI fragen und den Kurzanleitungen
   (Punkt 7). Zum Schluss, wie du es wolltest. Beim Schreiben der Anleitungen prüfe ich jeden
   Weg und notiere, was zu umständlich ist.

## Punkt 2: Hochladen, was ich gefunden habe

### Warum die Versionsfrage mal kommt und mal nicht

Die Frage kommt aus dem Feature Versionen. Es gibt drei Gründe, warum sie fehlt:

- Das Feature ist nur bei manchen Projekten eingeschaltet.
- Die Frage wird übersprungen, wenn es keinen neuen Commit gibt und nichts hochzuladen ist.
- Die Frage kommt nur bei „Änderungen hochladen“. Bei „In main übernehmen“ kommt sie nie.

Der letzte Grund ist der eigentliche Denkfehler. Heute fragt das Cockpit auf jedem Branch,
auch auf einem Neben-Branch wie „suche“. Eine Version gehört aber zu main, denn erst dort ist
die Änderung „fertig“.

**Vorschlag:**

- Die Frage kommt nur, wenn Änderungen auf main ankommen: beim Hochladen direkt auf main und beim
  Übernehmen eines Branches in main.
- Auf Neben-Branches kommt keine Frage. Das Cockpit sagt dann kurz: „Die Version legen Sie fest,
  wenn der Branch in main übernommen wird.“
- Wenn das Feature Versionen bei einem Projekt aus ist, sagt die Aktion „Versionsverlauf“ das und
  bietet „Versionen einschalten“ an.

### Das Textfeld, aus dem man nicht herauskommt

Das ist nicht die Versionsfrage selbst. Nach der Wahl „Kleine Korrektur“ schlägt das Feature
README einen neuen Abschnitt „Änderungen“ vor. Dafür nimmt es ein mehrzeiliges Textfeld. In so
einem Feld schreibt Tab ein Tabzeichen, statt weiterzuspringen. Deshalb kommst du nicht heraus.

**Vorschlag:**

- Der Vorschlag kommt in ein eigenes Fenster:
  - oben steht ein Satz, worum es geht;
  - darunter ein Ausgabefeld, nur lesbar, aber kopierbar, wie an den anderen Stellen;
  - Tab führt zu den Knöpfen „Übernehmen“, „Bearbeiten …“ und „Überspringen“;
  - Shift+Tab führt zurück in den Text;
  - Escape heißt „Überspringen“, also die sichere Antwort.
- Nur „Bearbeiten …“ macht den Text schreibbar. Dort springt Tab trotzdem weiter. Einen
  Zeilenumbruch gibt es mit Enter, und Strg+Enter heißt OK.
- Ich suche alle anderen mehrzeiligen Felder im Programm und gebe ihnen dieselbe Tab-Regel.

### Schritt 3 und 4 vertauscht

Die Schritte werden richtig sortiert. Ich vermute zwei Ursachen:

- Die Ansage für den nächsten Schritt kommt, während die Frage des vorigen Schritts noch offen
  ist. Der Screenreader liest dann zuerst die neue Ansage und danach das Fenster.
- Die Zahl der Schritte hängt davon ab, welche Features eingeschaltet sind. Dann heißt derselbe
  Schritt einmal „Schritt 3“ und ein andermal „Schritt 4“.

**Vorschlag:**

- Ansagen warten, bis eine offene Frage beantwortet ist.
- Schritte ohne Arbeit, etwa „Version hochladen“ ohne neue Version, werden nicht angesagt und
  nicht mitgezählt.
- Ein Test prüft die Reihenfolge der Ansagen.

### Töne und Fertig-Meldung

- Es gibt Windows-Systemklänge über QApplication.beep oder die Windows-Klänge über winsound.
  Dafür braucht es keine neue Bibliothek.
- Beim Start von Hochladen und Herunterladen kommt ein kurzer Ton.
- Bei Erfolg kommt ein heller Ton und eine kurze Meldung, zum Beispiel: „Hochgeladen: 3 Commits
  nach main.“ Die Meldung erscheint als Hinweis unten in der Statuszeile und wird vom
  Screenreader angesagt. Sie ist kein Fenster, das man wegklicken muss.
- Bei einem Fehler kommt der Windows-Fehlerton.
- Unter Einstellungen gibt es einen Schalter „Töne bei Hochladen und Herunterladen“. Er ist
  eingeschaltet.
- Ein Ton, der die ganze Zeit läuft, wäre störend. Ich mache stattdessen alle 10 Sekunden einen
  leisen Tick, solange es läuft. Einverstanden?

## Punkt 8: KI schneller

### Warum es so lange dauert

- Für den Commit-Vorschlag geht der ganze geänderte Code an die KI, ohne Obergrenze. Bei großen
  Änderungen sind das zehntausende Zeichen. Ein lokales Modell (Ollama) muss das zuerst
  „lesen“, und genau das dauert auf dem Rechner am längsten.
- Das Nachdenken ist schon aus. Daran liegt es also nicht.
- Beim ersten Aufruf muss Ollama das Modell erst laden. Das kostet allein oft 10 bis 20 Sekunden.

### Vorschlag

Zwei Stufen: „Kurz“ für Textfelder und „Gründlich“ für Exe, Code und Fehler.

Kurz bekommt nur das Nötigste:

- die Liste der Dateien;
- pro Datei die geänderten Zeilen, gekürzt auf ein festes Budget, zum Beispiel 6000 Zeichen.
  Ganz neue Dateien gehen nur mit Namen und den ersten Zeilen mit.
- Dazu eine kurze Antwortgrenze.

Gründlich bleibt wie heute, das Nachdenken darf eingeschaltet sein.

Weitere Punkte:

- **Vorwärmen:** Beim Start lädt das Cockpit das Modell im Hintergrund, und Ollama behält es
  30 Minuten im Speicher.
- **Starttest (Kalibrierung):** Er läuft einmal pro Modell und Rechner im Hintergrund. Das
  Cockpit ist sofort benutzbar.
  - Er misst mit drei kleinen festen Aufgaben, wie schnell das Modell liest und schreibt.
  - Daraus folgen das Budget für Kurz und Gründlich und die Antwortgrenzen. Ziel für Kurz sind
    5 bis 8 Sekunden.
  - Danach steht im KI-Menü: „KI ist eingestellt auf diesen Rechner.“
- **Einstellung im KI-Menü, so wie du es beschrieben hast:**
  - Tab führt zu einer kurzen Erklärung (Ausgabefeld);
  - Tab führt dann zu „Ergebnisse nicht genau genug …“;
  - mit den Pfeiltasten wählst du „Vorschläge für Textfelder“ oder „Antworten und Bearbeitung
    für Code oder komplexe Fragen“;
  - Tab führt zur Skala von +3 sehr genau bis -3 ungenau. Die Vorgabe ist 0.
  - Jede Stufe nach oben bedeutet mehr Text an die KI, eine längere Antwort und ab +2
    Nachdenken. Die 0 bei Textfeldern ist ungenauer als die 0 bei Code.
- **Wenn ein Vorschlag länger als 15 Sekunden braucht:** Das Cockpit sagt „KI denkt noch …“, und
  Escape bricht ab. Das Feld bleibt dann leer zum Selbstschreiben.

## Punkt 1 und 6: Filter ganz oben und sehen, was offen ist

- Ganz oben in der Liste steht eine Zeile „Anzeigen: Alle Projekte“. Enter öffnet die Auswahl,
  so wie bei der Zeile Repository. Die Auswahl bleibt gespeichert.
- Diese Filter schlage ich vor, etwas klarer benannt als in deinem Wunsch:
  - Alle Projekte;
  - Mit offenen Sachen: Commits nicht hochgeladen, Änderungen nicht committet, Pull Requests,
    Reviews;
  - Auf GitHub (mit oder ohne Release);
  - Mit Release;
  - Nur auf dem Rechner (nicht auf GitHub).
- Deine Punkte „Lokal, GitHub und/oder Release“ und „GitHub und/oder Release“ sind fast gleich,
  denn jedes Projekt in der Liste ist ja lokal. Deshalb mein Vorschlag: „Auf GitHub“ und „Mit
  Release“ getrennt.
- Sammlungen zeigen nur passende Projekte, mit dem Hinweis „2 von 5 Projekten“. Leere
  Sammlungen werden ausgeblendet.
- **Sichtbar machen, was offen ist:** Jede Projektzeile bekommt vorne kleine Zeichen. Die Farbe
  kommt nur aus dem Windows-Thema, nicht fest eingestellt. Die Information steckt immer auch im
  Zeichen, nie nur in der Farbe:
  - ● orange: nicht committet;
  - ↑ blau: nicht hochgeladen;
  - ↓: auf GitHub neuer;
  - PR grün: Pull Request offen;
  - R: Review wartet.

  Der Screenreader liest dieselbe Information kurz als Text, zum Beispiel: „Tagebuch, 2 offen:
  nicht hochgeladen, Pull Request“. Ohne offene Sachen kommt nichts dazu.
- **Modernes Aussehen:** Ich nehme den Qt-Stil „Fusion“ mit hellem und dunklem Thema nach der
  Windows-Einstellung, mehr Abstand in den Zeilen und einen deutlich sichtbaren Fokusrahmen. Das
  geht ohne neue Bibliothek.

## Punkt 3: Verlauf

### Versionsverlauf

- Jede Version ist eine Zeile, zum Beispiel: „Version 1.4.0, 03.10.2026, 5 Commits“.
- Ganz oben steht „In Arbeit (noch keine Version), 2 Commits“.
- Tab springt von der Versionsliste in die Liste ihrer Commits. Jeder Commit zeigt kurz Datum,
  Person und Text, zum Beispiel: „05.10., Pascal: Suche nach PDF verbessert“.
- Enter auf einem Commit zeigt die Details: die geänderten Dateien und auf Wunsch eine
  KI-Zusammenfassung.
- Noch ein Tab führt zu den Aktionen.

### Push-Verlauf pro Branch

- Neue Aktion an jeder Branch-Zeile: „Verlauf …“.
- Jede Zeile ist ein Hochladen, zum Beispiel: „06.10.2026 14:12, Pascal, 3 Commits nach main“.
- Tab führt in die Commits dieses Hochladens.

Ein Hinweis, weil du Git noch nicht so viel benutzt hast: Git selbst merkt sich nicht, wer wann
hochgeladen hat, nur die Commits. GitHub merkt es sich nur ungefähr. Das Cockpit speichert
deshalb ab jetzt jedes eigene Hochladen in seiner Datenbank. Für ältere Zeiten zeige ich die
Commits nach Tagen gruppiert.

### Rückgängig machen

Wichtig zu wissen: Was schon auf GitHub ist, sollte man nicht löschen, denn andere haben es
vielleicht schon. Man macht es mit einem neuen Commit rückgängig, der das Gegenteil enthält
(„revert“). Das ist sicher und ohne force push.

- Am Commit: „Diesen Commit rückgängig machen …“. Das Cockpit erklärt vorher, was passiert,
  fragt nach und macht einen neuen Commit.
- An einer Version: „Zu dieser Version zurück …“. Das Cockpit macht alle Commits danach in einem
  neuen Commit rückgängig. Vorher fragt es nach und legt eine Sicherheitskopie an.
- Noch nicht hochgeladene Commits darf man wirklich entfernen: „Letzten Commit zurücknehmen“.
  Die Änderungen bleiben dabei in den Dateien.

## Punkt 4 und 5: Schnellnavigation und Tastenhinweise

- Kontextmenü (Shift+F10 oder Menütaste) auf einem ausgeklappten Projekt. Der erste Eintrag ist
  „Schnellnavigation Tagebuch“. Danach kommen:
  - Hilfe (mit „KI chatten“);
  - Tastenbefehle;
  - Projekt verwalten;
  - Repository verwalten;
  - Branches verwalten;
  - Releases verwalten.
- Jeder Eintrag bekommt eine Zifferntaste: 1 Hilfe, 2 Tasten und so weiter.
- **Zusätzlicher Vorschlag:** Strg+K öffnet überall eine Befehlssuche. Man tippt „hoch“, und
  „Änderungen hochladen“ steht oben. Das ist heute in vielen Programmen Standard und spart die
  meisten Wege durch Menüs.
- **Tastenhinweise:** Hier gibt es einen Konflikt mit unserer Regel in CLAUDE.md: „Keine
  Accessible Description, weil sie die Braillezeile überlädt.“ Der übliche Standard wäre genau
  diese Beschreibung. Mein Vorschlag, der die Braillezeile frei lässt:
  - Sehende sehen die Tasten als Tooltip und in der Statuszeile, zum Beispiel: „Enter öffnet die
    Auswahl, Pfeil rechts klappt auf“.
  - Mit Strg+F1 sagt das Cockpit für das Element mit dem Fokus kurz: „Tasten hier: …“. Das hörst
    du nur, wenn du fragst.
  - Nur da, wo es nicht selbstverständlich ist: Listen mit Pfeil rechts zum Ausklappen, Tab
    zwischen Listen, Strg+Enter und Ähnliches. Bei einfachen Knöpfen schreibe ich nichts dazu.
  - Wenn du die Tasten doch im Namen selbst haben willst, etwa „Branches anzeigen, Enter“, ändere
    ich die Regel. Sag mir dann Bescheid.

## Punkt 7: Hilfe mit Kurzanleitungen (zum Schluss)

- Das Hilfefenster ist ein eigenes Fenster und nicht modal. Man kann mit Alt+Tab oder F6
  zurück ins Cockpit springen. F1 öffnet es überall.
- Aufbau von oben nach unten:
  - Suchfeld;
  - „KI fragen …“;
  - die Liste der Anleitungen;
  - darunter der Text der gewählten Anleitung als Ausgabefeld.
- Ohne Suche stehen die Anleitungen für den aktuellen Bereich oben. Auf der Startebene sind das
  zum Beispiel „Ordner hinzufügen“ und „Sammlung erstellen“, an einer Branch-Zeile „In main
  übernehmen“ und „Pull Request stellen“.
- Jede Anleitung hat das Schema „Schritt 1: …“, mit den Tasten, zum Beispiel: „Schritt 2:
  Drücken Sie Pfeil rechts, um das Projekt aufzuklappen.“
- KI fragen sucht zuerst in den Anleitungen. Wenn es nichts findet, bekommt die KI die Liste
  aller Aktionen mit Zeile und Taste. Daraus schreibt sie die Schritte. Sie bekommt keinen Code,
  deshalb geht es schnell.
- Die Anleitungen liegen als Textdateien im Programm. Ein Test prüft, dass jede genannte Aktion
  wirklich existiert. So fällt jede veraltete Anleitung auf.
- Alle deine Themen kommen hinein. Dazu kommen:
  - Konflikt beim Zusammenführen lösen;
  - Branch auf den neuen Stand von main bringen;
  - Änderungen verwerfen;
  - Sicherheitskopie zurückholen;
  - Exe testen, bevor man sie veröffentlicht.

## Was mir sonst noch fehlt oder zu umständlich ist

- **Konflikte beim Zusammenführen:** Wenn zwei Branches dieselbe Zeile ändern, braucht es eine
  geführte Hilfe: welche Datei, „meine Version / die andere / beide“. Das ist wohl die häufigste
  Hürde für Git-Neulinge. Ich würde es in den Branch `verlauf` nehmen.
- **Ein Knopf für den Alltag:** „Speichern und hochladen“ macht Commit, Hochladen und Pull Request
  in einem Weg, mit KI-Vorschlag für den Text. Heute sind das mehrere Aktionen.
- **Branch aktuell halten:** Ist main weiter, bietet die Branch-Zeile „main übernehmen“ an. Sonst
  gibt es später große Konflikte.
- **Änderungen verwerfen:** Für eine einzelne Datei oder für alles, mit Sicherheitskopie. Ich
  habe die Aktion nicht gefunden. Falls es sie schon gibt, ist sie zu versteckt.
- **Startansicht:** Beim Start wäre es gut, sofort zu hören: „3 Projekte mit offenen Sachen“.
- **Gesperrte Exe:** Noch offen von früher: Das Cockpit nennt das Programm, das die Exe sperrt,
  und bietet „Programm beenden“ an.

## Fragen an dich

1. Soll ich projektliste-neu zuerst fertig machen und überführen, bevor die neuen Branches
   beginnen?
2. Version nur, wenn es nach main geht: einverstanden?
3. Töne: einverstanden mit einem Ton bei Start und Ende und einem leisen Tick alle 10 Sekunden?
   Oder lieber nur bei Start und Ende?
4. Filter: einverstanden mit den fünf Filtern aus Punkt 1 und 6, also „Auf GitHub“ und „Mit
   Release“ getrennt?
5. Strg+K als Befehlssuche dazu: ja oder nein?
6. „Speichern und hochladen“ als Ein-Knopf-Weg: ja oder nein?
7. Tastenhinweise: Tooltip plus Strg+F1, oder doch im Namen? Das Zweite ändert eine Regel in
   CLAUDE.md.
