"""Phase 5b: Sicherheitsprüfung, .gitignore, Neues Projekt hochladen, Auf GitHub hochladen.

Alle Geheimnisse sind erfunden und werden erst zur Laufzeit zusammengesetzt. So erkennt kein
Scanner auf GitHub sie als echte Tokens im Code der Tests.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from cockpit.core import git, safety_check, upload
from cockpit.core.flows.engine import FlowContext
from cockpit.core.flows.questions import ScriptedAsker
from cockpit.core.projects import read_config
from cockpit.core.safety_check import Kind
from cockpit.core.upload import UploadSpec
from cockpit.ui import project_actions, upload_dialogs, upload_flow
from tests.conftest import FakePlatform, make_project, said
from tests.test_phase5a import EMAIL, NAME, account, live, sh, wait_idle  # noqa: F401

pytestmark = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")

# Beispiel-Geheimnisse, die die Prüfung finden muss. Sie sehen aus wie echte (ohne das Wort
# "Erfunden", das die Prüfung seit dem 28.09.2026 als erfunden erkennt) und werden erst hier
# zusammengesetzt, damit die Prüfung sie nicht in dieser Datei selbst findet.
GITHUB_TOKEN = "ghp" + "_" + "Qx7mZkRw0123456789abcdefghijklmnopqrstuv"
OPENAI_KEY = "sk" + "-proj-" + "Qx7mZkRw0123456789abcdefghij"
ANTHROPIC_KEY = "sk" + "-ant-" + "api03-Qx7mZkRw0123456789abcdef"
AWS_KEY = "AKIA" + "QX7MZKRW12345678"
PASSWORD_LINE = "pass" + 'word = "Sommer2026!"'


def write(folder: Path, name: str, text: str) -> Path:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def kinds(report) -> list[tuple[str, str, str, int]]:
    return [(f.kind.value, f.path, f.rule, f.line) for f in report.findings]


# -- Geheimnisse ----------------------------------------------------------------------------
@pytest.mark.parametrize("line, rule", [
    (f'TOKEN = "{GITHUB_TOKEN}"', "GitHub-Token"),
    (f"key = '{OPENAI_KEY}'", "OpenAI-Schlüssel"),
    (f"ANTHROPIC={ANTHROPIC_KEY}", "Anthropic-Schlüssel"),
    (f"aws = {AWS_KEY}", "AWS-Zugangsschlüssel"),
    ("-----BEGIN RSA " + "PRIVATE KEY-----", "Privater Schlüssel"),
    (PASSWORD_LINE, "Passwort oder Schlüssel im Code"),
    ("API" + '_KEY: "abc123def456"', "Passwort oder Schlüssel im Code"),
])
def test_secret_rules(tmp_path, line, rule):
    write(tmp_path, "config.py", f"x = 1\n{line}\n")
    report = safety_check.scan(tmp_path)
    assert kinds(report) == [("secret", "config.py", rule, 2)]
    assert report.findings[0].text == f"Geheimnis: config.py, Zeile 2, {rule}"
    assert line not in report.findings[0].text                  # nie den Wert nennen


@pytest.mark.parametrize("line", [
    'password = "changeme"',
    'password = os.environ["PASSWORD"]',
    'password = ""',
    'api_key = "<Ihr Schlüssel>"',
    'token = "${TOKEN}"',
    "print('kein Geheimnis')",
])
def test_placeholders_are_no_secrets(tmp_path, line):
    write(tmp_path, "config.py", line + "\n")
    assert safety_check.scan(tmp_path).ok


def test_env_and_key_files_stop_upload(tmp_path):
    write(tmp_path, ".env", "A=1\n")
    write(tmp_path, ".env.local", "A=1\n")
    write(tmp_path, ".env.example", "A=\n")
    write(tmp_path, "certs/server.pem", "x\n")
    report = safety_check.scan(tmp_path)
    assert sorted(f.path for f in report.blocking) == [".env", ".env.local", "certs/server.pem"]
    assert all(f.rule == "Datei mit Zugangsdaten" for f in report.blocking)


def test_private_data_and_large_files(tmp_path):
    write(tmp_path, "daten.db", "x")
    write(tmp_path, "app.log", "x")
    with open(tmp_path / "video.mp4", "wb") as f:
        f.truncate(60 * 1024 * 1024)
    with open(tmp_path / "riesig.zip", "wb") as f:
        f.truncate(120 * 1024 * 1024)
    report = safety_check.scan(tmp_path)
    assert sorted(kinds(report)) == [
        ("large", "video.mp4", "60 MB", 0),
        ("private_data", "app.log", "Logdatei", 0),
        ("private_data", "daten.db", "Datenbank", 0),
        ("too_large", "riesig.zip", "120 MB", 0),
    ]
    assert [f.path for f in report.blocking] == ["riesig.zip"]
    too_large = next(f for f in report.findings if f.kind is Kind.TOO_LARGE)
    assert too_large.text == "Zu groß für GitHub: riesig.zip, 120 MB"


def test_binary_files_are_not_read_line_by_line(tmp_path):
    (tmp_path / "bild.png").write_bytes(b"\x89PNG\0\0" + GITHUB_TOKEN.encode())
    assert safety_check.scan(tmp_path).ok


def test_not_a_secret_is_remembered_without_the_value(tmp_path):
    write(tmp_path, "tests/test_x.py", f'FAKE = "{GITHUB_TOKEN}"\n')
    finding = safety_check.scan(tmp_path).findings[0]
    safety_check.mark_not_secret(tmp_path, finding)
    assert safety_check.scan(tmp_path).ok
    stored = (tmp_path / "cockpit.toml").read_text(encoding="utf-8")
    assert GITHUB_TOKEN not in stored
    assert read_config(tmp_path)["safety"]["not_secret"] == [
        f"tests/test_x.py:{finding.fingerprint}"]
    write(tmp_path, "tests/test_x.py", f'FAKE = "{GITHUB_TOKEN}"  # geändert\n')
    assert not safety_check.scan(tmp_path).ok                   # neue Zeile: neu prüfen


def test_secret_in_earlier_commit_is_found(tmp_path):
    write(tmp_path, "config.py", f'TOKEN = "{GITHUB_TOKEN}"\n')
    sh(tmp_path, "init", "-q")
    sh(tmp_path, "add", "-A")
    sh(tmp_path, "commit", "-q", "-m", "mit Token")
    write(tmp_path, "config.py", 'TOKEN = os.environ["TOKEN"]\n')
    sh(tmp_path, "commit", "-q", "-am", "ohne Token")
    assert safety_check.scan(tmp_path).ok                       # heute sauber
    report = safety_check.scan(tmp_path, history_range="HEAD")
    assert kinds(report) == [("secret_history", "config.py", "GitHub-Token", 0)]
    assert report.findings[0].text == ("Geheimnis in einem früheren Commit: config.py, "
                                       "GitHub-Token")


def test_private_email_only_for_public_repositories(tmp_path):
    write(tmp_path, "a.py", "x = 1\n")
    emails = ["pascal@beispiel.de", EMAIL]
    assert safety_check.scan(tmp_path, public=False, emails=emails).ok
    report = safety_check.scan(tmp_path, public=True, emails=emails)
    assert kinds(report) == [("private_email", "", "pascal@beispiel.de", 0)]
    assert not report.blocking


# -- .gitignore -----------------------------------------------------------------------------
def test_gitignore_is_created_and_completed(tmp_path):
    added = safety_check.ensure_gitignore(tmp_path)
    assert ".venv/" in added and ".env" in added and "*.db" in added
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert text.startswith("# Ergänzt von CodeCockpit\n# Virtuelle Umgebungen")
    assert safety_check.ensure_gitignore(tmp_path) == []
    assert safety_check.gitignore_missing(tmp_path) == []


def test_gitignore_keeps_existing_lines(tmp_path):
    write(tmp_path, ".gitignore", "meine_datei.txt\n.venv/\n__pycache__/\n*.py[cod]\n"
                                  ".pytest_cache/\n.mypy_cache/\nvenv/\nenv/")
    added = safety_check.ensure_gitignore(tmp_path)
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert text.startswith("meine_datei.txt\n.venv/\n")
    assert ".venv/" not in added
    assert "# Virtuelle Umgebungen und Caches" not in text      # Gruppe war schon komplett
    assert "# Build-Ordner und Exe-Dateien\nbuild/" in text


def test_ignore_file_takes_tracked_file_out_of_git(tmp_path):
    write(tmp_path, "daten.db", "x")
    sh(tmp_path, "init", "-q")
    sh(tmp_path, "add", "-A")
    sh(tmp_path, "commit", "-q", "-m", "x")
    safety_check.ignore_file(tmp_path, "daten.db")
    assert (tmp_path / "daten.db").exists()                     # bleibt auf der Festplatte
    assert "/daten.db" in (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "daten.db" not in safety_check.files_to_upload(tmp_path)


# -- Vorbereiten ------------------------------------------------------------------------------
def test_suggest_name():
    assert upload.suggest_name("Mein Projekt") == "Mein-Projekt"
    assert upload.suggest_name("PDF-Chat") == "PDF-Chat"
    assert upload.suggest_name("Mein Übersetzer für Größen") == "Mein-Uebersetzer-fuer-Groessen"
    assert upload.suggest_name("§$%") == "projekt"


def test_name_problem_says_what_is_wrong():
    """Rückmeldung aus dem Test von 5b: Bei "Mein Test" war das Leerzeichen das Problem."""
    assert upload.name_problem("codecockpit-test") == ""
    assert upload.name_problem("Mein Test") == ("Der Name darf keine Leerzeichen enthalten. "
                                                "Nehmen Sie stattdessen einen Bindestrich, zum "
                                                "Beispiel Mein-Test.")
    assert upload.name_problem("Größe") == ("Der Name darf keine Umlaute enthalten, zum "
                                            "Beispiel Groesse.")
    assert upload.name_problem("a/b").startswith("Der Name darf nur Buchstaben, Ziffern")
    assert upload.name_problem("") == "Bitte einen Namen eingeben."


def test_prepare_creates_git_gitignore_license_and_identity(tmp_path):
    code = tmp_path / "Code"
    write(code, "main.py", "x\n")
    spec = UploadSpec("Neu", license="MIT")
    notes = upload.prepare(code, "Neu", spec, FakePlatform(), NAME, EMAIL, ScriptedAsker())
    assert git.is_repo(code) and git.identity(code) == (NAME, EMAIL)
    assert (code / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")
    assert NAME in (code / "LICENSE").read_text(encoding="utf-8")
    assert notes[0] == "Git-Repository angelegt."
    assert "Lizenzdatei MIT angelegt." in notes
    (code / "LICENSE").write_text("Eigene Lizenz\n", encoding="utf-8")
    upload.prepare(code, "Neu", spec, FakePlatform(), NAME, EMAIL, ScriptedAsker())
    assert (code / "LICENSE").read_text(encoding="utf-8") == "Eigene Lizenz\n"


def test_prepare_without_license(tmp_path):
    code = tmp_path / "Code"
    write(code, "main.py", "x\n")
    upload.prepare(code, "Neu", UploadSpec("Neu", license=upload.NO_LICENSE), FakePlatform(),
                   NAME, EMAIL, ScriptedAsker())
    assert not (code / "LICENSE").exists()


# -- Der Ablauf ------------------------------------------------------------------------------
def run_flow(services, project, spec, platform):
    context = FlowContext(services, project, ScriptedAsker(),
                          data={"spec": spec, "platform": platform, "git_email": EMAIL})
    steps = []
    summary = services.flows.run(upload.NEW_PROJECT, context,
                                 lambda n, total, text: steps.append(text))
    return summary, context.data, steps


def test_new_project_flow_pushes_first_version(make_services, projects_root, tmp_path):
    services = make_services()
    platform = FakePlatform()
    platform.base_dir = tmp_path / "plattform"
    platform.base_dir.mkdir()
    code = make_project(projects_root, "Neu") / "Code"
    project = services.projects.add(code.parent)
    spec = UploadSpec("Neu", "Test", private=True, license="MIT")
    upload.prepare(code, "Neu", spec, platform, NAME, EMAIL, ScriptedAsker())
    summary, data, steps = run_flow(services, project, spec, platform)
    assert summary.completed, summary.text()
    assert steps == ["Schritt 1 von 4: Sicherheitsprüfung", "Schritt 2 von 4: Commit wird erstellt",
                     "Schritt 3 von 4: Repository wird angelegt",
                     "Schritt 4 von 4: Wird hochgeladen"]
    assert summary.text() == ("Fertig. Neues privates Repository tester/Neu. "
                              "Branch main ist hochgeladen.")
    bare = platform.base_dir / "Neu.git"
    log = sh(bare, "log", "--format=%s|%an|%ae", "main")
    assert log.strip() == f"Erste Version|{NAME}|{EMAIL}"
    state = git.status(code)
    assert state.upstream == "origin/main" and state.changed == []
    # Noch einmal: kein zweites Repository, nichts Neues
    summary, _, _ = run_flow(services, project, spec, platform)
    assert summary.completed and len(platform.created) == 1


def test_flow_stops_on_secret_before_anything_is_created(make_services, projects_root,
                                                         tmp_path):
    services = make_services()
    platform = FakePlatform()
    platform.base_dir = tmp_path
    code = make_project(projects_root, "Geheim") / "Code"
    write(code, "config.py", f'TOKEN = "{GITHUB_TOKEN}"\n')
    project = services.projects.add(code.parent)
    spec = UploadSpec("Geheim")
    upload.prepare(code, "Geheim", spec, platform, NAME, EMAIL, ScriptedAsker())
    summary, _, _ = run_flow(services, project, spec, platform)
    assert not summary.completed
    assert summary.text().startswith("Nicht fertig. Schritt 1 von 4 ist fehlgeschlagen: "
                                     "Sicherheitsprüfung. Die Sicherheitsprüfung hat das "
                                     "Hochladen gestoppt.")
    assert platform.created == []
    assert git.run(["rev-parse", "-q", "--verify", "HEAD"], code, check=False).returncode != 0


def test_scan_skips_accepted_warnings(tmp_path):
    code = tmp_path / "Code"
    write(code, "daten.db", "x")
    spec = UploadSpec("X")
    assert [f.path for f in upload.scan(code, spec, EMAIL).warnings] == ["daten.db"]
    spec.accepted.add(("private_data", "daten.db", "Datenbank"))
    assert upload.scan(code, spec, EMAIL).ok


# -- Oberfläche: Sicherheitsprüfung ---------------------------------------------------------
def safety_dialog(qtbot, code, spec=None):
    spec = spec or UploadSpec("X")
    if not git.is_repo(code):
        git.init(code)
    report = upload.scan(code, spec, EMAIL)
    dialog = upload_dialogs.SafetyDialog(report, code, spec, EMAIL,
                                         rescan=lambda: upload.scan(code, spec, EMAIL))
    qtbot.addWidget(dialog)
    return dialog


def test_safety_dialog_lists_findings_and_blocks_continue(qtbot, tmp_path):
    code = tmp_path / "Code"
    write(code, "config.py", f'TOKEN = "{GITHUB_TOKEN}"\n')
    write(code, "daten.db", "x")
    dialog = safety_dialog(qtbot, code)
    assert dialog.windowTitle() == "Sicherheitsprüfung: 1 Fund stoppt das Hochladen, 1 Warnung"
    texts = [dialog.list.item(r).text() for r in range(dialog.list.count())]
    assert texts == ["Geheimnis: config.py, Zeile 1, GitHub-Token. Stoppt das Hochladen",
                     "Private Daten: daten.db, Datenbank. Kommt in .gitignore"]
    assert dialog.list.accessibleName() == "Funde"
    assert dialog.initial_focus_widget is dialog.list
    assert not dialog.continue_button.isEnabled()
    assert dialog.not_secret_button.isEnabled() and not dialog.accept_button.isEnabled()
    dialog.mark_current()                                       # kein Geheimnis
    assert dialog.continue_button.isEnabled()
    assert said("Als kein Geheimnis markiert.")
    dialog.finish()                                             # Warnung: sichere Vorgabe
    assert dialog.result() == dialog.DialogCode.Accepted
    assert "/daten.db" in (code / ".gitignore").read_text(encoding="utf-8")


def test_safety_dialog_ignore_and_accept(qtbot, tmp_path):
    code = tmp_path / "Code"
    write(code, ".env", "A=1\n")
    write(code, "app.log", "x")
    dialog = safety_dialog(qtbot, code)
    dialog.list.setCurrentRow(0)
    assert dialog.current().path == ".env"
    dialog.ignore_current()
    assert said(".env kommt in .gitignore und wird nicht hochgeladen.")
    assert dialog.continue_button.isEnabled()
    dialog.list.setCurrentRow(0)
    dialog.accept_current()
    assert dialog.list.item(0).text() == "Private Daten: app.log, Logdatei. Wird trotzdem hochgeladen"
    dialog.finish()
    assert "/app.log" not in (code / ".gitignore").read_text(encoding="utf-8")
    assert ("private_data", "app.log", "Logdatei") in dialog.accepted


def test_private_email_needs_explicit_confirmation(qtbot, tmp_path):
    code = tmp_path / "Code"
    write(code, "a.py", "x\n")
    git.init(code)
    git.set_identity(code, NAME, "pascal@beispiel.de")
    dialog = safety_dialog(qtbot, code, UploadSpec("X", private=False))
    assert dialog.list.item(0).text().startswith(
        "Private E-Mail-Adresse: pascal@beispiel.de. Sie wird im öffentlichen Repository")
    assert not dialog.continue_button.isEnabled()
    assert not dialog.ignore_button.isEnabled()
    dialog.accept_current()
    assert dialog.continue_button.isEnabled()


# -- Oberfläche: Angaben ---------------------------------------------------------------------
def test_upload_dialog_checks_name_and_builds_spec(qtbot, monkeypatch):
    errors = []
    monkeypatch.setattr(upload_dialogs, "show_error", lambda *a: errors.append(a[2]))
    dialog = upload_dialogs.UploadDialog("Neues Projekt hochladen", "Mein Projekt", "GitHub",
                                         "tester", ["verein"], True, "MIT")
    qtbot.addWidget(dialog)
    names = [dialog.form.fields[k].focus.accessibleName() for k in dialog.form.fields]
    assert names == ["Name auf GitHub", "Kurzbeschreibung", "Sichtbarkeit", "Lizenz", "Ziel"]
    assert dialog.initial_focus_widget is dialog.form.fields["name"].focus
    dialog.check()
    assert errors and errors[0].startswith("Der Name darf keine Leerzeichen enthalten.")
    dialog.form.fields["name"].set("Mein-Projekt")
    dialog.form.fields["visibility"].set("Öffentlich")
    dialog.form.fields["target"].set("verein")
    dialog.check()
    assert dialog.spec.name == "Mein-Projekt" and not dialog.spec.private
    assert dialog.spec.organization == "verein" and dialog.spec.license == "MIT"


# -- Oberfläche: ganzer Ablauf ----------------------------------------------------------------
def test_download_needs_an_account(live, qtbot, make_services):
    services = make_services()
    win = live(services)
    win.project_list.setCurrentRow(1)
    entries = win.current_entries()
    assert entries[0].label == ("Projekt von GitHub herunterladen …, nicht verfügbar: Es ist "
                                "noch kein Konto bei einer Plattform eingerichtet.")
    win.project_list.setCurrentRow(0)
    assert [e.label for e in win.current_entries()] == ["Projekt vom Rechner hinzufügen …"]


def test_add_local_then_upload_end_to_end(live, qtbot, account, projects_root, tmp_path,
                                          monkeypatch):
    """Rückmeldung aus dem Test von 5b: Hinzufügen und Hochladen sind getrennt. Nach dem
    Hinzufügen bietet das Cockpit das Hochladen an, Vorgabe ist "Später"."""
    services, acc, platform = account
    platform.base_dir = tmp_path / "plattform"
    platform.base_dir.mkdir()
    services.settings.update(git_name=NAME, git_email=EMAIL)
    source = tmp_path / "Quelle" / "Mein Rechner"
    write(source, "main.py", "print(1)\n")
    write(source, "alt.bak", "x")
    win = live(services)

    class FakeUploadDialog:
        def __init__(self, title, name, platform_name, user, organizations, private, license,
                     parent=None, *features, source=None):
            assert title == "Mein Rechner auf GitHub hochladen"
            assert (name, user, private, license) == ("Mein-Rechner", "tester", True, "MIT")
            self.spec = UploadSpec(name, "Rechnet", private, license)

        def exec(self):
            return True

    class FakeSafety:
        def __init__(self, report, code_dir, spec, email, rescan=None, parent=None):
            self.report, self.code_dir = report, code_dir
            self.accepted = set()

        def exec(self):
            assert [f.path for f in self.report.findings] == ["alt.bak"]
            safety_check.ignore_file(self.code_dir, "alt.bak")
            return True

    asked, questions, infos, errors = [], [], [], []
    monkeypatch.setattr(project_actions, "show_error", lambda *a: errors.append(a[2:]))
    monkeypatch.setattr(upload_flow, "show_error", lambda *a: errors.append(a[2:]))
    monkeypatch.setattr(project_actions, "pick_folder", lambda *a: source)
    monkeypatch.setattr(project_actions, "ask_buttons", lambda *a, **k: 0)     # verschieben
    monkeypatch.setattr(project_actions, "confirm",
                        lambda p, t, text, **k: asked.append((text, k)) or True)
    monkeypatch.setattr(upload_dialogs, "UploadDialog", FakeUploadDialog)
    monkeypatch.setattr(upload_dialogs, "SafetyDialog", FakeSafety)
    monkeypatch.setattr(upload_flow, "confirm", lambda p, t, text, **k: questions.append(text)
                        or True)
    monkeypatch.setattr(upload_flow, "show_info", lambda p, t, text: infos.append(text))
    win.run_entry(win.current_entries()[0])                    # Projekt vom Rechner hinzufügen
    qtbot.waitUntil(lambda: bool(infos) or bool(errors), timeout=20000)
    assert errors == []
    wait_idle(qtbot, win)
    target = projects_root / "Mein Rechner" / "Code"
    assert not source.exists() and (target / "main.py").exists()          # verschoben
    offer, buttons = asked[-1]
    assert offer.startswith("Mein Rechner ist noch nicht auf GitHub. Jetzt hochladen?")
    assert buttons == {"yes": "Jetzt hochladen …", "no": "Später"}
    assert questions[0].startswith("Das Cockpit prüft den Code auf Geheimnisse, legt auf "
                                   "GitHub das private Repository tester/Mein-Rechner an")
    assert "kopiert" not in questions[0]
    assert infos[0].startswith("Fertig. Neues privates Repository tester/Mein-Rechner.")
    assert "ist in der Zwischenablage" in infos[0]
    files = sh(platform.base_dir / "Mein-Rechner.git", "ls-tree", "--name-only", "main")
    assert "main.py" in files and "LICENSE" in files and "alt.bak" not in files
    project = services.projects.find_by_dir(target.parent)
    assert project.account_id == acc.id
    assert said("Schritt 4 von 4: Wird hochgeladen …")


def test_upload_offer_defaults_to_later(live, qtbot, account, projects_root, tmp_path,
                                        monkeypatch):
    services, acc, platform = account
    folder = make_project(tmp_path, "Spaeter")
    win = live(services)
    started = []
    monkeypatch.setattr(project_actions, "pick_folder", lambda *a: folder)
    monkeypatch.setattr(project_actions, "confirm", lambda *a, **k: False)   # Escape: Später
    monkeypatch.setattr(upload_flow.UploadRunner, "start", lambda self: started.append(1))
    win.controller.add_local()
    assert said("Spaeter hinzugefügt.") and started == []


def test_download_from_list_with_organizations(live, qtbot, account, projects_root, tmp_path,
                                               monkeypatch):
    from cockpit.platforms.base import GitCredentials, RemoteRepo, RepoRef
    from tests.test_phase5a import make_remote
    services, acc, platform = account
    bare = make_remote(tmp_path, "Vereinsseite")
    platform.git_credentials = lambda: GitCredentials(False, {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": f"url.{bare.parent.as_uri()}/.insteadOf",
        "GIT_CONFIG_VALUE_0": "https://github.com/verein/"})
    own = RemoteRepo(RepoRef("tester", "Eigenes"), True, "https://github.com/tester/Eigenes.git",
                     "https://github.com/tester/Eigenes", "2026-09-01T00:00:00Z")
    club = RemoteRepo(RepoRef("verein", "Vereinsseite"), False,
                      "https://github.com/verein/Vereinsseite.git",
                      "https://github.com/verein/Vereinsseite", "2026-09-20T00:00:00Z")
    platform.remote = [own]
    platform.organizations = lambda: ["verein"]
    original = platform.repositories
    platform.repositories = lambda owner="": [club] if owner == "verein" else original()
    win = live(services)
    shown = []
    monkeypatch.setattr(project_actions, "choose_from_list",
                        lambda parent, title, name, items, current=0: shown.append(items) or 1)
    win.project_list.setCurrentRow(1)
    win.run_entry(win.current_entries()[0])
    qtbot.waitUntil(lambda: said("Vereinsseite heruntergeladen."), timeout=15000)
    assert shown[0] == ["Adresse eingeben …",
                        "Vereinsseite, verein, öffentlich, aktualisiert am 20.09.2026",
                        "Eigenes, tester, privat, aktualisiert am 01.09.2026"]
    assert (projects_root / "Vereinsseite" / "Code" / "main" / "main.py").exists()


def test_upload_existing_project_is_offered_only_when_not_on_platform(live, qtbot, account,
                                                                     projects_root):
    services, acc, _ = account
    make_project(projects_root, "Lokal")
    win = live(services)
    project = services.projects.all()[0]
    from cockpit.core.actions import Target
    win.project_list.select(Target.CODE, project.id)
    entry = win.current_entries()[1]                           # oben: Projekt neu einlesen
    assert entry.label == "Auf GitHub hochladen …" and entry.action.is_default


def test_recheck_says_fixed_and_moves_to_next(qtbot, tmp_path):
    """Rückmeldung aus dem Test von 5b: Erneut prüfen sagt "Behoben" oder "Besteht weiter",
    der Fokus geht in die Liste."""
    code = tmp_path / "Code"
    write(code, "config.py", f'TOKEN = "{GITHUB_TOKEN}"\n{PASSWORD_LINE}\n')
    dialog = safety_dialog(qtbot, code)
    dialog.list.setCurrentRow(1)                               # Passwort
    dialog.recheck()
    assert said("Besteht weiter. Noch: 2 Funde stoppen das Hochladen")
    assert dialog.list.currentRow() == 1
    dialog.list.setCurrentRow(0)                               # Token entfernen
    write(code, "config.py", PASSWORD_LINE + "\n")
    dialog.recheck()
    assert said("Behoben. Noch: 1 Fund stoppt das Hochladen")
    assert dialog.current().rule == "Passwort oder Schlüssel im Code"
    write(code, "config.py", "x = 1\n")
    dialog.recheck()
    assert said("Behoben. Keine Funde mehr.")


def test_enter_activates_the_focused_button_not_in_the_list(qtbot, tmp_path):
    from PySide6.QtCore import Qt
    from tests.test_ui import show_active
    code = tmp_path / "Code"
    write(code, "config.py", f'TOKEN = "{GITHUB_TOKEN}"\n')
    dialog = safety_dialog(qtbot, code)
    show_active(qtbot, dialog)
    assert all(b.autoDefault() for b in (dialog.ignore_button, dialog.not_secret_button,
                                         dialog.recheck_button))
    dialog.list.setFocus()
    qtbot.keyClick(dialog.list, Qt.Key.Key_Return)             # nichts passiert
    assert len(dialog.report.findings) == 1 and dialog.isVisible()
    dialog.not_secret_button.setFocus()
    qtbot.keyClick(dialog.not_secret_button, Qt.Key.Key_Return)
    assert dialog.report.findings == []


@pytest.mark.parametrize("value", ["ghp" + "_" + "Erfunden0123456789abcdefghijklmnopqrstuv",
                                   "sk" + "-proj-" + "BeispielKey0123456789abcdef",
                                   "pass" + 'word = "NurFuerTests2026!"'])
def test_made_up_values_are_no_secrets(tmp_path, value):
    """Wunsch des Nutzers (28.09.2026): Erfundene Werte in Tests gelten nicht als Geheimnis."""
    write(tmp_path, "config.py", f'TOKEN = "{value}"\n')
    assert safety_check.scan(tmp_path).findings == []
    assert safety_check.is_made_up(value)
    assert not safety_check.is_made_up(GITHUB_TOKEN)


def test_allowlist_pragma(tmp_path):
    write(tmp_path, "kinds.py", "SECRET_KIND = " + '"secret_history"  # pragma: allowlist secret\n')
    assert safety_check.scan(tmp_path).findings == []
