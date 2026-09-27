"""Ablauf-Motor, Rückfragen, Adapter-Register und Dienste."""
from __future__ import annotations

import threading

import pytest

from cockpit.adapters import registry as adapters
from cockpit.adapters.base import Adapter
from cockpit.automation.none import NoAutomation
from cockpit.core.errors import Cancelled, CockpitError
from cockpit.core.flows.engine import Flow, FlowContext, ProjectBusy
from cockpit.core.flows.hooks import Hook
from cockpit.core.flows.questions import ChoiceQuestion, ScriptedAsker
from cockpit.core.flows.step import Step, StepResult
from cockpit.core.secret import Secret
from cockpit.vault.base import entry_name
from tests.conftest import (FAKE_TOKEN, FakeAI, FakeAutomation, FakeEmail, FakePlatform,
                            FakeVault, make_project, manifest)


def ok(text=""):
    return lambda context: StepResult(True, text)


def fail(text):
    return lambda context: StepResult(False, text, "technische Details")


def step(id, hook, run, order=100, flows=()):
    return Step(id, id.replace("_", " ").capitalize(), hook, run, order, flows=flows)


PUSH = Flow("push_changes", "Änderungen hochladen", (
    step("check", Hook.BEFORE_PUSH, ok(), order=10),
    step("push", Hook.PUSH, ok("Hochgeladen.")),
))


@pytest.fixture
def setup(make_services, projects_root):
    def factory(features=()):
        services = make_services(list(features))
        project = services.projects.add(make_project(projects_root, "PDF-Chat"))
        return services, project
    return factory


def run(services, project, flow=PUSH, asker=None, cancel=None):
    progress = []
    context = FlowContext(services, project, asker or ScriptedAsker(),
                          cancel_event=cancel or threading.Event())
    summary = services.flows.run(flow, context, lambda n, t, text: progress.append(text))
    return summary, progress


# -- Reihenfolge und Zählung --------------------------------------------------------------
def test_feature_steps_are_sorted_and_counted(setup):
    features = [
        manifest("exe", "Exe", enabled_by_default=True,
                 steps=(step("build_exe", Hook.AFTER_PUSH, ok("Exe gebaut.")),)),
        manifest("readme", "README", enabled_by_default=True,
                 steps=(step("check_readme", Hook.BEFORE_PUSH, ok(), order=50),)),
        manifest("off", "Aus", steps=(step("never", Hook.AFTER_PUSH, ok()),)),
    ]
    services, project = setup(features)
    summary, progress = run(services, project)
    assert progress == ["Schritt 1 von 4: Check", "Schritt 2 von 4: Check readme",
                        "Schritt 3 von 4: Push", "Schritt 4 von 4: Build exe"]
    assert summary.completed
    assert summary.text() == "Fertig. Hochgeladen. Exe gebaut."


def test_steps_can_be_limited_to_flows(setup):
    features = [manifest("x", enabled_by_default=True,
                         steps=(step("only_new", Hook.AFTER_PUSH, ok(), flows=("new_project",)),))]
    services, project = setup(features)
    assert [s.id for s in services.flows.steps_for(PUSH, project)] == ["check", "push"]


# -- Fehler ---------------------------------------------------------------------------------
def test_failure_before_push_aborts(setup):
    features = [manifest("readme", enabled_by_default=True,
                         steps=(step("check_readme", Hook.BEFORE_PUSH, fail("README fehlt.")),))]
    services, project = setup(features)
    summary, progress = run(services, project)
    assert summary.aborted_at.id == "check_readme"
    assert len(progress) == 2                                # Push lief nicht
    assert summary.text() == ("Nicht fertig. Schritt 2 von 3 ist fehlgeschlagen: "
                              "Check readme. README fehlt.")


def test_failure_after_push_continues(setup):
    features = [manifest("exe", enabled_by_default=True, steps=(
        step("build_exe", Hook.AFTER_PUSH, fail("Der Exe-Test ist fehlgeschlagen."), order=1),
        step("release", Hook.AFTER_PUSH, ok("Release veröffentlicht."), order=2)))]
    services, project = setup(features)
    summary, progress = run(services, project)
    assert summary.completed and len(progress) == 4
    assert summary.text() == ("Fertig, aber ein Schritt hat nicht geklappt: Build exe. "
                              "Der Exe-Test ist fehlgeschlagen. Hochgeladen. "
                              "Release veröffentlicht.")


