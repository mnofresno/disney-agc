"""Tests for audio classifier."""

from chromecast_agc.audio.analyzer import SpectrumFeatures
from chromecast_agc.audio.classifier import AudioClassifier, AudioTypeResult


def test_classify_dialogue(test_settings):
    """Test classification of dialogue."""
    classifier = AudioClassifier(test_settings)

    features = SpectrumFeatures(
        voice_ratio=0.4,
        voice_formants_ratio=0.25,
        bass_to_voice_ratio=0.3,
        high_to_voice_ratio=0.2,
        spectral_variation=0.8,
        background_music_ratio=0.1,
        ratio_voice_formants=0.25,
        ratio_bass=0.1,
        ratio_high=0.15,
    )

    result = classifier.classify(features)

    assert isinstance(result, AudioTypeResult)
    assert result.type in ["dialogue", "music", "unknown"]
    assert 0.0 <= result.confidence <= 1.0
    assert "dialogue" in result.scores
    assert "music" in result.scores


def test_classify_music(test_settings):
    """Test classification of music."""
    classifier = AudioClassifier(test_settings)

    features = SpectrumFeatures(
        voice_ratio=0.1,
        voice_formants_ratio=0.05,
        bass_to_voice_ratio=1.5,
        high_to_voice_ratio=2.0,
        spectral_variation=2.5,
        background_music_ratio=0.5,
        ratio_voice_formants=0.05,
        ratio_bass=0.3,
        ratio_high=0.4,
    )

    result = classifier.classify(features)

    assert isinstance(result, AudioTypeResult)
    assert result.type in ["dialogue", "music", "unknown"]
    assert 0.0 <= result.confidence <= 1.0


def test_classify_sung_song(test_settings):
    """Test classification of sung song (voice + background music)."""
    classifier = AudioClassifier(test_settings)

    features = SpectrumFeatures(
        voice_ratio=0.3,
        voice_formants_ratio=0.15,
        bass_to_voice_ratio=0.8,
        high_to_voice_ratio=1.0,
        spectral_variation=1.5,
        background_music_ratio=0.35,
        ratio_voice_formants=0.15,
        ratio_bass=0.2,
        ratio_high=0.25,
    )

    result = classifier.classify(features)

    assert isinstance(result, AudioTypeResult)
    assert result.type in ["dialogue", "music", "unknown"]


def test_classify_unknown(test_settings):
    """Test classification of unknown audio."""
    classifier = AudioClassifier(test_settings)

    features = SpectrumFeatures(
        voice_ratio=0.15,
        voice_formants_ratio=0.05,
        bass_to_voice_ratio=0.5,
        high_to_voice_ratio=0.5,
        spectral_variation=1.0,
        background_music_ratio=0.15,
        ratio_voice_formants=0.05,
        ratio_bass=0.15,
        ratio_high=0.15,
    )

    result = classifier.classify(features)

    assert isinstance(result, AudioTypeResult)
    assert result.type in ["dialogue", "music", "unknown"]


def test_classifier_thresholds(test_settings):
    """Test that classifier uses correct thresholds."""
    classifier = AudioClassifier(test_settings)

    assert classifier.dialogue_threshold == 0.15
    assert classifier.music_threshold == 0.35
