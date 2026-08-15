"""Arabic copy audit: numerals in the phase readout stay Western (0-9).

Classroom measurement convention: timings like "15.9 s of 20.0 s" must not be
rendered in Arabic-Indic digits (٠-٩) when the UI is Arabic. The readout is
formatted in Python (str.format always emits Latin digits), this test locks
that in. Plural forms: an audit of all user-visible strings found no %n-style
plural cases (numbers appear only in "Phase {n} of {total}" and timings,
where no noun is pluralized), so no Qt Linguist numerusform entries exist.
"""

from __future__ import annotations

from PySide6.QtCore import QLocale

from traffic_light.core import presets
from traffic_light.core.engine import SimulationEngine
from traffic_light.ui.panels import ControlPanel

ARABIC_INDIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"


def test_phase_readout_uses_western_digits_under_ar_locale(qtbot):
    previous = QLocale()
    QLocale.setDefault(QLocale("ar"))
    try:
        engine = SimulationEngine(presets.default_plan(), seed=0)
        for _ in range(159):
            engine.tick(0.1)  # 15.9 s — same sim time as the snapshots
        panel = ControlPanel()
        qtbot.addWidget(panel)
        panel.update_status(engine.state)

        assert "15.9" in panel.time_label.text()
        assert "20.0" in panel.time_label.text()
        assert "1" in panel.phase_label.text()
        assert "6" in panel.phase_label.text()
        for text in (panel.time_label.text(), panel.phase_label.text()):
            assert not any(d in text for d in ARABIC_INDIC_DIGITS), text
    finally:
        QLocale.setDefault(previous)


def test_speed_label_uses_western_digits(qtbot):
    QLocale.setDefault(QLocale("ar"))
    try:
        panel = ControlPanel()
        qtbot.addWidget(panel)
        panel.speed_slider.setValue(50)
        assert panel.speed_label.text() == "0.5×"
        assert not any(d in panel.speed_label.text() for d in ARABIC_INDIC_DIGITS)
    finally:
        QLocale.setDefault(QLocale.c())
