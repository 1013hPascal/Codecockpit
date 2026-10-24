"""Konfliktstellen einer Datei vorlesen und einzeln lösen (Wunsch des Nutzers vom 21.10.2026,
nach dem Vergleich mit GitHub Desktop).

Eine Datei mit Konflikt hat eine oder mehrere Stellen zwischen "<<<<<<<" und ">>>>>>>". Jede Stelle
lässt sich vorlesen: erst meine Fassung, dann die der Plattform. Danach wählt man pro Stelle meine
Fassung, die der Plattform oder beide. Nur diese Stelle in der Datei ändert sich, der Rest bleibt.

Rückweg: Solange das Zusammenführen nicht abgeschlossen ist, kennt Git alle Fassungen noch. Mit
restore() kommen alle Konfliktmarken der Datei zurück (git checkout -m), vorher mit
Sicherheitskopie der Datei.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from cockpit.core import backups, git
from cockpit.core.errors import CockpitError
from cockpit.core.sync import ConflictKind
from cockpit.core.text import count

MINE, THEIRS, BOTH = "mine", "theirs", "both"


@dataclass
class Block:
    """Eine Konfliktstelle. line: Zeile von "<<<<<<<" in der Datei, ab 1."""
    number: int
    line: int
    mine: list[str] = field(default_factory=list)
    theirs: list[str] = field(default_factory=list)
    base: list[str] = field(default_factory=list)          # nur bei diff3
    platform_name: str = "GitHub"

    def label(self, total: int) -> str:
        return (f"Stelle {self.number} von {total}, Zeile {self.line}: meine Fassung "
                f"{count(len(self.mine), 'Zeile', 'Zeilen')}, {self.platform_name} "
                f"{count(len(self.theirs), 'Zeile', 'Zeilen')}")

    def readable(self) -> list[str]:
        """Zum Vorlesen: zuerst meine Fassung, dann die der Plattform, jede Zeile mit Nummer."""
        lines = [f"Meine Fassung, {count(len(self.mine), 'Zeile', 'Zeilen')}:"]
        lines += [f"{n}: {text}" for n, text in enumerate(self.mine, 1)] or ["leer"]
        lines.append(f"Fassung von {self.platform_name}, "
                     f"{count(len(self.theirs), 'Zeile', 'Zeilen')}:")
        lines += [f"{n}: {text}" for n, text in enumerate(self.theirs, 1)] or ["leer"]
        if self.base:
            lines.append(f"Gemeinsamer Ausgangsstand, {count(len(self.base), 'Zeile', 'Zeilen')}:")
            lines += [f"{n}: {text}" for n, text in enumerate(self.base, 1)]
        return lines


@dataclass
class _Raw:
    start: int                                  # Index der Zeile "<<<<<<<"
    end: int                                    # Index der Zeile ">>>>>>>"
    first: list[bytes]
    second: list[bytes]
    base: list[bytes]


def _decode(line: bytes) -> str:
    return line.rstrip(b"\r\n").decode("utf-8", "replace")


def _scan(lines: list[bytes]) -> list[_Raw]:
    found: list[_Raw] = []
    section = ""
    current: _Raw | None = None
    for index, line in enumerate(lines):
        if line.startswith(b"<<<<<<<"):
            current = _Raw(index, index, [], [], [])
            section = "first"
        elif current is None:
            continue
        elif section == "first" and line.startswith(b"|||||||"):
            section = "base"
        elif section in ("first", "base") and line.startswith(b"======="):
            section = "second"
        elif section == "second" and line.startswith(b">>>>>>>"):
            current.end = index
            found.append(current)
            current, section = None, ""
        else:
            {"first": current.first, "base": current.base, "second": current.second}[
                section].append(line)
    return found


def _read(code_dir: Path, path: str) -> list[bytes]:
    try:
        return (code_dir / path).read_bytes().splitlines(keepends=True)
    except OSError as exc:
        raise CockpitError(f"{path} ließ sich nicht lesen.", str(exc)) from None


def _mine_first(kind: ConflictKind) -> bool:
    # Oben steht bei Git immer "ours": beim Zusammenführen meine Fassung, beim Zurücklegen der
    # beiseitegelegten Änderungen die der Plattform (wie in sync.label_conflicts).
    return kind is not ConflictKind.STASH


def blocks(code_dir: Path, path: str, kind: ConflictKind,
           platform_name: str = "GitHub") -> list[Block]:
    """Die Konfliktstellen der Datei, oben zuerst."""
    result = []
    for number, raw in enumerate(_scan(_read(code_dir, path)), 1):
        first = [_decode(x) for x in raw.first]
        second = [_decode(x) for x in raw.second]
        mine, theirs = (first, second) if _mine_first(kind) else (second, first)
        result.append(Block(number, raw.start + 1, mine, theirs,
                            [_decode(x) for x in raw.base], platform_name))
    return result


def resolve_block(code_dir: Path, path: str, number: int, choice: str,
                  kind: ConflictKind) -> int:
    """Eine Stelle lösen: MINE, THEIRS oder BOTH (meine zuerst). Gibt zurück, wie viele Stellen
    danach noch offen sind."""
    lines = _read(code_dir, path)
    found = _scan(lines)
    if not 1 <= number <= len(found):
        raise CockpitError("Diese Konfliktstelle gibt es nicht mehr. Lesen Sie die Datei neu.")
    raw = found[number - 1]
    mine, theirs = (raw.first, raw.second) if _mine_first(kind) else (raw.second, raw.first)
    # Zeilen in einer Stelle enden immer mit einem Zeilenende, weil danach eine Marke folgt
    chosen = {MINE: mine, THEIRS: theirs, BOTH: mine + theirs}[choice]
    new = lines[:raw.start] + chosen + lines[raw.end + 1:]
    try:
        (code_dir / path).write_bytes(b"".join(new))
    except OSError as exc:
        raise CockpitError(f"{path} ließ sich nicht speichern.", str(exc)) from None
    return len(found) - 1


def restore(code_dir: Path, path: str) -> Path:
    """Alle Konfliktmarken der Datei zurückholen, solange das Zusammenführen noch läuft. Vorher
    kommt die Datei, wie sie jetzt ist, in eine Sicherheitskopie. Gibt deren Ordner zurück."""
    folder = backups.new_backup_dir(code_dir.name, f"vor dem Zurückholen der Konflikte in "
                                    f"{Path(path).name}", code_dir)
    source = code_dir / path
    if source.is_file():
        target = folder / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    git.run(["checkout", "-m", "--", path], code_dir, action="Konflikt zurückholen")
    return folder
