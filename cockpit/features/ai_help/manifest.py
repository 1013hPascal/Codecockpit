"""Feature "KI-Hilfe" (Konzept 10.17, Teilschritt 8e).

Beantwortet Fragen zur Bedienung des Cockpits, zum Beispiel "Wo schalte ich Pull Requests ein?".
Grundlage sind die Anleitungen, die Einführungen der Features und eine Liste aller Menüs,
Tastenkürzel und Aktionen, die das Cockpit beim Fragen selbst erzeugt (Vorschlag aus Frage 22 zu
Phase 8). So ist sie auch nach neuen Features aktuell. Die Oberfläche steht in
ui/ai_help_dialog.py, erreichbar über Hilfe, KI-Hilfe.
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import AIToolChoice

FEATURE_ID = "ai_help"

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="KI-Hilfe",
    description="Beantwortet Fragen zur Bedienung des Cockpits und nennt den Weg mit Tasten. "
                "Im Menü Hilfe unter KI-Hilfe.",
    requires_services=("ai",),
    settings=(AIToolChoice("tool", "KI für die Hilfe"),),
    enabled_by_default=True,
)
