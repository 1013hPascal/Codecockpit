"""Bericht bei Fehlern beim Exe-Bau (Wunsch des Nutzers vom 14.10.2026).

Beim Zug-um-Zug-Streckenfinder lief PyInstaller ohne Fehler durch, aber im Ordner Release kam
keine Exe an. Warum, stand nirgends. Der Bericht sagt jetzt für jeden Schritt, was geklappt hat,
was die Exe gemeldet hat und was zu tun ist. Er steht in der Ausgabe und geht an die KI.

Aus exe.py herausgelöst am 21.10.2026, nur verschoben. Die Namen sind weiter über exe erreichbar.
Teile aus exe holen die Funktionen erst beim Aufruf, so gibt es keinen Kreis beim Import.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from cockpit.core.projects import Project


@dataclass
class BuildFacts:
    project: Project
    folder: str = ""                    # Branch, sonst leer
    step: int = 0                       # zuletzt begonnener Schritt
    built: Path | None = None           # gebaute Exe im temporären Ordner
    missing: list[str] = field(default_factory=list)
    tested: bool = False
    blocked: bool = False


_MISSING_LINE = re.compile(r"^missing module named '?([\w.]+)'? - imported by (.*)$")


def missing_modules(work: Path, code_dir: Path) -> list[str]:
    """Bibliotheken, die PyInstaller nicht gefunden hat, obwohl der Code des Projekts sie oben in
    einer Datei importiert. Aus der Warnliste build\\<Name>\\warn-<Name>.txt."""
    own = {p.stem for p in code_dir.glob("*.py")}
    found: list[str] = []
    for warn in sorted((work / "build").rglob("warn-*.txt")):
        try:
            text = warn.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for row in text.splitlines():
            match = _MISSING_LINE.match(row.strip())
            if not match:
                continue
            top = match.group(1).split(".")[0]
            for importer in match.group(2).split("),"):
                name = importer.strip().split(" (")[0]
                stem = Path(name).stem if name.endswith(".py") else name.split(".")[0]
                if stem in own and "top-level" in importer and top not in found:
                    found.append(top)
    return found


def first_error(text: str) -> str:
    """Die aussagekräftige Zeile einer Fehlermeldung, etwa "No module named 'PySide6'"."""
    rows = [r.strip() for r in text.splitlines() if r.strip() and r.strip() != "Close"]
    for row in reversed(rows):
        if "unhandled exception:" in row:
            return row.split("unhandled exception:", 1)[1].strip()
        if re.match(r"^\w*(Error|Exception)\b", row):
            return row
    return rows[-1] if rows else ""


# Bibliotheken, die es ab einer Python-Version nicht mehr als fertiges Paket (wheel) gibt, und
# ihr gleichwertiger Ersatz mit demselben Import (Rückmeldung des Nutzers vom 14.10.2026: pygame
# ließ sich unter Python 3.14 nicht installieren, pip wollte es selbst übersetzen und scheiterte).
WHEEL_REPLACEMENTS = {"pygame": ("pygame-ce", (3, 14))}
_FAILED_BUILD = re.compile(r"Failed to build '?([\w.\-]+)'?|Failed building wheel for ([\w.\-]+)"
                           r"|Could not build wheels for ([\w.\-]+)")
_NO_DISTRIBUTION = re.compile(r"No matching distribution found for ([\w.\-]+)")


def python_version(command: list[str] | None = None) -> tuple[int, int] | None:
    """Version des Pythons, mit dem das Cockpit baut, zum Beispiel (3, 14)."""
    from cockpit.core import exe
    command = command or exe.find_python()
    if command is None:
        return None
    try:
        result = subprocess.run([*command, "--version"], capture_output=True, text=True,
                                timeout=20, creationflags=exe.FLAGS)
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"Python (\d+)\.(\d+)", result.stdout + result.stderr)
    return (int(match.group(1)), int(match.group(2))) if match else None


def replacement_for(package: str, version: tuple[int, int] | None) -> str:
    """Gleichwertiger Ersatz für ein Paket ohne fertige Version für dieses Python, sonst leer."""
    found = WHEEL_REPLACEMENTS.get(package.lower())
    if found is None or version is None or version < found[1]:
        return ""
    return found[0]


def failed_package(text: str) -> str:
    """Name des Pakets, das pip selbst übersetzen wollte und nicht konnte."""
    match = _FAILED_BUILD.search(text)
    return next((g for g in match.groups() if g), "") if match else ""


def advice(text: str, facts: BuildFacts | None = None) -> list[str]:
    """Was zu tun ist, aus Fehlermeldung und Ausgabe. Jede Zeile beginnt mit "Was tun:"."""
    from cockpit.core import exe, long_paths
    tips: list[str] = []
    failed = failed_package(text)
    if failed:
        # Ein "No module named" stammt dann aus dem Übersetzen des Pakets, nicht aus dem Code
        # (vorher riet der Bericht bei pygame, distutils in requirements.txt einzutragen)
        replacement = WHEEL_REPLACEMENTS.get(failed.lower(), ("", None))[0]
        if replacement:
            tips.append(f"Was tun: {failed} gibt es für Ihre Python-Version nicht als fertiges "
                        f"Paket. In requirements.txt {failed} durch {replacement} ersetzen, "
                        "das wird genauso importiert. „Exe aus dem Code erstellen“ macht das im "
                        "Branch selbst.")
        else:
            tips.append(f"Was tun: {failed} gibt es für Ihre Python-Version nicht als fertiges "
                        "Paket, und pip konnte es nicht selbst übersetzen. Tragen Sie in "
                        "requirements.txt eine neuere Version ein oder installieren Sie zusätzlich "
                        "eine ältere Python-Version.")
    unknown = _NO_DISTRIBUTION.search(text)
    if unknown:
        tips.append(f"Was tun: Ein Paket {unknown.group(1)} gibt es nicht. Prüfen Sie den Namen "
                    "in requirements.txt. Der Name zum Importieren ist oft ein anderer als der "
                    "des Pakets, zum Beispiel win32com aus dem Paket pywin32.")
    module = None if failed else re.search(r"No module named '([\w.]+)'", text)
    missing = list(facts.missing) if facts else []
    if module and module.group(1).split(".")[0] not in missing:
        missing.insert(0, module.group(1).split(".")[0])
    if missing:
        tips.append(f"Was tun: {', '.join(missing)} in requirements.txt eintragen. Das Cockpit "
                    "installiert in die Bau-Umgebung nur, was dort steht. Bei „Exe aus dem Code "
                    "erstellen“ ergänzt es fehlende Einträge im Branch selbst.")
    if "_internal" in text and re.search(r"nicht gefunden|No such file|FileNotFound|not found",
                                         text, re.IGNORECASE):
        tips.append("Was tun: Der Code sucht eine Datei im Ordner _internal der Exe. Dort liegen "
                    "nur Programmteile, die Datei liegt neben der Exe. Im Code den Ordner über "
                    "sys.executable bestimmen statt über sys._MEIPASS oder __file__. „Problem mit "
                    "KI lösen“ kann das ändern.")
    elif re.search(r"FileNotFoundError|nicht gefunden|No such file", text, re.IGNORECASE):
        tips.append("Was tun: Eine Datei fehlt. Prüfen Sie in Schritt 1, ob sie neben die Exe "
                    "kommt, und ob der Code sie neben der Exe sucht (sys.executable).")
    if long_paths.is_long_path_error(text) or any(
            len(p) > 250 for p in re.findall(r"[A-Za-z]:\\[^'\"\n]+", text)):
        tips.append("Was tun: " + exe.LONG_PATHS)
    if re.search(r"PermissionError|Zugriff verweigert|Access is denied|nicht verschieben",
                 text, re.IGNORECASE):
        tips.append("Was tun: Eine Datei ist gesperrt. Schließen Sie die Exe und Explorer-Fenster "
                    "im Ordner Release und versuchen Sie es noch einmal.")
    if (facts is not None and facts.blocked) or "App-Steuerung" in text:
        tips.append("Was tun: Windows hat die Exe blockiert. Mit „Trotzdem behalten“ kommt sie in "
                    "den Ordner Release. Starten Sie sie dann selbst.")
    if exe.QUICK_EXIT in text:
        tips.append("Was tun: Prüfen Sie die Startdatei in Schritt 1. Sie muss das Fenster öffnen.")
    if not tips:
        tips.append("Was tun: „Problem mit KI lösen“ gibt diesen Bericht an die KI. Oder fragen "
                    "Sie mit „Mit KI chatten“ nach.")
    return tips


def build_report(facts: BuildFacts, message: str, details: str = "",
                 output: list[str] | None = None) -> list[str]:
    """Bericht für die Ausgabe und die KI: jeder Schritt mit Ergebnis, dann was zu tun ist."""
    text = "\n".join([message, details, *(output or [])[-60:]])
    report = ["Bericht zum Bau:"]
    report.append("Schritt 1, Bibliotheken: " + ("vorbereitet." if facts.step > 1 else
                                                 "nicht fertig. " + message))
    if facts.step >= 2:
        report.append(f"Schritt 2, PyInstaller: durchgelaufen, Exe gebaut: {facts.built.name}."
                      if facts.built is not None else
                      "Schritt 2, PyInstaller: nicht durchgelaufen. Die Ausgabe darüber nennt "
                      "den Grund.")
    if facts.missing:
        report.append("PyInstaller hat Bibliotheken nicht gefunden, die der Code importiert: "
                      f"{', '.join(facts.missing)}.")
    if facts.step >= 3:
        if facts.tested:
            report.append("Schritt 3, Start-Test: bestanden.")
        elif facts.blocked:
            report.append("Schritt 3, Start-Test: von Windows blockiert.")
        else:
            shown = first_error(details) or message
            report.append(f"Schritt 3, Start-Test: nicht bestanden. Meldung der Exe: {shown}")
    exe_dir = facts.project.exe_dir
    where = f"Ordner {exe_dir.name}" if exe_dir is not None else "Ordner Release"
    exists = exe_dir is not None and exe_dir.is_dir()
    if facts.step >= 4 and facts.tested:
        report.append(f"Schritt 4, Übernehmen in den {where}: nicht geklappt. {message}")
    else:
        reason = ("Windows den Test blockiert hat" if facts.blocked
                  else "der Test nicht bestanden ist" if facts.step >= 3
                  else "der Bau vorher abgebrochen ist")
        report.append(f"{where}: {'vorhanden' if exists else 'fehlt'}. Neue Exe dort abgelegt: "
                      f"nein, weil {reason}.")
    return report + advice(text, facts)
