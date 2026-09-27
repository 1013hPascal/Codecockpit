"""Phase 7: Feature-Verwaltung global und pro Projekt, Einführung beim ersten Einschalten.

Geprüft wird mit den Beispiel-Features aus cockpit/testdata_features: "Beispiel Grundlage" (mit
Einstellungen und einer Aktion) und "Beispiel Aufbau" (braucht die Grundlage).
"""
from __future__ import annotations

import pytest

from cockpit.core.features.manifest import FeatureManifest
from cockpit.core.features.registry import FeatureRegistry
from cockpit.core.projects import read_config
from cockpit.features.branches_prs.manifest import MANIFEST as PRS
from cockpit.ui import features_dialogs, text_dialog
from tests.conftest import make_project, said

DEMO = FeatureRegistry.discover("cockpit.testdata_features").all()
BASE, BUILD = "beispiel_grundlage", "beispiel_aufbau"
AI_FEATURE = FeatureManifest("ki_test", "KI-Test", "Braucht KI.", requires_services=("ai",),
                             introduction="")


@pytest.fixture
def services(make_services):
    return make_services(manifests=[*DEMO, PRS, AI_FEATURE])


@pytest.fixture
def intros(monkeypatch):
    """Einführungen mitschreiben statt anzeigen."""
    shown = []

    class FakeText:
        def __init__(self, title, text, name, parent=None):
            shown.append((title, text))

        def exec(self):
            return 0

    monkeypatch.setattr(text_dialog, "TextDialog", FakeText)
    return shown


def rows(dialog) -> list[str]:
    return [dialog.list.item(i).text() for i in range(dialog.list.count())]


def select(dialog, feature_id: str) -> None:
    dialog.list.setCurrentRow([m.id for m in dialog.manifests].index(feature_id))


def check(dialog, feature_id: str, on: bool = True) -> None:
    from PySide6.QtCore import Qt
    row = [m.id for m in dialog.manifests].index(feature_id)
    dialog.list.item(row).setCheckState(Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)


# -- Kern -----------------------------------------------------------------------------------------
def test_demo_features_are_valid():
    assert {m.id for m in DEMO} == {BASE, BUILD}
    assert all(m.problems() == [] for m in DEMO)
    assert FeatureRegistry([*DEMO]).dependents(BASE) == [BUILD]


def test_default_features_and_old_setting(services):
    features = services.features
    assert features.default_features() == set()
    services.settings.update(branches_by_default=True)          # alter Wert aus Phase 6
    assert features.default_features() == {"branches_prs"}
    features.set_default_features({BASE, "gibt-es-nicht"})
    assert features.default_features() == {BASE}                 # die Vorauswahl gilt allein
    assert services.settings.load().default_features == [BASE]


def test_grundeinstellungen_have_no_branches_entry():
    from cockpit.core.settings import setting_fields
    assert "branches_by_default" not in {f.key for f in setting_fields()}


def test_project_follows_default_until_changed(services, projects_root):
    services.projects.add(make_project(projects_root, "Tagebuch"))
    project = services.projects.all()[0]
    features = services.features
    features.set_default_features({BASE})
    assert features.follows_default(project)
    assert features.project_features(project) == {BASE}
    assert features.project_count(BASE) == 1
    features.set_project_features(project, {BUILD, BASE})
    assert not features.follows_default(project)
    features.set_default_features(set())
    assert features.project_features(project) == {BASE, BUILD}   # fest in cockpit.toml
    assert sorted(read_config(project.code_dir)["features"]["enabled"]) == [BUILD, BASE]


def test_needs_and_availability_without_switch(services):
    features = services.features
    assert features.needs(BUILD) == ["Beispiel Grundlage"]
    assert features.needs("branches_prs") == ["Plattform mit Pull Requests"]
    assert features.needs("ki_test") == ["KI"]
    features.set_globally_enabled("ki_test", False)
    state = features.availability_without_switch("ki_test")
    assert not state.available and state.reason.startswith("Benötigt KI.")
    assert features.availability_without_switch(BUILD).available


def test_intro_seen_is_remembered(services):
    features = services.features
    assert not features.intro_seen(BASE)
    features.mark_intro_seen(BASE)
    assert features.intro_seen(BASE) and not features.intro_seen(BUILD)


def test_upload_writes_features_into_cockpit_toml(tmp_path):
    from cockpit.core import upload
    from tests.conftest import FakePlatform
    code = tmp_path / "Code"
    code.mkdir()
    (code / "main.py").write_text("x\n", encoding="utf-8")
    spec = upload.UploadSpec("Neu", license=upload.NO_LICENSE, features={BUILD, BASE})
    upload.prepare(code, "Neu", spec, FakePlatform(), "T", "t@example.org", None)
    assert sorted(read_config(code)["features"]["enabled"]) == [BUILD, BASE]


