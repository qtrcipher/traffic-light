"""SerialSink: drive a real Arduino traffic light over USB serial.

Implements the HardwareSink protocol. Connects lazily (first state change, or
an explicit ``open()`` from the UI). Hardware failures must never propagate
into the StateBridge — the simulator keeps running when the cable is yanked —
so every serial error is swallowed into ``self.error`` for the UI to display.
"""

from __future__ import annotations

import serial

from traffic_light.core.signal import SignalState
from traffic_light.hardware.protocol import encode_line

_ERRORS = (OSError, serial.SerialException)


class SerialSink:
    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self.port = port
        self.baudrate = baudrate
        self.error: str | None = None
        self._serial: serial.Serial | None = None

    @property
    def connected(self) -> bool:
        return self._serial is not None and self.error is None

    def open(self) -> bool:
        """Open the port now. Returns success; on failure sets self.error."""
        if self._serial is not None:
            return self.error is None
        try:
            self._serial = serial.Serial(
                self.port, self.baudrate, timeout=1, write_timeout=1
            )
        except _ERRORS as exc:
            self.error = str(exc)
            self._serial = None
        return self.error is None

    def on_state(self, heads: dict[str, SignalState]) -> None:
        if self.error is not None:
            return  # errored sink stays silent until reopened
        try:
            if not self.open():
                return
            self._serial.write(encode_line(heads))
        except _ERRORS as exc:
            self.error = str(exc)
            self._close_quietly()

    def close(self) -> None:
        self._close_quietly()
        self.error = None

    def _close_quietly(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except _ERRORS:
                pass
            self._serial = None
