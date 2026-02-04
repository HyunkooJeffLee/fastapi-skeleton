from common.lib.config import get_settings


def test_settings_default_modules() -> None:
    settings = get_settings()
    assert "common.db.models" in settings.alembic_modules()
