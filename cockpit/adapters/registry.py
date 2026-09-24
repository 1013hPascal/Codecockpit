"""Tabelle aller Adapter pro Art.

Adapter werden erst beim ersten Gebrauch importiert. So bleiben Bibliotheken, die nur ein Adapter
braucht, optional. Ein neuer Adapter braucht nur einen Eintrag hier, keine Änderung am Kern.
"""
from __future__ import annotations

import importlib

from cockpit.adapters.base import Adapter
from cockpit.core.errors import CockpitError

KINDS = ("platform", "ai", "vault", "automation", "email")

# Art -> Name -> "modul:Klasse" oder die Klasse selbst (Tests)
ADAPTERS: dict[str, dict[str, str | type[Adapter]]] = {
    "platform": {},
    "ai": {},
    "vault": {},
    "automation": {"none": "cockpit.automation.none:NoAutomation"},
    "email": {},
}


def register(kind: str, name: str, target: str | type[Adapter]) -> None:
    if kind not in ADAPTERS:
        raise KeyError(kind)
    ADAPTERS[kind][name] = target


def unregister(kind: str, name: str) -> None:
    ADAPTERS[kind].pop(name, None)


def names(kind: str) -> list[str]:
    return sorted(ADAPTERS[kind])


def adapter_class(kind: str, name: str) -> type[Adapter]:
    try:
        target = ADAPTERS[kind][name]
    except KeyError:
        raise CockpitError(f"Den Adapter {name} gibt es nicht.", f"Art {kind}, Name {name}") from None
    if isinstance(target, str):
        module_name, _, class_name = target.partition(":")
        try:
            target = getattr(importlib.import_module(module_name), class_name)
        except (ImportError, AttributeError) as exc:
            raise CockpitError(f"Der Adapter {name} lässt sich nicht laden.", repr(exc)) from exc
    return target
