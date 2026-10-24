"""Paketübersicht, Kern (Wunsch des Nutzers vom 21.10.2026). pip, winget, choco und ollama sind
nachgebaut. Nichts wird echt installiert oder gelöscht."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from cockpit.core import backups
from cockpit.core.database import Database
from cockpit.features.packages import (base, catalog, choco_source, models, pip_source, record,
                                   runner, web, winget_source)
from cockpit.features.packages.base import Package

WINGET_LIST = """\
   - \\ |
Name                                Id                         Version      Available
-------------------------------------------------------------------------------------
Git                                 Git.Git                    2.55.0.3     2.55.0.5
Microsoft Edge                      Microsoft.Edge             155.0.4283.62
Ein sehr langer Programmname mit …  Lang.Programm              1.0
2 upgrades available.
"""
WINGET_PINS = """\
Name     Id        Version    Source  Pin type
-----------------------------------------------
Git      Git.Git   2.55.0.3   winget  Pinning
"""


class Fake:
    """Nachgebaute Programme: Antworten nach dem Anfang des Befehls."""

    def __init__(self, answers: dict[tuple, str], code: int = 0):
        self.answers = answers
        self.code = code
        self.calls: list[list[str]] = []
        self.elevated: list[list[str]] = []

    def _answer(self, args):
        for start, text in self.answers.items():
            if tuple(args[:len(start)]) == start or (
                    Path(args[0]).stem == start[0] and tuple(args[1:len(start)]) == start[1:]):
                return runner.Result(self.code, text.splitlines())
        return runner.Result(0, [])

    def run(self, args, cancel=None, on_line=None, cwd=None):
        self.calls.append(list(args))
        return self._answer(args)

    def run_elevated(self, args, cancel=None):
        self.elevated.append(list(args))
        return self._answer(args)


@pytest.fixture
def fake(monkeypatch):
    made = Fake({})
    monkeypatch.setattr(runner, "run", made.run)
    monkeypatch.setattr(runner, "elevated", made.run_elevated)
    monkeypatch.setattr(runner, "find", lambda program: program)
    return made


@pytest.fixture
def database(tmp_path):
    db = Database(tmp_path / "test.db")
    yield db
    db.close()


# -- Zeilen ---------------------------------------------------------------------------------------
def test_line_puts_the_important_part_first():
    package = Package("pip", "requests", "2.31.0", latest="2.32.3", checked=True,
                      size=520 * 1024, added=datetime(2026, 10, 12), place="Projekt Tagebuch",
                      license="Apache-2.0")
    assert package.line() == ("requests 2.31.0, veraltet, neu: 2.32.3, 520 KB, 12.10.2026, "
                              "Projekt Tagebuch, Lizenz Apache-2.0")
    assert Package("pip", "x", "1", checked=True).state() == "aktuell"
    assert Package("pip", "x", "1").state() == "noch nicht geprüft"
    assert base.size_text(3 * (1 << 30) + (1 << 29)) == "3,5 GB"


def test_newest_first_and_filter():
    old = Package("pip", "alt", "1", added=datetime(2025, 1, 1))
    new = Package("pip", "neu", "1", added=datetime(2026, 1, 1), cockpit=True)
    none = Package("pip", "ohne", "1", used_by=("Tagebuch",))
    assert [p.name for p in base.newest_first([old, none, new])] == ["neu", "alt", "ohne"]
    assert [p.name for p in base.apply_filter([old, new, none], base.COCKPIT)] == ["neu", "ohne"]
    assert [p.name for p in base.apply_filter([old, new, none], base.MACHINE)] == ["alt"]


def test_versions_and_major_jump():
    found = sorted(["1.10.0", "1.9.2", "2.0.0rc1", "2.0.0", "18.4-1"], key=base.version_key)
    assert found == ["1.9.2", "1.10.0", "2.0.0rc1", "2.0.0", "18.4-1"]
    assert base.major_jump("1.9.2", "2.0.0") and not base.major_jump("1.9.2", "1.10.0")


# -- pip ------------------------------------------------------------------------------------------
def test_pip_script_runs_in_real_python():
    """Das Prüfprogramm läuft im Python der Tests und findet pytest."""
    import subprocess
    out = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", pip_source.SCRIPT],
                         capture_output=True, text=True, timeout=120).stdout
    rows = {row[0].lower(): row for row in json.loads(out.strip().splitlines()[-1])}
    assert "pytest" in rows and rows["pytest"][1] and rows["pytest"][3] > 0


def test_pip_outdated_and_actions(fake, tmp_path):
    env = pip_source.Environment("Projekt Tagebuch", tmp_path / "python.exe", "Tagebuch", True, 3)
    rows = [["requests", "2.31.0", 1760000000, 1000, "Apache-2.0"], ["six", "1.16.0", 0, 0, ""]]
    fake.answers = {(str(env.python), "-I", "-X"): json.dumps(rows),
                    (str(env.python), "-I", "-m", "pip", "list"):
                        'warnung\n[{"name": "requests", "version": "2.31.0", '
                        '"latest_version": "2.32.3"}]'}
    packages = pip_source.list_packages(env)
    assert [p.name for p in packages] == ["requests", "six"]
    assert packages[0].cockpit and packages[0].owner == "Tagebuch" and packages[1].added is None
    pip_source.check_outdated(env, packages)
    assert packages[0].latest == "2.32.3" and packages[1].checked and not packages[1].outdated
    pip_source.install_version(packages[0], "2.30.0")
    assert fake.calls[-1][-3:] == ["install", "requests==2.30.0", "--disable-pip-version-check"]
    pip_source.uninstall(packages[1])
    assert fake.calls[-1][-4:-1] == ["uninstall", "-y", "six"]


def test_pip_environments(tmp_path, monkeypatch):
    from cockpit.core import exe
    from cockpit.core.projects import Project
    monkeypatch.setattr(exe, "find_pythons", lambda: [])
    folder = tmp_path / "Tagebuch"
    projects = [Project(7, "Tagebuch", folder, folder / "Code", folder / "Exe", linked=True)]
    python = exe.venv_python(projects[0].code_dir)
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    cache = tmp_path / "cache"
    for name in ("Tagebuch-p7", "Alt-p99"):
        (cache / "venvs" / name / "Scripts").mkdir(parents=True)
        (cache / "venvs" / name / "Scripts" / "python.exe").write_text("", encoding="utf-8")
    found = pip_source.environments(projects, cache)
    assert [e.label for e in found] == ["Projekt Tagebuch", "Exe-Bau ohne Projekt (Alt-p99)",
                                        "Exe-Bau Tagebuch"]
    assert found[0].project_id == 7 and found[1].project_id is None and found[1].cockpit


def test_pypi_versions_without_prereleases():
    def handler(request):
        return httpx.Response(200, json={"releases": {"1.0": [{}], "2.0": [{}], "2.1rc1": [{}],
                                                      "0.9": []},
                                         "info": {"project_urls": {"Changelog": "https://c"}}})
    web.transport = httpx.MockTransport(handler)
    try:
        assert pip_source.versions("x") == ["2.0", "1.0"]
        assert pip_source.change_log("x") == "https://c"
    finally:
        web.transport = None


# -- winget ---------------------------------------------------------------------------------------
def test_winget_table_and_pins(fake):
    fake.answers = {("winget", "list"): WINGET_LIST, ("winget", "pin", "list"): WINGET_PINS}
    from datetime import datetime as dt
    registry = {"Git": (dt(2026, 3, 1), 300 * 1024 * 1024),
                "Ein sehr langer Programmname mit Rest": (dt(2025, 1, 2), None)}
    packages = winget_source.list_packages(registry=registry)
    assert [(p.name, p.id, p.version, p.latest) for p in packages] == [
        ("Git", "Git.Git", "2.55.0.3", "2.55.0.5"),
        ("Microsoft Edge", "Microsoft.Edge", "155.0.4283.62", ""),
        ("Ein sehr langer Programmname mit …", "Lang.Programm", "1.0", "")]
    assert packages[0].pinned and packages[0].added == dt(2026, 3, 1)
    assert packages[2].added == dt(2025, 1, 2) and all(p.checked for p in packages)
    winget_source.upgrade(packages[1])
    assert fake.calls[-1][:5] == ["winget", "upgrade", "--id", "Microsoft.Edge", "--exact"]


def test_winget_versions(fake):
    fake.answers = {("winget", "show"): "Gefunden Git [Git.Git]\nVersion\n-------\n2.55.0.5\n"
                                        "2.55.0.3\n"}
    assert winget_source.versions(Package("winget", "Git", "1", key="Git.Git")) == [
        "2.55.0.5", "2.55.0.3"]


# -- Chocolatey ----------------------------------------------------------------------------------
def test_choco_list_outdated_and_admin(fake, tmp_path, monkeypatch):
    monkeypatch.setenv("ChocolateyInstall", str(tmp_path))
    (tmp_path / "lib" / "ollama").mkdir(parents=True)
    (tmp_path / "lib" / "ollama" / "a.nupkg").write_bytes(b"x" * 2048)
    fake.answers = {("choco", "list"): "chocolatey|2.7.3\nollama|0.31.1\n",
                    ("choco", "outdated"): "ollama|0.31.1|0.40.7|false\n",
                    ("choco", "pin", "list"): "chocolatey|2.7.3\n"}
    packages = choco_source.list_packages()
    assert packages[1].size == 2048 and packages[0].size is None
    choco_source.check_outdated(packages)
    assert packages[1].latest == "0.40.7" and packages[0].pinned and not packages[0].outdated
    choco_source.upgrade(packages[1])
    assert fake.elevated[-1][1:3] == ["upgrade", "ollama"] and fake.calls[-1][1] == "pin"


# -- Modelle --------------------------------------------------------------------------------------
def hf_repo(cache: Path, repo: str, revisions: list[str], current: str) -> Path:
    folder = cache / ("models--" + repo.replace("/", "--"))
    (folder / "refs").mkdir(parents=True)
    (folder / "refs" / "main").write_text(current, encoding="utf-8")
    for revision in revisions:
        (folder / "snapshots" / revision).mkdir(parents=True)
        (folder / "snapshots" / revision / "model.bin").write_bytes(b"m" * 1000)
    return folder


def test_huggingface_models_and_old_revisions(tmp_path, monkeypatch):
    monkeypatch.setattr(models, "hf_cache", lambda: tmp_path)
    hf_repo(tmp_path, "Systran/faster-whisper-small", ["aaa1111", "bbb2222"], "bbb2222")
    found = models.huggingface_models()
    assert found[0].name == "Systran/faster-whisper-small" and found[0].version == "bbb2222"
    assert found[0].size == 2007 and len(found[0].extra["revisions"]) == 2   # mit refs/main
    assert [p.name for p in models.hf_old_revisions(found[0])] == ["aaa1111"]
    assert models.hf_remove_old(found[0]) == 1000

    def handler(request):
        return httpx.Response(200, json={"sha": "ccc33334444"})
    web.transport = httpx.MockTransport(handler)
    try:
        models.hf_check(found)
    finally:
        web.transport = None
    assert found[0].latest == "ccc3333" and found[0].outdated


def ollama_manifest(root: Path, name: str, tag: str, size: int) -> bytes:
    path = root / "manifests" / "registry.ollama.ai" / "library" / name / tag
    path.parent.mkdir(parents=True)
    data = json.dumps({"config": {"size": 10}, "layers": [{"digest": "sha256:a", "size": size}]})
    path.write_text(data, encoding="utf-8")
    return data.encode("utf-8")


def test_ollama_models_check_and_keep_old(tmp_path, fake, monkeypatch):
    data = ollama_manifest(tmp_path, "llama3.2", "3b", 2_000_000_000)
    found = models.ollama_models(tmp_path)
    assert found[0].name == "llama3.2:3b" and found[0].size == 2_000_000_010
    assert found[0].extra["digest"] == hashlib.sha256(data).hexdigest()

    def handler(request):
        assert request.headers["Accept"] == models.OLLAMA_ACCEPT
        return httpx.Response(200, content=b"anders")
    web.transport = httpx.MockTransport(handler)
    try:
        models.ollama_check(found)
    finally:
        web.transport = None
    assert found[0].outdated
    kept = models.ollama_update(found[0], keep_old=True)
    assert fake.calls[0][:3] == ["ollama", "cp", "llama3.2:3b"] and kept.startswith(
        "llama3.2:3b-alt-")
    assert fake.calls[1] == ["ollama", "pull", "llama3.2:3b"]


def test_ollama_not_running_gives_a_clear_message(fake):
    fake.code = 1
    fake.answers = {("ollama", "rm"): "Error: could not connect to ollama app"}
    from cockpit.core.errors import CockpitError
    with pytest.raises(CockpitError) as raised:
        models.ollama_remove(Package("model", "x:1", "1", key="x:1", kind=models.OLLAMA))
    assert raised.value.message == models.NEEDS_OLLAMA


def test_model_files_in_a_folder(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "modell.gguf").write_bytes(b"g" * 10)
    (tmp_path / "a" / "klein.bin").write_bytes(b"b" * 10)          # zu klein für ein Modell
    (tmp_path / "a" / "text.txt").write_text("x", encoding="utf-8")
    found = models.scan_folder(tmp_path, "Ordner")
    assert [p.name for p in found] == ["modell.gguf"] and found[0].kind == models.FILE


# -- Merken, Festhalten, Löschen ------------------------------------------------------------------
def test_history_pins_and_previous_version(database):
    package = Package("pip", "requests", "2.31.0", place="Python 3.14")
    record.remember(database, package, "2.32.3")
    package.version = "2.32.3"
    assert record.previous_version(database, package) == "2.31.0"
    assert record.history(database)[0].startswith("requests: 2.31.0 zu 2.32.3, Python 3.14")
    record.set_pinned(database, package, True)
    other = Package("pip", "requests", "2.32.3", place="Python 3.14")
    record.mark_pins(database, [other])
    assert other.pinned and record.pinned(database, package)
    record.set_pinned(database, package, False)
    assert not record.pinned(database, package)


def test_delete_saves_a_list_instead_of_a_copy(database, fake, tmp_path, monkeypatch):
    monkeypatch.setattr(backups, "backups_dir", lambda: tmp_path / "kopien")
    (tmp_path / "kopien").mkdir()
    python = tmp_path / "python.exe"
    packages = [Package("pip", "six", "1.16.0", key="six", place="Python 3.14", location=python),
                Package("winget", "Git", "2.55", key="Git.Git", place="winget")]
    text = catalog.uninstall(database, packages)
    assert text.startswith("2 Einträge gelöscht.")
    saved = next((tmp_path / "kopien").iterdir()) / "Pakete.txt"
    content = saved.read_text(encoding="utf-8")
    assert f'"{python}" -m pip install six==1.16.0' in content
    assert "winget install --id Git.Git --exact --version 2.55" in content
    assert ["winget", "uninstall", "--id", "Git.Git"] == fake.calls[-1][:4]


def test_upgrade_all_skips_pinned_and_models(database, fake, tmp_path):
    python = tmp_path / "python.exe"
    packages = [Package("pip", "a", "1", key="a", latest="2", location=python),
                Package("pip", "b", "1", key="b", latest="2", location=python, pinned=True),
                Package("pip", "c", "1", key="c", latest="", location=python, checked=True),
                Package("model", "m", "1", key="m", latest="2", kind=models.OLLAMA)]
    assert catalog.upgrade_all(database, packages) == "1 Paket aktualisiert."
    assert [c[-2] for c in fake.calls] == ["a"]
    assert record.history(database)[0].startswith("a: 1 zu 2")


def test_space_line():
    by_source = {"model": [Package("model", "a", "", size=30 << 30),
                           Package("model", "b", "", size=3 << 30, cockpit=True)]}
    assert catalog.space_line(by_source) == ("Speicherplatz: Modelle: 33 GB, davon Cockpit: "
                                             "3,0 GB")
