"""Verschlüsselung für Tresordatei und Sicherung (Konzept 5.2, Verfahren aus dem Tagebuch).

Aus dem Passwort wird mit Scrypt ein 256-Bit-Schlüssel abgeleitet. Verschlüsselt wird mit
AES-GCM und einer eigenen zufälligen Nonce. AES-GCM erkennt auch jede Veränderung der Daten.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

SALT_LENGTH = 16
NONCE_LENGTH = 12
KEY_LENGTH = 32


class WrongPassword(Exception):
    """Das Passwort passt nicht, oder die Daten sind beschädigt."""


@dataclass(frozen=True)
class KdfParameters:
    n: int = 2 ** 15          # etwa 32 MB Speicher, auf üblichen Rechnern unter einer Sekunde
    r: int = 8
    p: int = 1


def new_salt() -> bytes:
    return os.urandom(SALT_LENGTH)


def derive_key(password: str, salt: bytes, params: KdfParameters = KdfParameters()) -> bytes:
    kdf = Scrypt(salt=salt, length=KEY_LENGTH, n=params.n, r=params.r, p=params.p)
    return kdf.derive(password.encode("utf-8"))


def encrypt(plaintext: bytes, key: bytes, associated: bytes | None = None) -> bytes:
    """Rückgabe: Nonce plus Chiffrat."""
    nonce = os.urandom(NONCE_LENGTH)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, associated)


def decrypt(data: bytes, key: bytes, associated: bytes | None = None) -> bytes:
    if len(data) <= NONCE_LENGTH:
        raise WrongPassword("Daten zu kurz.")
    try:
        return AESGCM(key).decrypt(data[:NONCE_LENGTH], data[NONCE_LENGTH:], associated)
    except InvalidTag as exc:
        raise WrongPassword("Entschlüsselung fehlgeschlagen.") from exc
