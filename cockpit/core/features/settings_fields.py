"""Beschreibung von Einstellungsfeldern.

Features und die Grundeinstellungen beschreiben ihre Einstellungen mit diesen Klassen. Die
Oberfläche baut daraus automatisch ein barrierefreies Formular (ui/form_builder.py).

Aufruf immer mit Kennung, Beschriftung und Standardwert, weitere Angaben mit Namen:
    Choice("test_mode", "Testart", "Start-Test", options=("Start-Test", "Selbsttest"))

Jedes Feld prüft selbst, ob ein Wert gültig ist: check(value) gibt den bereinigten Wert zurück oder
wirft ValueError mit einem einfachen deutschen Satz.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

WEEKDAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")


@dataclass(frozen=True)
class SettingField:
    key: str
    label: str                     # Beschriftung im Formular, kurz, das Wichtigste vorne
    default: Any = None

    fallback: ClassVar[Any] = None     # Standardwert, wenn keiner angegeben ist

    def __post_init__(self) -> None:
        if self.default is None and self.fallback is not None:
            object.__setattr__(self, "default", self.fallback)

    def check(self, value: Any) -> Any:
        return value


@dataclass(frozen=True, kw_only=True)
class Text(SettingField):
    required: bool = False
    pattern: str = ""              # regulärer Ausdruck, leer = alles erlaubt
    pattern_hint: str = ""         # Satz, der sagt, was erwartet wird
    fallback: ClassVar[Any] = ""

    def check(self, value: Any) -> str:
        text = str(value if value is not None else "").strip()
        if self.required and not text:
            raise ValueError(f"Bitte {self.label} ausfüllen.")
        if text and self.pattern and not re.fullmatch(self.pattern, text):
            raise ValueError(self.pattern_hint or f"{self.label} hat nicht das richtige Format.")
        return text


@dataclass(frozen=True, kw_only=True)
class Email(Text):
    pattern: str = r"[^@\s]+@[^@\s]+\.[^@\s]+"
    pattern_hint: str = "Bitte eine gültige E-Mail-Adresse eingeben."


@dataclass(frozen=True, kw_only=True)
class Folder(SettingField):
    must_exist: bool = True
    fallback: ClassVar[Any] = ""

    def check(self, value: Any) -> str:
        text = str(value if value is not None else "").strip().strip('"')
        if not text:
            raise ValueError(f"Bitte {self.label} angeben.")
        if self.must_exist and not Path(text).is_dir():
            raise ValueError(f"Den Ordner {text} gibt es nicht.")
        return text


@dataclass(frozen=True, kw_only=True)
class Number(SettingField):
    minimum: int | None = None
    maximum: int | None = None
    fallback: ClassVar[Any] = 0

    def check(self, value: Any) -> int:
        if isinstance(value, bool):
            raise ValueError(f"{self.label}: Bitte eine ganze Zahl eingeben.")
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{self.label}: Bitte eine ganze Zahl eingeben.") from None
        if self.minimum is not None and number < self.minimum:
            raise ValueError(f"{self.label}: Die Zahl muss mindestens {self.minimum} sein.")
        if self.maximum is not None and number > self.maximum:
            raise ValueError(f"{self.label}: Die Zahl darf höchstens {self.maximum} sein.")
        return number


@dataclass(frozen=True, kw_only=True)
class YesNo(SettingField):
    fallback: ClassVar[Any] = False

    def check(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        raise ValueError(f"{self.label}: Ja oder Nein erwartet.")


@dataclass(frozen=True, kw_only=True)
class Choice(SettingField):
    options: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.options:
            raise ValueError(f"Auswahlfeld {self.key} ohne Möglichkeiten.")
        if self.default is None:
            object.__setattr__(self, "default", self.options[0])
        if self.default not in self.options:
            raise ValueError(f"Auswahlfeld {self.key}: Standardwert ist keine der Möglichkeiten.")

    def check(self, value: Any) -> str:
        if value not in self.options:
            raise ValueError(f"{self.label}: Bitte eine der Möglichkeiten wählen.")
        return value


@dataclass(frozen=True, kw_only=True)
class Weekday(Choice):
    options: tuple[str, ...] = WEEKDAYS


@dataclass(frozen=True, kw_only=True)
class MultiChoice(SettingField):
    options: tuple[str, ...] = ()
    fallback: ClassVar[Any] = ()

    def check(self, value: Any) -> list[str]:
        chosen = list(value or [])
        unknown = [v for v in chosen if v not in self.options]
        if unknown:
            raise ValueError(f"{self.label}: Unbekannte Auswahl {', '.join(unknown)}.")
        return [o for o in self.options if o in chosen]          # Reihenfolge der Möglichkeiten


@dataclass(frozen=True, kw_only=True)
class TimeOfDay(SettingField):
    fallback: ClassVar[Any] = "08:00"

    def check(self, value: Any) -> str:
        text = str(value or "").strip()
        match = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
        if not match or int(match.group(1)) > 23 or int(match.group(2)) > 59:
            raise ValueError(f"{self.label}: Bitte eine Uhrzeit wie 08:00 eingeben.")
        return f"{int(match.group(1)):02d}:{match.group(2)}"
