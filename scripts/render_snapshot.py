#!/usr/bin/env python3
"""Render deterministic snapshot PNGs for one language (EN or AR).

One process per language because translation + RTL layout direction are set at
startup. Renders the main window in light and dark (same frozen engine state),
and — for AR — the quick-guide dialog (RTL exercise). Used by
scripts/regen_snapshots.py and tests/test_snapshots.py so both go through the
exact same code path.

Determinism: fixed window size, fixed engine seed (MainWindow uses seed=1),
engine pre-ticked 159 x 0.1 s to sim time 15.9 s, and the real-time QTimer
stopped before it can fire, so the grabbed state is always the same.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QLocale, QSettings, Qt

MAIN_SIZE = (1100, 760)
DASHBOARD_SIZE = (720, 760)
GUIDE_SIZE = (520, 280)
# 220 x 0.1 s = 22.0 s of simulated time: the sim sits in phase 2 (NS amber,
# EW red) with the pedestrian EW demand (requested at t=0) being served —
# the EW crosswalks show WALK in the main snapshots.
PRE_TICKS = 220


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["en", "ar"], required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    # Isolate QSettings so renders never touch the developer's real settings.
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, tempfile.mkdtemp()
    )

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    from traffic_light import app as app_module
    from traffic_light.ui import settings as prefs
    from traffic_light.ui import theme

    app_module.install_fonts(app)  # same bundled fonts as the real app

    prefs.set_language(args.lang)
    prefs.set_theme("light")
    QLocale.setDefault(QLocale(args.lang))
    if args.lang == "ar":
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app._translator = app_module._load_translator(app, args.lang)  # noqa: SLF001
    app.setStyleSheet(theme.stylesheet("light"))

    from traffic_light.ui.main_window import MainWindow

    window = MainWindow()
    window._timer.stop()  # noqa: SLF001 — freeze the sim before any tick fires
    window.resize(*MAIN_SIZE)
    window.engine.request_pedestrian("EW")  # served at the next EW-red phase
    for _ in range(PRE_TICKS):
        window.engine.tick(0.1)
    state = window.engine.state
    window.canvas.update()
    window.canvas.update_a11y(state)
    window.panel.update_status(state)
    window.show()
    app.processEvents()

    args.outdir.mkdir(parents=True, exist_ok=True)
    window.grab().save(str(args.outdir / f"main_{args.lang}_light.png"))

    # Dashboard mirrors the same frozen state; opened through the real toggle.
    window._toggle_dashboard(True)  # noqa: SLF001
    window.dashboard.resize(*DASHBOARD_SIZE)
    window.dashboard.show()
    app.processEvents()
    window.dashboard.grab().save(str(args.outdir / f"dashboard_{args.lang}_light.png"))

    window.apply_theme("dark")
    app.processEvents()
    window.grab().save(str(args.outdir / f"main_{args.lang}_dark.png"))
    window.dashboard.grab().save(str(args.outdir / f"dashboard_{args.lang}_dark.png"))

    if args.lang == "ar":
        from traffic_light.ui.guide import GuideDialog

        dialog = GuideDialog(window)
        dialog.setFixedSize(*GUIDE_SIZE)
        dialog.show()
        app.processEvents()
        dialog.grab().save(str(args.outdir / "guide_ar_dark.png"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
