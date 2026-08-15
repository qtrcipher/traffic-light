"""Hardware pillar seam — defined in Phase 1, implemented later.

The dashboard (pillar 2) and hardware controller (pillar 3) both consume
signal state through this protocol, so they plug in without touching core.
"""

from __future__ import annotations

from typing import Protocol

from traffic_light.core.signal import SignalState


class HardwareSink(Protocol):
    """Receives the full signal state whenever it changes."""

    def on_state(self, heads: dict[str, SignalState]) -> None:
        """`heads` maps head name (e.g. "N", "S", "E", "W") to its state."""
        ...
