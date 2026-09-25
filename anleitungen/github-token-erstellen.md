# GitHub-Token selbst erstellen

Diese Anleitung brauchen Sie nur, wenn Sie nicht „Mit GitHub anmelden“ nutzen. Zum Beispiel, weil Ihre Firma das vorschreibt.

Ein Token ist wie ein Passwort nur für das Cockpit. Er hat genau die Rechte, die Sie auswählen, und läuft nach der gewählten Zeit ab. Sie können ihn jederzeit widerrufen.

Tipp: In CodeCockpit kopiert Strg+C die markierte Zeile. So können Sie die Adresse unten kopieren.


## Token erstellen

1. Öffnen Sie im Browser diese Seite. Sie müssen bei GitHub angemeldet sein:
   https://github.com/settings/personal-access-tokens/new
2. Token name: zum Beispiel „CodeCockpit“.
3. Expiration: Wählen Sie, wie lange der Token gilt, zum Beispiel 90 Tage oder ein Jahr. Danach müssen Sie einen neuen erstellen. Manche Firmen schreiben eine Höchstdauer vor.
4. Resource owner: Ihr eigenes Konto. Für Repositories einer Organisation wählen Sie die Organisation.
5. Repository access: „All repositories“. Sonst kann das Cockpit keine neuen Repositories anlegen.
6. Permissions, Bereich „Repository permissions“. Stellen Sie diese Rechte auf „Read and write“:
   - Administration: zum Anlegen, Archivieren, Löschen und Ändern der Sichtbarkeit
   - Contents: zum Hochladen und Holen von Code
   - Workflows: zum Hochladen von Dateien im Ordner .github/workflows
   - Issues und Pull requests: für Rückmeldungen und Pull Requests in späteren Phasen
7. Metadata ist automatisch auf „Read-only“. Das ist richtig.
8. Wählen Sie ganz unten „Generate token“.
9. Der Token wird genau einmal angezeigt. Er beginnt mit „github_pat_“. Kopieren Sie ihn sofort.


## Im Cockpit eintragen

1. Menü Konten, Kontenverwaltung, „Neues Konto anlegen …“, Kontoart GitHub.
2. Fügen Sie den Token im Feld „Token“ mit Strg+V ein.
3. Wählen Sie „Verbindung testen“. Das Cockpit trägt Ihren Benutzernamen dann selbst ein.
4. Wählen Sie „Speichern“. Der Token liegt jetzt nur im Tresor.


## Wenn es nicht klappt

- „Der Token wurde abgelehnt“: Der Token ist abgelaufen, widerrufen oder falsch kopiert.
- „Freigabe für die Organisation fehlt“: Ihre Firma nutzt Single Sign-On. Das Cockpit bietet an, die Freigabeseite zu öffnen. Dort bestätigen Sie den Token für die Organisation.
- „Wartet auf Genehmigung“: Die Organisation muss den Token erst freigeben. Das macht ein Administrator. Das Cockpit meldet sich, sobald es geht.
