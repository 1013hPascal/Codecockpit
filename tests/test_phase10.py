"""Phase 10: Eintrag Exe, Exe übernehmen, bauen, testen, ersetzen, veröffentlichen und holen.

PyInstaller läuft hier nicht wirklich (das dauert Minuten). Bau und Test werden an den Nahtstellen
ersetzt. Echte Programme sind kleine .bat-Dateien. Alle Geheimnisse sind erfunden.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import httpx
import pytest

from cockpit.core import exe
from cockpit.core.errors import CockpitError
from cockpit.core.projects import read_config
from cockpit.features.exe_build.manifest import MANIFEST as EXE_BUILD
from tests.conftest import FAKE_TOKEN, make_project, said
from tests.test_phase5a import sh

windows = pytest.mark.skipif(sys.platform != "win32", reason="nur Windows")


def project_with(make_services, projects_root, exe_dir=True, manifests=None):
    services = make_services(manifests if manifests is not None else [EXE_BUILD])
    services.projects.add(make_project(projects_root, "Rechner", exe=exe_dir))
    return services, services.projects.all()[0]


def fake_exe(folder: Path, name: str = "Rechner.exe", text: str = "x") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


# -- Zustand --------------------------------------------------------------------------------------
def test_record_and_settings_round_trip(tmp_path):
    exe.write_record(tmp_path, exe.ExeRecord("release", "2026-09-27T10:00:00", "", "1.2.0"))
    settings = exe.BuildSettings("app.py", "App", one_file=False, windowed=False,
                                 datas=[["daten", "daten"]], hidden_imports=["x"])
    exe.write_settings(tmp_path, settings)
    record = exe.read_record(tmp_path)
    assert (record.source, record.version) == ("release", "1.2.0")
    assert exe.read_settings(tmp_path) == settings
    assert read_config(tmp_path)["exe"]["build"]["name"] == "App"


def test_status_lines(make_services, projects_root):
    services, project = project_with(make_services, projects_root)
    assert exe.status_line(project) == "Exe, noch keine Exe-Datei"
    fake_exe(project.exe_dir)
    assert exe.status_line(project).endswith("Herkunft unbekannt")
    exe.write_record(project.code_dir, exe.ExeRecord("extern", "2026-09-20T09:00:00"))
    assert exe.status_line(project) == "Exe, extern erstellt am 20.09.2026"
    exe.write_record(project.code_dir, exe.ExeRecord("release", "2026-09-21T09:00:00", "",
                                                     "1.3.0"))
    assert exe.status_line(project) == "Exe, Version 1.3.0, aus dem Release am 21.09.2026"
    exe.write_record(project.code_dir, exe.ExeRecord("cockpit", "2026-09-23T09:00:00", "abc"))
    assert exe.status_line(project, head="abc") == "Exe, vom Cockpit erstellt am 23.09.2026, aktuell"
    assert exe.status_line(project, head="def").endswith("älter als der Code")


def test_older_than_the_code_with_real_git(make_services, projects_root):
    services, project = project_with(make_services, projects_root)
    sh(project.code_dir, "init", "-q")
    sh(project.code_dir, "add", "-A")
    sh(project.code_dir, "commit", "-q", "-m", "Anfang")
    fake_exe(project.exe_dir)
    exe.write_record(project.code_dir, exe.ExeRecord("cockpit", exe.now(),
                                                     exe.head_commit(project.code_dir)))
    assert exe.status_line(project).endswith("aktuell")
    (project.code_dir / "neu.py").write_text("x = 1\n", encoding="utf-8")
    sh(project.code_dir, "add", "-A")
    sh(project.code_dir, "commit", "-q", "-m", "Weiter")
    assert exe.status_line(project).endswith("älter als der Code")


# -- Exe-Ordner und Übernehmen ------------------------------------------------------------------
def test_adopt_file_with_backup(make_services, projects_root, tmp_path):
    from cockpit.core import backups
    services, project = project_with(make_services, projects_root)
    fake_exe(project.exe_dir, "Alt.exe", "alt")
    source = fake_exe(tmp_path / "woanders", "Neu.exe", "neu")
    target = exe.adopt(project, source)
    assert target == project.exe_dir / "Neu.exe" and source.is_file()     # kopiert
    assert not (project.exe_dir / "Alt.exe").exists()
    saved = [b for b in backups.all_backups() if (b.path / "Alt.exe").is_file()]
    assert saved and (saved[0].path / "Alt.exe").read_text() == "alt"
    assert exe.read_record(project.code_dir).source == "extern"


def test_adopt_folder_and_errors(make_services, projects_root, tmp_path):
    services, project = project_with(make_services, projects_root)
    folder = tmp_path / "Programm"
    fake_exe(folder, "Programm.exe")
    (folder / "daten.bin").write_text("d")
    assert exe.adopt(project, folder).is_dir()
    assert exe.current_exe(project) == project.exe_dir / "Programm" / "Programm.exe"
    with pytest.raises(CockpitError, match="Exe-Datei wählen"):
        exe.adopt(project, fake_exe(tmp_path, "notiz.txt"))
    empty = tmp_path / "leer"
    empty.mkdir()
    with pytest.raises(CockpitError, match="keine Exe-Datei"):
        exe.adopt(project, empty)


def test_backup_rolls_back_when_the_exe_is_locked(make_services, projects_root, monkeypatch):
    services, project = project_with(make_services, projects_root)
    fake_exe(project.exe_dir, "a.exe")
    fake_exe(project.exe_dir, "b.exe")
    real_move = exe.shutil.move
    calls = []

    def move(src, dst):
        calls.append(src)
        if len(calls) == 2:
            raise PermissionError("gesperrt")
        return real_move(src, dst)
    monkeypatch.setattr(exe.shutil, "move", move)
    with pytest.raises(CockpitError, match="Läuft sie gerade"):
        exe.backup_current(project, "Test")
    assert sorted(p.name for p in project.exe_dir.iterdir()) == ["a.exe", "b.exe"]


def test_add_exe_dir(make_services, projects_root):
    services, project = project_with(make_services, projects_root, exe_dir=False)
    assert not project.has_exe_dir
    exe.add_exe_dir(project)
    assert project.has_exe_dir


# -- Bauen ----------------------------------------------------------------------------------------
@pytest.mark.parametrize("one_file", [True, False])
def test_spec_text_is_valid_python(one_file):
    settings = exe.BuildSettings("main.py", "Rechner", one_file=one_file, windowed=True,
                                 icon="app.ico", datas=[["daten", "daten"]])
    text = exe.spec_text(settings)
    compile(text, "Rechner.spec", "exec")
    assert "console=False" in text and "'app.ico'" in text
    assert ("COLLECT(" in text) is not one_file


def test_existing_spec_is_kept(tmp_path):
    settings = exe.BuildSettings(name="App")
    (tmp_path / "App.spec").write_text("# eigene Fassung\n", encoding="utf-8")
    exe.ensure_spec(tmp_path, settings)
    assert (tmp_path / "App.spec").read_text(encoding="utf-8") == "# eigene Fassung\n"


@windows
def test_start_test(tmp_path):
    ok = tmp_path / "ok.bat"
    ok.write_text("@exit /b 0\n")
    assert "ohne Fehler beendet" in exe.start_test(ok, 5)
    bad = tmp_path / "bad.bat"
    bad.write_text("@exit /b 3\n")
    with pytest.raises(CockpitError, match="Rückgabewert 3"):
        exe.start_test(bad, 5)
    slow = tmp_path / "slow.bat"
    slow.write_text("@ping -n 30 127.0.0.1 >nul\n")
    assert "lief 1 Sekunden" in exe.start_test(slow, 1)


def test_build_replaces_only_after_the_test(make_services, projects_root, tmp_path, monkeypatch):
    services, project = project_with(make_services, projects_root)
    fake_exe(project.exe_dir, "Rechner.exe", "alt")
    monkeypatch.setattr(exe, "prepare_venv", lambda code_dir, on_line, cancel: Path("py.exe"))
    monkeypatch.setattr(exe.paths, "cache_dir", lambda: tmp_path / "cache")
    (tmp_path / "cache").mkdir()

    def fake_build(code_dir, python, spec, work, on_line, cancel):
        return fake_exe(work / "dist", "Rechner.exe", "neu")
    monkeypatch.setattr(exe, "pyinstaller_build", fake_build)
    steps = []
    settings = exe.BuildSettings(name="Rechner")

    def failing_test(path, seconds, self_test, cancel, windowed=False):
        raise CockpitError("Test nicht bestanden.")
    monkeypatch.setattr(exe, "start_test", failing_test)
    with pytest.raises(CockpitError):
        exe.build(project, settings, steps.append, steps.append)
    assert (project.exe_dir / "Rechner.exe").read_text() == "alt"      # alte Exe bleibt
    monkeypatch.setattr(exe, "start_test", lambda path, seconds, self_test, cancel, windowed=False:
                        "Start-Test bestanden.")
    result = exe.build(project, settings, steps.append, steps.append)
    assert (project.exe_dir / "Rechner.exe").read_text() == "neu"
    assert result.backup is not None and (result.backup / "Rechner.exe").read_text() == "alt"
    assert "Schritt 3 von 4: Exe wird getestet" in steps and "Start-Test bestanden." in steps
    assert exe.read_record(project.code_dir).source == "cockpit"
    assert (project.code_dir / "Rechner.spec").is_file()


def test_own_exe_waits_for_restart(make_services, projects_root, tmp_path, monkeypatch):
    services, project = project_with(make_services, projects_root)
    (project.code_dir / "cockpit.toml").write_text("is_cockpit = true\n", encoding="utf-8")
    fake_exe(project.exe_dir, "Rechner.exe", "alt")
    monkeypatch.setattr(exe, "running_from", lambda folder: True)
    built = fake_exe(tmp_path / "dist", "Rechner.exe", "neu")
    result = exe.install(project, built, "abc")
    assert result.pending
    assert (project.exe_dir / exe.PENDING / "Rechner.exe").read_text() == "neu"
    assert (project.exe_dir / "Rechner.exe").read_text() == "alt"
    assert exe.current_exe(project) == project.exe_dir / "Rechner.exe"
    assert exe.status_line(project, head="abc").endswith("wartet auf den Neustart")
    monkeypatch.setattr(exe.paths, "cache_dir", lambda: tmp_path / "cache")
    script = exe.restart_script(project).read_text(encoding="utf-8")
    assert "tasklist" in script and f'"{project.exe_dir / "Rechner.exe"}"' in script
    assert f'start "" "{project.exe_dir / "Rechner.exe"}"' in script
    assert not exe.read_record(project.code_dir).pending


def test_find_python():
    assert exe.find_python() is not None


# -- Versionen und Releases -------------------------------------------------------------------------
def test_versions():
    assert exe.next_version([]) == "1.0.0"
    assert exe.next_version(["v1.2.9", "v1.10.0", "notiz"]) == "1.10.1"
    assert exe.check_version(" v2.0.0 ", ["v1.0.0"]) == "2.0.0"
    with pytest.raises(CockpitError, match="gibt es schon"):
        exe.check_version("1.0.0", ["v1.0.0"])
    with pytest.raises(CockpitError, match="wie 1.0.0"):
        exe.check_version("neu", [])


def test_assets_and_unpack(make_services, projects_root, tmp_path):
    from cockpit.platforms.base import ReleaseAsset
    services, project = project_with(make_services, projects_root)
    single = fake_exe(project.exe_dir)
    assert exe.asset_for_upload(project, single, tmp_path) == single
    folder_exe = fake_exe(project.exe_dir / "Programm", "Programm.exe")
    archive = exe.asset_for_upload(project, folder_exe, tmp_path)
    assert archive.suffix == ".zip" and "Programm/Programm.exe" in zipfile.ZipFile(archive).namelist()
    unpacked = exe.unpack(archive, tmp_path / "raus")
    assert (unpacked / "Programm.exe").is_file()
    assets = [ReleaseAsset(1, "quelle.tar.gz", 1), ReleaseAsset(2, "App.zip", 1),
              ReleaseAsset(3, "App.exe", 1)]
    assert exe.pick_asset(assets).id == 3 and exe.pick_asset(assets[:2]).id == 2
    assert exe.pick_asset(assets[:1]) is None


def github(handler):
    from cockpit.core.secret import Secret
    from cockpit.platforms.github import GitHubPlatform
    GitHubPlatform.transport = httpx.MockTransport(handler)
    return GitHubPlatform(token=Secret(FAKE_TOKEN), username="tester")


@pytest.fixture(autouse=True)
def _reset_transport():
    yield
    from cockpit.platforms.github import GitHubPlatform
    GitHubPlatform.transport = None


def test_github_releases(tmp_path):
    from cockpit.platforms.base import RepoRef
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "GET" and request.url.path.endswith("/releases"):
            return httpx.Response(200, json=[
                {"id": 7, "tag_name": "v1.0.0", "name": "Version 1.0.0", "html_url": "u",
                 "published_at": "2026-09-27T10:00:00Z", "draft": False,
                 "assets": [{"id": 70, "name": "App.exe", "size": 1024}]},
                {"id": 8, "tag_name": "v2.0.0", "draft": True, "assets": []}])
        if request.method == "POST" and request.url.path.endswith("/releases"):
            body = json.loads(request.content)
            return httpx.Response(201, json={
                "id": 9, "tag_name": body["tag_name"], "name": body["name"],
                "html_url": "https://github.com/tester/app/releases/tag/v1.0.1",
                "upload_url": "https://uploads.github.com/repos/tester/app/releases/9/assets"
                              "{?name,label}", "assets": []})
        if request.url.host == "uploads.github.com":
            return httpx.Response(201, json={"id": 90, "name": request.url.params["name"],
                                             "size": len(request.content)})
        if "/releases/assets/" in request.url.path:
            return httpx.Response(200, content=b"EXE-INHALT")
        return httpx.Response(404, json={"message": "Not Found"})

    platform = github(handler)
    ref = RepoRef("tester", "app")
    releases = platform.releases(ref)
    assert [r.tag for r in releases] == ["v1.0.0"] and releases[0].assets[0].name == "App.exe"
    release = platform.create_release(ref, "v1.0.1", "Version 1.0.1", "Neu.", "main")
    assert json.loads(seen[-1].content)["target_commitish"] == "main"
    file = fake_exe(tmp_path, "App.exe", "inhalt")
    asset = platform.upload_asset(ref, release, file)
    assert asset.name == "App.exe" and seen[-1].headers["Content-Type"] == \
        "application/octet-stream"
    assert seen[-1].headers["Authorization"] == f"Bearer {FAKE_TOKEN}"
    platform.download_asset(ref, releases[0].assets[0], tmp_path / "geholt.exe")
    assert (tmp_path / "geholt.exe").read_bytes() == b"EXE-INHALT"
    assert seen[-1].headers["Accept"] == "application/octet-stream"


# -- Einrichtung prüfen -----------------------------------------------------------------------------
def test_setup_check(make_services, projects_root):
    from cockpit.features.exe_build.setup_check import check, third_party_imports
    services, project = project_with(make_services, projects_root)
    code = project.code_dir
    assert check(project)[0].startswith("Nicht bereit")
    (code / "main.py").write_text("import os\nimport requests\nfrom PySide6 import QtCore\n"
                                  "import helfer\n\nhelfer.start()\n", encoding="utf-8")
    (code / "helfer.py").write_text("import yaml\n", encoding="utf-8")
    (code / "tests").mkdir()
    (code / "tests" / "test_x.py").write_text("import pytest\n", encoding="utf-8")
    (code / "requirements.txt").write_text("PySide6==6.11.2\nrequests>=2\n", encoding="utf-8")
    assert third_party_imports(code) == {"requests", "PySide6", "yaml"}
    settings = exe.BuildSettings(name="Rechner")
    exe.write_settings(code, settings)
    exe.ensure_spec(code, settings)
    lines = check(project)
    # Seit 10g ist eine fehlende Bibliothek ein Problem, weil sie dann in der Exe fehlt
    assert lines[0] == "Nicht bereit: 1 Problem, 1 Warnung."
    assert "In Ordnung: Rechner.spec ist da." in lines
    assert ("Problem: Diese Bibliotheken stehen nicht in requirements.txt und fehlen deshalb in "
            "der Exe: yaml.") in lines
    assert any(line.startswith("Warnung: Ohne feste Version: requests.") for line in lines)
    spec = code / "Rechner.spec"
    spec.write_text(spec.read_text(encoding="utf-8") + "# 'C:\\\\Users\\\\x'\n", encoding="utf-8")
    assert any(line.startswith("Problem: Rechner.spec enthält feste Pfade") for line in check(project))


def test_cockpit_can_build_itself():
    root = Path(__file__).resolve().parents[1]
    settings = exe.read_settings(root)
    assert settings.name == "CodeCockpit" and settings.self_test
    assert (root / settings.spec_name).is_file()
    compile((root / settings.spec_name).read_text(encoding="utf-8"), "spec", "exec")


def test_self_test_finds_everything(make_services):
    from cockpit.core.features.registry import FeatureRegistry
    from main import self_test_problems
    services = make_services(FeatureRegistry.discover().all())
    assert self_test_problems(services) == []


# -- Oberfläche -------------------------------------------------------------------------------------
def window_for(qtbot, services):
    from cockpit.ui.main_window import MainWindow
    win = MainWindow(services)
    qtbot.addWidget(win)
    win.reload_projects(refresh=False)
    return win


def labels(win):
    return [e.label for e in win.current_entries()]


def test_actions_follow_the_state(qtbot, make_services, projects_root):
    from cockpit.core.actions import Target
    services, project = project_with(make_services, projects_root, exe_dir=False)
    win = window_for(qtbot, services)
    win.project_list.select(Target.PROJECT, project.id)
    assert "Exe hinzufügen …" in labels(win)
    exe.add_exe_dir(project)
    win.reload_projects(refresh=False)
    win.project_list.select(Target.PROJECT, project.id)
    assert "Exe hinzufügen …" not in labels(win)
    win.project_list.select(Target.EXE, project.id)
    entries = labels(win)
    # Zusammengefasst am 30.09.2026: Erstellen mit Einrichten, Exe einlesen
    assert "Exe aus dem Code erstellen …" in entries and "Exe einlesen …" in entries
    assert "Wie funktioniert die Exe? …" in entries
    assert "Exe veröffentlichen …" not in entries             # kein Repository auf GitHub
    fake_exe(project.exe_dir)
    win.refresh_actions()
    assert "Exe aus dem Code erstellen …" in labels(win)
    services.features.disable("exe_build", project)
    win.refresh_actions()
    assert not any("aus dem Code" in e for e in labels(win))


def test_add_exe_action(qtbot, make_services, projects_root, monkeypatch):
    from cockpit.core.actions import Target
    from cockpit.ui import exe_flow
    services, project = project_with(make_services, projects_root, exe_dir=False)
    win = window_for(qtbot, services)
    questions = []
    monkeypatch.setattr(exe_flow, "confirm", lambda parent, title, text, **kw:
                        questions.append(text) or True)
    win.project_list.select(Target.PROJECT, project.id)
    entry = next(e for e in win.current_entries() if e.label == "Exe hinzufügen …")
    win.run_entry(entry)
    assert questions[0].startswith("Im Projektordner wird der Ordner Exe angelegt")
    assert project.exe_dir.is_dir() and said("Ordner Exe angelegt.")
    assert win.project_list.current_target() == (Target.EXE, project.id)


def test_build_dialog_shows_steps_and_result(qtbot, make_services, projects_root, monkeypatch):
    from cockpit.ui import exe_flow
    services, project = project_with(make_services, projects_root)

    def fake_build(project, settings, on_status, on_line, cancel, branch_dir=None,
                   branch_name=""):
        on_status("Schritt 1 von 4: Virtuelle Umgebung und Bibliotheken werden vorbereitet")
        on_line("Successfully installed pyinstaller")
        return exe.BuildResult(fake_exe(project.exe_dir))
    monkeypatch.setattr(exe, "build", fake_build)
    dialog = exe_flow.BuildDialog(services, project, exe.BuildSettings(name="Rechner"))
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.running, timeout=10000)
    lines = [dialog.output.item(i).text() for i in range(dialog.output.count())]
    assert lines[-1] == "Exe erstellt, getestet und übernommen: Rechner.exe."
    assert "Successfully installed pyinstaller" in lines
    assert said("Schritt 1 von 4") and dialog.output.accessibleName() == "Ausgabe"
    assert dialog.stop_button.isHidden()


def test_build_dialog_error_keeps_old_exe(qtbot, make_services, projects_root, monkeypatch):
    from cockpit.ui import exe_flow
    services, project = project_with(make_services, projects_root)

    def fake_build(project, settings, on_status, on_line, cancel, branch_dir=None,
                   branch_name=""):
        raise CockpitError("PyInstaller hat die Exe nicht gebaut.", "Rückgabewert 1")
    monkeypatch.setattr(exe, "build", fake_build)
    dialog = exe_flow.BuildDialog(services, project, exe.BuildSettings(name="Rechner"))
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.running, timeout=10000)
    assert dialog.result is None
    assert dialog.output.item(dialog.output.count() - 1).text() == \
        "Fehler: PyInstaller hat die Exe nicht gebaut."


def test_build_settings_dialog(qtbot, make_services, projects_root):
    from cockpit.ui import exe_flow
    services, project = project_with(make_services, projects_root)
    dialog = exe_flow.BuildSettingsDialog(project)
    qtbot.addWidget(dialog)
    assert dialog.form.fields["start_file"].get() == "main.py"
    dialog.form.fields["mode"].set(exe_flow.FOLDER)
    dialog.check()
    assert dialog.settings.name == "Rechner" and not dialog.settings.one_file
    dialog.form.fields["start_file"].set("fehlt.py")
    dialog.settings = None
    import cockpit.ui.exe_flow as flow
    errors = []
    flow.show_error, old = (lambda parent, title, text, details="": errors.append(text)), \
        flow.show_error
    try:
        dialog.check()
    finally:
        flow.show_error = old
    assert dialog.settings is None and "fehlt.py" in errors[0]


def test_publish_dialog(qtbot, make_services, projects_root):
    from cockpit.ui import exe_flow
    services, project = project_with(make_services, projects_root)
    dialog = exe_flow.PublishDialog(project, "1.0.1", ["v1.0.0"], "Rechner.exe")
    qtbot.addWidget(dialog)
    assert dialog.version_edit.text() == "1.0.1" and dialog.suggest_button is None
    dialog.notes_edit.setPlainText("Schneller.")
    dialog.check()
    assert (dialog.version, dialog.notes) == ("1.0.1", "Schneller.")


@windows
def test_blocked_by_smart_app_control(tmp_path, monkeypatch):
    """Test von Phase 10 auf dem Rechner des Nutzers: Windows blockierte die neue Exe."""
    def blocked(*args, **kwargs):
        raise OSError(22, "Eine Anwendungssteuerungsrichtlinie hat diese Datei blockiert",
                      None, 4551)
    monkeypatch.setattr(exe.subprocess, "Popen", blocked)
    with pytest.raises(CockpitError, match="Intelligente App-Steuerung") as info:
        exe.start_test(tmp_path / "App.exe", 5)
    assert info.value.message.endswith("Die bisherige Exe bleibt.")


def blocked_build(make_services, projects_root, tmp_path, monkeypatch):
    services, project = project_with(make_services, projects_root)
    fake_exe(project.exe_dir, "Rechner.exe", "alt")
    monkeypatch.setattr(exe, "prepare_venv", lambda code_dir, on_line, cancel: Path("py.exe"))
    monkeypatch.setattr(exe.paths, "cache_dir", lambda: tmp_path / "cache")
    (tmp_path / "cache").mkdir(exist_ok=True)
    monkeypatch.setattr(exe, "pyinstaller_build", lambda code_dir, python, spec, work, on_line,
                        cancel: fake_exe(work / "dist", "Rechner.exe", "neu"))

    def blocked(path, seconds, self_test, cancel, windowed=False):
        raise exe.BlockedByWindows(exe.BLOCKED)
    monkeypatch.setattr(exe, "start_test", blocked)
    return services, project


def test_blocked_test_leaves_the_choice(make_services, projects_root, tmp_path, monkeypatch):
    """Wunsch aus Phase 10: Kann das Cockpit nicht prüfen, prüft der Nutzer selbst."""
    services, project = blocked_build(make_services, projects_root, tmp_path, monkeypatch)
    result = exe.build(project, exe.BuildSettings(name="Rechner"), lambda s: None,
                       lambda s: None)
    assert result.untested and result.built.read_text() == "neu"
    assert (project.exe_dir / "Rechner.exe").read_text() == "alt"       # noch nicht übernommen
    installed = exe.install_untested(project, result)
    assert installed.exe.read_text() == "neu" and not result.work.exists()
    assert exe.status_line(project, head="").endswith("nicht geprüft")


@pytest.mark.parametrize("answer", [True, False])
def test_build_dialog_asks_when_blocked(qtbot, make_services, projects_root, tmp_path,
                                        monkeypatch, answer):
    from cockpit.ui import exe_flow
    services, project = blocked_build(make_services, projects_root, tmp_path, monkeypatch)
    questions = []
    monkeypatch.setattr(exe_flow, "confirm", lambda parent, title, text, **kw:
                        questions.append(text) or answer)
    dialog = exe_flow.BuildDialog(services, project, exe.BuildSettings(name="Rechner"))
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.running, timeout=10000)
    assert questions[0].startswith("Das Cockpit kann die neue Exe nicht selbst prüfen")
    last = dialog.output.item(dialog.output.count() - 1).text()
    if answer:
        assert last.startswith("Exe erstellt, nicht geprüft und übernommen")
        assert (project.exe_dir / "Rechner.exe").read_text() == "neu"
    else:
        assert last == "Die neue Exe wurde verworfen. Die bisherige bleibt."
        assert (project.exe_dir / "Rechner.exe").read_text() == "alt"
