# Konzept: CodeCockpit – modulare, barrierefreie Verwaltung von Code-Projekten

Name des Programms: **CodeCockpit**
Ordner: `GitHub\CodeCockpit\Code` und `GitHub\CodeCockpit\Exe`, Name der Exe: `CodeCockpit.exe`

**Programmbeschreibung** (für README und Repository):

Deutsch:
> Verwaltet deine Code-Projekte auf GitHub und GitLab ohne Terminal: hochladen, Exe bauen, README pflegen und Rückmeldungen im Blick behalten, unterstützt von lokaler KI. Barrierefrei entwickelt, vollständig per Tastatur bedienbar und optimiert für Screenreader und Braillezeile.

Englisch (Hauptsprache der README):
> Manage your code projects on GitHub and GitLab without the terminal: publish, build executables, maintain READMEs and keep track of feedback, assisted by local AI. Designed for accessibility, fully keyboard operable and optimized for screen readers and braille displays.

Die Reihenfolge ist bewusst gewählt: Im ersten Satz stehen die Funktionen und die lokale KI, im zweiten die Barrierefreiheit. Dass die KI austauschbar ist, steht in der README unter Funktionen.

Stand: sechster Entwurf. Abschnitt 18 fasst getroffene Entscheidungen und offene Fragen zusammen.

---

## 1. Ausgangslage und Ziel

Der Nutzer arbeitet mit Braillezeile und Screenreader. Die Verwaltung von GitHub über das Terminal ist damit mühsam, ebenso das manuelle Pflegen von README-Dateien und das wiederholte Erstellen von Exe-Dateien.

Ziel ist eine barrierefreie Desktop-Anwendung, mit der man Code-Projekte ohne Terminal verwaltet: hochladen, aktualisieren, Verlauf ansehen, Links teilen, Repositories verwalten. Darauf aufbauend gibt es optionale Funktionen wie README-Pflege, Exe-Erstellung, Rückmeldungen von GitHub, Antwortentwürfe und E-Mail-Berichte.

Das Programm soll zunächst privat genutzt werden, später aber auch im Unternehmen. Deshalb ist es **modular** aufgebaut und legt sich nicht auf einen Anbieter oder eine Arbeitsweise fest:

- Die **Grundfunktionen** funktionieren nur mit Python und Git, ohne KI und ohne n8n.
- Alle weiteren Funktionen sind **Features**, die global und pro Projekt ein- und ausgeschaltet werden.
- KI-Anbieter, Konten, Plattformen und Automatisierungsdienste sind austauschbar.
- Zugangsdaten werden **verschlüsselt** gespeichert.
- Jedes Projekt hat einen eigenen Ordner mit den Unterordnern `Code` und `Exe`. Die Projektordner können an **beliebigen Orten** liegen.
- **Profile** trennen privaten und beruflichen Einsatz.

## 2. Grundprinzipien

1. **Kern plus Features:** Der Kern ist klein, stabil und ohne optionale Abhängigkeiten lauffähig. Jede Zusatzfunktion ist ein eigenes Modul.
2. **Adapter statt fester Anbieter:** Überall, wo es Alternativen gibt (KI, Code-Plattform, E-Mail, Zugangsdaten-Speicher), spricht der Code nur mit einer Schnittstelle. Konkrete Anbieter sind austauschbare Adapter.
3. **Nichts Wichtiges ohne Bestätigung:** Die KI macht nur Vorschläge. Veröffentlichen, Löschen und Antworten erfordern immer eine ausdrückliche Bestätigung.
4. **Sicher als Standard:** Neue Repositories sind privat, Zugangsdaten verschlüsselt, jedes Hochladen wird auf Geheimnisse geprüft.
5. **Barrierefreiheit zuerst:** Alles per Tastatur, sinnvolle Beschriftungen, Statusmeldungen als Text, das Wichtigste vorne in jeder Zeile.
6. **Unternehmenstauglich:** Unterstützung für Organisationen, Single Sign-On, eigene Server, Firmen-Proxys und Firmen-KI.

## 3. Architektur

### 3.1 Schichten

```
Oberfläche (PySide6)
   │
Kern: Projekte, Profile, Konten, Tresor, Feature-Verwaltung, Abläufe
   │
Feature-Module: README, Exe, Releases, Rückmeldungen, E-Mail, …
   │
Adapter:
   Plattform   (GitHub, GitHub Enterprise; später GitLab, Azure DevOps …)
   KI          (Ollama, OpenAI-kompatibel, Azure OpenAI, Anthropic, Gemini …)
   Tresor      (Windows-Anmeldeinformationen, verschlüsselte Tresordatei)
   Automation  (n8n lokal, n8n im Unternehmen, ohne Automation)
```

### 3.2 Feature-Module

Jedes Feature ist ein eigenes Paket mit einer Beschreibungsdatei (Manifest):

- eindeutige Kennung, Name und Beschreibung (für die Feature-Verwaltung)
- Abhängigkeiten zu anderen Features oder Adaptern (z. B. „braucht KI“, „braucht Automation“)
- eigene Einstellungen (werden im Einstellungsdialog automatisch als Formular angezeigt)
- Aktionen, die es der Aktionsliste eines Projekts hinzufügt
- Schritte, die es in die Abläufe einhängt (Abschnitt 3.3)
- zugehörige n8n-Workflows (falls vorhanden)

Neue Features können später ergänzt werden, ohne den Kern zu ändern.

### 3.3 Abläufe mit Einhängepunkten

Die Abläufe des Kerns (z. B. „Änderungen hochladen“) bestehen aus festen Einhängepunkten. Aktive Features hängen dort ihre Schritte ein:

| Einhängepunkt | Beispiele für Schritte |
|---|---|
| vor der Commit-Nachricht | Änderungen zusammenfassen |
| Commit-Nachricht | KI-Vorschlag erstellen |
| vor dem Hochladen | Sicherheitsprüfung (Kern), README prüfen, Version festlegen |
| nach dem Hochladen | Exe erstellen und testen, Release veröffentlichen, Status an Automation melden |

Ist ein Feature für ein Projekt ausgeschaltet, entfällt sein Schritt. Der Fortschritt („Schritt 3 von 5“) zählt nur die tatsächlich aktiven Schritte.

### 3.4 Aufgabenteilung zwischen Cockpit und n8n

**Cockpit:** alles, was lokale Dateien betrifft oder eine Entscheidung des Nutzers braucht (Git, Prüfungen, README-Vorschläge, Exe, Antworten absenden, Einstellungen, Tresor).

**n8n:** alles, was zeitgesteuert im Hintergrund oder zwischen Diensten passiert (Rückmeldungen abfragen, E-Mails, Antwortentwürfe, Releases, Abhängigkeiten überwachen).

n8n ist selbst ein optionaler Adapter. Ohne n8n funktionieren Kern und alle lokalen Features. Features, die n8n brauchen, werden in der Feature-Verwaltung als „benötigt Automation“ gekennzeichnet.

## 4. Profile

Ein **Profil** bündelt alles, was zu einem Einsatzbereich gehört. Voreingestellt sind „Privat“ und „Beruflich“, weitere können angelegt werden.

Ein Profil legt fest:
- Plattform-Konto (z. B. privates GitHub-Konto oder Firmen-Organisation)
- KI-Anbieter und Modell
- Automations-Instanz (z. B. lokales n8n oder n8n-Server der Firma, oder keine)
- E-Mail-Konto und Empfänger
- Projekte-Hauptordner, in dem neue Projekte angelegt werden
- Standardwerte für neue Projekte (Sichtbarkeit, Lizenz, README-Sprachen, aktive Features)
- ob die KI bei Projekten dieses Profils überhaupt Code-Auszüge erhalten darf (wichtig bei Firmenrichtlinien)
- Git-Identität: Name und E-Mail-Adresse, die in Commits erscheinen (Abschnitt 9.8)
- ob Änderungen direkt in den Hauptzweig gehen oder über Branches und Pull Requests (Feature 10.14, Standard: im Profil Beruflich an)

Jedes Projekt gehört zu genau einem Profil. Der Projektbaum zeigt wahlweise alle Projekte oder nur die eines Profils (Menü Ansicht).

## 5. Konten und Tresor

### 5.1 Konten

Unter **Konten** werden alle Zugänge verwaltet, jeweils mit Anzeigename, Art, Benutzername und den zugehörigen Geheimnissen:

- Plattform-Konten (GitHub, GitHub Enterprise, später weitere)
- KI-Konten (API-Schlüssel, Endpunkt-Adresse)
- E-Mail-Konten (SMTP oder Anmeldung über Microsoft 365 bzw. Google)
- Automations-Konten (n8n-Adresse, n8n-API-Schlüssel, Verschlüsselungsschlüssel der lokalen n8n-Instanz)

Mehrere Konten gleicher Art sind möglich (z. B. privates und berufliches GitHub-Konto). Jedes Konto hat den Knopf **„Verbindung testen“** mit verständlichem Ergebnis.

### 5.2 Der Tresor

Alle Geheimnisse (Tokens, API-Schlüssel, Passwörter) liegen im **Tresor**, niemals im Klartext in Dateien, Logs oder der Datenbank. Es gibt zwei Speicherarten, wählbar pro Installation:

**Windows-Anmeldeinformationsverwaltung** (Standard für private Nutzung)
- Geschützt durch die Windows-Anmeldung, kein zusätzliches Passwort nötig
- Umsetzung mit der Bibliothek `keyring`

**Verschlüsselte Tresordatei mit Master-Passwort** (empfohlen, wenn mehrere Personen den Rechner nutzen oder die Einstellungen auf einen anderen Rechner mitgenommen werden sollen)
- Schlüssel wird mit Scrypt aus dem Master-Passwort abgeleitet, Verschlüsselung mit AES-GCM (gleiches Verfahren wie im Tagebuch-Projekt des Nutzers)
- Beim Start wird das Master-Passwort abgefragt. Menüpunkt „Tresor sperren“ entfernt den Schlüssel aus dem Arbeitsspeicher.
- Hinweis bei der Einrichtung: Geht das Master-Passwort verloren, müssen alle Zugangsdaten neu eingegeben werden.

**Auswahl bei der Ersteinrichtung:** Beim ersten Start fragt das Cockpit, welche Speicherart genutzt werden soll, und erklärt beide in wenigen Sätzen. Voreingestellt ist die Windows-Anmeldeinformationsverwaltung. Die Speicherart kann später unter Konten, Tresor-Einstellungen gewechselt werden. Dabei überträgt das Cockpit alle vorhandenen Zugangsdaten in die neue Speicherart und entfernt sie danach aus der alten, sodass nichts neu eingegeben werden muss.

Der Tresor ist ein Adapter. Weitere Speicherarten (z. B. ein Passwort-Manager der Firma) können später ergänzt werden.

### 5.3 Wichtig: Passwörter von Plattformen

GitHub und die meisten anderen Plattformen erlauben **keine Anmeldung mit Benutzername und Passwort** für Programme. Das Cockpit speichert daher nie das GitHub-Passwort, sondern:

- einen Zugangs-Token, der über die Anmeldung im Browser entsteht (Abschnitt 6), oder
- einen selbst erstellten Token.

Beides ist sicherer als ein Passwort, weil ein Token nur die nötigen Rechte hat und jederzeit widerrufen werden kann.

Passwörter werden nur dort gespeichert, wo sie tatsächlich gebraucht werden, z. B. ein App-Passwort für den E-Mail-Versand per SMTP.

### 5.4 Zugangsdaten für n8n

