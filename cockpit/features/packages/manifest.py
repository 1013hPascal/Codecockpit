"""Feature "Paketübersicht" (Wunsch des Nutzers vom 21.10.2026, Plan in PLAN-PAKETUEBERSICHT.md).

Überblick über Python-Bibliotheken, Programme aus winget und Chocolatey und Sprachmodelle, auf
dem ganzen Rechner und in den Projekten. Die Logik ohne Qt steht in diesem Ordner, die Oberfläche
in ui/package_dialogs.py und ui/package_flow.py. Das Menü Pakete gibt es nur, wenn das Feature
eingeschaltet ist.
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import AIToolChoice

FEATURE_ID = "packages"

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="Paketübersicht",
    description="Überblick über Bibliotheken, Programme aus winget und Chocolatey und "
                "Sprachmodelle: aktualisieren, Version wählen, löschen und aufräumen.",
    settings=(AIToolChoice("tool", "KI für Vorschläge zu neueren Modellen"),),
    enabled_by_default=True,
)
