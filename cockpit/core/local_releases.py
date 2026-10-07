"""Die Releases eines Projekts auf dem Rechner (Wunsch des Nutzers vom 06.10.2026).

Unter der Zeile Releases steht je Branch ein Release, zum Beispiel "Exe-main" und
"Exe-neue-funktion". Auf dem Rechner ist das je ein Ordner im Ordner Release: die normale Exe aus dem
Haupt-Branch und daneben die Ordner <Name>_branch_<Ordner> (Phase 10f). Ein Release für einen
Branch gibt es nur für Branches, die lokal auf dem Rechner sind.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from cockpit.core import backups, exe
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project

MAIN = ""                                   # Schlüssel des Releases aus dem Haupt-Branch


@dataclass(frozen=True)
class LocalRelease:
    folder: str                             # MAIN beim Haupt-Branch, sonst der Branch-Ordner
    path: Path                              # Ordner des Releases, beim Haupt-Branch evtl. noch leer

    @property
    def is_main(self) -> bool:
        return self.folder == MAIN

    def title(self, main: str = "main") -> str:
        """Zum Beispiel "Exe-main" oder "Exe-neue-funktion"."""
        return f"Exe-{main if self.is_main else self.folder}"


def main_name(project: Project, status=None) -> str:
    """Name des Haupt-Branches, zum Beispiel "main" oder "master"."""
    repo = getattr(status, "repo", None)
    if repo is not None and getattr(repo, "default_branch", ""):
        return repo.default_branch
    return project.code_dir.name if project.has_branch_folders else "main"


def main_release(project: Project) -> LocalRelease:
    """Ordner der normalen Exe. Bei der alten Ablage ohne eigenen Ordner der Ordner Release."""
    current = exe.current_exe(project)
    if current is not None:
        home = current.parent
        while home.parent != project.exe_dir and home != project.exe_dir:
            home = home.parent                  # Exe in einem Unterordner des Programmordners
        return LocalRelease(MAIN, home)
    return LocalRelease(MAIN, project.exe_dir / exe.home_name(project))


def branch_releases(project: Project) -> list[LocalRelease]:
    if not project.has_exe_dir:
        return []
    found = [p for p in project.exe_dir.iterdir() if p.is_dir() and exe.is_branch_exe(p)]
    return [LocalRelease(p.name.split(exe.BRANCH_MARK, 1)[1], p)
            for p in sorted(found, key=lambda p: p.name.lower())]


def all_releases(project: Project) -> list[LocalRelease]:
    """Das Release aus dem Haupt-Branch immer zuerst."""
    if not project.has_exe_dir:
        return []
    return [main_release(project), *branch_releases(project)]


def find(project: Project, folder: str) -> LocalRelease | None:
    return next((r for r in all_releases(project) if r.folder == folder), None)


def release_exe(release: LocalRelease) -> Path | None:
    if not release.path.is_dir():
        return None
    found = [p for p in release.path.rglob("*.exe") if p.is_file()]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def _day(timestamp: float) -> str:
    return f"{datetime.fromtimestamp(timestamp):%d.%m.%Y}"


def published_version(project: Project, release: LocalRelease) -> str:
    """Zuletzt veröffentlichte Version, leer wenn noch nie."""
    if release.is_main:
        record = exe.read_record(project.code_dir) if project.folder_found else None
        return record.version if record is not None and record.version else ""
    path = release.path / exe.VERSION_FILE
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


def published_line(project: Project, release: LocalRelease) -> str:
    """Zum Beispiel "zuletzt Version 1.2.0 am 04.10.2026" oder "noch nicht veröffentlicht"."""
    version = published_version(project, release)
    if not version:
        return "noch nicht veröffentlicht"
    candidates = [release.path / exe.VERSION_FILE]
    if release.is_main:
        candidates.insert(0, project.exe_dir / f"{exe.home_name(project)}-v{version}"
                          / exe.VERSION_FILE)
    stamp = next((p for p in candidates if p.is_file()), None)
    when = f" am {_day(stamp.stat().st_mtime)}" if stamp is not None else ""
    return f"zuletzt Version {version}{when}"


def line(project: Project, release: LocalRelease, main: str = "main") -> str:
    """Zeile in der Liste, das Wichtigste vorne."""
    if release.is_main:
        status = exe.status_line(project)
        return release.title(main) + status.removeprefix("Exe")
    built = release_exe(release)
    if built is None:
        return f"{release.title(main)}, noch keine Exe-Datei"
    return f"{release.title(main)}, vom {_day(built.stat().st_mtime)}"


def releases_line(project: Project) -> str:
    """Zeile Releases, zum Beispiel "Releases, 2 Releases"."""
    from cockpit.core.text import count
    size = len(all_releases(project))
    return f"Releases, {count(size, 'Release', 'Releases')}"


def create_branch_release(project: Project, folder: str) -> Path:
    """Leeren Release-Ordner für einen lokalen Branch anlegen."""
    exe_dir = exe.add_exe_dir(project)
    path = exe_dir / exe.branch_exe_name(exe.home_name(project), folder)
    if path.exists():
        raise CockpitError(f"Das Release Exe-{folder} gibt es schon.")
    path.mkdir()
    return path


def remove_local(project: Project, release: LocalRelease, main: str = "main") -> Path | None:
    """Release-Ordner in die Sicherheitskopien verschieben. Bei der alten Ablage ohne eigenen
    Ordner nur die Exe-Datei. None, wenn es lokal nichts gibt."""
    reason = f"Release {release.title(main)} entfernt"
    if release.path.resolve() == project.exe_dir.resolve():
        current = exe.current_exe(project)
        source = current
    else:
        source = release.path if release.path.exists() else None
    if source is None:
        return None
    try:
        return backups.move_into_backup(source, project.name, reason)
    except OSError as exc:
        raise CockpitError(exe.LOCKED, str(exc)) from None


def remote_release(project: Project, release: LocalRelease, published: list):
    """Das Release auf der Plattform zur zuletzt veröffentlichten Version, sonst None."""
    version = published_version(project, release)
    if not version:
        return None
    tag = f"v{version}" if release.is_main else f"v{version}-{release.folder}"
    return next((r for r in published if r.tag in (tag, tag[1:])), None)
