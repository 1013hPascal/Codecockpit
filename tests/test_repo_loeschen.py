"""Repository löschen, das nur auf GitHub liegt (Wunsch des Nutzers, 02.10.2026).

Bisher musste man es erst herunterladen. Jetzt steht "Repository löschen …" direkt bei den
Aktionen, mit denselben Rückfragen wie bei "Projekt verwalten". Die Plattform ist eine Attrappe.
"""
from __future__ import annotations

from cockpit.core.actions import Target
from cockpit.ui import project_actions, repo_dialogs
from tests.test_collections import add_remote_repos
from tests.test_phase5e import RepoFake, answers  # noqa: F401 (Fixture)
from tests.test_ui import window  # noqa: F401 (Fixture)


def remote_window(window, monkeypatch):  # noqa: F811
    win = window()
    repos = add_remote_repos(win.services, "Vokabeln", "Blog")
    win.reload_projects(refresh=False)
    fake = RepoFake()
    win.services.platforms[repos["Vokabeln"].account_id] = fake
    monkeypatch.setattr(project_actions.vault_ui, "ensure_unlocked", lambda *a: True)
    assert win.project_list.select(Target.REMOTE_REPO, repos["Vokabeln"].id)
    return win, repos["Vokabeln"], fake


def run(win, text):
    entry = next(e for e in win.current_entries() if e.action.text == text)
    win.run_entry(entry)


def test_action_is_listed(window, monkeypatch):  # noqa: F811
    win, _repo, _fake = remote_window(window, monkeypatch)
    texts = [e.action.text for e in win.current_entries()]
    assert texts == ["Herunterladen", "Auf GitHub öffnen", "Repository löschen …",
                     "Aus der Liste entfernen …"]
    entry = next(e for e in win.current_entries() if e.action.id == "delete_remote_repo")
    assert entry.availability.available


def test_delete_without_download(window, monkeypatch, answers, qtbot):  # noqa: F811
    win, repo, fake = remote_window(window, monkeypatch)
    monkeypatch.setattr(repo_dialogs.TypeNameDialog, "exec", lambda self: 1)
    answers.choice = 0                                             # Weiter zum Löschen
    run(win, "Repository löschen …")
    title, text, extra = answers.questions[0]
    assert text.startswith("Löschen lässt sich nicht rückgängig machen. Vokabeln ist danach")
    assert "Auf Ihrem Rechner gibt es keine Kopie." in text
    assert extra["buttons"] == ["Weiter zum Löschen …", "Stattdessen archivieren …",
                                "Abbrechen"] and extra["default"] == 2
    qtbot.waitUntil(lambda: fake.calls == [("delete", "Vokabeln", "")], timeout=10000)
    qtbot.waitUntil(lambda: win.services.remote_repos.find(repo.address) is None,
                    timeout=10000)
    assert not any(t.startswith("Vokabeln") for t in win.project_list.texts())
    assert any(t.startswith("Blog") for t in win.project_list.texts())


def test_cancel_or_wrong_name_deletes_nothing(window, monkeypatch, answers):  # noqa: F811
    win, repo, fake = remote_window(window, monkeypatch)
    answers.choice = 2                                             # Abbrechen
    run(win, "Repository löschen …")
    monkeypatch.setattr(repo_dialogs.TypeNameDialog, "exec", lambda self: 0)
    answers.choice = 0
    run(win, "Repository löschen …")
    assert fake.calls == []
    assert win.services.remote_repos.find(repo.address) is not None


def test_archive_instead(window, monkeypatch, answers, qtbot):  # noqa: F811
    win, repo, fake = remote_window(window, monkeypatch)
    asked = []
    monkeypatch.setattr(project_actions, "confirm",
                        lambda parent, title, text, **k: asked.append(text) or True)
    answers.choice = 1                                             # stattdessen archivieren
    run(win, "Repository löschen …")
    assert asked[0].startswith("Vokabeln wird schreibgeschützt.")
    qtbot.waitUntil(lambda: fake.calls == [("archive", "Vokabeln")], timeout=10000)
    assert win.services.remote_repos.find(repo.address) is not None   # bleibt in der Liste


def test_not_available_without_account(window, monkeypatch):  # noqa: F811
    win, repo, _fake = remote_window(window, monkeypatch)
    monkeypatch.setattr(win.services.accounts, "get", lambda account_id: None)
    entry = next(e for e in win.current_entries() if e.action.id == "delete_remote_repo")
    assert not entry.availability.available
    assert entry.availability.reason == "Das Konto zu diesem Repository gibt es nicht mehr."
