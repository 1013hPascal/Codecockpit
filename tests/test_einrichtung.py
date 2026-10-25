"""Einrichtungsassistent, überarbeitet am 29.09.2026 (Wunsch des Nutzers).

Knöpfe erst nach vorn, dann zurück. Neue Seiten: Zugangsdaten schützen, Code-Plattformen wählen und
einrichten (mit Git-Identität im Konto-Fenster), Tipps und Videos. Alle Geheimnisse sind erfunden.
"""
from __future__ import annotations

import httpx
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from cockpit.core import core_actions, paths
from cockpit.core.accounts import find_type
from cockpit.core.secret import Secret
from cockpit.platforms import github, github_login
from cockpit.platforms.github import GitHubPlatform
from cockpit.ui import accounts_dialog as ad
from cockpit.ui import ai_dialogs
from cockpit.ui import browser_login_dialog as bld
from cockpit.ui import setup_pages
from cockpit.ui import setup_wizard as sw
from cockpit.ui import videos
from tests.conftest import FakeVault, said
from tests.test_github import TOKEN, FakeGitHub
from tests.test_phase8b import quiet_machine  # noqa: F401 (Fixture)
from tests.test_ui import show_active
from tests.conftest import patch_split

NOREPLY = "94653295+1013hPascal@users.noreply.github.com"


@pytest.fixture(autouse=True)
def no_blocking_dialogs(monkeypatch):
    """Meldungsfenster würden die Tests anhalten. Fehler werden gesammelt."""
    shown: list[str] = []
    for module in (sw, ad, videos):
        patch_split(monkeypatch, module, "show_error",
                    lambda parent, title, text, *args, **kwargs: shown.append(text))
    patch_split(monkeypatch, sw, "confirm", lambda *args, **kwargs: True)
    return shown


@pytest.fixture
def opened(monkeypatch):
    files: list = []
    monkeypatch.setattr(core_actions, "open_path", files.append)
    return files


@pytest.fixture
def wizard(qtbot, make_services, quiet_machine):  # noqa: F811
    services = make_services()
    services.use_vault(services.make_vault("windows"))       # Test-Tresor im Arbeitsspeicher
    dialog = sw.SetupWizard(services)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    return dialog, services


