"""Application entry point: language, RTL, theme, translator, main window."""

from __future__ import annotations

import sys
from importlib import resources

from PySide6.QtCore import QLocale, QTranslator, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .ui import settings as prefs
from .ui import theme
from .ui.language_dialog import LanguageDialog
from .ui.main_window import MainWindow

APP_NAME = "Traffic Light"


def _load_translator(app: QApplication, language: str) -> QTranslator | None:
    """Install the .qm for `language` if one has been compiled. No-op otherwise
    (source strings are English, so EN needs nothing)."""
    if language == "en":
        return None
    qm = resources.files("traffic_light.i18n") / f"traffic_light_{language}.qm"
    if not qm.is_file():
        return None
    translator = QTranslator(app)
    with resources.as_file(qm) as path:
        if not translator.load(str(path)):
            return None
    app.installTranslator(translator)
    return translator  # keep a reference alive


def create_app(argv: list[str]) -> QApplication:
    app = QApplication(argv)
    app.setApplicationName(APP_NAME)

    language = prefs.language()
    if language is None:
        dialog = LanguageDialog()
        dialog.exec()
        language = dialog.chosen or "en"

    QLocale.setDefault(QLocale(language))
    if language == "ar":
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    app._translator = _load_translator(app, language)  # noqa: SLF001
    app.setStyleSheet(theme.stylesheet(prefs.theme()))
    return app


def main() -> int:
    app = create_app(sys.argv)
    icon = resources.files("traffic_light") / "assets" / "icon.svg"
    with resources.as_file(icon) as icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
