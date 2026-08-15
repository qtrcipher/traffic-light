"""Accessibility tests: accessible names, focus policy, live canvas description."""

from __future__ import annotations

from PySide6.QtCore import Qt

from traffic_light.core import presets
from traffic_light.core.engine import SimulationEngine
from traffic_light.ui.canvas import IntersectionCanvas
from traffic_light.ui.panels import ControlPanel
from traffic_light.ui.plan_editor import PlanEditorDialog


def make_canvas(qtbot):
    engine = SimulationEngine(presets.default_plan(), seed=0)
    canvas = IntersectionCanvas(engine)
    qtbot.addWidget(canvas)
    return engine, canvas


def test_canvas_has_accessible_name_and_is_focusable(qtbot):
    _, canvas = make_canvas(qtbot)
    assert canvas.accessibleName()
    assert canvas.focusPolicy() == Qt.FocusPolicy.StrongFocus


def test_canvas_description_tracks_phase(qtbot):
    engine, canvas = make_canvas(qtbot)
    canvas.update_a11y(engine.state)
    first = canvas.accessibleDescription()
    assert "1" in first and "6" in first
    engine.skip_to_next_phase()
    canvas.update_a11y(engine.state)
    assert canvas.accessibleDescription() != first
    assert "2" in canvas.accessibleDescription()


def test_panel_controls_have_accessible_text(qtbot):
    panel = ControlPanel()
    qtbot.addWidget(panel)
    assert panel.play_button.accessibleDescription()
    assert panel.speed_slider.accessibleName()
    assert panel.speed_slider.accessibleDescription()
    assert panel.preset_combo.accessibleName()
    assert panel.phase_label.accessibleName()
    assert panel.time_label.accessibleName()


def test_plan_editor_widgets_have_accessible_names(qtbot):
    dialog = PlanEditorDialog(presets.default_plan())
    qtbot.addWidget(dialog)
    assert dialog.table.accessibleName()
    assert dialog.validation_label.accessibleName()
    for column in range(3):
        assert dialog.table.cellWidget(0, column).accessibleName()


def test_stylesheet_has_focus_indicators():
    from traffic_light.ui import theme

    for name in theme.THEMES:
        assert ":focus" in theme.stylesheet(name)
