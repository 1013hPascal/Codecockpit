# Fragen zu Phase 5: Grundfunktionen

Stand: 25.09.2026.

So beantworten Sie die Fragen:

- Jede Frage beginnt mit [ ].
- Passt mein Vorschlag, schreiben Sie ein x in die Klammer: [x].
- Wollen Sie etwas anderes, schreiben Sie ein Ausrufezeichen hinein: [!]. Schreiben Sie Ihre Antwort hinter „Antwort:“.
- Ist etwas unklar, schreiben Sie ein Fragezeichen hinein: [?]. Ich erkläre es dann genauer.
- Mit der Suche nach [ ] finden Sie die Fragen, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## A. Ablauf der Phase

[ ] 1. Phase 5 in Teilschritte aufteilen
Frage: Phase 5 ist sehr groß. Soll ich sie in fünf Teilschritte aufteilen? Jeder Teilschritt bekommt eigene Tests und eine eigene Checkliste, zum Beispiel `checklisten\phase-05a.md`.
Vorschlag: Ja, in dieser Reihenfolge:
- 5a: Git-Grundlage, Git-Identität, Projekte hinzufügen, Umstellen oder Verknüpfen, Reparatur nach dem Verschieben, Stand der Projekte in der Projektliste.
- 5b: Sicherheitsprüfung und .gitignore, Neues Projekt hochladen.
- 5c: Änderungen hochladen, Änderungen holen, Projekt von der Plattform herunterladen.
- 5d: Verlauf und Rückgängig machen, mit Sicherheitskopien.
- 5e: Links, Repository verwalten, Aus der Liste entfernen.
Antwort:

[ ] 2. Test mit Ihrem echten GitHub-Konto
Frage: Ab 5b muss ich echte Repositories anlegen, damit Sie das Hochladen prüfen können. Darf die Checkliste Sie ein privates Test-Repository anlegen lassen?
Vorschlag: Ja. Es heißt „codecockpit-test“, ist privat und wird in 5e mit dem Cockpit wieder gelöscht. Die automatischen Tests arbeiten nie mit GitHub, nur mit einer Attrappe.
Antwort:


## B. Git und Projekte

[ ] 3. Git-Identität in jedem Projekt
Frage: Das Cockpit trägt Name und E-Mail-Adresse aus den Grundeinstellungen in jedes Projekt ein, nur für dieses Repository, nicht für den ganzen Rechner. Was passiert, wenn ein Projekt schon eine andere Identität hat?
Vorschlag: Das Cockpit fragt nach. Die sichere Vorgabe ist „Vorhandene behalten“.
Antwort:

[ ] 4. Projekte, die noch nicht auf der Plattform sind
Frage: Ein Projekt liegt schon im Projekte-Hauptordner, ist aber noch nicht auf GitHub. Wie kommt es hoch?
Vorschlag: Bei „Code“ gibt es dann die Aktion „Auf GitHub hochladen“. Sie läuft wie „Neues Projekt hochladen“, nur ohne das Kopieren. In der Projektliste steht „noch nicht auf GitHub“.
Antwort:

[ ] 5. Name des Haupt-Branches
Frage: Wie soll der Haupt-Branch neuer Repositories heißen?
Vorschlag: „main“, wie es GitHub heute vorgibt.
Antwort:

[ ] 6. Stand in der Projektliste
Frage: Die Projektliste soll zeigen, wie viele Dateien noch nicht hochgeladen sind. Dafür fragt das Cockpit Git bei jedem Projekt. Wann soll das passieren?
Vorschlag: Im Hintergrund beim Start, nach jeder Aktion am Projekt und mit Strg+R. Es gibt dabei keine Ansage und der Fokus bleibt, wo er ist.
Antwort:


## C. Sicherheitsprüfung

[ ] 7. Wie Geheimnisse gefunden werden
Frage: Es gibt fertige Programme, die Geheimnisse im Code finden, zum Beispiel gitleaks. Das wäre ein zusätzliches Programm. Oder das Cockpit bringt eigene Regeln mit.
Vorschlag: Eigene Regeln, ohne neue Bibliothek. Sie erkennen typische Tokens und Schlüssel, zum Beispiel von GitHub, OpenAI, Anthropic, AWS und Azure, dazu private Schlüssel, Zeilen wie `password = "..."` und `.env`-Dateien. Weitere Regeln lassen sich später ergänzen.
Antwort:

