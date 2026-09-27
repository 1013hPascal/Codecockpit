"""Branches und beiseitegelegte Änderungen (Konzept 10.14, Teilschritt 5f).

Grundfunktionen für Branches gehören zum Kern (ENTSCHEIDUNGEN.md): anlegen, wechseln, umbenennen,
löschen, in den Haupt-Branch übernehmen und Änderungen beiseitelegen (git stash). Alles wie im
Terminal und in GitHub Desktop, nie mit force push.

Die Übersicht zeigt lokale Branches und die der Plattform (origin) in einer Liste. Jede Zeile
nennt Name, Ort, wer zuletzt daran gearbeitet hat, und den Stand. Ein Branch, den es
nur auf der Plattform gibt, wird beim Wechseln lokal angelegt, wie git switch.

Beiseitegelegt wird mit einer Nachricht, die den Branch nennt: "CodeCockpit: beiseitegelegt auf
main". So kann das Cockpit beim Zurückwechseln anbieten, die Änderungen zurückzuholen.
"""
from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from cockpit.core import backups, git, history, sync
from cockpit.core.errors import CockpitError
from cockpit.core.text import count, join_words

log = logging.getLogger(__name__)

STASH_PREFIX = "CodeCockpit: beiseitegelegt auf "
DELETED_REF = "refs/codecockpit/geloescht/"     # gelöschte Branches bleiben hier erreichbar
_FIELD = "\x1f"


# -- Übersicht ------------------------------------------------------------------------------
@dataclass
class Branch:
    name: str
    local: bool = False
    remote: bool = False                    # origin/<name> gibt es
    current: bool = False
    default: bool = False                   # Haupt-Branch, zum Beispiel main
    upstream: str = ""                      # zum Beispiel "origin/suche-pdfs"
    ahead: int = 0                          # Commits noch nicht hochgeladen
    behind: int = 0                         # Commits auf der Plattform, noch nicht geholt
    ahead_main: int = 0                     # Commits, die im Haupt-Branch fehlen
    behind_main: int = 0                    # Commits des Haupt-Branches, die hier fehlen
    date: str = ""                          # letzter Commit, ISO
    author: str = ""                        # wer zuletzt daran gearbeitet hat
    open_pulls: int = 0                     # offene Pull Requests aus diesem Branch (Phase 6)

    def place(self, platform_name: str = "GitHub") -> str:
        """Wo der Branch liegt: "nur hier", "nur auf GitHub" oder "hier und auf GitHub"."""
        if self.local and self.remote:
            return f"hier und auf {platform_name}"
        return "nur hier" if self.local else f"nur auf {platform_name}"

    def line(self, main: str = "main", platform_name: str = "GitHub") -> str:
        """Zeile der Übersicht (Wunsch aus dem Test von 5f): Name, Ort, wer zuletzt daran
        gearbeitet hat, dann der Stand. Zum Beispiel "design, hier und auf GitHub, zuletzt von
        Anna am 24.09.2026, 2 Commits vor main"."""
        parts = [self.name]
        if self.current:
            parts.append("aktueller Branch")
        if self.default:
            parts.append("Haupt-Branch")
        parts.append(self.place(platform_name))
        when = _day(self.date)
        if self.author:
            parts.append(f"zuletzt von {self.author}" + (f" am {when}" if when else ""))
        if not self.default:
            if self.ahead_main:
                parts.append(f"{count(self.ahead_main, 'Commit', 'Commits')} vor {main}")
            if self.behind_main:
                parts.append(f"{count(self.behind_main, 'Commit', 'Commits')} hinter {main}")
            if not self.ahead_main and not self.behind_main:
                parts.append(f"gleich wie {main}")
        if self.open_pulls:
            parts.append(count(self.open_pulls, "offener Pull Request", "offene Pull Requests"))
        if self.local and self.remote:
            if self.ahead:
                parts.append(f"{count(self.ahead, 'Commit', 'Commits')} noch nicht hochgeladen")
            if self.behind:
                parts.append(f"{count(self.behind, 'Commit', 'Commits')} auf {platform_name} "
                             "noch nicht geholt")
        return ", ".join(parts)


