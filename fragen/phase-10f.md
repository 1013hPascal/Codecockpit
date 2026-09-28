# Fragen zu 10f: Ein Ordner pro Branch

Stand: 28.09.2026.

So beantworten Sie die Fragen:

- Jede Frage beginnt mit [ ].
- Passt mein Vorschlag, schreiben Sie ein x in die Klammer: [x].
- Wollen Sie etwas anderes, schreiben Sie ein Ausrufezeichen hinein: [!]. Schreiben Sie Ihre Antwort hinter „Antwort:“.
- Ist etwas unklar, schreiben Sie ein Fragezeichen hinein: [?].

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.


## Kurz: das Konzept

- Der Ordner Code enthält nur noch Ordner: `Code\main` und daneben einen Ordner pro Branch, zum Beispiel `Code\neue-funktion`.
- Technisch nutzt das Cockpit dafür die Git-Funktion „Worktree“. Alle Ordner teilen sich ein Repository. Ein Commit im Ordner neue-funktion landet immer im Branch neue-funktion.
- Sie können Claude in einem Branch-Ordner öffnen. Dann arbeitet Claude nur in diesem Branch.
- Das Cockpit merkt sich pro Projekt den Ordner main. Exe-Bau, cockpit.toml und alles andere arbeiten von dort aus wie bisher.
- Projekte mit der alten Struktur laufen weiter wie bisher. Umstellen geht per Aktion.
- Ein Branch-Name mit Schrägstrich wie `feature/login` wird zum Ordnernamen `feature-login`.


## Fragen

[x] 1. Anzeige in der Projektliste
Frage: Wie sehen Sie die Branch-Ordner im Cockpit?
Vorschlag: Unter „Code“ steht pro Ordner ein eigener Eintrag, zum Beispiel „main, 2 Dateien noch nicht hochgeladen“ und „neue-funktion, aktuell“. Jeder Eintrag hat seine eigenen Aktionen: Hochladen, Verlauf, Terminal, Ordner öffnen, Pull Request. So sehen Sie den Stand aller Branches auf einen Blick. Der Eintrag „Code“ selbst zeigt den Stand von main.
Die andere Möglichkeit: Es bleibt ein Eintrag „Code“. „Branch wechseln“ schaltet nur um, in welchem Ordner das Cockpit arbeitet. Das ist näher an heute, aber Sie sehen immer nur einen Branch.
Antwort: so wie du vorschlägst, ist glaube ich sinniger. besserer überblick.

[x] 2. Neuer Branch
Frage: Was passiert beim Anlegen eines Branches in einem umgestellten Projekt?
Vorschlag: Er bekommt immer einen eigenen Ordner. Vorher holt das Cockpit den neuesten Stand von main von GitHub. Der neue Ordner startet mit diesem Stand.
Antwort: so ist das ja glaube ich auch auf github

[x] 3. Branch, den es nur auf GitHub gibt
Frage: Was passiert mit einem Branch, den zum Beispiel ein Mitarbeiter auf GitHub angelegt hat?
Vorschlag: Er steht unter Code als „nur auf GitHub“. Enter fragt, ob er heruntergeladen werden soll, und legt dann seinen Ordner an.
Antwort: Kommentar dazu unten

[x] 4. Branch fertig
Frage: Was passiert, wenn ein Branch in main übernommen wurde?
Vorschlag: Das Cockpit bietet an, den Ordner zu entfernen. Gibt es darin noch Änderungen, die nicht hochgeladen sind, kommt der Ordner vorher in die Sicherheitskopien. Vorgabe ist „Behalten“.
Antwort:

[x] 5. Virtuelle Umgebung (.venv)
Frage: Jeder Ordner braucht für Python eine eigene virtuelle Umgebung. Wann wird sie angelegt?
Vorschlag: Hat main eine .venv, legt das Cockpit beim Anlegen des Branch-Ordners auch dort eine an, im Hintergrund, mit denselben Bibliotheken. Dann können Sie und Claude dort sofort Tests laufen lassen.
Antwort:

