"""Car spawning, queues and movement.

Movement model: simple point-mass cars per approach; a car advances when the
signal is green and the car ahead is far enough. Seeded RNG (from the engine)
drives spawn intervals so simulations are reproducible in tests.

Geometry: each approach is a one-dimensional track. A car's ``distance_m`` is
its distance to the stop line — positive while approaching, zero at the line,
negative once it has crossed into/past the intersection. Cars are removed once
they are ``EXIT_DIST_M`` past the line. The canvas maps these distances to
screen positions; traffic owns no rendering.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .signal import SignalState

APPROACHES = ("N", "S", "E", "W")

SPAWN_DIST_M = 120.0  # new cars appear this far behind the stop line (offscreen)
EXIT_DIST_M = 60.0  # cars are removed this far past the stop line
CAR_LENGTH_M = 4.5
MIN_GAP_M = 2.0  # bumper-to-bumper gap kept behind the car ahead
CRUISE_SPEED_MPS = 12.0  # ~43 km/h, one speed fits the classroom demo
NUM_CAR_COLORS = 6  # canvas maps indexes onto its theme palette


@dataclass(frozen=True)
class CarSnapshot:
    """Immutable view of one car, handed to the UI via the engine state."""

    approach: str
    distance_m: float
    color_index: int


class _Car:
    __slots__ = ("distance", "color_index")

    def __init__(self, distance: float, color_index: int) -> None:
        self.distance = distance
        self.color_index = color_index


class TrafficModel:
    """Cars on the four approaches. All randomness comes from the given RNG."""

    def __init__(self, rng: random.Random, rate_per_s: float = 0.25) -> None:
        if rate_per_s < 0:
            raise ValueError("spawn rate must be >= 0")
        self._rng = rng
        self.rate_per_s = rate_per_s
        self._cars: dict[str, list[_Car]] = {a: [] for a in APPROACHES}
        # Poisson-ish spawning: exponential inter-arrival times.
        self._next_spawn = {
            a: rng.expovariate(rate_per_s) if rate_per_s > 0 else math.inf
            for a in APPROACHES
        }

    def snapshot(self) -> tuple[CarSnapshot, ...]:
        return tuple(
            CarSnapshot(a, c.distance, c.color_index)
            for a in APPROACHES
            for c in self._cars[a]
        )

    def count(self) -> int:
        return sum(len(cars) for cars in self._cars.values())

    def spawn_burst(self, per_approach: int = 3) -> None:
        """Debug helper: stack a burst of cars behind the queue on every approach."""
        for approach in APPROACHES:
            for _ in range(per_approach):
                cars = self._cars[approach]
                position = (
                    SPAWN_DIST_M
                    if not cars
                    else cars[-1].distance + CAR_LENGTH_M + MIN_GAP_M
                )
                cars.append(_Car(position, self._rng.randrange(NUM_CAR_COLORS)))

    def update(self, dt_s: float, states: dict[str, SignalState]) -> None:
        """Advance spawning and movement by dt_s under the given signal states."""
        if dt_s <= 0:
            return
        for approach in APPROACHES:
            timer = self._next_spawn[approach] - dt_s
            while timer <= 0:
                self._try_spawn(approach)
                timer += self._rng.expovariate(self.rate_per_s)
            self._next_spawn[approach] = timer
            self._move(approach, dt_s, states[approach])

    def _try_spawn(self, approach: str) -> bool:
        cars = self._cars[approach]
        if cars and cars[-1].distance > SPAWN_DIST_M - (CAR_LENGTH_M + MIN_GAP_M):
            return False  # no room at the spawn point; skip this arrival
        cars.append(_Car(SPAWN_DIST_M, self._rng.randrange(NUM_CAR_COLORS)))
        return True

    def _move(self, approach: str, dt_s: float, state: SignalState) -> None:
        cars = self._cars[approach]
        stop_at_line = state is SignalState.RED
        for i, car in enumerate(cars):
            new = car.distance - CRUISE_SPEED_MPS * dt_s
            if i > 0:  # keep a gap behind the car ahead (list is front-first)
                new = max(new, cars[i - 1].distance + CAR_LENGTH_M + MIN_GAP_M)
            if stop_at_line and car.distance >= 0:  # may not enter on red
                new = max(new, 0.0)
            car.distance = new
        self._cars[approach] = [c for c in cars if c.distance > -EXIT_DIST_M]
