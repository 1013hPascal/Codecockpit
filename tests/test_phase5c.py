"""Phase 5c: Änderungen hochladen, Änderungen holen, Konflikte lösen.

Die "Plattform" ist ein nacktes Repository auf der Festplatte. Ein zweiter Klon spielt den
anderen Rechner, der Änderungen hochlädt.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cockpit.core import backups, git, project_status, sync
from cockpit.core.flows.engine import FlowContext
from cockpit.core.flows.questions import ScriptedAsker
from cockpit.core.sync import ConflictKind
from cockpit.ui import sync_dialogs, sync_flow
from tests.conftest import said
from tests.test_phase5a import (EMAIL, NAME, account, clone_into, live, make_remote,  # noqa: F401
                                sh, wait_idle)
from tests.test_phase5b import GITHUB_TOKEN, write

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


# -- Hilfen ---------------------------------------------------------------------------------
def setup_repo(tmp_path: Path, root: Path, files: dict[str, str] | None = None
               ) -> tuple[Path, Path, Path]:
    """Plattform, eigener Code-Ordner und ein zweiter Klon (anderer Rechner)."""
    bare = make_remote(tmp_path, "Tagebuch", files or {"main.py": "a\nb\nc\n",
                                                       "README.md": "# Tagebuch\n"})
    code = root / "Tagebuch" / "Code"
    clone_into(bare, code)
    git.set_identity(code, NAME, EMAIL)
    other = tmp_path / "anderer" / "Tagebuch"
    clone_into(bare, other)
    return bare, code, other


def push_from_other(other: Path, name: str, text: str, message: str = "Vom anderen Rechner"):
    write(other, name, text)
    sh(other, "add", "-A")
    sh(other, "commit", "-q", "-m", message)
    sh(other, "push", "-q")


def head(code: Path, ref: str = "HEAD") -> str:
    return sh(code, "rev-parse", ref).strip()


def stash_list(code: Path) -> str:
    return sh(code, "stash", "list").strip()


def run_push(services, code: Path, message: str):
    project = services.projects.find_by_dir(code.parent) or services.projects.add(code.parent)
    context = FlowContext(services, project, ScriptedAsker(),
                          data={"message": message, "public": False, "git_email": EMAIL})
    steps = []
    summary = services.flows.run(sync.PUSH_CHANGES, context,
                                 lambda n, total, text: steps.append(text))
    return summary, context.data, steps


# -- Änderungen lesen -----------------------------------------------------------------------
def test_changes_are_described_like_the_concept(tmp_path, projects_root):
    _, code, _ = setup_repo(tmp_path, projects_root, {"main.py": "1\n", "suche.py": "1\n",
                                                     "alt.py": "1\n", "README.md": "#\n"})
    write(code, "main.py", "2\n")
    write(code, "suche.py", "2\n")
    write(code, "README.md", "# neu\n")
    write(code, "export.py", "x\n")
    (code / "alt.py").unlink()
    changes = sync.changes(code)
    assert changes.describe() == ("3 Dateien geändert: README.md, main.py und suche.py. "
                                  "1 neue Datei: export.py. 1 Datei gelöscht: alt.py.")
    assert changes.summary() == "3 Dateien geändert, 1 neue Datei, 1 Datei gelöscht"
    assert changes.lines()[0] == "README.md, geändert"
    assert sorted(changes.existing) == ["README.md", "export.py", "main.py", "suche.py"]


def test_many_files_are_shortened(tmp_path, projects_root):
    _, code, _ = setup_repo(tmp_path, projects_root)
    for number in range(8):
        write(code, f"neu{number}.py", "x\n")
    assert sync.changes(code).describe() == (
        "8 neue Dateien: neu0.py, neu1.py, neu2.py, neu3.py und neu4.py und 3 weitere.")


def test_no_changes(tmp_path, projects_root):
    _, code, _ = setup_repo(tmp_path, projects_root)
    changes = sync.changes(code)
    assert not changes and changes.summary() == "keine Änderungen"


# -- Hochladen ------------------------------------------------------------------------------
def test_push_changes_commits_and_pushes(make_services, tmp_path, projects_root):
    services = make_services()
    bare, code, _ = setup_repo(tmp_path, projects_root)
    write(code, "main.py", "neu\n")
    summary, data, steps = run_push(services, code, "Suche verbessert\n\nMit mehr Treffern.")
    assert summary.completed, summary.text()
    assert steps == ["Schritt 1 von 3: Sicherheitsprüfung", "Schritt 2 von 3: Commit wird erstellt",
                     "Schritt 3 von 3: Wird hochgeladen"]
    assert summary.text() == "Fertig. Commit „Suche verbessert“. Branch main ist hochgeladen."
    assert sh(bare, "log", "-1", "--format=%B", "main").strip() == (
        "Suche verbessert\n\nMit mehr Treffern.")
    assert sh(bare, "log", "-1", "--format=%an <%ae>", "main").strip() == f"{NAME} <{EMAIL}>"
    assert git.status(code).ahead == 0 and not sync.changes(code)


def test_push_only_existing_commits(make_services, tmp_path, projects_root):
    services = make_services()
    bare, code, _ = setup_repo(tmp_path, projects_root)
    write(code, "neu.py", "x\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Lokal")
    summary, _, _ = run_push(services, code, "")
    assert summary.completed
    assert head(bare, "main") == head(code)


def test_push_refuses_when_platform_has_new_commits(make_services, tmp_path, projects_root):
    """Nie ein force push: Das Cockpit lädt nicht hoch und merkt sich, wie viel fehlt."""
    services = make_services()
    bare, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "anderes.py", "x\n")
    remote_head = head(bare, "main")
    write(code, "main.py", "neu\n")
    summary, data, _ = run_push(services, code, "Lokal geaendert")
    assert not summary.completed
    assert data["behind"] == 1
    assert "1 neuen Commit, die hier noch fehlen" in summary.text()
    assert head(bare, "main") == remote_head                     # nichts überschrieben
    assert sh(code, "log", "-1", "--format=%s").strip() == "Lokal geaendert"   # Commit bleibt


def test_push_is_stopped_by_a_secret_in_a_changed_file(make_services, tmp_path, projects_root):
    services = make_services()
    bare, code, _ = setup_repo(tmp_path, projects_root)
    before = head(bare, "main")
    write(code, "config.py", f'TOKEN = "{GITHUB_TOKEN}"\n')
    summary, _, _ = run_push(services, code, "Mit Token")
    assert not summary.completed
    assert "Sicherheitsprüfung hat das Hochladen gestoppt" in summary.text()
    assert head(bare, "main") == before
    assert GITHUB_TOKEN not in summary.text()


def test_scan_checks_only_changes(tmp_path, projects_root):
    """Was schon auf der Plattform liegt, prüft das Hochladen der Änderungen nicht noch einmal."""
    _, code, _ = setup_repo(tmp_path, projects_root, {"alt.py": "pass" + 'word = "Sommer2026!"\n'})
    assert sync.scan(code, False, EMAIL).ok
    write(code, "neu.py", "pass" + 'word = "Winter2026!"\n')
    assert [f.path for f in sync.scan(code, False, EMAIL).blocking] == ["neu.py"]


def test_scan_checks_unpushed_commits(tmp_path, projects_root):
    _, code, _ = setup_repo(tmp_path, projects_root)
    write(code, "config.py", f'TOKEN = "{GITHUB_TOKEN}"\n')
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Token")
    write(code, "config.py", "TOKEN = ''\n")
    report = sync.scan(code, False, EMAIL)
    assert [f.kind.value for f in report.blocking] == ["secret_history"]


def test_private_email_counts_only_for_public_repos(tmp_path, projects_root):
    _, code, _ = setup_repo(tmp_path, projects_root)
    git.set_identity(code, NAME, "privat@example.org")
    write(code, "neu.py", "x\n")
    assert sync.scan(code, False, EMAIL).ok
    assert [f.rule for f in sync.scan(code, True, EMAIL).findings] == ["privat@example.org"]


def test_visibility_comes_from_the_list_of_repositories(account, tmp_path):
    from cockpit.platforms.base import RemoteRepo, RepoRef
    services, acc, _ = account
    services.remote_repos.replace(acc.id, [
        RemoteRepo(RepoRef("tester", "Offen"), False, "https://github.com/tester/Offen.git",
                   "https://github.com/tester/Offen", ""),
        RemoteRepo(RepoRef("tester", "Geheim"), True, "https://github.com/tester/Geheim.git",
                   "https://github.com/tester/Geheim", "")])

    class P:
        def __init__(self, name):
            self.remote = git.parse_remote(f"https://github.com/Tester/{name}")
    assert sync.is_public(services, P("offen"))
    assert not sync.is_public(services, P("Geheim"))
    assert not sync.is_public(services, P("Unbekannt"))            # unbekannt gilt als privat


def test_prepare_commit_fills_missing_identity_only(tmp_path):
    code = tmp_path / "Code"
    code.mkdir()
    git.init(code)
    sync.prepare_commit(code, "X", NAME, EMAIL)
    assert git.identity(code) == (NAME, EMAIL)
    git.set_identity(code, "Alt", "alt@example.org")
    sync.prepare_commit(code, "X", NAME, EMAIL)                    # keine Rückfrage vor Commits
    assert git.identity(code) == ("Alt", "alt@example.org")


# -- Holen ----------------------------------------------------------------------------------
def test_fetch_reports_what_would_change(tmp_path, projects_root):
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "a\nB\nc\n")
    push_from_other(other, "neu.py", "x\n", "Zweiter")
    write(code, "main.py", "a\nb\nC\n")
    write(code, "eigene.py", "x\n")
    incoming = sync.fetch(code)
    assert (incoming.behind, incoming.ahead) == (2, 0)
    assert incoming.files == ["main.py", "neu.py"]
    assert incoming.local == ["eigene.py", "main.py"]
    assert incoming.overlap == ["main.py"]


def test_fetch_without_new_commits(tmp_path, projects_root):
    _, code, _ = setup_repo(tmp_path, projects_root)
    incoming = sync.fetch(code)
    assert incoming.behind == 0 and incoming.files == []


def test_fetch_needs_an_upstream(tmp_path):
    code = tmp_path / "Code"
    code.mkdir()
    git.init(code)
    write(code, "a.py", "1\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "x")
    with pytest.raises(Exception, match="noch nicht auf der Plattform"):
        sync.fetch(code)


def test_pull_fast_forward_keeps_other_changes_and_makes_a_backup(tmp_path, projects_root):
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "a\nB\nc\n")
    write(code, "README.md", "# eigene Änderung\n")
    incoming = sync.fetch(code)
    before = head(code)
    target = sync.backup(code, "Tagebuch", incoming)
    assert target.parent == backups.backups_dir()
    assert (target / "main.py").read_text(encoding="utf-8") == "a\nb\nc\n"          # Stand vor dem Holen
    assert (target / "README.md").read_text(encoding="utf-8") == "# eigene Änderung\n"
    assert before in (target / "Sicherheitskopie.txt").read_text(encoding="utf-8")
    outcome = sync.merge(code, stash=False)
    assert outcome.kind is ConflictKind.NONE
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nB\nc\n"
    assert (code / "README.md").read_text(encoding="utf-8") == "# eigene Änderung\n"
    assert git.status(code).behind == 0
    assert not sh(code, "for-each-ref", sync.BEFORE_PULL_REF).strip()


def test_pull_with_stash_puts_changes_back(tmp_path, projects_root):
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "A\nb\nc\n")
    write(code, "main.py", "a\nb\nC\n")                             # andere Stelle
    write(code, "eigene.py", "x\n")
    sync.fetch(code)
    outcome = sync.merge(code, stash=True)
    assert outcome.kind is ConflictKind.NONE
    assert (code / "main.py").read_text(encoding="utf-8") == "A\nb\nC\n"
    assert (code / "eigene.py").exists()
    assert stash_list(code) == ""


def stash_conflict(tmp_path, projects_root):
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "a\nVON GITHUB\nc\n")
    write(code, "main.py", "a\nMEINE\nc\n")
    write(code, "eigene.py", "x\n")
    before = head(code)
    sync.fetch(code)
    outcome = sync.merge(code, stash=True)
    return code, before, outcome


def test_stash_conflict_keep_mine(tmp_path, projects_root):
    code, before, outcome = stash_conflict(tmp_path, projects_root)
    assert outcome.kind is ConflictKind.STASH and outcome.conflicts == ["main.py"]
    assert sync.conflict_kind(code) is ConflictKind.STASH
    state = git.status(code)
    assert state.conflicts == ["main.py"]
    sync.resolve(code, "main.py", ConflictKind.STASH, keep_mine=True)
    assert sync.finish(code, ConflictKind.STASH).kind is ConflictKind.NONE
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nMEINE\nc\n"
    assert head(code) != before and git.status(code).behind == 0   # neue Commits sind da
    assert sorted(sync.changes(code).files) == ["eigene.py", "main.py"]
    assert stash_list(code) == ""
    assert sync.conflict_kind(code) is ConflictKind.NONE


def test_stash_conflict_take_theirs(tmp_path, projects_root):
    code, _, _ = stash_conflict(tmp_path, projects_root)
    sync.resolve(code, "main.py", ConflictKind.STASH, keep_mine=False)
    sync.finish(code, ConflictKind.STASH)
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nVON GITHUB\nc\n"
    assert sync.changes(code).files == ["eigene.py"]


def test_stash_conflict_abort_restores_everything(tmp_path, projects_root):
    code, before, _ = stash_conflict(tmp_path, projects_root)
    assert sync.abort(code, ConflictKind.STASH) is False
    assert head(code) == before
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nMEINE\nc\n"
    assert (code / "eigene.py").read_text(encoding="utf-8") == "x\n"
    assert stash_list(code) == ""
    assert sync.conflict_kind(code) is ConflictKind.NONE


def merge_conflict(tmp_path, projects_root):
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "a\nVON GITHUB\nc\n")
    write(code, "main.py", "a\nMEINE\nc\n")
    sh(code, "commit", "-q", "-am", "Meine")
    before = head(code)
    sync.fetch(code)
    return code, before, sync.merge(code, stash=False)


def test_merge_conflict_take_theirs(tmp_path, projects_root):
    code, before, outcome = merge_conflict(tmp_path, projects_root)
    assert outcome.kind is ConflictKind.MERGE and outcome.conflicts == ["main.py"]
    assert git.status(code).merging
    sync.resolve(code, "main.py", ConflictKind.MERGE, keep_mine=False)
    assert sync.finish(code, ConflictKind.MERGE).kind is ConflictKind.NONE
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nVON GITHUB\nc\n"
    parents = sh(code, "log", "-1", "--format=%P").split()
    assert len(parents) == 2 and before in parents                 # Merge-Commit wie git pull
    state = git.status(code)
    assert state.behind == 0 and state.ahead == 2 and not state.merging


def test_merge_conflict_keep_mine(tmp_path, projects_root):
    code, _, _ = merge_conflict(tmp_path, projects_root)
    sync.resolve(code, "main.py", ConflictKind.MERGE, keep_mine=True)
    sync.finish(code, ConflictKind.MERGE)
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nMEINE\nc\n"


def test_merge_conflict_abort(tmp_path, projects_root):
    code, before, _ = merge_conflict(tmp_path, projects_root)
    sync.abort(code, ConflictKind.MERGE)
    assert head(code) == before and not git.status(code).merging
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nMEINE\nc\n"


def test_merge_conflict_resolved_in_editor(tmp_path, projects_root):
    code, _, _ = merge_conflict(tmp_path, projects_root)
    assert sync.has_markers(code, "main.py")
    with pytest.raises(Exception, match="noch 1 Konflikt"):
        sync.finish(code, ConflictKind.MERGE)
    write(code, "main.py", "a\nBEIDES\nc\n")
    assert not sync.has_markers(code, "main.py")
    sync.mark_resolved(code, "main.py")
    sync.finish(code, ConflictKind.MERGE)
    assert sh(code, "show", "HEAD:main.py") == "a\nBEIDES\nc\n"


def test_merge_conflict_with_stash_gives_changes_back_on_abort(tmp_path, projects_root):
    # Eigener Commit und dazu eine Änderung ohne Commit in einer Datei, die GitHub auch ändert
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "a\nVON GITHUB\nc\n")
    push_from_other(other, "README.md", "# von GitHub\n", "Readme")
    write(code, "main.py", "a\nMEINE\nc\n")
    sh(code, "commit", "-q", "-am", "Meine")
    write(code, "README.md", "# ungespeichert\n")
    before = head(code)
    incoming = sync.fetch(code)
    assert incoming.overlap == ["README.md"]
    outcome = sync.merge(code, stash=True)
    assert outcome.kind is ConflictKind.MERGE and outcome.stash_kept
    assert sync.abort(code, ConflictKind.MERGE) is False
    assert head(code) == before
    assert (code / "README.md").read_text(encoding="utf-8") == "# ungespeichert\n"
    assert stash_list(code) == ""


def test_delete_modify_conflict(tmp_path, projects_root):
    _, code, other = setup_repo(tmp_path, projects_root)
    sh(other, "rm", "-q", "README.md")
    sh(other, "commit", "-q", "-m", "Gelöscht")
    sh(other, "push", "-q")
    write(code, "README.md", "# geändert\n")
    sh(code, "commit", "-q", "-am", "Geändert")
    sync.fetch(code)
    outcome = sync.merge(code, stash=False)
    assert outcome.conflicts == ["README.md"]
    sync.resolve(code, "README.md", ConflictKind.MERGE, keep_mine=False)   # gelöscht lassen
    sync.finish(code, ConflictKind.MERGE)
    assert not (code / "README.md").exists()


def test_status_lines_show_conflicts(tmp_path, projects_root, make_services):
    services = make_services()
    code, _, _ = merge_conflict(tmp_path, projects_root)
    project = services.projects.add(code.parent)
    status = project_status.compute(project)
    assert status.unfinished_merge == "1 Konflikt beim Zusammenführen"
    assert project_status.code_line(status).startswith("Code, 1 Konflikt beim Zusammenführen")
    sync.resolve(code, "main.py", ConflictKind.MERGE, keep_mine=True)
    status = project_status.compute(project)
    assert status.unfinished_merge == "Zusammenführen nicht abgeschlossen"
    assert "Zusammenführen nicht abgeschlossen" in project_status.project_line(project, status)


# -- Oberfläche -----------------------------------------------------------------------------
def select_code(win, services, code: Path):
    from cockpit.core.actions import Target
    project = services.projects.find_by_dir(code.parent)
    win.project_list.select(Target.CODE, project.id)
    return project


def labels(win) -> list[str]:
    return [e.label for e in win.current_entries()]


def test_code_actions_on_platform(live, qtbot, make_services, projects_root, tmp_path):
    services = make_services()
    setup_repo(tmp_path, projects_root)
    win = live(services)
    select_code(win, services, projects_root / "Tagebuch" / "Code")
    texts = labels(win)
    # Reihenfolge vom 30.09.2026
    # Seit dem 02.10.2026 mit dem Stand hinter dem Namen
    assert texts[:4] == ["Projekt neu einlesen", "Terminal …",
                         "Änderungen auf GitHub hochladen …, nichts offen",
                         "Änderungen von GitHub holen …, alles aktuell"]
    assert "Auf GitHub hochladen …" not in texts and "Konflikte lösen …" not in texts


def test_push_from_the_window(live, qtbot, make_services, projects_root, tmp_path, monkeypatch):
    services = make_services()
    services.settings.update(git_name=NAME, git_email=EMAIL)
    bare, code, _ = setup_repo(tmp_path, projects_root)
    write(code, "main.py", "neu\n")
    win = live(services)
    select_code(win, services, code)

    class FakeCommitDialog:
        def __init__(self, title, changes, parent=None, source=None):
            assert changes.summary() == "1 Datei geändert"
            self.message = "Neue Suche"

        def exec(self):
            return True

    monkeypatch.setattr(sync_dialogs, "CommitDialog", FakeCommitDialog)
    win.run_default_action()
    qtbot.waitUntil(lambda: said("Fertig. Commit „Neue Suche“. Branch main ist hochgeladen."),
                    timeout=20000)
    assert sh(bare, "log", "-1", "--format=%s", "main").strip() == "Neue Suche"
    assert said("Schritt 3 von 3: Wird hochgeladen …")
    wait_idle(qtbot, win)
    assert win.project_list.currentItem().text() == "Code, alles hochgeladen"


def test_push_without_changes(live, qtbot, make_services, projects_root, tmp_path):
    services = make_services()
    setup_repo(tmp_path, projects_root)
    win = live(services)
    select_code(win, services, projects_root / "Tagebuch" / "Code")
    win.run_default_action()
    qtbot.waitUntil(lambda: said("Es gibt nichts zum Hochladen. Alles ist hochgeladen."),
                    timeout=10000)


def test_push_behind_offers_pull_then_push(live, qtbot, make_services, projects_root, tmp_path,
                                           monkeypatch):
    services = make_services()
    services.settings.update(git_name=NAME, git_email=EMAIL)
    bare, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "anderes.py", "x\n")
    write(code, "main.py", "neu\n")
    win = live(services)
    select_code(win, services, code)

    class FakeCommitDialog:
        def __init__(self, title, changes, parent=None, source=None):
            self.message = "Lokal"

        def exec(self):
            return True

    questions = []
    monkeypatch.setattr(sync_dialogs, "CommitDialog", FakeCommitDialog)
    monkeypatch.setattr(sync_flow, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or True)
    win.run_default_action()
    qtbot.waitUntil(lambda: said("Fertig. Branch main ist hochgeladen."), timeout=30000)
    text, buttons = questions[0]
    assert text.startswith("Ihr Commit ist gespeichert, aber noch nicht hochgeladen. Auf GitHub "
                           "gibt es 1 neuen Commit, die hier noch fehlen.")
    assert buttons == {"yes": "Holen und hochladen …", "no": "Später"}
    assert questions[1][0].startswith("Auf GitHub gibt es 1 neuen Commit, sie ändern 1 Datei.")
    assert said("Geholt: 1 neuer Commit von GitHub.")
    assert len(questions) == 2                                       # kein drittes Nachfragen
    log = sh(bare, "log", "--format=%s", "main").split("\n")
    assert "Lokal" in log and "Vom anderen Rechner" in log


def test_pull_later_is_default(live, qtbot, make_services, projects_root, tmp_path, monkeypatch):
    services = make_services()
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "anderes.py", "x\n")
    before = head(code)
    win = live(services)
    select_code(win, services, code)
    monkeypatch.setattr(sync_flow, "confirm", lambda *a, **k: False)     # Escape
    win.run_entry(next(e for e in win.current_entries() if "holen" in e.label))
    wait_idle(qtbot, win)
    qtbot.wait(50)
    assert head(code) == before and not (code / "anderes.py").exists()


def test_pull_asks_for_stash_with_cancel_as_default(live, qtbot, make_services, projects_root,
                                                     tmp_path, monkeypatch):
    services = make_services()
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "A\nb\nc\n")
    write(code, "main.py", "a\nb\nC\n")
    win = live(services)
    select_code(win, services, code)
    asked = []

    def ask_buttons(parent, title, text, buttons, default, escape):
        asked.append((text, buttons, default, escape))
        return escape

    monkeypatch.setattr(sync_flow, "ask_buttons", ask_buttons)
    win.run_entry(next(e for e in win.current_entries() if "holen" in e.label))
    qtbot.waitUntil(lambda: bool(asked), timeout=10000)
    text, buttons, default, escape = asked[0]
    assert "In main.py haben Sie auch Änderungen, die noch nicht hochgeladen sind." in text
    assert buttons == ["Beiseitelegen und holen", "Abbrechen"] and default == escape == 1
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nb\nC\n"
    assert stash_list(code) == ""


def test_pull_with_conflict_opens_dialog_and_resolves(live, qtbot, make_services, projects_root,
                                                      tmp_path, monkeypatch):
    services = make_services()
    services.settings.update(git_name=NAME, git_email=EMAIL)
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "a\nVON GITHUB\nc\n")
    write(code, "main.py", "a\nMEINE\nc\n")
    win = live(services)
    select_code(win, services, code)
    seen = []

    class FakeConflictDialog:
        def __init__(self, code_dir, kind, platform_name, parent=None):
            seen.append((kind, sync.conflicted(code_dir), platform_name))
            sync.resolve(code_dir, "main.py", kind, keep_mine=True)

        def exec(self):
            return True

    monkeypatch.setattr(sync_flow, "ask_buttons", lambda *a, **k: 0)   # beiseitelegen
    monkeypatch.setattr(sync_dialogs, "ConflictDialog", FakeConflictDialog)
    win.run_entry(next(e for e in win.current_entries() if "holen" in e.label))
    qtbot.waitUntil(lambda: said("Zusammenführen abgeschlossen."), timeout=15000)
    assert seen == [(ConflictKind.STASH, ["main.py"], "GitHub")]
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nMEINE\nc\n"
    assert git.status(code).behind == 0 and stash_list(code) == ""


def test_conflict_abort_from_window(live, qtbot, make_services, projects_root, tmp_path,
                                    monkeypatch):
    services = make_services()
    code, before, _ = merge_conflict(tmp_path, projects_root)
    win = live(services)
    select_code(win, services, code)
    assert labels(win)[1] == "Konflikte lösen …"                  # Vorgabe für Enter

    class Cancel:
        def __init__(self, *a, **k):
            pass

        def exec(self):
            return False

    monkeypatch.setattr(sync_dialogs, "ConflictDialog", Cancel)
    win.run_default_action()
    assert said("Zusammenführen abgebrochen. Alles ist wie vor dem Holen.")
    assert head(code) == before


# -- Fenster --------------------------------------------------------------------------------
def test_commit_dialog(qtbot, tmp_path, projects_root, monkeypatch):
    from cockpit.ui import sync_dialogs as dialogs
    _, code, _ = setup_repo(tmp_path, projects_root)
    write(code, "main.py", "x\n")
    write(code, "neu.py", "x\n")
    errors = []
    monkeypatch.setattr(dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog = dialogs.CommitDialog("Änderungen hochladen", sync.changes(code))
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Änderungen hochladen: 1 Datei geändert, 1 neue Datei"
    assert dialog.initial_focus_widget is dialog.summary
    assert dialog.summary.accessibleName() == "Was haben Sie geändert?"
    assert dialog.files.accessibleName() == "Änderungen"
    assert [dialog.files.item(i).text() for i in range(dialog.files.count())] == [
        "main.py, geändert", "neu.py, neu"]
    assert dialog.ok_button.isDefault()
    dialog.check()
    assert errors == [dialogs.NO_MESSAGE] and dialog.result() == 0
    dialog.summary.setText("  Suche   verbessert ")
    dialog.details.setPlainText("Zeile eins\nZeile zwei")
    dialog.check()
    assert dialog.message == "Suche verbessert\n\nZeile eins\nZeile zwei"


def test_conflict_dialog(qtbot, tmp_path, projects_root, monkeypatch):
    from cockpit.ui import sync_dialogs as dialogs
    _, code, other = setup_repo(tmp_path, projects_root, {"a.py": "1\n", "b.py": "1\n",
                                                         "c.py": "1\n"})
    for name in ("a.py", "b.py", "c.py"):
        write(other, name, "github\n")
        write(code, name, "meine\n")
    sh(other, "commit", "-q", "-am", "x")
    sh(other, "push", "-q")
    sh(code, "commit", "-q", "-am", "y")
    sync.fetch(code)
    sync.merge(code, stash=False)
    opened = []
    monkeypatch.setattr(dialogs.core_actions, "open_path", lambda p: opened.append(p))
    dialog = dialogs.ConflictDialog(code, ConflictKind.MERGE, "GitHub")
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.activateWindow()
    qtbot.waitUntil(dialog.isActiveWindow, timeout=3000)
    rows = lambda: [dialog.list.item(i).text() for i in range(dialog.list.count())]  # noqa: E731
    assert dialog.windowTitle() == "Konflikte beim Zusammenführen: 3 Konflikte offen"
    assert rows() == ["a.py, Konflikt", "b.py, Konflikt", "c.py, Konflikt"]
    assert dialog.theirs_button.text() == "Fassung von &GitHub übernehmen"
    assert dialog.editor_button.text() == "Konflikt im &Editor anzeigen"
    # Abschließen ist immer erreichbar und sagt, was noch fehlt (Rückmeldung aus dem Test von 5c)
    assert dialog.finish_button.isEnabled()
    dialog.list.setCurrentRow(2)
    dialog.finish()
    assert said("Noch nicht fertig. Noch 3 Konflikte.")
    assert dialog.list.currentRow() == 0 and dialog.result() == 0
    dialog.choose(True)
    assert said("a.py: Ihre Fassung. Noch 2 Konflikte.")
    assert dialog.list.currentRow() == 1                           # weiter zur nächsten Datei
    assert not dialog.mine_button.isEnabled() or dialog.current() == "b.py"
    dialog.choose(False)
    assert said("b.py: Fassung von GitHub. Noch 1 Konflikt.")
    dialog.open_current()
    assert opened == [code / "c.py"]
    assert rows()[2] == "c.py, im Editor angezeigt, noch Konfliktmarken"
    assert (code / "c.py").read_text(encoding="utf-8").splitlines() == [
        "<<<<<<< Meine Fassung, c.py Zeile 1", "meine",
        "======= Fassung von GitHub, c.py Zeile 1", "github", ">>>>>>> Ende des Konflikts"]
    dialog.recheck()
    assert said("Keine Änderung. Noch 1 Konflikt.")
    write(code, "c.py", "beides\n")
    dialog.recheck()
    assert said("Gelöst: c.py. Alle Konflikte gelöst.")
    assert dialog.windowTitle() == "Konflikte beim Zusammenführen: alle Konflikte gelöst"
    assert rows() == ["a.py, gelöst: Ihre Fassung", "b.py, gelöst: Fassung von GitHub",
                      "c.py, gelöst: im Editor bearbeitet"]
    assert dialog.finish_button.hasFocus()                        # alles gelöst: zum Abschließen
    dialog.list.setCurrentRow(0)
    assert not dialog.mine_button.isEnabled()                       # schon gelöst
    dialog.finish()
    assert dialog.result() == 1
    sync.finish(code, ConflictKind.MERGE)
    assert [sh(code, "show", f"HEAD:{n}") for n in ("a.py", "b.py", "c.py")] == [
        "meine\n", "github\n", "beides\n"]


def test_conflict_dialog_escape_is_abort(qtbot, tmp_path, projects_root):
    from PySide6.QtCore import Qt
    from cockpit.ui import sync_dialogs as dialogs
    code, _, _ = merge_conflict(tmp_path, projects_root)
    dialog = dialogs.ConflictDialog(code, ConflictKind.MERGE, "GitHub")
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.keyClick(dialog.list, Qt.Key.Key_Return)                   # Enter in der Liste: nichts
    assert dialog.isVisible() and sync.conflicted(code) == ["main.py"]
    qtbot.keyClick(dialog, Qt.Key.Key_Escape)
    assert dialog.result() == 0


# -- Beschriftete Konfliktmarken ------------------------------------------------------------
def test_labels_name_version_file_and_line(tmp_path):
    text = ("eins\nzwei\n<<<<<<< HEAD\nmeine a\nmeine b\n=======\ngithub\n>>>>>>> origin/main\n"
            "mitte\n<<<<<<< HEAD\nm\n||||||| basis\nb\n=======\ng1\ng2\n>>>>>>> origin/main\n")
    write(tmp_path, "sub/main.py", text)
    assert sync.label_conflicts(tmp_path, "sub/main.py", ConflictKind.MERGE) == 2
    assert (tmp_path / "sub/main.py").read_text(encoding="utf-8").splitlines() == [
        "eins", "zwei",
        "<<<<<<< Meine Fassung, main.py Zeile 3", "meine a", "meine b",
        "======= Fassung von GitHub, main.py Zeile 3", "github",
        ">>>>>>> Ende des Konflikts",
        "mitte",
        "<<<<<<< Meine Fassung, main.py Zeile 6", "m",
        "||||||| Gemeinsamer Ausgangsstand", "b",
        "======= Fassung von GitHub, main.py Zeile 5", "g1", "g2",
        ">>>>>>> Ende des Konflikts"]
    assert sync.has_markers(tmp_path, "sub/main.py")
    # Noch einmal beschriften ändert nichts
    before = (tmp_path / "sub/main.py").read_bytes()
    sync.label_conflicts(tmp_path, "sub/main.py", ConflictKind.MERGE)
    assert (tmp_path / "sub/main.py").read_bytes() == before


def test_labels_for_stash_conflicts_start_with_github(tmp_path):
    (tmp_path / "a.py").write_bytes(b"<<<<<<< Updated upstream\r\ng\r\n=======\r\nm\r\n"
                                    b">>>>>>> Stashed changes\r\n")
    sync.label_conflicts(tmp_path, "a.py", ConflictKind.STASH, "GitHub")
    assert (tmp_path / "a.py").read_bytes() == (
        b"<<<<<<< Fassung von GitHub, a.py Zeile 1\r\ng\r\n"
        b"======= Meine Fassung, a.py Zeile 1\r\nm\r\n>>>>>>> Ende des Konflikts\r\n")


def test_labels_in_a_real_stash_conflict(tmp_path, projects_root):
    code, _, _ = stash_conflict(tmp_path, projects_root)
    sync.label_conflicts(code, "main.py", ConflictKind.STASH)
    lines = (code / "main.py").read_text(encoding="utf-8").splitlines()
    assert lines[1] == "<<<<<<< Fassung von GitHub, main.py Zeile 2"
    assert lines[2] == "VON GITHUB" and lines[4] == "MEINE"
    assert lines[3] == "======= Meine Fassung, main.py Zeile 2"


# -- Stand bei Code und Projekt neu einlesen --------------------------------------------------
def test_code_line_says_what_is_not_fetched(tmp_path, projects_root, make_services):
    services = make_services()
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "neu.py", "x\n")
    sync.fetch(code)
    project = services.projects.add(code.parent)
    status = project_status.compute(project)
    assert project_status.code_line(status) == (
        "Code, alles hochgeladen, 1 Änderung auf GitHub noch nicht geholt")


def test_reread_project_is_on_top_of_every_level(live, qtbot, make_services, projects_root,
                                                 tmp_path):
    from cockpit.core.actions import Target
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    (code.parent / "Exe").mkdir()
    win = live(services)
    project = select_code(win, services, code)
    for target in (Target.PROJECT, Target.CODE, Target.EXE):
        win.project_list.select(target, project.id)
        assert labels(win)[0] == "Projekt neu einlesen"
        assert not win.current_entries()[0].action.is_default     # Enter bleibt wie bisher
    write(code, "neu.py", "x\n")
    win.project_list.select(Target.CODE, project.id)
    win.run_entry(win.current_entries()[0])
    qtbot.waitUntil(lambda: said("Tagebuch neu eingelesen."), timeout=10000)
    assert win.project_list.currentItem().text() == "Code, 1 Datei noch nicht hochgeladen"
    file_menu = win.menuBar().actions()[0].menu()
    texts = [a.text() for a in file_menu.actions()]
    assert "Projekte &neu einlesen" in texts and "&Sicherheitskopien …" in texts


# -- Sicherheitskopien ------------------------------------------------------------------------
def test_backup_info_and_restore(tmp_path, projects_root):
    from cockpit.core import backups
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "a\nB\nc\n")
    write(code, "main.py", "a\nb\nMEINE\n")
    incoming = sync.fetch(code)
    folder = sync.backup(code, "Tagebuch", incoming)
    info = next(i for i in backups.all_backups() if i.path == folder)
    assert (info.project, info.reason, info.source_dir) == ("Tagebuch", "vor dem Holen", code)
    assert info.files() == ["main.py"]
    assert info.line().endswith(", Tagebuch, vor dem Holen, 1 Datei")
    assert info.notes[0].startswith("Commit vor dem Holen: ")
    write(code, "main.py", "kaputt\n")
    before = backups.restore(info, "main.py")
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nb\nMEINE\n"
    assert (before / "main.py").read_text(encoding="utf-8") == "kaputt\n"   # vorher gesichert
    assert backups.read_info(before).reason == "vor dem Wiederherstellen"
    (code / "main.py").unlink()
    assert backups.restore(info, "main.py") is None                 # nichts zu sichern
    assert (code / "main.py").exists()
    backups.delete(info)
    assert not folder.exists()


def test_old_backup_without_info_cannot_be_restored(tmp_path):
    from cockpit.core import backups
    from cockpit.core.errors import CockpitError
    folder = backups.backups_dir() / "2026-09-01_10-00-00 Alt venv"
    write(folder, "a.txt", "x")
    info = backups.read_info(folder)
    assert info.project == "Alt venv" and info.source_dir is None
    with pytest.raises(CockpitError, match="nicht bekannt, woher"):
        backups.restore(info, "a.txt")


def test_backups_dialog(qtbot, tmp_path, projects_root, monkeypatch):
    from cockpit.core import backups
    from cockpit.ui import backups_dialog
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "a\nB\nc\n")
    write(code, "main.py", "MEINE\n")
    folder = sync.backup(code, "Tagebuch", sync.fetch(code))
    write(code, "main.py", "anders\n")
    questions, opened = [], []
    monkeypatch.setattr(backups_dialog, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or True)
    monkeypatch.setattr(backups_dialog.core_actions, "open_path", opened.append)
    dialog = backups_dialog.BackupsDialog()
    qtbot.addWidget(dialog)
    assert dialog.windowTitle().startswith("Sicherheitskopien: ")
    assert dialog.list.item(0).text().endswith(", Tagebuch, vor dem Holen, 1 Datei")
    files = backups_dialog.BackupFilesDialog(dialog.items[0], dialog)
    qtbot.addWidget(files)
    assert files.list.accessibleName() == "Dateien"
    assert files.list.item(0).text() == "main.py"
    assert files.windowTitle().endswith(f", aus {code}")
    files.open_current()
    assert opened == [folder / "main.py"]
    files.restore_current()
    text, buttons = questions[-1]
    assert text.startswith("main.py aus der Sicherheitskopie vom ")
    assert "Die jetzige Datei kommt vorher selbst als Sicherheitskopie" in text
    assert buttons == {"yes": "Wiederherstellen", "no": "Abbrechen"}
    assert (code / "main.py").read_text(encoding="utf-8") == "MEINE\n"
    assert said("main.py wiederhergestellt.")
    dialog.fill()
    assert dialog.list.item(0).text().endswith("Tagebuch, vor dem Wiederherstellen, 1 Datei")
    dialog.list.setCurrentRow(0)
    count_before = len(backups.all_backups())
    dialog.delete_current()
    assert "wird endgültig gelöscht" in questions[-1][0]
    assert questions[-1][1] == {"yes": "Löschen", "no": "Abbrechen"}
    assert len(backups.all_backups()) == count_before - 1
    assert said("Sicherheitskopie gelöscht.")


def test_backups_dialog_cancel_changes_nothing(qtbot, tmp_path, projects_root, monkeypatch):
    from cockpit.ui import backups_dialog
    _, code, other = setup_repo(tmp_path, projects_root)
    push_from_other(other, "main.py", "a\nB\nc\n")
    write(code, "main.py", "MEINE\n")
    sync.backup(code, "Tagebuch", sync.fetch(code))
    write(code, "main.py", "anders\n")
    monkeypatch.setattr(backups_dialog, "confirm", lambda *a, **k: False)     # Escape
    dialog = backups_dialog.BackupsDialog()
    qtbot.addWidget(dialog)
    files = backups_dialog.BackupFilesDialog(dialog.items[0], dialog)
    qtbot.addWidget(files)
    files.restore_current()
    dialog.delete_current()
    assert (code / "main.py").read_text(encoding="utf-8") == "anders\n"
    assert len(dialog.items) == 1 and dialog.items[0].path.exists()

