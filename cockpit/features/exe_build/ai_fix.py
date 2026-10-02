"""Exe mit KI einrichten (Phase 10g).

Zwei Teile:
- Ohne KI, fest: richtige Startdatei, Ordner neben der Exe, fehlende Bibliotheken in
  requirements.txt. Das ergibt sich aus der Prüfung (setup_check).
- Mit KI: Änderungen am Code, zum Beispiel Daten neben der Exe statt im Startordner. Die KI
  bekommt die Prüfung, den Wunsch des Nutzers und Auszüge aus dem Code und antwortet in einem
  festen Format (Prompt exe_fix). Eine Änderung gilt nur, wenn ihr alter Text genau einmal in
  der Datei steht.

Nichts wird ohne Bestätigung geändert. apply() legt vorher eine Sicherheitskopie an.
"""
from __future__ import annotations

import re
import shutil
import threading
from dataclasses import dataclass, field
from pathlib import Path

from cockpit.core import backups, exe
from cockpit.core.errors import Cancelled, CockpitError
from cockpit.features.exe_build import setup_check

CONTEXT_LINES = 12                    # Zeilen vor und nach einer Fundstelle im Auszug
SMALL_FILE = 4000                     # kleinere Startdateien gehen ganz an die KI


@dataclass
class Change:
    file: str                         # relativ zum Ordner Code
    reason: str
    old: str                          # leer: neue Datei
    new: str
    problem: str = ""                 # warum die Änderung nicht passt, leer wenn sie passt

    def line(self) -> str:
        head = f"{self.file}: {self.reason}"
        return f"{head} Nicht übernehmbar: {self.problem}" if self.problem else head


@dataclass
class Proposal:
    summary: str = ""
    changes: list[Change] = field(default_factory=list)
    settings: exe.BuildSettings | None = None     # geänderte Exe-Einstellungen, sonst None
    settings_lines: list[str] = field(default_factory=list)

    @property
    def usable(self) -> list[Change]:
        return [c for c in self.changes if not c.problem]

    @property
    def empty(self) -> bool:
        return not self.usable and self.settings is None


# -- Fester Teil --------------------------------------------------------------------------------
def fixed_part(code_dir: Path, settings: exe.BuildSettings, progress=None) -> Proposal:
    """Was sich ohne KI sicher sagen lässt."""
    proposal = Proposal()
    start = settings.start_file
    if not (code_dir / start).is_file() or not setup_check.starts_something(code_dir / start):
        guess = setup_check.guess_start_file(code_dir)
        if guess != start and setup_check.starts_something(code_dir / guess):
            start = guess
            proposal.settings_lines.append(f"Startdatei: {guess} statt {settings.start_file}.")
    beside = list(settings.beside)
    for name in setup_check.data_folders(code_dir):
        if name not in beside:
            beside.append(name)
            proposal.settings_lines.append(f"Ordner neben der Exe: {name}.")
    if start != settings.start_file or beside != settings.beside:
        proposal.settings = exe.BuildSettings(start, settings.name, settings.one_file,
                                              settings.windowed, settings.icon, settings.datas,
                                              settings.hidden_imports, settings.self_test,
                                              settings.test_seconds, beside)
    missing = missing_packages(code_dir, progress)
    if missing:
        path = code_dir / "requirements.txt"
        old = path.read_text(encoding="utf-8") if path.is_file() else ""
        tail = "" if not old or old.endswith("\n") else "\n"
        proposal.changes.append(Change(
            "requirements.txt", f"Bibliotheken ergänzen, damit sie in die Exe kommen: "
            f"{', '.join(missing)}.", "", old + tail + "".join(f"{m}\n" for m in missing)))
    return proposal


def missing_packages(code_dir: Path, progress=None) -> list[str]:
    """Paketnamen für requirements.txt, die importiert werden, aber dort fehlen."""
    required = setup_check.requirements(code_dir)
    names = []
    for module in sorted(setup_check.third_party_imports(code_dir, progress)):
        package = setup_check.PACKAGE_NAMES.get(module.lower(), module)
        if setup_check._normalize(package) not in required and package not in names:
            names.append(package)
    return names


# -- Frage an die KI ----------------------------------------------------------------------------
def excerpts(code_dir: Path, start_file: str, max_chars: int) -> str:
    """Auszüge für die KI: die Startdatei (klein: ganz, sonst Anfang und Ende) und die Stellen,
    an denen der Code Daten im Startordner sucht."""
    parts: list[str] = []
    start = code_dir / start_file
    if start.is_file():
        text = start.read_text(encoding="utf-8", errors="replace")
        if len(text) > SMALL_FILE:
            lines = text.splitlines()
            text = "\n".join(lines[:40] + ["..."] + lines[-25:])
        parts.append(f"--- {start_file} ---\n{text}")
    for filename, name in setup_check.relative_data_paths(code_dir):
        lines = (code_dir / filename).read_text(encoding="utf-8", errors="replace").splitlines()
        for number, line in enumerate(lines):
            if f'"{name}"' in line or f"'{name}'" in line:
                first, last = max(0, number - CONTEXT_LINES), number + CONTEXT_LINES + 1
                parts.append(f"--- {filename}, Auszug ---\n" + "\n".join(lines[first:last]))
    return "\n\n".join(parts)[:max_chars]


ERROR_CHARS = 4000                    # so viel von der Fehlermeldung geht an die KI
_TRACE_FILE = re.compile(r'File "([^"]+\.py)", line (\d+)')


def error_excerpts(code_dir: Path, error: str) -> list[tuple[str, str]]:
    """Stellen im Code, die die Fehlermeldung nennt, zum Beispiel aus einem Traceback
    ("File ...\\gui.py", line 12). Nur Dateien im Ordner Code. Gibt (Datei, Auszug) zurück."""
    root = code_dir.resolve()
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, int]] = set()
    for raw, number in _TRACE_FILE.findall(error):
        path = Path(raw)
        if not path.is_absolute():
            path = code_dir / path
        try:
            path = path.resolve()
            relative = path.relative_to(root).as_posix()
        except (OSError, ValueError):
            continue
        line = int(number)
        if (relative, line) in seen or not path.is_file():
            continue
        seen.add((relative, line))
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        first, last = max(0, line - 1 - CONTEXT_LINES), line + CONTEXT_LINES
        found.append((relative, "\n".join(lines[first:last])))
    return found


def build_prompt(project_name: str, settings: exe.BuildSettings, check_lines: list[str],
                 wish: str, code: str, error: str = "") -> tuple[str, str]:
    from cockpit.ai import prompt_files
    error = error.strip()
    if len(error) > ERROR_CHARS:                 # das Ende enthält meist den eigentlichen Fehler
        error = "...\n" + error[-ERROR_CHARS:]
    prompt = prompt_files.fill(prompt_files.load("exe_fix"), projekt=project_name,
                               startdatei=settings.start_file,
                               neben=", ".join(settings.beside) or "keine",
                               pruefung="\n".join(check_lines), wunsch=wish.strip() or "keiner",
                               fehler=error or "keiner", code=code)
    return prompt, prompt_files.load("exe_fix_system")


_BLOCK = re.compile(r"(?:ALT|NEU):\s*\n<<<\n(.*?)\n?>>>", re.DOTALL)


def parse(answer: str) -> Proposal:
    """Antwort der KI im Format aus dem Prompt exe_fix_system lesen. Unvollständige Blöcke
    fallen weg."""
    proposal = Proposal()
    text = answer.replace("\r\n", "\n")
    match = re.search(r"ZUSAMMENFASSUNG:\s*(.+)", text)
    if match:
        proposal.summary = match.group(1).strip()
    for block in re.split(r"\n(?=AENDERUNG:)", text):
        if not block.lstrip().startswith("AENDERUNG:"):
            continue
        file = re.search(r"AENDERUNG:\s*(.+)", block).group(1).strip().strip("`\"'")
        reason = re.search(r"GRUND:\s*(.+)", block)
        bodies = _BLOCK.findall(block)
        if len(bodies) != 2 or not file:
            continue
        proposal.changes.append(Change(file.replace("\\", "/"), reason.group(1).strip()
                                       if reason else "", bodies[0], bodies[1]))
    return proposal


def check_changes(code_dir: Path, proposal: Proposal) -> None:
    """Jede Änderung prüfen: Datei im Ordner Code, alter Text genau einmal vorhanden."""
    root = code_dir.resolve()
    for change in proposal.changes:
        path = (code_dir / change.file).resolve()
        if not path.is_relative_to(root) or ".git" in path.relative_to(root).parts:
            change.problem = "Die Datei liegt nicht im Ordner Code."
        elif not change.old:
            if path.exists() and change.file != "requirements.txt":
                change.problem = "Die Datei gibt es schon."
        elif not path.is_file():
            change.problem = "Die Datei gibt es nicht."
        else:
            found = path.read_text(encoding="utf-8", errors="replace").count(change.old)
            if found != 1:
                change.problem = ("Der alte Text steht nicht in der Datei." if not found else
                                  "Der alte Text steht mehrmals in der Datei.")


