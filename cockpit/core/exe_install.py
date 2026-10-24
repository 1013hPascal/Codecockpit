"""Gebaute Exe testen und an ihren Platz bringen, auch für Branches.

Eine neue Exe ersetzt die alte erst nach bestandenem Test. Vorher kommt die alte in eine
Sicherheitskopie.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from cockpit.core import backups, paths
from cockpit.core.errors import Cancelled, CockpitError
from cockpit.core.exe_folders import (
    _into_home, _make_room, _previous, add_exe_dir, beside_names, doc_files, is_doc, place_beside,
    prune_versions)
from cockpit.core.exe_python import _environment, run_process
from cockpit.core.exe_state import (
    BLOCKED, BlockedByWindows, BuildSettings, ExeRecord, LOCKED, PENDING, branch_exe_name, exe_in,
    home_name, is_blocked, is_cockpit, looks_blocked, now, read_settings, running_from,
    write_record)
from cockpit.core.projects import Project

log = logging.getLogger(__name__)


@dataclass
class BuildResult:
    exe: Path                           # die übernommene (oder wartende) Exe
    pending: bool = False               # eigene Exe des Cockpits: wartet auf den Neustart
    backup: Path | None = None
    untested: bool = False              # Test blockiert: noch nicht übernommen, wartet auf Ja
    built: Path | None = None           # bei untested: die gebaute Exe im temporären Ordner
    work: Path | None = None            # bei untested: temporärer Ordner, danach löschen
    commit: str = ""
    branch: str = ""                    # Exe aus einem Branch-Ordner (Phase 10f): sein Name
    placed: list[str] = field(default_factory=list)   # neu neben die Exe gelegte Ordner (10g)
    # bei untested mit keep_failed: Der Test ist nicht bestanden, Meldung und Details dazu
    test_error: str = ""
    test_details: str = ""
    report: list[str] = field(default_factory=list)   # bei untested: Bericht zum Bau


def pyinstaller_build(code_dir: Path, python: Path, spec: Path, work: Path, on_line=None,
                      cancel=None) -> Path:
    """Baut in work. Gibt die Exe-Datei oder den Programmordner zurück."""
    dist = work / "dist"
    code = run_process([str(python), "-m", "PyInstaller", "--noconfirm", "--clean",
                        "--distpath", str(dist), "--workpath", str(work / "build"), str(spec)],
                       code_dir, on_line, cancel, _environment())
    if code:
        raise CockpitError("PyInstaller hat die Exe nicht gebaut. Die Ausgabe nennt den Grund.",
                           f"Rückgabewert {code}")
    built = [p for p in dist.iterdir()] if dist.is_dir() else []
    if not built:
        raise CockpitError("PyInstaller hat keine Exe erzeugt.")
    return built[0]


QUICK_EXIT = ("Die neue Exe hat sich gleich nach dem Start ohne Fenster beendet. Bei einem "
              "Programm mit Fenster ist das ein Fehler, meistens eine falsche Startdatei oder "
              "eine fehlende Bibliothek. „Exe aus dem Code erstellen …“ nennt in der Zusammenfassung "
              "mögliche Gründe. Die "
              "bisherige Exe bleibt.")


def error_window_text(pid: int) -> str:
    """Text eines Fehlerfensters der gestarteten Exe, sonst leer (in Tests ersetzbar)."""
    from cockpit.core import error_windows
    try:
        return error_windows.error_text(pid)
    except (OSError, AttributeError, ValueError):
        return ""


def start_test(exe: Path, seconds: int = 10, self_test: bool = False,
               cancel: threading.Event | None = None, windowed: bool = False) -> str:
    """Start-Test: läuft die Exe nach seconds noch, ist alles gut, dann wird sie beendet. Beendet
    sie sich vorher mit Fehler, ist der Test nicht bestanden. Mit self_test: --selbsttest und
    Rückgabewert 0 innerhalb einer Minute. Gibt einen Satz zum Ergebnis zurück, wirft
    CockpitError, wenn der Test nicht bestanden ist.
    windowed: Programm mit Fenster. Beendet es sich vorher, auch ohne Fehler, ist der Test nicht
    bestanden (Phase 10g: Die VokabelApp startete die Logik statt des Fensters)."""
    from cockpit.core.terminal import _kill_tree
    args = [str(exe), "--selbsttest"] if self_test else [str(exe)]
    try:
        process = subprocess.Popen(args, cwd=str(exe.parent), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        if is_blocked(exc):
            raise BlockedByWindows(BLOCKED + " Die bisherige Exe bleibt.", repr(exc)) from None
        raise CockpitError("Die neue Exe ließ sich nicht starten.", repr(exc)) from None
    limit = 60 if self_test else seconds
    deadline = time.monotonic() + limit
    next_look = time.monotonic() + 1
    try:
        while time.monotonic() < deadline:
            if cancel is not None and cancel.is_set():
                raise Cancelled()
            if time.monotonic() >= next_look:
                # Ein Absturz zeigt bei einer Exe mit Fenster ein Meldungsfenster, das Programm
                # läuft dann weiter. Das zählt nicht als bestanden (Rückmeldung vom 02.10.2026).
                next_look = time.monotonic() + 1
                shown = error_window_text(process.pid)
                if shown and looks_blocked(shown):
                    # Windows-Sicherheit sperrt einen Teil der Exe (Rückmeldung vom 11.10.2026)
                    raise BlockedByWindows(BLOCKED + " Die bisherige Exe bleibt.", shown)
                if shown:
                    raise CockpitError("Die neue Exe zeigt beim Start eine Fehlermeldung. Die "
                                       "bisherige Exe bleibt.", shown)
            code = process.poll()
            if code is not None:
                if code == 0 and windowed and not self_test:
                    raise CockpitError(QUICK_EXIT)
                if code == 0:
                    return "Selbsttest bestanden." if self_test else \
                        "Start-Test bestanden, das Programm hat sich ohne Fehler beendet."
                raise CockpitError(f"Die neue Exe ist beim Test mit Fehler beendet worden "
                                   f"(Rückgabewert {code}). Die bisherige Exe bleibt.")
            time.sleep(0.25)
        if self_test:
            raise CockpitError("Der Selbsttest hat nach einer Minute nicht geantwortet. Die "
                               "bisherige Exe bleibt.")
        return f"Start-Test bestanden, das Programm lief {seconds} Sekunden ohne Absturz."
    finally:
        if process.poll() is None:
            _kill_tree(process)


def install(project: Project, built: Path, commit: str, tested: bool = True) -> BuildResult:
    """Getestete Exe übernehmen. Die eigene laufende Exe des Cockpits wartet in Release\\_neu."""
    exe_dir = add_exe_dir(project)
    names = beside_names(project)
    home = exe_dir / home_name(project)
    if is_cockpit(project) and running_from(exe_dir):
        pending = exe_dir / PENDING
        backups.remove_tree(pending)
        pending.mkdir()
        target = _into_home(built, pending / home.name)
        place_beside(project, [n for n in names if is_doc(n)], pending / home.name, None, None)
        write_record(project.code_dir, ExeRecord("cockpit", now(), commit, pending=True,
                                                 tested=tested))
        return BuildResult(target, pending=True)
    old_home, backup = _make_room(project, home)
    try:
        target = _into_home(built, home)
    except OSError as exc:
        raise CockpitError("Die neue Exe ließ sich nicht in den Ordner Release verschieben. Die "
                           "bisherige steht in den Sicherheitskopien.", str(exc)) from None
    placed = place_beside(project, names, home, _previous(project, backup, old_home), old_home)
    write_record(project.code_dir, ExeRecord("cockpit", now(), commit, tested=tested))
    prune_versions(exe_dir, home.name, project.name)
    return BuildResult(target, backup=backup, placed=placed)


def branch_home(project: Project, folder: str) -> Path | None:
    """Ordner der Exe aus einem Branch, None wenn es sie nicht gibt."""
    if not project.has_exe_dir:
        return None
    home = project.exe_dir / branch_exe_name(home_name(project), folder)
    return home if home.is_dir() and any(home.glob("*.exe")) else None


def promote_branch(project: Project, folder: str, commit: str) -> BuildResult:
    """Nach dem Überführen in main: Die getestete Exe aus dem Branch wird die normale Exe. Die
    bisherige kommt in die Sicherheitskopien. Ordner der Nutzer neben der Exe (zum Beispiel eigene
    Vokabellisten) kommen von der bisherigen Exe, README und Lizenz aus dem Code."""
    source = branch_home(project, folder)
    if source is None:
        raise CockpitError("Die Exe aus dem Branch gibt es nicht mehr. Bitte bauen Sie sie neu.")
    work = Path(tempfile.mkdtemp(prefix="codecockpit-exe-", dir=paths.cache_dir()))
    staged = work / source.name
    try:
        try:
            shutil.move(str(source), str(staged))
        except OSError as exc:
            raise CockpitError(LOCKED, str(exc)) from None
        for name in beside_names(project):
            path = staged / name
            if is_doc(name) or not path.exists():
                continue
            if path.is_dir():
                backups.remove_tree(path)
            else:
                path.unlink()
        return install(project, staged, commit)
    finally:
        backups.remove_tree(work)


def install_untested(project: Project, result: BuildResult,
                     settings: BuildSettings | None = None,
                     source_dir: Path | None = None) -> BuildResult:
    """Nach dem Ja des Nutzers: die nicht geprüfte Exe übernehmen (Wunsch aus Phase 10).
    settings und source_dir bei einer Exe aus einem Branch, wie bei install_branch."""
    try:
        if result.branch:
            return install_branch(project, result.built, result.branch, settings, source_dir)
        return install(project, result.built, result.commit, tested=False)
    finally:
        discard(result)


def install_branch(project: Project, built: Path, folder: str,
                   settings: BuildSettings | None = None,
                   source_dir: Path | None = None) -> BuildResult:
    """Exe aus einem Branch-Ordner neben die normale Exe legen. Die normale bleibt unberührt,
    eine ältere Exe desselben Branches kommt in die Sicherheitskopien. Kein Vermerk in
    cockpit.toml, der gilt nur für die Exe aus dem Haupt-Branch. Die Ordner neben der Exe
    kommen aus dem Branch (source_dir) mit, wie bei der normalen Exe (Rückmeldung des Nutzers
    vom 02.10.2026: Meine-Vokabeln fehlte)."""
    settings = settings or read_settings(project.code_dir) or BuildSettings("main.py",
                                                                           project.name)
    exe_dir = add_exe_dir(project)
    home = exe_dir / branch_exe_name(settings.name or home_name(project), folder)
    backup = None
    if home.exists():
        try:
            backup = backups.move_into_backup(home, project.name, f"Branch-Exe {folder} ersetzt")
        except OSError as exc:
            raise CockpitError(LOCKED, str(exc)) from None
    try:
        target = _into_home(built, home)
    except OSError as exc:
        raise CockpitError("Die neue Exe ließ sich nicht in den Ordner Release verschieben.",
                           str(exc)) from None
    # Die Sicherheitskopie ist der alte Ordner selbst, die Ordner der Nutzer kommen von dort
    names = list(settings.beside)
    names += [n for n in doc_files(source_dir or project.code_dir) if n not in names]
    old_home = Path(".") if backup is not None and backup.is_dir() else None
    placed = place_beside(project, names, home, backup, old_home, source_dir)
    return BuildResult(target, backup=backup, branch=folder, placed=placed)


def stage_beside(built: Path, names: list[str], source_dir: Path) -> list[Path]:
    """Für den Start-Test: die Dateien und Ordner, die neben die Exe kommen, aus dem Ordner
    Repository neben die gebaute Exe kopieren. Gibt die angelegten Pfade zurück.
    Rückmeldung des Nutzers vom 14.10.2026: Der Streckenfinder sucht strecken.csv neben der Exe.
    Die kam aber erst nach dem Test dorthin, also fehlte sie im Test immer."""
    home = exe_in(built).parent
    staged: list[Path] = []
    for name in names:
        source, target = source_dir / name, home / name
        if target.exists() or not source.exists():
            continue
        try:
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
        except OSError:
            continue                          # dann fehlt sie im Test, wie bisher
        staged.append(target)
    return staged


def unstage(staged: list[Path]) -> None:
    """Die Kopien für den Test wieder entfernen. Neben die fertige Exe legt place_beside die
    Ordner, mit den Daten der Nutzer aus der bisherigen Exe."""
    for path in staged:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        except OSError:
            log.warning("Kopie für den Start-Test nicht entfernt: %s", path)


def discard(result: BuildResult) -> None:
    if result.work is not None:
        backups.remove_tree(result.work)
