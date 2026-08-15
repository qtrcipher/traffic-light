"""Core engine tests — headless, no Qt."""

from __future__ import annotations

import pytest

from traffic_light.core import presets
from traffic_light.core.cycle import Phase, TimingPlan
from traffic_light.core.engine import SimulationEngine
from traffic_light.core.signal import SignalState as S


def make_engine(seed: int = 0) -> SimulationEngine:
    return SimulationEngine(presets.default_plan(), seed=seed)


def test_initial_state_matches_first_phase():
    engine = make_engine()
    state = engine.state
    assert state.phase_index == 0
    assert state.phase_elapsed_s == 0.0
    # Default plan phase 0: NS green, EW red — NS axis drives N+S, EW drives E+W.
    assert state.heads == {"N": S.GREEN, "S": S.GREEN, "E": S.RED, "W": S.RED}
    assert engine.heads["N"].state is S.GREEN


def test_tick_advances_to_next_phase():
    engine = make_engine()
    engine.tick(20.0)  # first phase duration
    assert engine.state.phase_index == 1
    assert engine.state.heads["N"] is S.AMBER
    assert engine.state.heads["E"] is S.RED


def test_dt_larger_than_phase_lands_on_boundary():
    engine = make_engine()
    engine.tick(22.0)  # crosses the 20 s first phase, lands inside the amber phase
    assert engine.state.phase_index == 1
    assert engine.state.phase_elapsed_s == pytest.approx(2.0)


def test_cycle_wraps_around():
    engine = make_engine()
    engine.tick(engine.plan.cycle_s)
    assert engine.state.phase_index == 0
    assert engine.state.phase_elapsed_s == pytest.approx(0.0)


def test_negative_dt_rejected():
    engine = make_engine()
    with pytest.raises(ValueError):
        engine.tick(-1.0)


def test_invalid_plan_rejected_at_construction():
    bad = TimingPlan(name="x", phases=[Phase(S.GREEN, S.GREEN, 10.0)])
    with pytest.raises(ValueError):
        SimulationEngine(bad)


def test_determinism_same_seed_same_state():
    a, b = make_engine(seed=42), make_engine(seed=42)
    for _ in range(600):
        a.tick(0.1)
        b.tick(0.1)
    assert a.state == b.state
    assert a.state.cars  # the run actually spawned traffic


def test_different_seeds_diverge():
    a, b = make_engine(seed=1), make_engine(seed=2)
    for _ in range(600):
        a.tick(0.1)
        b.tick(0.1)
    assert a.state.cars != b.state.cars


def test_set_plan_validates():
    engine = make_engine()
    bad = TimingPlan(name="x", phases=[Phase(S.GREEN, S.GREEN, 10.0)])
    with pytest.raises(ValueError):
        engine.set_plan(bad)
    assert engine.plan.name == "Default"


def test_set_plan_applies_at_boundary_not_mid_phase():
    engine = make_engine()
    engine.tick(5.0)  # 5 s into the 20 s first phase
    engine.set_plan(presets.night_flash_plan())
    engine.tick(1.0)
    assert engine.plan.name == "Default"  # still mid-phase
    engine.tick(14.0)  # cross the boundary at t=20
    assert engine.plan.name == "Night flash"
    assert engine.state.phase_index == 0
    assert engine.state.heads["N"] is S.AMBER
    assert engine.state.heads["E"] is S.AMBER


def test_skip_to_next_phase():
    engine = make_engine()
    engine.skip_to_next_phase()
    assert engine.state.phase_index == 1
    assert engine.state.phase_elapsed_s == 0.0


def test_tick_split_matches_single_tick_for_phase_clock():
    a, b = make_engine(), make_engine()
    a.tick(23.0)
    for _ in range(230):
        b.tick(0.1)
    assert a.state.phase_index == b.state.phase_index
    assert a.state.phase_elapsed_s == pytest.approx(b.state.phase_elapsed_s, abs=1e-6)
