"""Alle Quellen der Paketübersicht an einer Stelle: laden, prüfen, ändern.

Laden ist schnell und kommt zuerst. Ob etwas veraltet ist, prüft check() danach im Hintergrund,
das braucht das Internet. Jede Änderung kommt vorher in den Verlauf (record.py).
"""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass

from cockpit.core.errors import CockpitError
from cockpit.features.packages import choco_source, models, pip_source, record, winget_source
from cockpit.features.packages.base import (CHOCO, MODEL, PIP, SOURCE_NAMES, SOURCES, WINGET,
                                        Package, size_text)
from cockpit.core.text import count

log = logging.getLogger(__name__)


@dataclass
class SourceInfo:
    source: str
    available: bool
    reason: str = ""                     # warum nicht verfügbar

    @property
    def name(self) -> str:
        return SOURCE_NAMES[self.source]


def sources() -> list[SourceInfo]:
    from cockpit.features.packages import runner
    found = []
    for source in SOURCES:
        if source == WINGET and not winget_source.available():
            found.append(SourceInfo(source, False, "winget ist nicht installiert"))
        elif source == CHOCO and not choco_source.available():
            found.append(SourceInfo(source, False, "Chocolatey ist nicht installiert"))
        elif source == PIP and runner.find("py") is None and runner.find("python") is None:
            found.append(SourceInfo(source, False, "Python ist nicht installiert"))
        else:
            found.append(SourceInfo(source, True))
    return found


def load(source: str, projects, database, cancel: threading.Event | None = None
         ) -> list[Package]:
    if source == PIP:
        packages = []
        for env in pip_source.environments(projects):
            if cancel is not None and cancel.is_set():
                break
            packages += pip_source.list_packages(env, cancel)
        record.mark_pins(database, packages)
        return packages
    if source == WINGET:
        return winget_source.list_packages(cancel)
    if source == CHOCO:
        return choco_source.list_packages(cancel)
    if source == MODEL:
        return models.all_models(record.scan_folders(database))
    raise CockpitError(f"Unbekannte Quelle {source}.")


def check(source: str, packages: list[Package], projects,
          cancel: threading.Event | None = None) -> None:
    """Veraltet oder aktuell. Ändert die Pakete selbst."""
    if source == PIP:
        by_env = defaultdict(list)
        for package in packages:
            by_env[str(package.location)].append(package)
        for env in pip_source.environments(projects):
            if cancel is not None and cancel.is_set():
                return
            if str(env.python) in by_env:
                pip_source.check_outdated(env, by_env[str(env.python)], cancel)
        from cockpit.features.packages import osv           # Stufe 3: bekannte Sicherheitslücken
        osv.mark(packages)
    elif source == CHOCO:
        choco_source.check_outdated(packages, cancel)
    elif source == MODEL:
        models.check(packages)
    # winget liefert die verfügbare Version schon beim Laden


def summary(source: str, packages: list[Package]) -> str:
    """Zeile in der Liste der Quellen: Name, Anzahl, veraltete, Größe."""
    parts = [SOURCE_NAMES[source], count(len(packages), "Eintrag", "Einträge")]
    old = sum(1 for p in packages if p.outdated)
    if any(p.checked for p in packages):
        parts.append(f"{old} veraltet" if old else "alles aktuell")
    sizes = [p.size for p in packages if p.size]
    if sizes:
        parts.append(size_text(sum(sizes)))
    return ", ".join(parts)


def space_line(by_source: dict[str, list[Package]]) -> str:
    """Oberste Zeile: wie viel Platz wo liegt, zum Beispiel "Modelle: 38 GB, davon Cockpit:
    3 GB" (Wunsch des Nutzers vom 21.10.2026)."""
    from cockpit.features.packages.base import for_cockpit
    names = {PIP: "Bibliotheken", WINGET: "winget", CHOCO: "Chocolatey", MODEL: "Modelle"}
    parts = []
    for source in SOURCES:
        packages = by_source.get(source)
        if not packages:
            continue
        total = sum(p.size or 0 for p in packages)
        own = sum(p.size or 0 for p in packages if for_cockpit(p))
        if total:
            text = f"{names[source]}: {size_text(total)}"
            if own:
                text += f", davon Cockpit: {size_text(own)}"
            parts.append(text)
    return "Speicherplatz: " + ("; ".join(parts) if parts else "noch nicht ermittelt")


# -- Ändern -------------------------------------------------------------------------------------
def _module(package: Package):
    return {PIP: pip_source, WINGET: winget_source, CHOCO: choco_source}.get(package.source)


def can_choose_version(package: Package) -> bool:
    return package.source in (PIP, WINGET, CHOCO) or package.kind in (models.HF, models.OLLAMA)


