"""Quick guide dialog: keyboard shortcuts and where the plan tools live.

Shown automatically at launch once the language has been chosen (i.e. from the
second launch on) until the user checks "Don't show again"; always re-openable
from the Help menu. The dismissal flag persists via ui/settings.
"""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QLabel, QPushButton, QVBoxLayout

from . import settings as prefs

_TIPS = (
    "Space — play / pause the simulation",
    "F11 — presentation mode (fullscreen for the classroom)",
    "Esc — leave presentation mode",
    "Plan editor… — edit phases and durations (toolbar)",
    "Save plan… / Load plan… — share plans as JSON files (toolbar)",
)


def should_show_guide(language_known: bool) -> bool:
    """Auto-show at launch only after the language picker has run (second
    launch onward), and only until the user dismisses the guide."""
    return language_known and not prefs.guide_dismissed()


class GuideDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Quick guide"))
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("A quick tour of the controls:")))
        for tip in _TIPS:
            layout.addWidget(QLabel(self.tr(tip)))

        self.dont_show = QCheckBox(self.tr("Don't show again"))
        layout.addWidget(self.dont_show)

        self.close_button = QPushButton(self.tr("Close"))
        self.close_button.setDefault(True)
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)

    def done(self, result: int) -> None:
        if self.dont_show.isChecked():
            prefs.set_guide_dismissed(True)
        super().done(result)
