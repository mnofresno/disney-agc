"""Tests for adaptive thresholds."""

from chromecast_agc.config.adaptive import AdaptiveThresholds


def test_adaptive_thresholds_initialization(test_settings):
    """Test adaptive thresholds initialization."""
    adaptive = AdaptiveThresholds(test_settings)

    assert adaptive.threshold_loud == test_settings.threshold_loud
    assert adaptive.threshold_quiet == test_settings.threshold_quiet
    assert adaptive.user_set_volume is None


def test_adjust_for_volume_increase(test_settings):
    """Test threshold adjustment when volume is increased."""
    adaptive = AdaptiveThresholds(test_settings)
    initial_quiet = adaptive.threshold_quiet

    adaptive.adjust_for_volume(volume=60, current_db=-50.0, previous_volume=40)

    assert adaptive.user_set_volume == 60
    assert adaptive.threshold_quiet >= initial_quiet


def test_adjust_for_volume_decrease(test_settings):
    """Test threshold adjustment when volume is decreased."""
    adaptive = AdaptiveThresholds(test_settings)
    initial_loud = adaptive.threshold_loud

    adaptive.adjust_for_volume(volume=30, current_db=-10.0, previous_volume=50)

    assert adaptive.user_set_volume == 30
    assert adaptive.threshold_loud <= initial_loud


def test_reset(test_settings):
    """Test resetting adaptive thresholds."""
    adaptive = AdaptiveThresholds(test_settings)
    initial_loud = adaptive.threshold_loud
    initial_quiet = adaptive.threshold_quiet

    adaptive.adjust_for_volume(volume=60, current_db=-30.0, previous_volume=40)
    adaptive.reset()

    assert adaptive.threshold_loud == initial_loud
    assert adaptive.threshold_quiet == initial_quiet
    assert adaptive.user_set_volume is None