# -- Feature-Verwaltung -----------------------------------------------------------------------------
def test_global_dialog_lines_and_info(qtbot, services, projects_root):
    services.projects.add(make_project(projects_root, "Tagebuch"))
    services.features.set_default_features({BASE})
    dialog = features_dialogs.GlobalFeaturesDialog(services)
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.windowTitle() == "Feature-Verwaltung: 4 Features"
    assert rows(dialog)[0] == "Beispiel Aufbau, eingeschaltet"
    assert rows(dialog)[1] == "Beispiel Grundlage, eingeschaltet, in 1 Projekt aktiv"
    assert rows(dialog)[3].startswith("KI-Test, eingeschaltet, nicht verfügbar: Benötigt KI.")
    select(dialog, BUILD)
    info = [dialog.info.item(i).text() for i in range(dialog.info.count())]
    assert info == ["Nur zum Testen. Braucht das Feature „Beispiel Grundlage“.",
                    "Braucht: Beispiel Grundlage.", "Für neue Projekte: aus.",
                    "In 0 Projekten eingeschaltet."]
    assert not dialog.default_box.isChecked() and not dialog.settings_button.isVisible()
    select(dialog, BASE)
    assert dialog.default_box.isChecked() and dialog.settings_button.isVisible()
    assert dialog.list.accessibleName() == "Features"
    assert dialog.info.accessibleName() == "Beschreibung"


def test_global_dialog_saves_switches_defaults_and_shows_intro(qtbot, services, intros):
    features = services.features
    features.set_globally_enabled(BUILD, False)
    dialog = features_dialogs.GlobalFeaturesDialog(services)
    qtbot.addWidget(dialog)
    assert rows(dialog)[0] == "Beispiel Aufbau, ausgeschaltet"
    check(dialog, BUILD)
    assert rows(dialog)[0] == "Beispiel Aufbau, eingeschaltet"
    check(dialog, "ki_test", False)
    select(dialog, BUILD)
    dialog.default_box.setChecked(True)
    dialog.save()
    assert features.globally_enabled(BUILD) and not features.globally_enabled("ki_test")
    assert features.default_features() == {BUILD}
    assert said("Feature-Verwaltung gespeichert.")
    assert [title for title, _ in intros] == ["Einführung: Beispiel Aufbau"]
    assert "Es braucht das Feature „Beispiel Grundlage“." in intros[0][1]
    assert features.intro_seen(BUILD)


def test_feature_settings_dialog(qtbot, services, monkeypatch):
    base = services.registry.get(BASE)
    dialog = features_dialogs.FeatureSettingsDialog(services, base)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Einstellungen: Beispiel Grundlage"
    assert dialog.form.values() == {"greeting": "Hallo aus dem Beispiel", "loud": False}
    monkeypatch.setattr(dialog.form, "values", lambda skip=frozenset(): {"greeting": "Moin",
                                                                          "loud": True})
    dialog.save()
    assert services.features.setting(BASE, "greeting") == "Moin"
    assert services.features.setting(BASE, "loud") is True
    assert said("Einstellungen für Beispiel Grundlage gespeichert.")


# -- Features eines Projekts ------------------------------------------------------------------
def project_dialog(qtbot, services, projects_root):
    services.projects.add(make_project(projects_root, "Tagebuch"))
    project = services.projects.all()[0]
    dialog = features_dialogs.ProjectFeaturesDialog(services, project)
    qtbot.addWidget(dialog)
    return project, dialog


def test_project_dialog_adds_dependencies(qtbot, services, projects_root, intros, monkeypatch):
    services.features.set_globally_enabled("ki_test", False)
    project, dialog = project_dialog(qtbot, services, projects_root)
    assert dialog.windowTitle() == "Features von Tagebuch: folgt der Vorauswahl"
    assert rows(dialog) == ["Beispiel Aufbau, aus", "Beispiel Grundlage, aus",
                            "Branches und Pull Requests, aus"]         # ohne KI-Test
    questions = []
    monkeypatch.setattr(features_dialogs, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or True)
    check(dialog, BUILD)
    dialog.save()
    text, buttons = questions[0]
    assert text.startswith("Beispiel Aufbau benötigt Beispiel Grundlage. Beispiel Grundlage "
                           "ist für dieses Projekt ausgeschaltet und wird mit eingeschaltet.")
    assert text.endswith("Die Auswahl steht danach in der Datei cockpit.toml im Ordner Code "
                         "und wird mit hochgeladen. Speichern?")
    assert buttons == {"yes": "Speichern", "no": "Abbrechen"}
    assert services.features.project_features(project) == {BASE, BUILD}
    assert said("Features von Tagebuch gespeichert.")
    assert [t for t, _ in intros] == ["Einführung: Beispiel Aufbau",
                                      "Einführung: Beispiel Grundlage"]


