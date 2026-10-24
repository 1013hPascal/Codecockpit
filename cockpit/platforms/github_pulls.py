"""Pull Requests auf GitHub: lesen, anlegen, kommentieren, Reviews, Checks, übernehmen.

Teil von GitHubPlatform (github.py).
"""
from __future__ import annotations

from cockpit.platforms.base import (
    Capability, Check, MERGE_METHODS, PlatformError, PullRequest, PullRequestComment,
    PullRequestFile, RepoRef, Review)
from cockpit.platforms.github_common import graphql_url
from cockpit.platforms.github_issues import _login


def _pull(data: dict) -> PullRequest:
    """Pull Request aus der Antwort von GitHub."""
    state = "merged" if data.get("merged_at") else data.get("state", "open")
    reviewers = tuple(r.get("login", "") for r in data.get("requested_reviewers") or [])
    return PullRequest(int(data.get("number", 0)), data.get("title", ""),
                       (data.get("head") or {}).get("ref", ""),
                       (data.get("base") or {}).get("ref", ""), _login(data), state,
                       bool(data.get("draft")), data.get("body") or "",
                       data.get("created_at", ""), data.get("html_url", ""), reviewers,
                       data.get("node_id", ""), data.get("mergeable"),
                       data.get("mergeable_state") or "",
                       (data.get("head") or {}).get("sha", ""),
                       ((data.get("head") or {}).get("repo") or {}).get("full_name", ""))


