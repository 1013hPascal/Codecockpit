"""README erstellen und aktualisieren (Konzept 10.2, Phase 9), ohne Qt.

1. plan_main: Vorschläge für die Hauptsprache. Fehlende Abschnitte kommen neu dazu. Vorhandene,
   die vom Cockpit stammen und unverändert sind, erneuert es, wenn sich die Fakten geändert haben
   (zum Beispiel neue Version, neue Prüfsumme). Selbst geschriebene bleiben unberührt.
2. Der Nutzer sieht jeden Vorschlag einzeln und übernimmt, passt an oder überspringt.
3. plan_translations: die übernommenen Abschnitte in die weiteren Sprachen.
4. apply: schreibt die Dateien, vorher kommen die alten in die Sicherheitskopien.
"""
from __future__ import annotations

import shutil
import threading
from pathlib import Path
from typing import Callable

from cockpit.core import backups, exe
from cockpit.core.projects import Project
from cockpit.features.readme import content
from cockpit.features.readme import document as doc
from cockpit.features.readme.content import Facts, Proposal

FEATURE_ID = "readme"


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
    head = doc.parse(_read(code_dir / "README.md")).head
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


def plan_main(services, project: Project, ai, cancel: threading.Event | None = None,
              status: Callable[[str], None] = lambda text: None) -> list[Proposal]:
    """Vorschläge für die README in der Hauptsprache. ai: TextAI oder None (dann nur die
    Abschnitte, die das Cockpit selbst schreiben kann)."""
    code_dir = project.code_dir
    main_code, _codes = languages(services, code_dir)
    file = "README.md"
    readme = doc.parse(_read(code_dir / file))
    facts = gather_facts(services, project)
    excerpt = None
    proposals: list[Proposal] = []
    for key in enabled_keys(services):
        if cancel is not None and cancel.is_set():
            break
        part = readme.find(key)
        title = part.title if part is not None else doc.heading(key, main_code)
        if part is not None and doc.is_own(code_dir, file, part):
            continue                                    # selbst geschrieben: nie anfassen
        text = content.fixed(key, facts, main_code) if main_code in ("en", "de") else ""
        if key in content.AI_KEYS and ai is not None and (part is None or key == "tools") \
                and not (key == "requirements" and facts.requirements):
            status(f"Die KI schreibt den Abschnitt {doc.KEY_NAMES[key]}.")
            if excerpt is None:
                excerpt = content.code_excerpt(code_dir, project.name, facts.start_file,
                                               ai.max_chars // 2)
            text = content.write_section(ai, key, main_code, facts, excerpt,
                                         part.body if part else "", cancel)
        elif text and main_code not in ("en", "de") and ai is not None:
            text = content.translate(ai, content.fixed(key, facts, "en"), main_code, cancel)
        if not text.strip():
            continue
        if part is None:
            proposals.append(Proposal(file, main_code, key, title, text, "neu"))
        elif doc.fingerprint(part.body) != doc.fingerprint(text):
            proposals.append(Proposal(file, main_code, key, title, text, "erneuert"))
    return proposals


def plan_translations(services, project: Project, ai, accepted: list[Proposal],
                      cancel: threading.Event | None = None,
                      status: Callable[[str], None] = lambda text: None) -> list[Proposal]:
    """Übernommene Abschnitte der Hauptsprache in die weiteren Sprachen (Frage 9). In einer
    Übersetzung selbst geschriebene Abschnitte bleiben unberührt."""
    code_dir = project.code_dir
    main_code, codes = languages(services, code_dir)
    proposals: list[Proposal] = []
    if ai is None:
        return proposals
    main = doc.parse(_read(code_dir / "README.md"))
    for code in codes[1:]:
        file = doc.file_name(code, main_code)
        target = doc.parse(_read(code_dir / file))
        wanted = {p.key: p.text for p in accepted}
        for part in main.parts:                         # fehlt in der Übersetzung ganz
            if part.key and part.key not in wanted and target.find(part.key) is None:
                wanted[part.key] = part.body
        for key in [k for k in doc.KEYS if k in wanted]:
            if cancel is not None and cancel.is_set():
                return proposals
            existing = target.find(key)
            if existing is not None and doc.is_own(code_dir, file, existing):
                continue
            status(f"Die KI übersetzt {doc.KEY_NAMES[key]} ins "
                   f"{content.LANGUAGE_NAMES.get(code, code)}.")
            text = content.translate(ai, wanted[key], code, cancel)
            if text.strip():
                proposals.append(Proposal(file, code, key,
                                          existing.title if existing else doc.heading(key, code),
                                          text, "übersetzt"))
    return proposals


def apply(services, project: Project, proposals: list[Proposal]) -> Path | None:
    """Übernommene Vorschläge schreiben. Alte Dateien vorher in die Sicherheitskopien. Gibt den
    Ordner der Sicherheitskopie zurück, None wenn es noch keine README gab."""
    code_dir = project.code_dir
    main_code, codes = languages(services, code_dir)
    facts_name, description = project.name, gather_facts(services, project).description
    files = sorted({p.file for p in proposals} | ({"README.md"} if len(codes) > 1 else set()))
    existing = [code_dir / f for f in files if (code_dir / f).is_file()]
    backup = None
    if existing:
        backup = backups.new_backup_dir(project.name, "README vor dem Aktualisieren", code_dir)
        for path in existing:
            shutil.copy2(path, backup / path.name)
    for file in files:
        code = main_code if file == "README.md" else file.split(".")[1]
        readme = doc.parse(_read(code_dir / file))
        for proposal in [p for p in proposals if p.file == file]:
            readme.put(proposal.key, proposal.title, proposal.text)
        line = doc.language_line(code, codes, main_code) if len(codes) > 1 else ""
        doc.set_head(readme, facts_name, description, line)
        (code_dir / file).write_text(readme.text(), encoding="utf-8")
        for proposal in [p for p in proposals if p.file == file]:
            doc.remember(code_dir, file, proposal.key, readme.find(proposal.key).body)
            if proposal.key == "requirements" and file == "README.md":
                doc.save(code_dir, {"requirements": readme.find("requirements").body})
    return backup