@pytest.fixture
def server(monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setattr(GitHubPlatform, "transport", httpx.MockTransport(fake.handler))
    return fake


def go_to(dialog, title: str) -> None:
    while dialog.page.title != title:
        dialog.skip() if dialog.page.can_skip else dialog.next()


def next_focus(widget):
    """Das nächste Steuerelement, das Tab erreicht."""
    widget = widget.nextInFocusChain()
    while not widget.isVisible() or widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
        widget = widget.nextInFocusChain()
    return widget


def texts(listing) -> list[str]:
    return [listing.item(r).text() for r in range(listing.count())]


# -- Knöpfe ---------------------------------------------------------------------------------
def test_forward_buttons_come_first(wizard):
    dialog, _ = wizard
    go_to(dialog, "Git")
    shown = [b for b in (dialog.next_button, dialog.skip_button, dialog.back_button,
                         dialog.cancel_button) if b.isVisible()]
    assert [b.text() for b in sorted(shown, key=lambda b: b.x())] == [
        "&Weiter", "Ü&berspringen", "&Zurück", "Abbrechen"]
    order, widget = [], dialog.next_button
    for _ in range(3):
        widget = widget.nextInFocusChain()
        while not (isinstance(widget, QPushButton) and widget.isVisible()):
            widget = widget.nextInFocusChain()
        order.append(widget)
    assert order == [dialog.skip_button, dialog.back_button, dialog.cancel_button]


def test_summary_has_finish_then_back(wizard):
    dialog, _ = wizard
    go_to(dialog, "Zusammenfassung")
    assert dialog.next_button.text() == "&Fertig"
    assert not dialog.skip_button.isVisible()
    assert dialog.back_button.isVisible()
    assert dialog.next_button.x() < dialog.back_button.x()


# -- Willkommen -----------------------------------------------------------------------------
def test_welcome_lists_features_and_offers_the_video(wizard, opened):
    dialog, _ = wizard
    page = dialog.page
    assert dialog.focusWidget() is page.text                  # zuerst der Text
    assert page.video_button.text() == "Kurze &Einführung anschauen"
    assert next_focus(page.text) is page.video_button         # Tab: Video, dann Weiter
    assert next_focus(page.video_button) is dialog.next_button
    lines = texts(page.text)
    assert lines[1].startswith("Das Cockpit hilft Ihnen, Ihre Code-Projekte zu verwalten")
    assert lines[2] == "In diesem Programm erwartet Sie:"
    assert lines[3:3 + len(sw.FEATURES)] == sw.FEATURES
    assert sw.FEATURES[0] == "Die wichtigsten Aktionen für Ihre Code-Projekte, ganz ohne Terminal"
    assert any(f.startswith("Neuigkeiten nach dem Start") for f in sw.FEATURES)
    assert any(line.startswith("Die Schritte: Zugangsdaten schützen, Git") for line in lines)
    assert lines[-1] == "Videos: erstellt mit Google NotebookLM"
    page.video_button.click()
    assert opened == [paths.resource_dir() / "erklärvideos" / videos.INTRO]
    assert said("Das Video wird geöffnet.")


def test_missing_video_shows_a_message(wizard, opened, no_blocking_dialogs, monkeypatch,
                                       tmp_path):
    monkeypatch.setattr(paths, "resource_dir", lambda: tmp_path)
    dialog, _ = wizard
    dialog.page.video_button.click()
    assert opened == []
    assert no_blocking_dialogs == ["Das Video wurde nicht gefunden."]


def test_videos_are_shipped():
    folder = paths.resource_dir() / videos.FOLDER
    assert (folder / videos.INTRO).is_file()
    assert (folder / videos.GIT_BASICS).is_file()
    spec = (paths.resource_dir() / "CodeCockpit.spec").read_text(encoding="utf-8")
    assert '"erklärvideos"' in spec


# -- Zugangsdaten schützen ------------------------------------------------------------------
def test_vault_page_explains_why(wizard):
    dialog, _ = wizard
    dialog.next()
    page = dialog.page
    assert dialog.heading.text() == "Schritt 2 von 8: Zugangsdaten schützen"
    lines = texts(page.text)
    assert lines[0].startswith("Für GitHub und für eine externe KI braucht das Cockpit "
                               "Zugangsdaten")
    assert not any("E-Mail-Konto" in line or "Automatisierung" in line for line in lines)
    assert any(line.startswith("Erstens: Windows-Anmeldeinformationsverwaltung, empfohlen.")
               for line in lines)
    assert "Zugangsdaten wie Tokens liegen immer verschlüsselt im Tresor." not in lines


# -- Code-Plattformen -----------------------------------------------------------------------
def test_platform_choice_is_a_checklist(wizard):
    dialog, _ = wizard
    go_to(dialog, "Code-Plattformen wählen")
    page = dialog.page
    assert dialog.heading.text() == "Schritt 4 von 8: Code-Plattformen wählen"
    assert dialog.focusWidget() is page.text                  # zuerst die Erklärung
    assert texts(page.text)[0].startswith("Eine Code-Plattform bewahrt Ihren Code im Internet")
    assert next_focus(page.text) is page.list
    assert page.list.accessibleName() == "Code-Plattformen"
    assert texts(page.list) == ["GitHub"]
    item = page.list.item(0)
    assert item.flags() & Qt.ItemFlag.ItemIsUserCheckable
    assert item.checkState() == Qt.CheckState.Checked          # die einzige Plattform
    assert dialog.skip_button.isVisible()


def test_without_platform_the_setup_page_is_left_out(wizard):
    dialog, _ = wizard
    go_to(dialog, "Code-Plattformen wählen")
    dialog.page.list.item(0).setCheckState(Qt.CheckState.Unchecked)
    dialog.next()
    assert dialog.page.title == "Projekte-Hauptordner"
    assert dialog.heading.text() == "Schritt 5 von 7: Projekte-Hauptordner"
    dialog.back()
    assert dialog.page.title == "Code-Plattformen wählen"


def test_setup_page_lists_chosen_platforms(wizard):
    dialog, services = wizard
    go_to(dialog, "Code-Plattformen wählen")
    dialog.next()
    page = dialog.page
    assert page.title == "Code-Plattformen einrichten"
    assert texts(page.list) == ["GitHub, noch nicht eingerichtet"]
    assert not dialog.skip_button.isVisible()
    assert dialog.next_button.text() == "&Weiter (1 nicht eingerichtet)"
    dialog.next()                                              # geht auch ohne Konto
    assert dialog.page.title == "Projekte-Hauptordner"


def test_setup_opens_the_account_dialog_with_identity(wizard, monkeypatch):
    dialog, services = wizard
    go_to(dialog, "Code-Plattformen wählen")
    dialog.next()
    page = dialog.page
    calls = []

    class FakeEdit:
        def __init__(self, services_, account_type, account, parent, with_identity=False):
            calls.append((account_type.adapter, account, with_identity))
            self.saved = services_.accounts.create(account_type, "GitHub privat", {
                "username": "1013hPascal", "token": Secret(TOKEN)})

        def exec(self):
            return True

    patch_split(monkeypatch, ad, "AccountEditDialog", FakeEdit)
    page.list.setCurrentRow(0)
    page.setup_current()
    assert calls == [("github", None, True)]
    assert texts(page.list) == ["GitHub, eingerichtet: GitHub privat, 1013hPascal"]
    assert dialog.next_button.text() == "&Weiter"
    assert said("Konto GitHub privat angelegt.")
    assert dialog.focusWidget() is page.list                   # zurück auf der Seite


# -- Konto-Fenster mit Git-Identität --------------------------------------------------------
class DoneLogin:
    def __init__(self, *args):
        self.token, self.username = Secret(TOKEN), "1013hPascal"

    def exec(self):
        return True


def edit_dialog(qtbot, services, monkeypatch):
    monkeypatch.setattr(github_login, "CLIENT_ID", "Ov23Test")
    dialog = ad.AccountEditDialog(services, find_type("platform", "github"), with_identity=True)
    qtbot.addWidget(dialog)
    return dialog


def test_result_page_has_identity_fields(qtbot, make_services, monkeypatch):
    services = make_services(vault=FakeVault())
    dialog = edit_dialog(qtbot, services, monkeypatch)
    monkeypatch.setattr(bld, "BrowserLoginDialog", DoneLogin)
    dialog.browser_login()
    assert dialog.stack.currentWidget() is dialog.done_page
    lines = texts(dialog.done_info)
    assert lines[0] == "Angemeldet als 1013hPascal."
    assert any(line.startswith("Darunter stehen Git-Name und Git-E-Mail-Adresse") for line in lines)
    form = dialog.identity_form
    assert [f.spec.label for f in form.fields.values()] == ["Git-Name für Commits",
                                                       "Git-E-Mail-Adresse für Commits"]
    assert form.fields["git_name"].get() == "1013hPascal"
    assert dialog.noreply_button.text() == "A&nonyme GitHub-Adresse übernehmen"
    form.fields["git_email"].set(NOREPLY)
    dialog.save_result()
    assert services.accounts.values(dialog.saved)["token"].reveal() == TOKEN
    settings = services.settings.load()
    assert (settings.git_name, settings.git_email) == ("1013hPascal", NOREPLY)


def test_identity_needs_both_or_none(qtbot, make_services, monkeypatch, no_blocking_dialogs):
    services = make_services(vault=FakeVault())
    dialog = edit_dialog(qtbot, services, monkeypatch)
    monkeypatch.setattr(bld, "BrowserLoginDialog", DoneLogin)
    dialog.browser_login()
    dialog.save_result()                                       # nur der Name steht da
    assert dialog.saved is None
    assert "Bitte Git-Name und Git-E-Mail-Adresse" in no_blocking_dialogs[0]
    dialog.identity_form.fields["git_name"].set("")
    dialog.save_result()                                       # beide leer: nur das Konto
    assert dialog.saved is not None
    assert services.settings.load().git_name == ""


def test_token_way_also_ends_on_the_result_page(qtbot, make_services, server, monkeypatch):
    services = make_services(vault=FakeVault())
    dialog = edit_dialog(qtbot, services, monkeypatch)
    dialog.form.fields["token"].focus.setText(TOKEN)
    dialog.save()                                               # testet erst die Verbindung
    qtbot.waitUntil(lambda: dialog.stack.currentWidget() is dialog.done_page, timeout=5000)
    assert dialog.saved is None                                 # noch nicht gespeichert
    assert texts(dialog.done_info)[0] == "Verbindung geklappt, angemeldet als 1013hPascal."
    dialog.take_noreply()
    qtbot.waitUntil(lambda: dialog.identity_form.fields["git_email"].get() != "", timeout=5000)
    assert dialog.identity_form.fields["git_email"].get() == NOREPLY
    qtbot.waitUntil(lambda: dialog.noreply_task is None, timeout=5000)
    dialog.save_result()
    assert dialog.saved.username == "1013hPascal"
    assert services.settings.load().git_email == NOREPLY


def test_without_identity_nothing_changes(qtbot, make_services, monkeypatch):
    services = make_services(vault=FakeVault())
    monkeypatch.setattr(github_login, "CLIENT_ID", "Ov23Test")
    dialog = ad.AccountEditDialog(services, find_type("platform", "github"))
    qtbot.addWidget(dialog)
    assert dialog.identity_form is None and dialog.noreply_button is None


def test_token_page_buttons_forward_first(qtbot, make_services, monkeypatch):
    services = make_services(vault=FakeVault())
    dialog = edit_dialog(qtbot, services, monkeypatch)
    dialog.show_page(dialog.token_page, speak=False)
    show_active(qtbot, dialog)
    assert dialog.test_button.x() < dialog.save_button.x() < dialog.back_button.x()


def test_login_texts_mention_clipboard_and_authorize():
    lines = GitHubPlatform.account_explanation(True)
    assert lines[2:6] == [
        "Im Browser anmelden, empfohlen. So geht es:",
        "1. Im Browser mit GitHub anmelden.",
        "2. Bei der Code-Verifizierung den Code mit Strg+V einfügen. Er liegt schon in der "
        "Zwischenablage.",
        "3. Ganz unten auf Autorisieren klicken, auf Englisch Authorize."]


def test_browser_dialog_names_authorize(qtbot, monkeypatch):
    monkeypatch.setattr(bld, "open_url", lambda url: None)
    monkeypatch.setattr(bld.BrowserLoginDialog, "start", lambda self: None)
    dialog = bld.BrowserLoginDialog(GitHubPlatform)
    qtbot.addWidget(dialog)
    assert "ganz unten auf der Seite Authorize, auf Deutsch Autorisieren" in dialog.confirm_line


# -- KI -------------------------------------------------------------------------------------
def test_ai_page_text(wizard, qtbot):
    dialog, _ = wizard
    go_to(dialog, "KI")
    page = dialog.page
    qtbot.waitUntil(lambda: page.task is None, timeout=10000)
    lines = texts(page.text)
    assert lines[0] == sw.AI_INTRO
    assert lines[2:2 + len(sw.AI_LINES)] == sw.AI_LINES       # ohne Features keine Liste
    assert any(line.startswith("Lokale KI: Sie läuft auf Ihrem Rechner.") for line in lines)
    assert any("Firmen-KI" in line for line in lines)
    assert lines[-1] == "Mit Tab kommen Sie zu KI einrichten."


def test_ai_dialog_from_the_wizard_saves(qtbot, make_services, quiet_machine,  # noqa: F811
                                         monkeypatch):
    services = make_services()
    dialog = ai_dialogs.AIManagerDialog(services, for_setup=True)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10000)
    assert dialog.close_button.text() == "&KI-Einstellungen speichern"
    assert texts(dialog.list)[:2] == ["Neue Text-KI einrichten …", "Neue Sprach-KI einrichten …"]
    opened = []
    monkeypatch.setattr(ai_dialogs.SpeechDialog, "__init__",
                        lambda self, services_, parent=None: opened.append("Sprach-KI"))
    monkeypatch.setattr(ai_dialogs.SpeechDialog, "exec", lambda self: True)
    dialog.list.setCurrentRow(1)
    assert dialog.model_button.isHidden()                      # passt nicht zur Zeile
    dialog.open_current()
    assert opened == ["Sprach-KI"]


