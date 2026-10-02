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
# Feste Pfade: Laufwerk wie "C:\..." oder Netzwerkpfad "\\\\server" bzw. r"\\server". Ein Text wie
# "\\" (ein Backslash) ist kein Pfad (Fehlalarm beim Cockpit selbst, Rückmeldung zu 10g).
_ABSOLUTE = re.compile(r'''["'](?:[A-Za-z]:[\\/]|\\\\\\\\\w)|r["']\\\\\w''')
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


def third_party_imports(code_dir: Path, progress=None) -> set[str]:
    """Importierte Module, die weder zur Standardbibliothek noch zum Projekt gehören. progress
    bekommt pro Datei eine Zeile, zum Beispiel "Datei 3 von 12 gelesen: main.py"."""
    local = {p.stem for p in code_dir.glob("*.py")} | {p.name for p in code_dir.iterdir()
                                                       if p.is_dir()}
    found: set[str] = set()
    files = python_files(code_dir)
    for number, path in enumerate(files, start=1):
        if progress is not None:
            progress(f"Datei {number} von {len(files)} gelesen: "
                     f"{path.relative_to(code_dir).as_posix()}")
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


_ENTRY = re.compile(r"^[A-Za-z_][\w.]*\(", re.MULTILINE)       # Aufruf ohne Einrückung
_BAT_PY = re.compile(r"([\w\-. ]+\.py)\b", re.IGNORECASE)
_STRING = re.compile(r"""["']([^"'\\/\n]{2,80})["']""")
_EXE_AWARE = ("sys.executable", "_MEIPASS", "__file__")
GUI_MODULES = ("PySide6", "PySide2", "PyQt5", "PyQt6", "tkinter", "wx", "kivy")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def starts_something(path: Path) -> bool:
    """Startet die Datei etwas, wenn man sie ausführt? Sie hat "__main__" oder einen Aufruf ohne
    Einrückung. Eine Datei nur mit Funktionen und Klassen startet nichts."""
    text = _read(path)
    return "__main__" in text or bool(_ENTRY.search(text))


def guess_start_file(code_dir: Path) -> str:
    """Vorschlag für die Startdatei (Phase 10g): die Datei, die eine .bat-Datei startet, dann eine
    mit "__main__" und Fenster, dann main.py, dann eine mit "__main__"."""
    for bat in sorted(code_dir.glob("*.bat")):
        for name in _BAT_PY.findall(_read(bat)):
            if (code_dir / name.strip()).is_file():
                return name.strip()
    candidates = sorted(p for p in code_dir.glob("*.py") if "__main__" in _read(p))
    for path in candidates:
        if any(module in _read(path) for module in GUI_MODULES):
            return path.name
    if (code_dir / "main.py").is_file():
        return "main.py"
    if candidates:
        return candidates[0].name
    return next((p.name for p in sorted(code_dir.glob("*.py"))), "main.py")


# Zusammenhang, in dem ein Name ein Pfad ist: open("x"), Path("x"), base_dir="x",
# config_path: str = "x". Nicht aber ordner / "x" oder os.path.join(ordner, "x"): Dann steht der
# Name hinter einem anderen Ort, zum Beispiel dem Projekt, das das Programm bearbeitet
# (Fehlalarme beim Cockpit selbst, Rückmeldung zu 10g).
_PATH_CONTEXT = re.compile(
    r"(?:\b(?:open|Path|exists|isdir|isfile|listdir|glob|scandir|join)\(\s*"
    r"|\b\w*(?:dir|path|file|folder|ordner|datei)\w*\s*(?::\s*[\w\[\]| ]+)?=\s*)$",
    re.IGNORECASE)


def _names_in_path_context(text: str, names: set[str]) -> set[str]:
    found: set[str] = set()
    for line in text.splitlines():
        for match in _STRING.finditer(line):
            if match.group(1) not in names:
                continue
            before = line[:match.start()]
            if re.search(r"/\s*$", before) or not _PATH_CONTEXT.search(before):
                continue
            found.add(match.group(1))
    return found


def _packages(code_dir: Path) -> set[str]:
    return {p.name for p in code_dir.iterdir() if p.is_dir() and (p / "__init__.py").is_file()}


def data_folders(code_dir: Path, known: set[str] | None = None) -> list[str]:
    """Ordner im Ordner Code, die der Code als Pfad nutzt, zum Beispiel "Meine-Vokabeln". Sie
    gehören meistens neben die Exe. known: Ordner, die die .spec-Datei schon einbindet."""
    folders = {p.name for p in code_dir.iterdir()
               if p.is_dir() and p.name not in SKIP_DIRS and not p.name.startswith(".")} \
        - _packages(code_dir) - (known or set())
    found: set[str] = set()
    for path in python_files(code_dir):
        found |= _names_in_path_context(_read(path), folders)
    return sorted(found)


def relative_data_paths(code_dir: Path, known: set[str] | None = None) -> list[tuple[str, str]]:
    """(Datei, Name): Der Code öffnet einen Ordner oder eine Datei aus dem Ordner Code nur mit
    Namen und bestimmt den Ort nicht über die Exe. In der Exe sucht er dann im Startordner."""
    names = {p.name for p in code_dir.iterdir()
             if p.name not in SKIP_DIRS and not p.name.startswith(".") and p.suffix != ".py"} \
        - _packages(code_dir) - (known or set())
    found: list[tuple[str, str]] = []
    for path in python_files(code_dir):
        text = _read(path)
        if any(marker in text for marker in _EXE_AWARE):
            continue
        for name in sorted(_names_in_path_context(text, names)):
            found.append((path.relative_to(code_dir).as_posix(), name))
    return found


