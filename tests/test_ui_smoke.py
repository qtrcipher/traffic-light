"""UI smoke tests — run under xvfb (Docker/CI) or a real display."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QDialog

from traffic_light.ui import settings as prefs
from traffic_light.ui.language_dialog import LanguageDialog
from traffic_light.ui.main_window import MainWindow


@pytest.fixture(autouse=True)
def clean_settings(tmp_path, monkeypatch):
    """Isolate QSettings so tests never touch the developer's real settings."""
    from PySide6.QtCore import QSettings

    monkeypatch.setattr(
        prefs, "settings", lambda: QSettings(str(tmp_path / "test.ini"), QSettings.Format.IniFormat)
    )


def test_language_picker_persists_choice(qtbot):
    dialog = LanguageDialog()
    qtbot.addWidget(dialog)
    dialog._pick("ar")
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert prefs.language() == "ar"


def test_language_unset_by_default():
    assert prefs.language() is None


def test_theme_defaults_to_light_and_persists(qtbot):
    assert prefs.theme() == "light"
    prefs.set_theme("dark")
    assert prefs.theme() == "dark"


def test_main_window_shows(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert window.isVisible()
    assert window.windowTitle() == "Traffic Light"