def test_ai_manager_keeps_close_outside_the_wizard(qtbot, make_services,
                                                   quiet_machine):  # noqa: F811
    services = make_services()
    dialog = ai_dialogs.AIManagerDialog(services)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: dialog.task is None, timeout=10000)
    assert dialog.close_button.text() == "&Schließen"


# -- Zusammenfassung ------------------------------------------------------------------------
def test_summary_with_tips_and_video(wizard, opened):
    dialog, _ = wizard
    go_to(dialog, "Zusammenfassung")
    page = dialog.page
    lines = texts(page.list)
    assert lines[0] == ("Die Einrichtung ist fertig. Hier sehen Sie, was eingerichtet ist und "
                        "was nicht.")
    assert any(line.startswith("F1 öffnet die Hilfe") for line in lines)
    assert lines[-1] == "Mit Tab gelangen Sie zu den Tipps, zum Video und zu Fertig."
    tips = texts(page.tips)
    assert tips[0] == "Für einen perfekten Start hier noch ein paar Tipps."
    assert any("Hilfe-Assistent" in tip for tip in tips)
    assert "Zum Beispiel: Wo finde ich welches Menü?" in tips
    assert any("Git für Anfänger" in tip for tip in tips)
    assert page.tips.accessibleName() == "Tipps für den Start"
    order = [page.list, page.tips, page.video_button, dialog.next_button]
    widget = page.list
    for expected in order[1:]:
        widget = widget.nextInFocusChain()
        while not widget.isVisible() or widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
            widget = widget.nextInFocusChain()
        assert widget is expected
    page.video_button.click()
    assert opened == [paths.resource_dir() / "erklärvideos" / videos.GIT_BASICS]


