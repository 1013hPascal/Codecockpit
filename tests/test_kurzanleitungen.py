"""Hilfefenster mit Kurzanleitungen (Wunsch des Nutzers vom 07.10.2026). Keine echte KI."""
from __future__ import annotations

import re

from PySide6.QtCore import Qt

from cockpit.core import core_actions, paths, quick_guides
from cockpit.core.actions import Target
from cockpit.core.features.registry import FeatureRegistry
from cockpit.ui import help_window
from tests.conftest import make_project, said

GUIDES = quick_guides.load(paths.resource_dir() / "anleitungen")


# -- Die Anleitungen selbst --------------------------------------------------------------------
def test_guides_are_complete_and_numbered():
    assert len(GUIDES) >= 30
    titles = [g.title for g in GUIDES]
    assert len(titles) == len(set(titles))
    for guide in GUIDES:
        assert guide.area in quick_guides.AREAS, guide.title
        numbers = [int(re.match(r"Schritt (\d+):", s).group(1)) for s in guide.steps]
        assert numbers == list(range(1, len(numbers) + 1)), guide.title
        assert guide.keywords, guide.title


def test_every_named_action_exists(qtbot, make_services):
    """Zeigt eine Anleitung auf eine Aktion, die es nicht mehr gibt, fällt das hier auf."""
    from tests.test_phase10f import window
    services = make_services(FeatureRegistry.discover().all())
    win = window(qtbot, services)
    known = {a.id for a in core_actions.CORE_ACTIONS} | {a.id for a in win.controller.actions()}
    for manifest in services.registry.all():
        known |= {a.id for a in manifest.actions}
    missing = {(g.title, a) for g in GUIDES for a in g.actions if a not in known}
    assert missing == set()


def test_user_wishes_are_covered():
    """Die Themen aus dem Wunsch des Nutzers haben je eine Anleitung."""
    wanted = ["Ordner hinzufügen", "verschoben", "Sammlung", "Branch erstellen",
              "Release", "Pull Request stellen", "Commit", "README", "Lizenz", "Review",
              "Pull Request übernehmen", "in main", "hochladen", "holen", "Exe erstellen",
              "verwalten", "löschen", "KI verknüpfen", "Git"]
    for words in wanted:
        assert quick_guides.search(GUIDES, words), words


# -- Suche ---------------------------------------------------------------------------------------
def test_search_ranks_titles_first():
    found = quick_guides.search(GUIDES, "Branch erstellen")
    assert found[0].title == "Branch erstellen"
    assert quick_guides.search(GUIDES, "hoch")[0].title.startswith("Änderungen hochladen")
    assert quick_guides.search(GUIDES, "xyzxyz") == []


def test_without_search_the_area_comes_first():
    releases = quick_guides.search(GUIDES, "", "releases")
    assert releases[0].area == "releases"
    start = quick_guides.search(GUIDES, "", "start")
    assert start[0].title == "Projektordner hinzufügen"


def test_good_match_or_ai():
    assert quick_guides.good_match(GUIDES, "Lizenz hinzufügen").title == "Lizenz hinzufügen"
    assert quick_guides.good_match(GUIDES, "Wie ändere ich die Farbe des Himmels") is None


# -- Fenster -------------------------------------------------------------------------------------
def opened(qtbot, make_services, projects_root, target=None):
    from tests.test_phase10f import window
    services = make_services()
    project = services.projects.add(make_project(projects_root, "Tagebuch", exe=True))
    win = window(qtbot, services)
    if target is not None:
        win.project_list.select(target, project.id)
    win.open_help()
    qtbot.addWidget(win.help_window)
    return win, win.help_window


def test_f1_opens_a_window_that_is_not_modal(qtbot, make_services, projects_root):
    win, helper = opened(qtbot, make_services, projects_root, Target.RELEASES)
    assert helper.isVisible() and not helper.isModal()
    assert helper.windowTitle() == "Hilfe"
    assert helper.search.accessibleName() == "Suchen"
    assert helper.list.accessibleName() == "Anleitungen"
    assert helper.steps.accessibleName() == "Schritte" and helper.steps.isReadOnly()
    assert helper.area == "releases"
    assert helper.list.item(0).text() in {g.title for g in GUIDES if g.area == "releases"}
    assert helper.steps.toPlainText().startswith("Schritt 1:")
    win.open_help()                                         # dasselbe Fenster wieder vorn
    assert win.help_window is helper


def test_typing_filters_and_enter_jumps(qtbot, make_services, projects_root):
    _win, helper = opened(qtbot, make_services, projects_root)
    helper.search.setText("Lizenz")
    assert helper.list.item(0).text() == "Lizenz hinzufügen"
    assert "Lizenz …" in helper.steps.toPlainText()
    qtbot.keyClick(helper.search, Qt.Key.Key_Return)
    assert helper.focusWidget() is helper.list or helper.list.hasFocus()


def test_ask_shows_a_guide_when_one_fits(qtbot, make_services, projects_root, monkeypatch):
    _win, helper = opened(qtbot, make_services, projects_root)
    asked = []
    monkeypatch.setattr(helper, "ask_ai", asked.append)
    helper.search.setText("Lizenz hinzufügen")
    helper.ask()
    assert asked == [] and said("Passende Anleitung: Lizenz hinzufügen.")
    helper.search.setText("Wie ändere ich die Farbe des Himmels")
    helper.ask()
    assert asked == ["Wie ändere ich die Farbe des Himmels"]


def test_ai_answer_goes_into_the_steps(qtbot, make_services, projects_root):
    _win, helper = opened(qtbot, make_services, projects_root)
    helper.show_answer("Schritt 1: Öffnen Sie das Menü. Schritt 2: Wählen Sie KI.")
    assert helper.steps.toPlainText().splitlines()[0] == "Schritt 1: Öffnen Sie das Menü."
    assert said("Anleitung der KI da.")


def test_area_of_rows():
    class FakeList:
        def __init__(self, target):
            self.target = target

        def current_target(self):
            return self.target, 1

    class FakeWindow:
        def __init__(self, target):
            self.project_list = FakeList(target)

    assert help_window.area_of(FakeWindow(Target.CODE)) == "branch"
    assert help_window.area_of(FakeWindow(Target.LIST_FILTER)) == "start"
    assert help_window.area_of(FakeWindow(Target.REPOSITORY)) == "repository"
