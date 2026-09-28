"""Inhalt der README-Abschnitte (Konzept 10.2, Phase 9), ohne Qt.

Was das Cockpit sicher weiß, schreibt es selbst: Download, Installation, Änderungen aus den
Versionen, Hinweis zu Windows-Warnungen, Lizenz und die Liste der Bibliotheken. Funktionen,
Bedienung, Systemanforderungen und die Erklärung der Bibliotheken schreibt die KI aus Auszügen des
Codes, ohne Geheimnisse (Frage 5 zu Phase 9). Übersetzungen macht ebenfalls die KI.

Alles hier sind nur Vorschläge (Proposal). Übernommen wird erst, was der Nutzer bestätigt.
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from pathlib import Path

from cockpit.features.readme import document as doc

AI_KEYS = ("features", "usage", "requirements", "tools")
DESCRIPTIONS = {
    "features": "die Funktionen des Programms, als kurze Liste mit Spiegelstrichen",
    "usage": "die Bedienung, mit den wichtigsten Tastenkürzeln, als kurze Liste",
    "requirements": "die Systemanforderungen: Betriebssystem, Arbeitsspeicher, Zusatzprogramme "
                    "wie Ollama oder ein Mikrofon, als kurze Liste",
    "tools": "die verwendeten Bibliotheken und Werkzeuge. Für jede aus der Liste unter Fakten "
             "genau eine Zeile: Name, Doppelpunkt, ein Satz, wofür das Programm sie nutzt",
}
LANGUAGE_NAMES = {"en": "Englisch", "de": "Deutsch", "fr": "Französisch", "es": "Spanisch"}


@dataclass
class Proposal:
    file: str                            # README.md oder README.de.md
    code: str                            # Sprache, zum Beispiel "de"
    key: str
    title: str                           # Überschrift in dieser Sprache
    text: str
    reason: str = "neu"                  # "neu", "erneuert", "übersetzt" oder ein Satz der KI

    @property
    def line(self) -> str:
        return f"{self.title}, {self.reason}"


@dataclass
class Facts:
    name: str
    description: str = ""
    clone_url: str = ""                  # https://github.com/besitzer/projekt.git
    download_url: str = ""               # .../releases/latest/download/Name.exe
    start_file: str = ""
    libraries: list[str] = field(default_factory=list)
    releases: list = field(default_factory=list)       # versions.Released, neueste zuerst
    windows_note: bool = False           # Exe-Erstellung aktiv
    checksum: str = ""                   # SHA-256 der aktuellen Exe
    license: str = ""                    # zum Beispiel "MIT"
    requirements: str = ""               # bestätigte Systemanforderungen (cockpit.toml)

    def lines(self) -> list[str]:
        """Für die KI: was das Cockpit sicher weiß."""
        result = [f"Name: {self.name}"]
        if self.description:
            result.append(f"Kurzbeschreibung: {self.description}")
        if self.libraries:
            result.append(f"Bibliotheken aus requirements.txt: {', '.join(self.libraries)}")
        if self.start_file:
            result.append(f"Startdatei: {self.start_file}")
        if self.windows_note:
            result.append("Es gibt eine Exe für Windows.")
        return result


def libraries(code_dir: Path) -> list[str]:
    """Bibliotheken aus requirements.txt, ohne die, die nur für Tests da sind."""
    path = code_dir / "requirements.txt"
    if not path.is_file():
        return []
    names = []
    tests_only = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("#") and "test" in line.lower():
            tests_only = True
        stripped = line.split("#", 1)[0].strip()
        match = re.match(r"([A-Za-z0-9_.\-]+)", stripped)
        if match and not tests_only:
            names.append(match.group(1))
    return names


def license_name(code_dir: Path, fallback: str = "") -> str:
    path = next((code_dir / n for n in ("LICENSE", "LICENSE.md", "LICENSE.txt")
                 if (code_dir / n).is_file()), None)
    if path is None:
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")[:400]
    for name in ("MIT", "Apache", "GPL", "LGPL", "BSD", "MPL"):
        if name in text:
            return {"Apache": "Apache-2.0", "MPL": "MPL-2.0"}.get(name, name)
    return fallback or "siehe LICENSE"


# -- Feste Abschnitte ---------------------------------------------------------------------------
def fixed(key: str, facts: Facts, code: str) -> str:
    """Abschnitt, den das Cockpit selbst schreibt, auf Englisch oder Deutsch. Leer: nicht
    möglich oder nicht nötig. Andere Sprachen übersetzt danach die KI."""
    german = code == "de"
    if key == "download" and facts.download_url:
        return (f"Die neueste Version: [{facts.download_url.rsplit('/', 1)[-1]} herunterladen]"
                f"({facts.download_url}). Für Windows 10 und 11." if german else
                f"Latest version: [download {facts.download_url.rsplit('/', 1)[-1]}]"
                f"({facts.download_url}). For Windows 10 and 11.")
    if key == "install" and facts.clone_url:
        folder = facts.clone_url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
        steps = [f"git clone {facts.clone_url}", f"cd {folder}", "python -m venv .venv",
                 r".venv\Scripts\activate"]
        if facts.libraries:
            steps.append("pip install -r requirements.txt")
        if facts.start_file:
            steps.append(f"python {facts.start_file}")
        intro = ("Sie brauchen Python 3.11 oder neuer und Git." if german else
                 "You need Python 3.11 or newer and Git.")
        return intro + "\n\n```\n" + "\n".join(steps) + "\n```"
    if key == "changes" and facts.releases:
        blocks = []
        for release in facts.releases:
            items = "\n".join(f"- {s}" for s in release.subjects[:10]) or "-"
            blocks.append(f"### {release.version} ({release.date})\n\n{items}")
        return "\n\n".join(blocks)
    if key == "windows" and facts.windows_note:
        text = ("Windows warnt vielleicht mit „Der Computer wurde durch Windows geschützt“, weil "
                "die Exe nicht signiert ist. Wählen Sie „Weitere Informationen“ und dann "
                "„Trotzdem ausführen“." if german else
                "Windows may warn with \"Windows protected your PC\" because the executable is "
                "not signed. Choose \"More info\" and then \"Run anyway\".")
        if facts.checksum:
            text += (f"\n\nPrüfsumme (SHA-256) der Exe: `{facts.checksum}`" if german else
                     f"\n\nChecksum (SHA-256) of the executable: `{facts.checksum}`")
        return text
    if key == "license" and facts.license:
        return (f"Lizenz: {facts.license}. Der vollständige Text steht in [LICENSE](LICENSE)."
                if german else
                f"License: {facts.license}. See [LICENSE](LICENSE) for the full text.")
    if key == "requirements" and facts.requirements:
        return facts.requirements
    if key == "tools" and facts.libraries:
        return "\n".join(f"- {name}" for name in facts.libraries)
    return ""


# -- KI -----------------------------------------------------------------------------------------
def code_excerpt(code_dir: Path, name: str, start_file: str, max_chars: int) -> str:
    """Überblick für die KI: Dateien, Bibliotheken, Anfang der Startdatei. Ohne Geheimnisse."""
    from cockpit.features.ai_assistant.context import confidential, project_context, redact
    parts = [project_context(code_dir, name, max_chars // 2)]
    start = code_dir / start_file if start_file else None
    if start is not None and start.is_file() and not confidential(start_file):
        text = start.read_text(encoding="utf-8", errors="replace")
        parts.append(f"Anfang von {start_file}:\n" + redact("\n".join(text.splitlines()[:120])))
    return "\n\n".join(parts)[:max_chars]


def write_section(ai, key: str, code: str, facts: Facts, excerpt: str,
                  current: str = "", cancel: threading.Event | None = None) -> str:
    from cockpit.ai import prompt_files
    prompt = prompt_files.fill(
        prompt_files.load("readme_section"), abschnitt=DESCRIPTIONS[key],
        sprache=LANGUAGE_NAMES.get(code, "Englisch"), fakten="\n".join(facts.lines()),
        bisher=fixed(key, facts, code) or current or "nichts", code=excerpt)
    return clean(ai.ask(prompt, prompt_files.load("readme_section_system"), cancel))


def translate(ai, text: str, code: str, cancel: threading.Event | None = None) -> str:
    from cockpit.ai import prompt_files
    prompt = prompt_files.fill(prompt_files.load("readme_translate"),
                               sprache=LANGUAGE_NAMES.get(code, "Englisch"), inhalt=text)
    return clean(ai.ask(prompt, prompt_files.load("readme_translate_system"), cancel))


def clean(answer: str) -> str:
    """Überschrift und Code-Zaun um die ganze Antwort entfernen, falls die KI sie mitliefert."""
    text = answer.strip()
    text = re.sub(r"^```(?:markdown|md)?\s*\n(.*)\n```$", r"\1", text, flags=re.DOTALL)
    return re.sub(r"^#{1,3} .*\n+", "", text).strip()


# -- Prüfung vor dem Hochladen ------------------------------------------------------------------
_BLOCK = re.compile(r"NEU:\s*\n<<<\n(.*?)\n?>>>", re.DOTALL)


def parse_check(answer: str) -> list[tuple[str, str, str]]:
    """(Überschrift, Grund, neuer Text) aus der Antwort im Format des Prompts readme_check."""
    found = []
    for block in re.split(r"\n(?=ABSCHNITT:)", answer.replace("\r\n", "\n")):
        if not block.lstrip().startswith("ABSCHNITT:"):
            continue
        title = re.search(r"ABSCHNITT:\s*(.+)", block).group(1).strip().lstrip("#").strip()
        reason = re.search(r"GRUND:\s*(.+)", block)
        body = _BLOCK.search(block)
        if title and body:
            found.append((title, reason.group(1).strip() if reason else "", body.group(1).strip()))
    return found
