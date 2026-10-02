"""Wünsche des Nutzers vom 02.10.2026.

1. Nach einem Fehler beim Bau: "Problem mit KI lösen", auch mehrmals hintereinander.
2. Stand hinter den Aktionen, zum Beispiel "3 Dateien offen" oder "alles aktuell".
3. "Branches verwalten" mit "Branches anzeigen" (lokal, nur auf GitHub, alle). In der
   Projektliste nur noch die lokalen Branches.
4. Ganz oben Sammlungen und einzelne Projekte gemischt, das zuletzt Geänderte oben.
Die Plattform ist ein nacktes Repository auf der Festplatte, kein echtes Netz.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from cockpit.core import git, project_status, worktrees
from cockpit.core.actions import Action, ActionContext, ActionEntry, Target, entries_for
from cockpit.core.availability import Availability
from cockpit.core.git import RemoteAddress, RepoStatus
from cockpit.core.project_status import ProjectStatus
from cockpit.core.projects import Project
from cockpit.ui import exe_flow
from cockpit.ui.branch_dialogs import (ALL, LOCAL, REMOTE, SHOW_PREFIX, BranchesDialog,
                                       filtered)
from cockpit.ui.project_list import children_of
from tests.conftest import said
from tests.test_phase10f import structured, window
from tests.test_phase5a import account, sh  # noqa: F401
from tests.test_phase8b import quiet_machine  # noqa: F401 (Fixture)
from tests.test_projektuebersichten import (FakeTextAI, entries, exe_code,  # noqa: F401
                                            exe_window, texts)

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

REMOTE_ADDRESS = RemoteAddress("github.com", "tester", "Tagebuch")


# -- 1. Problem mit KI lösen ------------------------------------------------------------------
def build_dialog(qtbot, monkeypatch, tmp_path, fail=True):
    from cockpit.core import exe
    from cockpit.core.errors import CockpitError

    def fake_build(project, settings, on_status, on_line, cancel, branch_dir=None,
                   branch_name=""):
        on_line('File "gui.py", line 3, in <module>')
        on_line("ModuleNotFoundError: No module named 'vokabeln'")
        if fail:
            raise CockpitError("Der Start-Test ist fehlgeschlagen.", "Exit-Code 1")
        return exe.BuildResult(tmp_path / "Rechner.exe")

    monkeypatch.setattr(exe, "build", fake_build)
    project = Project(1, "Rechner", tmp_path, tmp_path / "Code", None)
    dialog = exe_flow.BuildDialog(None, project, exe.BuildSettings("gui.py", "Rechner"))
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitUntil(lambda: not dialog.running, timeout=5000)
    return dialog


def test_failed_build_offers_the_ai(qtbot, monkeypatch, tmp_path):
    dialog = build_dialog(qtbot, monkeypatch, tmp_path)
    assert dialog.fix_button.isVisible()
    assert dialog.fix_button.text() == "Problem mit &KI lösen"
    assert dialog.fix_button.isDefault()
    assert "ModuleNotFoundError: No module named 'vokabeln'" in dialog.error_text
    assert dialog.error_text.startswith("Der Start-Test ist fehlgeschlagen.")
    dialog.fix_button.click()
    assert dialog.fix_requested and not dialog.isVisible()


def test_successful_build_has_no_ai_button(qtbot, monkeypatch, tmp_path):
    dialog = build_dialog(qtbot, monkeypatch, tmp_path, fail=False)
    assert not dialog.fix_button.isVisible()


def test_build_hands_the_error_to_the_ai(exe_window, monkeypatch):
    win, project, _built, _shown = exe_window
    monkeypatch.undo()                                       # das echte build()
    from cockpit.core import exe

    class FailedBuild:
        def __init__(self, *args, **kwargs):
            self.result, self.fix_requested, self.error_text = None, True, "Fehlertext"

        def exec(self):
            return False

    monkeypatch.setattr(exe_flow, "BuildDialog", FailedBuild)
    monkeypatch.setattr(exe_flow, "confirm", lambda *a, **k: True)
    monkeypatch.setattr(exe, "find_python", lambda: ["py"])
    monkeypatch.setattr(exe, "read_settings", lambda folder: exe.BuildSettings("main.py", "R"))
    fixes = []
    monkeypatch.setattr(exe_flow.ExeActions, "fix_with_ai",
                        lambda self, p, error: fixes.append(error))
    win.controller.exe.build(ActionContext(win.services, project, Target.EXE))
    assert fixes == ["Fehlertext"]


def test_fix_with_ai_starts_without_a_wish(exe_window, monkeypatch):
    from cockpit.ui import exe_ai
    win, project, _built, _shown = exe_window
    started = []
    monkeypatch.setattr(exe_ai.ExeAIFlow, "start_fix", lambda self, error: started.append(error))
    win.controller.exe.fix_with_ai(project, "Fehlertext")
    assert started == ["Fehlertext"]


def test_start_fix_shows_progress_and_sends_the_error(exe_window, monkeypatch):
    from cockpit.ui import exe_ai
    win, project, _built, _shown = exe_window
    asked, shown = [], []

    class AI(FakeTextAI):
        def ask(self, prompt, system="", cancel=None):
            asked.append(prompt)
            return "ZUSAMMENFASSUNG: Keine Änderung am Code nötig."

    monkeypatch.setattr(exe_ai.ExeAIFlow, "_ai", lambda self, purpose: AI())

    class Work(exe_ai.WorkDialog):
        def exec(self):
            shown.append(self.what)
            return super().exec()

    monkeypatch.setattr(exe_ai, "WorkDialog", Work)
    finished = []
    flow = exe_ai.ExeAIFlow(win.controller.exe, project,
                            on_finished=lambda lines, folder=None: finished.append(lines))
    flow.start_fix("Traceback: ModuleNotFoundError: No module named 'vokabeln'")
    assert shown == ["Die KI versucht, das Problem zu lösen"]
    assert "No module named 'vokabeln'" in asked[0]
    assert finished and finished[0][0].startswith("Es gibt keine Änderung")


def test_error_excerpts_find_the_lines(projects_root):
    from cockpit.features.exe_build import ai_fix
    code, _settings = exe_code(projects_root)
    (code / "gui.py").write_text("\n".join(f"zeile {n}" for n in range(1, 40)), encoding="utf-8")
    error = (f'File "{code / "gui.py"}", line 20, in <module>\n'
             'File "C:\\Python314\\Lib\\os.py", line 5\nKeyError')
    found = ai_fix.error_excerpts(code, error)
    assert [name for name, _text in found] == ["gui.py"]           # nur Dateien im Ordner Code
    assert "zeile 20" in found[0][1]


def test_prompt_contains_the_error():
    from cockpit.core import exe
    from cockpit.features.exe_build import ai_fix
    prompt, system = ai_fix.build_prompt("Rechner", exe.BuildSettings("main.py", "Rechner"),
                                         [], "", "code", "X" * 5000 + "Ende des Fehlers")
    assert "Fehler beim letzten Bau oder Test der Exe:" in prompt
    assert "Ende des Fehlers" in prompt and "X" * 4100 not in prompt
    assert "behebe vor allem diesen Fehler" in system
    plain, _ = ai_fix.build_prompt("Rechner", exe.BuildSettings("main.py", "Rechner"), [], "",
                                   "code")
    assert "Fehler beim letzten Bau oder Test der Exe:\nkeiner" in plain


def test_second_round_reads_the_branch(tmp_path, projects_root, make_services, qtbot):
    """Mehrere Durchgänge: Gibt es Cockpit-exe-bauen schon, liest die KI dort weiter."""
    from cockpit.features.exe_build import exe_branch
    from cockpit.ui import exe_ai
    services, project, _other = structured(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    assert exe_ai.ExeAIFlow(win.controller.exe, project).source_dir == project.code_dir
    folder = exe_branch.prepare(project)
    finished = []
    flow = exe_ai.ExeAIFlow(win.controller.exe, project,
                            on_finished=lambda lines, folder=None: finished.append(folder))
    assert flow.source_dir == folder
    flow._finish(["Nichts geändert."])
    assert finished == [folder]                     # gebaut wird wieder aus dem Branch


# -- 2. Stand hinter den Aktionen -------------------------------------------------------------
def test_entry_label_with_detail():
    action = Action("x", "Änderungen auf GitHub hochladen …", Target.CODE, lambda c: None)
    assert ActionEntry(action, Availability.yes(), "3 Dateien offen").label == \
        "Änderungen auf GitHub hochladen …, 3 Dateien offen"
    assert ActionEntry(action, Availability.no("Kein Git."), "3 Dateien offen").label == \
        "Änderungen auf GitHub hochladen …, nicht verfügbar: Kein Git."


def test_broken_detail_never_breaks_the_list():
    def broken(context):
        raise RuntimeError("kaputt")

    action = Action("x", "Test", Target.CODE, lambda c: None, detail=broken)
    found = entries_for([action], ActionContext(None, None, Target.CODE))
    assert found[0].label == "Test"


def status_with(pending=0, ahead=0, behind=0, changed=(), pulls=0):
    repo = RepoStatus(is_repo=True, branch="main", upstream="origin/main", ahead=ahead,
                      behind=behind, changed=list(changed), remote_url="x", has_commits=True)
    return ProjectStatus(1, repo, pending=pending, open_pulls=pulls)


@pytest.mark.parametrize("status, push, pull, discard", [
    (status_with(), "nichts offen", "alles aktuell", "nichts geändert"),
    (status_with(pending=3, changed=["a", "b", "c"]), "3 Dateien offen", "alles aktuell",
     "3 Dateien geändert"),
    (status_with(ahead=1, behind=2), "1 Commit nicht hochgeladen", "2 neue Änderungen",
     "nichts geändert"),
])
def test_code_actions_say_what_is_open(status, push, pull, discard):
    from cockpit.ui import project_actions as pa
    context = ActionContext(None, None, Target.CODE, status=status)
    assert pa._push_detail(context) == push
    assert pa._pull_detail(context) == pull
    assert pa._changed_detail(context) == discard
    assert pa._push_detail(ActionContext(None, None, Target.CODE)) == ""     # Stand unbekannt


def test_pull_requests_say_how_many_are_open(qtbot, tmp_path, projects_root, make_services):
    from cockpit.platforms.base import PullRequest
    services, project, _other = structured(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    online = dataclasses.replace(project, remote=REMOTE_ADDRESS)
    context = ActionContext(services, online, Target.CODE)
    detail = win.controller._all_pulls_detail
    assert detail(context) == "keine offen"
    services.pull_request_cache.replace(REMOTE_ADDRESS, [
        PullRequest(1, "Design", "design", "main", "Anna"),
        PullRequest(2, "Suche", "suche", "main", "Ben")])
    assert detail(context) == "2 offen"
    status = project_status.compute(project)
    action = next(e.action for e in entries(win, online, Target.CODE, status)
                  if e.action.id == "pull_requests")
    assert action.detail is not None
    status.open_pulls = 1
    from cockpit.ui.project_actions import _branch_pulls_detail
    assert _branch_pulls_detail(ActionContext(services, online, Target.CODE,
                                              status=status)) == "1 offen"


def test_exe_states(tmp_path, projects_root, make_services, monkeypatch):
    from cockpit.core import exe
    services, project, _other = structured(tmp_path, projects_root, make_services)
    assert exe.build_state(project) == "noch keine Exe"
    project.exe_dir.mkdir(parents=True, exist_ok=True)
    (project.exe_dir / "Tagebuch.exe").write_bytes(b"MZ")
    head = exe.head_commit(project.code_dir)
    exe.write_record(project.code_dir, exe.ExeRecord("cockpit", "2026-10-02T10:00:00", head))
    assert exe.build_state(project) == "Exe aktuell"
    assert exe.publish_state(project) == "noch nicht veröffentlicht"
    exe.write_record(project.code_dir, exe.ExeRecord("cockpit", "2026-10-02T10:00:00", "alt",
                                                     version="1.2.0"))
    assert exe.build_state(project) == "Code geändert seit dem letzten Bau"
    assert exe.publish_state(project) == "zuletzt Version 1.2.0"


# -- 3. Branches anzeigen ---------------------------------------------------------------------
def overview(qtbot, project, folders=None):
    from cockpit.core import branches
    dialog = BranchesDialog(project, branches.list_branches(project.code_dir),
                            folders=folders or {})
    qtbot.addWidget(dialog)
    dialog.show()
    return dialog


def rows(dialog) -> list[str]:
    return [dialog.list.item(r).text() for r in range(dialog.list.count())]


def test_overview_shows_local_branches_first(qtbot, tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    dialog = overview(qtbot, project)
    lines = rows(dialog)
    assert lines[0] == "Neuer Branch …"
    assert lines[1] == f"{SHOW_PREFIX}Die Sie lokal haben"
    names = [b.name for b in dialog.items]
    assert "design" not in names and "main" in names              # design liegt nur auf GitHub
    dialog.set_show(REMOTE)
    assert [b.name for b in dialog.items] == ["design"]
    assert rows(dialog)[1] == f"{SHOW_PREFIX}Die nur auf GitHub sind"
    assert said("Die nur auf GitHub sind: 1 Branch.")
    dialog.set_show(ALL)
    assert {"design", "main", "suche"} <= {b.name for b in dialog.items}


def test_space_and_enter_open_the_choice(qtbot, tmp_path, projects_root, make_services,
                                         monkeypatch):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    opened = []
    monkeypatch.setattr(BranchesDialog, "choose_show", lambda self: opened.append(True))
    dialog = overview(qtbot, project)
    dialog.list.setCurrentRow(1)
    dialog.list.setFocus()
    qtbot.keyClick(dialog.list, Qt.Key.Key_Space)
    qtbot.keyClick(dialog.list, Qt.Key.Key_Return)
    assert opened == [True, True]


def test_remote_only_branch_can_be_downloaded_renamed_deleted(qtbot, tmp_path, projects_root,
                                                              make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    dialog = overview(qtbot, project)
    dialog.set_show(REMOTE)
    dialog.list.setCurrentRow(dialog.row_of("design"))
    assert dialog.switch_button.isVisible() and dialog.switch_button.text() == "&Herunterladen"
    assert dialog.rename_button.isVisible() and dialog.delete_button.isVisible()
    assert not dialog.merge_button.isVisible()


def test_merge_button_says_what_is_open(qtbot, tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    dialog = overview(qtbot, project)
    dialog.list.setCurrentRow(dialog.row_of("suche"))
    assert dialog.merge_button.text() == "In &main übernehmen …, 2 Commits offen"
    sh(project.code_dir, "merge", "-q", "suche")
    dialog.reload("suche")
    dialog.list.setCurrentRow(dialog.row_of("suche"))
    assert dialog.merge_button.text() == "In &main übernehmen …, alles aktuell"


def test_filtered():
    from cockpit.core.branches import Branch
    items = [Branch("main", local=True, remote=True), Branch("design", remote=True),
             Branch("lokal", local=True)]
    assert [b.name for b in filtered(items, LOCAL)] == ["main", "lokal"]
    assert [b.name for b in filtered(items, REMOTE)] == ["design"]
    assert len(filtered(items, ALL)) == 3


def test_project_list_shows_only_local_branches(tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    worktrees.open_branch(project, "suche")
    targets = [target for _text, target, _key in
               children_of(project, project_status.compute(project))]
    assert Target.REMOTE_BRANCHES not in targets and Target.REMOTE_BRANCH not in targets
    assert targets == [Target.CODE, Target.BRANCH_OVERVIEW, Target.BRANCH]


# -- 4. Reihenfolge ganz oben -----------------------------------------------------------------
def test_collections_and_projects_are_mixed_by_date(qtbot, tmp_path):
    from cockpit.core.project_collections import Collection
    from cockpit.ui.project_list import ProjectList

    def project(pid, name, day):
        folder = tmp_path / name
        (folder / "Code").mkdir(parents=True)
        return Project(pid, name, folder, folder / "Code", None,
                       last_updated=f"2026-09-{day:02d}T10:00:00")

    listing = ProjectList()
    qtbot.addWidget(listing)
    old, new, member, newest = (project(1, "Alt", 1), project(2, "Neu", 20),
                                project(3, "InSammlung", 10), project(4, "Ganz neu", 25))
    web = Collection(7, "Web")
    listing.set_projects([old, new, member, newest], [], [web], {member.id: web.id})
    names = listing.texts()[3:]
    assert [n.split(",")[0] for n in names] == ["Ganz neu", "Neu", "Sammlung Web", "Alt"]
    newer = dataclasses.replace(member, last_updated="2026-09-30T10:00:00")
    listing.set_projects([old, new, newer, newest], [], [web], {member.id: web.id})
    assert listing.texts()[3].startswith("Sammlung Web")          # jetzt ganz oben
