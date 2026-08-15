"""Snapshot regression: main window EN/AR x light/dark, guide AR/dark.

Renders through scripts/render_snapshot.py (same code path as
scripts/regen_snapshots.py, so tests always match the committed references)
and compares pixel-wise. Each render is a subprocess: translation and RTL
layout direction can only be set before widgets are created.

Tolerance: per-channel difference up to CHANNEL_TOLERANCE is ignored, and up
to MAX_DIFF_CHANNEL_FRACTION of all channels may exceed it. Font rasterization
differs across OSes and CI runners, so antialiased text edges will never match
pixel-perfect; the canvas (roads, signals, cars) is font-independent and fully
deterministic, which is what these snapshots primarily protect.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from PySide6.QtGui import QImage

SNAPSHOTS = Path(__file__).parent / "snapshots"
RENDER = Path(__file__).parent.parent / "scripts" / "render_snapshot.py"

CHANNEL_TOLERANCE = 32  # per-channel delta ignored entirely
# Windows runners land at ~2.9% (Segoe UI fallback vs. the reference machine's
# fonts), so the budget needs headroom beyond that. Real breakage — wrong
# theme, missing RTL mirror, blank canvas — moves tens of percent.
MAX_DIFF_CHANNEL_FRACTION = 0.05  # of all channels, may exceed the tolerance

# Per-image tolerance overrides. With the bundled fonts (Atkinson Hyperlegible
# + IBM Plex Sans Arabic), glyph SHAPES are identical on every OS; what remains
# is rasterizer antialiasing (CoreText / FreeType / DirectWrite), which scales
# with glyph area. Measured macOS-reference vs Ubuntu-Docker (2026-08-15):
#   main 2.4–4.3% · dashboard en 3.8–5.0% · dashboard ar 7.9–11.5% · guide 17.4%
# Budgets = observation + headroom for the third rasterizer (Windows). Real
# breakage moves far more: one wrong dashboard lamp ~15% of channels, wrong
# theme / blank / missing RTL mirror tens of percent. The AR dashboards sit at
# that lamp floor, so they are catastrophic-breakage smoke tests; the EN
# dashboards (10% budget) stay the sensitive structural check — lamp layout
# and colors are language-independent.
DIFF_FRACTION_OVERRIDES = {
    "guide_ar_dark.png": 0.25,
    "dashboard_en_light.png": 0.10,
    "dashboard_en_dark.png": 0.10,
    "dashboard_ar_light.png": 0.15,
    "dashboard_ar_dark.png": 0.15,
    # AR chrome (menus, panel labels) measures 4.3–4.4% on Ubuntu — under the
    # 5% goal but close; 7% is headroom for DirectWrite on Windows, still far
    # below any real breakage.
    "main_ar_light.png": 0.07,
    "main_ar_dark.png": 0.07,
}

MAIN_COMBOS = [
    (lang, theme)
    for lang in ("en", "ar")
    for theme in ("light", "dark")
]


def render(tmp_path: Path, lang: str) -> None:
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    subprocess.run(
        [sys.executable, str(RENDER), "--lang", lang, "--outdir", str(tmp_path)],
        check=True,
        env=env,
        capture_output=True,
    )


def diff_channel_fraction(actual: Path, expected: Path) -> float:
    a = QImage(str(actual)).convertToFormat(QImage.Format.Format_RGB888)
    b = QImage(str(expected)).convertToFormat(QImage.Format.Format_RGB888)
    assert a.size() == b.size(), f"size mismatch: {a.size()} vs {b.size()}"
    stride = a.bytesPerLine()
    raw_a = a.bits().tobytes()
    raw_b = b.bits().tobytes()
    bad = 0
    total = 0
    for y in range(a.height()):
        row = slice(y * stride, y * stride + a.width() * 3)
        for x, z in zip(raw_a[row], raw_b[row]):
            total += 1
            if abs(x - z) > CHANNEL_TOLERANCE:
                bad += 1
    return bad / total


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> Path:
    """Render all snapshot combos once (2 subprocesses: en, ar)."""
    outdir = tmp_path_factory.mktemp("rendered_snapshots")
    for lang in ("en", "ar"):
        render(outdir, lang)
    return outdir


@pytest.mark.parametrize("lang,theme", MAIN_COMBOS)
def test_main_window_snapshot(rendered, lang, theme):
    name = f"main_{lang}_{theme}.png"
    fraction = diff_channel_fraction(rendered / name, SNAPSHOTS / name)
    allowed = DIFF_FRACTION_OVERRIDES.get(name, MAX_DIFF_CHANNEL_FRACTION)
    assert fraction <= allowed, (
        f"main {lang}/{theme}: {fraction:.4%} of channels differ"
    )


@pytest.mark.parametrize("lang,theme", MAIN_COMBOS)
def test_dashboard_snapshot(rendered, lang, theme):
    name = f"dashboard_{lang}_{theme}.png"
    fraction = diff_channel_fraction(rendered / name, SNAPSHOTS / name)
    allowed = DIFF_FRACTION_OVERRIDES.get(name, MAX_DIFF_CHANNEL_FRACTION)
    assert fraction <= allowed, (
        f"dashboard {lang}/{theme}: {fraction:.4%} of channels differ"
    )


def test_guide_snapshot_ar_dark(rendered):
    name = "guide_ar_dark.png"
    fraction = diff_channel_fraction(rendered / name, SNAPSHOTS / name)
    allowed = DIFF_FRACTION_OVERRIDES.get(name, MAX_DIFF_CHANNEL_FRACTION)
    assert fraction <= allowed, f"guide ar/dark: {fraction:.4%} of channels differ"