- Das Cockpit speichert die n8n-Adresse und den n8n-API-Schlüssel im Tresor.
- Zugangsdaten, die n8n selbst braucht (GitHub-Token mit Leserechten, E-Mail-Zugang, KI-Schlüssel), legt das Cockpit über die n8n-API als n8n-Zugangsdaten an. n8n verschlüsselt sie mit seinem eigenen Schlüssel.
- Bei der lokalen n8n-Instanz sorgt das Cockpit dafür, dass ein fester Verschlüsselungsschlüssel gesetzt ist, und bewahrt ihn im Tresor auf. So bleiben die n8n-Zugangsdaten auch nach einer Neuinstallation lesbar.
- Der Nutzer muss die n8n-Oberfläche dafür nicht öffnen.

### 5.5 E-Mail-Konten

Für E-Mails braucht es zwei Angaben:
- **Absender:** das Postfach, über das n8n die E-Mails verschickt
- **Empfänger:** die Adresse, an die Berichte und Benachrichtigungen gehen

Standard: **Absender und Empfänger sind dasselbe Postfach.** Man schickt sich die Berichte also selbst. Der Empfänger kann aber jede beliebige Adresse sein.

Arten der Anbindung:

1. **SMTP mit App-Passwort** (Standard für private Nutzung)
   - Vorlagen für gängige Anbieter mit vorausgefülltem Server und Port. In der ersten Version: **Gmail und iCloud** sowie „Anderer Anbieter“ für eigene Angaben. Weitere Vorlagen (z. B. 1&1, GMX, web.de, Outlook.com, T-Online) können später ergänzt werden.
   - Einzugeben sind nur E-Mail-Adresse und Passwort.
   - Das Cockpit erklärt pro Anbieter kurz, was vorher im Postfach einzustellen ist, z. B. bei Gmail: Zwei-Faktor-Anmeldung einschalten und ein App-Passwort erstellen; bei GMX und web.de: Versand über externe Programme erlauben.
   - Wo möglich wird ein **App-Passwort** statt des Hauptpassworts verwendet. So kennt n8n nie das eigentliche Passwort, und der Zugang kann einzeln widerrufen werden.
2. **Microsoft 365 mit Anmeldung** (für Unternehmen): Viele Firmen erlauben keinen Versand per einfacher SMTP-Anmeldung mehr. Die Anmeldung erfolgt dann über das Microsoft-Konto. Dafür ist meist eine App-Registrierung durch die IT nötig. Das Cockpit erklärt, welche Angaben die IT liefern muss.
3. **Gmail mit Anmeldung:** möglich, erfordert aber ein eigenes Projekt in der Google Cloud Console und ist deutlich aufwendiger. Daher nicht Standard.

Vorlagen der ersten Version (Claude Code prüft die Serverdaten vor der Umsetzung anhand der aktuellen Hilfeseiten der Anbieter):

| Anbieter | SMTP-Server | Port | Benutzername | Passwort |
|---|---|---|---|---|
| Gmail | smtp.gmail.com | 587 (STARTTLS) | vollständige Gmail-Adresse | App-Passwort (setzt Zwei-Faktor-Anmeldung voraus) |
| iCloud | smtp.mail.me.com | 587 (STARTTLS) | vollständige iCloud-Adresse | app-spezifisches Passwort (setzt Zwei-Faktor-Anmeldung voraus) |

Bei iCloud muss die Absenderadresse die iCloud-Adresse selbst sein (oder ein bei Apple eingerichteter Alias).

Standardempfehlung im Profil Privat: **Absender Gmail oder iCloud**, **Empfänger das Postfach, das der Nutzer am häufigsten liest**. Absender und Empfänger dürfen verschieden sein.

Optionale Empfehlung für privat: ein **eigenes kostenloses Absender-Postfach** nur für Berichte. Dann liegt für das Hauptpostfach überhaupt kein Zugang in n8n.

Der Knopf **„Test-E-Mail senden“** verschickt eine Test-E-Mail direkt aus dem Cockpit, unabhängig von n8n. So lässt sich prüfen, ob die Angaben stimmen.

### 5.6 Sicherung

Der Code ist durch die Plattform gesichert, Tresor und Einstellungen des Cockpits aber nicht. Deshalb:

- **Sicherung erstellen** (Menü Datei): schreibt eine einzelne, verschlüsselte Sicherungsdatei in einen wählbaren Ordner (z. B. USB-Stick oder Cloud-Ordner). Sie enthält Tresor-Inhalt, Profile, Konten, Feature-Einstellungen, Projektliste und die Cockpit-Datenbank (Verlauf gelesener Rückmeldungen, Antwortentwürfe).
- Die Sicherung wird mit einem **Sicherungspasswort** verschlüsselt (Scrypt und AES-GCM). Das gilt auch, wenn der Tresor die Windows-Anmeldeinformationsverwaltung nutzt, denn deren Inhalt lässt sich ohne das Windows-Konto sonst nicht wiederherstellen.
- **Sicherung wiederherstellen** (Menü Datei): auch auf einem neuen Rechner, z. B. nach einem Laptop-Wechsel.
- Optional eine **Erinnerung** („Letzte Sicherung vor 30 Tagen“), Zeitraum einstellbar.
- Nach jeder Änderung an Konten oder Tresor weist das Cockpit einmal darauf hin, dass eine neue Sicherung sinnvoll ist.

## 6. Anmeldung bei Plattformen: privat und beruflich

### 6.1 Privat (github.com)

Zwei Wege, der Nutzer wählt:

1. **„Mit GitHub anmelden“ (empfohlen):** Das Cockpit zeigt einen kurzen Code an und öffnet die GitHub-Anmeldeseite im Browser. Dort meldet man sich wie gewohnt an (inklusive Zwei-Faktor-Anmeldung) und gibt den Code ein. Das Cockpit erhält einen Token und legt ihn im Tresor ab. Technisch ist das der „Device Flow“ von GitHub. Dafür wird das Cockpit einmalig als OAuth-App bei GitHub registriert. Der Code wird zusätzlich in die Zwischenablage kopiert, damit er nicht abgetippt werden muss.
2. **Token selbst erstellen:** Das Cockpit erklärt Schritt für Schritt, wie man einen Fine-grained Personal Access Token mit genau den nötigen Rechten anlegt, und nimmt ihn entgegen.

### 6.2 Beruflich (Organisationen und Unternehmen)

Im Unternehmen gibt es zusätzliche Regeln. Das Cockpit unterstützt:

- **GitHub-Organisationen:** Repositories werden wahlweise im eigenen Konto oder in einer Organisation angelegt. Die Organisation wird im Profil festgelegt.
- **Single Sign-On (SAML):** Viele Firmen verlangen, dass ein Token zusätzlich für die Organisation freigegeben wird. Erhält das Cockpit deshalb eine Ablehnung, erkennt es das an der Antwort von GitHub und erklärt, was zu tun ist, mit direktem Link zur Freigabeseite.
- **Genehmigungspflichtige Tokens:** Manche Organisationen müssen Fine-grained Tokens erst genehmigen. Das Cockpit zeigt den Status „Wartet auf Genehmigung“ verständlich an.
- **GitHub Enterprise Server:** eigene Serveradresse im Konto einstellbar.
- **GitHub App:** Für Automatisierungen im Team (z. B. n8n auf einem Firmenserver) kann statt eines persönlichen Tokens eine GitHub App verwendet werden. Sie ist nicht an eine Person gebunden und wird in Firmen oft bevorzugt.
- **Git-Anmeldung:** Für die Git-Befehle kann wahlweise der im Tresor gespeicherte Token oder der Git Credential Manager (in Git für Windows enthalten, unterstützt Single Sign-On) genutzt werden.
- **Firmennetzwerk:** Proxy-Einstellungen und die Nutzung des Windows-Zertifikatsspeichers (Bibliothek `truststore`), damit das Cockpit auch in Netzen mit eigener Zertifikatsprüfung funktioniert.
- **Eingeschränkte Rechte:** Fehlt einem Konto ein Recht (z. B. zum Löschen von Repositories), wird die entsprechende Aktion nicht versteckt, sondern mit Erklärung als nicht verfügbar gekennzeichnet.

### 6.3 Weitere Plattformen

Die Plattform ist ein Adapter. Eingeplant sind die in Unternehmen verbreiteten Plattformen:

- **GitHub** (github.com) und **GitHub Enterprise** (Cloud und eigener Server): erste Version
- **GitLab** (gitlab.com und selbst betriebene GitLab-Server): Anmeldung im Browser oder mit persönlichem Zugangs-Token
- **Azure DevOps** (Microsoft): Anmeldung mit persönlichem Zugangs-Token oder Microsoft-Konto

Später möglich: Bitbucket, Gitea.

**Fähigkeiten statt Gleichmacherei:** Nicht jede Plattform kann alles. Azure DevOps kennt zum Beispiel keine Sterne und keine Release-Seiten mit Downloads wie GitHub, und Sicherheitswarnungen gibt es je nach Plattform in unterschiedlicher Form. Jeder Adapter meldet deshalb, welche Fähigkeiten er hat (Repositories anlegen, Releases, Sterne, Issues, Sicherheitswarnungen, Löschen, Archivieren …). Features, die eine Fähigkeit brauchen, die die Plattform eines Projekts nicht hat, werden bei diesem Projekt als „nicht verfügbar“ mit Begründung angezeigt. Wo es sinnvolle Entsprechungen gibt (z. B. Work Items in Azure DevOps statt Issues), nutzt der Adapter diese.

## 7. Projekte und Speicherorte

### 7.1 Aufbau eines Projekts

Jedes Projekt bekommt einen eigenen Ordner mit dem Namen des Projekts. Darin legt das Cockpit zwei Unterordner an:

```
PDF-Chat\
  Code\   ← Quellcode, das ist das Git-Repository
  Exe\    ← die aktuelle Exe (bzw. der Programmordner), nicht Teil des Repositories
```

- Das Git-Repository ist der Ordner `Code`. Der Ordner `Exe` liegt daneben und landet deshalb nie versehentlich im Repository.
- Die Projekteinstellungen stehen in `Code\cockpit.toml` (ohne Geheimnisse) und werden mitversioniert. So gehen sie nicht verloren und sind auf einem anderen Rechner sofort da.
- Der Ordner `Exe` wird erst angelegt, wenn zum ersten Mal eine Exe erstellt wird.
- Große externe Ressourcen (z. B. heruntergeladene Modelle, Abschnitt 10.12) liegen nicht im Ordner `Exe`, sondern im Benutzerdatenordner. Sie gehen beim Ersetzen der Exe also nicht verloren.

### 7.2 Speicherorte

