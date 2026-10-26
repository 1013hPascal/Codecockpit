"""Signaltöne zur Wahl, Paketliste gespeichert, Aktualisieren und Filtern oben, Warteton bei
Paketaktionen (Wunsch des Nutzers vom 24.10.2026)."""
from __future__ import annotations

import threading
import wave
from datetime import datetime
from pathlib import Path

import pytest

from cockpit.features.packages import base, cache, catalog, usage
from cockpit.features.packages.base import PIP, WINGET, Package
from cockpit.features.packages.manifest import MANIFEST
from cockpit.ui import sounds
from tests.conftest import said


@pytest.fixture(autouse=True)
def default_sounds():
    sounds.configure()
    yield
    sounds.configure()


# -- Auswahl der Töne -----------------------------------------------------------------------------
def test_each_kind_has_its_own_sounds(tmp_path, monkeypatch):
    from cockpit.core import paths
    monkeypatch.setattr(paths, "cache_dir", lambda: tmp_path)
    ids = [c.id for options in sounds.CHOICES.values() for c in options]
    assert len(ids) == len(set(ids))                            # nie derselbe Ton in zwei Arten
    data = {}
    for kind, options in sounds.CHOICES.items():
        assert len(options) >= 4                                # genug Auswahl
        names = [c.name for c in options]
        assert len(names) == len(set(names))
        for choice in options:
            if choice.make is not None:
                data[choice.id] = choice.make()
    assert len(set(data.values())) == len(data)                 # auch der Klang ist verschieden
    for kind in sounds.CHOICES:
        path = sounds.sound_file(kind)
        with wave.open(str(path)) as wav:
            assert wav.getframerate() == sounds.RATE and wav.getnframes() > 0


def test_melodies_are_offered():
    names = [c.name for options in sounds.CHOICES.values() for c in options]
    assert any("Melodie" in n for n in names) and any("Dreiklang" in n for n in names)


def test_defaults_are_lower_than_before():
    """Der Nutzer fand die alten Töne zu hoch. Die alten stehen am Ende, "wie früher"."""
    for kind, options in sounds.CHOICES.items():
        assert sounds.DEFAULTS[kind] == options[0].id
        assert "früher" not in options[0].name
        assert any("früher" in c.name for c in options)


def test_configure_and_unknown_ids():
    sounds.configure(work="work_wood", ai="ai_chord", done="done_gong")
    assert sounds.chosen(sounds.TICK) == "work_wood"
    assert sounds.chosen(sounds.DONE) == "done_gong"
    sounds.configure(work="ai_chord", ai="gibt es nicht")      # fremde Art: Vorgabe
    assert sounds.chosen(sounds.TICK) == sounds.DEFAULTS[sounds.TICK]
    assert sounds.chosen(sounds.AI_TICK) == sounds.DEFAULTS[sounds.AI_TICK]


def test_no_sound_choice_has_no_file():
    sounds.configure(done="done_none")
    assert sounds.sound_file(sounds.DONE) is None


def test_muted_plays_nothing(monkeypatch):
    calls = []
    monkeypatch.setattr(sounds, "_sound", calls.append)
    sounds.configure(muted=True)
    sounds._play(sounds.TICK)
    sounds.preview("work_wood")                                 # Anhören geht trotzdem
    assert calls == ["work_wood"]
    sounds.configure()
    sounds._play(sounds.DONE)
    assert calls == ["work_wood", sounds.DONE]


def test_settings_have_sound_fields(make_services):
    services = make_services([])
    settings = services.settings.load()
    assert settings.sounds_off is False and settings.sound_work == ""
    services.settings.update(sounds_off=True, sound_ai="ai_knock")
    settings = services.settings.load()
    assert settings.sounds_off is True and settings.sound_ai == "ai_knock"


