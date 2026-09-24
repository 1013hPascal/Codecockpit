"""Tresor in der Oberfläche: entsperren bei Bedarf und Speicherart wechseln (Konzept 5.2).

Der Wechsel beschreibt vorher, was passiert, und braucht eine Bestätigung. Er überträgt alle
Einträge, prüft sie und entfernt sie erst danach aus der alten Speicherart.
"""
from __future__ import annotations

import logging

from PySide6.QtWidgets import QWidget

from cockpit.core.errors import CockpitError
from cockpit.core.services import Services
from cockpit.core.text import count
from cockpit.core.vault_service import KINDS, move_entries
from cockpit.ui.announcer import announce
from cockpit.ui.common import confirm
from cockpit.ui.error_dialog import show_error
from cockpit.ui.password_dialogs import NewPasswordDialog, UnlockDialog
from cockpit.vault.base import Vault

log = logging.getLogger(__name__)


def ensure_unlocked(services: Services, parent: QWidget | None) -> bool:
    """True, wenn der Tresor offen ist oder nach Eingabe des Master-Passworts geöffnet wurde."""
    vault = services.vault
    if vault.vault is None:
        show_error(parent, "Tresor", "Es ist noch kein Tresor eingerichtet.")
        return False
    if vault.is_unlocked():
        return True
    if UnlockDialog(vault.unlock, parent).exec():
        announce("Tresor entsperrt.")
        return True
    return False


def prepare_vault(services: Services, kind: str, parent: QWidget | None) -> Vault | None:
    """Neue Speicherart bereitstellen: Windows prüfen, Tresordatei anlegen oder öffnen.
    Gibt den entsperrten Adapter zurück, None bei Abbruch oder Fehler."""
    vault = services.make_vault(kind)
    if kind == "vault_file":
        if vault.exists():
            if not UnlockDialog(vault.unlock, parent).exec():
                return None
            return vault
        dialog = NewPasswordDialog(parent=parent)
        if not dialog.exec():
            return None
        vault.create(dialog.new_password)
        return vault
    result = vault.test_connection()
    if not result.ok:
        show_error(parent, "Tresor", result.text, result.details)
        return None
    return vault


def switch_vault(services: Services, kind: str, parent: QWidget | None) -> bool:
    """Speicherart wechseln. Ohne bisherigen Tresor wird die neue einfach übernommen."""
    current = services.vault.vault
    if current is not None and current.kind == kind:
        return True
    if current is not None:
        if not ensure_unlocked(services, parent):
            return False
        number = len(current.names())
        text = (f"Die Zugangsdaten werden von {KINDS[current.kind]} nach {KINDS[kind]} "
                f"übertragen ({count(number, 'Eintrag', 'Einträge')}). Danach werden sie in "
                f"{KINDS[current.kind]} gelöscht. Nichts muss neu eingegeben werden. Wechseln?")
        if not confirm(parent, "Speicherart wechseln", text, yes="Wechseln", no="Abbrechen"):
            return False
    new = prepare_vault(services, kind, parent)
    if new is None:
        return False
    if current is not None:
        try:
            moved = move_entries(current, new, services.vault.index)
        except CockpitError as exc:
            show_error(parent, "Speicherart wechseln", exc.message, exc.details)
            return False
        if current.kind == "vault_file":
            current.destroy()
        announce(f"Speicherart gewechselt. {count(moved, 'Eintrag', 'Einträge')} übertragen.")
    services.use_vault(new)
    return True