- Neue Projekte werden im **Projekte-Hauptordner** des Profils angelegt, z. B. `GitHub\`. Er ist in den Einstellungen änderbar.
- Projektordner können aber an **beliebigen Orten** liegen, auch auf Netzlaufwerken.
- Alle Unterordner des Projekte-Hauptordners, die einen Ordner `Code` enthalten, werden automatisch als Projekte erkannt.
- Die Zuordnung von Projekt, Profil und Pfad steht in der Datenbank des Cockpits.
- Wird ein Projektordner verschoben oder ist ein Netzlaufwerk nicht erreichbar, bleibt das Projekt in der Liste mit dem Hinweis „Ordner nicht gefunden“ und der Aktion „Neuen Ort angeben“.

### 7.3 Projekte in die Liste bekommen

- **Neues Projekt hochladen:** Ordner mit dem Code wählen. Das Cockpit legt im Projekte-Hauptordner den Projektordner mit `Code` an und kopiert den Code hinein (Abschnitt 9.1).
- **Von der Plattform herunterladen** (Klonen, z. B. ein bestehendes Firmen-Repository): Das Cockpit legt den Projektordner an und lädt den Code in `Code`.
- **Vorhandenes Projekt hinzufügen:** Man wählt den **Projektordner** (den Ordner, der `Code` und gegebenenfalls `Exe` enthält). Das Cockpit erkennt beide Unterordner selbst. Projekte im Projekte-Hauptordner erscheinen ohnehin automatisch.

### 7.4 Ordner, die nicht diesem Aufbau entsprechen

Der Nutzer stellt seine eigenen Projekte selbst auf den Aufbau aus 7.1 um (`GitHub\<Projekt>\Code` und `GitHub\<Projekt>\Exe`). Das Cockpit braucht deshalb keinen Assistenten für eine Massen-Umstellung.

Für andere Nutzer und für Firmen-Repositories gilt: Wählt man beim Hinzufügen einen Ordner, der keinen Unterordner `Code` enthält, bietet das Cockpit an:

1. **Umstellen:** Projektordner anlegen, den gewählten Ordner als `Code` hineinverschieben. Vorher wird beschrieben, was passiert, erst nach Bestätigung ausgeführt.
2. **Nur verknüpfen:** Die Ordner bleiben, wo sie sind. Code-Ordner und Exe-Ordner werden einzeln angegeben. Gedacht für Repositories, deren Aufbau man nicht ändern darf.

### 7.5 Nach dem Verschieben von Projekten

Werden Projekte von Hand verschoben, erkennt das Cockpit beim Öffnen typische Folgen und bietet die Reparatur an:

- **Virtuelle Umgebung (`.venv`) funktioniert nicht mehr:** Virtuelle Umgebungen enthalten feste Pfade und lassen sich nicht verschieben. Das Cockpit legt sie nach Rückfrage neu an und installiert die `requirements.txt`.
- **Feste Pfade in der `.spec`-Datei:** werden von „Exe-Einrichtung prüfen“ gefunden und können automatisch in relative Pfade umgewandelt werden.
- **Git-Verlauf und Verbindung zur Plattform** bleiben beim Verschieben erhalten, solange der versteckte Ordner `.git` mitverschoben wurde. Fehlt er, meldet das Cockpit das verständlich und bietet an, das Projekt mit der Plattform neu zu verbinden.

## 8. Bedienung

Alles ist per Tastatur bedienbar. Status und Fortschritt werden als Text ausgegeben, gut lesbar auf der Braillezeile. Aufbau und Bedienlogik werden aus den bisherigen PySide6-Projekten des Nutzers übernommen (Chatbot, Tagebuch).

### 8.1 Menüleiste

**Datei**
- Neues Projekt hochladen (Strg+N)
- Vorhandenes Projekt hinzufügen
- Projekt von der Plattform herunterladen
- Sicherung erstellen …
- Sicherung wiederherstellen …
- Beenden (Strg+Q)

**Ansicht**
- Alle Profile / nur Profil „Privat“ / nur Profil „Beruflich“ / … (wählbar)

**Features**
- Feature-Verwaltung … (Abschnitt 8.5)

**KI** (ergänzt am 27.09.2026, Abschnitt 11.1)
- KI-Verwaltung … (KI-Werkzeuge für Text und Sprache, lokal oder extern)
- KI-Features … (öffnet die Feature-Verwaltung bei den KI-Features)

**Konten**
- Kontenverwaltung …
- Tresor-Einstellungen …
- Tresor sperren (nur bei Tresordatei)

**Automatisierungen** (nur sichtbar, wenn eine Automations-Instanz eingerichtet ist)
- Übersicht der Automatisierungen
- Rückmeldungen jetzt abfragen (F5)
- Wochenbericht jetzt senden
- Abhängigkeiten jetzt prüfen
- n8n starten bzw. neu starten (nur lokale Instanz)

**Einstellungen**
- Profile …
- KI-Anbieter …
- Ordner …
- Netzwerk (Proxy, Zertifikate) …
- Einstellungen der aktiven Features … (ein Eintrag pro Feature mit eigenen Einstellungen)

**Hilfe**
- Tastenkürzel
- Über CodeCockpit

### 8.2 Projektbaum

Die Projekte werden als **Baum** angezeigt (ausklappbare Liste).

**Oberste Ebene:**
- Ganz oben: **„Neues Projekt hochladen“**
- Darunter alle Projekte, zuletzt aktualisierte oben. Das Wichtigste steht vorne:
  - „PDF-Chat, aktualisiert am 21.09.2026, 2 neue Rückmeldungen“
  - „Tagebuch, aktualisiert am 18.09.2026, 3 geänderte Dateien noch nicht hochgeladen“
  - „Bildbeschreiber, noch nicht auf GitHub“
  - „Rechnungsprüfung, Beruflich, aktualisiert am 10.09.2026“ (Profil wird genannt, wenn alle Profile angezeigt werden)
  - „Notizen, Ordner nicht gefunden“

**Zweite Ebene** (nach dem Ausklappen eines Projekts): die vorhandenen Unterordner, zum Beispiel:
  - „Code, 3 Dateien noch nicht hochgeladen“ bzw. „Code, alles hochgeladen“
  - „Exe, Version 1.4.0, erstellt am 23.09.2026“

Es werden nur Ordner angezeigt, die es gibt. Hat ein Projekt noch keine Exe, erscheint nur „Code“.

**Tastatur im Baum:**
- **Pfeil hoch/runter:** zwischen den Einträgen wechseln
- **Pfeil rechts** auf einem Projekt: Projekt ausklappen. **Alle anderen Projekte werden dabei automatisch zugeklappt.** Es ist also immer höchstens ein Projekt offen, damit man nicht versehentlich im falschen Projekt landet.
- **Pfeil rechts** auf einem ausgeklappten Projekt: springt zum ersten Unterordner
- **Pfeil links** auf einem Unterordner: springt zurück zum Projekt
- **Pfeil links** auf einem ausgeklappten Projekt: klappt es zu
- **Tab:** springt in die Aktionsliste des ausgewählten Eintrags (Abschnitt 8.3)
- **Enter:** führt die wichtigste Aktion aus (bei Code: „Änderungen hochladen“, bei Exe: „Exe starten“, bei einem Projekt: ausklappen)

Der Screenreader liest Ebene sowie „ausgeklappt“ bzw. „zugeklappt“ vor. Umsetzung mit einem Baum-Widget (`QTreeView`), dessen Barrierefreiheit geprüft wird. Das automatische Zuklappen geschieht so, dass der Fokus auf dem gerade ausgeklappten Projekt bleibt.

### 8.3 Aktionen mit Tab

Mit **Tab** springt man vom ausgewählten Eintrag im Baum in die Aktionsliste. Die Aktionen hängen davon ab, **was** ausgewählt ist, und davon, welche Features für das Projekt aktiv sind. Umschalt+Tab führt zurück in den Baum, genau auf den Eintrag, von dem man kam. Enter führt die Aktion aus, Escape führt aus jeder Unteransicht zurück.

**Projekt ausgewählt** (alles, was das ganze Projekt betrifft):
- Rückmeldungen, z. B. „Rückmeldungen, 2 neu“ (Feature Rückmeldungen)
- Links kopieren bzw. öffnen (Projektseite, README, Download falls Releases aktiv)
- Projektordner öffnen
- Features dieses Projekts
- Projekteinstellungen
- Repository verwalten (Sichtbarkeit ändern, archivieren, löschen)
- Aus der Liste entfernen

**Code ausgewählt:**
- Änderungen hochladen
- Änderungen von der Plattform holen
- Verlauf
- README ansehen, README neu erstellen (Feature README)
- Änderungen verwerfen (Abschnitt 9.7)
- Branch wechseln, Pull Request erstellen (Feature Branches und Pull Requests)
- Code-Ordner öffnen

**Exe ausgewählt** (überarbeitet am 27.09.2026, Einzelheiten in 10.4):
- Exe starten
- Exe aus dem Code erstellen bzw. aktualisieren (Feature Exe-Erstellung)
- Exe-Datei wählen
- Exe veröffentlichen, Exe aus dem Release holen
- Exe-Einrichtung prüfen
- Exe-Ordner öffnen
- Wie funktioniert die Exe?

Hat ein Projekt noch keinen Ordner `Exe`, gibt es auf der Projektzeile die Aktion **„Exe hinzufügen …“**. Danach erscheint der Eintrag „Exe“.

### 8.4 Features dieses Projekts

Eine Liste mit Kontrollkästchen, ein Eintrag pro Feature, z. B. „Exe-Erstellung, aktiv“. Leertaste schaltet um. Per Tab erreichbar: Beschreibung des ausgewählten Features, dann „Speichern“.

- Voreinstellung für neue Projekte kommt aus dem Profil.
- Features, die global ausgeschaltet sind, erscheinen nicht.
- Hat ein Feature Abhängigkeiten, wird das erklärt: „Antwortentwürfe benötigt Rückmeldungen und KI. Rückmeldungen ist für dieses Projekt ausgeschaltet. Beide einschalten?“

### 8.5 Feature-Verwaltung (Menü Features)

Globale Übersicht aller Features, gleiche Bedienung wie in 8.4:

- Global ein- und ausschalten. Ein global ausgeschaltetes Feature taucht nirgends auf, auch nicht in Menüs und Aktionslisten.
- Zu jedem Feature: Beschreibung, Abhängigkeiten, ob es KI oder Automation benötigt, bei wie vielen Projekten es aktiv ist.
- Knopf „Einstellungen dieses Features“.
- Features, deren Voraussetzungen fehlen (z. B. keine Automation eingerichtet), werden als „nicht verfügbar“ mit Begründung angezeigt.

### 8.6 Fortschritt und Fehler

Längere Abläufe zeigen den Fortschritt schrittweise als Text und sagen ihn an: „Schritt 3 von 5: Exe wird erstellt …“

Am Ende eine kurze Zusammenfassung: „Fertig. Version 1.4.0 ist hochgeladen, die Exe wurde getestet und veröffentlicht. Download-Link wurde in die Zwischenablage kopiert.“

Fehler werden in einfachem Deutsch erklärt. Die technische Originalmeldung ist über „Details anzeigen“ erreichbar.

### 8.7 Ersteinrichtung

Beim ersten Start führt ein Assistent durch die Einrichtung. Jede Seite ist ein einfaches Formular mit „Weiter“, „Zurück“ und „Überspringen“. Nur die Wahl des Tresors ist Pflicht. Alles kann später über die Menüs geändert werden.

1. **Willkommen:** kurze Erklärung, was das Cockpit kann
2. **Tresor:** Speicherart wählen (Abschnitt 5.2), bei Tresordatei Master-Passwort festlegen
3. **Profil:** Name des ersten Profils (Standard „Privat“)
4. **Plattform-Konto:** „Mit GitHub anmelden“, Token eingeben oder andere Plattform wählen
   - Danach **Git-Identität** festlegen: Name und E-Mail-Adresse für Commits. Bei GitHub schlägt das Cockpit die anonyme noreply-Adresse vor (Abschnitt 9.8).
5. **Ordner:** Projekte-Hauptordner (z. B. `GitHub\`). Die darin gefundenen Projekte werden angezeigt und bei Bedarf repariert (Abschnitt 7.5).
6. **KI:** Das Cockpit prüft, ob Ollama läuft, und listet die installierten Modelle. Alternativ anderen Anbieter einrichten oder ohne KI starten.
7. **Automation:** n8n lokal, n8n-Server der Firma oder keine Automation. Ist n8n nicht installiert, erklärt das Cockpit die Installation und bietet an, diesen Schritt später nachzuholen.
8. **E-Mail:** Konto einrichten (Abschnitt 5.5) oder überspringen
9. **Features:** Vorauswahl passend zu dem, was eingerichtet wurde. Ohne n8n sind z. B. Rückmeldungen und Wochenbericht ausgeschaltet.
10. **Zusammenfassung:** was eingerichtet wurde und was übersprungen wurde, mit Hinweis, wo es sich nachholen lässt

## 9. Grundfunktionen (Kern)

Diese Funktionen brauchen nur Python und Git. Keine KI, kein n8n.

### 9.1 Neues Projekt hochladen

1. Ordner mit dem Code auswählen (beliebiger Ort). Das Cockpit legt im Projekte-Hauptordner den Projektordner mit dem Unterordner `Code` an und kopiert den Code hinein. Der ursprüngliche Ordner bleibt unverändert, bis der Nutzer ihn selbst löscht.
2. Profil wählen (Standard: zuletzt genutztes).
3. Angaben, vorbelegt aus dem Profil:
   - Name auf der Plattform (Vorschlag aus dem Ordnernamen)
   - Kurzbeschreibung
   - **Sichtbarkeit: privat (Standard)** oder öffentlich
   - Lizenz (inklusive „Keine Lizenz / firmenintern“)
   - Ziel: eigenes Konto oder Organisation
   - Aktive Features für dieses Projekt (Kontrollkästchen)
4. Sicherheitsprüfung (9.6).
5. Schritte aktiver Features (z. B. README erstellen).
6. Repository anlegen, erster Commit „Erste Version“, hochladen.
7. Schritte aktiver Features nach dem Hochladen (z. B. erste Exe, Release).
8. Links anzeigen, Projektlink in die Zwischenablage kopieren.

### 9.2 Änderungen hochladen

1. Anzeige der Änderungen in lesbarer Form: „3 Dateien geändert: main.py, suche.py, README.md. 1 neue Datei: export.py.“
2. Textfeld „Was hast du geändert?“ für die Commit-Nachricht. (Mit Feature KI-Assistent: Knopf „Vorschlag erstellen lassen“.)
3. Sicherheitsprüfung (9.6).
4. Schritte aktiver Features vor dem Hochladen.
5. Commit und Push.
6. Schritte aktiver Features nach dem Hochladen.
7. Zusammenfassung.

Schlägt ein Schritt nach dem Hochladen fehl (z. B. der Exe-Test), bleibt der Code trotzdem hochgeladen. Der Nutzer erhält eine klare Meldung, was nicht geklappt hat.

### 9.3 Änderungen von der Plattform holen

Holt Änderungen, die z. B. Kollegen oder man selbst auf einem anderen Rechner hochgeladen hat. Bei Konflikten wird nichts automatisch zusammengeführt, sondern verständlich erklärt, welche Dateien betroffen sind.

Geändert am 25.09.2026 (siehe ENTSCHEIDUNGEN.md): Das Cockpit holt wie GitHub Desktop mit Merge. Bei einem Konflikt wählt man pro Datei „Meine Fassung behalten“, „Fassung von GitHub übernehmen“ oder „Im Editor öffnen“, oder man bricht das Zusammenführen ab.

### 9.4 Verlauf

Liste aller Commits, neueste oben: „23.09.2026, Version 1.4.0: Suche in mehreren PDFs ergänzt“. Enter zeigt Details (Autor, geänderte Dateien, ausgeführte Feature-Schritte).

In den Details per Tab erreichbar:
- **Datei aus dieser Version wiederherstellen** (Auswahl der Datei aus der Liste der geänderten Dateien)
- **Diese Version rückgängig machen** (Abschnitt 9.7)

### 9.5 Repository verwalten

- **Sichtbarkeit ändern** (privat ↔ öffentlich), mit Rückfrage. Vor dem Wechsel auf öffentlich läuft die Sicherheitsprüfung über das gesamte Repository.
- **Archivieren**: Repository wird schreibgeschützt, bleibt aber erhalten. Wird als sanftere Alternative zum Löschen angeboten.
- **Löschen**:
  - Rückfrage mit Hinweis, dass das nicht rückgängig gemacht werden kann, und dem Angebot, stattdessen zu archivieren.
  - Zur Bestätigung muss der Name des Repositories eingetippt werden.
  - Der lokale Ordner bleibt immer erhalten. Das Projekt kann danach aus der Liste entfernt oder als „nur lokal“ behalten werden.
  - Benötigt ein Recht, das der Token ausdrücklich haben muss. Fehlt es (in Firmen häufig), erklärt das Cockpit das.
- **Mitarbeiter** einladen und entfernen (ergänzt am 25.09.2026).
- **Aus der Liste entfernen**: nur aus dem Cockpit, ohne Änderung an Plattform oder Ordner.

Das Cockpit führt nie einen „force push“ aus.

### 9.6 Sicherheitsprüfung

Teil des Kerns und nicht abschaltbar, weil ein versehentlich veröffentlichtes Passwort großen Schaden anrichten kann:

- **Geheimnisse:** API-Schlüssel, Tokens, Passwörter im Code, `.env`-Dateien. Werden welche gefunden, wird das Hochladen gestoppt und erklärt, was gefunden wurde. Einzelne Funde können nach Prüfung bewusst als „kein Geheimnis“ markiert werden.
- **Private Daten:** Warnung bei Datenbanken, Logdateien und ähnlichen Dateien.
- **Große Dateien:** Warnung ab 50 MB.
- **`.gitignore`:** wird angelegt bzw. ergänzt (virtuelle Umgebungen, Caches, Build-Ordner, `.env`, Datenbanken, Logs, Exe-Dateien).
- **Private E-Mail-Adresse:** Warnung, wenn ein öffentliches Repository Commits mit einer privaten E-Mail-Adresse enthalten würde (Abschnitt 9.8).

### 9.7 Rückgängig machen

Für den Fall, dass man sich etwas kaputt gemacht hat. Alle Aktionen beschreiben vorher genau, was passiert, und brauchen eine Bestätigung. Nichts davon schreibt die Geschichte auf der Plattform um, es gibt also nie einen „force push“.

- **Änderungen verwerfen** (Aktion bei „Code“): zeigt alle noch nicht hochgeladenen Änderungen als Liste mit Kontrollkästchen. Die ausgewählten Dateien werden auf den zuletzt hochgeladenen Stand zurückgesetzt. Neue, noch nie hochgeladene Dateien werden nicht gelöscht, sondern in den Papierkorb verschoben.
- **Datei aus einer früheren Version wiederherstellen** (im Verlauf): Die Datei wird auf den Stand dieser Version gesetzt. Das ist danach eine normale Änderung, die man wie gewohnt hochlädt.
- **Version rückgängig machen** (im Verlauf): Es wird ein neuer Commit erstellt, der die Änderungen dieser Version wieder aufhebt, z. B. „Rückgängig: Suche in mehreren PDFs ergänzt“. Der Verlauf bleibt vollständig erhalten.
- Vor jeder dieser Aktionen legt das Cockpit eine lokale Sicherheitskopie der betroffenen Dateien an (für 30 Tage im Benutzerdatenordner), damit auch ein versehentliches Zurücksetzen rückgängig gemacht werden kann.

### 9.8 Git-Identität und Schutz der E-Mail-Adresse

In jedem Commit stehen ein Name und eine E-Mail-Adresse. Bei öffentlichen Repositories kann diese Adresse jeder sehen.

- Die Git-Identität wird **pro Profil** festgelegt (bei der Ersteinrichtung und in den Profileinstellungen) und für die Projekte dieses Profils gesetzt. So erscheint in privaten Projekten die private und in beruflichen Projekten die berufliche Identität.
- Für GitHub schlägt das Cockpit die **anonyme noreply-Adresse** des Kontos vor (Format `ID+Benutzername@users.noreply.github.com`) und liest sie über die Plattform aus, damit sie nicht abgetippt werden muss.
- Das Cockpit erklärt, dass man bei GitHub zusätzlich die Einstellung „E-Mail-Adresse privat halten“ einschalten kann, dann lehnt GitHub Pushes mit der privaten Adresse ab.
- Die Sicherheitsprüfung (9.6) warnt, wenn ein Repository öffentlich ist oder öffentlich gemacht werden soll und Commits eine private Adresse enthalten.

### 9.9 Terminal

Ergänzt am 27.09.2026 (Wunsch des Nutzers): Das Cockpit deckt nicht jede Möglichkeit von Git und GitHub ab. Für alles Übrige gibt es ein eingebautes Terminal. Es gehört zum Kern und ist immer da.

- Aktion „Terminal …“ auf der Projektzeile und bei „Code“. Das Terminal startet im Ordner des Projekts bzw. im Ordner `Code`.
- Aufbau des Fensters: ein Eingabefeld für den Befehl. Mit Umschalt+Tab erreicht man die Ausgabe, mit Tab die Erklärung der KI.
- Die Ausgabe ist eine Liste, eine Zeile pro Zeile der Ausgabe, wie im Terminal: zuerst der eingegebene Befehl, dann die Ausgabe und Fehlermeldungen. So lässt sie sich mit Pfeiltasten und Braillezeile Zeile für Zeile lesen.
- Schlägt ein Befehl fehl, schreibt die KI in das Feld „Erklärung der KI“, warum das wahrscheinlich passiert ist und was man tun kann. Das Feld gibt es nur, wenn das Feature „Terminal-Erklärung“ (10.16) aktiv ist. Ohne KI gibt es das Terminal ohne dieses Feld.
- Git bekommt die Zugangsdaten des Kontos wie bei allen Aktionen des Cockpits über Umgebungsvariablen. Tokens erscheinen nie in der Ausgabe, auch nicht in der Erklärung.
- Befehle, die auf eine Eingabe warten oder einen Editor öffnen würden, werden so gestartet, dass sie das nicht tun (zum Beispiel ohne Pager). Ein laufender Befehl lässt sich abbrechen.
- Ein force push wird auch hier nie ausgeführt. Das Cockpit erklärt stattdessen, warum.

## 10. Features

Jedes Feature ist global und pro Projekt schaltbar. Übersicht:

| Feature | Benötigt | Kurzbeschreibung |
|---|---|---|
| KI-Assistent | KI | Commit-Vorschläge, Kurzbeschreibungen |
| README-Pflege | KI | README erstellen, prüfen, übersetzen |
| Versionen | – | Versionsnummern und Git-Tags |
| Exe-Erstellung | – | Exe bauen, testen, Einrichtung prüfen |
| Releases | Versionen, Automation | Veröffentlichen auf der Plattform mit Download |
| Rückmeldungen | Automation | Sterne, Issues, Kommentare, Downloads |
| Antwortentwürfe | Rückmeldungen, KI | Entwürfe für Antworten auf Issues |
| E-Mail-Benachrichtigungen | Rückmeldungen, E-Mail | E-Mail bei neuen Issues und Kommentaren |
| Wochenbericht | Automation, E-Mail | Wöchentliche Zusammenfassung per E-Mail |
| Abhängigkeiten-Wächter | Automation | Neue Versionen, Sicherheitswarnungen |
| Erinnerung | Automation | Hinweis auf nicht hochgeladene Änderungen |
| Externe Ressourcen | – | Große Modelle und Daten außerhalb der Exe bereitstellen |
| Lizenzprüfung | – | Lizenzen der Bibliotheken prüfen und Konflikte melden |
| Branches und Pull Requests | Plattform mit Pull Requests | Änderungen über eigene Zweige und Übernahme-Anträge |
| Spracheingabe | Sprach-KI (Whisper) | In jedes Eingabefeld diktieren (ergänzt am 27.09.2026) |
| Terminal-Erklärung | KI | Erklärt Fehler im eingebauten Terminal (ergänzt am 27.09.2026) |
| KI-Hilfe | KI | Beantwortet Fragen zur Bedienung des Cockpits (ergänzt am 27.09.2026) |

### 10.1 KI-Assistent

- Vorschlag für die Commit-Nachricht aus den Änderungen
- Vorschlag für die Kurzbeschreibung neuer Projekte
- Die KI bekommt nie den ganzen Code, sondern eine vorbereitete Übersicht (Dateiliste, geänderte Stellen, Imports).

### 10.2 README-Pflege

**Aufbau jeder README:**
1. Name und Kurzbeschreibung
2. Download (falls Releases aktiv)
3. Funktionen
4. Bedienung, mit Tastenkürzeln
5. Systemanforderungen (Betriebssystem, Arbeitsspeicher, Grafik, Zusatzprogramme wie Ollama mit bestimmtem Modell)
6. Verwendete Werkzeuge, KI und Algorithmen (z. B. PyMuPDF, faster-whisper), jeweils mit einem Satz, wofür es genutzt wird
7. Installation aus dem Quellcode
8. Änderungen (letzte Versionen, falls Versionen aktiv)
9. **Hinweis zu Windows-Warnungen** (falls Exe-Erstellung aktiv, Abschnitt 10.4)
10. Lizenz, mit Hinweis auf die Lizenzen der verwendeten Bibliotheken (falls Lizenzprüfung aktiv)

Welche Abschnitte vorkommen, ist in den Feature-Einstellungen wählbar.

**Pflege:**
- Bibliotheken werden direkt aus `requirements.txt` und Imports ermittelt, die KI schreibt nur die Erklärungen dazu.
- Systemanforderungen: Vorschlag des Cockpits, einmal bestätigt, danach in `cockpit.toml`.
- Automatisch gepflegte Abschnitte sind mit unsichtbaren Markierungen versehen (`<!-- cockpit:start -->` … `<!-- cockpit:ende -->`). Selbst geschriebene Texte werden nie verändert.
- Vor dem Hochladen prüft die KI, ob die README zu den Änderungen passt, und beschreibt Vorschläge in Worten: Übernehmen, Bearbeiten, Überspringen.

**Sprachen:**
- Auswahl als Liste mit Kontrollkästchen: **Englisch** (Standard), Deutsch, Französisch, Spanisch. Die Liste ist erweiterbar.
- Eine Sprache ist die **Hauptsprache** (Standard: Englisch). Sie steht in `README.md`, denn diese Datei zeigt die Plattform automatisch an.
- Weitere Sprachen stehen in eigenen Dateien: `README.de.md`, `README.fr.md`, `README.es.md`.
- Oben in jeder Datei steht eine Zeile mit Links zu allen Sprachfassungen, z. B. „English | Deutsch | Français | Español“.
- Ändert sich die Hauptfassung, erstellt die KI die Übersetzungen der geänderten Abschnitte. Selbst geschriebene Abschnitte werden nur nach Rückfrage übersetzt.

### 10.3 Versionen

- Beim Hochladen Auswahl „Kleine Korrektur“, „Neue Funktion“, „Große Änderung“, daraus wird die Versionsnummer berechnet (1.3.2 → 1.3.3, 1.4.0 oder 2.0.0).
- Die Version wird als Git-Tag gesetzt und im Verlauf angezeigt.

### 10.4 Exe-Erstellung

Überarbeitet am 27.09.2026 (Wunsch des Nutzers). Viele Projekte haben neben dem Code eine fertige Exe. Die Exe ist deshalb ein eigener Eintrag im Projekt, wie „Code“. Offene Einzelheiten stehen in `fragen\phase-10.md`.

**Der Eintrag „Exe“:**
- Ein Projekt hat den Eintrag „Exe“, sobald es den Ordner `Exe` gibt. Fehlt er, gibt es auf der Projektzeile die Aktion „Exe hinzufügen …“. Sie legt den Ordner an (oder verknüpft bei verknüpften Projekten einen vorhandenen Ordner). Danach erscheint „Exe“ unter „Code“.
- Die Zeile nennt das Wichtigste vorne, zum Beispiel:
  - „Exe, noch keine Exe-Datei“
  - „Exe, Version 1.4.0, erstellt am 23.09.2026, aktuell“
  - „Exe, erstellt am 23.09.2026, älter als der Code“ (der Code hat seit dem Bau neue Commits)
  - „Exe, von Hand hinzugefügt am 20.09.2026“ oder „Exe, aus dem Release 1.3.0“
- Das Cockpit merkt sich in `cockpit.toml` unter `[exe]`, woher die Exe kommt (vom Cockpit gebaut, von Hand gewählt, aus einem Release), wann, aus welchem Commit und mit welcher Version. So weiß es, ob die Exe zum Code passt und ob es sie selbst aktualisieren kann.

**Aktionen bei „Exe“** (Tab vom Eintrag, Knöpfe, die nicht passen, fehlen):
- **Exe starten** (Enter auf dem Eintrag).
- **Exe aus dem Code erstellen …** bzw. **Exe aus dem Code aktualisieren …**, wenn schon eine da ist. Nur mit Feature „Exe-Erstellung“.
- **Exe-Datei wählen …**: eine vorhandene Exe von woanders in den Ordner `Exe` übernehmen, zum Beispiel wenn man sie selbst gebaut hat. Mit Rückfrage und Sicherheitskopie der bisherigen Exe.
- **Exe veröffentlichen …**: Release auf GitHub mit Versionsnummer anlegen und die Exe anhängen (siehe 10.5).
- **Exe aus dem Release holen …**: die Exe des neuesten Releases herunterladen. Nur, wenn das Repository Releases mit einer Exe hat, zum Beispiel bei heruntergeladenen Projekten anderer Personen.
- **Exe-Einrichtung prüfen**.
- **Exe-Ordner öffnen**.
- **Wie funktioniert die Exe? …**: Anleitung wie „Branches verstehen“, auch im Menü Hilfe.

**Bauen:**
- Gebaut wird mit PyInstaller. Das Cockpit braucht dafür Python auf dem Rechner. Fehlt es, erklärt eine Anleitung die Installation (wie bei Git), und „Exe aus dem Code erstellen“ sagt, warum es nicht geht.
- Jedes Projekt bekommt eine eigene virtuelle Umgebung (`Code\.venv`). Das Cockpit legt sie bei Bedarf an, installiert `requirements.txt` und PyInstaller. PyInstaller wird so erst beim ersten Bauen heruntergeladen und steckt nicht im Cockpit selbst.
- Beim ersten Bauen fragt ein kurzer Dialog: Startdatei (Vorschlag: `main.py`), Name der Exe (Vorschlag: Projektname), Bauart (eine Datei oder Programmordner), Symbol (freiwillig). Daraus entsteht eine `.spec`-Datei im Code-Ordner. Sie wird hochgeladen und bei jedem weiteren Bau wiederverwendet.
- Der Bau läuft im Hintergrund in einem temporären Ordner, mit Fortschritt als Text („Schritt 2 von 4: Bibliotheken werden installiert“). Die Ausgabe von PyInstaller steht in einer Liste, eine Zeile pro Zeile, wie im Terminal. Schlägt der Bau fehl, erklärt das Cockpit den Fehler, mit KI, falls das Feature Terminal-Erklärung aktiv ist.
- **Alte Exe wird ersetzt, aber nie ohne funktionierende Exe:**
  1. Die neue Exe wird im temporären Ordner gebaut und getestet.
  2. Nur wenn der Test bestanden ist, kommt die bisherige Exe als Sicherheitskopie in den Ordner `backups`, und die neue Exe ersetzt sie.
  3. Schlägt der Test fehl, bleibt die alte Exe unverändert.
- Läuft die alte Exe gerade, bittet das Cockpit, sie zu schließen.
- **Bauart:** eine einzelne Exe-Datei (Standard, gut für kleine Programme) oder ein Programmordner (besser für große Programme, startet schneller, wird als ZIP-Datei veröffentlicht).
- **Was im ersten Build steckt, bleibt drin:** Dateien, die in der `.spec`-Datei stehen, kommen immer mit. Die Einrichtungsprüfung warnt bei zu großen Exe-Dateien (Prüfpunkt 10).

**Test:**
1. Start-Test: Exe starten. Läuft sie nach 10 Sekunden noch ohne Absturz, ist der Test bestanden. Danach beendet das Cockpit sie.
2. Selbsttest (empfohlen): Das Programm unterstützt `--selbsttest`, prüft selbst alles Wichtige und beendet sich mit Code 0. Das Cockpit kann anbieten, diese Option einzubauen.

**Warnungen von Windows und Virenscannern:**
- Nicht signierte Exe-Dateien lösen bei anderen Nutzern oft eine Warnung von Windows SmartScreen aus („Der Computer wurde durch Windows geschützt“). Manche Virenscanner melden sie fälschlich als verdächtig.
- Das Cockpit fügt der README einen kurzen Hinweis hinzu: warum die Warnung erscheint und wie man das Programm trotzdem startet („Weitere Informationen“, dann „Trotzdem ausführen“). Dazu die Prüfsumme (SHA-256) der Exe. Die Prüfsumme steht auch in den Versionshinweisen des Releases.
- **Signieren (optional, später):** Ist ein Code-Signing-Zertifikat vorhanden, kann das Cockpit die Exe nach dem Build signieren. Zertifikat und Passwort liegen im Tresor.
- Bei der Bauart „einzelne Exe-Datei“ sind Fehlalarme häufiger. Treten sie auf, schlägt das Cockpit „Programmordner“ vor.

**Sonderfall: Das Cockpit baut seine eigene Exe.**
Das Cockpit liegt selbst als Projekt im Projekte-Hauptordner und kann sich damit selbst verwalten. Windows erlaubt aber nicht, eine Exe zu löschen, die gerade läuft. Deshalb:
1. Die neue Exe wird wie gewohnt in einem temporären Ordner gebaut und getestet.
2. Nach bestandenem Test wird sie im Ordner `Exe` als „wartende Aktualisierung“ abgelegt (`Exe\_neu\`).
3. Das Cockpit meldet: „Die neue Version wird beim nächsten Start übernommen. Jetzt neu starten?“
4. Beim Neustart übernimmt ein kleines Startskript den Austausch: Es wartet, bis das alte Cockpit beendet ist, ersetzt die Exe, startet die neue Version und räumt `_neu` auf.
5. Startet die neue Version nicht, wird die alte wiederhergestellt.
Das Cockpit erkennt sich selbst an `is_cockpit = true` in seiner `cockpit.toml`. Seine Exe braucht kein installiertes Python.

**Exe-Einrichtung prüfen** (eigene Aktion): prüft, ob die Exe künftig ohne Handarbeit gebaut werden kann. Übernimmt bei Bedarf eine selbst gebaute Einrichtung (vorhandene `.spec`-Datei). Geprüft wird:

1. `.spec` vorhanden, Startdatei und Symbol existieren
2. keine festen Pfade wie `C:\Users\…`, alle Pfade relativ zum Projekt
3. alle eingebundenen Dateien liegen im Projektordner
4. alle importierten Bibliotheken stehen in `requirements.txt`
5. feste Versionsnummern in `requirements.txt`
6. Probe-Build in einer frischen, leeren virtuellen Umgebung
7. Auswertung der PyInstaller-Warnungen mit Vorschlägen für versteckte Imports
8. Start-Test bzw. Selbsttest der Probe-Exe
9. externe Voraussetzungen (z. B. Ollama-Modell) sind dokumentiert
10. **Größe:** Warnung, wenn eine einzelne Exe größer als 500 MB ist. Fehler bei mehr als 2 GB, weil GitHub einzelne Download-Dateien nur bis 2 GB annimmt. Große eingebundene Dateien werden einzeln genannt, mit dem Vorschlag, sie auszulagern (10.12) oder „Programmordner“ zu wählen.

Ergebnis als Liste, Ergebnis jeweils vorne („In Ordnung: …“, „Problem: …“, „Warnung: …“), oben eine Gesamtbewertung. Sicher behebbare Probleme lassen sich per „Automatisch beheben“ nach Bestätigung korrigieren.

### 10.5 Releases

- Ergänzt am 27.09.2026: Schon in Phase 10 gibt es bei „Exe“ die Aktionen „Exe veröffentlichen …“ (Release mit Versionsnummer anlegen, Exe anhängen, direkt über die Schnittstelle von GitHub) und „Exe aus dem Release holen …“. Phase 14 ergänzt Versionshinweise, n8n und GitHub Actions.
- Ergänzt am 28.09.2026, Updates der Exe des Cockpits: Die Exe sieht beim Start und danach täglich im neuesten Release von 1013hPascal/Codecockpit nach (ohne Anmeldung). Neu ist eine Datei, wenn ihre Prüfsumme (SHA-256, von GitHub angegeben) von der laufenden Exe abweicht und das Release jünger ist als die Exe. Rückfrage: Aktualisieren, Versionshinweise, Diese Version überspringen, Später (Vorgabe). Die neue Exe wird geprüft, wartet in Exe\_neu und wird beim Neustart oder Beenden getauscht. Die bisherige kommt in die Sicherheitskopien. Daten in %APPDATA% bleiben unberührt. Schalter in den Grundeinstellungen, dazu Hilfe, Nach Updates suchen.
- Nach erfolgreichem Build und Test: Release auf der Plattform anlegen, Versionshinweise aus den Commit-Nachrichten formulieren (mit KI, falls verfügbar), Exe anhängen.
- Stabiler Download-Link, der immer auf die neueste Version zeigt: `https://github.com/NUTZER/PROJEKT/releases/latest/download/PROJEKT.exe`
- Funktioniert auch ohne Exe-Feature (dann Release nur mit Quellcode).
- Wird über n8n ausgeführt. Ist keine Automation eingerichtet, kann das Cockpit Releases als Ausweichlösung auch direkt anlegen.

