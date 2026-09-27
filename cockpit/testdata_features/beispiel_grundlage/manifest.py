"""Beispiel Grundlage: hat eigene Einstellungen und eine Aktion bei Code (nur Testdaten)."""
from cockpit.core.actions import Action, ActionContext, Target
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import Text, YesNo


def _greet(context: ActionContext) -> None:
    services = context.services
    text = services.features.setting("beispiel_grundlage", "greeting")
    loud = services.features.setting("beispiel_grundlage", "loud")
    context.announce(f"{text}{'!' if loud else '.'}")


MANIFEST = FeatureManifest(
    id="beispiel_grundlage",
    name="Beispiel Grundlage",
    description="Nur zum Testen. Bringt die Aktion „Beispiel-Gruß“ bei Code und zwei "
                "Einstellungen mit.",
    settings=(Text("greeting", "Gruß", "Hallo aus dem Beispiel", required=True),
              YesNo("loud", "Mit Ausrufezeichen", False)),
    actions=(Action("beispiel_gruss", "Beispiel-Gruß", Target.CODE, _greet, order=99),),
)
