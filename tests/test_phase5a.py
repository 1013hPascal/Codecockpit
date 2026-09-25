"""Phase 5a: Git-Grundlage, Git-Identität, Projekte hinzufügen, Umstellen, Verknüpfen, Reparatur
nach dem Verschieben, Stand in der Projektliste, Repositories des Kontos.

Die Tests benutzen das echte Git mit Repositories in temporären Ordnern. Die "Plattform" ist ein
nacktes Repository (bare) im Dateisystem. Es gibt kein Netz.
"""
from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from cockpit.core import backups, git, identity, project_setup, project_status, venv_repair
from cockpit.core.actions import Target
from cockpit.core.errors import CockpitError
from cockpit.core.flows.questions import ScriptedAsker
from cockpit.core.git import RemoteAddress
from cockpit.core.projects import classify_folder
from cockpit.platforms.base import RemoteRepo, RepoRef
from cockpit.ui import common, project_actions
from cockpit.ui.main_window import MainWindow
from tests.conftest import FakePlatform, make_project, said

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

NAME, EMAIL = "Test Person", "1+tester@users.noreply.example"


# -- Hilfen ---------------------------------------------------------------------------------
def sh(cwd: Path, *args: str) -> str:
    """Git mit fester Identität auf der Befehlszeile (nur in Tests, ohne Geheimnisse)."""
    result = subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=t@example.org",
                             "-c", "init.defaultBranch=main", *args], cwd=cwd,
                            capture_output=True, text=True, check=True)
    return result.stdout


def make_remote(base: Path, name: str, files: dict[str, str] | None = None) -> Path:
    """Nacktes Repository mit einem ersten Commit, wie ein Repository auf der Plattform."""
    work = base / "arbeit" / name
    work.mkdir(parents=True)
    sh(work, "init", "-q")
    for filename, content in (files or {"main.py": "print('hallo')\n"}).items():
        (work / filename).write_text(content, encoding="utf-8")
    sh(work, "add", "-A")
    sh(work, "commit", "-q", "-m", "Erste Version")
    bare = base / "plattform" / f"{name}.git"
    bare.parent.mkdir(parents=True, exist_ok=True)
    sh(base, "clone", "-q", "--bare", str(work), str(bare))
    return bare


def clone_into(bare: Path, code_dir: Path) -> None:
    code_dir.parent.mkdir(parents=True, exist_ok=True)
    sh(code_dir.parent, "clone", "-q", str(bare), str(code_dir))


def stored_repo(services, account_id: int, bare: Path, name: str, pushed: str = ""):
    repo = RemoteRepo(RepoRef("tester", name), True, bare.as_uri(),
                      f"https://github.com/tester/{name}", pushed)
    services.remote_repos.replace(account_id, [repo])
    return next(r for r in services.remote_repos.all() if r.name == name)


@pytest.fixture
def account(make_services, account_adapter, monkeypatch):
    """Dienste mit einem Plattform-Konto. Die Plattform ist eine Attrappe ohne Zugangsdaten."""
    from cockpit.core.accounts import find_type
    from tests.conftest import FAKE_TOKEN, FakeVault
    from cockpit.core.secret import Secret
    monkeypatch.setattr(account_adapter, "display_name", "GitHub")
    services = make_services(vault=FakeVault())
    acc = services.accounts.create(find_type("platform", account_adapter.kind), "Test", {
        "username": "tester", "url": "https://github.com", "team": "",
        "token": Secret(FAKE_TOKEN)})
    platform = FakePlatform()
    services.platforms[acc.id] = platform
    return services, acc, platform


# -- Adressen -------------------------------------------------------------------------------
@pytest.mark.parametrize("url", [
    "https://github.com/1013hPascal/Tagebuch.git",
    "https://github.com/1013hPascal/Tagebuch",
    "https://www.github.com/1013hPascal/Tagebuch/",
    "git@github.com:1013hPascal/Tagebuch.git",
    "ssh://git@github.com/1013hPascal/Tagebuch.git",
])
def test_parse_remote(url):
    address = git.parse_remote(url)
    assert address == RemoteAddress("github.com", "1013hPascal", "Tagebuch")
    assert address.key == "github.com/1013hpascal/tagebuch"


def test_parse_remote_rejects_nonsense():
    assert git.parse_remote("") is None
    assert git.parse_remote("kein repository") is None
    assert git.parse_remote(r"C:\Ordner") is None


def test_git_errors_are_explained_in_simple_german():
    result = subprocess.CompletedProcess(["push", "origin"], 128, "",
                                         "fatal: Authentication failed for 'https://x'")
    assert git.explain(result).message.startswith("Die Anmeldung bei der Plattform")
    result = subprocess.CompletedProcess(["clone"], 128, "", "fatal: repository 'x' not found")
    assert "nicht gefunden" in git.explain(result).message
    result = subprocess.CompletedProcess(["status"], 128, "", "fatal: not a git repository")
    assert git.explain(result).message == "Der Ordner ist kein Git-Repository."


