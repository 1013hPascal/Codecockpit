"""Commits nachbessern, übernehmen, umsortieren, zusammenfassen, Branch ab hier, Co-Autoren
(Wunsch des Nutzers vom 21.10.2026, nach dem Vergleich mit GitHub Desktop).

Hochgeladene Commits bleiben immer, wie sie sind: kein force push.
"""
from __future__ import annotations

import pytest

from cockpit.core import git, history, rewrite, sync
from cockpit.core.errors import CockpitError
from tests.conftest import patch_split

needs_git = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


def run(code, *args):
    return git.run(list(args), code).stdout.strip()


def commit(code, name, text, message):
    (code / name).write_bytes(text.encode())
    run(code, "add", "-A")
    run(code, "commit", "-q", "-m", message)


def repo(tmp_path):
    """Ein Commit hochgeladen, drei noch nicht."""
    bare = tmp_path / "remote.git"
    git.run(["init", "-q", "--bare", "-b", "main", str(bare)], tmp_path)
    code = tmp_path / "code"
    code.mkdir()
    run(code, "init", "-q", "-b", "main")
    run(code, "config", "user.name", "Ich")
    run(code, "config", "user.email", "ich@example.com")
    run(code, "remote", "add", "origin", str(bare))
    commit(code, "a.txt", "a\n", "Start")
    run(code, "push", "-q", "-u", "origin", "main")
    commit(code, "b.txt", "b\n", "B dazu")
    commit(code, "c.txt", "c\n", "C dazu")
    commit(code, "d.txt", "d\n", "D dazu")
    return code


def subjects(code):
    return run(code, "log", "--format=%s").splitlines()


@needs_git
def test_amend_changes_message_and_takes_changes(tmp_path):
    code = repo(tmp_path)
    newest = history.log_commits(code)[0]
    assert rewrite.can_amend(newest)
    (code / "d.txt").write_bytes(b"d neu\n")
    rewrite.amend(code, newest, "D dazu, besser\n\nMit Text", with_changes=True)
    assert subjects(code)[0] == "D dazu, besser"
    assert run(code, "show", "HEAD:d.txt") == "d neu" and not sync.changes(code)
    assert run(code, "for-each-ref", "--format=%(refname)", "refs/codecockpit/vorher/")


@needs_git
def test_amend_only_message_leaves_changes(tmp_path):
    code = repo(tmp_path)
    (code / "d.txt").write_bytes(b"d neu\n")
    rewrite.amend(code, history.log_commits(code)[0], "Nur Nachricht", with_changes=False)
    assert subjects(code)[0] == "Nur Nachricht" and sync.changes(code).modified == ["d.txt"]


@needs_git
def test_uploaded_commits_stay(tmp_path):
    code = repo(tmp_path)
    uploaded = next(c for c in history.log_commits(code) if c.uploaded)
    assert not rewrite.can_amend(uploaded)
    with pytest.raises(CockpitError):
        rewrite.amend(code, uploaded, "x", False)
    with pytest.raises(CockpitError) as error:
        rewrite.reorder(code, rewrite.Plan([rewrite.Step(uploaded)]))
    assert error.value.message == rewrite.UPLOADED


@needs_git
def test_reorder_and_squash(tmp_path):
    code = repo(tmp_path)
    local = rewrite.local_commits(code, history.log_commits(code))
    assert [c.subject for c in local] == ["B dazu", "C dazu", "D dazu"]
    b, c, d = (rewrite.Step(x) for x in local)
    d.squash = True                                   # D mit C zusammen
    rewrite.reorder(code, rewrite.Plan([c, d, b]))     # C+D zuerst, dann B
    assert subjects(code) == ["B dazu", "C dazu", "Start"]
    body = run(code, "log", "-1", "--skip=1", "--format=%b")
    assert "Zusammengefasst aus:" in body and "- D dazu" in body
    assert sorted(p.name for p in code.iterdir() if p.suffix == ".txt") == [
        "a.txt", "b.txt", "c.txt", "d.txt"]