### 10.6 Rückmeldungen

- Abfrage einmal täglich (Standard 8:00 Uhr) oder wöchentlich, einstellbar, zusätzlich manuell mit F5.
- Erfasst: Sterne, Issues, Kommentare, Forks, Download-Zahlen.
- Ansicht im Cockpit als Liste, neueste oben, z. B. „Neu: Kommentar von anna-k zu Issue ‚Absturz beim Öffnen großer PDFs‘, 21.09.2026, Antwortentwurf vorhanden“. Oben: „Zuletzt abgefragt: heute, 08:00 Uhr“.
- Enter öffnet den vollständigen Text, per Tab: Antwortentwurf (falls vorhanden), „Auf der Plattform öffnen“.

### 10.7 Antwortentwürfe

- Für neue Issues und Kommentare erstellt die KI einen höflichen Entwurf in der Sprache des Fragenden, auf Basis von Issue-Text, Gesprächsverlauf und README. Kann sie die Frage nicht beantworten, formuliert sie Rückfragen statt etwas zu erfinden.
- **Nie automatisch gesendet.** Im Cockpit per Tab: „Entwurf bearbeiten“, „Antworten“ (sendet nach Bestätigung), „Entwurf verwerfen“.
- Gesendet wird ausschließlich vom Cockpit, n8n hat dafür keine Rechte.

