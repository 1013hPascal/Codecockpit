"""Log mit Schutz vor Geheimnissen.

Der Formatierer maskiert die fertige Logzeile, also auch Tracebacks und Werte aus Argumenten:
alle angemeldeten Geheimnisse (siehe secret.py) und typische Muster von Tokens und Schlüsseln.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from cockpit.core import secret

MASK = "***"

_PATTERNS = [
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),              # GitHub-Tokens (klassisch, OAuth, App)
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),            # GitHub Fine-grained Token
    re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}"),               # GitLab
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),                  # OpenAI, Anthropic und ähnliche
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/\-]+=*"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)(\S+)"),
    re.compile(r"(?i)(https?://)[^/\s:@]+:[^/\s@]+@"),        # Zugangsdaten in Adressen
]


def mask_secrets(text: str) -> str:
    for value in secret.known_values():
        if value in text:
            text = text.replace(value, MASK)
    for pattern in _PATTERNS:
        if pattern.groups == 2:
            text = pattern.sub(lambda m: m.group(1) + MASK, text)
        elif pattern.groups == 1:
            text = pattern.sub(lambda m: m.group(1) + MASK + "@", text)
        else:
            text = pattern.sub(MASK, text)
    return text


class SecretMaskingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return mask_secrets(super().format(record))


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(log_dir: Path, level: int = logging.INFO) -> Path:
    """Richtet das Log in log_dir/app.log ein und gibt den Pfad zurück."""
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "app.log"
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(SecretMaskingFormatter(LOG_FORMAT))
    root = logging.getLogger()
    for old in list(root.handlers):
        if getattr(old, "_cockpit", False):
            root.removeHandler(old)
            old.close()
    handler._cockpit = True
    root.addHandler(handler)
    root.setLevel(level)
    return path
