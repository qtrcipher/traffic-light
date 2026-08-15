"""Quiz mode: pause the sim, ask about the plan's phase order, resume.

The question generator derives everything from the live engine state and the
current TimingPlan — no hardcoded answers. One round is ROUND_SIZE questions;
the dialog shows the score as it goes. Strings use
QCoreApplication.translate so the generator stays testable headless.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from ..core.cycle import TimingPlan
from ..core.engine import SimulationEngine
from ..core.signal import SignalState

ROUND_SIZE = 5
_CONTEXT = "QuizDialog"

_STATE_NAMES = {
    SignalState.RED: "Red",
    SignalState.AMBER: "Amber",
    SignalState.GREEN: "Green",
    SignalState.OFF: "Off",
}

QUESTION_KINDS = ("next_green_axis", "next_ns_state")


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


@dataclass
class Question:
    text: str
    options: list[str]
    correct: str
    explanation: str


def make_question(plan: TimingPlan, phase_index: int, kind: str) -> Question:
    """Build a question whose correct answer follows from the plan's order."""
    phases = plan.phases
    total = len(phases)
    next_index = (phase_index + 1) % total
    next_phase = phases[next_index]
    explanation = _tr(
        "Phase {n} of {total} is next in the plan: NS {ns}, EW {ew}."
    ).format(
        n=next_index + 1,
        total=total,
        ns=_tr(_STATE_NAMES[next_phase.ns]),
        ew=_tr(_STATE_NAMES[next_phase.ew]),
    )

    if kind == "next_ns_state":
        correct = _tr(_STATE_NAMES[next_phase.ns])
        distractors = [
            _tr(name)
            for state, name in _STATE_NAMES.items()
            if _tr(name) != correct
        ][:2]
        return Question(
            text=_tr("What will the NS signals show when the current phase ends?"),
            options=[correct, *distractors],
            correct=correct,
            explanation=explanation,
        )

    if kind == "next_green_axis":
        correct = _tr("Neither")
        for k in range(1, total + 1):
            phase = phases[(phase_index + k) % total]
            if phase.ns is SignalState.GREEN:
                correct = _tr("NS")
                break
            if phase.ew is SignalState.GREEN:
                correct = _tr("EW")
                break
        return Question(
            text=_tr("Which axis gets the next green?"),
            options=[_tr("NS"), _tr("EW"), _tr("Neither")],
            correct=correct,
            explanation=explanation,
        )

    raise ValueError(f"unknown question kind: {kind!r}")


@dataclass
class QuizRound:
    """State of one round: which question we're on and the score so far."""

    index: int = 0
    score: int = 0
    answered: bool = field(default=False)


class QuizDialog(QDialog):
    """One multiple-choice question at a time, drawn from the engine state."""

    def __init__(self, engine: SimulationEngine, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Quiz"))
        self.setModal(False)
        self.engine = engine
        self.round = QuizRound()
        self._rng = random.Random()
        self._question: Question | None = None

        layout = QVBoxLayout(self)
        self.progress_label = QLabel()
        self.progress_label.setAccessibleName(self.tr("Quiz progress"))
        layout.addWidget(self.progress_label)

        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setMinimumWidth(420)
        self.question_label.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.question_label.setAccessibleName(self.tr("Question"))
        layout.addWidget(self.question_label)

        self.option_buttons: list[QPushButton] = []
        for _ in range(3):
            button = QPushButton()
            button.clicked.connect(self._on_option_clicked)
            layout.addWidget(button)
            self.option_buttons.append(button)

        self.feedback_label = QLabel()
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setAccessibleName(self.tr("Answer feedback"))
        layout.addWidget(self.feedback_label)

        self.next_button = QPushButton(self.tr("Next question"))
        self.next_button.clicked.connect(self._advance)
        layout.addWidget(self.next_button)

        self._ask()

    def _ask(self) -> None:
        kind = QUESTION_KINDS[self.round.index % len(QUESTION_KINDS)]
        self._question = make_question(
            self.engine.plan, self.engine.state.phase_index, kind
        )
        self.round.answered = False
        self.question_label.setText(self._question.text)
        options = list(self._question.options)
        self._rng.shuffle(options)
        for button, option in zip(self.option_buttons, options):
            button.setText(option)
            button.setEnabled(True)
        self.feedback_label.setText("")
        self.next_button.hide()
        self._update_progress()

    def _update_progress(self) -> None:
        self.progress_label.setText(
            self.tr("Question {n} of {total} — score {score}").format(
                n=self.round.index + 1, total=ROUND_SIZE, score=self.round.score
            )
        )

    def _on_option_clicked(self) -> None:
        if self.round.answered or self._question is None:
            return
        self.round.answered = True
        chosen = self.sender().text()
        if chosen == self._question.correct:
            self.round.score += 1
            verdict = self.tr("Correct!")
        else:
            verdict = self.tr("Not quite — the answer is {answer}.").format(
                answer=self._question.correct
            )
        self.feedback_label.setText(
            f"{verdict} {self._question.explanation}"
        )
        for button in self.option_buttons:
            button.setEnabled(False)
        self.next_button.setText(
            self.tr("Finish")
            if self.round.index + 1 >= ROUND_SIZE
            else self.tr("Next question")
        )
        self.next_button.show()
        self._update_progress()

    def _advance(self) -> None:
        if self.round.index + 1 >= ROUND_SIZE:
            self.accept()  # round over — main window resumes the sim
            return
        self.round.index += 1
        self._ask()