### 10.8 E-Mail-Benachrichtigungen

- E-Mail mit allen neuen Issues und Kommentaren einer Abfrage, mit Titel, Absender, Text, Link und ggf. Antwortentwurf.
- Kommt höchstens so oft, wie abgefragt wird (Standard: einmal täglich).
- Sicherheitswarnungen aus dem Abhängigkeiten-Wächter können zusätzlich sofort gemeldet werden.

### 10.9 Wochenbericht

- Standard Montag 8:00 Uhr, Wochentag und Uhrzeit einstellbar.
- Inhalt: neue Sterne und Downloads pro Projekt, offene und unbeantwortete Issues, Hinweise des Abhängigkeiten-Wächters, Projekte mit nicht hochgeladenen Änderungen, Projekte ohne Aktualisierung seit mehr als 3 Monaten (einstellbar).
- Schlicht aufgebaut mit klaren Überschriften, gut lesbar mit Screenreader.
- Pro Profil ein eigener Bericht an die Adresse des Profils, damit private und berufliche Projekte getrennt bleiben.

### 10.10 Abhängigkeiten-Wächter

- Wöchentlich: `requirements.txt` jedes Repositories lesen, neueste Versionen über die PyPI-API abfragen, Sicherheitswarnungen der Plattform (Dependabot) abrufen.
- Hinweise im Cockpit und im Wochenbericht. Es wird nichts automatisch aktualisiert.
- Beim Anlegen eines Repositories werden die Sicherheitswarnungen der Plattform eingeschaltet, falls dieses Feature aktiv ist.