def _day(iso: str) -> str:
    try:
        return f"{datetime.fromisoformat(iso):%d.%m.%Y}" if iso else ""
    except ValueError:
        return ""


def default_branch(code_dir: Path) -> str:
    return git.status(code_dir).default_branch


def _ref_exists(code_dir: Path, ref: str) -> bool:
    return git.run(["rev-parse", "-q", "--verify", ref], code_dir, check=False).returncode == 0


def _ahead_behind(code_dir: Path, base: str, ref: str) -> tuple[int, int]:
    """Commits in ref, die base fehlen, und umgekehrt."""
    result = git.run(["rev-list", "--left-right", "--count", f"{base}...{ref}"], code_dir,
                     check=False)
    try:
        behind, ahead = (int(x) for x in result.stdout.split())
    except ValueError:
        return 0, 0
    return ahead, behind


def list_branches(code_dir: Path) -> list[Branch]:
    """Alle Branches, lokal und auf der Plattform. Reihenfolge: aktueller, Haupt-Branch, dann die
    übrigen mit dem neuesten Commit zuerst."""
    state = git.status(code_dir)
    main = state.default_branch
    fields = _FIELD.join(["%(refname)", "%(upstream:short)", "%(authordate:iso-strict)",
                          "%(authorname)"])
    result = git.run(["for-each-ref", f"--format={fields}", "refs/heads", "refs/remotes/origin"],
                     code_dir, action="Branches lesen")
    found: dict[str, Branch] = {}
    for line in result.stdout.splitlines():
        ref, upstream, date, author = (line.split(_FIELD) + ["", "", ""])[:4]
        if ref.startswith("refs/heads/"):
            name = ref[len("refs/heads/"):]
            branch = found.setdefault(name, Branch(name))
            # Der lokale Stand zählt vor dem der Plattform
            branch.local, branch.upstream = True, upstream
            branch.date, branch.author = date or branch.date, author or branch.author
        elif ref.startswith("refs/remotes/origin/"):
            name = ref[len("refs/remotes/origin/"):]
            if name == "HEAD":
                continue
            branch = found.setdefault(name, Branch(name))
            branch.remote = True
            branch.date = branch.date or date
            branch.author = branch.author or author
    base = main if _ref_exists(code_dir, f"refs/heads/{main}") else f"origin/{main}"
    for branch in found.values():
        branch.current = branch.local and branch.name == state.branch
        branch.default = branch.name == main
        ref = branch.name if branch.local else f"origin/{branch.name}"
        if not branch.default and _ref_exists(code_dir, base):
            branch.ahead_main, branch.behind_main = _ahead_behind(code_dir, base, ref)
        if branch.local and branch.upstream:
            branch.ahead, branch.behind = _ahead_behind(code_dir, branch.upstream, branch.name)
    rest = sorted((b for b in found.values() if not b.current and not b.default),
                  key=lambda b: b.date, reverse=True)
    first = [b for b in found.values() if b.current]
    first += [b for b in found.values() if b.default and not b.current]
    return first + rest


def refresh(code_dir: Path, env: dict[str, str] | None = None, cancel=None) -> None:
    """Stand der Plattform holen, gelöschte Branches der Plattform vergessen (git fetch --prune).
    Nur, wenn das Projekt eine Verbindung origin hat."""
    if git.config_get(code_dir, "remote.origin.url"):
        git.run(["fetch", "--prune", "origin"], code_dir, env=env, timeout=None, cancel=cancel,
                action="Holen")


