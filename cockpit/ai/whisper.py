"""Sprach-KI: Whisper lokal mit faster-whisper (Konzept 10.15 und 11.1, Teilschritt 8d).

Vorbild ist das Tagebuch des Nutzers: faster-whisper auf dem Prozessor mit int8. Die Aufnahme
bleibt nur im Arbeitsspeicher (recording.py) und wird nie gespeichert.

Die Modelle liegen im Datenordner unter models\\whisper\\<Modell>, nicht in der Exe. Das Cockpit
lädt ein Modell erst nach Rückfrage herunter. Welches Modell gilt, steht in der Datenbank
(MODEL_KEY). Ohne Wahl gilt die Empfehlung nach Arbeitsspeicher (models.SPEECH_TIERS).
"""
from __future__ import annotations

import importlib.util
import logging
import threading
from pathlib import Path

from cockpit.ai import models
from cockpit.core import backups, paths
from cockpit.core.errors import CockpitError

log = logging.getLogger(__name__)

MODEL_KEY = "ai.whisper_model"
DEFAULT_MODEL = "small"
LIBRARIES = ("faster_whisper", "sounddevice", "numpy")
NO_LIBRARIES = ("Für die Spracheingabe fehlen Bibliotheken: faster-whisper, sounddevice und "
                "numpy. In der Exe sind sie enthalten. Beim Start aus dem Code installieren Sie "
                "sie mit pip install -r requirements.txt.")
# Ungefähre Größe des Downloads in MB, für den Fortschritt
SIZES_MB = {"small": 484, "medium": 1530, "large-v3-turbo": 1620}
LANGUAGES = {"Deutsch": "de", "Englisch": "en", "Automatisch erkennen": None}

_model = None
_model_name = ""
_lock = threading.Lock()


def problem() -> str:
    """Warum es keine Sprach-KI gibt, leer wenn die Bibliotheken da sind."""
    missing = [name for name in LIBRARIES if importlib.util.find_spec(name) is None]
    return NO_LIBRARIES if missing else ""


def models_dir() -> Path:
    return paths.data_dir() / "models" / "whisper"


def model_dir(name: str) -> Path:
    return models_dir() / name


def hf_cache() -> Path:
    """Zwischenspeicher von Hugging Face. Dort liegen zum Beispiel die Modelle des Tagebuchs."""
    import os
    if os.environ.get("HF_HUB_CACHE"):
        return Path(os.environ["HF_HUB_CACHE"])
    if os.environ.get("HF_HOME"):
        return Path(os.environ["HF_HOME"]) / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def _repository(name: str) -> str:
    try:
        from faster_whisper.utils import _MODELS
        return _MODELS.get(name, f"Systran/faster-whisper-{name}")
    except ImportError:
        return f"Systran/faster-whisper-{name}"


def cached_dir(name: str) -> Path | None:
    """Ordner des Modells im Zwischenspeicher von Hugging Face, sonst None (Wunsch aus dem Test
    von 8d: Modelle des Tagebuchs nicht noch einmal herunterladen)."""
    snapshots = hf_cache() / ("models--" + _repository(name).replace("/", "--")) / "snapshots"
    try:
        found = [p for p in snapshots.iterdir() if (p / "model.bin").is_file()]
    except OSError:
        return None
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def own_copy(name: str) -> bool:
    """Liegt das Modell im Datenordner des Cockpits? Nur das lässt sich hier löschen."""
    return (model_dir(name) / "model.bin").is_file()


def model_path(name: str) -> Path | None:
    if own_copy(name):
        return model_dir(name)
    return cached_dir(name)


def is_downloaded(name: str) -> bool:
    return model_path(name) is not None


def downloaded() -> list[str]:
    return [tier.model for tier in models.SPEECH_TIERS if is_downloaded(tier.model)]


def chosen_model(database, ram_gb: float | None) -> str:
    """Gewähltes Modell, sonst die Empfehlung nach Arbeitsspeicher, sonst small."""
    stored = database.get_value(MODEL_KEY, "") if database is not None else ""
    if stored:
        return str(stored)
    tier = models.recommended(models.SPEECH_TIERS, ram_gb)
    return tier.model if tier is not None else DEFAULT_MODEL


def size_text(name: str) -> str:
    tier = next((t for t in models.SPEECH_TIERS if t.model == name), None)
    return tier.size if tier is not None else "unbekannt"


def folder_mb(name: str) -> int:
    """Wie viel schon heruntergeladen ist, für den Fortschritt."""
    folder = model_dir(name)
    if not folder.is_dir():
        return 0
    return round(sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()) / 1_048_576)


def download(name: str) -> Path:
    """Modell von Hugging Face herunterladen. Blockiert, also im Hintergrund aufrufen."""
    if problem():
        raise CockpitError(problem())
    from faster_whisper.utils import download_model
    target = model_dir(name)
    target.mkdir(parents=True, exist_ok=True)
    try:
        download_model(name, output_dir=str(target))
    except Exception as exc:                     # Netz, Speicherplatz, Hugging Face
        raise CockpitError(f"Das Whisper-Modell {name} ließ sich nicht herunterladen. Bitte "
                           "prüfen Sie die Internetverbindung und den freien Speicherplatz.",
                           repr(exc)) from None
    if not is_downloaded(name):
        raise CockpitError(f"Das Whisper-Modell {name} ist unvollständig.")
    return target


def delete(name: str) -> None:
    """Heruntergeladenes Modell löschen. Es lässt sich jederzeit neu herunterladen, deshalb
    ohne Sicherheitskopie (ENTSCHEIDUNGEN.md, 8d). Nur die Kopie im Datenordner des Cockpits,
    nie den Zwischenspeicher von Hugging Face, den auch andere Programme nutzen."""
    global _model, _model_name
    with _lock:
        if _model_name == name:
            _model, _model_name = None, ""
    backups.remove_tree(model_dir(name))


def _load(name: str):
    global _model, _model_name
    with _lock:
        if _model is None or _model_name != name:
            from faster_whisper import WhisperModel
            log.info("Lade Whisper-Modell %s", name)
            _model = WhisperModel(str(model_path(name)), device="cpu", compute_type="int8")
            _model_name = name
        return _model


def transcribe(audio, name: str, language: str | None = "de") -> str:
    """Aufnahme (float32, 16 kHz, mono) in Text. Blockiert, also im Hintergrund aufrufen."""
    if audio is None or getattr(audio, "size", 0) == 0:
        return ""
    if not is_downloaded(name):
        raise CockpitError(f"Das Whisper-Modell {name} ist nicht heruntergeladen.")
    try:
        segments, _info = _load(name).transcribe(audio, language=language)
        parts = [segment.text.strip() for segment in segments]
    except Exception as exc:
        raise CockpitError("Die Spracherkennung ist fehlgeschlagen.", repr(exc)) from None
    return " ".join(part for part in parts if part).strip()
