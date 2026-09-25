# CodeCockpit bei GitHub als OAuth-App registrieren

Diese Anleitung brauchen Sie nur einmal, als Entwickler des Cockpits. Nutzer des Cockpits müssen das nicht machen.

Die Registrierung ist nötig für „Mit GitHub anmelden“. Dabei entsteht eine Client-ID. Sie ist öffentlich und kein Geheimnis. Sie steht später fest im Programm.

Dauer: etwa fünf Minuten.


## Schritte

1. Öffnen Sie im Browser diese Seite. Sie müssen bei GitHub angemeldet sein:
   https://github.com/settings/applications/new
2. Füllen Sie das Formular aus:
   - Application name: CodeCockpit
   - Homepage URL: https://github.com/1013hPascal
   - Application description: kann leer bleiben
   - Authorization callback URL: http://127.0.0.1
3. Kreuzen Sie das Kästchen „Enable Device Flow“ an. Das ist wichtig. Ohne diesen Haken funktioniert die Anmeldung im Browser nicht.
4. Wählen Sie „Register application“.
5. Es öffnet sich die Seite der neuen App. Dort steht „Client ID“, gefolgt von einer Zeichenkette, die mit „Ov23“ oder „Iv1“ beginnt.
6. Kopieren Sie die Client-ID und geben Sie sie mir im Terminal.


## Wichtig

- Wählen Sie nicht „Generate a new client secret“. Das Cockpit braucht kein Client Secret. Ein Secret dürfte ohnehin nicht im Programm stehen.
- Die Callback-Adresse http://127.0.0.1 wird nie benutzt. GitHub verlangt nur, dass dort etwas steht.
- Sie können die App jederzeit unter Settings, Developer settings, OAuth Apps wieder löschen. Dann funktioniert „Mit GitHub anmelden“ nicht mehr, Tokens bleiben aber gültig, bis Sie sie widerrufen.
