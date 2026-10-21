"""Python für den Bau wählen und Bibliotheken vorher prüfen (Wunsch des Nutzers vom 20.10.2026).

Beim Waagenzähler scheiterte pip erst nach Minuten, weil es pygame für Python 3.14 nicht fertig
gab. Jetzt prüft das Cockpit das vorher in Sekunden und nimmt ein älteres Python, wenn das hilft.
"""
from __future__ import annotations

import subprocess

import pytest

from cockpit.core import exe
from cockpit.core.errors import CockpitError

PY314 = exe.PythonInstall((3, 14), [r"C:\Python314\python.exe"])
PY313 = exe.PythonInstall((3, 13), [r"C:\Python313\python.exe"])


def code(tmp_path, text="pygame\nPySide6\n"):
    folder = tmp_path / "code"
    folder.mkdir(parents=True)
    (folder / "requirements.txt").write_text(text, encoding="utf-8")
    return folder


def checks(monkeypatch, results):
    monkeypatch.setattr(exe, "wheel_check",
                        lambda python, code_dir, cancel=None: results[python.label])


def test_newest_python_when_everything_is_there(tmp_path, monkeypatch):
    monkeypatch.setattr(exe, "find_pythons", lambda: [PY314, PY313])
    checks(monkeypatch, {"3.14": [], "3.13": []})
    lines = []
    assert exe.choose_python(code(tmp_path), "", lines.append) is PY314
    assert lines[-1] == "Alle Bibliotheken gibt es fertig für Python 3.14."


def test_older_python_when_a_wheel_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(exe, "find_pythons", lambda: [PY314, PY313])
    checks(monkeypatch, {"3.14": ["pygame"], "3.13": []})
    lines = []
    assert exe.choose_python(code(tmp_path), "", lines.append) is PY313
    assert lines[-1] == ("Python 3.13 wird benutzt, weil es für Python 3.14 diese Bibliotheken "
                         "nicht fertig gibt: pygame.")


def test_only_one_python_says_what_to_do(tmp_path, monkeypatch):
    monkeypatch.setattr(exe, "find_pythons", lambda: [PY314])
    checks(monkeypatch, {"3.14": ["pygame"]})
    lines = []
    assert exe.choose_python(code(tmp_path), "", lines.append) is PY314
    assert lines[-1].startswith("Achtung: Für Python 3.14 gibt es diese Bibliotheken nicht "
                                "fertig: pygame.")
    assert lines[-1].endswith("Abhilfe: in requirements.txt pygame durch pygame-ce ersetzen.")


def test_chosen_python_wins(tmp_path, monkeypatch):
    monkeypatch.setattr(exe, "find_pythons", lambda: [PY314, PY313])
    checks(monkeypatch, {"3.14": [], "3.13": []})
    lines = []
    assert exe.choose_python(code(tmp_path), "3.13", lines.append) is PY313
    assert exe.choose_python(code(tmp_path / "b"), "3.9", lines.append) is PY314
    assert "Python 3.9 ist nicht installiert. Das Cockpit wählt selbst." in lines


def test_no_python_at_all(tmp_path, monkeypatch):
    monkeypatch.setattr(exe, "find_pythons", lambda: [])
    with pytest.raises(CockpitError) as error:
        exe.choose_python(code(tmp_path))
    assert error.value.message == exe.NO_PYTHON


class Result:
    def __init__(self, code, out=""):
        self.returncode, self.stdout, self.stderr = code, out, ""


def test_missing_wheels_reads_pip_and_remembers(tmp_path, monkeypatch, home):
    monkeypatch.setattr(exe.paths, "cache_dir", lambda: tmp_path / "cache")
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        assert "--dry-run" in args and "--only-binary=:all:" in args
        return Result(1, "ERROR: Could not find a version that satisfies the requirement pygame "
                         "(from versions: none)\nERROR: No matching distribution found for pygame")

    monkeypatch.setattr(exe.subprocess, "run", run)
    folder = code(tmp_path)
    assert exe.missing_wheels(PY314, folder) == ["pygame"]
    assert exe.missing_wheels(PY314, folder) == ["pygame"] and len(calls) == 1   # gemerkt
    (folder / "requirements.txt").write_text("pygame-ce\n", encoding="utf-8")
    monkeypatch.setattr(exe.subprocess, "run", lambda args, **kw: Result(0))
    assert exe.missing_wheels(PY314, folder) == []


def test_missing_wheels_without_internet_is_unknown(tmp_path, monkeypatch, home):
    monkeypatch.setattr(exe.paths, "cache_dir", lambda: tmp_path / "cache")
    monkeypatch.setattr(exe.subprocess, "run", lambda args, **kw: Result(
        1, "WARNING: Retrying ... Failed to establish a new connection"))
    assert exe.missing_wheels(PY314, code(tmp_path)) is None
    assert exe.missing_wheels(PY314, tmp_path) == []             # ohne requirements.txt


def test_find_pythons_reads_the_launcher(tmp_path, monkeypatch):
    for version in ("314", "313"):
        (tmp_path / f"Python{version}").mkdir()
        (tmp_path / f"Python{version}" / "python.exe").write_text("", encoding="utf-8")
    listing = (f" -V:3.14 *        {tmp_path / 'Python314' / 'python.exe'}\n"
               f" -V:3.13          {tmp_path / 'Python313' / 'python.exe'}\n"
               f" -V:3.12          {tmp_path / 'fehlt' / 'python.exe'}\n")
    monkeypatch.setattr(exe.shutil, "which", lambda name: "py.exe")
    monkeypatch.setattr(exe.subprocess, "run",
                        lambda args, **kw: subprocess.CompletedProcess(args, 0, listing, ""))
    assert [p.label for p in exe.find_pythons()] == ["3.14", "3.13"]


def test_venv_with_another_python_is_made_again(tmp_path, monkeypatch):
    venv = tmp_path / "venv"
    (venv / "Scripts").mkdir(parents=True)
    (venv / "Scripts" / "python.exe").write_text("", encoding="utf-8")
    (venv / "pyvenv.cfg").write_text("home = C:\\Python314\nversion = 3.14.6\n",
                                     encoding="utf-8")
    assert exe.venv_version(venv) == (3, 14)
    monkeypatch.setattr(exe, "choose_python", lambda *a, **k: PY313)
    made = []

    def run_process(args, cwd, on_line, cancel, env):
        made.append(args)
        if "venv" in args:
            (venv / "Scripts").mkdir(parents=True)
            (venv / "Scripts" / "python.exe").write_text("", encoding="utf-8")
        return 0

    monkeypatch.setattr(exe, "run_process", run_process)
    monkeypatch.setattr(exe, "_works", lambda python: True)
    lines = []
    exe.prepare_venv(code(tmp_path), lines.append, venv=venv, python_wanted="")
    assert "Die Bau-Umgebung wird für Python 3.13 neu angelegt." in lines
    assert made[0][:3] == [r"C:\Python313\python.exe", "-m", "venv"]


def test_settings_keep_the_python(tmp_path):
    folder = tmp_path / "code"
    folder.mkdir()
    exe.write_settings(folder, exe.BuildSettings("main.py", "Rechner", python="3.13"))
    assert exe.read_settings(folder).python == "3.13"
    exe.write_settings(folder, exe.BuildSettings("main.py", "Rechner"))
    assert exe.read_settings(folder).python == ""
