"""Issues lesen, anlegen, kommentieren, schließen, mit Labels und Zuweisen, mit und ohne KI
(Wunsch des Nutzers vom 21.10.2026). GitHub ist nachgebaut, die KI ist erfunden."""
from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest

from cockpit.core import issues
from cockpit.core.secret import Secret
from cockpit.platforms.base import Issue, IssueComment, RepoRef
from cockpit.platforms.github import GitHubPlatform

TOKEN = "gho_ErfundenerTestTokenFuerIssues1234567"
REF = RepoRef("anna", "suche")
ISSUE = Issue(12, "Suche in PDFs geht nicht", "anna", body="Beim Suchen in PDFs kommt nichts.",
              labels=("Fehler",), assignees=("ben",), comments=2)


@pytest.fixture
def hub(monkeypatch):
    sent: list[httpx.Request] = []
    answers = {
        ("GET", "/repos/anna/suche/issues"): [
            {"number": 12, "title": "Suche", "user": {"login": "anna"}, "state": "open",
             "labels": [{"name": "Fehler"}], "assignees": [{"login": "ben"}], "comments": 2},
            {"number": 13, "title": "Ein PR", "user": {"login": "ben"}, "pull_request": {}}],
        ("POST", "/repos/anna/suche/issues"): {"number": 14, "title": "Neu",
                                                "user": {"login": "ich"}},
        ("PUT", "/repos/anna/suche/issues/12/labels"): [],
        ("PATCH", "/repos/anna/suche/issues/12"): {},
        ("GET", "/repos/anna/suche/labels"): [{"name": "wunsch"}, {"name": "Fehler"}],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        body = answers.get((request.method, request.url.path))
        if body is None:
            return httpx.Response(404, json={"message": "Not Found"})
        return httpx.Response(200, json=body)

    monkeypatch.setattr(GitHubPlatform, "transport", httpx.MockTransport(handler))
    return GitHubPlatform("https://github.com", Secret(TOKEN)), sent


def test_github_issues_without_pull_requests(hub):
    platform, _sent = hub
    found = platform.issues(REF)
    assert [i.number for i in found] == [12]
    assert found[0].labels == ("Fehler",) and found[0].assignees == ("ben",)
    assert platform.issue_labels(REF) == ["Fehler", "wunsch"]


def test_github_create_label_assign_close(hub):
    platform, sent = hub
    created = platform.create_issue(REF, "Neu", "Text", ("wunsch",), ("ben",))
    assert created.number == 14
    assert json.loads(sent[-1].content) == {"title": "Neu", "body": "Text",
                                            "labels": ["wunsch"], "assignees": ["ben"]}
    platform.set_issue_labels(REF, 12, ("Fehler", "wunsch"))
    assert json.loads(sent[-1].content) == {"labels": ["Fehler", "wunsch"]}
    platform.set_issue_assignees(REF, 12, ())
    assert json.loads(sent[-1].content) == {"assignees": []}
    platform.set_issue_open(REF, 12, False)
    assert json.loads(sent[-1].content) == {"state": "closed"}


def test_lines_and_details():
    assert issues.issue_line(ISSUE) == ("Nr. 12: Suche in PDFs geht nicht, von anna, Fehler, "
                                        "zugewiesen an ben, 2 Kommentare")
    details = issues.issue_details(ISSUE)
    assert details[:2] == ["Nr. 12: Suche in PDFs geht nicht", "Offen"]
    assert "Labels: Fehler" in details and details[-1] == "Beim Suchen in PDFs kommt nichts."


def test_branch_names_without_ai():
    assert issues.branch_name(ISSUE) == "12-suche-in-pdfs-geht-nicht"
    assert issues.clean_branch_name("Suche Reparieren", 12) == "12-suche-reparieren"
    assert issues.clean_branch_name("`12-suche--pdf`", 12) == "12-suche-pdf"


def test_ai_summary_and_branch_without_secrets():
    from cockpit.features.ai_assistant import suggest
    asked = []

    def ask(request, system, cancel, max_tokens):
        asked.append(request)
        return "Branch: Suche PDF\n\nPDFs werden nicht durchsucht. Ben baut einen Leser ein."
    ai = SimpleNamespace(max_chars=8000, ask=ask)
    comments = [IssueComment("ben", "", "Mein Schlüssel ist ghp_" + "A" * 36)]
    found = suggest.issue(ai, ISSUE, comments, "Deutsch")
    assert found.summary == "12-suche-pdf"
    assert found.details.startswith("PDFs werden nicht durchsucht.")
    assert "ghp_" + "A" * 36 not in asked[0] and "Suche in PDFs geht nicht" in asked[0]


# -- Fenster ---------------------------------------------------------------------------------------
class FakePlatform:
    def __init__(self):
        self.calls = []
        self.items = [ISSUE, Issue(11, "Alt", "ben", state="open")]

    def issues(self, ref, state):
        return list(self.items)

    def issue(self, ref, number):
        return ISSUE

    def issue_comments(self, ref, number):
        return [IssueComment("ben", "2026-10-20T10:00:00Z", "Ich schaue es mir an.")]

    def set_issue_labels(self, ref, number, labels):
        self.calls.append(("labels", number, labels))

    def create_issue(self, ref, title, body, labels, people):
        self.calls.append(("create", title, body, labels, people))
        return Issue(15, title, "ich")


def test_issues_dialog_without_ai(qtbot, monkeypatch):
    from cockpit.ui import branch_dialogs, issue_dialogs
    made = []
    dialog = issue_dialogs.IssuesDialog(FakePlatform(), REF, FakePlatform().items,
                                        ["Fehler", "wunsch"], ["ben"], None, None, made.append)
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.windowTitle() == "Issues von suche: 2 Issues, offene"
    assert dialog.list.accessibleName() == "Issues"
    assert dialog.branch_button.isVisible() and dialog.state_button.text() == "Issue s&chließen …"

    def exec_name(self):
        self.name = self.edit.text()
        return 1
    monkeypatch.setattr(branch_dialogs.BranchNameDialog, "exec", exec_name)
    dialog.branch_for_current()
    assert made == ["12-suche-in-pdfs-geht-nicht"]
    dialog.suggested[12] = "12-pdf-leser"                 # von der KI
    dialog.branch_for_current()
    assert made[-1] == "12-pdf-leser"


def test_labels_are_set_in_background(qtbot, monkeypatch):
    from cockpit.ui import issue_dialogs, sync_dialogs
    platform = FakePlatform()
    dialog = issue_dialogs.IssuesDialog(platform, REF, platform.items, ["Fehler", "wunsch"], [])
    qtbot.addWidget(dialog)

    def exec_all(self):
        self.chosen = list(self.items)
        return 1
    monkeypatch.setattr(sync_dialogs.CheckListDialog, "exec", exec_all)
    dialog.edit_labels()
    qtbot.waitUntil(lambda: platform.calls == [("labels", 12, ("Fehler", "wunsch"))],
                    timeout=5000)
    qtbot.waitUntil(lambda: not dialog.worker.busy, timeout=5000)


def test_create_issue_dialog(qtbot, monkeypatch):
    from cockpit.ui import issue_dialogs
    errors = []
    monkeypatch.setattr(issue_dialogs, "show_error", lambda *a, **k: errors.append(a[2]))
    dialog = issue_dialogs.CreateIssueDialog(["Fehler"], [])
    qtbot.addWidget(dialog)
    assert dialog.labels_button.isVisibleTo(dialog) and not dialog.people_button.isVisibleTo(dialog)
    dialog.check()
    assert errors == [issue_dialogs.NO_TITLE]
    dialog.title_edit.setText("  Neue   Suche ")
    dialog.body_edit.setPlainText("Text")
    dialog.check()
    assert (dialog.title, dialog.body, dialog.result()) == ("Neue Suche", "Text", 1)


def test_details_show_comments_and_ai_summary(qtbot):
    from cockpit.ui import issue_dialogs
    dialog = issue_dialogs.IssueDetailsDialog(FakePlatform(), REF, ISSUE)
    qtbot.addWidget(dialog)
    assert dialog.ai_button is None                       # ohne KI-Assistent kein Knopf
    qtbot.waitUntil(lambda: dialog.comments.item(0).text().startswith("ben, 20.10.2026"),
                    timeout=5000)
    dialog.apply_summary(SimpleNamespace(summary="12-pdf-leser", details="PDFs fehlen."))
    assert dialog.info.item(1).text() == "Zusammenfassung der KI: PDFs fehlen."
    assert dialog.info.item(2).text() == "Vorgeschlagener Branch: 12-pdf-leser"
    assert dialog.branch_suggestion == "12-pdf-leser"
