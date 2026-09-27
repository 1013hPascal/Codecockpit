"""Änderungen hochladen und holen (Konzept 9.2 und 9.3, Teilschritt 5c).

Hochladen: Commit mit der Nachricht des Nutzers und git push, wie im Terminal. Geprüft werden nur
die geänderten Dateien und die Commits, die noch nicht hochgeladen sind. Gibt es auf der Plattform
neue Commits, lädt das Cockpit nicht hoch, sondern bietet an, sie zuerst zu holen. Nie ein force
push.

Holen wie GitHub Desktop (ENTSCHEIDUNGEN.md): git fetch, dann git merge. Vorher kommen die
betroffenen Dateien als Sicherheitskopie in den Ordner backups. Stören Änderungen, die noch nicht
hochgeladen sind, legt das Cockpit sie nach Rückfrage beiseite (git stash) und danach wieder
zurück.

Konflikte gibt es in zwei Arten:
- MERGE: Beim Zusammenführen von Commits (git merge). Meine Fassung ist "ours".
- STASH: Beim Zurücklegen der beiseitegelegten Änderungen (git stash pop). Meine Fassung ist
  "theirs", weil der Stash auf den neuen Stand gelegt wird.
Pro Datei wählt man die eigene Fassung, die der Plattform oder bearbeitet sie im Editor.
"""
from __future__ import annotations

import logging
import shutil
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from cockpit.core import backups, git, identity, safety_check
from cockpit.core.errors import CockpitError
from cockpit.core.flows.engine import Flow, FlowContext
from cockpit.core.flows.hooks import Hook
from cockpit.core.flows.step import Step, StepResult
from cockpit.core.projects import Project
from cockpit.core.text import count, join_words

log = logging.getLogger(__name__)

STASH_MESSAGE = "CodeCockpit: vor dem Holen"
BEFORE_PULL_REF = "refs/codecockpit/vor-dem-holen"     # Commit vor dem Holen, für Abbrechen
MARKERS = ("<<<<<<< ", ">>>>>>> ")
NAMES_SHOWN = 5                           # so viele Dateinamen nennt die Beschreibung


def environment(services, project: Project) -> dict[str, str]:
    """Zugang für Git als Umgebungsvariablen. Leer, wenn das Projekt kein Konto hat."""
    platform = services.platform_for(project) if services is not None else None
    return dict(platform.git_credentials().environment) if platform is not None else {}


def is_public(services, project: Project) -> bool:
    """Ist das Repository öffentlich? Unbekannt gilt als privat (ENTSCHEIDUNGEN.md)."""
    if services is None or project.remote is None:
        return False
    stored = services.remote_repos.find(project.remote)
    return stored is not None and not stored.private


# -- Änderungen ---------------------------------------------------------------------------------
@dataclass
class Changes:
    modified: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    renamed: list[str] = field(default_factory=list)

    @property
    def files(self) -> list[str]:
        return self.modified + self.added + self.deleted + self.renamed

    @property
    def existing(self) -> list[str]:
        """Dateien, die es noch gibt. Nur diese prüft die Sicherheitsprüfung."""
        return self.modified + self.added + self.renamed

    def __bool__(self) -> bool:
        return bool(self.files)

    @staticmethod
    def _names(files: list[str]) -> str:
        shown = join_words(files[:NAMES_SHOWN])
        rest = len(files) - NAMES_SHOWN
        return f"{shown} und {rest} weitere" if rest > 0 else shown

    def parts(self) -> list[tuple[str, list[str]]]:
        return [(text, files) for text, files in (
            (count(len(self.modified), "Datei geändert", "Dateien geändert"), self.modified),
            (count(len(self.added), "neue Datei", "neue Dateien"), self.added),
            (count(len(self.deleted), "Datei gelöscht", "Dateien gelöscht"), self.deleted),
            (count(len(self.renamed), "Datei umbenannt", "Dateien umbenannt"), self.renamed),
        ) if files]

    def summary(self) -> str:
        """Kurz für den Fenstertitel: "3 Dateien geändert, 1 neue Datei"."""
        return ", ".join(text for text, _ in self.parts()) or "keine Änderungen"

    def describe(self) -> str:
        """Konzept 9.2: "3 Dateien geändert: main.py, suche.py und README.md. 1 neue Datei:
        export.py." """
        return " ".join(f"{text}: {self._names(files)}." for text, files in self.parts())

    def lines(self) -> list[str]:
        """Eine Zeile pro Datei, der Name vorne: "main.py, geändert"."""
        result = []
        for files, what in ((self.modified, "geändert"), (self.added, "neu"),
                            (self.deleted, "gelöscht"), (self.renamed, "umbenannt")):
            result.extend(f"{f}, {what}" for f in files)
        return result


