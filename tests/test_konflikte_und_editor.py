"""Konfliktstellen vorlesen und einzeln lösen, im Editor öffnen (Wunsch des Nutzers vom
21.10.2026, nach dem Vergleich mit GitHub Desktop)."""
from __future__ import annotations

from pathlib import Path

import pytest

from cockpit.core import conflicts, editor, git, sync
from cockpit.core.errors import CockpitError
from cockpit.core.sync import ConflictKind

needs_git = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


def run(code, *args):
    return git.run(list(args), code).stdout.strip()


def conflict_repo(tmp_path, newline=b"\n"):
    """main.py mit zwei Stellen, die in beiden Branches anders geändert sind."""
    code = tmp_path / "code"
    code.mkdir()
    run(code, "init", "-q", "-b", "main")
    run(code, "config", "user.name", "Ich")
    run(code, "config", "user.email", "ich@example.com")
    run(code, "config", "core.autocrlf", "false")
    lines = lambda *xs: newline.join(x.encode() for x in xs) + newline  # noqa: E731
    gap = [f"z{n}" for n in range(6)]                # Abstand, sonst wird es eine Stelle
    (code / "main.py").write_bytes(lines("a", "b", *gap, "f", "g"))
    run(code, "add", "-A")
    run(code, "commit", "-q", "-m", "Start")
    run(code, "checkout", "-q", "-b", "andere")
    (code / "main.py").write_bytes(lines("a", "B andere", *gap, "F andere", "g"))
    run(code, "commit", "-q", "-am", "andere")
    run(code, "checkout", "-q", "main")
    (code / "main.py").write_bytes(lines("a", "B meine", "B meine 2", *gap, "F meine", "g"))
    run(code, "commit", "-q", "-am", "meine")
    git.run(["merge", "andere"], code, check=False)
    assert sync.conflicted(code) == ["main.py"]
    return code


@needs_git
def test_blocks_are_read_in_order(tmp_path):
    code = conflict_repo(tmp_path)
    found = conflicts.blocks(code, "main.py", ConflictKind.MERGE)
    assert [b.line for b in found] == [2, 14]
    assert found[0].mine == ["B meine", "B meine 2"] and found[0].theirs == ["B andere"]
    assert found[0].label(2) == ("Stelle 1 von 2, Zeile 2: meine Fassung 2 Zeilen, GitHub "
                                 "1 Zeile")
    assert found[0].readable() == ["Meine Fassung, 2 Zeilen:", "1: B meine", "2: B meine 2",
                                   "Fassung von GitHub, 1 Zeile:", "1: B andere"]


@needs_git
def test_stash_kind_swaps_the_sides(tmp_path):
    code = conflict_repo(tmp_path)
    found = conflicts.blocks(code, "main.py", ConflictKind.STASH)
    assert found[0].mine == ["B andere"]


@needs_git
@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_resolve_block_by_block(tmp_path, newline):
    code = conflict_repo(tmp_path, newline)
    assert conflicts.resolve_block(code, "main.py", 2, conflicts.THEIRS,
                                   ConflictKind.MERGE) == 1
    assert conflicts.resolve_block(code, "main.py", 1, conflicts.BOTH, ConflictKind.MERGE) == 0
    data = (code / "main.py").read_bytes()
    assert data == newline.join([b"a", b"B meine", b"B meine 2", b"B andere",
                                 *[f"z{n}".encode() for n in range(6)], b"F andere", b"g"]) + newline
    assert not sync.has_markers(code, "main.py")


@needs_git
def test_resolve_a_missing_block(tmp_path):
    code = conflict_repo(tmp_path)
    with pytest.raises(CockpitError):
        conflicts.resolve_block(code, "main.py", 5, conflicts.MINE, ConflictKind.MERGE)


@needs_git
def test_restore_brings_markers_back_with_backup(tmp_path, home):
    code = conflict_repo(tmp_path)
    conflicts.resolve_block(code, "main.py", 1, conflicts.MINE, ConflictKind.MERGE)
    folder = conflicts.restore(code, "main.py")
    assert len(conflicts.blocks(code, "main.py", ConflictKind.MERGE)) == 2
    assert b"B andere" not in (folder / "main.py").read_bytes().split(b"=======")[0]
    assert (folder / "main.py").is_file()


