"""Tresor (beide Speicherarten, Wechsel) und Konten."""
from __future__ import annotations

import json
import sqlite3

import pytest

from cockpit import testdata
from cockpit.core.accounts import account_types, find_type
from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret
from cockpit.core.services import Services
from cockpit.core.vault_service import NameIndex, move_entries
from cockpit.vault.base import VaultLocked
from cockpit.vault.vault_file import FileVault, check_new_password
from cockpit.vault.windows import WindowsVault
from tests.conftest import FAKE_TOKEN, FakeVault, MemoryKeyring, make_project

PASSWORD = Secret("ErfundenesMasterPasswort1")


def file_vault(tmp_path) -> FileVault:
    return FileVault(tmp_path / "vault.bin")


# -- Tresordatei ----------------------------------------------------------------------------
def test_file_vault_roundtrip_and_lock(tmp_path):
    vault = file_vault(tmp_path)
    assert not vault.exists()
    vault.create(PASSWORD)
    vault.write("codecockpit/account/1/token", Secret(FAKE_TOKEN))
    assert vault.read("codecockpit/account/1/token").reveal() == FAKE_TOKEN
    vault.lock()
    assert not vault.is_unlocked()
    with pytest.raises(VaultLocked):
        vault.read("codecockpit/account/1/token")
    again = file_vault(tmp_path)
    again.unlock(PASSWORD)
    assert again.names() == ["codecockpit/account/1/token"]


def test_file_vault_contains_no_plaintext(tmp_path):
    vault = file_vault(tmp_path)
    vault.create(PASSWORD)
    vault.write("codecockpit/account/7/token", Secret(FAKE_TOKEN))
    raw = (tmp_path / "vault.bin").read_bytes()
    assert FAKE_TOKEN.encode() not in raw
    assert b"account/7" not in raw                     # auch die Namen sind verschlüsselt
    assert PASSWORD.reveal().encode() not in raw


def test_wrong_password_is_explained(tmp_path):
    file_vault(tmp_path).create(PASSWORD)
    with pytest.raises(CockpitError, match="Master-Passwort ist falsch"):
        file_vault(tmp_path).unlock(Secret("falsch-falsch"))


def test_changed_header_is_detected(tmp_path):
    file_vault(tmp_path).create(PASSWORD)
    path = tmp_path / "vault.bin"
    content = json.loads(path.read_text())
    content["kdf"]["p"] = 2
    path.write_text(json.dumps(content))
    with pytest.raises(CockpitError):
        file_vault(tmp_path).unlock(PASSWORD)


def test_broken_or_missing_file_is_explained(tmp_path):
    with pytest.raises(CockpitError, match="nicht gefunden"):
        file_vault(tmp_path).unlock(PASSWORD)
    (tmp_path / "vault.bin").write_text("kaputt")
    with pytest.raises(CockpitError, match="beschädigt"):
        file_vault(tmp_path).unlock(PASSWORD)


def test_change_password(tmp_path):
    vault = file_vault(tmp_path)
    vault.create(PASSWORD)
    vault.write("a", Secret("wert-a"))
    with pytest.raises(CockpitError, match="bisherige"):
        vault.change_password(Secret("falsch-falsch"), Secret("NeuesPasswort2"))
    vault.change_password(PASSWORD, Secret("NeuesPasswort2"))
    fresh = file_vault(tmp_path)
    with pytest.raises(CockpitError):
        fresh.unlock(PASSWORD)
    fresh.unlock(Secret("NeuesPasswort2"))
    assert fresh.read("a").reveal() == "wert-a"


def test_create_refuses_to_overwrite(tmp_path):
    file_vault(tmp_path).create(PASSWORD)
    with pytest.raises(CockpitError, match="schon eine Tresordatei"):
        file_vault(tmp_path).create(PASSWORD)


def test_new_password_rules():
    with pytest.raises(CockpitError, match="mindestens 8"):
        check_new_password(Secret("kurz"), Secret("kurz"))
    with pytest.raises(CockpitError, match="stimmen nicht"):
        check_new_password(Secret("langes-pass1"), Secret("langes-pass2"))
    check_new_password(Secret("langes-pass1"), Secret("langes-pass1"))


