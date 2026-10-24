"""Tresor im Hauptfenster: sperren, entsperren, automatisch sperren, Konten.

Teil von MainWindow (main_window.py).
"""
from __future__ import annotations

import time

from cockpit.core.text import count
from cockpit.ui import vault_ui
from cockpit.ui.accounts_dialog import AccountsDialog
from cockpit.ui.announcer import announce
from cockpit.ui.common import show_info
from cockpit.ui.vault_settings_dialog import VaultSettingsDialog


class VaultMixin:
    """Tresor und Konten."""

    # -- Konten und Tresor ---------------------------------------------------------------
    def update_vault_actions(self) -> None:
        """Sperren und Entsperren gibt es nur bei der Tresordatei."""
        vault = self.services.vault
        self.act_lock.setVisible(vault.needs_unlock and vault.is_unlocked())
        self.act_unlock.setVisible(vault.needs_unlock and not vault.is_unlocked())

    def open_accounts(self) -> None:
        AccountsDialog(self.services, self).exec()
        self.services.forget_platforms()
        self.restart_lock_timer()
        self.reload_projects(refresh=False)
        self.refresh_remote()

    def open_vault_settings(self) -> None:
        VaultSettingsDialog(self.services, self).exec()
        self.update_vault_actions()
        self.restart_lock_timer()

    def lock_vault(self) -> None:
        self.services.vault.lock()
        self.update_vault_actions()
        announce("Tresor gesperrt.")

    def unlock_vault(self) -> None:
        vault_ui.ensure_unlocked(self.services, self)
        self.update_vault_actions()
        self.restart_lock_timer()

    def restart_lock_timer(self) -> None:
        vault = self.services.vault
        minutes = self.services.settings.load().auto_lock_minutes
        self.last_input = time.time()
        if vault.needs_unlock and vault.is_unlocked() and minutes > 0:
            self.lock_timer.start()
        else:
            self.lock_timer.stop()

    def check_auto_lock(self) -> None:
        minutes = self.services.settings.load().auto_lock_minutes
        if minutes > 0 and time.time() - self.last_input >= minutes * 60:
            self.auto_lock()

    def auto_lock(self) -> None:
        self.lock_timer.stop()
        if self.services.vault.needs_unlock and self.services.vault.is_unlocked():
            self.services.vault.lock()
            self.update_vault_actions()
            minutes = self.services.settings.load().auto_lock_minutes
            text = (f"Der Tresor wurde nach {count(minutes, 'Minute', 'Minuten')} ohne "
                    "Eingabe gesperrt.")
            # Meldungsfenster mit OK (Wunsch aus dem Test): NVDA liest es sicher vor, auch wenn
            # man gerade in einem anderen Programm war und zurückkommt.
            announce(text, speak=False)
            show_info(self, "Tresor gesperrt", text)
