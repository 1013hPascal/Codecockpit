"""CodeCockpit starten: python main.py (mit Testdaten: python main.py --testdaten)."""
from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QLibraryInfo, QLocale, QTimer, QTranslator
from PySide6.QtWidgets import QApplication

from cockpit import APP_NAME, __version__, testdata
from cockpit.core import paths
from cockpit.core.logging_setup import setup_logging
from cockpit.core.services import Services
from cockpit.ui.main_window import MainWindow

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
    projects_root = None
    if use_testdata:
        _, projects_root = testdata.prepare()

    setup_logging(paths.logs_dir())
    log.info("%s %s startet%s", APP_NAME, __version__, " mit Testdaten" if use_testdata else "")

    app = QApplication(sys.argv[:1])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    _german_qt(app)

    services = Services.create(paths.database_path())
    if projects_root is not None:
        services.settings.update(projects_root=str(projects_root))
        services.projects.scan(projects_root)
        testdata.remove_missing_example(projects_root)

    window = MainWindow(services, testdata=use_testdata)
    window.showMaximized()
    window.initial_focus()
    QTimer.singleShot(300, window.startup)
    if "--selbsttest" in args:
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
