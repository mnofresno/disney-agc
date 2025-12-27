"""Tests for state manager."""

from chromecast_agc.audio.classifier import AudioTypeResult
from chromecast_agc.state.manager import ApplicationState, StateManager


def test_state_manager_initialization(test_settings):
    """Test state manager initialization."""
    manager = StateManager(test_settings)

    assert manager.get_current_volume() is None
    assert manager.get_target_db() == test_settings.target_db


def test_update_volume(test_settings):
    """Test volume update."""
    manager = StateManager(test_settings)

    manager.update_volume(50)
    assert manager.get_current_volume() == 50


def test_update_audio_level(test_settings):
    """Test audio level update."""
    manager = StateManager(test_settings)

    manager.update_audio_level(-25.0)
    state = manager.get_state()
    assert state.audio_level_db == -25.0


def test_update_audio_type(test_settings):
    """Test audio type update."""
    manager = StateManager(test_settings)

    result = AudioTypeResult(
        type="dialogue",
        confidence=0.8,
        features=None,
        scores={"dialogue": 0.8, "music": 0.2},
    )

    manager.update_audio_type(result)
    state = manager.get_state()
    assert state.audio_type == "dialogue"
    assert state.audio_confidence == 0.8


def test_record_manual_adjustment(test_settings):
    """Test manual adjustment recording."""
    manager = StateManager(test_settings)

    manager.record_manual_adjustment()
    state = manager.get_state()
    assert state.is_manual_mode is True
    assert state.manual_pause_remaining > 0


def test_adjust_baseline(test_settings):
    """Test baseline adjustment."""
    manager = StateManager(test_settings)
    initial_target = manager.get_target_db()

    manager.adjust_baseline(5.0)
    assert manager.get_target_db() == initial_target + 5.0


def test_get_state(test_settings):
    """Test getting complete state."""
    manager = StateManager(test_settings)

    manager.update_volume(45)
    manager.update_audio_level(-28.0)

    result = AudioTypeResult(
        type="music",
        confidence=0.7,
        features=None,
        scores={"dialogue": 0.3, "music": 0.7},
    )
    manager.update_audio_type(result)

    state = manager.get_state()

    assert isinstance(state, ApplicationState)
    assert state.current_volume == 45
    assert state.audio_level_db == -28.0
    assert state.audio_type == "music"
    assert state.audio_confidence == 0.7
