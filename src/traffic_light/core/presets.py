"""Built-in timing plans shown in the toolbar."""

from __future__ import annotations

from .cycle import Phase, TimingPlan
from .signal import SignalState as S


def default_plan() -> TimingPlan:
    """Standard fixed-time 4-way cycle."""
    return TimingPlan(
        name="Default",
        phases=[
            Phase(S.GREEN, S.RED, 20.0),
            Phase(S.AMBER, S.RED, 3.0),
            Phase(S.RED, S.RED, 1.5),  # all-red clearance
            Phase(S.RED, S.GREEN, 20.0),
            Phase(S.RED, S.AMBER, 3.0),
            Phase(S.RED, S.RED, 1.5),
        ],
    )


def rush_hour_plan() -> TimingPlan:
    """Longer NS green for the heavier axis."""
    return TimingPlan(
        name="Rush hour",
        phases=[
            Phase(S.GREEN, S.RED, 35.0),
            Phase(S.AMBER, S.RED, 3.0),
            Phase(S.RED, S.RED, 1.5),
            Phase(S.RED, S.GREEN, 15.0),
            Phase(S.RED, S.AMBER, 3.0),
            Phase(S.RED, S.RED, 1.5),
        ],
    )


def night_flash_plan() -> TimingPlan:
    """Flashing amber both ways (caution), as used at night."""
    return TimingPlan(
        name="Night flash",
        phases=[
            Phase(S.AMBER, S.AMBER, 1.0),
            Phase(S.OFF, S.OFF, 1.0),
        ],
    )


PRESETS = {
    "default": default_plan,
    "rush_hour": rush_hour_plan,
    "night_flash": night_flash_plan,
}
