# Plan: Paketübersicht

Stand: 21.10.2026. Wunsch des Nutzers: Überblick über alles, was heruntergeladen wurde, mit Aktualisieren, Löschen, Version wählen und Aufräumen.

## Das Wichtigste

- Neues Menü „P&akete“ in der Menüzeile, Alt+A. Alt+P bleibt für die Liste „Projekte“.
- Ein eigenes Feature „Paketübersicht“. Man kann es in der Feature-Verwaltung ausschalten, dann verschwindet das Menü.
- Keine neue Bibliothek. Das Cockpit ruft pip, winget, choco und ollama auf. Für Hugging Face, PyPI und OSV nutzt es httpx, das schon da ist.
- Die Logik steht im Feature selbst (cockpit/features/packages) und kennt kein Qt. Der Kern holt nie etwas aus den Features.

## Entscheidungen des Nutzers

- Quellen: pip, winget, Chocolatey und Sprachmodelle.
- Filter oben: „Alles“, „Nur Cockpit-Projekte“, „Nur übriger Rechner“.
- Vor dem Löschen keine Kopie der Dateien, sondern eine Liste mit Name, Version und Quelle in den Sicherheitskopien. Damit holt das Cockpit alles wieder (Antwort vom 21.10.2026).
- Gesamttest erst ganz zum Schluss.

## Bedienung

- Fenster „Paketübersicht“: oben der Filter, dann die Liste der Quellen. Jede Zeile beginnt mit dem Namen der Quelle, danach Anzahl, veraltete und Größe. Ganz oben eine Zeile mit dem Speicherplatz.
- Enter auf einer Quelle öffnet die Pakete. Jede Zeile: Name, Version, „aktuell“ oder „veraltet, neu: 2.3.1“, Größe, Datum, „gehört zu Projekt X“ oder „benutzt von …“. Neueste zuerst.
- Tab führt zu den Knöpfen: Aktualisieren, Version wählen, Festhalten, Zurück zur vorherigen Version, Löschen, Alle veralteten aktualisieren, Änderungen ansehen.
- Ob ein Paket aktuell ist, kommt im Hintergrund kurz nach der Liste. Keine Flut von Ansagen, nur am Ende eine.
- Löschen fragt immer nach, Vorgabe und Escape „Abbrechen“.

## Stufe 1: Übersicht und Grundaktionen

1. Logik: `cockpit/features/packages/base.py` mit `Package`, `Source`, Größe, Datum, Zugehörigkeit.
2. pip: globales Python (alle über `py -0p`), jede Umgebung eines Projekts, Umgebungen für den Exe-Bau. Ein kleines Prüfprogramm im jeweiligen Python liefert Name, Version, Datum, Größe und Lizenz als JSON. Veraltet über `pip list --outdated --format=json`.
3. winget: `winget list --source winget`, Spalten aus der Kopfzeile. Datum aus der Windows-Registrierung, wenn vorhanden.
4. Chocolatey: `choco list -r` und `choco outdated -r`. Datum und Größe aus dem Ordner lib. Ändern braucht Administratorrechte, Windows fragt danach.
5. Modelle: Hugging Face (Zwischenspeicher), Ollama (Ordner models, ohne laufenden Dienst lesbar), Modelle des Cockpits (Spracheingabe), LM Studio und GPT4All, wenn vorhanden.
6. Aktionen: Aktualisieren, Version wählen (Liste der Versionen), Festhalten, Löschen. Bei Modellen: neue Fassung herunterladen und die alte behalten, andere Fassung herunterladen, alte Fassungen entfernen.
7. Verlauf in der Datenbank: alte und neue Version vor jedem Ändern. Daraus „Zurück zu 2.1.0“.
8. Oberfläche: Menü, Fenster, Filter, Speicherplatz. Feature mit Einführung.

## Stufe 2: Aufräumen und „Wer benutzt was“

1. „Benutzt von“: Das Cockpit sucht in den Projekten nach Modellnamen und Bibliotheken (requirements.txt, Code, Einstellungen der KI-Verwaltung).
2. Aufräumen: Umgebungen von Projekten, die es nicht mehr gibt, alte Umgebungen vom Exe-Bau, Zwischenspeicher von pip, Modelle ohne Benutzer, alte Fassungen von Modellen. Liste mit Kästchen und Größe, vorher die Summe des Platzes.
3. „Ordner nach Modellen durchsuchen …“: große Modelldateien in einem gewählten Ordner.

## Stufe 3: Tauschen in Projekten, Sicherheit, neuer Rechner

1. Neuere Bibliothek in Projekten: Liste der Projekte mit veralteter Version in requirements.txt. Austausch in einem eigenen Branch, neu installieren, Tests des Projekts laufen lassen, Ergebnis melden. Überführen in main macht der Nutzer.
2. Neueres Modell in Projekten: neuere Fassung desselben Modells. Nachfolger nur als Vorschlag der KI, deutlich so gekennzeichnet. Austausch im Code in einem eigenen Branch, vorher Liste der Stellen.
3. Sicherheitslücken für pip-Pakete über die freie Datenbank OSV.
4. Warnung bei einem Sprung der ersten Versionsstelle, mit Link auf die Änderungen.
5. Lizenz in der Zeile, mit der vorhandenen Einordnung.
6. Liste für einen neuen Rechner: speichern als Datei und wieder einlesen. Beim Einlesen eine Liste mit Kästchen, was fehlt.

## Prüfung

- Nach jedem Schritt nur seine eigenen Tests. Werkzeuge werden in Tests nachgebaut, nie echt aufgerufen.
- Am Schluss der Gesamttest, Checkliste in `checklisten\paketuebersicht.md`, Kurzanleitungen und Einträge in ENTSCHEIDUNGEN.md.
