"""VirtualSink: a loopback HardwareSink for classrooms without hardware.

Records every state it receives (``.received``) and logs each one — the demo
and test path for the Hardware… panel's "Virtual device" entry. Exposes the
same open/close/error surface as SerialSink so the panel treats them alike.
"""

from __future__ import annotations

import logging

from traffic_light.core.signal import SignalState
from traffic_light.hardware.protocol import encode_line

_logger = logging.getLogger(__name__)


class VirtualSink:
    def __init__(self) -> None:
        self.received: list[dict[str, SignalState]] = []
        self.error: str | None = None

    @property
    def connected(self) -> bool:
        return True

    def open(self) -> bool:
        return True

    def on_state(self, heads: dict[str, SignalState]) -> None:
        self.received.append(dict(heads))
        _logger.info("virtual light: %s", encode_line(heads).decode("ascii").strip())

    def close(self) -> None:
        self.error = None
