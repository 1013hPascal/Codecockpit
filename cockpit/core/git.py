"""Aufruf von Git. In Phase 2 nur die Suche nach git.exe, der Rest folgt in Phase 5."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

GUIDE = "anleitungen/git-installieren.md"


def find_git() -> Path | None:
    """Pfad zu git.exe oder None, wenn Git nicht installiert ist."""
    found = shutil.which("git")
    if found:
        return Path(found)
    candidates = [Path(os.environ.get(var, "")) / "Git" / "cmd" / "git.exe"
                  for var in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)")]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "Programs" / "Git" / "cmd" / "git.exe")
    return next((c for c in candidates if c.is_file()), None)
