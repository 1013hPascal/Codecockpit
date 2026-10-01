"""Die Exe eines Projekts (Konzept 10.4, Phase 10).

Zustand im Git-Ordner des Projekts, Datei codecockpit-exe.toml (seit 10g, vorher in
Code\\cockpit.toml, Abschnitt [exe]; ohne Git weiter dort): woher die Exe kommt ("cockpit": vom Cockpit
erstellt, "extern": extern erstellt und von Hand gewählt, "release": aus einem Release), wann, aus
welchem Commit und mit welcher Version. Die Einstellungen zum Bauen stehen unter [exe.build].

Grundsätze:
- Im Ordner Exe liegt nur die aktuelle Exe (eine Datei oder ein Programmordner).
- Eine bisherige Exe kommt immer erst in eine Sicherheitskopie, bevor eine neue sie ersetzt.
- Eine neu gebaute Exe ersetzt die alte erst, wenn sie den Test bestanden hat.
- Das Cockpit selbst kann seine laufende Exe nicht ersetzen. Die neue Exe wartet dann in Exe\\_neu
  und wird beim Neustart übernommen.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from cockpit.core import backups, git, paths
from cockpit.core.errors import Cancelled, CockpitError
from cockpit.core.projects import Project, read_config, write_config

log = logging.getLogger(__name__)

SECTION = "exe"
PENDING = "_neu"                        # wartende Aktualisierung der eigenen Exe
BRANCH_MARK = "_branch_"                # Exe aus einem Branch-Ordner (Phase 10f)
SOURCES = {"cockpit": "vom Cockpit erstellt", "extern": "extern erstellt",
           "release": "aus dem Release"}
PYTHON_GUIDE = "anleitungen/python-installieren.md"
EXE_GUIDE = "anleitungen/exe-verstehen.md"
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
BLOCKED = ("Windows hat die Exe blockiert. Das macht die Intelligente App-Steuerung (Smart App "
           "Control) bei Programmen ohne digitale Signatur, die Windows noch nicht kennt. Sie "
           "finden sie in Windows-Sicherheit unter App- und Browsersteuerung.")
BLOCKED_ERRORS = {4551, 1260}           # Anwendungssteuerungsrichtlinie, Gruppenrichtlinie


class BlockedByWindows(CockpitError):
    """Windows lässt das Cockpit die Exe nicht starten. Der Nutzer kann sie selbst prüfen."""


def is_blocked(exc: OSError) -> bool:
    return getattr(exc, "winerror", None) in BLOCKED_ERRORS


LOCKED = ("Die bisherige Exe lässt sich nicht verschieben. Läuft sie gerade? Bitte schließen Sie "
          "das Programm und versuchen Sie es noch einmal.")


# -- Zustand ------------------------------------------------------------------------------------
@dataclass
class ExeRecord:
    source: str                         # "cockpit", "extern" oder "release"
    date: str                           # ISO, zum Beispiel "2026-09-27T16:00:00"
    commit: str = ""                    # nur bei "cockpit": Stand des Codes beim Bau
    version: str = ""                   # bei "release" und nach dem Veröffentlichen
    pending: bool = False               # wartet in Exe\_neu auf den Neustart
    tested: bool = True                 # False: Windows ließ den Test nicht zu (Phase 10)


@dataclass
class BuildSettings:
    start_file: str = "main.py"
    name: str = ""
    one_file: bool = True
    windowed: bool = True
    icon: str = ""
    datas: list[list[str]] = field(default_factory=list)      # [Quelle, Ziel] relativ zu Code
    hidden_imports: list[str] = field(default_factory=list)
    self_test: bool = False             # Programm kennt --selbsttest
    test_seconds: int = 10
    # Ordner, die neben die Exe gehören, zum Beispiel "Meine-Vokabeln" (Phase 10g). Beim ersten
    # Bau kommen sie aus dem Ordner Code dorthin, danach bleiben sie, wie die Nutzer sie haben.
    beside: list[str] = field(default_factory=list)

    @property
    def spec_name(self) -> str:
        return f"{self.name}.spec"


RECORD_FILE = "codecockpit-exe.toml"
RECORD_KEYS = ("source", "date", "commit", "version", "pending", "tested")


def _local_record(code_dir: Path) -> Path | None:
    """Wunsch aus dem Test von 10g: Der Zustand der Exe ist Sache dieses Rechners und liegt im
    Git-Ordner, der nie hochgeladen wird. In cockpit.toml machte er aus jedem Bau eine neue
    Änderung zum Hochladen. Ohne Git bleibt er in cockpit.toml."""
    if not git.is_repo(code_dir):
        return None
    folder = git.git_dir(code_dir)
    return folder / RECORD_FILE if folder.is_dir() else None


def read_record(code_dir: Path) -> ExeRecord | None:
    import tomllib
    local = _local_record(code_dir)
    data: object = None
    if local is not None and local.is_file():
        try:
            data = tomllib.loads(local.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            log.warning("Zustand der Exe nicht lesbar: %s (%s)", local, exc)
    old = read_config(code_dir).get(SECTION, {})            # bis 10g: in cockpit.toml
    # Eine ältere Exe des Cockpits schreibt noch in cockpit.toml. Dann gilt der neuere Eintrag
    # (Rückmeldung zum Test von 8e: sonst stand der alte Stand in der Zeile Exe).
    if isinstance(old, dict) and old.get("source") in SOURCES and (
            not isinstance(data, dict) or str(old.get("date", "")) > str(data.get("date", ""))):
        data = old
    if not isinstance(data, dict) or data.get("source") not in SOURCES:
        return None
    return ExeRecord(data["source"], str(data.get("date", "")), str(data.get("commit", "")),
                     str(data.get("version", "")), bool(data.get("pending", False)),
                     bool(data.get("tested", True)))


def write_record(code_dir: Path, record: ExeRecord) -> None:
    values = {"source": record.source, "date": record.date, "commit": record.commit,
              "version": record.version, "pending": record.pending, "tested": record.tested}
    data = read_config(code_dir)
    section = data.get(SECTION) if isinstance(data.get(SECTION), dict) else {}
    local = _local_record(code_dir)
    if local is None:
        section.update(values)
        data[SECTION] = section
        write_config(code_dir, data)
        return
    import tomli_w
    local.write_text(tomli_w.dumps(values), encoding="utf-8")
    if any(key in section for key in RECORD_KEYS):
        # Einmal aufräumen: der alte Zustand aus cockpit.toml (bis 10g)
        for key in RECORD_KEYS:
            section.pop(key, None)
        data[SECTION] = section
        write_config(code_dir, data)


def read_settings(code_dir: Path) -> BuildSettings | None:
    """Einstellungen zum Bauen, None vor dem ersten Bau."""
    section = read_config(code_dir).get(SECTION, {})
    build = section.get("build") if isinstance(section, dict) else None
    if not isinstance(build, dict) or not build.get("name"):
        return None
    defaults = BuildSettings()
    return BuildSettings(
        str(build.get("start_file", defaults.start_file)), str(build["name"]),
        bool(build.get("one_file", True)), bool(build.get("windowed", True)),
        str(build.get("icon", "")), [list(map(str, d)) for d in build.get("datas", [])],
        [str(h) for h in build.get("hidden_imports", [])], bool(build.get("self_test", False)),
        int(build.get("test_seconds", 10)), [str(b) for b in build.get("beside", [])])


def write_settings(code_dir: Path, settings: BuildSettings) -> None:
    data = read_config(code_dir)
    section = data.get(SECTION) if isinstance(data.get(SECTION), dict) else {}
    section["build"] = {"start_file": settings.start_file, "name": settings.name,
                        "one_file": settings.one_file, "windowed": settings.windowed,
                        "icon": settings.icon, "datas": settings.datas,
                        "hidden_imports": settings.hidden_imports,
                        "self_test": settings.self_test, "test_seconds": settings.test_seconds,
                        "beside": settings.beside}
    data[SECTION] = section
    write_config(code_dir, data)


def is_cockpit(project: Project) -> bool:
    return bool(read_config(project.code_dir).get("is_cockpit"))


def head_commit(code_dir: Path) -> str:
    if not git.is_repo(code_dir):
        return ""
    result = git.run(["rev-parse", "HEAD"], code_dir, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def current_exe(project: Project) -> Path | None:
    """Die Exe im Ordner Exe (auch in einem Programmordner), ohne die wartende."""
    if not project.has_exe_dir:
        return None
    found = [p for p in project.exe_dir.rglob("*.exe")
             if p.is_file() and PENDING not in p.relative_to(project.exe_dir).parts
             and not any(BRANCH_MARK in part for part in p.relative_to(project.exe_dir).parts)]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def _day(iso: str) -> str:
    try:
        return f"{datetime.fromisoformat(iso):%d.%m.%Y}"
    except ValueError:
        return ""


def status_line(project: Project, head: str | None = None) -> str:
    """Zeile im Projektbaum, das Wichtigste vorne (Konzept 10.4)."""
    exe = current_exe(project)
    record = read_record(project.code_dir) if project.folder_found else None
    if exe is None:
        if record is not None and record.pending:
            return "Exe, neue Version wartet auf den Neustart"
        return "Exe, noch keine Exe-Datei"
    if record is None:
        created = datetime.fromtimestamp(exe.stat().st_mtime)
        return f"Exe, {exe.name}, vom {created:%d.%m.%Y}, Herkunft unbekannt"
    parts = ["Exe"]
    if record.version:
        parts.append(f"Version {record.version}")
    parts.append(f"{SOURCES[record.source]} am {_day(record.date)}")
    if record.source == "cockpit" and record.commit:
        head = head_commit(project.code_dir) if head is None else head
        if head:
            parts.append("aktuell" if head == record.commit else "älter als der Code")
    if not record.tested:
        parts.append("nicht geprüft")
    if record.pending:
        parts.append("neue Version wartet auf den Neustart")
    return ", ".join(parts)


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# -- Exe-Ordner ----------------------------------------------------------------------------------
def add_exe_dir(project: Project) -> Path:
    """Ordner Exe anlegen (Aktion "Exe hinzufügen …")."""
    if project.exe_dir is None:
        raise CockpitError("Bei diesem verknüpften Projekt ist kein Exe-Ordner festgelegt.")
    project.exe_dir.mkdir(parents=True, exist_ok=True)
    return project.exe_dir


def backup_current(project: Project, reason: str, keep: tuple[str, ...] = ()) -> Path | None:
    """Inhalt des Ordners Exe (ohne _neu) in eine Sicherheitskopie verschieben. Klappt ein Teil
    nicht, kommt alles zurück, und es gibt einen Fehler (zum Beispiel weil die Exe läuft).
    keep: Ordner neben der Exe, die bleiben, wo sie sind (Phase 10g)."""
    items = [p for p in project.exe_dir.iterdir()
             if p.name != PENDING and not is_branch_exe(p)       # Branch-Exen bleiben (10f)
             and p.name not in keep]
    if not items:
        return None
    folder = backups.new_backup_dir(project.name, reason, project.exe_dir)
    moved: list[Path] = []
    try:
        for item in items:
            shutil.move(str(item), str(folder / item.name))
            moved.append(item)
    except OSError as exc:
        for item in moved:
            try:
                shutil.move(str(folder / item.name), str(item))
            except OSError:
                log.exception("Zurückverschieben fehlgeschlagen: %s", item)
        raise CockpitError(LOCKED, str(exc)) from None
    log.info("Exe gesichert: %s", folder)
    return folder


def _put(source: Path, target_dir: Path, move: bool) -> Path:
    target = target_dir / source.name
    if move:
        shutil.move(str(source), str(target))
    elif source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)
    return target


def adopt(project: Project, source: Path, kind: str = "extern", version: str = "",
          move: bool = False) -> Path:
    """Eine vorhandene Exe (Datei oder Programmordner) in den Ordner Exe übernehmen. Die
    bisherige kommt vorher in eine Sicherheitskopie."""
    if not source.exists():
        raise CockpitError(f"{source} gibt es nicht.")
    if source.is_file() and source.suffix.lower() != ".exe":
        raise CockpitError("Bitte eine Exe-Datei wählen.")
    if source.is_dir() and not any(source.rglob("*.exe")):
        raise CockpitError("In diesem Ordner liegt keine Exe-Datei.")
    exe_dir = add_exe_dir(project)
    if source.resolve().is_relative_to(exe_dir.resolve()):
        raise CockpitError("Diese Exe liegt schon im Ordner Exe.")
    names = beside_names(project)
    old_home = _home_of(project)
    backup = backup_current(project, "Exe ersetzt", tuple(names))
    try:
        target = _put(source, exe_dir, move)
    except OSError as exc:
        raise CockpitError("Die Exe ließ sich nicht übernehmen.", str(exc)) from None
    place_beside(project, names, exe_in(target).parent, backup, old_home)
    write_record(project.code_dir, ExeRecord(kind, now(), "", version))
    return target


# -- Ordner neben der Exe (Phase 10g) ------------------------------------------------------------
def beside_names(project: Project) -> list[str]:
    settings = read_settings(project.code_dir) if project.folder_found else None
    return list(settings.beside) if settings is not None else []


def _home_of(project: Project) -> Path | None:
    """Ordner der bisherigen Exe, relativ zum Ordner Exe ("." bei einer einzelnen Exe-Datei)."""
    current = current_exe(project)
    if current is None:
        return None
    return current.parent.relative_to(project.exe_dir)


def place_beside(project: Project, names: list[str], home: Path, backup: Path | None,
                 old_home: Path | None) -> list[str]:
    """Ordner neben die Exe legen. Ein vorhandener bleibt unverändert. Lag er bei der bisherigen
    Exe (jetzt in der Sicherheitskopie), kommt er von dort zurück, mit allem, was die Nutzer
    hinzugefügt haben. Sonst, beim ersten Mal, kommt er aus dem Ordner Code. Gibt die neu
    angelegten Namen zurück."""
    placed: list[str] = []
    for name in names:
        target = home / name
        if target.exists():
            continue
        previous = backup / old_home / name if backup is not None and old_home is not None \
            else None
        source = previous if previous is not None and previous.exists() else project.code_dir / name
        try:
            if source.is_dir():
                shutil.copytree(source, target)
            elif source.is_file():
                shutil.copy2(source, target)
            else:
                continue
        except OSError as exc:
            raise CockpitError(f"Der Ordner {name} ließ sich nicht neben die Exe legen.",
                               str(exc)) from None
        placed.append(name)
    return placed


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
    bekommt er eine eigene, damit main sauber bleibt."""
    main = project.code_dir
    code_dir = code_dir or main
    key = str(main.resolve()).lower()
    suffix = ""
    if code_dir.resolve() != main.resolve() and \
            _requirements_text(code_dir) != _requirements_text(main):
        key += "|" + code_dir.name.lower()
        suffix = "-b"
    name = re.sub(r"[^A-Za-z0-9_-]", "", project.name)[:20] or "Projekt"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]
    return paths.cache_dir() / "venvs" / f"{name}-{digest}{suffix}"


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