def test_summary_names_platform_and_identity(wizard):
    dialog, services = wizard
    services.accounts.create(find_type("platform", "github"), "GitHub privat",
                             {"username": "1013hPascal", "token": Secret(TOKEN)})
    services.settings.update(git_name="1013hPascal", git_email=NOREPLY)
    go_to(dialog, "Code-Plattformen wählen")
    dialog.next()
    dialog.next()
    go_to(dialog, "Zusammenfassung")
    lines = texts(dialog.page.list)
    assert (f"Eingerichtet: GitHub-Konto: GitHub privat, 1013hPascal. Git-Identität: "
            f"1013hPascal, {NOREPLY}.") in lines


# -- Features wählen (22.10.2026) -----------------------------------------------------------
@pytest.fixture
def full_wizard(qtbot, make_services, quiet_machine):  # noqa: F811
    from cockpit.core.features.registry import FeatureRegistry
    services = make_services(FeatureRegistry.discover().all())
    services.use_vault(services.make_vault("windows"))
    dialog = sw.SetupWizard(services)
    qtbot.addWidget(dialog)
    show_active(qtbot, dialog)
    return dialog, services


def test_features_are_grouped_by_what_they_need(full_wizard):
    _, services = full_wizard
    free = {m.id for m in sw.features_in(services, "free")}
    assert {"versions", "exe_build", "packages"} <= free
    assert not free & {"news", "activity", "releases", "ai_help", "dictation", "readme"}
    assert {"news", "activity", "releases"} <= {m.id for m in sw.features_in(services, "platform")}
    assert {"ai_help", "dictation"} <= {m.id for m in sw.features_in(services, "ai")}