def test_git_never_asks_for_a_password(monkeypatch):
    env = git._environment({"X": "1"})
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GCM_INTERACTIVE"] == "never"
    assert env["X"] == "1"


# -- Stand eines Repositories ---------------------------------------------------------------
def test_status_of_folder_without_git(tmp_path):
    state = git.status(tmp_path)
    assert not state.is_repo


def test_status_counts_changes_and_unpushed_commits(tmp_path):
    bare = make_remote(tmp_path, "Tagebuch")
    code = tmp_path / "Tagebuch" / "Code"
    clone_into(bare, code)
    state = git.status(code)
    assert state.is_repo and state.branch == "main" and state.upstream == "origin/main"
    assert state.remote_url.endswith("Tagebuch.git")
    assert state.changed == [] and git.pending_files(code, state) == 0
    assert state.last_upload                                  # Datum des Commits auf der Plattform
    (code / "main.py").write_text("print('neu')\n", encoding="utf-8")
    (code / "neu.py").write_text("x = 1\n", encoding="utf-8")
    state = git.status(code)
    assert sorted(state.changed) == ["main.py", "neu.py"]
    assert git.pending_files(code, state) == 2
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Neu")
    (code / "noch.py").write_text("y = 2\n", encoding="utf-8")
    state = git.status(code)
    assert state.ahead == 1
    assert git.pending_files(code, state) == 3                # 2 im Commit, 1 geändert


def test_status_handles_renamed_files(tmp_path):
    bare = make_remote(tmp_path, "Umbenannt", {"a.py": "print(1)\n" * 20})
    code = tmp_path / "Umbenannt" / "Code"
    clone_into(bare, code)
    sh(code, "mv", "a.py", "b.py")
    state = git.status(code)
    assert state.changed == ["b.py"]


# -- Git-Identität --------------------------------------------------------------------------
def test_identity_is_set_only_in_the_repository(tmp_path):
    code = tmp_path / "Code"
    code.mkdir()
    assert identity.state(code, NAME, EMAIL) is identity.IdentityState.NO_REPO
    git.init(code)
    assert identity.state(code, "", "") is identity.IdentityState.NOT_SET
    assert identity.state(code, NAME, EMAIL) is identity.IdentityState.MISSING
    assert identity.ensure(code, "Test", NAME, EMAIL, ScriptedAsker())
    assert git.identity(code) == (NAME, EMAIL)
    config = (code / ".git" / "config").read_text(encoding="utf-8")
    assert NAME in config and EMAIL in config                  # lokal, nicht global
    assert identity.state(code, NAME, EMAIL) is identity.IdentityState.SAME


def test_different_identity_is_kept_unless_confirmed(tmp_path):
    code = tmp_path / "Code"
    code.mkdir()
    git.init(code)
    git.set_identity(code, "Alt", "alt@example.org")
    asker = ScriptedAsker(False)
    assert not identity.ensure(code, "Tagebuch", NAME, EMAIL, asker)
    assert git.identity(code) == ("Alt", "alt@example.org")
    question = asker.questions[0]
    assert question.no == "Vorhandene behalten" and not question.default_yes
    assert question.text.startswith("Tagebuch hat eine andere Git-Identität: Alt, "
                                    "alt@example.org.")
    assert identity.ensure(code, "Tagebuch", NAME, EMAIL, ScriptedAsker(True))
    assert git.identity(code) == (NAME, EMAIL)


def test_escape_keeps_the_identity(tmp_path):
    code = tmp_path / "Code"
    code.mkdir()
    git.init(code)
    git.set_identity(code, "Alt", "alt@example.org")
    assert not identity.ensure(code, "X", NAME, EMAIL, ScriptedAsker(None))
    assert git.identity(code) == ("Alt", "alt@example.org")


# -- Projekte hinzufügen, umstellen, verknüpfen, neuer Ort ----------------------------------
def test_classify_folder(projects_root, tmp_path):
    project = make_project(projects_root, "Tagebuch")
    assert classify_folder(project) == ("project", project)
    assert classify_folder(project / "Code") == ("project", project)
    other = tmp_path / "irgendwo"
    other.mkdir()
    assert classify_folder(other) == ("other", other)


def test_convert_moves_folder_into_new_project_dir(make_services, projects_root, tmp_path):
    services = make_services()
    folder = tmp_path / "alt" / "Rechner"
    folder.mkdir(parents=True)
    (folder / "main.py").write_text("print(1)\n", encoding="utf-8")
    project, moved = services.projects.convert(folder, projects_root)
    assert moved
    assert not folder.exists()
    assert (projects_root / "Rechner" / "Code" / "main.py").read_text() == "print(1)\n"
    assert project.name == "Rechner" and project.code_dir == projects_root / "Rechner" / "Code"


