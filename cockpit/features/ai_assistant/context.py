"""Was die KI für einen Vorschlag bekommt (Konzept 10.1, Frage 8 zu Phase 8).

Nie der ganze Code, sondern eine vorbereitete Übersicht:
- Commit: die Liste der geänderten Dateien und die geänderten Zeilen.
- Pull Request: die Commit-Nachrichten, die Liste der Dateien und die geänderten Zeilen.
- Kurzbeschreibung: die Dateiliste, der Anfang der README, die Imports und requirements.txt.

Datenschutz:
- Dateien, die die Sicherheitsprüfung als Geheimnis oder private Daten erkennt (zum Beispiel .env
  oder eine Datenbank), gehen nie mit. Die Übersicht nennt nur ihren Namen.
- Zeilen mit einem gefundenen Geheimnis werden durch "[entfernt]" ersetzt.
- Höchstens so viele Zeichen, wie die Grundeinstellung erlaubt.
"""
from __future__ import annotations

import re
from pathlib import Path

from cockpit.core import git, safety_check, sync
from cockpit.core.ai_tools import limit_text
from cockpit.core.logging_setup import mask_secrets

REMOVED = "[entfernt]"
NEW_FILE_LINES = 80                  # von neuen Dateien nur der Anfang
MAX_NEW_FILE_BYTES = 200_000
_DIFF_HEADER = re.compile(r"^diff --git a/(.+?) b/(.+)$")
_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w., ]+))")


def confidential(path: str) -> bool:
    """Datei mit Geheimnissen oder privaten Daten, die nie an die KI geht."""
    return bool(safety_check.SECRET_FILES.search(path) or safety_check.PRIVATE_FILES.search(path))


def redact(text: str) -> str:
    """Zeilen mit einem gefundenen Geheimnis ersetzen, bekannte Geheimnisse verdecken."""
    lines = [REMOVED if safety_check._secret_in_line(line) else line
             for line in text.splitlines()]
    return mask_secrets("\n".join(lines))


def filter_diff(diff: str) -> str:
    """Abschnitte vertraulicher Dateien aus einem git diff entfernen."""
    kept: list[str] = []
    skip = False
    for line in diff.splitlines():
        match = _DIFF_HEADER.match(line)
        if match:
            skip = confidential(match.group(2))
            if skip:
                kept.append(f"Datei {match.group(2)}: Inhalt nicht gesendet, vertraulich.")
                continue
        if not skip:
            kept.append(line)
    return "\n".join(kept)


def _has_commit(code_dir: Path) -> bool:
    return git.run(["rev-parse", "-q", "--verify", "HEAD"], code_dir,
                   check=False).returncode == 0


def _new_file(code_dir: Path, path: str) -> str:
    file = code_dir / path
    try:
        if not file.is_file() or file.stat().st_size > MAX_NEW_FILE_BYTES:
            return f"Neue Datei {path}: zu groß, Inhalt nicht gesendet."
        data = file.read_bytes()
    except OSError:
        return f"Neue Datei {path}: nicht lesbar."
    if b"\0" in data[:8192]:
        return f"Neue Datei {path}: keine Textdatei."
    lines = data.decode("utf-8", "replace").splitlines()
    head = "\n".join(lines[:NEW_FILE_LINES])
    more = f"\n… und {len(lines) - NEW_FILE_LINES} weitere Zeilen" \
        if len(lines) > NEW_FILE_LINES else ""
    return f"Neue Datei {path}:\n{head}{more}"


def commit_context(code_dir: Path, max_chars: int) -> str:
    """Übersicht für die Commit-Nachricht."""
    changes = sync.changes(code_dir)
    parts = ["Geänderte Dateien:", *changes.lines()]
    tracked = [f for f in changes.modified + changes.deleted + changes.renamed]
    if tracked and _has_commit(code_dir):
        diff = git.run(["diff", "HEAD", "--no-color", "--unified=2", "--", *tracked], code_dir,
                       check=False).stdout
        if diff.strip():
            parts += ["", "Geänderte Zeilen:", filter_diff(diff)]
    for path in changes.added:
        parts += ["", f"Neue Datei {path}: Inhalt nicht gesendet, vertraulich."
                  if confidential(path) else _new_file(code_dir, path)]
    return limit_text(redact("\n".join(parts)), max_chars)


def pull_request_context(code_dir: Path, head: str, base: str, max_chars: int) -> str:
    """Übersicht für Titel und Beschreibung eines Pull Requests."""
    from cockpit.core.pull_requests import _base_ref, commit_subjects
    base_ref = _base_ref(code_dir, base)
    parts = [f"Branch {head} soll nach {base}.", "", "Commit-Nachrichten:",
             *commit_subjects(code_dir, head, base)]
    names = git.run(["diff", "--name-status", f"{base_ref}...{head}"], code_dir,
                    check=False).stdout.strip()
    if names:
        parts += ["", "Geänderte Dateien:", names]
    diff = git.run(["diff", "--no-color", "--unified=1", f"{base_ref}...{head}"], code_dir,
                   check=False).stdout
    if diff.strip():
        parts += ["", "Geänderte Zeilen:", filter_diff(diff)]
    return limit_text(redact("\n".join(parts)), max_chars)


def _imports(code_dir: Path, files: list[str]) -> list[str]:
    found: set[str] = set()
    for path in [f for f in files if f.endswith(".py")][:60]:
        try:
            text = (code_dir / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines()[:80]:
            match = _IMPORT.match(line)
            if not match:
                continue
            names = match.group(1) or match.group(2)
            for name in names.split(","):
                name = name.strip().split(" ")[0].split(".")[0]
                if name:
                    found.add(name)
    return sorted(found)


def project_context(code_dir: Path, name: str, max_chars: int) -> str:
    """Übersicht für die Kurzbeschreibung eines neuen Projekts."""
    files = [f for f in safety_check.files_to_upload(code_dir) if not confidential(f)]
    parts = [f"Projekt: {name}", "", "Dateien:", *files[:150]]
    if len(files) > 150:
        parts.append(f"… und {len(files) - 150} weitere Dateien")
    for readme in ("README.md", "README.txt", "README"):
        if readme in files:
            text = (code_dir / readme).read_text(encoding="utf-8", errors="replace")
            parts += ["", f"Anfang von {readme}:", "\n".join(text.splitlines()[:60])]
            break
    imports = _imports(code_dir, files)
    if imports:
        parts += ["", "Importierte Module: " + ", ".join(imports)]
    if "requirements.txt" in files:
        text = (code_dir / "requirements.txt").read_text(encoding="utf-8", errors="replace")
        parts += ["", "requirements.txt:", "\n".join(text.splitlines()[:40])]
    return limit_text(redact("\n".join(parts)), max_chars)
