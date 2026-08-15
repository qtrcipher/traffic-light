"""Design tokens from the Phase 0 design direction (docs/plans/2026-08-15-*).

Flat + soft rounding; indigo chrome; fixed signal colors; light theme and a
dark "asphalt" theme. Widgets read colors from here — no raw hex elsewhere.
"""

from __future__ import annotations

# Signal colors are semantic and identical in both themes.
SIGNAL_RED = "#DC2626"
SIGNAL_AMBER = "#F59E0B"
SIGNAL_GREEN = "#16A34A"

RADIUS_PX = 16

# Muted car paint colors for the canvas (indexed by core.traffic color_index).
CAR_COLORS = ("#64748B", "#7D8F69", "#5B7C99", "#B26E7E", "#B4714E", "#8A6E94")

LIGHT = {
    "primary": "#4F46E5",
    "on_primary": "#FFFFFF",
    "accent": "#EA580C",
    "background": "#EEF2FF",
    "foreground": "#1E1B4B",
    "muted": "#EBEEF8",
    "border": "#C7D2FE",
    "road": "#9CA3AF",
    "road_line": "#F9FAFB",
    "housing": "#1F2937",
    "error": "#B91C1C",
}

DARK = {
    "primary": "#818CF8",
    "on_primary": "#1E1B4B",
    "accent": "#EA580C",
    "background": "#1E1B4B",
    "foreground": "#EEF2FF",
    "muted": "#2E2A5E",
    "border": "#4338CA",
    "road": "#111827",
    "road_line": "#4B5563",
    "housing": "#030712",
    "error": "#F87171",
}

THEMES = {"light": LIGHT, "dark": DARK}


def stylesheet(theme: str) -> str:
    """Application-level stylesheet for the given theme name."""
    t = THEMES[theme]
    return f"""
    QWidget {{
        background: {t['background']};
        color: {t['foreground']};
        font-size: 16px;
    }}
    QPushButton {{
        background: {t['primary']};
        color: {t['on_primary']};
        border: none;
        border-radius: {RADIUS_PX}px;
        padding: 8px 16px;
    }}
    QPushButton:hover {{ opacity: 0.9; }}
    QDialog, QComboBox, QLineEdit {{
        border: 1px solid {t['border']};
        border-radius: {RADIUS_PX}px;
    }}
    QPushButton:focus, QComboBox:focus, QLineEdit:focus, QDoubleSpinBox:focus,
    QTableWidget:focus, QSlider:focus, QCheckBox:focus {{
        border: 2px solid {t['accent']};
    }}
    """
