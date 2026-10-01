"""Projektübersichten und Aktionsmenüs, überarbeitet am 30.09.2026 (Wunsch des Nutzers).

Unter dem Projekt: Main-Branch, dann "Branches verwalten". Die Aktionsmenüs von Main-Branch, Branch,
Exe und Projekt in der gewünschten Reihenfolge. Exe: ein Knopf zum Einrichten und Erstellen,
"Exe einlesen" und "Links der Exe". Die Plattform ist ein nacktes Repository, kein echtes Netz.
"""
from __future__ import annotations

import dataclasses

import pytest
from PySide6.QtCore import Qt

from cockpit.core import core_actions, git, project_status, worktrees
from cockpit.core.actions import ActionContext, Target, entries_for
from cockpit.core.git import RemoteAddress
from cockpit.platforms.base import Release, ReleaseAsset
from cockpit.ui import exe_flow
from cockpit.ui.branch_dialogs import NEW_BRANCH_TEXT, BranchesDialog
from cockpit.ui.project_list import BRANCH_OVERVIEW_TEXT, children_of
from tests.conftest import make_project, said
from tests.test_phase10f import structured, window
from tests.test_phase5a import account, sh  # noqa: F401
from tests.test_phase5f import branch_repo

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

REMOTE = RemoteAddress("github.com", "tester", "Tagebuch")


def texts(entries) -> list[str]:
    return [e.action.text for e in entries]


def in_order(found: list[str], expected: list[str]) -> bool:
    """Die erwarteten Einträge stehen alle da, in dieser Reihenfolge."""
    return [t for t in found if t in expected] == expected


def entries(win, project, target, status=None, worktree=None, main_project=None):
    context = ActionContext(win.services, project, target, status=status, worktree=worktree,
                            main_project=main_project)
    return entries_for(core_actions.all_actions(context) + win.controller.actions(), context)