def _works(python: Path) -> bool:
    """Startet das Python der Umgebung? Nach einem Wechsel der Python-Version nicht mehr."""
    try:
        return subprocess.run([str(python), "-c", "pass"], capture_output=True, timeout=30,
                              creationflags=FLAGS).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def prepare_venv(code_dir: Path, on_line=None, cancel=None, venv: Path | None = None) -> Path:
    """Virtuelle Umgebung anlegen, requirements.txt und PyInstaller installieren. venv: Ort der
    Umgebung, sonst .venv im Ordner Code. Eine kaputte Umgebung wird neu angelegt."""
    from cockpit.core import long_paths, safety_check
    venv = venv or code_dir / ".venv"
    python = python_in(venv)
    env = _environment()
    if python.is_file() and not _works(python):
        shutil.rmtree(venv, ignore_errors=True)
    if not python.is_file():
        base = find_python()
        if base is None:
            raise CockpitError("Python wurde nicht gefunden. Zum Erstellen einer Exe braucht das "
                               "Cockpit Python. Die Anleitung steht im Menü Hilfe unter Python "
                               "installieren.")
        venv.parent.mkdir(parents=True, exist_ok=True)
        if run_process([*base, "-m", "venv", str(venv)], code_dir, on_line, cancel, env):
            raise CockpitError("Die virtuelle Umgebung ließ sich nicht anlegen.")
    if git.is_repo(code_dir) and venv.parent == code_dir:
        safety_check.ensure_gitignore(code_dir)          # .venv nie hochladen
    packages = ["pyinstaller"]
    args = [str(python), "-m", "pip", "install", "--quiet", "--progress-bar", "off"]
    if (code_dir / "requirements.txt").is_file():
        args += ["-r", "requirements.txt"]
    output: list[str] = []

    def line(text: str) -> None:
        output.append(text)
        if on_line is not None:
            on_line(text)

    if run_process(args + packages, code_dir, line, cancel, env):
        if long_paths.is_long_path_error("\n".join(output)):
            raise CockpitError(LONG_PATHS, "\n".join(output[-5:]))
        raise CockpitError("Die Bibliotheken ließen sich nicht installieren. Die Ausgabe nennt den "
                           "Grund.")
    return python