@needs_git
def test_reorder_needs_a_clean_folder(tmp_path):
    code = repo(tmp_path)
    (code / "a.txt").write_bytes(b"geaendert\n")
    local = rewrite.local_commits(code, history.log_commits(code))
    with pytest.raises(CockpitError) as error:
        rewrite.reorder(code, rewrite.Plan([rewrite.Step(c) for c in reversed(local)]))
    assert error.value.message == rewrite.NOT_CLEAN
    assert subjects(code)[0] == "D dazu"


@needs_git
def test_reorder_conflict_keeps_everything(tmp_path):
    code = repo(tmp_path)
    commit(code, "b.txt", "b zwei\n", "B ändern")       # hängt von "B dazu" ab
    local = rewrite.local_commits(code, history.log_commits(code))
    steps = [rewrite.Step(c) for c in local]
    steps[0], steps[-1] = steps[-1], steps[0]           # "B ändern" vor "B dazu"
    before = run(code, "rev-parse", "HEAD")
    with pytest.raises(CockpitError):
        rewrite.reorder(code, rewrite.Plan(steps))
    assert run(code, "rev-parse", "HEAD") == before and not sync.changes(code)


@needs_git
def test_cherry_pick_into_another_folder(tmp_path):
    code = repo(tmp_path)
    other = tmp_path / "andere"
    run(code, "worktree", "add", "-q", "-b", "andere", str(other), "origin/main")
    picked = history.log_commits(code)[1]                     # "C dazu"
    rewrite.cherry_pick(other, picked)
    assert subjects(other)[0] == "C dazu" and (other / "c.txt").is_file()
    with pytest.raises(CockpitError) as error:
        rewrite.cherry_pick(other, picked)                    # schon da
    assert "schon" in error.value.message


@needs_git
def test_branch_at_an_earlier_commit(tmp_path):
    code = repo(tmp_path)
    start = history.log_commits(code)[-1]
    rewrite.branch_at(code, "von-start", start)
    assert run(code, "rev-parse", "von-start") == start.sha
    assert git.status(code).branch == "main"                 # nicht gewechselt


@needs_git
def test_coauthors(tmp_path):
    code = repo(tmp_path)
    run(code, "commit", "-q", "--allow-empty", "-m", "Von Kim", "--author",
        "Kim <kim@example.com>")
    assert sync.known_people(code) == ["Kim <kim@example.com>"]
    message = sync.with_coauthors("Suche\n\nText", ["Kim <kim@example.com>"])
    assert message == "Suche\n\nText\n\nCo-authored-by: Kim <kim@example.com>"
    assert sync.with_coauthors("Suche", []) == "Suche"


@needs_git
def test_reorder_dialog_moves_and_squashes(qtbot, tmp_path, monkeypatch):
    from cockpit.ui import history_dialogs
    code = repo(tmp_path)
    local = rewrite.local_commits(code, history.log_commits(code))
    dialog = history_dialogs.ReorderDialog(local)
    qtbot.addWidget(dialog)
    assert [dialog.list.item(r).text() for r in range(3)] == ["D dazu", "C dazu", "B dazu"]
    dialog.list.setCurrentRow(2)                      # B dazu
    dialog.move(1)                                    # nach oben
    assert [dialog.list.item(r).text() for r in range(3)] == ["D dazu", "B dazu", "C dazu"]
    dialog.list.setCurrentRow(0)
    dialog.toggle_squash()
    assert dialog.list.item(0).text() == "D dazu, wird mit dem Commit darunter zusammengefasst"
    dialog.list.setCurrentRow(2)
    dialog.toggle_squash()                            # der älteste: geht nicht
    assert not dialog.plan.steps[0].squash
    patch_split(monkeypatch, history_dialogs, "confirm", lambda *a, **k: True)
    dialog.take()
    assert [s.commit.subject for s in dialog.plan.steps] == ["C dazu", "B dazu", "D dazu"]