def test_project_dialog_takes_dependents_along(qtbot, services, projects_root, monkeypatch):
    services.features.set_globally_enabled("ki_test", False)
    services.projects.add(make_project(projects_root, "Tagebuch"))
    project = services.projects.all()[0]
    services.features.set_project_features(project, {BASE, BUILD, "ki_test"})
    for feature_id in (BASE, BUILD):
        services.features.mark_intro_seen(feature_id)
    dialog = features_dialogs.ProjectFeaturesDialog(services, project)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Features von Tagebuch: eigene Auswahl"
    questions = []
    monkeypatch.setattr(features_dialogs, "confirm",
                        lambda p, t, text, **k: questions.append(text) or True)
    check(dialog, BASE, False)
    dialog.save()
    assert questions[0].startswith("Ohne Beispiel Grundlage geht auch Beispiel Aufbau aus.")
    assert services.features.project_features(project) == {"ki_test"}   # versteckt, bleibt


def test_project_dialog_without_changes(qtbot, services, projects_root, monkeypatch):
    project, dialog = project_dialog(qtbot, services, projects_root)
    monkeypatch.setattr(features_dialogs, "confirm", lambda *a, **k: pytest.fail("keine Frage"))
    dialog.save()
    assert said("Nichts geändert.")
    assert services.features.follows_default(project)             # cockpit.toml unverändert


def test_project_dialog_escape_changes_nothing(qtbot, services, projects_root, monkeypatch):
    project, dialog = project_dialog(qtbot, services, projects_root)
    monkeypatch.setattr(features_dialogs, "confirm", lambda *a, **k: False)
    check(dialog, BASE)
    dialog.save()
    assert services.features.follows_default(project)


# -- Menü, Aktionen, Hochladen ---------------------------------------------------------------
def test_menu_and_project_action(qtbot, services, projects_root):
    from cockpit.core.actions import Target
    from cockpit.ui.main_window import MainWindow
    services.projects.add(make_project(projects_root, "Tagebuch"))
    project = services.projects.all()[0]
    win = MainWindow(services)
    qtbot.addWidget(win)
    titles = [a.text() for a in win.menuBar().actions()]
    assert titles[:3] == ["&Datei", "&Features", "K&onten"]
    features_menu = win.menuBar().actions()[1].menu()
    assert [a.text() for a in features_menu.actions()] == ["Feature-&Verwaltung …"]
    win.reload_projects(refresh=False)
    win.project_list.select(Target.PROJECT, project.id)
    assert "Features dieses Projekts …" in [e.label for e in win.current_entries()]
    # Die Aktion des Features erscheint bei Code nur, wenn es aktiv ist
    win.project_list.select(Target.CODE, project.id)
    assert "Beispiel-Gruß" not in [e.label for e in win.current_entries()]
    services.features.set_project_features(project, {BASE})
    assert "Beispiel-Gruß" in [e.label for e in win.current_entries()]
    services.features.set_globally_enabled(BASE, False)            # global aus: verschwindet
    assert "Beispiel-Gruß" not in [e.label for e in win.current_entries()]


def test_project_action_without_features(qtbot, make_services, projects_root):
    from cockpit.core.actions import Target
    from cockpit.ui.main_window import MainWindow
    services = make_services()
    services.projects.add(make_project(projects_root, "Tagebuch"))
    project = services.projects.all()[0]
    win = MainWindow(services)
    qtbot.addWidget(win)
    win.reload_projects(refresh=False)
    win.project_list.select(Target.PROJECT, project.id)
    labels = [e.label for e in win.current_entries()]
    assert ("Features dieses Projekts …, nicht verfügbar: Es ist kein Feature eingeschaltet. "
            "Das geht im Menü Features.") in labels


def test_upload_dialog_offers_features(qtbot):
    from cockpit.ui import upload_dialogs
    dialog = upload_dialogs.UploadDialog("Hochladen", "Neu", "GitHub", "tester", [], True, "MIT",
                                         None, [(BASE, "Beispiel Grundlage"),
                                                (BUILD, "Beispiel Aufbau")], {BASE})
    qtbot.addWidget(dialog)
    assert dialog.form.values()["features"] == ["Beispiel Grundlage"]
    dialog.check()
    assert dialog.spec.features == {BASE}


def test_global_dialog_tab_order(qtbot, services):
    dialog = features_dialogs.GlobalFeaturesDialog(services)
    qtbot.addWidget(dialog)
    dialog.show()
    select(dialog, BASE)                                           # mit Einstellungen
    seen, widget = [], dialog.list
    for _ in range(6):
        widget = widget.nextInFocusChain()
        while not widget.isVisible() or widget.focusPolicy() == 0:
            widget = widget.nextInFocusChain()
        seen.append(widget)
    assert seen == [dialog.info, dialog.default_box, dialog.intro_button,
                    dialog.settings_button, dialog.save_button, dialog.cancel_button]
