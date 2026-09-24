from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import Number
from cockpit.core.flows.hooks import Hook
from cockpit.core.flows.step import Step, StepResult

MANIFEST = FeatureManifest(
    id="alpha",
    name="Alpha",
    description="Beispiel-Feature für Tests.",
    settings=(Number("wait", "Wartezeit in Sekunden", 10, minimum=1, maximum=60),),
    steps=(Step("alpha_step", "Alpha arbeitet", Hook.AFTER_PUSH,
                lambda context: StepResult(True, "Alpha fertig.")),),
    enabled_by_default=True,
)
