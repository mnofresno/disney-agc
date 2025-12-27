"""Tests for audio normalizer."""

import numpy as np

from chromecast_agc.audio.normalizer import AudioNormalizer


def test_normalize_weak_signal(test_settings):
    """Test normalization of weak signal."""
    normalizer = AudioNormalizer(test_settings)

    weak_signal = np.random.randn(1000) * 0.01
    normalized = normalizer.normalize(weak_signal)

    assert isinstance(normalized, np.ndarray)
    assert len(normalized) == len(weak_signal)

    rms_normalized = np.sqrt(np.mean(normalized**2))
    assert rms_normalized > np.sqrt(np.mean(weak_signal**2))


def test_normalize_strong_signal(test_settings):
    """Test normalization of strong signal."""
    normalizer = AudioNormalizer(test_settings)

    strong_signal = np.random.randn(1000) * 0.5
    normalized = normalizer.normalize(strong_signal)

    assert isinstance(normalized, np.ndarray)
    assert len(normalized) == len(strong_signal)


def test_normalize_silence(test_settings):
    """Test normalization of silence."""
    normalizer = AudioNormalizer(test_settings)

    silence = np.zeros(1000)
    normalized = normalizer.normalize(silence)

    assert isinstance(normalized, np.ndarray)
    assert np.allclose(normalized, silence)


def test_normalize_respects_max_factor(test_settings):
    """Test that normalization respects max factor limit."""
    normalizer = AudioNormalizer(test_settings)

    very_weak_signal = np.random.randn(1000) * 0.001
    normalized = normalizer.normalize(very_weak_signal)

    rms_normalized = np.sqrt(np.mean(normalized**2))
    max_expected_rms = test_settings.normalization_target_rms * test_settings.normalization_max_factor

    assert rms_normalized <= max_expected_rms * 1.1
