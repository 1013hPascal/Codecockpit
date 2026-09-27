"""Exe-Einrichtung prüfen (Konzept 10.4). Ergebnis als Zeilen, das Ergebnis jeweils vorne.

Geprüft wird ohne Netz und ohne Bau: .spec-Datei, Startdatei, Symbol, feste Pfade, eingebundene
Dateien, Bibliotheken in requirements.txt, feste Versionen und die Größe der Exe. Probe-Build und
Start-Test laufen bei "Exe aus dem Code erstellen".
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from cockpit.core import exe
from cockpit.core.projects import Project
from cockpit.core.text import count

OK, PROBLEM, WARNING = "In Ordnung", "Problem", "Warnung"
WARN_BYTES = 500 * 1024 * 1024
LIMIT_BYTES = 2 * 1024 * 1024 * 1024

# Import-Name -> Name des Pakets in requirements.txt, wo sie sich unterscheiden
PACKAGE_NAMES = {"pil": "pillow", "cv2": "opencv-python", "sklearn": "scikit-learn",
                 "fitz": "pymupdf", "docx": "python-docx", "dotenv": "python-dotenv",
                 "yaml": "pyyaml", "win32api": "pywin32", "win32con": "pywin32",
                 "bs4": "beautifulsoup4", "tomli_w": "tomli-w", "pytestqt": "pytest-qt",
                 "faster_whisper": "faster-whisper"}
SKIP_DIRS = {".venv", "venv", "env", "build", "dist", "__pycache__", ".git", "tests", "test"}
_ABSOLUTE = re.compile(r"[\"'](?:[A-Za-z]:[\\/]|\\\\)")
_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w., ]+))", re.MULTILINE)
_REQUIREMENT = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*(\[[^\]]*\])?\s*([=<>!~]=?.*)?$")


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def requirements(code_dir: Path) -> dict[str, str]:
    """Paketname (normalisiert) -> Versionsangabe."""
    path = code_dir / "requirements.txt"
    found: dict[str, str] = {}
    if not path.is_file():
        return found
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        match = _REQUIREMENT.match(line)
        if match:
            found[_normalize(match.group(1))] = (match.group(3) or "").strip()
    return found


def python_files(code_dir: Path) -> list[Path]:
    return [p for p in code_dir.rglob("*.py")
            if not SKIP_DIRS & set(p.relative_to(code_dir).parts[:-1])]


def third_party_imports(code_dir: Path) -> set[str]:
    """Importierte Module, die weder zur Standardbibliothek noch zum Projekt gehören."""
    local = {p.stem for p in code_dir.glob("*.py")} | {p.name for p in code_dir.iterdir()
                                                       if p.is_dir()}
    found: set[str] = set()
    for path in python_files(code_dir):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in _IMPORT.finditer(text):
            names = match.group(1) or match.group(2)
            for name in names.split(","):
                top = name.strip().split(" ")[0].split(".")[0]
                if top and not top.startswith("_"):
                    found.add(top)
    stdlib = set(sys.stdlib_module_names)
    return {m for m in found if m not in stdlib and m not in local}


def check(project: Project) -> list[str]:
    """Alle Prüfpunkte. Erste Zeile: Gesamtbewertung."""
    code_dir = project.code_dir
    lines: list[str] = []
    settings = exe.read_settings(code_dir)
    spec = code_dir / settings.spec_name if settings else None
    if settings is None or not spec.is_file():
        specs = sorted(code_dir.glob("*.spec"))
        if specs:
            spec = specs[0]
            lines.append(f"{WARNING}: Die Datei {spec.name} ist da, aber das Cockpit kennt die "
                         "Einstellungen noch nicht. Beim nächsten Bau übernimmt es sie.")
        else:
            lines.append(f"{PROBLEM}: Es gibt noch keine .spec-Datei. Sie entsteht beim ersten "
                         "„Exe aus dem Code erstellen“.")
            spec = None
    else:
        lines.append(f"{OK}: {spec.name} ist da.")
    if settings is not None:
        start = code_dir / settings.start_file
        lines.append(f"{OK}: Startdatei {settings.start_file} ist da." if start.is_file()
                     else f"{PROBLEM}: Die Startdatei {settings.start_file} fehlt.")
        if settings.icon:
            lines.append(f"{OK}: Symbol {settings.icon} ist da." if (code_dir / settings.icon)
                         .is_file() else f"{PROBLEM}: Das Symbol {settings.icon} fehlt.")
        for source, _target in settings.datas:
            path = (code_dir / source).resolve()
            if not path.exists():
                lines.append(f"{PROBLEM}: Die eingebundene Datei {source} fehlt.")
            elif not path.is_relative_to(code_dir.resolve()):
                lines.append(f"{PROBLEM}: {source} liegt außerhalb des Ordners Code.")
    if spec is not None:
        text = spec.read_text(encoding="utf-8", errors="replace")
        lines.append(f"{PROBLEM}: {spec.name} enthält feste Pfade wie C:\\. Bitte Pfade relativ "
                     "zum Ordner Code angeben." if _ABSOLUTE.search(text)
                     else f"{OK}: Keine festen Pfade in {spec.name}.")

    required = requirements(code_dir)
    if not (code_dir / "requirements.txt").is_file():
        lines.append(f"{WARNING}: Es gibt keine requirements.txt.")
    missing = sorted(m for m in third_party_imports(code_dir)
                     if _normalize(PACKAGE_NAMES.get(m.lower(), m)) not in required)
    lines.append(f"{WARNING}: Diese Bibliotheken stehen nicht in requirements.txt: "
                 f"{', '.join(missing)}." if missing
                 else f"{OK}: Alle importierten Bibliotheken stehen in requirements.txt.")
    loose = sorted(name for name, version in required.items() if not version.startswith("=="))
    lines.append(f"{WARNING}: Ohne feste Version: {', '.join(loose)}. Besser zum Beispiel "
                 "paket==1.2.3." if loose else f"{OK}: Alle Versionen sind fest.")

    current = exe.current_exe(project)
    if current is not None:
        size = current.stat().st_size
        megabytes = round(size / (1024 * 1024))
        if size > LIMIT_BYTES:
            lines.append(f"{PROBLEM}: Die Exe ist {megabytes} MB groß. GitHub nimmt einzelne "
                         "Dateien nur bis 2 GB an. Wählen Sie die Bauart Programmordner.")
        elif size > WARN_BYTES:
            lines.append(f"{WARNING}: Die Exe ist {megabytes} MB groß und startet langsam. Die "
                         "Bauart Programmordner startet schneller.")
        else:
            lines.append(f"{OK}: Größe der Exe {megabytes} MB.")
    lines.append("Hinweis: Probe-Build und Start-Test laufen bei „Exe aus dem Code erstellen“.")
    problems = len([line for line in lines if line.startswith(PROBLEM)])
    warnings = len([line for line in lines if line.startswith(WARNING)])
    if problems:
        summary = (f"Nicht bereit: {count(problems, 'Problem', 'Probleme')}, "
                   f"{count(warnings, 'Warnung', 'Warnungen')}.")
    elif warnings:
        summary = f"Bereit, mit {count(warnings, 'Warnung', 'Warnungen')}."
    else:
        summary = "Bereit: Die Exe lässt sich ohne Handarbeit bauen."
    return [summary] + lines
