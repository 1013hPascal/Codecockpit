"""Neuere Bibliotheken und Modelle in Projekten einsetzen (Stufe 3 der Paketübersicht).

Wunsch des Nutzers vom 21.10.2026: Programme im Cockpit sollen veraltete Bibliotheken und Modelle
durch neuere ersetzen können. Damit nichts kaputtgeht, passiert das nie in main:
- Bibliotheken: Im Branch Cockpit-pakete-aktualisieren ändert das Cockpit requirements.txt,
  installiert neu und lässt die Tests des Projekts laufen, wenn es welche gibt.
- Modelle: Im Branch Cockpit-modell-tauschen ersetzt es den Namen des Modells an den Stellen, die
  der Nutzer vorher gesehen und gewählt hat.
Main bleibt, wie es ist. Überführen oder verwerfen macht der Nutzer wie bei jedem Branch. Der
Branch ist zugleich die Sicherheitskopie: In main steht der alte Stand.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path

from cockpit.core import exe
from cockpit.core.errors import CockpitError
from cockpit.features.packages import runner, usage
from cockpit.features.packages.base import Package, version_key

log = logging.getLogger(__name__)

LIBRARY_BRANCH = "Cockpit-pakete-aktualisieren"
MODEL_BRANCH = "Cockpit-modell-tauschen"
_PINNED = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*==\s*([^\s;#]+)")


@dataclass
class LibraryChange:
    project: object                     # Project
    name: str
    old: str
    new: str

    def line(self) -> str:
        return f"{self.project.name}: {self.name} {self.old} zu {self.new}"


@dataclass
class Place:
    project: object
    path: str                           # relativ zum Code-Ordner
    number: int
    text: str

    def line(self) -> str:
        return f"{self.project.name}: {self.path} Zeile {self.number}: {self.text.strip()[:120]}"


# -- Bibliotheken ---------------------------------------------------------------------------------
def pinned(requirements: Path) -> dict[str, str]:
    """Name -> Version für Einträge mit ==."""
    try:
        lines = requirements.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    found = {}
    for line in lines:
        match = _PINNED.match(line)
        if match:
            found[usage.normalize(match.group(1))] = match.group(3)
    return found


def outdated_in_projects(projects, latest: dict[str, str]) -> list[LibraryChange]:
    """latest: normalisierter Name -> neueste Version, zum Beispiel aus den geprüften Paketen."""
    found = []
    for project in projects:
        for name, version in pinned(project.code_dir / "requirements.txt").items():
            new = latest.get(name, "")
            if new and version_key(new) > version_key(version):
                found.append(LibraryChange(project, name, version, new))
    return found


def latest_versions(packages: list[Package]) -> dict[str, str]:
    """Neueste bekannte Version je Bibliothek aus den gelesenen pip-Paketen."""
    found: dict[str, str] = {}
    for package in packages:
        if not package.checked:
            continue
        newest = package.latest or package.version
        name = usage.normalize(package.name)
        if name not in found or version_key(newest) > version_key(found[name]):
            found[name] = newest
    return found


def rewrite_requirements(path: Path, changes: dict[str, str]) -> list[str]:
    """Versionen in requirements.txt ersetzen, Rest der Zeile bleibt. Gibt die Namen zurück."""
    raw = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    done, lines = [], []
    for line in raw.replace("\r\n", "\n").split("\n"):
        match = _PINNED.match(line)
        if match and usage.normalize(match.group(1)) in changes:
            new = changes[usage.normalize(match.group(1))]
            line = line[:match.start(3)] + new + line[match.end(3):]
            done.append(match.group(1))
        lines.append(line)
    path.write_bytes(newline.join(lines).encode("utf-8"))
    return done


def _python_for(folder: Path) -> Path | None:
    python = exe.venv_python(folder)
    return python if python.is_file() else None


def has_tests(folder: Path) -> bool:
    return (folder / "tests").is_dir() or any(folder.glob("test_*.py"))


def update_libraries(project, changes: list[LibraryChange], cancel=None, on_line=None
                     ) -> list[str]:
    """Im eigenen Branch: requirements.txt ändern, Commit, installieren, Tests. Gibt den Bericht
    zurück, eine Zeile pro Schritt."""
    from cockpit.features.exe_build import exe_branch
    folder = exe_branch.prepare(project, LIBRARY_BRANCH)
    wanted = {usage.normalize(c.name): c.new for c in changes}
    done = rewrite_requirements(folder / "requirements.txt", wanted)
    report = [f"Branch {LIBRARY_BRANCH}: requirements.txt geändert für {', '.join(done)}."]
    summary = ", ".join(f"{c.name} {c.old} zu {c.new}" for c in changes)
    if exe_branch.commit(folder, ["requirements.txt"], f"Bibliotheken aktualisiert: {summary}"):
        report.append("Commit angelegt. Main ist unverändert.")
    python = _python_for(folder)
    if python is None:
        report.append("Das Projekt hat in diesem Ordner keine virtuelle Umgebung. Installiert "
                      "und getestet wurde deshalb nichts.")
        return report
    result = runner.run([str(python), "-I", "-m", "pip", "install", "-r", "requirements.txt",
                         "--disable-pip-version-check"], cancel, on_line, cwd=folder)
    if not result.ok:
        report.append("Installieren hat nicht geklappt. Die letzten Zeilen:")
        report += result.lines[-8:]
        return report
    report.append("Neu installiert.")
    if not has_tests(folder):
        report.append("Das Projekt hat keine Tests. Bitte starten Sie es selbst und prüfen Sie "
                      "es.")
        return report
    tests = runner.run([str(python), "-m", "pytest", "-q", "-p", "no:cacheprovider"], cancel,
                       on_line, cwd=folder)
    last = next((line for line in reversed(tests.lines) if line.strip()), "")
    report.append(("Tests bestanden: " if tests.ok else "Tests nicht bestanden: ") + last)
    return report


# -- Modelle --------------------------------------------------------------------------------------
def find_places(projects, names: list[str]) -> list[Place]:
    """Stellen im Code, an denen einer der Namen steht."""
    from cockpit.features.ai_assistant.context import confidential
    found = []
    wanted = [n.lower() for n in names if n]
    for project in projects:
        root = project.code_dir
        for folder, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in usage.SKIP_DIRS and not d.startswith(".")]
            for name in files:
                path = Path(folder) / name
                relative = path.relative_to(root).as_posix()
                if path.suffix.lower() not in usage.TEXT_SUFFIXES or confidential(relative):
                    continue
                try:
                    if path.stat().st_size > usage.MAX_FILE_BYTES:
                        continue
                    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
                except OSError:
                    continue
                for number, line in enumerate(lines, start=1):
                    lower = line.lower()
                    if any(usage._contains(lower, w) for w in wanted):
                        found.append(Place(project, relative, number, line))
    return found


def replace_model(project, places: list[Place], old_names: list[str], new: str) -> list[str]:
    """Im eigenen Branch die gewählten Stellen ändern und committen. Gibt den Bericht zurück."""
    from cockpit.features.exe_build import exe_branch
    folder = exe_branch.prepare(project, MODEL_BRANCH)
    by_file: dict[str, set[int]] = {}
    for place in places:
        by_file.setdefault(place.path, set()).add(place.number)
    pattern = re.compile("|".join(re.escape(n) for n in sorted(old_names, key=len, reverse=True)),
                         re.IGNORECASE)
    changed = []
    for relative, numbers in by_file.items():
        path = folder / relative
        try:
            raw = path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise CockpitError(f"{relative} ließ sich nicht lesen.", repr(exc)) from None
        newline = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.replace("\r\n", "\n").split("\n")
        for number in numbers:
            if 0 < number <= len(lines):
                lines[number - 1] = pattern.sub(new, lines[number - 1], count=1)
        path.write_bytes(newline.join(lines).encode("utf-8"))
        changed.append(relative)
    report = [f"Branch {MODEL_BRANCH}: {len(places)} Stellen in {len(changed)} Dateien geändert."]
    if exe_branch.commit(folder, changed, f"Modell getauscht: {old_names[0]} zu {new}"):
        report.append("Commit angelegt. Main ist unverändert. Bitte starten Sie das Projekt "
                      "aus dem Branch und prüfen Sie es, bevor Sie ihn in main überführen.")
    return report


def successor_prompt(package: Package) -> str:
    from cockpit.ai import prompt_files
    return prompt_files.fill(prompt_files.load("packages_successor"), modell=package.name,
                             ort=package.place)


def parse_successors(answer: str) -> list[str]:
    """Eine Zeile pro Vorschlag: "Name: Grund". Höchstens fünf."""
    found = []
    for line in answer.splitlines():
        line = line.strip().lstrip("-*•").strip()
        line = re.sub(r"^\d+[.)]\s*", "", line)
        if line.lower().startswith("kein vorschlag"):
            continue
        if ":" in line and len(line) < 300:
            found.append(line.replace("**", "").replace("`", ""))
    return found[:5]
