"""Python und virtuelle Umgebung für den Bau der Exe.

Dazu die Wahl des Pythons (Wunsch des Nutzers vom 20.10.2026) und die Prüfung der Wheels.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from cockpit.core import git, paths
from cockpit.core.errors import Cancelled, CockpitError
from cockpit.core.exe_report import WHEEL_REPLACEMENTS, python_version
from cockpit.core.exe_state import FLAGS
from cockpit.core.projects import Project

log = logging.getLogger(__name__)


# -- Python und virtuelle Umgebung ---------------------------------------------------------------
def find_python() -> list[str] | None:
    """Befehl für ein installiertes Python 3. Die Exe des Cockpits bringt keins mit."""
    candidates: list[list[str]] = []
    if not getattr(sys, "frozen", False):
        candidates.append([sys.executable])
    candidates += [["py", "-3"], ["python"]]
    for command in candidates:
        if shutil.which(command[0]) is None and not Path(command[0]).is_file():
            continue
        try:
            result = subprocess.run([*command, "--version"], capture_output=True, text=True,
                                    timeout=20, creationflags=FLAGS)
        except (OSError, subprocess.SubprocessError):
            continue
        if result.returncode == 0 and "Python 3" in (result.stdout + result.stderr):
            return command
    return None


def venv_python(code_dir: Path) -> Path:
    return code_dir / ".venv" / "Scripts" / "python.exe"


def python_in(venv: Path) -> Path:
    return venv / "Scripts" / "python.exe"


def _requirements_text(code_dir: Path) -> str:
    path = code_dir / "requirements.txt"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(sorted(line.strip() for line in lines if line.strip()
                            and not line.strip().startswith("#")))


def build_venv(project: Project, code_dir: Path | None = None) -> Path:
    """Ort der virtuellen Umgebung zum Bauen (Wunsch des Nutzers, 01.10.2026): kurz, unter
    %LOCALAPPDATA%\\CodeCockpit\\venvs, nicht im Projektordner. Sonst wird der Pfad bei tief
    liegenden Projekten mit Bibliotheken wie PySide6 länger als Windows erlaubt.
    Ein Branch nutzt die Umgebung von main mit, wenn seine requirements.txt gleich ist. Sonst
    bekommt er eine eigene, damit main sauber bleibt.
    Seit dem 11.10.2026 hängt der Name an der Nummer des Projekts, nicht mehr am Pfad. Vorher
    bekam ein Projekt nach dem Umbenennen eines Ordners eine neue, leere Umgebung, und Schritt 1
    lud alle Bibliotheken neu herunter (Rückmeldung des Nutzers). Eine Umgebung mit dem alten
    Namen für den jetzigen Pfad wird einmal umbenannt und weiter benutzt."""
    main = project.code_dir
    code_dir = code_dir or main
    old_key = str(main.resolve()).lower()
    marker = f"-p{project.id}"
    old_suffix = ""
    if code_dir.resolve() != main.resolve() and \
            _requirements_text(code_dir) != _requirements_text(main):
        old_key += "|" + code_dir.name.lower()
        old_suffix = "-b"
        branch = hashlib.sha1(code_dir.name.lower().encode("utf-8")).hexdigest()[:6]
        marker += f"-{branch}-b"
    root = paths.cache_dir() / "venvs"
    # Schon vorhanden, vielleicht unter einem früheren Projektnamen
    found = sorted(root.glob(f"*{marker}")) if root.is_dir() else []
    if found:
        return found[0]
    name = re.sub(r"[^A-Za-z0-9_-]", "", project.name)[:20] or "Projekt"
    venv = root / f"{name}{marker}"
    old_digest = hashlib.sha1(old_key.encode("utf-8")).hexdigest()[:8]
    old = root / f"{name}-{old_digest}{old_suffix}"
    if old.is_dir():
        try:
            old.rename(venv)
        except OSError as exc:
            log.warning("Umgebung %s nicht umbenannt: %s", old.name, exc)
            return old
    return venv


def run_process(args: list[str], cwd: Path, on_line: Callable[[str], None] | None = None,
                cancel: threading.Event | None = None, env: dict | None = None) -> int:
    """Programm ausführen, jede Zeile der Ausgabe an on_line. Wirft Cancelled bei Abbruch."""
    from cockpit.core.logging_setup import mask_secrets
    from cockpit.core.terminal import _kill_tree, clean_line
    try:
        process = subprocess.Popen(args, cwd=str(cwd), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   creationflags=FLAGS, env=env)
    except OSError as exc:
        raise CockpitError(f"{Path(args[0]).name} ließ sich nicht starten.", repr(exc)) from None
    stopped = threading.Event()

    def watch() -> None:
        while not stopped.wait(0.2):
            if cancel is not None and cancel.is_set():
                _kill_tree(process)
                return

    threading.Thread(target=watch, daemon=True).start()
    try:
        assert process.stdout is not None
        for raw in process.stdout:
            line = mask_secrets(clean_line(raw.decode("utf-8", "replace")))
            if line.strip() and on_line is not None:
                on_line(line)
        code = process.wait()
    finally:
        stopped.set()
    if cancel is not None and cancel.is_set():
        raise Cancelled()
    return code


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    return env


LONG_PATHS = ("Die Bibliotheken ließen sich nicht installieren, weil ein Pfad länger ist, als "
              "Windows erlaubt. Abhilfe: lange Pfade in Windows einschalten.")


PIP_HINT = ("Die Bibliotheken werden geprüft und, wenn nötig, heruntergeladen. Beim ersten Mal "
            "kann das über 10 Minuten dauern, auch wenn eine Weile nichts Neues erscheint.")


QUIET_PIP = ("Requirement already satisfied", "Using cached")


def _works(python: Path) -> bool:
    """Startet das Python der Umgebung? Nach einem Wechsel der Python-Version nicht mehr."""
    try:
        return subprocess.run([str(python), "-c", "pass"], capture_output=True, timeout=30,
                              creationflags=FLAGS).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


# -- Python für den Bau wählen (Wunsch des Nutzers vom 20.10.2026) ---------------------------------
# Python 3.14 war beim Waagenzähler zu neu: pygame gab es dafür nicht fertig, und pip scheiterte
# erst nach Minuten beim Übersetzen. Jetzt prüft das Cockpit vorher in Sekunden, ob es jede
# Bibliothek fertig gibt, und nimmt automatisch ein älteres installiertes Python, wenn das hilft.
NO_PYTHON = ("Python wurde nicht gefunden. Zum Erstellen einer Exe braucht das Cockpit Python. "
             "Die Anleitung steht im Menü Hilfe unter Python installieren.")


_PY_LIST = re.compile(r"-V:(\d+)\.(\d+)(\S*)\s+\*?\s*(\S.*\.exe)\s*$", re.IGNORECASE)


_NO_MATCH = re.compile(r"(?:No matching distribution found for|Could not find a version that "
                       r"satisfies the requirement)\s+([A-Za-z0-9_.\-]+)")


@dataclass
class PythonInstall:
    version: tuple[int, int]
    command: list[str]

    @property
    def label(self) -> str:
        return f"{self.version[0]}.{self.version[1]}"


def find_pythons() -> list[PythonInstall]:
    """Installierte Pythons, das neueste zuerst. Über den Python-Starter py, sonst das eine, das
    find_python findet."""
    found: dict[tuple[int, int], PythonInstall] = {}
    if shutil.which("py") is not None:
        try:
            result = subprocess.run(["py", "-0p"], capture_output=True, text=True, timeout=20,
                                    creationflags=FLAGS)
            for row in (result.stdout + result.stderr).splitlines():
                match = _PY_LIST.search(row.strip())
                # 32-Bit-Versionen (-32) nur, wenn es keine 64-Bit-Version gibt
                if match and Path(match.group(4)).is_file():
                    version = (int(match.group(1)), int(match.group(2)))
                    if version not in found or not match.group(3):
                        found[version] = PythonInstall(version, [match.group(4)])
        except (OSError, subprocess.SubprocessError):
            pass
    if not found:
        command = find_python()
        version = python_version(command) if command is not None else None
        if command is not None and version is not None:
            found[version] = PythonInstall(version, command)
    return [found[v] for v in sorted(found, reverse=True)]


def missing_wheels(python: PythonInstall, code_dir: Path, cancel=None) -> list[str] | None:
    """Bibliotheken aus requirements.txt, die es für dieses Python nicht als fertiges Paket gibt.
    pip prüft das, ohne etwas zu installieren. None, wenn die Prüfung nicht ging, zum Beispiel
    ohne Internet. Das Ergebnis wird je Python und requirements.txt gemerkt."""
    path = code_dir / "requirements.txt"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    key = f"{python.label}|{hashlib.sha1(text.encode('utf-8')).hexdigest()}"
    cache = paths.cache_dir() / "wheel-check.json"
    try:
        known = json.loads(cache.read_text(encoding="utf-8")) if cache.is_file() else {}
    except (OSError, ValueError):
        known = {}
    if isinstance(known.get(key), list):
        return known[key]
    try:
        result = subprocess.run([*python.command, "-m", "pip", "install", "--dry-run",
                                 "--ignore-installed", "--only-binary=:all:", "--quiet",
                                 "--disable-pip-version-check", "-r", str(path)],
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=300, cwd=code_dir,
                                env=_environment(), creationflags=FLAGS)
    except (OSError, subprocess.SubprocessError):
        return None
    if cancel is not None and cancel.is_set():
        raise Cancelled()
    if result.returncode == 0:
        missing: list[str] = []
    else:
        missing = sorted(set(_NO_MATCH.findall(result.stdout + result.stderr)), key=str.lower)
        if not missing:
            return None                          # anderer Fehler, etwa keine Verbindung
    known[key] = missing
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(known, indent=1), encoding="utf-8")
    except OSError:
        pass
    return missing


wheel_check = missing_wheels                    # in Tests ersetzbar, dort ohne Internet


def choose_python(code_dir: Path, wanted: str = "", on_line=None,
                  cancel=None) -> PythonInstall:
    """Das Python für den Bau. wanted: "3.13" aus den Exe-Einstellungen, leer für automatisch.
    Automatisch: das neueste installierte, für das es alle Bibliotheken fertig gibt. Gibt es das
    nicht, das neueste, mit einem Hinweis, was fehlt."""
    say = on_line or (lambda text: None)
    installs = find_pythons()
    if not installs:
        raise CockpitError(NO_PYTHON)
    if wanted:
        chosen = next((p for p in installs if p.label == wanted), None)
        if chosen is not None:
            say(f"Python {chosen.label} wird benutzt, wie in den Exe-Einstellungen gewählt.")
            return chosen
        say(f"Python {wanted} ist nicht installiert. Das Cockpit wählt selbst.")
    say("Es wird geprüft, ob es alle Bibliotheken fertig für Python gibt.")
    first_missing: list[str] | None = None
    for python in installs:
        missing = wheel_check(python, code_dir, cancel)
        if missing is None or not missing:
            if python is not installs[0] and first_missing:
                say(f"Python {python.label} wird benutzt, weil es für Python "
                    f"{installs[0].label} diese Bibliotheken nicht fertig gibt: "
                    f"{', '.join(first_missing)}.")
            elif missing == []:
                say(f"Alle Bibliotheken gibt es fertig für Python {python.label}.")
            return python
        if first_missing is None:
            first_missing = missing
    newest = installs[0]
    replaced = [f"{m} durch {WHEEL_REPLACEMENTS[m.lower()][0]}" for m in first_missing or []
                if m.lower() in WHEEL_REPLACEMENTS]
    say(f"Achtung: Für Python {newest.label} gibt es diese Bibliotheken nicht fertig: "
        f"{', '.join(first_missing or [])}. pip versucht, sie selbst zu übersetzen, das scheitert "
        "oft." + (f" Abhilfe: in requirements.txt {', '.join(replaced)} ersetzen."
                  if replaced else " Abhilfe: eine ältere Python-Version zusätzlich "
                                   "installieren, zum Beispiel 3.13. Das Cockpit nimmt sie dann "
                                   "selbst."))
    return newest


def venv_version(venv: Path) -> tuple[int, int] | None:
    """Python-Version einer virtuellen Umgebung aus pyvenv.cfg."""
    try:
        text = (venv / "pyvenv.cfg").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = re.search(r"^version(?:_info)?\s*=\s*(\d+)\.(\d+)", text, re.MULTILINE)
    return (int(match.group(1)), int(match.group(2))) if match else None


def prepare_venv(code_dir: Path, on_line=None, cancel=None, venv: Path | None = None,
                 python_wanted: str | None = None) -> Path:
    """Virtuelle Umgebung anlegen, requirements.txt und PyInstaller installieren. venv: Ort der
    Umgebung, sonst .venv im Ordner Repository. Eine kaputte Umgebung wird neu angelegt.
    python_wanted: None wie bisher (irgendein Python), sonst die Wahl aus den Exe-Einstellungen
    ("" für automatisch). Passt die Version der Umgebung nicht, wird sie neu angelegt."""
    from cockpit.core import long_paths, safety_check
    venv = venv or code_dir / ".venv"
    python = python_in(venv)
    env = _environment()
    base: list[str] | None = None
    if python_wanted is not None:
        chosen = choose_python(code_dir, python_wanted, on_line, cancel)
        base = chosen.command
        if python.is_file() and venv_version(venv) not in (None, chosen.version):
            if on_line is not None:
                on_line(f"Die Bau-Umgebung wird für Python {chosen.label} neu angelegt.")
            shutil.rmtree(venv, ignore_errors=True)
    if python.is_file() and not _works(python):
        shutil.rmtree(venv, ignore_errors=True)
    if not python.is_file():
        base = base or find_python()
        if base is None:
            raise CockpitError(NO_PYTHON)
        venv.parent.mkdir(parents=True, exist_ok=True)
        if run_process([*base, "-m", "venv", str(venv)], code_dir, on_line, cancel, env):
            raise CockpitError("Die virtuelle Umgebung ließ sich nicht anlegen.")
    if git.is_repo(code_dir) and venv.parent == code_dir:
        safety_check.ensure_gitignore(code_dir)          # .venv nie hochladen
    packages = ["pyinstaller"]
    # Ohne --quiet (Rückmeldung des Nutzers vom 11.10.2026): Beim ersten Mal lädt pip oft
    # mehrere hundert MB. Mit --quiet stand minutenlang nichts da, es sah aus wie ein Fehler.
    args = [str(python), "-m", "pip", "install", "--progress-bar", "off"]
    if (code_dir / "requirements.txt").is_file():
        args += ["-r", "requirements.txt"]
    output: list[str] = []

    def line(text: str) -> None:
        output.append(text)
        # Was schon da ist, nicht bei jedem Bau einzeln auflisten
        if on_line is not None and not text.lstrip().startswith(QUIET_PIP):
            on_line(text)

    if on_line is not None:
        on_line(PIP_HINT)
    if run_process(args + packages, code_dir, line, cancel, env):
        if long_paths.is_long_path_error("\n".join(output)):
            raise CockpitError(LONG_PATHS, "\n".join(output[-5:]))
        raise CockpitError("Die Bibliotheken ließen sich nicht installieren. Die Ausgabe nennt den "
                           "Grund.")
    return python