# -- Fenster Signaltöne ---------------------------------------------------------------------------
def test_sounds_dialog_saves_and_previews(qtbot, make_services, monkeypatch):
    from cockpit.ui.sounds_dialog import SoundsDialog
    heard = []
    monkeypatch.setattr(sounds, "preview", heard.append)
    services = make_services([])
    dialog = SoundsDialog(services)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Signaltöne"
    assert dialog.off.text() == "Alle Signaltöne &aus" and not dialog.off.isChecked()
    assert heard == []                                          # beim Öffnen still
    work = dialog.boxes[sounds.TICK]
    assert work.accessibleName() == "Programm arbeitet"
    assert dialog.boxes[sounds.AI_TICK].accessibleName() == "KI arbeitet"
    assert dialog.boxes[sounds.DONE].accessibleName() == "Erfolg"
    work.setCurrentIndex(2)
    assert heard == [sounds.CHOICES[sounds.TICK][2].id]
    dialog.off.setChecked(True)
    dialog.save()
    settings = services.settings.load()
    assert settings.sounds_off and settings.sound_work == sounds.CHOICES[sounds.TICK][2].id
    assert settings.sound_done == sounds.DEFAULTS[sounds.DONE]
    assert sounds.muted() and said("Signaltöne aus.")
    again = SoundsDialog(services)
    qtbot.addWidget(again)
    assert again.off.isChecked() and again.boxes[sounds.TICK].currentIndex() == 2


def test_sounds_dialog_cancel_changes_nothing(qtbot, make_services, monkeypatch):
    from cockpit.ui.sounds_dialog import SoundsDialog
    monkeypatch.setattr(sounds, "preview", lambda _id: None)
    services = make_services([])
    dialog = SoundsDialog(services)
    qtbot.addWidget(dialog)
    dialog.off.setChecked(True)
    dialog.reject()
    assert services.settings.load().sounds_off is False and not sounds.muted()


def test_settings_menu_has_sounds(qtbot, make_services):
    from tests.test_phase10f import window
    win = window(qtbot, make_services([]))
    texts = [a.text() for menu in win.menuBar().actions() if menu.text() == "&Einstellungen"
             for a in menu.menu().actions()]
    assert "&Signaltöne …" in texts


# -- Gespeicherte Paketliste ----------------------------------------------------------------------
def packages() -> list[Package]:
    return [Package(PIP, "requests", "2.31.0", key="requests", place="Python 3.14",
                    location=Path("python.exe"), latest="2.32.3", checked=True,
                    added=datetime(2026, 10, 1, 9, 30), size=1234),
            Package(PIP, "six", "1.16.0", place="Projekt Tagebuch", owner="Tagebuch",
                    cockpit=True, used_by=("Tagebuch",), pinned=True,
                    extra={"revisions": ["abc"]})]


def test_cache_round_trip(make_services):
    database = make_services([]).database
    assert cache.load(database) == ({}, set(), None)
    cache.save(database, {PIP: packages(), WINGET: None}, {PIP, WINGET},
               now=datetime(2026, 10, 24, 18, 5))
    data, checked, saved = cache.load(database)
    assert set(data) == {PIP} and checked == {PIP}
    assert saved == datetime(2026, 10, 24, 18, 5)
    assert [p.line() for p in data[PIP]] == [p.line() for p in packages()]
    assert data[PIP][0].location == Path("python.exe") and data[PIP][1].used_by == ("Tagebuch",)


def test_cache_unreadable_is_empty(make_services):
    database = make_services([]).database
    database.set_value(cache.KEY, {"saved": "kein Datum", "data": {}})
    assert cache.load(database) == ({}, set(), None)


@pytest.fixture
def counted_catalog(monkeypatch):
    loads = []
    monkeypatch.setattr(catalog, "sources", lambda: [catalog.SourceInfo(PIP, True)])

    def load(source, projects, db, cancel=None):
        loads.append(source)
        return [Package(**{**p.__dict__}) for p in packages()]
    monkeypatch.setattr(catalog, "load", load)
    monkeypatch.setattr(catalog, "check", lambda *a, **k: None)
    monkeypatch.setattr(usage, "mark", lambda *a, **k: None)
    return loads


def opened(qtbot, services):
    from cockpit.ui import package_dialogs
    dialog = package_dialogs.SourcesDialog(services)
    qtbot.addWidget(dialog)
    if not any(v is not None for v in dialog.data.values()):
        dialog.refresh_all()
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10000)
    return dialog


