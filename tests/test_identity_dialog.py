"""Git-Identität nach dem Anlegen eines Plattform-Kontos (Wunsch des Nutzers, 28.09.2026).

Alle Geheimnisse sind erfunden.
"""
from __future__ import annotations

from cockpit.core.accounts import find_type
from cockpit.core.secret import Secret
from tests.conftest import FAKE_TOKEN, FakeVault, said


def platform_account(services, account_adapter):
    services.vault.vault = FakeVault()
    account_type = find_type("platform", account_adapter.kind)
    return services.accounts.create(account_type, "Kontotest", {
        "username": "tester", "url": "https://git.example", "token": Secret(FAKE_TOKEN)})


def test_identity_dialog_takes_the_noreply_address(qtbot, make_services, account_adapter):
    from cockpit.ui.identity_dialog import GitIdentityDialog
    services = make_services()
    account = platform_account(services, account_adapter)
    dialog = GitIdentityDialog(services, account)
    qtbot.addWidget(dialog)
    assert dialog.form.fields["git_email"].focus.accessibleName() == \
        "Git-E-Mail-Adresse für Commits"
    dialog.take_noreply()
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10000)
    assert dialog.form.fields["git_email"].get() == "1+tester@users.noreply.example"
    assert said("Adresse übernommen: 1+tester@users.noreply.example")
    dialog.form.fields["git_name"].set("Tester")
    dialog.save()
    settings = services.settings.load()
    assert (settings.git_name, settings.git_email) == ("Tester", "1+tester@users.noreply.example")


def test_skip_changes_nothing(qtbot, make_services, account_adapter):
    from cockpit.ui.identity_dialog import GitIdentityDialog
    services = make_services()
    services.settings.update(git_name="Alt", git_email="alt@example.org")
    dialog = GitIdentityDialog(services, platform_account(services, account_adapter))
    qtbot.addWidget(dialog)
    dialog.form.fields["git_name"].set("Neu")
    dialog.reject()
    assert services.settings.load().git_name == "Alt"


def test_new_platform_account_offers_the_identity(qtbot, make_services, account_adapter,
                                                  monkeypatch):
    from cockpit.ui import accounts_dialog, identity_dialog
    services = make_services()
    account = platform_account(services, account_adapter)
    shown = []

    class FakeEdit:
        def __init__(self, services, account_type, account, parent):
            self.saved = account_obj

        def exec(self):
            return 1

    class FakeIdentity:
        def __init__(self, services, saved, parent):
            shown.append(saved.display_name)

        def exec(self):
            return 0

    account_obj = account
    monkeypatch.setattr(accounts_dialog, "AccountEditDialog", FakeEdit)
    monkeypatch.setattr(identity_dialog, "GitIdentityDialog", FakeIdentity)
    monkeypatch.setattr(accounts_dialog, "account_types",
                        lambda: [find_type("platform", account_adapter.kind)])
    dialog = accounts_dialog.AccountsDialog(services)
    qtbot.addWidget(dialog)
    dialog.new_account()
    assert shown == ["Kontotest"]