# -- Windows-Anmeldeinformationsverwaltung --------------------------------------------------
def test_windows_vault_uses_keyring_and_index(make_services, memory_keyring):
    vault = WindowsVault(NameIndex(make_services().database), service="Test")
    vault.write("codecockpit/account/1/token", Secret(FAKE_TOKEN))
    assert memory_keyring.entries[("Test", "codecockpit/account/1/token")] == FAKE_TOKEN
    assert vault.names() == ["codecockpit/account/1/token"]
    assert vault.read("codecockpit/account/1/token").reveal() == FAKE_TOKEN
    vault.delete("codecockpit/account/1/token")
    vault.delete("codecockpit/account/1/token")           # zweimal löschen schadet nicht
    assert vault.names() == [] and memory_keyring.entries == {}
    assert vault.test_connection().ok


def test_windows_vault_errors_are_explained(make_services):
    from keyring.errors import KeyringError

    class Broken(MemoryKeyring):
        def get_password(self, service, username):
            raise KeyringError("Zugriff verweigert")

    vault = WindowsVault(NameIndex(make_services().database), backend=Broken())
    with pytest.raises(CockpitError, match="abgelehnt"):
        vault.read("x")


# -- Tresor-Dienst und Wechsel ----------------------------------------------------------------
def test_vault_service_without_vault(make_services):
    services = make_services()
    assert services.vault.vault is None
    with pytest.raises(CockpitError, match="noch kein Tresor"):
        services.vault.read("x")


def test_vault_service_uses_configured_kind(make_services):
    services = make_services()
    services.use_vault(services.make_vault("windows"))
    assert services.settings.load().vault_kind == "windows"
    services.vault.write("n", Secret("wert-n"))
    reopened = Services(database=services.database, settings=services.settings,
                        projects=services.projects, registry=services.registry)
    assert reopened.vault.kind == "windows"
    assert reopened.vault.read("n").reveal() == "wert-n"


def test_vault_file_is_created_in_data_dir(make_services, home):
    services = make_services()
    vault = services.make_vault("vault_file")
    assert vault.path == home / "vault.bin"


@pytest.mark.parametrize("direction", ["windows_to_file", "file_to_windows"])
def test_move_entries_between_kinds(make_services, tmp_path, direction):
    index = NameIndex(make_services().database)
    windows = WindowsVault(index, service="Test")
    file = file_vault(tmp_path)
    file.create(PASSWORD)
    old, new = (windows, file) if direction == "windows_to_file" else (file, windows)
    old.write("codecockpit/account/1/token", Secret(FAKE_TOKEN))
    old.write("codecockpit/account/2/password", Secret("app-passwort"))
    assert move_entries(old, new, index) == 2
    assert new.read("codecockpit/account/1/token").reveal() == FAKE_TOKEN
    assert old.read("codecockpit/account/1/token") is None
    assert sorted(index.list()) == ["codecockpit/account/1/token",
                                    "codecockpit/account/2/password"]


def test_failed_move_changes_nothing(make_services):
    class Forgetful(FakeVault):
        def read(self, name):
            return Secret("etwas anderes")

    old = FakeVault()
    old.write("a", Secret("wert-a"))
    new = Forgetful()
    with pytest.raises(CockpitError, match="nichts verändert"):
        move_entries(old, new, NameIndex(make_services().database))
    assert old.read("a").reveal() == "wert-a"
    assert new.entries == {}


def test_move_needs_unlocked_vaults(make_services, tmp_path):
    file = file_vault(tmp_path)
    file.create(PASSWORD)
    file.lock()
    with pytest.raises(VaultLocked):
        move_entries(file, FakeVault(), NameIndex(make_services().database))


# -- Konten ---------------------------------------------------------------------------------
@pytest.fixture
def store(make_services, account_adapter):
    services = make_services(vault=FakeVault())
    return services, find_type("platform", account_adapter.kind)


def test_account_types_need_fields(account_adapter):
    labels = [t.label for t in account_types()]
    assert "Kontotest, Plattform" in labels
    assert not any(label.startswith("Keine Automation") for label in labels)


def test_create_account_keeps_secret_out_of_database(store):
    services, account_type = store
    account = services.accounts.create(account_type, "GitHub privat",
                                       {"username": "1013hPascal", "team": "Blau",
                                        "token": Secret(FAKE_TOKEN)})
    assert account.label == "GitHub privat, Kontotest, Plattform, 1013hPascal"
    assert account.url == "https://git.example"
    assert account.extra == {"team": "Blau"}
    assert services.vault.read(f"codecockpit/account/{account.id}/token").reveal() == FAKE_TOKEN
    assert FAKE_TOKEN.encode() not in services.database.path.read_bytes()
    values = services.accounts.values(account)
    assert values["token"].reveal() == FAKE_TOKEN and values["username"] == "1013hPascal"


