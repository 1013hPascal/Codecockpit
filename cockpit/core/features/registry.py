"""Findet und prüft alle Features.

Das Register durchsucht das Paket cockpit.features. Jedes Unterpaket mit manifest.py und MANIFEST
ist ein Feature. Neue Features brauchen deshalb keine Änderung am Kern.

Ein Feature, das sich nicht laden lässt, bringt das Programm nicht zum Absturz. Es fehlt dann, und
der Grund steht in load_errors und im Log.
"""
from __future__ import annotations

import dataclasses
import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Iterable

from cockpit.core.errors import CockpitError
from cockpit.core.features.manifest import FeatureManifest

log = logging.getLogger(__name__)

DEFAULT_PACKAGE = "cockpit.features"


class FeatureRegistryError(CockpitError):
    pass


class FeatureRegistry:
    def __init__(self, manifests: Iterable[FeatureManifest],
                 load_errors: list[str] | None = None) -> None:
        self.load_errors = list(load_errors or [])
        self._features: dict[str, FeatureManifest] = {}
        for manifest in manifests:
            if manifest.id in self._features:
                raise FeatureRegistryError(f"Die Feature-Kennung {manifest.id} gibt es doppelt.")
            self._features[manifest.id] = _with_feature_id(manifest)
        self._check()

    @classmethod
    def discover(cls, package: str = DEFAULT_PACKAGE) -> "FeatureRegistry":
        manifests, errors = [], []
        root = importlib.import_module(package)
        for info in pkgutil.iter_modules(root.__path__):
            if not info.ispkg:
                continue
            name = f"{package}.{info.name}.manifest"
            try:
                module = importlib.import_module(name)
                manifest = module.MANIFEST
            except Exception as exc:                     # ein kaputtes Feature stoppt nicht alles
                log.exception("Feature %s lässt sich nicht laden", info.name)
                errors.append(f"Das Feature {info.name} lässt sich nicht laden: {exc}")
                continue
            manifests.append(dataclasses.replace(manifest,
                                                 package_dir=Path(module.__file__).parent))
        return cls(manifests, errors)

    def _check(self) -> None:
        problems = []
        for manifest in self._features.values():
            problems.extend(manifest.problems())
            for dependency in manifest.requires_features:
                if dependency not in self._features:
                    problems.append(f"Feature {manifest.id} braucht das unbekannte Feature "
                                    f"{dependency}.")
        if problems:
            raise FeatureRegistryError("Die Features sind fehlerhaft beschrieben.",
                                       "\n".join(problems))
        for feature_id in self._features:
            self._check_cycle(feature_id, [])

    def _check_cycle(self, feature_id: str, path: list[str]) -> None:
        if feature_id in path:
            circle = " -> ".join(path[path.index(feature_id):] + [feature_id])
            raise FeatureRegistryError("Die Features hängen im Kreis voneinander ab.", circle)
        for dependency in self._features[feature_id].requires_features:
            self._check_cycle(dependency, path + [feature_id])

    # -- Abfragen -------------------------------------------------------------------------
    def get(self, feature_id: str) -> FeatureManifest:
        try:
            return self._features[feature_id]
        except KeyError:
            raise FeatureRegistryError(f"Das Feature {feature_id} gibt es nicht.") from None

    def __contains__(self, feature_id: object) -> bool:
        return feature_id in self._features

    def all(self) -> list[FeatureManifest]:
        """Alle Features, alphabetisch nach Namen."""
        return sorted(self._features.values(), key=lambda m: m.name.lower())

    def ids(self) -> list[str]:
        return [m.id for m in self.all()]

    def dependencies(self, feature_id: str) -> list[str]:
        """Alle direkt und indirekt benötigten Features, benötigte zuerst."""
        ordered: list[str] = []

        def visit(current: str) -> None:
            for dependency in self._features[current].requires_features:
                visit(dependency)
                if dependency not in ordered:
                    ordered.append(dependency)

        visit(feature_id)
        return ordered

    def dependents(self, feature_id: str) -> list[str]:
        """Alle Features, die direkt oder indirekt dieses Feature brauchen."""
        return [m.id for m in self.all() if feature_id in self.dependencies(m.id)]


def _with_feature_id(manifest: FeatureManifest) -> FeatureManifest:
    """Schritte kennen ihr Feature, damit Log und Zusammenfassung es nennen können."""
    steps = tuple(dataclasses.replace(s, feature_id=manifest.id) for s in manifest.steps)
    return dataclasses.replace(manifest, steps=steps)
