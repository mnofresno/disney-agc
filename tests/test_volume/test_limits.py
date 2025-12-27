"""Tests for volume limits."""

from chromecast_agc.volume.limits import VolumeLimits


def test_apply_limits_automatic(test_settings):
    """Test applying limits for automatic adjustments."""
    limits = VolumeLimits(test_settings)

    volume = limits.apply_limits(90, is_manual=False)
    assert volume <= test_settings.volume_baseline_max

    volume = limits.apply_limits(10, is_manual=False)
    assert volume >= test_settings.volume_min


def test_apply_limits_manual(test_settings):
    """Test applying limits for manual adjustments."""
    limits = VolumeLimits(test_settings)

    volume = limits.apply_limits(90, is_manual=True)
    assert volume <= test_settings.volume_max
    assert volume == 90

    volume = limits.apply_limits(5, is_manual=True)
    assert volume >= test_settings.volume_min


def test_can_exceed_baseline(test_settings):
    """Test baseline exceed check."""
    limits = VolumeLimits(test_settings)

    assert limits.can_exceed_baseline(is_manual=True) is True
    assert limits.can_exceed_baseline(is_manual=False) is False
