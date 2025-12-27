"""Tests for volume controller."""

import time
from unittest.mock import MagicMock

from chromecast_agc.audio.classifier import AudioTypeResult
from chromecast_agc.chromecast.adapters import PyChromecastAdapter
from chromecast_agc.state.history import HistoryManager
from chromecast_agc.volume.controller import VolumeController


def test_volume_controller_initialization(test_settings):
    """Test volume controller initialization."""
    chromecast = PyChromecastAdapter()
    state = MagicMock()
    history = HistoryManager(test_settings)

    controller = VolumeController(test_settings, chromecast, state, history)

    assert controller.settings == test_settings
    assert controller.chromecast == chromecast
    assert controller.state == state


def test_manual_adjust_increase(test_settings):
    """Test manual volume increase."""
    chromecast = PyChromecastAdapter()
    chromecast.get_volume = MagicMock(return_value=50)
    chromecast.set_volume = MagicMock(return_value=True)
    state = MagicMock()
    history = HistoryManager(test_settings)

    controller = VolumeController(test_settings, chromecast, state, history)

    result = controller.manual_adjust(5)

    assert result is True
    chromecast.set_volume.assert_called_with(55)
    state.record_manual_adjustment.assert_called_once()


def test_manual_adjust_decrease(test_settings):
    """Test manual volume decrease."""
    chromecast = PyChromecastAdapter()
    chromecast.get_volume = MagicMock(return_value=50)
    chromecast.set_volume = MagicMock(return_value=True)
    state = MagicMock()
    history = HistoryManager(test_settings)

    controller = VolumeController(test_settings, chromecast, state, history)

    result = controller.manual_adjust(-5)

    assert result is True
    chromecast.set_volume.assert_called_with(45)


def test_manual_adjust_no_volume(test_settings):
    """Test manual adjust when volume is None."""
    chromecast = PyChromecastAdapter()
    chromecast.get_volume = MagicMock(return_value=None)
    state = MagicMock()
    history = HistoryManager(test_settings)

    controller = VolumeController(test_settings, chromecast, state, history)

    result = controller.manual_adjust(5)

    assert result is False


def test_adjust_based_on_type_dialogue(test_settings):
    """Test volume adjustment for dialogue."""
    chromecast = PyChromecastAdapter()
    chromecast.get_volume = MagicMock(return_value=50)
    chromecast.set_volume = MagicMock(return_value=True)
    state = MagicMock()
    state.get_state.return_value.is_manual_mode = False
    history = HistoryManager(test_settings)

    controller = VolumeController(test_settings, chromecast, state, history)
    controller.last_adjustment_time = time.time() - 1.0

    result = AudioTypeResult(
        type="dialogue",
        confidence=0.9,
        features=None,
        scores={"dialogue": 0.9, "music": 0.1},
    )

    new_volume = controller.adjust_based_on_type(-25.0, result)

    assert new_volume is not None
    assert new_volume > 50
