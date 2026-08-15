"""Right-side control panel: transport, speed, phase readout, presets.

The panel owns no simulation logic — it emits signals and the main window
wires them to the engine. The main window feeds the readout back in via
``update_status``.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

from ..core import presets
from ..core.engine import EngineState

SLIDER_MIN = 50  # 0.5×
SLIDER_MAX = 400  # 4.0×

_PRESET_LABELS = {
    "default": "Default",
    "rush_hour": "Rush hour",
    "night_flash": "Night flash",
}


def slider_to_speed(value: int) -> float:
    """Map the speed slider position onto the 0.5×–4× range."""
    return value / 100.0


class ControlPanel(QWidget):
    playToggled = Signal(bool)  # True = now playing
    speedChanged = Signal(float)
    presetChosen = Signal(str)  # key into core.presets.PRESETS
    pedestrianRequested = Signal(str)  # "NS" or "EW" — the road being crossed

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.playing = True
        self.setFixedWidth(280)

        layout = QVBoxLayout(self)

        self.play_button = QPushButton(self.tr("Pause"))
        self.play_button.setAccessibleDescription(
            self.tr("Start or pause the simulation. Shortcut: Space.")
        )
        self.play_button.clicked.connect(self._on_play_clicked)
        layout.addWidget(self.play_button)

        speed_caption = QLabel(self.tr("Speed"))
        layout.addWidget(speed_caption)
        self.speed_label = QLabel("1.0×")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(SLIDER_MIN, SLIDER_MAX)
        self.speed_slider.setValue(100)
        self.speed_slider.setAccessibleName(self.tr("Simulation speed"))
        self.speed_slider.setAccessibleDescription(
            self.tr("Scales playback from 0.5× to 4× real time.")
        )
        speed_caption.setBuddy(self.speed_slider)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        layout.addWidget(self.speed_slider)
        layout.addWidget(self.speed_label)

        self.phase_label = QLabel()
        self.phase_label.setAccessibleName(self.tr("Current phase"))
        self.time_label = QLabel()
        self.time_label.setAccessibleName(self.tr("Phase elapsed time"))
        layout.addWidget(self.phase_label)
        layout.addWidget(self.time_label)

        preset_caption = QLabel(self.tr("Preset"))
        layout.addWidget(preset_caption)
        self.preset_combo = QComboBox()
        self.preset_combo.setAccessibleName(self.tr("Timing plan preset"))
        for key in presets.PRESETS:
            self.preset_combo.addItem(self.tr(_PRESET_LABELS[key]), userData=key)
        preset_caption.setBuddy(self.preset_combo)
        self.preset_combo.activated.connect(self._on_preset_activated)
        layout.addWidget(self.preset_combo)

        # Pedestrian demand buttons: lit while the request waits to be served.
        ped_row = QHBoxLayout()
        self.ped_buttons: dict[str, QPushButton] = {}
        for axis, label, description in (
            ("NS", "Pedestrian NS", "Request to cross the north–south road."),
            ("EW", "Pedestrian EW", "Request to cross the east–west road."),
        ):
            button = QPushButton(self.tr(label))
            button.setCheckable(True)
            button.setAccessibleName(self.tr(description))
            button.clicked.connect(
                lambda _=False, a=axis: self.pedestrianRequested.emit(a)
            )
            ped_row.addWidget(button)
            self.ped_buttons[axis] = button
        layout.addLayout(ped_row)
        layout.addStretch(1)

    def update_status(self, state: EngineState) -> None:
        """Refresh the phase/elapsed readout from an engine snapshot."""
        self.phase_label.setText(
            self.tr("Phase {n} of {total}").format(
                n=state.phase_index + 1, total=state.phase_count
            )
        )
        self.time_label.setText(
            self.tr("{elapsed:.1f} s of {duration:.1f} s").format(
                elapsed=state.phase_elapsed_s, duration=state.phase_duration_s
            )
        )
        for axis, button in self.ped_buttons.items():
            pending = state.ped_demand.get(axis, False)
            if button.isChecked() != pending:
                button.setChecked(pending)

    def _on_play_clicked(self) -> None:
        self.playing = not self.playing
        self.play_button.setText(self.tr("Pause") if self.playing else self.tr("Play"))
        self.playToggled.emit(self.playing)

    def _on_speed_changed(self, value: int) -> None:
        speed = slider_to_speed(value)
        self.speed_label.setText(f"{speed:g}×")
        self.speedChanged.emit(speed)

    def _on_preset_activated(self, index: int) -> None:
        self.presetChosen.emit(self.preset_combo.itemData(index))