class GitHubPulls:
    """Pull Requests."""

    # -- Pull Requests ---------------------------------------------------------------------------
    def pull_requests(self, repo: RepoRef, state: str = "open") -> list[PullRequest]:
        path = f"/repos/{repo.owner}/{repo.name}/pulls"
        result: list[PullRequest] = []
        for page in range(1, 11):                        # höchstens 1000
            items = self.request("GET", path, "Pull Requests lesen", Capability.PULL_REQUESTS,
                                 params={"state": state, "sort": "created",
                                         "direction": "desc", "per_page": 100,
                                         "page": page}).json()
            result.extend(_pull(item) for item in items)
            if len(items) < 100:
                break
        return result

    def pull_request(self, repo: RepoRef, number: int) -> PullRequest:
        return _pull(self.request("GET", f"/repos/{repo.owner}/{repo.name}/pulls/{number}",
                                  "Pull Request lesen", Capability.PULL_REQUESTS).json())

    def create_pull_request(self, repo: RepoRef, head: str, base: str, title: str, body: str,
                            draft: bool = False, reviewers: tuple[str, ...] = ()) -> PullRequest:
        base_path = f"/repos/{repo.owner}/{repo.name}/pulls"
        created = _pull(self.request("POST", base_path, "Pull Request erstellen",
                                     Capability.PULL_REQUESTS,
                                     json={"title": title, "head": head, "base": base,
                                           "body": body, "draft": draft}).json())
        if reviewers:
            self.request("POST", f"{base_path}/{created.number}/requested_reviewers",
                         "Prüfer anfragen", Capability.PULL_REQUESTS,
                         json={"reviewers": list(reviewers)})
            created = PullRequest(**{**created.__dict__, "reviewers": tuple(reviewers)})
        return created

    def pull_request_comments(self, repo: RepoRef, number: int) -> list[PullRequestComment]:
        base = f"/repos/{repo.owner}/{repo.name}"
        general = self.request("GET", f"{base}/issues/{number}/comments", "Kommentare lesen",
                               Capability.PULL_REQUESTS, params={"per_page": 100}).json()
        on_lines = self.request("GET", f"{base}/pulls/{number}/comments", "Kommentare lesen",
                                Capability.PULL_REQUESTS, params={"per_page": 100}).json()
        found = [PullRequestComment(_login(c), c.get("created_at", ""), c.get("body") or "")
                 for c in general]
        found += [PullRequestComment(_login(c), c.get("created_at", ""), c.get("body") or "",
                                     c.get("path", ""),
                                     int(c.get("line") or c.get("original_line") or 0))
                  for c in on_lines]
        return sorted(found, key=lambda c: c.created)

    def add_pull_request_comment(self, repo: RepoRef, number: int, body: str) -> None:
        self.request("POST", f"/repos/{repo.owner}/{repo.name}/issues/{number}/comments",
                     "Kommentar schreiben", Capability.PULL_REQUESTS, json={"body": body})

    def pull_request_files(self, repo: RepoRef, number: int) -> list[PullRequestFile]:
        items = self.request("GET", f"/repos/{repo.owner}/{repo.name}/pulls/{number}/files",
                             "Dateien lesen", Capability.PULL_REQUESTS,
                             params={"per_page": 100}).json()
        return [PullRequestFile(f.get("filename", ""), f.get("status", "modified"),
                                int(f.get("additions") or 0), int(f.get("deletions") or 0),
                                f.get("patch") or "") for f in items]

    def set_pull_request_open(self, repo: RepoRef, number: int, open_: bool) -> None:
        self.request("PATCH", f"/repos/{repo.owner}/{repo.name}/pulls/{number}",
                     "Pull Request öffnen" if open_ else "Pull Request schließen",
                     Capability.PULL_REQUESTS, json={"state": "open" if open_ else "closed"})

    def mark_ready_for_review(self, repo: RepoRef, pull: PullRequest) -> None:
        """Geht nur über GraphQL, die REST-Schnittstelle kann das nicht."""
        node_id = pull.node_id or self.pull_request(repo, pull.number).node_id
        query = ("mutation($id: ID!) { markPullRequestReadyForReview(input: "
                 "{pullRequestId: $id}) { pullRequest { isDraft } } }")
        data = self.request("POST", graphql_url(self.url), "Zum Prüfen freigeben",
                            Capability.PULL_REQUESTS,
                            json={"query": query, "variables": {"id": node_id}}).json()
        if data.get("errors"):
            raise PlatformError("GitHub hat die Freigabe abgelehnt.",
                                str(data["errors"][0].get("message", "")))

    def reviews(self, repo: RepoRef, number: int) -> list[Review]:
        items = self.request("GET", f"/repos/{repo.owner}/{repo.name}/pulls/{number}/reviews",
                             "Reviews lesen", Capability.PULL_REQUESTS,
                             params={"per_page": 100}).json()
        return [Review(_login(r), r.get("state", ""), r.get("body") or "",
                       r.get("submitted_at") or "") for r in items]

    def submit_review(self, repo: RepoRef, number: int, event: str, body: str) -> None:
        self.request("POST", f"/repos/{repo.owner}/{repo.name}/pulls/{number}/reviews",
                     "Review abgeben", Capability.PULL_REQUESTS,
                     json={"event": event, "body": body})

    def merge_methods(self, repo: RepoRef) -> list[str]:
        data = self.request("GET", f"/repos/{repo.owner}/{repo.name}", "Repository lesen").json()
        allowed = {"merge": data.get("allow_merge_commit", True),
                   "squash": data.get("allow_squash_merge", True),
                   "rebase": data.get("allow_rebase_merge", True)}
        return [m for m in MERGE_METHODS if allowed[m]]

    def merge_pull_request(self, repo: RepoRef, number: int, method: str) -> None:
        self.request("PUT", f"/repos/{repo.owner}/{repo.name}/pulls/{number}/merge",
                     "Übernehmen", Capability.PULL_REQUESTS, json={"merge_method": method})

    def pull_request_checks(self, repo: RepoRef, pull: PullRequest) -> list[Check]:
        """Check-Läufe (zum Beispiel GitHub Actions) und ältere Statusmeldungen anderer Dienste.
        Beide gibt es bei GitHub nebeneinander."""
        sha = pull.head_sha or self.pull_request(repo, pull.number).head_sha
        if not sha:
            return []
        base = f"/repos/{repo.owner}/{repo.name}/commits/{sha}"
        runs = self.request("GET", f"{base}/check-runs", "Checks lesen",
                            params={"per_page": 100}).json()
        found = [Check(r.get("name", ""), r.get("status") or "", r.get("conclusion") or "",
                       r.get("html_url") or "", ((r.get("output") or {}).get("title") or ""))
                 for r in runs.get("check_runs", [])]
        statuses = self.request("GET", f"{base}/status", "Checks lesen").json()
        for status in statuses.get("statuses", []):
            state = status.get("state", "")
            found.append(Check(status.get("context", ""),
                               "queued" if state == "pending" else "completed",
                               "" if state == "pending" else state,
                               status.get("target_url") or "", status.get("description") or ""))
        return found
