"""WCAG contrast checks for text-bearing theme tokens (AA normal text, 4.5:1)."""

from __future__ import annotations

import pytest

from traffic_light.ui import theme

MIN_RATIO = 4.5


def _relative_luminance(hex_color: str) -> float:
    r, g, b = (
        int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)
    )

    def linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = linear(r), linear(g), linear(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    la, lb = _relative_luminance(a), _relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize("theme_name", sorted(theme.THEMES))
@pytest.mark.parametrize(
    "fg_key,bg_key",
    [
        ("foreground", "background"),  # panel and label text
        ("on_primary", "primary"),  # button text
        ("error", "background"),  # plan editor validation messages
    ],
)
def test_text_tokens_meet_aa(theme_name, fg_key, bg_key):
    t = theme.THEMES[theme_name]
    ratio = contrast_ratio(t[fg_key], t[bg_key])
    assert ratio >= MIN_RATIO, (
        f"{theme_name}: {fg_key} on {bg_key} is {ratio:.2f}:1"
    )
