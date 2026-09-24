"""Schnittstelle für den Tresor (Konzept 5.2). Die echten Adapter kommen in Phase 3.

Namen von Einträgen haben die Form codecockpit/account/<Nummer>/<Feld>. Werte sind immer Secret.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import ClassVar

from cockpit.adapters.base import Adapter
from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret

NAME_PREFIX = "codecockpit/"


def entry_name(*parts: object) -> str:
    return NAME_PREFIX + "/".join(str(p) for p in parts)


class VaultLocked(CockpitError):
    def __init__(self) -> None:
        super().__init__("Der Tresor ist gesperrt. Bitte zuerst entsperren.")


class Vault(Adapter):
    needs_unlock: ClassVar[bool] = False   # True bei der Tresordatei mit Master-Passwort

    def is_unlocked(self) -> bool:
        return True

    def unlock(self, password: Secret) -> None:
        """Wirft CockpitError bei falschem Passwort."""

    def lock(self) -> None:
        """Entfernt den Schlüssel aus dem Arbeitsspeicher."""

    @abstractmethod
    def read(self, name: str) -> Secret | None: ...

    @abstractmethod
    def write(self, name: str, value: Secret) -> None: ...

    @abstractmethod
    def delete(self, name: str) -> None: ...

    @abstractmethod
    def names(self) -> list[str]: ...