# -- Projektliste ---------------------------------------------------------------------------
def test_main_branch_then_branches_overview(qtbot, tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    worktrees.open_branch(project, "suche")
    win = window(qtbot, services)
    win.project_list.update_status(project_status.compute(project), project)
    win.project_list.expand(project.id, speak=False)
    rows = win.project_list.texts()
    start = rows.index(next(r for r in rows if r.startswith("Tagebuch"))) + 1
    assert rows[start].startswith("Main-Branch, ")
    assert rows[start + 1] == BRANCH_OVERVIEW_TEXT
    assert rows[start + 2].startswith("Branch suche")
    assert win.project_list.select(Target.BRANCH_OVERVIEW, project.id)
    labels = [e.action.text for e in win.current_entries()]
    assert labels == ["Branches verwalten …"]
    assert win.current_entries()[0].action.is_default


def test_overview_row_without_branch_folders(tmp_path, projects_root):
    from cockpit.core.database import Database
    from cockpit.core.projects import ProjectStore
    _bare, code, _other = branch_repo(tmp_path, projects_root)
    project = ProjectStore(Database(tmp_path / "db.sqlite")).add(code.parent)
    rows = children_of(project, project_status.compute(project))
    assert rows[0][1] is Target.CODE and rows[0][0].startswith("Code")
    assert rows[1] == (BRANCH_OVERVIEW_TEXT, Target.BRANCH_OVERVIEW, None)


def test_no_overview_without_commits(tmp_path, projects_root):
    from cockpit.core.database import Database
    from cockpit.core.projects import ProjectStore
    folder = make_project(projects_root, "Neu")
    project = ProjectStore(Database(tmp_path / "db.sqlite")).add(folder)
    rows = children_of(project, project_status.compute(project))
    assert [target for _text, target, _key in rows] == [Target.CODE]


# -- Aktionsmenüs ---------------------------------------------------------------------------
MAIN_ORDER = ["Projekt neu einlesen", "Terminal …", "Änderungen auf GitHub hochladen …",
              "Änderungen von GitHub holen …", "Pull Requests …", "Verlauf …",
              "Änderungen verwerfen …", "Änderungen beiseitelegen …", "Git-Identität …",
              "Code-Ordner öffnen"]


def test_main_branch_menu(qtbot, tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    status = project_status.compute(project)
    found = texts(entries(win, dataclasses.replace(project, remote=REMOTE), Target.CODE, status))
    assert in_order(found, MAIN_ORDER), found
    assert found[:3] == MAIN_ORDER[:3]
    for gone in ("Branches …", "Neuer Branch …", "Pull-Requests-Übersicht …"):
        assert gone not in found


def test_branch_menu(qtbot, tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    tree = worktrees.open_branch(project, "suche")
    win = window(qtbot, services)
    status = project_status.for_folder(project_status.compute(project), "suche")
    branch = dataclasses.replace(project, code_dir=tree.path, remote=REMOTE)
    found = texts(entries(win, branch, Target.CODE, status, tree, project))
    expected = ["Projekt neu einlesen", "Terminal …", "Änderungen auf GitHub hochladen …",
                "Änderungen von GitHub holen …", "Pull Request erstellen …",
                "Pull-Requests-Übersicht …", "Verlauf …", "Änderungen verwerfen …",
                "Änderungen beiseitelegen …", "Git-Identität …", "Code-Ordner öffnen"]
    assert in_order(found, expected), found
    for gone in ("Branch-Ordner entfernen …", "suche verwalten …", "Neuer Branch …",
                 "Pull Requests …"):
        assert gone not in found


def test_project_menu(qtbot, tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    found = texts(entries(win, dataclasses.replace(project, remote=REMOTE), Target.PROJECT))
    expected = ["Projekt neu einlesen", "Terminal …", "Projekt verwalten …", "Links …",
                "Features dieses Projekts …", "Aus der Liste entfernen …",
                "Projektordner öffnen"]
    assert in_order(found, expected), found
    assert found[0] == "Projekt neu einlesen" and found[-1] == "Projektordner öffnen"
    assert "Repository verwalten …" not in found


def exe_services(make_services, projects_root):
    from cockpit.features.exe_build.manifest import MANIFEST
    make_project(projects_root, "Rechner", exe=True)
    services = make_services([MANIFEST])
    services.projects.scan(projects_root)
    return services, next(p for p in services.projects.all() if p.name == "Rechner")


def test_exe_menu(qtbot, make_services, projects_root):
    services, project = exe_services(make_services, projects_root)
    win = window(qtbot, services)
    found = texts(entries(win, dataclasses.replace(project, remote=REMOTE), Target.EXE))
    expected = ["Projekt neu einlesen", "Exe starten", "Exe aus dem Code erstellen …",
                "Exe einlesen …", "Links der Exe …", "Exe-Ordner öffnen",
                "Wie funktioniert die Exe? …"]
    assert in_order(found, expected), found
    for gone in ("Exe-Einrichtung prüfen", "Exe mit KI einrichten …", "Exe-Datei wählen …",
                 "Exe aus dem Release holen …", "Exe aus dem Code aktualisieren …"):
        assert gone not in found


# -- Exe aus dem Code erstellen -------------------------------------------------------------
@pytest.fixture
def exe_window(qtbot, make_services, projects_root, monkeypatch):
    services, project = exe_services(make_services, projects_root)
    win = window(qtbot, services)
    built, shown = [], []
    monkeypatch.setattr(exe_flow.ExeActions, "build", lambda self, c: built.append(c.project.name))

    class FakeReady:
        def __init__(self, project_, lines, parent=None):
            shown.append(lines)

        def exec(self):
            return True

    monkeypatch.setattr(exe_flow, "ReadyDialog", FakeReady)
    return win, project, built, shown


def choose(monkeypatch, pick: str, asked: list):
    def fake(parent, title, name, items):
        asked.append(list(items))
        return items.index(pick) if pick in items else None
    monkeypatch.setattr(exe_flow, "choose_from_list", fake)


def test_build_without_ai_checks_then_offers_build(exe_window, monkeypatch, qtbot):
    win, project, built, shown = exe_window
    monkeypatch.setattr(win.services, "ai_problem", lambda tool_id=None: "Keine KI.")
    asked = []
    choose(monkeypatch, exe_flow.WITHOUT_AI, asked)
    context = ActionContext(win.services, project, Target.EXE)
    win.controller.exe.build_menu(context)
    assert asked == [[exe_flow.WITHOUT_AI, exe_flow.WITH_AI]]     # ohne KI oben
    qtbot.waitUntil(lambda: built == ["Rechner"], timeout=10000)
    assert shown and shown[0]                                     # Ergebnis der Prüfung


def test_build_with_ai_is_first_when_ai_is_there(exe_window, monkeypatch):
    win, project, built, shown = exe_window
    monkeypatch.setattr(win.services, "ai_problem", lambda tool_id=None: "")
    asked, started = [], []
    choose(monkeypatch, exe_flow.WITH_AI, asked)

    class FakeFlow:
        def __init__(self, actions, project_, on_finished=None):
            self.on_finished = on_finished

        def start(self):
            started.append(True)
            self.on_finished(["Änderungen übernommen."])

    from cockpit.ui import exe_ai
    monkeypatch.setattr(exe_ai, "ExeAIFlow", FakeFlow)
    win.controller.exe.build_menu(ActionContext(win.services, project, Target.EXE))
    assert asked == [[exe_flow.WITH_AI, exe_flow.WITHOUT_AI]]     # mit KI oben
    assert started == [True]
    assert shown == [["Änderungen übernommen."]] and built == ["Rechner"]


def test_cancelled_choice_builds_nothing(exe_window, monkeypatch):
    win, project, built, shown = exe_window
    choose(monkeypatch, "nichts", [])
    win.controller.exe.build_menu(ActionContext(win.services, project, Target.EXE))
    assert built == [] and shown == []


def test_ready_dialog(qtbot):
    from cockpit.core.projects import Project
    from pathlib import Path
    project = Project(1, "Rechner", Path("x"), Path("x/Code"), None)
    dialog = exe_flow.ReadyDialog(project, ["Startdatei: main.py gefunden."])
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Exe aus dem Code erstellen: Rechner"
    assert dialog.list.accessibleName() == "Ergebnis der Einrichtung"
    assert dialog.list.item(0).text() == "Startdatei: main.py gefunden."
    assert dialog.build_button.text() == "Exe e&rstellen" and dialog.build_button.isDefault()


def test_ai_flow_reports_an_empty_proposal(monkeypatch):
    from cockpit.features.exe_build.ai_fix import Proposal
    from cockpit.ui import exe_ai
    got = []
    monkeypatch.setattr(exe_ai, "show_info", lambda *a, **k: got.append("Meldung"))

    class Actions:
        window = services = None

    flow = exe_ai.ExeAIFlow(Actions(), None, on_finished=got.append)
    flow.review(Proposal(summary="Alles passt."))
    assert got == [["Es gibt keine Änderung, die das Cockpit übernehmen kann. Die KI sagt: "
                    "Alles passt."]]


# -- Exe einlesen und Links -----------------------------------------------------------------
def test_import_exe_offers_file_or_release(exe_window, monkeypatch):
    win, project, _built, _shown = exe_window
    called = []
    monkeypatch.setattr(exe_flow.ExeActions, "choose", lambda self, c: called.append("Datei"))
    monkeypatch.setattr(exe_flow.ExeActions, "fetch", lambda self, c: called.append("Release"))
    asked = []
    choose(monkeypatch, exe_flow.FROM_RELEASE, asked)
    online = dataclasses.replace(project, remote=REMOTE)
    win.controller.exe.import_exe(ActionContext(win.services, online, Target.EXE))
    assert asked == [[exe_flow.FROM_FILE, exe_flow.FROM_RELEASE]] and called == ["Release"]
    asked.clear()
    choose(monkeypatch, exe_flow.FROM_FILE, asked)
    win.controller.exe.import_exe(ActionContext(win.services, project, Target.EXE))
    assert asked == [[exe_flow.FROM_FILE]] and called == ["Release", "Datei"]


def test_download_links():
    asset = ReleaseAsset(1, "Rechner.exe", 1000)
    release = Release(1, "v1.2.0", "Version 1.2.0",
                      "https://github.com/tester/Rechner/releases/tag/v1.2.0", "2026-09-30",
                      (asset,))
    assert exe_flow.download_links(release, asset) == [
        ("Release v1.2.0", "https://github.com/tester/Rechner/releases/tag/v1.2.0"),
        ("Download der Exe v1.2.0",
         "https://github.com/tester/Rechner/releases/download/v1.2.0/Rechner.exe"),
        ("Download der neuesten Exe",
         "https://github.com/tester/Rechner/releases/latest/download/Rechner.exe")]


# -- README ---------------------------------------------------------------------------------
def test_readme_offers_create_or_edit_and_settings(qtbot, make_services, projects_root,
                                                   monkeypatch):
    from cockpit.ui import common
    make_project(projects_root, "Doku")
    services = make_services([])
    services.projects.scan(projects_root)
    win = window(qtbot, services)
    project = next(p for p in services.projects.all() if p.name == "Doku")
    readme = win.controller.readme
    called, asked = [], []
    monkeypatch.setattr(type(readme), "start", lambda self, c: called.append("erstellen"))
    monkeypatch.setattr(type(readme), "edit", lambda self, c: called.append("bearbeiten"))
    monkeypatch.setattr(type(readme), "languages", lambda self, c: called.append("Einstellungen"))
    monkeypatch.setattr(common, "choose_from_list",
                        lambda parent, title, name, items: asked.append(list(items)) or 0)
    context = ActionContext(services, project, Target.PROJECT)
    readme.choose(context)
    assert asked[-1] == ["README erstellen …", "README-Einstellungen …"]
    (project.code_dir / "README.md").write_text("# Doku\n", encoding="utf-8")
    readme.choose(context)
    assert asked[-1] == ["README bearbeiten …", "README-Einstellungen …"]
    assert called == ["erstellen", "bearbeiten"]


# -- Branches verwalten ---------------------------------------------------------------------
def overview(qtbot, project, folders=None):
    from cockpit.core import branches
    dialog = BranchesDialog(project, branches.list_branches(project.code_dir),
                            folders=folders or {})
    qtbot.addWidget(dialog)
    dialog.show()
    return dialog


def test_overview_starts_with_new_branch(qtbot, tmp_path, projects_root, make_services,
                                         monkeypatch):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    dialog = overview(qtbot, project)
    assert dialog.list.item(0).text() == NEW_BRANCH_TEXT
    assert dialog.list.currentRow() == 0
    assert dialog.list.item(1).text().startswith("main, ")
    assert not dialog.new_button.isVisible()                   # steht jetzt in der Liste
    called = []
    monkeypatch.setattr(BranchesDialog, "new_branch", lambda self: called.append("neu"))
    dialog.list.setFocus()
    qtbot.keyClick(dialog.list, Qt.Key.Key_Return)
    assert called == ["neu"]


def test_main_row_shows_exe_state(qtbot, tmp_path, projects_root, make_services):
    from cockpit.core import exe
    services, project, _other = structured(tmp_path, projects_root, make_services)
    project.exe_dir.mkdir(parents=True, exist_ok=True)
    (project.exe_dir / "Tagebuch.exe").write_bytes(b"MZ")
    exe.write_record(project.code_dir, exe.ExeRecord("release", "2026-09-30T10:00:00",
                                                     version="1.2.0"))
    dialog = overview(qtbot, project)
    dialog.list.setCurrentRow(dialog.row_of("main"))
    assert dialog.exe_info.isVisible()
    lines = [dialog.exe_info.item(r).text() for r in range(dialog.exe_info.count())]
    assert lines[0].startswith("Exe, Version 1.2.0")
    assert lines[1] == "Veröffentlicht als Version 1.2.0."
    assert dialog.exe_info.accessibleName() == "Exe"
    assert not dialog.merge_button.isVisible()
    dialog.list.setCurrentRow(dialog.row_of("suche"))
    assert not dialog.exe_info.isVisible()


def test_exe_lines_without_release(tmp_path, projects_root, make_services):
    from cockpit.ui.branch_dialogs import exe_lines
    services, project, _other = structured(tmp_path, projects_root, make_services)
    assert exe_lines(project) == ["Exe: Dieses Projekt hat keinen Ordner Exe."]
    project.exe_dir.mkdir(parents=True, exist_ok=True)
    (project.exe_dir / "Tagebuch.exe").write_bytes(b"MZ")
    assert exe_lines(project)[-1] == "Noch nicht veröffentlicht."


def test_branch_row_has_merge_rename_remove_delete(qtbot, tmp_path, projects_root,
                                                   make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    tree = worktrees.open_branch(project, "suche")
    dialog = overview(qtbot, project, {"suche": tree.folder})
    dialog.list.setCurrentRow(dialog.row_of("suche"))
    for button in (dialog.merge_button, dialog.rename_button, dialog.delete_button,
                   dialog.remove_button):
        assert button.isVisible(), button.text()
    dialog.remove_folder()
    assert dialog.remove_request and dialog.remove_name == "suche"
    other = overview(qtbot, project, {"suche": tree.folder})
    other.list.setCurrentRow(other.row_of("lokal-neu"))        # ohne Ordner
    assert not other.remove_button.isVisible()


def test_overview_remove_request_removes_the_folder(qtbot, tmp_path, projects_root,
                                                    make_services, monkeypatch):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    worktrees.open_branch(project, "suche")
    win = window(qtbot, services)
    removed = []
    monkeypatch.setattr(type(win.controller.worktrees), "remove_tree",
                        lambda self, p, tree: removed.append(tree.branch))

    class FakeDialog:
        new_request = open_request = delete_request = ""
        remove_request, remove_name = True, "suche"

        def __init__(self, *args, **kwargs):
            pass

        def exec(self):
            return True

    from cockpit.ui import branch_dialogs
    monkeypatch.setattr(branch_dialogs, "BranchesDialog", FakeDialog)
    context = ActionContext(services, project, Target.BRANCH_OVERVIEW,
                            status=project_status.compute(project))
    win.controller.branches_action(context)
    qtbot.waitUntil(lambda: removed == ["suche"], timeout=10000)


# -- Fortschritt beim Einrichten mit KI (Wunsch vom 01.10.2026) ------------------------------
class FakeTextAI:
    name = "Test-KI"
    max_chars = 20000

    def __init__(self, answer="ZUSAMMENFASSUNG: Passt.", wait_for_cancel=False):
        self.answer, self.wait_for_cancel = answer, wait_for_cancel

    def ask(self, prompt, system="", cancel=None):
        if self.wait_for_cancel:
            import time
            from cockpit.core.errors import Cancelled
            while not cancel.is_set():
                time.sleep(0.05)
            raise Cancelled()
        return self.answer


def exe_code(projects_root):
    from cockpit.core import exe
    code = make_project(projects_root, "Rechner") / "Code"
    (code / "hilfe.py").write_text("import requests\n", encoding="utf-8")
    return code, exe.BuildSettings("main.py", "Rechner")


def test_ask_reports_each_file_and_the_ai(projects_root):
    from cockpit.features.exe_build import ai_fix
    code, settings = exe_code(projects_root)
    lines = []
    proposal = ai_fix.ask(FakeTextAI(), "Rechner", code, settings, "", progress=lines.append)
    assert proposal.summary == "Passt."
    assert lines[0] == "Der Code wird gelesen."
    assert "Datei 1 von 2 gelesen: hilfe.py" in lines and "Datei 2 von 2 gelesen: main.py" in lines
    sent = next(line for line in lines if line.startswith("An die KI gesendet: "))
    assert "aus main.py" in sent and sent.endswith("auf die Antwort von Test-KI.")
    assert lines[-1] == "Antwort der KI ist da."


def test_ask_stops_before_the_ai_when_cancelled(projects_root):
    import threading
    from cockpit.core.errors import Cancelled
    from cockpit.features.exe_build import ai_fix
    code, settings = exe_code(projects_root)
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(Cancelled):
        ai_fix.ask(FakeTextAI(), "Rechner", code, settings, "", cancel)


def work_dialog(qtbot, work, with_ai=True):
    from cockpit.core.projects import Project
    from pathlib import Path
    from cockpit.ui.exe_ai import WorkDialog
    dialog = WorkDialog(Project(1, "Rechner", Path("x"), Path("x/Code"), None), work, with_ai)
    qtbot.addWidget(dialog)
    return dialog


def test_work_dialog_shows_progress_and_closes_with_the_result(qtbot):
    def work(task):
        task.status.emit("Datei 1 von 1 gelesen: main.py")
        task.status.emit("An die KI gesendet: 10 Zeichen aus main.py.")
        return "Vorschlag"

    dialog = work_dialog(qtbot, work)
    assert dialog.windowTitle() == "Exe mit KI einrichten: Rechner, läuft"
    assert dialog.list.accessibleName() == "Fortschritt"
    assert dialog.exec()
    assert dialog.result_value == "Vorschlag"
    lines = [dialog.list.item(r).text() for r in range(dialog.list.count())]
    assert lines[0].startswith("Die KI liest den Code.")
    assert lines[1:] == ["Datei 1 von 1 gelesen: main.py",
                         "An die KI gesendet: 10 Zeichen aus main.py."]
    assert dialog.list.currentRow() == 0                       # Markierung bleibt oben
    assert said("Der Code ist gelesen. Die KI arbeitet.")


def test_work_dialog_counts_the_time(qtbot, monkeypatch):
    dialog = work_dialog(qtbot, lambda task: None)
    monkeypatch.setattr(dialog, "seconds", lambda: 75)
    dialog.tick()
    assert dialog.list.item(0).text() == "Die KI liest den Code. Läuft seit 1 Minute 15 Sekunden."
    monkeypatch.setattr(dialog, "seconds", lambda: 1)
    dialog.tick()
    assert dialog.list.item(0).text() == "Die KI liest den Code. Läuft seit 1 Sekunde."


def test_work_dialog_cancel_closes_at_once(qtbot, projects_root):
    from PySide6.QtCore import QTimer
    from cockpit.features.exe_build import ai_fix
    from cockpit.ui import exe_ai
    code, settings = exe_code(projects_root)

    def work(task):
        return ai_fix.ask(FakeTextAI(wait_for_cancel=True), "Rechner", code, settings, "",
                          task.cancel_event, progress=task.status.emit)

    dialog = work_dialog(qtbot, work)
    QTimer.singleShot(300, dialog.cancel_button.click)
    assert not dialog.exec()
    assert dialog.result_value is None and dialog.failure is None
    qtbot.waitUntil(lambda: not exe_ai._RUNNING, timeout=5000)  # Aufgabe ist ausgelaufen


def test_work_dialog_reports_errors(qtbot):
    from cockpit.core.errors import CockpitError

    def work(task):
        raise CockpitError("Die KI antwortet nicht.", "Zeitüberschreitung")

    dialog = work_dialog(qtbot, work)
    assert not dialog.exec()
    assert dialog.failure == ("Die KI antwortet nicht.", "Zeitüberschreitung")


# -- Änderungen der KI im Branch Cockpit-exe-bauen (Wunsch vom 01.10.2026) --------------------
def change_in(folder, text="neu\n"):
    (folder / "exe_fix.txt").write_text(text, encoding="utf-8")


def test_ai_branch_with_branch_folders(tmp_path, projects_root, make_services):
    from cockpit.core import branches
    from cockpit.features.exe_build import exe_branch
    services, project, _other = structured(tmp_path, projects_root, make_services)
    folder = exe_branch.prepare(project)
    assert folder != project.code_dir and folder.name == "Cockpit-exe-bauen"
    assert git.status(folder).branch == "Cockpit-exe-bauen"
    change_in(folder)
    (folder / "anderes.txt").write_text("nicht mitnehmen\n", encoding="utf-8")
    assert exe_branch.commit(folder, ["exe_fix.txt", "cockpit.toml"])
    assert not (project.code_dir / "exe_fix.txt").exists()       # main bleibt unberührt
    assert "anderes.txt" in git.run(["status", "--porcelain"], folder).stdout   # nicht committet
    assert exe_branch.prepare(project) == folder                 # wird weiterbenutzt
    (folder / "anderes.txt").unlink()
    outcome = exe_branch.merge_into_main(project)
    assert outcome.kind.name == "NONE"
    assert (project.code_dir / "exe_fix.txt").read_text(encoding="utf-8") == "neu\n"
    exe_branch.delete(project)
    assert not folder.exists()
    assert "Cockpit-exe-bauen" not in [b.name for b in branches.list_branches(project.code_dir)
                                       if b.local]


def test_ai_branch_without_branch_folders(tmp_path, projects_root):
    from cockpit.features.exe_build import exe_branch
    from cockpit.core.database import Database
    from cockpit.core.projects import ProjectStore
    _bare, code, _other = branch_repo(tmp_path, projects_root)
    project = ProjectStore(Database(tmp_path / "db.sqlite")).add(code.parent)
    assert exe_branch.prepare(project) == code
    assert git.status(code).branch == "Cockpit-exe-bauen"
    change_in(code)
    assert exe_branch.commit(code, ["exe_fix.txt"])
    assert not exe_branch.commit(code, ["exe_fix.txt"])            # nichts Neues
    exe_branch.merge_into_main(project)
    assert git.status(code).branch == "main"
    assert (code / "exe_fix.txt").is_file()
    exe_branch.delete(project)


def test_where_text_names_the_branch(tmp_path, projects_root, make_services):
    from cockpit.features.exe_build import exe_branch
    services, project, _other = structured(tmp_path, projects_root, make_services)
    text = exe_branch.where_text(project)
    assert text.startswith("Die Änderungen kommen in den Branch Cockpit-exe-bauen, nicht in main.")
    assert "eigenen Ordner" in text


def test_review_asks_with_branch_text(qtbot, tmp_path, projects_root, make_services,
                                      monkeypatch):
    from cockpit.features.exe_build.ai_fix import Change, Proposal
    from cockpit.ui import exe_ai
    services, project, _other = structured(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    asked, applied = [], []
    monkeypatch.setattr(exe_ai, "confirm", lambda parent, title, text, **k: asked.append(text)
                        or True)
    monkeypatch.setattr(exe_ai.ProposalDialog, "exec", lambda self: True)
    monkeypatch.setattr(exe_ai.ExeAIFlow, "apply_in_branch",
                        lambda self, proposal: applied.append(proposal))
    flow = exe_ai.ExeAIFlow(win.controller.exe, project, on_finished=lambda *a: None)
    flow.review(Proposal(changes=[Change("main.py", "Grund", "", "x\n")]))
    assert "Cockpit-exe-bauen, nicht in main" in asked[0]
    assert "Erst dann entscheiden Sie" in asked[0]
    assert len(applied) == 1


def test_apply_in_branch_changes_only_the_branch(qtbot, tmp_path, projects_root, make_services):
    from cockpit.features.exe_build.ai_fix import Change, Proposal
    from cockpit.ui import exe_ai
    services, project, _other = structured(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    got = []
    flow = exe_ai.ExeAIFlow(win.controller.exe, project,
                            on_finished=lambda lines, folder=None: got.append((lines, folder)))
    flow.apply_in_branch(Proposal(changes=[Change("exe_fix.txt", "Grund", "", "neu\n")]))
    qtbot.waitUntil(lambda: bool(got), timeout=10000)
    lines, folder = got[0]
    assert folder.name == "Cockpit-exe-bauen" and (folder / "exe_fix.txt").is_file()
    assert not (project.code_dir / "exe_fix.txt").exists()
    assert lines[0].startswith("Änderungen im Branch Cockpit-exe-bauen übernommen")
    assert git.run(["status", "--porcelain"], folder).stdout.strip() == ""   # committet


def test_ready_with_branch_builds_from_the_branch(exe_window, monkeypatch, tmp_path):
    win, project, built, shown = exe_window
    branch_builds = []
    monkeypatch.setattr(exe_flow.ExeActions, "build_ai_branch",
                        lambda self, p, folder: branch_builds.append(folder))
    context = ActionContext(win.services, project, Target.EXE)
    win.controller.exe.offer_build(context, ["Änderungen im Branch …"], tmp_path)
    assert branch_builds == [tmp_path] and built == []


@pytest.mark.parametrize("choice, merged, delete", [(0, False, None), (1, True, False),
                                                    (2, True, True)])
def test_after_test_offers_three_ways(exe_window, monkeypatch, choice, merged, delete):
    win, project, _built, _shown = exe_window
    asked, merges = [], []

    def fake_ask(parent, title, text, buttons, default, escape):
        asked.append((buttons, default, escape))
        return choice

    monkeypatch.setattr(exe_flow, "ask_buttons", fake_ask)
    monkeypatch.setattr(exe_flow.ExeActions, "merge_ai_branch",
                        lambda self, p, delete: merges.append(delete))
    win.controller.exe.after_branch_test(project, "Rechner_branch_Cockpit-exe-bauen.exe")
    assert asked == [([exe_flow.AFTER_TEST_LATER, exe_flow.AFTER_TEST_KEEP,
                       exe_flow.AFTER_TEST_DELETE], 0, 0)]       # sicher: später
    assert merges == ([delete] if merged else [])


def test_merge_ai_branch_from_the_window(qtbot, tmp_path, projects_root, make_services):
    from cockpit.features.exe_build import exe_branch
    services, project, _other = structured(tmp_path, projects_root, make_services)
    folder = exe_branch.prepare(project)
    change_in(folder)
    exe_branch.commit(folder, ["exe_fix.txt"])
    win = window(qtbot, services)
    win.controller.exe.merge_ai_branch(project, delete=True)
    assert (project.code_dir / "exe_fix.txt").is_file() and not folder.exists()
    assert said("Cockpit-exe-bauen ist in main übernommen. Main ist noch nicht hochgeladen. "
                "Der Branch Cockpit-exe-bauen ist gelöscht.")


# -- Kurzer Ort für die Umgebung zum Bauen und lange Pfade (Wunsch vom 01.10.2026) ------------
def test_build_venv_is_short_and_shared_with_the_branch(tmp_path, projects_root, make_services):
    from cockpit.core import exe, paths
    from cockpit.features.exe_build import exe_branch
    services, project, _other = structured(tmp_path, projects_root, make_services)
    main_venv = exe.build_venv(project)
    assert main_venv.parent == paths.cache_dir() / "venvs"
    assert main_venv.name.startswith("Tagebuch-") and len(main_venv.name) <= 30
    folder = exe_branch.prepare(project)
    assert exe.build_venv(project, folder) == main_venv          # gleiche requirements.txt
    (folder / "requirements.txt").write_text("requests==2.32.0\n", encoding="utf-8")
    own = exe.build_venv(project, folder)
    assert own != main_venv and own.name.endswith("-b")           # main bleibt sauber


def fake_venv(tmp_path):
    venv = tmp_path / "venv"
    (venv / "Scripts").mkdir(parents=True)
    (venv / "Scripts" / "python.exe").write_bytes(b"")
    return venv


def test_prepare_venv_names_long_paths(tmp_path, monkeypatch):
    from cockpit.core import exe
    from cockpit.core.errors import CockpitError
    venv = fake_venv(tmp_path)
    monkeypatch.setattr(exe, "_works", lambda python: True)

    def pip(args, cwd, on_line=None, cancel=None, env=None):
        on_line("HINT: This error might have occurred since this system does not have Windows "
                "Long Path support enabled.")
        return 1

    monkeypatch.setattr(exe, "run_process", pip)
    with pytest.raises(CockpitError) as raised:
        exe.prepare_venv(tmp_path, venv=venv)
    assert raised.value.message == exe.LONG_PATHS


def test_prepare_venv_replaces_a_broken_environment(tmp_path, monkeypatch):
    from cockpit.core import exe
    venv = fake_venv(tmp_path)
    calls = []
    monkeypatch.setattr(exe, "_works", lambda python: False)
    monkeypatch.setattr(exe, "find_python", lambda: ["py"])

    def run(args, cwd, on_line=None, cancel=None, env=None):
        calls.append(args)
        if "venv" in args:
            (venv / "Scripts").mkdir(parents=True)
            (venv / "Scripts" / "python.exe").write_bytes(b"neu")
        return 0

    monkeypatch.setattr(exe, "run_process", run)
    python = exe.prepare_venv(tmp_path, venv=venv)
    assert calls[0] == ["py", "-m", "venv", str(venv)]            # neu angelegt
    assert python.read_bytes() == b"neu"


def test_long_path_hint_is_recognised():
    from cockpit.core import long_paths
    assert long_paths.is_long_path_error("... does not have Windows Long Path support enabled")
    assert not long_paths.is_long_path_error("No matching distribution found")
    assert isinstance(long_paths.enabled(), bool)


def test_build_failure_offers_long_paths(qtbot, monkeypatch):
    from cockpit.core import exe
    offered = []
    monkeypatch.setattr(exe_flow, "offer_long_paths", lambda parent: offered.append(True))
    dialog = exe_flow.BuildDialog.__new__(exe_flow.BuildDialog)
    monkeypatch.setattr(exe_flow.BuildDialog, "ended", lambda self, text, urgent=False: None)
    dialog.output = type("Out", (), {"addItem": lambda self, text: None})()
    exe_flow.BuildDialog.failed(dialog, exe.LONG_PATHS, "Details")
    assert offered == [True]
    exe_flow.BuildDialog.failed(dialog, "Etwas anderes.", "")
    assert offered == [True]


@pytest.mark.parametrize("agree, works, expected", [(False, True, False), (True, True, True),
                                                    (True, False, False)])
def test_offer_long_paths(monkeypatch, agree, works, expected):
    from cockpit.core import long_paths
    asked, enabled = [], []
    monkeypatch.setattr(long_paths, "enabled", lambda: False)
    monkeypatch.setattr(long_paths, "enable", lambda: enabled.append(True) or works)
    monkeypatch.setattr(exe_flow, "confirm", lambda parent, title, text, **k: asked.append(k)
                        or agree)
    monkeypatch.setattr(exe_flow, "show_info", lambda *a, **k: None)
    monkeypatch.setattr(exe_flow, "show_error", lambda *a, **k: None)
    assert exe_flow.offer_long_paths(None) is expected
    assert asked == [{"yes": "Einschalten", "no": "Nicht jetzt"}]
    assert enabled == ([True] if agree else [])


def test_setup_check_warns_about_long_paths(projects_root, monkeypatch):
    from cockpit.core import exe, long_paths
    from cockpit.features.exe_build import setup_check
    code, settings = exe_code(projects_root)
    monkeypatch.setattr(long_paths, "enabled", lambda: False)
    lines = setup_check.check_for(code, settings)
    assert any(line.startswith("Warnung: Lange Pfade sind in Windows ausgeschaltet.")
               for line in lines)
    monkeypatch.setattr(long_paths, "enabled", lambda: True)
    assert not any("Lange Pfade" in line for line in setup_check.check_for(code, settings))


def test_build_dialog_continues_after_success(qtbot, monkeypatch, tmp_path):
    """Rückmeldung vom 01.10.2026: Nach dem Bau aus Cockpit-exe-bauen blieb das Fenster offen,
    die Frage danach kam nicht."""
    from cockpit.core import exe
    from cockpit.core.projects import Project
    built = tmp_path / "Exe" / "VokabelApp_branch_Cockpit-exe-bauen" / "VokabelApp.exe"

    def fake_build(project, settings, on_status, on_line, cancel, branch_dir=None,
                   branch_name=""):
        on_status("Schritt 4 von 4: Exe wird übernommen")
        return exe.BuildResult(built, branch=branch_name)

    monkeypatch.setattr(exe, "build", fake_build)
    project = Project(1, "VokabelApp", tmp_path, tmp_path / "Code", None)
    settings = exe.BuildSettings("gui.py", "VokabelApp")
    dialog = exe_flow.BuildDialog(None, project, settings, branch_dir=tmp_path / "Code",
                                  branch_name="Cockpit-exe-bauen", continue_after=True)
    qtbot.addWidget(dialog)
    assert dialog.exec()                                        # schließt sich selbst
    assert dialog.result.exe == built
    stays = exe_flow.BuildDialog(None, project, settings, branch_dir=tmp_path / "Code")
    qtbot.addWidget(stays)
    stays.show()
    qtbot.waitUntil(lambda: not stays.running, timeout=5000)
    qtbot.wait(100)
    assert stays.isVisible() and stays.result is not None        # sonst bleibt es offen


def test_branch_question_names_the_subfolder(exe_window, monkeypatch, tmp_path):
    from cockpit.core import exe
    win, project, _built, _shown = exe_window
    branch_dir = tmp_path / "Branch"
    branch_dir.mkdir()
    built = project.exe_dir / "Rechner_branch_Cockpit-exe-bauen" / "Rechner.exe"

    class FakeBuild:
        def __init__(self, *args, **kwargs):
            assert kwargs["continue_after"] is True
            self.result = exe.BuildResult(built, branch="Cockpit-exe-bauen")

        def exec(self):
            return True

    monkeypatch.setattr(exe_flow, "BuildDialog", FakeBuild)
    monkeypatch.setattr(exe, "read_settings", lambda folder: exe.BuildSettings("main.py",
                                                                                "Rechner"))
    named = []
    monkeypatch.setattr(exe_flow.ExeActions, "after_branch_test",
                        lambda self, p, name: named.append(name))
    win.controller.exe.build_ai_branch(project, branch_dir)
    assert named == [r"Rechner_branch_Cockpit-exe-bauen\Rechner.exe"]
