"""Welches Feature wo aktiv ist (Konzept 3.2, 8.4 und 8.5).

- Global an oder aus steht in der Datenbank. Standard ist an.
- Pro Projekt steht die Liste der eingeschalteten Features in Code\\cockpit.toml. Fehlt sie, gilt
  die Vorauswahl aus den Grundeinstellungen bzw. der Standard der Features.
- Aktiv ist ein Feature in einem Projekt, wenn es global an, im Projekt eingeschaltet und
  verfügbar ist. Verfügbar heißt: benötigte Dienste eingerichtet, benötigte Features verfügbar und
  im Projekt eingeschaltet, benötigte Fähigkeiten von der Plattform des Projekts unterstützt.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from cockpit.core.availability import Availability
from cockpit.core.database import Database
from cockpit.core.errors import CockpitError
from cockpit.core.features.manifest import SERVICES, FeatureManifest
from cockpit.core.features.registry import FeatureRegistry
from cockpit.core.text import join_words
from cockpit.platforms.base import CAPABILITY_NAMES, Capability

if TYPE_CHECKING:
    from cockpit.core.projects import Project, ProjectStore
    from cockpit.core.settings import SettingsStore


@dataclass(frozen=True)
class Requirement:
    kind: str          # "feature", "service" oder "capability"
    id: str
    name: str          # deutscher Name, zum Beispiel "Rückmeldungen" oder "KI"
    reason: str        # warum sie fehlt


class FeatureDependencyError(CockpitError):
    def __init__(self, message: str, missing: list[Requirement]) -> None:
        super().__init__(message)
        self.missing = missing


class FeatureManager:
    def __init__(self, registry: FeatureRegistry, database: Database,
                 projects: "ProjectStore", settings: "SettingsStore",
                 service_availability: Callable[[str], Availability],
                 capabilities_for: Callable[["Project"], set[Capability] | None]) -> None:
        self.registry = registry
        self.database = database
        self.projects = projects
        self.settings = settings
        self.service_availability = service_availability
        self.capabilities_for = capabilities_for

    # -- Global ---------------------------------------------------------------------------
    def globally_enabled(self, feature_id: str) -> bool:
        self.registry.get(feature_id)
        row = self.database.query_one("SELECT enabled FROM features_global WHERE feature_id = ?",
                                      (feature_id,))
        return True if row is None else bool(row["enabled"])

    def set_globally_enabled(self, feature_id: str, enabled: bool) -> None:
        self.registry.get(feature_id)
        self.database.execute(
            "INSERT INTO features_global (feature_id, enabled) VALUES (?, ?) "
            "ON CONFLICT(feature_id) DO UPDATE SET enabled = excluded.enabled",
            (feature_id, int(enabled)))

    def visible_features(self) -> list[FeatureManifest]:
        """Global eingeschaltete Features. Ausgeschaltete erscheinen nirgends (Konzept 8.5)."""
        return [m for m in self.registry.all() if self.globally_enabled(m.id)]

    # -- Pro Projekt ----------------------------------------------------------------------
    def default_features(self) -> set[str]:
        """Vorauswahl für neue Projekte und für Projekte, die in cockpit.toml nichts festlegen.
        Ist sie in der Feature-Verwaltung gespeichert, gilt nur sie (Phase 7)."""
        settings = self.settings.load()
        chosen = settings.default_features
        if chosen is not None:
            return {f for f in chosen if f in self.registry}
        result = {m.id for m in self.registry.all() if m.enabled_by_default}
        for manifest in self.registry.all():
            if manifest.default_setting and getattr(settings, manifest.default_setting, False):
                result.add(manifest.id)
        return result

    def set_default_features(self, feature_ids: set[str]) -> None:
        self.settings.update(default_features=sorted(f for f in feature_ids
                                                     if f in self.registry))

    def follows_default(self, project: "Project") -> bool:
        """True, wenn cockpit.toml des Projekts nichts zu Features festlegt."""
        return self.projects.enabled_features(project) is None

    def set_project_features(self, project: "Project", feature_ids: set[str]) -> None:
        """Die Auswahl fest in cockpit.toml schreiben (ohne Prüfung der Abhängigkeiten)."""
        self.projects.set_enabled_features(project, {f for f in feature_ids
                                                     if f in self.registry})

    def project_count(self, feature_id: str) -> int:
        """In wie vielen Projekten der Liste das Feature eingeschaltet ist."""
        return len([p for p in self.projects.all()
                    if p.folder_found and feature_id in self.project_features(p)])

    def needs(self, feature_id: str) -> list[str]:
        """Was das Feature braucht, als Namen: andere Features, Dienste, Fähigkeiten."""
        manifest = self.registry.get(feature_id)
        names = [self.registry.get(d).name for d in manifest.requires_features
                 if d in self.registry]
        names += [SERVICES[s] for s in manifest.requires_services]
        names += [f"Plattform mit {CAPABILITY_NAMES[c]}" for c in manifest.requires_capabilities]
        return names

    # -- Einführung (ENTSCHEIDUNGEN.md: erscheint beim allerersten Einschalten) ----------------
    def intro_seen(self, feature_id: str) -> bool:
        return feature_id in (self.database.get_value("features.intro_seen", []) or [])

    def mark_intro_seen(self, feature_id: str) -> None:
        seen = set(self.database.get_value("features.intro_seen", []) or [])
        self.database.set_value("features.intro_seen", sorted(seen | {feature_id}))

    def project_features(self, project: "Project") -> set[str]:
        """Im Projekt eingeschaltete Features (ohne Rücksicht auf Verfügbarkeit)."""
        stored = self.projects.enabled_features(project)
        chosen = self.default_features() if stored is None else stored
        return {f for f in chosen if f in self.registry}

    def enabled_in_project(self, feature_id: str, project: "Project") -> bool:
        return feature_id in self.project_features(project)

    def availability(self, feature_id: str, project: "Project | None" = None) -> Availability:
        manifest = self.registry.get(feature_id)
        if not self.globally_enabled(feature_id):
            return Availability.no(f"{manifest.name} ist ausgeschaltet.")
        for service in manifest.requires_services:
            state = self.service_availability(service)
            if not state:
                return Availability.no(f"Benötigt {SERVICES[service]}. {state.reason}".strip())
        enabled = self.project_features(project) if project is not None else set()
        for dependency in manifest.requires_features:
            name = self.registry.get(dependency).name
            if project is not None and dependency not in enabled:
                return Availability.no(
                    f"Benötigt {name}. {name} ist für dieses Projekt ausgeschaltet.")
            state = self.availability(dependency, project)
            if not state:
                return Availability.no(f"Benötigt {name}. {state.reason}")
        if project is not None and manifest.requires_capabilities:
            reason = self._capability_reason(manifest, project)
            if reason:
                return Availability.no(reason)
        return Availability.yes()

    def availability_without_switch(self, feature_id: str) -> Availability:
        """Wie availability ohne Projekt, aber ohne Rücksicht darauf, ob das Feature selbst
        global eingeschaltet ist. Für die Feature-Verwaltung vor dem Speichern: Fehlt ein Dienst
        wie KI oder Automation, auch bei einem benötigten Feature?"""
        manifest = self.registry.get(feature_id)
        for service in manifest.requires_services:
            state = self.service_availability(service)
            if not state:
                return Availability.no(f"Benötigt {SERVICES[service]}. {state.reason}".strip())
        for dependency in manifest.requires_features:
            state = self.availability_without_switch(dependency)
            if not state:
                return Availability.no(f"Benötigt {self.registry.get(dependency).name}. "
                                       f"{state.reason}")
        return Availability.yes()

    def _capability_reason(self, manifest: FeatureManifest, project: "Project") -> str:
        capabilities = self.capabilities_for(project)
        if capabilities is None:
            return "Das Projekt ist mit keiner Plattform verbunden."
        missing = [c for c in manifest.requires_capabilities if c not in capabilities]
        if missing:
            names = join_words(CAPABILITY_NAMES[c] for c in missing)
            return f"Die Plattform dieses Projekts unterstützt nicht: {names}."
        return ""

    def active(self, feature_id: str, project: "Project") -> bool:
        return (self.enabled_in_project(feature_id, project)
                and self.availability(feature_id, project).available)

    def active_features(self, project: "Project") -> list[FeatureManifest]:
        return [m for m in self.registry.all() if self.active(m.id, project)]

    def missing_requirements(self, feature_id: str, project: "Project") -> list[Requirement]:
        """Alles, was fehlt, damit das Feature im Projekt aktiv sein kann."""
        manifest = self.registry.get(feature_id)
        enabled = self.project_features(project)
        missing: list[Requirement] = []
        seen: set[tuple[str, str]] = set()

        def add(requirement: Requirement) -> None:
            if (requirement.kind, requirement.id) not in seen:
                seen.add((requirement.kind, requirement.id))
                missing.append(requirement)

        def collect(current: FeatureManifest) -> None:
            # Reihenfolge: eigene Features, eigene Dienste, Plattform, dann was die Features brauchen
            for dependency in current.requires_features:
                dep = self.registry.get(dependency)
                if not self.globally_enabled(dependency):
                    add(Requirement("feature", dependency, dep.name,
                                    f"{dep.name} ist global ausgeschaltet."))
                elif dependency not in enabled:
                    add(Requirement("feature", dependency, dep.name,
                                    f"{dep.name} ist für dieses Projekt ausgeschaltet."))
            for service in current.requires_services:
                state = self.service_availability(service)
                if not state:
                    add(Requirement("service", service, SERVICES[service], state.reason))
            reason = self._capability_reason(current, project) if current.requires_capabilities \
                else ""
            if reason:
                add(Requirement("capability", current.id, "Plattform", reason))
            for dependency in current.requires_features:
                collect(self.registry.get(dependency))

        collect(manifest)
        return missing

    def requirements_text(self, feature_id: str, project: "Project") -> str:
        """Zum Beispiel: "Antwortentwürfe benötigt Rückmeldungen und KI. Rückmeldungen ist für
        dieses Projekt ausgeschaltet. Es ist kein KI-Anbieter eingerichtet." Leer, wenn nichts
        fehlt."""
        missing = self.missing_requirements(feature_id, project)
        if not missing:
            return ""
        name = self.registry.get(feature_id).name
        needed = join_words(r.name for r in missing if r.kind != "capability")
        parts = [f"{name} benötigt {needed}." if needed else ""]
        parts += [r.reason for r in missing]
        return " ".join(p for p in parts if p)

    def enable(self, feature_id: str, project: "Project",
               with_dependencies: bool = False) -> list[str]:
        """Feature im Projekt einschalten. Gibt alle eingeschalteten Kennungen zurück.

        Fehlen benötigte Features, wird FeatureDependencyError geworfen, außer mit
        with_dependencies=True: dann werden sie mit eingeschaltet. Fehlende Dienste oder
        Fähigkeiten verhindern das Einschalten nicht, das Feature ist dann nur nicht verfügbar."""
        manifest = self.registry.get(feature_id)
        if not self.globally_enabled(feature_id):
            raise CockpitError(f"{manifest.name} ist global ausgeschaltet.")
        enabled = self.project_features(project)
        needed = [d for d in self.registry.dependencies(feature_id) if d not in enabled]
        blocked = [d for d in needed if not self.globally_enabled(d)]
        if blocked:
            names = join_words(self.registry.get(d).name for d in blocked)
            raise CockpitError(f"{manifest.name} benötigt {names}. "
                               "Bitte zuerst in der Feature-Verwaltung einschalten.")
        if needed and not with_dependencies:
            missing = [r for r in self.missing_requirements(feature_id, project)
                       if r.kind == "feature"]
            raise FeatureDependencyError(self.requirements_text(feature_id, project), missing)
        switched = [d for d in needed] + ([feature_id] if feature_id not in enabled else [])
        self.projects.set_enabled_features(project, enabled | set(switched))
        return switched

    def enabled_dependents(self, feature_id: str, project: "Project") -> list[str]:
        """Eingeschaltete Features, die ausfallen, wenn dieses ausgeschaltet wird."""
        enabled = self.project_features(project)
        return [d for d in self.registry.dependents(feature_id) if d in enabled]

    def disable(self, feature_id: str, project: "Project") -> list[str]:
        """Feature und alle davon abhängigen Features im Projekt ausschalten.
        Gibt die ausgeschalteten Kennungen zurück. Vorher enabled_dependents() fragen."""
        self.registry.get(feature_id)
        enabled = self.project_features(project)
        switched = [f for f in [feature_id, *self.enabled_dependents(feature_id, project)]
                    if f in enabled]
        self.projects.set_enabled_features(project, enabled - set(switched))
        return switched

    # -- Einstellungen der Features -------------------------------------------------------
    def setting(self, feature_id: str, key: str) -> Any:
        field = self._field(feature_id, key)
        row = self.database.query_one(
            "SELECT value FROM feature_settings WHERE feature_id = ? AND key = ?",
            (feature_id, key))
        if row is None:
            return field.default
        try:
            return field.check(json.loads(row["value"]))
        except ValueError:
            return field.default

    def set_setting(self, feature_id: str, key: str, value: Any) -> None:
        value = self._field(feature_id, key).check(value)
        self.database.execute(
            "INSERT INTO feature_settings (feature_id, key, value) VALUES (?, ?, ?) "
            "ON CONFLICT(feature_id, key) DO UPDATE SET value = excluded.value",
            (feature_id, key, json.dumps(value, ensure_ascii=False)))

    def _field(self, feature_id: str, key: str):
        for field in self.registry.get(feature_id).settings:
            if field.key == key:
                return field
        raise KeyError(f"{feature_id}.{key}")