def test_nothing_is_read_until_refresh(qtbot, make_services, counted_catalog):
    """Wunsch des Nutzers vom 26.10.2026: Gelesen wird nur mit "Paketübersicht aktualisieren",
    auch beim allerersten Öffnen nicht."""
    from cockpit.ui import package_dialogs
    dialog = package_dialogs.SourcesDialog(make_services([MANIFEST]))
    qtbot.addWidget(dialog)
    assert dialog.task is None and counted_catalog == []
    assert dialog.list.currentRow() == package_dialogs.REFRESH_ROW
    assert dialog.list.item(2).text() == "Kritisch, noch nicht gelesen"
    assert dialog.list.item(3).text() == "Python-Bibliotheken (pip), noch nicht gelesen"
    dialog.open_current()                                       # Enter auf der obersten Zeile
    assert dialog.list.item(0).text() == "Paketübersicht aktualisieren, läuft …"
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10000)
    assert counted_catalog == [PIP]
    assert dialog.list.item(0).text() == "Paketübersicht aktualisieren"


def test_list_is_kept_until_refresh(qtbot, make_services, counted_catalog):
    services = make_services([MANIFEST])
    first = opened(qtbot, services)
    assert counted_catalog == [PIP]
    assert ". Stand: " in first.list.item(1).text()
    second = opened(qtbot, services)                            # wie nach einem Neustart
    assert counted_catalog == [PIP]                             # nicht neu gelesen
    assert second.list.item(3).text().startswith("Python-Bibliotheken (pip), 2 Einträge")
    assert second.list.currentRow() == 3                        # auf der ersten Quelle
    assert PIP in second.checked
    second.refresh_all()
    assert said("Pakete werden neu gelesen.")
    qtbot.waitUntil(lambda: second.task is None, timeout=10000)
    assert counted_catalog == [PIP, PIP]


def test_critical_row_and_show_only_outdated(qtbot, make_services, counted_catalog,
                                             monkeypatch):
    from cockpit.ui import package_dialogs
    sources = opened(qtbot, make_services([MANIFEST]))
    sources.data[PIP][0].warning = "Sicherheitslücke bekannt, behoben in 9.9.9"
    sources.fill()
    assert sources.list.item(2).text() == "Kritisch: 1 Bibliothek mit Sicherheitslücke"
    critical = package_dialogs.PackagesDialog(sources, base.CRITICAL)
    qtbot.addWidget(critical)
    assert critical.windowTitle() == "Kritisch: Bibliotheken mit Sicherheitslücke: 1 Eintrag"
    assert [p.name for p in critical.shown] == [sources.data[PIP][0].name]
    dialog = package_dialogs.PackagesDialog(sources, PIP)
    qtbot.addWidget(dialog)
    layout = dialog.layout()
    assert layout.itemAt(0).layout().itemAt(0).widget() is dialog.show_button
    assert dialog.show_button.accessibleName() == "Anzeigen: Alle"
    asked = []
    monkeypatch.setattr(package_dialogs, "choose_from_list", lambda parent, title, name, items,
                        current: asked.append((items, current)) or 1)
    dialog.choose_show()
    assert asked == [(["Alle", "Nur veraltete"], 0)]
    assert dialog.show_button.accessibleName() == "Anzeigen: Nur veraltete"
    assert dialog.shown and all(p.outdated for p in dialog.shown)
    assert len(dialog.shown) < len(sources.data[PIP])


def test_buttons_on_top_and_filter(qtbot, make_services, counted_catalog, monkeypatch):
    from cockpit.ui import package_dialogs
    dialog = opened(qtbot, make_services([MANIFEST]))
    layout = dialog.layout()
    assert layout.itemAt(0).layout().itemAt(0).widget() is dialog.filter
    assert dialog.list.item(0).text() == package_dialogs.REFRESH_TEXT
    assert dialog.chosen_filter == base.ALL == "Alle"
    asked = []
    monkeypatch.setattr(package_dialogs, "choose_from_list", lambda parent, title, name, items,
                        current: asked.append((items, current)) or 2)
    dialog.choose_filter()
    assert asked == [(["Alle", "Nur im Cockpit", "Nur auf dem Rechner, nicht im Cockpit"], 0)]
    assert dialog.filter.accessibleName() == "Filtern: Nur auf dem Rechner, nicht im Cockpit"
    assert dialog.list.item(3).text().startswith("Python-Bibliotheken (pip), 1 Eintrag")
    assert said("Filter: Nur auf dem Rechner, nicht im Cockpit.")
    again = opened(qtbot, make_services([MANIFEST]))
    assert again.chosen_filter == base.ALL                      # neu geöffnet: wieder Alle


