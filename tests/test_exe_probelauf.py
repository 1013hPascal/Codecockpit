"""Probelauf vor dem Exe-Bau (Wunsch des Nutzers vom 21.10.2026). Läuft mit dem Python der
Tests, ohne PyInstaller."""
from __future__ import annotations

import sys
from pathlib import Path

from cockpit.core import exe_probe

PYTHON = Path(sys.executable)


def write(folder: Path, name: str, text: str) -> None:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def test_clean_project_passes(tmp_path):
    write(tmp_path, "main.py", "import os\nimport helfer\nfrom paket import teil\n")
    write(tmp_path, "helfer.py", "import json\n")
    write(tmp_path, "paket/__init__.py", "")
    write(tmp_path, "paket/teil.py", "from pathlib import Path\n")
    result = exe_probe.probe(PYTHON, tmp_path, "main.py")
    assert result.ok and result.files == 4
    assert exe_probe.problem(result) is None


def test_missing_library_and_syntax_error(tmp_path):
    write(tmp_path, "main.py", "import helfer\nimport gibt_es_nicht_xyz\n")
    write(tmp_path, "helfer.py", "def kaputt(:\n    pass\n")
    write(tmp_path, "tests/test_a.py", "import pytest_nicht_da\n")    # nicht erreichbar
    result = exe_probe.probe(PYTHON, tmp_path, "main.py")
    assert result.missing == [("gibt_es_nicht_xyz", "main.py")]
    assert [s[:2] for s in result.syntax] == [("helfer.py", 1)]
    error = exe_probe.problem(result)
    assert "gibt_es_nicht_xyz" in error.message and "helfer.py" in error.message
    assert "requirements.txt" in error.message


def test_imports_in_functions_and_try_are_ignored(tmp_path):
    write(tmp_path, "main.py", "try:\n    import fehlt_a\nexcept ImportError:\n    pass\n"
                               "def f():\n    import fehlt_b\n")
    assert exe_probe.probe(PYTHON, tmp_path, "main.py").ok


def test_probe_problem_is_no_error(tmp_path):
    write(tmp_path, "main.py", "import os\n")
    assert exe_probe.probe(tmp_path / "kein-python.exe", tmp_path, "main.py").ok
    assert exe_probe.probe(PYTHON, tmp_path, "fehlt.py").ok
