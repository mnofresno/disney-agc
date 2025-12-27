"""Tests for configuration settings."""

import pytest

from chromecast_agc.config.defaults import (
    get_default_settings,
    get_settings_for_distance,
)
from chromecast_agc.config.settings import Settings


def test_default_settings():
    """Test default settings creation."""
    settings = get_default_settings()

    assert isinstance(settings, Settings)
    assert settings.device_name == "AceituTele"
    assert 0 <= settings.volume_min < settings.volume_max <= 100
    assert settings.sample_rate > 0


def test_settings_validation_valid(test_settings):
    """Test settings validation with valid values."""
    test_settings.validate()


def test_settings_validation_invalid_volume():
    """Test settings validation with invalid volume."""
    settings = Settings(volume_min=50, volume_max=30)

    with pytest.raises(AssertionError):
        settings.validate()


def test_settings_validation_invalid_thresholds():
    """Test settings validation with invalid thresholds."""
    settings = Settings(threshold_loud=-50, threshold_quiet=-20)

    with pytest.raises(AssertionError):
        settings.validate()


def test_get_settings_for_distance():
    """Test getting settings optimized for distance."""
    settings = get_settings_for_distance(6.0)

    assert isinstance(settings, Settings)
    assert settings.volume_max == 85
    assert settings.volume_baseline_max == 75
    assert settings.target_db == -25.0
