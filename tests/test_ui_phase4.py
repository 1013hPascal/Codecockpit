"""Oberfläche Phase 4: Anmeldung im Browser, GitHub-Konto im Assistenten, Hinweise zu Single Sign-On."""
from __future__ import annotations

import httpx
import pytest
from PySide6.QtWidgets import QApplication, QPushButton

from cockpit.adapters.base import TestResult
from cockpit.core.accounts import find_type
from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret
from cockpit.platforms import github
from cockpit.platforms.base import BrowserLogin
from cockpit.platforms.github import GitHubPlatform
from cockpit.ui import accounts_dialog as ad
from cockpit.ui import browser_login_dialog as bld
from cockpit.ui import setup_wizard as sw
from tests.conftest import FakeVault, said
from tests.test_github import TOKEN, FakeGitHub
from tests.test_ui import show_active


@pytest.fixture(autouse=True)
def no_blocking_dialogs(monkeypatch):
    """Meldungsfenster würden die Tests anhalten."""
    opened: list[str] = []
    monkeypatch.setattr(bld, "open_url", opened.append)
    monkeypatch.setattr(bld, "show_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(ad, "show_info", lambda *args, **kwargs: None)
    monkeypatch.setattr(ad, "show_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(sw, "confirm", lambda *args, **kwargs: True)
    monkeypatch.setattr(sw, "show_error", lambda *args, **kwargs: None)
    return opened


@pytest.fixture
def server(monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setattr(GitHubPlatform, "transport", httpx.MockTransport(fake.handler))
    return fake


class FakeLoginPlatform:
    """Plattform mit Anmeldung im Browser, ohne Netz."""
    display_name = "GitHub"
    fail = False

    def __init__(self, url="", token=None):
        self.token = token

    @classmethod
    def start_browser_login(cls, url=""):
        return BrowserLogin("ABCD-1234", "https://github.com/login/device", "geraet", 5, 900)

    @classmethod
    def wait_for_browser_login(cls, login, url="", cancel=None):
        if cls.fail:
            raise CockpitError("Die Anmeldung wurde im Browser abgelehnt.")
        return Secret(TOKEN)

    def current_user(self):
        from cockpit.platforms.base import User
        return User("1013hPascal", "94653295")


# -- Anmeldung im Browser -------------------------------------------------------------------
def test_browser_login_dialog_shows_code_opens_browser_and_returns_token(qtbot,
                                                                          no_blocking_dialogs):
    dialog = bld.BrowserLoginDialog(FakeLoginPlatform)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: dialog.token is not None, timeout=5000)
    assert dialog.token.reveal() == TOKEN
    assert dialog.username == "1013hPascal"
    assert dialog.steps.item(0).text() == "Ihr Code: ABCD-1234"
    assert QApplication.clipboard().text() == "ABCD-1234"
    assert no_blocking_dialogs == ["https://github.com/login/device"]
    assert said("Angemeldet als 1013hPascal.")


def test_browser_login_denied(qtbot, monkeypatch):
    monkeypatch.setattr(FakeLoginPlatform, "fail", True)
    dialog = bld.BrowserLoginDialog(FakeLoginPlatform)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: dialog.result() == 0 and not dialog.isVisible()
                    and said("abgelehnt"), timeout=5000)
    assert dialog.token is None


def test_browser_button_only_with_client_id(qtbot, make_services, monkeypatch):
    services = make_services(vault=FakeVault())
    account_type = find_type("platform", "github")
    monkeypatch.setattr(github, "CLIENT_ID", "")
    without = ad.AccountEditDialog(services, account_type)
    qtbot.addWidget(without)
    assert without.browser_button is None
    monkeypatch.setattr(github, "CLIENT_ID", "Ov23Test")
    dialog = ad.AccountEditDialog(services, account_type)
    qtbot.addWidget(dialog)
    assert dialog.browser_button.text() == "Im &Browser anmelden …"


def test_browser_login_leads_to_done_page_and_saves(qtbot, make_services, monkeypatch):
    services = make_services(vault=FakeVault())
    monkeypatch.setattr(github, "CLIENT_ID", "Ov23Test")
    dialog = ad.AccountEditDialog(services, find_type("platform", "github"))
    qtbot.addWidget(dialog)

    class Done:
        def __init__(self, *args):
            self.token, self.username = Secret(TOKEN), "1013hPascal"

        def exec(self):
            return True

    monkeypatch.setattr(bld, "BrowserLoginDialog", Done)
    dialog.browser_login()
    assert dialog.stack.currentWidget() is dialog.done_page
    assert dialog.done_info.item(0).text() == "Angemeldet als 1013hPascal."
    assert dialog.done_form.fields["display_name"].get() == "GitHub 1013hPascal"
    assert dialog.initial_focus_widget is dialog.done_info
    dialog.save_result()
    values = services.accounts.values(dialog.saved)
    assert values["token"].reveal() == TOKEN
    assert values["username"] == "1013hPascal"
    assert values["url"] == "https://github.com"


def test_token_way_has_no_username_field_and_fills_it_on_save(qtbot, make_services, server):
    services = make_services(vault=FakeVault())
    dialog = ad.AccountEditDialog(services, find_type("platform", "github"))
    qtbot.addWidget(dialog)
    assert "username" not in dialog.form.fields                 # trägt das Cockpit selbst ein
    dialog.form.fields["token"].focus.setText(TOKEN)
    dialog.save()                                               # testet erst, dann speichern
    qtbot.waitUntil(lambda: dialog.saved is not None, timeout=5000)
    assert services.accounts.values(dialog.saved)["username"] == "1013hPascal"


def test_token_way_does_not_save_a_rejected_token(qtbot, make_services, server):
    server.route("GET", "/user", 401, {"message": "Bad credentials"})
    services = make_services(vault=FakeVault())
    dialog = ad.AccountEditDialog(services, find_type("platform", "github"))
    qtbot.addWidget(dialog)
    dialog.form.fields["token"].focus.setText("falsch")
    dialog.save()
    qtbot.waitUntil(dialog.save_button.isEnabled, timeout=5000)
    assert dialog.saved is None and services.accounts.all() == []


def test_sso_result_offers_the_link(qtbot, monkeypatch, no_blocking_dialogs):
    monkeypatch.setattr(ad, "confirm", lambda *args, **kwargs: True)
    ad.show_test_result(None, TestResult(False, github.SSO_REQUIRED, "HTTP 403",
                                         link="https://github.com/orgs/firma/sso",
                                         link_text="Freigabeseite im Browser öffnen?"))
    assert no_blocking_dialogs == ["https://github.com/orgs/firma/sso"]


def test_ui_stays_usable_during_connection_test(qtbot, make_services, monkeypatch):
    """Das Netz läuft im Hintergrund: Die Schaltfläche ist gesperrt, bis der Test fertig ist."""
    services = make_services(vault=FakeVault())
    dialog = ad.AccountEditDialog(services, find_type("platform", "github"))
    qtbot.addWidget(dialog)
    dialog.form.fields["token"].focus.setText(TOKEN)

    def slow(request):
        import time
        time.sleep(0.3)
        return httpx.Response(401, json={"message": "Bad credentials"})

    monkeypatch.setattr(GitHubPlatform, "transport", httpx.MockTransport(slow))
    dialog.test_connection()
    assert not dialog.test_button.isEnabled()
    assert said("Verbindung wird getestet")
    qtbot.waitUntil(dialog.test_button.isEnabled, timeout=5000)


# -- Assistent ------------------------------------------------------------------------------
@pytest.fixture
def wizard(qtbot, make_services):
    services = make_services()
    services.use_vault(services.make_vault("windows"))       # Test-Tresor im Arbeitsspeicher
    dialog = sw.SetupWizard(services)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    return dialog, services


def go_to(dialog, title: str) -> None:
    while dialog.page.title != title:
        dialog.skip() if dialog.page.can_skip else dialog.next()


def test_wizard_github_page_counts_missing_accounts(wizard):
    dialog, services = wizard
    go_to(dialog, "Code-Plattformen wählen")
    dialog.next()                                             # GitHub ist angehakt
    assert dialog.heading.text() == "Schritt 5 von 8: Code-Plattformen einrichten"
    assert dialog.focusWidget() is dialog.page.list
    assert dialog.next_button.text() == "&Weiter (1 nicht eingerichtet)"
    services.accounts.create(find_type("platform", "github"), "GitHub privat",
                             {"username": "1013hPascal", "token": Secret(TOKEN)})
    dialog.page.on_show()
    dialog.update_next_text()
    assert dialog.next_button.text() == "&Weiter"
    dialog.next()
    assert dialog.page.title == "Projekte-Hauptordner"
    assert dialog.pages[4].done_text == "GitHub-Konto: GitHub privat, 1013hPascal."


def test_wizard_mnemonics_still_unique(wizard):
    import re
    dialog, _ = wizard
    for page in dialog.pages:
        texts = [b.text() for b in (dialog.back_button, dialog.skip_button, dialog.next_button,
                                    dialog.cancel_button)]
        texts += [w.text() for w in page.findChildren(QPushButton)]
        keys = [m.group(1).lower() for t in texts if (m := re.search(r"&(\w)", t))]
        assert len(keys) == len(set(keys)), (page.title, texts)


def test_token_guide_button_sits_before_the_token(qtbot, make_services, monkeypatch):
    from PySide6.QtCore import Qt
    services = make_services(vault=FakeVault())
    dialog = ad.AccountEditDialog(services, find_type("platform", "github"))
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    if dialog.token_button is not None:
        dialog.token_button.click()                          # Weg mit Token wählen
    assert dialog.guide_button.text() == "&Anleitung für den Token …"
    url = dialog.form.fields["url"].focus
    token = dialog.form.fields["token"].focus
    opened = []

    class FakeText:
        def __init__(self, title, text, name, parent=None):
            opened.append((title, text))

        def exec(self):
            return True

    monkeypatch.setattr(ad, "TextDialog", FakeText)
    dialog.show_guide()
    assert opened[0][0] == "GitHub-Token erstellen"
    assert "personal-access-tokens/new" in opened[0][1]
    url.setFocus()
    qtbot.keyClick(url, Qt.Key.Key_Tab)
    assert dialog.guide_button.hasFocus()
    qtbot.keyClick(dialog.guide_button, Qt.Key.Key_Tab)
    assert token.hasFocus()


def test_login_steps_mention_authorize(qtbot):
    dialog = bld.BrowserLoginDialog(FakeLoginPlatform)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: dialog.token is not None, timeout=5000)
    lines = [dialog.steps.item(r).text() for r in range(dialog.steps.count())]
    assert any("Authorize" in line for line in lines)


