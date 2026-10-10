"""Nacharbeit aus der Überprüfung vom 08.10.2026."""
from __future__ import annotations

from PySide6.QtCore import Qt

from cockpit.core import local_releases
from cockpit.ui.proposal_dialog import ProposalDialog
from tests.conftest import make_project


def test_release_search_stays_shallow(make_services, projects_root):
    """In einem Programmordner liegen tausende Dateien. Gesucht wird nur oben und eine Ebene
    tiefer, und der Filter „Mit Release“ höchstens zwei Ebenen tief."""
    services = make_services()
    project = services.projects.add(make_project(projects_root, "Tagebuch", exe=True))
    assert not local_releases.has_any_exe(project)
    deep = project.exe_dir / "Tagebuch" / "_internal" / "tief" / "nochtiefer"
    deep.mkdir(parents=True)
    (deep / "helfer.exe").write_bytes(b"MZ")
    assert not local_releases.has_any_exe(project)                 # zu tief, zählt nicht
    (project.exe_dir / "Tagebuch" / "Tagebuch.exe").write_bytes(b"MZ")
    assert local_releases.has_any_exe(project)
    main = local_releases.find(project, "")
    assert local_releases.release_exe(main).name == "Tagebuch.exe"


def test_enter_in_the_proposal_text_does_not_skip(qtbot):
    dialog = ProposalDialog("README", "Vorschlag.", "Text")
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.edit.setFocus()
    qtbot.waitUntil(dialog.edit.hasFocus, timeout=2000)
    qtbot.keyClick(dialog.edit, Qt.Key.Key_Return)
    assert dialog.isVisible() and dialog.result() == 0           # nicht übersprungen
    dialog.skip_button.setFocus()
    qtbot.keyClick(dialog.skip_button, Qt.Key.Key_Return)
    assert dialog.result() == dialog.DialogCode.Rejected


def test_closing_the_main_window_closes_the_help(qtbot, make_services, projects_root):
    from tests.test_phase10f import window
    win = window(qtbot, make_services())
    win.open_help()
    helper = win.help_window
    assert helper.isVisible()
    win.close()
    assert not helper.isVisible()
