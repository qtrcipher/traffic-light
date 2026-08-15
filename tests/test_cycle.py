"""Core timing-plan tests — headless, no Qt."""

from __future__ import annotations

import pytest

from traffic_light.core import presets
from traffic_light.core.cycle import MIN_CYCLE_S, Phase, TimingPlan
from traffic_light.core.signal import SignalState as S


def test_all_presets_are_valid():
    for make in presets.PRESETS.values():
        assert make().validate() == []


def test_empty_plan_is_invalid():
    assert TimingPlan(name="x").validate()


def test_both_axes_green_is_rejected():
    plan = TimingPlan(name="x", phases=[Phase(S.GREEN, S.GREEN, 10.0)])
    assert any("both" in e for e in plan.validate())


def test_amber_shorter_than_minimum_is_rejected():
    plan = TimingPlan(name="x", phases=[Phase(S.AMBER, S.RED, 0.5)])
    assert any("amber" in e for e in plan.validate())


def test_short_cycle_is_rejected_when_green_present():
    plan = TimingPlan(name="x", phases=[Phase(S.GREEN, S.RED, 2.0)])
    assert plan.cycle_s < MIN_CYCLE_S
    assert any("Cycle" in e for e in plan.validate())


def test_night_flash_short_cycle_allowed_without_green():
    plan = TimingPlan(name="x", phases=[Phase(S.AMBER, S.AMBER, 1.0), Phase(S.OFF, S.OFF, 1.0)])
    assert plan.validate() == []


def test_json_round_trip(tmp_path):
    plan = presets.default_plan()
    path = tmp_path / "plan.json"
    plan.save(path)
    loaded = TimingPlan.load(path)
    assert loaded.name == plan.name
    assert loaded.phases == plan.phases


def test_from_json_rejects_garbage():
    with pytest.raises(ValueError):
        TimingPlan.from_json('{"name": "x", "phases": [{"ns": "purple"}]}')


def test_from_json_rejects_invalid_plan():
    with pytest.raises(ValueError):
        TimingPlan.from_json(
            '{"name": "x", "phases": [{"ns": "green", "ew": "green", "duration_s": 10}]}'
        )