def test_exceptions_in_steps_become_results(setup):
    def boom(context):
        raise RuntimeError(f"kaputt {FAKE_TOKEN}")

    def expected(context):
        raise CockpitError("Keine Verbindung.", "Timeout")

    features = [manifest("x", enabled_by_default=True, steps=(
        step("a", Hook.AFTER_PUSH, boom, order=1), step("b", Hook.AFTER_PUSH, expected, order=2)))]
    services, project = setup(features)
    summary, _ = run(services, project)
    texts = [r.text for _, r in summary.failures]
    assert texts == ["Unerwarteter Fehler.", "Keine Verbindung."]


def test_cancel_stops_the_flow(setup):
    cancel = threading.Event()

    def cancel_now(context):
        cancel.set()
        return StepResult(True)

    flow = Flow("f", "Test", (step("a", Hook.BEFORE_PUSH, cancel_now, order=1),
                              step("b", Hook.BEFORE_PUSH, ok(), order=2)))
    services, project = setup()
    summary, progress = run(services, project, flow, cancel=cancel)
    assert summary.cancelled and len(progress) == 1
    assert summary.text() == "Abgebrochen. Test wurde nicht fertig."


def test_questions_reach_the_asker(setup):
    def choose(context):
        answer = context.ask(ChoiceQuestion("README", "Vorschlag übernehmen?",
                                            ("Übernehmen", "Bearbeiten", "Überspringen")))
        context.data["choice"] = answer
        return StepResult(True)

    flow = Flow("f", "Test", (step("a", Hook.BEFORE_PUSH, choose),))
    services, project = setup()
    asker = ScriptedAsker(2)
    context = FlowContext(services, project, asker)
    services.flows.run(flow, context)
    assert context.data["choice"] == 2
    assert asker.questions[0].title == "README"


def test_asking_after_cancel_raises(setup):
    services, project = setup()
    context = FlowContext(services, project, ScriptedAsker(True))
    context.cancel_event.set()
    with pytest.raises(Cancelled):
        context.ask(ChoiceQuestion("x", "y", ("a",)))


def test_only_one_flow_per_project(setup):
    services, project = setup()
    started, release = threading.Event(), threading.Event()

    def wait(context):
        started.set()
        release.wait(5)
        return StepResult(True)

    flow = Flow("f", "Test", (step("a", Hook.BEFORE_PUSH, wait),))
    thread = threading.Thread(target=run, args=(services, project, flow))
    thread.start()
    assert started.wait(5)
    assert services.flows.is_busy(project)
    with pytest.raises(ProjectBusy, match="läuft schon ein Vorgang"):
        run(services, project, flow)
    release.set()
    thread.join(5)
    assert not services.flows.is_busy(project)


# -- Adapter ----------------------------------------------------------------------------------
def test_adapter_registry_loads_lazily_and_explains_unknown():
    assert adapters.adapter_class("automation", "none") is NoAutomation
    with pytest.raises(CockpitError, match="gibt es nicht"):
        adapters.adapter_class("ai", "gibt_es_nicht")
    adapters.register("ai", "fake", FakeAI)
    try:
        assert adapters.adapter_class("ai", "fake") is FakeAI
        assert "fake" in adapters.names("ai")
    finally:
        adapters.unregister("ai", "fake")


def test_broken_adapter_path_is_explained():
    adapters.register("ai", "broken", "cockpit.gibt.es.nicht:Klasse")
    try:
        with pytest.raises(CockpitError, match="lässt sich nicht laden"):
            adapters.adapter_class("ai", "broken")
    finally:
        adapters.unregister("ai", "broken")


def test_fakes_fulfil_every_interface():
    for cls in (FakePlatform, FakeAI, FakeVault, FakeAutomation, FakeEmail, NoAutomation):
        adapter = cls()
        assert isinstance(adapter, Adapter)
        assert adapter.test_connection().text


def test_no_automation_explains_itself():
    automation = NoAutomation()
    assert not automation.test_connection().ok
    with pytest.raises(CockpitError, match="keine Automation"):
        automation.call_webhook("x", {})


def test_vault_stores_secrets():
    vault = FakeVault()
    name = entry_name("account", 1, "token")
    assert name == "codecockpit/account/1/token"
    vault.write(name, Secret(FAKE_TOKEN))
    assert vault.read(name).reveal() == FAKE_TOKEN
    assert vault.names() == [name]


def test_services_availability_and_privacy_rule(make_services):
    services = make_services()
    assert not services.service_availability("ai")
    assert not services.service_availability("automation")
    assert not services.service_availability("email")
    cloud = FakeAI(is_local=False)
    services = make_services(ai=cloud, automation=FakeAutomation(), email=FakeEmail())
    assert services.service_availability("ai") and services.service_availability("email")
    assert services.ai_for("commit_message").provider is cloud
    services.settings.update(ai_local_only=True)
    assert services.ai_for("commit_message") is None