def changes(code_dir: Path) -> Changes:
    """Änderungen, die noch nicht in einem Commit sind, wie git status."""
    result = git.run(["status", "--porcelain=v1", "-z", "--untracked-files=all"], code_dir,
                     action="Stand lesen")
    found = Changes()
    entries = iter(result.stdout.split("\0"))
    for entry in entries:
        if len(entry) < 4:
            continue
        code, path = entry[:2], entry[3:]
        if code[0] in "RC":
            next(entries, None)                    # alter Name
            found.renamed.append(path)
        elif code == "??" or "A" in code:
            found.added.append(path)
        elif "D" in code:
            found.deleted.append(path)
        else:
            found.modified.append(path)
    return found


# -- Sicherheitsprüfung beim Hochladen ------------------------------------------------------------
def scan(code_dir: Path, public: bool, git_email: str,
         accepted: set[tuple[str, str, str]] | None = None) -> safety_check.Report:
    """Prüft die geänderten Dateien und die Commits, die noch nicht hochgeladen sind."""
    upstream = git.status(code_dir).upstream
    history = f"{upstream}..HEAD" if upstream else "HEAD"
    emails = safety_check.commit_emails(code_dir, history)
    emails.append(git.identity(code_dir)[1] or git_email)
    report = safety_check.scan(code_dir, files=changes(code_dir).existing, public=public,
                               emails=emails, history_range=history)
    accepted = accepted or set()
    report.findings = [f for f in report.findings
                       if (f.kind.value, f.path, f.rule) not in accepted]
    return report


# -- Schritte des Ablaufs "Änderungen hochladen" ---------------------------------------------------
def _step_check(context: FlowContext) -> StepResult:
    data = context.data
    report = scan(context.project.code_dir, data.get("public", False), data.get("git_email", ""),
                  data.get("accepted"))
    if report.blocking:
        return StepResult(False, "Die Sicherheitsprüfung hat das Hochladen gestoppt.",
                          report.blocking[0].text)
    if report.warnings:
        return StepResult(False, "Die Sicherheitsprüfung hat neue Warnungen gefunden. Bitte "
                          "starten Sie das Hochladen noch einmal.", report.warnings[0].text)
    return StepResult(True)


def _step_commit(context: FlowContext) -> StepResult:
    message: str = context.data.get("message", "")
    code_dir = context.project.code_dir
    if not message:
        return StepResult(True)                    # nur Commits hochladen, die schon da sind
    git.run(["add", "-A"], code_dir, action="Dateien vormerken")
    if git.run(["diff", "--cached", "--quiet"], code_dir, check=False).returncode == 0:
        return StepResult(True)
    args = ["commit", "-q"]
    for paragraph in message.split("\n\n"):
        if paragraph.strip():
            args += ["-m", paragraph.strip()]
    git.run(args, code_dir, action="Commit")
    context.data["commit"] = git.run(["rev-parse", "HEAD"], code_dir,
                                     action="Commit").stdout.strip()
    first = message.strip().splitlines()[0]
    return StepResult(True, f"Commit „{first}“.")


