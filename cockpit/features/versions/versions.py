"""Versionen mit Git-Tags (Konzept 10.3, Phase 9), ohne Qt.

Beim Hochladen wählt man "Keine neue Version" (Vorgabe), "Kleine Korrektur", "Neue Funktion" oder
"Große Änderung". Daraus wird die Nummer berechnet: aus 1.3.2 wird 1.3.3, 1.4.0 oder 2.0.0. Die
Version kommt als Tag v1.3.3 an den Commit. Steht die Nummer auch im Code, zum Beispiel
__version__ = "1.3.2", ändert das Cockpit sie mit, im selben Commit (Frage 3 zu Phase 9).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from cockpit.core import git

_TAG = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
_VERSION_LINE = re.compile(r"""^(__version__\s*=\s*)(["'])(\d+\.\d+\.\d+)(["'])""", re.MULTILINE)
SKIP = {".venv", "venv", "env", "build", "dist", "__pycache__", ".git", "tests"}

NONE, PATCH, MINOR, MAJOR = 0, 1, 2, 3
KIND_NAMES = ("Keine neue Version", "Kleine Korrektur", "Neue Funktion", "Große Änderung")


def parse(text: str) -> tuple[int, int, int] | None:
    match = _TAG.match(text.strip())
    return tuple(int(x) for x in match.groups()) if match else None


def tags(code_dir: Path) -> list[str]:
    return [t for t in git.run(["tag", "--list"], code_dir, check=False).stdout.split() if t]


def current(code_dir: Path) -> str:
    """Höchste Version aus den Tags, leer wenn es noch keine gibt."""
    versions = sorted(v for v in map(parse, tags(code_dir)) if v)
    return ".".join(map(str, versions[-1])) if versions else ""


def bump(version: str, kind: int) -> str:
    """Nächste Nummer. Ohne bisherige Version ist die erste 1.0.0."""
    parsed = parse(version) if version else None
    if parsed is None:
        return "1.0.0"
    major, minor, patch = parsed
    if kind == MAJOR:
        return f"{major + 1}.0.0"
    if kind == MINOR:
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def options(version: str) -> tuple[str, ...]:
    """Die Auswahl beim Hochladen, mit der Nummer, die daraus würde."""
    return (KIND_NAMES[NONE],) + tuple(f"{KIND_NAMES[kind]}, Version {bump(version, kind)}"
                                        for kind in (PATCH, MINOR, MAJOR))


def find_version_file(code_dir: Path) -> str:
    """Datei mit __version__ = "x.y.z": oben im Ordner Code oder in einem Paket darunter."""
    candidates = sorted(code_dir.glob("*.py")) + sorted(code_dir.glob("*/__init__.py"))
    for path in candidates:
        if SKIP & set(path.relative_to(code_dir).parts[:-1]):
            continue
        try:
            if _VERSION_LINE.search(path.read_text(encoding="utf-8", errors="replace")):
                return path.relative_to(code_dir).as_posix()
        except OSError:
            continue
    return ""


def set_version_in_file(path: Path, version: str) -> bool:
    """Nummer in der Datei ersetzen. False, wenn dort keine steht."""
    text = path.read_text(encoding="utf-8")
    new, found = _VERSION_LINE.subn(lambda m: f"{m.group(1)}{m.group(2)}{version}{m.group(4)}",
                                   text, count=1)
    if found:
        path.write_text(new, encoding="utf-8")
    return bool(found)


def create_tag(code_dir: Path, version: str) -> str:
    tag = f"v{version}"
    git.run(["tag", "-a", tag, "-m", f"Version {version}"], code_dir, action="Version setzen")
    return tag


def push_tag(code_dir: Path, version: str, env: dict[str, str] | None = None,
             cancel=None) -> None:
    git.run(["push", "origin", f"refs/tags/v{version}"], code_dir, env=env, timeout=None,
            cancel=cancel, action="Version hochladen")


@dataclass
class Released:
    version: str
    date: str                          # TT.MM.JJJJ
    subjects: list[str]                # Commit-Nachrichten, erste Zeile


def history(code_dir: Path, limit: int = 3) -> list[Released]:
    """Die letzten Versionen mit ihren Commits, neueste zuerst. Für die README (Änderungen)."""
    ordered = sorted((v, t) for t in tags(code_dir) if (v := parse(t)))
    result: list[Released] = []
    for index in range(len(ordered) - 1, max(-1, len(ordered) - 1 - limit), -1):
        version, tag = ordered[index]
        since = f"{ordered[index - 1][1]}..{tag}" if index > 0 else tag
        log = git.run(["log", "--format=%s", "--no-merges", since], code_dir, check=False)
        date = git.run(["log", "-1", "--format=%cd", "--date=format:%d.%m.%Y", tag], code_dir,
                       check=False).stdout.strip()
        subjects = [s for s in log.stdout.splitlines() if s.strip()]
        result.append(Released(".".join(map(str, version)), date, subjects))
    return result
