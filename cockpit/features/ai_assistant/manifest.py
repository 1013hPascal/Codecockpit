"""Feature "KI-Assistent" (Konzept 10.1, Teilschritt 8c).

Der Knopf "Vorschlag der KI" (Alt+V) füllt Felder mit einem Vorschlag:
- "Änderungen hochladen": Was haben Sie geändert? und Beschreibung.
- "Pull Request erstellen": Titel und Beschreibung.
- "Auf GitHub hochladen": Kurzbeschreibung.
Die KI ist immer nur ein Vorschlag, Sie entscheiden. Sie bekommt nie den ganzen Code, sondern eine
vorbereitete Übersicht (context.py). Die Oberfläche steht in ui/ai_suggest.py.
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import AIToolChoice, Choice

FEATURE_ID = "ai_assistant"
LANGUAGES = ("Deutsch", "Englisch")

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="KI-Assistent",
    description="Schlägt Commit-Nachrichten, Titel und Beschreibung von Pull Requests und die "
                "Kurzbeschreibung neuer Projekte vor. Sie entscheiden, was Sie übernehmen.",
    requires_services=("ai",),
    settings=(AIToolChoice("tool", "KI für Vorschläge"),
              Choice("language", "Sprache der Vorschläge", "Deutsch", options=LANGUAGES)),
    enabled_by_default=True,
)