### 10.11 Erinnerung

- Hinweis, wenn ein Projekt lokale Änderungen hat, die seit mehr als 7 Tagen (einstellbar) nicht hochgeladen wurden.
- Im Cockpit und im Wochenbericht, auf Wunsch zusätzlich als eigene E-Mail.
- Da n8n keinen Zugriff auf die Projektordner hat, meldet das Cockpit den Projektstatus beim Start und nach jedem Hochladen an n8n.

### 10.12 Externe Ressourcen

Für große Modelle und Daten, die nicht in die Exe gehören oder nicht hineinpassen.

**Regeln:**
- **Ollama-Modelle** (z. B. Gemma 12B) sind nie Teil der Exe. Sie werden von Ollama verwaltet und gespeichert. Das Programm braucht dann Ollama und das Modell als Voraussetzung.
- **Was beim ersten Build in der Exe war, bleibt drin**, solange die Grenzen aus Prüfpunkt 10 eingehalten werden.
- **Große Dateien, die nicht in der Exe sind**, werden beim ersten Start des Programms heruntergeladen.
- Faustregel für neue Projekte: Dateien bis 100 MB einbinden, größere auslagern. Die Grenze ist einstellbar.

**Arten von Ressourcen:**
- Ollama-Modell (Name, z. B. `gemma3:12b`)
- Modell von Hugging Face (z. B. ein Whisper-Modell)
- Datei von einer Internetadresse
- Datei als eigener Download im Release (bis 2 GB je Datei)

