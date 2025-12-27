"""Tests for dependency management."""

from unittest.mock import MagicMock, patch

from chromecast_agc.utils.dependencies import (
    check_dependencies,
    get_platform_dependencies,
)


@patch("platform.system")
def test_get_platform_dependencies_macos(mock_system):
    """Test getting dependencies for macOS."""
    mock_system.return_value = "Darwin"

    deps = get_platform_dependencies()

    assert "numpy" in deps
    assert "sounddevice" in deps
    assert "pychromecast" in deps
    assert "pynput" in deps
    assert "keyboard" not in deps


@patch("platform.system")
def test_get_platform_dependencies_linux(mock_system):
    """Test getting dependencies for Linux."""
    mock_system.return_value = "Linux"

    deps = get_platform_dependencies()

    assert "numpy" in deps
    assert "sounddevice" in deps
    assert "pychromecast" in deps
    assert "keyboard" in deps
    assert "pynput" not in deps


@patch("builtins.__import__")
def test_check_dependencies_all_installed(mock_import):
    """Test checking dependencies when all are installed."""
    mock_import.return_value = MagicMock()

    result = check_dependencies()

    assert result is True


@patch("builtins.__import__")
def test_check_dependencies_missing(mock_import):
    """Test checking dependencies when some are missing."""

    def side_effect(name, *args, **kwargs):
        if name == "numpy":
            raise ImportError()
        return MagicMock()

    mock_import.side_effect = side_effect

    result = check_dependencies()

    assert result is False
