"""CodeCockpit starten: python main.py

Optionen:
  --testdaten   mit Beispielprojekten und Testkonto in einem eigenen Datenordner
  --selbsttest  kurz starten und mit Code 0 beenden, ohne Einrichtung und ohne Rückfragen
"""
from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QLibraryInfo, QLocale, QTimer, QTranslator
from PySide6.QtWidgets import QApplication

from cockpit import APP_NAME, __version__, testdata, testdata_platform
from cockpit.core import paths
from cockpit.core.errors import CockpitError
from cockpit.core.logging_setup import setup_logging
from cockpit.core.services import Services
from cockpit.ui.error_dialog import show_error
from cockpit.ui.main_window import MainWindow
from cockpit.ui.setup_wizard import SetupWizard

log = logging.getLogger("cockpit")


def _german_qt(app: QApplication) -> QTranslator:
    """Deutsche Texte für Qt-eigene Schaltflächen und Dialoge (zum Beispiel "Abbrechen")."""
    translator = QTranslator(app)
    folder = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load(QLocale(QLocale.Language.German), "qtbase", "_", folder):
        app.installTranslator(translator)
    return translator


def self_test_problems(services: Services) -> list[str]:
    """Prüft, ob alles Mitgelieferte da ist (wichtig in der Exe): Anleitungen, Prompts, Features."""
    from cockpit.ai import prompt_files
    problems = list(services.registry.load_errors)
    for guide in ("anleitungen/git-installieren.md", "anleitungen/exe-verstehen.md"):
        if not (paths.resource_dir() / guide).is_file():
            problems.append(f"Fehlt: {guide}")
    try:
        prompt_files.load("terminal_explain_system")
    except CockpitError as exc:
        problems.append(exc.message)
    for manifest in services.registry.all():
        if not manifest.introduction_text():
            problems.append(f"Einführung fehlt: {manifest.id}")
    return problems


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    use_testdata = "--testdaten" in args
    self_test = "--selbsttest" in args
    if self_test and not use_testdata:
        # Der Selbsttest (zum Beispiel nach dem Bau der Exe) berührt nie die echten Daten
        import os
        import tempfile
        os.environ["CODECOCKPIT_HOME"] = tempfile.mkdtemp(prefix="codecockpit-selbsttest-")
    projects_root = None
    app = QApplication(sys.argv[:1])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    _german_qt(app)
    if use_testdata:
        try:
            _, projects_root = testdata.prepare()
        except CockpitError as exc:
            show_error(None, APP_NAME, exc.message, exc.details)
            return 1

    setup_logging(paths.logs_dir())
    log.info("%s %s startet%s", APP_NAME, __version__, " mit Testdaten" if use_testdata else "")

    registry = None
    if use_testdata:
        # Beispiel-Features nur mit Testdaten (ENTSCHEIDUNGEN.md, Phase 7)
        from cockpit.core.features.registry import FeatureRegistry
        registry = FeatureRegistry(FeatureRegistry.discover().all()
                                   + FeatureRegistry.discover("cockpit.testdata_features").all())
    services = Services.create(paths.database_path(), registry=registry,
                               vault_service_name=testdata.VAULT_SERVICE if use_testdata
                               else "CodeCockpit")
    if projects_root is not None:
        services.settings.update(projects_root=str(projects_root))
        services.projects.scan(projects_root)
        testdata.remove_missing_example(projects_root)
        testdata_platform.register()

    if not self_test:
        # Erster Start: Einrichtung. Ohne Tresor geht es nicht weiter (Konzept 8.7).
        if not services.settings.load().setup_done:
            if not SetupWizard(services).exec():
                log.info("Einrichtung abgebrochen")
                services.close()
                return 0
        # Die Tresordatei bleibt beim Start gesperrt. Das Master-Passwort wird erst abgefragt,
        # wenn Zugangsdaten gebraucht werden (Wunsch des Nutzers, ENTSCHEIDUNGEN.md).

    window = MainWindow(services, testdata=use_testdata)
    window.showMaximized()
    window.initial_focus()
    QTimer.singleShot(300, window.startup)
    if self_test:
        # Selbsttest (Konzept 10.4): starten, kurz laufen lassen, mit Code 0 beenden
        def finish() -> None:
            problems = self_test_problems(services)
            log.info("Selbsttest: %s", " | ".join(problems or window.project_list.texts()))
            app.exit(0 if window.project_list.texts() and not problems else 1)
        QTimer.singleShot(1500, finish)
    code = app.exec()
    services.close()
    log.info("%s beendet", APP_NAME)
    return code


if __name__ == "__main__":
    sys.exit(main())
