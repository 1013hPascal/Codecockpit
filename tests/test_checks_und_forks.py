"""Checks bei Pull Requests und Forks (Wunsch des Nutzers vom 21.10.2026, nach dem Vergleich mit
GitHub Desktop). GitHub ist nachgebaut (httpx.MockTransport), kein echtes Netz."""
from __future__ import annotations

import httpx
import pytest

from cockpit.core import forks, git, pull_requests
from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret
from cockpit.platforms.base import Check, PullRequest, RepoRef
from cockpit.platforms.github import GitHubPlatform

TOKEN = "gho_ErfundenerTestTokenFuerChecks123456"
needs_git = pytest.mark.skipif(git.find_git() is None, reason="Git ist nicht installiert")


@pytest.fixture
def routes(monkeypatch):
    table: dict[tuple[str, str], list] = {}
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        answers = table.get((request.method, request.url.path))
        if not answers:
            return httpx.Response(404, json={"message": "Not Found"})
        status, body = answers[0] if len(answers) == 1 else answers.pop(0)
        return httpx.Response(status, json=body)

    monkeypatch.setattr(GitHubPlatform, "transport", httpx.MockTransport(handler))
    monkeypatch.setattr(GitHubPlatform, "sleep", staticmethod(lambda seconds: None))
    table["seen"] = seen
    return table


def platform() -> GitHubPlatform:
    return GitHubPlatform("https://github.com", Secret(TOKEN))


# -- Checks --------------------------------------------------------------------------------------
def test_checks_from_check_runs_and_statuses(routes):
    base = "/repos/anna/suche/commits/abc123"
    routes[("GET", f"{base}/check-runs")] = [(200, {"check_runs": [
        {"name": "Tests", "status": "completed", "conclusion": "failure",
         "html_url": "https://x", "output": {"title": "2 Fehler"}},
        {"name": "Lint", "status": "completed", "conclusion": "success"},
        {"name": "Bau", "status": "in_progress", "conclusion": None}]})]
    routes[("GET", f"{base}/status")] = [(200, {"statuses": [
        {"context": "ci/extern", "state": "pending", "description": "wartet"}]})]
    pull = PullRequest(7, "Suche", "suche", "main", "anna", head_sha="abc123")
    checks = platform().pull_request_checks(RepoRef("anna", "suche"), pull)
    assert [c.name for c in checks] == ["Tests", "Lint", "Bau", "ci/extern"]
    assert pull_requests.checks_text(checks) == ("Checks: 1 fehlgeschlagen (Tests), 2 laufen "
                                                 "noch, 1 erfolgreich")
    assert pull_requests.check_lines(checks)[0] == "Tests: fehlgeschlagen, 2 Fehler"
    assert pull_requests.check_lines(checks)[-1] == "Lint: erfolgreich"


def test_checks_text_without_checks():
    assert pull_requests.checks_text([]) == ""
    assert pull_requests.check_lines([]) == ["Für diesen Pull Request gibt es keine Checks."]
    assert pull_requests.checks_text([Check("A", "completed", "success")]) == \
        "Checks: 1 erfolgreich"


def test_pull_knows_head_sha_and_fork(routes):
    routes[("GET", "/repos/anna/suche/pulls/7")] = [(200, {
        "number": 7, "title": "Suche", "user": {"login": "ben"}, "state": "open",
        "head": {"ref": "suche", "sha": "abc123", "repo": {"full_name": "ben/suche"}},
        "base": {"ref": "main"}})]
    pull = platform().pull_request(RepoRef("anna", "suche"), 7)
    assert pull.head_sha == "abc123" and pull.head_repo == "ben/suche"


def test_merge_dialog_shows_checks_first(qtbot):
    from PySide6.QtWidgets import QListWidget
    from cockpit.ui.pull_request_dialogs import MergeDialog
    pull = PullRequest(7, "Suche", "suche", "main", "anna")
    dialog = MergeDialog(pull, ["merge"], "1 Genehmigung", None, "Checks: 1 fehlgeschlagen (Tests)")
    qtbot.addWidget(dialog)
    info = dialog.findChild(QListWidget)
    assert info.item(1).text() == "Checks: 1 fehlgeschlagen (Tests)"


# -- Forks auf der Plattform ---------------------------------------------------------------------
def test_can_push_and_fork_waits_until_ready(routes):
    routes[("GET", "/repos/anna/suche")] = [(200, {"permissions": {"push": False}})]
    routes[("POST", "/repos/anna/suche/forks")] = [(202, {
        "owner": {"login": "ich"}, "name": "suche", "private": False,
        "clone_url": "https://github.com/ich/suche.git",
        "html_url": "https://github.com/ich/suche"})]
    routes[("GET", "/repos/ich/suche/branches")] = [(404, {"message": "Not Found"}),
                                                    (404, {"message": "Not Found"}),
                                                    (200, [])]
    hub = platform()
    assert hub.can_push(RepoRef("anna", "suche")) is False
    fork = hub.fork(RepoRef("anna", "suche"))
    assert fork.ref == RepoRef("ich", "suche")
    assert fork.clone_url == "https://github.com/ich/suche.git"
    waited = [r for r in routes["seen"] if r.url.path.endswith("/branches")]
    assert len(waited) == 3