# -- .spec-Datei ---------------------------------------------------------------------------------
def spec_text(settings: BuildSettings) -> str:
    icon = repr(settings.icon) if settings.icon else "None"
    datas = [tuple(d) for d in settings.datas]
    head = (f"# Erstellt von CodeCockpit. Sie dürfen die Datei anpassen, das Cockpit nutzt sie\n"
            f"# bei jedem Bau weiter. Pfade sind relativ zum Ordner Code.\n\n"
            f"a = Analysis([{settings.start_file!r}], pathex=[], binaries=[], "
            f"datas={datas!r},\n"
            f"             hiddenimports={settings.hidden_imports!r}, excludes=[])\n"
            f"pyz = PYZ(a.pure)\n\n")
    if settings.one_file:
        return head + (f"exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], "
                       f"name={settings.name!r},\n"
                       f"          console={not settings.windowed!r}, icon={icon}, upx=False)\n")
    return head + (f"exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name={settings.name!r},\n"
                   f"          console={not settings.windowed!r}, icon={icon}, upx=False)\n"
                   f"coll = COLLECT(exe, a.binaries, a.datas, name={settings.name!r}, "
                   f"upx=False)\n")


def ensure_spec(code_dir: Path, settings: BuildSettings) -> Path:
    """Vorhandene .spec-Datei weiterverwenden, sonst eine neue schreiben."""
    path = code_dir / settings.spec_name
    if not path.is_file():
        path.write_text(spec_text(settings), encoding="utf-8")
    return path


