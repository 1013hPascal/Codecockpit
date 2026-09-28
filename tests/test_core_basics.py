"""Geheimnisse, Log, Datenbank, Einstellungen, Einstellungsfelder, Texte."""
from __future__ import annotations

import logging
import pickle
from pathlib import Path

import pytest

from cockpit.core import paths
from cockpit.core.database import MIGRATIONS, Database
from cockpit.core.features import settings_fields as sf
from cockpit.core.logging_setup import mask_secrets, setup_logging
from cockpit.core.secret import Secret
from cockpit.core.settings import SettingsStore, setting_fields
from cockpit.core.text import count, join_words, one_sentence_per_line
from tests.conftest import FAKE_TOKEN


# -- Geheimnisse ------------------------------------------------------------------------------
def test_secret_never_shows_its_value():
    secret = Secret("MeinGeheimesPasswort99")
    for text in (str(secret), repr(secret), f"{secret}", "%s" % secret, f"{[secret]}"):
        assert "MeinGeheimesPasswort99" not in text
    assert secret.reveal() == "MeinGeheimesPasswort99"


def test_secret_compares_and_cannot_be_pickled():
    assert Secret("abcdef") == Secret("abcdef")
    assert Secret("abcdef") != Secret("abcdeg")
    with pytest.raises(TypeError):
        pickle.dumps(Secret("abcdef"))


def test_log_masks_known_secrets_patterns_and_tracebacks(tmp_path):
    path = setup_logging(tmp_path / "logs")
    log = logging.getLogger("test.secrets")
    known = Secret("GeheimerWertAusDemTresor")
    log.info("Wert %s und %s", known.reveal(), FAKE_TOKEN)
    log.info("Header Authorization: Bearer abc.def.ghi und https://nutzer:passwort@example.com/x")
    log.info("Schlüssel sk-ErfundenerSchluessel1234567890")
    try:
        raise ValueError(f"Fehler mit {known.reveal()}")
    except ValueError:
        log.exception("Ausnahme")
    for handler in logging.getLogger().handlers:
        handler.flush()
    text = path.read_text(encoding="utf-8")
    for leaked in ("GeheimerWertAusDemTresor", FAKE_TOKEN, "abc.def.ghi", "passwort@",
                   "sk-ErfundenerSchluessel"):
        assert leaked not in text, leaked
    assert "***" in text


def test_mask_secrets_leaves_normal_text():
    assert mask_secrets("Schritt 3 von 5: Exe wird erstellt") == \
        "Schritt 3 von 5: Exe wird erstellt"


# -- Pfade --------------------------------------------------------------------------------
def test_data_dir_follows_environment(home):
    assert paths.data_dir() == home
    assert paths.database_path() == home / "cockpit.db"
    assert paths.logs_dir().is_dir()


def test_default_projects_root_is_parent_of_project_folder():
    here = paths.program_dir()
    # Seit 10f liegt der Code auch in Code\main oder in einem Branch-Ordner daneben
    project_dir = here.parent.parent if here.parent.name == "Code" else here.parent
    assert "Code" in (here.name, here.parent.name)
    assert paths.default_projects_root() == project_dir.parent


# -- Datenbank ----------------------------------------------------------------------------
def test_database_migrates_to_latest_version(tmp_path):
    db = Database(tmp_path / "a.db")
    assert db.version == len(MIGRATIONS)
    assert {"settings", "projects", "accounts", "vault_names", "features_global",
            "feature_settings"} <= set(db.table_names())
    db.close()
    again = Database(tmp_path / "a.db")                 # zweites Öffnen ändert nichts
    assert again.version == len(MIGRATIONS)
    again.close()


def test_database_values_roundtrip(tmp_path):
    db = Database(tmp_path / "a.db")
    db.set_value("x", {"a": [1, 2], "b": "Ä"})
    assert db.get_value("x") == {"a": [1, 2], "b": "Ä"}
    assert db.get_value("fehlt", 5) == 5
    db.close()


# -- Einstellungen ------------------------------------------------------------------------
def test_settings_defaults(tmp_path):
    store = SettingsStore(Database(tmp_path / "a.db"))
    settings = store.load()
    assert settings.default_private is True
    assert settings.default_license == "MIT"
    assert settings.projects_root == str(paths.default_projects_root())
    assert settings.default_features is None


