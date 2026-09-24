"""Verschlüsselte Tresordatei mit Master-Passwort (Konzept 5.2).

Die Datei enthält einen lesbaren Kopf (Format und Parameter der Schlüsselableitung) und die
verschlüsselten Einträge. Der Kopf ist in die Verschlüsselung eingebunden: Wird er verändert, lässt
sich die Datei nicht mehr öffnen. Der Schlüssel liegt nur im Arbeitsspeicher, solange der Tresor
entsperrt ist. "Tresor sperren" entfernt ihn.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from cockpit.adapters.base import TestResult
from cockpit.core.errors import CockpitError
from cockpit.core.secret import Secret
from cockpit.vault import crypto
from cockpit.vault.base import Vault, VaultLocked

FORMAT = 1
MIN_PASSWORD_LENGTH = 8
DEFAULT_KDF = crypto.KdfParameters()

WRONG_PASSWORD = "Das Master-Passwort ist falsch."


def check_new_password(password: Secret, repeated: Secret) -> None:
    """Wirft CockpitError mit verständlichem Text, wenn das neue Passwort nicht passt."""
    if len(password.reveal()) < MIN_PASSWORD_LENGTH:
        raise CockpitError(f"Das Master-Passwort muss mindestens {MIN_PASSWORD_LENGTH} "
                           "Zeichen lang sein.")
    if password != repeated:
        raise CockpitError("Die beiden Passwörter stimmen nicht überein.")


class FileVault(Vault):
    kind = "vault_file"
    display_name = "Verschlüsselte Tresordatei"
    needs_unlock = True

    def __init__(self, path: Path, params: crypto.KdfParameters | None = None) -> None:
        self.path = Path(path)
        self.params = params or DEFAULT_KDF
        self._key: bytes | None = None
        self._salt: bytes | None = None
        self._entries: dict[str, str] | None = None

    # -- Zustand --------------------------------------------------------------------------
    def exists(self) -> bool:
        return self.path.is_file()

    def is_unlocked(self) -> bool:
        return self._entries is not None

    def test_connection(self) -> TestResult:
        if not self.exists():
            return TestResult(False, "Die Tresordatei gibt es noch nicht.", str(self.path))
        if not self.is_unlocked():
            return TestResult(True, "Die Tresordatei ist vorhanden und gesperrt.")
        return TestResult(True, "Die Tresordatei ist entsperrt.")

    # -- Anlegen, Entsperren, Sperren -----------------------------------------------------
    def create(self, password: Secret) -> None:
        """Neue, leere Tresordatei anlegen. Danach ist der Tresor entsperrt."""
        if self.exists():
            raise CockpitError("Es gibt schon eine Tresordatei.", str(self.path))
        self._salt = crypto.new_salt()
        self._key = crypto.derive_key(password.reveal(), self._salt, self.params)
        self._entries = {}
        self._save()

    def unlock(self, password: Secret) -> None:
        header, payload = self._read_file()
        salt = base64.b64decode(header["kdf"]["salt"])
        params = crypto.KdfParameters(header["kdf"]["n"], header["kdf"]["r"], header["kdf"]["p"])
        key = crypto.derive_key(password.reveal(), salt, params)
        try:
            data = crypto.decrypt(payload, key, _associated(header))
        except crypto.WrongPassword:
            raise CockpitError(WRONG_PASSWORD) from None
        entries = json.loads(data.decode("utf-8"))
        for value in entries.values():
            Secret(value)                           # beim Log-Filter anmelden
        self._salt, self._key, self.params = salt, key, params
        self._entries = entries

    def lock(self) -> None:
        self._key = None
        self._entries = None

    def change_password(self, old: Secret, new: Secret) -> None:
        """Master-Passwort ändern. Das alte muss stimmen, auch wenn der Tresor entsperrt ist."""
        header, payload = self._read_file()
        salt = base64.b64decode(header["kdf"]["salt"])
        params = crypto.KdfParameters(header["kdf"]["n"], header["kdf"]["r"], header["kdf"]["p"])
        try:
            data = crypto.decrypt(payload, crypto.derive_key(old.reveal(), salt, params),
                                  _associated(header))
        except crypto.WrongPassword:
            raise CockpitError("Das bisherige Master-Passwort ist falsch.") from None
        self._entries = json.loads(data.decode("utf-8"))
        self.params = DEFAULT_KDF
        self._salt = crypto.new_salt()
        self._key = crypto.derive_key(new.reveal(), self._salt, self.params)
        self._save()

    def destroy(self) -> None:
        """Tresordatei löschen (nach dem Wechsel der Speicherart)."""
        self.lock()
        self.path.unlink(missing_ok=True)

    # -- Einträge -------------------------------------------------------------------------
    def _require_unlocked(self) -> dict[str, str]:
        if self._entries is None:
            raise VaultLocked()
        return self._entries

    def read(self, name: str) -> Secret | None:
        value = self._require_unlocked().get(name)
        return Secret(value) if value is not None else None

    def write(self, name: str, value: Secret) -> None:
        self._require_unlocked()[name] = value.reveal()
        self._save()

    def delete(self, name: str) -> None:
        if self._require_unlocked().pop(name, None) is not None:
            self._save()

    def names(self) -> list[str]:
        return sorted(self._require_unlocked())

    # -- Datei ----------------------------------------------------------------------------
    def _header(self) -> dict:
        return {"format": FORMAT, "kdf": {"salt": base64.b64encode(self._salt).decode("ascii"),
                                          "n": self.params.n, "r": self.params.r,
                                          "p": self.params.p}}

    def _save(self) -> None:
        header = self._header()
        plaintext = json.dumps(self._entries, ensure_ascii=False).encode("utf-8")
        payload = crypto.encrypt(plaintext, self._key, _associated(header))
        content = dict(header, data=base64.b64encode(payload).decode("ascii"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(content), encoding="utf-8")
        os.replace(temporary, self.path)            # nie eine halb geschriebene Datei

    def _read_file(self) -> tuple[dict, bytes]:
        try:
            content = json.loads(self.path.read_text(encoding="utf-8"))
            header = {"format": content["format"], "kdf": content["kdf"]}
            payload = base64.b64decode(content["data"])
        except FileNotFoundError:
            raise CockpitError("Die Tresordatei wurde nicht gefunden.", str(self.path)) from None
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CockpitError("Die Tresordatei ist beschädigt.", repr(exc)) from None
        if header["format"] != FORMAT:
            raise CockpitError("Die Tresordatei hat ein unbekanntes Format.",
                               f"Format {header['format']}")
        return header, payload


def _associated(header: dict) -> bytes:
    return json.dumps(header, sort_keys=True).encode("utf-8")
