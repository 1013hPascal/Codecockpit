"""Bericht zum Bau und fehlende Bibliotheken (Rückmeldung des Nutzers vom 14.10.2026).

Beim Zug-um-Zug-Streckenfinder fehlte requirements.txt. PyInstaller baute ohne PySide6 und
networkx, die Exe stürzte beim Start ab, und im Ordner Release kam nichts an. Warum, stand nirgends.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cockpit.core import exe
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.features.exe_build import setup_check

GUI = "from PySide6.QtWidgets import QApplication\nfrom engine import load\n"
ENGINE = "import csv\nimport networkx as nx\nfrom PIL import Image\n"
WARN = """
missing module named 'collections.abc' - imported by typing (top-level), logging (top-level)
missing module named resource - imported by posix (top-level)
missing module named networkx - imported by engine (top-level)
missing module named 'PySide6.QtWidgets' - imported by C:\\x\\code\\gui.py (top-level)
missing module named PySide6 - imported by C:\\x\\code\\gui.py (top-level)
missing module named yaml - imported by engine (delayed, optional)
"""
CRASH = ("Unhandled exception in script\nFailed to execute script 'gui' due to unhandled "
         "exception: No module named 'PySide6'\nClose")


def code(tmp_path) -> Path:
    folder = tmp_path / "code"
    folder.mkdir()
    (folder / "gui.py").write_text(GUI, encoding="utf-8")
    (folder / "engine.py").write_text(ENGINE, encoding="utf-8")
    return folder


def project(tmp_path) -> Project:
    (tmp_path / "Release").mkdir(exist_ok=True)
    return Project(1, "Strecken", tmp_path, tmp_path / "code", tmp_path / "Release")


# -- requirements.txt ergänzen -------------------------------------------------------------------
def test_complete_requirements_creates_the_file(tmp_path):
    folder = code(tmp_path)
    assert setup_check.missing_requirements(folder) == ["networkx", "pillow", "PySide6"]
    assert setup_check.complete_requirements(folder) == ["networkx", "pillow", "PySide6"]
    assert (folder / "requirements.txt").read_text(encoding="utf-8") == \
        "networkx\npillow\nPySide6\n"
    assert setup_check.complete_requirements(folder) == []          # nichts mehr zu tun


def test_complete_requirements_keeps_what_is_there(tmp_path):
    folder = code(tmp_path)
    (folder / "requirements.txt").write_text("PySide6==6.12.0", encoding="utf-8")
    assert setup_check.complete_requirements(folder) == ["networkx", "pillow"]
    assert (folder / "requirements.txt").read_text(encoding="utf-8") == \
        "PySide6==6.12.0\nnetworkx\npillow\n"


def test_meipass_for_a_file_beside_the_exe_is_a_problem(tmp_path):
    folder = code(tmp_path)
    (folder / "strecken.csv").write_text("a,b\n", encoding="utf-8")
    (folder / "engine.py").write_text(
        "import sys\nbase = getattr(sys, '_MEIPASS', '.')\nNAME = 'strecken.csv'\n",
        encoding="utf-8")
    settings = exe.BuildSettings("gui.py", "Strecken", beside=["strecken.csv"])
    lines = setup_check.check_for(folder, settings)
    assert any("sucht strecken.csv über sys._MEIPASS" in line for line in lines)


# -- Warnliste von PyInstaller -------------------------------------------------------------------
def test_missing_modules_only_from_own_top_level_imports(tmp_path):
    folder = code(tmp_path)
    warn = tmp_path / "work" / "build" / "Strecken" / "warn-Strecken.txt"
    warn.parent.mkdir(parents=True)
    warn.write_text(WARN, encoding="utf-8")
    assert exe.missing_modules(tmp_path / "work", folder) == ["networkx", "PySide6"]
    assert exe.missing_modules(tmp_path / "leer", folder) == []


# -- Bericht und Ratschläge ----------------------------------------------------------------------
def test_report_after_a_failed_start_test(tmp_path):
    facts = exe.BuildFacts(project(tmp_path), step=3, built=tmp_path / "Strecken.exe",
                           missing=["networkx"])
    report = exe.build_report(facts, "Die neue Exe zeigt beim Start eine Fehlermeldung.", CRASH)
    assert report[0] == "Bericht zum Bau:"
    assert "Schritt 1, Bibliotheken: vorbereitet." in report
    assert "Schritt 2, PyInstaller: durchgelaufen, Exe gebaut: Strecken.exe." in report
    assert "Schritt 3, Start-Test: nicht bestanden. Meldung der Exe: No module named " \
           "'PySide6'" in report
    assert "Ordner Release: vorhanden. Neue Exe dort abgelegt: nein, weil der Test nicht " \
           "bestanden ist." in report
    tips = [line for line in report if line.startswith("Was tun:")]
    assert tips[0].startswith("Was tun: PySide6, networkx in requirements.txt eintragen.")


def test_report_when_pyinstaller_failed(tmp_path):
    facts = exe.BuildFacts(project(tmp_path), step=2)
    report = exe.build_report(facts, "PyInstaller hat die Exe nicht gebaut.", "Rückgabewert 1")
    assert any(line.startswith("Schritt 2, PyInstaller: nicht durchgelaufen.") for line in report)
    assert any("weil der Bau vorher abgebrochen ist" in line for line in report)
    assert report[-1].startswith("Was tun: „Problem mit KI lösen“")


@pytest.mark.parametrize("text, expected", [
    ("Failed to execute script 'gui' due to unhandled exception: CSV-Datei nicht gefunden: "
     "C:\\Release\\Strecken\\_internal\\strecken.csv", "im Ordner _internal"),
    ("FileNotFoundError: [Errno 2] No such file or directory: 'daten.csv'", "Eine Datei fehlt"),
    ("FileNotFoundError: [Errno 2] No such file or directory: 'C:\\" + "x" * 260 + "'",
     "lange Pfade"),
    ("PermissionError: [WinError 5] Zugriff verweigert", "Eine Datei ist gesperrt"),
])
def test_advice(text, expected):
    assert any(expected in tip for tip in exe.advice(text))


# -- Der Bau hängt den Bericht an -----------------------------------------------------------------
def test_build_puts_the_report_into_the_result_and_the_error(tmp_path, monkeypatch):
    proj = project(tmp_path)
    folder = code(tmp_path)
    monkeypatch.setattr(exe.paths, "cache_dir", lambda: tmp_path / "cache")
    (tmp_path / "cache").mkdir()
    monkeypatch.setattr(exe, "head_commit", lambda code_dir: "abc")
    monkeypatch.setattr(exe, "prepare_venv", lambda code_dir, on_line, cancel, venv=None: "py")

    def fake_build(code_dir, python, spec, work, on_line, cancel):
        warn = work / "build" / "Strecken" / "warn-Strecken.txt"
        warn.parent.mkdir(parents=True)
        warn.write_text(WARN, encoding="utf-8")
        target = work / "dist" / "Strecken"
        target.mkdir(parents=True)
        (target / "Strecken.exe").write_text("neu", encoding="utf-8")
        return target

    monkeypatch.setattr(exe, "pyinstaller_build", fake_build)
    monkeypatch.setattr(exe, "start_test", lambda *a, **kw: (_ for _ in ()).throw(
        CockpitError("Die neue Exe zeigt beim Start eine Fehlermeldung.", CRASH)))
    lines = []
    settings = exe.BuildSettings("gui.py", "Strecken")
    result = exe.build(proj, settings, lambda s: None, lines.append, keep_failed=True)
    assert any(line.startswith("Achtung: PyInstaller hat diese Bibliotheken nicht gefunden")
               for line in lines)
    assert result.report[0] == "Bericht zum Bau:"
    assert any("Meldung der Exe: No module named 'PySide6'" in line for line in result.report)
    exe.discard(result)
    with pytest.raises(CockpitError) as raised:
        exe.build(proj, settings, lambda s: None, lambda s: None)
    assert CRASH in raised.value.details and "Bericht zum Bau:" in raised.value.details