# -- Anlegen, wechseln, umbenennen, löschen ------------------------------------------------------
def name_problem(code_dir: Path, name: str) -> str:
    """Leer, wenn der Name passt, sonst ein Satz, was nicht passt."""
    if not name:
        return "Bitte geben Sie einen Namen ein."
    if re.search(r"\s", name):
        return "Der Name darf keine Leerzeichen enthalten. Nehmen Sie zum Beispiel Bindestriche."
    if git.run(["check-ref-format", "--branch", name], code_dir, check=False).returncode != 0:
        return ("Diesen Namen erlaubt Git nicht. Erlaubt sind zum Beispiel Buchstaben, Ziffern, "
                "Bindestrich und Schrägstrich.")
    existing = {b.name.lower() for b in list_branches(code_dir)}
    if name.lower() in existing:
        return f"Einen Branch {name} gibt es schon."
    return ""


def suggest_name(text: str) -> str:
    """Vorschlag aus einem Satz: "Suche in PDFs" wird zu "suche-in-pdfs"."""
    text = text.lower()
    for old, new in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(old, new)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:50]


def create(code_dir: Path, name: str) -> None:
    """Neuen Branch vom aktuellen Stand anlegen und hinwechseln, wie git switch -c. Änderungen
    ohne Commit kommen mit, wie in Git und GitHub Desktop."""
    problem = name_problem(code_dir, name)
    if problem:
        raise CockpitError(problem)
    git.run(["switch", "-q", "-c", name], code_dir, action="Branch anlegen")


def switch(code_dir: Path, name: str) -> None:
    """Zu einem Branch wechseln. Gibt es ihn nur auf der Plattform, legt Git ihn lokal an.
    Würden Änderungen ohne Commit überschrieben, weigert sich Git, und es ändert sich nichts."""
    result = git.run(["switch", "-q", name], code_dir, check=False)
    if result.returncode != 0:
        text = (result.stderr or result.stdout).lower()
        if "would be overwritten" in text or "overwritten by checkout" in text:
            raise CockpitError(f"Ihre Änderungen ohne Commit passen nicht zu {name}. Git würde sie "
                               "überschreiben. Es wurde nicht gewechselt. Legen Sie die Änderungen "
                               "beiseite oder laden Sie sie zuerst hoch.",
                               f"git switch: {(result.stderr or result.stdout).strip()}")
        raise git.explain(result, "Branch wechseln")


def rename_local(code_dir: Path, old: str, new: str) -> None:
    problem = name_problem(code_dir, new)
    if problem:
        raise CockpitError(problem)
    git.run(["branch", "-m", old, new], code_dir, action="Branch umbenennen")


def rename_remote(code_dir: Path, old: str, new: str, env: dict[str, str] | None = None,
                  local: bool = True) -> None:
    """Auf der Plattform umbenennen, wie im Terminal: den neuen Namen hochladen, den alten
    löschen. Kein force push. local: Es gibt den Branch (schon mit dem neuen Namen) auch hier,
    dann folgt er danach dem neuen Namen auf der Plattform."""
    if local:
        push = ["push", "-u", "origin", f"{new}:refs/heads/{new}"]
    else:
        push = ["push", "origin", f"refs/remotes/origin/{old}:refs/heads/{new}"]
    git.run(push, code_dir, env=env, timeout=None, action="Branch umbenennen")
    git.run(["push", "origin", "--delete", old], code_dir, env=env, timeout=None,
            action="Branch umbenennen")
    git.run(["fetch", "--prune", "origin"], code_dir, env=env, timeout=None, check=False)


def unmerged(code_dir: Path, name: str) -> int:
    """Commits dieses Branches, die es in keinem anderen Branch und nicht auf der Plattform gibt."""
    others = [f"^{b.name}" if b.local else f"^origin/{b.name}"
              for b in list_branches(code_dir) if b.name != name]
    remote = [f"^origin/{name}"] if _ref_exists(code_dir, f"refs/remotes/origin/{name}") else []
    result = git.run(["rev-list", "--count", name, *others, *remote], code_dir, check=False)
    try:
        return int(result.stdout.strip() or 0)
    except ValueError:
        return 0


