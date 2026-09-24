"""Der Tresor aus Sicht des Kerns: gewählte Speicherart, Namensliste und Wechsel (Konzept 5.2).

Die konkrete Speicherart ist ein Adapter (cockpit/vault). Der Kern kennt nur die Schnittstelle
Vault. Die Namen aller Einträge stehen zusätzlich ohne Werte in der Tabelle vault_names. Die
Windows-Anmeldeinformationsverwaltung braucht das, weil sie nicht auflisten kann.
"""
from __future__ import annotations

import logging
from pathlib import Path

from cockpit.adapters import registry as adapter_registry
from cockpit.core.database import Database
from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret
from cockpit.vault.base import Vault, VaultLocked

log = logging.getLogger(__name__)

KINDS = {"windows": "Windows-Anmeldeinformationsverwaltung",
         "vault_file": "Verschlüsselte Tresordatei"}
VAULT_FILE_NAME = "vault.bin"
NOT_SET_UP = "Es ist noch kein Tresor eingerichtet."

adapter_registry.register("vault", "windows", "cockpit.vault.windows:WindowsVault")
adapter_registry.register("vault", "vault_file", "cockpit.vault.vault_file:FileVault")


class NameIndex:
    """Namen der Tresor-Einträge in der Datenbank, nie die Werte."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def add(self, name: str) -> None:
        self.database.execute("INSERT OR IGNORE INTO vault_names (name) VALUES (?)", (name,))

    def remove(self, name: str) -> None:
        self.database.execute("DELETE FROM vault_names WHERE name = ?", (name,))

    def list(self) -> list[str]:
        return [r["name"] for r in self.database.query("SELECT name FROM vault_names ORDER BY name")]

    def clear(self) -> None:
        self.database.execute("DELETE FROM vault_names")


def create_vault(kind: str, database: Database, data_dir: Path,
                 service: str = "CodeCockpit") -> Vault:
    """Adapter für die Speicherart erzeugen."""
    cls = adapter_registry.adapter_class("vault", kind)
    if kind == "windows":
        return cls(NameIndex(database), service=service)
    if kind == "vault_file":
        return cls(data_dir / VAULT_FILE_NAME)
    return cls()


class VaultService:
    """Einheitlicher Zugang zum Tresor. vault ist None, solange keiner eingerichtet ist."""

    def __init__(self, vault: Vault | None, index: NameIndex) -> None:
        self.vault = vault
        self.index = index

    @property
    def kind(self) -> str:
        return self.vault.kind if self.vault is not None else ""

    @property
    def display_name(self) -> str:
        return self.vault.display_name if self.vault is not None else "Kein Tresor"

    @property
    def needs_unlock(self) -> bool:
        return self.vault is not None and self.vault.needs_unlock

    def is_unlocked(self) -> bool:
        return self.vault is not None and self.vault.is_unlocked()

    def unlock(self, password: Secret) -> None:
        self._vault().unlock(password)
        log.info("Tresor entsperrt")

    def lock(self) -> None:
        if self.vault is not None:
            self.vault.lock()
            log.info("Tresor gesperrt")

    def _vault(self) -> Vault:
        if self.vault is None:
            raise CockpitError(NOT_SET_UP)
        return self.vault

    def _unlocked(self) -> Vault:
        vault = self._vault()
        if not vault.is_unlocked():
            raise VaultLocked()
        return vault

    def read(self, name: str) -> Secret | None:
        return self._unlocked().read(name)

    def write(self, name: str, value: Secret) -> None:
        self._unlocked().write(name, value)
        self.index.add(name)

    def delete(self, name: str) -> None:
        self._unlocked().delete(name)
        self.index.remove(name)

    def names(self) -> list[str]:
        return self._unlocked().names()

    def delete_prefix(self, prefix: str) -> None:
        for name in self.names():
            if name.startswith(prefix):
                self.delete(name)


def move_entries(old: Vault, new: Vault, index: NameIndex) -> int:
    """Alle Einträge in die neue Speicherart übertragen, prüfen, dann in der alten löschen.

    Schlägt das Zurücklesen fehl, werden die schon kopierten Einträge in der neuen Speicherart
    wieder entfernt, und die alte bleibt unverändert. Gibt die Zahl der Einträge zurück."""
    if not old.is_unlocked() or not new.is_unlocked():
        raise VaultLocked()
    names = old.names()
    copied: list[str] = []
    try:
        for name in names:
            value = old.read(name)
            if value is None:
                continue
            new.write(name, value)
            copied.append(name)
            if new.read(name) != value:
                raise CockpitError("Ein Eintrag ließ sich in der neuen Speicherart nicht "
                                   "richtig speichern. Es wurde nichts verändert.", name)
    except Exception:
        for name in copied:
            try:
                new.delete(name)
            except Exception:                          # Aufräumen darf den Fehler nicht verdecken
                log.exception("Aufräumen nach fehlgeschlagenem Wechsel")
        raise
    for name in copied:
        old.delete(name)
        index.add(name)
    log.info("Tresor gewechselt: %s Einträge von %s nach %s", len(copied), old.kind, new.kind)
    return len(copied)
