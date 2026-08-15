"""Signal states and signal heads."""

from __future__ import annotations

import enum


class SignalState(enum.Enum):
    """States a signal head can show. `OFF` covers night-flash / powered-down."""

    RED = "red"
    AMBER = "amber"
    GREEN = "green"
    OFF = "off"


class SignalHead:
    """One approach's signal head (e.g. the northbound light)."""

    def __init__(self, name: str, state: SignalState = SignalState.RED) -> None:
        self.name = name
        self.state = state

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"SignalHead({self.name!r}, {self.state.value})"
