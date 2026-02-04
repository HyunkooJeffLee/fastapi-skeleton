"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

for path in (
    ROOT / "packages" / "common" / "src",
    ROOT / "apps" / "internal_api" / "src",
    ROOT / "apps" / "external_api" / "src",
    ROOT / "apps" / "backoffice_api" / "src",
):
    sys.path.insert(0, str(path))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_LOG_LEVEL", "warning")
os.environ.setdefault("DB_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture(autouse=True)
def reset_settings_and_db() -> None:
    from common.db.session import reset_db
    from common.lib.config import reset_settings_cache

    reset_settings_cache()
    reset_db()
    yield
    reset_settings_cache()
    reset_db()
