"""Feature "Exe-Erstellung" (Konzept 10.4, Phase 10).

Bauen, Veröffentlichen und die Einrichtungsprüfung. Der Eintrag Exe, Exe starten, Exe-Datei wählen,
Exe aus dem Release holen und Exe-Ordner öffnen gehören zum Kern (fragen/phase-10.md, Frage 2).
Der Ablauf steht in core/exe.py, die Oberfläche in ui/exe_flow.py.
"""
from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.settings_fields import Number

FEATURE_ID = "exe_build"

MANIFEST = FeatureManifest(
    id=FEATURE_ID,
    name="Exe-Erstellung",
    description="Baut aus dem Code eine Exe mit PyInstaller, testet sie und ersetzt die alte erst "
                "danach. Veröffentlicht die Exe auf GitHub und prüft die Einrichtung.",
    settings=(Number("test_seconds", "Start-Test: so viele Sekunden muss die Exe laufen", 10,
                     minimum=3, maximum=120),),
    enabled_by_default=True,
)
