"""Feature-System: Manifest, Register, Abhängigkeiten, Verfügbarkeit, Einstellungen."""
from __future__ import annotations

import pytest

from cockpit.core.features import settings_fields as sf
from cockpit.core.features.manager import FeatureDependencyError
from cockpit.core.features.registry import FeatureRegistry, FeatureRegistryError
from cockpit.core.errors import CockpitError
from cockpit.platforms.base import Capability
from tests.conftest import FakeAI, FakeAutomation, FakePlatform, make_project, manifest

# Aufbau wie im Konzept: Antwortentwürfe braucht Rückmeldungen und KI, Rückmeldungen braucht
# Automation, Releases braucht Versionen, Automation und die Fähigkeit Releases.
FEATURES = [
    manifest("versions", "Versionen", enabled_by_default=True),
    manifest("feedback", "Rückmeldungen", requires_services=("automation",)),
    manifest("drafts", "Antwortentwürfe", requires_features=("feedback",),
             requires_services=("ai",)),
    manifest("releases", "Releases", requires_features=("versions",),
             requires_services=("automation",), requires_capabilities=(Capability.RELEASES,)),
    manifest("exe", "Exe-Erstellung", enabled_by_default=True,
             settings=(sf.Number("wait", "Wartezeit", 10, minimum=3, maximum=120),)),
]


@pytest.fixture
def project(make_services, projects_root):
    folder = make_project(projects_root, "PDF-Chat")

    def factory(**kwargs):
        services = make_services(FEATURES, **kwargs)
        return services, services.projects.add(folder)

    return factory


# -- Register -----------------------------------------------------------------------------
def test_registry_rejects_duplicates_unknown_dependencies_and_cycles():
    with pytest.raises(FeatureRegistryError, match="doppelt"):
        FeatureRegistry([manifest("a"), manifest("a")])
    with pytest.raises(FeatureRegistryError) as info:
        FeatureRegistry([manifest("a", requires_features=("fehlt",))])
    assert "unbekannte Feature fehlt" in info.value.details
    with pytest.raises(FeatureRegistryError, match="Kreis"):
        FeatureRegistry([manifest("a", requires_features=("b",)),
                         manifest("b", requires_features=("a",))])


def test_manifest_problems_are_reported():
    with pytest.raises(FeatureRegistryError) as info:
        FeatureRegistry([manifest("Falsch-Name"), manifest("x", requires_services=("kaffee",))])
    assert "ungültig" in info.value.details
    assert "kaffee" in info.value.details


def test_registry_dependencies_and_dependents():
    registry = FeatureRegistry(FEATURES)
    assert registry.dependencies("drafts") == ["feedback"]
    assert registry.dependents("feedback") == ["drafts"]
    assert registry.dependents("versions") == ["releases"]
    assert [m.name for m in registry.all()][0] == "Antwortentwürfe"      # alphabetisch


def test_discover_loads_features_and_survives_broken_ones():
    registry = FeatureRegistry.discover("tests.sample_features")
    assert registry.ids() == ["alpha"]
    assert any("broken" in e for e in registry.load_errors)
    alpha = registry.get("alpha")
    assert alpha.introduction_text().startswith("# Alpha")
    assert alpha.steps[0].feature_id == "alpha"


def test_real_features_package_is_valid():
    registry = FeatureRegistry.discover()
    assert registry.load_errors == []
    for feature in registry.all():
        assert feature.introduction_text(), f"{feature.id} ohne Einführung"


# -- Global und pro Projekt ---------------------------------------------------------------
def test_global_switch(project):
    services, _ = project()
    manager = services.features
    assert manager.globally_enabled("exe")
    manager.set_globally_enabled("exe", False)
    assert not manager.globally_enabled("exe")
    assert "exe" not in [m.id for m in manager.visible_features()]


def test_project_defaults_come_from_features_and_settings(project):
    services, pdf = project()
    assert services.features.project_features(pdf) == {"versions", "exe"}
    services.settings.update(default_features=["exe"])
    assert services.features.project_features(pdf) == {"exe"}


def test_active_requires_enabled_and_available(project):
    services, pdf = project()
    manager = services.features
    assert manager.active("exe", pdf)
    manager.set_globally_enabled("exe", False)
    assert not manager.active("exe", pdf)


def test_missing_service_is_explained(project):
    services, pdf = project()
    state = services.features.availability("feedback", pdf)
    assert not state
    assert state.reason == "Benötigt Automation. Es ist keine Automation eingerichtet."
    services, pdf = project(automation=FakeAutomation())
    assert services.features.availability("feedback", pdf)


def test_dependency_switched_off_in_project_is_explained(project):
    services, pdf = project(automation=FakeAutomation(), ai=FakeAI())
    state = services.features.availability("drafts", pdf)
    assert state.reason == "Benötigt Rückmeldungen. Rückmeldungen ist für dieses Projekt " \
                           "ausgeschaltet."


def test_requirements_text_like_in_the_concept(project):
    services, pdf = project()
    assert services.features.requirements_text("drafts", pdf) == (
        "Antwortentwürfe benötigt Rückmeldungen, KI und Automation. "
        "Rückmeldungen ist für dieses Projekt ausgeschaltet. "
        "Es ist keine Text-KI eingerichtet. Das geht im Menü KI, KI-Verwaltung. "
        "Es ist keine Automation eingerichtet.")


def test_enable_asks_for_dependencies(project):
    services, pdf = project(automation=FakeAutomation(), ai=FakeAI())
    manager = services.features
    with pytest.raises(FeatureDependencyError) as info:
        manager.enable("drafts", pdf)
    assert [r.id for r in info.value.missing] == ["feedback"]
    assert manager.enable("drafts", pdf, with_dependencies=True) == ["feedback", "drafts"]
    assert manager.active("drafts", pdf) and manager.active("feedback", pdf)


def test_disable_takes_dependents_along(project):
    services, pdf = project(automation=FakeAutomation(), ai=FakeAI())
    manager = services.features
    manager.enable("drafts", pdf, with_dependencies=True)
    assert manager.enabled_dependents("feedback", pdf) == ["drafts"]
    assert manager.disable("feedback", pdf) == ["feedback", "drafts"]
    assert not manager.enabled_in_project("drafts", pdf)


def test_globally_disabled_dependency_blocks_enabling(project):
    services, pdf = project(automation=FakeAutomation(), ai=FakeAI())
    services.features.set_globally_enabled("feedback", False)
    with pytest.raises(CockpitError, match="Feature-Verwaltung"):
        services.features.enable("drafts", pdf, with_dependencies=True)


def test_capabilities_of_the_platform(project):
    services, pdf = project(automation=FakeAutomation())
    manager = services.features
    assert manager.availability("releases", pdf).reason == \
        "Das Projekt ist mit keiner Plattform verbunden."
    services.database.execute("UPDATE projects SET account_id = 1 WHERE id = ?", (pdf.id,))
    pdf = services.projects.get(pdf.id)
    services.platforms[1] = FakePlatform({Capability.CREATE_REPO})
    assert manager.availability("releases", pdf).reason == \
        "Die Plattform dieses Projekts unterstützt nicht: Releases."
    services.platforms[1] = FakePlatform()
    assert manager.availability("releases", pdf)


def test_feature_settings(project):
    services, _ = project()
    manager = services.features
    assert manager.setting("exe", "wait") == 10
    manager.set_setting("exe", "wait", 30)
    assert manager.setting("exe", "wait") == 30
    with pytest.raises(ValueError, match="höchstens 120"):
        manager.set_setting("exe", "wait", 500)
    with pytest.raises(KeyError):
        manager.setting("exe", "gibt_es_nicht")
