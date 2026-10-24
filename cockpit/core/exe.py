"""Die Exe eines Projekts (Konzept 10.4, Phase 10).

Zustand im Git-Ordner des Projekts, Datei codecockpit-exe.toml (seit 10g, vorher in
Repository\\cockpit.toml, Abschnitt [exe]; ohne Git weiter dort): woher die Exe kommt ("cockpit": vom Cockpit
erstellt, "extern": extern erstellt und von Hand gewählt, "release": aus einem Release), wann, aus
welchem Commit und mit welcher Version. Die Einstellungen zum Bauen stehen unter [exe.build].

Grundsätze:
- Jede Exe hat im Ordner Release einen eigenen Ordner (Wunsch des Nutzers vom 03.10.2026), zum
  Beispiel Release\\VokabelApp und Release\\VokabelApp_branch_Cockpit-exe-bauen. Darin liegen die Exe,
  README, Lizenz und die Ordner neben der Exe.
- README und Lizenz liegen immer neben der Exe und sind immer die aktuellen aus dem Code.
- Die aktuelle Exe liegt immer im festen Ordner, zum Beispiel Release\\VokabelApp. Nach dem
  Veröffentlichen steht darin version.txt. Ersetzt eine neue Exe eine veröffentlichte, heißt deren
  Ordner danach VokabelApp-v1.2.0. Die letzten zwei alten Versionen bleiben so liegen, ältere kommen
  in die Sicherheitskopien (Wünsche des Nutzers vom 04.10. und 20.10.2026).
- Eine bisherige Exe kommt immer erst in eine Sicherheitskopie, bevor eine neue sie ersetzt.
- Eine neu gebaute Exe ersetzt die alte erst, wenn sie den Test bestanden hat.
- Das Cockpit selbst kann seine laufende Exe nicht ersetzen. Die neue Exe wartet dann in Release\\_neu
  und wird beim Neustart übernommen.
"""
from __future__ import annotations

import logging
import os
import shutil  # noqa: F401  (Tests ersetzen exe.shutil.move und exe.shutil.which)
import subprocess  # noqa: F401  (Tests ersetzen exe.subprocess.run und Popen)
import tempfile
import threading
from pathlib import Path
from typing import Callable

from cockpit.core import backups, paths
from cockpit.core.errors import CockpitError
from cockpit.core.projects import Project
# Aufgeteilt am 21.10.2026: Bericht und Veröffentlichen stehen in eigenen Dateien. Die Namen
# bleiben hier erreichbar, für den Code im Cockpit und für die Tests.
from cockpit.core.exe_publish import (  # noqa: F401
    asset_for_upload, asset_name, check_version, mark_published, next_version, pick_asset, unpack)
from cockpit.core.exe_report import (  # noqa: F401
    WHEEL_REPLACEMENTS, BuildFacts, advice, build_report, failed_package, first_error,
    missing_modules, python_version, replacement_for)
# Aufgeteilt am 22.10.2026: Zustand, Ordner, Python, spec-Datei, Ersetzen und Neustart stehen in
# eigenen Dateien. Die Namen bleiben hier erreichbar, für den Code im Cockpit und für die Tests.
from cockpit.core.exe_state import (  # noqa: F401
    BLOCKED, BRANCH_MARK, BlockedByWindows, BuildSettings, EXE_GUIDE, ExeRecord, FLAGS, LOCKED,
    PENDING, PYTHON_GUIDE, RECORD_FILE, VERSION_FILE, _VERSION_HOME, branch_exe_name, build_state,
    current_exe, exe_in, folder_version, head_commit, home_name, is_blocked, is_branch_exe,
    is_cockpit, looks_blocked, now, publish_state, read_record, read_settings, running_from,
    status_line, write_record, write_settings)
from cockpit.core.exe_folders import (  # noqa: F401
    _make_room, add_exe_dir, adopt, backup_current, beside_names, doc_files, is_doc, is_readme, loose_items,
    missing_docs, place_beside, prune_versions, release_docs, retire_home, tidy_release)
from cockpit.core.exe_python import (  # noqa: F401
    LONG_PATHS, NO_PYTHON, PIP_HINT, PythonInstall, build_venv, choose_python, find_python,
    find_pythons, missing_wheels, prepare_venv, python_in, run_process, venv_python, venv_version)
from cockpit.core.exe_spec import change_settings, ensure_spec, own_spec, spec_text  # noqa: F401
from cockpit.core.exe_install import (  # noqa: F401
    BuildResult, QUICK_EXIT, branch_home, discard, install, install_branch, install_untested,
    promote_branch, pyinstaller_build, stage_beside, start_test, unstage)
from cockpit.core.exe_restart import (  # noqa: F401
    clean_environment, launch_restart, restart_script, swap_script)

log = logging.getLogger(__name__)


# -- Bauen, testen, ersetzen ----------------------------------------------------------------------
STEPS = ("Virtuelle Umgebung und Bibliotheken werden vorbereitet", "Exe wird gebaut",
         "Exe wird getestet", "Exe wird übernommen")


def build(project: Project, settings: BuildSettings, on_status: Callable[[str], None],
          on_line: Callable[[str], None], cancel: threading.Event | None = None,
          branch_dir: Path | None = None, branch_name: str = "",
          keep_failed: bool = False) -> BuildResult:
    """Der ganze Ablauf, blockiert. on_status bekommt "Schritt 1 von 4: …".
    branch_dir: aus diesem Branch-Ordner bauen (Phase 10f). Die Exe heißt dann
    <Name>_branch_<Ordner>.exe und kommt neben die normale. branch_name ersetzt den Ordner im
    Namen, zum Beispiel wenn der Ordner Repository selbst auf dem Branch steht.
    keep_failed: Besteht die Exe den Test nicht, kein Fehler, sondern ein Ergebnis mit untested
    und test_error. Der Nutzer entscheidet dann, ob er sie trotzdem behält (Wunsch des Nutzers
    vom 11.10.2026)."""
    code_dir = branch_dir or project.code_dir
    folder = (branch_name or branch_dir.name) if branch_dir is not None else ""
    # Für den Bericht bei einem Fehler (Wunsch des Nutzers vom 14.10.2026)
    facts = BuildFacts(project, folder)
    output: list[str] = []

    def line(text: str) -> None:
        output.append(text)
        del output[:-200]
        on_line(text)

    def step(number: int) -> None:
        facts.step = number
        on_status(f"Schritt {number} von {len(STEPS)}: {STEPS[number - 1]}")

    def with_report(exc: CockpitError) -> CockpitError:
        exc.details = "\n".join(p for p in [exc.details, *build_report(
            facts, exc.message, exc.details, output)] if p)
        return exc

    commit = head_commit(code_dir)
    step(1)
    try:
        python = prepare_venv(code_dir, line, cancel, venv=build_venv(project, code_dir),
                              python_wanted=settings.python)
    except CockpitError as exc:
        raise with_report(exc) from None
    # Probelauf (21.10.2026): Syntaxfehler und fehlende Bibliotheken in Sekunden statt Minuten
    from cockpit.core import exe_probe
    line("Probelauf: Code und Bibliotheken werden geprüft.")
    checked = exe_probe.probe(python, code_dir, settings.start_file, cancel)
    failed = exe_probe.problem(checked)
    if failed is not None:
        for text in checked.lines():
            line(text)
        raise with_report(failed)
    if checked.files:
        line(f"Probelauf bestanden, {checked.files} Dateien geprüft.")
    spec = ensure_spec(code_dir, settings)
    work = Path(tempfile.mkdtemp(prefix="codecockpit-exe-", dir=paths.cache_dir()))
    keep = False
    try:
        step(2)
        try:
            built = pyinstaller_build(code_dir, python, spec, work, line, cancel)
        except CockpitError as exc:
            raise with_report(exc) from None
        facts.built = exe_in(built)
        facts.missing = missing_modules(work, code_dir)
        if facts.missing:
            line(f"Achtung: PyInstaller hat diese Bibliotheken nicht gefunden, der Code "
                 f"importiert sie aber: {', '.join(facts.missing)}. Sie fehlen in der Exe.")
        step(3)
        staged = stage_beside(built, list(settings.beside) + [
            n for n in doc_files(code_dir) if n not in settings.beside], code_dir)
        try:
            line(start_test(exe_in(built), settings.test_seconds, settings.self_test,
                            cancel, settings.windowed))
        except BlockedByWindows as exc:
            # Der Nutzer entscheidet in der Oberfläche, ob er selbst prüft (install_untested)
            keep = True
            facts.blocked = True
            return BuildResult(exe_in(built), untested=True, built=built, work=work,
                               commit=commit, branch=folder,
                               report=build_report(facts, exc.message, exc.details, output))
        except CockpitError as exc:
            if not keep_failed:
                raise with_report(exc) from None
            keep = True
            return BuildResult(exe_in(built), untested=True, built=built, work=work,
                               commit=commit, branch=folder, test_error=exc.message,
                               test_details=exc.details,
                               report=build_report(facts, exc.message, exc.details, output))
        finally:
            unstage(staged)
        facts.tested = True
        step(4)
        try:
            if folder:
                return install_branch(project, built, folder, settings, code_dir)
            return install(project, built, commit)
        except CockpitError as exc:
            raise with_report(exc) from None
    finally:
        if not keep:
            backups.remove_tree(work)


