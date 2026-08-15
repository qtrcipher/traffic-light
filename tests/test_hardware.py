"""Hardware pillar tests: line protocol, sinks, panel logic."""

from __future__ import annotations

import pytest
import serial

from traffic_light.core.signal import SignalState as S
from traffic_light.hardware.protocol import decode_line, encode_line
from traffic_light.hardware.serial_sink import SerialSink
from traffic_light.hardware.virtual import VirtualSink
from traffic_light.ui.bridge import StateBridge
from traffic_light.ui.hardware_panel import VIRTUAL_PORT, HardwarePanel

HEADS_GREEN_NS = {"N": S.GREEN, "S": S.GREEN, "E": S.RED, "W": S.RED}


# --- protocol ---


def test_encode_line_fixed_order():
    assert encode_line(HEADS_GREEN_NS) == b"N:G;S:G;E:R;W:R\n"


def test_encode_line_all_states():
    heads = {"N": S.RED, "S": S.AMBER, "E": S.GREEN, "W": S.OFF}
    assert encode_line(heads) == b"N:R;S:A;E:G;W:O\n"


def test_round_trip():
    heads = {"N": S.AMBER, "S": S.OFF, "E": S.GREEN, "W": S.RED}
    assert decode_line(encode_line(heads)) == heads


def test_decode_accepts_str_and_missing_newline():
    assert decode_line("N:G;S:G;E:R;W:R") == HEADS_GREEN_NS
    assert decode_line(b"N:G;S:G;E:R;W:R\r\n") == HEADS_GREEN_NS


def test_encode_missing_head_rejected():
    with pytest.raises(ValueError):
        encode_line({"N": S.GREEN})


def test_encode_unknown_state_rejected():
    with pytest.raises(ValueError):
        encode_line({"N": "purple", "S": S.RED, "E": S.RED, "W": S.RED})


@pytest.mark.parametrize(
    "bad",
    [
        b"",  # empty
        b"N:G;S:G;E:R\n",  # too few heads
        b"N:G;S:G;E:R;W:R;X:G\n",  # too many heads
        b"N:G;S:G;W:R;E:R\n",  # wrong head order
        b"N-G;S:G;E:R;W:R\n",  # missing colon
        b"N:G;S:G;E:R;W:X\n",  # unknown state letter
        b"N:GG;S:G;E:R;W:R\n",  # wrong token length
        b"N:G;S:G;E:R;W:\xff\n",  # non-ASCII
    ],
)
def test_decode_malformed_rejected(bad):
    with pytest.raises(ValueError):
        decode_line(bad)


# --- VirtualSink ---


def test_virtual_sink_records_states():
    sink = VirtualSink()
    assert sink.connected
    sink.on_state(HEADS_GREEN_NS)
    sink.on_state({"N": S.RED, "S": S.RED, "E": S.GREEN, "W": S.GREEN})
    assert sink.received == [
        HEADS_GREEN_NS,
        {"N": S.RED, "S": S.RED, "E": S.GREEN, "W": S.GREEN},
    ]
    sink.close()
    assert sink.error is None


# --- SerialSink with mocked serial.Serial ---


class FakeSerial:
    instances: list[FakeSerial] = []
    fail_on_write = False
    fail_on_open = False

    def __init__(self, port, baudrate, timeout=None, write_timeout=None):
        if FakeSerial.fail_on_open:
            raise serial.SerialException(f"cannot open {port}")
        self.port = port
        self.baudrate = baudrate
        self.writes: list[bytes] = []
        self.closed = False
        FakeSerial.instances.append(self)

    def write(self, data):
        if FakeSerial.fail_on_write:
            raise serial.SerialException("device disconnected")
        self.writes.append(data)

    def close(self):
        self.closed = True


@pytest.fixture
def fake_serial(monkeypatch):
    FakeSerial.instances = []
    FakeSerial.fail_on_write = False
    FakeSerial.fail_on_open = False
    monkeypatch.setattr("traffic_light.hardware.serial_sink.serial.Serial", FakeSerial)
    return FakeSerial


def test_serial_sink_lazy_connect_and_writes(fake_serial):
    sink = SerialSink("/dev/ttyUSB0")
    assert not sink.connected
    assert FakeSerial.instances == []  # lazy: nothing opened yet
    sink.on_state(HEADS_GREEN_NS)
    assert sink.connected
    assert FakeSerial.instances[0].writes == [b"N:G;S:G;E:R;W:R\n"]
    sink.close()
    assert FakeSerial.instances[0].closed
    assert not sink.connected


def test_serial_sink_open_failure_sets_error(fake_serial):
    FakeSerial.fail_on_open = True
    sink = SerialSink("/dev/ttyUSB0")
    assert sink.open() is False
    assert "cannot open" in sink.error
    sink.on_state(HEADS_GREEN_NS)  # errored sink stays silent, never raises
    assert FakeSerial.instances == []


def test_serial_sink_write_error_swallowed(fake_serial):
    sink = SerialSink("/dev/ttyUSB0")
    sink.on_state(HEADS_GREEN_NS)
    FakeSerial.fail_on_write = True
    sink.on_state(HEADS_GREEN_NS)  # must not raise into the bridge
    assert "disconnected" in sink.error
    assert not sink.connected
    sink.on_state(HEADS_GREEN_NS)  # stays silent once errored
    assert len(FakeSerial.instances[0].writes) == 1


# --- panel ---


class FakePortInfo:
    def __init__(self, device, description):
        self.device = device
        self.description = description


@pytest.fixture
def panel(qtbot, monkeypatch):
    monkeypatch.setattr(
        "traffic_light.ui.hardware_panel.list_ports.comports",
        lambda: [FakePortInfo("/dev/ttyUSB0", "USB Serial")],
    )
    bridge = StateBridge()
    widget = HardwarePanel(bridge, lambda: HEADS_GREEN_NS)
    qtbot.addWidget(widget)
    return widget, bridge


def test_panel_lists_virtual_and_serial_ports(panel):
    widget, _ = panel
    assert widget.port_combo.itemData(0) == VIRTUAL_PORT
    assert widget.port_combo.itemData(1) == "/dev/ttyUSB0"
    assert "Virtual" in widget.port_combo.itemText(0)


def test_panel_connect_virtual_registers_sink(panel):
    widget, bridge = panel
    widget.connect_button.click()
    assert widget._sink is not None
    assert widget._sink in bridge._sinks
    # The live state was replayed on connect.
    assert widget._sink.received == [HEADS_GREEN_NS]
    assert "Connected" in widget.status_label.text()
    assert widget.connect_button.text() == "Disconnect"

    # Bridge changes flow through.
    bridge.push(type("St", (), {"heads": {"N": S.RED, "S": S.RED, "E": S.GREEN, "W": S.GREEN}})())
    assert len(widget._sink.received) == 2

    widget.connect_button.click()  # disconnect
    assert widget._sink is None
    assert bridge._sinks == []
    assert "Disconnected" in widget.status_label.text()


def test_panel_connect_bad_port_shows_error(panel, monkeypatch):
    widget, bridge = panel
    FakeSerial.fail_on_open = True
    monkeypatch.setattr(
        "traffic_light.hardware.serial_sink.serial.Serial", FakeSerial
    )
    widget.port_combo.setCurrentIndex(1)
    widget.connect_button.click()
    assert widget._sink is None
    assert bridge._sinks == []
    assert "Error" in widget.status_label.text()
    assert "cannot open" in widget.status_label.text()
    assert widget.connect_button.text() == "Connect"


def test_panel_close_disconnects(panel):
    widget, bridge = panel
    widget.connect_button.click()
    assert bridge._sinks
    widget.close()
    assert bridge._sinks == []
    assert widget._sink is None
