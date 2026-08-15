"""Main window: simulator canvas, control panel, toolbar, ~30 fps timer loop.

One-way data flow: the QTimer scales real elapsed time by the panel's speed,
feeds it to engine.tick, and the canvas/panel re-read the engine snapshot.
UI edits go the other way only as validated TimingPlans via engine.set_plan.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from ..core import presets
from ..core.cycle import TimingPlan
from ..core.engine import SimulationEngine
from . import settings as prefs
from .canvas import IntersectionCanvas
from .guide import GuideDialog
from .panels import ControlPanel
from .plan_editor import PlanEditorDialog

TIMER_INTERVAL_MS = 33  # ~30 fps


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(self.tr("Traffic Light"))
        self.resize(1024, 720)

        self.engine = SimulationEngine(presets.default_plan(), seed=1)
        self.playing = True
        self.speed = 1.0
        self._presenting = False

        self.canvas = IntersectionCanvas(self.engine, prefs.theme())
        self.panel = ControlPanel()
        central = QWidget()
        row = QHBoxLayout(central)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.canvas, 1)
        row.addWidget(self.panel)
        self.setCentralWidget(central)

        toolbar = self.addToolBar(self.tr("Main"))
        toolbar.setObjectName("mainToolbar")
        toolbar.addAction(self.tr("Save plan…"), self._save_plan)
        toolbar.addAction(self.tr("Load plan…"), self._load_plan)
        toolbar.addAction(self.tr("Plan editor…"), self._open_plan_editor)
        toolbar.addAction(self.tr("Presentation mode"), self._enter_presentation)

        view_menu = self.menuBar().addMenu(self.tr("&View"))
        for name in prefs.THEMES:
            action = QAction(prefs.THEMES[name], self, checkable=True)
            action.setChecked(prefs.theme() == name)
            action.triggered.connect(lambda _=False, t=name: self.apply_theme(t))
            view_menu.addAction(action)

        help_menu = self.menuBar().addMenu(self.tr("&Help"))
        help_menu.addAction(self.tr("Quick guide"), self._show_guide)
        help_menu.addAction(self.tr("About Traffic Light"), self._show_about)

        if os.environ.get("TRAFFIC_LIGHT_DEBUG") == "1":
            debug_menu = self.menuBar().addMenu(self.tr("&Debug"))
            debug_menu.addAction(self.tr("Step one phase"), self._debug_step_phase)
            debug_menu.addAction(self.tr("Spawn car burst"), self._debug_spawn_burst)

        self.panel.playToggled.connect(self._set_playing)
        self.panel.speedChanged.connect(self._set_speed)
        self.panel.presetChosen.connect(self._apply_preset)

        # Logical keyboard order: canvas first, then the panel top to bottom.
        QWidget.setTabOrder(self.canvas, self.panel.play_button)
        QWidget.setTabOrder(self.panel.play_button, self.panel.speed_slider)
        QWidget.setTabOrder(self.panel.speed_slider, self.panel.preset_combo)

        QShortcut(QKeySequence(Qt.Key.Key_Space), self, activated=self._toggle_play)
        QShortcut(
            QKeySequence(Qt.Key.Key_F11), self, activated=self._enter_presentation
        )
        QShortcut(
            QKeySequence(Qt.Key.Key_Escape), self, activated=self._exit_presentation
        )

        self._clock = QElapsedTimer()
        self._clock.start()
        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_INTERVAL_MS)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def apply_theme(self, name: str) -> None:
        from . import theme

        prefs.set_theme(name)
        self.window().setStyleSheet(theme.stylesheet(name))
        self.canvas.set_theme(name)

    def _on_tick(self) -> None:
        self._advance(self._clock.restart() / 1000.0)

    def _advance(self, dt_s: float) -> None:
        """Advance the engine by a real-time delta (scaled by speed), repaint."""
        if self.playing:
            self.engine.tick(dt_s * self.speed)
        self.canvas.update()
        self.canvas.update_a11y(self.engine.state)
        self.panel.update_status(self.engine.state)

    def _set_playing(self, playing: bool) -> None:
        self.playing = playing

    def _toggle_play(self) -> None:
        self.panel.play_button.click()

    def _set_speed(self, speed: float) -> None:
        self.speed = speed

    def _apply_preset(self, key: str) -> None:
        self.engine.set_plan(presets.PRESETS[key]())

    def _save_plan(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save plan"),
            "",
            self.tr("Traffic light plans (*.json)"),
        )
        if path:
            self.engine.plan.save(Path(path))

    def _load_plan(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Load plan"),
            "",
            self.tr("Traffic light plans (*.json)"),
        )
        if path:
            self._load_plan_from(path)

    def _load_plan_from(self, path: str) -> None:
        """Load a plan file. On failure, offer to restore the default plan."""
        try:
            plan = TimingPlan.load(Path(path))
        except (OSError, ValueError) as exc:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Critical)
            box.setWindowTitle(self.tr("Load plan"))
            box.setText(self.tr("Could not load the plan file."))
            box.setDetailedText(str(exc))
            restore = box.addButton(
                self.tr("Restore default plan"), QMessageBox.ButtonRole.AcceptRole
            )
            box.addButton(self.tr("Cancel"), QMessageBox.ButtonRole.RejectRole)
            box.exec()
            if box.clickedButton() is restore:
                self.engine.set_plan(presets.default_plan())
            return
        self.engine.set_plan(plan)

    def _open_plan_editor(self) -> None:
        dialog = PlanEditorDialog(self.engine.plan, self)
        if dialog.exec():
            self.engine.set_plan(dialog.plan())

    def _show_guide(self) -> None:
        GuideDialog(self).exec()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            self.tr("About Traffic Light"),
            self.tr(
                "Open-source traffic light intersection simulator for "
                "classrooms.\nhttps://github.com/qtrcipher/traffic-light"
            ),
        )

    def _enter_presentation(self) -> None:
        if self._presenting:
            return
        self._presenting = True
        self.panel.hide()
        self.showFullScreen()

    def _exit_presentation(self) -> None:
        if not self._presenting:
            return
        self._presenting = False
        self.showNormal()
        self.panel.show()

    def _debug_step_phase(self) -> None:
        self.engine.skip_to_next_phase()
        self.canvas.update()
        self.canvas.update_a11y(self.engine.state)
        self.panel.update_status(self.engine.state)

    def _debug_spawn_burst(self) -> None:
        self.engine.traffic.spawn_burst()
        self.canvas.update()
