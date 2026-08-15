"""Push adapter between the pull-based engine and HardwareSink consumers.

The engine exposes a pull-based ``state`` snapshot; pillars 2 (dashboard) and
3 (hardware controller) want push. MainWindow feeds every tick's snapshot to
``push`` — the bridge fans out ``on_state`` only when the head states actually
changed (phase changes), never 30 times per second. Lives on the UI side so
core/ stays Qt-free and dumb about consumers.
"""

from __future__ import annotations

from ..core.engine import EngineState
from ..core.signal import SignalState


class StateBridge:
    def __init__(self) -> None:
        self._sinks: list = []
        self._last: dict[str, SignalState] | None = None

    def add_sink(self, sink) -> None:
        self._sinks.append(sink)

    def remove_sink(self, sink) -> None:
        if sink in self._sinks:
            self._sinks.remove(sink)

    def push(self, state: EngineState) -> None:
        """Forward to sinks only if the per-head states changed (or first push)."""
        if state.heads == self._last:
            return
        self._last = dict(state.heads)
        for sink in self._sinks:
            sink.on_state(state.heads)

    @property
    def last(self) -> dict[str, SignalState] | None:
        """The most recently broadcast head states (for late-opening sinks)."""
        return dict(self._last) if self._last is not None else None