def change_settings(code_dir: Path, project_name: str, settings: BuildSettings) -> Path | None:
    """Exe-Einstellungen ändern (Phase 10g). Die .spec-Datei wird neu geschrieben, wenn sich
    etwas darin ändert. Die alte kommt vorher in die Sicherheitskopien. Gibt diese zurück."""
    old = read_settings(code_dir)
    write_settings(code_dir, settings)
    backup = None
    if old is not None and (code_dir / old.spec_name).is_file():
        spec = code_dir / old.spec_name
        if spec.read_text(encoding="utf-8", errors="replace") != spec_text(settings) \
                or old.spec_name != settings.spec_name:
            backup = backups.new_backup_dir(project_name, "Exe-Einstellungen geändert", code_dir)
            shutil.copy2(spec, backup / spec.name)
            if old.spec_name != settings.spec_name:
                spec.unlink()
    (code_dir / settings.spec_name).write_text(spec_text(settings), encoding="utf-8")
    return backup


def spec_is_one_file(spec: Path) -> bool:
    return "COLLECT(" not in spec.read_text(encoding="utf-8", errors="replace")


# -- Bauen, testen, ersetzen ----------------------------------------------------------------------
STEPS = ("Virtuelle Umgebung und Bibliotheken werden vorbereitet", "Exe wird gebaut",
         "Exe wird getestet", "Exe wird übernommen")


