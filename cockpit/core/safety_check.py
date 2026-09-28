"""Sicherheitsprüfung vor dem Hochladen (Konzept 9.6). Teil des Kerns und nicht abschaltbar.

Geprüft wird:
- Geheimnisse: Tokens und Schlüssel bekannter Anbieter, private Schlüssel, Zeilen wie
  password = "...", .env-Dateien und Schlüsseldateien. Ein Geheimnis stoppt das Hochladen.
- Geheimnisse in Commits, die noch nicht hochgeladen sind (auch wenn die Datei sie heute nicht
  mehr enthält, würde der Verlauf sie veröffentlichen).
- Private Daten: Datenbanken, Logdateien und ähnliches. Warnung, Vorgabe "In .gitignore".
- Große Dateien: ab 50 MB Warnung, ab 100 MB Stopp, weil GitHub sie ablehnt.
- Private E-Mail-Adresse in einem öffentlichen Repository. Warnung.

Ein Fund nennt nie das Geheimnis selbst, nur Datei, Zeile und Art. Funde, die nach Prüfung kein
Geheimnis sind, werden in cockpit.toml als Fingerabdruck gemerkt: Dateiname und ein Hash der
Zeile, nie der Wert (ENTSCHEIDUNGEN.md).
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from cockpit.core import git
from cockpit.core.projects import read_config, write_config

log = logging.getLogger(__name__)

WARN_BYTES = 50 * 1024 * 1024
LIMIT_BYTES = 100 * 1024 * 1024
MAX_SCAN_BYTES = 5 * 1024 * 1024           # größere Dateien werden nicht Zeile für Zeile gelesen


class Kind(Enum):
    SECRET = "secret"                      # stoppt
    SECRET_IN_HISTORY = "secret_history"   # stoppt  # pragma: allowlist secret
    TOO_LARGE = "too_large"                # stoppt
    LARGE = "large"                        # Warnung
    PRIVATE_DATA = "private_data"          # Warnung
    PRIVATE_EMAIL = "private_email"        # Warnung

    @property
    def blocking(self) -> bool:
        return self in (Kind.SECRET, Kind.SECRET_IN_HISTORY, Kind.TOO_LARGE)


# Regeln für Geheimnisse: Name für die Meldung, Muster. Neue Regeln einfach anhängen.
SECRET_RULES: list[tuple[str, re.Pattern]] = [
    ("GitHub-Token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})")),
    ("Anthropic-Schlüssel", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI-Schlüssel", re.compile(r"\bsk-(?!ant-)(?:proj-)?[A-Za-z0-9_\-]{20,}")),
    ("AWS-Zugangsschlüssel", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Azure-Schlüssel", re.compile(r"(?i)AccountKey=[A-Za-z0-9+/=]{40,}")),
    ("Google-Schlüssel", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Slack-Token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("GitLab-Token", re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}")),
    ("Privater Schlüssel", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY")),
    ("Passwort oder Schlüssel im Code", re.compile(
        r"""(?ix)\b(?:password|passwort|passwd|pwd|secret|api_?key|access_?token|auth_?token)
            \w*\s*[:=]\s*["']([^"'\s]{6,})["']""")),
]

# Werte, die offensichtlich keine echten Geheimnisse sind (Platzhalter in Beispielen)
_PLACEHOLDER = re.compile(r"(?i)^(?:x+|\*+|\.+|changeme|change_me|your[_-].*|dein[_-].*|"
                          r"<.*>|\$\{.*\}|\{\{.*\}\}|example.*|beispiel.*|test.*|dummy.*|"
                          r"password|passwort|secret|none|null)$")

SECRET_FILES = re.compile(r"(?i)(?:^|/)(?:\.env(?:\.(?!example$|sample$|template$|beispiel$)"
                          r"[^/]*)?|[^/]*\.(?:pem|key|pfx|p12|kdbx|keystore|jks)|"
                          r"id_(?:rsa|dsa|ecdsa|ed25519))$")
PRIVATE_FILES = re.compile(r"(?i)\.(?:db|sqlite|sqlite3|db3|mdb|accdb|log|bak|dump|sql)$")
PRIVATE_NAMES = {"db": "Datenbank", "sqlite": "Datenbank", "sqlite3": "Datenbank",
                 "db3": "Datenbank", "mdb": "Datenbank", "accdb": "Datenbank",
                 "log": "Logdatei", "bak": "Sicherungsdatei", "dump": "Datenbank-Abzug",
                 "sql": "Datenbank-Abzug"}


@dataclass(frozen=True)
class Finding:
    kind: Kind
    path: str                     # relativ zum Code-Ordner, mit /
    rule: str = ""                # "GitHub-Token", "Datenbank", "70 MB" ...
    line: int = 0                 # 0: betrifft die ganze Datei
    fingerprint: str = ""         # für "kein Geheimnis"

    @property
    def text(self) -> str:
        """Für die Liste, das Wichtigste vorne. Nennt nie das Geheimnis selbst."""
        where = f"{self.path}, Zeile {self.line}" if self.line else self.path
        if self.kind is Kind.SECRET:
            return f"Geheimnis: {where}, {self.rule}"
        if self.kind is Kind.SECRET_IN_HISTORY:
            return f"Geheimnis in einem früheren Commit: {self.path}, {self.rule}"
        if self.kind is Kind.TOO_LARGE:
            return f"Zu groß für GitHub: {self.path}, {self.rule}"
        if self.kind is Kind.LARGE:
            return f"Große Datei: {self.path}, {self.rule}"
        if self.kind is Kind.PRIVATE_DATA:
            return f"Private Daten: {self.path}, {self.rule}"
        return f"Private E-Mail-Adresse: {self.rule}"

    @property
    def whole_file(self) -> bool:
        """Lässt sich mit .gitignore lösen."""
        return self.kind not in (Kind.PRIVATE_EMAIL, Kind.SECRET_IN_HISTORY)


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    @property
    def blocking(self) -> list[Finding]:
        return [f for f in self.findings if f.kind.blocking]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if not f.kind.blocking]

    @property
    def ok(self) -> bool:
        return not self.findings


def fingerprint(path: str, line_text: str) -> str:
    """Fingerabdruck einer Zeile: kurzer Hash, aus dem sich der Wert nicht zurückrechnen lässt."""
    digest = hashlib.sha256(f"{path}\n{line_text.strip()}".encode("utf-8")).hexdigest()
    return digest[:16]


def _size_text(size: int) -> str:
    return f"{round(size / (1024 * 1024))} MB"


def _is_binary(data: bytes) -> bool:
    return b"\0" in data[:8192]


def _secret_in_line(line: str) -> str:
    """Name der Regel, die in der Zeile anschlägt, sonst leer."""
    if ALLOWLIST in line.lower():
        return ""                        # ausdrücklich als kein Geheimnis vermerkt
    for name, pattern in SECRET_RULES:
        match = pattern.search(line)
        if not match:
            continue
        value = match.group(1) if match.groups() else match.group(0)
        if name == "Passwort oder Schlüssel im Code" and _PLACEHOLDER.match(value):
            continue
        if is_made_up(value):
            continue
        return name
    return ""


# Vermerk in einer Zeile, die kein Geheimnis enthält, obwohl sie so aussieht (wie bei
# detect-secrets), zum Beispiel beim Namen einer Art von Fund oben in Kind.
ALLOWLIST = "pragma: allowlist secret"

# Wörter, an denen man erfundene Werte in Tests und Beispielen erkennt (Wunsch des Nutzers,
# 28.09.2026). Echte Tokens bestehen aus Zufallszeichen. Nur Wörter ab 7 Buchstaben, damit ein
# echter Token nicht zufällig eines davon enthält.
MADE_UP_MARKERS = ("erfunden", "nurfuertest", "fuertests", "beispiel", "example", "placeholder",
                   "platzhalter", "dummytoken", "faketoken", "testtoken")


def is_made_up(value: str) -> bool:
    """Ein Wert, der ausdrücklich als erfunden gekennzeichnet ist, ist kein Geheimnis."""
    lowered = value.lower()
    return any(marker in lowered for marker in MADE_UP_MARKERS)


# -- Was wird hochgeladen? -------------------------------------------------------------------
def files_to_upload(code_dir: Path) -> list[str]:
    """Alle Dateien, die Git hochladen würde: verfolgte und neue, ohne die aus .gitignore."""
    if not git.is_repo(code_dir):
        return sorted(p.relative_to(code_dir).as_posix() for p in code_dir.rglob("*")
                      if p.is_file() and ".git" not in p.relative_to(code_dir).parts)
    result = git.run(["ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                     code_dir, action="Dateien lesen")
    return sorted({f for f in result.stdout.split("\0") if f and (code_dir / f).is_file()})


def ignored_fingerprints(code_dir: Path) -> set[str]:
    safety = read_config(code_dir).get("safety", {})
    values = safety.get("not_secret", []) if isinstance(safety, dict) else []
    return {str(v) for v in values}


def mark_not_secret(code_dir: Path, finding: Finding) -> None:
    """Fund als "kein Geheimnis" merken (in cockpit.toml, nur Dateiname und Fingerabdruck)."""
    data = read_config(code_dir)
    safety = data.get("safety") if isinstance(data.get("safety"), dict) else {}
    values = list(safety.get("not_secret", []))
    entry = f"{finding.path}:{finding.fingerprint}"
    if entry not in values:
        values.append(entry)
    safety["not_secret"] = sorted(values)
    data["safety"] = safety
    write_config(code_dir, data)


# -- Prüfung ---------------------------------------------------------------------------------
def scan(code_dir: Path, files: list[str] | None = None, public: bool = False,
         emails: list[str] | None = None, history_range: str = "") -> Report:
    """Prüft die Dateien (Standard: alles, was hochgeladen würde).

    public: das Repository ist oder wird öffentlich, dann zählen private E-Mail-Adressen.
    emails: Adressen, die in den Commits stehen werden.
    history_range: Commits, die noch nicht hochgeladen sind, zum Beispiel "origin/main..HEAD"
    oder "HEAD" bei einem Repository, das noch nie hochgeladen wurde."""
    report = Report()
    skip = ignored_fingerprints(code_dir)
    for relative in files if files is not None else files_to_upload(code_dir):
        path = code_dir / relative
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if SECRET_FILES.search(relative):
            report.findings.append(Finding(Kind.SECRET, relative, "Datei mit Zugangsdaten",
                                           fingerprint=fingerprint(relative, "<datei>")))
            continue
        if size >= LIMIT_BYTES:
            report.findings.append(Finding(Kind.TOO_LARGE, relative, _size_text(size)))
            continue
        if size >= WARN_BYTES:
            report.findings.append(Finding(Kind.LARGE, relative, _size_text(size)))
        match = PRIVATE_FILES.search(relative)
        if match:
            extension = relative.rsplit(".", 1)[-1].lower()
            report.findings.append(Finding(Kind.PRIVATE_DATA, relative,
                                           PRIVATE_NAMES.get(extension, "private Daten")))
            continue
        if size > MAX_SCAN_BYTES:
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            log.warning("Nicht lesbar: %s (%r)", relative, exc)
            continue
        if _is_binary(data):
            continue
        for number, line in enumerate(data.decode("utf-8", "replace").splitlines(), start=1):
            rule = _secret_in_line(line)
            if not rule:
                continue
            mark = fingerprint(relative, line)
            if f"{relative}:{mark}" in skip:
                continue
            report.findings.append(Finding(Kind.SECRET, relative, rule, number, mark))
    if history_range and git.is_repo(code_dir):
        report.findings.extend(_scan_history(code_dir, history_range, skip))
    if public:
        for email in sorted(set(emails or [])):
            if email and not is_noreply(email):
                report.findings.append(Finding(Kind.PRIVATE_EMAIL, "", email))
    return report


def _scan_history(code_dir: Path, history_range: str, skip: set[str]) -> list[Finding]:
    """Geheimnisse in hinzugefügten Zeilen der Commits, die noch nicht hochgeladen sind."""
    result = git.run(["log", "-p", "--no-color", "--format=", "--no-ext-diff", history_range],
                     code_dir, check=False)
    findings: dict[tuple[str, str], Finding] = {}
    current = ""
    for line in result.stdout.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else ""
            continue
        if not line.startswith("+") or not current:
            continue
        rule = _secret_in_line(line[1:])
        if rule:
            mark = fingerprint(current, line[1:])
            if f"{current}:{mark}" not in skip:
                findings.setdefault((current, rule), Finding(Kind.SECRET_IN_HISTORY, current,
                                                             rule, 0, mark))
    # Was heute noch in der Datei steht, meldet schon die Prüfung der Dateien
    return list(findings.values())


def is_noreply(email: str) -> bool:
    return "noreply" in email.lower()


def commit_emails(code_dir: Path, history_range: str) -> list[str]:
    if not history_range or not git.is_repo(code_dir):
        return []
    result = git.run(["log", "--format=%ae", history_range], code_dir, check=False)
    return sorted({e.strip() for e in result.stdout.splitlines() if e.strip()})


# -- .gitignore ------------------------------------------------------------------------------
GITIGNORE_DEFAULTS = [
    "# Virtuelle Umgebungen und Caches",
    ".venv/", "venv/", "env/", "__pycache__/", "*.py[cod]", ".pytest_cache/", ".mypy_cache/",
    "# Build-Ordner und Exe-Dateien",
    "build/", "dist/", "*.exe",
    "# Geheimnisse und private Daten",
    ".env", ".env.*", "!.env.example", "*.db", "*.sqlite", "*.sqlite3", "*.log",
]
_HEADER = "# Ergänzt von CodeCockpit"


def gitignore_missing(code_dir: Path) -> list[str]:
    """Muster aus GITIGNORE_DEFAULTS, die in .gitignore noch fehlen (ohne Kommentare)."""
    try:
        existing = {line.strip() for line in (code_dir / ".gitignore").read_text(
            encoding="utf-8", errors="replace").splitlines()}
    except FileNotFoundError:
        existing = set()
    return [p for p in GITIGNORE_DEFAULTS if not p.startswith("#") and p not in existing]


def ensure_gitignore(code_dir: Path, extra: list[str] | None = None) -> list[str]:
    """.gitignore anlegen oder ergänzen. Gibt die neuen Zeilen zurück. Vorhandene Zeilen bleiben
    unverändert, neue kommen ans Ende."""
    path = code_dir / ".gitignore"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        text = ""
    existing = {line.strip() for line in text.splitlines()}
    lines: list[str] = []
    if extra is None:
        comment, group = "", []
        for pattern in [*GITIGNORE_DEFAULTS, "#"]:
            if pattern.startswith("#"):
                if group:                          # Kommentar nur mit neuen Zeilen darunter
                    lines += [comment, *group]
                comment, group = pattern, []
            elif pattern not in existing:
                group.append(pattern)
    else:
        lines = [p for p in extra if p not in existing]
    added = [p for p in lines if not p.startswith("#")]
    if not added:
        return []
    if text and not text.endswith("\n"):
        text += "\n"
    block = "\n".join([_HEADER, *lines]) + "\n"
    path.write_text(text + ("\n" if text else "") + block, encoding="utf-8")
    return added


def ignore_file(code_dir: Path, relative: str) -> None:
    """Eine Datei in .gitignore aufnehmen. Ist sie schon in Git, wird sie dort herausgenommen,
    bleibt aber auf der Festplatte (git rm --cached)."""
    ensure_gitignore(code_dir, ["/" + relative])
    if git.is_repo(code_dir):
        tracked = git.run(["ls-files", "--error-unmatch", "--", relative], code_dir,
                          check=False).returncode == 0
        if tracked:
            git.run(["rm", "--cached", "-q", "--", relative], code_dir,
                    action="Aus Git herausnehmen")
