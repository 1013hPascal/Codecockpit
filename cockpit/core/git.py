"""Aufruf von Git (Konzept 9, Grundsatz aus ENTSCHEIDUNGEN.md: wie Git im Terminal).

Das Cockpit nutzt dieselben Git-Befehle wie das Terminal und GitHub Desktop. Es gibt nie einen
force push.

Zugangsdaten bekommt Git nur über Umgebungsvariablen (GitCredentials der Plattform), nie über die
Befehlszeile, weil andere Programme die Befehlszeile sehen können. Git fragt nie selbst nach einem
Passwort (GIT_TERMINAL_PROMPT=0): Fehlt der Zugang, kommt eine verständliche Meldung.

Fehler von Git werden als GitError mit einfachem Text und der Originalmeldung als Details gemeldet.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from cockpit.core.errors import Cancelled, CockpitError

log = logging.getLogger(__name__)

GUIDE = "anleitungen/git-installieren.md"
MAIN_BRANCH = "main"                   # Haupt-Branch neuer Repositories (ENTSCHEIDUNGEN.md)
NOT_INSTALLED = ("Git wurde nicht gefunden. Die Anleitung steht im Menü Hilfe unter "
                 "Git installieren.")


class GitError(CockpitError):
    """Git ist fehlgeschlagen. details enthält die Meldung von Git."""


def find_git() -> Path | None:
    """Pfad zu git.exe oder None, wenn Git nicht installiert ist."""
    found = shutil.which("git")
    if found:
        return Path(found)
    candidates = [Path(os.environ.get(var, "")) / "Git" / "cmd" / "git.exe"
                  for var in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)")]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "Programs" / "Git" / "cmd" / "git.exe")
    return next((c for c in candidates if c.is_file()), None)


def _environment(extra: Mapping[str, str] | None) -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"         # nie im Hintergrund auf eine Eingabe warten
    env["GCM_INTERACTIVE"] = "never"         # Git Credential Manager: kein eigenes Fenster
    env["LC_ALL"] = "C"                      # Meldungen auf Englisch, damit sie erkennbar sind
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    if extra:
        env.update(extra)
    return env


def run(args: list[str], cwd: Path | None = None, env: Mapping[str, str] | None = None,
        check: bool = True, timeout: float | None = 600,
        cancel: threading.Event | None = None, action: str = "") -> subprocess.CompletedProcess:
    """git mit den Argumenten ausführen. Blockiert, also bei längeren Befehlen nur im Hintergrund.

    env: zusätzliche Umgebungsvariablen, zum Beispiel die Zugangsdaten der Plattform.
    cancel: bricht Git ab, sobald es gesetzt ist (Cancelled).
    action: kurze Beschreibung für die Fehlermeldung, zum Beispiel "Herunterladen".
    """
    git = find_git()
    if git is None:
        raise GitError(NOT_INSTALLED)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        process = subprocess.Popen(
            [str(git), *args], cwd=str(cwd) if cwd else None, env=_environment(env),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=flags)
    except OSError as exc:
        raise GitError("Git ließ sich nicht starten.", repr(exc)) from None
    deadline = time.monotonic() + timeout if timeout else None
    while True:
        try:
            out, err = process.communicate(timeout=0.2)
            break
        except subprocess.TimeoutExpired:
            if cancel is not None and cancel.is_set():
                process.kill()
                process.communicate()
                raise Cancelled() from None
            if deadline is not None and time.monotonic() > deadline:
                process.kill()
                process.communicate()
                raise GitError("Git hat zu lange gebraucht und wurde abgebrochen.",
                               f"git {args[0]} nach {timeout} Sekunden") from None
    result = subprocess.CompletedProcess(args, process.returncode,
                                         out.decode("utf-8", "replace"),
                                         err.decode("utf-8", "replace"))
    if check and result.returncode != 0:
        raise explain(result, action)
    return result


def explain(result: subprocess.CompletedProcess, action: str = "") -> GitError:
    """Häufige Meldungen von Git in einfaches Deutsch übersetzen."""
    text = (result.stderr or result.stdout).strip()
    lowered = text.lower()
    doing = f" ({action})" if action else ""
    details = f"git {' '.join(result.args[:2])}: {text}"
    if "could not resolve host" in lowered or "unable to access" in lowered and (
            "timed out" in lowered or "failed to connect" in lowered):
        return GitError("Die Plattform ist nicht erreichbar. Bitte prüfen Sie die "
                        "Internetverbindung.", details)
    if ("authentication failed" in lowered or "could not read username" in lowered
            or "invalid username or password" in lowered or "403" in lowered):
        return GitError("Die Anmeldung bei der Plattform hat nicht geklappt. Bitte prüfen Sie "
                        "das Konto in der Kontenverwaltung.", details)
    if "not found" in lowered and ("repository" in lowered or "remote" in lowered):
        return GitError("Das Repository wurde auf der Plattform nicht gefunden. Möglicherweise "
                        "fehlt der Zugriff.", details)
    if "tell me who you are" in lowered or "empty ident" in lowered:
        return GitError("Für Commits fehlen Name und E-Mail-Adresse. Bitte tragen Sie sie im "
                        "Menü Einstellungen unter Grundeinstellungen ein.", details)
    if "rejected" in lowered and ("fetch first" in lowered or "non-fast-forward" in lowered):
        return GitError("Auf der Plattform gibt es Änderungen, die hier noch fehlen. Bitte holen "
                        "Sie sie zuerst.", details)
    if "protected branch" in lowered:
        return GitError("Der Branch ist auf der Plattform geschützt. Direktes Hochladen ist dort "
                        "nicht erlaubt.", details)
    if "not a git repository" in lowered:
        return GitError("Der Ordner ist kein Git-Repository.", details)
    if "already exists and is not an empty directory" in lowered:
        return GitError("Der Zielordner gibt es schon und er ist nicht leer.", details)
    return GitError(f"Git meldet einen Fehler{doing}.", details)


# -- Adressen von Repositories ------------------------------------------------------------------
@dataclass(frozen=True)
class RemoteAddress:
    host: str                  # "github.com"
    owner: str                 # "1013hPascal"
    name: str                  # "Tagebuch"

    @property
    def key(self) -> str:
        """Vergleichbarer Schlüssel ohne Groß- und Kleinschreibung."""
        return f"{self.host}/{self.owner}/{self.name}".lower()


_SCP = re.compile(r"^(?:[\w.-]+@)?(?P<host>[\w.-]+):(?P<path>[^\\].*)$")


def parse_remote(url: str) -> RemoteAddress | None:
    """https://github.com/owner/name(.git), git@github.com:owner/name.git, ssh://... ."""
    url = (url or "").strip()
    if not url:
        return None
    if "://" in url:
        parsed = urlparse(url)
        host, path = (parsed.hostname or "").lower(), parsed.path
    else:
        match = _SCP.match(url)
        if not match:
            return None
        host, path = match["host"].lower(), match["path"]
    parts = [p for p in path.strip("/").split("/") if p]
    if len(parts) < 2 or not host:
        return None
    name = parts[-1][:-4] if parts[-1].lower().endswith(".git") else parts[-1]
    if host == "www.github.com":
        host = "github.com"
    return RemoteAddress(host, "/".join(parts[:-1]), name)


