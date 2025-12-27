"""Tests for audio history manager."""

from chromecast_agc.audio.classifier import AudioTypeResult
from chromecast_agc.state.history import HistoryManager


def test_history_initialization(test_settings):
    """Test history manager initialization."""
    history = HistoryManager(test_settings)

    assert len(history.audio_levels) == 0
    assert len(history.audio_types) == 0


def test_add_audio_level(test_settings):
    """Test adding audio level."""
    history = HistoryManager(test_settings)

    history.add_audio_level(-25.0)
    history.add_audio_level(-30.0)

    assert len(history.audio_levels) == 2


def test_add_audio_type(test_settings):
    """Test adding audio type."""
    history = HistoryManager(test_settings)

    result = AudioTypeResult(
        type="dialogue",
        confidence=0.8,
        features=None,
        scores={"dialogue": 0.8, "music": 0.2},
    )

    history.add_audio_type(result)

    assert len(history.audio_types) == 1


def test_get_avg_audio_level(test_settings):
    """Test getting average audio level."""
    history = HistoryManager(test_settings)

    history.add_audio_level(-20.0)
    history.add_audio_level(-30.0)

    avg = history.get_avg_audio_level()
    assert avg == -25.0


def test_get_avg_audio_level_empty(test_settings):
    """Test getting average from empty history."""
    history = HistoryManager(test_settings)

    avg = history.get_avg_audio_level()
    assert avg == 0.0


def test_get_recent_avg_audio_level(test_settings):
    """Test getting recent average."""
    history = HistoryManager(test_settings)

    history.add_audio_level(-20.0)
    history.add_audio_level(-30.0)
    history.add_audio_level(-40.0)

    recent_avg = history.get_recent_avg_audio_level(2)
    assert recent_avg == -35.0


def test_get_predominant_audio_type(test_settings):
    """Test getting predominant audio type."""
    history = HistoryManager(test_settings)

    dialogue_result = AudioTypeResult(
        type="dialogue",
        confidence=0.8,
        features=None,
        scores={"dialogue": 0.8, "music": 0.2},
    )

    history.add_audio_type(dialogue_result)
    history.add_audio_type(dialogue_result)

    predominant = history.get_predominant_audio_type()

    assert predominant is not None
    assert predominant.type == "dialogue"


def test_get_predominant_audio_type_insufficient(test_settings):
    """Test getting predominant with insufficient history."""
    history = HistoryManager(test_settings)

    result = history.get_predominant_audio_type()
    assert result is None


def test_clear(test_settings):
    """Test clearing history."""
    history = HistoryManager(test_settings)

    history.add_audio_level(-25.0)
    history.add_audio_type(
        AudioTypeResult(
            type="dialogue",
            confidence=0.8,
            features=None,
            scores={"dialogue": 0.8, "music": 0.2},
        )
    )

    history.clear()

    assert len(history.audio_levels) == 0
    assert len(history.audio_types) == 0