def ask(ai, project_name: str, code_dir: Path, settings: exe.BuildSettings, wish: str,
        cancel: threading.Event | None = None, progress=None, error: str = "") -> Proposal:
    """Fester Teil plus Vorschlag der KI. Blockiert, also im Hintergrund aufrufen. ai: TextAI
    oder None (dann nur der feste Teil). progress bekommt Zeilen zum Stand, zum Beispiel
    welche Datei gelesen ist (Wunsch des Nutzers, 01.10.2026)."""
    say = progress or (lambda text: None)
    say("Der Code wird gelesen.")
    proposal = fixed_part(code_dir, settings, progress)
    if cancel is not None and cancel.is_set():
        raise Cancelled()
    if ai is None:
        check_changes(code_dir, proposal)
        return proposal
    effective = proposal.settings or settings
    say("Die Einrichtung der Exe wird geprüft.")
    lines = setup_check.check_for(code_dir, effective)
    code = excerpts(code_dir, effective.start_file, ai.max_chars // 2)
    if error:
        say("Die Fehlermeldung wird gelesen.")
        for filename, text in error_excerpts(code_dir, error):
            say(f"Stelle aus der Fehlermeldung gelesen: {filename}")
            code += f"\n\n--- {filename}, Stelle aus der Fehlermeldung ---\n{text}"
        code = code[:ai.max_chars // 2]
    files = sorted({part.split(",")[0] for part in re.findall(r"^--- (.+?) ---$", code,
                                                               re.MULTILINE)})
    prompt, system = build_prompt(project_name, effective, lines, wish, code, error)
    name = getattr(ai, "name", "")
    say(f"An die KI gesendet: {len(code)} Zeichen aus {', '.join(files) or 'keiner Datei'}. "
        f"Jetzt wartet das Cockpit auf die Antwort " + (f"von {name}." if name else "der KI."))
    answered = parse(ai.ask(prompt, system, cancel))
    say("Antwort der KI ist da.")
    proposal.summary = answered.summary
    proposal.changes += [c for c in answered.changes if c.file != "requirements.txt"]
    check_changes(code_dir, proposal)
    return proposal


# -- Fragen nach einem Schritt (Wunsch des Nutzers, 02.10.2026) ------------------------------------
CHAT_CHARS = 6000                       # so viel vom Fensterinhalt geht an die KI


def chat_hints(history: list[tuple[str, str]]) -> str:
    """Gespräch als Hinweise für die Wiederholung des letzten Schritts."""
    return "\n".join(f"Frage: {question}\nAntwort der KI: {answer}"
                     for question, answer in history)


def ask_chat(ai, project_name: str, step: str, content: list[str],
             history: list[tuple[str, str]], question: str,
             cancel: threading.Event | None = None) -> str:
    """Frage zum gerade abgeschlossenen Schritt. Die KI antwortet nur, sie ändert nichts."""
    from cockpit.ai import prompt_files
    prompt = prompt_files.fill(prompt_files.load("exe_chat"), projekt=project_name,
                               schritt=step,
                               inhalt="\n".join(content)[:CHAT_CHARS] or "nichts",
                               gespraech=chat_hints(history) or "noch keins",
                               frage=question.strip())
    return ai.ask(prompt, prompt_files.load("exe_chat_system"), cancel)


def with_hints(wish: str, hints: str) -> str:
    """Wunsch für die Wiederholung: der bisherige Wunsch und die Hinweise aus dem Gespräch."""
    if not hints.strip():
        return wish
    head = wish.strip() + "\n\n" if wish.strip() else ""
    return head + "Hinweise aus dem Gespräch mit dem Nutzer:\n" + hints.strip()


# -- Übernehmen ---------------------------------------------------------------------------------
def apply(project_name: str, code_dir: Path, proposal: Proposal) -> Path:
    """Die passenden Änderungen übernehmen. Die betroffenen Dateien und cockpit.toml kommen
    vorher in eine Sicherheitskopie. Gibt deren Ordner zurück."""
    changes = proposal.usable
    folder = backups.new_backup_dir(project_name, "vor den Änderungen für die Exe", code_dir)
    for name in {c.file for c in changes} | {"cockpit.toml"}:
        source = code_dir / name
        if source.is_file():
            target = folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for change in changes:
        path = code_dir / change.file
        if change.old:
            text = path.read_text(encoding="utf-8")
            if text.count(change.old) != 1:
                raise CockpitError(f"{change.file} hat sich inzwischen geändert. Es wurde nicht "
                                   "alles übernommen. Die Sicherheitskopie steht im Ordner "
                                   "backups.")
            path.write_text(text.replace(change.old, change.new), encoding="utf-8")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(change.new, encoding="utf-8")
    if proposal.settings is not None:
        exe.change_settings(code_dir, project_name, proposal.settings)
    return folder
