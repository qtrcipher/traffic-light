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
MAX_DIFF_CHANNEL_FRACTION = 0.02  # of all channels, may exceed the tolerance

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
    fraction = diff_channel_fraction(
        rendered / f"main_{lang}_{theme}.png",
        SNAPSHOTS / f"main_{lang}_{theme}.png",
    )
    assert fraction <= MAX_DIFF_CHANNEL_FRACTION, (
        f"main {lang}/{theme}: {fraction:.4%} of channels differ"
    )


def test_guide_snapshot_ar_dark(rendered):
    fraction = diff_channel_fraction(
        rendered / "guide_ar_dark.png", SNAPSHOTS / "guide_ar_dark.png"
    )
    assert fraction <= MAX_DIFF_CHANNEL_FRACTION, (
        f"guide ar/dark: {fraction:.4%} of channels differ"
    )
