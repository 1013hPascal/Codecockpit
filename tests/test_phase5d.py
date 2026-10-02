"""Phase 5d: Verlauf und Rückgängig machen, mit Sicherheitskopien.

Die "Plattform" ist ein nacktes Repository auf der Festplatte. Der Papierkorb ist in allen Tests
ersetzt: Dateien kommen in einen Ordner im temporären Verzeichnis.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cockpit.core import backups, git, history, trash
from cockpit.core.errors import CockpitError
from cockpit.ui import history_dialogs
from tests.conftest import said
from tests.test_phase5a import EMAIL, NAME, live, sh, wait_idle  # noqa: F401
from tests.test_phase5b import write
from tests.test_phase5c import (head, labels, push_from_other, run_push, select_code,
                                setup_repo)

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


@pytest.fixture(autouse=True)
def recycle_bin(tmp_path, monkeypatch):
    """Nie der echte Papierkorb: gelöschte Dateien kommen nach tmp_path/papierkorb."""
    folder = tmp_path / "papierkorb"
    folder.mkdir()

    def move(paths):
        for path in paths:
            path.replace(folder / path.name)
    monkeypatch.setattr(trash, "move_to_recycle_bin", move)
    return folder


def commit(code: Path, message: str, files: dict[str, str | None], date: str = "") -> str:
    """Dateien schreiben (None: löschen) und committen."""
    for name, text in files.items():
        if text is None:
            (code / name).unlink()
        else:
            write(code, name, text)
    sh(code, "add", "-A")
    args = ["commit", "-q", "-m", message]
    if date:
        args += ["--date", date]
    sh(code, *args)
    return head(code)


def read(code: Path, name: str) -> str:
    return (code / name).read_text(encoding="utf-8")


def history_repo(tmp_path, projects_root):
    """Tagebuch mit Verlauf: Erste Version, Hilfe (Tag v1.0.0), Einstellungen, alt.py gelöscht.
    Alles hochgeladen."""
    bare, code, other = setup_repo(tmp_path, projects_root, {"main.py": "a\nb\nc\n",
                                                             "alt.py": "alt\n"})
    commit(code, "Hilfe ergänzt", {"hilfe.py": "hilfe\n"}, "2026-09-21T10:00:00")
    sh(code, "tag", "v1.0.0")
    commit(code, "Einstellungen ergänzt", {"einstellungen.py": "x\n", "main.py": "a\nB\nc\n"},
           "2026-09-22T11:30:00")
    commit(code, "Alte Datei entfernt", {"alt.py": None}, "2026-09-23T09:15:00")
    sh(code, "push", "-q", "--tags", "origin", "main")
    return bare, code, other


# -- Verlauf ------------------------------------------------------------------------------------
def test_log_lists_versions_newest_first(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    commit(code, "Noch lokal", {"main.py": "lokal\n"}, "2026-09-24T08:00:00")
    commits = history.log_commits(code)
    assert [c.line() for c in commits[:4]] == [
        "24.09.2026: Noch lokal, noch nicht hochgeladen",
        "23.09.2026: Alte Datei entfernt",
        "22.09.2026: Einstellungen ergänzt",
        "21.09.2026, Version 1.0.0: Hilfe ergänzt"]
    assert commits[-1].subject == "Erste Version" and not commits[-1].parents
    assert commits[0].newest and not commits[1].newest
    assert commits[3].version == "1.0.0" and commits[3].tags == ["v1.0.0"]


def test_log_of_an_empty_repository(tmp_path):
    code = tmp_path / "leer"
    code.mkdir()
    git.init(code)
    assert history.log_commits(code) == []


def test_log_without_upstream_marks_nothing(tmp_path):
    code = tmp_path / "lokal"
    code.mkdir()
    git.init(code)
    commit(code, "Erste Version", {"a.py": "1\n"})
    assert history.log_commits(code)[0].line().endswith(": Erste Version")


def test_commit_files_and_details(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    commits = history.log_commits(code)
    assert history.commit_files(code, commits[0]).lines() == ["alt.py, gelöscht"]
    assert history.commit_files(code, commits[1]).summary() == "1 Datei geändert, 1 neue Datei"
    first = history.commit_files(code, commits[-1])
    assert sorted(first.added) == ["alt.py", "main.py"]
    commit(code, "Umbenannt", {"hilfe.py": None, "anleitung.py": "hilfe\n"})
    renamed = history.commit_files(code, history.log_commits(code)[0])
    assert renamed.renamed == ["anleitung.py"]
    lines = history.details(commits[2], ["Exe wird erstellt: Exe getestet"])
    assert lines[0] == "Nachricht: Hilfe ergänzt"
    assert lines[1] == "Von Test am 21.09.2026 um 10:00 Uhr"
    assert "Version 1.0.0" in lines
    assert "Schritt aus dem Cockpit: Exe wird erstellt: Exe getestet" in lines
    assert lines[-1] == f"Commit {commits[2].short}"


def test_details_show_body_and_state(tmp_path, projects_root):
    _, code, _ = setup_repo(tmp_path, projects_root)
    write(code, "x.py", "1\n")
    sh(code, "add", "-A")
    sh(code, "commit", "-q", "-m", "Kurz", "-m", "Erste Zeile.\nZweite Zeile.")
    lines = history.details(history.log_commits(code)[0])
    assert lines[:3] == ["Nachricht: Kurz", "Erste Zeile.", "Zweite Zeile."]
    assert "Noch nicht hochgeladen" in lines


# -- Datei wiederherstellen ---------------------------------------------------------------------
def test_restore_file_from_a_version(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    before = head(code)
    write(code, "main.py", "kaputt\n")
    first = history.log_commits(code)[-1]
    folder = history.restore_file(code, "Tagebuch", first, "main.py",
                                  history.commit_files(code, first))
    assert read(code, "main.py") == "a\nb\nc\n"
    assert head(code) == before                                   # Verlauf unverändert
    assert "main.py" in sh(code, "status", "--porcelain")          # normale Änderung
    info = backups.read_info(folder)
    assert info.reason == "vor dem Wiederherstellen" and info.source_dir == code
    assert (folder / "main.py").read_text(encoding="utf-8") == "kaputt\n"
    assert info.notes[0].startswith(f"Version: {first.short} vom ")


def test_restore_a_file_deleted_in_that_version(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    removed = history.log_commits(code)[0]                          # "Alte Datei entfernt"
    files = history.commit_files(code, removed)
    assert history.restore_source(removed, "alt.py", files) == removed.parents[0]
    assert history.restore_file(code, "Tagebuch", removed, "alt.py", files) is None
    assert read(code, "alt.py") == "alt\n"


def test_restore_file_is_refused_during_a_merge(tmp_path, projects_root):
    from tests.test_phase5c import merge_conflict
    code, *_ = merge_conflict(tmp_path, projects_root)
    first = history.log_commits(code)[-1]
    with pytest.raises(CockpitError, match="Konflikte"):
        history.restore_file(code, "Tagebuch", first, "main.py", history.commit_files(code, first))


# -- Version rückgängig machen -----------------------------------------------------------------
def test_revert_creates_a_new_commit(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    old_head = head(code)
    settings = history.log_commits(code)[1]                         # "Einstellungen ergänzt"
    folder = history.revert(code, "Tagebuch", settings)
    commits = history.log_commits(code)
    assert commits[0].subject == "Rückgängig: Einstellungen ergänzt"
    assert commits[0].parents == [old_head]                          # Verlauf bleibt vollständig
    assert f"Macht Commit {settings.sha} rückgängig." in commits[0].body
    assert commits[0].line().endswith(", noch nicht hochgeladen")
    assert read(code, "main.py") == "a\nb\nc\n"
    assert not (code / "einstellungen.py").exists()
    assert sh(code, "status", "--porcelain").strip() == ""
    info = backups.read_info(folder)
    assert info.reason == "vor dem Rückgängigmachen"
    assert sorted(info.files()) == ["einstellungen.py", "main.py"]


def test_revert_refuses_when_the_files_have_own_changes(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    write(code, "main.py", "meine\n")
    old_head = head(code)
    with pytest.raises(CockpitError, match="In main.py gibt es Änderungen ohne Commit"):
        history.revert(code, "Tagebuch", history.log_commits(code)[1])
    assert head(code) == old_head and read(code, "main.py") == "meine\n"


def test_revert_with_a_conflict_changes_nothing(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    commit(code, "Später geändert", {"main.py": "a\nNEU\nc\n"})
    old_head = head(code)
    with pytest.raises(CockpitError, match="nicht von selbst rückgängig"):
        history.revert(code, "Tagebuch", history.log_commits(code)[2])
    assert head(code) == old_head
    assert sh(code, "status", "--porcelain").strip() == ""
    assert read(code, "main.py") == "a\nNEU\nc\n"


def test_revert_twice_is_refused(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    target = history.log_commits(code)[1]
    history.revert(code, "Tagebuch", target)
    again = head(code)
    with pytest.raises(CockpitError):
        history.revert(code, "Tagebuch", target)
    assert head(code) == again
    assert sh(code, "status", "--porcelain").strip() == ""


def test_revert_refuses_merges_and_the_first_version(tmp_path, projects_root):
    from tests.test_phase5c import merge_conflict
    from cockpit.core import sync
    code, *_ = merge_conflict(tmp_path, projects_root)
    sync.resolve(code, "main.py", sync.ConflictKind.MERGE, True)
    sync.finish(code, sync.ConflictKind.MERGE)
    commits = history.log_commits(code)
    assert commits[0].is_merge
    with pytest.raises(CockpitError, match="Zusammenführen von zwei Ständen"):
        history.revert(code, "Tagebuch", commits[0])
    with pytest.raises(CockpitError, match="erste Version"):
        history.revert(code, "Tagebuch", commits[-1])


# -- Commit zurücknehmen ----------------------------------------------------------------------
def test_undo_newest_commit_keeps_the_files(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    uploaded = head(code)
    commit(code, "Noch lokal", {"main.py": "lokal\n", "neu.py": "n\n"})
    commits = history.log_commits(code)
    assert history.can_undo(commits[0]) and not history.can_undo(commits[1])
    history.undo_commit(code, commits[0])
    assert head(code) == uploaded
    assert read(code, "main.py") == "lokal\n" and read(code, "neu.py") == "n\n"
    assert {c.path for c in history.local_changes(code)} == {"main.py", "neu.py"}


def test_undo_is_refused_for_uploaded_commits(tmp_path, projects_root):
    _, code, _ = history_repo(tmp_path, projects_root)
    newest = history.log_commits(code)[0]
    assert not history.can_undo(newest)
    with pytest.raises(CockpitError, match="noch nicht hochgeladen"):
        history.undo_commit(code, newest)


# -- Änderungen verwerfen ---------------------------------------------------------------------
def test_discard_changes(tmp_path, projects_root, recycle_bin):
    _, code, _ = history_repo(tmp_path, projects_root)
    write(code, "main.py", "geändert\n")
    (code / "hilfe.py").unlink()
    write(code, "neu.py", "neu\n")
    write(code, "vorgemerkt.py", "v\n")
    sh(code, "add", "vorgemerkt.py")
    write(code, "bleibt.py", "b\n")
    changes = history.local_changes(code)
    assert [c.line() for c in changes] == ["bleibt.py, neu", "hilfe.py, gelöscht",
                                           "main.py, geändert", "neu.py, neu",
                                           "vorgemerkt.py, neu"]
    chosen = [c for c in changes if c.path != "bleibt.py"]
    assert history.discard_description(chosen) == (
        "2 Dateien kommen auf den Stand des letzten Commits zurück: hilfe.py und main.py. "
        "2 neue Dateien kommen in den Papierkorb: neu.py und vorgemerkt.py.")
    folder = history.discard(code, "Tagebuch", chosen)
    assert read(code, "main.py") == "a\nB\nc\n" and read(code, "hilfe.py") == "hilfe\n"
    assert not (code / "neu.py").exists() and not (code / "vorgemerkt.py").exists()
    assert (recycle_bin / "neu.py").exists() and (recycle_bin / "vorgemerkt.py").exists()
    assert [c.line() for c in history.local_changes(code)] == ["bleibt.py, neu"]
    info = backups.read_info(folder)
    assert info.reason == "vor dem Verwerfen"
    assert sorted(info.files()) == ["main.py", "neu.py", "vorgemerkt.py"]
    assert (folder / "main.py").read_text(encoding="utf-8") == "geändert\n"


def test_discard_a_staged_rename(tmp_path, projects_root, recycle_bin):
    _, code, _ = history_repo(tmp_path, projects_root)
    sh(code, "mv", "hilfe.py", "anleitung.py")
    changes = history.local_changes(code)
    assert [c.line() for c in changes] == ["anleitung.py, umbenannt, vorher hilfe.py"]
    history.discard(code, "Tagebuch", changes)
    assert read(code, "hilfe.py") == "hilfe\n" and not (code / "anleitung.py").exists()
    assert history.local_changes(code) == []


def test_discard_is_refused_during_a_merge(tmp_path, projects_root):
    from tests.test_phase5c import merge_conflict
    code, *_ = merge_conflict(tmp_path, projects_root)
    with pytest.raises(CockpitError, match="Konflikte"):
        history.local_changes(code)


def test_real_recycle_bin_function_exists():
    assert trash._move_to_recycle_bin([]) is None                 # leere Liste: nichts zu tun


# -- Schritte der Features pro Commit ----------------------------------------------------------
def test_feature_steps_are_recorded_per_commit(make_services, tmp_path, projects_root):
    from cockpit.core.flows.engine import Flow, FlowSummary
    from cockpit.core.flows.hooks import Hook
    from cockpit.core.flows.step import Step, StepResult
    services = make_services()
    _, code, _ = setup_repo(tmp_path, projects_root)
    write(code, "x.py", "1\n")
    summary, data, _ = run_push(services, code, "Mit Schritten")
    assert data["commit"] == head(code)
    project = services.projects.find_by_dir(code.parent)
    core = Step("core", "Kern", Hook.PUSH, lambda c: StepResult(True))
    exe = Step("exe", "Exe wird erstellt", Hook.AFTER_PUSH, lambda c: StepResult(True),
               feature_id="exe")
    fake = FlowSummary(Flow("x", "X"), 2, [(core, StepResult(True, "a")),
                                          (exe, StepResult(True, "Exe getestet"))])
    lines = history.feature_step_lines(fake)
    assert lines == ["Exe wird erstellt: Exe getestet"]
    history.record_steps(services.database, project.id, data["commit"], lines)
    assert history.recorded_steps(services.database, project.id, data["commit"]) == lines
    assert history.recorded_steps(services.database, project.id, "unbekannt") == []


# -- Oberfläche -----------------------------------------------------------------------------
def test_code_actions_for_history(live, qtbot, make_services, projects_root, tmp_path):
    services = make_services()
    _, code, _ = history_repo(tmp_path, projects_root)
    win = live(services)
    select_code(win, services, code)
    texts = labels(win)
    assert "Verlauf …" in texts
    assert "Änderungen verwerfen …, nicht verfügbar: Es gibt keine Änderungen ohne Commit." in texts
    assert texts.index("Verlauf …") < texts.index("Git-Identität …")
    write(code, "main.py", "x\n")
    win.refresh_status()
    wait_idle(qtbot, win)
    assert "Änderungen verwerfen …, 1 Datei geändert" in labels(win)    # Stand seit 02.10.


def test_history_dialog_and_revert(qtbot, make_services, tmp_path, projects_root, monkeypatch):
    services = make_services()
    services.settings.update(git_name=NAME, git_email=EMAIL)
    _, code, _ = history_repo(tmp_path, projects_root)
    project = services.projects.add(code.parent)
    questions = []
    monkeypatch.setattr(history_dialogs, "confirm",
                        lambda p, t, text, **k: questions.append((t, text, k)) or True)
    dialog = history_dialogs.HistoryDialog(services, project, history.log_commits(code))
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Verlauf von Tagebuch: 4 Versionen"
    assert dialog.list.item(2).text() == "21.09.2026, Version 1.0.0: Hilfe ergänzt"
    details = history_dialogs.VersionDialog(services, project, dialog.commits[1], dialog)
    qtbot.addWidget(details)
    assert details.windowTitle() == "22.09.2026: Einstellungen ergänzt"
    assert details.info.item(0).text() == "Nachricht: Einstellungen ergänzt"
    assert details.files.accessibleName() == "Dateien, 1 Datei geändert, 1 neue Datei"
    assert [details.files.item(i).text() for i in range(2)] == [
        "main.py, geändert", "einstellungen.py, neu"]
    assert details.undo_button is None                           # schon hochgeladen
    details.revert()
    title, text, buttons = questions[-1]
    assert title == "Version rückgängig machen"
    assert text.startswith("Das Cockpit erstellt einen neuen Commit „Rückgängig: Einstellungen "
                           "ergänzt“.")
    assert "Der Verlauf bleibt vollständig erhalten." in text
    assert buttons == {"yes": "Rückgängig machen", "no": "Abbrechen"}
    assert details.history_changed and details.result() == 1
    assert said("Rückgängig gemacht. Neuer Commit „Rückgängig: Einstellungen ergänzt“.")
    dialog.reload(0)
    assert dialog.list.item(0).text().endswith(
        ": Rückgängig: Einstellungen ergänzt, noch nicht hochgeladen")
    assert dialog.windowTitle() == "Verlauf von Tagebuch: 5 Versionen"


def test_version_dialog_restore_and_undo(qtbot, make_services, tmp_path, projects_root,
                                         monkeypatch):
    services = make_services()
    _, code, _ = history_repo(tmp_path, projects_root)
    project = services.projects.add(code.parent)
    commit(code, "Noch lokal", {"main.py": "lokal\n"})
    answers = []
    monkeypatch.setattr(history_dialogs, "confirm",
                        lambda p, t, text, **k: answers.append((text, k)) or len(answers) > 1)
    commits = history.log_commits(code)
    first = history_dialogs.VersionDialog(services, project, commits[-1])
    qtbot.addWidget(first)
    first.files.setCurrentRow(1)                                   # main.py
    first.restore_current()                                        # Escape: nichts passiert
    assert read(code, "main.py") == "lokal\n" and not first.files_changed
    text, buttons = answers[0]
    assert text.startswith("main.py kommt auf den Stand der Version vom ")
    assert "Die jetzige Datei kommt vorher als Sicherheitskopie" in text
    assert buttons == {"yes": "Wiederherstellen", "no": "Abbrechen"}
    first.restore_current()
    assert read(code, "main.py") == "a\nb\nc\n" and first.files_changed
    assert said("main.py wiederhergestellt.")
    newest = history_dialogs.VersionDialog(services, project, commits[0])
    qtbot.addWidget(newest)
    assert newest.undo_button is not None
    newest.undo()
    assert "Keine Datei wird verändert." in answers[-1][0]
    assert answers[-1][1] == {"yes": "Zurücknehmen", "no": "Abbrechen"}
    assert newest.history_changed
    assert history.log_commits(code)[0].subject == "Alte Datei entfernt"


def test_revert_of_a_merge_explains_without_question(qtbot, make_services, tmp_path,
                                                     projects_root, monkeypatch):
    from tests.test_phase5c import merge_conflict
    from cockpit.core import sync
    services = make_services()
    code, *_ = merge_conflict(tmp_path, projects_root)
    sync.resolve(code, "main.py", sync.ConflictKind.MERGE, True)
    sync.finish(code, sync.ConflictKind.MERGE)
    project = services.projects.add(code.parent)
    errors = []
    monkeypatch.setattr(history_dialogs, "show_error", lambda *a: errors.append(a[2]))
    monkeypatch.setattr(history_dialogs, "confirm", lambda *a, **k: pytest.fail("keine Frage"))
    dialog = history_dialogs.VersionDialog(services, project, history.log_commits(code)[0])
    qtbot.addWidget(dialog)
    dialog.revert()
    assert "Zusammenführen von zwei Ständen" in errors[0]


def test_discard_dialog(qtbot, tmp_path, projects_root, monkeypatch):
    _, code, _ = history_repo(tmp_path, projects_root)
    write(code, "main.py", "x\n")
    write(code, "neu.py", "n\n")
    errors, questions = [], []
    monkeypatch.setattr(history_dialogs, "show_error", lambda *a: errors.append(a[2]))
    monkeypatch.setattr(history_dialogs, "confirm",
                        lambda p, t, text, **k: questions.append((text, k)) or True)
    dialog = history_dialogs.DiscardDialog("Tagebuch", history.local_changes(code))
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Änderungen verwerfen in Tagebuch: 2 Änderungen"
    assert dialog.list.item(0).text() == "main.py, geändert"
    assert dialog.list.item(0).checkState().name == "Unchecked"   # nichts vorausgewählt
    dialog.check()
    assert errors == [history_dialogs.NO_CHOICE] and dialog.result() == 0
    dialog.toggle_all()
    assert len(dialog.checked()) == 2 and dialog.all_button.text() == "Alle &abwählen"
    dialog.toggle_all()
    assert dialog.checked() == []
    from PySide6.QtCore import Qt
    dialog.list.item(1).setCheckState(Qt.CheckState.Checked)
    dialog.check()
    text, buttons = questions[-1]
    assert text == ("1 neue Datei kommt in den Papierkorb: neu.py. Vorher kommen die Dateien als "
                    "Sicherheitskopie in den Ordner backups. Verwerfen?")
    assert buttons == {"yes": "Verwerfen", "no": "Abbrechen"}
    assert [c.path for c in dialog.chosen] == ["neu.py"] and dialog.result() == 1


def test_discard_from_the_window(live, qtbot, make_services, projects_root, tmp_path,
                                 monkeypatch, recycle_bin):
    services = make_services()
    _, code, _ = history_repo(tmp_path, projects_root)
    write(code, "main.py", "x\n")
    win = live(services)
    select_code(win, services, code)

    class FakeDiscard:
        def __init__(self, name, changes, parent=None):
            self.chosen = changes

        def exec(self):
            return True

    monkeypatch.setattr(history_dialogs, "DiscardDialog", FakeDiscard)
    entry = next(e for e in win.current_entries() if e.action.id == "discard")
    win.run_entry(entry)
    assert said("1 Änderung verworfen.")
    assert read(code, "main.py") == "a\nB\nc\n"
    wait_idle(qtbot, win)
    assert win.project_list.currentItem().text() == "Code, alles hochgeladen"


def test_history_from_the_window(live, qtbot, make_services, projects_root, tmp_path,
                                 monkeypatch):
    services = make_services()
    _, code, _ = history_repo(tmp_path, projects_root)
    win = live(services)
    select_code(win, services, code)
    shown = []

    class FakeHistory:
        def __init__(self, services, project, commits, parent=None):
            shown.append([c.subject for c in commits])
            self.changed = True

        def exec(self):
            return True

    monkeypatch.setattr(history_dialogs, "HistoryDialog", FakeHistory)
    entry = next(e for e in win.current_entries() if e.action.id == "history")
    win.run_entry(entry)
    qtbot.waitUntil(lambda: bool(shown), timeout=10000)
    assert shown[0][0] == "Alte Datei entfernt"
    wait_idle(qtbot, win)


def test_fetched_commits_count_as_uploaded(tmp_path, projects_root):
    """Nach dem Holen stehen die geholten Commits ohne "noch nicht hochgeladen" im Verlauf."""
    from cockpit.core import sync
    _, code, other = history_repo(tmp_path, projects_root)
    sh(other, "pull", "-q")
    push_from_other(other, "fremd.py", "f\n", "Vom anderen Rechner")
    sync.fetch(code)
    sync.merge(code, stash=False)
    assert history.log_commits(code)[0].line().endswith(": Vom anderen Rechner")


def test_testdata_have_a_history(tmp_path, monkeypatch):
    from cockpit import testdata
    from cockpit.core.paths import HOME_VARIABLE
    monkeypatch.setenv(HOME_VARIABLE, str(tmp_path / "vorher"))
    _, root = testdata.prepare(tmp_path / "Testdaten")
    pdf = root / "PDF-Chat" / "Code"
    lines = [c.line() for c in history.log_commits(pdf)]
    assert lines == ["23.09.2026: Hilfetext geändert", "22.09.2026: Alte Datei entfernt",
                     "21.09.2026: Einstellungen ergänzt",
                     "20.09.2026, Version 1.0.0: Hilfe ergänzt", "19.09.2026: Erste Version"]
    assert [c.line() for c in history.local_changes(pdf)] == ["main.py, geändert",
                                                              "versuch.py, neu"]
    rezepte = history.log_commits(root / "Rezepte" / "Code")
    assert rezepte[0].subject == "Rezept geändert" and history.can_undo(rezepte[0])
    # Die Version "Hilfetext geändert" lässt sich sauber rückgängig machen
    history.revert(pdf, "PDF-Chat", history.log_commits(pdf)[0], NAME, EMAIL)
    assert (pdf / "hilfe.py").read_text(encoding="utf-8") == "print('Hilfe')\n"
