"""Sprachmodelle auf dem Rechner.

- Hugging Face: der gemeinsame Zwischenspeicher (hub). Jede Fassung ist ein Ordner unter
  snapshots, so liegen alte und neue Fassung nebeneinander.
- Ollama: der Ordner models. Er lässt sich lesen, ohne dass Ollama läuft. Zum Herunterladen und
  Löschen braucht es Ollama.
- Die Modelle der Spracheingabe im Datenordner des Cockpits.
- Modelldateien von LM Studio, GPT4All und in Ordnern, die der Nutzer durchsuchen ließ.

Alles andere findet das Cockpit nicht von selbst, weil ein Suchlauf über die ganze Festplatte zu
lange dauert.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path

from cockpit.core import backups
from cockpit.core.errors import CockpitError
from cockpit.features.packages import runner
from cockpit.features.packages.base import MODEL, Package, folder_size, mtime

log = logging.getLogger(__name__)

HF, OLLAMA, OWN, FILE = "huggingface", "ollama", "cockpit", "datei"
KIND_NAMES = {HF: "Hugging Face", OLLAMA: "Ollama", OWN: "Spracheingabe des Cockpits",
              FILE: "Modelldatei"}
MODEL_SUFFIXES = (".gguf", ".safetensors", ".bin", ".pt", ".pth", ".onnx", ".ckpt")
MIN_MODEL_BYTES = 100 * 1024 * 1024        # kleinere .bin-Dateien sind meist keine Modelle
NEWER = "neuere Fassung"                     # Ollama nennt keine Versionsnummer
OLLAMA_HOST = "registry.ollama.ai"
OLLAMA_ACCEPT = "application/vnd.docker.distribution.manifest.v2+json"
NEEDS_OLLAMA = ("Ollama antwortet nicht. Starten Sie Ollama und versuchen Sie es noch einmal. "
                "Die Anleitung steht im Menü Hilfe unter Ollama installieren.")


# -- Hugging Face --------------------------------------------------------------------------------
def hf_cache() -> Path:
    from cockpit.ai.whisper import hf_cache as cache
    return cache()


def _hf_repo(folder: Path) -> str:
    return folder.name.removeprefix("models--").replace("--", "/", 1)


def _hf_current(folder: Path) -> str:
    try:
        return (folder / "refs" / "main").read_text(encoding="utf-8").strip()
    except OSError:
        snapshots = _snapshots(folder)
        return max(snapshots, key=lambda p: p.stat().st_mtime).name if snapshots else ""


def _snapshots(folder: Path) -> list[Path]:
    try:
        return [p for p in (folder / "snapshots").iterdir() if p.is_dir()]
    except OSError:
        return []


def huggingface_models(cache: Path | None = None) -> list[Package]:
    cache = cache or hf_cache()
    found = []
    try:
        folders = sorted(p for p in cache.iterdir() if p.is_dir() and p.name.startswith("models--"))
    except OSError:
        return []
    for folder in folders:
        current = _hf_current(folder)
        snapshots = _snapshots(folder)
        dates = [d for d in (mtime(p) for p in snapshots) if d is not None]
        found.append(Package(
            MODEL, _hf_repo(folder), current[:7] or "?", key=_hf_repo(folder),
            place=KIND_NAMES[HF], location=folder, size=folder_size(folder),
            added=max(dates) if dates else mtime(folder), kind=HF,
            extra={"revision": current, "revisions": [p.name for p in snapshots]}))
    return found


def hf_check(packages: list[Package], session=None) -> None:
    from cockpit.features.packages import web
    for package in packages:
        if package.kind != HF:
            continue
        data = web.get_json(f"https://huggingface.co/api/models/{package.id}", session)
        if not data or not data.get("sha"):
            continue
        package.checked = True
        sha = data["sha"]
        package.latest = "" if sha.startswith(package.extra.get("revision", "~")) else sha[:7]


def hf_download(package_id: str, revision: str | None = None, cancel=None) -> Path:
    """Fassung herunterladen. Die bisherige bleibt liegen (Wunsch des Nutzers vom 21.10.2026)."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise CockpitError("Zum Herunterladen von Hugging Face fehlt die Bibliothek "
                           "huggingface_hub. Sie kommt mit der Spracheingabe.") from None
    try:
        return Path(snapshot_download(package_id, revision=revision, cache_dir=str(hf_cache())))
    except Exception as exc:                       # Netz, Speicherplatz, unbekannte Fassung
        raise CockpitError(f"{package_id} ließ sich nicht herunterladen. Bitte prüfen Sie den "
                           "Namen der Fassung, die Internetverbindung und den freien Platz.",
                           repr(exc)) from None