def delete_local(code_dir: Path, name: str) -> str:
    """Lokalen Branch löschen. Sein letzter Commit bleibt unter refs/codecockpit/geloescht/
    erreichbar, damit nichts verloren geht. Gibt diesen Verweis zurück."""
    state = git.status(code_dir)
    if name == state.branch:
        raise CockpitError(f"{name} ist der aktuelle Branch. Wechseln Sie zuerst zu einem anderen.")
    if name == state.default_branch:
        raise CockpitError(f"{name} ist der Haupt-Branch. Er lässt sich hier nicht löschen.")
    keep = f"{DELETED_REF}{name}-{datetime.now():%Y-%m-%d_%H-%M-%S}"
    git.run(["update-ref", keep, f"refs/heads/{name}"], code_dir, action="Branch löschen")
    git.run(["branch", "-D", name], code_dir, action="Branch löschen")
    log.info("Branch %s gelöscht, Sicherung unter %s", name, keep)
    return keep


def delete_remote(code_dir: Path, name: str, env: dict[str, str] | None = None) -> None:
    """Branch auf der Plattform löschen (git push --delete, kein force push)."""
    if name == default_branch(code_dir):
        raise CockpitError(f"{name} ist der Haupt-Branch. Er lässt sich hier nicht löschen.")
    remote_ref = f"refs/remotes/origin/{name}"
    if _ref_exists(code_dir, remote_ref):                 # Commits bleiben hier erreichbar
        keep = f"{DELETED_REF}{name}-github-{datetime.now():%Y-%m-%d_%H-%M-%S}"
        git.run(["update-ref", keep, remote_ref], code_dir, check=False)
    git.run(["push", "origin", "--delete", name], code_dir, env=env, timeout=None,
            action="Branch löschen")


# -- In den Haupt-Branch übernehmen -------------------------------------------------------------
def merge_preview(code_dir: Path, source: str) -> sync.Incoming:
    """Was das Übernehmen von source in den aktuellen Branch ändern würde."""
    state = git.status(code_dir)
    ahead, behind = _ahead_behind(code_dir, "HEAD", source)
    incoming = sync.Incoming(state.branch, source, behind=ahead, ahead=behind)
    if ahead:
        result = git.run(["diff", "--name-only", "-z", f"HEAD...{source}"], code_dir,
                         action="Übernehmen")
        incoming.files = sorted(f for f in result.stdout.split("\0") if f)
    incoming.local = sorted(sync.changes(code_dir).files)
    incoming.overlap = sorted(set(incoming.files) & set(incoming.local))
    return incoming


def merge_into_current(code_dir: Path, project_name: str, source: str) -> sync.MergeOutcome:
    """source in den aktuellen Branch übernehmen (git merge). Vorher eine Sicherheitskopie der
    betroffenen Dateien. Konflikte löst man wie beim Holen."""
    if sync.changes(code_dir):
        raise CockpitError("Es gibt Änderungen ohne Commit. Laden Sie sie zuerst hoch oder legen "
                           "Sie sie beiseite.")
    incoming = merge_preview(code_dir, source)
    sync.backup(code_dir, project_name, incoming, reason="vor dem Übernehmen")
    return sync.merge(code_dir, stash=False, source=source)


# -- Beiseitelegen (Stash) ---------------------------------------------------------------------
@dataclass
class Stash:
    index: int
    message: str
    date: datetime | None
    files: list[str]

    @property
    def ref(self) -> str:
        return f"stash@{{{self.index}}}"

    @property
    def branch(self) -> str:
        """Branch, auf dem beiseitegelegt wurde, soweit bekannt."""
        if STASH_PREFIX in self.message:
            return self.message.split(STASH_PREFIX, 1)[1].strip()
        match = re.match(r"(?:WIP on|On) ([^:]+):", self.message)
        return match[1] if match else ""

    def line(self) -> str:
        """"25.09.2026 14:03, auf main, 2 Dateien: main.py und neu.py"."""
        parts = [f"{self.date:%d.%m.%Y %H:%M}" if self.date else "ohne Datum"]
        if self.branch:
            parts.append(f"auf {self.branch}")
        names = join_words(self.files[:3]) + (" und weitere" if len(self.files) > 3 else "")
        parts.append(f"{count(len(self.files), 'Datei', 'Dateien')}: {names}")
        if sync.STASH_MESSAGE in self.message:
            parts.append("vor dem Holen")
        return ", ".join(parts)


