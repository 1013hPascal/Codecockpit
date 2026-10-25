"""Feature "Erklärungen" (Wunsch des Nutzers vom 25.10.2026).

Ganz oben in der Projektliste, in den Aktionen und in den Menüs steht ein Eintrag "Erklärung". In
vielen Fenstern steht zuletzt der Knopf "Erklärung …". Er öffnet eine Liste mit kurzen Absätzen:
was man dort machen kann und welche Tasten dahin führen. Die Texte stehen in texts.py, die
Oberfläche in ui/explanations.py.

Ausschalten: das ganze Feature in der Feature-Verwaltung, einzelne Erklärungen in seinen
Einstellungen oder mit "Diese Erklärung nicht mehr anzeigen".
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import MultiChoice
from cockpit.features.explanations.texts import ALL_TITLES

FEATURE_ID = "explanations"
SHOWN = "shown"

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="Erklärungen",
    description="Ganz oben in Listen und Menüs steht ein Eintrag Erklärung, in Fenstern ein "
                "Knopf Erklärung. Er erklärt kurz, was man dort machen kann.",
    settings=(MultiChoice(SHOWN, "Erklärungen anzeigen für", default=ALL_TITLES,
                          options=ALL_TITLES),),
    enabled_by_default=True,
)