def _step_push(context: FlowContext) -> StepResult:
    code_dir = context.project.code_dir
    env = context.data.get("env") or {}
    git.run(["fetch", "origin"], code_dir, env=env, timeout=None, cancel=context.cancel_event,
            action="Holen")
    state = git.status(code_dir)
    if not state.branch:
        raise CockpitError("Es ist gerade kein Branch ausgewählt. Hochladen geht nur auf einem "
                           "Branch.")
    if state.behind:
        context.data["behind"] = state.behind
        return StepResult(False, f"Auf der Plattform gibt es "
                          f"{count(state.behind, 'neuen Commit', 'neue Commits')}, die hier "
                          "noch fehlen. Bitte holen Sie sie zuerst.")
    if state.upstream and not state.ahead:
        return StepResult(True, "Es war schon alles hochgeladen.")
    args = ["push", "origin", state.branch] if state.upstream else [
        "push", "-u", "origin", state.branch]
    try:
        git.run(args, code_dir, env=env, timeout=None, cancel=context.cancel_event,
                action="Hochladen")
    except git.GitError as exc:
        if "geschützt" in exc.message:
            context.data["protected"] = state.branch       # Angebot: neuer Branch (6c)
        raise
    context.data["branch"] = state.branch
    return StepResult(True, f"Branch {state.branch} ist hochgeladen.")


PUSH_CHANGES = Flow("push_changes", "Änderungen hochladen", (
    Step("safety_check", "Sicherheitsprüfung", Hook.BEFORE_COMMIT_MESSAGE, _step_check, order=10),
    Step("commit", "Commit wird erstellt", Hook.BEFORE_PUSH, _step_commit, order=900),
    Step("push", "Wird hochgeladen", Hook.PUSH, _step_push, order=20),
))


def prepare_commit(code_dir: Path, project_name: str, git_name: str, git_email: str) -> None:
    """Vor jedem Commit: fehlt die Identität im Repository, die aus den Grundeinstellungen
    eintragen (ENTSCHEIDUNGEN.md). Eine andere Identität bleibt ohne Rückfrage."""
    identity.ensure(code_dir, project_name, git_name, git_email, None)


# -- Holen ------------------------------------------------------------------------------------
class ConflictKind(Enum):
    NONE = ""
    MERGE = "merge"                # beim Zusammenführen der Commits
    STASH = "stash"                # beim Zurücklegen der beiseitegelegten Änderungen


@dataclass
class Incoming:
    """Was das Holen bringen würde, nach git fetch."""
    branch: str
    upstream: str
    behind: int = 0                                     # neue Commits auf der Plattform
    ahead: int = 0                                      # eigene Commits, noch nicht hochgeladen
    files: list[str] = field(default_factory=list)      # Dateien, die die neuen Commits ändern
    local: list[str] = field(default_factory=list)      # eigene Änderungen ohne Commit
    overlap: list[str] = field(default_factory=list)    # beides: dann Stash nötig


def fetch(code_dir: Path, env: dict[str, str] | None = None,
          cancel: threading.Event | None = None) -> Incoming:
    """git fetch und prüfen, was das Zusammenführen ändern würde."""
    state = git.status(code_dir)
    if not state.branch:
        raise CockpitError("Es ist gerade kein Branch ausgewählt. Holen geht nur auf einem "
                           "Branch.")
    if not state.upstream:
        raise CockpitError(f"Der Branch {state.branch} ist noch nicht auf der Plattform. Laden "
                           "Sie ihn zuerst hoch.")
    git.run(["fetch", "origin"], code_dir, env=env, timeout=None, cancel=cancel,
            action="Holen")
    state = git.status(code_dir)
    incoming = Incoming(state.branch, state.upstream, state.behind, state.ahead)
    if not state.behind:
        return incoming
    result = git.run(["diff", "--name-only", "-z", f"HEAD...{state.upstream}"], code_dir,
                     action="Holen")
    incoming.files = sorted(f for f in result.stdout.split("\0") if f)
    incoming.local = sorted(changes(code_dir).files)
    incoming.overlap = sorted(set(incoming.files) & set(incoming.local))
    return incoming