def test_convert_refuses_existing_target(make_services, projects_root, tmp_path):
    services = make_services()
    (projects_root / "Rechner").mkdir()
    folder = tmp_path / "Rechner"
    folder.mkdir()
    with pytest.raises(CockpitError, match="gibt es schon"):
        services.projects.convert(folder, projects_root)
    assert folder.exists()


def test_convert_copies_across_drives(make_services, projects_root, tmp_path, monkeypatch):
    from cockpit.core import projects as projects_module
    monkeypatch.setattr(projects_module, "same_drive", lambda a, b: False)
    services = make_services()
    folder = tmp_path / "Rechner"
    folder.mkdir()
    (folder / "a.py").write_text("1\n", encoding="utf-8")
    project, moved = services.projects.convert(folder, projects_root)
    assert not moved
    assert (folder / "a.py").exists()                          # alter Ordner unverändert
    assert (project.code_dir / "a.py").exists()


def test_linked_project_keeps_its_folders(make_services, tmp_path):
    services = make_services()
    code = tmp_path / "Firma" / "repo"
    code.mkdir(parents=True)
    exe = tmp_path / "Firma" / "build"
    exe.mkdir()
    project = services.projects.add_linked(code, exe)
    assert project.linked and project.code_dir == code and project.exe_dir == exe
    assert project.has_exe_dir
    without = services.projects.add_linked(tmp_path / "Firma" / "build")
    assert without.exe_dir is None and not without.has_exe_dir
    assert services.projects.add_linked(code).id == project.id     # nicht doppelt


def test_relocate_project_and_linked_project(make_services, projects_root, tmp_path):
    services = make_services()
    make_project(projects_root, "Tagebuch")
    project = services.projects.add(projects_root / "Tagebuch")
    new_place = tmp_path / "neu"
    new_place.mkdir()
    os.rename(projects_root / "Tagebuch", new_place / "Tagebuch")
    assert not services.projects.get(project.id).folder_found
    moved = services.projects.relocate(project, new_place / "Tagebuch" / "Code")
    assert moved.folder_found and moved.project_dir == new_place / "Tagebuch"
    with pytest.raises(CockpitError, match="keinen Unterordner Code"):
        services.projects.relocate(moved, tmp_path)
    code = tmp_path / "repo"
    code.mkdir()
    linked = services.projects.add_linked(code)
    other = tmp_path / "repo2"
    other.mkdir()
    assert services.projects.relocate(linked, other).code_dir == other


def test_relocate_refuses_folder_of_other_project(make_services, projects_root):
    services = make_services()
    make_project(projects_root, "A")
    make_project(projects_root, "B")
    a = services.projects.add(projects_root / "A")
    services.projects.add(projects_root / "B")
    with pytest.raises(CockpitError, match="gehört schon zum Projekt B"):
        services.projects.relocate(a, projects_root / "B")


# -- Repositories der Plattform -------------------------------------------------------------
def test_remote_repos_first_fetch_marks_nothing_as_new(account):
    services, acc, _ = account
    one = RemoteRepo(RepoRef("tester", "Eins"), True, "https://github.com/tester/Eins.git",
                     "https://github.com/tester/Eins", "2026-09-20T10:00:00Z")
    two = RemoteRepo(RepoRef("tester", "Zwei"), False, "https://github.com/tester/Zwei.git",
                     "https://github.com/tester/Zwei", "2026-09-22T10:00:00Z")
    assert services.remote_repos.replace(acc.id, [one]) == []
    new = services.remote_repos.replace(acc.id, [one, two])
    assert [r.name for r in new] == ["Zwei"]
    assert [r.name for r in services.remote_repos.all()] == ["Zwei", "Eins"]
    assert services.remote_repos.all()[0].host == "github.com"
    local = {RemoteAddress("github.com", "Tester", "eins").key}
    assert [r.name for r in services.remote_repos.only_remote(local)] == ["Zwei"]


def test_remote_repos_disappear_with_the_account(account):
    services, acc, _ = account
    repo = RemoteRepo(RepoRef("tester", "Eins"), True, "u", "https://github.com/tester/Eins")
    services.remote_repos.replace(acc.id, [repo])
    services.accounts.delete(acc)
    assert services.remote_repos.all() == []


