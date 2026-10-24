"""Zustand der Exe eines Projekts: Herkunft, Einstellungen zum Bauen, Zeile im Projektbaum.

Die Grundsätze stehen in exe.py.
"""
from __future__ import annotations

import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from cockpit.core import git
from cockpit.core.errors import CockpitError
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


BLOCKED_WORDS = ("blockiert", "blocked", "app-steuerung", "app control", "anwendungssteuerung")


def looks_blocked(text: str) -> bool:
    """Meldet das Fenster der Exe, dass Windows sie oder einen Teil davon blockiert?"""
    lowered = text.lower()
    return any(word in lowered for word in BLOCKED_WORDS)


LOCKED = ("Die bisherige Exe lässt sich nicht verschieben. Läuft sie gerade? Bitte schließen Sie "
          "das Programm und versuchen Sie es noch einmal.")


# -- Zustand ------------------------------------------------------------------------------------
@dataclass
class ExeRecord:
    source: str                         # "cockpit", "extern" oder "release"
    date: str                           # ISO, zum Beispiel "2026-09-27T16:00:00"
    commit: str = ""                    # nur bei "cockpit": Stand des Codes beim Bau
    version: str = ""                   # bei "release" und nach dem Veröffentlichen
    pending: bool = False               # wartet in Release\_neu auf den Neustart
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
    # Bau kommen sie aus dem Ordner Repository dorthin, danach bleiben sie, wie die Nutzer sie haben.
    beside: list[str] = field(default_factory=list)
    python: str = ""                    # "3.13" oder leer für automatisch (20.10.2026)

    @property
    def spec_name(self) -> str:
        return f"{self.name}.spec"


RECORD_FILE = "codecockpit-exe.toml"


VERSION_FILE = "version.txt"            # neben der Exe: veröffentlichte Version (04.10.2026)


_VERSION_HOME = re.compile(r"-v\d+\.\d+\.\d+$")


def is_version_home(path: Path) -> bool:
    """Ordner einer veröffentlichten Version, zum Beispiel VokabelApp-v1.2.0."""
    return path.is_dir() and bool(_VERSION_HOME.search(path.name))


# Wunsch des Nutzers vom 20.10.2026: Die aktuelle Version liegt immer im festen Ordner, zum
# Beispiel Release\CodeCockpit. Wird sie ersetzt und war sie veröffentlicht, heißt ihr Ordner
# danach Name-vVersion. Die letzten KEEP_VERSIONS alten Versionen bleiben daneben, ältere kommen
# in die Sicherheitskopien. Vorher hieß der Ordner schon beim Veröffentlichen Name-vVersion, und
# im Ordner Release lagen am Ende nur noch Versionsordner.
KEEP_VERSIONS = 2


def _version_of(path: Path) -> tuple[int, ...]:
    match = re.search(r"-v(\d+)\.(\d+)\.(\d+)$", path.name)
    return tuple(int(x) for x in match.groups()) if match else ()


def folder_version(folder: Path) -> str:
    """Veröffentlichte Version aus version.txt im Ordner, sonst leer."""
    try:
        text = (folder / VERSION_FILE).read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return text if re.fullmatch(r"\d+\.\d+\.\d+", text) else ""


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
        int(build.get("test_seconds", 10)), [str(b) for b in build.get("beside", [])],
        str(build.get("python", "")))


def write_settings(code_dir: Path, settings: BuildSettings) -> None:
    data = read_config(code_dir)
    section = data.get(SECTION) if isinstance(data.get(SECTION), dict) else {}
    section["build"] = {"start_file": settings.start_file, "name": settings.name,
                        "one_file": settings.one_file, "windowed": settings.windowed,
                        "icon": settings.icon, "datas": settings.datas,
                        "hidden_imports": settings.hidden_imports,
                        "self_test": settings.self_test, "test_seconds": settings.test_seconds,
                        "beside": settings.beside}
    if settings.python:
        section["build"]["python"] = settings.python
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
    """Die Exe im Ordner Release (auch in einem Programmordner), ohne die wartende."""
    if not project.has_exe_dir:
        return None
    found = [p for p in project.exe_dir.rglob("*.exe")
             if p.is_file() and PENDING not in p.relative_to(project.exe_dir).parts
             and not any(BRANCH_MARK in part for part in p.relative_to(project.exe_dir).parts)]
    # Die im festen Ordner gilt, alte Versionen daneben nicht (20.10.2026)
    home = (project.exe_dir / home_name(project)).resolve()
    fixed = [p for p in found if p.parent.resolve() == home]
    return max(fixed or found, key=lambda p: p.stat().st_mtime) if found else None


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


def build_state(project: Project) -> str:
    """Kurzer Stand für "Exe aus dem Code erstellen …" (Wunsch des Nutzers, 02.10.2026)."""
    if current_exe(project) is None:
        return "noch keine Exe"
    record = read_record(project.code_dir) if project.folder_found else None
    if record is None or record.source != "cockpit" or not record.commit:
        return ""
    head = head_commit(project.code_dir)
    if not head:
        return ""
    return "Exe aktuell" if head == record.commit else "Code geändert seit dem letzten Bau"


def publish_state(project: Project) -> str:
    """Kurzer Stand für "Exe veröffentlichen …"."""
    record = read_record(project.code_dir) if project.folder_found else None
    if record is not None and record.version:
        return f"zuletzt Version {record.version}"
    return "noch nicht veröffentlicht"


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def home_name(project: Project, source: Path | None = None) -> str:
    """Name des eigenen Ordners der Exe: der Name aus den Exe-Einstellungen, sonst der Name der
    gewählten Exe ohne Versionsnummer (VokabelApp-1.2.0 wird VokabelApp)."""
    settings = read_settings(project.code_dir) if project.folder_found else None
    if settings is not None and settings.name:
        return settings.name
    if source is not None:
        name = source.stem if source.is_file() else source.name
        return re.sub(r"-v?\d+\.\d+\.\d+$", "", name) or name
    return project.name.replace(" ", "-")


def exe_in(built: Path) -> Path:
    if built.is_file():
        return built
    found = sorted(built.glob("*.exe"))
    if not found:
        raise CockpitError("Im gebauten Programmordner fehlt die Exe.")
    return found[0]


def running_from(folder: Path) -> bool:
    """Läuft dieses Programm als Exe aus folder? (Nur dann ist die eigene Exe gesperrt.)"""
    if not getattr(sys, "frozen", False):
        return False
    try:
        return Path(sys.executable).resolve().is_relative_to(folder.resolve())
    except OSError:
        return False


def branch_exe_name(name: str, folder: str) -> str:
    """Ordner der Exe aus einem Branch, zum Beispiel "CodeCockpit_branch_neue-funktion" (Wunsch
    aus den Fragen zu 10f, seit dem 03.10.2026 immer ein Ordner)."""
    return f"{name}{BRANCH_MARK}{folder}"


def is_branch_exe(path: Path) -> bool:
    return BRANCH_MARK in path.name
