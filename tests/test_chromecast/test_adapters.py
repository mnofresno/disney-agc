"""Tests for Chromecast adapters."""

from unittest.mock import MagicMock, patch

from chromecast_agc.chromecast.adapters import CattAdapter, PyChromecastAdapter


def test_pychromecast_adapter_initialization():
    """Test PyChromecast adapter initialization."""
    adapter = PyChromecastAdapter()

    assert adapter.cast is None
    assert adapter.browser is None
    assert adapter.is_connected() is False


@patch("builtins.__import__")
def test_pychromecast_adapter_connect_success(mock_import):
    """Test successful connection with PyChromecast."""
    adapter = PyChromecastAdapter()

    mock_pychromecast = MagicMock()
    mock_cast = MagicMock()
    mock_cast.wait = MagicMock()
    mock_browser = MagicMock()

    mock_pychromecast.get_listed_chromecasts.return_value = (
        [mock_cast],
        mock_browser,
    )

    def import_side_effect(name, *args, **kwargs):
        if name == "pychromecast":
            return mock_pychromecast
        return __import__(name, *args, **kwargs)

    mock_import.side_effect = import_side_effect

    result = adapter.connect("TestDevice")

    assert result is True
    assert adapter.is_connected() is True
    assert adapter.cast == mock_cast


@patch("builtins.__import__")
def test_pychromecast_adapter_connect_failure(mock_import):
    """Test failed connection with PyChromecast."""
    adapter = PyChromecastAdapter()

    mock_pychromecast = MagicMock()
    mock_pychromecast.get_listed_chromecasts.return_value = ([], MagicMock())

    def import_side_effect(name, *args, **kwargs):
        if name == "pychromecast":
            return mock_pychromecast
        return __import__(name, *args, **kwargs)

    mock_import.side_effect = import_side_effect

    result = adapter.connect("TestDevice")

    assert result is False
    assert adapter.is_connected() is False


def test_catt_adapter_initialization():
    """Test Catt adapter initialization."""
    adapter = CattAdapter("TestDevice")

    assert adapter.device_name == "TestDevice"
    assert adapter.is_connected() is False


@patch("subprocess.run")
def test_catt_adapter_connect_success(mock_run):
    """Test successful connection with Catt."""
    adapter = CattAdapter("TestDevice")
    mock_run.return_value.returncode = 0

    result = adapter.connect("TestDevice")

    assert result is True
    assert adapter.is_connected() is True


@patch("subprocess.run")
def test_catt_adapter_connect_failure(mock_run):
    """Test failed connection with Catt."""
    adapter = CattAdapter("TestDevice")
    mock_run.return_value.returncode = 1

    result = adapter.connect("TestDevice")

    assert result is False
