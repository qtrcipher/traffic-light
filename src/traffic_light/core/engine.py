"""Simulation engine: a deterministic clock that steps a TimingPlan.

Contract (fixed so UI and hardware code can target it):

- ``SimulationEngine(plan, seed=...)`` — deterministic; seeded RNG for traffic.
  Raises ValueError if the plan is invalid.
- ``engine.tick(dt_s)`` — advance by a real-time delta; the UI's speed slider
  scales ``dt_s`` so behavior is identical at any speed. Sub-steps at phase
  boundaries so a large dt lands exactly on the boundary, never overshoots.
- ``engine.state`` — EngineState snapshot: current phase index, elapsed,
  per-head SignalStates for N/S/E/W (the NS axis drives the N and S heads,
  EW drives E and W), and immutable car snapshots for the canvas.
- ``engine.set_plan(plan)`` — validates, then applies the TimingPlan at the
  next phase boundary, never mid-phase. Raises ValueError if invalid.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .cycle import TimingPlan
from .signal import SignalHead, SignalState
from .traffic import APPROACHES, CarSnapshot, TrafficModel

_EPS_S = 1e-9  # float tolerance for phase-boundary comparisons


@dataclass(frozen=True)
class EngineState:
    """Immutable snapshot of the simulation, consumed by UI and hardware."""

    phase_index: int
    phase_count: int
    phase_elapsed_s: float
    phase_duration_s: float
    sim_time_s: float
    heads: dict[str, SignalState]
    cars: tuple[CarSnapshot, ...]


class SimulationEngine:
    def __init__(
        self, plan: TimingPlan, seed: int = 0, spawn_rate_per_s: float = 0.25
    ) -> None:
        errors = plan.validate()
        if errors:
            raise ValueError("Invalid plan: " + " ".join(str(e) for e in errors))
        self.plan = plan
        self._pending: TimingPlan | None = None
        self._rng = random.Random(seed)
        self.traffic = TrafficModel(self._rng, rate_per_s=spawn_rate_per_s)
        self.heads = {a: SignalHead(f"{a} head") for a in APPROACHES}
        self._phase_index = 0
        self._elapsed = 0.0
        self._sim_time = 0.0
        self._sync_heads()

    def tick(self, dt_s: float) -> None:
        if dt_s < 0:
            raise ValueError("dt_s must be >= 0")
        remaining = float(dt_s)
        while remaining > _EPS_S:
            duration = self.plan.phases[self._phase_index].duration_s
            step = min(remaining, duration - self._elapsed)
            if step <= 0:  # already exactly on a boundary; advance first
                self._advance_phase()
                continue
            self._elapsed += step
            self._sim_time += step
            self.traffic.update(step, self._approach_states())
            remaining -= step
            if self._elapsed >= duration - _EPS_S:
                self._advance_phase()
        self._sync_heads()

    def set_plan(self, plan: TimingPlan) -> None:
        """Queue a validated plan; it takes over at the next phase boundary."""
        errors = plan.validate()
        if errors:
            raise ValueError("Invalid plan: " + " ".join(str(e) for e in errors))
        self._pending = plan

    def skip_to_next_phase(self) -> None:
        """Debug helper: jump straight to the next phase boundary."""
        self._advance_phase()
        self._sync_heads()

    @property
    def state(self) -> EngineState:
        phase = self.plan.phases[self._phase_index]
        return EngineState(
            phase_index=self._phase_index,
            phase_count=len(self.plan.phases),
            phase_elapsed_s=self._elapsed,
            phase_duration_s=phase.duration_s,
            sim_time_s=self._sim_time,
            heads={name: head.state for name, head in self.heads.items()},
            cars=self.traffic.snapshot(),
        )

    @property
    def pending_plan(self) -> TimingPlan | None:
        """A validated plan queued by set_plan, not yet applied."""
        return self._pending

    def _approach_states(self) -> dict[str, SignalState]:
        phase = self.plan.phases[self._phase_index]
        return {"N": phase.ns, "S": phase.ns, "E": phase.ew, "W": phase.ew}

    def _advance_phase(self) -> None:
        if self._pending is not None:
            self.plan = self._pending
            self._pending = None
            self._phase_index = 0
        else:
            self._phase_index = (self._phase_index + 1) % len(self.plan.phases)
        self._elapsed = 0.0

    def _sync_heads(self) -> None:
        for name, state in self._approach_states().items():
            self.heads[name].state = state
