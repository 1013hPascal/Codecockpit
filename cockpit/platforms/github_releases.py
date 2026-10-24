"""Releases und GitHub Actions: anlegen, Dateien hoch- und herunterladen, Läufe und Protokolle.

Teil von GitHubPlatform (github.py).
"""
from __future__ import annotations

import httpx

from cockpit.core.errors import Cancelled
from cockpit.platforms.base import (
    Capability, NetworkError, PlatformError, Release, ReleaseAsset, RepoRef, WorkflowJob,
    WorkflowRun)
from cockpit.platforms.github_common import NO_CONNECTION


def _release(data: dict) -> Release:
    assets = tuple(ReleaseAsset(int(a["id"]), a.get("name", ""), int(a.get("size", 0)),
                                int(a.get("download_count", 0)))
                   for a in data.get("assets", []))
    return Release(int(data["id"]), data.get("tag_name", ""), data.get("name") or "",
                   data.get("html_url", ""), data.get("published_at") or "", assets,
                   (data.get("upload_url") or "").split("{")[0], data.get("body") or "")


def _run(data: dict) -> WorkflowRun:
    title = data.get("display_title") or ""
    if not title:
        message = (data.get("head_commit") or {}).get("message") or ""
        title = message.splitlines()[0] if message else ""
    return WorkflowRun(int(data["id"]), data.get("name") or "", data.get("status") or "",
                       data.get("conclusion") or "", data.get("head_branch") or "",
                       data.get("created_at") or "", title, data.get("html_url") or "")


class GitHubReleases:
    """Releases und Actions."""

    # -- Releases (Phase 10) ---------------------------------------------------------------------
    def releases(self, repo: RepoRef) -> list[Release]:
        data = self.request("GET", f"/repos/{repo.owner}/{repo.name}/releases",
                            "Releases lesen", params={"per_page": 30}).json()
        return [_release(item) for item in data if not item.get("draft")]

    def create_release(self, repo: RepoRef, tag: str, name: str, body: str,
                       target: str) -> Release:
        data = self.request("POST", f"/repos/{repo.owner}/{repo.name}/releases",
                            "Release anlegen", Capability.RELEASES,
                            json={"tag_name": tag, "target_commitish": target, "name": name,
                                  "body": body}).json()
        return _release(data)

    def upload_asset(self, repo: RepoRef, release: Release, path) -> ReleaseAsset:
        url = release.upload_url
        if not url:
            raise PlatformError("GitHub hat keine Adresse zum Hochladen genannt.",
                                f"Release {release.tag}")
        with open(path, "rb") as file:
            data = self.request("POST", url, "Datei hochladen", Capability.RELEASES,
                                params={"name": path.name}, content=file,
                                headers_extra={"Content-Type": "application/octet-stream"},
                                timeout=httpx.Timeout(3600, connect=15)).json()
        return ReleaseAsset(int(data["id"]), data["name"], int(data.get("size", 0)))

    def update_release_notes(self, repo: RepoRef, release: Release, body: str) -> Release:
        data = self.request("PATCH", f"/repos/{repo.owner}/{repo.name}/releases/{release.id}",
                            "Versionshinweise ändern", Capability.RELEASES,
                            json={"body": body}).json()
        return _release(data)

    def delete_release(self, repo: RepoRef, release: Release) -> None:
        self.request("DELETE", f"/repos/{repo.owner}/{repo.name}/releases/{release.id}",
                     "Release löschen", Capability.RELEASES)

    # -- GitHub Actions (Phase 14) -----------------------------------------------------------
    def has_workflows(self, repo: RepoRef) -> bool:
        data = self.request("GET", f"/repos/{repo.owner}/{repo.name}/actions/workflows",
                            "Workflows lesen", params={"per_page": 1}).json()
        return int(data.get("total_count", 0)) > 0

    def workflow_runs(self, repo: RepoRef, limit: int = 20) -> list[WorkflowRun]:
        data = self.request("GET", f"/repos/{repo.owner}/{repo.name}/actions/runs",
                            "Läufe lesen", params={"per_page": limit}).json()
        return [_run(item) for item in data.get("workflow_runs", [])]

    def run_jobs(self, repo: RepoRef, run_id: int) -> list[WorkflowJob]:
        data = self.request("GET", f"/repos/{repo.owner}/{repo.name}/actions/runs/{run_id}/jobs",
                            "Aufgaben lesen", params={"per_page": 50}).json()
        jobs = []
        for job in data.get("jobs", []):
            failed = tuple(s.get("name", "") for s in job.get("steps") or []
                           if s.get("conclusion") == "failure")
            jobs.append(WorkflowJob(int(job["id"]), job.get("name", ""),
                                    job.get("conclusion") or "", failed))
        return jobs

    def job_log(self, repo: RepoRef, job_id: int) -> str:
        """GitHub leitet zur Datei weiter. httpx lässt den Token dabei weg (anderer Rechner)."""
        response = self.request("GET", f"/repos/{repo.owner}/{repo.name}/actions/jobs/{job_id}/logs",
                                "Ausgabe lesen", follow_redirects=True)
        return response.text

    def rerun(self, repo: RepoRef, run: WorkflowRun) -> None:
        which = "rerun-failed-jobs" if run.failed else "rerun"
        self.request("POST", f"/repos/{repo.owner}/{repo.name}/actions/runs/{run.id}/{which}",
                     "Neu starten")

    def download_asset(self, repo: RepoRef, asset: ReleaseAsset, target, cancel=None) -> None:
        """Mit Accept: application/octet-stream leitet GitHub zur Datei weiter. Der Token geht
        dabei nicht mit, weil httpx ihn bei einem anderen Rechner weglässt."""
        path = f"/repos/{repo.owner}/{repo.name}/releases/assets/{asset.id}"
        headers = {"Authorization": f"Bearer {self.token.reveal()}",
                   "Accept": "application/octet-stream"}
        try:
            with self.client().stream("GET", path, headers=headers,
                                      timeout=httpx.Timeout(3600, connect=15)) as response:
                if response.status_code >= 400:
                    response.read()
                    raise self._error(response, "GET", path, "Datei herunterladen", None)
                with open(target, "wb") as file:
                    for chunk in response.iter_bytes(1024 * 256):
                        if cancel is not None and cancel.is_set():
                            raise Cancelled()
                        file.write(chunk)
        except httpx.HTTPError as exc:
            raise NetworkError(NO_CONNECTION, repr(exc)) from None
