"""Optik (PLAN-OPTIK.md, 22.10.2026). Alles nur für das Auge: Texte und Accessible Names der
Zeilen bleiben gleich."""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QListWidget

from cockpit.core.actions import Target
from cockpit.ui import look
from cockpit.ui.project_labels import ROLE_PROJECT
from cockpit.ui.project_list_delegate import CLOSED, OPEN, ProjectRowDelegate
from cockpit.ui.row_delegate import DIM, HEAD, NORMAL, RowDelegate, runs
from cockpit.ui.state_panel import state_lines
from tests.test_ui import window  # noqa: F401 (Fixture)


def project_row(win, name: str):
    project = next(p for p in win.services.projects.all() if p.name == name)
    return win.project_list.row_of(Target.PROJECT, project.id), project


# -- Schritt 1: Gliederung der Projektliste -------------------------------------------------
def test_projects_are_bold_with_arrow(window):  # noqa: F811
    win = window()
    plist = win.project_list
    assert isinstance(plist.itemDelegate(), ProjectRowDelegate)
    row, _ = project_row(win, "Tagebuch")
    assert plist.row_look(row) == (0, CLOSED, True)
    assert plist.row_look(0) == (0, "", False)               # "Neue Projektsammlung"


def test_rows_below_a_project_are_indented(window):  # noqa: F811
    win = window()
    plist = win.project_list
    row, project = project_row(win, "Tagebuch")
    before = plist.texts()
    plist.expand(project.id, speak=False)
    assert plist.row_look(row) == (0, OPEN, True)
    children = [r for r in range(plist.count())
                if r != row and plist.item(r).data(ROLE_PROJECT) == project.id]
    assert children and all(plist.row_look(r) == (1, "", False) for r in children)
    plist.collapse(speak=False)
    assert plist.texts() == before                            # Text unverändert
    assert plist.row_look(row) == (0, CLOSED, True)


def test_rows_paint_without_errors(window):  # noqa: F811
    win = window()
    plist = win.project_list
    _, project = project_row(win, "Tagebuch")
    plist.expand(project.id, speak=False)
    assert not plist.viewport().grab().isNull()               # ruft paint für jede Zeile auf


# -- Schritt 2: Stand, nur für das Auge -----------------------------------------------------
def test_state_lines_split_the_row():
    assert state_lines("Tagebuch, aktualisiert am 18.09.2026, 3 Dateien noch nicht hochgeladen, "
                       "ausgeklappt") == ("Tagebuch", ["aktualisiert am 18.09.2026",
                                                       "3 Dateien noch nicht hochgeladen"])
    assert state_lines("Neue Projektsammlung") == ("Neue Projektsammlung", [])


def test_state_panel_follows_the_row_and_is_no_tab_stop(window):  # noqa: F811
    win = window()
    panel = win.state_panel
    assert panel.focusPolicy() == Qt.FocusPolicy.NoFocus
    assert panel.accessibleName() == "Stand"
    plist = win.project_list
    row, _ = project_row(win, "Tagebuch")
    plist.item(row).setText("Tagebuch, 2 offene Pull Requests")
    plist.setCurrentRow(row)
    assert "2 offene Pull Requests" in panel.text()
    plist.setCurrentRow(0)                                    # "Neue Projektsammlung"
    assert panel.text() == ""
    assert win.areas == [win.project_list, win.actions_list]  # Tab-Kreis unverändert


# -- Schritt 3: zwei Textebenen -------------------------------------------------------------
def test_runs_keep_the_text_and_mark_head_and_time():
    text = "Tagebuch: neuer Kommentar zu Issue 12, von anna, heute 18:03"
    pieces = runs(text, ": ")
    assert "".join(t for t, _ in pieces) == text
    assert pieces[0] == ("Tagebuch", HEAD)
    assert pieces[-1] == ("heute 18:03", DIM)
    project = "Tagebuch, aktualisiert am 18.09.2026, 3 Dateien noch nicht hochgeladen"
    pieces = runs(project)
    assert "".join(t for t, _ in pieces) == project
    assert ("aktualisiert am 18.09.2026", DIM) in pieces
    assert ("3 Dateien noch nicht hochgeladen", NORMAL) in pieces
    assert runs("Code, alles hochgeladen", bold_head=False)[0] == ("Code", NORMAL)


def test_news_list_uses_the_row_delegate(qtbot, make_services):
    from cockpit.ui.news_dialogs import ActivityDialog, NewsDialog
    services = make_services()
    for dialog in (NewsDialog(services, None), ActivityDialog(services)):
        qtbot.addWidget(dialog)
        assert isinstance(dialog.list.itemDelegate(), RowDelegate)


# -- Schritte 4, 5 und 7: Fokus, Erklärungen, Symbole -----------------------------------------
def test_look_uses_only_palette_colors():
    folder = Path(look.__file__).parent
    for name in ("look.py", "row_delegate.py", "project_list_delegate.py", "state_panel.py"):
        source = (folder / name).read_text(encoding="utf-8")
        assert not re.search(r"#[0-9a-fA-F]{3,6}\b|QColor\(|rgb\(", source), name
    assert "palette(highlight)" in look.STYLE


def test_explanations_look_like_text_but_stay_lists(qtbot):
    widget = QListWidget()
    qtbot.addWidget(widget)
    look.mark_explanation(widget)
    assert widget.property("explanation") is True
    assert widget.frameShape() == QListWidget.Shape.NoFrame


def test_app_icon_and_menu_icons(window):  # noqa: F811
    icon = look.app_icon(QApplication.instance().palette())
    assert not icon.isNull() and icon.availableSizes()
    win = window()
    actions = {a.text(): a for a in win.findChildren(QAction)}
    assert not actions["Hilfe und &Kurzanleitungen …"].icon().isNull()
    assert actions["&Beenden"].icon().isNull()                # nur bekannte Einträge


# -- Schritt 6: Gruppen ---------------------------------------------------------------------
def test_ai_group_row_is_bold(qtbot, make_services):
    from cockpit.core.features.registry import FeatureRegistry
    from cockpit.ui.features_dialogs import GlobalFeaturesDialog
    dialog = GlobalFeaturesDialog(make_services(FeatureRegistry.discover().all()))
    qtbot.addWidget(dialog)
    row = dialog.rows.index(None)
    assert dialog.list.item(row).font().bold()
    assert not dialog.list.item(0).font().bold()
