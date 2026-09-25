"""Testdaten für die Tests mit NVDA (Start mit start_testdaten.bat).

Alles liegt in einem eigenen Ordner %LOCALAPPDATA%\\CodeCockpit\\Testdaten und wird bei jedem
Start neu angelegt. Die echten Daten des Cockpits werden nicht berührt.

Die Einrichtung beginnt bei jedem Start neu. Wählt man die Windows-Anmeldeinformationsverwaltung,
liegen die Test-Zugangsdaten dort unter einem eigenen Namen (VAULT_SERVICE) und werden beim nächsten
Start gelöscht. Dazu gibt es die Testplattform für die Kontenverwaltung (testdata_platform.py).

Beispielprojekte:
- PDF-Chat: Code und Exe. Die Exe ist absichtlich keine echte Exe, damit man das Fehlerfenster
  testen kann.
- Tagebuch: nur Code.
- Bildbeschreiber: Code und ein leerer Ordner Exe.
- Notizen: steht in der Liste, der Ordner fehlt aber ("Ordner nicht gefunden").

Ab Phase 5a mit Git (nur, wenn Git installiert ist):
- PDF-Chat und Tagebuch sind Git-Repositories. Ihre "Plattform" ist ein Ordner mit nackten
  Repositories (Testdaten\\Plattform). PDF-Chat ist ganz hochgeladen, in Tagebuch ist eine Datei
  geändert.
- Tagebuch hat eine virtuelle Umgebung, die angeblich an einem anderen Ort angelegt wurde. So lässt
  sich "Virtuelle Umgebung neu anlegen" prüfen.
- Bildbeschreiber hat keinen Git-Ordner ("noch nicht auf GitHub").
- Ab Phase 5c: Ein "anderer Rechner" (Testdaten\\Anderer Rechner) hat Änderungen zu PDF-Chat,
  Tagebuch und Rezepte hochgeladen. Rezepte hat dazu einen eigenen Commit, der dieselbe Zeile
  ändert (Konflikt beim Zusammenführen). Bei Tagebuch gibt es einen Konflikt mit der Änderung,
  die noch nicht hochgeladen ist.
- Ab Phase 5d: PDF-Chat hat einen Verlauf mit fünf Versionen, eine davon mit dem Tag v1.0.0. Dazu
  kommen eine geänderte Datei (main.py) und eine neue Datei (versuch.py) zum Verwerfen. Der Commit
  "Rezept geändert" in Rezepte ist noch nicht hochgeladen und lässt sich zurücknehmen.
- Im Ordner Testdaten\\Andere Ordner liegen Ordner zum Prüfen von "Vorhandenes Projekt
  hinzufügen": "Wetter" (Projektordner mit Code), "Rechner" und "Firmenprojekt" (ohne Code),
  "Vereinsseite" (mit anderer Git-Identität), "codecockpit-test" (mit erfundenen Geheimnissen) und "Notizen" (neuer Ort für das fehlende Projekt).
"""
from __future__ import annotations

import logging
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from cockpit import APP_NAME
from cockpit.core import git
from cockpit.core.backups import remove_tree
from cockpit.core.errors import CockpitError
from cockpit.core.paths import HOME_VARIABLE

log = logging.getLogger(__name__)

VAULT_SERVICE = "CodeCockpit Testdaten"
IN_USE = ("Die Testdaten werden noch von einem offenen CodeCockpit benutzt. Bitte schließen Sie "
          "zuerst alle Fenster von CodeCockpit mit Testdaten.")

FAKE_EXE_TEXT = "Dies ist keine echte Exe. Sie gehört zu den Testdaten von CodeCockpit.\n"


def base_dir() -> Path:
    local = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    return local / APP_NAME / "Testdaten"