**Umsetzung:**
- Die Ressourcen stehen in `cockpit.toml`: Name, Art, Quelle, Größe, Zielordner, Prüfsumme.
- Auf Wunsch erzeugt das Cockpit für das Projekt ein kleines Modul `ressourcen.py`. Es prüft beim Programmstart, ob alles vorhanden ist, lädt Fehlendes mit barrierefreier Fortschrittsanzeige herunter („Modell wird heruntergeladen: 45 Prozent“) und prüft die Prüfsumme. Ollama-Modelle lädt es über Ollama selbst. Gespeichert wird im Benutzerdatenordner (z. B. `%LOCALAPPDATA%\Programmname\`), nicht neben der Exe.
- Der Selbsttest meldet fehlende Ressourcen verständlich, statt abzustürzen.
- In der README stehen die Ressourcen unter Systemanforderungen, mit Downloadgröße und benötigtem Speicherplatz.

### 10.13 Lizenzprüfung

Jede verwendete Bibliothek hat eine eigene Lizenz. Manche Lizenzen stellen Bedingungen, die mit der Lizenz des eigenen Projekts nicht zusammenpassen. Beispiel: **PyMuPDF** steht unter der AGPL (oder einer kostenpflichtigen Lizenz). Wer ein Programm mit PyMuPDF veröffentlicht, muss nach der AGPL unter anderem den eigenen Quellcode unter derselben Lizenz zugänglich machen. Mit der MIT-Lizenz passt das nicht zusammen.

- **Ermitteln:** Das Cockpit liest die Lizenzen der Bibliotheken aus der virtuellen Umgebung des Projekts (Paket-Metadaten) und ergänzt fehlende Angaben über die PyPI-API. Berücksichtigt werden auch Bibliotheken, die indirekt mitinstalliert werden.
- **Einordnen:** Lizenzen werden in Gruppen eingeteilt: freizügig (z. B. MIT, BSD, Apache 2.0), schwaches Copyleft (z. B. LGPL, MPL), starkes Copyleft (z. B. GPL, AGPL), unbekannt.
- **Prüfen:** Das Cockpit vergleicht mit der Projektlizenz und der Verbreitungsart (nur Quellcode oder zusätzlich Exe). Ergebnis als Liste, Ergebnis vorne: „Konflikt: PyMuPDF (AGPL) passt nicht zur Projektlizenz MIT, wenn die Exe veröffentlicht wird“, „Unbekannt: Lizenz von paketname nicht ermittelbar“, „In Ordnung: 23 Bibliotheken mit freizügigen Lizenzen“.
- **Lösungswege vorschlagen**, ohne selbst zu entscheiden: Projektlizenz anpassen, Bibliothek durch eine mit freizügiger Lizenz ersetzen (z. B. pypdf statt PyMuPDF, wo der Funktionsumfang reicht), Repository privat lassen.
- **Wann:** beim ersten Hochladen, vor dem Wechsel auf „öffentlich“, vor jedem Release und wenn sich die `requirements.txt` ändert. Bei Konflikten wird gewarnt, aber nicht blockiert.
- **README:** Liste der verwendeten Bibliotheken mit ihren Lizenzen. Bei einer Exe werden die Lizenztexte der enthaltenen Bibliotheken zusätzlich als Datei beigelegt, wie es viele Lizenzen verlangen.
- **Profil Beruflich:** Das Unternehmen kann eine Liste erlaubter und verbotener Lizenzen hinterlegen (Teil der exportierbaren Einstellungen). Dann richtet sich die Prüfung danach.
- Das Cockpit weist darauf hin, dass die Prüfung keine Rechtsberatung ersetzt.

### 10.14 Branches und Pull Requests

Ergänzt am 25.09.2026 (siehe ENTSCHEIDUNGEN.md): Mit Branches soll alles gehen, was GitHub kann, ohne Terminal. Die Grundfunktionen für Branches gehören zum Kern und sind immer da:

- **Immer sichtbar, wo man ist:** In der Projektliste steht „Code, Branch suche-pdfs“, wenn man nicht auf dem Hauptzweig ist. Ansagen beim Hochladen und Holen nennen den Branch.
- **Übersicht „Branches“** bei „Code“: alle Branches, lokal und auf der Plattform, mit Stand, zum Beispiel „suche-pdfs, 2 Commits vor main, 1 offener Pull Request“.
- Branch anlegen, wechseln, umbenennen, löschen.
- Hochladen und Holen arbeiten immer mit dem aktuellen Branch.
- In den Hauptzweig übernehmen: direkt zusammenführen oder über einen Pull Request (Feature).
- Änderungen beiseitelegen und zurückholen (Stash), zum Beispiel vor dem Wechsel des Branches.

Das Feature „Branches und Pull Requests“ ergänzt:

- Pull Requests erstellen, ansehen, Kommentare lesen und schreiben, prüfen (Review mit „genehmigen“ oder „Änderungen anfordern“), übernehmen, schließen.
- Schutzregeln für den Hauptzweig, wenn man Admin ist, zum Beispiel „Nur über Pull Request“ oder „Mindestens eine Genehmigung“.
- Die folgenden Punkte aus der ersten Fassung.

In Unternehmen ist das direkte Hochladen in den Hauptzweig oft gesperrt. Man arbeitet stattdessen in einem eigenen Zweig (Branch) und beantragt die Übernahme (Pull Request, bei GitLab Merge Request). Privat bleibt dieses Feature normalerweise aus.

- **Ist das Feature aktiv**, fragt „Änderungen hochladen“ zusätzlich, in welchen Zweig hochgeladen wird: bestehenden Zweig wählen oder neuen anlegen. Der Name wird aus der Commit-Nachricht vorgeschlagen (z. B. `suche-mehrere-pdfs`).
- Nach dem Hochladen: **„Pull Request erstellen“** mit Titel und Beschreibung (Vorschlag aus den Commit-Nachrichten, mit KI falls aktiv), Ziel-Zweig und optional Prüfern.
- Unter „Code“ im Projektbaum wird der aktuelle Zweig angezeigt: „Code, Zweig suche-mehrere-pdfs, 1 offener Pull Request“.
- **Pull-Request-Status** (offen, genehmigt, Änderungen angefordert, übernommen) und Kommentare zum Pull Request erscheinen unter Rückmeldungen.
- Nach der Übernahme bietet das Cockpit an, zum Hauptzweig zurückzuwechseln, die neuesten Änderungen zu holen und den erledigten Zweig aufzuräumen.
- **Branch wechseln:** Liste der Zweige. Gibt es noch nicht hochgeladene Änderungen, wird vorher gefragt, was mit ihnen passieren soll.
- **Geschützter Hauptzweig:** Lehnt die Plattform einen Push in den Hauptzweig ab, weil er geschützt ist, erklärt das Cockpit das und bietet an, dieses Feature für das Projekt einzuschalten und die Änderungen in einen neuen Zweig hochzuladen.
- Exe-Erstellung und Releases laufen bei aktivem Feature standardmäßig erst, wenn Änderungen im Hauptzweig angekommen sind.

### 10.15 Spracheingabe

Ergänzt am 27.09.2026 (Wunsch des Nutzers).

- Diktieren in jedes Eingabefeld des Cockpits, zum Beispiel die Commit-Nachricht oder einen Kommentar.
- Ein Tastenkürzel startet die Aufnahme, dasselbe Kürzel beendet sie. Der erkannte Text wird an der Schreibmarke eingefügt. Ein zweites Kürzel bricht die Aufnahme ab, ohne etwas einzufügen. Strg+D startet und beendet, Strg+Umschalt+D bricht ab (D wie Diktieren).
- Ansagen: „Aufnahme läuft.“, „Text eingefügt.“, „Aufnahme abgebrochen.“
- Spracherkennung mit Whisper, lokal auf dem Rechner oder bei einem externen Anbieter (Abschnitt 11.1). Vorbild ist das Tagebuch des Nutzers (faster-whisper und sounddevice).

### 10.16 Terminal-Erklärung

Ergänzt am 27.09.2026. Erklärt im eingebauten Terminal (9.9), warum ein Befehl fehlgeschlagen ist und was man tun kann. Die KI bekommt den Befehl und die Ausgabe, ohne Tokens und ohne gefundene Geheimnisse. Standard ist die lokale Text-KI.

### 10.17 KI-Hilfe

Ergänzt am 27.09.2026. Beantwortet Fragen zur Bedienung des Cockpits, zum Beispiel „Wo schalte ich Pull Requests ein?“. Grundlage sind die Anleitungen, die Einführungen der Features und eine Beschreibung der Menüs und Aktionen. Die Antwort nennt den Weg mit Tasten. Erreichbar über das Menü Hilfe.

## 11. KI-Anbieter

Die KI ist ein Adapter. Unter Einstellungen, KI-Anbieter werden beliebig viele Anbieter eingerichtet. Jedes Profil wählt einen davon, und in den Feature-Einstellungen kann für einzelne Aufgaben ein anderer gewählt werden (z. B. lokale KI für Commit-Vorschläge, stärkere Cloud-KI für Übersetzungen).

Unterstützte Adapter in der ersten Version:
- **Ollama** (lokal, Standard im Profil Privat, Modell aus den installierten Modellen wählbar)
- **OpenAI-kompatible Schnittstelle** mit frei einstellbarer Adresse. Deckt viele Fälle ab, z. B. LM Studio, eigene Firmen-Server und viele KI-Gateways in Unternehmen.
- **Azure OpenAI**
- **Anthropic (Claude)**
- **Google Gemini**

Weitere Adapter können ergänzt werden.

Pro Anbieter: Name, Art, Adresse, Modell, API-Schlüssel (im Tresor), zusätzliche Header (manche Firmen-Gateways verlangen welche), Knopf „Verbindung testen“.

**Datenschutz:** Wird eine Aufgabe erstmals an einen Anbieter außerhalb des eigenen Rechners geschickt, weist das Cockpit einmal darauf hin: „Für Commit-Vorschläge werden Auszüge aus deinem Code an Anthropic gesendet. Einverstanden?“. Im Profil kann festgelegt werden, dass Code-Auszüge nur an lokale oder firmeninterne Anbieter gehen dürfen.

Alle Prompts liegen in eigenen Dateien und können angepasst werden.

Die KI-Einstellungen werden auch an n8n übergeben, damit n8n für Antwortentwürfe und Versionshinweise denselben Anbieter nutzt.

### 11.1 KI-Verwaltung und lokale KI

Ergänzt am 27.09.2026 (Wunsch des Nutzers).

- Das Menü „KI“ bündelt alles zur KI. „KI-Verwaltung …“ zeigt die KI-Werkzeuge, getrennt nach Art: Text-KI (für Vorschläge, Erklärungen, Hilfe) und Sprach-KI (für die Spracheingabe).
- Jedes Werkzeug ist lokal oder extern. Lokal: Ollama für Text, Whisper für Sprache, beides auf dem eigenen Rechner. Extern: ein Anbieter aus der Kontenverwaltung. Wählt man „Extern einrichten …“, öffnet sich die Kontenverwaltung bei den KI-Anbietern.
- Man kann mehrere Werkzeuge einrichten. Die KI-Features wählen in ihren Einstellungen, welches sie nutzen. Vorgabe ist das Standard-Werkzeug der jeweiligen Art.
- „KI-Features …“ öffnet die Feature-Verwaltung (8.5) bei den KI-Features: KI-Assistent, Spracheingabe, Terminal-Erklärung, KI-Hilfe.

**Lokale KI passend zum Rechner:**
- Das Cockpit liest Arbeitsspeicher, Prozessor und Grafikkarte selbst aus. Gelingt das nicht, erklärt es, wo man die Angaben in Windows findet, und fragt sie ab.
- Daraus schlägt es ein Modell vor, in drei Stufen nach Arbeitsspeicher: ab 16 GB, ab 32 GB und ab 64 GB. Mehr Stufen braucht es nicht, für größere Modelle gibt es firmeninterne Anbieter. Die Namen der Modelle stehen an einer einzigen Stelle und lassen sich anpassen.
- Für Whisper gibt es ebenso eine Empfehlung nach Arbeitsspeicher und Grafikkarte.
- Ist ein Modell noch nicht installiert, erklärt das Cockpit den Befehl (zum Beispiel `ollama pull …`) und bietet an, ihn im eingebauten Terminal auszuführen.

## 12. Automation mit n8n

### 12.1 Einrichtung

- **Privat:** n8n lokal auf dem Laptop unter `http://localhost:5678`, kostenlos, kein eigener Server nötig. Installation über Node.js. Das Cockpit prüft beim Start, ob n8n läuft, und startet es bei Bedarf.
- **Beruflich:** alternativ Anbindung an einen n8n-Server der Firma über Adresse und API-Schlüssel. Dann startet das Cockpit nichts selbst.
- Jedes Profil wählt seine Automations-Instanz oder „keine Automation“.

### 12.2 Barrierefreiheit von n8n

Der grafische Workflow-Editor von n8n ist mit Screenreader und Braillezeile voraussichtlich schwer bedienbar. Deshalb:

- Workflows liegen als **JSON-Dateien** im Ordner des jeweiligen Features und werden versioniert. Claude Code schreibt sie.
- Wird ein Feature eingeschaltet, spielt das Cockpit die zugehörigen Workflows über die n8n-API ein und aktiviert sie. Wird es global ausgeschaltet, werden sie deaktiviert.
- Zugangsdaten legt das Cockpit über die n8n-API an (Abschnitt 5.4).
- Zu jedem Workflow gibt es eine Datei `BESCHREIBUNG.md` mit Auslöser, Schritten und Ergebnis in Worten. So lernt der Nutzer, wie n8n-Workflows aufgebaut sind.
- Die Ansicht „Automatisierungen“ zeigt Status, letzte Ausführung und Fehler jedes Workflows.

### 12.3 Verbindung zwischen Cockpit und n8n

**Cockpit → n8n (Webhooks):**
- „Einstellungen übernehmen“ bei jeder relevanten Änderung (Empfänger, Zeiten, aktive Features pro Projekt, KI-Anbieter)
- „Projektstatus melden“ beim Start und nach jedem Hochladen
- „Release veröffentlichen“
- „Jetzt ausführen“ für einzelne Workflows

**n8n → Cockpit:** Das Cockpit ruft beim Start und bei F5 den Webhook „Neuigkeiten abrufen“ auf und erhält Rückmeldungen, Hinweise und Entwürfe.

Webhooks sind mit einem geheimen Schlüssel abgesichert, der im Tresor und in n8n hinterlegt ist, damit nicht jedes Programm auf dem Rechner sie aufrufen kann.

Die Daten werden in n8n gespeichert (z. B. in einer n8n-Datentabelle). Welche Speicherart die installierte n8n-Version am besten unterstützt, prüft Claude Code bei der Umsetzung.

### 12.4 Umgang mit ausgeschaltetem Laptop

Zeitgesteuerte Workflows einer lokalen n8n-Instanz laufen nur, wenn der Laptop an ist, und n8n holt verpasste Termine nicht von selbst nach. Deshalb:

- Jeder Workflow merkt sich, wann er zuletzt erfolgreich lief.
- Beim Start prüft das Cockpit, ob etwas überfällig ist, und löst es aus.
- Rückmeldungen werden immer seit der letzten erfolgreichen Abfrage geholt, es geht nichts verloren.
- E-Mails nennen den Stand der Daten, z. B. „Projektstatus vom 20.09.2026“.

### 12.5 Workflows

| Workflow | Feature | Auslöser |
|---|---|---|
| Rückmeldungen sammeln | Rückmeldungen | täglich bzw. wöchentlich, F5 |
| Neuigkeiten abrufen | Rückmeldungen | Webhook |
| Benachrichtigung | E-Mail-Benachrichtigungen | nach „Rückmeldungen sammeln“ |
| Antwortentwürfe | Antwortentwürfe | nach „Rückmeldungen sammeln“ |
| Wochenbericht | Wochenbericht | wöchentlich |
| Abhängigkeiten prüfen | Abhängigkeiten-Wächter | wöchentlich, vor dem Wochenbericht |
| Erinnerung | Erinnerung | täglich |
| Release veröffentlichen | Releases | Webhook |
| Einstellungen übernehmen, Projektstatus | (Kern der Automation) | Webhook |

Jeder Workflow berücksichtigt, für welche Projekte das zugehörige Feature aktiv ist.

## 13. Einstellungen im Überblick

Alle Einstellungsdialoge sind einfache Formulare mit beschrifteten Feldern und „Speichern“ und „Abbrechen“. Änderungen, die n8n betreffen, werden automatisch übergeben.

**Profile:** anlegen, umbenennen, löschen. Pro Profil: Plattform-Konto, Organisation, KI-Anbieter, Automations-Instanz, E-Mail-Konto und Empfänger, Standardordner, Standardwerte für neue Projekte (Sichtbarkeit Standard privat, Lizenz, README-Sprachen, aktive Features), KI-Datenschutzregel.

**Kontenverwaltung:** Konten anlegen, bearbeiten, testen, löschen (Abschnitt 5).

**Tresor-Einstellungen:** Speicherart, Master-Passwort ändern, automatisch sperren nach Inaktivität.

**KI-Anbieter:** Anbieter anlegen, bearbeiten, testen (Abschnitt 11).

**Ordner:** Projekte-Hauptordner pro Profil.

**Netzwerk:** Proxy (keiner, System, manuell), Windows-Zertifikatsspeicher nutzen (Standard an).

**Feature-Einstellungen:** je ein Eintrag pro aktivem Feature mit eigenen Einstellungen, z. B.:
- Rückmeldungen: täglich oder wöchentlich, Uhrzeit
- Wochenbericht: Wochentag, Uhrzeit, Zeitraum für „länger nicht aktualisiert“
- Erinnerung: nach wie vielen Tagen, zusätzlich per E-Mail
- README: Abschnitte, Sprachen, Hauptsprache
- Exe: Testart, Wartezeit beim Start-Test

### 13.1 Einstellungen weitergeben

Für den Einsatz im Unternehmen können Profile, Feature-Auswahl und Einstellungen **ohne Geheimnisse** als Datei exportiert und importiert werden. So kann ein Team mit einheitlichen Einstellungen starten. Zugangsdaten gibt jeder selbst ein.

## 14. Technik

- Python 3.11 oder neuer, PySide6
- Git für Windows (Prüfung beim Start)
- Plattform-Adapter: GitHub REST API (`requests` oder `PyGithub`), GitLab (`python-gitlab`), Azure DevOps REST API
- `keyring` und `cryptography` für den Tresor
- `truststore` für Firmenzertifikate
- PyInstaller (nur Feature Exe)
- KI-Adapter mit `requests` bzw. den offiziellen Bibliotheken der Anbieter
- SQLite für Projekte, Profile, Verlauf, gelesene Rückmeldungen
- n8n (optional, lokal über Node.js oder als Firmen-Server)

Vorgeschlagene Paketstruktur (die Struktur der bestehenden Projekte des Nutzers hat Vorrang):

```
cockpit/
  ui/
  kern/          Projekte, Profile, Abläufe, Sicherheitsprüfung, Feature-Verwaltung
  tresor/        Adapter: windows, tresordatei
  plattformen/   Adapter: github, gitlab, azure_devops
  ki/            Adapter: ollama, openai_kompatibel, azure_openai, anthropic, gemini
  automation/    Adapter: n8n
  features/
    ki_assistent/
    readme/
    versionen/
    exe/
    releases/
    rueckmeldungen/     (mit n8n-workflows/)
    antwortentwuerfe/   (mit n8n-workflows/)
    ...
tests/
```

## 15. Umsetzung in Phasen

Nach jeder Phase ist das Programm nutzbar.

1. **Analyse** der bestehenden Projekte des Nutzers (Aufbau, Bedienung, Barrierefreiheit), Zusammenfassung an den Nutzer
2. **Grundgerüst:** Architektur mit Kern, Feature-System und Adapter-Schnittstellen (Plattform-Adapter mit Fähigkeiten-Abfrage, Abschnitt 6.3), Menüleiste, Profile
3. **Tresor, Konten und Ersteinrichtung:** beide Speicherarten mit Wechsel, Kontenverwaltung, Einrichtungsassistent (wird in späteren Phasen um weitere Seiten ergänzt)
4. **Plattform-Anbindung GitHub:** Anmeldung im Browser und per Token, Verbindungstest, Organisationen, Single-Sign-On-Hinweise
5. **Grundfunktionen:** Git-Identität mit noreply-Adresse, Projektaufbau mit `Code` und `Exe`, Projektbaum mit automatischem Zuklappen, Projekte hinzufügen und klonen, Reparatur nach dem Verschieben, neues Projekt hochladen, Änderungen hochladen und holen, Verlauf, Rückgängig machen, Links, Repository verwalten mit Mitarbeitern, Sicherheitsprüfung, Grundfunktionen für Branches
6. **Feature Branches und Pull Requests** mit Reviews und Schutzregeln (vorgezogen, siehe ENTSCHEIDUNGEN.md)
7. **Feature-Verwaltung** global und pro Projekt
8. **KI-Adapter** (zuerst Ollama und OpenAI-kompatibel), KI-Verwaltung mit lokaler KI passend zum Rechner, eingebautes Terminal mit Terminal-Erklärung, Feature KI-Assistent, Spracheingabe mit Whisper, KI-Hilfe (ergänzt am 27.09.2026)
9. **Features README-Pflege** (mit Sprachen) und **Versionen** mit Tags
10. **Feature Exe-Erstellung** inklusive „Exe-Einrichtung prüfen“, Hinweis zu Windows-Warnungen und Selbstaktualisierung des Cockpits, dazu **Feature Externe Ressourcen** und **Feature Lizenzprüfung**
11. **n8n-Grundlagen:** Automations-Adapter, Einspielen von Workflows, Ansicht Automatisierungen, Feature Rückmeldungen
12. **E-Mail:** Konten (SMTP mit Anbietervorlagen, Microsoft 365), Test-E-Mail, Features E-Mail-Benachrichtigungen und Wochenbericht
13. **Features Antwortentwürfe, Abhängigkeiten-Wächter, Erinnerung**
14. **Feature Releases** mit GitHub Actions (Läufe ansehen, Fehler lesen, neu starten)
15. **Weitere KI-Adapter** (Azure OpenAI, Anthropic, Gemini)
16. **Weitere Plattform-Adapter:** GitLab und Azure DevOps
17. **Sicherung** erstellen und wiederherstellen, Export und Import von Einstellungen, optionales Signieren der Exe, Feinschliff

## 16. Spätere Erweiterungen

- Weitere Plattform-Adapter: Bitbucket, Gitea
- Exe in der Cloud bauen mit GitHub Actions (in Firmen übliche Arbeitsweise „CI/CD“). Die Prüfung der Exe-Einrichtung ist dafür eine gute Vorbereitung.
- Feature Blog-Entwurf zu neuen Versionen
- Tresor-Adapter für Passwort-Manager von Unternehmen
- Weitere Programmiersprachen neben Python (z. B. eigene Build-Features für andere Sprachen)

## 17. Hinweise für Claude Code

- Vor der Umsetzung die bestehenden PySide6-Projekte des Nutzers analysieren und deren Aufbau, Bedienung und Barrierefreiheit übernehmen (Phase 1).
- Die Adapter-Schnittstellen und das Feature-System sorgfältig entwerfen, bevor Features gebaut werden. Neue Anbieter und Features sollen ohne Änderungen am Kern möglich sein.
- Geheimnisse nie in Dateien, Logs oder Fehlermeldungen schreiben.
- Jede Phase mit Tests abschließen, insbesondere für Tresor, Sicherheitsprüfung, Feature-Abhängigkeiten, Versionsberechnung, Rückgängig-Funktionen und Lizenzeinordnung.
- **Barrierefreiheit testen:** Zu jeder Phase eine kurze Testanleitung für den Nutzer schreiben, die er mit Screenreader und Braillezeile durchgeht: welche Tasten, was angesagt werden soll, wo der Fokus landen soll. Besonders gründlich beim Projektbaum (Ausklappen, automatisches Zuklappen, Ansage von Ebene und Zustand), bei Listen mit Kontrollkästchen und bei allen Dialogen. Rückmeldungen des Nutzers haben Vorrang vor Annahmen.
- Aktionen, die Dateien verändern oder löschen, immer mit Beschreibung und Bestätigung umsetzen und vorher eine lokale Sicherheitskopie anlegen.

## 18. Entscheidungen und offene Fragen

### Entschieden

- Neue Repositories sind **standardmäßig privat**, die Sichtbarkeit wird beim Anlegen gewählt.
- Standardlizenz im Profil Privat: **MIT**.
- Versionsnummern nach dem Schema **1.2.3** mit der Auswahl „Kleine Korrektur / Neue Funktion / Große Änderung“.
- README-Hauptsprache standardmäßig **Englisch**, weitere Sprachen per Mehrfachauswahl (Deutsch, Französisch, Spanisch, erweiterbar).
- Rückmeldungen werden **einmal täglich** abgefragt, wahlweise wöchentlich.
- Grundfunktionen ohne KI und n8n, alles andere als schaltbare Features.
- KI-Anbieter frei wählbar (lokal, Firma, Cloud), typische Adapter werden eingebaut.
- Plattformen: GitHub und GitHub Enterprise zuerst, GitLab und Azure DevOps eingeplant.
- Zugangsdaten verschlüsselt im Tresor. Die Speicherart wird bei der **Ersteinrichtung gewählt** (Standard: Windows-Anmeldeinformationsverwaltung) und kann später gewechselt werden.
- E-Mail: Absender und Empfänger standardmäßig dasselbe Postfach, Anbindung per SMTP mit App-Passwort und Anbietervorlagen, für Firmen Microsoft 365. Vorlagen der ersten Version: Gmail und iCloud.
- Große Dateien: Was im ersten Build steckt, bleibt drin. Ollama-Modelle sind nie Teil der Exe. Andere große Dateien werden als externe Ressourcen beim ersten Start heruntergeladen.
- Projekte in beliebigen Ordnern, Trennung privat und beruflich über Profile.
- Jedes Projekt hat einen eigenen Ordner mit `Code` und `Exe`. Der Nutzer stellt seine bestehenden Projekte selbst um, das Cockpit repariert typische Folgen des Verschiebens.
- Im Ordner `Exe` liegt immer nur die aktuelle Version. Die alte wird erst nach bestandenem Test der neuen gelöscht.
- Projekte werden als Baum angezeigt. Beim Ausklappen eines Projekts klappen alle anderen zu.
- Git-Identität pro Profil, bei GitHub mit anonymer noreply-Adresse als Vorschlag.
- Lizenzprüfung der Bibliotheken als Feature, warnt bei Konflikten (z. B. PyMuPDF/AGPL mit MIT).
- README erhält einen Hinweis zu Windows-Warnungen und die Prüfsumme der Exe. Signieren optional.
- Das Cockpit kann seine eigene Exe bauen, der Austausch erfolgt beim nächsten Start.
- Branches und Pull Requests als Feature, im Profil Beruflich standardmäßig an.
- Rückgängig machen als Grundfunktion, ohne die Geschichte auf der Plattform umzuschreiben.
- Verschlüsselte Sicherung von Tresor und Einstellungen.
- Faustregel für neue Projekte: Dateien bis **100 MB** in die Exe einbinden, größere als externe Ressource auslagern (Grenze einstellbar).

### Offen

Keine. Das Konzept ist bereit für die Umsetzung mit Claude Code.
