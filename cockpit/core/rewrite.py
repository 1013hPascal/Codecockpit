"""Commits nachbessern, übernehmen, zusammenfassen und umsortieren (Wunsch des Nutzers vom
21.10.2026, nach dem Vergleich mit GitHub Desktop).

Grenze, die nie verletzt wird: Was schon hochgeladen ist, bleibt, wie es ist. Nachbessern,
Zusammenfassen und Umsortieren gehen nur bei Commits, die noch nicht hochgeladen sind. Sonst
bräuchte es einen force push, und den gibt es im Cockpit nie (CLAUDE.md).

Jede Änderung merkt sich vorher den alten Stand unter refs/codecockpit/vorher/... Geht etwas
schief, kommt der alte Stand zurück, und die Fehlermeldung sagt, was passiert ist.

- amend: den neuesten Commit nachbessern: neue Nachricht, auf Wunsch mit den Änderungen ohne
  Commit.
- cherry_pick: einen Commit in einen anderen Branch übernehmen (git cherry-pick -x). Mit
  Branch-Ordnern im Ordner dieses Branches.
- reorder: die Commits, die noch nicht hochgeladen sind, neu ordnen und zusammenfassen. Wie
  "interactive rebase", aber ohne Editor: Das Cockpit baut die Commits in der neuen Reihenfolge
  neu auf.
- branch_at: neuer Branch ab einem früheren Commit.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from cockpit.core import git
from cockpit.core.errors import CockpitError
from cockpit.core.history import Commit

log = logging.getLogger(__name__)

BEFORE_REF = "refs/codecockpit/vorher/"
UPLOADED = ("Das geht nur bei Commits, die noch nicht hochgeladen sind. Hochgeladene Commits "
            "bleiben, wie sie sind, sonst müsste das Cockpit die Geschichte auf der Plattform "
            "überschreiben.")
NOT_CLEAN = ("Dafür darf es keine Änderungen ohne Commit geben. Laden Sie sie zuerst hoch, legen "
             "Sie sie beiseite oder verwerfen Sie sie.")


def _remember(code_dir: Path, what: str) -> str:
    """Den jetzigen Stand merken. Gibt den Commit zurück."""
    head = git.run(["rev-parse", "HEAD"], code_dir, action=what).stdout.strip()
    ref = f"{BEFORE_REF}{what.lower().replace(' ', '-')}-{datetime.now():%Y-%m-%d_%H-%M-%S}"
    git.run(["update-ref", ref, head], code_dir, action=what)
    return head


def _clean(code_dir: Path) -> bool:
    result = git.run(["status", "--porcelain", "--untracked-files=no"], code_dir, check=False)
    return not result.stdout.strip()


def _unfinished(code_dir: Path) -> bool:
    folder = git.git_dir(code_dir)
    return any((folder / name).exists() for name in
               ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"))


def _message_args(message: str) -> list[str]:
    args: list[str] = []
    for paragraph in message.split("\n\n"):
        if paragraph.strip():
            args += ["-m", paragraph.strip()]
    if not args:
        raise CockpitError("Bitte schreiben Sie eine Nachricht für den Commit.")
    return args


# -- Nachbessern ---------------------------------------------------------------------------------
def can_amend(commit: Commit) -> bool:
    return commit.newest and not commit.uploaded and len(commit.parents) == 1


def amend(code_dir: Path, commit: Commit, message: str, with_changes: bool) -> None:
    """Den neuesten Commit nachbessern. with_changes: die Änderungen ohne Commit kommen mit
    hinein, sonst ändert sich nur die Nachricht."""
    if not can_amend(commit):
        raise CockpitError(UPLOADED if commit.uploaded else
                           "Nachbessern geht nur beim neuesten Commit.")
    if _unfinished(code_dir):
        raise CockpitError("Ein Zusammenführen ist noch nicht abgeschlossen.")
    _remember(code_dir, "Nachbessern")
    if with_changes:
        git.run(["add", "-A"], code_dir, action="Dateien vormerken")
        git.run(["commit", "-q", "--amend", *_message_args(message)], code_dir,
                action="Nachbessern")
    else:
        # --only ohne Pfade: nur die Nachricht, Vorgemerktes bleibt draußen
        git.run(["commit", "-q", "--amend", "--only", *_message_args(message)], code_dir,
                action="Nachbessern")
    log.info("Commit %s nachgebessert", commit.short)


# -- In einen anderen Branch übernehmen -----------------------------------------------------------
def cherry_pick(target_dir: Path, commit: Commit) -> str:
    """Den Commit in den Branch übernehmen, der in target_dir ausgecheckt ist. Gibt den neuen
    Commit zurück. Bei einem Konflikt bleibt alles, wie es war."""
    if commit.is_merge:
        raise CockpitError("Ein Zusammenführen lässt sich nicht einzeln übernehmen.")
    if not _clean(target_dir):
        raise CockpitError(f"Im Ziel-Branch gibt es Änderungen ohne Commit. {NOT_CLEAN}")
    if _unfinished(target_dir):
        raise CockpitError("Im Ziel-Branch ist ein Zusammenführen noch nicht abgeschlossen.")
    _remember(target_dir, "Übernehmen")
    result = git.run(["cherry-pick", "-x", commit.sha], target_dir, check=False)
    if result.returncode != 0:
        git.run(["cherry-pick", "--abort"], target_dir, check=False)
        text = (result.stderr + result.stdout).lower()
        # Zuerst "empty": Git schreibt dann "now empty, possibly due to conflict resolution"
        if "empty" in text:
            raise CockpitError("Der Ziel-Branch hat diese Änderungen schon. Es wurde nichts "
                               "übernommen.")
        if "conflict" in text:
            raise CockpitError("Der Commit passt nicht ohne Konflikt in den Ziel-Branch. Es wurde "
                               "nichts übernommen. Holen Sie die Änderung besser über einen Pull "
                               "Request oder übernehmen Sie sie im Terminal.",
                               (result.stderr or result.stdout).strip())
        raise git.explain(result, "Übernehmen")
    return git.run(["rev-parse", "HEAD"], target_dir, action="Übernehmen").stdout.strip()


# -- Zusammenfassen und umsortieren -------------------------------------------------------------
@dataclass
class Step:
    """Ein Commit im neuen Verlauf. squash: mit dem Schritt davor zusammenfassen."""
    commit: Commit
    squash: bool = False


@dataclass
class Plan:
    steps: list[Step] = field(default_factory=list)       # älteste zuerst

    def lines(self) -> list[str]:
        """Für die Liste: neueste oben, das Wichtigste vorne."""
        result = []
        for step in reversed(self.steps):
            text = step.commit.subject
            if step.squash:
                text += ", wird mit dem Commit darunter zusammengefasst"
            result.append(text)
        return result


def local_commits(code_dir: Path, commits: list[Commit]) -> list[Commit]:
    """Die Commits, die noch nicht hochgeladen sind, älteste zuerst. Nur ohne Zusammenführungen,
    sonst lässt sich die Reihenfolge nicht sicher ändern."""
    local = [c for c in commits if not c.uploaded]
    if any(c.is_merge for c in local):
        raise CockpitError("Unter den Commits, die noch nicht hochgeladen sind, ist ein "
                           "Zusammenführen. Dann lässt sich die Reihenfolge nicht ändern.")
    return list(reversed(local))


def _combined_message(group: list[Commit]) -> str:
    first = group[0]
    if len(group) == 1:
        return f"{first.subject}\n\n{first.body}" if first.body else first.subject
    lines = [f"- {c.subject}" for c in group]
    return first.subject + "\n\nZusammengefasst aus:\n" + "\n".join(lines)


def reorder(code_dir: Path, plan: Plan) -> None:
    """Den Verlauf so neu aufbauen, wie plan es sagt. Nur Commits, die noch nicht hochgeladen
    sind, und nur ohne Änderungen ohne Commit."""
    if not plan.steps:
        return
    if any(step.commit.uploaded for step in plan.steps):
        raise CockpitError(UPLOADED)
    if plan.steps[0].squash:
        raise CockpitError("Der älteste Commit hat keinen darunter, mit dem er sich "
                           "zusammenfassen ließe.")
    if not _clean(code_dir) or _unfinished(code_dir):
        raise CockpitError(NOT_CLEAN)
    oldest = min(plan.steps, key=lambda s: s.commit.date).commit
    shas = {s.commit.sha for s in plan.steps}
    base = next((p for c in (s.commit for s in plan.steps) for p in c.parents
                 if p not in shas), oldest.parents[0] if oldest.parents else "")
    if not base:
        raise CockpitError("Der allererste Commit lässt sich nicht verschieben.")
    head = _remember(code_dir, "Umsortieren")
    groups: list[list[Commit]] = []
    for step in plan.steps:
        if step.squash and groups:
            groups[-1].append(step.commit)
        else:
            groups.append([step.commit])
    try:
        git.run(["reset", "-q", "--hard", base], code_dir, action="Umsortieren")
        for group in groups:
            for commit in group:
                result = git.run(["cherry-pick", "-n", commit.sha], code_dir, check=False)
                if result.returncode != 0:
                    raise CockpitError("Die Commits passen in dieser Reihenfolge nicht ohne "
                                       "Konflikt zusammen. Es bleibt alles, wie es war.",
                                       (result.stderr or result.stdout).strip())
            if git.run(["diff", "--cached", "--quiet"], code_dir, check=False).returncode == 0:
                continue                    # hebt sich auf, kein leerer Commit
            # -C: Nachricht, Person und Datum des ersten Commits der Gruppe
            git.run(["commit", "-q", "--no-verify", "-C", group[0].sha], code_dir,
                    action="Umsortieren")
            if len(group) > 1:
                git.run(["commit", "-q", "--amend", "--no-verify",
                         *_message_args(_combined_message(group))], code_dir,
                        action="Zusammenfassen")
    except CockpitError:
        git.run(["cherry-pick", "--abort"], code_dir, check=False)
        git.run(["reset", "-q", "--hard", head], code_dir, check=False)
        raise
    log.info("Verlauf umsortiert: %d Commits zu %d", len(plan.steps), len(groups))


# -- Branch ab einem früheren Commit --------------------------------------------------------------
def branch_at(code_dir: Path, name: str, commit: Commit) -> None:
    """Neuen Branch ab diesem Commit, ohne zu wechseln (ohne Branch-Ordner)."""
    from cockpit.core import branches
    problem = branches.name_problem(code_dir, name)
    if problem:
        raise CockpitError(problem)
    git.run(["branch", name, commit.sha], code_dir, action="Branch anlegen")
