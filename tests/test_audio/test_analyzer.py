"""Tests for audio analyzer."""

import numpy as np

from chromecast_agc.audio.analyzer import AudioAnalyzer, SpectrumFeatures


def test_calculate_db_silence(default_settings):
    """Test dB calculation for silence."""
    analyzer = AudioAnalyzer(default_settings)
    silence = np.zeros(1000)
    db = analyzer.calculate_db(silence)
    assert db == -np.inf


def test_calculate_db_signal(default_settings):
    """Test dB calculation for audio signal."""
    analyzer = AudioAnalyzer(default_settings)
    signal = np.random.randn(1000) * 0.1
    db = analyzer.calculate_db(signal)
    assert isinstance(db, float)
    assert db < 0
    assert db != -np.inf


def test_analyze_spectrum_silence(default_settings):
    """Test spectrum analysis for silence."""
    analyzer = AudioAnalyzer(default_settings)
    silence = np.zeros(1000)
    features = analyzer.analyze_spectrum(silence)

    assert isinstance(features, SpectrumFeatures)
    assert features.voice_ratio == 0.0
    assert features.background_music_ratio == 0.0


def test_analyze_spectrum_voice_signal(default_settings):
    """Test spectrum analysis for voice-like signal."""
    analyzer = AudioAnalyzer(default_settings)

    # Create a signal with energy in voice formants (500-2000 Hz)
    t = np.linspace(0, 0.1, int(default_settings.sample_rate * 0.1))
    signal = np.sin(2 * np.pi * 1000 * t)  # 1kHz tone (in voice formants range)
    signal += np.random.randn(len(signal)) * 0.01

    features = analyzer.analyze_spectrum(signal)

    assert isinstance(features, SpectrumFeatures)
    assert features.voice_formants_ratio > 0
    assert features.voice_ratio > 0


def test_analyze_spectrum_music_signal(default_settings):
    """Test spectrum analysis for music-like signal."""
    analyzer = AudioAnalyzer(default_settings)

    # Create a signal with energy in bass and highs
    t = np.linspace(0, 0.1, int(default_settings.sample_rate * 0.1))
    signal = np.sin(2 * np.pi * 100 * t)  # 100Hz bass
    signal += np.sin(2 * np.pi * 5000 * t) * 0.5  # 5kHz high
    signal += np.random.randn(len(signal)) * 0.01

    features = analyzer.analyze_spectrum(signal)

    assert isinstance(features, SpectrumFeatures)
    assert features.background_music_ratio > 0
    assert features.bass_to_voice_ratio >= 0
