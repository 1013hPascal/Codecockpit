"""Phase 8a: Eingebautes Terminal.

Die Befehle laufen wirklich in PowerShell, aber nur harmlose (echo, git log, Start-Sleep) in
temporären Ordnern. Alle Geheimnisse sind erfunden.
"""
from __future__ import annotations

import sys
import threading
import time

import pytest

from cockpit.core import git, terminal
from cockpit.core.errors import Cancelled, CockpitError
from cockpit.ui import terminal_dialog
from tests.conftest import said
from tests.test_phase5a import sh
from tests.test_phase5b import write

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Terminal nutzt PowerShell")


# -- Kern -----------------------------------------------------------------------------------------
def test_output_lines_and_exit_codes(tmp_path):
    result = terminal.run("echo eins; echo 'Ä zwei'; echo ''", tmp_path)
    assert result.ok and result.lines == ["eins", "Ä zwei"]      # leere Zeilen fallen weg
    failed = terminal.run("echo vorher; exit 3", tmp_path)
    assert failed.code == 3 and failed.lines == ["vorher"]


def test_errors_are_plain_text(tmp_path):
    result = terminal.run("Get-Item gibt-es-nicht.txt", tmp_path)
    assert result.code == 1
    assert len(result.lines) == 1 and "gibt-es-nicht.txt" in result.lines[0]
    assert "CLIXML" not in result.lines[0] and "In Zeile" not in result.lines[0]
    native = terminal.run("git gibtesnicht", tmp_path)
    assert native.code == 1 and native.lines[0].startswith("git: 'gibtesnicht' is not a git")


def test_lines_arrive_one_by_one(tmp_path):
    seen = []
    terminal.run("echo a; echo b", tmp_path, seen.append)
    assert seen == ["a", "b"]


def test_runs_in_the_given_folder(tmp_path):
    (tmp_path / "hier.txt").write_text("x", encoding="utf-8")
    result = terminal.run("(Get-ChildItem -Name) -join ','", tmp_path)
    assert result.lines == ["hier.txt"]


@pytest.mark.parametrize("command", [
    "git push -f", "git push --force origin main", "git push --force-with-lease",
    "git push origin +main", "echo x; git push -uf origin main"])
def test_force_push_is_blocked(tmp_path, command):
    assert terminal.is_force_push(command)
    with pytest.raises(CockpitError, match="force push"):
        terminal.run(command, tmp_path)


@pytest.mark.parametrize("command", ["git push", "git push -u origin main", "git log -f",
                                     "git fetch --force"])
def test_normal_commands_are_not_force_push(command):
    assert not terminal.is_force_push(command)


def test_secrets_are_masked(tmp_path):
    from cockpit.core.secret import Secret
    fake = Secret("ghp_ErfundenFuerDasTerminal0123456789ab")
    fake.reveal()                                                 # jetzt bekannt
    result = terminal.run(f"echo 'Token {fake.reveal()}'; echo 'Wert GEHEIMERWERT123'",
                          tmp_path, extra_env={"GIT_CONFIG_VALUE_0": "GEHEIMERWERT123"})
    assert result.lines == ["Token ***", "Wert ***"]


def test_git_never_waits(tmp_path):
    git.init(tmp_path)
    write(tmp_path, "a.txt", "x\n")
    sh(tmp_path, "add", "-A")
    started = time.monotonic()
    result = terminal.run("git -c user.name=T -c user.email=t@example.org commit", tmp_path)
    assert time.monotonic() - started < 20                        # kein Editor, kein Warten
    assert result.code != 0
    env = terminal.environment()
    assert env["GIT_PAGER"] == "cat" and env["GIT_TERMINAL_PROMPT"] == "0"


def test_cancel_stops_the_command(tmp_path):
    cancel = threading.Event()
    threading.Timer(1.0, cancel.set).start()
    started = time.monotonic()
    with pytest.raises(Cancelled):
        terminal.run("Start-Sleep -Seconds 30; echo nie", tmp_path, cancel=cancel)
    assert time.monotonic() - started < 15


def test_empty_command(tmp_path):
    with pytest.raises(CockpitError, match="Bitte geben Sie einen Befehl ein"):
        terminal.run("   ", tmp_path)


# -- Fenster ------------------------------------------------------------------------------
def rows(dialog) -> list[str]:
    return [dialog.output.item(i).text() for i in range(dialog.output.count())]