[ ] 8. Funde als „kein Geheimnis“ markieren
Frage: Wo merkt sich das Cockpit, dass ein Fund kein Geheimnis ist?
Vorschlag: In `cockpit.toml` des Projekts. Dort steht nur der Dateiname und ein Fingerabdruck der Zeile, nie der Wert selbst. So gilt die Markierung auch auf einem anderen Rechner.
Antwort:

[ ] 9. Große Dateien
Frage: Das Konzept warnt ab 50 MB. GitHub lehnt Dateien über 100 MB ab.
Vorschlag: Ab 50 MB eine Warnung mit Rückfrage. Die Vorgabe ist „In .gitignore aufnehmen“. Ab 100 MB stoppt das Cockpit, weil GitHub die Datei sowieso ablehnen würde.
Antwort:

[ ] 10. Private Daten
Frage: Was passiert bei Datenbanken, Logdateien und ähnlichen Dateien?
Vorschlag: Eine Warnung mit Rückfrage. Die Vorgabe ist „In .gitignore aufnehmen“. Die andere Wahl ist „Trotzdem hochladen“.
Antwort:


## D. Hochladen und Holen

[ ] 11. Welche Dateien hochgeladen werden
Frage: Soll man vor dem Hochladen einzelne Dateien auswählen können?
Vorschlag: Nein. Es werden alle Änderungen hochgeladen, die die Sicherheitsprüfung durchlassen. Was nicht hoch soll, kommt in `.gitignore`. Das hält den Ablauf einfach.
Antwort:

[ ] 12. Lizenzdatei
Frage: Beim neuen Projekt wählt man eine Lizenz. Soll das Cockpit die Datei `LICENSE` selbst anlegen?
Vorschlag: Ja. Den Lizenztext holt es von GitHub und trägt Ihren Namen und das Jahr ein. Bei „Keine Lizenz / firmenintern“ entsteht keine Datei. Liegt schon eine `LICENSE` im Ordner, bleibt sie unverändert.
Antwort:

[ ] 13. Holen, wenn auch hier etwas geändert wurde
Frage: Auf GitHub und hier auf dem Rechner gibt es neue Änderungen. Was macht „Änderungen holen“?
Vorschlag: Betreffen die Änderungen verschiedene Dateien, führt Git sie zusammen. Betreffen sie dieselbe Stelle, macht das Cockpit nichts, stellt den alten Stand wieder her und nennt die betroffenen Dateien (Konzept 9.3).
Antwort:

[ ] 14. Projekt von der Plattform herunterladen
Frage: Wie wählt man das Repository aus?
Vorschlag: Eine Liste Ihrer Repositories und der Repositories Ihrer Organisationen, neueste oben. Als letzter Eintrag „Adresse eingeben …“ für fremde Repositories.
Antwort:


## E. Verlauf und Repository verwalten

[ ] 15. Ausgeführte Feature-Schritte im Verlauf
Frage: Das Konzept zeigt in den Details eines Commits auch die ausgeführten Feature-Schritte. Wo werden sie gespeichert?
Vorschlag: In der Datenbank des Cockpits, nur für Commits, die mit dem Cockpit hochgeladen wurden. Andere Commits zeigen nur Autor und Dateien.
Antwort:

[ ] 16. Recht zum Löschen eines Repositories
Frage: Das Recht zum Löschen fragt das Cockpit erst beim Löschen an (Entscheidung aus Phase 4). Wie genau?
Vorschlag: Bei Anmeldung im Browser startet das Cockpit eine zweite Anmeldung im Browser mit diesem Recht. Der neue Zugang wird nur für das Löschen benutzt und danach verworfen. Bei einem selbst erstellten Token erklärt das Cockpit, welches Recht Sie auf GitHub ergänzen müssen.
Antwort:

[ ] 17. Neue Dateien beim Verwerfen
Frage: Beim Verwerfen von Änderungen kommen neue Dateien in den Papierkorb (Konzept 9.7). Dafür gibt es die Bibliothek send2trash oder eine Funktion von Windows.
Vorschlag: Die Funktion von Windows, ohne neue Bibliothek. Zusätzlich legt das Cockpit wie immer vorher eine Sicherheitskopie an.
Antwort:
