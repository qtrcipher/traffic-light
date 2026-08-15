"""Wire protocol between the app and an Arduino-based traffic light.

One line per state change, fixed head order, one letter per state::

    N:G;S:G;E:R;W:R\\n

Letters: R=red, A=amber, G=green, O=off. The decoder is the reference for the
Arduino sketch (hardware/arduino/traffic_light.ino) and is used by tests.
Qt-free, like everything under core/ and hardware/.
"""

from __future__ import annotations

from traffic_light.core.signal import SignalState

HEAD_ORDER = ("N", "S", "E", "W")

_STATE_LETTERS = {
    SignalState.RED: "R",
    SignalState.AMBER: "A",
    SignalState.GREEN: "G",
    SignalState.OFF: "O",
}
_LETTER_STATES = {letter: state for state, letter in _STATE_LETTERS.items()}


def encode_line(heads: dict[str, SignalState]) -> bytes:
    """Encode the four head states as one protocol line (ASCII, \\n-terminated)."""
    parts = []
    for head in HEAD_ORDER:
        if head not in heads:
            raise ValueError(f"missing head: {head!r}")
        try:
            letter = _STATE_LETTERS[heads[head]]
        except KeyError:
            raise ValueError(f"unknown signal state: {heads[head]!r}") from None
        parts.append(f"{head}:{letter}")
    return (";".join(parts) + "\n").encode("ascii")


def decode_line(data: bytes | str) -> dict[str, SignalState]:
    """Decode one protocol line. Raises ValueError on malformed input."""
    if isinstance(data, bytes):
        try:
            text = data.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError(f"line is not ASCII: {exc}") from exc
    else:
        text = data
    text = text.rstrip("\n").rstrip("\r")
    tokens = text.split(";")
    if len(tokens) != len(HEAD_ORDER):
        raise ValueError(f"expected {len(HEAD_ORDER)} heads, got {len(tokens)}")
    heads: dict[str, SignalState] = {}
    for head, token in zip(HEAD_ORDER, tokens):
        if len(token) != 3 or token[1] != ":" or token[0] != head:
            raise ValueError(f"malformed token for head {head!r}: {token!r}")
        letter = token[2]
        if letter not in _LETTER_STATES:
            raise ValueError(f"unknown state letter: {letter!r}")
        heads[head] = _LETTER_STATES[letter]
    return heads
