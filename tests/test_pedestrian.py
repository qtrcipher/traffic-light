"""Pedestrian crossing tests — demand, WALK windows, determinism (headless)."""

from __future__ import annotations

import pytest

from traffic_light.core import presets
from traffic_light.core.engine import PED_WALK_S, SimulationEngine
from traffic_light.core.signal import PedestrianState as P
from traffic_light.core.signal import SignalState as S

WALK = P.WALK
DONT = P.DONT_WALK


def make_engine(seed: int = 0) -> SimulationEngine:
    return SimulationEngine(presets.default_plan(), seed=seed)


def test_no_demand_never_walks():
    engine = make_engine()
    engine.tick(engine.plan.cycle_s)
    for axis in ("NS", "EW"):
        assert engine.state.pedestrians[axis] is DONT
        assert engine.state.ped_demand[axis] is False


def test_request_rejects_unknown_axis():
    engine = make_engine()
    with pytest.raises(ValueError):
        engine.request_pedestrian("diagonal")


def test_walk_only_while_crossed_road_is_red():
    # EW crossing demand: EW road is red from the NS-amber phase onward.
    engine = make_engine()
    engine.request_pedestrian("EW")
    assert engine.state.ped_demand["EW"] is True

    engine.tick(10.0)  # mid NS-green: EW road still has red, phase hasn't turned
    assert engine.state.pedestrians["EW"] is DONT  # not served mid-phase

    engine.tick(10.0)  # t=20: NS amber phase starts, EW red -> served
    assert engine.state.pedestrians["EW"] is WALK
    assert engine.state.ped_demand["EW"] is False  # demand consumed


def test_walk_window_capped_by_phase_duration():
    engine = make_engine()
    engine.request_pedestrian("EW")
    engine.tick(20.0)  # served: window = min(5, 3 s amber phase) = 3 s
    engine.tick(2.9)
    assert engine.state.pedestrians["EW"] is WALK
    engine.tick(0.2)  # t=23.1: window over (still inside the phase)
    assert engine.state.pedestrians["EW"] is DONT


def test_walk_window_max_five_seconds():
    engine = make_engine()
    engine.tick(23.0)  # all-red phase starts; request mid-phase so it is
    engine.request_pedestrian("NS")  # served at the NEXT NS-red phase start
    engine.tick(1.5)  # t=24.5: phase 3 (EW green 20 s), NS red -> 5 s window
    assert engine.state.pedestrians["NS"] is WALK
    engine.tick(PED_WALK_S - 0.1)
    assert engine.state.pedestrians["NS"] is WALK
    engine.tick(0.2)
    assert engine.state.pedestrians["NS"] is DONT


def test_walk_never_spans_phases():
    engine = make_engine()
    engine.request_pedestrian("NS")
    engine.tick(23.0)  # all-red phase (1.5 s): served with 1.5 s window
    assert engine.state.pedestrians["NS"] is WALK
    engine.tick(1.5)  # next phase starts -> window cannot carry over
    assert engine.state.pedestrians["NS"] is DONT


def test_skip_to_next_phase_serves_demand():
    engine = make_engine()
    engine.request_pedestrian("EW")
    engine.skip_to_next_phase()  # NS amber, EW red
    assert engine.state.pedestrians["EW"] is WALK


def test_pedestrian_determinism():
    a, b = make_engine(seed=42), make_engine(seed=42)
    for engine in (a, b):
        engine.request_pedestrian("EW")
        for _ in range(300):
            engine.tick(0.1)
        engine.request_pedestrian("NS")
        for _ in range(300):
            engine.tick(0.1)
    assert a.state == b.state
    assert a.state.pedestrians["NS"] is WALK or a.state.ped_demand["NS"] is False
