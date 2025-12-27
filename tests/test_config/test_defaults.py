"""Tests for default configurations."""

from chromecast_agc.config.defaults import (
    get_default_settings,
    get_settings_for_distance,
)


def test_get_default_settings():
    """Test getting default settings."""
    settings = get_default_settings()

    assert settings.device_name == "AceituTele"
    assert settings.volume_min == 20
    assert isinstance(settings.volume_max, int)
    assert settings.volume_max > 0


def test_get_settings_for_distance():
    """Test getting settings for specific distance."""
    settings = get_settings_for_distance(6.0)

    assert settings.device_name == "AceituTele"
    assert settings.volume_max == 85
    assert settings.volume_baseline_max == 75
    assert settings.target_db == -25.0
    assert settings.threshold_loud == -20.0
    assert settings.threshold_quiet == -45.0


def test_get_settings_for_distance_custom():
    """Test getting settings for custom distance."""
    settings = get_settings_for_distance(10.0)

    assert isinstance(settings.volume_max, int)
    assert settings.volume_max <= 100
