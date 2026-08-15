"""Timing plans: phases, validation, JSON (de)serialization.

A TimingPlan is a loop of phases. Each phase gives both axis signal states
(NS and EW) and a duration in seconds. Validation rules are the same ones the
plan editor enforces in the UI — core owns them so they apply to loaded files
too.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .signal import SignalState

MIN_AMBER_S = 1.0
MIN_CYCLE_S = 5.0


@dataclass
class Phase:
    ns: SignalState
    ew: SignalState
    duration_s: float


@dataclass
class TimingPlan:
    name: str
    phases: list[Phase] = field(default_factory=list)

    @property
    def cycle_s(self) -> float:
        return sum(p.duration_s for p in self.phases)

    def validate(self) -> list[str]:
        """Return a list of problems; empty means the plan is valid."""
        errors: list[str] = []
        if not self.phases:
            errors.append("Plan has no phases.")
            return errors
        for i, p in enumerate(self.phases):
            if p.duration_s <= 0:
                errors.append(f"Phase {i + 1}: duration must be positive.")
            if (p.ns is SignalState.AMBER or p.ew is SignalState.AMBER) and p.duration_s < MIN_AMBER_S:
                errors.append(f"Phase {i + 1}: amber must be at least {MIN_AMBER_S:g}s.")
            if p.ns is SignalState.GREEN and p.ew is SignalState.GREEN:
                errors.append(f"Phase {i + 1}: NS and EW cannot both be green.")
        if self.cycle_s < MIN_CYCLE_S and any(
            SignalState.GREEN in (p.ns, p.ew) for p in self.phases
        ):
            errors.append(f"Cycle must be at least {MIN_CYCLE_S:g}s.")
        return errors

    def to_json(self) -> str:
        return json.dumps(
            {
                "name": self.name,
                "phases": [
                    {"ns": p.ns.value, "ew": p.ew.value, "duration_s": p.duration_s}
                    for p in self.phases
                ],
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, text: str) -> TimingPlan:
        """Parse a plan. Raises ValueError on malformed input or failed validation."""
        try:
            data = json.loads(text)
            phases = [
                Phase(SignalState(p["ns"]), SignalState(p["ew"]), float(p["duration_s"]))
                for p in data["phases"]
            ]
            plan = cls(name=str(data["name"]), phases=phases)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid plan file: {exc}") from exc
        errors = plan.validate()
        if errors:
            raise ValueError("Invalid plan: " + " ".join(errors))
        return plan

    @classmethod
    def load(cls, path: Path) -> TimingPlan:
        return cls.from_json(path.read_text(encoding="utf-8"))

    def save(self, path: Path) -> None:
        path.write_text(self.to_json() + "\n", encoding="utf-8")