@dataclass
class BuildResult:
    exe: Path                           # die übernommene (oder wartende) Exe
    pending: bool = False               # eigene Exe des Cockpits: wartet auf den Neustart
    backup: Path | None = None
    untested: bool = False              # Test blockiert: noch nicht übernommen, wartet auf Ja
    built: Path | None = None           # bei untested: die gebaute Exe im temporären Ordner
    work: Path | None = None            # bei untested: temporärer Ordner, danach löschen
    commit: str = ""
    branch: str = ""                    # Exe aus einem Branch-Ordner (Phase 10f): sein Name
    placed: list[str] = field(default_factory=list)   # neu neben die Exe gelegte Ordner (10g)


def pyinstaller_build(code_dir: Path, python: Path, spec: Path, work: Path, on_line=None,
                      cancel=None) -> Path:
    """Baut in work. Gibt die Exe-Datei oder den Programmordner zurück."""
    dist = work / "dist"
    code = run_process([str(python), "-m", "PyInstaller", "--noconfirm", "--clean",
                        "--distpath", str(dist), "--workpath", str(work / "build"), str(spec)],
                       code_dir, on_line, cancel, _environment())
    if code:
        raise CockpitError("PyInstaller hat die Exe nicht gebaut. Die Ausgabe nennt den Grund.",
                           f"Rückgabewert {code}")
    built = [p for p in dist.iterdir()] if dist.is_dir() else []
    if not built:
        raise CockpitError("PyInstaller hat keine Exe erzeugt.")
    return built[0]


def exe_in(built: Path) -> Path:
    if built.is_file():
        return built
    found = sorted(built.glob("*.exe"))
    if not found:
        raise CockpitError("Im gebauten Programmordner fehlt die Exe.")
    return found[0]


QUICK_EXIT = ("Die neue Exe hat sich gleich nach dem Start ohne Fenster beendet. Bei einem "
              "Programm mit Fenster ist das ein Fehler, meistens eine falsche Startdatei oder "
              "eine fehlende Bibliothek. „Exe aus dem Code erstellen …“ mit „Exe ohne KI einrichten …“ nennt mögliche Gründe. Die "
              "bisherige Exe bleibt.")


