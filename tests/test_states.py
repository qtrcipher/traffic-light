"""Control x state coverage: empty/error states, presentation mode, extremes."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from traffic_light.core import presets
from traffic_light.core.cycle import TimingPlan
from traffic_light.ui.main_window import MainWindow
from traffic_light.ui.plan_editor import PlanEditorDialog


@pytest.fixture
def window(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    return w


def _click_message_box_button(text: str) -> None:
    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, QMessageBox):
            for button in widget.buttons():
                if button.text() == text:
                    button.click()
                    return
    raise AssertionError(f"no message box button: {text!r}")


# --- plan editor: empty state ---


def test_plan_editor_empty_plan_is_guided_error(qtbot):
    dialog = PlanEditorDialog(TimingPlan(name="Empty"))
    qtbot.addWidget(dialog)
    assert dialog.table.rowCount() == 0
    assert not dialog.apply_button.isEnabled()
    assert dialog.validation_label.text()  # "The plan has no phases."


def test_plan_editor_empty_then_add_row_is_valid(qtbot):
    # Guided flow: one added row (green/red, 10 s) is a complete valid plan.
    dialog = PlanEditorDialog(TimingPlan(name="Empty"))
    qtbot.addWidget(dialog)
    dialog.add_button.click()
    assert dialog.apply_button.isEnabled()
    assert dialog.validation_label.text() == ""


# --- load plan: error and success paths ---


def test_load_invalid_plan_offers_restore_default(qtbot, window, tmp_path):
    window.engine.set_plan(presets.rush_hour_plan())
    window.engine.tick(50.0)  # let it apply; engine is now on Rush hour
    assert window.engine.plan.name == "Rush hour"

    bad = tmp_path / "bad.json"
    bad.write_text('{"name": "x", "phases": [{"ns": "purple"}]}')
    QTimer.singleShot(
        0, lambda: _click_message_box_button("Restore default plan")
    )
    window._load_plan_from(str(bad))
    pending = window.engine.pending_plan
    assert pending is not None
    assert pending.name == "Default"


def test_load_invalid_plan_cancel_keeps_current(qtbot, window, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json at all")
    QTimer.singleShot(0, lambda: _click_message_box_button("Cancel"))
    window._load_plan_from(str(bad))
    assert window.engine.pending_plan is None
    assert window.engine.plan.name == "Default"


def test_load_valid_plan_queues_it(qtbot, window, tmp_path):
    path = tmp_path / "plan.json"
    presets.night_flash_plan().save(path)
    window._load_plan_from(str(path))
    pending = window.engine.pending_plan
    assert pending is not None
    assert pending.name == "Night flash"


def test_load_missing_file_offers_restore(qtbot, window, tmp_path):
    QTimer.singleShot(
        0, lambda: _click_message_box_button("Restore default plan")
    )
    window._load_plan_from(str(tmp_path / "does-not-exist.json"))
    assert window.engine.pending_plan is not None


# --- presentation mode ---


def test_presentation_mode_toggle(qtbot, window):
    window.show()
    assert not window._presenting
    assert window.panel.isVisible()

    window._enter_presentation()
    assert window._presenting
    assert window.isFullScreen()
    assert not window.panel.isVisible()

    window._exit_presentation()
    assert not window._presenting
    assert not window.isFullScreen()
    assert window.panel.isVisible()


def test_presentation_enter_is_idempotent(qtbot, window):
    window.show()
    window._enter_presentation()
    window._enter_presentation()
    assert window._presenting
    window._exit_presentation()
    assert not window._presenting


# --- speed slider extremes wired to the window ---


def test_speed_slider_extremes(qtbot, window):
    seen = []
    window.panel.speedChanged.connect(seen.append)
    window.panel.speed_slider.setValue(50)
    assert window.speed == 0.5
    window.panel.speed_slider.setValue(400)
    assert window.speed == 4.0
    assert seen == [0.5, 4.0]


# --- paused timer: engine does not advance ---


def test_paused_timer_does_not_advance_engine(qtbot, window):
    window.playing = False
    before = window.engine.state.sim_time_s
    window._advance(0.5)
    window._advance(0.5)
    assert window.engine.state.sim_time_s == before


def test_running_timer_advances_engine(qtbot, window):
    window.playing = True
    before = window.engine.state.sim_time_s
    window._advance(0.5)
    assert window.engine.state.sim_time_s > before


def test_speed_scales_engine_advance(qtbot, window):
    window.playing = True
    window.speed = 2.0
    before = window.engine.state.sim_time_s
    window._advance(0.5)
    assert window.engine.state.sim_time_s == pytest.approx(before + 1.0)