def can_update(package: Package) -> bool:
    return package.source != MODEL or package.kind in (models.HF, models.OLLAMA)


def can_pin(package: Package) -> bool:
    return package.source in (PIP, WINGET, CHOCO)


def upgrade(database, package: Package, keep_old: bool = True, cancel=None, on_line=None) -> str:
    """Auf die neueste Version. Gibt eine kurze Meldung zurück."""
    if package.source == MODEL:
        if package.kind == models.HF:
            models.hf_download(package.id, None, cancel)
            record.remember(database, package, package.latest or "neueste")
            return (f"Neue Fassung von {package.name} geladen. Die bisherige bleibt, bis Sie "
                    "„Alte Fassungen entfernen“ wählen.")
        if package.kind == models.OLLAMA:
            kept = models.ollama_update(package, keep_old, cancel, on_line)
            record.remember(database, package, "neueste")
            return f"{package.name} aktualisiert." + (f" Die bisherige heißt {kept}." if kept
                                                     else "")
        raise CockpitError(f"{package.name} lässt sich hier nicht aktualisieren.")
    _module(package).upgrade(package, cancel, on_line)
    record.remember(database, package, package.latest or "neueste")
    return f"{package.name} aktualisiert."


def install_version(database, package: Package, version: str, cancel=None, on_line=None) -> str:
    if package.source == MODEL:
        if package.kind == models.HF:
            models.hf_download(package.id, version, cancel)
            record.remember(database, package, version)
            return f"Fassung {version} von {package.name} geladen. Die bisherige bleibt."
        if package.kind == models.OLLAMA:
            name = package.id.rsplit(":", 1)[0] + ":" + version
            models.ollama_pull(name, cancel, on_line)
            return f"{name} geladen. {package.name} bleibt."
        raise CockpitError(f"Bei {package.name} lässt sich keine Fassung wählen.")
    _module(package).install_version(package, version, cancel, on_line)
    record.remember(database, package, version)
    return f"{package.name} hat jetzt Version {version}."


def versions(package: Package, cancel=None) -> list[str]:
    if package.source == PIP:
        return pip_source.versions(package.id)
    if package.source in (WINGET, CHOCO):
        return _module(package).versions(package, cancel)
    return []                            # Modelle: Fassung oder Tag selbst eingeben


def uninstall(database, packages: list[Package], cancel=None, on_line=None) -> str:
    """Löschen. Vorher kommt die Liste in die Sicherheitskopien. Gibt eine Meldung zurück."""
    record.save_list(packages, "vor dem Löschen")
    done, failed = [], []
    for package in packages:
        try:
            if package.source == MODEL:
                models.delete(package, cancel)
            else:
                _module(package).uninstall(package, cancel, on_line)
            record.remember(database, package, "")
            done.append(package.name)
        except CockpitError as exc:
            log.warning("Löschen von %s: %s", package.name, exc.message)
            failed.append(f"{package.name}: {exc.message}")
    text = f"{count(len(done), 'Eintrag', 'Einträge')} gelöscht."
    if failed:
        raise CockpitError(text + " Nicht gelöscht: " + "; ".join(failed[:5]),
                           "\n".join(failed))
    return text + " Die Liste zum Wiederherstellen steht in den Sicherheitskopien."


def set_pinned(database, package: Package, on: bool, cancel=None) -> str:
    if package.source == WINGET:
        winget_source.pin(package, on, cancel)
    elif package.source == CHOCO:
        choco_source.pin(package, on, cancel)
    elif package.source != PIP:
        raise CockpitError(f"{package.name} lässt sich nicht festhalten.")
    if package.source == PIP:
        record.set_pinned(database, package, on)
    package.pinned = on
    return f"{package.name} " + ("festgehalten." if on else "nicht mehr festgehalten.")


def upgrade_all(database, packages: list[Package], cancel=None, on_line=None) -> str:
    """Alle veralteten, die nicht festgehalten sind. Modelle bleiben, wie sie sind, weil ein
    neues Modell oft Gigabyte braucht."""
    wanted = [p for p in packages if p.outdated and not p.pinned and p.source != MODEL]
    done, failed = 0, []
    for package in wanted:
        if cancel is not None and cancel.is_set():
            break
        try:
            upgrade(database, package, cancel=cancel, on_line=on_line)
            done += 1
        except CockpitError as exc:
            failed.append(f"{package.name}: {exc.message}")
    text = f"{count(done, 'Paket', 'Pakete')} aktualisiert."
    if failed:
        raise CockpitError(text + f" {len(failed)} nicht aktualisiert.", "\n".join(failed))
    return text