def backup(code_dir: Path, project_name: str, incoming: Incoming,
           reason: str = "vor dem Holen") -> Path:
    """Sicherheitskopie vor dem Holen oder Übernehmen: alle Dateien, die das Zusammenführen ändern
    könnte, und alle eigenen Änderungen. Dazu der Commit davor in Sicherheitskopie.txt."""
    head = git.run(["rev-parse", "HEAD"], code_dir, action="Sicherheitskopie").stdout.strip()
    target = backups.new_backup_dir(project_name, reason, code_dir, [
        f"Commit {reason}: {head}", f"Branch: {incoming.branch}"])
    for relative in sorted(set(incoming.files) | set(incoming.local)):
        source = code_dir / relative
        if source.is_file():
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    log.info("Sicherheitskopie vor dem Holen: %s", target)
    return target


@dataclass
class MergeOutcome:
    kind: ConflictKind = ConflictKind.NONE             # NONE: fertig ohne Konflikte
    conflicts: list[str] = field(default_factory=list)
    stash_kept: bool = False                            # Änderungen liegen noch im Stash


def merge(code_dir: Path, stash: bool, source: str = "@{u}") -> MergeOutcome:
    """git merge mit dem Stand der Plattform (source "@{u}") oder einem anderen Branch.
    stash: eigene Änderungen vorher beiseitelegen."""
    git.run(["update-ref", BEFORE_PULL_REF, "HEAD"], code_dir, action="Holen")
    if stash:
        git.run(["stash", "push", "--include-untracked", "-m", STASH_MESSAGE], code_dir,
                action="Beiseitelegen")
    result = git.run(["merge", "--no-edit", source], code_dir, check=False)
    if result.returncode != 0:
        found = conflicted(code_dir)
        if found:
            return MergeOutcome(ConflictKind.MERGE, found, stash)
        if stash:
            _restore_stash(code_dir)
        _forget_before_pull(code_dir)
        raise git.explain(result, "Zusammenführen")
    return _done(code_dir, _pop_own_stash(code_dir))


def _done(code_dir: Path, outcome: MergeOutcome) -> MergeOutcome:
    if outcome.kind is ConflictKind.NONE:
        _forget_before_pull(code_dir)
    return outcome


def _forget_before_pull(code_dir: Path) -> None:
    git.run(["update-ref", "-d", BEFORE_PULL_REF], code_dir, check=False)


def conflicted(code_dir: Path) -> list[str]:
    """Dateien mit einem offenen Konflikt."""
    result = git.run(["diff", "--name-only", "-z", "--diff-filter=U"], code_dir, check=False)
    return sorted({f for f in result.stdout.split("\0") if f})


def merge_source_label(code_dir: Path, platform_name: str = "GitHub") -> str:
    """Wessen Fassung beim Zusammenführen die zweite ist: die Plattform oder ein Branch. Git
    schreibt den Branch in .git/MERGE_MSG, zum Beispiel "Merge branch 'suche-pdfs'"."""
    try:
        first = (code_dir / ".git" / "MERGE_MSG").read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError):
        return platform_name
    prefix = "Merge branch '"
    if first.startswith(prefix) and "' of " not in first:
        return f"Branch {first[len(prefix):].split(chr(39))[0]}"
    return platform_name


def merging(code_dir: Path) -> bool:
    return (code_dir / ".git" / "MERGE_HEAD").exists()


def conflict_kind(code_dir: Path) -> ConflictKind:
    """Läuft gerade ein Zusammenführen, das noch nicht abgeschlossen ist?"""
    if not git.is_repo(code_dir):
        return ConflictKind.NONE
    if merging(code_dir):
        return ConflictKind.MERGE
    return ConflictKind.STASH if conflicted(code_dir) else ConflictKind.NONE


