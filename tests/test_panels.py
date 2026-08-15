"""Control panel tests — speed mapping, transport, presets."""

from __future__ import annotations

from traffic_light.ui.panels import SLIDER_MAX, SLIDER_MIN, ControlPanel, slider_to_speed


def test_slider_to_speed_endpoints_and_midpoint():
    assert slider_to_speed(SLIDER_MIN) == 0.5
    assert slider_to_speed(100) == 1.0
    assert slider_to_speed(SLIDER_MAX) == 4.0


def test_play_button_toggles_and_emits(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    seen = []
    panel.playToggled.connect(seen.append)

    assert panel.playing is True
    panel.play_button.click()
    assert panel.playing is False
    assert panel.play_button.text() == "Play"
    panel.play_button.click()
    assert panel.playing is True
    assert panel.play_button.text() == "Pause"
    assert seen == [False, True]


def test_speed_slider_emits_mapped_speed(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    seen = []
    panel.speedChanged.connect(seen.append)

    panel.speed_slider.setValue(200)
    assert seen == [2.0]
    assert panel.speed_label.text() == "2×"


def test_preset_combo_emits_preset_key(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    seen = []
    panel.presetChosen.connect(seen.append)

    index = panel.preset_combo.findData("night_flash")
    assert index >= 0
    panel.preset_combo.setCurrentIndex(index)
    panel.preset_combo.activated.emit(index)
    assert seen == ["night_flash"]


def test_update_status_shows_phase_and_time(qtbot):
    from traffic_light.core import presets
    from traffic_light.core.engine import SimulationEngine

    engine = SimulationEngine(presets.default_plan(), seed=0)
    engine.tick(5.0)
    panel = ControlPanel()
    qtbot.addWidget(panel)
    panel.update_status(engine.state)
    assert "1" in panel.phase_label.text()
    assert "6" in panel.phase_label.text()  # default plan has 6 phases
    assert "5.0" in panel.time_label.text()
