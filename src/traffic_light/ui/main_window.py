"""Main window. Phase 1: scaffold shell — simulator canvas lands in Phase 2."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QMainWindow, QWidget

from . import settings as prefs


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(self.tr("Traffic Light"))
        self.resize(1024, 720)

        placeholder = QLabel(self.tr("Simulator canvas — coming in Phase 2"))
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(placeholder)

        view_menu = self.menuBar().addMenu(self.tr("&View"))
        for name in prefs.THEMES:
            action = QAction(prefs.THEMES[name], self, checkable=True)
            action.setChecked(prefs.theme() == name)
            action.triggered.connect(lambda _=False, t=name: self.apply_theme(t))
            view_menu.addAction(action)

    def apply_theme(self, name: str) -> None:
        from . import theme

        prefs.set_theme(name)
        self.window().setStyleSheet(theme.stylesheet(name))
