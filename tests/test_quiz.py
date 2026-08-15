"""Quiz mode tests: generator correctness against known plans + dialog flow."""

from __future__ import annotations

import pytest

from traffic_light.core import presets
from traffic_light.core.engine import SimulationEngine
from traffic_light.ui.quiz import ROUND_SIZE, QuizDialog, make_question
from traffic_light.ui.main_window import MainWindow

DEFAULT = presets.default_plan()


def test_next_ns_state_answer():
    # Default plan phase 0 is NS green; the phase after it is NS amber.
    q = make_question(DEFAULT, 0, "next_ns_state")
    assert q.correct == "Amber"
    assert q.correct in q.options
    assert len(q.options) == 3
    assert "Phase 2 of 6" in q.explanation


def test_next_ns_state_wraps_around():
    # Last phase (all-red) wraps to phase 0: NS green.
    q = make_question(DEFAULT, len(DEFAULT.phases) - 1, "next_ns_state")
    assert q.correct == "Green"


def test_next_green_axis_skips_all_red():
    q = make_question(DEFAULT, 0, "next_green_axis")
    assert q.correct == "EW"  # phases 1-2 are amber/all-red, phase 3 is EW green
    assert q.options == ["NS", "EW", "Neither"]


def test_next_green_axis_from_ew_green():
    q = make_question(DEFAULT, 3, "next_green_axis")
    assert q.correct == "NS"


def test_next_green_axis_neither_when_no_green():
    q = make_question(presets.night_flash_plan(), 0, "next_green_axis")
    assert q.correct == "Neither"


def test_unknown_question_kind_rejected():
    with pytest.raises(ValueError):
        make_question(DEFAULT, 0, "whoami")


def make_dialog(qtbot):
    engine = SimulationEngine(DEFAULT, seed=0)
    dialog = QuizDialog(engine)
    qtbot.addWidget(dialog)
    return dialog


def click_correct(dialog):
    for button in dialog.option_buttons:
        if button.text() == dialog._question.correct:
            button.click()
            return
    raise AssertionError("correct option not shown")


def test_dialog_first_question_shown(qtbot):
    dialog = make_dialog(qtbot)
    assert dialog.question_label.text()
    assert "1" in dialog.progress_label.text()
    assert str(ROUND_SIZE) in dialog.progress_label.text()
    assert dialog.next_button.isHidden()


def test_correct_answer_scores_and_explains(qtbot):
    dialog = make_dialog(qtbot)
    click_correct(dialog)
    assert dialog.round.score == 1
    assert "Correct!" in dialog.feedback_label.text()
    assert "Phase" in dialog.feedback_label.text()  # explanation appended
    assert not dialog.next_button.isHidden()  # hidden dialog: isVisible is False
    assert all(not b.isEnabled() for b in dialog.option_buttons)


def test_wrong_answer_reveals_correct(qtbot):
    dialog = make_dialog(qtbot)
    for button in dialog.option_buttons:
        if button.text() != dialog._question.correct:
            button.click()
            break
    assert dialog.round.score == 0
    assert "the answer is" in dialog.feedback_label.text()
    assert dialog._question.correct in dialog.feedback_label.text()


def test_full_round_finishes(qtbot):
    dialog = make_dialog(qtbot)
    for i in range(ROUND_SIZE):
        click_correct(dialog)
        assert dialog.round.score == i + 1
        dialog.next_button.click()
    assert dialog.result() == QuizDialog.DialogCode.Accepted


def test_quiz_toggle_pauses_and_resumes(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.playing is True

    window.quiz_action.setChecked(True)
    window._toggle_quiz(True)
    assert window.playing is False
    assert window._quiz is not None
    assert window._quiz.isVisible()

    window._quiz.accept()  # student finishes the round
    assert window.playing is True
    assert not window.quiz_action.isChecked()


def test_quiz_cancel_resumes_too(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window._toggle_quiz(True)
    window._quiz.reject()  # student bails out mid-round
    assert window.playing is True
