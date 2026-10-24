"""Issues auf GitHub: lesen, anlegen, kommentieren, Labels und Zuständige.

Teil von GitHubPlatform (github.py).
"""
from __future__ import annotations

from cockpit.platforms.base import Capability, Issue, IssueComment, RepoRef


def _login(item: dict) -> str:
    return (item.get("user") or {}).get("login", "")


def _issue(data: dict) -> Issue:
    return Issue(int(data.get("number", 0)), data.get("title", ""), _login(data),
                 data.get("state", "open"), data.get("body") or "",
                 tuple(label.get("name", "") for label in data.get("labels") or []
                       if isinstance(label, dict)),
                 tuple(a.get("login", "") for a in data.get("assignees") or []),
                 data.get("created_at", ""), data.get("html_url", ""),
                 int(data.get("comments") or 0))


class GitHubIssues:
    """Issues."""

    # -- Issues (21.10.2026) ----------------------------------------------------------------------
    def issues(self, repo: RepoRef, state: str = "open") -> list[Issue]:
        path = f"/repos/{repo.owner}/{repo.name}/issues"
        result: list[Issue] = []
        for page in range(1, 11):                        # höchstens 1000
            items = self.request("GET", path, "Issues lesen", Capability.ISSUES,
                                 params={"state": state, "sort": "created", "direction": "desc",
                                         "per_page": 100, "page": page}).json()
            # GitHub liefert Pull Requests hier mit, sie haben den Schlüssel pull_request
            result.extend(_issue(item) for item in items if "pull_request" not in item)
            if len(items) < 100:
                break
        return result

    def issue(self, repo: RepoRef, number: int) -> Issue:
        return _issue(self.request("GET", f"/repos/{repo.owner}/{repo.name}/issues/{number}",
                                   "Issue lesen", Capability.ISSUES).json())

    def create_issue(self, repo: RepoRef, title: str, body: str,
                     labels: tuple[str, ...] = (), assignees: tuple[str, ...] = ()) -> Issue:
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = list(labels)
        if assignees:
            data["assignees"] = list(assignees)
        return _issue(self.request("POST", f"/repos/{repo.owner}/{repo.name}/issues",
                                   "Issue anlegen", Capability.ISSUES, json=data).json())

    def issue_comments(self, repo: RepoRef, number: int) -> list[IssueComment]:
        items = self.request("GET", f"/repos/{repo.owner}/{repo.name}/issues/{number}/comments",
                             "Kommentare lesen", Capability.ISSUES,
                             params={"per_page": 100}).json()
        return [IssueComment(_login(c), c.get("created_at", ""), c.get("body") or "")
                for c in items]

    def add_issue_comment(self, repo: RepoRef, number: int, body: str) -> None:
        self.request("POST", f"/repos/{repo.owner}/{repo.name}/issues/{number}/comments",
                     "Kommentar schreiben", Capability.ISSUES, json={"body": body})

    def set_issue_open(self, repo: RepoRef, number: int, open_: bool) -> None:
        self.request("PATCH", f"/repos/{repo.owner}/{repo.name}/issues/{number}",
                     "Issue öffnen" if open_ else "Issue schließen", Capability.ISSUES,
                     json={"state": "open" if open_ else "closed"})

    def issue_labels(self, repo: RepoRef) -> list[str]:
        items = self.request("GET", f"/repos/{repo.owner}/{repo.name}/labels", "Labels lesen",
                             Capability.ISSUES, params={"per_page": 100}).json()
        return sorted((i.get("name", "") for i in items), key=str.lower)

    def set_issue_labels(self, repo: RepoRef, number: int, labels: tuple[str, ...]) -> None:
        self.request("PUT", f"/repos/{repo.owner}/{repo.name}/issues/{number}/labels",
                     "Labels setzen", Capability.ISSUES, json={"labels": list(labels)})

    def assignable(self, repo: RepoRef) -> list[str]:
        items = self.request("GET", f"/repos/{repo.owner}/{repo.name}/assignees",
                             "Personen lesen", Capability.ISSUES, params={"per_page": 100}).json()
        return sorted((i.get("login", "") for i in items), key=str.lower)

    def set_issue_assignees(self, repo: RepoRef, number: int,
                            assignees: tuple[str, ...]) -> None:
        self.request("PATCH", f"/repos/{repo.owner}/{repo.name}/issues/{number}",
                     "Zuweisen", Capability.ISSUES, json={"assignees": list(assignees)})
