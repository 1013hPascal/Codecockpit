"""Fester Ordner für die aktuelle Exe (Wunsch des Nutzers vom 20.10.2026).

Im Ordner Release des Cockpits lagen nur noch CodeCockpit-v1.1.27 bis CodeCockpit-v1.1.30, und das
Update tauschte die Exe in dem Ordner, aus dem sie lief. Jetzt liegt die aktuelle Version immer in
Release\\Name. Wird eine veröffentlichte ersetzt, heißt ihr Ordner Name-vVersion. Die letzten zwei
alten Versionen bleiben, ältere kommen in die Sicherheitskopien.
"""
from __future__ import annotations

import subprocess
import sys
import time

import pytest

from cockpit.core import backups, exe, update
from tests.conftest import patch_running_from


def version_folder(release, name, version, text="alt"):
    folder = release / f"{name}-v{version}"
    folder.mkdir(parents=True)
    (folder / f"{name}.exe").write_text(text, encoding="utf-8")
    (folder / exe.VERSION_FILE).write_text(version + "\n", encoding="utf-8")
    return folder


def test_retire_home_names_a_published_folder(tmp_path):
    home = tmp_path / "Release" / "Rechner"
    home.mkdir(parents=True)
    assert exe.retire_home(home) is None and home.is_dir()          # nicht veröffentlicht
    (home / exe.VERSION_FILE).write_text("1.2.0\n", encoding="utf-8")
    assert exe.retire_home(home) == tmp_path / "Release" / "Rechner-v1.2.0"
    assert not home.exists()


def test_only_the_newest_two_versions_stay(tmp_path, home):
    release = tmp_path / "Release"
    for version in ("1.1.9", "1.1.10", "1.1.27", "1.2.0"):
        version_folder(release, "CodeCockpit", version)
    version_folder(release, "Anderes", "0.1.0")
    moved = exe.prune_versions(release, "CodeCockpit", "CodeCockpit")
    assert sorted(p.name for p in moved) == ["CodeCockpit-v1.1.10", "CodeCockpit-v1.1.9"]
    assert sorted(p.name for p in release.iterdir()) == [
        "Anderes-v0.1.0", "CodeCockpit-v1.1.27", "CodeCockpit-v1.2.0"]
    copies = [p.name for p in backups.backups_dir().iterdir()]
    assert any("Alte Version CodeCockpit-v1.1.9" in name for name in copies)


def test_running_version_is_not_pruned(tmp_path, home, monkeypatch):
    release = tmp_path / "Release"
    for version in ("1.0.0", "1.1.0", "1.2.0"):
        version_folder(release, "CodeCockpit", version)
    patch_running_from(monkeypatch, lambda folder: folder.name.endswith("1.0.0"))
    assert exe.prune_versions(release, "CodeCockpit", "CodeCockpit") == []


def test_fixed_home_of_the_running_exe(tmp_path):
    release = tmp_path / "Release"
    assert update.fixed_home(release / "CodeCockpit" / "CodeCockpit.exe") == \
        release / "CodeCockpit"
    assert update.fixed_home(release / "CodeCockpit-v1.1.28" / "CodeCockpit.exe") == \
        release / "CodeCockpit"
    assert update.fixed_home(tmp_path / "Downloads" / "CodeCockpit.exe") is None
    assert update.pending_dir(release / "CodeCockpit-v1.1.28" / "CodeCockpit.exe") == \
        release / exe.PENDING


@pytest.mark.skipif(sys.platform != "win32", reason="nur Windows")
def test_update_puts_the_new_version_into_the_fixed_folder(tmp_path, home, monkeypatch):
    monkeypatch.setattr(exe.paths, "cache_dir", lambda: tmp_path / "cache")
    release = tmp_path / "Release mit Leerzeichen"
    current = release / "CodeCockpit"
    current.mkdir(parents=True)
    (current / "CodeCockpit.exe").write_text("1.1.29", encoding="utf-8")
    (current / exe.VERSION_FILE).write_text("1.1.29\n", encoding="utf-8")
    pending = release / exe.PENDING
    pending.mkdir()
    (pending / "CodeCockpit.exe").write_text("1.1.30", encoding="utf-8")
    (pending / exe.VERSION_FILE).write_text("1.1.30\n", encoding="utf-8")
    waiting = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(2)"])
    monkeypatch.setattr(exe.os, "getpid", lambda: waiting.pid)
    script = update.swap(current / "CodeCockpit.exe", "1.1.30", start=False)
    started = time.monotonic()
    subprocess.run(["cmd.exe", "/c", str(script)], timeout=60,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    waiting.wait()
    assert time.monotonic() - started >= 1
    assert (current / "CodeCockpit.exe").read_text(encoding="utf-8") == "1.1.30"
    assert exe.folder_version(current) == "1.1.30"
    old = release / "CodeCockpit-v1.1.29"
    assert (old / "CodeCockpit.exe").read_text(encoding="utf-8") == "1.1.29"
    assert not pending.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="nur Windows")
def test_update_from_an_old_version_folder(tmp_path, home, monkeypatch):
    """So liegt es beim Nutzer: Das Cockpit läuft aus CodeCockpit-v1.1.28, CodeCockpit fehlt."""
    monkeypatch.setattr(exe.paths, "cache_dir", lambda: tmp_path / "cache")
    release = tmp_path / "Release"
    running = version_folder(release, "CodeCockpit", "1.1.28")
    pending = release / exe.PENDING
    pending.mkdir()
    (pending / "CodeCockpit.exe").write_text("neu", encoding="utf-8")
    script = update.swap(running / "CodeCockpit.exe", "1.1.31", start=True)
    text = script.read_text(encoding="utf-8")
    # Nicht ausführen: Das Skript würde die Test-"Exe" starten
    assert f'start "" "{release / "CodeCockpit" / "CodeCockpit.exe"}"' in text
    assert f'mkdir "{release / "CodeCockpit"}"' in text
    assert str(running) not in text                                # bleibt als alte Version
    script.unlink()