def test_github_lists_own_repositories(monkeypatch):
    import httpx
    from cockpit.core.secret import Secret
    from cockpit.platforms.github import GitHubPlatform
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=[
            {"owner": {"login": "1013hPascal"}, "name": "Alt", "private": True,
             "clone_url": "https://github.com/1013hPascal/Alt.git",
             "html_url": "https://github.com/1013hPascal/Alt", "pushed_at": "2025-01-01T00:00:00Z"},
            {"owner": {"login": "1013hPascal"}, "name": "Neu", "private": False,
             "clone_url": "https://github.com/1013hPascal/Neu.git",
             "html_url": "https://github.com/1013hPascal/Neu", "pushed_at": "2026-09-01T00:00:00Z"},
        ])

    monkeypatch.setattr(GitHubPlatform, "transport", httpx.MockTransport(handler))
    repos = GitHubPlatform("https://github.com", Secret("gho_ErfundenerToken123")).repositories()
    assert [r.ref.name for r in repos] == ["Neu", "Alt"]
    assert repos[1].private and not repos[0].private
    assert seen[0].url.path == "/user/repos"
    assert seen[0].url.params["affiliation"] == "owner"


# -- Herunterladen und verbinden ------------------------------------------------------------
def test_download_clones_into_projects_root(account, projects_root, tmp_path):
    services, acc, _ = account
    bare = make_remote(tmp_path, "Rechner")
    repo = stored_repo(services, acc.id, bare, "Rechner", "2026-09-20T10:00:00Z")
    project = project_setup.download(services, repo, projects_root)
    assert (projects_root / "Rechner" / "Code" / "main.py").exists()
    assert project.account_id == acc.id
    assert project.remote.name == "Rechner"
    assert project.last_updated.startswith("2026-09-20")


def test_download_refuses_non_empty_target(account, projects_root, tmp_path):
    services, acc, _ = account
    bare = make_remote(tmp_path, "Rechner")
    repo = stored_repo(services, acc.id, bare, "Rechner")
    make_project(projects_root, "Rechner")
    with pytest.raises(CockpitError, match="nicht leer"):
        project_setup.download(services, repo, projects_root)


def test_connect_keeps_files_and_shows_differences(account, projects_root, tmp_path):
    services, acc, _ = account
    bare = make_remote(tmp_path, "Notizen", {"a.py": "alt\n", "b.py": "b\n"})
    code = projects_root / "Notizen" / "Code"
    code.mkdir(parents=True)
    (code / "a.py").write_text("geändert\n", encoding="utf-8")
    (code / "b.py").write_text("b\n", encoding="utf-8")
    project = services.projects.add(projects_root / "Notizen")
    branch = project_setup.connect(services, project, bare.as_uri(), acc.id)
    assert branch == "main"
    assert (code / "a.py").read_text(encoding="utf-8") == "geändert\n"   # unverändert
    state = git.status(code)
    assert state.upstream == "origin/main" and state.changed == ["a.py"]
    assert services.projects.get(project.id).account_id == acc.id


def test_connect_refuses_existing_repository(account, tmp_path):
    services, acc, _ = account
    code = tmp_path / "X" / "Code"
    code.mkdir(parents=True)
    git.init(code)
    project = services.projects.add(tmp_path / "X")
    with pytest.raises(CockpitError, match="schon mit Git verbunden"):
        project_setup.connect(services, project, "https://github.com/a/b.git", acc.id)


# -- Stand und Zeilen der Projektliste ------------------------------------------------------
def test_lines_for_projects(make_services, projects_root, tmp_path):
    services = make_services()
    bare = make_remote(tmp_path, "Tagebuch")
    clone_into(bare, projects_root / "Tagebuch" / "Code")
    make_project(projects_root, "Bildbeschreiber")
    services.projects.scan(projects_root)
    projects = {p.name: p for p in services.projects.all()}
    status = project_status.compute(projects["Tagebuch"])
    project_status.remember(services.projects, projects["Tagebuch"], status)
    tagebuch = services.projects.get(projects["Tagebuch"].id)
    date = datetime.fromisoformat(tagebuch.last_updated).strftime("%d.%m.%Y")
    assert project_status.project_line(tagebuch, status) == f"Tagebuch, aktualisiert am {date}"
    assert project_status.code_line(status) == "Code, alles hochgeladen"
    (tagebuch.code_dir / "neu.py").write_text("1\n", encoding="utf-8")
    status = project_status.compute(tagebuch)
    assert project_status.project_line(tagebuch, status) == (
        f"Tagebuch, aktualisiert am {date}, 1 Datei noch nicht hochgeladen")
    assert project_status.code_line(status) == "Code, 1 Datei noch nicht hochgeladen"
    sh(tagebuch.code_dir, "switch", "-q", "-c", "suche-pdfs")
    status = project_status.compute(tagebuch)
    assert project_status.code_line(status).startswith("Code, Branch suche-pdfs, ")
    bild = projects["Bildbeschreiber"]
    status = project_status.compute(bild)
    assert project_status.project_line(bild, status) == "Bildbeschreiber, noch nicht auf GitHub"
    assert project_status.code_line(status) == "Code, noch nicht auf GitHub"


