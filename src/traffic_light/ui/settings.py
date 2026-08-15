"""Language + theme settings, persisted via QSettings."""

from __future__ import annotations

from PySide6.QtCore import QSettings

_ORG = "TrafficLight"
_APP = "TrafficLight"

LANGUAGES = {"en": "English", "ar": "العربية"}
THEMES = {"light": "Light", "dark": "Dark"}

KEY_LANGUAGE = "ui/language"
KEY_THEME = "ui/theme"
KEY_GUIDE_DISMISSED = "ui/guide_dismissed"


def settings() -> QSettings:
    return QSettings(_ORG, _APP)


def language() -> str | None:
    """Persisted language code, or None if never chosen (first launch)."""
    value = settings().value(KEY_LANGUAGE)
    return str(value) if value else None


def set_language(code: str) -> None:
    if code not in LANGUAGES:
        raise ValueError(f"Unknown language: {code}")
    settings().setValue(KEY_LANGUAGE, code)


def theme() -> str:
    value = str(settings().value(KEY_THEME, "light"))
    return value if value in THEMES else "light"


def set_theme(name: str) -> None:
    if name not in THEMES:
        raise ValueError(f"Unknown theme: {name}")
    settings().setValue(KEY_THEME, name)


def guide_dismissed() -> bool:
    """True once the user checked "Don't show again" on the quick guide."""
    value = settings().value(KEY_GUIDE_DISMISSED, False)
    return value if isinstance(value, bool) else str(value).lower() == "true"


def set_guide_dismissed(dismissed: bool = True) -> None:
    settings().setValue(KEY_GUIDE_DISMISSED, dismissed)