def prepare(base: Path | None = None) -> tuple[Path, Path]:
    """Testdaten neu anlegen. Gibt (Datenordner, Projekte-Hauptordner) zurück und lenkt den
    Datenordner des Cockpits dorthin um."""
    base = base or base_dir()
    if base.exists():
        # Erst umbenennen: Das klappt nur, wenn kein offenes Cockpit Dateien darin benutzt.
        # So wird nie ein halber Ordner gelöscht, während ein anderes Fenster ihn noch braucht.
        old = base.with_name(base.name + "-alt")
        remove_tree(old)                    # Rest eines früheren Starts
        if old.exists():
            raise CockpitError(IN_USE, f"{old} ließ sich nicht löschen.")
        try:
            base.rename(old)
        except OSError as exc:
            raise CockpitError(IN_USE, str(exc)) from None
        remove_old_vault_entries(old / "Daten" / "cockpit.db")
        remove_tree(old)
    home = base / "Daten"
    root = base / "Projekte"
    home.mkdir(parents=True)
    root.mkdir(parents=True)

    def project(name: str, files: dict[str, str], exe: str | None = None,
                empty_exe: bool = False) -> Path:
        code = root / name / "Code"
        code.mkdir(parents=True)
        for filename, content in files.items():
            (code / filename).write_text(content, encoding="utf-8")
        if exe is not None or empty_exe:
            (root / name / "Exe").mkdir()
        if exe is not None:
            (root / name / "Exe" / exe).write_text(FAKE_EXE_TEXT, encoding="utf-8")
        return code

    # Reihenfolge der Änderungszeit: zuletzt angelegte stehen oben
    project("Notizen", {"notizen.py": "print('Notizen')\n"})
    project("Rezepte", {"rezepte.py": "REZEPT = 'Pfannkuchen'\n"})
    project("Bildbeschreiber", {"main.py": "print('Bildbeschreiber')\n"}, empty_exe=True)
    time.sleep(0.02)
    project("Tagebuch", {"main.py": "print('Tagebuch')\n", "README.md": "# Tagebuch\n"})
    time.sleep(0.02)
    project("PDF-Chat", {"main.py": "print('PDF-Chat')\n", "README.md": "# PDF-Chat\n",
                         "alt.py": "# Diese Datei wird später gelöscht\n"},
            exe="PDF-Chat.exe")
    if git.find_git() is not None:
        try:
            add_git(base, root)
        except (OSError, subprocess.CalledProcessError) as exc:
            log.warning("Testdaten ohne Git: %r", exc)
    others = base / "Andere Ordner"
    (others / "Wetter" / "Code").mkdir(parents=True)
    (others / "Wetter" / "Code" / "wetter.py").write_text("print('Wetter')\n", encoding="utf-8")
    for name in ("Rechner", "Firmenprojekt"):
        (others / name).mkdir(parents=True)
        (others / name / "main.py").write_text(f"print('{name}')\n", encoding="utf-8")
    # Für "Auf GitHub hochladen" (Phase 5b): mit erfundenem Token, Passwort-Zeile, .env und
    # Datenbank. Der Token wird erst hier zusammengesetzt und ist nicht echt.
    # "sicherheitstest" ist derselbe Inhalt für Nachtests, ohne je hochgeladen zu werden.
    fake_token = "ghp" + "_" + "Erfunden" + "0123456789" * 3
    for name in ("codecockpit-test", "sicherheitstest"):
        test = others / name
        test.mkdir(parents=True)
        (test / "main.py").write_text("print('Test für CodeCockpit')\n", encoding="utf-8")
        (test / "config.py").write_text(f'TOKEN = "{fake_token}"\npassword = "Sommer2026!"\n',
                                        encoding="utf-8")
        (test / ".env").write_text("GEHEIM=erfunden\n", encoding="utf-8")
        (test / "daten.db").write_bytes(b"SQLite format 3\0erfunden")
    # Neuer Ort für Notizen (das Projekt fehlt im Hauptordner)
    (others / "Notizen" / "Code").mkdir(parents=True)
    (others / "Notizen" / "Code" / "notizen.py").write_text("print('Notizen')\n",
                                                           encoding="utf-8")
    if git.find_git() is not None:
        # Projekt mit einer anderen Git-Identität, für die Rückfrage beim Hinzufügen
        code = others / "Vereinsseite" / "Code"
        code.mkdir(parents=True)
        (code / "index.html").write_text("<h1>Verein</h1>\n", encoding="utf-8")
        try:
            _git(code, "init", "-q")
            _git(code, "config", "--local", "user.name", "Alter Name")
            _git(code, "config", "--local", "user.email", "alt@example.org")
        except (OSError, subprocess.CalledProcessError) as exc:
            log.warning("Testdaten ohne Vereinsseite: %r", exc)
    os.environ[HOME_VARIABLE] = str(home)
    return home, root


