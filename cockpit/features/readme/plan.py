"""README schreiben, überarbeiten und übersetzen (Konzept 10.2, Phase 9), ohne Qt.

Wunsch des Nutzers vom 03.10.2026: Die KI schreibt die ganze README auf einmal, statt jeden
Abschnitt einzeln vorzuschlagen.
1. compose: Die KI schreibt die README in der Hauptsprache, aus Fakten, fertigen Bausteinen,
   Auszügen des Codes, Infodateien und Hinweisen des Nutzers. Mit bisherigem Text und Anweisungen
   überarbeitet sie ihn.
2. Der Nutzer liest und ändert den Text und bestätigt mit „fertig so“.
3. save_files schreibt die Dateien. Die alten kommen vorher in die Sicherheitskopien.
4. translate: die fertige README in die weiteren Sprachen, jede zum Lesen und Anpassen.
import_file übernimmt eine fertige README aus einer Datei.
"""
from __future__ import annotations

import re
import shutil
import threading
from pathlib import Path
from typing import Callable

from cockpit.core import backups, exe
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
from cockpit.features.readme import content
from cockpit.features.readme import document as doc
from cockpit.features.readme.content import Facts

FEATURE_ID = "readme"
MAIN_FILE = "README.md"


def _setting(services, key: str, fallback):
    try:
        value = services.features.setting(FEATURE_ID, key)
    except KeyError:
        return fallback
    return fallback if value in (None, "") else value


def languages(services, code_dir: Path) -> tuple[str, list[str]]:
    """Hauptsprache und alle Sprachen als Kürzel. Pro Projekt in cockpit.toml, sonst aus den
    Einstellungen des Features (Frage 8 zu Phase 9)."""
    stored = doc.settings(code_dir)
    main = stored.get("main_language") or _setting(services, "main_language", "Englisch")
    others = stored.get("languages")
    if not isinstance(others, list):
        others = list(_setting(services, "languages", ["Deutsch"]))
    main_code = doc.LANGUAGES.get(main, ("en", ""))[0]
    codes = [main_code] + [doc.LANGUAGES[o][0] for o in others
                           if o in doc.LANGUAGES and doc.LANGUAGES[o][0] != main_code]
    return main_code, codes


def enabled_keys(services) -> list[str]:
    names = _setting(services, "sections", list(doc.KEY_NAMES.values()))
    return [key for key in doc.KEYS if doc.KEY_NAMES[key] in names]


def _active(services, feature_id: str, project: Project) -> bool:
    try:
        return feature_id in services.registry and services.features.active(feature_id, project)
    except Exception:
        return False


def gather_facts(services, project: Project) -> Facts:
    code_dir = project.code_dir
    facts = Facts(project.name, libraries=content.libraries(code_dir))
    head = doc.parse(_read(code_dir / MAIN_FILE)).head
    lines = [l for l in head.splitlines() if l.strip() and not l.startswith("#") and "|" not in l]
    facts.description = lines[0].strip() if lines else ""
    settings = exe.read_settings(code_dir)
    facts.start_file = settings.start_file if settings else ""
    if project.remote is not None:
        base = f"https://{project.remote.host}/{project.remote.owner}/{project.remote.name}"
        facts.clone_url = base + ".git"
        if settings is not None and _active(services, "exe_build", project):
            asset = f"{settings.name}.zip"            # immer der ganze Ordner (03.10.2026)
            facts.download_url = f"{base}/releases/latest/download/{asset}"
    if _active(services, "exe_build", project):
        facts.windows_note = True
        current = exe.current_exe(project)
        if current is not None and current.is_file():
            from cockpit.core.update import sha256
            facts.checksum = sha256(current)
    if _active(services, "versions", project):
        from cockpit.features.versions import versions
        facts.releases = versions.history(code_dir)
    fallback = services.settings.load().default_license if services is not None else ""
    facts.license = content.license_name(code_dir, fallback)
    facts.requirements = str(doc.settings(code_dir).get("requirements", ""))
    return facts


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


# -- Infodateien --------------------------------------------------------------------------------
def info_text(paths: list[Path], max_chars: int) -> tuple[str, list[str]]:
    """Text der Infodateien für die KI, ohne Geheimnisse. Gibt auch die Namen der Dateien zurück,
    die nicht mitgehen: vertrauliche, unlesbare und solche, die kein Text sind."""
    from cockpit.features.ai_assistant.context import confidential, redact
    parts: list[str] = []
    skipped: list[str] = []
    for path in paths:
        try:
            data = path.read_bytes()[:max(max_chars, 1) * 4]
        except OSError:
            skipped.append(path.name)
            continue
        if confidential(path.name) or b"\0" in data[:4096]:
            skipped.append(path.name)
            continue
        text = redact(data.decode("utf-8", errors="replace")).strip()
        if text:
            parts.append(f"Datei {path.name}:\n{text}")
    return "\n\n".join(parts)[:max_chars], skipped


