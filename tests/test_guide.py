"""Quick guide (onboarding) tests."""

from __future__ import annotations

from traffic_light.ui import settings as prefs
from traffic_light.ui.guide import GuideDialog, should_show_guide
from traffic_light.ui.main_window import MainWindow


def test_guide_not_dismissed_by_default():
    assert prefs.guide_dismissed() is False


def test_dismissal_persists():
    prefs.set_guide_dismissed(True)
    assert prefs.guide_dismissed() is True


def test_should_show_guide_only_after_language_chosen():
    assert should_show_guide(language_known=False) is False
    assert should_show_guide(language_known=True) is True
    prefs.set_guide_dismissed(True)
    assert should_show_guide(language_known=True) is False


def test_close_without_checkbox_keeps_guide_enabled(qtbot):
    dialog = GuideDialog()
    qtbot.addWidget(dialog)
    dialog.accept()
    assert prefs.guide_dismissed() is False


def test_checkbox_dismisses_guide(qtbot):
    dialog = GuideDialog()
    qtbot.addWidget(dialog)
    dialog.dont_show.setChecked(True)
    dialog.accept()
    assert prefs.guide_dismissed() is True


def test_guide_lists_shortcuts(qtbot):
    from PySide6.QtWidgets import QLabel

    dialog = GuideDialog()
    qtbot.addWidget(dialog)
    texts = [label.text() for label in dialog.findChildren(QLabel)]
    joined = "\n".join(texts)
    for keyword in ("Space", "F11", "Esc", "Plan editor", "Save plan"):
        assert keyword in joined


def test_help_menu_offers_guide_and_about(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    help_menu = None
    for action in window.menuBar().actions():
        if action.text() == "&Help":
            help_menu = action.menu()
    assert help_menu is not None
    labels = [a.text() for a in help_menu.actions()]
    assert "Quick guide" in labels
    assert "About Traffic Light" in labels