def test_new_github_account_offers_two_ways_after_the_explanation(qtbot, make_services,
                                                                  monkeypatch):
    """Test Phase 4: Erst die Erklärung, dann die Wahl: Im Browser oder mit Token."""
    from PySide6.QtCore import Qt
    monkeypatch.setattr(github, "CLIENT_ID", "Ov23Test")
    services = make_services(vault=FakeVault())
    dialog = ad.AccountEditDialog(services, find_type("platform", "github"))
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    assert dialog.stack.currentWidget() is dialog.choice_page
    qtbot.waitUntil(dialog.explanation.hasFocus, timeout=2000)
    lines = [dialog.explanation.item(r).text() for r in range(dialog.explanation.count())]
    assert lines[1] == "Es gibt zwei Wege. Mit Tab kommen Sie zu den beiden Knöpfen."
    assert any(line.startswith("Ihren Benutzernamen müssen Sie nicht") for line in lines)
    qtbot.keyClick(dialog.explanation, Qt.Key.Key_Tab)
    assert dialog.browser_button.hasFocus()
    qtbot.keyClick(dialog.browser_button, Qt.Key.Key_Tab)
    assert dialog.token_button.hasFocus()
    assert dialog.token_button.text() == "Mit &Token anmelden …"
    dialog.token_button.click()
    assert dialog.stack.currentWidget() is dialog.token_page
    assert dialog.form.fields["display_name"].focus.hasFocus()
    names = [dialog.form.fields[k].focus.accessibleName() for k in dialog.form.fields]
    assert names == ["Anzeigename", "Serveradresse", "Token"]
    dialog.back_button.click()
    assert dialog.stack.currentWidget() is dialog.choice_page


def test_explanation_without_browser_login(qtbot, make_services, monkeypatch):
    monkeypatch.setattr(github, "CLIENT_ID", "")
    services = make_services(vault=FakeVault())
    dialog = ad.AccountEditDialog(services, find_type("platform", "github"))
    qtbot.addWidget(dialog)
    assert dialog.stack.currentWidget() is dialog.token_page   # keine Wahl nötig
    assert dialog.initial_focus_widget is dialog.explanation
    lines = [dialog.explanation.item(r).text() for r in range(dialog.explanation.count())]
    assert not any("zwei Wege" in line for line in lines)


def test_editing_an_account_starts_in_the_first_field(qtbot, make_services):
    services = make_services(vault=FakeVault())
    account_type = find_type("platform", "github")
    account = services.accounts.create(account_type, "GitHub privat",
                                       {"username": "a", "token": Secret(TOKEN)})
    dialog = ad.AccountEditDialog(services, account_type, account)
    qtbot.addWidget(dialog)
    assert dialog.initial_focus_widget is dialog.form.fields["display_name"].focus