def test_feature_page_comes_after_the_folder(full_wizard):
    dialog, _ = full_wizard
    go_to(dialog, "Projekte-Hauptordner")
    dialog.next()
    page = dialog.page
    assert page.title == "Features wählen"
    # go_to hat die Plattform übersprungen, deshalb fehlt "Code-Plattformen einrichten"
    assert dialog.heading.text() == "Schritt 6 von 8: Features wählen"
    assert dialog.focusWidget() is page.text
    assert next_focus(page.text) is page.list
    assert page.list.accessibleName() == "Features"
    rows = texts(page.list)
    assert rows and all(page.list.item(r).checkState() == Qt.CheckState.Checked
                        for r in range(len(rows)))
    assert any(row.startswith("Versionen: ") for row in rows)
    # Wunsch des Nutzers (25.10.2026): alle Features, mit dem, was sie brauchen
    assert {m.id for m in page.features} == {m.id for m in dialog.services.registry.all()}
    assert any(row.startswith("Neuigkeiten: ") and "Braucht: " in row for row in rows)
    assert any(row.startswith("KI-Hilfe: ") and "Braucht: " in row for row in rows)
    assert any(row.startswith("Erklärungen: ") for row in rows)
    groups = [sw.feature_group(dialog.services, m) for m in page.features]
    order = setup_pages.FEATURE_GROUPS
    assert groups == sorted(groups, key=order.index)              # ohne Einrichtung oben


