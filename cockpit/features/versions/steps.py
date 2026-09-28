"""Schritte des Features Versionen im Ablauf "Änderungen hochladen" (Phase 9).

1. Vor dem Commit: fragen, ob es eine neue Version ist. Vorgabe "Keine neue Version". Bei Ja die
   Nummer im Code ändern, damit sie in denselben Commit kommt.
2. Nach dem Commit: Tag setzen.
3. Nach dem Hochladen des Branches: Tag hochladen.
"""
from __future__ import annotations

from cockpit.core import git
from cockpit.core.flows.engine import FlowContext
from cockpit.core.flows.questions import ChoiceQuestion
from cockpit.core.flows.step import StepResult
from cockpit.features.versions import versions

FEATURE_ID = "versions"


def _version_file(context: FlowContext) -> str:
    chosen = ""
    if context.services is not None:
        try:
            chosen = context.services.features.setting(FEATURE_ID, "version_file") or ""
        except KeyError:
            chosen = ""
    return chosen or versions.find_version_file(context.project.code_dir)


def choose(context: FlowContext) -> StepResult:
    code_dir = context.project.code_dir
    state = git.status(code_dir)
    if not context.data.get("message") and state.upstream and not state.ahead:
        return StepResult(True)                        # nichts Neues, also keine Version
    version = versions.current(code_dir)
    answer = context.ask(ChoiceQuestion(
        "Version", f"Ist das eine neue Version? Bisher: {version or 'noch keine'}.",
        versions.options(version), 0))
    if not answer:
        return StepResult(True)
    new = versions.bump(version, int(answer))
    context.data["version"] = new
    name = _version_file(context)
    if name and (code_dir / name).is_file() and versions.set_version_in_file(code_dir / name, new):
        context.data["version_file"] = name
    return StepResult(True)


def tag(context: FlowContext) -> StepResult:
    new = context.data.get("version")
    if not new:
        return StepResult(True)
    code_dir = context.project.code_dir
    name = context.data.get("version_file")
    if name and not context.data.get("commit"):
        # Ohne eigenen Commit im Ablauf (nur hochladen): Versionsnummer allein committen
        git.run(["add", "--", name], code_dir, action="Version setzen")
        if git.run(["diff", "--cached", "--quiet"], code_dir, check=False).returncode != 0:
            git.run(["commit", "-q", "-m", f"Version {new}"], code_dir, action="Version setzen")
    versions.create_tag(code_dir, new)
    return StepResult(True, f"Version {new}.")


def push(context: FlowContext) -> StepResult:
    new = context.data.get("version")
    if not new:
        return StepResult(True)
    versions.push_tag(context.project.code_dir, new, context.data.get("env") or {},
                      context.cancel_event)
    return StepResult(True)
