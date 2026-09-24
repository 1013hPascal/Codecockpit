"""Die festen Einhängepunkte der Abläufe (Konzept 3.3).

PUSH ist der Schritt des Kerns, der wirklich hochlädt. Bis einschließlich PUSH bricht ein Fehler
den Ablauf ab. Danach laufen die übrigen Schritte trotz Fehler weiter (Konzept 9.2).
"""
from __future__ import annotations

from enum import IntEnum


class Hook(IntEnum):
    BEFORE_COMMIT_MESSAGE = 1
    COMMIT_MESSAGE = 2
    BEFORE_PUSH = 3
    PUSH = 4
    AFTER_PUSH = 5

    @property
    def aborts_on_failure(self) -> bool:
        return self <= Hook.PUSH
