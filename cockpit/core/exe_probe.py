"""Probelauf vor dem Exe-Bau (Wunsch des Nutzers vom 21.10.2026: Exe-Bau robuster machen).

PyInstaller braucht oft Minuten. Zwei häufige Fehler zeigen sich aber schon in Sekunden:
- Eine Python-Datei hat einen Syntaxfehler.
- Eine Bibliothek, die der Code oben in einer Datei importiert, fehlt in der virtuellen Umgebung,
  meist weil sie nicht in requirements.txt steht.

Der Probelauf startet das Python der virtuellen Umgebung mit einem kleinen Prüfprogramm. Es geht
von der Startdatei aus allen eigenen Imports nach, übersetzt jede dieser Dateien (ohne sie
auszuführen) und fragt für jede fremde Bibliothek, ob Python sie findet. Geprüft werden nur
Imports ganz oben in einer Datei, nicht solche in Funktionen oder in try, weil die oft mit Absicht
fehlen dürfen.
"""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from cockpit.core.errors import CockpitError

log = logging.getLogger(__name__)

FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Läuft im Python der virtuellen Umgebung: python -I -X utf8 -c SCRIPT <Code-Ordner> <Startdatei>
SCRIPT = r'''
import ast, importlib.util, json, sys
from pathlib import Path
root, start = Path(sys.argv[1]), sys.argv[2]
seen, todo, syntax, missing, checked = set(), [root / start], [], [], set()

def local(name):
    parts = name.split(".")
    for base in (root, root / "src"):
        target = base.joinpath(*parts)
        for candidate in (target.with_suffix(".py"), target / "__init__.py"):
            if candidate.is_file():
                return candidate
        if (base / parts[0]).is_dir():
            return base / parts[0] / "__init__.py"
    return None

while todo:
    path = todo.pop()
    if path in seen or not path.is_file():
        continue
    seen.add(path)
    try:
        tree = ast.parse(path.read_bytes(), str(path))
    except SyntaxError as exc:
        syntax.append([str(path.relative_to(root)), exc.lineno or 0, exc.msg or ""])
        continue
    names = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            names.append(node.module)
            names += [node.module + "." + a.name for a in node.names if a.name != "*"]
    for name in names:
        found = local(name)
        if found is not None:
            todo.append(found)
            continue
        top = name.split(".")[0]
        if top in checked or name != top and local(top) is not None:
            continue
        checked.add(top)
        try:
            spec = importlib.util.find_spec(top)
        except (ImportError, ValueError):
            spec = None
        if spec is None:
            missing.append([top, str(path.relative_to(root))])
print(json.dumps({"files": len(seen), "syntax": syntax, "missing": missing}))
'''


@dataclass
class ProbeResult:
    files: int = 0
    syntax: list[tuple[str, int, str]] = field(default_factory=list)   # Datei, Zeile, Meldung
    missing: list[tuple[str, str]] = field(default_factory=list)        # Bibliothek, Datei

    @property
    def ok(self) -> bool:
        return not self.syntax and not self.missing

    def lines(self) -> list[str]:
        result = [f"Syntaxfehler in {path} Zeile {line}: {message}"
                  for path, line, message in self.syntax]
        result += [f"Bibliothek {name} fehlt, importiert in {path}" for name, path in self.missing]
        return result


def probe(python: Path, code_dir: Path, start_file: str, cancel=None) -> ProbeResult:
    """Blockiert einige Sekunden. Klappt der Probelauf selbst nicht, ist das kein Fehler des
    Projekts: Dann gibt es ein leeres Ergebnis, und der Bau läuft wie bisher."""
    if not (code_dir / start_file).is_file():
        return ProbeResult()
    try:
        result = subprocess.run([str(python), "-I", "-X", "utf8", "-c", SCRIPT, str(code_dir),
                                 start_file], cwd=str(code_dir), capture_output=True,
                                timeout=120, creationflags=FLAGS, stdin=subprocess.DEVNULL)
        data = json.loads(result.stdout.decode("utf-8", "replace").strip().splitlines()[-1])
    except (OSError, subprocess.TimeoutExpired, ValueError, IndexError) as exc:
        log.warning("Probelauf nicht möglich: %r", exc)
        return ProbeResult()
    return ProbeResult(int(data.get("files", 0)),
                       [tuple(item) for item in data.get("syntax", [])],
                       [tuple(item) for item in data.get("missing", [])])


def problem(result: ProbeResult) -> CockpitError | None:
    """Die Fehlermeldung für den Bau, None wenn alles passt."""
    if result.ok:
        return None
    parts = []
    if result.syntax:
        path, line, message = result.syntax[0]
        parts.append(f"In {path} steht in Zeile {line} ein Fehler im Code: {message}.")
    if result.missing:
        names = sorted({name for name, _ in result.missing})
        parts.append(f"Diese Bibliotheken fehlen in der virtuellen Umgebung: {', '.join(names)}. "
                     "Tragen Sie sie in requirements.txt ein.")
    return CockpitError("Der Probelauf vor dem Bau hat Fehler gefunden. Die Exe wurde nicht "
                        f"gebaut. {' '.join(parts)}", "\n".join(result.lines()))
