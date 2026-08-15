#!/usr/bin/env python3
"""Regenerate the reference snapshot PNGs under tests/snapshots/.

Run this on the reference machine whenever the UI intentionally changes:

    .venv/bin/python scripts/regen_snapshots.py

Spawns scripts/render_snapshot.py once per language (a fresh process is needed
for translation + RTL to take effect) and writes the committed references.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "tests" / "snapshots"
RENDER = ROOT / "scripts" / "render_snapshot.py"

LANGUAGES = ("en", "ar")


def render(lang: str, outdir: Path) -> None:
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    subprocess.run(
        [sys.executable, str(RENDER), "--lang", lang, "--outdir", str(outdir)],
        check=True,
        env=env,
    )


def main() -> int:
    for lang in LANGUAGES:
        render(lang, SNAPSHOTS)
    written = sorted(p.name for p in SNAPSHOTS.glob("*.png"))
    print(f"wrote {len(written)} snapshots to {SNAPSHOTS}:")
    for name in written:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
