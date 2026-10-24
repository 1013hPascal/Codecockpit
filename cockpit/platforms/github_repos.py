"""Repositories auf GitHub: anlegen, ändern, löschen, Mitarbeiter, Schutz der Branches, Forks.

Teil von GitHubPlatform (github.py).
"""
from __future__ import annotations

from cockpit.platforms.base import (
    BranchProtection, Capability, Collaborator, NewRepo, NotFound, RemoteRepo, RepoInfo,
    RepoLinks, RepoRef)
from cockpit.platforms.github_common import INVITE_PERMISSIONS, web_base


def _role(person: dict) -> str:
    """Recht eines Mitarbeiters: role_name, sonst das höchste aus permissions."""
    role = str(person.get("role_name") or "")
    if role:
        return _permission(role)
    permissions = person.get("permissions") or {}
    for name in ("admin", "maintain", "push", "triage", "pull"):
        if permissions.get(name):
            return _permission(name)
    return "read"


def _permission(value: str) -> str:
    """Werte der API ("pull", "push", "write" ...) auf read, triage, write, maintain, admin."""
    return {"pull": "read", "push": "write"}.get(value, value or "read")


class GitHubRepos:
    """Repositories und Mitarbeiter."""

    # -- Repositories ------------------------------------------------------------------------
    def repositories(self, owner: str = "") -> list[RemoteRepo]:
        if owner:
            path, params = f"/orgs/{owner}/repos", {"sort": "pushed", "type": "all"}
        else:
            path, params = "/user/repos", {"sort": "pushed", "affiliation": "owner"}
        result: list[RemoteRepo] = []
        for page in range(1, 51):                        # höchstens 5000 Repositories
            items = self.request("GET", path, "Repositories lesen", params={
                **params, "per_page": 100, "page": page}).json()
            for data in items:
                result.append(RemoteRepo(
                    RepoRef(data["owner"]["login"], data["name"]), bool(data.get("private")),
                    data.get("clone_url", ""), data.get("html_url", ""),
                    data.get("pushed_at") or "", bool(data.get("archived"))))
            if len(items) < 100:
                break
        return sorted(result, key=lambda r: r.pushed_at, reverse=True)

    def create_repo(self, spec: NewRepo) -> RepoRef:
        path = f"/orgs/{spec.organization}/repos" if spec.organization else "/user/repos"
        data = self.request("POST", path, "Repository anlegen", Capability.CREATE_REPO,
                            json={"name": spec.name, "description": spec.description,
                                  "private": spec.private, "auto_init": False}).json()
        return RepoRef(data["owner"]["login"], data["name"])

    def repo_info(self, repo: RepoRef) -> RepoInfo:
        data = self.request("GET", f"/repos/{repo.owner}/{repo.name}", "Repository lesen").json()
        return RepoInfo(RepoRef(data["owner"]["login"], data["name"]), bool(data["private"]),
                        bool(data.get("archived")), data.get("default_branch", "main"),
                        data.get("html_url", ""))

    def set_visibility(self, repo: RepoRef, private: bool) -> None:
        self.request("PATCH", f"/repos/{repo.owner}/{repo.name}", "Sichtbarkeit ändern",
                     Capability.CHANGE_VISIBILITY, json={"private": private})

    def archive(self, repo: RepoRef) -> None:
        self.request("PATCH", f"/repos/{repo.owner}/{repo.name}", "Archivieren",
                     Capability.ARCHIVE, json={"archived": True})

    def delete(self, repo: RepoRef) -> None:
        self.request("DELETE", f"/repos/{repo.owner}/{repo.name}", "Löschen",
                     Capability.DELETE_REPO)

    def rename_repo(self, repo: RepoRef, name: str) -> RepoRef:
        data = self.request("PATCH", f"/repos/{repo.owner}/{repo.name}", "Umbenennen",
                            json={"name": name}).json()
        return RepoRef(data["owner"]["login"], data["name"])

    def rename_branch(self, repo: RepoRef, old: str, new: str) -> None:
        from urllib.parse import quote
        self.request("POST", f"/repos/{repo.owner}/{repo.name}/branches/{quote(old, safe='')}"
                     "/rename", "Branch umbenennen", json={"new_name": new})

    def unarchive(self, repo: RepoRef) -> None:
        self.request("PATCH", f"/repos/{repo.owner}/{repo.name}", "Archivierung aufheben",
                     Capability.ARCHIVE, json={"archived": False})

    def settings_url(self, repo: RepoRef) -> str:
        return f"{web_base(self.url)}/{repo.owner}/{repo.name}/settings"

    # -- Mitarbeiter ---------------------------------------------------------------------------
    def collaborators(self, repo: RepoRef) -> list[Collaborator]:
        base = f"/repos/{repo.owner}/{repo.name}"
        people = self.request("GET", f"{base}/collaborators", "Mitarbeiter lesen",
                              Capability.COLLABORATORS,
                              params={"affiliation": "direct", "per_page": 100}).json()
        result = [Collaborator(p.get("login", ""), _role(p)) for p in people]
        invitations = self.request("GET", f"{base}/invitations", "Einladungen lesen",
                                   Capability.COLLABORATORS, params={"per_page": 100}).json()
        result += [Collaborator((i.get("invitee") or {}).get("login", ""),
                                _permission(i.get("permissions", "")), int(i.get("id", 0)))
                   for i in invitations]
        return sorted(result, key=lambda c: c.login.lower())

    def invite(self, repo: RepoRef, login: str, permission: str) -> bool:
        try:
            response = self.request(
                "PUT", f"/repos/{repo.owner}/{repo.name}/collaborators/{login}",
                "Mitarbeiter einladen", Capability.COLLABORATORS,
                json={"permission": INVITE_PERMISSIONS.get(permission, "push")})
        except NotFound as exc:
            raise NotFound(f"Den Benutzer {login} gibt es auf GitHub nicht, oder das "
                           "Repository ist nicht erreichbar.", exc.details) from None
        return response.status_code == 201

    def change_permission(self, repo: RepoRef, person: Collaborator, permission: str) -> None:
        value = INVITE_PERMISSIONS.get(permission, "push")
        base = f"/repos/{repo.owner}/{repo.name}"
        if person.invited:
            # Bei Einladungen heißen die Werte read, write, admin ...
            self.request("PATCH", f"{base}/invitations/{person.invitation_id}",
                         "Recht ändern", Capability.COLLABORATORS,
                         json={"permissions": permission})
            return
        self.request("PUT", f"{base}/collaborators/{person.login}", "Recht ändern",
                     Capability.COLLABORATORS, json={"permission": value})

    def remove_collaborator(self, repo: RepoRef, login: str) -> None:
        self.request("DELETE", f"/repos/{repo.owner}/{repo.name}/collaborators/{login}",
                     "Mitarbeiter entfernen", Capability.COLLABORATORS)

    def cancel_invitation(self, repo: RepoRef, invitation_id: int) -> None:
        self.request("DELETE", f"/repos/{repo.owner}/{repo.name}/invitations/{invitation_id}",
                     "Einladung zurückziehen", Capability.COLLABORATORS)

    # -- Forks (21.10.2026) -----------------------------------------------------------------------
    def can_push(self, repo: RepoRef) -> bool:
        data = self.request("GET", f"/repos/{repo.owner}/{repo.name}", "Repository lesen").json()
        return bool((data.get("permissions") or {}).get("push"))

    def fork(self, repo: RepoRef, cancel=None) -> RemoteRepo:
        """GitHub legt den Fork im Hintergrund an. Gibt es ihn schon, kommt der vorhandene
        zurück. Danach wird gewartet, bis er sich lesen lässt (höchstens etwa eine Minute)."""
        data = self.request("POST", f"/repos/{repo.owner}/{repo.name}/forks", "Fork anlegen",
                            Capability.FORKS, json={"default_branch_only": False}).json()
        ref = RepoRef(data["owner"]["login"], data["name"])
        for _ in range(30):
            try:
                self.request("GET", f"/repos/{ref.owner}/{ref.name}/branches",
                             "Fork lesen", params={"per_page": 1})
                break
            except NotFound:
                self._wait(2, cancel)
        return RemoteRepo(ref, bool(data.get("private")), data.get("clone_url", ""),
                          data.get("html_url", ""), data.get("pushed_at") or "")

    # -- Schutzregeln -----------------------------------------------------------------------------
    def branch_protection(self, repo: RepoRef, branch: str) -> BranchProtection | None:
        try:
            data = self.request("GET", f"/repos/{repo.owner}/{repo.name}/branches/{branch}/"
                                "protection", "Schutzregeln lesen",
                                Capability.BRANCH_PROTECTION).json()
        except NotFound:
            return None                                  # "Branch not protected"
        reviews = data.get("required_pull_request_reviews")
        return BranchProtection(
            reviews is not None,
            int((reviews or {}).get("required_approving_review_count") or 0),
            bool((reviews or {}).get("dismiss_stale_reviews")),
            bool((data.get("enforce_admins") or {}).get("enabled")),
            not bool((data.get("allow_deletions") or {}).get("enabled")))

    def set_branch_protection(self, repo: RepoRef, branch: str,
                              rules: BranchProtection | None) -> None:
        path = f"/repos/{repo.owner}/{repo.name}/branches/{branch}/protection"
        if rules is None or rules.empty:
            try:
                self.request("DELETE", path, "Schutzregeln entfernen",
                             Capability.BRANCH_PROTECTION)
            except NotFound:
                pass                                     # war schon ungeschützt
            return
        reviews = ({"required_approving_review_count": rules.approvals,
                    "dismiss_stale_reviews": rules.dismiss_stale}
                   if rules.pull_request_required else None)
        self.request("PUT", path, "Schutzregeln speichern", Capability.BRANCH_PROTECTION, json={
            "required_status_checks": None,
            "enforce_admins": rules.enforce_admins,
            "required_pull_request_reviews": reviews,
            "restrictions": None,
            "allow_force_pushes": False,             # nie (CLAUDE.md)
            "allow_deletions": not rules.prevent_deletion,
        })

    def links(self, repo: RepoRef) -> RepoLinks:
        page = f"{web_base(self.url)}/{repo.owner}/{repo.name}"
        return RepoLinks(page, f"{page}#readme", f"{page}/releases/latest")

    def clone_url(self, repo: RepoRef) -> str:
        return f"{web_base(self.url)}/{repo.owner}/{repo.name}.git"

    def license_text(self, spdx: str, holder: str, year: int) -> str | None:
        """Lizenztext aus den Vorlagen von GitHub, mit Name und Jahr (Konzept 9.1)."""
        try:
            body = self.request("GET", f"/licenses/{spdx.lower()}", "Lizenztext lesen").json()
        except NotFound:
            return None
        text = str(body.get("body", ""))
        for placeholder in ("[year]", "[yyyy]"):
            text = text.replace(placeholder, str(year))
        for placeholder in ("[fullname]", "[name of copyright owner]"):
            text = text.replace(placeholder, holder)
        return text or None
