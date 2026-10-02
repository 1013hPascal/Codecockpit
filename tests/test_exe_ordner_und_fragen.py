"""Rückmeldung vom 02.10.2026 zur Vokabel-App.

1. Der Ordner Meine-Vokabeln kam nicht neben die Exe: beim Bau aus einem Branch gar nicht, und
   ein fehlender Ordner wurde nicht leer angelegt. Die Exe-Einstellungen zeigen die Ordner jetzt
   als Liste mit Kontrollkästchen.
2. Nach jedem Schritt im KI-Modus ein Fragefeld. Die KI antwortet, man kann diskutieren, dann
   "Weiter" oder "Mit den Hinweisen wiederholen".
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

from cockpit.core import exe
from cockpit.core.actions import ActionContext, Target
from cockpit.core.projects import Project
from cockpit.features.exe_build import ai_fix
from cockpit.ui import exe_ai, exe_flow
from cockpit.ui.exe_chat import ExeChat
from tests.conftest import said
from tests.test_phase8b import quiet_machine  # noqa: F401 (Fixture)
from tests.test_projektuebersichten import FakeTextAI, exe_window  # noqa: F401


def vokabel_project(tmp_path) -> Project:
    root = tmp_path / "VokabelApp"
    code = root / "Code"
    (code / "Meine-Vokabeln" / "Spanisch").mkdir(parents=True)
    (code / "Meine-Vokabeln" / "Spanisch" / "essen.csv").write_text("a;b\n", encoding="utf-8")
    (code / "gui.py").write_text('engine = Engine(base_dir="Meine-Vokabeln")\n'
                                 'path = Path("Meine-Vokabeln")\n', encoding="utf-8")
    (code / "config.csv").write_text("x\n", encoding="utf-8")
    (code / "paket").mkdir()
    (code / "paket" / "__init__.py").write_text("", encoding="utf-8")
    (root / "Exe").mkdir()
    return Project(1, "VokabelApp", root, code, root / "Exe")


# -- 1. Ordner neben der Exe ------------------------------------------------------------------
def test_branch_exe_gets_its_folders(tmp_path):
    project = vokabel_project(tmp_path)
    branch = tmp_path / "Branch"
    (branch / "Meine-Vokabeln").mkdir(parents=True)
    (branch / "Meine-Vokabeln" / "neu.csv").write_text("x\n", encoding="utf-8")
    built = tmp_path / "dist" / "VokabelApp"
    built.mkdir(parents=True)
    (built / "VokabelApp.exe").write_bytes(b"MZ")
    settings = exe.BuildSettings("gui.py", "VokabelApp", one_file=False,
                                 beside=["Meine-Vokabeln", "Daten"])
    result = exe.install_branch(project, built, "Cockpit-exe-bauen", settings, branch)
    home = result.exe.parent
    assert (home / "Meine-Vokabeln" / "neu.csv").is_file()      # aus dem Branch
    assert (home / "Daten").is_dir()                            # leer angelegt
    assert result.placed == ["Meine-Vokabeln", "Daten"]


def test_missing_folder_is_created_empty_but_not_files(tmp_path):
    project = vokabel_project(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    placed = exe.place_beside(project, ["Leer", "fehlt.csv", "Meine-Vokabeln"], home, None, None)
    assert placed == ["Leer", "Meine-Vokabeln"]
    assert (home / "Leer").is_dir() and not any((home / "Leer").iterdir())
    assert not (home / "fehlt.csv").exists()


def test_beside_candidates(tmp_path):
    project = vokabel_project(tmp_path)
    assert exe_flow.beside_candidates(project.code_dir) == ["config.csv", "Meine-Vokabeln"]


def test_settings_dialog_has_a_checklist(qtbot, tmp_path):
    project = vokabel_project(tmp_path)
    dialog = exe_flow.BuildSettingsDialog(project)
    qtbot.addWidget(dialog)
    texts = [dialog.beside.item(r).text() for r in range(dialog.beside.count())]
    assert texts == ["config.csv", "Meine-Vokabeln, vom Code benutzt"]
    assert dialog.beside.accessibleName() == "Ordner und Dateien neben der Exe"
    assert dialog.beside.item(1).checkState() == Qt.CheckState.Checked     # vorgeschlagen
    assert dialog.beside.item(0).checkState() == Qt.CheckState.Unchecked
    dialog.new_name.setText("Sicherungen")
    dialog.add_new()
    assert dialog.beside.item(2).text() == "Sicherungen, wird neben der Exe leer angelegt"
    assert said("Sicherungen kommt neben die Exe.")
    dialog.beside.item(1).setCheckState(Qt.CheckState.Unchecked)
    assert dialog.chosen_beside() == ["Sicherungen"]
    dialog.form.fields["start_file"].set("gui.py")
    dialog.check()
    assert dialog.settings.beside == ["Sicherungen"]


def test_settings_dialog_keeps_saved_folders(qtbot, tmp_path):
    project = vokabel_project(tmp_path)
    current = exe.BuildSettings("gui.py", "VokabelApp", beside=["Meine-Vokabeln", "Extra"])
    dialog = exe_flow.BuildSettingsDialog(project, current=current)
    qtbot.addWidget(dialog)
    assert dialog.chosen_beside() == ["Meine-Vokabeln", "Extra"]


def test_ready_lines_name_the_folders(tmp_path):
    project = vokabel_project(tmp_path)
    assert exe_flow.beside_line(project).startswith("Neben die Exe kommt kein Ordner.")
    exe.write_settings(project.code_dir, exe.BuildSettings("gui.py", "VokabelApp",
                                                           beside=["Meine-Vokabeln"]))
    assert exe_flow.beside_line(project) == "Neben die Exe kommen: Meine-Vokabeln."


def test_prompt_explains_the_folders():
    _prompt, system = ai_fix.build_prompt("V", exe.BuildSettings("gui.py", "V"), [], "", "")
    assert "Ordner neben der Exe" in system and "exist_ok=True" in system


# -- 2. Fragen nach einem Schritt -------------------------------------------------------------
class ChatAI(FakeTextAI):
    def __init__(self):
        super().__init__()
        self.prompts = []

    def ask(self, prompt, system="", cancel=None):
        self.prompts.append((prompt, system))
        return "Ja, der Ordner kommt mit. Er liegt dann neben der Exe."


def test_ask_chat_sends_step_content_and_history():
    ai = ChatAI()
    answer = ai_fix.ask_chat(ai, "VokabelApp", "Vorschlag gemacht", ["Zeile 1", "Zeile 2"],
                             [("Erste Frage?", "Erste Antwort.")], "Kommt der Ordner mit?")
    prompt, system = ai.prompts[0]
    assert answer.startswith("Ja")
    assert "Gerade abgeschlossener Schritt: Vorschlag gemacht" in prompt
    assert "Zeile 1\nZeile 2" in prompt
    assert "Frage: Erste Frage?\nAntwort der KI: Erste Antwort." in prompt
    assert prompt.rstrip().endswith("Kommt der Ordner mit?")
    assert "Ändere selbst nichts" in system


def test_with_hints():
    assert ai_fix.with_hints("", "") == ""
    assert ai_fix.with_hints("Ordner mitnehmen", "Frage: x\nAntwort der KI: y") == (
        "Ordner mitnehmen\n\nHinweise aus dem Gespräch mit dem Nutzer:\nFrage: x\nAntwort der KI: y")


def chat(qtbot, monkeypatch, make_services):
    ai = ChatAI()
    widget = ExeChat(make_services(), "VokabelApp", "Vorschlag gemacht", lambda: ["Inhalt"])
    qtbot.addWidget(widget)
    monkeypatch.setattr(widget, "_prepare_ai", lambda: ai)
    return widget, ai


def test_chat_answers_one_sentence_per_line(qtbot, monkeypatch, make_services):
    widget, ai = chat(qtbot, monkeypatch, make_services)
    assert widget.answers.accessibleName() == "Gespräch mit der KI"
    widget.question.setText("Kommt Meine-Vokabeln mit?")
    qtbot.keyClick(widget.question, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: widget.task is None and bool(widget.history), timeout=5000)
    lines = [widget.answers.item(r).text() for r in range(widget.answers.count())]
    assert lines == ["Sie: Kommt Meine-Vokabeln mit?", "KI: Ja, der Ordner kommt mit.",
                     "Er liegt dann neben der Exe."]
    assert widget.question.text() == ""
    assert said("Antwort da.")
    assert widget.hints().startswith("Frage: Kommt Meine-Vokabeln mit?\nAntwort der KI: Ja")


def proposal():
    return ai_fix.Proposal(summary="Ordner über die Exe finden.",
                           changes=[ai_fix.Change("gui.py", "Grund", "alt", "neu")])


def test_proposal_dialog_repeats_only_with_hints(qtbot, make_services):
    project = Project(1, "VokabelApp", Path("x"), Path("x/Code"), None)
    dialog = exe_ai.ProposalDialog(project, proposal(), services=make_services())
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.chat is not None
    assert "Bisher:" in dialog.lines() and "neu" in dialog.lines()
    dialog.repeat()
    assert dialog.isVisible() and dialog.repeat_hints == ""       # erst fragen
    dialog.chat.history.append(("Frage?", "Antwort."))
    dialog.repeat()
    assert not dialog.isVisible() and dialog.repeat_hints.startswith("Frage: Frage?")


def test_proposal_dialog_without_ai_has_no_chat(qtbot):
    project = Project(1, "VokabelApp", Path("x"), Path("x/Code"), None)
    dialog = exe_ai.ProposalDialog(project, proposal())
    qtbot.addWidget(dialog)
    assert dialog.chat is None


def test_review_repeats_with_the_hints(exe_window, monkeypatch):
    win, project, _built, _shown = exe_window
    runs = []
    flow = exe_ai.ExeAIFlow(win.controller.exe, project, on_finished=lambda *a: None)
    flow.ai, flow.wish, flow.error = ChatAI(), "Ordner mitnehmen", ""
    monkeypatch.setattr(exe_ai.ExeAIFlow, "run",
                        lambda self, ai, wish, error="": runs.append(wish))

    class Repeating:
        def __init__(self, *args, **kwargs):
            self.repeat_hints = "Frage: x\nAntwort der KI: y"

        def exec(self):
            return False

    monkeypatch.setattr(exe_ai, "ProposalDialog", Repeating)
    flow.review(proposal())
    assert runs == ["Ordner mitnehmen\n\nHinweise aus dem Gespräch mit dem Nutzer:\nFrage: x\n"
                    "Antwort der KI: y"]
    assert said("Der letzte Schritt wird mit den Hinweisen wiederholt.")


def test_ready_dialog_repeats_the_last_step(exe_window, monkeypatch, tmp_path):
    win, project, built, _shown = exe_window
    monkeypatch.undo()
    repeated = []

    class Flow:
        ai = object()

        def repeat(self, hints):
            repeated.append(hints)

    class Repeating:
        def __init__(self, project_, lines, parent=None, services=None):
            assert services is not None                    # mit KI: Fragefeld da
            self.repeat_hints = "Frage: x\nAntwort der KI: y"

        def exec(self):
            return False

    monkeypatch.setattr(exe_flow, "ReadyDialog", Repeating)
    win.controller.exe.offer_build(ActionContext(win.services, project, Target.EXE), ["x"],
                                   tmp_path, Flow())
    assert repeated == ["Frage: x\nAntwort der KI: y"]


def test_ready_dialog_buttons(qtbot, make_services):
    project = Project(1, "VokabelApp", Path("x"), Path("x/Code"), None)
    dialog = exe_flow.ReadyDialog(project, ["Änderungen übernommen."], services=make_services())
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.chat is not None
    assert dialog.build_button.text() == "Exe e&rstellen"
    dialog.repeat()
    assert dialog.isVisible()                                     # ohne Frage kein Wiederholen
    plain = exe_flow.ReadyDialog(project, ["x"])
    qtbot.addWidget(plain)
    assert plain.chat is None


# -- 3. Einstellungen als erster Schritt (Wunsch vom 02.10.2026) -------------------------------
def test_flow_dialog_starts_with_the_folders(qtbot, tmp_path):
    project = vokabel_project(tmp_path)
    dialog = exe_flow.BuildSettingsDialog(project, in_flow=True)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Exe aus dem Code erstellen: VokabelApp, Einstellungen"
    assert dialog.initial_focus_widget is dialog.beside


def settings_window(exe_window, monkeypatch, answer):
    """answer(dialog) wählt im Einstellungs-Fenster und gibt True für Weiter zurück."""
    win, project, _built, _shown = exe_window
    monkeypatch.undo()
    shown = []

    def fake_exec(dialog):
        shown.append(dialog.chosen_beside())
        if not answer(dialog):
            return False
        dialog.form.fields["start_file"].set("main.py")
        dialog.check()
        return dialog.settings is not None

    monkeypatch.setattr(exe_flow.BuildSettingsDialog, "exec", fake_exec)
    return win, project, shown


def test_settings_step_saves_the_choice(exe_window, monkeypatch):
    def choose(dialog):
        dialog.new_name.setText("Meine-Vokabeln")
        dialog.add_new()
        return True

    win, project, shown = settings_window(exe_window, monkeypatch, choose)
    assert win.controller.exe.settings_step(project)
    assert exe.read_settings(project.code_dir).beside == ["Meine-Vokabeln"]
    assert (project.code_dir / exe.read_settings(project.code_dir).spec_name).is_file()
    assert said("Exe-Einstellungen gespeichert.")
    assert win.controller.exe.settings_step(project)                # gespeicherte Auswahl
    assert shown[-1] == ["Meine-Vokabeln"]


def test_cancelled_settings_stop_the_flow(exe_window, monkeypatch):
    win, project, shown = settings_window(exe_window, monkeypatch, lambda dialog: False)
    asked = []
    monkeypatch.setattr(exe_flow, "choose_from_list", lambda *a: asked.append(a) or None)
    win.controller.exe.build_menu(ActionContext(win.services, project, Target.EXE))
    assert shown and asked == []                                  # keine Frage mit oder ohne KI
    assert exe.read_settings(project.code_dir) is None


def test_settings_come_before_the_ai_choice(exe_window, monkeypatch):
    win, project, _built, _shown = exe_window
    order = []
    monkeypatch.setattr(exe_flow.ExeActions, "settings_step",
                        lambda self, p: order.append("Einstellungen") or True)
    monkeypatch.setattr(exe_flow, "choose_from_list",
                        lambda *a: order.append("mit oder ohne KI") or None)
    win.controller.exe.build_menu(ActionContext(win.services, project, Target.EXE))
    assert order == ["Einstellungen", "mit oder ohne KI"]


def test_branch_build_uses_the_new_folders(exe_window, monkeypatch, tmp_path):
    win, project, _built, _shown = exe_window
    branch = tmp_path / "Branch"
    branch.mkdir()
    exe.write_settings(project.code_dir, exe.BuildSettings("main.py", "Rechner",
                                                           beside=["Meine-Vokabeln"]))
    exe.write_settings(branch, exe.BuildSettings("main.py", "Rechner", beside=["Daten"]))
    used = []

    class FakeBuild:
        def __init__(self, services, project_, settings, *args, **kwargs):
            used.append(settings.beside)
            self.result, self.fix_requested = None, False

        def exec(self):
            return False

    monkeypatch.setattr(exe_flow, "BuildDialog", FakeBuild)
    monkeypatch.setattr(exe, "find_python", lambda: ["py"])
    win.controller.exe.build_ai_branch(project, branch)
    assert used == [["Meine-Vokabeln", "Daten"]]


# -- 4. Fehlerfenster beim Start und selbst testen (Rückmeldung vom 02.10.2026) ----------------
def test_start_test_fails_on_an_error_window(tmp_path, monkeypatch):
    """Bei einer Exe mit Fenster lief das Programm mit Fehlerfenster weiter, der Test bestand."""
    import sys
    import pytest
    from cockpit.core.errors import CockpitError
    script = tmp_path / "laeuft.py"
    script.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    monkeypatch.setattr(exe, "error_window_text",
                        lambda pid: "Unhandled exception in script\nNameError: name 'sys'")
    monkeypatch.setattr(exe.subprocess, "Popen", _python_popen(sys.executable, script))
    with pytest.raises(CockpitError) as raised:
        exe.start_test(tmp_path / "VokabelApp.exe", seconds=5, windowed=True)
    assert raised.value.message.startswith("Die neue Exe zeigt beim Start eine Fehlermeldung.")
    assert "NameError: name 'sys'" in raised.value.details


def _python_popen(python, script):
    import subprocess
    real = subprocess.Popen

    def popen(args, **kwargs):
        return real([python, str(script)], **kwargs)
    return popen


def test_error_window_is_read(tmp_path):
    """Echtes Meldungsfenster wie bei PyInstaller: Titel und Fehlermeldung werden gelesen."""
    import subprocess
    import sys
    import time
    import pytest
    if sys.platform != "win32":
        pytest.skip("nur Windows")
    from cockpit.core import error_windows
    child = ("import ctypes\nctypes.windll.user32.MessageBoxW(0, 'Traceback (most recent call "
             "last):\\nNameError: name sys is not defined', 'Unhandled exception in script', 0)\n")
    process = subprocess.Popen([sys.executable, "-c", child])
    try:
        text = ""
        for _ in range(60):
            time.sleep(0.25)
            text = error_windows.error_text(process.pid)
            if text:
                break
        assert text.startswith("Unhandled exception in script")
        assert "NameError: name sys is not defined" in text
        assert error_windows.error_text(999999) == ""            # fremder Prozess: nichts
    finally:
        process.kill()


def self_test_dialog(qtbot, tmp_path):
    project = vokabel_project(tmp_path)
    dialog = exe_flow.SelfTestDialog(project, project.exe_dir / "VokabelApp.exe")
    qtbot.addWidget(dialog)
    dialog.show()
    return dialog


def test_self_test_needs_a_message_for_the_ai(qtbot, tmp_path):
    dialog = self_test_dialog(qtbot, tmp_path)
    assert dialog.windowTitle() == "Exe selbst testen: VokabelApp"
    assert dialog.edit.accessibleName() == "Fehlermeldung oder Beschreibung"
    dialog.request_fix()
    assert dialog.isVisible() and dialog.choice == ""
    assert said("Bitte fügen Sie zuerst die Fehlermeldung ein")
    dialog.edit.setPlainText("NameError: name 'sys' is not defined")
    dialog.request_fix()
    assert dialog.choice == exe_flow.SelfTestDialog.FIX
    assert dialog.error_text == "NameError: name 'sys' is not defined"


def test_self_test_starts_the_exe(qtbot, tmp_path, monkeypatch):
    from cockpit.core import core_actions
    started = []
    monkeypatch.setattr(core_actions, "start_program", started.append)
    dialog = self_test_dialog(qtbot, tmp_path)
    dialog.start_exe()
    assert started == [dialog.exe_path]


def test_choose_self_test_opens_the_window(exe_window, monkeypatch, tmp_path):
    win, project, _built, _shown = exe_window
    monkeypatch.setattr(exe_flow, "ask_buttons", lambda *a, **k: 0)   # selbst testen
    tested = []
    monkeypatch.setattr(exe_flow.ExeActions, "self_test",
                        lambda self, p, path: tested.append(path))
    win.controller.exe.after_branch_test(project, "x.exe", tmp_path / "x.exe")
    assert tested == [tmp_path / "x.exe"]


def test_pasted_error_goes_to_the_ai(exe_window, monkeypatch, tmp_path):
    win, project, _built, _shown = exe_window
    fixes, merges = [], []

    class Dialog:
        FIX, MERGE = "fix", "merge"

        def __init__(self, *args):
            self.choice, self.error_text = "fix", "NameError: name 'sys' is not defined"

        def exec(self):
            return True

    monkeypatch.setattr(exe_flow, "SelfTestDialog", Dialog)
    monkeypatch.setattr(exe_flow.ExeActions, "fix_with_ai",
                        lambda self, p, error: fixes.append(error))
    monkeypatch.setattr(exe_flow.ExeActions, "merge_ai_branch",
                        lambda self, p, delete: merges.append(delete))
    win.controller.exe.self_test(project, tmp_path / "x.exe")
    assert fixes == ["NameError: name 'sys' is not defined"]
    Dialog.__init__ = lambda self, *a: setattr(self, "choice", "merge")
    monkeypatch.setattr(exe_flow, "ask_buttons", lambda *a, **k: 1)       # Branch löschen
    win.controller.exe.self_test(project, tmp_path / "x.exe")
    assert merges == [True]


# -- 5. Leerer Ordner neben der Exe wird gefüllt (Rückmeldung vom 02.10.2026) ------------------
def test_empty_folder_from_the_start_test_gets_the_files(tmp_path):
    """Die Exe legte Meine-Vokabeln beim Start-Test leer an. Die Vokabeln fehlten danach."""
    project = vokabel_project(tmp_path)
    home = tmp_path / "home"
    (home / "Meine-Vokabeln").mkdir(parents=True)                 # von der Exe angelegt
    placed = exe.place_beside(project, ["Meine-Vokabeln"], home, None, None)
    assert placed == ["Meine-Vokabeln"]
    assert (home / "Meine-Vokabeln" / "Spanisch" / "essen.csv").is_file()


def test_folder_with_user_data_stays_untouched(tmp_path):
    project = vokabel_project(tmp_path)
    home = tmp_path / "home"
    (home / "Meine-Vokabeln").mkdir(parents=True)
    (home / "Meine-Vokabeln" / "eigene.csv").write_text("meins\n", encoding="utf-8")
    assert exe.place_beside(project, ["Meine-Vokabeln"], home, None, None) == []
    assert [p.name for p in (home / "Meine-Vokabeln").iterdir()] == ["eigene.csv"]


def test_empty_previous_folder_does_not_hide_the_code(tmp_path):
    project = vokabel_project(tmp_path)
    backup = tmp_path / "backup"
    (backup / "Meine-Vokabeln").mkdir(parents=True)               # alte Exe: nur leer
    home = tmp_path / "home"
    home.mkdir()
    exe.place_beside(project, ["Meine-Vokabeln"], home, backup, Path("."))
    assert (home / "Meine-Vokabeln" / "Spanisch" / "essen.csv").is_file()


def test_files_like_the_readme_can_be_chosen(tmp_path):
    project = vokabel_project(tmp_path)
    (project.code_dir / "readme.md").write_text("# Vokabeln\n", encoding="utf-8")
    (project.code_dir / "start.bat").write_text("@echo off\n", encoding="utf-8")
    names = exe_flow.beside_candidates(project.code_dir)
    assert "readme.md" in names and "start.bat" in names and "gui.py" not in names
    home = tmp_path / "home"
    home.mkdir()
    exe.place_beside(project, ["readme.md"], home, None, None)
    assert (home / "readme.md").read_text(encoding="utf-8") == "# Vokabeln\n"


def test_readme_is_always_refreshed(tmp_path):
    """Wunsch des Nutzers: Die README neben der Exe ist immer die aktuelle aus dem Code."""
    from cockpit.core import backups
    project = vokabel_project(tmp_path)
    readme = project.code_dir / "README.md"
    readme.write_text("# Version 1\n", encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir()
    assert exe.place_beside(project, ["README.md"], home, None, None) == ["README.md"]
    assert exe.place_beside(project, ["README.md"], home, None, None) == []   # gleich: nichts
    readme.write_text("# Version 2\n", encoding="utf-8")
    assert exe.place_beside(project, ["README.md"], home, None, None) == ["README.md"]
    assert (home / "README.md").read_text(encoding="utf-8") == "# Version 2\n"
    saved = list(backups.backups_dir().rglob("README.md"))
    assert [p.read_text(encoding="utf-8") for p in saved] == ["# Version 1\n"]
    (project.code_dir / "config.csv").write_text("neu\n", encoding="utf-8")
    (home / "config.csv").write_text("eigene Einstellung\n", encoding="utf-8")
    exe.place_beside(project, ["config.csv"], home, None, None)               # andere Dateien
    assert (home / "config.csv").read_text(encoding="utf-8") == "eigene Einstellung\n"
    assert exe.is_readme("readme.de.md") and not exe.is_readme("config.csv")