def _git(cwd: Path, *args: str) -> None:
    """Git für die Testdaten, mit fester Identität nur auf dieser Befehlszeile (ohne
    Geheimnisse)."""
    subprocess.run([str(git.find_git()), "-c", "user.name=Testdaten",
                    "-c", "user.email=testdaten@example.org", "-c", "init.defaultBranch=main",
                    *args], cwd=cwd, check=True, capture_output=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def add_git(base: Path, root: Path) -> None:
    """PDF-Chat und Tagebuch zu Git-Repositories mit einer "Plattform" im Dateisystem machen."""
    platform = base / "Plattform"
    platform.mkdir()
    for name in ("PDF-Chat", "Tagebuch", "Rezepte"):
        code = root / name / "Code"
        _git(code, "init", "-q")
        _git(code, "add", "-A")
        _git(code, "commit", "-q", "-m", "Erste Version", "--date", "2026-09-19T09:00:00")
        bare = platform / f"{name}.git"
        _git(platform, "init", "-q", "--bare", str(bare))
        _git(code, "remote", "add", "origin", bare.as_uri())
        _git(code, "push", "-q", "-u", "origin", "main")
    add_history(root / "PDF-Chat" / "Code")
    (root / "Tagebuch" / "Code" / "main.py").write_text("print('Tagebuch, geändert')\n",
                                                        encoding="utf-8")
    # Virtuelle Umgebung, die angeblich an einem anderen Ort angelegt wurde
    venv = root / "Tagebuch" / "Code" / ".venv"
    (venv / "Scripts").mkdir(parents=True)
    python = Path(getattr(sys, "_base_executable", sys.executable))
    python = python.with_name("python.exe") if python.name.lower() == "pythonw.exe" else python
    old = base / "Alter Ort" / "Tagebuch" / "Code" / ".venv"
    (venv / "pyvenv.cfg").write_text(
        f"home = {python.parent}\ninclude-system-site-packages = false\n"
        f"version = {sys.version.split()[0]}\nexecutable = {python}\n"
        f"command = {python} -m venv {old}\n", encoding="utf-8")
    (venv / "Scripts" / "activate.bat").write_text(f'@echo off\nset "VIRTUAL_ENV={old}"\n',
                                                   encoding="utf-8")
    (root / "Tagebuch" / "Code" / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    _git(root / "Tagebuch" / "Code", "add", ".gitignore")
    _git(root / "Tagebuch" / "Code", "commit", "-q", "-m", ".gitignore")
    _git(root / "Tagebuch" / "Code", "push", "-q")
    add_other_computer(base, root)


def add_history(code: Path) -> None:
    """Phase 5d: Verlauf für PDF-Chat, alles hochgeladen. Danach eine geänderte und eine neue
    Datei, die noch nicht hochgeladen sind (zum Verwerfen)."""
    versions = [
        ("Hilfe ergänzt", {"hilfe.py": "print('Hilfe')\n"}, "2026-09-20T10:00:00"),
        ("Einstellungen ergänzt", {"einstellungen.py": "SPRACHE = 'de'\n",
                                   "main.py": "print('PDF-Chat mit Einstellungen')\n"},
         "2026-09-21T11:30:00"),
        ("Alte Datei entfernt", {"alt.py": None}, "2026-09-22T09:15:00"),
        ("Hilfetext geändert", {"hilfe.py": "print('Hilfe, versehentlich kaputt')\n"},
         "2026-09-23T16:45:00"),
    ]
    for message, files, date in versions:
        for name, content in files.items():
            if content is None:
                (code / name).unlink()
            else:
                (code / name).write_text(content, encoding="utf-8")
        _git(code, "add", "-A")
        _git(code, "commit", "-q", "-m", message, "--date", date)
        if message == "Hilfe ergänzt":
            _git(code, "tag", "v1.0.0")
    _git(code, "push", "-q", "--tags", "origin", "main")
    (code / "main.py").write_text("print('PDF-Chat, nur ausprobiert')\n", encoding="utf-8")
    (code / "versuch.py").write_text("print('Versuch')\n", encoding="utf-8")


def add_other_computer(base: Path, root: Path) -> None:
    """Phase 5c: Ein "anderer Rechner" lädt Änderungen hoch, damit man Holen prüfen kann.

    - PDF-Chat: eine neue Datei. Holen geht ohne Rückfrage nach Beiseitelegen.
    - Tagebuch: main.py ist hier geändert und auf der Plattform anders geändert. Holen fragt nach
      Beiseitelegen, danach gibt es einen Konflikt beim Zurücklegen.
    - Rezepte: Hier und auf der Plattform gibt es je einen Commit, der dieselbe Zeile ändert.
      Holen führt zu einem Konflikt beim Zusammenführen.
    Danach holt das Cockpit den Stand (git fetch), damit die Liste "noch nicht geholt" zeigt."""
    platform = base / "Plattform"
    other = base / "Anderer Rechner"
    other.mkdir()
    changes = {
        "PDF-Chat": ("suche.py", "print('Suche in mehreren PDFs')\n", "Suche ergänzt"),
        "Tagebuch": ("main.py", "print('Tagebuch vom anderen Rechner')\n", "Ausgabe geändert"),
        "Rezepte": ("rezepte.py", "REZEPT = 'Apfelstrudel'\n", "Rezept vom anderen Rechner"),
    }
    for name, (filename, content, message) in changes.items():
        _git(other, "clone", "-q", (platform / f"{name}.git").as_uri(), name)
        (other / name / filename).write_text(content, encoding="utf-8")
        _git(other / name, "add", "-A")
        _git(other / name, "commit", "-q", "-m", message)
        _git(other / name, "push", "-q")
    code = root / "Rezepte" / "Code"
    (code / "rezepte.py").write_text("REZEPT = 'Kartoffelsuppe'\n", encoding="utf-8")
    _git(code, "commit", "-q", "-am", "Rezept geändert")
    for name in changes:
        _git(root / name / "Code", "fetch", "-q")


def remove_missing_example(root: Path) -> None:
    """Nach dem ersten Einlesen den Ordner von Notizen löschen, damit er als fehlend erscheint."""
    remove_tree(root / "Notizen")


def remove_old_vault_entries(database: Path, backend=None) -> int:
    """Test-Zugangsdaten des letzten Starts aus der Windows-Anmeldeinformationsverwaltung löschen.
    Gelöscht wird nur unter VAULT_SERVICE, nie unter dem echten Namen des Cockpits."""
    if not database.is_file():
        return 0
    try:
        connection = sqlite3.connect(database)
        try:
            names = [row[0] for row in connection.execute("SELECT name FROM vault_names")]
        finally:
            connection.close()                  # sonst lässt Windows den Ordner nicht löschen
    except sqlite3.Error:
        return 0
    if not names:
        return 0
    import keyring
    from keyring.errors import KeyringError
    backend = backend or keyring.get_keyring()
    removed = 0
    for name in names:
        try:
            backend.delete_password(VAULT_SERVICE, name)
            removed += 1
        except KeyringError:
            pass
    log.info("%s alte Test-Einträge im Tresor gelöscht", removed)
    return removed
