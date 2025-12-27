"""Tests for platform detection."""

import sys
from unittest.mock import MagicMock, patch

from chromecast_agc.utils.platform import (
    get_keyboard_module,
    is_linux,
    is_macos,
    is_windows,
)


@patch("platform.system")
def test_is_macos(mock_system):
    """Test macOS detection."""
    mock_system.return_value = "Darwin"
    assert is_macos() is True

    mock_system.return_value = "Linux"
    assert is_macos() is False


@patch("platform.system")
def test_is_linux(mock_system):
    """Test Linux detection."""
    mock_system.return_value = "Linux"
    assert is_linux() is True

    mock_system.return_value = "Darwin"
    assert is_linux() is False


@patch("platform.system")
def test_is_windows(mock_system):
    """Test Windows detection."""
    mock_system.return_value = "Windows"
    assert is_windows() is True

    mock_system.return_value = "Linux"
    assert is_windows() is False


@patch("chromecast_agc.utils.platform.is_macos")
def test_get_keyboard_module_macos(mock_is_macos):
    """Test getting keyboard module on macOS."""
    mock_is_macos.return_value = True
    mock_pynput = MagicMock()

    with patch.dict(sys.modules, {"pynput": mock_pynput}):
        module = get_keyboard_module()

    assert module == mock_pynput


@patch("chromecast_agc.utils.platform.is_macos")
def test_get_keyboard_module_linux(mock_is_macos):
    """Test getting keyboard module on Linux."""
    mock_is_macos.return_value = False
    mock_keyboard = MagicMock()

    with patch.dict(sys.modules, {"keyboard": mock_keyboard}):
        module = get_keyboard_module()

    assert module == mock_keyboard
