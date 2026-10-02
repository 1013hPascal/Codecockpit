"""Branch für die Änderungen der KI an der Exe-Einrichtung (Wunsch des Nutzers, 01.10.2026).

Die KI ändert nie direkt main. Ihre Änderungen kommen in den Branch Cockpit-exe-bauen:
- Mit Branch-Ordnern bekommt er einen eigenen Ordner und beginnt beim Stand von main
  auf diesem Rechner.
- Ohne Branch-Ordner legt das Cockpit ihn vom Stand von main an und wechselt im Ordner Code
  dorthin.
Dort entsteht ein Commit mit den Änderungen. Die Exe wird aus dem Branch gebaut und kommt als
eigene Datei neben die normale Exe. Erst danach entscheidet der Nutzer, ob der Branch in main
übernommen wird.
"""
from __future__ import annotations

from pathlib import Path

from cockpit.core import branches, git, sync, worktrees
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project

BRANCH = "Cockpit-exe-bauen"
COMMIT_MESSAGE = "Exe-Einrichtung mit KI"


def where_text(project: Project) -> str:
    """Satz für die Rückfrage vor dem Übernehmen."""
    main = git.status(project.code_dir).default_branch or "main"
    if project.has_branch_folders:
        return (f"Die Änderungen kommen in den Branch {BRANCH}, nicht in {main}. Er bekommt "
                f"einen eigenen Ordner im Ordner Code und beginnt beim Stand von {main}.")
    return (f"Die Änderungen kommen in den Branch {BRANCH}, nicht in {main}. Das Cockpit legt "
            f"ihn vom Stand von {main} an und wechselt im Ordner Code dorthin.")


def _local(code_dir: Path, name: str) -> bool:
    return git.run(["rev-parse", "-q", "--verify", f"refs/heads/{name}"], code_dir,
                   check=False).returncode == 0


def prepare(project: Project) -> Path:
    """Ordner, in dem der Branch ausgecheckt ist. Gibt es ihn schon, wird er weiterbenutzt.
    Ein neuer Branch beginnt beim Stand von main auf diesem Rechner, nicht auf der Plattform.
    So passt der Vorschlag der KI genau, und es braucht kein Netz."""
    code_dir = project.code_dir
    state = git.status(code_dir)
    main = state.default_branch or "main"
    if project.has_branch_folders:
        if _local(code_dir, BRANCH):
            return worktrees.open_branch(project, BRANCH).path
        worktrees.prune(code_dir)
        path = worktrees.free_folder(project, BRANCH)
        git.run(["worktree", "add", "-q", "--no-track", "-b", BRANCH, str(path), main],
                code_dir, action="Branch-Ordner anlegen")
        return path
    if state.branch == BRANCH:
        return code_dir
    if _local(code_dir, BRANCH):
        branches.switch(code_dir, BRANCH)
        return code_dir
    git.run(["switch", "-q", "-c", BRANCH, main], code_dir, action="Branch anlegen")
    return code_dir


def commit(code_dir: Path, files: list[str]) -> bool:
    """Nur die geänderten Dateien committen, keine anderen Änderungen. False: nichts zu tun."""
    existing = [f for f in dict.fromkeys(files) if (code_dir / f).exists()]
    if not existing:
        return False
    git.run(["add", "--", *existing], code_dir, action="Dateien vormerken")
    if git.run(["diff", "--cached", "--quiet"], code_dir, check=False).returncode == 0:
        return False
    git.run(["commit", "-q", "-m", COMMIT_MESSAGE], code_dir, action="Commit")
    return True


def merge_into_main(project: Project) -> sync.MergeOutcome:
    """Den Branch in main übernehmen, wie git merge. Ohne Branch-Ordner wechselt das Cockpit
    vorher zu main. Konflikte löst die Oberfläche wie beim Holen."""
    code_dir = project.code_dir
    main = git.status(code_dir).default_branch or "main"
    if not project.has_branch_folders and git.status(code_dir).branch != main:
        branches.switch(code_dir, main)
    return branches.merge_into_current(code_dir, project.name, BRANCH)


def delete(project: Project) -> None:
    """Branch und, mit Branch-Ordnern, seinen Ordner löschen. Der letzte Commit bleibt unter
    einem Sicherungsverweis erreichbar (branches.delete_local)."""
    if project.has_branch_folders:
        tree = next((t for t in worktrees.list_worktrees(project) if t.branch == BRANCH), None)
        if tree is not None:
            worktrees.remove(project, tree)
    if _local(project.code_dir, BRANCH):
        branches.delete_local(project.code_dir, BRANCH)
    else:
        raise CockpitError(f"Den Branch {BRANCH} gibt es nicht mehr.")