def test_pin_is_kept_in_the_saved_list(qtbot, make_services, counted_catalog, monkeypatch):
    from cockpit.ui import package_dialogs
    services = make_services([MANIFEST])
    sources = opened(qtbot, services)
    dialog = package_dialogs.PackagesDialog(sources, PIP)
    qtbot.addWidget(dialog)
    requests = next(p for p in sources.data[PIP] if p.name == "requests")
    dialog.list.setCurrentRow([p.name for p in dialog.shown].index("requests"))

    def set_pinned(db, package, on, cancel=None):
        package.pinned = on
        return "Festgehalten."
    monkeypatch.setattr(catalog, "set_pinned", set_pinned)
    dialog.toggle_pin()
    qtbot.waitUntil(lambda: requests.pinned and not dialog.worker.busy, timeout=5000)
    qtbot.waitUntil(lambda: any(p.name == "requests" and p.pinned
                                for p in cache.load(services.database)[0][PIP]), timeout=5000)


# -- Warteton bei Paketaktionen -------------------------------------------------------------------
def wait_for_thread(qtbot, task) -> None:
    """Bis der Thread wirklich zu Ende ist. Das Ergebnis kommt schon kurz vorher an. Schließt der
    Test das Fenster dazwischen, bricht Qt den ganzen Testlauf ab."""
    from shiboken6 import isValid
    qtbot.waitUntil(lambda: not isValid(task) or task.isFinished(), timeout=5000)
    if isValid(task):
        task.wait(5000)
    qtbot.wait(50)                                              # "fertig" noch zustellen



def test_package_action_plays_work_and_done(qtbot, make_services, counted_catalog, monkeypatch,
                                            played):
    from cockpit.ui import package_dialogs
    sources = opened(qtbot, make_services([MANIFEST]))
    dialog = package_dialogs.PackagesDialog(sources, PIP)
    qtbot.addWidget(dialog)
    monkeypatch.setattr(sounds, "TICK_MS", 50)
    gate = threading.Event()

    def work():
        gate.wait(5)
        return "Fertig."
    dialog.run(work, "Wird aktualisiert.")
    qtbot.waitUntil(lambda: sounds.TICK in played, timeout=3000)
    task = dialog.worker.task
    gate.set()
    wait_for_thread(qtbot, task)
    qtbot.waitUntil(lambda: played[-1] == sounds.DONE, timeout=5000)
    assert played[0] == sounds.START
    qtbot.waitUntil(lambda: sources.task is None, timeout=10000)


def test_package_action_error_plays_error(qtbot, make_services, counted_catalog, monkeypatch,
                                          played):
    from cockpit.core.errors import CockpitError
    from cockpit.ui import package_dialogs
    monkeypatch.setattr(package_dialogs, "show_error", lambda *a, **k: None, raising=False)
    from cockpit.ui import repo_dialog_parts
    monkeypatch.setattr(repo_dialog_parts, "show_error", lambda *a, **k: None)
    sources = opened(qtbot, make_services([MANIFEST]))
    dialog = package_dialogs.PackagesDialog(sources, PIP)
    qtbot.addWidget(dialog)

    gate = threading.Event()

    def work():
        gate.wait(5)
        raise CockpitError("pip ging nicht")
    dialog.run(work, "Wird gelöscht.")
    task = dialog.worker.task
    gate.set()
    wait_for_thread(qtbot, task)
    qtbot.waitUntil(lambda: sounds.ERROR in played, timeout=3000)
    assert played == [sounds.START, sounds.ERROR]
