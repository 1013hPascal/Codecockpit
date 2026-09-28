# Checkliste Phase 9: Versionen und README-Pflege

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Testen Sie am besten mit einem kleinen Projekt, zum Beispiel der VokabelApp. Schalten Sie dort in „Features dieses Projekts …“ die Features Versionen und README-Pflege ein. Die README-Pflege braucht eine Text-KI.


## Versionen

[ ] 1. Frage beim Hochladen
Tasten: Eine Datei ändern, auf Code „Änderungen hochladen …“, Commit-Nachricht, Enter.
Ansage: Nach der Sicherheitsprüfung die Auswahl „Version“ mit „Ist das eine neue Version? Bisher: noch keine.“ Zur Wahl: „Keine neue Version“, „Kleine Korrektur, Version 1.0.0“, „Neue Funktion, Version 1.0.0“, „Große Änderung, Version 1.0.0“. Markiert ist „Keine neue Version“.
Fokus: In der Auswahl.
Ergebnis:

[ ] 2. Neue Version setzen
Tasten: „Neue Funktion …“ wählen, Enter.
Ansage: Am Ende „Fertig. Commit „…“. Version 1.0.0. Branch main ist hochgeladen.“
Auf GitHub: Unter Tags steht v1.0.0.
Ergebnis:

[ ] 3. Nächste Version
Tasten: Noch eine Änderung hochladen, „Kleine Korrektur“ wählen.
Ansage: In der Auswahl steht „Bisher: 1.0.0.“ und „Kleine Korrektur, Version 1.0.1“. Am Ende „Version 1.0.1.“
Ergebnis:

[ ] 4. Verlauf
Tasten: Auf Code „Verlauf …“.
Ansage: Die Zeile des Commits nennt „Version 1.0.1“.
Fokus: Im Verlauf.
Ergebnis:

[ ] 5. Nummer im Code
Tasten: Beim Cockpit selbst, im Branch-Ordner, Version einschalten und eine Änderung hochladen, „Kleine Korrektur“.
Ansage: Wie oben.
Im Code: In cockpit\__init__.py steht die neue Nummer, im selben Commit. Es bleibt keine Datei „noch nicht hochgeladen“.
Ergebnis:

[ ] 6. Exe veröffentlichen
Tasten: Nach einer neuen Version auf Exe „Exe veröffentlichen …“.
Ansage: Im Feld Version steht die eben gesetzte Nummer.
Fokus: Im Feld Version.
Ergebnis:


## README erstellen

[ ] 7. Aktion
Tasten: Auf der Projektzeile eines Projekts ohne README, Tab.
Ansage: „README erstellen …“ und „README-Sprachen …“.
Ergebnis:

[ ] 8. Abschnitte einzeln
Tasten: Enter auf „README erstellen …“.
Ansage: „Die README wird vorbereitet.“, leise in der Statuszeile, welchen Abschnitt die KI gerade schreibt. Dann ein Fenster „README, Englisch: Download, 1 von …“. Im Textfeld der Abschnitt.
Fokus: Im Textfeld.
Ergebnis:

[ ] 9. Übernehmen, anpassen, überspringen
Tasten: Beim ersten Abschnitt Alt+B, beim zweiten den Text ändern und Alt+B, beim dritten Alt+R, beim vierten Escape.
Ansage: Jeweils der nächste Abschnitt. Escape überspringt wie Alt+R.
Fokus: Im Textfeld des nächsten Abschnitts.
Ergebnis:

[ ] 10. Übersetzungen
Tasten: Nach dem letzten Abschnitt der Hauptsprache warten.
Ansage: „Die Übersetzungen werden vorbereitet.“, dann Fenster „README, Deutsch: …“ für die übernommenen Abschnitte, auch einzeln.
Am Ende: „README geschrieben: README.de.md, README.md.“
Ergebnis:

[ ] 11. Ergebnis
Tasten: Auf der Projektzeile „README ansehen“.
Ansage: Oben „# Name“, dann „English | [Deutsch](README.de.md)“, dann die übernommenen Abschnitte. Keine Markierungen und keine Kommentare im Text.
Ergebnis:

[ ] 12. Alle abbrechen
Tasten: „README bearbeiten …“, dann Alt+K für „Vorschläge der KI …“, im ersten Fenster Alt+A.
Ansage: „Abgebrochen.“ Die README ist unverändert.
Ergebnis:


## README pflegen

[ ] 13. Eigene Texte bleiben
Tasten: „README bearbeiten …“, einen übernommenen Abschnitt im Text ändern, Alt+S. Dann noch einmal „README bearbeiten …“ und „Vorschläge der KI …“.
Ansage: Dieser Abschnitt wird nicht mehr vorgeschlagen. Unveränderte Abschnitte des Cockpits kommen nur, wenn sich etwas geändert hat, zum Beispiel nach einer neuen Version.
Ergebnis:

[ ] 14. Sprachen eines Projekts
Tasten: Auf der Projektzeile „README-Sprachen …“. Hauptsprache auf Deutsch, bei den weiteren Sprachen Englisch anhaken, Speichern.
Ansage: „README-Sprachen gespeichert.“ Bei den nächsten Vorschlägen der KI ist README.md deutsch.
Fokus: Zurück in der Aktionsliste.
Ergebnis:

[ ] 15. Prüfung vor dem Hochladen
Tasten: Eine Funktion im Code ergänzen, „Änderungen hochladen …“.
Ansage: Nach der Commit-Nachricht leise „Die KI prüft die README.“ Hat sie einen Vorschlag: Fenster „README: Features“ mit dem Grund und dem neuen Text. OK übernimmt, Abbrechen überspringt.
Am Ende: „README angepasst.“ in der Zusammenfassung, wenn Sie übernommen haben. Die Änderung ist im selben Commit.
Ergebnis:

[ ] 16. Nur README geändert
Tasten: Nur die README ändern und hochladen.
Ansage: Keine Prüfung der README.
Ergebnis:

[ ] 17. Prüfung ausschalten
Tasten: Feature-Verwaltung, README-Pflege, Einstellungen, „Vor dem Hochladen prüfen …“ ausschalten.
Ansage: Beim nächsten Hochladen keine Prüfung.
Ergebnis:

[ ] 18. README bearbeiten
Tasten: Auf der Projektzeile „README bearbeiten …“. Gibt es mehrere Sprachen, erst die Datei wählen. Im Text etwas ändern, Alt+S.
Ansage: „README.md gespeichert. Die alte steht in den Sicherheitskopien.“ Escape mit ungespeicherten Änderungen fragt „Verwerfen?“, Vorgabe „Zurück“.
Fokus: Im Textfeld, nach dem Speichern zurück in der Aktionsliste.
Ergebnis:

[ ] 19. Neue Version ergänzt die README
Tasten: Etwas im Code ändern, „Änderungen hochladen …“, bei der Version „Neue Funktion“ wählen. Das geht auch, wenn die Prüfung vor dem Hochladen ausgeschaltet ist.
Ansage: Erst ein Fenster „README: Änderungen“ (oder „Changes“) mit der neuen Version und den Commits seit der letzten. Danach die Vorschläge der KI für andere Abschnitte, zum Beispiel „README: Funktionen“. OK übernimmt, Abbrechen überspringt.
Am Ende: „Version … README angepasst.“ Alles ist im selben Commit.
Ergebnis:
