"""Prüfung der README vor dem Hochladen (Konzept 10.2, Frage 10 zu Phase 9).

Läuft vor dem Commit, damit Änderungen an der README im selben Commit landen. Nur wenn sich
mehr als die README geändert hat, eine README da ist und die Prüfung eingeschaltet ist. Die KI
schlägt Abschnitte vor, der Nutzer sieht jeden Vorschlag und übernimmt ihn, passt ihn an oder
überspringt ihn (Vorgabe). Selbst geschriebene Abschnitte schlägt sie nur vor, übernommen wird
auch dort nur nach Bestätigung. Klappt die KI nicht, geht das Hochladen trotzdem weiter.
"""
from __future__ import annotations

import logging
import shutil

from cockpit.core import backups, git, sync
from cockpit.core.errors import CockpitError
from cockpit.core.flows.engine import FlowContext
from cockpit.core.flows.questions import ConfirmQuestion, TextQuestion
from cockpit.core.flows.step import StepResult
from cockpit.features.readme import content
from cockpit.features.readme import document as doc
from cockpit.features.readme.plan import FEATURE_ID, _setting

log = logging.getLogger(__name__)
README_FILES = ("README.md",)


def _ai(context: FlowContext):
    services = context.services
    tool = _setting(services, "tool", 0) or None
    try:
        ai = services.ai_for(FEATURE_ID, context.project, tool)
    except CockpitError as exc:                          # zum Beispiel Tresor gesperrt
        log.info("README-Prüfung ohne KI: %s", exc.message)
        return None
    if ai is None:
        return None
    if not ai.is_local and not services.ai_tools.consent_given(FEATURE_ID, ai.name):
        agreed = context.ask(ConfirmQuestion(
            "KI außerhalb Ihres Rechners",
            f"Für die Prüfung der README gehen die Liste der geänderten Dateien, ein Überblick "
            f"der Änderungen und die README an {ai.name}. Diese KI läuft außerhalb Ihres "
            "Rechners. Einverstanden?", yes="Einverstanden", no="Nicht senden"))
        if not agreed:
            return None
        services.ai_tools.give_consent(FEATURE_ID, ai.name)
    return ai


def check(context: FlowContext) -> StepResult:
    services, project = context.services, context.project
    if services is None or not _setting(services, "check_on_upload", True):
        return StepResult(True)
    code_dir = project.code_dir
    path = code_dir / "README.md"
    if not path.is_file():
        return StepResult(True)
    changed = sync.changes(code_dir).files
    code_changes = [f for f in changed if not f.split("/")[-1].upper().startswith("README")
                    and f.split("/")[-1] != "cockpit.toml"]
    if not code_changes:
        return StepResult(True)          # nichts, nur die README oder nur Einstellungen geändert
    ai = _ai(context)
    if ai is None:
        return StepResult(True)
    context.status("Die KI prüft die README.")
    from cockpit.ai import prompt_files
    from cockpit.features.ai_assistant.context import filter_diff, redact
    readme = doc.parse(path.read_text(encoding="utf-8"))
    sections = "\n\n".join(f"## {p.title}\n{p.body}" for p in readme.parts)
    stat = git.run(["diff", "--stat", "HEAD"], code_dir, check=False).stdout
    diff = redact(filter_diff(git.run(["diff", "HEAD"], code_dir, check=False).stdout))
    budget = max(1000, ai.max_chars - len(sections) - 1500)
    prompt = prompt_files.fill(prompt_files.load("readme_check"),
                               nachricht=context.data.get("message", "") or "keine",
                               dateien="\n".join(changed[:80]),
                               aenderungen=(stat + "\n" + diff)[:budget], readme=sections)
    try:
        answer = ai.ask(prompt, prompt_files.load("readme_check_system"), context.cancel_event)
    except CockpitError as exc:
        return StepResult(True, f"README nicht geprüft: {exc.message}")
    taken = 0
    backup_done = False
    for title, reason, text in content.parse_check(answer):
        part = next((p for p in readme.parts if p.title.lower() == title.lower()), None)
        if part is None:
            continue
        own = doc.is_own(code_dir, "README.md", part)
        label = (f"Vorschlag der KI für „{part.title}“: {reason}"
                 + (" Diesen Abschnitt haben Sie selbst geschrieben." if own else "")
                 + " OK übernimmt den Text, auch angepasst. Abbrechen überspringt.")
        new = context.ask(TextQuestion(f"README: {part.title}", label, text, multiline=True))
        if not new or not str(new).strip():
            continue
        if not backup_done:
            folder = backups.new_backup_dir(project.name, "README vor der Prüfung", code_dir)
            shutil.copy2(path, folder / path.name)
            backup_done = True
        part.body = str(new).strip()
        path.write_text(readme.text(), encoding="utf-8")
        if part.key and not own:
            doc.remember(code_dir, "README.md", part.key, part.body)
        taken += 1
    return StepResult(True, "README angepasst." if taken else "")
