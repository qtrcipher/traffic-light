"""Shared fixtures for UI tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def clean_settings(tmp_path, monkeypatch):
    """Isolate QSettings so tests never touch the developer's real settings."""
    from PySide6.QtCore import QSettings

    from traffic_light.ui import settings as prefs

    monkeypatch.setattr(
        prefs,
        "settings",
        lambda: QSettings(str(tmp_path / "test.ini"), QSettings.Format.IniFormat),
    )
