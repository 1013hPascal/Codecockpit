"""Liste für einen neuen Rechner (Stufe 3 der Paketübersicht).

Speichern: Programme aus winget und Chocolatey, Bibliotheken im globalen Python und Modelle aus
Ollama und Hugging Face, je mit Version, in einer JSON-Datei. Umgebungen der Projekte gehören
nicht hinein: Die entstehen aus requirements.txt neu.
Einlesen: Das Cockpit vergleicht mit dem, was schon da ist, und zeigt nur, was fehlt.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from cockpit.core.errors import CockpitError
from cockpit.features.packages import choco_source, models, pip_source, winget_source
from cockpit.features.packages.base import CHOCO, MODEL, PIP, WINGET, Package

FORMAT = 1


@dataclass
class Wanted:
    source: str                         # PIP, WINGET, CHOCO oder MODEL
    key: str
    version: str = ""
    kind: str = ""                      # bei Modellen: ollama oder huggingface

    def line(self) -> str:
        names = {PIP: "Bibliothek", WINGET: "winget", CHOCO: "Chocolatey", MODEL: "Modell"}
        return f"{self.key} {self.version}".strip() + f", {names[self.source]}"


def to_data(by_source: dict[str, list[Package]]) -> dict:
    data = {"format": FORMAT, "created": datetime.now().isoformat(timespec="seconds"),
            "winget": [], "choco": [], "pip": [], "models": []}
    for package in by_source.get(WINGET) or []:
        data["winget"].append({"id": package.id, "version": package.version})
    for package in by_source.get(CHOCO) or []:
        data["choco"].append({"id": package.id, "version": package.version})
    for package in by_source.get(PIP) or []:
        if not package.cockpit and package.extra.get("project_id") is None:
            data["pip"].append({"name": package.name, "version": package.version})
    for package in by_source.get(MODEL) or []:
        if package.kind in (models.OLLAMA, models.HF):
            data["models"].append({"kind": package.kind, "id": package.id})
    return data


def save(path: Path, by_source: dict[str, list[Package]]) -> int:
    data = to_data(by_source)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return sum(len(data[k]) for k in ("winget", "choco", "pip", "models"))


def read(path: Path) -> list[Wanted]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CockpitError(f"Die Datei {path.name} ließ sich nicht lesen.", repr(exc)) from None
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise CockpitError(f"{path.name} ist keine Liste der Paketübersicht.")
    found = [Wanted(WINGET, i["id"], i.get("version", "")) for i in data.get("winget", [])]
    found += [Wanted(CHOCO, i["id"], i.get("version", "")) for i in data.get("choco", [])]
    found += [Wanted(PIP, i["name"], i.get("version", "")) for i in data.get("pip", [])]
    found += [Wanted(MODEL, i["id"], kind=i.get("kind", "")) for i in data.get("models", [])]
    return found


def missing(wanted: list[Wanted], by_source: dict[str, list[Package]]) -> list[Wanted]:
    """Was hier fehlt. Eine andere Version zählt als vorhanden."""
    have = {(s, p.id.lower()) for s, packages in by_source.items() for p in packages or []}
    return [w for w in wanted if (w.source, w.key.lower()) not in have]


def install(item: Wanted, python: Path | None, with_version: bool, cancel=None,
            on_line=None) -> None:
    version = item.version if with_version else ""
    if item.source == WINGET:
        winget_source.install_by_id(item.key, version, cancel, on_line)
    elif item.source == CHOCO:
        choco_source.install_by_id(item.key, version, cancel, on_line)
    elif item.source == PIP:
        if python is None:
            raise CockpitError("Es ist kein Python installiert.")
        package = Package(PIP, item.key, "", key=item.key, location=python)
        if version:
            pip_source.install_version(package, version, cancel, on_line)
        else:
            pip_source.upgrade(package, cancel, on_line)
    elif item.kind == models.OLLAMA:
        models.ollama_pull(item.key, cancel, on_line)
    elif item.kind == models.HF:
        models.hf_download(item.key, None, cancel)
