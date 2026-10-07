"""Korrekturen beim Hochladen (Rückmeldung des Nutzers vom 07.10.2026).

Versionsfrage nur auf main, Schritte ohne Arbeit werden nicht gezählt, Rückfragen nennen ihren
Schritt, der README-Vorschlag kommt in ein Fenster, aus dem Tab herausführt, und Töne beim Hoch-
und Herunterladen.
"""
from __future__ import annotations

import dataclasses
import threading

import pytest
from PySide6.QtCore import Qt

from cockpit.core import git, worktrees
from cockpit.core.flows.engine import Flow, FlowContext
from cockpit.core.flows.hooks import Hook
from cockpit.core.flows.questions import ChoiceQuestion, ScriptedAsker
from cockpit.core.flows.step import Step, StepResult
from cockpit.ui import sounds
from cockpit.ui.proposal_dialog import ProposalDialog
from tests.conftest import make_project, manifest, said

needs_git = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


# -- Schritte zählen und nennen ------------------------------------------------------------------
def asking(context):
    context.data["answer"] = context.ask(ChoiceQuestion("Version", "Neue Version?", ("Nein", "Ja")))
    return StepResult(True)


FLOW = Flow("push_changes", "Änderungen hochladen", (
    Step("check", "Sicherheitsprüfung", Hook.BEFORE_PUSH, lambda c: StepResult(True), 10),
    Step("choose", "Version festlegen", Hook.BEFORE_PUSH, asking, 20),
    Step("tag", "Version als Tag setzen", Hook.BEFORE_PUSH, lambda c: StepResult(True), 30,
         applies=lambda c: c.data.get("answer") == 1),
    Step("push", "Wird hochgeladen", Hook.PUSH, lambda c: StepResult(True, "Hochgeladen.")),
))


def run_flow(make_services, projects_root, answer):
    services = make_services([])
    project = services.projects.add(make_project(projects_root, "Rechner"))
    asker = ScriptedAsker(answer)
    progress = []
    context = FlowContext(services, project, asker, threading.Event())
    summary = services.flows.run(FLOW, context, lambda n, t, text: progress.append(text))
    return summary, progress, asker


def test_steps_without_work_are_not_counted(make_services, projects_root):
    summary, progress, _asker = run_flow(make_services, projects_root, 0)
    assert progress == ["Schritt 1 von 3: Sicherheitsprüfung",
                        "Schritt 2 von 3: Version festlegen", "Schritt 3 von 3: Wird hochgeladen"]
    assert summary.completed and summary.text() == "Fertig. Hochgeladen."


def test_a_chosen_version_adds_its_step(make_services, projects_root):
    _summary, progress, _asker = run_flow(make_services, projects_root, 1)
    assert progress == ["Schritt 1 von 3: Sicherheitsprüfung",
                        "Schritt 2 von 3: Version festlegen",
                        "Schritt 3 von 4: Version als Tag setzen",
                        "Schritt 4 von 4: Wird hochgeladen"]


def test_questions_name_their_step(make_services, projects_root):
    _summary, _progress, asker = run_flow(make_services, projects_root, 0)
    assert asker.questions[0].title == "Version, Schritt 2 von 3: Version festlegen"


# -- Versionsfrage nur auf main -------------------------------------------------------------------
@needs_git
def test_no_version_question_on_another_branch(tmp_path, projects_root, make_services):
    from cockpit.features.versions import steps
    from tests.test_phase10f import structured
    services, project, _other = structured(tmp_path, projects_root, make_services)
    tree = worktrees.open_branch(project, "suche")
    on_branch = dataclasses.replace(project, code_dir=tree.path)
    asker = ScriptedAsker()
    context = FlowContext(services, on_branch, asker, data={"message": "Suche verbessert"})
    result = steps.choose(context)
    assert asker.questions == []
    assert result.ok and result.text == ("Die Version legen Sie fest, wenn die Änderungen in "
                                         "main hochgeladen werden.")
    context = FlowContext(services, project, asker, data={"message": "Neu"})
    steps.choose(context)
    assert asker.questions[0].text.startswith("Ist das eine neue Version?")


# -- README-Vorschlag ----------------------------------------------------------------------------------
def test_proposal_is_read_only_and_tab_leaves_it(qtbot):
    dialog = ProposalDialog("README: Änderungen", "Vorschlag der KI.", "## Änderungen\n\n- neu")
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.edit.setFocus()
    assert dialog.edit.isReadOnly() and dialog.edit.tabChangesFocus()
    qtbot.keyClick(dialog.edit, Qt.Key.Key_Tab)
    assert dialog.focusWidget() is dialog.take_button
    assert dialog.edit.toPlainText() == "## Änderungen\n\n- neu"     # kein Tabzeichen
    assert dialog.skip_button.isDefault()                            # die sichere Antwort


def test_proposal_edit_and_take(qtbot):
    dialog = ProposalDialog("README", "Vorschlag.", "alt")
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.edit_button.click()
    assert not dialog.edit.isReadOnly() and said("Text bearbeitbar.")
    dialog.edit.setPlainText("neu")
    dialog.take_button.click()
    assert dialog.result() == dialog.DialogCode.Accepted and dialog.text == "neu"


def test_proposal_escape_skips(qtbot):
    dialog = ProposalDialog("README", "Vorschlag.", "alt")
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.keyClick(dialog, Qt.Key.Key_Escape)
    assert dialog.result() == dialog.DialogCode.Rejected


# -- Töne ---------------------------------------------------------------------------------------------
def test_transfer_sound_start_ticks_and_end(qtbot, played):
    sound = sounds.TransferSound(True)
    sound.timer.setInterval(20)
    sound.start()
    qtbot.waitUntil(lambda: sounds.TICK in played, timeout=2000)
    sound.finish(True)
    assert played[0] == sounds.START and played[-1] == sounds.DONE
    assert not sound.timer.isActive()


def test_transfer_sound_error_cancel_and_off(played):
    sound = sounds.TransferSound(True)
    sound.start()
    sound.finish(False)
    assert played == [sounds.START, sounds.ERROR]
    played.clear()
    sound = sounds.TransferSound(True)
    sound.start()
    sound.stop()
    sound.finish(True)                                 # nach Abbrechen kein Ton mehr
    assert played == [sounds.START]
    played.clear()
    sound = sounds.TransferSound(False)
    sound.start()
    sound.finish(True)
    assert played == []


def test_run_task_plays_for_transfers_only(qtbot, make_services, played):
    from tests.test_phase10f import window
    services = make_services([])
    win = window(qtbot, services)
    done = []
    win.controller.run_task("t1", lambda task: 1, done.append, "Test")
    qtbot.waitUntil(lambda: done == [1], timeout=5000)
    assert played == []
    win.controller.run_task("t2", lambda task: 2, done.append, "Test", transfer=True)
    qtbot.waitUntil(lambda: done == [1, 2], timeout=5000)
    assert played == [sounds.START, sounds.DONE]
    played.clear()
    settings = services.settings.load()
    settings.transfer_sounds = False
    services.settings.save(settings)
    win.controller.run_task("t3", lambda task: 3, done.append, "Test", transfer=True)
    qtbot.waitUntil(lambda: done == [1, 2, 3], timeout=5000)
    assert played == []
