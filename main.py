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


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    use_testdata = "--testdaten" in args
    self_test = "--selbsttest" in args
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

    services = Services.create(paths.database_path(),
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
            log.info("Selbsttest: %s", " | ".join(window.project_list.texts()))
            app.exit(0 if window.project_list.texts() else 1)
        QTimer.singleShot(1500, finish)
    code = app.exec()
    services.close()
    log.info("%s beendet", APP_NAME)
    return code


if __name__ == "__main__":
    sys.exit(main())
