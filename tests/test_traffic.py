"""Core traffic tests — headless, deterministic via seeded RNG."""

from __future__ import annotations

import random

from traffic_light.core.signal import SignalState as S
from traffic_light.core.traffic import (
    APPROACHES,
    CAR_LENGTH_M,
    MIN_GAP_M,
    SPAWN_DIST_M,
    TrafficModel,
)

RED_ALL = {a: S.RED for a in APPROACHES}
GREEN_ALL = {a: S.GREEN for a in APPROACHES}


def make_traffic(seed: int = 0, rate: float = 0.5) -> TrafficModel:
    return TrafficModel(random.Random(seed), rate_per_s=rate)


def run(model: TrafficModel, seconds: float, states: dict) -> None:
    steps = int(seconds / 0.1)
    for _ in range(steps):
        model.update(0.1, states)


def test_cars_spawn_and_approach():
    model = make_traffic()
    run(model, 5.0, GREEN_ALL)
    cars = model.snapshot()
    assert cars  # rate 0.5/s over 5 s spawns traffic
    assert all(c.distance_m < SPAWN_DIST_M for c in cars)  # they moved forward


def test_queue_forms_on_red():
    model = make_traffic()
    run(model, 20.0, RED_ALL)
    cars = model.snapshot()
    assert cars
    assert all(c.distance_m >= 0.0 for c in cars)  # nobody entered on red
    assert any(c.distance_m == 0.0 for c in cars)  # someone is waiting at the line


def test_queue_keeps_gaps():
    model = make_traffic()
    run(model, 20.0, RED_ALL)
    for approach in APPROACHES:
        distances = sorted(
            (c.distance_m for c in model.snapshot() if c.approach == approach),
            reverse=True,
        )
        for ahead, behind in zip(distances, distances[1:]):
            assert ahead - behind >= CAR_LENGTH_M + MIN_GAP_M - 1e-9


def test_queue_clears_on_green():
    model = make_traffic(rate=0.0)  # burst-only traffic, fully explicit
    model.spawn_burst(per_approach=2)
    run(model, 12.0, RED_ALL)  # 120 m at 12 m/s: reach the line and queue
    assert any(c.distance_m == 0.0 for c in model.snapshot())
    run(model, 3.0, GREEN_ALL)
    assert all(c.distance_m < 0.0 for c in model.snapshot())  # everyone crossed


def test_deterministic_under_fixed_seed():
    a, b = make_traffic(seed=7), make_traffic(seed=7)
    run(a, 30.0, RED_ALL)
    run(b, 30.0, RED_ALL)
    assert a.snapshot() == b.snapshot()


def test_spawn_burst_adds_cars_on_every_approach():
    model = make_traffic(rate=0.0)  # no natural spawns
    model.spawn_burst(per_approach=3)
    cars = model.snapshot()
    assert model.count() == 4 * 3
    for approach in APPROACHES:
        assert sum(1 for c in cars if c.approach == approach) == 3


def test_negative_rate_rejected():
    import pytest

    with pytest.raises(ValueError):
        make_traffic(rate=-1.0)
