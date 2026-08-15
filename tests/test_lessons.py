"""Guided lessons tests."""

from __future__ import annotations

from traffic_light.ui.lessons import LESSONS, LessonViewer


def test_four_built_in_lessons():
    assert len(LESSONS) == 4
    assert [l["id"] for l in LESSONS] == [
        "cycle_anatomy",
        "amber_too_short",
        "rush_hour",
        "pedestrians",
    ]
    for lesson in LESSONS:
        assert lesson["title"] and lesson["body"] and lesson["try"]


def test_initial_card(qtbot):
    viewer = LessonViewer()
    qtbot.addWidget(viewer)
    assert viewer.title_label.text() == "Anatomy of a cycle"
    assert "loop of phases" in viewer.body_label.text()
    assert "6" in viewer.try_label.text()  # "the Default plan has 6"
    assert viewer.try_label.text().startswith("Try it:")
    assert "1" in viewer.position_label.text()
    assert "4" in viewer.position_label.text()
    assert not viewer.prev_button.isEnabled()
    assert viewer.next_button.isEnabled()


def test_next_previous_navigation(qtbot):
    viewer = LessonViewer()
    qtbot.addWidget(viewer)
    viewer.next_button.click()
    assert viewer.title_label.text() == "Why amber can't be too short"
    assert viewer.prev_button.isEnabled()
    assert viewer.picker.currentIndex() == 1

    viewer.next_button.click()
    viewer.next_button.click()
    assert viewer.title_label.text() == "Pedestrian demand"
    assert not viewer.next_button.isEnabled()  # clamped at the last lesson

    viewer.prev_button.click()
    assert viewer.title_label.text() == "Rush hour vs default"


def test_picker_jumps_to_lesson(qtbot):
    viewer = LessonViewer()
    qtbot.addWidget(viewer)
    viewer._show(2)
    assert viewer.title_label.text() == "Rush hour vs default"
    assert viewer.picker.currentIndex() == 2
    assert "3" in viewer.position_label.text()


def test_lesson_viewer_accessible_names(qtbot):
    viewer = LessonViewer()
    qtbot.addWidget(viewer)
    assert viewer.picker.accessibleName()
    assert viewer.title_label.accessibleName()
    assert viewer.try_label.accessibleName()
