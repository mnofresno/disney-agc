"""Tests for volume adjustment strategies."""

from chromecast_agc.audio.classifier import AudioTypeResult
from chromecast_agc.volume.strategy import (
    DialogueStrategy,
    MusicStrategy,
    SilenceStrategy,
)


def test_dialogue_strategy_high_confidence(test_settings):
    """Test dialogue strategy with high confidence."""
    strategy = DialogueStrategy()

    result = AudioTypeResult(
        type="dialogue",
        confidence=0.9,
        features=None,
        scores={"dialogue": 0.9, "music": 0.1},
    )

    adjustment = strategy.calculate_adjustment(result, -25.0, test_settings)

    assert adjustment > 0
    assert adjustment > test_settings.adjustment_step


def test_dialogue_strategy_low_confidence(test_settings):
    """Test dialogue strategy with low confidence."""
    strategy = DialogueStrategy()

    result = AudioTypeResult(
        type="dialogue",
        confidence=0.2,
        features=None,
        scores={"dialogue": 0.2, "music": 0.8},
    )

    adjustment = strategy.calculate_adjustment(result, -25.0, test_settings)

    assert adjustment == 0


def test_music_strategy_high_confidence(test_settings):
    """Test music strategy with high confidence."""
    strategy = MusicStrategy()

    result = AudioTypeResult(
        type="music",
        confidence=0.8,
        features=None,
        scores={"dialogue": 0.2, "music": 0.8},
    )

    adjustment = strategy.calculate_adjustment(result, -15.0, test_settings)

    assert adjustment < 0


def test_music_strategy_low_confidence(test_settings):
    """Test music strategy with low confidence."""
    strategy = MusicStrategy()

    result = AudioTypeResult(
        type="music",
        confidence=0.4,
        features=None,
        scores={"dialogue": 0.6, "music": 0.4},
    )

    adjustment = strategy.calculate_adjustment(result, -15.0, test_settings)

    assert adjustment == 0


def test_silence_strategy(test_settings):
    """Test silence strategy."""
    strategy = SilenceStrategy()

    result = AudioTypeResult(
        type="unknown",
        confidence=0.0,
        features=None,
        scores={"dialogue": 0.0, "music": 0.0},
    )

    adjustment = strategy.calculate_adjustment(result, -70.0, test_settings)

    assert adjustment > 0
    assert adjustment == int(test_settings.adjustment_step * 2)