def test_unchecked_feature_is_off_and_checked_ones_are_on(full_wizard):
    dialog, services = full_wizard
    go_to(dialog, "Features wählen")
    page = dialog.page
    row = next(r for r, m in enumerate(page.features) if m.id == "packages")
    page.list.item(row).setCheckState(Qt.CheckState.Unchecked)
    dialog.next()
    assert dialog.page.title == "KI"
    assert not services.features.globally_enabled("packages")
    assert services.features.globally_enabled("versions")
    assert "versions" in services.features.default_features()     # sonst standardmäßig aus
    total = len(page.features)
    go_to(dialog, "Zusammenfassung")
    assert (f"Eingerichtet: Features: {total - 1} von {total} eingeschaltet."
            in texts(dialog.page.list))


def test_skipped_feature_page_changes_nothing(full_wizard):
    dialog, services = full_wizard
    go_to(dialog, "Features wählen")
    dialog.skip()
    assert services.settings.load().default_features is None
    go_to(dialog, "Zusammenfassung")
    assert ("Übersprungen: Features wählen. Nachholen: Menü Features, Feature-Verwaltung."
            in texts(dialog.page.list))


def test_platform_and_ai_pages_name_their_features(full_wizard, qtbot):
    dialog, _ = full_wizard
    go_to(dialog, "Code-Plattformen wählen")
    lines = texts(dialog.page.text)
    assert "Dazu kommen diese Features:" in lines
    assert any(line.startswith("Neuigkeiten: ") for line in lines)
    go_to(dialog, "KI")
    qtbot.waitUntil(lambda: dialog.page.task is None, timeout=10000)
    lines = texts(dialog.page.text)
    assert "Mit KI nutzen Sie diese Features:" in lines
    assert any(line.startswith("KI-Hilfe: ") for line in lines)


def test_git_page_explains_git(wizard):
    dialog, _ = wizard
    go_to(dialog, "Git")
    lines = texts(dialog.page.state)
    assert lines[1:1 + len(sw.GIT_LINES)] == sw.GIT_LINES
