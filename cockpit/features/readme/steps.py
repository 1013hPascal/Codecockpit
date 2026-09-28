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


class _Editor:
    """Übernimmt bestätigte Abschnitte in README.md. Vor der ersten Änderung eine Sicherheitskopie."""

    def __init__(self, context: FlowContext) -> None:
        self.context = context
        self.code_dir = context.project.code_dir
        self.path = self.code_dir / "README.md"
        self.readme = doc.parse(self.path.read_text(encoding="utf-8"))
        self.backup_done = False
        self.taken = 0

    def offer(self, key: str, title: str, reason: str, text: str) -> None:
        """Vorschlag als Textfrage: OK übernimmt, auch angepasst. Abbrechen überspringt."""
        part = next((p for p in self.readme.parts if p.title.lower() == title.lower()), None)
        own = part is not None and doc.is_own(self.code_dir, "README.md", part)
        label = (f"Vorschlag der KI für „{title}“: {reason}"
                 + (" Diesen Abschnitt haben Sie selbst geschrieben." if own else "")
                 + " OK übernimmt den Text, auch angepasst. Abbrechen überspringt.")
        new = self.context.ask(TextQuestion(f"README: {title}", label, text, multiline=True))
        if not new or not str(new).strip():
            return
        if not self.backup_done:
            project = self.context.project
            folder = backups.new_backup_dir(project.name, "README vor der Prüfung", self.code_dir)
            shutil.copy2(self.path, folder / self.path.name)
            self.backup_done = True
        key = key or (part.key if part is not None else "")
        if part is not None:
            part.body = str(new).strip()
        elif key:
            self.readme.put(key, title, str(new))
        else:
            return
        self.path.write_text(self.readme.text(), encoding="utf-8")
        body = self.readme.find(key).body if key and self.readme.find(key) else ""
        if key and not own and body:
            doc.remember(self.code_dir, "README.md", key, body)
        self.taken += 1


def _changes_proposal(context: FlowContext, version: str) -> tuple[str, str] | None:
    """Abschnitt Änderungen mit der neuen Version (Wunsch des Nutzers zu Phase 9): die Commits
    seit der letzten Version und die Nachricht dieses Commits."""
    from datetime import date

    from cockpit.features.readme.plan import enabled_keys, languages
    from cockpit.features.versions import versions
    services = context.services
    if "changes" not in enabled_keys(services):
        return None
    code_dir = context.project.code_dir
    last = versions.current(code_dir)
    since = f"v{last}..HEAD" if last else "HEAD"
    subjects = [s for s in git.run(["log", "--format=%s", "--no-merges", since], code_dir,
                                   check=False).stdout.splitlines() if s.strip()]
    message = (context.data.get("message") or "").strip().splitlines()
    if message and message[0] not in subjects:
        subjects.insert(0, message[0])
    released = versions.Released(version, f"{date.today():%d.%m.%Y}", subjects)
    main_code, _codes = languages(services, code_dir)
    facts = content.Facts(context.project.name,
                          releases=[released] + versions.history(code_dir, limit=2))
    text = content.fixed("changes", facts, main_code if main_code in ("en", "de") else "en")
    return doc.heading("changes", main_code), text


def check(context: FlowContext) -> StepResult:
    """Läuft nach der Frage nach der Version. Bei einer neuen Version immer (Wunsch des Nutzers
    zu Phase 9), sonst nur, wenn die Prüfung eingeschaltet ist und sich Code geändert hat."""
    services, project = context.services, context.project
    if services is None:
        return StepResult(True)
    code_dir = project.code_dir
    path = code_dir / "README.md"
    if not path.is_file():
        return StepResult(True)
    version = context.data.get("version", "")
    changed = sync.changes(code_dir).files
    code_changes = [f for f in changed if not f.split("/")[-1].upper().startswith("README")
                    and f.split("/")[-1] != "cockpit.toml"]
    if not version and (not _setting(services, "check_on_upload", True) or not code_changes):
        return StepResult(True)          # nichts, nur die README oder nur Einstellungen geändert
    editor = _Editor(context)
    if version:
        proposal = _changes_proposal(context, version)
        if proposal is not None:
            title, text = proposal
            existing = editor.readme.find("changes")
            editor.offer("changes", existing.title if existing else title,
                         f"Version {version} kommt dazu.", text)
    ai = _ai(context)
    if ai is None:
        return StepResult(True, "README angepasst." if editor.taken else "")
    context.status("Die KI prüft die README.")
    from cockpit.ai import prompt_files
    from cockpit.features.ai_assistant.context import filter_diff, redact
    sections = "\n\n".join(f"## {p.title}\n{p.body}" for p in editor.readme.parts
                           if p.key != "changes")
    stat = git.run(["diff", "--stat", "HEAD"], code_dir, check=False).stdout
    diff = redact(filter_diff(git.run(["diff", "HEAD"], code_dir, check=False).stdout))
    if version:
        from cockpit.features.versions import versions
        last = versions.current(code_dir)
        log = git.run(["log", "--format=%s", "--no-merges", f"v{last}..HEAD" if last else "HEAD"],
                      code_dir, check=False).stdout
        stat = f"Commits seit der letzten Version:\n{log}\n{stat}"
    budget = max(1000, ai.max_chars - len(sections) - 1500)
    prompt = prompt_files.fill(prompt_files.load("readme_check"),
                               nachricht=context.data.get("message", "") or "keine",
                               version=f"Neue Version {version}." if version else "Keine.",
                               dateien="\n".join(changed[:80]) or "keine",
                               aenderungen=(stat + "\n" + diff)[:budget], readme=sections)
    try:
        answer = ai.ask(prompt, prompt_files.load("readme_check_system"), context.cancel_event)
    except CockpitError as exc:
        return StepResult(True, f"README nicht geprüft: {exc.message}")
    for title, reason, text in content.parse_check(answer):
        if next((p for p in editor.readme.parts if p.title.lower() == title.lower()), None):
            editor.offer("", title, reason, text)
    return StepResult(True, "README angepasst." if editor.taken else "")