def stashes(code_dir: Path) -> list[Stash]:
    result = git.run(["stash", "list", f"--format=%gs{_FIELD}%cI"], code_dir, check=False)
    found = []
    for index, line in enumerate(result.stdout.splitlines()):
        message, _, date = line.partition(_FIELD)
        try:
            when = datetime.fromisoformat(date) if date else None
        except ValueError:
            when = None
        found.append(Stash(index, message, when, stash_files(code_dir, f"stash@{{{index}}}")))
    return found


def stash_files(code_dir: Path, ref: str) -> list[str]:
    """Dateien eines Stashs, auch die neuen (ohne Commit, --include-untracked)."""
    tracked = git.run(["stash", "show", "--name-only", "-z", ref], code_dir, check=False).stdout
    files = {f for f in tracked.split("\0") if f}
    if _ref_exists(code_dir, f"{ref}^3"):
        untracked = git.run(["ls-tree", "-r", "-z", "--name-only", f"{ref}^3"], code_dir,
                            check=False).stdout
        files |= {f for f in untracked.split("\0") if f}
    return sorted(files)


def stash_push(code_dir: Path, project_name: str) -> Path | None:
    """Alle Änderungen ohne Commit beiseitelegen, auch neue Dateien. Vorher eine Sicherheitskopie.
    Gibt deren Ordner zurück."""
    changed = sync.changes(code_dir)
    if not changed:
        raise CockpitError("Es gibt keine Änderungen ohne Commit.")
    branch = git.status(code_dir).branch or "unbekannt"
    folder = history.backup_files(code_dir, project_name, "vor dem Beiseitelegen", changed.files)
    git.run(["stash", "push", "--include-untracked", "-m", f"{STASH_PREFIX}{branch}"], code_dir,
            action="Beiseitelegen")
    return folder


def stash_for_branch(code_dir: Path, branch: str) -> Stash | None:
    """Neueste beiseitegelegte Änderung des Cockpits für diesen Branch."""
    return next((s for s in stashes(code_dir) if s.message.endswith(f"{STASH_PREFIX}{branch}")),
                None)


def stash_restore(code_dir: Path, stash: Stash) -> None:
    """Beiseitegelegte Änderungen zurückholen (git stash pop). Geht nur ohne eigene Änderungen.
    Passen sie nicht mehr zum Stand, bleibt alles, wie es war, und sie bleiben beiseitegelegt."""
    if sync.changes(code_dir):
        raise CockpitError("Es gibt Änderungen ohne Commit. Laden Sie sie zuerst hoch, legen Sie "
                           "sie beiseite oder verwerfen Sie sie.")
    result = git.run(["stash", "apply", stash.ref], code_dir, check=False)
    if result.returncode != 0 or sync.conflicted(code_dir):
        _undo_apply(code_dir, stash)
        where = f" Wechseln Sie zu {stash.branch} und versuchen Sie es dort." if stash.branch else ""
        raise CockpitError("Die Änderungen passen nicht mehr zum jetzigen Stand. Es wurde nichts "
                           f"verändert, sie bleiben beiseitegelegt.{where}",
                           f"git stash apply: {(result.stderr or result.stdout).strip()}")
    git.run(["stash", "drop", "-q", stash.ref], code_dir, action="Zurückholen")


