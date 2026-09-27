"""Beispiel Aufbau: braucht Beispiel Grundlage (nur Testdaten)."""
from cockpit.core.features.manifest import FeatureManifest

MANIFEST = FeatureManifest(
    id="beispiel_aufbau",
    name="Beispiel Aufbau",
    description="Nur zum Testen. Braucht das Feature „Beispiel Grundlage“.",
    requires_features=("beispiel_grundlage",),
)