def start_test(exe: Path, seconds: int = 10, self_test: bool = False,
               cancel: threading.Event | None = None, windowed: bool = False) -> str:
    """Start-Test: läuft die Exe nach seconds noch, ist alles gut, dann wird sie beendet. Beendet
    sie sich vorher mit Fehler, ist der Test nicht bestanden. Mit self_test: --selbsttest und
    Rückgabewert 0 innerhalb einer Minute. Gibt einen Satz zum Ergebnis zurück, wirft
    CockpitError, wenn der Test nicht bestanden ist.
    windowed: Programm mit Fenster. Beendet es sich vorher, auch ohne Fehler, ist der Test nicht
    bestanden (Phase 10g: Die VokabelApp startete die Logik statt des Fensters)."""
    from cockpit.core.terminal import _kill_tree
    args = [str(exe), "--selbsttest"] if self_test else [str(exe)]
    try:
        process = subprocess.Popen(args, cwd=str(exe.parent), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        if is_blocked(exc):
            raise BlockedByWindows(BLOCKED + " Die bisherige Exe bleibt.", repr(exc)) from None
        raise CockpitError("Die neue Exe ließ sich nicht starten.", repr(exc)) from None
    limit = 60 if self_test else seconds
    deadline = time.monotonic() + limit
    try:
        while time.monotonic() < deadline:
            if cancel is not None and cancel.is_set():
                raise Cancelled()
            code = process.poll()
            if code is not None:
                if code == 0 and windowed and not self_test:
                    raise CockpitError(QUICK_EXIT)
                if code == 0:
                    return "Selbsttest bestanden." if self_test else \
                        "Start-Test bestanden, das Programm hat sich ohne Fehler beendet."
                raise CockpitError(f"Die neue Exe ist beim Test mit Fehler beendet worden "
                                   f"(Rückgabewert {code}). Die bisherige Exe bleibt.")
            time.sleep(0.25)
        if self_test:
            raise CockpitError("Der Selbsttest hat nach einer Minute nicht geantwortet. Die "
                               "bisherige Exe bleibt.")
        return f"Start-Test bestanden, das Programm lief {seconds} Sekunden ohne Absturz."
    finally:
        if process.poll() is None:
            _kill_tree(process)


def running_from(folder: Path) -> bool:
    """Läuft dieses Programm als Exe aus folder? (Nur dann ist die eigene Exe gesperrt.)"""
    if not getattr(sys, "frozen", False):
        return False
    try:
        return Path(sys.executable).resolve().is_relative_to(folder.resolve())
    except OSError:
        return False


def install(project: Project, built: Path, commit: str, tested: bool = True) -> BuildResult:
    """Getestete Exe übernehmen. Die eigene laufende Exe des Cockpits wartet in Exe\\_neu."""
    exe_dir = add_exe_dir(project)
    if is_cockpit(project) and running_from(exe_dir):
        pending = exe_dir / PENDING
        backups.remove_tree(pending)
        pending.mkdir()
        target = _put(built, pending, move=True)
        write_record(project.code_dir, ExeRecord("cockpit", now(), commit, pending=True,
                                                 tested=tested))
        return BuildResult(exe_in(target), pending=True)
    names = beside_names(project)
    old_home = _home_of(project)
    backup = backup_current(project, "Exe ersetzt", tuple(names))
    try:
        target = _put(built, exe_dir, move=True)
    except OSError as exc:
        raise CockpitError("Die neue Exe ließ sich nicht in den Ordner Exe verschieben. Die "
                           "bisherige steht in den Sicherheitskopien.", str(exc)) from None
    placed = place_beside(project, names, exe_in(target).parent, backup, old_home)
    write_record(project.code_dir, ExeRecord("cockpit", now(), commit, tested=tested))
    return BuildResult(exe_in(target), backup=backup, placed=placed)


def install_untested(project: Project, result: BuildResult) -> BuildResult:
    """Nach dem Ja des Nutzers: die nicht geprüfte Exe übernehmen (Wunsch aus Phase 10)."""
    try:
        if result.branch:
            return install_branch(project, result.built, result.branch)
        return install(project, result.built, result.commit, tested=False)
    finally:
        discard(result)


def branch_exe_name(settings: BuildSettings, folder: str, built: Path) -> str:
    """Zum Beispiel "CodeCockpit_branch_neue-funktion.exe" (Wunsch aus den Fragen zu 10f)."""
    return f"{settings.name}{BRANCH_MARK}{folder}" + (".exe" if built.is_file() else "")


def is_branch_exe(path: Path) -> bool:
    return BRANCH_MARK in path.name


def install_branch(project: Project, built: Path, folder: str,
                   settings: BuildSettings | None = None) -> BuildResult:
    """Exe aus einem Branch-Ordner neben die normale Exe legen. Die normale bleibt unberührt,
    eine ältere Exe desselben Branches kommt in die Sicherheitskopien. Kein Vermerk in
    cockpit.toml, der gilt nur für die Exe aus dem Haupt-Branch."""
    settings = settings or read_settings(project.code_dir) or BuildSettings("main.py",
                                                                           project.name)
    exe_dir = add_exe_dir(project)
    target = exe_dir / branch_exe_name(settings, folder, built)
    backup = None
    if target.exists():
        try:
            backup = backups.move_into_backup(target, project.name, f"Branch-Exe {folder} ersetzt")
        except OSError as exc:
            raise CockpitError(LOCKED, str(exc)) from None
    try:
        shutil.move(str(built), str(target))
    except OSError as exc:
        raise CockpitError("Die neue Exe ließ sich nicht in den Ordner Exe verschieben.",
                           str(exc)) from None
    return BuildResult(exe_in(target), backup=backup, branch=folder)


def discard(result: BuildResult) -> None:
    if result.work is not None:
        backups.remove_tree(result.work)


def build(project: Project, settings: BuildSettings, on_status: Callable[[str], None],
          on_line: Callable[[str], None], cancel: threading.Event | None = None,
          branch_dir: Path | None = None, branch_name: str = "") -> BuildResult:
    """Der ganze Ablauf, blockiert. on_status bekommt "Schritt 1 von 4: …".
    branch_dir: aus diesem Branch-Ordner bauen (Phase 10f). Die Exe heißt dann
    <Name>_branch_<Ordner>.exe und kommt neben die normale. branch_name ersetzt den Ordner im
    Namen, zum Beispiel wenn der Ordner Code selbst auf dem Branch steht."""
    code_dir = branch_dir or project.code_dir
    folder = (branch_name or branch_dir.name) if branch_dir is not None else ""

    def step(number: int) -> None:
        on_status(f"Schritt {number} von {len(STEPS)}: {STEPS[number - 1]}")

    commit = head_commit(code_dir)
    step(1)
    python = prepare_venv(code_dir, on_line, cancel, venv=build_venv(project, code_dir))
    spec = ensure_spec(code_dir, settings)
    work = Path(tempfile.mkdtemp(prefix="codecockpit-exe-", dir=paths.cache_dir()))
    keep = False
    try:
        step(2)
        built = pyinstaller_build(code_dir, python, spec, work, on_line, cancel)
        step(3)
        try:
            on_line(start_test(exe_in(built), settings.test_seconds, settings.self_test,
                               cancel, settings.windowed))
        except BlockedByWindows:
            # Der Nutzer entscheidet in der Oberfläche, ob er selbst prüft (install_untested)
            keep = True
            return BuildResult(exe_in(built), untested=True, built=built, work=work,
                               commit=commit, branch=folder)
        step(4)
        if folder:
            return install_branch(project, built, folder, settings)
        return install(project, built, commit)
    finally:
        if not keep:
            backups.remove_tree(work)


# -- Eigene Exe: Austausch beim Neustart ------------------------------------------------------------
def restart_script(project: Project) -> Path:
    """Startskript, das auf das Ende des Cockpits wartet, die wartende Exe übernimmt und sie
    startet. Die bisherige Exe kommt vorher in eine Sicherheitskopie."""
    exe_dir = project.exe_dir
    pending = exe_dir / PENDING
    new_items = list(pending.iterdir()) if pending.is_dir() else []
    if not new_items:
        raise CockpitError("Es wartet keine neue Version.")
    folder = backups.new_backup_dir(project.name, "Exe vor dem Neustart ersetzt", exe_dir)
    old_items = [p for p in exe_dir.iterdir() if p.name != PENDING]
    new_exe = exe_in(new_items[0])
    script = swap_script(exe_dir, old_items, new_items, folder,
                         exe_dir / new_exe.relative_to(pending))
    record = read_record(project.code_dir)
    if record is not None:
        record.pending = False
        write_record(project.code_dir, record)
    return script


def swap_script(exe_dir: Path, old_items: list[Path], new_items: list[Path], backup: Path,
                start: Path | None, pid: int | None = None) -> Path:
    """Skript, das auf das Ende des Cockpits wartet, old_items in die Sicherheitskopie backup
    verschiebt, new_items aus Exe\\_neu nach exe_dir holt und start startet (None: nicht starten).
    Genutzt vom Neustart nach dem Bauen und von der Selbst-Aktualisierung (update.py)."""
    pending = exe_dir / PENDING
    pid = pid or os.getpid()                  # auf das Ende dieses Prozesses warten
    # Befehle mit vollem Pfad (kein anderes find aus dem Suchpfad). Beim Test des Nutzers kam
    # das Skript nicht aus der Warteschleife, und die neue Exe blieb in Exe\_neu liegen.
    system = r"%SystemRoot%\System32"
    lines = ["@echo off", "chcp 65001 >nul", "set versuche=0",
             ":warten",
             f'"{system}\\tasklist.exe" /FI "PID eq {pid}" /NH | "{system}\\find.exe" '
             f'" {pid} " >nul',
             "if not errorlevel 1 (timeout /t 1 /nobreak >nul & goto warten)"]
    # Kurz nach dem Beenden kann Windows die alte Exe noch sperren: bis zu 30 Versuche
    moves = [(item, backup / item.name) for item in old_items] + \
            [(item, exe_dir / item.name) for item in new_items]
    for number, (source, target) in enumerate(moves, start=1):
        lines += [f":schieben{number}",
                  f'move /Y "{source}" "{target}" >nul 2>nul',
                  f"if not errorlevel 1 goto fertig{number}",
                  "set /a versuche+=1",
                  "if %versuche% geq 30 goto aufgeben",
                  "timeout /t 1 /nobreak >nul",
                  f"goto schieben{number}",
                  f":fertig{number}"]
    lines.append(f'rmdir /S /Q "{pending}"')
    if start is not None:
        lines.append(f'start "" "{start}"')
    lines.append('(goto) 2>nul & del "%~f0"')
    lines.append(":aufgeben")
    # Klappt das Tauschen nicht, startet wenigstens die bisherige Exe wieder, falls sie noch da ist
    if start is not None:
        lines.append(f'if exist "{start}" start "" "{start}"')
    lines.append('(goto) 2>nul & del "%~f0"')
    script = paths.cache_dir() / "cockpit-neustart.bat"
    script.parent.mkdir(parents=True, exist_ok=True)
    # Genau CR LF je Zeile. write_text hätte aus jedem \n noch einmal \r\n gemacht.
    script.write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))
    return script


