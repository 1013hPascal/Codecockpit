"""Feature "README-Pflege" (Konzept 10.2, Phase 9).

README erstellen und aktualisieren, in mehreren Sprachen, und vor dem Hochladen prüfen. Die
Oberfläche steht in ui/readme_flow.py.
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import AIToolChoice, Choice, MultiChoice, YesNo
from cockpit.core.flows.hooks import Hook
from cockpit.core.flows.step import Step
from cockpit.features.readme import document as doc
from cockpit.features.readme import steps

FEATURE_ID = "readme"
OTHER_LANGUAGES = tuple(name for name in doc.LANGUAGES)

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="README-Pflege",
    description="README erstellen und aktualisieren, auch in weiteren Sprachen. Vor dem "
                "Hochladen prüft die KI, ob die README noch zu den Änderungen passt.",
    requires_services=("ai",),
    settings=(
        Choice("main_language", "Hauptsprache der README (für neue Projekte)", "Englisch",
               options=tuple(doc.LANGUAGES)),
        MultiChoice("languages", "Weitere Sprachen (für neue Projekte)", ["Deutsch"],
                    options=OTHER_LANGUAGES),
        MultiChoice("sections", "Abschnitte", list(doc.KEY_NAMES.values()),
                    options=tuple(doc.KEY_NAMES.values())),
        YesNo("check_on_upload", "Vor dem Hochladen prüfen, ob die README passt", True),
        AIToolChoice("tool", "KI für die README"),
    ),
    # Nach der Frage nach der Version (Versionen: 500), vor dem Commit (900)
    steps=(Step("readme_check", "README wird geprüft", Hook.BEFORE_PUSH, steps.check, order=600,
                feature_id=FEATURE_ID, flows=("push_changes",)),),
    enabled_by_default=False,
)
