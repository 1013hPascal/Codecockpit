"""Auswählen, was in den Commit kommt (Wunsch des Nutzers vom 21.10.2026).

Dateien abhaken, bei geänderten Dateien einzelne Abschnitte wählen. Was nicht gewählt ist, bleibt
in den Dateien für einen späteren Commit.
"""
from __future__ import annotations

import threading

import pytest
from PySide6.QtCore import Qt

from cockpit.core import git, staging, sync
from cockpit.core.flows.engine import FlowContext

needs_git = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

BEFORE = "".join(f"zeile {n}\n" for n in range(1, 41))


def repo(tmp_path, newline="\n"):
    code = tmp_path / "code"
    code.mkdir()
    git.run(["init", "-q", "-b", "main"], code)
    git.run(["config", "user.name", "Test"], code)
    git.run(["config", "user.email", "test@example.com"], code)
    git.run(["config", "core.autocrlf", "false"], code)
    (code / "a.py").write_bytes(BEFORE.replace("\n", newline).encode())
    (code / "b.py").write_bytes(b"eins\n")
    git.run(["add", "-A"], code)
    git.run(["commit", "-q", "-m", "Start"], code)
    # Zwei Änderungen weit auseinander: zwei Abschnitte
    text = BEFORE.replace("zeile 3\n", "zeile 3 neu\n").replace("zeile 35\n", "zeile 35 neu\n")
    (code / "a.py").write_bytes(text.replace("\n", newline).encode())
    (code / "b.py").write_bytes(b"zwei\n")
    (code / "c.py").write_bytes(b"print('neu')\n")
    return code


def committed(code, path):
    return git.run(["show", f"HEAD:{path}"], code, check=False).stdout


@needs_git
def test_hunks_of_a_changed_file(tmp_path):
    code = repo(tmp_path)
    diff = staging.file_diff(code, "a.py", "geändert")
    assert len(diff.hunks) == 2 and diff.partial_possible
    assert diff.hunks[0].label == "Zeile 1 bis 6, 1 neu, 1 entfernt"
    assert "Neu: zeile 3 neu" in diff.hunks[0].readable()
    assert "Entfernt: zeile 3" in diff.hunks[0].readable()
    new = staging.file_diff(code, "c.py", "neu")
    assert new.text == ["print('neu')"] and not new.partial_possible


@needs_git
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_only_the_chosen_hunk_is_committed(tmp_path, newline):
    code = repo(tmp_path, newline)
    found = sync.changes(code)
    staging.stage(code, {"a.py": {0}, "c.py": None}, found.kinds())
    git.run(["commit", "-q", "-m", "Teil"], code)
    text = committed(code, "a.py")
    assert "zeile 3 neu" in text and "zeile 35 neu" not in text
    assert committed(code, "c.py") == "print('neu')\n"
    assert committed(code, "b.py") == "eins\n"                     # nicht gewählt
    rest = sync.changes(code)                                       # bleibt für später
    assert sorted(rest.files) == ["a.py", "b.py"]
    assert "zeile 35 neu" in (code / "a.py").read_text(encoding="utf-8")


@needs_git
def test_commit_step_uses_the_selection(tmp_path, make_services, projects_root):
    from tests.conftest import make_project
    code = repo(tmp_path)
    services = make_services([])
    project = services.projects.add(make_project(projects_root, "Rechner"))
    import dataclasses
    project = dataclasses.replace(project, code_dir=code)
    context = FlowContext(services, project, None, threading.Event(),
                          data={"message": "Nur b", "selection": {"b.py": None}})
    result = sync._step_commit(context)
    assert result.ok and committed(code, "b.py") == "zwei\n"
    assert "zeile 3 neu" not in committed(code, "a.py")
    context = FlowContext(services, project, None, threading.Event(),
                          data={"message": "Rest"})
    sync._step_commit(context)                                     # ohne Auswahl: alles
    assert not sync.changes(code)


@needs_git
def test_renamed_file_takes_the_old_name_along(tmp_path):
    code = repo(tmp_path)
    git.run(["mv", "b.py", "bb.py"], code)
    found = sync.changes(code)
    assert found.origins == {"bb.py": "b.py"}
    staging.stage(code, {"bb.py": None}, found.kinds(), found.origins)
    git.run(["commit", "-q", "-m", "Umbenannt"], code)
    assert committed(code, "b.py") == "" and committed(code, "bb.py")


@needs_git
def test_dialog_unchecks_files_and_chooses_hunks(qtbot, tmp_path, monkeypatch):
    from cockpit.ui import sync_dialogs
    code = repo(tmp_path)
    dialog = sync_dialogs.CommitDialog("Änderungen hochladen", sync.changes(code), code_dir=code)
    qtbot.addWidget(dialog)
    assert dialog.selection is None                                  # alles angehakt
    b = next(dialog.files.item(r) for r in range(dialog.files.count())
             if dialog.files.item(r).text().startswith("b.py"))
    b.setCheckState(Qt.CheckState.Unchecked)

    class Chooser:
        def __init__(self, diff, chosen, parent=None):
            self.chosen = {1}

        def exec(self):
            return 1

    monkeypatch.setattr(sync_dialogs, "HunksDialog", Chooser)
    dialog.files.setCurrentRow(0)                                    # a.py, geändert
    dialog.show_file()
    assert dialog.files.item(0).text() == "a.py, geändert, 1 von 2 Abschnitten"
    assert dialog.selection == {"a.py": {1}, "c.py": None}
    dialog.summary.setText("Teil")
    errors = []
    monkeypatch.setattr(sync_dialogs, "show_error", lambda parent, title, text: errors.append(text))
    for r in range(dialog.files.count()):
        dialog.files.item(r).setCheckState(Qt.CheckState.Unchecked)
    dialog.check()
    assert errors == [sync_dialogs.NOTHING_CHOSEN] and dialog.result() == 0


@needs_git
def test_hunks_dialog_space_and_take(qtbot, tmp_path):
    from cockpit.ui.sync_dialogs import HunksDialog
    code = repo(tmp_path)
    dialog = HunksDialog(staging.file_diff(code, "a.py", "geändert"), None)
    qtbot.addWidget(dialog)
    assert dialog.list.item(0).checkState() == Qt.CheckState.Checked
    dialog.list.item(0).setCheckState(Qt.CheckState.Unchecked)
    dialog.take()
    assert dialog.chosen == {1}


@needs_git
def test_ai_sees_only_the_chosen_files_and_hunks(tmp_path):
    """Der KI-Vorschlag passt zur Auswahl: nur a.py Abschnitt 2 und c.py, ohne b.py."""
    from cockpit.features.ai_assistant import context
    code = repo(tmp_path)
    text = context.commit_context(code, 8000, {"a.py": {1}, "c.py": None})
    assert "a.py, geändert" in text and "c.py, neu" in text and "b.py" not in text
    assert "+zeile 35 neu" in text and "zeile 3 neu" not in text
    assert "+zwei" not in text and "Neue Datei c.py:\nprint('neu')" in text
    everything = context.commit_context(code, 8000)
    assert "+zeile 3 neu" in everything and "+zwei" in everything