[!] 6. Exe
Frage: Aus welchem Ordner wird die Exe gebaut?
Vorschlag: Immer aus main. Eine Exe aus einem Branch zum Ausprobieren kommt später dazu, falls Sie das brauchen.
Antwort: ja, exe aus branch wäre auch nicht schlecht. die soll dann unter exe kommen und den namen cockpit_branch_name.ede also name ist ein Platzhalter

[x] 7. Neue Projekte
Frage: Bekommen neue Projekte gleich die neue Struktur?
Vorschlag: Ja, beim Herunterladen von GitHub, beim Anlegen und beim Hinzufügen vom Rechner. Dafür gibt es einen Schalter in den Grundeinstellungen: „Neue Projekte mit einem Ordner pro Branch“, Vorgabe an. Beim Hinzufügen fragt das Cockpit, welcher Branch der Ordner ist, wenn er nicht auf main steht.
Antwort: Ja

[x] 8. Bestehende Projekte umstellen
Frage: Wie werden bestehende Projekte umgestellt?
Vorschlag: Aktion „Ordner für Branches einrichten …“ auf Code. Sie sagt vorher, was passiert: Der Inhalt von Code wandert nach `Code\main`. Gibt es nicht hochgeladene Änderungen, bleiben sie erhalten. Vorher wird eine Sicherheitskopie angelegt. Die virtuelle Umgebung wird danach repariert, weil sie feste Pfade enthält. Andere lokale Branches bekommen erst einen Ordner, wenn Sie sie öffnen.
Antwort: ja

[ ] 9. Feature oder fester Teil
Frage: Wo gehört das hin?
Vorschlag: Die Branch-Ordner gehören zum Feature „Branches und Pull Requests“. Ist das Feature aus, arbeitet das Cockpit nur mit main. Dass es `Code\main` gibt, erkennt der Kern immer.
Antwort: nein fester Teil

[x] 10. Nur verknüpfte Projekte
Frage: Gilt das auch für Projekte, deren Ordner nur verknüpft sind?
Vorschlag: Vorerst nicht. Dort bleibt alles wie bisher.
Antwort:

[!] 11. Das Cockpit selbst und Claude
Frage: Wie stellen wir das Cockpit selbst um?
Vorschlag: Zum Schluss, wenn alles getestet ist. Sie beenden dafür Claude und das Cockpit. Wichtig: Claude merkt sich Einstellungen und Erinnerungen pro Ordner. Nach dem Umzug nach `Code\main` kopiere ich diese Daten in den neuen Ordner, damit nichts verloren geht. Danach starten Sie Claude in `Code\main`.
Antwort: also das ist kein Problem sobald die neue exe da ist, kann ich mein projekt, das in der exe ist, umbauen. so mache ich es auch gerade. also ich tue gerade so, als wäre das projekt ein projekt in meinem Programm. 

[x] 12. Update-Test
Frage: Soll das die Version 1.1.1 werden, mit der wir das Update testen?
Vorschlag: Ja. Sie veröffentlichen vorher 1.1.0 und starten diese. Nach 10f bauen und veröffentlichen Sie 1.1.1. Die laufende 1.1.0 sollte sich dann melden.
Antwort: ja, wie gesagt, ich  utze das Programm ja, habe es woander hinkompiert. sobald eine neue exe da ist, sollte mein Programm danach fragen. 


Kommentar:
also bei den branches, dass können ja auch echt viele werden. 
vielleihct, bei eigenem branch, die in der liste anzeigen. 
und bei externe branches, also branches von anderen usern, das so machen, wie es bei main ist, gerade, dann klickt man au fextern, kann dann branches auswählen. der wird dann in der liste angezeigt. bei dem sollte man dann im aktionsmenü in liste anpinnen machen, dann taucht es bei den eigenen branches auch auf. so kann man das mitverfolgen. 
irgendwie so.