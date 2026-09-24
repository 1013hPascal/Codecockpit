"""Gemeinsame Fehlerklassen.

Jeder Fehler hat einen einfachen deutschen Text für die Oberfläche und getrennt davon technische
Details. Die Details erscheinen nur hinter "Details anzeigen" und im Log, nie mit Geheimnissen.
"""
from __future__ import annotations


class CockpitError(Exception):
    """Ein erwarteter, verständlich erklärbarer Fehler."""

    def __init__(self, message: str, details: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class Cancelled(Exception):
    """Der Vorgang wurde vom Nutzer abgebrochen."""