def _own_stash_on_top(code_dir: Path) -> bool:
    top = git.run(["stash", "list", "-1", "--format=%gs"], code_dir, check=False).stdout.strip()
    return top.endswith(STASH_MESSAGE)


def _pop_own_stash(code_dir: Path) -> MergeOutcome:
    if not _own_stash_on_top(code_dir):
        return MergeOutcome()
    result = git.run(["stash", "pop"], code_dir, check=False)
    if result.returncode == 0:
        return MergeOutcome()
    found = conflicted(code_dir)
    if found:
        return MergeOutcome(ConflictKind.STASH, found, True)
    raise CockpitError("Ihre beiseitegelegten Änderungen ließen sich nicht zurücklegen. Sie "
                       "liegen weiter im Stash und in der Sicherheitskopie.",
                       f"git stash pop: {(result.stderr or result.stdout).strip()}")


def _restore_stash(code_dir: Path) -> None:
    if _own_stash_on_top(code_dir):
        git.run(["stash", "pop"], code_dir, check=False)


def _stages(code_dir: Path, path: str) -> set[str]:
    result = git.run(["ls-files", "-u", "-z", "--", path], code_dir, check=False)
    return {entry.split(" ")[2].split("\t")[0] for entry in result.stdout.split("\0") if entry}


def resolve(code_dir: Path, path: str, kind: ConflictKind, keep_mine: bool) -> None:
    """Konflikt einer Datei lösen: eigene Fassung oder die der Plattform."""
    mine_is_ours = kind is ConflictKind.MERGE
    side = "--ours" if keep_mine == mine_is_ours else "--theirs"
    stage = "2" if side == "--ours" else "3"
    if stage in _stages(code_dir, path):
        git.run(["checkout", side, "--", path], code_dir, action="Konflikt lösen")
        git.run(["add", "--", path], code_dir, action="Konflikt lösen")
    else:                                               # auf dieser Seite gelöscht
        git.run(["rm", "-q", "--", path], code_dir, action="Konflikt lösen")


def label_conflicts(code_dir: Path, path: str, kind: ConflictKind,
                    platform_name: str = "GitHub") -> int:
    """Konfliktmarken in der Datei verständlich beschriften (Wunsch aus dem Test von 5c).

    Git schreibt "<<<<<<< HEAD", "=======" und ">>>>>>> origin/main". Daraus wird zum Beispiel
    "<<<<<<< Meine Fassung, main.py Zeile 7", "======= Fassung von GitHub, main.py Zeile 7" und
    ">>>>>>> Ende des Konflikts". Die Zeilennummer gilt jeweils in der Datei dieser Fassung.
    Nur die Zeilen mit den Marken ändern sich, der Code dazwischen bleibt, auch wenn er schon
    bearbeitet ist. Gibt die Zahl der Konflikte zurück."""
    file = code_dir / path
    try:
        data = file.read_bytes()
    except OSError:
        return 0
    mine = "Meine Fassung"
    theirs = f"Fassung von {platform_name}"
    # Oben steht bei Git immer "ours": beim Zusammenführen meine Fassung, beim Zurücklegen des
    # Stashs die Fassung der Plattform.
    first, second = (mine, theirs) if kind is ConflictKind.MERGE else (theirs, mine)
    name = Path(path).name
    lines = data.splitlines(keepends=True)
    result: list[bytes] = []
    line_first = line_second = 0                 # Zeilen bisher in beiden Fassungen
    section = ""                                  # "", "first", "base", "second"
    blocks = 0
    for line in lines:
        ending = line[len(line.rstrip(b"\r\n")):]
        if line.startswith(b"<<<<<<<"):
            section = "first"
            blocks += 1
            label = f"<<<<<<< {first}, {name} Zeile {line_first + 1}"
            result.append(label.encode("utf-8") + ending)
            start_second = line_second + 1
            continue
        if section == "first" and line.startswith(b"|||||||"):
            section = "base"
            result.append("||||||| Gemeinsamer Ausgangsstand".encode("utf-8") + ending)
            continue
        if section in ("first", "base") and line.startswith(b"======="):
            section = "second"
            label = f"======= {second}, {name} Zeile {start_second}"
            result.append(label.encode("utf-8") + ending)
            continue
        if section == "second" and line.startswith(b">>>>>>>"):
            section = ""
            result.append(">>>>>>> Ende des Konflikts".encode("utf-8") + ending)
            continue
        if section in ("", "first"):
            line_first += 1
        if section in ("", "second"):
            line_second += 1
        result.append(line)
    if blocks:
        new = b"".join(result)
        if new != data:
            file.write_bytes(new)
    return blocks


