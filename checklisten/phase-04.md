# Checkliste Phase 4: GitHub-Anbindung

Stand: 25.09.2026. Getestet wird mit NVDA und Braillezeile.

So füllen Sie die Checkliste aus:

- Jeder Prüfpunkt beginnt mit [ ].
- Hat alles gepasst, schreiben Sie ein x in die Klammer: [x].
- Gab es ein Problem, schreiben Sie ein Ausrufezeichen hinein: [!]. Beschreiben Sie das Problem kurz hinter „Ergebnis:“.
- Mit der Suche nach [ ] finden Sie die Punkte, die noch offen sind.

Wenn Sie fertig sind, speichern Sie die Datei und sagen Sie mir im Terminal Bescheid.

Hinweis: Ansagen in Dialogen sind noch ein offener Punkt (TODO.md). Wo hier eine Ansage erwartet wird, notieren Sie bitte nur, ob sie kam. Wichtige Ergebnisse erscheinen zusätzlich als Meldungsfenster.


## Vorbereitung

1. Die OAuth-App ist registriert (25.09.2026). „Im Browser anmelden“ ist damit verfügbar.
2. Die ganze Checkliste, alle Abschnitte A bis D, testen Sie mit `start_testdaten.bat`, nicht mit `start.bat`. Nur dort erscheint der Einrichtungsassistent bei jedem Start neu, den Abschnitt B braucht. Sie melden sich dabei mit Ihrem echten GitHub-Konto an. Die Zugangsdaten landen dann unter dem Namen „CodeCockpit Testdaten“ und werden beim nächsten Start mit Testdaten gelöscht. Ihre echten Daten bleiben unberührt.
3. Das Cockpit legt in dieser Phase nichts auf GitHub an und löscht nichts. Es liest nur Ihr Konto und Ihre Organisationen.


## A. Menü Hilfe

[ ] 1. Anleitung für den Token
Tasten: Alt+H, „GitHub-Token erstellen …“, Enter, Pfeiltasten.
Erwartet: Eine Liste mit der Anleitung. Die Zeile mit der Adresse „https://github.com/settings/personal-access-tokens/new“ lässt sich mit Strg+C kopieren. Escape schließt.
Ergebnis:


## B. Anmeldung im Browser

[ ] 2. Einrichtungsassistent: Seite GitHub-Konto
Tasten: Im Assistenten bis Schritt 4 mit Alt+W.
Erwartet: „Schritt 4 von 7: GitHub-Konto“. Der Fokus steht in der Liste „Erklärung“. Mit Tab kommen Sie zu „GitHub-Konto einrichten …“.
Ergebnis:

[ ] 3. Ohne Konto weiter
Tasten: Alt+W.
Erwartet: Meldung „Es ist noch kein GitHub-Konto eingerichtet. …“. Nach OK steht der Fokus auf „GitHub-Konto einrichten …“.
Ergebnis:

[ ] 4. Konto-Fenster
Tasten: Alt+E (GitHub-Konto einrichten).
Erwartet: Fenster „Neues Konto: GitHub“. Felder: Anzeigename, Benutzername, Serveradresse (https://github.com), Token. Dann „Verbindung testen“, „Speichern“, „Im Browser anmelden …“, „Abbrechen“.
Ergebnis:

[ ] 5. Im Browser anmelden: Code
Tasten: Alt+B.
Erwartet: Fenster „Mit GitHub anmelden“. Der Fokus steht in der Liste „Anmeldung“, die erste Zeile lautet „Ihr Code:“ mit acht Zeichen und einem Bindestrich. Die Zeilen darunter erklären die Schritte. Der Browser öffnet die Seite github.com/login/device.
Ergebnis:

[ ] 6. Im Browser bestätigen
Tasten: Im Browser anmelden, falls nötig. Den Code mit Strg+V einfügen, „Continue“, dann „Authorize CodeCockpit“. Danach mit Alt+Tab zurück ins Cockpit.
Erwartet: Das Fenster „Mit GitHub anmelden“ schließt sich von selbst. Im Konto-Fenster steht beim Benutzernamen „1013hPascal“, der Anzeigename lautet „GitHub 1013hPascal“. Das Feld Token ist leer, NVDA liest eventuell den Hinweis „Über die Anmeldung im Browser erhalten“.
Ergebnis:

[ ] 7. Verbindung testen nach der Anmeldung
Tasten: Alt+V.
Erwartet: Kurz „Verbindung wird getestet …“, dann eine Meldung „Verbindung in Ordnung. Angemeldet als 1013hPascal.“, falls Sie Mitglied in Organisationen sind, auch deren Namen. Während des Tests ist „Verbindung testen“ gesperrt.
Ergebnis:

[ ] 8. Speichern
Tasten: Alt+S.
Erwartet: Das Fenster schließt. Im Assistenten führt Alt+W jetzt weiter zu „Projekte-Hauptordner“.
Ergebnis:

[ ] 9. Anonyme Adresse übernehmen
Tasten: Weiter bis „Git-Identität“, Tab bis „Anonyme GitHub-Adresse übernehmen“, Enter.
Erwartet: Im Feld Git-Name steht „1013hPascal“, im Feld Git-E-Mail-Adresse „94653295+1013hPascal@users.noreply.github.com“. Der Fokus steht im Feld E-Mail-Adresse.
Ergebnis:

[ ] 10. Anmeldung abbrechen
Tasten: Später in der Kontenverwaltung ein neues GitHub-Konto anlegen, Alt+B, dann im Fenster „Mit GitHub anmelden“ Tab bis „Abbrechen“, Enter.
Erwartet: Das Fenster schließt sofort, nichts wird gespeichert.
Ergebnis:


## C. Anmeldung mit Token

[ ] 11. Falscher Token
Tasten: Kontenverwaltung, „Neues Konto anlegen …“, Kontoart „GitHub, Plattform“. Im Feld Token „falsch“ eintragen, Alt+V.
Erwartet: Fehlermeldung „Der Token wurde abgelehnt. Er ist abgelaufen, widerrufen oder falsch kopiert.“ Unter „Details anzeigen“ steht „HTTP 401“. Der Token selbst steht nirgends.
Ergebnis:

[ ] 12. Selbst erstellter Token (freiwillig)
Tasten: Einen Token nach der Anleitung aus Punkt 1 erstellen und im Feld Token einfügen, Alt+V.
Erwartet: „Verbindung in Ordnung. Angemeldet als 1013hPascal.“ Der Benutzername wird selbst eingetragen.
Ergebnis:


## D. Ohne Internet

[ ] 13. Keine Verbindung
Tasten: WLAN ausschalten oder Netzwerkkabel ziehen. Dann in der Kontenverwaltung Ihr GitHub-Konto markieren, Tab bis „Verbindung testen“, Enter.
Erwartet: Fehlermeldung „GitHub ist nicht erreichbar. Bitte prüfen Sie die Internetverbindung.“ Danach das Netz wieder einschalten.
Ergebnis:

Platz für Ihren Kommentar:
