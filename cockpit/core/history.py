"""Verlauf und Rückgängig machen (Konzept 9.4 und 9.7, Teilschritt 5d).

Verlauf: alle Commits des aktuellen Branches, neueste oben, wie git log. Eine Version ist ein
Commit. Trägt ein Commit ein Git-Tag wie v1.4.0, heißt er "Version 1.4.0".

Rückgängig machen, ohne je die Geschichte auf der Plattform umzuschreiben:
- Datei aus einer Version wiederherstellen: nur die Datei im Ordner ändert sich (git restore).
  Danach ist das eine normale Änderung.
- Version rückgängig machen: ein neuer Commit "Rückgängig: …" (git revert).
- Commit zurücknehmen: nur für den neuesten Commit, solange er nicht hochgeladen ist, wie "Undo" in
  GitHub Desktop (git reset --mixed HEAD~1). Die Dateien bleiben unverändert.
- Änderungen verwerfen: Änderungen ohne Commit zurück auf den Stand des letzten Commits, wie
  "Discard changes" in GitHub Desktop. Neue Dateien kommen in den Papierkorb.

Vor allem, was Dateien verändert, kommen die betroffenen Dateien als Sicherheitskopie in den Ordner
backups (backups.py).
"""
from __future__ import annotations

import json
import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from cockpit.core import backups, git, sync, trash
from cockpit.core.errors import CockpitError
from cockpit.core.sync import Changes
from cockpit.core.text import count, join_words

log = logging.getLogger(__name__)

_FIELD = "\x1f"
_VERSION_TAG = re.compile(r"^v?(\d+(?:\.\d+)*)$", re.IGNORECASE)
CHUNK = 100                                 # so viele Pfade pro Git-Aufruf


# -- Verlauf ------------------------------------------------------------------------------------
@dataclass
class Commit:
    sha: str
    parents: list[str]
    author: str
    date: datetime
    subject: str
    body: str = ""
    tags: list[str] = field(default_factory=list)
    uploaded: bool = True                   # False: noch nicht auf der Plattform
    newest: bool = False                    # der neueste Commit des Branches (HEAD)

    @property
    def short(self) -> str:
        return self.sha[:7]

    @property
    def is_merge(self) -> bool:
        return len(self.parents) > 1

    @property
    def version(self) -> str:
        """Versionsnummer aus einem Tag wie v1.4.0, sonst leer."""
        for tag in self.tags:
            match = _VERSION_TAG.match(tag)
            if match:
                return match[1]
        return ""

    def line(self) -> str:
        """Konzept 9.4: "23.09.2026, Version 1.4.0: Suche in mehreren PDFs ergänzt"."""
        head = f"{self.date:%d.%m.%Y}"
        if self.version:
            head += f", Version {self.version}"
        text = f"{head}: {self.subject}"
        return text if self.uploaded else f"{text}, noch nicht hochgeladen"


def log_commits(code_dir: Path) -> list[Commit]:
    """Alle Commits des aktuellen Branches, neueste zuerst. Leer, wenn es noch keinen gibt."""
    if git.run(["rev-parse", "-q", "--verify", "HEAD"], code_dir, check=False).returncode != 0:
        return []
    fields = _FIELD.join(["%H", "%P", "%an", "%aI", "%D", "%s", "%b"])
    result = git.run(["log", "-z", "--decorate-refs=refs/tags/", f"--format={fields}", "HEAD"],
                     code_dir, action="Verlauf lesen")
    upstream = git.status(code_dir).upstream
    not_uploaded: set[str] = set()
    if upstream:
        not_uploaded = set(git.run(["rev-list", f"{upstream}..HEAD"], code_dir,
                                   check=False).stdout.split())
    commits = []
    for record in result.stdout.split("\0"):
        parts = record.split(_FIELD)
        if len(parts) < 7:
            continue
        sha, parents, author, date, refs, subject, body = parts[:7]
        tags = [r.strip()[len("tag: "):] for r in refs.split(",") if r.strip().startswith("tag: ")]
        commits.append(Commit(sha.strip(), parents.split(), author,
                              datetime.fromisoformat(date), subject, body.strip(), tags,
                              uploaded=sha.strip() not in not_uploaded))
    if commits:
        commits[0].newest = True
    return commits


def commit_files(code_dir: Path, commit: Commit) -> Changes:
    """Was diese Version geändert hat. Beim Zusammenführen: was es in den Branch gebracht hat."""
    if commit.parents:
        args = ["diff", "--name-status", "-z", "-M", commit.parents[0], commit.sha]
    else:
        args = ["diff-tree", "-r", "--root", "--no-commit-id", "--name-status", "-z", commit.sha]
    entries = iter(git.run(args, code_dir, action="Verlauf lesen").stdout.split("\0"))
    found = Changes()
    for code in entries:
        if not code:
            continue
        path = next(entries, "")
        if code[0] in "RC":
            path = next(entries, "")              # der neue Name folgt auf den alten
            found.renamed.append(path)
        elif code[0] == "A":
            found.added.append(path)
        elif code[0] == "D":
            found.deleted.append(path)
        else:
            found.modified.append(path)
    return found


def details(commit: Commit, steps: list[str] | None = None) -> list[str]:
    """Angaben zu einer Version als Zeilen, das Wichtigste vorne."""
    lines = [f"Nachricht: {commit.subject}"]
    lines.extend(line.strip() for line in commit.body.splitlines() if line.strip())
    lines.append(f"Von {commit.author} am {commit.date:%d.%m.%Y um %H:%M} Uhr")
    if commit.version:
        lines.append(f"Version {commit.version}")
    if not commit.uploaded:
        lines.append("Noch nicht hochgeladen")
    if commit.is_merge:
        lines.append("Zusammenführen von zwei Ständen")
    for step in steps or []:
        lines.append(f"Schritt aus dem Cockpit: {step}")
    lines.append(f"Commit {commit.short}")
    return lines


# -- Ausgeführte Schritte der Features (ENTSCHEIDUNGEN.md: nur für Commits aus dem Cockpit) --------
def record_steps(database, project_id: int, sha: str, lines: list[str]) -> None:
    if lines:
        database.execute("INSERT OR REPLACE INTO commit_steps (project_id, sha, steps) "
                         "VALUES (?, ?, ?)", (project_id, sha, json.dumps(lines,
                                                                           ensure_ascii=False)))


def recorded_steps(database, project_id: int, sha: str) -> list[str]:
    row = database.query_one("SELECT steps FROM commit_steps WHERE project_id = ? AND sha = ?",
                             (project_id, sha))
    try:
        return list(json.loads(row["steps"])) if row is not None else []
    except ValueError:
        return []


def feature_step_lines(summary) -> list[str]:
    """Die Schritte der Features aus der Zusammenfassung eines Ablaufs, zum Beispiel
    "Exe wird erstellt: Exe getestet"."""
    return [f"{step.title}: {result.text}" if result.text else step.title
            for step, result in summary.results if step.feature_id]


# -- Gemeinsame Prüfungen --------------------------------------------------------------------
def _no_unfinished_merge(code_dir: Path) -> None:
    if sync.conflict_kind(code_dir) is not sync.ConflictKind.NONE:
        raise CockpitError("Das Zusammenführen ist noch nicht abgeschlossen. Bitte lösen Sie "
                           "zuerst die Konflikte.")


def _copy_into(folder: Path, code_dir: Path, relatives: list[str]) -> int:
    copied = 0
    for relative in relatives:
        source = code_dir / relative
        if source.is_file():
            target = folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied += 1
    return copied


def backup_files(code_dir: Path, project_name: str, reason: str, relatives: list[str],
                 notes: list[str] | None = None) -> Path | None:
    """Sicherheitskopie der Dateien, die es gibt. None, wenn keine davon existiert."""
    existing = [r for r in relatives if (code_dir / r).is_file()]
    if not existing:
        return None
    folder = backups.new_backup_dir(project_name, reason, code_dir, notes)
    _copy_into(folder, code_dir, existing)
    log.info("Sicherheitskopie %s: %s", reason, folder)
    return folder


def _version_note(commit: Commit) -> str:
    return f"Version: {commit.short} vom {commit.date:%d.%m.%Y}, {commit.subject}"


# -- Datei aus einer Version wiederherstellen ---------------------------------------------------
def restore_source(commit: Commit, path: str, files: Changes) -> str:
    """Aus welchem Commit die Datei kommt. Wurde sie in dieser Version gelöscht, kommt sie mit dem
    Stand direkt davor zurück."""
    if path in files.deleted:
        if not commit.parents:
            raise CockpitError(f"{path} gab es vor dieser Version nicht.")
        return commit.parents[0]
    return commit.sha


def restore_file(code_dir: Path, project_name: str, commit: Commit, path: str,
                 files: Changes) -> Path | None:
    """Die Datei auf den Stand dieser Version setzen. Nur die Datei im Ordner ändert sich, nicht
    der Verlauf. Gibt den Ordner der Sicherheitskopie zurück (None: es gab die Datei nicht)."""
    _no_unfinished_merge(code_dir)
    source = restore_source(commit, path, files)
    folder = backup_files(code_dir, project_name, "vor dem Wiederherstellen", [path],
                          [_version_note(commit)])
    git.run(["restore", f"--source={source}", "--worktree", "--", path], code_dir,
            action="Wiederherstellen")
    log.info("%s aus %s wiederhergestellt", path, source[:7])
    return folder


# -- Version rückgängig machen -----------------------------------------------------------------
def revert_message(commit: Commit) -> str:
    return f"Rückgängig: {commit.subject}"


def revert(code_dir: Path, project_name: str, commit: Commit, git_name: str = "",
           git_email: str = "") -> Path | None:
    """Neuer Commit, der die Änderungen dieser Version aufhebt (git revert). Der Verlauf bleibt
    vollständig. Gibt den Ordner der Sicherheitskopie zurück."""
    _no_unfinished_merge(code_dir)
    if commit.is_merge:
        raise CockpitError("Diese Version ist ein Zusammenführen von zwei Ständen. Sie lässt sich "
                           "hier nicht als Ganzes rückgängig machen. Sie können aber einzelne "
                           "Dateien aus der Version davor wiederherstellen.")
    if not commit.parents:
        raise CockpitError("Das ist die erste Version. Sie lässt sich nicht rückgängig machen.")
    files = commit_files(code_dir, commit)
    touched = sorted(set(files.files) | set(_renamed_from(code_dir, commit)))
    busy = sorted(set(touched) & set(sync.changes(code_dir).files))
    if busy:
        raise CockpitError(f"In {join_words(busy[:5])} gibt es Änderungen ohne Commit. Bitte laden "
                           "Sie sie zuerst hoch oder verwerfen Sie sie.")
    if git.run(["diff", "--cached", "--quiet"], code_dir, check=False).returncode != 0:
        raise CockpitError("Es gibt vorgemerkte Änderungen. Bitte laden Sie sie zuerst hoch.")
    sync.prepare_commit(code_dir, project_name, git_name, git_email)
    folder = backup_files(code_dir, project_name, "vor dem Rückgängigmachen", touched,
                          [_version_note(commit)])
    result = git.run(["revert", "--no-commit", commit.sha], code_dir, check=False)
    if result.returncode != 0:
        git.run(["revert", "--abort"], code_dir, check=False)
        git.run(["reset", "-q", "--merge"], code_dir, check=False)
        raise CockpitError("Diese Version lässt sich nicht von selbst rückgängig machen, weil "
                           "spätere Versionen dieselben Stellen geändert haben. Es wurde nichts "
                           "verändert. Sie können stattdessen einzelne Dateien aus der Version "
                           "davor wiederherstellen.",
                           f"git revert: {(result.stderr or result.stdout).strip()}")
    if git.run(["diff", "--cached", "--quiet"], code_dir, check=False).returncode == 0:
        git.run(["revert", "--abort"], code_dir, check=False)
        raise CockpitError("Die Änderungen dieser Version sind schon rückgängig gemacht. Es wurde "
                           "nichts verändert.")
    git.run(["commit", "-q", "-m", revert_message(commit),
             "-m", f"Macht Commit {commit.sha} rückgängig."], code_dir, action="Rückgängig machen")
    log.info("Version %s rückgängig gemacht", commit.short)
    return folder


def _renamed_from(code_dir: Path, commit: Commit) -> list[str]:
    """Alte Namen umbenannter Dateien, auch sie ändert git revert."""
    result = git.run(["diff", "--name-status", "-z", "-M", "--diff-filter=R",
                      commit.parents[0], commit.sha], code_dir, check=False)
    parts = [p for p in result.stdout.split("\0") if p]
    return [parts[i + 1] for i in range(0, len(parts) - 2, 3)]


# -- Commit zurücknehmen ----------------------------------------------------------------------
def can_undo(commit: Commit) -> bool:
    """Nur der neueste Commit, solange er nicht hochgeladen ist, wie in GitHub Desktop."""
    return commit.newest and not commit.uploaded and len(commit.parents) == 1


