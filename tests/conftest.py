"""Pytest configuration and fixtures."""

import pytest

from chromecast_agc.config.settings import Settings


@pytest.fixture
def default_settings():
    return Settings()


@pytest.fixture
def test_settings():
    return Settings(
        device_name="TestDevice",
        volume_min=0,
        volume_max=100,
        volume_baseline_max=80,
        target_db=-20.0,
        threshold_loud=-15.0,
        threshold_quiet=-35.0,
        adjustment_step=5,
        min_adjustment_interval=0.1,
        manual_pause_duration=5.0,
        sample_rate=44100,
        chunk_duration=0.1,
        smoothing_window=3,
        normalization_target_rms=0.1,
        normalization_max_factor=10.0,
        silence_threshold_db=-60.0,
    )
