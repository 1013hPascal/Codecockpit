"""Auf GitHub hochladen (Konzept 9.1, geändert: Hinzufügen und Hochladen sind getrennt).

Ablauf:
1. Vorbereiten (prepare): Git-Repository anlegen, .gitignore anlegen oder ergänzen, LICENSE
   anlegen, Git-Identität. Das Projekt ist schon in der Liste (ENTSCHEIDUNGEN.md: Hinzufügen und
   Hochladen sind getrennt, es wird nie kopiert).
2. Sicherheitsprüfung mit Rückfragen in der Oberfläche.
3. Der Ablauf NEW_PROJECT mit den Schritten des Kerns und der aktiven Features:
   Sicherheitsprüfung, Commit "Erste Version", Repository anlegen, Hochladen.

Nie ein force push. Das Hochladen darf wiederholt werden: Gibt es das Repository schon (Remote
origin), wird es nicht noch einmal angelegt.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from cockpit.core import git, identity, safety_check
from cockpit.core.projects import read_config, write_config
from cockpit.core.errors import CockpitError
from cockpit.core.flows.engine import Flow, FlowContext
from cockpit.core.flows.hooks import Hook
from cockpit.core.flows.step import Step, StepResult

log = logging.getLogger(__name__)

NO_LICENSE = "Keine Lizenz / firmenintern"
FIRST_MESSAGE = "Erste Version"
NAME_PATTERN = re.compile(r"[A-Za-z0-9._-]+")


@dataclass
class UploadSpec:
    name: str                          # Name auf der Plattform
    description: str = ""
    private: bool = True
    license: str = "MIT"               # SPDX-Kennung oder NO_LICENSE
    organization: str = ""             # leer: eigenes Konto
    account_id: int | None = None
    accepted: set[tuple[str, str, str]] = field(default_factory=set)   # bestätigte Warnungen
    features: set[str] | None = None   # Features für cockpit.toml (Phase 7), None: nichts ändern


def suggest_name(folder_name: str) -> str:
    """Vorschlag für den Namen auf der Plattform: Leerzeichen werden zu Bindestrichen, Umlaute
    werden umschrieben, andere Zeichen fallen weg."""
    name = "-".join(folder_name.split())
    for old, new in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "Ae"), ("Ö", "Oe"),
                     ("Ü", "Ue"), ("ß", "ss")):
        name = name.replace(old, new)
    return "".join(c for c in name if (c.isascii() and c.isalnum()) or c in "-_.") or "projekt"


def name_problem(name: str) -> str:
    """Was am Namen für die Plattform nicht passt, als Satz. Leer, wenn alles passt."""
    name = name.strip()
    if not name:
        return "Bitte einen Namen eingeben."
    if NAME_PATTERN.fullmatch(name):
        return ""
    if " " in name:
        return ("Der Name darf keine Leerzeichen enthalten. Nehmen Sie stattdessen einen "
                f"Bindestrich, zum Beispiel {suggest_name(name)}.")
    if any(c in "äöüÄÖÜß" for c in name):
        return f"Der Name darf keine Umlaute enthalten, zum Beispiel {suggest_name(name)}."
    return ("Der Name darf nur Buchstaben, Ziffern, Punkt, Bindestrich und Unterstrich "
            f"enthalten, zum Beispiel {suggest_name(name)}.")


def history_range(code_dir: Path) -> str:
    """Commits, die noch nicht hochgeladen sind."""
    if not git.is_repo(code_dir):
        return ""
    if git.run(["rev-parse", "-q", "--verify", "HEAD"], code_dir, check=False).returncode != 0:
        return ""
    upstream = git.run(["rev-parse", "--abbrev-ref", "-q", "@{u}"], code_dir,
                       check=False).stdout.strip()
    return f"{upstream}..HEAD" if upstream else "HEAD"


def prepare(code_dir: Path, project_name: str, spec: UploadSpec, platform, git_name: str,
            git_email: str, asker) -> list[str]:
    """Git, .gitignore, LICENSE und Identität. Gibt kurze Sätze zurück, was getan wurde."""
    done: list[str] = []
    if not git.is_repo(code_dir):
        git.init(code_dir)
        done.append("Git-Repository angelegt.")
    identity.ensure(code_dir, project_name, git_name, git_email, asker)
    added = safety_check.ensure_gitignore(code_dir)
    if added:
        done.append(f".gitignore ergänzt um {len(added)} Einträge.")
    if spec.license and spec.license != NO_LICENSE and not _has_license(code_dir):
        text = platform.license_text(spec.license, git_name or spec.name, datetime.now().year)
        if text:
            (code_dir / "LICENSE").write_text(text, encoding="utf-8")
            done.append(f"Lizenzdatei {spec.license} angelegt.")
        else:
            done.append("Die Lizenzvorlage war nicht erreichbar. Es wurde keine LICENSE angelegt.")
    if spec.features is not None:
        # Konzept 9.1: Die Features stehen in cockpit.toml und kommen mit in die erste Version
        data = read_config(code_dir)
        features = data.get("features") if isinstance(data.get("features"), dict) else {}
        features["enabled"] = sorted(spec.features)
        data["features"] = features
        write_config(code_dir, data)
    return done


def _has_license(code_dir: Path) -> bool:
    return any(p.is_file() and p.stem.upper() in ("LICENSE", "LICENCE", "COPYING")
               for p in code_dir.iterdir())


def scan(code_dir: Path, spec: UploadSpec, git_email: str) -> safety_check.Report:
    """Sicherheitsprüfung vor dem ersten Hochladen, ohne schon bestätigte Warnungen."""
    history = history_range(code_dir)
    emails = safety_check.commit_emails(code_dir, history)
    local_email = git.identity(code_dir)[1] if git.is_repo(code_dir) else ""
    emails.append(local_email or git_email)
    report = safety_check.scan(code_dir, public=not spec.private, emails=emails,
                               history_range=history)
    report.findings = [f for f in report.findings
                       if (f.kind.value, f.path, f.rule) not in spec.accepted]
    return report


# -- Schritte des Ablaufs ---------------------------------------------------------------------
def _step_check(context: FlowContext) -> StepResult:
    spec: UploadSpec = context.data["spec"]
    report = scan(context.project.code_dir, spec, context.data.get("git_email", ""))
    if report.blocking:
        first = report.blocking[0]
        return StepResult(False, "Die Sicherheitsprüfung hat das Hochladen gestoppt.",
                          first.text)
    if report.warnings:
        return StepResult(False, "Die Sicherheitsprüfung hat neue Warnungen gefunden. Bitte "
                          "starten Sie das Hochladen noch einmal.", report.warnings[0].text)
    return StepResult(True)


def _step_commit(context: FlowContext) -> StepResult:
    code_dir = context.project.code_dir
    git.run(["add", "-A"], code_dir, action="Dateien vormerken")
    unborn = git.run(["rev-parse", "-q", "--verify", "HEAD"], code_dir,
                     check=False).returncode != 0
    changes = git.run(["diff", "--cached", "--quiet"], code_dir, check=False).returncode != 0
    if unborn:
        git.run(["commit", "-q", "-m", FIRST_MESSAGE], code_dir, action="Commit")
        return StepResult(True)
    if changes:
        git.run(["commit", "-q", "-m", "Änderungen vor dem ersten Hochladen"], code_dir,
                action="Commit")
    return StepResult(True)


def _step_create(context: FlowContext) -> StepResult:
    code_dir = context.project.code_dir
    spec: UploadSpec = context.data["spec"]
    platform = context.data["platform"]
    existing = git.config_get(code_dir, "remote.origin.url")
    if existing:
        context.data["remote_url"] = existing
        return StepResult(True)
    from cockpit.platforms.base import NewRepo
    ref = platform.create_repo(NewRepo(spec.name, spec.description, spec.private,
                                       spec.organization, spec.license))
    url = platform.clone_url(ref)
    git.run(["remote", "add", "origin", url], code_dir, action="Verbinden")
    context.data["remote_url"] = url
    context.data["repo"] = ref
    visibility = "privates" if spec.private else "öffentliches"
    return StepResult(True, f"Neues {visibility} Repository {ref.owner}/{ref.name}.")


def _step_push(context: FlowContext) -> StepResult:
    code_dir = context.project.code_dir
    platform = context.data["platform"]
    branch = git.status(code_dir).branch or git.MAIN_BRANCH
    env = dict(platform.git_credentials().environment)
    git.run(["push", "-u", "origin", branch], code_dir, env=env, timeout=None,
            cancel=context.cancel_event, action="Hochladen")
    context.data["branch"] = branch
    return StepResult(True, f"Branch {branch} ist hochgeladen.")


NEW_PROJECT = Flow("new_project", "Neues Projekt hochladen", (
    Step("safety_check", "Sicherheitsprüfung", Hook.BEFORE_COMMIT_MESSAGE, _step_check, order=10),
    Step("first_commit", "Commit wird erstellt", Hook.BEFORE_PUSH, _step_commit, order=900),
    Step("create_repo", "Repository wird angelegt", Hook.PUSH, _step_create, order=10),
    Step("push", "Wird hochgeladen", Hook.PUSH, _step_push, order=20),
))
