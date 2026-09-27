"""Vorgeschlagene lokale Modelle nach Arbeitsspeicher (Konzept 11.1).

Die Namen stehen nur hier und lassen sich hier anpassen. Drei Stufen reichen: ab 16, 32 und 64 GB.
Für größere Modelle gibt es firmeninterne Anbieter.

Stand 27.09.2026, geprüft gegen die Bibliothek von Ollama (ollama.com/library/gemma4).
"""
from __future__ import annotations

from dataclasses import dataclass

# Windows meldet etwas weniger als den eingebauten Speicher, zum Beispiel 31,7 statt 32 GB
TOLERANCE = 0.9


@dataclass(frozen=True)
class Tier:
    min_ram_gb: int
    model: str
    size: str                   # Größe des Downloads, zum Beispiel "etwa 8 GB"


# Text-KI mit Ollama: etwa 4, 12 und 26 Milliarden Parameter
TEXT_TIERS = (
    Tier(16, "gemma4:e4b", "etwa 10 GB"),
    Tier(32, "gemma4:12b", "etwa 8 GB"),
    Tier(64, "gemma4:26b", "etwa 19 GB"),
)

# Sprach-KI mit Whisper (ab Teilschritt 8d)
SPEECH_TIERS = (
    Tier(16, "small", "etwa 500 MB"),
    Tier(32, "medium", "etwa 1,5 GB"),
    Tier(64, "large-v3-turbo", "etwa 1,6 GB"),
)


def fits(tier: Tier, ram_gb: float | None) -> bool:
    return ram_gb is not None and ram_gb >= tier.min_ram_gb * TOLERANCE


def recommended(tiers: tuple[Tier, ...], ram_gb: float | None) -> Tier | None:
    """Größte Stufe, die zum Arbeitsspeicher passt. None: weniger als 16 GB oder unbekannt."""
    matching = [t for t in tiers if fits(t, ram_gb)]
    return matching[-1] if matching else None


def is_installed(model: str, installed: list[str]) -> bool:
    """Ollama nennt Modelle ohne Angabe als "name:latest"."""
    names = set(installed) | {m.removesuffix(":latest") for m in installed}
    return model in names


def suggestion_line(tier: Tier, ram_gb: float | None, installed: list[str]) -> str:
    """Zum Beispiel "gemma4:12b, ab 32 GB Arbeitsspeicher, etwa 8 GB, empfohlen, installiert"."""
    parts = [tier.model, f"ab {tier.min_ram_gb} GB Arbeitsspeicher", tier.size]
    best = recommended(TEXT_TIERS if tier in TEXT_TIERS else SPEECH_TIERS, ram_gb)
    if tier == best:
        parts.append("empfohlen für Ihren Rechner")
    elif ram_gb is not None and not fits(tier, ram_gb):
        parts.append("zu groß für Ihren Rechner")
    parts.append("installiert" if is_installed(tier.model, installed) else "nicht installiert")
    return ", ".join(parts)


def pull_command(model: str) -> str:
    return f"ollama pull {model}"
