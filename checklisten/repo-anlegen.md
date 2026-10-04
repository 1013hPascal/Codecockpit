# Checkliste: Repository anlegen, wenn es fehlt, und Adresse nach dem Löschen entfernen

Tragen Sie bei jedem Punkt [x] für OK oder [!] für ein Problem ein. Unter „Ergebnis:“ ist Platz für Ihre Anmerkung.

Starten Sie das Cockpit aus dem Ordner Code\main, nachdem Sie hochgeladen haben, oder aus der neuen Exe.


[ ] 1. Chatbot für Text: Rückfrage beim Einlesen
Tasten: Projektzeile „Chatbot für Text“, „Projekt neu einlesen“.
Ansage: Rückfrage „Das Repository 1013hPascal/Chatbot-fuer-Text gibt es auf GitHub noch nicht. Jetzt anlegen und hochladen? …“ mit „Jetzt anlegen …“ und „Später“ (Vorgabe, auch mit Escape).
Ergebnis:

[ ] 2. Gut sichtbar in den Aktionen
Tasten: Nach „Später“ Tab in die Aktionen der Projektzeile.
Ansage: Oben steht „Repository auf GitHub anlegen und hochladen …“. Bei Code steht „Auf GitHub hochladen …“, nicht „Änderungen auf GitHub hochladen …“.
Ergebnis:

[ ] 3. Projekt verwalten
Tasten: „Projekt verwalten …“.
Ansage: Statt einer Fehlermeldung kommt dieselbe Rückfrage wie in Punkt 1.
Ergebnis:

[ ] 4. Anlegen und hochladen
Tasten: „Repository auf GitHub anlegen und hochladen …“.
Ansage: Das Fenster zum Hochladen schlägt den Namen Chatbot-fuer-Text vor. Nach dem Hochladen gibt es das Repository auf GitHub, und der Code ist dort. Die Aktion zum Anlegen ist verschwunden.
Ergebnis:

[ ] 5. Projekt ohne Repository einlesen
Tasten: Bei einem Projekt, das noch nie auf GitHub war, „Projekt neu einlesen“.
Ansage: Rückfrage „… ist noch nicht auf GitHub. Jetzt hochladen? …“, Vorgabe „Später“.
Ergebnis:

[ ] 6. Löschen entfernt die Adresse
Tasten: Ein Test-Repository über „Projekt verwalten …“ löschen, danach „Aus der Liste entfernen“ wählen. Den Ordner wieder mit „Projekt vom Rechner hinzufügen“ aufnehmen.
Ansage: Die Meldung nach dem Löschen sagt „Die Verbindung zum gelöschten Repository ist entfernt.“ Nach dem Hinzufügen heißt das Projekt „noch nicht auf GitHub“, und das Cockpit bietet das Hochladen an.
Ergebnis:

[ ] 7. Löschen eines Repositorys nur auf GitHub
Tasten: Bei „nur auf GitHub“ ein Repository löschen, zu dem es auf dem Rechner noch einen Ordner gibt.
Ansage: „… ist auf GitHub gelöscht. Verbindung entfernt bei: …“ mit dem Namen des Projekts.
Ergebnis:
