"""Paketübersicht: Fenster, Menü, Aufräumen, Tauschen in Projekten, Sicherheitslücken und die
Liste für einen neuen Rechner (Wunsch des Nutzers vom 21.10.2026). Alle Programme sind
nachgebaut."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from cockpit.core import git
from cockpit.features.packages import (base, catalog, cleanup, models, osv, project_update,
                                       transfer, usage, web)
from cockpit.features.packages.base import MODEL, PIP, WINGET, Package
from cockpit.features.packages.manifest import MANIFEST
from tests.conftest import make_project, said

needs_git = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


def pip_packages() -> list[Package]:
    return [Package(PIP, "requests", "2.31.0", key="requests", place="Python 3.14",
                    location=Path("python.exe"), latest="2.32.3", checked=True,
                    added=datetime(2026, 10, 1)),
            Package(PIP, "six", "1.16.0", key="six", place="Projekt Tagebuch", owner="Tagebuch",
                    cockpit=True, location=Path("python.exe"), checked=True,
                    added=datetime(2026, 10, 5))]


@pytest.fixture
def fake_catalog(monkeypatch):
    calls = []
    monkeypatch.setattr(catalog, "sources", lambda: [catalog.SourceInfo(PIP, True),
                                                     catalog.SourceInfo(WINGET, False,
                                                                        "winget fehlt")])
    monkeypatch.setattr(catalog, "load", lambda source, projects, db, cancel=None:
                        [Package(**{**p.__dict__}) for p in pip_packages()])

    def check(source, packages, projects, cancel=None):
        calls.append(("check", source))
    monkeypatch.setattr(catalog, "check", check)
    monkeypatch.setattr(usage, "mark", lambda *a, **k: None)
    return calls


def opened(qtbot, make_services, monkeypatch):
    from cockpit.ui import package_dialogs
    services = make_services([MANIFEST])
    dialog = package_dialogs.SourcesDialog(services)
    qtbot.addWidget(dialog)
    dialog.refresh_all()                        # gelesen wird nur auf Wunsch (26.10.2026)
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10000)
    return services, dialog


def test_sources_dialog_reads_and_checks(qtbot, make_services, fake_catalog, monkeypatch):
    _services, dialog = opened(qtbot, make_services, monkeypatch)
    assert dialog.windowTitle() == "Paketübersicht"
    assert dialog.list.accessibleName() == "Quellen"
    assert dialog.filter.accessibleName() == "Filtern: Alle"
    assert dialog.list.item(0).text() == "Paketübersicht aktualisieren"
    assert dialog.list.item(1).text().startswith("Speicherplatz:")
    assert dialog.list.item(2).text() == "Kritisch: keine bekannte Sicherheitslücke"
    assert dialog.list.item(3).text() == ("Python-Bibliotheken (pip), 2 Einträge, 1 veraltet")
    assert dialog.list.item(4).text() == ("Programme aus winget, nicht verfügbar: winget fehlt")
    assert said("Prüfung fertig: 1 Paket ist veraltet.")
    dialog.set_filter(base.COCKPIT)
    assert dialog.list.item(3).text() == "Python-Bibliotheken (pip), 1 Eintrag, alles aktuell"
    assert not dialog.cleanup_button.isVisibleTo(dialog)            # ohne Ablauf


def test_packages_dialog_buttons_and_update(qtbot, make_services, fake_catalog, monkeypatch,
                                            played):
    from cockpit.ui import package_dialogs
    _services, sources = opened(qtbot, make_services, monkeypatch)
    dialog = package_dialogs.PackagesDialog(sources, PIP)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Python-Bibliotheken (pip): 2 Einträge"
    assert dialog.list.accessibleName() == "Pakete" and dialog.search.accessibleName() == "Suchen"
    assert dialog.list.item(0).text().startswith("six 1.16.0, aktuell")     # neueste oben
    assert not dialog.update_button.isVisibleTo(dialog)
    dialog.list.setCurrentRow(1)
    assert dialog.update_button.isVisibleTo(dialog) and dialog.all_button.isVisibleTo(dialog)
    asked, done = [], []
    monkeypatch.setattr(package_dialogs, "ask_buttons", lambda parent, title, text, buttons,
                        **kw: asked.append((text, buttons, kw)) or 0)
    monkeypatch.setattr(catalog, "upgrade", lambda db, package, **kw: done.append(
        package.name) or "requests aktualisiert.")
    dialog.update_current()
    qtbot.waitUntil(lambda: done == ["requests"], timeout=5000)
    text, buttons, kw = asked[0]
    assert text.startswith("requests wird von 2.31.0 auf 2.32.3 aktualisiert, Python 3.14.")
    assert buttons == ["Aktualisieren", "Abbrechen"] and kw == {"default": 1, "escape": 1}
    qtbot.waitUntil(lambda: not dialog.worker.busy and sources.task is None, timeout=10000)
    dialog.search.setText("six")
    assert dialog.list.count() == 1


def test_delete_asks_and_names_the_list(qtbot, make_services, fake_catalog, monkeypatch):
    from cockpit.ui import package_dialogs
    _services, sources = opened(qtbot, make_services, monkeypatch)
    dialog = package_dialogs.PackagesDialog(sources, PIP)
    qtbot.addWidget(dialog)
    asked = []
    monkeypatch.setattr(package_dialogs, "confirm", lambda parent, title, text, **kw:
                        asked.append((text, kw)) or False)
    dialog.delete_current()
    text, kw = asked[0]
    assert text.startswith("six 1.16.0 wird gelöscht, Projekt Tagebuch.")
    assert "nur eine Liste in den Sicherheitskopien" in text
    assert kw == {"yes": "Löschen", "no": "Abbrechen"}


def test_menu_only_with_the_feature(qtbot, make_services):
    from tests.test_phase10f import window
    services = make_services([MANIFEST])
    win = window(qtbot, services)
    assert win.packages.menu.title() == "P&akete" and win.packages.menu.menuAction().isVisible()
    texts = [a.text() for a in win.packages.menu.actions() if a.text()]
    assert texts[0] == "&Paketübersicht …" and "&Aufräumen …" in texts
    services.features.set_globally_enabled(MANIFEST.id, False)
    win.packages.update_menu()
    assert not win.packages.menu.menuAction().isVisible()


# -- Wer benutzt was -------------------------------------------------------------------------------
def test_usage_of_models_and_global_libraries(tmp_path):
    from cockpit.core.projects import Project
    folder = tmp_path / "Chat"
    (folder / "Code").mkdir(parents=True)
    (folder / "Code" / "main.py").write_text('MODEL = "gemma4:12b"\n', encoding="utf-8")
    (folder / "Code" / "requirements.txt").write_text("Requests==2.31\n", encoding="utf-8")
    (folder / "Code" / ".env").write_text("WHISPER=Systran/faster-whisper-small\n",
                                          encoding="utf-8")
    project = Project(1, "Chat", folder, folder / "Code", None, linked=True)
    found = [Package(MODEL, "gemma4:12b", "", key="gemma4:12b", kind=models.OLLAMA),
             Package(MODEL, "Systran/faster-whisper-small", "", key="Systran/faster-whisper-small",
                     kind=models.HF),
             Package(MODEL, "gemma4:120b", "", key="gemma4:120b", kind=models.OLLAMA)]
    usage.mark(MODEL, found, [project])
    assert found[0].used_by == ("Chat",)
    assert found[1].used_by == () and found[1].extra["unused"]          # .env ist vertraulich
    assert found[2].used_by == ()                                       # nicht 12b mit 120b
    libraries = [Package(PIP, "requests", "2.32", place="Python 3.14")]
    usage.mark(PIP, libraries, [project])
    assert libraries[0].used_by == ("Chat",) and base.for_cockpit(libraries[0])


# -- Aufräumen ------------------------------------------------------------------------------------
def test_cleanup_candidates(tmp_path, monkeypatch):
    from cockpit.core.projects import Project
    cache = tmp_path / "cache"
    for name in ("Tagebuch-p1", "Weg-p9"):
        (cache / "venvs" / name).mkdir(parents=True)
        (cache / "venvs" / name / "a.py").write_bytes(b"x" * 100)
    project = Project(1, "Tagebuch", tmp_path / "T", tmp_path / "T" / "Code", None, linked=True)
    monkeypatch.setattr(cleanup, "pip_cache_dir", lambda: tmp_path / "pip")
    (tmp_path / "pip" / "http").mkdir(parents=True)
    (tmp_path / "pip" / "http" / "x").write_bytes(b"p" * 50)
    hub = tmp_path / "hub"
    (hub / "models--a--leer" / "snapshots").mkdir(parents=True)
    monkeypatch.setattr(models, "hf_cache", lambda: hub)
    unused = Package(MODEL, "alt:1b", "", key="alt:1b", kind=models.OLLAMA, size=10,
                     extra={"unused": True})
    found = cleanup.candidates([project], [unused], cache)
    assert [c.text for c in found] == [
        "Umgebung für den Exe-Bau ohne Projekt: Weg-p9",
        "Zwischenspeicher von pip, wird bei Bedarf neu gefüllt",
        "Leerer Download: a/leer",
        "Modell ohne bekannten Benutzer: alt:1b"]
    from cockpit.core import backups
    monkeypatch.setattr(backups, "backups_dir", lambda: tmp_path / "kopien")
    (tmp_path / "kopien").mkdir()
    freed, failed = cleanup.apply(found[:2])
    assert freed == 150 and failed == []
    assert not (cache / "venvs" / "Weg-p9").exists() and (cache / "venvs" / "Tagebuch-p1").exists()
    assert (tmp_path / "pip").is_dir() and not any((tmp_path / "pip").iterdir())


# -- Sicherheitslücken ------------------------------------------------------------------------------
def test_osv_marks_vulnerable_packages():
    def handler(request):
        if request.url.path.endswith("querybatch"):
            body = json.loads(request.content)
            assert body["queries"][0] == {"package": {"name": "requests", "ecosystem": "PyPI"},
                                          "version": "2.31.0"}
            return httpx.Response(200, json={"results": [{"vulns": [{"id": "GHSA-1"}]}, {}]})
        return httpx.Response(200, json={"affected": [{"ranges": [{"events": [
            {"introduced": "0"}, {"fixed": "2.32.0"}]}]}]})
    web.transport = httpx.MockTransport(handler)
    try:
        packages = pip_packages()
        assert osv.mark(packages) == 1
    finally:
        web.transport = None
    assert packages[0].warning == "Sicherheitslücke bekannt, behoben in 2.32.0"
    assert "Sicherheitslücke bekannt" in packages[0].line() and not packages[1].warning


# -- Liste für einen neuen Rechner ----------------------------------------------------------------
def test_transfer_save_read_and_missing(tmp_path):
    by_source = {WINGET: [Package(WINGET, "Git", "2.55", key="Git.Git")],
                 PIP: pip_packages(),
                 MODEL: [Package(MODEL, "gemma4:12b", "", key="gemma4:12b", kind=models.OLLAMA),
                         Package(MODEL, "x.gguf", "", key="C:/x.gguf", kind=models.FILE)]}
    path = tmp_path / "Pakete.json"
    assert transfer.save(path, by_source) == 3            # ohne Projekt-Umgebung und Datei
    wanted = transfer.read(path)
    assert [w.line() for w in wanted] == ["Git.Git 2.55, winget", "requests 2.31.0, Bibliothek",
                                          "gemma4:12b, Modell"]
    assert [w.key for w in transfer.missing(wanted, {WINGET: by_source[WINGET]})] == [
        "requests", "gemma4:12b"]
    path.write_text("{}", encoding="utf-8")
    from cockpit.core.errors import CockpitError
    with pytest.raises(CockpitError):
        transfer.read(path)


# -- Tauschen in Projekten -------------------------------------------------------------------------
def git_project(tmp_path, requirements: str, code: str = ""):
    from cockpit.core.projects import Project
    folder = tmp_path / "Chat"
    code_dir = folder / "Code"
    code_dir.mkdir(parents=True)
    git.run(["init", "-q", "-b", "main"], code_dir)
    git.run(["config", "user.name", "Test"], code_dir)
    git.run(["config", "user.email", "test@example.com"], code_dir)
    (code_dir / "requirements.txt").write_bytes(requirements.encode("utf-8"))
    (code_dir / "main.py").write_text(code or "print(1)\n", encoding="utf-8")
    git.run(["add", "-A"], code_dir)
    git.run(["commit", "-q", "-m", "Start"], code_dir)
    return Project(1, "Chat", folder, code_dir, None, linked=True)


@needs_git
def test_libraries_are_updated_in_a_branch(tmp_path):
    project = git_project(tmp_path, "requests==2.31.0  # Netz\r\nsix\r\nnumpy[x]==1.26.0\r\n")
    changes = project_update.outdated_in_projects([project], {"requests": "2.32.3",
                                                              "numpy": "1.26.0"})
    assert [c.line() for c in changes] == ["Chat: requests 2.31.0 zu 2.32.3"]
    report = project_update.update_libraries(project, changes)
    assert report[0].startswith("Branch Cockpit-pakete-aktualisieren: requirements.txt geändert")
    assert "keine virtuelle Umgebung" in report[-1]
    text = (project.code_dir / "requirements.txt").read_bytes().decode("utf-8")
    assert text == "requests==2.32.3  # Netz\r\nsix\r\nnumpy[x]==1.26.0\r\n"
    assert git.status(project.code_dir).branch == project_update.LIBRARY_BRANCH
    main = git.run(["show", "main:requirements.txt"], project.code_dir).stdout
    assert "requests==2.31.0" in main


@needs_git
def test_model_is_replaced_only_at_chosen_places(tmp_path):
    project = git_project(tmp_path, "", 'A = "gemma4:12b"\nB = "gemma4:12b"\n')
    places = project_update.find_places([project], ["gemma4:12b"])
    assert [p.line() for p in places] == ['Chat: main.py Zeile 1: A = "gemma4:12b"',
                                          'Chat: main.py Zeile 2: B = "gemma4:12b"']
    project_update.replace_model(project, places[:1], ["gemma4:12b"], "qwen3:8b")
    text = (project.code_dir / "main.py").read_text(encoding="utf-8")
    assert text == 'A = "qwen3:8b"\nB = "gemma4:12b"\n'
    assert git.status(project.code_dir).branch == project_update.MODEL_BRANCH


def test_successors_from_the_ai_answer():
    answer = "1. qwen3:8b: neuer, 5 GB\n- **gemma3:4b**: kleiner\nKein Vorschlag: nichts\n"
    assert project_update.parse_successors(answer) == ["qwen3:8b: neuer, 5 GB",
                                                       "gemma3:4b: kleiner"]