def undo_commit(code_dir: Path, commit: Commit) -> None:
    """Den neuesten Commit zurücknehmen. Seine Änderungen bleiben in den Dateien und erscheinen
    wieder als Änderungen ohne Commit. Keine Datei ändert sich."""
    _no_unfinished_merge(code_dir)
    head = git.run(["rev-parse", "HEAD"], code_dir, action="Commit zurücknehmen").stdout.strip()
    if head != commit.sha or not can_undo(commit):
        raise CockpitError("Zurücknehmen geht nur beim neuesten Commit, solange er noch nicht "
                           "hochgeladen ist.")
    git.run(["reset", "-q", "--mixed", commit.parents[0]], code_dir, action="Commit zurücknehmen")
    log.info("Commit %s zurückgenommen", commit.short)


# -- Änderungen verwerfen ---------------------------------------------------------------------
@dataclass(frozen=True)
class LocalChange:
    path: str
    what: str                       # "geändert", "neu", "gelöscht", "umbenannt"
    old_path: str = ""              # bei "umbenannt": der alte Name
    staged_new: bool = False        # neue Datei, schon vorgemerkt (git add)

    def line(self) -> str:
        if self.old_path:
            return f"{self.path}, umbenannt, vorher {self.old_path}"
        return f"{self.path}, {self.what}"


def local_changes(code_dir: Path) -> list[LocalChange]:
    """Änderungen ohne Commit, wie git status."""
    result = git.run(["status", "--porcelain=v1", "-z", "--untracked-files=all"], code_dir,
                     action="Stand lesen")
    found: list[LocalChange] = []
    entries = iter(result.stdout.split("\0"))
    for entry in entries:
        if len(entry) < 4:
            continue
        code, path = entry[:2], entry[3:]
        if "U" in code or code in ("AA", "DD"):
            raise CockpitError("Das Zusammenführen ist noch nicht abgeschlossen. Bitte lösen Sie "
                               "zuerst die Konflikte.")
        if code[0] in "RC":
            old = next(entries, "")
            found.append(LocalChange(path, "umbenannt", old if code[0] == "R" else "", True))
        elif code == "??":
            found.append(LocalChange(path, "neu"))
        elif code[0] == "A":
            found.append(LocalChange(path, "neu", staged_new=True))
        elif "D" in code:
            found.append(LocalChange(path, "gelöscht"))
        else:
            found.append(LocalChange(path, "geändert"))
    return sorted(found, key=lambda c: c.path.lower())


def discard_description(items: list[LocalChange]) -> str:
    """Was beim Verwerfen passiert, für die Rückfrage."""
    back = [c.path for c in items if c.what in ("geändert", "gelöscht")]
    back += [c.old_path for c in items if c.old_path]
    new = [c.path for c in items if c.what == "neu" or c.what == "umbenannt"]
    parts = []
    if back:
        verb = "kommt" if len(back) == 1 else "kommen"
        parts.append(f"{count(len(back), 'Datei', 'Dateien')} {verb} auf den Stand des letzten "
                     f"Commits zurück: {join_words(back[:5])}{_more(back)}.")
    if new:
        verb = "kommt" if len(new) == 1 else "kommen"
        parts.append(f"{count(len(new), 'neue Datei', 'neue Dateien')} {verb} in den Papierkorb: "
                     f"{join_words(new[:5])}{_more(new)}.")
    return " ".join(parts)


def _more(names: list[str]) -> str:
    return f" und {len(names) - 5} weitere" if len(names) > 5 else ""


def discard(code_dir: Path, project_name: str, items: list[LocalChange]) -> Path | None:
    """Die gewählten Änderungen verwerfen. Vorher kommen alle betroffenen Dateien, die es gibt,
    in eine Sicherheitskopie. Gibt deren Ordner zurück."""
    _no_unfinished_merge(code_dir)
    if not items:
        return None
    folder = backup_files(code_dir, project_name, "vor dem Verwerfen", [c.path for c in items])
    unstage = [c.path for c in items if c.staged_new]
    restore = [c.path for c in items if c.what in ("geändert", "gelöscht")]
    restore += [c.old_path for c in items if c.old_path]
    to_trash = [code_dir / c.path for c in items if c.what in ("neu", "umbenannt")]
    for start in range(0, len(unstage), CHUNK):
        git.run(["rm", "-q", "--cached", "--", *unstage[start:start + CHUNK]], code_dir,
                action="Verwerfen")
    for start in range(0, len(restore), CHUNK):
        git.run(["restore", "--source=HEAD", "--staged", "--worktree", "--",
                 *restore[start:start + CHUNK]], code_dir, action="Verwerfen")
    trash.move_to_recycle_bin([p for p in to_trash if p.exists()])
    log.info("Verworfen in %s: %s", project_name, ", ".join(c.path for c in items))
    return folder
