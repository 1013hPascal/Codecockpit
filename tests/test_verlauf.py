"""Versionsverlauf, Zu einer Version zurück und Hochladeverlauf (Wunsch des Nutzers vom
07.10.2026). Git arbeitet mit einem nackten Repository als Plattform. Keine Geheimnisse.
"""
from __future__ import annotations

from datetime import datetime

import pytest

from cockpit.core import git, history
from cockpit.ui import history_dialogs
from tests.conftest import said
from tests.test_phase5d import EMAIL, NAME, commit, history_repo, sh

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


def by_subject(code):
    return {c.subject: c for c in history.log_commits(code)}


# -- Gruppen ------------------------------------------------------------------------------------
def test_versions_group_their_commits(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    groups = history.group_versions(history.log_commits(code))
    assert [g.line() for g in groups] == ["In Arbeit, noch keine Version, 2 Commits",
                                          "Version 1.0.0 vom 21.09.2026, 2 Commits"]
    assert [c.subject for c in groups[1].commits] == ["Hilfe ergänzt", "Erste Version"]
    assert groups[1].head.version == "1.0.0"


def test_without_versions_by_day(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    sh(code, "tag", "-d", "v1.0.0")
    lines = [g.line() for g in history.group_versions(history.log_commits(code))]
    assert lines[0] == "23.09.2026, 1 Commit" and lines[1] == "22.09.2026, 1 Commit"


def test_commit_line_names_date_person_and_text(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    commit(code, "Noch lokal", {"main.py": "lokal\n"}, "2026-09-24T08:00:00")
    first = history.log_commits(code)[0]
    assert first.short_line().startswith("24.09.2026, ")
    assert first.short_line().endswith(": Noch lokal, noch nicht hochgeladen")


# -- Zu einer Version zurück --------------------------------------------------------------------
def test_back_to_a_version_is_a_new_commit(tmp_path, projects_root, home):
    _, code, _ = history_repo(tmp_path, projects_root)
    version = by_subject(code)["Hilfe ergänzt"]
    before = len(history.log_commits(code))
    folder = history.back_to(code, "Tagebuch", version, NAME, EMAIL)
    commits = history.log_commits(code)
    assert len(commits) == before + 1                             # nichts geht verloren
    assert commits[0].subject == "Zurück zu Version 1.0.0" and not commits[0].uploaded
    assert (code / "alt.py").read_text(encoding="utf-8") == "alt\n"   # wieder da
    assert not (code / "einstellungen.py").exists()                  # kam erst danach
    assert (code / "main.py").read_text(encoding="utf-8") == "a\nb\nc\n"
    assert folder is not None and (folder / "main.py").is_file()     # Sicherheitskopie
    with pytest.raises(Exception, match="schon auf dem Stand"):
        history.back_to(code, "Tagebuch", by_subject(code)["Hilfe ergänzt"], NAME, EMAIL)


def test_back_to_needs_a_clean_folder(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    (code / "main.py").write_text("offen\n", encoding="utf-8")
    with pytest.raises(Exception, match="Änderungen ohne Commit"):
        history.back_to(code, "Tagebuch", by_subject(code)["Hilfe ergänzt"], NAME, EMAIL)


# -- Fenster ------------------------------------------------------------------------------------
def test_dialog_versions_then_commits_and_back(qtbot, make_services, tmp_path, projects_root,
                                               monkeypatch):
    services = make_services()
    services.settings.update(git_name=NAME, git_email=EMAIL)
    _, code, _ = history_repo(tmp_path, projects_root)
    project = services.projects.add(code.parent)
    asked = []
    monkeypatch.setattr(history_dialogs, "confirm",
                        lambda p, t, text, **k: asked.append((t, text, k)) or True)
    dialog = history_dialogs.HistoryDialog(services, project, history.log_commits(code))
    qtbot.addWidget(dialog)
    assert dialog.initial_focus_widget is dialog.versions
    assert dialog.versions.accessibleName() == "Versionen"
    assert dialog.list.accessibleName() == "Commits"
    assert not dialog.back_button.isEnabled()                      # „In Arbeit“
    dialog.versions.setCurrentRow(1)
    assert dialog.back_button.isEnabled()
    assert dialog.list.count() == 2 and dialog.current().subject == "Hilfe ergänzt"
    dialog.back_to_version()
    title, text, buttons = asked[-1]
    assert title == "Zu dieser Version zurück"
    assert text.startswith("Das Cockpit setzt alle Dateien auf den Stand der Version 1.0.0")
    assert buttons == {"yes": "Zurück zur Version", "no": "Abbrechen"}
    assert dialog.changed and said("Zurück zu Version 1.0.0. Neuer Commit, noch nicht "
                                   "hochgeladen.")
    assert dialog.versions.item(0).text() == "In Arbeit, noch keine Version, 3 Commits"


# -- Hochladeverlauf ------------------------------------------------------------------------------
def test_pushes_are_recorded_and_listed(tmp_path, projects_root, make_services):
    services = make_services()
    _, code, _ = history_repo(tmp_path, projects_root)
    project = services.projects.add(code.parent)
    old = history.remote_head(code, "main")
    commit(code, "Neu A", {"a.py": "a\n"})
    commit(code, "Neu B", {"b.py": "b\n"})
    sh(code, "push", "-q", "origin", "main")
    new = history.remote_head(code, "main")
    history.record_push(services.database, project.id,
                        history.Push("main", "2026-10-06T14:12:00", "Pascal", old, new))
    history.record_push(services.database, project.id,
                        history.Push("main", "2026-10-06T15:00:00", "Pascal", new, new))
    uploads = history.upload_history(services.database, project.id, code, "main")
    assert uploads[0].text == "06.10.2026 14:12, Pascal, 2 Commits nach main"
    assert [c.subject for c in uploads[0].commits] == ["Neu B", "Neu A"]
    assert uploads[1].text == "23.09.2026, 1 Commit, vor dem Aufzeichnen"
    assert history.pushes(services.database, project.id, "andere") == []


def test_upload_history_dialog(qtbot, make_services, tmp_path, projects_root):
    services = make_services()
    _, code, _ = history_repo(tmp_path, projects_root)
    project = services.projects.add(code.parent)
    uploads = history.upload_history(services.database, project.id, code, "main")
    dialog = history_dialogs.UploadHistoryDialog(services, project, "main", uploads)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle().startswith("Hochladeverlauf von main: ")
    assert dialog.uploads_list.accessibleName() == "Hochgeladen"
    assert dialog.uploads_list.item(0).text() == "23.09.2026, 1 Commit, vor dem Aufzeichnen"
    assert dialog.list.item(0).text().endswith(": Alte Datei entfernt")


def test_push_flow_records_the_upload(tmp_path, projects_root, make_services):
    """Das Hochladen aus dem Cockpit merkt sich Branch, Zeit, Person und Stand."""
    services = make_services()
    _, code, _ = history_repo(tmp_path, projects_root)
    project = services.projects.add(code.parent)
    push = history.Push("main", datetime(2026, 10, 7, 9, 5).isoformat(), "Pascal", "", "")
    history.record_push(services.database, project.id, push)       # ohne neuen Stand: nichts
    assert history.pushes(services.database, project.id, "main") == []
