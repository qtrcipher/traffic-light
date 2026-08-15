"""Status dashboard + state bridge tests."""

from __future__ import annotations

from traffic_light.core import presets
from traffic_light.core.engine import SimulationEngine
from traffic_light.core.signal import SignalState as S
from traffic_light.ui.bridge import StateBridge
from traffic_light.ui.dashboard import DashboardWindow
from traffic_light.ui.main_window import MainWindow


class RecordingSink:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def on_state(self, heads):
        self.calls.append(dict(heads))


def make_engine() -> SimulationEngine:
    return SimulationEngine(presets.default_plan(), seed=0)


# --- bridge: fires on change only ---


def test_bridge_fires_once_for_unchanged_state():
    engine = make_engine()
    bridge = StateBridge()
    sink = RecordingSink()
    bridge.add_sink(sink)

    bridge.push(engine.state)  # first push: initial state
    assert len(sink.calls) == 1
    for _ in range(30):  # same phase, 30 "ticks" — no refire
        engine.tick(0.1)
        bridge.push(engine.state)
    assert len(sink.calls) == 1


def test_bridge_fires_on_phase_change():
    engine = make_engine()
    bridge = StateBridge()
    sink = RecordingSink()
    bridge.add_sink(sink)
    bridge.push(engine.state)

    engine.skip_to_next_phase()
    bridge.push(engine.state)
    assert len(sink.calls) == 2
    assert sink.calls[-1]["N"] is S.AMBER


def test_bridge_fans_out_and_removes():
    engine = make_engine()
    bridge = StateBridge()
    a, b = RecordingSink(), RecordingSink()
    bridge.add_sink(a)
    bridge.add_sink(b)
    bridge.push(engine.state)
    assert a.calls and b.calls
    bridge.remove_sink(a)
    engine.skip_to_next_phase()
    bridge.push(engine.state)
    assert len(a.calls) == 1
    assert len(b.calls) == 2


def test_bridge_replays_last_state_for_late_sinks():
    engine = make_engine()
    bridge = StateBridge()
    bridge.push(engine.state)
    assert bridge.last == engine.state.heads


# --- dashboard rendering state ---


def test_dashboard_lamps_track_states(qtbot):
    dashboard = DashboardWindow()
    qtbot.addWidget(dashboard)
    dashboard.on_state({"N": S.GREEN, "S": S.GREEN, "E": S.RED, "W": S.RED})
    assert dashboard._lamps["N"]._state is S.GREEN
    assert dashboard._lamps["S"]._state is S.GREEN
    assert dashboard._lamps["E"]._state is S.RED
    assert dashboard._lamps["W"]._state is S.RED


def test_dashboard_accessible_names_live_update(qtbot):
    dashboard = DashboardWindow()
    qtbot.addWidget(dashboard)
    dashboard.on_state({"N": S.GREEN, "S": S.RED, "E": S.AMBER, "W": S.OFF})
    assert dashboard._lamps["N"].accessibleName() == "North signal: green"
    assert dashboard._lamps["S"].accessibleName() == "South signal: red"
    assert dashboard._lamps["E"].accessibleName() == "East signal: amber"
    assert dashboard._lamps["W"].accessibleName() == "West signal: off"


def test_dashboard_readout(qtbot):
    engine = make_engine()
    for _ in range(159):
        engine.tick(0.1)
    dashboard = DashboardWindow()
    qtbot.addWidget(dashboard)
    dashboard.update_status(engine.state)
    assert "1" in dashboard.phase_label.text()
    assert "6" in dashboard.phase_label.text()
    assert "15.9" in dashboard.time_label.text()


def test_dashboard_set_theme(qtbot):
    from traffic_light.ui import theme

    dashboard = DashboardWindow("light")
    qtbot.addWidget(dashboard)
    dashboard.set_theme("dark")
    assert dashboard._lamps["N"]._colors is theme.THEMES["dark"]


# --- main window integration ---


def test_dashboard_toggle_from_main_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.dashboard is None  # not auto-opened at launch

    window.dashboard_action.setChecked(True)
    window._toggle_dashboard(True)
    assert window.dashboard is not None
    assert window.dashboard.isVisible()
    # Opening replays the current state immediately.
    assert window.dashboard._lamps["N"]._state is S.GREEN

    # Bridge drives lamps on phase change.
    window.engine.skip_to_next_phase()
    window._advance(0.0)
    assert window.dashboard._lamps["N"]._state is S.AMBER

    window._toggle_dashboard(False)
    assert not window.dashboard.isVisible()


def test_dashboard_close_unchecks_action(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.dashboard_action.setChecked(True)
    window._toggle_dashboard(True)
    window.dashboard.close()
    assert not window.dashboard_action.isChecked()
