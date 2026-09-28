# Fragen zu Phase 9: README-Pflege und Versionen

Stand: 29.09.2026. Grundlage: Konzept 10.2 (README-Pflege) und 10.3 (Versionen).

So beantworten Sie die Fragen:

* Jede Frage beginnt mit \[ ].
* Passt mein Vorschlag, schreiben Sie ein x in die Klammer: \[x].
* Wollen Sie etwas anderes, schreiben Sie ein Ausrufezeichen hinein: \[!]. Schreiben Sie Ihre Antwort hinter „Antwort:“.
* Ist etwas unklar, schreiben Sie ein Fragezeichen hinein: \[?].

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.



## Kurz: was das Konzept schon sagt

* Versionen: Beim Hochladen wählen Sie „Kleine Korrektur“, „Neue Funktion“ oder „Große Änderung“. Daraus berechnet das Cockpit die Nummer, zum Beispiel aus 1.3.2 wird 1.3.3, 1.4.0 oder 2.0.0. Die Version wird als Git-Tag gesetzt und im Verlauf angezeigt.
* README: feste Reihenfolge der Abschnitte (Name, Download, Funktionen, Bedienung, Systemanforderungen, Werkzeuge, Installation, Änderungen, Hinweis zu Windows-Warnungen, Lizenz). Welche vorkommen, ist einstellbar.
* Vom Cockpit gepflegte Abschnitte stehen zwischen unsichtbaren Markierungen. Selbst geschriebene Texte werden nie verändert.
* Hauptsprache in README.md, Standard Englisch. Weitere Sprachen in README.de.md und so weiter, oben in jeder Datei Links zu allen Fassungen.



## Fragen

\[x] 1. Aufteilung
Frage: In welchen Schritten bauen wir Phase 9?
Vorschlag: Drei Teilschritte, jeweils mit Checkliste.

* 9a: Versionen mit Tags. Klein und die Grundlage für die Änderungen in der README.
* 9b: README erstellen und pflegen, nur in der Hauptsprache.
* 9c: Weitere Sprachen und die Prüfung der README vor dem Hochladen.
Antwort: in einem schritt

\[x] 2. Keine neue Version
Frage: Nicht jedes Hochladen ist eine neue Version. Was ist die Vorgabe?
Vorschlag: Beim Hochladen steht als vierte Wahl „Keine neue Version“, und das ist die Vorgabe. Eine Version setzen Sie nur, wenn Sie sie wirklich wollen.
Antwort:

\[x] 3. Version im Code
Frage: Das Cockpit selbst hat seine Versionsnummer im Code (**version** in cockpit\_*init*\_.py). Die haben wir bisher von Hand angepasst und dabei einmal vergessen. Soll das Cockpit sie beim Setzen einer Version mitändern?
Vorschlag: Ja. In den Einstellungen des Features steht „Datei mit der Versionsnummer“, freiwillig. Findet das Cockpit eine Zeile wie **version** = "1.2.0", schlägt es die Datei selbst vor. Die Änderung kommt in denselben Commit.
Antwort:

\[x] 4. Versionen und Releases
Frage: „Exe veröffentlichen“ fragt bisher selbst nach der Version und legt den Tag an. Wie passt das zusammen?
Vorschlag: Ist das Feature Versionen an, schlägt „Exe veröffentlichen“ die zuletzt gesetzte Version vor und nutzt ihren Tag. Ohne das Feature bleibt es wie bisher.
Antwort:

\[x] 5. Neue README
Frage: Wie entsteht eine README für ein Projekt, das noch keine hat?
Vorschlag: Aktion „README erstellen …“ auf Code. Das Cockpit sammelt, was es sicher weiß: Name, Kurzbeschreibung von GitHub, Bibliotheken aus requirements.txt, Download-Link, Lizenz. Die KI schreibt Funktionen und Bedienung aus dem Code, ohne Geheimnisse. Sie sehen den Entwurf vorher als Liste, ein Abschnitt pro Zeile, und können ihn übernehmen, bearbeiten oder verwerfen.
Antwort:

\[x] 6. Vorhandene README
Frage: Was passiert mit einer README, die schon da ist, zum Beispiel selbst geschrieben?
Vorschlag: Das Cockpit ändert nichts daran. Es bietet an, fehlende Abschnitte ans Ende anzuhängen, mit Markierung. Nur markierte Abschnitte pflegt es später selbst. Vorher kommt die alte README in die Sicherheitskopien.
Antwort:

\[x] 7. Abschnitte wählen
Frage: Wie wählen Sie, welche Abschnitte vorkommen?
Vorschlag: In den Einstellungen des Features als Liste mit Kontrollkästchen. Vorgabe: alle, außer Lizenzen der Bibliotheken, bis die Lizenzprüfung gebaut ist.
Antwort:

\[x] 8. Sprachen
Frage: Welche Sprachen und welche Hauptsprache?
Vorschlag: Wie im Konzept: Hauptsprache Englisch, weitere Sprachen per Liste mit Kontrollkästchen, Vorgabe Deutsch. Einstellbar in den Grundeinstellungen für neue Projekte und pro Projekt in den Einstellungen des Features.
Antwort:

\[x] 9. Übersetzen
Frage: Wann übersetzt das Cockpit?
Vorschlag: Ändert sich ein markierter Abschnitt in der Hauptsprache, übersetzt die KI nur diesen Abschnitt in die anderen Sprachen. Selbst geschriebene Abschnitte nur nach Rückfrage. Die Übersetzungen sehen Sie vorher.
Antwort:

\[x] 10. Prüfung vor dem Hochladen
Frage: Soll die KI bei jedem Hochladen prüfen, ob die README noch passt? Das dauert bei lokaler KI einige Sekunden.
Vorschlag: Ja, als Schritt im Ablauf „Hochladen“, aber nur, wenn sich Code geändert hat und nicht nur die README. Sie beschreibt Vorschläge in Worten. Wahl: Übernehmen, Bearbeiten, Überspringen. Vorgabe „Überspringen“. Abschaltbar in den Einstellungen des Features.
Antwort:

\[x] 11. Systemanforderungen
Frage: Woher kommen die Systemanforderungen?
Vorschlag: Das Cockpit schlägt sie einmal vor, zum Beispiel „Windows 10 oder 11, 8 GB Arbeitsspeicher, für die Spracheingabe ein Mikrofon“. Sie bestätigen oder ändern sie. Danach stehen sie in cockpit.toml und werden nur auf Wunsch neu vorgeschlagen.
Antwort:

\[x] 12. Branch
Frage: In welchem Branch baue ich Phase 9?
Vorschlag: Sie legen einen neuen Branch mit Ordner an, zum Beispiel „readme-versionen“. Ein kurzer Name vermeidet das Problem mit zu langen Pfaden. Ich baue dort und sage Ihnen, wann Sie ihn in main übernehmen können.
Antwort: ich habe eine mit phase-9 angelegt.



also die readme wenn shcon was da ist, kann er die neuen abschnitte mir geben zum lesen und ich kann dan übernehmen licken. und dann nächsten abschnit, übernehmen oder anpassen irgendwie so. wenn es übernommenist sollnicht merh gekennzeichnet sein, das sieht sonst in der readme komich aus.

