"""Aufräumrunde der Aktionen (Liste des Nutzers vom 20.10.2026).

Seltene Aktionen stehen unter "Weitere …", "Terminal …" steht auf jeder Zeile ganz unten, und
Strg+T öffnet es direkt. "Branches verwalten …" steht in der Auswahl "Branches …".
"""
from __future__ import annotations

import dataclasses

from cockpit.core import project_status
from cockpit.core.actions import (MORE_TEXT, TERMINAL_ORDER, Action, ActionEntry, Target,
                                  find_entry, shown_entries)
from cockpit.core.availability import Availability
from tests.test_phase10f import structured, window
from tests.test_projektuebersichten import REMOTE


def entry(action_id, text, order=100, more=False):
    return ActionEntry(Action(action_id, text, Target.CODE, lambda c: None, order=order,
                              more=more), Availability.yes())


def test_rare_actions_go_under_more_and_terminal_stays_last():
    entries = [entry("push", "Hochladen", 10), entry("stash", "Beiseitelegen", 36, more=True),
               entry("history", "Verlauf", 30), entry("terminal_code", "Terminal …",
                                                      TERMINAL_ORDER)]
    shown = shown_entries(entries)
    assert [e.text for e in shown] == ["Hochladen", "Verlauf", MORE_TEXT, "Terminal …"]
    assert [c.text for c in shown[2].children] == ["Beiseitelegen"]
    assert find_entry(shown, "stash").text == "Beiseitelegen"
    assert shown_entries(entries[:1]) == entries[:1]                 # ohne Seltenes kein Menü


def test_action_list_shows_more(qtbot, tmp_path, projects_root, make_services):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    win.project_list.update_status(project_status.compute(project), project)
    win.project_list.expand(project.id, speak=False)
    assert win.project_list.select(Target.PROJECT, project.id)
    win.refresh_actions()
    texts = win.actions_list.texts()
    assert texts[-2:] == [MORE_TEXT, "Terminal …"]
    more = win.actions_list.entries[-2]
    assert "Features dieses Projekts …" in [c.text for c in more.children]
    assert "Features dieses Projekts …" not in texts
    assert win.focus_action(project.id, "project_features")          # springt auf "Weitere …"
    assert win.actions_list.current_entry() is win.actions_list.entries[-2]


def test_ctrl_t_opens_the_terminal_of_the_row(qtbot, tmp_path, projects_root, make_services,
                                              monkeypatch):
    services, project, _other = structured(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    opened = []
    monkeypatch.setattr(win.controller, "terminal_action",
                        lambda context, folder, where: opened.append((folder, where)))
    win.project_list.update_status(project_status.compute(project), project)
    assert win.project_list.select(Target.PROJECT, project.id)
    win.open_terminal_here()
    assert opened == [(project.project_dir, "")]


def test_branches_choice_offers_manage(qtbot, tmp_path, projects_root, make_services,
                                       monkeypatch):
    from cockpit.ui import project_actions, project_list
    services, project, _other = structured(tmp_path, projects_root, make_services)
    win = window(qtbot, services)
    win.project_list.update_status(project_status.compute(project), project)
    win.project_list.expand(project.id, speak=False)
    assert win.project_list.select(Target.REPOSITORY, project.id)
    offered, managed = [], []
    monkeypatch.setattr(project_list, "pick_show", lambda listing, names, current, extra=None:
                        offered.append(extra) or project_actions.MANAGE_BRANCHES)
    monkeypatch.setattr(win.controller, "branches_action", managed.append)
    context = win.action_context()
    context.project = dataclasses.replace(context.project, remote=REMOTE)
    win.controller.branch_show_action(context)
    assert offered == [{project_actions.MANAGE_BRANCHES: "Branches verwalten …"}]
    assert len(managed) == 1