def has_markers(code_dir: Path, path: str) -> bool:
    """Stehen noch Konfliktmarken in der Datei?"""
    try:
        text = (code_dir / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(line.startswith(MARKERS) for line in text.splitlines())


def mark_resolved(code_dir: Path, path: str) -> None:
    """Im Editor gelöst: die Datei als gelöst vormerken."""
    if (code_dir / path).exists():
        git.run(["add", "--", path], code_dir, action="Konflikt lösen")
    else:
        git.run(["rm", "-q", "--", path], code_dir, action="Konflikt lösen")


def finish(code_dir: Path, kind: ConflictKind) -> MergeOutcome:
    """Zusammenführen abschließen, wenn alle Konflikte gelöst sind. Danach werden beiseitegelegte
    Änderungen zurückgelegt. Dabei kann es erneut Konflikte geben (Art STASH)."""
    open_files = conflicted(code_dir)
    if open_files:
        raise CockpitError(f"Es gibt noch {count(len(open_files), 'Konflikt', 'Konflikte')}.")
    if kind is ConflictKind.MERGE:
        if merging(code_dir):
            git.run(["commit", "--no-edit", "-q"], code_dir, action="Zusammenführen")
        return _done(code_dir, _pop_own_stash(code_dir))
    git.run(["reset", "-q"], code_dir, action="Zusammenführen")     # wie nach git stash pop
    if _own_stash_on_top(code_dir):
        git.run(["stash", "drop", "-q"], code_dir, action="Zusammenführen")
    return _done(code_dir, MergeOutcome())


def abort(code_dir: Path, kind: ConflictKind) -> bool:
    """Zusammenführen abbrechen: zurück zum Stand vor dem Holen, mit den eigenen Änderungen.
    Gibt True zurück, wenn die eigenen Änderungen danach noch im Stash liegen."""
    if kind is ConflictKind.MERGE:
        git.run(["merge", "--abort"], code_dir, action="Zusammenführen abbrechen")
        _restore_stash(code_dir)
        _forget_before_pull(code_dir)
        return _own_stash_on_top(code_dir)
    # Art STASH: Alle eigenen Änderungen liegen noch im Stash, deshalb geht hier nichts verloren.
    # Die Dateien, die der Stash als neue Dateien mitbringt, kommen weg, sonst lässt er sich
    # nicht noch einmal zurücklegen.
    if _own_stash_on_top(code_dir):
        untracked = git.run(["ls-tree", "-r", "-z", "--name-only", "stash@{0}^3"], code_dir,
                            check=False).stdout
        for relative in (f for f in untracked.split("\0") if f):
            (code_dir / relative).unlink(missing_ok=True)
    before = git.run(["rev-parse", "-q", "--verify", BEFORE_PULL_REF], code_dir,
                     check=False).stdout.strip()
    git.run(["reset", "-q", "--hard", *([before] if before else [])], code_dir,
            action="Zusammenführen abbrechen")
    _restore_stash(code_dir)
    _forget_before_pull(code_dir)
    return _own_stash_on_top(code_dir)