# -- Forks in Git ----------------------------------------------------------------------------------
def run(cwd, *args):
    return git.run(list(args), cwd).stdout.strip()


def fork_setup(tmp_path):
    """Original und Fork als Bare-Repositories, code ist der heruntergeladene Fork."""
    seed = tmp_path / "seed"
    seed.mkdir()
    run(seed, "init", "-q", "-b", "main")
    run(seed, "config", "user.name", "Anna")
    run(seed, "config", "user.email", "anna@example.com")
    (seed / "a.txt").write_bytes(b"a\n")
    run(seed, "add", "-A")
    run(seed, "commit", "-q", "-m", "Start")
    original = tmp_path / "original.git"
    run(tmp_path, "clone", "-q", "--bare", str(seed), str(original))
    fork = tmp_path / "fork.git"
    run(tmp_path, "clone", "-q", "--bare", str(original), str(fork))
    code = tmp_path / "code"
    run(tmp_path, "clone", "-q", str(fork), str(code))
    run(code, "config", "user.name", "Ich")
    run(code, "config", "user.email", "ich@example.com")
    run(seed, "remote", "add", "origin", str(original))
    return seed, original, code


@needs_git
def test_upstream_fetch_and_update_main(tmp_path):
    seed, original, code = fork_setup(tmp_path)
    assert forks.upstream(code) is None and not forks.has_upstream(code)
    forks.add_upstream(code, original.as_uri())
    assert forks.has_upstream(code)
    (seed / "b.txt").write_bytes(b"b\n")
    run(seed, "add", "-A")
    run(seed, "commit", "-q", "-m", "B im Original")
    run(seed, "push", "-q", "origin", "main")
    forks.fetch(code)
    assert forks.main_branch(code) == "main"
    assert forks.behind(code) == (1, 0)
    assert forks.update_main(code) == 1
    assert (code / "b.txt").is_file() and forks.behind(code) == (0, 0)
    assert git.status(code).ahead == 1                    # noch nicht im Fork hochgeladen
    assert forks.branches(code) == ["main"]


@needs_git
def test_update_main_never_loses_own_commits(tmp_path):
    seed, original, code = fork_setup(tmp_path)
    forks.add_upstream(code, original.as_uri())
    (code / "eigen.txt").write_bytes(b"x\n")
    run(code, "add", "-A")
    run(code, "commit", "-q", "-m", "Eigenes")
    (seed / "b.txt").write_bytes(b"b\n")
    run(seed, "add", "-A")
    run(seed, "commit", "-q", "-m", "B im Original")
    run(seed, "push", "-q", "origin", "main")
    forks.fetch(code)
    before = run(code, "rev-parse", "HEAD")
    with pytest.raises(CockpitError, match="eigene Commits"):
        forks.update_main(code)
    assert run(code, "rev-parse", "HEAD") == before


@needs_git
def test_update_main_only_on_main(tmp_path):
    _seed, original, code = fork_setup(tmp_path)
    forks.add_upstream(code, original.as_uri())
    forks.fetch(code)
    run(code, "checkout", "-q", "-b", "arbeit")
    with pytest.raises(CockpitError, match="Haupt-Branch"):
        forks.update_main(code)


# -- Pull Request an das Original ------------------------------------------------------------------
@needs_git
def test_pull_request_goes_to_original(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from cockpit.ui import pull_request_flow
    _seed, original, code = fork_setup(tmp_path)
    forks.add_upstream(code, "https://github.com/anna/suche.git")
    made = []

    class Platform:
        def create_pull_request(self, ref, head, base, title, body, draft, reviewers):
            made.append((ref, head, base))
            return PullRequest(3, title, head, base, "ich")

    runner = pull_request_flow.PullRequestRunner.__new__(pull_request_flow.PullRequestRunner)
    runner.project = SimpleNamespace(code_dir=code, id=1, name="suche", remote=None)
    runner.services = None
    runner.window = SimpleNamespace(refresh_status=lambda ids: None)
    runner.controller = SimpleNamespace(
        run_task=lambda key, work, done, title: done(work(None)))
    monkeypatch.setattr(pull_request_flow.repo_admin, "repo_ref",
                        lambda project: RepoRef("ich", "suche"))
    dialog = SimpleNamespace(head="arbeit", base="main", title="Suche", body="", draft=False,
                             reviewers=())
    runner._create(Platform(), dialog, None, forks.upstream(code))
    assert made == [(RepoRef("anna", "suche"), "ich:arbeit", "main")]