def test_line_for_missing_folder_and_remote_only(make_services, projects_root):
    services = make_services()
    make_project(projects_root, "Notizen")
    project = services.projects.add(projects_root / "Notizen")
    import shutil
    shutil.rmtree(projects_root / "Notizen")
    project = services.projects.get(project.id)
    assert project_status.project_line(project, project_status.compute(project)) == \
        "Notizen, Ordner nicht gefunden"
    assert project_status.remote_line("Rechner", "2026-09-10T08:00:00Z") == \
        "Rechner, nur auf GitHub, aktualisiert am 10.09.2026"


# -- Virtuelle Umgebung ---------------------------------------------------------------------
def fake_venv(code: Path, recorded: Path, python: Path) -> None:
    venv = code / ".venv"
    (venv / "Scripts").mkdir(parents=True)
    (venv / "pyvenv.cfg").write_text(
        f"home = {python.parent}\nversion = 3.14.6\nexecutable = {python}\n"
        f"command = {python} -m venv {recorded}\n", encoding="utf-8")
    (venv / "Scripts" / "activate.bat").write_text(
        f'@echo off\nset "VIRTUAL_ENV={recorded}"\n', encoding="utf-8")


def test_venv_check(tmp_path):
    python = tmp_path / "Python" / "python.exe"
    python.parent.mkdir()
    python.write_text("", encoding="utf-8")
    code = tmp_path / "A" / "Code"
    code.mkdir(parents=True)
    assert not venv_repair.check(code).exists
    fake_venv(code, code / ".venv", python)
    assert venv_repair.check(code) == venv_repair.VenvState(True, False, "", str(python),
                                                            "3.14.6")
    other = tmp_path / "B" / "Code"
    other.mkdir(parents=True)
    fake_venv(other, tmp_path / "alt" / "Code" / ".venv", python)
    state = venv_repair.check(other)
    assert state.broken and state.reason == "Das Projekt wurde verschoben."
    python.unlink()
    assert venv_repair.check(code).reason == "Das Python, mit dem sie angelegt wurde, fehlt."


def test_venv_repair_moves_old_venv_into_backup(tmp_path, monkeypatch):
    python = tmp_path / "python.exe"
    python.write_text("", encoding="utf-8")
    code = tmp_path / "B" / "Code"
    code.mkdir(parents=True)
    (code / "requirements.txt").write_text("httpx\n", encoding="utf-8")
    fake_venv(code, tmp_path / "alt" / ".venv", python)
    commands = []
    monkeypatch.setattr(venv_repair, "_run", lambda command, cwd, cancel: commands.append(
        command[1:] if command[0] == str(python) else command[-4:]))
    steps = []
    backup = venv_repair.repair(code, "B", lambda s, t, n: steps.append(f"{s} von {t}: {n}"))
    assert not (code / ".venv").exists()
    assert (backup / "pyvenv.cfg").exists()
    assert backup.parent.parent == backups.backups_dir()
    assert steps == ["1 von 3: Alte Umgebung wird gesichert",
                     "2 von 3: Neue Umgebung wird angelegt",
                     "3 von 3: Pakete aus requirements.txt werden installiert"]
    assert commands[0] == ["-m", "venv", ".venv"]
    assert commands[1] == ["pip", "install", "-r", "requirements.txt"]


def test_venv_repair_needs_python(tmp_path, monkeypatch):
    code = tmp_path / "Code"
    code.mkdir()
    fake_venv(code, tmp_path / "alt" / ".venv", tmp_path / "fehlt" / "python.exe")
    monkeypatch.setattr(venv_repair.shutil, "which", lambda name: None)
    with pytest.raises(CockpitError, match="Python 3.14 wurde nicht gefunden"):
        venv_repair.repair(code, "X", lambda *a: None)
    assert (code / ".venv").exists()                           # nichts angefasst


# -- Sicherheitskopien ----------------------------------------------------------------------
def test_old_backups_are_removed_after_30_days():
    old = backups.new_backup_dir("Alt", "venv")
    new = backups.new_backup_dir("Neu", "venv")
    foreign = backups.backups_dir() / "von Hand angelegt"
    foreign.mkdir()
    later = datetime.now() + timedelta(days=31)
    os.rename(old, backups.backups_dir() / ("2000-01-01_00-00-00" + old.name[19:]))
    assert backups.remove_old() == 1
    assert new.exists() and foreign.exists()
    assert backups.remove_old(later) == 1                      # jetzt auch die neue
    assert foreign.exists()                                    # fremde Ordner nie


# -- Oberfläche -----------------------------------------------------------------------------
@pytest.fixture
def live(qtbot, projects_root):
    """Hauptfenster mit Abfrage des Stands im Hintergrund."""
    created = []

    def factory(services):
        win = MainWindow(services)
        qtbot.addWidget(win)
        win.show()
        win.activateWindow()
        qtbot.waitUntil(win.isActiveWindow, timeout=3000)
        win.initial_focus()
        created.append(win)
        wait_idle(qtbot, win)
        return win

    yield factory
    for win in created:
        win.close()