# -- Schreiben und überarbeiten -----------------------------------------------------------------
def compose(services, project: Project, ai, notes: str = "", info: str = "", current: str = "",
            wishes: str = "", cancel: threading.Event | None = None,
            status: Callable[[str], None] = lambda text: None) -> str:
    """Die ganze README in der Hauptsprache. Ohne current schreibt die KI sie neu, mit current
    und wishes überarbeitet sie den Text. ai: TextAI."""
    from cockpit.ai import prompt_files
    code_dir = project.code_dir
    main_code, _codes = languages(services, code_dir)
    facts = gather_facts(services, project)
    keys = enabled_keys(services)
    status("Die KI überarbeitet die README." if current else "Die KI schreibt die README.")
    values = dict(
        name=project.name, sprache=content.LANGUAGE_NAMES.get(main_code, "Englisch"),
        fakten="\n".join(facts.lines()), bausteine=content.blocks(keys, facts, main_code) or "keine",
        hinweise=notes.strip() or "keine", infos=info.strip() or "keine",
        code=content.code_excerpt(code_dir, project.name, facts.start_file, ai.max_chars // 3))
    if current.strip():
        prompt = prompt_files.fill(prompt_files.load("readme_revise"), bisher=current.strip(),
                                   wuensche=wishes.strip() or "Verbessere Sprache und Aufbau.",
                                   **values)
    else:
        headings = "\n".join(f"- {doc.heading(key, main_code)}" for key in keys)
        prompt = prompt_files.fill(prompt_files.load("readme_write"), abschnitte=headings,
                                   **values)
    text = content.clean_file(ai.ask(prompt, prompt_files.load("readme_write_system"), cancel))
    if not text:
        raise CockpitError("Die KI hat keinen Text geliefert. Bitte versuchen Sie es noch einmal.")
    return text


def translate(services, project: Project, ai, text: str, only: list[str] | None = None,
              cancel: threading.Event | None = None,
              status: Callable[[str], None] = lambda text: None) -> list[tuple[str, str, str]]:
    """Die README in alle weiteren Sprachen, oder nur in die Sprachen only. Gibt (Datei,
    Sprache, Text) zurück."""
    main_code, codes = languages(services, project.code_dir)
    source = _with_language_line(text, project.name, "")
    result = []
    for code in [c for c in codes[1:] if only is None or c in only]:
        if cancel is not None and cancel.is_set():
            break
        status(f"Die KI übersetzt die README ins {content.LANGUAGE_NAMES.get(code, code)}.")
        translated = content.translate_file(ai, source, code, cancel)
        if translated:
            result.append((doc.file_name(code, main_code), code, translated))
    return result


def missing_translations(services, project: Project) -> list[str]:
    """Weitere Sprachen, für die es noch keine Datei gibt."""
    main_code, codes = languages(services, project.code_dir)
    return [c for c in codes[1:] if not (project.code_dir / doc.file_name(c, main_code)).is_file()]


# -- Speichern ----------------------------------------------------------------------------------
def _with_language_line(text: str, title: str, line: str) -> str:
    """Nur den Kopf ändern: die Zeile mit den Sprachen einfügen, erneuern oder entfernen."""
    text = text.replace("\r\n", "\n")
    readme = doc.parse(text)
    doc.set_head(readme, title, "", line)
    start = re.search(r"(?m)^## ", text)
    rest = text[start.start():] if start else ""
    return "\n\n".join(p for p in (readme.head, rest.strip()) if p).strip() + "\n"


def save_files(services, project: Project, files: dict[str, str]) -> Path | None:
    """README-Dateien schreiben. Bei mehreren Sprachen bekommt jede vorhandene Datei oben die
    Links zu allen. Was sich ändert und schon da war, kommt vorher in die Sicherheitskopien.
    Gibt deren Ordner zurück, None wenn es nichts zu sichern gab."""
    code_dir = project.code_dir
    main_code, codes = languages(services, code_dir)
    final = {name: text.replace("\r\n", "\n").rstrip() + "\n" for name, text in files.items()}
    if len(codes) > 1:
        present = [c for c in codes if doc.file_name(c, main_code) in final
                   or (code_dir / doc.file_name(c, main_code)).is_file()]
        for code in present:
            name = doc.file_name(code, main_code)
            text = final.get(name) or _read(code_dir / name)
            line = doc.language_line(code, present, main_code) if len(present) > 1 else ""
            final[name] = _with_language_line(text, project.name, line)
    changed = {name: text for name, text in final.items() if _read(code_dir / name) != text}
    existing = [code_dir / name for name in changed if (code_dir / name).is_file()]
    backup = None
    if existing:
        backup = backups.new_backup_dir(project.name, "README vor dem Speichern", code_dir)
        for path in existing:
            shutil.copy2(path, backup / path.name)
    for name, text in changed.items():
        (code_dir / name).write_text(text, encoding="utf-8")
    part = doc.parse(final.get(MAIN_FILE, "")).find("requirements")
    if part is not None and part.body:
        doc.save(code_dir, {"requirements": part.body})   # für die Prüfung vor dem Hochladen
    return backup


def import_file(services, project: Project, source: Path) -> Path | None:
    """Eine fertige README aus einer Datei als README.md übernehmen."""
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise CockpitError(f"Die Datei {source.name} ließ sich nicht lesen.", str(exc)) from None
    try:
        if b"\0" in data:
            raise UnicodeDecodeError("utf-8", data, 0, 1, "Nullbyte")
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise CockpitError(f"{source.name} ist keine Textdatei in UTF-8. Bitte wählen Sie eine "
                           "Markdown- oder Textdatei.") from None
    if not text.strip():
        raise CockpitError(f"{source.name} ist leer.")
    return save_files(services, project, {MAIN_FILE: text})