def dialog_for(qtbot, tmp_path):
    dialog = terminal_dialog.TerminalDialog(tmp_path, "Tagebuch, Code")
    qtbot.addWidget(dialog)
    return dialog


def test_dialog_runs_commands(qtbot, tmp_path):
    dialog = dialog_for(qtbot, tmp_path)
    assert dialog.windowTitle() == "Terminal: Tagebuch, Code"
    assert dialog.edit.accessibleName() == "Befehl"
    assert dialog.output.accessibleName() == "Ausgabe"
    assert rows(dialog) == [f"Ordner: {tmp_path}"]
    dialog.edit.setText("echo hallo")
    dialog.run_command()
    qtbot.waitUntil(lambda: not dialog.running, timeout=20000)
    assert rows(dialog)[1:] == ["> echo hallo", "hallo", "Fertig."]
    assert said("Fertig. 1 Zeile Ausgabe.")
    assert dialog.edit.text() == ""
    dialog.edit.setText("exit 2")
    dialog.run_command()
    qtbot.waitUntil(lambda: not dialog.running, timeout=20000)
    assert rows(dialog)[-1] == "Fehler, Rückgabewert 2."


def test_history_with_arrow_keys(qtbot, tmp_path):
    from PySide6.QtCore import Qt
    dialog = dialog_for(qtbot, tmp_path)
    for command in ("echo eins", "echo zwei"):
        dialog.edit.setText(command)
        dialog.run_command()
        qtbot.waitUntil(lambda: not dialog.running, timeout=20000)
    qtbot.keyClick(dialog.edit, Qt.Key.Key_Up)
    assert dialog.edit.text() == "echo zwei"
    qtbot.keyClick(dialog.edit, Qt.Key.Key_Up)
    assert dialog.edit.text() == "echo eins"
    qtbot.keyClick(dialog.edit, Qt.Key.Key_Down)
    qtbot.keyClick(dialog.edit, Qt.Key.Key_Down)
    assert dialog.edit.text() == ""


def test_force_push_in_the_dialog(qtbot, tmp_path):
    dialog = dialog_for(qtbot, tmp_path)
    dialog.edit.setText("git push --force")
    dialog.run_command()
    assert not dialog.running
    assert rows(dialog)[-1] == terminal.FORCE_PUSH
    assert said("Gesperrt. " + terminal.FORCE_PUSH)


def test_escape_cancels_a_running_command(qtbot, tmp_path):
    dialog = dialog_for(qtbot, tmp_path)
    dialog.show()
    dialog.edit.setText("Start-Sleep -Seconds 30")
    dialog.run_command()
    assert dialog.stop_button.isVisible()
    dialog.reject()                                                # Escape
    qtbot.waitUntil(lambda: not dialog.running, timeout=20000)
    assert rows(dialog)[-1] == "Abgebrochen."
    assert dialog.isVisible()                                     # erst das zweite Escape schließt
    dialog.reject()
    assert not dialog.isVisible()


def test_copy_line(qtbot, tmp_path):
    from PySide6.QtGui import QGuiApplication
    dialog = dialog_for(qtbot, tmp_path)
    dialog.output.setCurrentRow(0)
    dialog.copy_line()
    assert QGuiApplication.clipboard().text() == f"Ordner: {tmp_path}"


def test_open_terminal_warns_once(qtbot, make_services, tmp_path, monkeypatch):
    from cockpit.ui import common
    services = make_services()
    infos, opened = [], []
    monkeypatch.setattr(common, "show_info", lambda p, t, text: infos.append(text))

    class FakeDialog:
        def __init__(self, folder, title, env, parent=None):
            opened.append((folder, title))

        def exec(self):
            return 0

    monkeypatch.setattr(terminal_dialog, "TerminalDialog", FakeDialog)
    terminal_dialog.open_terminal(services, None, tmp_path, "X")
    terminal_dialog.open_terminal(services, None, tmp_path, "X")
    assert infos == [terminal.WARNING] and len(opened) == 2


def test_terminal_actions(qtbot, make_services, projects_root):
    from cockpit.core.actions import Target
    from cockpit.ui.main_window import MainWindow
    from tests.conftest import make_project
    services = make_services()
    services.projects.add(make_project(projects_root, "Tagebuch"))
    project = services.projects.all()[0]
    win = MainWindow(services)
    qtbot.addWidget(win)
    win.reload_projects(refresh=False)
    for target in (Target.PROJECT, Target.CODE):
        win.project_list.select(target, project.id)
        assert "Terminal …" in [e.label for e in win.current_entries()]
