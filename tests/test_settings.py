"""Tests for settings configuration."""
import pytest


def test_settings_has_defaults():
    """Settings should have expected default values."""
    from bot.settings import settings

    # TELEGRAM_KEY_BOT might be empty or set via env
    assert hasattr(settings, "TELEGRAM_KEY_BOT")
    assert settings.REDIS_URL == "redis://localhost:6379/0"
    assert settings.VIA_CACHE_TTL == 60
    assert settings.DB_SYNC_INTERVAL_SECONDS == 900
    assert hasattr(settings, "ADMIN_IDS")


def test_settings_admin_ids_parsing():
    """ADMIN_IDS should be parseable as comma-separated integers."""
    from bot.handlers.admin import _load_admin_ids

    ids = _load_admin_ids()
    assert isinstance(ids, set)


def test_settings_extra_ignored():
    """Unknown env vars should not crash settings."""
    from bot.settings import Settings
    # Config should have extra='ignore'
    config_dict = Settings.model_config
    assert config_dict.get("extra") == "ignore"