def hf_old_revisions(package: Package) -> list[Path]:
    current = package.extra.get("revision", "")
    return [p for p in _snapshots(package.location) if p.name != current]


def hf_remove_old(package: Package) -> int:
    """Alte Fassungen entfernen, die aktuelle bleibt. Gibt die frei gewordenen Bytes zurück.
    Dateien unter blobs, auf die keine verbliebene Fassung mehr zeigt, gehen mit."""
    folder = package.location
    before = folder_size(folder)
    for snapshot in hf_old_revisions(package):
        backups.remove_tree(snapshot)
    used = set()
    for snapshot in _snapshots(folder):
        for root, _dirs, files in os.walk(snapshot):
            for name in files:
                path = Path(root) / name
                try:
                    if path.is_symlink():
                        used.add(path.resolve().name)
                except OSError:
                    continue
    blobs = folder / "blobs"
    if blobs.is_dir() and used:
        for blob in blobs.iterdir():
            if blob.name not in used:
                try:
                    blob.unlink()
                except OSError:
                    pass
    return before - folder_size(folder)


# -- Ollama --------------------------------------------------------------------------------------
def ollama_dir() -> Path:
    if os.environ.get("OLLAMA_MODELS"):
        return Path(os.environ["OLLAMA_MODELS"])
    return Path.home() / ".ollama" / "models"


def _ollama_name(host: str, namespace: str, model: str, tag: str) -> str:
    base = model if namespace == "library" else f"{namespace}/{model}"
    if host != OLLAMA_HOST:
        base = f"{host}/{namespace}/{model}"
    return f"{base}:{tag}"


def ollama_models(models_dir: Path | None = None) -> list[Package]:
    root = (models_dir or ollama_dir()) / "manifests"
    found = []
    if not root.is_dir():
        return []
    for manifest in sorted(root.rglob("*")):
        if not manifest.is_file():
            continue
        parts = manifest.relative_to(root).parts
        if len(parts) != 4:
            continue
        host, namespace, model, tag = parts
        try:
            data = manifest.read_bytes()
            layers = json.loads(data)
        except (OSError, ValueError):
            continue
        size = sum(int(layer.get("size", 0)) for layer in layers.get("layers", []))
        size += int((layers.get("config") or {}).get("size", 0))
        name = _ollama_name(host, namespace, model, tag)
        found.append(Package(                    # das Tag steht schon im Namen
            MODEL, name, "", key=name, place=KIND_NAMES[OLLAMA], location=manifest,
            size=size or None, added=mtime(manifest), kind=OLLAMA,
            extra={"digest": hashlib.sha256(data).hexdigest(), "host": host,
                   "repository": f"{namespace}/{model}", "tag": tag,
                   "layers": [layer.get("digest", "") for layer in layers.get("layers", [])]}))
    return found


def ollama_check(packages: list[Package]) -> None:
    """Gibt es unter demselben Namen eine neuere Fassung? Vergleicht die Prüfsumme des
    Manifests mit der im Verzeichnis von Ollama."""
    from cockpit.features.packages import web
    for package in packages:
        if package.kind != OLLAMA:
            continue
        extra = package.extra
        response = web.get_response(f"https://{extra['host']}/v2/{extra['repository']}/"
                                    f"manifests/{extra['tag']}", {"Accept": OLLAMA_ACCEPT})
        if response is None or response.status_code != 200:
            continue
        package.checked = True
        newer = hashlib.sha256(response.content).hexdigest() != extra["digest"]
        package.latest = NEWER if newer else ""


def _ollama(args: list[str], cancel=None, on_line=None) -> runner.Result:
    if runner.find("ollama") is None:
        raise CockpitError("Ollama ist nicht installiert.")
    result = runner.run(["ollama", *args], cancel, on_line)
    if not result.ok:
        text = result.text.lower()
        if "could not connect" in text or "connection refused" in text or "not running" in text:
            raise CockpitError(NEEDS_OLLAMA, result.text[-500:])
        raise CockpitError(f"ollama {args[0]} hat nicht geklappt.", result.text[-1500:])
    return result


def ollama_keep_name(package: Package, today: datetime | None = None) -> str:
    """Name für die bisherige Fassung, zum Beispiel llama3.2:3b-alt-20261021."""
    return f"{package.id}-alt-{(today or datetime.now()):%Y%m%d}"