def launch_restart(script: Path) -> None:
    """Skript unsichtbar starten. Ohne DETACHED_PROCESS: Damit bekam jeder Befehl im Skript ein
    eigenes Konsolenfenster, beim Test des Nutzers das leere Fenster "find". Die neue
    Prozessgruppe lässt das Skript weiterlaufen, wenn das Cockpit sich beendet."""
    subprocess.Popen(["cmd.exe", "/c", str(script)], close_fds=True,
                     creationflags=FLAGS | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))


# -- Versionen und Veröffentlichen ------------------------------------------------------------------
_VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def next_version(tags: list[str]) -> str:
    """Nach 1.3.0 kommt 1.3.1, ohne Release 1.0.0."""
    versions = sorted(tuple(int(x) for x in m.groups()) for m in map(_VERSION.match, tags) if m)
    if not versions:
        return "1.0.0"
    major, minor, patch = versions[-1]
    return f"{major}.{minor}.{patch + 1}"


def check_version(text: str, tags: list[str]) -> str:
    match = _VERSION.match(text.strip())
    if not match:
        raise CockpitError("Bitte eine Versionsnummer wie 1.0.0 eingeben.")
    version = ".".join(match.groups())
    if f"v{version}" in tags or version in tags:
        raise CockpitError(f"Die Version {version} gibt es schon.")
    return version


