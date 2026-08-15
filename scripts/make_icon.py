"""Regenerate PNG icon sizes from assets/icon.svg. Run: python scripts/make_icon.py"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QGuiApplication, QIcon, QImage, QPainter

ASSETS = Path(__file__).resolve().parent.parent / "src" / "traffic_light" / "assets"


def main() -> None:
    app = QGuiApplication([])  # noqa: F841 - needed for QPainter
    source = ASSETS / "icon.svg"
    for size in (256, 512):
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        QIcon(str(source)).paint(painter, 0, 0, size, size)
        painter.end()
        image.save(str(ASSETS / f"icon-{size}.png"))
        print(f"wrote icon-{size}.png")


if __name__ == "__main__":
    main()
