"""Timing plan editor dialog: phase table with live validation.

The dialog edits a copy of the plan; the caller reads ``dialog.plan()`` after
Accept and hands it to the engine. Validation rules live in core (TimingPlan.
validate) — the dialog only surfaces them and keeps Apply disabled until the
plan is valid.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.cycle import MIN_AMBER_S, MIN_CYCLE_S, Phase, TimingPlan, ValidationIssue
from ..core.signal import SignalState
from . import settings as prefs
from . import theme

_STATE_ORDER = (SignalState.RED, SignalState.AMBER, SignalState.GREEN, SignalState.OFF)
_STATE_LABELS = {
    SignalState.RED: "Red",
    SignalState.AMBER: "Amber",
    SignalState.GREEN: "Green",
    SignalState.OFF: "Off",
}


class PlanEditorDialog(QDialog):
    def __init__(self, plan: TimingPlan, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Edit timing plan"))

        layout = QVBoxLayout(self)
        name_caption = QLabel(self.tr("Plan name"))
        layout.addWidget(name_caption)
        self.name_edit = QLineEdit(plan.name)
        name_caption.setBuddy(self.name_edit)
        layout.addWidget(self.name_edit)

        self.table = QTableWidget(0, 3)
        self.table.setAccessibleName(self.tr("Phases"))
        self.table.setHorizontalHeaderLabels(
            [self.tr("NS signal"), self.tr("EW signal"), self.tr("Duration (s)")]
        )
        for phase in plan.phases:
            self._append_row(phase)
        layout.addWidget(self.table)

        row_buttons = QHBoxLayout()
        self.add_button = QPushButton(self.tr("Add phase"))
        self.add_button.clicked.connect(self._on_add)
        self.remove_button = QPushButton(self.tr("Remove phase"))
        self.remove_button.clicked.connect(self._on_remove)
        row_buttons.addWidget(self.add_button)
        row_buttons.addWidget(self.remove_button)
        row_buttons.addStretch(1)
        layout.addLayout(row_buttons)

        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        self.validation_label.setAccessibleName(self.tr("Validation messages"))
        error_color = theme.THEMES[prefs.theme()]["error"]
        self.validation_label.setStyleSheet(f"color: {error_color};")
        layout.addWidget(self.validation_label)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        self.apply_button = QPushButton(self.tr("Apply"))
        self.apply_button.clicked.connect(self.accept)
        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.reject)
        action_row.addWidget(self.apply_button)
        action_row.addWidget(cancel_button)
        layout.addLayout(action_row)

        self._revalidate()

    def plan(self) -> TimingPlan:
        """The plan as currently shown in the table (may be invalid)."""
        phases = []
        for row in range(self.table.rowCount()):
            ns = self.table.cellWidget(row, 0).currentData()
            ew = self.table.cellWidget(row, 1).currentData()
            duration = self.table.cellWidget(row, 2).value()
            phases.append(Phase(ns, ew, duration))
        name = self.name_edit.text().strip() or self.tr("Untitled")
        return TimingPlan(name=name, phases=phases)

    def _append_row(self, phase: Phase) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, state in ((0, phase.ns), (1, phase.ew)):
            combo = QComboBox()
            for signal_state in _STATE_ORDER:
                combo.addItem(
                    self.tr(_STATE_LABELS[signal_state]), userData=signal_state
                )
            combo.setCurrentIndex(_STATE_ORDER.index(state))
            combo.setAccessibleName(
                self.tr("NS signal") if column == 0 else self.tr("EW signal")
            )
            combo.currentIndexChanged.connect(self._revalidate)
            self.table.setCellWidget(row, column, combo)
        duration = QDoubleSpinBox()
        duration.setRange(0.5, 600.0)
        duration.setSingleStep(0.5)
        duration.setValue(phase.duration_s)
        duration.setAccessibleName(self.tr("Duration (s)"))
        duration.valueChanged.connect(self._revalidate)
        self.table.setCellWidget(row, 2, duration)

    def _on_add(self) -> None:
        # Guided default for a new blank phase: a plain NS-green step.
        self._append_row(Phase(SignalState.GREEN, SignalState.RED, 10.0))
        self._revalidate()

    def _on_remove(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
        self._revalidate()

    def _issue_text(self, issue: ValidationIssue) -> str:
        """Translate a core validation code into the UI language."""
        n = issue.phase
        if issue.code == "no_phases":
            return self.tr("The plan has no phases.")
        if issue.code == "nonpositive_duration":
            return self.tr("Phase {n}: duration must be positive.").format(n=n)
        if issue.code == "amber_too_short":
            return self.tr("Phase {n}: amber must be at least {min} s.").format(
                n=n, min=f"{MIN_AMBER_S:g}"
            )
        if issue.code == "both_axes_green":
            return self.tr("Phase {n}: NS and EW cannot both be green.").format(n=n)
        if issue.code == "cycle_too_short":
            return self.tr("The cycle must be at least {min} s.").format(
                min=f"{MIN_CYCLE_S:g}"
            )
        return str(issue)  # unknown code: English fallback from core

    def _revalidate(self) -> None:
        issues = self.plan().validate()
        self.validation_label.setText(
            "\n".join(self._issue_text(i) for i in issues)
        )
        self.apply_button.setEnabled(not issues)
