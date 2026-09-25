"""Git-Identität in jedem Projekt (Konzept 9.8, ENTSCHEIDUNGEN.md).

Das Cockpit trägt Name und E-Mail-Adresse aus den Grundeinstellungen nur im Repository ein, nie
global für den ganzen Rechner. Hat ein Repository schon eine andere Identität, fragt es nach. Die
sichere Vorgabe ist "Vorhandene behalten".
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path

from cockpit.core import git
from cockpit.core.flows.questions import Asker, ConfirmQuestion


class IdentityState(Enum):
    NO_REPO = "no_repo"              # noch kein Git-Repository
    NOT_SET = "not_set"              # in den Grundeinstellungen fehlt Name oder Adresse
    SAME = "same"
    MISSING = "missing"              # im Repository steht noch nichts
    DIFFERENT = "different"


def state(code_dir: Path, name: str, email: str) -> IdentityState:
    if not git.is_repo(code_dir):
        return IdentityState.NO_REPO
    if not name or not email:
        return IdentityState.NOT_SET
    current = git.identity(code_dir)
    if current == ("", ""):
        return IdentityState.MISSING
    if current == (name, email):
        return IdentityState.SAME
    return IdentityState.DIFFERENT


def ensure(code_dir: Path, project_name: str, name: str, email: str,
           asker: Asker | None) -> bool:
    """Identität eintragen, bei einer anderen vorher fragen. True, wenn danach die Identität aus
    den Grundeinstellungen gilt."""
    current_state = state(code_dir, name, email)
    if current_state is IdentityState.SAME:
        return True
    if current_state is IdentityState.MISSING:
        git.set_identity(code_dir, name, email)
        return True
    if current_state is IdentityState.DIFFERENT and asker is not None:
        old_name, old_email = git.identity(code_dir)
        old = ", ".join(v for v in (old_name, old_email) if v)
        question = ConfirmQuestion(
            "Git-Identität",
            f"{project_name} hat eine andere Git-Identität: {old}. In den Grundeinstellungen "
            f"steht: {name}, {email}. Soll das Projekt die Identität aus den Grundeinstellungen "
            "bekommen?",
            yes="Grundeinstellungen übernehmen", no="Vorhandene behalten")
        if asker.ask(question):
            git.set_identity(code_dir, name, email)
            return True
    return False
