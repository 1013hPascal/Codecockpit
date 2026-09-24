"""Tresor in der Windows-Anmeldeinformationsverwaltung (Konzept 5.2), über die Bibliothek keyring.

Geschützt durch die Windows-Anmeldung, kein zusätzliches Passwort. Die Anmeldeinformations-
verwaltung kann ihre Einträge nicht auflisten. Deshalb führt das Cockpit eine Liste der Namen
(ohne Werte) in seiner Datenbank.
"""
from __future__ import annotations

from typing import Protocol

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

from cockpit.adapters.base import TestResult
from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret
from cockpit.vault.base import Vault

SERVICE = "CodeCockpit"
ACCESS_DENIED = "Die Windows-Anmeldeinformationsverwaltung hat den Zugriff abgelehnt."


class NameIndex(Protocol):
    def add(self, name: str) -> None: ...
    def remove(self, name: str) -> None: ...
    def list(self) -> list[str]: ...


class WindowsVault(Vault):
    kind = "windows"
    display_name = "Windows-Anmeldeinformationsverwaltung"
    needs_unlock = False

    def __init__(self, index: NameIndex, service: str = SERVICE, backend=None) -> None:
        self.index = index
        self.service = service
        self.backend = backend if backend is not None else keyring.get_keyring()

    def test_connection(self) -> TestResult:
        probe = "codecockpit/probe"
        try:
            self.backend.set_password(self.service, probe, "probe")
            ok = self.backend.get_password(self.service, probe) == "probe"
            self.backend.delete_password(self.service, probe)
        except KeyringError as exc:
            return TestResult(False, ACCESS_DENIED, repr(exc))
        if not ok:
            return TestResult(False, "Der Probe-Eintrag ließ sich nicht zurücklesen.")
        return TestResult(True, "Die Windows-Anmeldeinformationsverwaltung ist bereit.")

    def read(self, name: str) -> Secret | None:
        try:
            value = self.backend.get_password(self.service, name)
        except KeyringError as exc:
            raise CockpitError(ACCESS_DENIED, repr(exc)) from None
        return Secret(value) if value is not None else None

    def write(self, name: str, value: Secret) -> None:
        try:
            self.backend.set_password(self.service, name, value.reveal())
        except KeyringError as exc:
            raise CockpitError(ACCESS_DENIED, repr(exc)) from None
        self.index.add(name)

    def delete(self, name: str) -> None:
        try:
            self.backend.delete_password(self.service, name)
        except PasswordDeleteError:
            pass                                        # schon weg
        except KeyringError as exc:
            raise CockpitError(ACCESS_DENIED, repr(exc)) from None
        self.index.remove(name)

    def names(self) -> list[str]:
        return self.index.list()
