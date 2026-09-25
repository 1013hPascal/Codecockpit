"""Repositories der Plattform-Konten für die Projektliste (ENTSCHEIDUNGEN.md, Phase 5).

Alle Repositories des eigenen Kontos erscheinen von selbst in der Projektliste. Liegt eines noch
nicht auf dem Rechner, heißt es dort "nur auf GitHub", und Enter lädt es herunter.

Die Liste wird im Hintergrund von der Plattform geholt und in der Datenbank gemerkt. So steht sie
beim nächsten Start sofort da, auch ohne Netz und bei gesperrtem Tresor.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

from cockpit.core.database import Database
from cockpit.core.git import RemoteAddress


@dataclass(frozen=True)
class StoredRepo:
    id: int
    account_id: int
    host: str
    owner: str
    name: str
    private: bool
    clone_url: str
    web_url: str
    pushed_at: str

    @property
    def address(self) -> RemoteAddress:
        return RemoteAddress(self.host, self.owner, self.name)


class RemoteRepoStore:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _from_row(row) -> StoredRepo:
        return StoredRepo(row["id"], row["account_id"], row["host"], row["owner"], row["name"],
                          bool(row["private"]), row["clone_url"], row["web_url"],
                          row["pushed_at"])

    def all(self) -> list[StoredRepo]:
        rows = self.database.query("SELECT * FROM remote_repos ORDER BY pushed_at DESC")
        return [self._from_row(r) for r in rows]

    def get(self, repo_id: int) -> StoredRepo | None:
        row = self.database.query_one("SELECT * FROM remote_repos WHERE id = ?", (repo_id,))
        return self._from_row(row) if row else None

    def find(self, address: RemoteAddress) -> StoredRepo | None:
        """Repository zu einer Adresse, ohne Groß- und Kleinschreibung."""
        return next((r for r in self.all() if r.address.key == address.key), None)

    def replace(self, account_id: int, repos: list) -> list[StoredRepo]:
        """Die Liste eines Kontos durch die aktuelle der Plattform ersetzen (repos: RemoteRepo).
        Gibt die Repositories zurück, die vorher nicht bekannt waren. Beim allerersten Abruf eines
        Kontos gilt keines als neu."""
        known = {(r["owner"].lower(), r["name"].lower()) for r in self.database.query(
            "SELECT owner, name FROM remote_repos WHERE account_id = ?", (account_id,))}
        first_time = not self.database.get_value(f"remote_repos.fetched.{account_id}", False)
        now = datetime.now().isoformat(timespec="seconds")
        with self.database.transaction() as conn:
            conn.execute("DELETE FROM remote_repos WHERE account_id = ?", (account_id,))
            for repo in repos:
                host = (urlparse(repo.web_url or repo.clone_url).hostname or "").lower()
                conn.execute(
                    "INSERT INTO remote_repos (account_id, host, owner, name, private, clone_url,"
                    " web_url, pushed_at, first_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (account_id, host, repo.ref.owner, repo.ref.name, int(repo.private),
                     repo.clone_url, repo.web_url, repo.pushed_at, now))
        self.database.set_value(f"remote_repos.fetched.{account_id}", True)
        if first_time:
            return []
        return [r for r in self.all() if r.account_id == account_id
                and (r.owner.lower(), r.name.lower()) not in known]

    def only_remote(self, local_keys: set[str]) -> list[StoredRepo]:
        """Repositories, zu denen es kein Projekt auf dem Rechner gibt."""
        seen: set[str] = set()
        result = []
        for repo in self.all():
            key = repo.address.key
            if key in local_keys or key in seen:
                continue
            seen.add(key)
            result.append(repo)
        return result