def ollama_update(package: Package, keep_old: bool, cancel=None, on_line=None) -> str:
    """Neue Fassung holen. keep_old: Die bisherige bleibt unter einem eigenen Namen."""
    kept = ""
    if keep_old:
        kept = ollama_keep_name(package)
        _ollama(["cp", package.id, kept], cancel, on_line)
    _ollama(["pull", package.id], cancel, on_line)
    return kept


def ollama_pull(name: str, cancel=None, on_line=None) -> None:
    _ollama(["pull", name], cancel, on_line)


def ollama_remove(package: Package, cancel=None) -> None:
    _ollama(["rm", package.id], cancel)


# -- Modelle des Cockpits (Spracheingabe) ----------------------------------------------------------
def own_models() -> list[Package]:
    from cockpit.ai import whisper
    found = []
    root = whisper.models_dir()
    if not root.is_dir():
        return []
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        found.append(Package(MODEL, f"Whisper {folder.name}", "", key=folder.name,
                             place=KIND_NAMES[OWN], location=folder, size=folder_size(folder),
                             added=mtime(folder), kind=OWN, cockpit=True,
                             owner="Spracheingabe des Cockpits", checked=True))
    return found


# -- Modelldateien --------------------------------------------------------------------------------
def known_folders() -> list[tuple[str, Path]]:
    """Ordner bekannter Programme, wenn es sie gibt."""
    home = Path.home()
    local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    places = [("LM Studio", home / ".lmstudio" / "models"),
              ("LM Studio", home / ".cache" / "lm-studio" / "models"),
              ("GPT4All", local / "nomic.ai" / "GPT4All"),
              ("Jan", home / "jan" / "models")]
    return [(name, path) for name, path in places if path.is_dir()]


def is_model_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix not in MODEL_SUFFIXES:
        return False
    try:
        size = path.stat().st_size
    except OSError:
        return False
    return suffix in (".gguf", ".safetensors") or size >= MIN_MODEL_BYTES


def scan_folder(folder: Path, place: str, cancel: threading.Event | None = None,
                skip: tuple[Path, ...] = ()) -> list[Package]:
    """Modelldateien in einem Ordner und seinen Unterordnern. skip: Ordner, die schon anders
    erfasst sind, etwa der Zwischenspeicher von Hugging Face."""
    found = []
    skipped = [str(s).lower() for s in skip]
    for root, dirs, files in os.walk(folder):
        if cancel is not None and cancel.is_set():
            break
        if any(str(root).lower().startswith(s) for s in skipped):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not d.startswith(".") or d in (".lmstudio", ".cache")]
        for name in files:
            path = Path(root) / name
            if is_model_file(path):
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                found.append(Package(MODEL, path.name, "", key=str(path), place=place,
                                     location=path, size=size, added=mtime(path), kind=FILE,
                                     checked=True, extra={"folder": str(path.parent)}))
    return found


def file_models(extra_folders: list[Path] = ()) -> list[Package]:
    found = []
    for name, folder in known_folders():
        found += scan_folder(folder, name)
    for folder in extra_folders:
        if folder.is_dir():
            found += scan_folder(folder, f"Ordner {folder}", skip=(hf_cache(), ollama_dir()))
    seen, unique = set(), []
    for package in found:
        if package.id.lower() not in seen:
            seen.add(package.id.lower())
            unique.append(package)
    return unique


# -- Alle Modelle ---------------------------------------------------------------------------------
def all_models(extra_folders: list[Path] = ()) -> list[Package]:
    return huggingface_models() + ollama_models() + own_models() + file_models(extra_folders)


def check(packages: list[Package]) -> None:
    hf_check(packages)
    ollama_check(packages)


def delete(package: Package, cancel=None) -> None:
    """Löschen. Vorher legt der Aufrufer die Liste in den Sicherheitskopien ab (record.py)."""
    if package.kind == OLLAMA:
        ollama_remove(package, cancel)
    elif package.kind == OWN:
        from cockpit.ai import whisper
        whisper.delete(package.id)
    elif package.kind == HF:
        backups.remove_tree(package.location)
    elif package.kind == FILE:
        try:
            package.location.unlink()
        except OSError as exc:
            raise CockpitError(f"{package.name} ließ sich nicht löschen.", repr(exc)) from None
    if package.kind in (HF, OWN) and package.location is not None and package.location.exists():
        raise CockpitError(f"{package.name} ließ sich nicht ganz löschen. Wird es gerade benutzt?")