def asset_for_upload(project: Project, exe: Path, work: Path) -> Path:
    """Einzelne Exe direkt, Programmordner als ZIP-Datei. Gibt es Ordner neben der Exe (10g),
    kommen sie in die ZIP-Datei, und zwar so, wie sie im Ordner Code stehen, nicht mit den
    eigenen Daten aus dem Ordner Exe."""
    folder = exe.parent
    names = [n for n in beside_names(project) if (project.code_dir / n).exists()]
    one_file = folder.resolve() == project.exe_dir.resolve()
    if one_file and not names:
        return exe
    staging = work / (exe.stem if one_file else folder.name)
    if one_file:
        staging.mkdir(parents=True)
        shutil.copy2(exe, staging / exe.name)
    else:
        shutil.copytree(folder, staging, ignore=lambda _d, items: [
            i for i in items if _d == str(folder) and i in names])
    for name in names:
        source = project.code_dir / name
        if source.is_dir():
            shutil.copytree(source, staging / name)
        else:
            shutil.copy2(source, staging / name)
    archive = shutil.make_archive(str(staging), "zip", staging.parent, staging.name)
    return Path(archive)


def pick_asset(assets) -> object | None:
    """Exe-Datei bevorzugt, sonst eine ZIP-Datei."""
    for suffix in (".exe", ".zip"):
        for asset in assets:
            if asset.name.lower().endswith(suffix):
                return asset
    return None


def unpack(download: Path, work: Path) -> Path:
    """Heruntergeladene Datei: Exe direkt, ZIP-Datei entpackt (der Programmordner)."""
    if download.suffix.lower() == ".exe":
        return download
    target = work / download.stem
    shutil.unpack_archive(str(download), str(target))
    inner = [p for p in target.iterdir()]
    return inner[0] if len(inner) == 1 and inner[0].is_dir() else target
