"""Feature "Terminal-Erklärung" (Konzept 10.16, Teilschritt 8b).

Schlägt im eingebauten Terminal ein Befehl fehl, schreibt die KI in das Feld "Erklärung der KI",
warum das wahrscheinlich passiert ist und was man tun kann. Die KI bekommt den Befehl, den
Rückgabewert und das Ende der Ausgabe, ohne Tokens und höchstens so viele Zeichen, wie die
Grundeinstellung erlaubt. Die Oberfläche steht in ui/terminal_dialog.py.
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import AIToolChoice

FEATURE_ID = "terminal_explain"

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="Terminal-Erklärung",
    description="Schlägt im Terminal ein Befehl fehl, erklärt die KI, warum, und was Sie tun "
                "können. Die Erklärung steht im Terminal mit Tab nach dem Befehlsfeld.",
    requires_services=("ai",),
    settings=(AIToolChoice("tool", "KI für Erklärungen"),),
    enabled_by_default=True,
)
