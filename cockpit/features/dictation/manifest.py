"""Feature "Spracheingabe" (Konzept 10.15, Teilschritt 8d).

In jedes Textfeld des Cockpits diktieren: Strg+D startet und beendet, Strg+Umschalt+D bricht ab.
Kein Knopf, nur die Tasten (Wunsch des Nutzers). Die Spracherkennung macht Whisper lokal
(cockpit/ai/whisper.py), die Oberfläche steht in ui/dictation.py. Das Feature gilt für das ganze
Cockpit, nicht pro Projekt.
"""
from cockpit.ai.whisper import LANGUAGES
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import Choice, Number

FEATURE_ID = "dictation"

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="Spracheingabe",
    description="In jedes Textfeld diktieren. Strg+D startet und beendet die Aufnahme, "
                "Strg+Umschalt+D bricht ab. Die Sprache erkennt Whisper auf Ihrem Rechner.",
    requires_services=("speech",),
    settings=(Choice("language", "Sprache", "Deutsch", options=tuple(LANGUAGES)),
              Number("max_minutes", "Aufnahme endet von selbst nach so vielen Minuten", 10,
                     minimum=1, maximum=30)),
    enabled_by_default=True,
)