def _undo_apply(code_dir: Path, stash: Stash) -> None:
    """Nach einem misslungenen Zurückholen: Vorher gab es keine Änderungen, also zurück auf den
    letzten Commit und die mitgebrachten neuen Dateien entfernen."""
    git.run(["reset", "-q", "--hard", "HEAD"], code_dir, check=False)
    if _ref_exists(code_dir, f"{stash.ref}^3"):
        untracked = git.run(["ls-tree", "-r", "-z", "--name-only", f"{stash.ref}^3"], code_dir,
                            check=False).stdout
        for relative in (f for f in untracked.split("\0") if f):
            (code_dir / relative).unlink(missing_ok=True)


def stash_to_branch(code_dir: Path, stash: Stash, name: str) -> None:
    """Als neuen Branch zurückholen (git stash branch): Der Branch beginnt dort, wo die Änderungen
    beiseitegelegt wurden. Das passt immer."""
    if sync.changes(code_dir):
        raise CockpitError("Es gibt Änderungen ohne Commit. Laden Sie sie zuerst hoch, legen Sie "
                           "sie beiseite oder verwerfen Sie sie.")
    problem = name_problem(code_dir, name)
    if problem:
        raise CockpitError(problem)
    git.run(["stash", "branch", name, stash.ref], code_dir, action="Als Branch zurückholen")


def stash_drop(code_dir: Path, project_name: str, stash: Stash) -> Path:
    """Beiseitegelegte Änderungen löschen. Vorher kommen ihre Dateien als Sicherheitskopie in den
    Ordner backups. Gibt deren Ordner zurück."""
    folder = backups.new_backup_dir(project_name, "beiseitegelegt, gelöscht", code_dir,
                                    [f"Beiseitegelegt: {stash.message}"])
    refs = [stash.ref]
    if _ref_exists(code_dir, f"{stash.ref}^3"):
        refs.append(f"{stash.ref}^3")                   # neue Dateien liegen im dritten Elternteil
    for relative in stash.files:
        data = next((d for d in (_show(code_dir, r, relative) for r in refs) if d is not None),
                    None)
        if data is not None:
            target = folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    git.run(["stash", "drop", "-q", stash.ref], code_dir, action="Löschen")
    log.info("Beiseitegelegte Änderungen gelöscht, Sicherheitskopie %s", folder)
    return folder


def _show(code_dir: Path, ref: str, relative: str) -> bytes | None:
    """Inhalt einer Datei aus einem Commit als Bytes, None wenn es sie dort nicht gibt."""
    found = git.find_git()
    if found is None:
        raise git.GitError(git.NOT_INSTALLED)
    result = subprocess.run([str(found), "show", f"{ref}:{relative}"], cwd=str(code_dir),
                            capture_output=True,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return result.stdout if result.returncode == 0 else None


# -- Geschützter Haupt-Branch (Phase 6c) ------------------------------------------------------
MOVED_REF = "refs/codecockpit/vor-dem-verschieben/"


def move_commits_to_new_branch(code_dir: Path, name: str) -> str:
    """Die Commits, die noch nicht hochgeladen sind, in einen neuen Branch verschieben (Konzept
    10.14: main ist geschützt). Der neue Branch beginnt beim jetzigen Stand, Sie wechseln zu ihm.
    Der alte Branch kommt auf den Stand der Plattform. Keine Datei ändert sich, und der alte Stand
    bleibt unter refs/codecockpit/vor-dem-verschieben/ erreichbar. Gibt den alten Branch zurück."""
    state = git.status(code_dir)
    old = state.branch
    if not old:
        raise CockpitError("Es ist gerade kein Branch ausgewählt.")
    problem = name_problem(code_dir, name)
    if problem:
        raise CockpitError(problem)
    keep = f"{MOVED_REF}{old}-{datetime.now():%Y-%m-%d_%H-%M-%S}"
    git.run(["update-ref", keep, "HEAD"], code_dir, action="Branch anlegen")
    git.run(["switch", "-q", "-c", name], code_dir, action="Branch anlegen")
    if state.upstream:
        git.run(["branch", "-f", old, state.upstream], code_dir, action="Branch anlegen")
    log.info("Commits von %s nach %s verschoben, alter Stand unter %s", old, name, keep)
    return old

