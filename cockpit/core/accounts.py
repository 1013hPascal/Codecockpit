"""Konten (Konzept 5.1): Zugänge zu Plattformen, KI, E-Mail und Automation.

Jedes Konto gehört zu einem Adapter. Der Adapter sagt mit account_fields, welche Angaben nötig
sind. Angaben ohne Geheimnis stehen in der Datenbank, Geheimnisse nur im Tresor unter
codecockpit/account/<Nummer>/<Feld>.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from cockpit.adapters import registry as adapter_registry
from cockpit.adapters.base import AccountField, Adapter, TestResult
from cockpit.core.database import Database
from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret
from cockpit.core.vault_service import VaultService
from cockpit.vault.base import entry_name

log = logging.getLogger(__name__)

ACCOUNT_KINDS = {"platform": "Plattform", "ai": "KI", "email": "E-Mail",
                 "automation": "Automation"}
_COLUMNS = ("username", "url")                 # Felder mit eigener Spalte in der Datenbank


@dataclass(frozen=True)
class AccountType:
    kind: str                     # "platform", "ai", "email" oder "automation"
    adapter: str                  # Name im Adapter-Register, zum Beispiel "github"
    display_name: str             # "GitHub"
    fields: tuple[AccountField, ...]

    @property
    def label(self) -> str:
        return f"{self.display_name}, {ACCOUNT_KINDS[self.kind]}"


def account_types() -> list[AccountType]:
    """Alle Adapter, für die man ein Konto anlegen kann (sie haben account_fields)."""
    types = []
    for kind in ACCOUNT_KINDS:
        for name in adapter_registry.names(kind):
            try:
                cls = adapter_registry.adapter_class(kind, name)
            except CockpitError:
                log.exception("Adapter %s/%s nicht ladbar", kind, name)
                continue
            if cls.account_fields:
                types.append(AccountType(kind, name, cls.display_name, tuple(cls.account_fields)))
    return sorted(types, key=lambda t: t.label.lower())


def find_type(kind: str, adapter: str) -> AccountType | None:
    return next((t for t in account_types() if t.kind == kind and t.adapter == adapter), None)


@dataclass(frozen=True)
class Account:
    id: int
    kind: str
    adapter: str
    display_name: str
    username: str = ""
    url: str = ""
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def label(self) -> str:
        """Für Listen: Name zuerst, dann Art, dann Benutzername."""
        account_type = find_type(self.kind, self.adapter)
        type_name = account_type.label if account_type else f"{self.adapter}, unbekannte Art"
        parts = [self.display_name, type_name]
        if self.username:
            parts.append(self.username)
        return ", ".join(parts)


class AccountStore:
    def __init__(self, database: Database, vault: VaultService) -> None:
        self.database = database
        self.vault = vault

    # -- Lesen ---------------------------------------------------------------------------
    @staticmethod
    def _from_row(row) -> Account:
        try:
            extra = json.loads(row["extra"])
        except ValueError:
            extra = {}
        return Account(row["id"], row["kind"], row["adapter"], row["display_name"],
                       row["username"], row["url"], extra)

    def all(self) -> list[Account]:
        rows = self.database.query("SELECT * FROM accounts ORDER BY display_name COLLATE NOCASE")
        return [self._from_row(r) for r in rows]

    def get(self, account_id: int) -> Account | None:
        row = self.database.query_one("SELECT * FROM accounts WHERE id = ?", (account_id,))
        return self._from_row(row) if row else None

    def values(self, account: Account, with_secrets: bool = True) -> dict[str, Any]:
        """Alle Angaben des Kontos. Geheimnisse als Secret, dafür muss der Tresor offen sein."""
        account_type = self._type(account)
        result: dict[str, Any] = {}
        for f in account_type.fields:
            if f.secret:
                if with_secrets:
                    result[f.key] = self.vault.read(self._secret_name(account.id, f.key))
            elif f.key in _COLUMNS:
                result[f.key] = getattr(account, f.key)
            else:
                result[f.key] = account.extra.get(f.key, f.default)
        return result

    # -- Ändern --------------------------------------------------------------------------
    def create(self, account_type: AccountType, display_name: str,
               values: dict[str, Any]) -> Account:
        self._check(account_type, display_name, values, new=True)
        columns, extra = self._split(account_type, values)
        cursor = self.database.execute(
            "INSERT INTO accounts (kind, adapter, display_name, username, url, extra) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (account_type.kind, account_type.adapter, display_name.strip(),
             columns.get("username", ""), columns.get("url", ""),
             json.dumps(extra, ensure_ascii=False)))
        account_id = cursor.lastrowid
        try:
            self._write_secrets(account_id, account_type, values)
        except Exception:
            self.database.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            raise
        log.info("Konto angelegt: %s (%s)", display_name, account_type.adapter)
        return self.get(account_id)

    def update(self, account: Account, display_name: str, values: dict[str, Any]) -> Account:
        """Leere Geheimnisse bleiben unverändert."""
        account_type = self._type(account)
        self._check(account_type, display_name, values, new=False)
        columns, extra = self._split(account_type, values)
        self._write_secrets(account.id, account_type, values)
        self.database.execute(
            "UPDATE accounts SET display_name = ?, username = ?, url = ?, extra = ? WHERE id = ?",
            (display_name.strip(), columns.get("username", ""), columns.get("url", ""),
             json.dumps(extra, ensure_ascii=False), account.id))
        return self.get(account.id)

    def delete(self, account: Account) -> None:
        """Konto und seine Geheimnisse im Tresor löschen. Projekte verlieren die Zuordnung."""
        if any(f.secret for f in self._type(account).fields) or self._has_secrets(account.id):
            self.vault.delete_prefix(entry_name("account", account.id) + "/")
        self.database.execute("UPDATE projects SET account_id = NULL WHERE account_id = ?",
                              (account.id,))
        self.database.execute("DELETE FROM accounts WHERE id = ?", (account.id,))
        log.info("Konto gelöscht: %s", account.display_name)

    # -- Verbindung ------------------------------------------------------------------------
    def adapter_for(self, account: Account) -> Adapter:
        cls = adapter_registry.adapter_class(account.kind, account.adapter)
        return cls.from_account(self.values(account))

    def test(self, account: Account) -> TestResult:
        try:
            return self.adapter_for(account).test_connection()
        except CockpitError as exc:
            return TestResult(False, exc.message, exc.details)
        except Exception as exc:                        # ein Adapter darf hier nie abstürzen
            log.exception("Verbindungstest %s", account.adapter)
            return TestResult(False, "Der Verbindungstest ist fehlgeschlagen.", repr(exc))

    # -- Hilfen ----------------------------------------------------------------------------
    def _type(self, account: Account) -> AccountType:
        account_type = find_type(account.kind, account.adapter)
        if account_type is None:
            raise CockpitError(f"Die Kontoart {account.adapter} gibt es nicht mehr.")
        return account_type

    @staticmethod
    def _secret_name(account_id: int, key: str) -> str:
        return entry_name("account", account_id, key)

    def _has_secrets(self, account_id: int) -> bool:
        prefix = entry_name("account", account_id) + "/"
        return any(n.startswith(prefix) for n in self.vault.index.list())

    @staticmethod
    def _check(account_type: AccountType, display_name: str, values: dict[str, Any],
               new: bool) -> None:
        if not display_name.strip():
            raise CockpitError("Bitte einen Anzeigenamen eingeben.")
        for f in account_type.fields:
            value = values.get(f.key)
            text = value.reveal() if isinstance(value, Secret) else str(value or "")
            if f.required and not text.strip() and (new or not f.secret):
                raise CockpitError(f"Bitte {f.label} ausfüllen.")

    @staticmethod
    def _split(account_type: AccountType, values: dict[str, Any]) -> tuple[dict, dict]:
        columns, extra = {}, {}
        for f in account_type.fields:
            if f.secret:
                continue
            text = str(values.get(f.key) or f.default).strip()
            (columns if f.key in _COLUMNS else extra)[f.key] = text
        return columns, extra

    def _write_secrets(self, account_id: int, account_type: AccountType,
                       values: dict[str, Any]) -> None:
        for f in account_type.fields:
            value = values.get(f.key)
            if not f.secret or value is None:
                continue
            secret = value if isinstance(value, Secret) else Secret(str(value))
            if secret.reveal():
                self.vault.write(self._secret_name(account_id, f.key), secret)
