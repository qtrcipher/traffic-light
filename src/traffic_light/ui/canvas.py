"""Top-down 4-way intersection canvas. Renders engine state; owns no logic.

World coordinates are metres relative to the intersection centre; the engine's
per-approach distances (metres to the stop line) are mapped onto the four
approach lanes assuming right-hand traffic. Signal heads sit on the right-hand
corner of each approach, just before its stop line.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..core.engine import SimulationEngine
from ..core.signal import PedestrianState, SignalState
from ..core.traffic import CAR_LENGTH_M
from . import theme

_HALF_SPAN_M = 85.0  # metres visible from the centre to each canvas edge
_ROAD_HALF_WIDTH_M = 7.0  # two 3.5 m lanes per road
_LANE_OFFSET_M = 1.75
_CAR_WIDTH_M = 2.0
_HEAD_MARGIN_M = 1.2  # gap between road edge and signal head
_HEAD_HOUSING_M = (2.4, 7.2)  # width x length of a 3-lamp housing
_CROSSWALK_OFFSET_M = 2.5  # band centre this far outside the intersection edge
_PED_BOX_M = 1.8  # pedestrian signal box size

_SIGNAL_COLORS = {
    SignalState.RED: theme.SIGNAL_RED,
    SignalState.AMBER: theme.SIGNAL_AMBER,
    SignalState.GREEN: theme.SIGNAL_GREEN,
}

# Head position per approach: (dx, dy) in metres from the centre, vertical housing?
_HEAD_PLACEMENT = {
    "N": (-1.0, -1.0, True),  # top-left corner
    "S": (1.0, 1.0, True),  # bottom-right corner
    "E": (1.0, -1.0, False),  # top-right corner
    "W": (-1.0, 1.0, False),  # bottom-left corner
}


class IntersectionCanvas(QWidget):
    def __init__(
        self, engine: SimulationEngine, theme_name: str = "light", parent=None
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._colors = theme.THEMES[theme_name]
        self.setMinimumSize(480, 480)
        # Keyboard/screen-reader access: the canvas is focusable and carries a
        # live text description of the simulation (see update_a11y).
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(self.tr("Intersection canvas"))
        self._a11y_phase: tuple[int, int] | None = None

    def update_a11y(self, state) -> None:
        """Refresh the accessible description when the phase changes."""
        key = (state.phase_index, state.phase_count)
        if key != self._a11y_phase:
            self._a11y_phase = key
            self.setAccessibleDescription(
                self.tr("Phase {n} of {total}.").format(
                    n=state.phase_index + 1, total=state.phase_count
                )
            )

    def set_theme(self, name: str) -> None:
        self._colors = theme.THEMES[name]
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale = min(self.width(), self.height()) / (2 * _HALF_SPAN_M)
        cx, cy = self.width() / 2, self.height() / 2
        self._draw_roads(painter, cx, cy, scale)
        self._draw_crosswalks(painter, cx, cy, scale)
        self._draw_cars(painter, cx, cy, scale)
        self._draw_heads(painter, cx, cy, scale)
        self._draw_ped_signals(painter, cx, cy, scale)
        painter.end()

    def _draw_roads(self, p: QPainter, cx: float, cy: float, scale: float) -> None:
        road = QColor(self._colors["road"])
        half = _ROAD_HALF_WIDTH_M * scale
        p.fillRect(QRectF(cx - half, 0, 2 * half, self.height()), road)
        p.fillRect(QRectF(0, cy - half, self.width(), 2 * half), road)

        pen = QPen(QColor(self._colors["road_line"]))
        pen.setWidthF(max(1.5, 0.25 * scale))
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawLine(cx, 0, cx, cy - half)
        p.drawLine(cx, cy + half, cx, self.height())
        p.drawLine(0, cy, cx - half, cy)
        p.drawLine(cx + half, cy, self.width(), cy)

    def _draw_crosswalks(self, p: QPainter, cx: float, cy: float, scale: float) -> None:
        """Zebra stripes across each arm, just outside the stop line."""
        half = _ROAD_HALF_WIDTH_M
        band = _CROSSWALK_OFFSET_M  # stripe length along the road axis
        stripe = 1.6  # stripe width across the road
        gap = 1.6
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._colors["road_line"]))
        edges = {
            "N": (cx, cy - (half + band) * scale, True),
            "S": (cx, cy + (half + band) * scale, True),
            "E": (cx + (half + band) * scale, cy, False),
            "W": (cx - (half + band) * scale, cy, False),
        }
        for _, (ax, ay, vertical_arm) in edges.items():
            # Walk across the road width, painting one stripe per step.
            start = -half + 0.8
            while start + stripe <= half - 0.8:
                if vertical_arm:  # N/S arms: stripes are vertical bars
                    rect = QRectF(
                        ax + start * scale,
                        ay - (band / 2) * scale,
                        stripe * scale,
                        band * scale,
                    )
                else:  # E/W arms: horizontal bars
                    rect = QRectF(
                        ax - (band / 2) * scale,
                        ay + start * scale,
                        band * scale,
                        stripe * scale,
                    )
                p.drawRect(rect)
                start += stripe + gap

    def _draw_ped_signals(self, p: QPainter, cx: float, cy: float, scale: float) -> None:
        """Small pedestrian boxes at the crosswalk ends (WALK/DONT WALK)."""
        peds = self._engine.state.pedestrians
        half = _ROAD_HALF_WIDTH_M
        box = _PED_BOX_M * scale
        side = (half + 1.4) * scale
        # Just beyond the crosswalk band's outer edge, at the end OPPOSITE the
        # arm's vehicle head (heads own the near corners and would overlap).
        far = (half + _CROSSWALK_OFFSET_M + _PED_BOX_M) * scale
        placements = {
            "NS": [
                (cx + side, cy - far),  # N-arm crosswalk, east end
                (cx - side, cy + far),  # S-arm crosswalk, west end
            ],
            "EW": [
                (cx + far, cy + side),  # E-arm crosswalk, south end
                (cx - far, cy - side),  # W-arm crosswalk, north end
            ],
        }
        for axis, boxes in placements.items():
            walking = peds[axis] is PedestrianState.WALK
            for bx, by in boxes:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(self._colors["housing"]))
                rect = QRectF(bx - box / 2, by - box / 2, box, box)
                p.drawRoundedRect(rect, box / 4, box / 4)
                dot = box * 0.45
                color = theme.SIGNAL_GREEN if walking else theme.SIGNAL_RED
                p.setBrush(QColor(color))
                p.drawEllipse(QRectF(bx - dot / 2, by - dot / 2, dot, dot))

    def _draw_cars(self, p: QPainter, cx: float, cy: float, scale: float) -> None:
        edge = _ROAD_HALF_WIDTH_M
        lane = _LANE_OFFSET_M
        p.setPen(Qt.PenStyle.NoPen)
        length = CAR_LENGTH_M * scale
        width = _CAR_WIDTH_M * scale
        radius = width / 3
        for car in self._engine.state.cars:
            d = car.distance_m
            if car.approach == "N":  # enters from the top, drives down
                x, y, vertical = cx - lane * scale, cy - (edge + d) * scale, True
            elif car.approach == "S":  # from the bottom, drives up
                x, y, vertical = cx + lane * scale, cy + (edge + d) * scale, True
            elif car.approach == "E":  # from the right, drives left
                x, y, vertical = cx + (edge + d) * scale, cy - lane * scale, False
            else:  # "W": from the left, drives right
                x, y, vertical = cx - (edge + d) * scale, cy + lane * scale, False
            color = QColor(theme.CAR_COLORS[car.color_index % len(theme.CAR_COLORS)])
            p.setBrush(color)
            if vertical:
                rect = QRectF(x - width / 2, y - length / 2, width, length)
            else:
                rect = QRectF(x - length / 2, y - width / 2, length, width)
            p.drawRoundedRect(rect, radius, radius)

    def _draw_heads(self, p: QPainter, cx: float, cy: float, scale: float) -> None:
        heads = self._engine.state.heads
        offset = (_ROAD_HALF_WIDTH_M + _HEAD_MARGIN_M) * scale
        for approach, (sx, sy, vertical) in _HEAD_PLACEMENT.items():
            self._draw_head(
                p, cx + sx * offset, cy + sy * offset, scale, vertical, heads[approach]
            )

    def _draw_head(
        self,
        p: QPainter,
        x: float,
        y: float,
        scale: float,
        vertical: bool,
        state: SignalState,
    ) -> None:
        w_m, l_m = _HEAD_HOUSING_M
        w, length = w_m * scale, l_m * scale
        if vertical:
            housing = QRectF(x - w / 2, y - length / 2, w, length)
        else:
            housing = QRectF(x - length / 2, y - w / 2, length, w)
        housing_color = QColor(self._colors["housing"])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(housing_color)
        p.drawRoundedRect(housing, w / 2.5, w / 2.5)

        lamp_r = w * 0.32
        # Lamp order: red, amber, green — top-to-bottom (N/S) or, for E/W,
        # left-to-right; orientation detail only, both axes read the same.
        for i, lamp_state in enumerate(
            (SignalState.RED, SignalState.AMBER, SignalState.GREEN)
        ):
            frac = (i + 0.5) / 3 - 0.5
            lx = x if vertical else x + frac * (length - w)
            ly = y + frac * (length - w) if vertical else y
            if state is lamp_state:
                color = QColor(_SIGNAL_COLORS[lamp_state])
            else:
                color = QColor(_SIGNAL_COLORS[lamp_state]).darker(280)
            p.setBrush(color)
            p.drawEllipse(QRectF(lx - lamp_r, ly - lamp_r, 2 * lamp_r, 2 * lamp_r))