def wait_idle(qtbot, win):
    qtbot.waitUntil(lambda: win.status_task is None and win.remote_task is None
                    and not win.controller.busy, timeout=15000)


def row_texts(win) -> list[str]:
    return win.project_list.texts()


def test_project_list_shows_status_without_moving_focus(live, qtbot, account, projects_root,
                                                       tmp_path):
    from cockpit.ui.announcer import announcer
    services, acc, _ = account
    bare = make_remote(tmp_path, "Tagebuch")
    clone_into(bare, projects_root / "Tagebuch" / "Code")
    make_project(projects_root, "Bildbeschreiber")
    win = live(services)
    texts = row_texts(win)
    assert any(t.startswith("Tagebuch, aktualisiert am ") for t in texts)
    assert "Bildbeschreiber, noch nicht auf GitHub" in texts
    tagebuch = next(p for p in services.projects.all() if p.name == "Tagebuch")
    win.project_list.select(Target.CODE, tagebuch.id)
    assert win.project_list.currentItem().text() == "Code, alles hochgeladen"
    (tagebuch.code_dir / "neu.py").write_text("1\n", encoding="utf-8")
    announced = len(announcer.messages)
    win.refresh_status([tagebuch.id])
    qtbot.waitUntil(lambda: win.project_list.currentItem().text()
                    == "Code, 1 Datei noch nicht hochgeladen", timeout=10000)
    assert win.project_list.current_target() == (Target.CODE, tagebuch.id)   # Fokus bleibt
    assert len(announcer.messages) == announced                              # keine Ansage


def test_remote_only_repo_is_listed_and_enter_downloads_it(live, qtbot, account, projects_root,
                                                           tmp_path):
    from cockpit.platforms.base import GitCredentials
    services, acc, platform = account
    bare = make_remote(tmp_path, "Rechner")
    # Wie auf GitHub: Die Adresse ist https://github.com/..., Git holt aber aus dem Test-Ordner.
    # Das geht über dieselben Umgebungsvariablen, mit denen sonst der Zugang an Git geht.
    platform.git_credentials = lambda: GitCredentials(False, {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": f"url.{bare.parent.as_uri()}/.insteadOf",
        "GIT_CONFIG_VALUE_0": "https://github.com/tester/"})
    platform.remote = [RemoteRepo(RepoRef("tester", "Rechner"), True,
                                  "https://github.com/tester/Rechner.git",
                                  "https://github.com/tester/Rechner", "2026-09-10T08:00:00Z")]
    services.remote_repos.replace(acc.id, platform.remote)
    services.settings.update(git_name=NAME, git_email=EMAIL)
    win = live(services)
    assert "Rechner, nur auf GitHub, aktualisiert am 10.09.2026" in row_texts(win)
    repo = services.remote_repos.all()[0]
    assert win.project_list.select(Target.REMOTE_REPO, repo.id)
    assert [e.label for e in win.current_entries()] == ["Herunterladen", "Auf GitHub öffnen"]
    qtbot.keyClick(win.project_list, Qt.Key.Key_Return)
    wait_idle(qtbot, win)
    qtbot.waitUntil(lambda: said("Rechner heruntergeladen."), timeout=10000)
    project = next(p for p in services.projects.all() if p.name == "Rechner")
    assert (project.code_dir / "main.py").exists()
    assert git.identity(project.code_dir) == (NAME, EMAIL)
    assert win.project_list.current_target() == (Target.PROJECT, project.id)
    assert not any("nur auf GitHub" in t for t in row_texts(win))


def test_refresh_remote_downloads_new_repos_when_switched_on(live, qtbot, account, projects_root,
                                                            tmp_path):
    services, acc, platform = account
    services.remote_repos.replace(acc.id, [])                  # erster Abruf schon erledigt
    bare = make_remote(tmp_path, "Neu")
    platform.remote = [RemoteRepo(RepoRef("tester", "Neu"), True, bare.as_uri(),
                                  "https://github.com/tester/Neu", "2026-09-24T08:00:00Z")]
    services.settings.update(auto_clone_new=True)
    win = live(services)
    win.refresh_remote()
    wait_idle(qtbot, win)
    qtbot.waitUntil(lambda: said("Neu heruntergeladen."), timeout=10000)
    assert (projects_root / "Neu" / "Code" / "main.py").exists()


def test_refresh_remote_without_auto_download(live, qtbot, account, projects_root, tmp_path):
    services, acc, platform = account
    services.remote_repos.replace(acc.id, [])
    platform.remote = [RemoteRepo(RepoRef("tester", "Neu"), True, "file:///x",
                                  "https://github.com/tester/Neu", "2026-09-24T08:00:00Z")]
    win = live(services)
    win.refresh_remote()
    wait_idle(qtbot, win)
    assert "Neu, nur auf GitHub, aktualisiert am 24.09.2026" in row_texts(win)
    assert not (projects_root / "Neu").exists()


