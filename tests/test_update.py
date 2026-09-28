"""Selbst-Aktualisierung der Exe: Release prüfen, herunterladen, Prüfsumme, Austausch, Rückfrage.

GitHub wird mit httpx.MockTransport ersetzt. Die "Exe" ist eine kleine Textdatei.
"""
from __future__ import annotations

import hashlib
import os
import sys
import time
from datetime import datetime, timezone

import httpx
import pytest

from cockpit.core import exe, update
from cockpit.core.errors import CockpitError

NEW_BYTES = b"neue Version"


def release(content: bytes = NEW_BYTES, tag: str = "v1.1.0", digest: str | None = None,
            published: str = "2030-01-01T10:00:00Z", name: str = "CodeCockpit.exe") -> dict:
    digest = digest if digest is not None else "sha256:" + hashlib.sha256(content).hexdigest()
    return {"tag_name": tag, "body": "Neu: Updates.\nBehoben: Fehler.", "published_at": published,
            "assets": [{"name": name, "digest": digest, "size": len(content),
                        "updated_at": published,
                        "browser_download_url": "https://example.com/CodeCockpit.exe"}]}


def transport(data: dict | None, content: bytes = NEW_BYTES, status: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.github.com":
            assert request.url.path == "/repos/1013hPascal/Codecockpit/releases/latest"
            assert "Authorization" not in request.headers
            if data is None:
                return httpx.Response(404, json={"message": "Not Found"})
            return httpx.Response(200, json=data)
        return httpx.Response(status, content=content)
    return httpx.MockTransport(handler)


@pytest.fixture
def own(tmp_path):
    folder = tmp_path / "Exe"
    folder.mkdir()
    path = folder / "CodeCockpit.exe"
    path.write_bytes(b"alte Version")
    stamp = datetime(2029, 1, 1, tzinfo=timezone.utc).timestamp()
    os.utime(path, (stamp, stamp))
    return path


# -- Prüfen ---------------------------------------------------------------------------------------
def test_newer_release_is_found(own):
    found = update.check(own, transport=transport(release()))
    assert (found.version, found.asset_name) == ("1.1.0", "CodeCockpit.exe")
    assert found.digest == hashlib.sha256(NEW_BYTES).hexdigest()


def test_same_file_is_no_update(own):
    assert update.check(own, transport=transport(release(b"alte Version"))) is None


def test_own_newer_exe_is_not_replaced(own):
    """Selbst gebaute Exe, jünger als das Release: kein Update."""
    old = release(published="2028-01-01T10:00:00Z")
    assert update.check(own, transport=transport(old)) is None


def test_skipped_version(own):
    assert update.check(own, "v1.1.0", transport=transport(release())) is None
    assert update.check(own, "v1.0.0", transport=transport(release())) is not None


def test_no_release_or_no_digest(own):
    assert update.check(own, transport=transport(None)) is None
    assert update.check(own, transport=transport(release(digest=""))) is None
    assert update.check(own, transport=transport(release(name="Quellcode.zip"))) is None


def test_network_error_is_plain_text(own):
    def broken(request):
        raise httpx.ConnectError("kaputt")
    with pytest.raises(CockpitError, match="Keine Verbindung"):
        update.check(own, transport=httpx.MockTransport(broken))


def test_not_frozen_has_no_own_exe():
    assert update.own_exe() is None


# -- Herunterladen und Austausch ------------------------------------------------------------------
def test_download_checks_digest(own):
    found = update.check(own, transport=transport(release()))
    target = update.download(found, own, transport=transport(release()))
    assert target == own.parent / exe.PENDING / "CodeCockpit.exe"
    assert target.read_bytes() == NEW_BYTES
    assert update.is_waiting(own)
    assert own.read_bytes() == b"alte Version"


def test_changed_download_is_deleted(own):
    found = update.check(own, transport=transport(release()))
    with pytest.raises(CockpitError, match="beschädigt oder verändert"):
        update.download(found, own, transport=transport(release(), content=b"untergeschoben"))
    assert not (own.parent / exe.PENDING).exists()
    assert own.read_bytes() == b"alte Version"


def test_swap_script(own):
    found = update.check(own, transport=transport(release()))
    update.download(found, own, transport=transport(release()))
    script = update.swap(own, found.version, start=True).read_text(encoding="utf-8")
    assert f'move /Y "{own}"' in script and "Exe vor dem Update auf 1.1.0" in script
    assert f'move /Y "{own.parent / exe.PENDING / own.name}" "{own}"' in script
    assert f'start "" "{own}"' in script
    later = update.swap(own, found.version, start=False).read_text(encoding="utf-8")
    assert "start " not in later


def test_swap_without_waiting_file(own):
    with pytest.raises(CockpitError, match="keine neue Version"):
        update.swap(own, "1.1.0", start=True)


# -- Einstellung und Oberfläche -------------------------------------------------------------------
def test_setting_default_on(make_services):
    services = make_services([])
    assert services.settings.load().update_check is True
    assert "update_check" in [f.key for f in __import__(
        "cockpit.core.settings", fromlist=["x"]).setting_fields()]


def window_with_exe(qtbot, make_services, own):
    from cockpit.ui.main_window import MainWindow
    services = make_services([])
    win = MainWindow(services)
    qtbot.addWidget(win)
    win.updater.exe_path = own
    return services, win


def test_menu_entry_from_code(qtbot, make_services, monkeypatch):
    from cockpit.ui import update_ui
    from cockpit.ui.main_window import MainWindow
    win = MainWindow(make_services([]))
    qtbot.addWidget(win)
    shown = []
    monkeypatch.setattr(update_ui, "show_info", lambda parent, title, text: shown.append(text))
    win.updater.check_now()
    assert "nur für die Exe" in shown[0]


def test_ask_skip_and_later(qtbot, make_services, own, monkeypatch):
    from cockpit.ui import update_ui
    services, win = window_with_exe(qtbot, make_services, own)
    found = update.check(own, transport=transport(release()))
    monkeypatch.setattr(update_ui, "ask_update", lambda parent, f: update_ui.SKIP)
    win.updater.ask(found)
    assert services.database.get_value(update.SKIPPED_KEY) == "v1.1.0"
    downloads = []
    monkeypatch.setattr(win.updater, "download", downloads.append)
    monkeypatch.setattr(update_ui, "ask_update", lambda parent, f: update_ui.LATER)
    win.updater.ask(found)
    assert downloads == []
    monkeypatch.setattr(update_ui, "ask_update", lambda parent, f: update_ui.UPDATE)
    win.updater.ask(found)
    assert downloads == [found]


def test_auto_check_once_a_day(qtbot, make_services, own, monkeypatch):
    services, win = window_with_exe(qtbot, make_services, own)
    runs = []
    monkeypatch.setattr(win.updater, "run", lambda manual: runs.append(manual))
    services.database.set_value(update.LAST_CHECK_KEY, time.time() - 60)
    win.updater.auto_check()
    assert runs == []
    services.database.set_value(update.LAST_CHECK_KEY, time.time() - update.CHECK_EVERY - 1)
    win.updater.auto_check()
    assert runs == [False]
    services.settings.update(update_check=False)
    win.updater.auto_check()
    assert runs == [False]


def test_later_swaps_on_close(qtbot, make_services, own, monkeypatch):
    from cockpit.ui import update_ui
    services, win = window_with_exe(qtbot, make_services, own)
    found = update.check(own, transport=transport(release()))
    update.download(found, own, transport=transport(release()))
    launched = []
    monkeypatch.setattr(exe, "launch_restart", launched.append)
    monkeypatch.setattr(update_ui, "confirm", lambda *a, **k: False)
    win.updater.downloaded(found)
    assert launched == []
    win.updater.shutdown()
    assert len(launched) == 1
    assert 'start ""' not in launched[0].read_text(encoding="utf-8")


# -- Austausch-Skript wirklich ausführen (Rückmeldung zum Updater, 29.09.2026) ------------------
@pytest.mark.skipif(sys.platform != "win32", reason="nur Windows")
def test_swap_script_really_swaps_after_the_process_ended(tmp_path, monkeypatch):
    import subprocess
    import time
    monkeypatch.setattr(exe.paths, "cache_dir", lambda: tmp_path / "cache")
    folder = tmp_path / "Exe mit Leerzeichen"
    (folder / exe.PENDING).mkdir(parents=True)
    old = folder / "CodeCockpit.exe"
    old.write_text("alt", encoding="utf-8")
    new = folder / exe.PENDING / "CodeCockpit.exe"
    new.write_text("neu", encoding="utf-8")
    backup = tmp_path / "Sicherung"
    backup.mkdir()
    waiting = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(3)"])
    script = exe.swap_script(folder, [old], [new], backup, None, pid=waiting.pid)
    text = script.read_bytes()
    assert b"\r\r\n" not in text and b"\\System32\\find.exe" in text
    started = time.monotonic()
    subprocess.run(["cmd.exe", "/c", str(script)], timeout=60,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert time.monotonic() - started >= 2                # hat auf das Ende gewartet
    waiting.wait()
    assert old.read_text(encoding="utf-8") == "neu"
    assert (backup / "CodeCockpit.exe").read_text(encoding="utf-8") == "alt"
    assert not (folder / exe.PENDING).exists()