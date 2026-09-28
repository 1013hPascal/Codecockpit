"""Phase 5f: Übersicht "Branches" und beiseitegelegte Änderungen (Stash).

Die "Plattform" ist ein nacktes Repository auf der Festplatte, ein zweiter Klon spielt den anderen
Rechner. Kein echtes Netz.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from cockpit.core import backups, branches, git, project_status, sync
from cockpit.core.errors import CockpitError
from cockpit.core.sync import ConflictKind
from cockpit.ui import branch_dialogs
from tests.conftest import said
from tests.test_phase5a import live, sh, wait_idle  # noqa: F401
from tests.test_phase5b import write
from tests.test_phase5c import head, labels, select_code, setup_repo

# Die Commits der Tests macht "Test" (siehe sh), heute
BY = f"zuletzt von Test am {datetime.now():%d.%m.%Y}"

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


def commit(code: Path, message: str, files: dict[str, str]) -> None:
    for name, text in files.items():
        write(code, name, text)
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", message)


def read(code: Path, name: str) -> str:
    return (code / name).read_text(encoding="utf-8")


def branch_repo(tmp_path, projects_root):
    """Tagebuch mit Branch suche (2 Commits, hochgeladen), lokal-neu (1 Commit, nur hier) und
    design (nur auf der Plattform)."""
    bare, code, other = setup_repo(tmp_path, projects_root)
    sh(code, "switch", "-q", "-c", "suche")
    commit(code, "Suche 1", {"suche.py": "1\n"})
    commit(code, "Suche 2", {"suche.py": "2\n"})
    sh(code, "push", "-q", "-u", "origin", "suche")
    sh(code, "switch", "-q", "main")
    sh(code, "switch", "-q", "-c", "lokal-neu")
    commit(code, "Nur lokal", {"lokal.py": "x\n"})
    sh(code, "switch", "-q", "main")
    sh(other, "switch", "-q", "-c", "design")
    commit(other, "Design", {"design.css": "body {}\n"})
    sh(other, "push", "-q", "-u", "origin", "design")
    branches.refresh(code)
    return bare, code, other


def by_name(code: Path) -> dict[str, branches.Branch]:
    return {b.name: b for b in branches.list_branches(code)}


# -- Übersicht --------------------------------------------------------------------------------
def test_list_branches_local_and_remote(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    items = branches.list_branches(code)
    assert items[0].name == "main" and items[0].current and items[0].default
    lines = {b.name: b.line() for b in items}
    # Wunsch aus dem Test von 5f: Name, Ort, wer zuletzt daran gearbeitet hat, dann der Stand
    assert lines["main"] == f"main, aktueller Branch, Haupt-Branch, hier und auf GitHub, {BY}"
    assert lines["suche"] == f"suche, hier und auf GitHub, {BY}, 2 Commits vor main"
    assert lines["lokal-neu"] == f"lokal-neu, nur hier, {BY}, 1 Commit vor main"
    assert lines["design"] == f"design, nur auf GitHub, {BY}, 1 Commit vor main"


def test_line_shows_upload_state_and_behind_main(tmp_path, projects_root):
    _, code, other = branch_repo(tmp_path, projects_root)
    sh(code, "switch", "-q", "suche")
    commit(code, "Suche 3", {"suche.py": "3\n"})
    sh(code, "switch", "-q", "main")
    commit(code, "Main weiter", {"main.py": "neu\n"})
    line = by_name(code)["suche"].line("main", "GitHub")
    assert line == (f"suche, hier und auf GitHub, {BY}, 3 Commits vor main, 1 Commit hinter "
                    "main, 1 Commit noch nicht hochgeladen")
    sh(code, "switch", "-q", "-c", "gleich")
    assert by_name(code)["gleich"].line() == (f"gleich, aktueller Branch, nur hier, {BY}, "
                                              "gleich wie main")


def test_refresh_forgets_deleted_remote_branches(tmp_path, projects_root):
    _, code, other = branch_repo(tmp_path, projects_root)
    sh(other, "push", "-q", "origin", "--delete", "design")
    branches.refresh(code)
    assert "design" not in by_name(code)


def test_name_problems(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    assert branches.name_problem(code, "neue-suche") == ""
    assert "Leerzeichen" in branches.name_problem(code, "neue suche")
    assert "erlaubt Git nicht" in branches.name_problem(code, "a..b")
    assert branches.name_problem(code, "Suche") == "Einen Branch Suche gibt es schon."
    assert branches.name_problem(code, "") == "Bitte geben Sie einen Namen ein."
    assert branches.suggest_name("Suche in PDFs für Größe!") == "suche-in-pdfs-fuer-groesse"


# -- Anlegen, wechseln ------------------------------------------------------------------------
def test_create_takes_changes_along(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    write(code, "main.py", "geändert\n")
    branches.create(code, "neu")
    assert git.status(code).branch == "neu"
    assert read(code, "main.py") == "geändert\n"
    with pytest.raises(CockpitError, match="gibt es schon"):
        branches.create(code, "neu")


def test_switch_to_a_branch_only_on_the_platform(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    branches.switch(code, "design")
    state = git.status(code)
    assert state.branch == "design" and state.upstream == "origin/design"
    assert read(code, "design.css") == "body {}\n"


def test_switch_refuses_to_overwrite_changes(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    sh(code, "switch", "-q", "suche")
    write(code, "suche.py", "meine\n")
    with pytest.raises(CockpitError, match="Git würde sie überschreiben"):
        branches.switch(code, "main")
    assert git.status(code).branch == "suche" and read(code, "suche.py") == "meine\n"


# -- Umbenennen, löschen --------------------------------------------------------------------
def test_rename_local_and_on_the_platform(tmp_path, projects_root):
    bare, code, _ = branch_repo(tmp_path, projects_root)
    branches.rename_local(code, "suche", "pdf-suche")
    branches.rename_remote(code, "suche", "pdf-suche")
    remote = sh(bare, "branch", "--list").split()
    assert "pdf-suche" in remote and "suche" not in remote
    item = by_name(code)["pdf-suche"]
    assert item.local and item.remote and item.upstream == "origin/pdf-suche"
    assert "suche" not in by_name(code)


def test_rename_a_branch_only_on_the_platform(tmp_path, projects_root):
    bare, code, _ = branch_repo(tmp_path, projects_root)
    branches.rename_remote(code, "design", "neues-design", local=False)
    remote = sh(bare, "branch", "--list").split()
    assert "neues-design" in remote and "design" not in remote
    assert not by_name(code)["neues-design"].local


def test_delete_local_keeps_the_commits(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    tip = head(code, "lokal-neu")
    assert branches.unmerged(code, "lokal-neu") == 1
    assert branches.unmerged(code, "suche") == 0                  # liegt auf der Plattform
    keep = branches.delete_local(code, "lokal-neu")
    assert "lokal-neu" not in by_name(code)
    assert head(code, keep) == tip                                # nichts verloren
    with pytest.raises(CockpitError, match="aktuelle Branch"):
        branches.delete_local(code, "main")


def test_delete_on_the_platform(tmp_path, projects_root):
    bare, code, _ = branch_repo(tmp_path, projects_root)
    branches.delete_remote(code, "design")
    branches.refresh(code)
    assert "design" not in sh(bare, "branch", "--list")
    assert "design" not in by_name(code)
    kept = sh(code, "for-each-ref", "--format=%(refname)", branches.DELETED_REF)
    assert "design-github-" in kept
    with pytest.raises(CockpitError, match="Haupt-Branch"):
        branches.delete_remote(code, "main")


# -- In main übernehmen ----------------------------------------------------------------------
def test_merge_into_main(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    preview = branches.merge_preview(code, "suche")
    assert preview.behind == 2 and preview.files == ["suche.py"]
    outcome = branches.merge_into_current(code, "Tagebuch", "suche")
    assert outcome.kind is ConflictKind.NONE
    assert read(code, "suche.py") == "2\n"
    assert sh(code, "log", "-1", "--format=%s").strip() in ("Merge branch 'suche'", "Suche 2")
    info = backups.all_backups()[0]
    assert info.reason == "vor dem Übernehmen"


def test_merge_with_conflict_and_label(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    sh(code, "switch", "-q", "suche")
    commit(code, "Suche ändert main", {"main.py": "SUCHE\n"})
    sh(code, "switch", "-q", "main")
    commit(code, "Main ändert main", {"main.py": "MAIN\n"})
    before = head(code)
    outcome = branches.merge_into_current(code, "Tagebuch", "suche")
    assert outcome.kind is ConflictKind.MERGE and outcome.conflicts == ["main.py"]
    assert sync.merge_source_label(code, "GitHub") == "Branch suche"
    sync.abort(code, ConflictKind.MERGE)
    assert head(code) == before and read(code, "main.py") == "MAIN\n"


def test_merge_label_after_pull_is_the_platform(tmp_path, projects_root):
    from tests.test_phase5c import merge_conflict
    code, *_ = merge_conflict(tmp_path, projects_root)
    assert sync.merge_source_label(code, "GitHub") == "GitHub"


def test_merge_needs_a_clean_folder(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    write(code, "main.py", "x\n")
    with pytest.raises(CockpitError, match="Änderungen ohne Commit"):
        branches.merge_into_current(code, "Tagebuch", "suche")


# -- Beiseitelegen ---------------------------------------------------------------------------
def test_stash_push_list_and_restore(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    write(code, "main.py", "meine\n")
    write(code, "neu.txt", "n\n")
    folder = branches.stash_push(code, "Tagebuch")
    assert backups.read_info(folder).reason == "vor dem Beiseitelegen"
    assert sync.changes(code).files == []
    items = branches.stashes(code)
    assert len(items) == 1 and items[0].branch == "main"
    assert items[0].files == ["main.py", "neu.txt"]
    assert items[0].line().endswith(", auf main, 2 Dateien: main.py und neu.txt")
    assert git.status(code).stashes == 1
    assert branches.stash_for_branch(code, "main") is not None
    assert branches.stash_for_branch(code, "suche") is None
    branches.stash_restore(code, items[0])
    assert read(code, "main.py") == "meine\n" and read(code, "neu.txt") == "n\n"
    assert branches.stashes(code) == []


def test_stash_restore_that_does_not_fit_changes_nothing(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    write(code, "main.py", "meine\n")
    write(code, "neu.txt", "n\n")
    branches.stash_push(code, "Tagebuch")
    commit(code, "Main anders", {"main.py": "anders\n"})
    with pytest.raises(CockpitError, match="passen nicht mehr"):
        branches.stash_restore(code, branches.stashes(code)[0])
    assert read(code, "main.py") == "anders\n" and not (code / "neu.txt").exists()
    assert sh(code, "status", "--porcelain").strip() == ""
    assert len(branches.stashes(code)) == 1                        # bleibt beiseitegelegt


def test_stash_restore_needs_a_clean_folder(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    write(code, "main.py", "meine\n")
    branches.stash_push(code, "Tagebuch")
    write(code, "anderes.py", "x\n")
    with pytest.raises(CockpitError, match="Änderungen ohne Commit"):
        branches.stash_restore(code, branches.stashes(code)[0])


def test_stash_to_branch_always_fits(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    write(code, "main.py", "meine\n")
    branches.stash_push(code, "Tagebuch")
    commit(code, "Main anders", {"main.py": "anders\n"})
    branches.stash_to_branch(code, branches.stashes(code)[0], "gerettet")
    assert git.status(code).branch == "gerettet"
    assert read(code, "main.py") == "meine\n"
    assert branches.stashes(code) == []


def test_stash_drop_makes_a_backup(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    write(code, "main.py", "meine\n")
    write(code, "unter/neu.txt", "n\n")
    branches.stash_push(code, "Tagebuch")
    folder = branches.stash_drop(code, "Tagebuch", branches.stashes(code)[0])
    assert branches.stashes(code) == []
    assert (folder / "main.py").read_text(encoding="utf-8") == "meine\n"
    assert (folder / "unter" / "neu.txt").read_text(encoding="utf-8") == "n\n"
    assert backups.read_info(folder).reason == "beiseitegelegt, gelöscht"


def test_pull_stash_is_listed_as_before_pulling(tmp_path, projects_root):
    _, code, _ = branch_repo(tmp_path, projects_root)
    write(code, "main.py", "x\n")
    sh(code, "stash", "push", "-q", "-m", sync.STASH_MESSAGE)
    assert branches.stashes(code)[0].line().endswith("vor dem Holen")


# -- Stand in der Liste --------------------------------------------------------------------
def test_code_line_for_new_branch_and_stash(make_services, tmp_path, projects_root):
    services = make_services()
    _, code, _ = branch_repo(tmp_path, projects_root)
    project = services.projects.add(code.parent)
    sh(code, "switch", "-q", "lokal-neu")
    status = project_status.compute(project)
    assert project_status.code_line(status) == "Code, Branch lokal-neu, Branch noch nicht auf GitHub"
    sh(code, "switch", "-q", "main")
    write(code, "main.py", "x\n")
    branches.stash_push(code, "Tagebuch")
    status = project_status.compute(project)
    assert project_status.code_line(status) == ("Code, alles hochgeladen, "
                                                "Änderungen beiseitegelegt")
    assert status.repo.has_commits


def test_empty_repository_has_no_commits(tmp_path):
    code = tmp_path / "leer"
    code.mkdir()
    git.init(code)
    assert not git.status(code).has_commits


# -- Aktionen und Fenster ---------------------------------------------------------------------
@pytest.fixture
def answers(monkeypatch):
    class Answers:
        yes = True
        choice = 0
    record = Answers()
    record.questions, record.errors = [], []

    def confirm(parent, title, text, **k):
        record.questions.append((title, text, k))
        return record.yes

    def ask_buttons(parent, title, text, buttons, default, escape):
        record.questions.append((title, text, {"buttons": buttons, "default": default}))
        return record.choice

    monkeypatch.setattr(branch_dialogs, "confirm", confirm)
    monkeypatch.setattr(branch_dialogs, "ask_buttons", ask_buttons)
    monkeypatch.setattr(branch_dialogs, "show_error", lambda *a: record.errors.append(a[2]))
    return record


def dialog_for(qtbot, make_services, code):
    services = make_services()
    project = services.projects.find_by_dir(code.parent) or services.projects.add(code.parent)
    dialog = branch_dialogs.BranchesDialog(project, branches.list_branches(code))
    qtbot.addWidget(dialog)
    return dialog


def rows(dialog) -> list[str]:
    return [dialog.list.item(i).text() for i in range(dialog.list.count())]


def select(dialog, name: str) -> None:
    dialog.list.setCurrentRow([b.name for b in dialog.items].index(name))


def test_code_actions(live, qtbot, make_services, projects_root, tmp_path):
    services = make_services()
    _, code, _ = branch_repo(tmp_path, projects_root)
    win = live(services)
    select_code(win, services, code)
    texts = labels(win)
    assert texts.index("Branches …") < texts.index("Verlauf …")
    assert "Änderungen beiseitelegen …, nicht verfügbar: Es gibt keine Änderungen ohne Commit." \
        in texts
    assert "Beiseitegelegte Änderungen …" not in texts
    write(code, "main.py", "x\n")
    branches.stash_push(code, "Tagebuch")
    win.refresh_status()
    wait_idle(qtbot, win)
    assert "Beiseitegelegte Änderungen …" in labels(win)


def test_branches_from_the_window(live, qtbot, make_services, projects_root, tmp_path,
                                  monkeypatch):
    services = make_services()
    _, code, _ = branch_repo(tmp_path, projects_root)
    win = live(services)
    select_code(win, services, code)
    shown = []

    class FakeBranches:
        new_request = open_request = ""

        def __init__(self, project, items, env, platform_name, parent=None, folders=None):
            shown.append([b.name for b in items])

        def exec(self):
            return 0

    monkeypatch.setattr(branch_dialogs, "BranchesDialog", FakeBranches)
    entry = next(e for e in win.current_entries() if e.action.id == "branches")
    win.run_entry(entry)
    qtbot.waitUntil(lambda: bool(shown), timeout=10000)
    assert shown[0][0] == "main" and "design" in shown[0]
    wait_idle(qtbot, win)


def test_stash_push_from_the_window(live, qtbot, make_services, projects_root, tmp_path,
                                    monkeypatch):
    from cockpit.ui import project_actions
    services = make_services()
    _, code, _ = branch_repo(tmp_path, projects_root)
    write(code, "main.py", "x\n")
    win = live(services)
    select_code(win, services, code)
    questions = []
    monkeypatch.setattr(project_actions, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or True)
    entry = next(e for e in win.current_entries() if e.action.id == "stash_push")
    win.run_entry(entry)
    assert questions[0][0].startswith("Alle Änderungen ohne Commit werden beiseitegelegt: "
                                      "1 Datei geändert.")
    assert questions[0][1] == {"yes": "Beiseitelegen", "no": "Abbrechen"}
    assert said("Änderungen beiseitegelegt.")
    assert len(branches.stashes(code)) == 1
    wait_idle(qtbot, win)


def test_dialog_lines_and_enter_switches(qtbot, make_services, tmp_path, projects_root, answers):
    from PySide6.QtCore import Qt
    _, code, _ = branch_repo(tmp_path, projects_root)
    dialog = dialog_for(qtbot, make_services, code)
    assert dialog.windowTitle() == "Branches von Tagebuch: 4 Branches"
    assert rows(dialog)[0] == f"main, aktueller Branch, Haupt-Branch, hier und auf GitHub, {BY}"
    dialog.switch_current()
    assert said("Sie sind schon auf main.")
    select(dialog, "design")
    qtbot.keyClick(dialog.list, Qt.Key.Key_Return)
    assert git.status(code).branch == "design"
    assert said("Gewechselt zu design.")
    assert dialog.changed and dialog.list.currentItem().text().startswith("design, aktueller")


def test_switch_with_changes_asks_and_offers_restore(qtbot, make_services, tmp_path,
                                                     projects_root, answers):
    _, code, _ = branch_repo(tmp_path, projects_root)
    dialog = dialog_for(qtbot, make_services, code)
    write(code, "main.py", "meine\n")
    answers.choice = 2                                             # Abbrechen
    select(dialog, "suche")
    dialog.switch_current()
    assert git.status(code).branch == "main"
    title, text, extra = answers.questions[0]
    assert text.startswith("Sie haben Änderungen ohne Commit: 1 Datei geändert. Beiseitelegen:")
    assert extra == {"buttons": ["Beiseitelegen und wechseln", "Mitnehmen und wechseln",
                                 "Abbrechen"], "default": 2}
    answers.choice = 0                                             # beiseitelegen
    dialog.switch_current()
    assert git.status(code).branch == "suche" and read(code, "main.py") == "a\nb\nc\n"
    assert branches.stashes(code)[0].branch == "main"
    select(dialog, "main")
    dialog.switch_current()                                        # zurück: Angebot
    title, text, buttons = answers.questions[-1]
    assert text.startswith("Auf main haben Sie am ")
    assert buttons == {"yes": "Zurückholen", "no": "Später"}
    assert read(code, "main.py") == "meine\n"
    assert said("Änderungen zurückgeholt.")


def test_switch_taking_changes_along(qtbot, make_services, tmp_path, projects_root, answers):
    _, code, _ = branch_repo(tmp_path, projects_root)
    dialog = dialog_for(qtbot, make_services, code)
    write(code, "main.py", "meine\n")
    answers.choice = 1
    select(dialog, "suche")
    dialog.switch_current()
    assert git.status(code).branch == "suche" and read(code, "main.py") == "meine\n"
    assert branches.stashes(code) == []


def test_new_branch(qtbot, make_services, tmp_path, projects_root, answers, monkeypatch):
    _, code, _ = branch_repo(tmp_path, projects_root)
    dialog = dialog_for(qtbot, make_services, code)

    class FakeName:
        def __init__(self, title, hint, code_dir, current="", parent=None):
            assert hint.startswith("Er beginnt bei main.")
            self.name = "neue-idee"

        def exec(self):
            return 1

    monkeypatch.setattr(branch_dialogs, "BranchNameDialog", FakeName)
    dialog.new_branch()
    assert git.status(code).branch == "neue-idee"
    assert said("Branch neue-idee angelegt. Sie sind jetzt auf neue-idee.")
    assert dialog.list.currentItem().text() == (
        f"neue-idee, aktueller Branch, nur hier, {BY}, gleich wie main")


def test_branch_name_dialog(qtbot, tmp_path, projects_root, monkeypatch):
    _, code, _ = branch_repo(tmp_path, projects_root)
    errors = []
    monkeypatch.setattr(branch_dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog = branch_dialogs.BranchNameDialog("Neuer Branch", "Hinweis", code)
    qtbot.addWidget(dialog)
    assert dialog.edit.accessibleName() == "Name des Branches"
    dialog.edit.setText("mit leer")
    dialog.check()
    assert "Leerzeichen" in errors[0] and dialog.result() == 0
    dialog.edit.setText("ohne-leer")
    dialog.check()
    assert dialog.name == "ohne-leer" and dialog.result() == 1


def test_merge_into_main_from_another_branch(qtbot, make_services, tmp_path, projects_root,
                                             answers):
    _, code, _ = branch_repo(tmp_path, projects_root)
    sh(code, "switch", "-q", "suche")
    dialog = dialog_for(qtbot, make_services, code)
    assert dialog.merge_button.text() == "In &main übernehmen …"
    select(dialog, "main")
    dialog.merge_current()
    assert "selbst der Haupt-Branch" in answers.errors[-1]
    select(dialog, "suche")
    answers.yes = False
    dialog.merge_current()
    title, text, buttons = answers.questions[-1]
    assert text.startswith("Das Cockpit wechselt zu main. Die 2 Commits aus suche kommen in main")
    assert buttons == {"yes": "Übernehmen", "no": "Abbrechen"}
    assert git.status(code).branch == "suche"                     # Escape: nichts passiert
    answers.yes = True
    dialog.merge_current()
    assert git.status(code).branch == "main" and read(code, "suche.py") == "2\n"
    assert said("suche ist in main übernommen. main ist noch nicht hochgeladen.")


def test_merge_conflict_opens_the_conflict_window(qtbot, make_services, tmp_path, projects_root,
                                                  answers, monkeypatch):
    _, code, _ = branch_repo(tmp_path, projects_root)
    sh(code, "switch", "-q", "suche")
    commit(code, "Suche ändert main", {"main.py": "SUCHE\n"})
    sh(code, "switch", "-q", "main")
    commit(code, "Main ändert main", {"main.py": "MAIN\n"})
    labels_seen = []

    class KeepMine:
        def __init__(self, code_dir, kind, label, parent=None):
            labels_seen.append(label)
            sync.resolve(code_dir, "main.py", kind, True)

        def exec(self):
            return 1

    monkeypatch.setattr(branch_dialogs.sync_dialogs, "ConflictDialog", KeepMine)
    dialog = dialog_for(qtbot, make_services, code)
    select(dialog, "suche")
    dialog.merge_current()
    assert labels_seen == ["Branch suche"]
    assert read(code, "main.py") == "MAIN\n" and not sync.merging(code)
    assert said("suche ist in main übernommen. main ist noch nicht hochgeladen.")


def test_rename_and_delete_in_the_dialog(qtbot, make_services, tmp_path, projects_root,
                                         answers, monkeypatch):
    bare, code, _ = branch_repo(tmp_path, projects_root)
    dialog = dialog_for(qtbot, make_services, code)

    class FakeName:
        def __init__(self, title, hint, code_dir, current="", parent=None):
            self.name = current + "-2"

        def exec(self):
            return 1

    monkeypatch.setattr(branch_dialogs, "BranchNameDialog", FakeName)
    select(dialog, "main")
    dialog.rename_current()
    assert "Haupt-Branch" in answers.errors[-1]
    select(dialog, "suche")
    dialog.rename_current()
    assert "Offene Pull Requests zum alten Namen werden dabei geschlossen." in \
        answers.questions[-1][1]
    qtbot.waitUntil(lambda: not dialog.worker.busy, timeout=10000)
    assert said("suche heißt jetzt suche-2, auch auf GitHub.")
    assert "suche-2" in sh(bare, "branch", "--list")

    select(dialog, "lokal-neu")
    dialog.delete_current()
    text = answers.questions[-1][1]
    assert "Er enthält 1 Commit, die es sonst nirgends gibt." in text
    assert "lokal-neu" not in [b.name for b in dialog.items]
    assert said("lokal-neu gelöscht.")

    answers.choice = 2                                             # hier und auf GitHub
    select(dialog, "suche-2")
    dialog.delete_current()
    assert answers.questions[-1][2]["buttons"] == ["Nur auf diesem Rechner", "Nur auf GitHub",
                                                   "Hier und auf GitHub", "Abbrechen"]
    assert answers.questions[-1][2]["default"] == 3
    qtbot.waitUntil(lambda: not dialog.worker.busy, timeout=10000)
    assert said("suche-2 gelöscht, auch auf GitHub.")
    assert "suche-2" not in sh(bare, "branch", "--list")


def test_stash_dialog(qtbot, make_services, tmp_path, projects_root, monkeypatch):
    _, code, _ = branch_repo(tmp_path, projects_root)
    services = make_services()
    project = services.projects.add(code.parent)
    write(code, "main.py", "eins\n")
    branches.stash_push(code, "Tagebuch")
    write(code, "main.py", "zwei\n")
    branches.stash_push(code, "Tagebuch")
    questions, errors = [], []
    monkeypatch.setattr(branch_dialogs, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or True)
    monkeypatch.setattr(branch_dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog = branch_dialogs.StashDialog(project)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Beiseitegelegte Änderungen von Tagebuch: 2 Einträge"
    assert rows(dialog)[0].endswith(", auf main, 1 Datei: main.py")
    dialog.restore_current()                                       # der neueste: "zwei"
    assert questions[-1][1] == {"yes": "Zurückholen", "no": "Abbrechen"}
    assert read(code, "main.py") == "zwei\n" and dialog.changed
    dialog.restore_current()                                       # jetzt mit Änderungen
    assert "Änderungen ohne Commit" in errors[-1]
    sh(code, "checkout", "--", "main.py")

    class FakeName:
        def __init__(self, title, hint, code_dir, current="", parent=None):
            assert current.startswith("beiseitegelegt-")
            self.name = "gerettet"

        def exec(self):
            return 1

    monkeypatch.setattr(branch_dialogs, "BranchNameDialog", FakeName)
    write(code, "x.py", "x\n")
    branches.stash_push(code, "Tagebuch")
    dialog.fill()
    dialog.list.setCurrentRow(0)
    dialog.delete_current()
    assert "als Sicherheitskopie" in questions[-1][0]
    assert said("Beiseitegelegte Änderungen gelöscht.")
    dialog.branch_current()
    assert git.status(code).branch == "gerettet" and read(code, "main.py") == "eins\n"
    assert rows(dialog) == ["Nichts beiseitegelegt."]


def test_testdata_have_branches_and_a_stash(tmp_path, monkeypatch):
    from cockpit import testdata
    from cockpit.core.paths import HOME_VARIABLE
    monkeypatch.setenv(HOME_VARIABLE, str(tmp_path / "vorher"))
    _, root = testdata.prepare(tmp_path / "Testdaten")
    pdf = root / "PDF-Chat" / "Code"
    lines = {b.name: b.line() for b in branches.list_branches(pdf)}
    assert lines["suche-pdfs"] == ("suche-pdfs, hier und auf GitHub, zuletzt von Testdaten am "
                                   "24.09.2026, 2 Commits vor main")
    assert lines["neues-design"].startswith("neues-design, nur auf GitHub, zuletzt von Testdaten")
    stash = branches.stashes(root / "Rezepte" / "Code")
    assert len(stash) == 1 and stash[0].files == ["notiz.txt"] and stash[0].branch == "main"


def test_delete_only_on_the_platform(qtbot, make_services, tmp_path, projects_root, answers):
    """Wunsch aus dem Test von 5f: auch nur auf GitHub löschen."""
    bare, code, _ = branch_repo(tmp_path, projects_root)
    dialog = dialog_for(qtbot, make_services, code)
    answers.choice = 1
    select(dialog, "suche")
    dialog.delete_current()
    qtbot.waitUntil(lambda: not dialog.worker.busy, timeout=10000)
    assert said("suche gelöscht, auf GitHub.")
    assert "suche" not in sh(bare, "branch", "--list")
    assert by_name(code)["suche"].line() == f"suche, nur hier, {BY}, 2 Commits vor main"


def test_buttons_that_do_not_fit_are_hidden(qtbot, make_services, tmp_path, projects_root):
    """Wunsch aus dem Test von 5f: Beim Haupt-Branch gibt es kein "In main übernehmen"."""
    _, code, _ = branch_repo(tmp_path, projects_root)
    sh(code, "switch", "-q", "suche")
    dialog = dialog_for(qtbot, make_services, code)
    dialog.show()
    visible = lambda: (dialog.merge_button.isVisible(), dialog.rename_button.isVisible(),  # noqa
                       dialog.delete_button.isVisible())
    select(dialog, "main")
    assert visible() == (False, False, False)
    assert dialog.switch_button.text() == "Zu main &wechseln"      # Wunsch aus dem Test von 6a
    select(dialog, "suche")                                        # aktueller Branch
    assert visible() == (True, True, False)
    assert not dialog.switch_button.isVisible()
    select(dialog, "design")
    assert visible() == (True, True, True)


def test_branches_guide_in_the_help_menu():
    import inspect
    from cockpit.core import paths
    from cockpit.ui import main_window
    assert '"B&ranches verstehen …", self.show_branches_guide' in inspect.getsource(main_window)
    text = (paths.resource_dir() / "anleitungen" / "branches-verstehen.md").read_text(
        encoding="utf-8")
    assert "Welche Branches darf ich löschen?" in text
    assert "Git kopiert also nicht einfach alle Dateien" in text