def spec_known(code_dir: Path, spec: Path | None) -> set[str]:
    """Namen im Ordner Code, die die .spec-Datei schon nennt. Sie stecken in der Exe."""
    text = _read(spec) if spec is not None and spec.is_file() else ""
    return {p.name for p in code_dir.iterdir() if p.name in text} if text else set()


def _spec_of(code_dir: Path, settings: exe.BuildSettings | None) -> Path | None:
    if settings is not None and (code_dir / settings.spec_name).is_file():
        return code_dir / settings.spec_name
    specs = sorted(code_dir.glob("*.spec"))
    return specs[0] if specs else None


def required_beside(code_dir: Path, settings: exe.BuildSettings | None = None) -> list[str]:
    """Was neben die Exe muss, weil der Code es benutzt und die .spec-Datei es nicht schon in
    die Exe packt: Ordner und Dateien, die es im Ordner Code gibt (Wunsch des Nutzers vom
    03.10.2026: in den Exe-Einstellungen angehakt und als "unbedingt nötig" markiert)."""
    known = spec_known(code_dir, _spec_of(code_dir, settings))
    names = data_folders(code_dir, known)
    names += [name for _file, name in relative_data_paths(code_dir, known)
              if (code_dir / name).exists() and name not in names]
    return names


def check(project: Project) -> list[str]:
    """Alle Prüfpunkte. Erste Zeile: Gesamtbewertung."""
    return check_for(project.code_dir, exe.read_settings(project.code_dir),
                     exe.current_exe(project))


def check_for(code_dir: Path, settings: exe.BuildSettings | None,
              current: Path | None = None) -> list[str]:
    """Wie check, mit vorgegebenen Einstellungen (Phase 10g, für die KI). current: die Exe."""
    lines: list[str] = []
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
        if not start.is_file():
            lines.append(f"{PROBLEM}: Die Startdatei {settings.start_file} fehlt.")
        elif not starts_something(start):
            guess = guess_start_file(code_dir)
            hint = f" Wahrscheinlich ist {guess} richtig." if guess != settings.start_file else ""
            lines.append(f"{PROBLEM}: Die Startdatei {settings.start_file} startet nichts. Sie "
                         f"enthält nur Funktionen und Klassen.{hint}")
        else:
            lines.append(f"{OK}: Startdatei {settings.start_file} ist da.")
        for name in settings.beside:
            if not (code_dir / name).exists():
                lines.append(f"{PROBLEM}: Der Ordner {name}, der neben die Exe soll, fehlt im "
                             "Ordner Code.")
        # Was die .spec-Datei schon einbindet, fehlt in der Exe nicht (beim Cockpit: anleitungen)
        known = spec_known(code_dir, spec)
        for name in data_folders(code_dir, known):
            if name not in settings.beside:
                lines.append(f"{WARNING}: Der Code nutzt den Ordner {name}. In der Exe fehlt er. "
                             "Tragen Sie ihn unter „Ordner neben der Exe“ ein.")
        for filename, name in relative_data_paths(code_dir, known):
            lines.append(f"{WARNING}: {filename} sucht {name} im Startordner. Gestartet aus "
                         "einem anderen Ordner, findet die Exe es nicht. Besser den Ort über "
                         "die Exe bestimmen (sys.executable).")
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

    from cockpit.features.exe_build import imports_check
    for path in python_files(code_dir):
        lacking = imports_check.missing(_read(path))
        if lacking:
            lines.append(f"{PROBLEM}: {path.relative_to(code_dir).as_posix()} benutzt etwas, "
                         f"ohne es zu importieren. Es fehlt: {', '.join(lacking)}. Die Exe "
                         "stürzt dann mit NameError ab.")
    from cockpit.core import long_paths
    if not long_paths.enabled():
        lines.append(f"{WARNING}: Lange Pfade sind in Windows ausgeschaltet. Bei Bibliotheken "
                     "mit tief verschachtelten Dateien wie PySide6 kann das Installieren "
                     "scheitern. Das Cockpit bietet dann an, sie einzuschalten.")
    required = requirements(code_dir)
    if not (code_dir / "requirements.txt").is_file():
        lines.append(f"{WARNING}: Es gibt keine requirements.txt.")
    missing = sorted(m for m in third_party_imports(code_dir)
                     if _normalize(PACKAGE_NAMES.get(m.lower(), m)) not in required)
    # Problem, nicht nur Warnung (10g): Das Cockpit installiert in die virtuelle Umgebung nur,
    # was in requirements.txt steht. Was fehlt, fehlt auch in der Exe.
    lines.append(f"{PROBLEM}: Diese Bibliotheken stehen nicht in requirements.txt und fehlen "
                 f"deshalb in der Exe: {', '.join(missing)}." if missing
                 else f"{OK}: Alle importierten Bibliotheken stehen in requirements.txt.")
    loose = sorted(name for name, version in required.items() if not version.startswith("=="))
    lines.append(f"{WARNING}: Ohne feste Version: {', '.join(loose)}. Besser zum Beispiel "
                 "paket==1.2.3." if loose else f"{OK}: Alle Versionen sind fest.")

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