# -- Zustand eines Repositories -----------------------------------------------------------------
@dataclass
class RepoStatus:
    """Was Git über den Stand des Code-Ordners weiß (ohne Netz, Stand des letzten Holens)."""
    is_repo: bool = False
    branch: str = ""                       # leer: kein Branch (zum Beispiel mitten im Rebase)
    upstream: str = ""                     # "origin/main", leer: nie hochgeladen
    ahead: int = 0                         # Commits noch nicht hochgeladen
    behind: int = 0                        # Commits auf der Plattform, noch nicht geholt
    changed: list[str] = field(default_factory=list)       # geänderte und neue Dateien
    remote_url: str = ""
    default_branch: str = MAIN_BRANCH      # Haupt-Branch auf der Plattform, soweit bekannt
    last_upload: str = ""                  # Datum des letzten hochgeladenen Commits, ISO
    conflicts: list[str] = field(default_factory=list)     # Dateien mit Konflikt
    merging: bool = False                  # Zusammenführen noch nicht abgeschlossen

    @property
    def remote(self) -> RemoteAddress | None:
        return parse_remote(self.remote_url)


def is_repo(code_dir: Path) -> bool:
    return (code_dir / ".git").exists()


def status(code_dir: Path) -> RepoStatus:
    """Stand des Repositories. Kein Git-Ordner: RepoStatus(is_repo=False)."""
    if not is_repo(code_dir):
        return RepoStatus()
    result = run(["status", "--porcelain=v2", "--branch", "-z", "--untracked-files=all"],
                 code_dir, action="Stand lesen")
    state = RepoStatus(is_repo=True)
    entries = iter(result.stdout.split("\0"))
    for entry in entries:
        if entry.startswith("# branch.head "):
            head = entry[len("# branch.head "):]
            state.branch = "" if head == "(detached)" else head
        elif entry.startswith("# branch.upstream "):
            state.upstream = entry[len("# branch.upstream "):]
        elif entry.startswith("# branch.ab "):
            ahead, behind = entry[len("# branch.ab "):].split()
            state.ahead, state.behind = abs(int(ahead)), abs(int(behind))
        elif entry[:2] in ("1 ", "u "):
            path = entry.split(" ", 8 if entry[0] == "1" else 10)[-1]
            state.changed.append(path)
            if entry[0] == "u":
                state.conflicts.append(path)
        elif entry.startswith("2 "):
            state.changed.append(entry.split(" ", 9)[-1])
            next(entries, None)            # alter Name der umbenannten Datei, zählt nicht
        elif entry.startswith("? "):
            state.changed.append(entry[2:])
    state.remote_url = config_get(code_dir, "remote.origin.url")
    state.merging = (code_dir / ".git" / "MERGE_HEAD").exists()
    head = run(["symbolic-ref", "--short", "-q", "refs/remotes/origin/HEAD"], code_dir,
               check=False).stdout.strip()
    state.default_branch = head.partition("/")[2] or MAIN_BRANCH
    if state.upstream:
        log_result = run(["log", "-1", "--format=%cI", state.upstream], code_dir, check=False)
        state.last_upload = log_result.stdout.strip()
    return state


