"""Plan editor dialog tests — live validation drives the Apply button."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDoubleSpinBox

from traffic_light.core import presets
from traffic_light.core.cycle import Phase
from traffic_light.core.signal import SignalState as S
from traffic_light.ui.plan_editor import PlanEditorDialog


def make_dialog(qtbot, plan=None):
    dialog = PlanEditorDialog(plan or presets.default_plan())
    qtbot.addWidget(dialog)
    return dialog


def test_default_plan_is_valid_and_apply_enabled(qtbot):
    dialog = make_dialog(qtbot)
    assert dialog.apply_button.isEnabled()
    assert dialog.validation_label.text() == ""


def test_table_round_trips_plan(qtbot):
    plan = presets.default_plan()
    dialog = make_dialog(qtbot, plan)
    assert dialog.table.rowCount() == len(plan.phases)
    assert dialog.plan() == plan


def test_both_axes_green_disables_apply(qtbot):
    dialog = make_dialog(qtbot)
    ew_combo = dialog.table.cellWidget(0, 1)
    assert isinstance(ew_combo, QComboBox)
    ew_combo.setCurrentIndex(list((S.RED, S.AMBER, S.GREEN, S.OFF)).index(S.GREEN))
    assert not dialog.apply_button.isEnabled()
    assert "green" in dialog.validation_label.text()


def test_short_amber_disables_apply(qtbot):
    dialog = make_dialog(qtbot)
    duration = dialog.table.cellWidget(1, 2)  # amber phase in the default plan
    assert isinstance(duration, QDoubleSpinBox)
    duration.setValue(0.5)
    assert not dialog.apply_button.isEnabled()
    assert "amber" in dialog.validation_label.text()


def test_add_and_remove_phase(qtbot):
    dialog = make_dialog(qtbot)
    rows = dialog.table.rowCount()
    dialog.add_button.click()
    assert dialog.table.rowCount() == rows + 1
    dialog.table.setCurrentCell(rows, 0)
    dialog.remove_button.click()
    assert dialog.table.rowCount() == rows


def test_removing_all_phases_disables_apply(qtbot):
    plan = presets.night_flash_plan()
    dialog = make_dialog(qtbot, plan)
    for row in (1, 0):
        dialog.table.setCurrentCell(row, 0)
        dialog.remove_button.click()
    assert dialog.table.rowCount() == 0
    assert not dialog.apply_button.isEnabled()
    assert dialog.validation_label.text()


def test_plan_reads_back_edited_values(qtbot):
    dialog = make_dialog(qtbot)
    ns_combo = dialog.table.cellWidget(0, 0)
    ns_combo.setCurrentIndex(list((S.RED, S.AMBER, S.GREEN, S.OFF)).index(S.AMBER))
    duration = dialog.table.cellWidget(0, 2)
    duration.setValue(12.0)
    first = dialog.plan().phases[0]
    assert first == Phase(S.AMBER, S.RED, 12.0)