def test_required_fields_are_checked(store):
    services, account_type = store
    with pytest.raises(CockpitError, match="Anzeigenamen"):
        services.accounts.create(account_type, " ", {"username": "a", "token": Secret("t")})
    with pytest.raises(CockpitError, match="Token ausfüllen"):
        services.accounts.create(account_type, "A", {"username": "a", "token": Secret("")})
    assert services.accounts.all() == []


def test_update_keeps_empty_secret(store):
    services, account_type = store
    account = services.accounts.create(account_type, "A", {"username": "a",
                                                            "token": Secret(FAKE_TOKEN)})
    updated = services.accounts.update(account, "B", {"username": "b", "token": Secret("")})
    assert updated.display_name == "B" and updated.username == "b"
    assert services.accounts.values(updated)["token"].reveal() == FAKE_TOKEN


def test_delete_removes_secrets_and_project_link(store, projects_root):
    services, account_type = store
    account = services.accounts.create(account_type, "A", {"username": "a",
                                                            "token": Secret(FAKE_TOKEN)})
    project = services.projects.add(make_project(projects_root, "P"))
    services.database.execute("UPDATE projects SET account_id = ? WHERE id = ?",
                              (account.id, project.id))
    services.accounts.delete(account)
    assert services.accounts.all() == []
    assert services.vault.index.list() == []
    assert services.projects.get(project.id).account_id is None


def test_delete_needs_unlocked_vault(make_services, account_adapter, tmp_path):
    vault = file_vault(tmp_path)
    vault.create(PASSWORD)
    services = make_services(vault=vault)
    account = services.accounts.create(find_type("platform", account_adapter.kind), "A",
                                       {"username": "a", "token": Secret(FAKE_TOKEN)})
    vault.lock()
    with pytest.raises(VaultLocked):
        services.accounts.delete(account)
    assert services.accounts.all()                        # nichts gelöscht


def test_connection_test(store):
    services, account_type = store
    good = services.accounts.create(account_type, "Gut", {"username": "a",
                                                           "token": Secret(FAKE_TOKEN)})
    bad = services.accounts.create(account_type, "Schlecht", {"username": "b",
                                                               "token": Secret("falsch-1")})
    assert services.accounts.test(good).text == "Angemeldet als a."
    result = services.accounts.test(bad)
    assert not result.ok and result.details == "HTTP 401"


def test_unknown_account_type_is_explained(store, account_adapter):
    services, account_type = store
    account = services.accounts.create(account_type, "A", {"username": "a",
                                                            "token": Secret("t-1234")})
    from cockpit.adapters import registry
    registry.unregister("platform", account_adapter.kind)
    assert "unbekannte Art" in services.accounts.get(account.id).label
    assert not services.accounts.test(account).ok


# -- Testdaten --------------------------------------------------------------------------------
def test_testdata_removes_only_its_own_vault_entries(tmp_path, memory_keyring):
    database = tmp_path / "cockpit.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE vault_names (name TEXT PRIMARY KEY)")
    connection.execute("INSERT INTO vault_names VALUES ('codecockpit/account/1/token')")
    connection.commit()
    connection.close()
    memory_keyring.set_password(testdata.VAULT_SERVICE, "codecockpit/account/1/token", "x")
    memory_keyring.set_password("CodeCockpit", "codecockpit/account/1/token", "echt")
    assert testdata.remove_old_vault_entries(database) == 1
    assert memory_keyring.entries == {("CodeCockpit", "codecockpit/account/1/token"): "echt"}
    database.unlink()                                    # Datei ist wieder freigegeben


def test_test_platform():
    from cockpit.testdata_platform import GOOD_TOKEN, TestPlatform
    assert TestPlatform.from_account({"username": "a", "token": Secret(GOOD_TOKEN)}) \
        .test_connection().ok
    assert not TestPlatform.from_account({"username": "a", "token": Secret("x")}) \
        .test_connection().ok


def test_testdata_in_use_is_explained_and_nothing_is_deleted(tmp_path, monkeypatch):
    from pathlib import Path
    from cockpit.core.errors import CockpitError
    base = tmp_path / "Testdaten"
    testdata.prepare(base)

    def locked(self, target):
        raise PermissionError("[WinError 32] benutzt")

    monkeypatch.setattr(Path, "rename", locked)
    with pytest.raises(CockpitError, match="noch von einem offenen CodeCockpit"):
        testdata.prepare(base)
    assert (base / "Projekte" / "PDF-Chat" / "Code").is_dir()