def pending_files(code_dir: Path, state: RepoStatus) -> int:
    """Dateien, die noch nicht hochgeladen sind: geändert, neu oder in Commits, die noch fehlen."""
    files = set(state.changed)
    if state.upstream and state.ahead:
        result = run(["diff", "--name-only", "-z", state.upstream, "HEAD"], code_dir,
                     check=False)
        files.update(f for f in result.stdout.split("\0") if f)
    return len(files)


# -- Einstellungen und Identität -----------------------------------------------------------------
def config_get(code_dir: Path, key: str, local: bool = True) -> str:
    args = ["config", "--local", "--get", key] if local else ["config", "--get", key]
    return run(args, code_dir, check=False).stdout.strip()


def identity(code_dir: Path) -> tuple[str, str]:
    """Name und E-Mail-Adresse, die nur in diesem Repository eingetragen sind."""
    return config_get(code_dir, "user.name"), config_get(code_dir, "user.email")


def set_identity(code_dir: Path, name: str, email: str) -> None:
    """Nur für dieses Repository, nie global (ENTSCHEIDUNGEN.md)."""
    run(["config", "--local", "user.name", name], code_dir, action="Git-Identität eintragen")
    run(["config", "--local", "user.email", email], code_dir, action="Git-Identität eintragen")


# -- Anlegen, verbinden, herunterladen -----------------------------------------------------------
def init(code_dir: Path, branch: str = MAIN_BRANCH) -> None:
    run(["init", "-b", branch], code_dir, action="Repository anlegen")


def clone(url: str, target: Path, env: Mapping[str, str] | None = None,
          cancel: threading.Event | None = None) -> None:
    """Wie git clone. Der Zielordner darf nicht existieren oder muss leer sein."""
    target.parent.mkdir(parents=True, exist_ok=True)
    run(["clone", "--", url, str(target)], target.parent, env=env, timeout=None,
        cancel=cancel, action="Herunterladen")


def connect(code_dir: Path, url: str, env: Mapping[str, str] | None = None,
            cancel: threading.Event | None = None) -> str:
    """Einen Code-Ordner ohne Git-Ordner wieder mit seinem Repository verbinden (Konzept 7.5).

    Die Dateien im Ordner bleiben unverändert. Git kennt danach den Verlauf der Plattform, und
    Unterschiede erscheinen als noch nicht hochgeladene Änderungen. Gibt den Branch zurück."""
    if is_repo(code_dir):
        raise GitError("Der Ordner ist schon mit Git verbunden.")
    run(["init"], code_dir, action="Verbinden")
    run(["remote", "add", "origin", url], code_dir, action="Verbinden")
    run(["fetch", "origin"], code_dir, env=env, timeout=None, cancel=cancel, action="Holen")
    run(["remote", "set-head", "origin", "--auto"], code_dir, env=env, check=False)
    head = run(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], code_dir,
               check=False).stdout.strip()
    branch = head.partition("/")[2] or MAIN_BRANCH
    run(["symbolic-ref", "HEAD", f"refs/heads/{branch}"], code_dir, action="Verbinden")
    if head:
        # Nur der Index wird gesetzt (--mixed), nie die Dateien.
        run(["reset", "--mixed", "-q", f"origin/{branch}"], code_dir, action="Verbinden")
        run(["branch", f"--set-upstream-to=origin/{branch}"], code_dir, action="Verbinden")
    return branch
