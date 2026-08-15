"""Hardware… panel: connect the simulator to an Arduino light over serial.

Non-modal dialog: pick a serial port (or the virtual demo device), connect,
and the sink is registered on the main window's StateBridge — from then on it
receives every signal change. Errors (unplugged cable, busy port) show in the
status label and never disturb the simulator.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from serial.tools import list_ports

from ..core.signal import SignalState
from ..hardware.serial_sink import SerialSink
from ..hardware.virtual import VirtualSink
from . import settings as prefs
from . import theme

VIRTUAL_PORT = "virtual"
_STATUS_POLL_MS = 500


class HardwarePanel(QDialog):
    def __init__(
        self,
        bridge,
        get_heads: Callable[[], dict[str, SignalState]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Hardware"))
        self.setModal(False)
        self._bridge = bridge
        self._get_heads = get_heads
        self._sink = None

        layout = QVBoxLayout(self)
        port_row = QHBoxLayout()
        port_row.addWidget(QLabel(self.tr("Port")))
        self.port_combo = QComboBox()
        self.port_combo.setAccessibleName(self.tr("Serial port"))
        self.refresh_button = QPushButton(self.tr("Refresh"))
        self.refresh_button.clicked.connect(self.refresh_ports)
        port_row.addWidget(self.port_combo, 1)
        port_row.addWidget(self.refresh_button)
        layout.addLayout(port_row)

        self.connect_button = QPushButton(self.tr("Connect"))
        self.connect_button.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self.connect_button)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setAccessibleName(self.tr("Hardware status"))
        layout.addWidget(self.status_label)

        self._status_timer = QTimer(self)
        self._status_timer.setInterval(_STATUS_POLL_MS)
        self._status_timer.timeout.connect(self._poll_status)

        self.refresh_ports()
        self._set_status(self.tr("Disconnected"))

    def refresh_ports(self) -> None:
        self.port_combo.clear()
        self.port_combo.addItem(
            self.tr("Virtual device (demo)"), userData=VIRTUAL_PORT
        )
        for info in list_ports.comports():
            self.port_combo.addItem(
                f"{info.device} — {info.description}", userData=info.device
            )

    def _on_connect_clicked(self) -> None:
        if self._sink is None:
            self._connect()
        else:
            self._disconnect()

    def _connect(self) -> None:
        port = self.port_combo.currentData()
        sink = VirtualSink() if port == VIRTUAL_PORT else SerialSink(port)
        if not sink.open():
            self._set_status(
                self.tr("Error: {message}").format(message=sink.error), error=True
            )
            return
        self._sink = sink
        self._bridge.add_sink(sink)
        sink.on_state(self._get_heads())  # replay the live state immediately
        self.connect_button.setText(self.tr("Disconnect"))
        self.port_combo.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self._set_status(
            self.tr("Connected to {port}").format(
                port=self.port_combo.currentText()
            )
        )
        self._status_timer.start()

    def _disconnect(self) -> None:
        self._status_timer.stop()
        if self._sink is not None:
            self._bridge.remove_sink(self._sink)
            self._sink.close()
            self._sink = None
        self.connect_button.setText(self.tr("Connect"))
        self.port_combo.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self._set_status(self.tr("Disconnected"))

    def _poll_status(self) -> None:
        """Reflect sink errors live (e.g. cable unplugged mid-session)."""
        if self._sink is not None and self._sink.error:
            self._set_status(
                self.tr("Error: {message}").format(message=self._sink.error),
                error=True,
            )

    def _set_status(self, text: str, error: bool = False) -> None:
        self.status_label.setText(text)
        if error:
            error_color = theme.THEMES[prefs.theme()]["error"]
            self.status_label.setStyleSheet(f"color: {error_color};")
        else:
            self.status_label.setStyleSheet("")

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        self._disconnect()
        super().closeEvent(event)
