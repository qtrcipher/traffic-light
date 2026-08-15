"""First-launch language picker (EN/AR), shown once, persisted via QSettings."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from . import settings as prefs


class LanguageDialog(QDialog):
    """Modal picker with one button per language. Result via .chosen."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.chosen: str | None = None
        self.setWindowTitle("Language / اللغة")
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choose your language\nاختر لغتك"))

        row = QHBoxLayout()
        for code, label in prefs.LANGUAGES.items():
            button = QPushButton(label)
            button.setMinimumSize(120, 48)
            button.clicked.connect(lambda _=False, c=code: self._pick(c))
            row.addWidget(button)
        layout.addLayout(row)

    def _pick(self, code: str) -> None:
        self.chosen = code
        prefs.set_language(code)
        self.accept()
