"""Feature "Neuigkeiten" (Wunsch des Nutzers vom 22.10.2026, Plan in PLAN-NEUIGKEITEN-UND-MODULE.md).

Nach dem Start eine kurze Ansage, was andere seit dem letzten Besuch getan haben, und das Fenster
"Neuigkeiten" im Menü Neuigkeiten. Die Logik ohne Qt steht in news.py, die Oberfläche in
ui/news_flow.py und ui/news_dialogs.py.
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.features.news.news import FEATURE_ID
from cockpit.platforms.base import Capability

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="Neuigkeiten",
    description="Nach dem Start ansagen, was seit dem letzten Besuch neu ist: Issues, Pull "
                "Requests, Kommentare, Sterne, Forks, Releases und fehlgeschlagene Läufe.",
    # Die Daten kommen von der Plattform. Die Einrichtung zeigt das Feature deshalb bei GitHub.
    requires_capabilities=(Capability.ACTIVITY,),
    enabled_by_default=True,
)
