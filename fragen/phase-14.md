# Fragen zu Phase 14: Releases und GitHub Actions

Stand: 29.09.2026. Grundlage: Konzept 10.5 (Releases) und Abschnitt 15, Punkt 14.

So beantworten Sie die Fragen:

* Jede Frage beginnt mit \[ ].
* Passt mein Vorschlag, schreiben Sie ein x in die Klammer: \[x].
* Wollen Sie etwas anderes, schreiben Sie ein Ausrufezeichen hinein: \[!]. Schreiben Sie Ihre Antwort hinter „Antwort:“.
* Ist etwas unklar, schreiben Sie ein Fragezeichen hinein: \[?].

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.



## Kurz: was es schon gibt und was neu dazukommt

* Schon da: „Exe veröffentlichen …“ legt ein Release mit Exe an, „Exe aus dem Release holen …“ holt eine. Das Feature Versionen setzt Tags beim Hochladen.
* Neu: ein Feature „Releases“ für alle Projekte, auch ohne Exe. Dazu eine Übersicht der Releases und eine Übersicht der GitHub Actions: Läufe ansehen, Fehler lesen, neu starten.
* GitHub Actions sind kleine Programme, die GitHub selbst ausführt, zum Beispiel Tests nach jedem Hochladen. Sie stehen im Repository im Ordner .github\\workflows.



## Fragen

\[x] 1. Release nach einer neuen Version
Frage: Soll das Cockpit nach dem Hochladen einer neuen Version ein Release anbieten?
Vorschlag: Ja. Nach dem Hochladen fragt es: „Für Version 1.4.0 ein Release auf GitHub anlegen?“ Vorgabe „Später“. Ist die Exe-Erstellung aktiv, geht es weiter wie bei „Exe veröffentlichen“, mit der Exe. Sonst ein Release nur mit dem Quellcode, den GitHub selbst als ZIP-Datei anhängt.
Antwort:

\[x] 2. Versionshinweise
Frage: Wer schreibt die Versionshinweise, und in welcher Sprache?
Vorschlag: Die KI schlägt sie aus den Commits seit dem letzten Release vor, wie heute schon bei „Exe veröffentlichen“. Sprache ist die Hauptsprache der README. Sie sehen und ändern den Text vor dem Veröffentlichen.
Antwort:

\[x] 3. Übersicht der Releases
Frage: Wie sehen Sie Ihre Releases?
Vorschlag: Auf der Projektzeile „Releases …“. Eine Liste, neueste oben, zum Beispiel „1.4.0, 29.09.2026, 12 Downloads, mit Exe“. Per Tab: „Versionshinweise ansehen“, „Versionshinweise bearbeiten …“, „Link kopieren“, „Im Browser öffnen“, „Release löschen …“. Löschen fragt vorher, Vorgabe „Abbrechen“. Das Tag im Code bleibt dabei.
Antwort:

\[x] 4. Übersicht der GitHub Actions
Frage: Wie sehen Sie die Läufe der GitHub Actions?
Vorschlag: Auf der Projektzeile „GitHub Actions …“, nur wenn das Repository Workflows hat. Eine Liste der letzten Läufe, neueste oben, zum Beispiel „Fehlgeschlagen: Tests, Branch main, 29.09.2026 14:10, Commit „Neue Suche““. Per Tab: „Fehler lesen“, „Neu starten“, „Im Browser öffnen“.
Antwort:

\[x] 5. Fehler lesen
Frage: Was zeigt „Fehler lesen“?
Vorschlag: Den fehlgeschlagenen Schritt und das Ende seiner Ausgabe, eine Zeile pro Zeile, ohne Farbcodes. Darunter, wie im Terminal, eine Erklärung der KI, warum es wahrscheinlich schiefging. Die KI bekommt nur die Ausgabe, ohne Tokens.
Antwort:

\[x] 6. Hinweis in der Projektliste
Frage: Soll die Projektzeile zeigen, wenn der letzte Lauf fehlgeschlagen ist?
Vorschlag: Ja, am Ende der Zeile, zum Beispiel „…, GitHub Actions fehlgeschlagen“. Abgefragt wird zusammen mit den Pull Requests, ohne eigene Ansage.
Antwort:

\[x] 7. Exe in der Cloud bauen
Frage: Mit GitHub Actions könnte GitHub die Exe selbst bauen, jedes Mal wenn Sie eine Version hochladen, und sie ans Release hängen. Ihr Rechner braucht dafür kein PyInstaller. An Smart App Control ändert das aber nichts, die Exe ist weiter nicht signiert. Im Konzept steht das unter „später“. Soll es jetzt schon kommen?
Vorschlag: Noch nicht. Erst die Übersichten und Releases. Die Cloud lohnt sich, wenn später das Signieren dazukommt, zum Beispiel mit SignPath. Beides passt dann gut zusammen.
Antwort:

\[x] 8. Rechte des Zugangs
Frage: Für GitHub Actions braucht der Zugang zu GitHub das Recht, Workflows zu lesen und neu zu starten. Vielleicht hat Ihre Anmeldung dieses Recht noch nicht.
Vorschlag: Das Cockpit prüft das beim ersten Öffnen der Übersicht. Fehlt das Recht, sagt es, was fehlt, und bietet „Neu anmelden …“ an.
Antwort:

\[x] 9. Branch
Frage: In welchem Branch baue ich Phase 14?
Vorschlag: Sie legen einen Branch mit kurzem Namen an, zum Beispiel „releases“. Ich baue dort.
Antwort:

