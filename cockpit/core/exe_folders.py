"""Ordner der Exe im Ordner Release: anlegen, aufräumen, übernehmen, alte Versionen.

Dazu README, Lizenz und die Ordner neben der Exe (Phase 10g).
"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from cockpit.core import backups
from cockpit.core.errors import CockpitError
from cockpit.core.exe_state import (
    ExeRecord, KEEP_VERSIONS, LOCKED, PENDING, _version_of, current_exe, exe_in, folder_version,
    home_name, is_branch_exe, is_version_home, now, read_settings, running_from, write_record)
from cockpit.core.projects import Project

log = logging.getLogger(__name__)


def retire_home(home: Path) -> Path | None:
    """Den Ordner der bisherigen Version umbenennen in Name-vVersion, wenn sie veröffentlicht war
    (version.txt). Gibt den neuen Ordner zurück, sonst None (dann kommt er wie bisher in die
    Sicherheitskopien)."""
    version = folder_version(home) if home.is_dir() else ""
    if not version:
        return None
    target = home.parent / f"{home.name}-v{version}"
    if target.exists() or running_from(home):
        return None
    try:
        os.rename(home, target)
    except OSError as exc:
        log.warning("Ordner der bisherigen Version nicht umbenannt: %s (%s)", home, exc)
        return None
    return target


def prune_versions(release: Path, name: str, project_name: str,
                   keep: int = KEEP_VERSIONS) -> list[Path]:
    """Nur die neuesten keep Versionsordner von name behalten, ältere in die Sicherheitskopien.
    Ein Ordner, aus dem das Cockpit gerade läuft, bleibt. Gibt die verschobenen Ordner zurück."""
    if not release.is_dir():
        return []
    folders = sorted((p for p in release.iterdir() if is_version_home(p)
                      and p.name.lower().startswith(f"{name.lower()}-v")),
                     key=_version_of, reverse=True)
    moved: list[Path] = []
    for folder in folders[keep:]:
        if running_from(folder):
            continue
        try:
            backup = backups.new_backup_dir(project_name, f"Alte Version {folder.name}", release)
            shutil.move(str(folder), str(backup / folder.name))
            moved.append(folder)
        except OSError as exc:
            log.warning("Alte Version nicht verschoben: %s (%s)", folder, exc)
    return moved


# -- Exe-Ordner ----------------------------------------------------------------------------------
def add_exe_dir(project: Project) -> Path:
    """Ordner Release anlegen (Aktion "Exe hinzufügen …")."""
    if project.exe_dir is None:
        raise CockpitError("Bei diesem verknüpften Projekt ist kein Exe-Ordner festgelegt.")
    project.exe_dir.mkdir(parents=True, exist_ok=True)
    return project.exe_dir


def loose_items(project: Project) -> list[Path]:
    """Liegt eine Exe direkt im Ordner Release (alter Aufbau oder von Hand hineinkopiert), alles,
    was zu ihr gehört: alles außer _neu, Branch-Exen, Versionen und dem Ordner der normalen Exe.
    Sonst leer."""
    if not project.has_exe_dir:
        return []
    items = list(project.exe_dir.iterdir())
    if not any(p.is_file() and p.suffix.lower() == ".exe" for p in items):
        return []
    home = home_name(project).lower()
    return sorted((p for p in items if p.name != PENDING and not is_branch_exe(p)
                   and not is_version_home(p) and p.name.lower() != home
                   and p.name.lower() != "desktop.ini"), key=lambda p: p.name.lower())


def tidy_release(project: Project) -> Path:
    """Die lose Exe mit allem, was dazugehört, in den Ordner der normalen Exe verschieben, also
    nach "Exe-main" (Wunsch des Nutzers vom 14.10.2026). Nur der Ort ändert sich. Klappt ein Teil
    nicht, kommt alles zurück."""
    items = loose_items(project)
    home = project.exe_dir / home_name(project)
    if not items:
        return home
    if home.exists():
        raise CockpitError(f"Den Ordner {home.name} gibt es schon.")
    home.mkdir()
    moved: list[Path] = []
    try:
        for item in items:
            os.rename(item, home / item.name)
            moved.append(item)
    except OSError as exc:
        for item in moved:
            try:
                os.rename(home / item.name, item)
            except OSError:
                log.exception("Zurückverschieben fehlgeschlagen: %s", item)
        try:
            home.rmdir()
        except OSError:
            pass
        raise CockpitError(LOCKED, str(exc)) from None
    return home


def backup_current(project: Project, reason: str, keep: tuple[str, ...] = ()) -> Path | None:
    """Inhalt des Ordners Exe (ohne _neu) in eine Sicherheitskopie verschieben. Klappt ein Teil
    nicht, kommt alles zurück, und es gibt einen Fehler (zum Beispiel weil die Exe läuft).
    keep: Ordner neben der Exe, die bleiben, wo sie sind (Phase 10g)."""
    items = [p for p in project.exe_dir.iterdir()
             if p.name != PENDING and not is_branch_exe(p)       # Branch-Exen bleiben (10f)
             and not is_version_home(p)                          # Versionen bleiben (04.10.2026)
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
    """Eine vorhandene Exe (Datei oder Programmordner) in den Ordner Release übernehmen. Die
    bisherige kommt vorher in eine Sicherheitskopie."""
    if not source.exists():
        raise CockpitError(f"{source} gibt es nicht.")
    if source.is_file() and source.suffix.lower() != ".exe":
        raise CockpitError("Bitte eine Exe-Datei wählen.")
    if source.is_dir() and not any(source.rglob("*.exe")):
        raise CockpitError("In diesem Ordner liegt keine Exe-Datei.")
    exe_dir = add_exe_dir(project)
    if source.resolve().is_relative_to(exe_dir.resolve()):
        raise CockpitError("Diese Exe liegt schon im Ordner Release.")
    names = beside_names(project)
    home = exe_dir / home_name(project, source)
    old_home, backup = _make_room(project, home)
    try:
        target = _into_home(source, home, move)
    except OSError as exc:
        raise CockpitError("Die Exe ließ sich nicht übernehmen.", str(exc)) from None
    place_beside(project, names, home, _previous(project, backup, old_home), old_home)
    write_record(project.code_dir, ExeRecord(kind, now(), "", version))
    prune_versions(exe_dir, home.name, project.name)
    return target


def _previous(project: Project, backup: Path | None, old_home: Path | None) -> Path | None:
    """Wo die Daten der bisherigen Exe jetzt liegen: in der Sicherheitskopie, oder noch im
    Ordner Release, wenn es ein Ordner einer veröffentlichten Version ist (der bleibt liegen)."""
    if old_home is None:
        return backup
    if backup is not None and (backup / old_home).exists():
        return backup
    return project.exe_dir


def _into_home(built: Path, home: Path, move: bool = True) -> Path:
    """Exe-Datei oder Programmordner als eigenen Ordner home ablegen. Gibt die Exe zurück."""
    if built.is_file():
        home.mkdir(parents=True)
        _put(built, home, move)
    elif move:
        shutil.move(str(built), str(home))
    else:
        shutil.copytree(built, home)
    return exe_in(home)


# -- Ordner neben der Exe (Phase 10g) ------------------------------------------------------------
def beside_names(project: Project, code_dir: Path | None = None) -> list[str]:
    """Was neben die Exe kommt: die gewählten Ordner und Dateien, dazu immer README und Lizenz
    (Wunsch des Nutzers vom 03.10.2026)."""
    code_dir = code_dir or project.code_dir
    settings = read_settings(code_dir) if code_dir.is_dir() else None
    names = list(settings.beside) if settings is not None else []
    return names + [n for n in doc_files(code_dir) if n not in names]


def is_doc(name: str) -> bool:
    """README oder Lizenz: README.md, readme.txt, README.de.md, LICENSE, LICENSE.md ..."""
    lower = Path(name).name.lower()
    return lower.startswith("readme") or lower.split(".")[0] in ("license", "licence", "copying")


def doc_files(code_dir: Path) -> list[str]:
    """README- und Lizenzdateien im Ordner Repository."""
    try:
        return sorted(p.name for p in code_dir.iterdir()
                      if p.is_file() and is_doc(p.name)
                      and p.suffix.lower() in ("", ".md", ".txt", ".rst"))
    except OSError:
        return []


def _home_of(project: Project) -> Path | None:
    """Ordner der bisherigen Exe, relativ zum Ordner Release ("." bei einer einzelnen Exe-Datei)."""
    current = current_exe(project)
    if current is None:
        return None
    return current.parent.relative_to(project.exe_dir)


def place_beside(project: Project, names: list[str], home: Path, backup: Path | None,
                 old_home: Path | None, source_dir: Path | None = None) -> list[str]:
    """Ordner neben die Exe legen. Ein vorhandener bleibt unverändert. Lag er bei der bisherigen
    Exe (jetzt in der Sicherheitskopie), kommt er von dort zurück, mit allem, was die Nutzer
    hinzugefügt haben. Sonst, beim ersten Mal, kommt er aus dem Ordner Repository (source_dir, sonst
    der Ordner Repository des Projekts). Gibt es ihn dort nicht, wird er leer angelegt (Wunsch des
    Nutzers, 02.10.2026). Gibt die neu angelegten oder gefüllten Namen zurück.
    Ein leerer Ordner zählt nicht als vorhanden: Die Exe legt ihn beim Start-Test oft selbst an,
    dann würden die Dateien aus dem Code fehlen (Rückmeldung vom 02.10.2026, Meine-Vokabeln war
    leer). Er wird gefüllt, aus der bisherigen Exe oder aus dem Ordner Repository."""
    placed: list[str] = []
    source_dir = source_dir or project.code_dir
    for name in names:
        target = home / name
        if is_doc(name) and (source_dir / name).is_file():
            # Wunsch des Nutzers (02.10.2026): Die README ist immer die aktuelle aus dem Code,
            # seit dem 03.10.2026 auch die Lizenz
            if _refresh_file(project, source_dir / name, target):
                placed.append(name)
            continue
        if target.exists() and not _empty_dir(target):
            continue
        previous = backup / old_home / name if backup is not None and old_home is not None \
            else None
        source = previous if previous is not None and previous.exists() \
            and not _empty_dir(previous) else source_dir / name
        if target.exists():                           # leerer Ordner: nur füllen
            if source.is_dir() and not _empty_dir(source):
                try:
                    shutil.copytree(source, target, dirs_exist_ok=True)
                except OSError as exc:
                    raise CockpitError(f"Der Ordner {name} ließ sich nicht neben der Exe "
                                       "füllen.", str(exc)) from None
                placed.append(name)
            continue
        try:
            if source.is_dir():
                shutil.copytree(source, target)
            elif source.is_file():
                shutil.copy2(source, target)
            elif not Path(name).suffix:
                target.mkdir(parents=True)            # leerer Ordner, den der Code füllt
            else:
                continue
        except OSError as exc:
            raise CockpitError(f"Der Ordner {name} ließ sich nicht neben die Exe legen.",
                               str(exc)) from None
        placed.append(name)
    return placed


def is_readme(name: str) -> bool:
    """README, README.md, readme.txt, README.de.md ..."""
    return Path(name).name.lower().startswith("readme")


def release_docs(project: Project) -> list[Path]:
    """README und Lizenz, die beim Veröffentlichen zusätzlich einzeln am Release hängen."""
    return [project.code_dir / n for n in doc_files(project.code_dir)]


def missing_docs(code_dir: Path) -> list[str]:
    """Was vor dem Bauen und Veröffentlichen fehlt: "README", "Lizenz" oder beides."""
    names = doc_files(code_dir)
    missing = []
    if not any(n.lower().startswith("readme") for n in names):
        missing.append("README")
    if not any(not n.lower().startswith("readme") for n in names):
        missing.append("Lizenz")
    return missing


def _refresh_file(project: Project, source: Path, target: Path) -> bool:
    """Datei neben der Exe durch die aus dem Code ersetzen. Ist die bisherige anders, kommt sie
    vorher in die Sicherheitskopien. Gibt True zurück, wenn sich etwas geändert hat."""
    try:
        if target.is_file():
            if target.read_bytes() == source.read_bytes():
                return False
            backups.move_into_backup(target, project.name, f"{target.name} neben der Exe ersetzt")
        shutil.copy2(source, target)
    except OSError as exc:
        raise CockpitError(f"{source.name} ließ sich nicht neben die Exe legen.",
                           str(exc)) from None
    return True


def _empty_dir(path: Path) -> bool:
    try:
        return path.is_dir() and not any(path.iterdir())
    except OSError:
        return False


def _make_room(project: Project, home: Path, reason: str = "Exe ersetzt"
               ) -> tuple[Path | None, Path | None]:
    """Platz für die neue Exe im festen Ordner home. War die bisherige veröffentlicht, heißt ihr
    Ordner danach Name-vVersion, sonst kommt sie in die Sicherheitskopien. Gibt den Ort der
    bisherigen Exe relativ zu Release (für ihre Daten) und die Sicherheitskopie zurück."""
    old_home = _home_of(project)
    retired = retire_home(home)
    if retired is not None:
        old_home = Path(retired.name)
    return old_home, backup_current(project, reason)