def test_settings_have_auto_download_switch_off_by_default(make_services):
    services = make_services()
    assert services.settings.load().auto_clone_new is False
    from cockpit.core.settings import setting_fields
    labels = [f.label for f in setting_fields()]
    assert "Neue Repositories automatisch herunterladen" in labels


def test_add_existing_project_folder(live, qtbot, make_services, projects_root, tmp_path,
                                     monkeypatch):
    services = make_services()
    (tmp_path / "leer").mkdir()
    services.settings.update(projects_root=str(tmp_path / "leer"))
    win = live(services)
    folder = make_project(tmp_path, "Extern")
    monkeypatch.setattr(project_actions, "pick_folder", lambda *a: folder / "Code")
    win.controller.add_local()
    assert said("Extern hinzugefügt.")
    project = services.projects.find_by_dir(folder)
    assert win.project_list.current_target() == (Target.PROJECT, project.id)
    win.controller.add_local()
    assert said("Extern ist schon in der Liste.")


def test_add_other_folder_offers_convert_link_and_cancel(live, qtbot, make_services,
                                                         projects_root, tmp_path, monkeypatch):
    services = make_services()
    win = live(services)
    folder = tmp_path / "irgendwo" / "Rechner"
    folder.mkdir(parents=True)
    monkeypatch.setattr(project_actions, "pick_folder", lambda *a: folder)
    asked = []

    def buttons(parent, title, text, labels, default, escape):
        asked.append((labels, default, escape, text))
        return answers.pop(0)

    monkeypatch.setattr(project_actions, "ask_buttons", buttons)
    monkeypatch.setattr(project_actions, "confirm", lambda *a, **k: True)
    answers = [2]
    win.controller.add_local()                              # Abbrechen
    assert services.projects.all() == [] and folder.exists()
    labels, default, escape, text = asked[0]
    assert labels == ["In den Projekte-Hauptordner verschieben …", "Am Ort lassen …",
                      "Abbrechen"]
    assert default == escape == 2                              # sichere Vorgabe
    assert text.startswith("Der Ordner Rechner hat keinen Unterordner Code.")
    answers = [0]
    win.controller.add_local()                              # Umstellen
    assert (projects_root / "Rechner" / "Code").is_dir() and not folder.exists()
    assert said("Rechner hinzugefügt.")


def test_link_without_exe(live, qtbot, make_services, tmp_path, monkeypatch):
    services = make_services()
    win = live(services)
    folder = tmp_path / "Firma"
    folder.mkdir()
    monkeypatch.setattr(project_actions, "pick_folder", lambda *a: folder)
    monkeypatch.setattr(project_actions, "ask_buttons", lambda *a, **k: 1)
    monkeypatch.setattr(project_actions, "confirm", lambda *a, **k: False)   # ohne Exe-Ordner
    win.controller.add_local()
    project = services.projects.all()[0]
    assert project.linked and project.exe_dir is None and project.code_dir == folder


def test_relocate_only_for_missing_folder(live, qtbot, make_services, projects_root, tmp_path,
                                          monkeypatch):
    make_project(projects_root, "Notizen")
    services = make_services()
    win = live(services)
    project = services.projects.all()[0]
    win.project_list.select(Target.PROJECT, project.id)
    assert "Neuen Ort angeben …" not in [e.label for e in win.current_entries()]
    new_place = tmp_path / "neu"
    new_place.mkdir()
    os.rename(projects_root / "Notizen", new_place / "Notizen")
    win.reload_projects()
    wait_idle(qtbot, win)
    win.project_list.select(Target.PROJECT, project.id)
    entries = win.current_entries()
    assert entries[0].label == "Projekt neu einlesen"
    assert entries[1].label == "Neuen Ort angeben …"
    monkeypatch.setattr(project_actions, "pick_folder", lambda *a: new_place / "Notizen")
    win.run_entry(entries[1])
    assert said("Neuer Ort für Notizen gespeichert.")
    assert services.projects.get(project.id).folder_found


def test_connect_and_venv_actions_only_when_needed(live, qtbot, account, projects_root,
                                                   tmp_path, monkeypatch):
    services, acc, _ = account
    make_project(projects_root, "OhneGit")
    bare = make_remote(tmp_path, "MitGit")
    clone_into(bare, projects_root / "MitGit" / "Code")
    win = live(services)
    by_name = {p.name: p for p in services.projects.all()}
    win.project_list.select(Target.CODE, by_name["OhneGit"].id)
    labels = [e.label for e in win.current_entries()]
    assert "Mit vorhandenem Repository verbinden …" in labels
    assert "Virtuelle Umgebung neu anlegen …" not in labels
    win.project_list.select(Target.CODE, by_name["MitGit"].id)
    assert "Mit vorhandenem Repository verbinden …" not in [
        e.label for e in win.current_entries()]


