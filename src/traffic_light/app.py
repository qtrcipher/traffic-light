"""Application entry point: language, RTL, theme, translator, main window."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QTimer, QTranslator, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

# Absolute imports (not `from .ui import ...`): PyInstaller runs this file as
# __main__, where package-relative imports fail. They work identically for
# `python -m traffic_light.app` and the console script.
from traffic_light.ui import settings as prefs
from traffic_light.ui import theme
from traffic_light.ui.guide import GuideDialog, should_show_guide
from traffic_light.ui.language_dialog import LanguageDialog
from traffic_light.ui.main_window import MainWindow

APP_NAME = "Traffic Light"


def _resource(*parts: str) -> Path:
    """Path to bundled package data. Inside a PyInstaller one-file bundle the
    datas land under sys._MEIPASS/traffic_light; from source they live next to
    this file."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS) / "traffic_light"  # noqa: SLF001
    else:
        base = Path(__file__).resolve().parent
    return base.joinpath(*parts)


def _load_translator(app: QApplication, language: str) -> QTranslator | None:
    """Install the .qm for `language` if one has been compiled. No-op otherwise
    (source strings are English, so EN needs nothing)."""
    if language == "en":
        return None
    qm = _resource("i18n", f"traffic_light_{language}.qm")
    if not qm.is_file():
        return None
    translator = QTranslator(app)
    if not translator.load(str(qm)):
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
    language_known = prefs.language() is not None
    app = create_app(sys.argv)
    app.setWindowIcon(QIcon(str(_resource("assets", "icon.svg"))))
    window = MainWindow()
    window.show()

    # Smoke-test hook: TRAFFIC_LIGHT_SHOT=/path/out.png grabs the window after
    # 2 s and quits (used to verify frozen builds headlessly).
    shot = os.environ.get("TRAFFIC_LIGHT_SHOT")
    if shot:
        QTimer.singleShot(2000, lambda: (window.grab().save(shot), app.quit()))

    if should_show_guide(language_known):
        GuideDialog(window).exec()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
