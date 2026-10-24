"""Feature "Aktivität" (Wunsch des Nutzers vom 22.10.2026, Plan in PLAN-NEUIGKEITEN-UND-MODULE.md).

Zahlen, die zeigen, wie beliebt ein Programm ist: Aufrufe, Klone, Downloads, Sterne. Das Cockpit
speichert sie einmal am Tag, so entsteht eine Statistik über die 14 Tage von GitHub hinaus. Die
Logik ohne Qt steht in activity.py, die Oberfläche in ui/news_flow.py und ui/news_dialogs.py.
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.features.activity.activity import FEATURE_ID
from cockpit.platforms.base import Capability

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="Aktivität",
    description="Aufrufe, Klone, Downloads und Sterne der Projekte, einmal am Tag gespeichert. "
                "Dazu die letzten Kommentare und Issues.",
    requires_capabilities=(Capability.ACTIVITY,),
    enabled_by_default=True,
)
