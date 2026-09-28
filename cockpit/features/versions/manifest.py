"""Feature "Versionen" (Konzept 10.3, Phase 9): Versionsnummern und Git-Tags beim Hochladen."""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import Text
from cockpit.core.flows.hooks import Hook
from cockpit.core.flows.step import Step
from cockpit.features.versions import steps

FEATURE_ID = steps.FEATURE_ID
FLOWS = ("push_changes",)

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="Versionen",
    description="Beim Hochladen fragt das Cockpit, ob es eine neue Version ist, und setzt die "
                "Nummer als Tag. Steht sie im Code, ändert es sie mit.",
    settings=(Text("version_file", "Datei mit der Versionsnummer, freiwillig. Leer: das Cockpit "
                   "sucht selbst nach __version__", ""),),
    steps=(Step("version_choose", "Version festlegen", Hook.BEFORE_PUSH, steps.choose, order=500,
                feature_id=FEATURE_ID, flows=FLOWS),
           Step("version_tag", "Version als Tag setzen", Hook.BEFORE_PUSH, steps.tag, order=950,
                feature_id=FEATURE_ID, flows=FLOWS),
           Step("version_push", "Version hochladen", Hook.PUSH, steps.push, order=30,
                feature_id=FEATURE_ID, flows=FLOWS)),
    enabled_by_default=False,
)
