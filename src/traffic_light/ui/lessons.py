"""Guided lessons: short classroom cards that point at the live simulator.

Content is data (LESSONS), not hardcoded widgets — the viewer renders one
card at a time with prev/next and a picker. English source strings are
translated at display time via the viewer's tr() (context LessonViewer).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

LESSONS = [
    {
        "id": "cycle_anatomy",
        "title": "Anatomy of a cycle",
        "body": "A timing plan is a loop of phases. Each phase sets the NS and "
        "EW signals and lasts a fixed number of seconds: green, amber, a "
        "short all-red clearance, then the other axis gets its turn.",
        "try": "Watch one full cycle on the canvas and count the phases — "
        "the Default plan has 6.",
    },
    {
        "id": "amber_too_short",
        "title": "Why amber can't be too short",
        "body": "Amber is the warning that green is ending. If it is shorter "
        "than one second, drivers cannot react safely — so the plan editor "
        "validates every phase and refuses unsafe plans.",
        "try": "Open the plan editor and set an amber phase to 0.5 s. The "
        "Apply button stays disabled and tells you why.",
    },
    {
        "id": "rush_hour",
        "title": "Rush hour vs default",
        "body": "When one axis carries more traffic, it needs more green "
        "time. The Rush hour preset gives the NS axis 35 s of green; the EW "
        "axis only 15 s.",
        "try": "Switch presets from the combo and watch how the car queues "
        "grow and drain differently on each axis.",
    },
    {
        "id": "pedestrians",
        "title": "Pedestrian demand",
        "body": "Pedestrians may only cross a road while its traffic is "
        "stopped. A button press is remembered as demand, and the WALK "
        "window opens at the start of the next phase where that road is red.",
        "try": "Press Pedestrian EW, then watch the crossing signals turn "
        "green the next time EW traffic is stopped.",
    },
]


class LessonViewer(QDialog):
    """Non-modal card viewer for the built-in lessons."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Lessons"))
        self.setModal(False)
        self._index = 0

        layout = QVBoxLayout(self)
        self.picker = QComboBox()
        self.picker.setAccessibleName(self.tr("Choose a lesson"))
        for lesson in LESSONS:
            self.picker.addItem(self.tr(lesson["title"]))
        self.picker.activated.connect(self._show)
        layout.addWidget(self.picker)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 700;")
        self.title_label.setAccessibleName(self.tr("Lesson title"))
        layout.addWidget(self.title_label)

        self.body_label = QLabel()
        self.body_label.setWordWrap(True)
        self.body_label.setMinimumWidth(380)
        layout.addWidget(self.body_label)

        self.try_label = QLabel()
        self.try_label.setWordWrap(True)
        self.try_label.setAccessibleName(self.tr("Try it yourself"))
        layout.addWidget(self.try_label)

        nav = QHBoxLayout()
        self.prev_button = QPushButton(self.tr("Previous"))
        self.prev_button.clicked.connect(self._previous)
        self.next_button = QPushButton(self.tr("Next"))
        self.next_button.clicked.connect(self._next)
        self.position_label = QLabel()
        nav.addWidget(self.prev_button)
        nav.addWidget(self.next_button)
        nav.addStretch(1)
        nav.addWidget(self.position_label)
        layout.addLayout(nav)

        self._show(0)

    def _show(self, index: int) -> None:
        self._index = max(0, min(index, len(LESSONS) - 1))
        lesson = LESSONS[self._index]
        if self.picker.currentIndex() != self._index:
            self.picker.setCurrentIndex(self._index)
        self.title_label.setText(self.tr(lesson["title"]))
        self.body_label.setText(self.tr(lesson["body"]))
        self.try_label.setText(self.tr("Try it: {instruction}").format(
            instruction=self.tr(lesson["try"])
        ))
        self.position_label.setText(
            self.tr("Lesson {n} of {total}").format(
                n=self._index + 1, total=len(LESSONS)
            )
        )
        self.prev_button.setEnabled(self._index > 0)
        self.next_button.setEnabled(self._index < len(LESSONS) - 1)

    def _previous(self) -> None:
        self._show(self._index - 1)

    def _next(self) -> None:
        self._show(self._index + 1)
