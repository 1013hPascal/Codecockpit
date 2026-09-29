"""SQLite-Datenbank des Cockpits mit Versionsnummer und Umbau-Schritten (Migrationen).

Die Datenbank enthält nie Geheimnisse. Geheimnisse liegen nur im Tresor, hier stehen höchstens
ihre Namen (Tabelle vault_names).
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

# Jeder Eintrag ist ein Umbau-Schritt. Die Position in der Liste plus eins ist die Version.
# Bestehende Einträge nie ändern, nur neue anhängen.
MIGRATIONS: list[str] = [
    """
    CREATE TABLE settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    CREATE TABLE projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        project_dir TEXT NOT NULL UNIQUE,
        code_dir TEXT NOT NULL,
        exe_dir TEXT,
        account_id INTEGER,
        added_at TEXT NOT NULL,
        last_updated TEXT
    );
    CREATE TABLE accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        adapter TEXT NOT NULL,
        display_name TEXT NOT NULL,
        username TEXT NOT NULL DEFAULT '',
        url TEXT NOT NULL DEFAULT '',
        extra TEXT NOT NULL DEFAULT '{}'
    );
    CREATE TABLE vault_names (
        name TEXT PRIMARY KEY
    );
    CREATE TABLE features_global (
        feature_id TEXT PRIMARY KEY,
        enabled INTEGER NOT NULL
    );
    CREATE TABLE feature_settings (
        feature_id TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        PRIMARY KEY (feature_id, key)
    );
    """,
    # Phase 5a: verknüpfte Projekte, Adresse auf der Plattform, Repositories der Konten
    """
    ALTER TABLE projects ADD COLUMN linked INTEGER NOT NULL DEFAULT 0;
    ALTER TABLE projects ADD COLUMN remote_host TEXT NOT NULL DEFAULT '';
    ALTER TABLE projects ADD COLUMN remote_owner TEXT NOT NULL DEFAULT '';
    ALTER TABLE projects ADD COLUMN remote_name TEXT NOT NULL DEFAULT '';
    CREATE TABLE remote_repos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
        host TEXT NOT NULL,
        owner TEXT NOT NULL,
        name TEXT NOT NULL,
        private INTEGER NOT NULL DEFAULT 1,
        clone_url TEXT NOT NULL,
        web_url TEXT NOT NULL DEFAULT '',
        pushed_at TEXT NOT NULL DEFAULT '',
        first_seen TEXT NOT NULL,
        UNIQUE (account_id, owner, name)
    );
    """,
    # Phase 5d: ausgeführte Schritte der Features pro Commit, für die Details im Verlauf
    """
    CREATE TABLE commit_steps (
        project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        sha TEXT NOT NULL,
        steps TEXT NOT NULL,
        PRIMARY KEY (project_id, sha)
    );
    """,
    # Phase 6a: offene Pull Requests pro Repository, für "1 offener Pull Request"
    """
    CREATE TABLE pull_request_cache (
        repo TEXT NOT NULL,
        number INTEGER NOT NULL,
        head TEXT NOT NULL,
        base TEXT NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL DEFAULT '',
        draft INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (repo, number)
    );
    """,
    # Projektsammlungen: Ein Projekt steht in höchstens einer Sammlung (Primärschlüssel)
    """
    CREATE TABLE collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );
    CREATE TABLE collection_members (
        project_id INTEGER PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
        collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE
    );
    """,
    # Repositories, die nur auf der Plattform liegen, in Sammlungen. Schlüssel ist die Adresse,
    # weil die Zeilen in remote_repos beim Abfragen neu angelegt werden.
    """
    CREATE TABLE collection_remote_members (
        repo_key TEXT PRIMARY KEY,
        collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE
    );
    """,
]


class Database:
    """Dünne Hülle um sqlite3. Nutzbar aus mehreren Threads (eine Sperre für alles)."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path) if str(path) != ":memory:" else path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self.migrate()

    # -- Aufbau --------------------------------------------------------------------------
    @property
    def version(self) -> int:
        with self._lock:
            return self._conn.execute("PRAGMA user_version").fetchone()[0]

    def migrate(self) -> None:
        with self._lock:
            current = self.version
            for number, script in enumerate(MIGRATIONS[current:], start=current + 1):
                with self._conn:
                    self._conn.executescript(script)
                    self._conn.execute(f"PRAGMA user_version = {number}")

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- Zugriff --------------------------------------------------------------------------
    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        with self._lock, self._conn:
            return self._conn.execute(sql, params)

    def query(self, sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def query_one(self, sql: str, params: tuple | dict = ()) -> sqlite3.Row | None:
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock, self._conn:
            yield self._conn

    def table_names(self) -> list[str]:
        rows = self.query("SELECT name FROM sqlite_master WHERE type = 'table' "
                          "AND name NOT LIKE 'sqlite_%' ORDER BY name")
        return [row["name"] for row in rows]

    # -- Einfache Schlüssel-Wert-Einstellungen -------------------------------------------
    def get_value(self, key: str, default: Any = None) -> Any:
        row = self.query_one("SELECT value FROM settings WHERE key = ?", (key,))
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except ValueError:
            return default

    def set_value(self, key: str, value: Any) -> None:
        self.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                     (key, json.dumps(value, ensure_ascii=False)))
