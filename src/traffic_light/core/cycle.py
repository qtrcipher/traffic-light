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


@dataclass(frozen=True)
class ValidationIssue:
    """One plan problem. ``code`` is stable so the UI can translate it;
    ``phase`` is the 1-based phase number when the problem is phase-specific.
    ``str(issue)`` is the English fallback, used in file-load errors."""

    code: str
    phase: int | None = None

    def __str__(self) -> str:
        if self.code == "no_phases":
            return "Plan has no phases."
        if self.code == "nonpositive_duration":
            return f"Phase {self.phase}: duration must be positive."
        if self.code == "amber_too_short":
            return f"Phase {self.phase}: amber must be at least {MIN_AMBER_S:g}s."
        if self.code == "both_axes_green":
            return f"Phase {self.phase}: NS and EW cannot both be green."
        if self.code == "cycle_too_short":
            return f"Cycle must be at least {MIN_CYCLE_S:g}s."
        return self.code


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

    def validate(self) -> list[ValidationIssue]:
        """Return a list of problems; empty means the plan is valid."""
        issues: list[ValidationIssue] = []
        if not self.phases:
            issues.append(ValidationIssue("no_phases"))
            return issues
        for i, p in enumerate(self.phases):
            n = i + 1
            if p.duration_s <= 0:
                issues.append(ValidationIssue("nonpositive_duration", n))
            if (p.ns is SignalState.AMBER or p.ew is SignalState.AMBER) and p.duration_s < MIN_AMBER_S:
                issues.append(ValidationIssue("amber_too_short", n))
            if p.ns is SignalState.GREEN and p.ew is SignalState.GREEN:
                issues.append(ValidationIssue("both_axes_green", n))
        if self.cycle_s < MIN_CYCLE_S and any(
            SignalState.GREEN in (p.ns, p.ew) for p in self.phases
        ):
            issues.append(ValidationIssue("cycle_too_short"))
        return issues

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
            raise ValueError("Invalid plan: " + " ".join(str(e) for e in errors))
        return plan

    @classmethod
    def load(cls, path: Path) -> TimingPlan:
        return cls.from_json(path.read_text(encoding="utf-8"))

    def save(self, path: Path) -> None:
        path.write_text(self.to_json() + "\n", encoding="utf-8")
