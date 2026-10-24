"""Auswählen, was in den Commit kommt (Wunsch des Nutzers vom 21.10.2026).

Vorher nahm das Hochladen immer alle Dateien (git add -A). Jetzt kann man Dateien abhaken und bei
geänderten Dateien einzelne Abschnitte wählen. Ein Abschnitt ist ein Block zusammenhängender
Änderungen, wie ihn git diff zeigt ("Zeile 12 bis 18, 3 neu, 1 entfernt"). Einzelne Zeilen gibt
es mit Absicht nicht: Mit Screenreader wäre das zu viel Pfeilarbeit (Antwort des Nutzers).

Was nicht gewählt ist, bleibt unverändert in den Dateien und kann später in einen eigenen Commit.

Ablauf beim Commit (stage): Erst wird alles aus dem Index genommen (git reset), dann kommen
ganze Dateien mit git add, gewählte Abschnitte mit git apply --cached. Die Dateien auf der
Festplatte ändern sich dabei nie.
"""
from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from cockpit.core import git
from cockpit.core.text import count

MAX_NEW_LINES = 400                  # so viele Zeilen einer neuen Datei werden angezeigt
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

# Pfad -> None: die ganze Datei, sonst die Nummern der gewählten Abschnitte
Selection = dict[str, "set[int] | None"]


@dataclass
class Hunk:
    number: int                      # ab 0, in der Reihenfolge von git diff
    header: str                      # "@@ -10,4 +10,6 @@ def suche():"
    lines: list[str] = field(default_factory=list)   # mit +, - oder Leerzeichen vorne
    start: int = 0                   # erste Zeile in der neuen Fassung

    @property
    def added(self) -> int:
        return sum(1 for line in self.lines if line.startswith("+"))

    @property
    def removed(self) -> int:
        return sum(1 for line in self.lines if line.startswith("-"))

    @property
    def label(self) -> str:
        """Für die Liste, das Wichtigste vorne: "Zeile 12 bis 18, 3 neu, 1 entfernt"."""
        length = sum(1 for line in self.lines if not line.startswith("-"))
        end = self.start + max(length, 1) - 1
        where = f"Zeile {self.start}" if end <= self.start else f"Zeile {self.start} bis {end}"
        parts = [where]
        if self.added:
            parts.append(f"{self.added} neu")
        if self.removed:
            parts.append(f"{self.removed} entfernt")
        context = self.header.split("@@", 2)[-1].strip() if self.header.count("@@") >= 2 else ""
        if context:
            parts.append(f"in {context}")
        return ", ".join(parts)

    def readable(self) -> list[str]:
        """Zum Vorlesen: jede Zeile mit einem Wort vorne statt + und -."""
        result = []
        for line in self.lines:
            text = line[1:].rstrip("\r") or "(leere Zeile)"
            if line.startswith("+"):
                result.append(f"Neu: {text}")
            elif line.startswith("-"):
                result.append(f"Entfernt: {text}")
            elif not line.startswith("\\"):
                result.append(f"Gleich: {text}")
        return result


@dataclass
class FileDiff:
    path: str
    kind: str                        # "geändert", "neu", "gelöscht", "umbenannt"
    head: list[str] = field(default_factory=list)    # Kopf des Patches bis vor dem ersten @@
    hunks: list[Hunk] = field(default_factory=list)
    binary: bool = False
    text: list[str] = field(default_factory=list)    # Inhalt einer neuen Datei zum Lesen

    @property
    def partial_possible(self) -> bool:
        """Nur geänderte Textdateien mit mehr als einem Abschnitt lassen sich aufteilen."""
        return self.kind == "geändert" and not self.binary and len(self.hunks) > 1

    def summary(self) -> str:
        if self.binary:
            return "keine Textdatei, nur ganz wählbar"
        if self.kind == "neu":
            return count(len(self.text), "Zeile", "Zeilen")
        if self.kind == "gelöscht":
            return "wird gelöscht"
        return count(len(self.hunks), "Abschnitt", "Abschnitte")


def parse(diff: str) -> tuple[list[str], list[Hunk], bool]:
    """Ausgabe von git diff für eine Datei: Kopf, Abschnitte, Binärdatei?"""
    head: list[str] = []
    hunks: list[Hunk] = []
    binary = False
    # split statt splitlines: Bei Windows-Zeilenenden muss das \r im Patch bleiben, sonst passt
    # er nicht mehr auf die Datei
    rows = diff.split("\n")
    if rows and rows[-1] == "":
        rows.pop()
    for line in rows:
        match = _HUNK.match(line)
        if match:
            hunks.append(Hunk(len(hunks), line, start=int(match.group(3))))
        elif hunks:
            hunks[-1].lines.append(line)
        else:
            head.append(line)
            if line.startswith("Binary files ") or line.startswith("GIT binary patch"):
                binary = True
    return head, hunks, binary


def file_diff(code_dir: Path, path: str, kind: str) -> FileDiff:
    """Was sich an einer Datei gegenüber dem letzten Commit geändert hat."""
    found = FileDiff(path, kind)
    if kind == "neu":
        file = code_dir / path
        try:
            data = file.read_bytes()
        except OSError:
            return found
        if b"\0" in data[:8000]:
            found.binary = True
            return found
        lines = data.decode("utf-8", errors="replace").splitlines()
        found.text = lines[:MAX_NEW_LINES] + ([f"… und {len(lines) - MAX_NEW_LINES} weitere "
                                                f"Zeilen"] if len(lines) > MAX_NEW_LINES else [])
        return found
    if kind == "gelöscht":
        return found
    result = git.run(["diff", "--no-color", "--no-ext-diff", "-U3", "HEAD", "--", path],
                     code_dir, check=False)
    found.head, found.hunks, found.binary = parse(result.stdout)
    return found


def patch_for(diff: FileDiff, numbers: set[int]) -> str:
    """Patch mit nur den gewählten Abschnitten, für git apply --cached."""
    lines = list(diff.head)
    for hunk in diff.hunks:
        if hunk.number in numbers:
            lines.append(hunk.header)
            lines.extend(hunk.lines)
    return "\n".join(lines) + "\n"


def stage(code_dir: Path, selection: Selection, kinds: dict[str, str],
          origins: dict[str, str] | None = None) -> None:
    """Genau das Gewählte in den Index bringen. kinds: Pfad -> Art der Änderung. origins: bei
    umbenannten Dateien der alte Name, er kommt mit, sonst bliebe die alte Datei bestehen."""
    if git.run(["rev-parse", "-q", "--verify", "HEAD"], code_dir, check=False).returncode == 0:
        git.run(["reset", "-q"], code_dir, action="Auswahl vorbereiten")
    whole = [path for path, numbers in selection.items() if numbers is None]
    whole += [origins[path] for path in list(whole) if origins and path in origins]
    for start in range(0, len(whole), 100):
        git.run(["add", "-A", "--", *whole[start:start + 100]], code_dir,
                action="Dateien vormerken")
    for path, numbers in selection.items():
        if numbers is None or not numbers:
            continue
        diff = file_diff(code_dir, path, kinds.get(path, "geändert"))
        if {h.number for h in diff.hunks} <= numbers:
            git.run(["add", "--", path], code_dir, action="Dateien vormerken")
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False,
                                         encoding="utf-8", newline="\n") as file:
            file.write(patch_for(diff, numbers))
            patch = Path(file.name)
        try:
            git.run(["apply", "--cached", "--recount", "--whitespace=nowarn", str(patch)],
                    code_dir, action="Abschnitte vormerken")
        finally:
            patch.unlink(missing_ok=True)