@needs_git
def test_blocks_dialog_reads_and_resolves(qtbot, tmp_path, monkeypatch):
    from PySide6.QtCore import Qt
    from cockpit.ui import conflict_dialogs, text_dialog
    code = conflict_repo(tmp_path)
    read = []
    monkeypatch.setattr(text_dialog.TextDialog, "exec", lambda self: read.append(self.lines))
    dialog = conflict_dialogs.ConflictBlocksDialog(code, "main.py", ConflictKind.MERGE, "GitHub")
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.windowTitle() == "Konfliktstellen in main.py: 2 Stellen offen"
    assert dialog.list.accessibleName() == "Stellen"
    qtbot.keyClick(dialog.list, Qt.Key.Key_Return)
    assert read[0][0] == "Meine Fassung, 2 Zeilen:"
    dialog.choose(conflicts.MINE)
    assert dialog.list.count() == 1 and dialog.isVisible()
    assert dialog.list.item(0).text().startswith("Stelle 1 von 1, Zeile 10")
    dialog.choose(conflicts.THEIRS)
    assert dialog.result() == 1


@needs_git
def test_conflict_dialog_marks_file_after_blocks(qtbot, tmp_path, monkeypatch):
    from cockpit.ui import conflict_dialogs, sync_dialogs

    def solve_all(self):
        conflicts.resolve_block(self.code_dir, self.path, 1, conflicts.MINE, self.kind)
        conflicts.resolve_block(self.code_dir, self.path, 1, conflicts.MINE, self.kind)
        return 1
    monkeypatch.setattr(conflict_dialogs.ConflictBlocksDialog, "exec", solve_all)
    code = conflict_repo(tmp_path)
    dialog = sync_dialogs.ConflictDialog(code, ConflictKind.MERGE, "GitHub")
    qtbot.addWidget(dialog)
    dialog.read_blocks()
    assert dialog.list.item(0).text() == "main.py, gelöst: Stelle für Stelle"
    assert sync.conflicted(code) == []


# -- Editor ----------------------------------------------------------------------------------
def test_editor_commands(tmp_path):
    file = tmp_path / "a.py"
    file.write_text("x", encoding="utf-8")
    code = editor.Editor("Visual Studio Code", Path("C:/VS/Code.exe"), "vscode")
    assert code.command(file, 7) == [str(Path("C:/VS/Code.exe")), "--goto", f"{file}:7"]
    assert code.command(tmp_path) == [str(Path("C:/VS/Code.exe")), str(tmp_path)]
    npp = editor.Editor("Notepad++", Path("n.exe"), "notepadpp")
    assert npp.command(file, 3) == ["n.exe", "-n3", str(file)]
    assert not npp.opens_folders


def test_setting_must_exist(tmp_path):
    with pytest.raises(CockpitError):
        editor.find(str(tmp_path / "gibt-es-nicht.exe"))
    program = tmp_path / "notepad++.exe"
    program.write_bytes(b"")
    assert editor.find(f'"{program}"').kind == "notepadpp"


def test_open_in_editor_and_folder_fallback(tmp_path, monkeypatch):
    from cockpit.core import core_actions
    program = tmp_path / "Code.exe"
    program.write_bytes(b"")
    started, opened = [], []
    monkeypatch.setattr(editor, "start", started.append)
    monkeypatch.setattr(core_actions, "open_path", opened.append)
    file = tmp_path / "a.py"
    file.write_text("x", encoding="utf-8")
    assert editor.open_in_editor(file, 2, str(program)) == "Code"
    assert started == [[str(program), "--goto", f"{file}:2"]]
    npp = tmp_path / "notepad++.exe"
    npp.write_bytes(b"")
    assert editor.open_in_editor(tmp_path, setting=str(npp)) == "Explorer"
    assert opened == [tmp_path]


def test_open_in_editor_action_is_listed():
    from cockpit.core.core_actions import CORE_ACTIONS
    action = next(a for a in CORE_ACTIONS if a.id == "open_in_editor")
    assert action.text == "Im Editor öffnen"
