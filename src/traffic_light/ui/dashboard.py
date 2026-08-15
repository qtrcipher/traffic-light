"""Status dashboard (pillar 2): a glanceable board mirroring the simulator.

Four large lamps (N/S/E/W) in the theme signal colors, plus the current phase
and elapsed time in classroom-legible type. Non-modal sibling window of the
simulator; consumes engine state as a HardwareSink via the StateBridge (lamps)
plus a per-tick ``update_status`` for the readout (same pattern as the panel).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QGridLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from ..core.engine import EngineState
from ..core.signal import SignalState
from . import theme

_HEAD_NAMES = {"N": "North", "S": "South", "E": "East", "W": "West"}
# 2x2 grid positions, compass-sensible: north top-left, south bottom-right.
_HEAD_CELLS = {"N": (0, 0), "E": (0, 1), "W": (1, 0), "S": (1, 1)}

_STATE_NAMES = {
    SignalState.RED: "red",
    SignalState.AMBER: "amber",
    SignalState.GREEN: "green",
    SignalState.OFF: "off",
}
_SIGNAL_COLORS = {
    SignalState.RED: theme.SIGNAL_RED,
    SignalState.AMBER: theme.SIGNAL_AMBER,
    SignalState.GREEN: theme.SIGNAL_GREEN,
}

_READOUT_PX = 36


class SignalLamp(QWidget):
    """One big rounded lamp: signal color when lit, dark housing when not."""

    def __init__(self, theme_name: str = "light", parent=None) -> None:
        super().__init__(parent)
        self._state = SignalState.OFF
        self._colors = theme.THEMES[theme_name]
        self.setMinimumSize(200, 200)

    def set_state(self, state: SignalState) -> None:
        if state is not self._state:
            self._state = state
            self.update()

    def set_theme(self, name: str) -> None:
        self._colors = theme.THEMES[name]
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(12, 12, -12, -12)
        if self._state is SignalState.OFF:
            color = QColor(self._colors["housing"])
        else:
            color = QColor(_SIGNAL_COLORS[self._state])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(rect, rect.width() / 6, rect.width() / 6)
        painter.end()


class DashboardWindow(QMainWindow):
    """HardwareSink consumer: four lamps + phase/elapsed readout."""

    closed = Signal()

    def __init__(self, theme_name: str = "light", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Status dashboard"))
        self.resize(720, 760)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        central = QWidget()
        layout = QVBoxLayout(central)
        grid = QGridLayout()
        self._lamps: dict[str, SignalLamp] = {}
        self._head_labels: dict[str, QLabel] = {}
        for head, (row, column) in _HEAD_CELLS.items():
            cell = QVBoxLayout()
            lamp = SignalLamp(theme_name)
            lamp.setAccessibleName(
                self.tr("{head} signal: {state}").format(
                    head=self.tr(_HEAD_NAMES[head]), state=self.tr("off")
                )
            )
            name = QLabel(self.tr(_HEAD_NAMES[head]))
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name.setStyleSheet(f"font-size: {_READOUT_PX}px; font-weight: 700;")
            cell.addWidget(lamp, 1)
            cell.addWidget(name)
            grid.addLayout(cell, row, column)
            self._lamps[head] = lamp
            self._head_labels[head] = name
        layout.addLayout(grid, 1)

        self.phase_label = QLabel()
        self.phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phase_label.setStyleSheet(f"font-size: {_READOUT_PX}px; font-weight: 700;")
        self.phase_label.setAccessibleName(self.tr("Current phase"))
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(f"font-size: {_READOUT_PX}px;")
        self.time_label.setAccessibleName(self.tr("Phase elapsed time"))
        layout.addWidget(self.phase_label)
        layout.addWidget(self.time_label)
        self.setCentralWidget(central)

    # HardwareSink ---------------------------------------------------------
    def on_state(self, heads: dict[str, SignalState]) -> None:
        for head, state in heads.items():
            lamp = self._lamps[head]
            lamp.set_state(state)
            lamp.setAccessibleName(
                self.tr("{head} signal: {state}").format(
                    head=self.tr(_HEAD_NAMES[head]),
                    state=self.tr(_STATE_NAMES[state]),
                )
            )

    def update_status(self, state: EngineState) -> None:
        self.phase_label.setText(
            self.tr("Phase {n} of {total}").format(
                n=state.phase_index + 1, total=state.phase_count
            )
        )
        self.time_label.setText(
            self.tr("{elapsed:.1f} s").format(elapsed=state.phase_elapsed_s)
        )

    def set_theme(self, name: str) -> None:
        for lamp in self._lamps.values():
            lamp.set_theme(name)

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        self.closed.emit()
        super().closeEvent(event)
