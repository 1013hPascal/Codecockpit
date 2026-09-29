"""Feature "Releases" (Konzept 10.5 und Abschnitt 15, Punkt 14; Phase 14).

Releases anlegen, auch ohne Exe, Übersicht der Releases und der GitHub Actions: Läufe ansehen,
Fehler lesen, neu starten. Die Oberfläche steht in ui/releases_flow.py.
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import AIToolChoice
from cockpit.features.releases.runs import FEATURE_ID
from cockpit.platforms.base import Capability

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="Releases",
    description="Nach einer neuen Version ein Release anlegen, auch ohne Exe. Übersicht der "
                "Releases und der GitHub Actions: Läufe ansehen, Fehler lesen, neu starten.",
    requires_capabilities=(Capability.RELEASES,),
    settings=(AIToolChoice("tool", "KI für Versionshinweise und Fehler"),),
    enabled_by_default=True,
)