def test_settings_update_checks_values(tmp_path):
    store = SettingsStore(Database(tmp_path / "a.db"))
    store.update(git_name="1013hPascal", git_email="1+x@users.noreply.github.com",
                 projects_root=str(tmp_path))
    assert store.load().git_name == "1013hPascal"
    with pytest.raises(ValueError, match="E-Mail"):
        store.update(git_email="keine-adresse")
    with pytest.raises(ValueError, match="gibt es nicht"):
        store.update(projects_root=str(tmp_path / "fehlt"))
    with pytest.raises(ValueError):
        store.update(default_license="Unbekannt")


def test_settings_ignore_broken_values(tmp_path):
    db = Database(tmp_path / "a.db")
    db.set_value("core.default_private", "kein bool")
    assert SettingsStore(db).load().default_private is True


def test_setting_fields_have_labels_and_unique_keys():
    fields = setting_fields()
    assert len({f.key for f in fields}) == len(fields)
    assert all(f.label for f in fields)


# -- Einstellungsfelder -----------------------------------------------------------------------
def test_fields_check_values():
    assert sf.Number("n", "Tage", 7, minimum=1, maximum=30).check("5") == 5
    with pytest.raises(ValueError, match="mindestens 1"):
        sf.Number("n", "Tage", 7, minimum=1).check(0)
    with pytest.raises(ValueError):
        sf.Number("n", "Tage").check(True)
    assert sf.TimeOfDay("t", "Uhrzeit").check("8:00") == "08:00"
    with pytest.raises(ValueError):
        sf.TimeOfDay("t", "Uhrzeit").check("25:00")
    assert sf.Weekday("w", "Wochentag").default == "Montag"
    assert sf.MultiChoice("m", "Sprachen", options=("Englisch", "Deutsch")).check(
        ["Deutsch", "Englisch"]) == ["Englisch", "Deutsch"]
    with pytest.raises(ValueError):
        sf.MultiChoice("m", "Sprachen", options=("Englisch",)).check(["Klingonisch"])
    assert sf.YesNo("y", "Ja?").default is False
    assert sf.Text("x", "Name", required=True).check(" A ") == "A"
    with pytest.raises(ValueError, match="ausfüllen"):
        sf.Text("x", "Name", required=True).check("")


def test_choice_rejects_wrong_default():
    with pytest.raises(ValueError):
        sf.Choice("c", "Wahl", "C", options=("A", "B"))
    assert sf.Choice("c", "Wahl", options=("A", "B")).default == "A"


def test_folder_field(tmp_path):
    assert sf.Folder("f", "Ordner").check(f'"{tmp_path}"') == str(tmp_path)
    with pytest.raises(ValueError):
        sf.Folder("f", "Ordner").check(str(tmp_path / "nein"))
    assert sf.Folder("f", "Ordner", must_exist=False).check(str(tmp_path / "nein"))


# -- Texte --------------------------------------------------------------------------------
def test_german_text_helpers():
    assert join_words(["A"]) == "A"
    assert join_words(["A", "B", "C"]) == "A, B und C"
    assert count(1, "Projekt", "Projekte") == "1 Projekt"
    assert count(0, "Projekt", "Projekte") == "0 Projekte"


def test_one_sentence_per_line_keeps_abbreviations():
    text = "Das ging schief. Bitte z. B. neu starten! Danach 2 Minuten warten."
    assert one_sentence_per_line(text).splitlines() == [
        "Das ging schief.", "Bitte z. B. neu starten!", "Danach 2 Minuten warten."]


def test_no_database_table_contains_secrets(make_services, projects_root):
    """Nach typischer Arbeit steht kein Test-Geheimnis in der Datenbank."""
    from tests.conftest import FakeVault, make_project
    vault = FakeVault()
    services = make_services(vault=vault)
    vault.write("codecockpit/account/1/token", Secret(FAKE_TOKEN))
    make_project(projects_root, "A")
    services.projects.scan(projects_root)
    services.settings.update(git_name="Test")
    raw = Path(services.database.path).read_bytes()
    assert FAKE_TOKEN.encode() not in raw
