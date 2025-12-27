"""Integration tests for audio processing pipeline."""

import numpy as np
import pytest

from chromecast_agc.audio.analyzer import AudioAnalyzer
from chromecast_agc.audio.classifier import AudioClassifier
from chromecast_agc.audio.normalizer import AudioNormalizer


@pytest.mark.integration
def test_audio_pipeline_dialogue(test_settings):
    """Test complete audio pipeline for dialogue."""
    normalizer = AudioNormalizer(test_settings)
    analyzer = AudioAnalyzer(test_settings)
    classifier = AudioClassifier(test_settings)

    # Create dialogue-like signal
    t = np.linspace(0, 0.1, int(test_settings.sample_rate * 0.1))
    signal = np.sin(2 * np.pi * 1000 * t)  # 1kHz (voice formants)
    signal += np.random.randn(len(signal)) * 0.01

    # Process through pipeline
    normalized = normalizer.normalize(signal)
    db = analyzer.calculate_db(normalized)
    features = analyzer.analyze_spectrum(normalized)
    result = classifier.classify(features)

    assert db != -np.inf
    assert features.voice_formants_ratio > 0
    assert result.type in ["dialogue", "music", "unknown"]
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.integration
def test_audio_pipeline_music(test_settings):
    """Test complete audio pipeline for music."""
    normalizer = AudioNormalizer(test_settings)
    analyzer = AudioAnalyzer(test_settings)
    classifier = AudioClassifier(test_settings)

    # Create music-like signal
    t = np.linspace(0, 0.1, int(test_settings.sample_rate * 0.1))
    signal = np.sin(2 * np.pi * 100 * t)  # 100Hz bass
    signal += np.sin(2 * np.pi * 5000 * t) * 0.5  # 5kHz high
    signal += np.random.randn(len(signal)) * 0.01

    # Process through pipeline
    normalized = normalizer.normalize(signal)
    db = analyzer.calculate_db(normalized)
    features = analyzer.analyze_spectrum(normalized)
    result = classifier.classify(features)

    assert db != -np.inf
    assert features.bass_to_voice_ratio > 0
    assert result.type in ["dialogue", "music", "unknown"]
    assert 0.0 <= result.confidence <= 1.0
