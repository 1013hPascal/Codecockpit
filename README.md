# Codecockpit
Cockpit für Windows, das Code-Projekte auf GitHub verwaltet, von KI unterstützt und mit automatisierten Abläufen.

## Download

Die neueste Version: [CodeCockpit.zip herunterladen](https://github.com/1013hPascal/Codecockpit/releases/latest/download/CodeCockpit.zip). Für Windows 10 und 11.

## Funktionen

- Verwaltung von Code-Projekten auf GitHub.
- Unterstützung durch KI für Vorschläge bei Commit-Nachrichten, Titeln und Beschreibungen von Pull Requests sowie Kurzbeschreibungen neuer Projekte und Versionshinweise.
- Automatisierte Abläufe für das Prüfen, Bauen, Testen und Veröffentlichen.
- Terminal-Erklärungen: Bei fehlgeschlagenen Befehlen im eingebauten Terminal erklärt die KI den Fehler und macht Lösungsvorschläge.
- Barrierefreie Bedienung vollständig mit der Tastatur.
- Unterstützung von lokaler KI (z.B. via Ollama) oder externen KI-Diensten über eine OpenAI-kompatible Schnittstelle.

## Bedienung

Das Programm ist barrierefrei und vollständig per Tastatur bedienbar.

## Systemanforderungen

Windows 10 oder 11.

## Werkzeuge und Bibliotheken

- PySide6
- tomli_w
- keyring
- cryptography
- httpx
- truststore
- faster-whisper
- sounddevice
- numpy

## Installation aus dem Quellcode

Sie brauchen Python 3.11 oder neuer und Git.

```
git clone https://github.com/1013hPascal/Codecockpit.git
cd Codecockpit
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Änderungen

### 1.1.27 (14.10.2026)

- Mehrere Module und UI Komponenten überarbeitet

### 1.1.26 (11.10.2026)

- Logik für das Beibehalten alter Versionen bei Neustarts korrigiert

### 1.1.25 (11.10.2026)

- Fehlerbehebung beim Erstellen von Exe-Dateien für VokabelApp und Tagebuch

## Windows-Warnungen

Windows warnt vielleicht mit „Der Computer wurde durch Windows geschützt“, weil die Exe nicht signiert ist. Wählen Sie „Weitere Informationen“ und dann „Trotzdem ausführen“.

Prüfsumme (SHA-256) der Exe: `ec2cf77dfee4f4ad8929221a1af6e86981f09efe345f18a4e99e6a1806a44b6f`

## Lizenz

Lizenz: MIT. Der vollständige Text steht in [LICENSE](LICENSE).