def test_connect_action_runs_in_background(live, qtbot, account, projects_root, tmp_path,
                                           monkeypatch):
    services, acc, _ = account
    bare = make_remote(tmp_path, "OhneGit")
    stored_repo(services, acc.id, bare, "OhneGit")
    make_project(projects_root, "OhneGit")
    win = live(services)
    project = next(p for p in services.projects.all() if p.name == "OhneGit")
    win.project_list.select(Target.CODE, project.id)
    entry = next(e for e in win.current_entries()
                 if e.label == "Mit vorhandenem Repository verbinden …")
    chosen = []
    monkeypatch.setattr(project_actions, "choose_from_list",
                        lambda parent, title, name, items, current: chosen.append(
                            (items, current)) or current)
    monkeypatch.setattr(project_actions, "confirm", lambda *a, **k: True)
    win.run_entry(entry)
    wait_idle(qtbot, win)
    qtbot.waitUntil(lambda: said("OhneGit ist verbunden, Branch main."), timeout=10000)
    assert chosen[0] == (["Adresse eingeben …", "OhneGit, tester"], 1)
    assert git.is_repo(project.code_dir)


def test_list_choice_dialog_is_accessible(qtbot):
    dialog = common.ListChoiceDialog("Titel", "Repositories", ["A", "B"], 1)
    qtbot.addWidget(dialog)
    assert dialog.list.accessibleName() == "Repositories"
    assert dialog.chosen == 1
    assert dialog.initial_focus_widget is dialog.list


def test_action_list_keeps_selection_on_background_change(live, qtbot, make_services,
                                                          projects_root):
    make_project(projects_root, "A", exe=True)
    services = make_services()
    win = live(services)
    project = services.projects.all()[0]
    win.project_list.select(Target.CODE, project.id)
    before = win.actions_list.texts()
    win.actions_list.setCurrentRow(len(before) - 1)
    win.refresh_actions(keep_selection=True)
    assert win.actions_list.currentRow() == len(before) - 1


def test_remove_tree_deletes_read_only_files(tmp_path):
    """Git legt schreibgeschützte Dateien an. Früher blieb deshalb der alte Ordner der Testdaten
    liegen, und start_testdaten.bat startete nicht mehr."""
    import stat
    folder = tmp_path / "alt" / ".git" / "objects"
    folder.mkdir(parents=True)
    locked = folder / "ab12"
    locked.write_text("x", encoding="utf-8")
    os.chmod(locked, stat.S_IREAD)
    backups.remove_tree(tmp_path / "alt")
    assert not (tmp_path / "alt").exists()


def test_testdata_can_be_prepared_twice(tmp_path, monkeypatch):
    from cockpit import testdata
    monkeypatch.setenv("CODECOCKPIT_HOME", str(tmp_path / "home"))
    base = tmp_path / "Testdaten"
    testdata.prepare(base)
    assert (base / "Projekte" / "Tagebuch" / "Code" / ".git").is_dir()
    testdata.prepare(base)
    assert not base.with_name("Testdaten-alt").exists()
    assert (base / "Andere Ordner" / "Vereinsseite" / "Code" / ".git").is_dir()


def test_identity_action_shows_and_sets_identity(live, qtbot, make_services, projects_root,
                                                 monkeypatch):
    code = make_project(projects_root, "Verein") / "Code"
    git.init(code)
    git.set_identity(code, "Alt", "alt@example.org")
    services = make_services()
    services.settings.update(git_name=NAME, git_email=EMAIL)
    win = live(services)
    project = services.projects.all()[0]
    win.project_list.select(Target.CODE, project.id)
    entry = next(e for e in win.current_entries() if e.label == "Git-Identität …")
    asked = []
    monkeypatch.setattr(project_actions, "confirm",
                        lambda parent, title, text, **k: asked.append((text, k)) or True)
    win.run_entry(entry)
    text, buttons = asked[0]
    assert text.startswith("Eingetragen: Alt, alt@example.org. In den Grundeinstellungen steht:")
    assert buttons["no"] == "Vorhandene behalten"
    assert git.identity(code) == (NAME, EMAIL)
    shown = []
    monkeypatch.setattr(project_actions, "show_info", lambda p, t, text: shown.append(text))
    win.run_entry(entry)
    assert shown == [f"{NAME}, {EMAIL}. Das ist die Identität aus den Grundeinstellungen."]


def test_identity_action_only_for_repositories(live, qtbot, make_services, projects_root):
    make_project(projects_root, "OhneGit")
    services = make_services()
    win = live(services)
    win.project_list.select(Target.CODE, services.projects.all()[0].id)
    assert "Git-Identität …" not in [e.label for e in win.current_entries()]
