"""Feature "Branches und Pull Requests" (Konzept 10.14, ENTSCHEIDUNGEN.md zu Phase 6).

Pull Requests ansehen, erstellen, prüfen und übernehmen gehört zum Kern. Dieses Feature ändert nur
den Ablauf beim Hochladen: Auf main fragt "Änderungen hochladen", in welchen Branch hochgeladen
wird, und danach bietet das Cockpit an, einen Pull Request zu erstellen. Den Ablauf selbst steuert
ui/sync_flow.py, weil er Rückfragen braucht.

Bis Phase 7 schaltet man es mit einer Aktion bei Code ein und aus.
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.platforms.base import Capability

FEATURE_ID = "branches_prs"

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="Branches und Pull Requests",
    description="Beim Hochladen fragt das Cockpit, in welchen Branch hochgeladen wird, und "
                "bietet danach einen Pull Request an. So kommen Änderungen nur über eine "
                "Prüfung in main.",
    requires_capabilities=(Capability.PULL_REQUESTS,),
    enabled_by_default=False,
    default_setting="branches_by_default",          # Grundeinstellung für neue Projekte
)
